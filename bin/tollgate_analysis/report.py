"""Report dell'implementatore (spec 18.5), taglio di maxTurns (6.3), token dal transcript."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

STATUSES = ("DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT")
REQUIRED = ("v", "task", "status", "done", "tests", "files", "concerns", "left")
CUT_PREFIX = "NOTE: this agent stopped at its"


@dataclass
class ImplReport:
    status: str
    data: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    unknown_status: bool = False

    @property
    def valid(self) -> bool:
        return not self.missing


def _last_json(text: str) -> dict | None:
    dec = json.JSONDecoder()
    pos = text.rfind("{")
    while pos >= 0:
        try:
            obj, _ = dec.raw_decode(text, pos)
            if isinstance(obj, dict) and "status" in obj:
                return obj
        except json.JSONDecodeError:
            pass
        pos = text.rfind("{", 0, pos)
    return None


def parse_report(text: str | None) -> ImplReport:
    data = _last_json(text or "")
    if data is None:
        return ImplReport("DONE", {}, list(REQUIRED))
    missing = [k for k in REQUIRED if k not in data]
    status = data.get("status")
    unknown = status not in STATUSES
    return ImplReport("DONE" if unknown else status, data, missing, unknown)


def is_turn_cut(tool_response: dict | None) -> bool:
    """Il blocco lo scrive Claude Code, separato dall'output del subagente (P0, E6)."""
    if not isinstance(tool_response, dict):
        return False
    if not isinstance(tool_response.get("harnessNoteCount"), int) \
            or tool_response["harnessNoteCount"] < 1:
        return False
    content = tool_response.get("content")
    if not isinstance(content, list) or not content or not isinstance(content[0], dict):
        return False
    return str(content[0].get("text", "")).startswith(CUT_PREFIX)


def transcript_tokens(path) -> int:
    """Token nuovi del subagente: input + cache_creation + output, una volta per messaggio
    (decisione 20). cache_read resta fuori perché riconta il contesto a ogni turno."""
    seen: dict[str, int] = {}
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return 0
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
            total = sum(int(usage.get(k) or 0) for k in
                        ("input_tokens", "cache_creation_input_tokens", "output_tokens"))
            seen[str(msg.get("id") or f"riga-{n}")] = total
    return sum(seen.values())
