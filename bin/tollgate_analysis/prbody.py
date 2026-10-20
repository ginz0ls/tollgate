"""Corpo della PR (spec 6.4, decisione 10 di P3b).

Ogni testo che non scrive tollgate (rilievi dei revisori, deroghe, esiti dei comandi) entra solo
tramite `neutralize`: recinto più lungo di ogni sequenza di backtick, menzioni spente, nessun
commento HTML, lunghezza massima. Il blocco JSON di 18.1 sta per ultimo."""
from __future__ import annotations

from . import brief, prblock

MAX_TEXT = 2000
TRUNCATED = "… (troncato)"
ZWSP = "\u200b"


def _cap(text, max_len: int = MAX_TEXT) -> str:
    text = str(text)
    return text[:max_len].rstrip() + TRUNCATED if len(text) > max_len else text


def neutralize(text: str, max_len: int = MAX_TEXT) -> str:
    text = _cap(text, max_len)
    text = (text.replace("@", "@" + ZWSP).replace("<!--", "<!" + ZWSP + "--")
            .replace("-->", "--" + ZWSP + ">"))
    fence = brief.fence(text)
    return f"{fence}\n{text}\n{fence}"


def _section(title: str, lines: list[str]) -> list[str]:
    """Il tetto vale per ogni voce, non per la sezione: una voce lunga non nasconde le altre."""
    joined = "\n".join(_cap(x) for x in lines)
    return [f"## {title}", neutralize(joined, len(joined)), ""]


def _note(n: dict) -> str:
    file, line = n.get("file") or "(file non indicato)", n.get("line")
    where = f"{file}:{line}" if line is not None else file
    return f"[{n.get('severity') or '?'}] {where} ({n.get('rule') or 'senza regola'}): {n.get('text')}"


def _unverified(n: dict) -> str:
    why = n.get("verification_reason")
    return _note(n) + (f" [non verificato: {why}]" if why else " [non verificato]")


def render(*, issue: int, level: str, dod_lines: list[str], notes: list[dict],
           waivers: list[str], warnings: list[str], block: dict,
           unverified: list[dict] = ()) -> str:
    out = [f"Closes #{int(issue)}", "", f"Livello: {level}", ""]
    out += _section("Definition of Done", dod_lines)
    if notes:
        out += _section("Note della revisione (non bloccanti)", [_note(n) for n in notes])
    if unverified:
        out += _section("Rilievi non verificati", [_unverified(n) for n in unverified])
    if waivers:
        out += _section("Deroghe", waivers)
    if warnings:
        out += _section("Avvisi", warnings)
    out.append(prblock.render(block))
    return "\n".join(out) + "\n"
