"""Confronto puro dei modelli AI usati da un progetto con gli elenchi dei fornitori.

Nessuna rete e nessun modulo di tollgate: prende pagine già lette (dizionari JSON) e testo di
file, restituisce righe d'avviso. Le righe vengono da file e da elenchi esterni: ogni testo
variabile passa da `_plain` prima di uscire."""
from __future__ import annotations

import re
from dataclasses import dataclass

PROVIDERS = ("anthropic", "gemini", "openai", "openrouter")

_QUOTED = tuple(re.compile(q + r"([^" + q + r"\n]*)" + q) for q in ('"', "'", "`"))
_LITERAL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/~-]{1,127}")
_PROVIDER_PREFIX = re.compile(r"(?:anthropic|google|openai|openrouter):")
_DATED = re.compile(r"[0-9]{8}")
_CLAUDE_VERSIONED = re.compile(r"claude-(?:[a-z0-9]+-)?[0-9]")
_GEMINI_VERSIONED = re.compile(r"gemini-[0-9]")
_GEMINI_NAME = re.compile(r"gemini-([0-9]+(?:\.[0-9]+)*)-(.+)")
_GEMINI_SUFFIX = re.compile(r"[0-9]{3}|preview|exp|experimental|latest")
_GEMINI_UNSTABLE = frozenset(("preview", "exp", "experimental", "latest"))
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_EPOCH = "1970-01-01"

NOT_LISTED = "non è nell'elenco: ritirato o scritto male"


class ModelsFormatError(ValueError):
    """Una pagina dell'elenco ha una forma diversa da quella attesa."""


@dataclass(frozen=True)
class ModelInfo:
    provider: str
    id: str
    family: str | None
    stable: bool
    created: str | None
    retires: str | None
    retiring: bool


def _plain(text: str) -> str:
    """Testo di un file o di un elenco esterno per l'uscita: i caratteri non stampabili
    diventano `?`."""
    return "".join(c if c.isprintable() else "?" for c in str(text))


def _norm(name: str) -> str:
    """Nome senza `models/` iniziale e senza prefisso `<fornitore>:` (forma di Agno)."""
    name = name.removeprefix("models/")
    m = _PROVIDER_PREFIX.match(name)
    return (name[m.end():] if m else name).removeprefix("models/")


def normalize(name: str) -> str:
    """Nome senza `models/` iniziale e senza prefisso `<fornitore>:`, come lo confrontano
    `used` e `findings`."""
    return _norm(name)


# --- Lettura degli elenchi -------------------------------------------------------------

def gemini_family(model_id: str) -> tuple[str, tuple[int, ...]] | None:
    """`(variante, versione)` di `gemini-<versione>-<variante>[-<suffisso>]`; `None` se il
    nome non ha una versione dopo `gemini-`. Stanno fuori dalla variante i suffissi (un numero
    di tre cifre, `preview`, `exp`, `experimental`, `latest`) e le date numeriche che li
    seguono; le parole dopo un suffisso (la modalità: `tts`, `image`) restano nella variante."""
    m = _GEMINI_NAME.fullmatch(_norm(model_id))
    if not m:
        return None
    variant = []
    after_suffix = False
    for part in m.group(2).split("-"):
        if _GEMINI_SUFFIX.fullmatch(part):
            after_suffix = True
        elif not (after_suffix and part.isdigit()):
            variant.append(part)
    if not variant or "" in variant:
        return None
    return "-".join(variant), tuple(int(n) for n in m.group(1).split("."))


def _gemini_stable(model_id: str) -> bool:
    return not _GEMINI_UNSTABLE & set(_norm(model_id).split("-"))


def _text(value) -> str | None:
    return value if isinstance(value, str) else None


def _items(page, key: str) -> list:
    if not isinstance(page, dict) or not isinstance(page.get(key), list):
        raise ModelsFormatError(f"la pagina non ha la lista «{key}»")
    return page[key]


def _parse_anthropic(item: dict) -> ModelInfo | None:
    mid = item.get("id")
    if not isinstance(mid, str) or not mid:
        return None
    lifecycle = item.get("lifecycle")
    return ModelInfo("anthropic", mid, _text(item.get("line")) or None, lifecycle == "active",
                     _text(item.get("created_at")), _text(item.get("retires_at")),
                     lifecycle == "deprecated")


def _parse_gemini(item: dict) -> ModelInfo | None:
    name = item.get("name")
    if not isinstance(name, str) or not name.removeprefix("models/"):
        return None
    mid = name.removeprefix("models/")
    fam = gemini_family(mid)
    return ModelInfo("gemini", mid, fam[0] if fam else None, _gemini_stable(mid), None, None, False)


def _date_parser(provider: str, field: str):
    def parse(item: dict) -> ModelInfo | None:
        mid = item.get("id")
        if not isinstance(mid, str) or not mid:
            return None
        date = item.get(field)
        date = date if isinstance(date, str) and date else None
        return ModelInfo(provider, mid, None, False, None, date, date is not None)
    return parse


_PARSERS = {
    "anthropic": ("data", _parse_anthropic),
    "gemini": ("models", _parse_gemini),
    "openai": ("data", _date_parser("openai", "shutdown_date")),
    "openrouter": ("data", _date_parser("openrouter", "expiration_date")),
}


