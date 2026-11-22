"""Report dell'implementatore (spec 18.5), taglio di maxTurns (6.3), token dal transcript."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

STATUSES = ("DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT")
REQUIRED = ("v", "task", "status", "done", "tests", "files", "concerns", "left")
CUT_PREFIX = "NOTE: this agent stopped at its"


@dataclass
class ImplReport:
    """`status` è lo stato normalizzato (maiuscolo, senza spazi). Uno stato fuori da
    STATUSES rende il report non valido (fail-closed, spec 18.5)."""
    status: str
    data: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    unknown_status: bool = False

    @property
    def valid(self) -> bool:
        return not self.missing and not self.unknown_status


MAX_SCAN_CHARS = 65536
MAX_DECODES = 500


def json_candidates(text: str, key: str) -> list[dict]:
    """Oggetti JSON con la chiave `key`, dal fondo del testo verso l'inizio. Esamina solo la coda
    di MAX_SCAN_CHARS caratteri e al più MAX_DECODES aperture di `{` (decisione 23)."""
    dec = json.JSONDecoder()
    out: list[dict] = []
    lo = max(0, len(text) - MAX_SCAN_CHARS)
    pos = text.rfind("{", lo)
    decodes = 0
    while pos >= lo and decodes < MAX_DECODES:
        decodes += 1
        try:
            obj, _ = dec.raw_decode(text, pos)
            if isinstance(obj, dict) and key in obj:
                out.append(obj)
        except json.JSONDecodeError:
            pass
        pos = text.rfind("{", lo, pos)
    return out


def _last_json(text: str) -> dict | None:
    """Preferisce l'oggetto che contiene tutti i campi REQUIRED; altrimenti l'ultimo."""
    cands = json_candidates(text, "status")
    for c in cands:
        if all(k in c for k in REQUIRED):
            return c
    return cands[0] if cands else None


def parse_report(text: str | None) -> ImplReport:
    data = _last_json(text or "")
    if data is None:
        return ImplReport("DONE", {}, list(REQUIRED))
    missing = [k for k in REQUIRED if k not in data]
    raw = data.get("status")
    status = raw.strip().upper() if isinstance(raw, str) else str(raw)
    return ImplReport(status, data, missing, status not in STATUSES)


def is_turn_cut(tool_response: dict | None) -> bool:
    """Il blocco lo scrive Claude Code, separato dall'output del subagente (P0, E6)."""
    if not isinstance(tool_response, dict):
        return False
    count = tool_response.get("harnessNoteCount")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        return False
    content = tool_response.get("content")
    if not isinstance(content, list) or not content or not isinstance(content[0], dict):
        return False
    return str(content[0].get("text", "")).startswith(CUT_PREFIX)


def _count(v) -> int:
    """Solo gli interi veri contano: stringhe, liste, float (anche 1e999) e bool si saltano."""
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


_USAGE_KEYS = (("input", "input_tokens"), ("cache_creation", "cache_creation_input_tokens"),
               ("cache_read", "cache_read_input_tokens"), ("output", "output_tokens"))


def _messages(path) -> dict[str, tuple[str, dict[str, int]]]:
    """Per ogni messaggio della trascrizione (un id una volta, vale l'ultima riga): modello e uso.
    Lettura tollerante: file assente o illeggibile, righe non JSON e usi malformati si saltano."""
    seen: dict[str, tuple[str, dict[str, int]]] = {}
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return seen
    with fh:
        for n, line in enumerate(fh):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = row.get("message") if isinstance(row, dict) else None
            usage = msg.get("usage") if isinstance(msg, dict) else None
            if not isinstance(usage, dict):
                continue
            model = msg.get("model")
            seen[str(msg.get("id") or f"riga-{n}")] = (
                model if isinstance(model, str) and model else "sconosciuto",
                {name: _count(usage.get(key)) for name, key in _USAGE_KEYS})
    return seen


def new_tokens(usage: dict[str, int]) -> int:
    """Token nuovi di un uso: input + cache_creation + output (`cache_read` resta fuori)."""
    return usage["input"] + usage["cache_creation"] + usage["output"]


def transcript_usage(path) -> dict[str, dict[str, int]]:
    """Uso del subagente per modello (decisione 3 di C1): `input`, `cache_creation`, `cache_read`,
    `output`, un messaggio una volta (come `transcript_tokens`); modello assente: `sconosciuto`.
    `{}` senza file o senza nessuna riga di uso."""
    out: dict[str, dict[str, int]] = {}
    for model, use in _messages(path).values():
        total = out.setdefault(model, dict.fromkeys((n for n, _ in _USAGE_KEYS), 0))
        for name, v in use.items():
            total[name] += v
    return out


def transcript_tokens(path) -> int:
    """Token nuovi del subagente: input + cache_creation + output, una volta per messaggio
    (decisione 20). cache_read resta fuori perché riconta il contesto a ogni turno."""
    return sum(new_tokens(u) for _, u in _messages(path).values())
