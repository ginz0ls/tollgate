"""La presa della taglia del lavoro (C1, decisione 2): registra `size_decided` e scrive la colonna.

La regola è in `tollgate_analysis.worksize`; qui si legge la riga del lavoro, si chiama `preview`
e si registra. Un evento a ogni chiamata, anche quando la taglia non cambia: sono i dati per
confrontare in futuro un modello con le regole."""
from __future__ import annotations

from tollgate_analysis import worksize

from . import clock, db, phases
from .events import record_event

CAUSES = ("start", "plan", "level", "approve_spec", "act")


def _write(conn, work: int, row, size: str, by: str, now) -> None:
    if size != row["size"] or by != row["size_by"]:
        conn.execute("UPDATE work_items SET size = ?, size_by = ?, updated = ? WHERE id = ?",
                     (size, by, clock.fmt(now), work))


def decide(conn, work: int, signals: worksize.Signals, *, cause: str, confirmed: bool = False,
           now, session=None) -> str:
    """Propone, applica (mai giù, grande solo con il sì) e registra. Dà la riga per l'utente."""
    if cause not in CAUSES or cause == "act":
        raise ValueError(f"causa della taglia sconosciuta: {cause}")
    with db.tx(conn):
        row = phases.get_work(conn, work)
        proposal = worksize.propose(signals)
        pv = worksize.preview(signals, row["size"], row["size_by"], cause=cause,
                              confirmed=confirmed)
        by = "user" if worksize.holds_user_size(signals, row["size_by"], cause=cause,
                                                confirmed=confirmed) else "rules"
        record_event(conn, "size_decided",
                     {"proposed": proposal.size, "applied": pv.applied, "previous": row["size"],
                      "cause": cause, "by": by, "reason": proposal.reason,
                      "signals": signals._asdict(), "confirmed": True if confirmed else None},
                     now=now, session=session, work=work)
        _write(conn, work, row, pv.applied, by, now)
    return pv.line


def set_by_user(conn, work: int, size: str, reason: str, *, now, session=None) -> str:
    """La taglia fissata dall'utente (atto `approve size`): anche verso il basso."""
    if size not in worksize.SIZES:
        raise ValueError(f"taglia sconosciuta: {size}")
    with db.tx(conn):
        row = phases.get_work(conn, work)
        record_event(conn, "size_decided",
                     {"proposed": size, "applied": size, "previous": row["size"], "cause": "act",
                      "by": "user", "reason": reason, "signals": None, "confirmed": True},
                     now=now, session=session, work=work)
        _write(conn, work, row, size, "user", now)
    return f"taglia: {worksize.LABELS[size]} (scelta dall'utente) — {reason}"
