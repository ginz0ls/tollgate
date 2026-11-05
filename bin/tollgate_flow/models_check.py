"""Controllo dei modelli AI dichiarati da un progetto (B3-bis, decisioni 1-7 e 13).

Legge i file di `[models] files` dalla punta di `ref` (mai dal working tree), ne estrae i nomi di
modello, li confronta con gli elenchi ufficiali dei fornitori di cui l'ambiente ha una chiave e
restituisce righe d'avviso. Avvisa e basta: non solleva mai, non rifiuta nulla. Le righe vengono
da file e da elenchi esterni: ogni testo variabile passa da `_plain` prima di uscire."""
from __future__ import annotations

import re
import time
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from tollgate_analysis import models
from tollgate_core import git
from tollgate_core.config import Config
from tollgate_core.paths import State

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
MAX_LINES = 12
DEADLINE_S = 20
MAX_FILE_BYTES = 256 * 1024
# Le righe per fornitore di `findings` cominciano così; un letterale non ha spazi, quindi quelle
# per modello (`<fornitore>: <letterale> (<file>): …`) non possono confondersi.
_NOT_CHECKED = ("ritiro non controllato:", "più nuovo non controllato:")
_BINARY_HEAD = 8000  # byte esaminati per riconoscere un file binario (come in `git._text`)


def _plain(text: str) -> str:
    """Testo di un repo per l'uscita: i caratteri non stampabili diventano `?`."""
    return "".join(c if c.isprintable() else "?" for c in str(text))


def _read_files(repo: Path, ref: str, files: list[str]) -> tuple[dict[str, str], list[str]]:
    """Testo dei file leggibili (nell'ordine di `files`) e una riga per ognuno che non lo è."""
    texts: dict[str, str] = {}
    lines: list[str] = []
    for rel in files:
        shown = _plain(rel)
        info = git.object_info_at(repo, ref, rel)
        if info is None:
            lines.append(f"modelli: {shown}: non trovato su {_plain(ref)}")
        elif info[0] != "blob":
            lines.append(f"modelli: {shown}: non è un file")
        elif info[1] > MAX_FILE_BYTES:
            lines.append(f"modelli: {shown}: non letto (binario o oltre 256 KiB)")
        else:
            data = git.show(repo, ref, rel)
            if data is None:
                lines.append(f"modelli: {shown}: non trovato su {_plain(ref)}")
            elif b"\0" in data[:_BINARY_HEAD]:
                lines.append(f"modelli: {shown}: non letto (binario o oltre 256 KiB)")
            else:
                texts[rel] = data.decode("utf-8", "replace")
    return texts, lines


def _wanted(provider, found: set[str]) -> bool:
    """Un letterale ha la forma dei nomi del fornitore (`hint`, sul nome già normalizzato)."""
    if not provider.hint:
        return False
    return any(re.fullmatch(provider.hint, models.normalize(lit)) for lit in found)


def _provider_lines(modelsfetch, state: State, provider, key: str, found: set[str],
                    where: dict[str, str], *, now: datetime, deadline, refresh: bool,
                    show_cache: bool, fetch) -> tuple[list[str], list[str]]:
    """`(righe per modello, righe per fornitore)` di un fornitore con la sua chiave."""
    name = provider.name
    try:
        pages, cache_line = modelsfetch.cached_pages(
            state, provider, key, now=now, deadline=deadline, refresh=refresh, fetch=fetch,
            validate=lambda got: models.parse_pages(name, got))
        infos = models.parse_pages(name, pages)
    except modelsfetch.DeadlineSkipped:
        return [], [f"modelli: {name}: saltato, tempo del controllo finito"]
    except modelsfetch.FetchError as e:
        return [], [f"modelli: {name}: elenco non letto: {e}"]
    except models.ModelsFormatError:
        return [], [f"modelli: {name}: elenco non letto: forma inattesa"]
    per_provider = []
    if cache_line is not None and (show_cache or not cache_line.startswith("elenco dalla cache")):
        per_provider.append(f"modelli: {name}: {cache_line}")
    matches = models.used(found, infos)
    lines = models.findings(name, matches, infos, found, where=where, page=provider.page)
    prefix = f"modelli: {name}: "
    own = [l for l in lines if l.startswith(prefix)
           and l[len(prefix):].startswith(_NOT_CHECKED)]
    return [l for l in lines if l not in own], per_provider + own


def _check(state: State, repo: Path, ref: str, cfg: Config, *, environ: Mapping[str, str],
           now: datetime, plugin_root: Path | None, refresh: bool, show_cache: bool, fetch,
           clock) -> list[str]:
    if not cfg.get("components.models_check"):
        return []
    from tollgate_flow import modelsfetch  # rete: solo quando serve, mai al solo import
    files = cfg.get("models.files")
    if not files:
        if "ai" in cfg.profiles:
            return ["modelli: il profilo ai è dichiarato ma [models] files è vuoto: "
                    "la sentinella non sa dove cercare"]
        return []
    providers = modelsfetch.load_providers(PLUGIN_ROOT if plugin_root is None else plugin_root)
    texts, general = _read_files(repo, ref, files)
    found: set[str] = set()
    where: dict[str, str] = {}
    for rel, text in texts.items():
        for lit in models.literals(text):
            found.add(lit)
            where.setdefault(lit, rel)
    keys = {name: modelsfetch.api_key(p, environ) for name, p in providers.items()}
    per_model: list[str] = []
    per_provider: list[str] = []
    if not any(keys.values()):
        general.append("modelli: nessuna chiave nell'ambiente: imposta "
                       + ", ".join(p.env[0] for p in providers.values()))
    elif found:
        deadline = modelsfetch.Deadline(DEADLINE_S, time.monotonic if clock is None else clock)
        for name, provider in providers.items():
            key = keys[name]
            if key is None:
                if _wanted(provider, found):
                    per_provider.append(f"modelli: {name}: non controllato: manca la chiave "
                                        f"({', '.join(provider.env)})")
            else:
                got_model, got_provider = _provider_lines(
                    modelsfetch, state, provider, key, found, where, now=now, deadline=deadline,
                    refresh=refresh, show_cache=show_cache, fetch=fetch)
                per_model += got_model
                per_provider += got_provider
    lines = per_model + per_provider + general
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES] + [f"modelli: … e altri {len(lines) - MAX_LINES} avvisi"]
    return lines


def check(state: State, repo: Path, ref: str, cfg: Config, *, environ: Mapping[str, str],
          now: datetime, plugin_root: Path | None = None, refresh: bool = False,
          show_cache: bool = True, fetch=None, clock=None) -> list[str]:
    """Righe d'avviso (senza il prefisso `avviso: `) sui modelli dichiarati da `[models] files`,
    lette da `ref`. In ordine: per modello, per fornitore, generali; al più `MAX_LINES`. Con
    `show_cache=False` la riga della cache fresca non compare. Non solleva mai: un'eccezione
    inattesa dà la sola riga «controllo non riuscito»."""
    try:
        return _check(state, repo, ref, cfg, environ=environ, now=now, plugin_root=plugin_root,
                      refresh=refresh, show_cache=show_cache, fetch=fetch, clock=clock)
    except Exception as e:
        return [f"modelli: controllo non riuscito ({type(e).__name__})"]
