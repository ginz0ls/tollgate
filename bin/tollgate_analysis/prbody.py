"""Corpo della PR (spec 6.4, decisione 10 di P3b).

Ogni testo che non scrive tollgate (rilievi dei revisori, deroghe, esiti dei comandi) entra solo
tramite `neutralize`: recinto più lungo di ogni sequenza di backtick, menzioni spente, nessun
commento HTML, lunghezza massima. Il blocco JSON di 18.1 sta per ultimo."""
from __future__ import annotations

from . import brief, prblock

MAX_TEXT = 2000
TRUNCATED = "… (troncato)"
ZWSP = "​"


def neutralize(text: str, max_len: int = MAX_TEXT) -> str:
    text = str(text)
    if len(text) > max_len:
        text = text[:max_len].rstrip() + TRUNCATED
    text = (text.replace("@", "@" + ZWSP).replace("<!--", "<!" + ZWSP + "--")
            .replace("-->", "--" + ZWSP + ">"))
    fence = brief.fence(text)
    return f"{fence}\n{text}\n{fence}"


def _section(title: str, lines: list[str]) -> list[str]:
    return [f"## {title}", neutralize("\n".join(lines)), ""]


def _note(n: dict) -> str:
    where = f"{n.get('file')}:{n.get('line')}" if n.get("line") is not None else n.get("file")
    return f"[{n.get('severity')}] {where} ({n.get('rule')}): {n.get('text')}"


def render(*, issue: int, level: str, dod_lines: list[str], notes: list[dict],
           waivers: list[str], warnings: list[str], block: dict) -> str:
    out = [f"Closes #{int(issue)}", "", f"Livello: {level}", ""]
    out += _section("Definition of Done", dod_lines)
    if notes:
        out += _section("Note della revisione (non bloccanti)", [_note(n) for n in notes])
    if waivers:
        out += _section("Deroghe", waivers)
    if warnings:
        out += _section("Avvisi", warnings)
    out.append(prblock.render(block))
    return "\n".join(out) + "\n"
