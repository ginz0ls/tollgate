"""Client HTTP stretto per gli elenchi dei modelli dei fornitori, e cache di 24 ore.

È l'unico modulo del plugin che esce in rete (B3-bis, decisioni 5, 7 e 9). Gli hook non lo
importano mai. La chiave va solo in un'intestazione e non esce da qui: gli errori diventano
`FetchError` con un testo fisso, sollevata fuori da ogni `except`, così nessuna eccezione
originale (che può contenere URL o intestazioni) resta in `__context__` o `__cause__`."""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
import tomllib
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tollgate_analysis.models import PROVIDERS, ModelsFormatError
from tollgate_core import clock
from tollgate_core.paths import State

CACHE_HOURS = 24
_CHUNK = 64 * 1024
_PAGINGS = ("anthropic", "gemini", "none")
_KNOWN_KEYS = frozenset(("url", "paging", "auth", "headers", "env", "page", "hint"))
_REQUIRED_KEYS = ("url", "paging", "auth", "env", "page")
_HEADER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")
_ENV_NAME = re.compile(r"[A-Z][A-Z0-9_]*")


class ProvidersError(ValueError):
    """`templates/models.toml` illeggibile o non valido."""


class FetchError(Exception):
    """Lettura di un elenco non riuscita; il testo è sempre uno dei testi fissi del client."""


class DeadlineSkipped(FetchError):
    """Scadenza del controllo già finita prima di chiedere l'elenco, e nessuna cache da usare."""


@dataclass(frozen=True)
class Provider:
    name: str
    url: str
    host: str
    paging: str
    auth: str
    headers: dict[str, str]
    env: tuple[str, ...]
    page: str
    hint: str


class Deadline:
    """Scadenza unica di un controllo: `left()` secondi rimasti, `check()` solleva a scadenza."""

    def __init__(self, seconds: float, clock=time.monotonic):
        self._clock = clock
        self._end = clock() + seconds

    def left(self) -> float:
        return max(0.0, self._end - self._clock())

    def check(self) -> None:
        if self.left() <= 0:
            raise FetchError("tempo scaduto")


# --- Dati dei fornitori ----------------------------------------------------------------

def _parse_provider(name: str, raw) -> Provider:
    def bad(why: str) -> ProvidersError:
        return ProvidersError(f"templates/models.toml: [{name}]: {why}")

    if not isinstance(raw, dict):
        raise bad("non è una tabella")
    unknown = sorted(set(raw) - _KNOWN_KEYS)
    if unknown:
        raise bad(f"chiave sconosciuta «{unknown[0]}»")
    for key in _REQUIRED_KEYS:
        if key not in raw:
            raise bad(f"manca «{key}»")
    url, paging, auth, page = raw["url"], raw["paging"], raw["auth"], raw["page"]
    hint, headers, env = raw.get("hint", ""), raw.get("headers", {}), raw["env"]
    if not all(isinstance(v, str) for v in (url, paging, auth, page, hint)):
        raise bad("url, paging, auth, page e hint devono essere testo")
    try:
        parts = urlsplit(url)
        port = parts.port
        host = parts.hostname
    except ValueError:
        raise bad("url non valido") from None
    if parts.scheme != "https" or not host:
        raise bad("url deve essere https con un host")
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        raise bad("url non può contenere utente o password")
    if port is not None or ":" in parts.netloc:
        raise bad("url non può contenere una porta")
    if any(k.lower() == "key" for k, _ in parse_qsl(parts.query, keep_blank_values=True)):
        raise bad("url non può contenere key= nella query")
    if parts.fragment:
        raise bad("url non può contenere un frammento")
    if paging not in _PAGINGS:
        raise bad(f"paging deve essere uno tra {', '.join(_PAGINGS)}")
    if auth != "bearer" and not _HEADER_NAME.fullmatch(auth):
        raise bad("auth deve essere «bearer» o il nome di un'intestazione")
    if not page.startswith("https://"):
        raise bad("page deve essere un indirizzo https")
    if not isinstance(headers, dict) or not all(
            isinstance(k, str) and _HEADER_NAME.fullmatch(k) and isinstance(v, str) and v
            and v.isascii() and v.isprintable() for k, v in headers.items()):
        raise bad("headers deve essere una tabella di intestazioni di testo")
    if (not isinstance(env, list) or not env
            or not all(isinstance(v, str) and _ENV_NAME.fullmatch(v) for v in env)):
        raise bad("env deve essere un elenco non vuoto di nomi di variabile")
    try:
        re.compile(hint)
    except re.error:
        raise bad("hint non è un'espressione regolare valida") from None
    return Provider(name, url, host, paging, auth, dict(headers), tuple(env), page, hint)


