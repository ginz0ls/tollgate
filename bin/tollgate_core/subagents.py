"""Righe di `subagents` (spec 6.3, 7.2, 12.2): partenza, ripresa, nome, chiusura."""
from __future__ import annotations

from datetime import timedelta

from . import clock, db, tasks
from .events import record_event

STATES = ("running", "done", "cut", "budget", "interrupted", "tampered")


def get(conn, agent_id: str):
    return conn.execute("SELECT * FROM subagents WHERE id = ?", (agent_id,)).fetchone()


def start(conn, *, agent_id: str, type_: str, session: str, work: int | None,
          task: int | None, base_sha: str | None, fingerprint: str | None, now) -> bool:
    """Registra la partenza; alla ripresa (stessa riga) non tocca agent_base_sha né l'impronta."""
    ts = clock.fmt(now)
    with db.tx(conn):
        row = get(conn, agent_id)
        resumed = row is not None and row["started"] is not None
        if row is None:
            conn.execute("INSERT INTO subagents (id, type, work, task, session, agent_base_sha, "
                         "fingerprint, started, last_seen, state) "
                         "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running')",
                         (agent_id, type_, work, task, session, base_sha, fingerprint, ts, ts))
        elif not resumed:
            conn.execute("UPDATE subagents SET type = ?, work = coalesce(work, ?), task = ?, "
                         "session = ?, agent_base_sha = ?, fingerprint = ?, started = ?, "
                         "last_seen = ?, state = 'running' WHERE id = ?",
                         (type_, work, task, session, base_sha, fingerprint, ts, ts, agent_id))
        else:
            conn.execute("UPDATE subagents SET resumes = resumes + 1, state = 'running', "
                         "ended = NULL, last_seen = ?, task = coalesce(task, ?) WHERE id = ?",
                         (ts, task, agent_id))
        record_event(conn, "subagent_start", {"id": agent_id, "type": type_, "task": task,
                                              "resumed": resumed},
                     now=now, session=session, work=work)
    return resumed


def touch(conn, agent_id: str, *, now) -> None:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET last_seen = ? WHERE id = ?",
                     (clock.fmt(now), agent_id))


def set_name(conn, agent_id: str, name: str, *, session: str, work: int | None, now) -> None:
    """Il nome arriva da PostToolUse Agent, che in background può precedere SubagentStart."""
    with db.tx(conn):
        if get(conn, agent_id) is None:
            conn.execute("INSERT INTO subagents (id, name, work, session, last_seen) "
                         "VALUES (?, ?, ?, ?, ?)",
                         (agent_id, name, work, session, clock.fmt(now)))
        else:
            conn.execute("UPDATE subagents SET name = ? WHERE id = ?", (name, agent_id))


def set_report(conn, agent_id: str, text: str) -> None:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET report = ? WHERE id = ?", (text, agent_id))


def add_veto(conn, agent_id: str) -> int:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET vetoes = vetoes + 1 WHERE id = ?", (agent_id,))
        row = get(conn, agent_id)
        return row["vetoes"] if row else 0


def finish(conn, agent_id: str, *, state: str, now, declared_status: str | None = None,
           tokens: int | None = None, session: str | None = None) -> None:
    if state not in STATES or state == "running":
        raise ValueError(f"stato di chiusura non ammesso: {state}")
    with db.tx(conn):
        row = get(conn, agent_id)
        if row is None:
            raise ValueError(f"subagente {agent_id} sconosciuto")
        started = clock.parse(row["started"]) if row["started"] else now
        conn.execute("UPDATE subagents SET ended = ?, state = ?, declared_status = ?, "
                     "tokens = coalesce(?, tokens), duration = ? WHERE id = ?",
                     (clock.fmt(now), state, declared_status, tokens,
                      (now - started).total_seconds(), agent_id))
        record_event(conn, "subagent_stop",
                     {"id": agent_id, "type": row["type"], "task": row["task"],
                      "declared_status": declared_status, "tokens": tokens, "state": state},
                     now=now, session=session or row["session"], work=row["work"])


def by_name(conn, name: str, *, work: int | None):
    return conn.execute("SELECT * FROM subagents WHERE name = ? AND work IS ? "
                        "ORDER BY coalesce(started, last_seen) DESC LIMIT 1",
                        (name, work)).fetchone()


def running(conn, *, work: int | None = None) -> list:
    sql, params = "SELECT * FROM subagents WHERE state = 'running'", []
    if work is not None:
        sql += " AND work = ?"
        params.append(work)
    return conn.execute(sql + " ORDER BY started", params).fetchall()


def is_stale(row, *, now, stale_minutes: int) -> bool:
    seen = row["last_seen"] or row["started"]
    return seen is not None and seen <= clock.fmt(now - timedelta(minutes=stale_minutes))


def interrupt(conn, agent_id: str, *, now, session: str | None = None) -> None:
    """Un implementatore interrotto riporta il suo task a pending senza consumare un giro."""
    with db.tx(conn):
        row = get(conn, agent_id)
        if row is None or row["state"] != "running":
            return
        conn.execute("UPDATE subagents SET state = 'interrupted', ended = ? WHERE id = ?",
                     (clock.fmt(now), agent_id))
        if row["work"] is not None and row["task"] is not None:
            t = conn.execute("SELECT state FROM tasks WHERE work = ? AND number = ?",
                             (row["work"], row["task"])).fetchone()
            if t is not None and t["state"] == "running":
                tasks.task_event(conn, row["work"], row["task"], "interrupted", now=now,
                                 session=session)
        record_event(conn, "subagent_stop", {"id": agent_id, "type": row["type"],
                                             "task": row["task"], "declared_status": None,
                                             "tokens": None, "state": "interrupted"},
                     now=now, session=session or row["session"], work=row["work"])
