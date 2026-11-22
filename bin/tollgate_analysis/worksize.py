"""La taglia del lavoro (C1, decisione 2): piccolo, medio, grande.

Funzioni pure: `propose` guarda i segnali e propone, `preview` applica la regola «mai giù, grande
solo con `approve spec <n>`, la taglia dell'utente resta» e compone la riga per l'utente. Chi
registra (`tollgate_core.sizes`) e chi inietta la riga (il controllo del piano) chiamano la stessa
`preview`, così le due cose coincidono per costruzione."""
from __future__ import annotations

from typing import NamedTuple

from . import profiles as prof

SIZES = ("small", "medium", "large")
LABELS = {"small": "piccolo", "medium": "medio", "large": "grande"}
MEDIUM_MIN_TASKS = 4
MEDIUM_MIN_AREAS = 2


class Signals(NamedTuple):
    level: str
    tasks: int
    areas: int
    slices: int


class Proposal(NamedTuple):
    size: str
    reason: str


class Preview(NamedTuple):
    applied: str
    line: str


def _areas_text(n: int) -> str:
    return f"{n} area" if n == 1 else f"{n} aree"


def _plan_text(s: Signals) -> str:
    text = f"piano con {s.tasks} task"
    return f"{text} su {_areas_text(s.areas)}" if s.areas else text


def propose(signals: Signals) -> Proposal:
    """Le regole, nell'ordine: più fette → grande; L2, 4 task o 2 aree → medio; altrimenti piccolo
    (decisione 2)."""
    s = signals
    if s.slices > 1:
        return Proposal("large", f"{s.slices} fette previste")
    plan_big = s.tasks >= MEDIUM_MIN_TASKS or s.areas >= MEDIUM_MIN_AREAS
    if s.level == "L2" or plan_big:
        parts = ["livello L2"] if s.level == "L2" else []
        if plan_big or s.tasks:
            parts.append(_plan_text(s))
        return Proposal("medium", ", ".join(parts))
    return Proposal("small", _plan_text(s) if s.tasks else "ancora nessun piano")


def areas(paths, profiles: dict[str, dict]) -> int:
    """I profili verticali distinti dei file: un file del generico non conta."""
    return len({v for v in (prof.vertical_for(p, profiles) for p in paths) if v})


def _rank(size: str | None) -> int:
    return SIZES.index(size) if size in SIZES else -1


def _is_yes(proposal: Proposal, cause: str, confirmed: bool) -> bool:
    """Il sì dell'utente alle fette: `approve spec <n>` con `n > 1`."""
    return proposal.size == "large" and cause == "approve_spec" and confirmed


def holds_user_size(signals: Signals, current_by: str | None, *, cause: str,
                    confirmed: bool = False) -> bool:
    """La taglia dell'utente resta, tranne davanti al sì alle fette (un altro sì dell'utente)."""
    return current_by == "user" and not _is_yes(propose(signals), cause, confirmed)


def preview(signals: Signals, current: str | None, current_by: str | None, *, cause: str,
            confirmed: bool = False) -> Preview:
    proposal = propose(signals)
    yes = _is_yes(proposal, cause, confirmed)
    held = holds_user_size(signals, current_by, cause=cause, confirmed=confirmed)
    target = proposal.size if proposal.size != "large" or yes else "medium"
    applied = current if held or _rank(current) >= _rank(target) else target
    label = LABELS[applied]
    if held:
        line = (f"taglia: {label} (scelta dall'utente) — le regole proporrebbero "
                f"{LABELS[proposal.size]}: {proposal.reason}")
    elif proposal.size == "large" and applied != "large" and signals.level != "L2":
        line = (f"taglia proposta: grande ({proposal.reason}) — le fette diventano issue solo da "
                "una spec approvata: per averle, apri un'issue nuova per il lavoro a fette e "
                "avviala con /tollgate:start #<nuova> L2 (spec e /tollgate:approve spec <n>); "
                "questo lavoro resta medio e le fette restano un documento")
    else:
        line = f"taglia: {label} — {proposal.reason}"
    return Preview(applied, line)