def load_providers(plugin_root: Path) -> dict[str, Provider]:
    path = Path(plugin_root) / "templates" / "models.toml"
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise ProvidersError(f"templates/models.toml non letto: {type(e).__name__}") from None
    missing = sorted(set(PROVIDERS) - set(raw))
    extra = sorted(set(raw) - set(PROVIDERS))
    if missing or extra:
        raise ProvidersError("templates/models.toml: fornitori attesi " + ", ".join(PROVIDERS)
                             + (f"; mancano {', '.join(missing)}" if missing else "")
                             + (f"; in più {', '.join(extra)}" if extra else ""))
    return {name: _parse_provider(name, raw[name]) for name in PROVIDERS}


def api_key(provider: Provider, environ: Mapping[str, str]) -> str | None:
    """La prima variabile non vuota dell'elenco del fornitore (prima quella dedicata); un valore
    che non può stare in un'intestazione (non ASCII, caratteri di controllo) si salta."""
    for name in provider.env:
        value = (environ.get(name) or "").strip()
        if value and value.isascii() and value.isprintable():
            return value
    return None


# --- Client ----------------------------------------------------------------------------

class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._refuse(req, fp, code, msg, headers)

    def _refuse(self, req, fp, code, msg, headers):
        if fp is not None:
            fp.close()
        raise FetchError("redirect rifiutato")

    http_error_301 = http_error_302 = http_error_303 = _refuse
    http_error_307 = http_error_308 = _refuse


def build_opener() -> urllib.request.OpenerDirector:
    """Solo `https`, nessun proxy dell'ambiente, nessun redirect. `ProxyHandler({})` non lascia
    traccia in `opener.handlers` (senza proxy non ha metodi da registrare), ma è ciò che toglie
    i proxy: `OpenerDirector()` da solo non ne usa nessuno. `UnknownHandler` dà un `URLError`
    pulito per ogni schema che non sia `https`."""
    opener = urllib.request.OpenerDirector()
    for handler in (urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(),
                    urllib.request.UnknownHandler(), urllib.request.HTTPDefaultErrorHandler(),
                    urllib.request.HTTPErrorProcessor(), _RefuseRedirect()):
        opener.add_handler(handler)
    return opener


def _next_url(provider: Provider, url: str, page) -> str | None:
    if not isinstance(page, dict):
        return None
    if provider.paging == "anthropic":
        param, token = "after_id", page.get("last_id") if page.get("has_more") is True else None
    elif provider.paging == "gemini":
        param, token = "pageToken", page.get("nextPageToken")
    else:
        return None
    if not isinstance(token, str) or not token:
        return None
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != param]
    query.append((param, token))
    return urlunsplit(parts._replace(query=urlencode(query)))


