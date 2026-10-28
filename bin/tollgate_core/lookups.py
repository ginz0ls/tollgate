"""Letture registrate per task e nota di ricerca (B1, passo «informati prima»).

Le letture appartengono al task, non al singolo implementatore (decisione 5): un implementatore
nuovo eredita quelle dei giri precedenti. La nota sta in `tasks.research_note`, con l'esito in
`tasks.research_ok`."""
from __future__ import annotations

from datetime import timedelta
from typing import NamedTuple

from . import clock, db

KINDS = ("read", "grep", "bash_read", "fetch", "search", "docs")


class Lookup(NamedTuple):
    kind: str
    target: str


def record(conn, *, work: int, task: int | None, agent_id: str | None, session: str | None,
           kind: str, target: str, now) -> None:
    """Una lettura; la stessa terna (lavoro, task, tipo, bersaglio) non si registra due volte."""
    if kind not in KINDS:
        raise ValueError(f"tipo di lettura sconosciuto: {kind}")
    if not target:
        raise ValueError("bersaglio della lettura vuoto")
    with db.tx(conn):
        # `IS` e non `=`: con task NULL il confronto con `=` non è mai vero.
        if conn.execute("SELECT 1 FROM lookups WHERE work = ? AND task IS ? AND kind = ? "
                        "AND target = ?", (work, task, kind, target)).fetchone():
            return
        conn.execute("INSERT INTO lookups (work, task, agent_id, session, kind, target, at) "
                     "VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (work, task, agent_id, session, kind, target, clock.fmt(now)))


def for_task(conn, work: int, task: int) -> list[Lookup]:
    """Le letture del task in ordine di registrazione, senza doppioni."""
    rows = conn.execute("SELECT kind, target FROM lookups WHERE work = ? AND task = ? "
                        "ORDER BY id", (work, task)).fetchall()
    return list(dict.fromkeys(Lookup(r[0], r[1]) for r in rows))


def detach_tasks(conn, work: int) -> None:
    """Dopo `reopen plan` i task si rinumerano: le letture del lavoro non valgono più per un
    numero (decisione 14)."""
    with db.tx(conn):
        conn.execute("UPDATE lookups SET task = NULL WHERE work = ? AND task IS NOT NULL",
                     (work,))


def set_note(conn, work: int, task: int, *, text: str, ok: bool) -> None:
    with db.tx(conn):
        conn.execute("UPDATE tasks SET research_note = ?, research_ok = ? "
                     "WHERE work = ? AND number = ?", (text, int(ok), work, task))


def note(conn, work: int, task: int) -> tuple[str | None, bool]:
    row = conn.execute("SELECT research_note, research_ok FROM tasks WHERE work = ? "
                       "AND number = ?", (work, task)).fetchone()
    if row is None:
        return None, False
    return row[0], bool(row[1])


def prune(conn, *, now, days: int) -> int:
    """Cancella le letture dei lavori chiusi da più di `days` giorni. Non esiste un'ora di
    chiusura: vale l'ultimo aggiornamento del lavoro chiuso."""
    limit = clock.fmt(now - timedelta(days=days))
    with db.tx(conn):
        return conn.execute(
            "DELETE FROM lookups WHERE work IN "
            "(SELECT id FROM work_items WHERE phase = 'closed' AND updated < ?)",
            (limit,)).rowcount
