"""Sessioni viste dagli hook, sessione viva e lavoro legato (spec 0, 6.6, 12.4)."""
from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

from . import clock, db
from .paths import State, ensure_dirs

BOUND_DIR = "bound"
_SAFE = re.compile(r"^[A-Za-z0-9_-]+$")


def touch(conn, session: str, *, now) -> None:
    with db.tx(conn):
        conn.execute("INSERT INTO session_seen (session, last_seen) VALUES (?, ?) "
                     "ON CONFLICT(session) DO UPDATE SET last_seen = excluded.last_seen",
                     (session, clock.fmt(now)))


def alive(conn, session: str, *, now, stale_minutes: int) -> bool:
    row = conn.execute("SELECT last_seen FROM session_seen WHERE session = ?",
                       (session,)).fetchone()
    return row is not None and row[0] > clock.fmt(now - timedelta(minutes=stale_minutes))


def bound_work(conn, session: str):
    """Il lavoro attivo a cui la sessione è legata (il più recente, se più d'uno)."""
    for row in conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' "
                            "ORDER BY updated DESC, id DESC"):
        if session in json.loads(row["sessions"]):
            return row
    return None


def work_for_path(conn, path):
    """Il lavoro attivo il cui worktree contiene il percorso (risolto, anche se non esiste)."""
    p = Path(path).resolve()
    for row in conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' "
                            "AND worktree IS NOT NULL ORDER BY id"):
        wt = Path(row["worktree"]).resolve()
        if p == wt or wt in p.parents:
            return row
    return None


def mark_bound(state: State, session: str) -> None:
    """Segnalino per il wrapper (decisione 22): la sessione è legata a un lavoro."""
    if not _SAFE.match(session):
        return
    ensure_dirs(state)
    d = state.root / BOUND_DIR
    d.mkdir(mode=0o700, exist_ok=True)
    (d / session).touch()