def _get_json(provider: Provider, key: str, url: str, deadline: Deadline, opener, timeout: float,
              max_bytes: int):
    """Una pagina letta e decodificata. Ritorna `(pagina, None)` o `(None, testo dell'errore)`:
    l'eccezione la solleva il chiamante, fuori da ogni `except`."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != provider.host:
        return None, "host diverso da quello del fornitore"
    headers = {"Accept": "application/json", **provider.headers}
    if provider.auth == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    else:
        headers[provider.auth] = key
    reason = None
    body = bytearray()
    resp = None
    try:
        deadline.check()
        resp = opener.open(urllib.request.Request(url, headers=headers, method="GET"),
                           timeout=min(timeout, deadline.left()))
        status = getattr(resp, "status", 200)
        if 300 <= status < 400:
            reason = "redirect rifiutato"
        elif status != 200:
            reason = _http_reason(status)
        else:
            while True:
                deadline.check()
                chunk = resp.read(min(_CHUNK, max_bytes + 1 - len(body)))
                if not chunk:
                    break
                body += chunk
                if len(body) > max_bytes:
                    reason = "risposta troppo grande"
                    break
    except FetchError as e:
        reason = str(e)
    except HTTPError as e:
        reason = "redirect rifiutato" if 300 <= e.code < 400 else _http_reason(e.code)
        e.close()
    except URLError as e:
        reason = "tempo scaduto" if isinstance(e.reason, TimeoutError) else "nessuna risposta"
    except TimeoutError:
        reason = "tempo scaduto"
    except (OSError, HTTPException, ValueError):
        reason = "nessuna risposta"
    finally:
        close = getattr(resp, "close", None)
        if close is not None:
            close()
    if reason is not None:
        return None, reason
    try:
        return json.loads(bytes(body).decode("utf-8")), None
    except (ValueError, RecursionError):
        return None, "risposta non JSON"


def _http_reason(status: int) -> str:
    if status in (401, 403):
        return "chiave rifiutata"
    if status == 429:
        return "troppe richieste"
    return f"errore HTTP {status}"


def fetch_pages(provider: Provider, key: str, *, deadline: Deadline, opener=None,
                timeout: float = 5.0, max_bytes: int = 8 * 1024 * 1024,
                max_pages: int = 10) -> list[dict]:
    """Tutte le pagine dell'elenco di un fornitore. `FetchError` con un testo fisso se qualcosa
    va storto: mai il corpo, mai l'URL con i parametri, mai la chiave."""
    if opener is None:
        opener = build_opener()
    pages: list[dict] = []
    url: str | None = provider.url
    while url is not None:
        if len(pages) >= max_pages:
            reason = "troppe pagine"
            break
        page, reason = _get_json(provider, key, url, deadline, opener, timeout, max_bytes)
        if reason is not None:
            break
        pages.append(page)
        url = _next_url(provider, url, page)
    else:
        return pages
    raise FetchError(reason)


# --- Cache -----------------------------------------------------------------------------

def _cache_path(state: State, provider: Provider) -> Path:
    return state.root / "models" / f"{provider.name}.json"


def _write_cache(path: Path, text: str) -> None:
    """Temporaneo con nome unico nella stessa cartella e `os.replace`: due controlli
    concorrenti non si pestano; se la scrittura fallisce il temporaneo non resta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except (OSError, ValueError):
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_cache(path: Path, validate: Callable[[list[dict]], object]):
    """`(fetched_at, pagine)` o `None` se manca, è illeggibile o non passa la convalida."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        fetched = clock.parse(data["fetched_at"])
        pages = data["pages"]
        if not isinstance(pages, list) or not all(isinstance(p, dict) for p in pages):
            return None
        validate(pages)
    except Exception:
        return None
    return fetched, pages


def cached_pages(state: State, provider: Provider, key: str, *, now: datetime, deadline: Deadline,
                 validate: Callable[[list[dict]], object], refresh: bool = False,
                 fetch=None) -> tuple[list[dict], str | None]:
    """Le pagine dell'elenco: dalla cache se ha meno di `CACHE_HOURS` ore, altrimenti dalla rete.
    Seconda voce: `None` se vengono dalla rete, altrimenti la riga di cache (senza il prefisso
    `modelli: <fornitore>: `). `validate` si chiama sulle pagine nuove prima di scrivere la
    cache. Rete fallita (o scadenza del controllo già finita, o risposta di forma inattesa) con
    una cache leggibile: si usa quella e la cache non cambia; senza, `FetchError`
    (`DeadlineSkipped` se la scadenza era finita prima di chiedere; `ModelsFormatError` se la
    forma era sbagliata)."""
    path = _cache_path(state, provider)
    cached = _read_cache(path, validate)
    if cached is not None and not refresh:
        age = now - cached[0]
        if timedelta(0) <= age < timedelta(hours=CACHE_HOURS):
            return cached[1], f"elenco dalla cache del {cached[0]:%Y-%m-%d}"
    if fetch is None:
        fetch = fetch_pages
    failure = None
    skipped = False
    pages = None
    if deadline.left() <= 0:
        failure, skipped = "tempo scaduto", True
    else:
        try:
            pages = fetch(provider, key, deadline=deadline)
        except FetchError as e:
            failure = str(e)
    if failure is None:
        try:
            validate(pages)
        except ModelsFormatError:
            if cached is None:
                raise
            failure = "forma inattesa"
    if failure is not None:
        if cached is None:
            raise (DeadlineSkipped if skipped else FetchError)(failure)
        return cached[1], (f"rete non riuscita ({failure}), "
                           f"elenco dalla cache del {cached[0]:%Y-%m-%d}")
    try:
        _write_cache(path, json.dumps({"fetched_at": clock.fmt(now), "pages": pages}))
    except (OSError, ValueError):
        pass
    return pages, None