def parse_pages(provider: str, pages: list[dict]) -> list[ModelInfo]:
    """Modelli di un fornitore da tutte le sue pagine. Una forma inattesa è
    `ModelsFormatError`; un elemento senza `id`/`name` stringa si salta."""
    if provider not in _PARSERS:
        raise ModelsFormatError("fornitore sconosciuto")
    if not isinstance(pages, list):
        raise ModelsFormatError("le pagine non sono una lista")
    key, parse = _PARSERS[provider]
    out = []
    for page in pages:
        for item in _items(page, key):
            got = parse(item) if isinstance(item, dict) else None
            if got is not None:
                out.append(got)
    return out


# --- Nomi nel testo --------------------------------------------------------------------

def literals(text: str) -> set[str]:
    """Letterali tra `"`, `'` o `` ` `` (sulla stessa riga) che sembrano un ID di modello."""
    found = set()
    for quoted in _QUOTED:
        for m in quoted.finditer(text):
            if _LITERAL.fullmatch(m.group(1)):
                found.add(m.group(1))
    return found


def used(literals: set[str], infos: list[ModelInfo]) -> list[tuple[str, ModelInfo]]:
    """Coppie `(letterale, modello)` per i letterali che coincidono con un ID dell'elenco,
    dopo `_norm` su entrambi. Per Anthropic un letterale `L` con un ID `L-AAAAMMGG` nell'elenco
    vale come il più recente di quegli ID (alias senza data)."""
    by_id = {}
    for info in infos:
        by_id.setdefault(_norm(info.id), info)
    out = []
    for lit in sorted(literals):
        name = _norm(lit)
        hit = by_id.get(name)
        if hit is None:
            dated = [i for n, i in by_id.items() if i.provider == "anthropic"
                     and n.startswith(name + "-") and _DATED.fullmatch(n[len(name) + 1:])]
            hit = max(dated, key=lambda i: _norm(i.id), default=None)
        if hit is not None:
            out.append((lit, hit))
    return out


# --- Righe d'avviso --------------------------------------------------------------------

def _known_date(value: str | None) -> str | None:
    """`created` utile al confronto: assente o all'epoca (data ignota) non lo è."""
    return None if not value or value.startswith(_EPOCH) else value


def _day(value: str | None) -> str:
    if not value:
        return "data non indicata"
    m = _ISO_DATE.match(value)
    return m.group(0) if m else _plain(value)


def _newer_anthropic(info: ModelInfo, infos: list[ModelInfo]) -> ModelInfo | None:
    created = _known_date(info.created)
    if info.family is None or created is None:
        return None
    better = [i for i in infos if i.stable and i.family == info.family
              and _known_date(i.created) is not None and i.created > created]
    return max(better, key=lambda i: (i.created, i.id), default=None)


def _newer_gemini(info: ModelInfo, infos: list[ModelInfo]) -> ModelInfo | None:
    fam = gemini_family(info.id)
    if fam is None or "latest" in _norm(info.id).split("-"):
        return None
    better = [(g[1], i) for i in infos if i.stable and (g := gemini_family(i.id)) is not None
              and g[0] == fam[0] and g[1] > fam[1]]
    return max(better, key=lambda p: (p[0], p[1].id))[1] if better else None


def _model_texts(provider: str, literal: str, info: ModelInfo, infos: list[ModelInfo]) -> list[str]:
    texts = []
    if _norm(literal) != _norm(info.id):
        texts.append(f"alias di {_plain(info.id)}")
    if info.retiring:
        if provider == "anthropic":
            texts.append(f"deprecato, ritiro previsto il {_day(info.retires)}")
        else:
            texts.append(f"ritiro il {_day(info.retires)}")
    newer = {"anthropic": _newer_anthropic, "gemini": _newer_gemini}.get(provider)
    better = newer(info, infos) if newer else None
    if better is not None:
        texts.append(f"esiste {_plain(_norm(better.id))}, più recente della stessa famiglia")
    return texts


def _unlisted(provider: str, name: str) -> bool:
    if provider == "anthropic":
        return _CLAUDE_VERSIONED.match(name) is not None
    if provider == "gemini":
        return _GEMINI_VERSIONED.match(name) is not None
    return False


_NOT_CHECKED = {
    "gemini": "ritiro non controllato: l'elenco non lo dà",
    "openai": "più nuovo non controllato: l'elenco non lo dà",
    "openrouter": "più nuovo non controllato: l'elenco non lo dà, "
                  "guarda la pagina del fornitore originale",
}


def findings(provider: str, matches: list[tuple[str, ModelInfo]], infos: list[ModelInfo],
             literals: set[str], *, where: dict[str, str], page: str) -> list[str]:
    """Righe (senza il prefisso `avviso: `) per un fornitore: prima quelle per modello, poi
    quelle per fornitore. `where` dice in quale file compare ogni letterale."""
    def line(lit: str, text: str) -> str:
        return f"modelli: {provider}: {_plain(lit)} ({_plain(where.get(lit, '?'))}): " \
               f"{text} — {_plain(page)}"

    lines = []
    for lit, info in matches:
        lines += [line(lit, t) for t in _model_texts(provider, lit, info, infos)]
    matched = {lit for lit, _ in matches}
    lines += [line(lit, NOT_LISTED) for lit in sorted(literals - matched)
              if _unlisted(provider, _norm(lit))]
    if matches and provider in _NOT_CHECKED:
        lines.append(f"modelli: {provider}: {_NOT_CHECKED[provider]} — {_plain(page)}")
    return list(dict.fromkeys(lines))
