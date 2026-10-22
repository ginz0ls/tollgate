"""Il commento del gate sulla PR (spec 9.2, criterio 27).

Riporta lo SHA giudicato nel marcatore della prima riga: la CLI lo legge (`fixtask.GATE_MARKER`)
e lega il task di correzione a quello SHA. Le voci «da leggere» stanno in cima, le informative in
un blocco richiudibile. Il testo che non scrive tollgate (`Item.data`, elenco `watch`, `errors`)
passa solo da `prbody.neutralize`; tutto il commento sta entro `MAX_BODY`."""
from __future__ import annotations

import re

from tollgate_analysis import prbody
from tollgate_analysis.prbody import MAX_BODY

from . import attention
from .model import Evaluation, Item

MARKER_PREFIX = "<!-- tollgate-verdict"     # uguale a fixtask.GATE_MARKER (lo controlla un test)
GUARD_PREFIX = "<!-- tollgate-guard"
_SHA = re.compile(r"[0-9a-f]{40}")
_MARKER = re.compile(re.escape(MARKER_PREFIX) + r" ([0-9a-f]{40}) -->")
_CAPS = (prbody.MAX_TEXT, 1000, 500, 250, 120, 60, 30)


def _check_sha(sha: str) -> str:
    if not _SHA.fullmatch(sha):
        raise ValueError(f"SHA non valido: {sha!r}")
    return sha


def marker(sha: str) -> str:
    return f"{MARKER_PREFIX} {_check_sha(sha)} -->"


def marker_sha(body: str) -> str | None:
    """Lo SHA nel marcatore in testa al commento, `None` se manca o non è di 40 esadecimali."""
    m = _MARKER.match(body.lstrip())
    return m.group(1) if m else None


def _item(item: Item, cap: int) -> list[str]:
    out = [f"- {prbody.defuse(item.text)}"]
    if item.data:
        out += ["", prbody.neutralize(item.data, cap), ""]
    return out


def _lines(items: list[str], cap: int) -> list[str]:
    """Un solo recinto per un elenco di stringhe: il tetto vale per ogni voce."""
    joined = "\n".join(prbody._cap(x, cap) for x in items)
    return ["", prbody.neutralize(joined, len(joined)), ""]


def _build(sha: str, ev: Evaluation, cap: int, keep: int | None) -> str:
    def limited(items: list) -> tuple[list, list[str]]:
        if keep is None or len(items) <= keep:
            return items, []
        return items[:keep], [f"… (troncato: altre {len(items) - keep} voci omesse)", ""]

    out = [marker(sha), "", f"## tollgate: verdetto sullo SHA `{sha}`", ""]
    if ev.errors:
        out += ["**Errore nel calcolo del gate**", ""]
        shown, note = limited(ev.errors)
        out += _lines(shown, cap) + note
    if ev.red:
        out += ["### Da correggere", ""]
        shown, note = limited(ev.red)
        for it in shown:
            out += _item(it, cap)
        out += note
    read = [i for i in ev.attention if attention.group(i.key) == attention.READ]
    info = [i for i in ev.attention if attention.group(i.key) == attention.INFO]
    if read:
        out += ["### Da leggere", ""]
        shown, note = limited(read)
        for it in shown:
            out += _item(it, cap)
        out += note
    if info:
        out += ["<details>", f"<summary>Informative ({len(info)})</summary>", ""]
        shown, note = limited(info)
        for it in shown:
            out += _item(it, cap)
        out += note + ["</details>", ""]
    if ev.watch:
        out += ["### File da tenere d'occhio", ""]
        shown, note = limited(ev.watch)
        out += _lines(shown, cap) + note
    if not (ev.errors or ev.red or read or info or ev.watch):
        out += ["Nessuna voce.", ""]
    return "\n".join(out).rstrip() + "\n"


def render(sha: str, ev: Evaluation) -> str:
    """Il commento del gate per lo SHA `sha`. Sta entro `MAX_BODY`: prima si accorciano le voci,
    poi si tolgono dalla coda con una nota."""
    _check_sha(sha)
    for cap in _CAPS:
        body = _build(sha, ev, cap, None)
        if len(body) <= MAX_BODY:
            return body
    keep = max(len(ev.errors), len(ev.red), len(ev.attention), len(ev.watch))
    while keep > 1:
        keep //= 2
        body = _build(sha, ev, _CAPS[-1], keep)
        if len(body) <= MAX_BODY:
            return body
    return body


def render_guard(sha: str, problems: list[str]) -> str:
    """Il commento di `tollgate-guard` quando lo stato resta in attesa: spiega i problemi."""
    out = [f"{GUARD_PREFIX} {_check_sha(sha)} -->", "",
           f"## tollgate: in attesa sullo SHA `{sha}`", ""]
    if problems:
        out += _lines(problems[:50], prbody.MAX_TEXT)
        if len(problems) > 50:
            out += [f"… (troncato: altri {len(problems) - 50} problemi omessi)", ""]
    return "\n".join(out).rstrip() + "\n"
