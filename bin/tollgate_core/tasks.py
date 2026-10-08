"""Task del piano e transizioni di tasks.state (spec 6.3)."""
from __future__ import annotations

import json
import sqlite3

from . import db
from .events import record_event

STATES = ("pending", "running", "review", "done", "blocked")
KINDS = ("plan", "fix")
_TRANSITIONS = {
    ("pending", "start"): "running",
    ("running", "report_done"): "review",
    ("running", "report_blocked"): "blocked",
    ("running", "needs_context"): "running",
    ("running", "budget_exceeded"): "blocked",
    ("running", "interrupted"): "pending",
    ("review", "fix"): "running",
    ("review", "approved"): "done",
    ("blocked", "unblocked"): "pending",
}
TASK_EVENTS = tuple(sorted({e for _, e in _TRANSITIONS}))
_VERDICT = {"fix": "changes", "approved": "approved"}


class TaskTransitionError(Exception):
    pass


def get_task(conn, work: int, number: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM tasks WHERE work = ? AND number = ?",
                       (work, number)).fetchone()
    if row is None:
        raise ValueError(f"task {number} del lavoro {work} inesistente")
    return row


def next_number(conn, work: int) -> int:
    return conn.execute("SELECT coalesce(max(number), 0) + 1 FROM tasks WHERE work = ?",
                        (work,)).fetchone()[0]


def _log(conn, row, *, now, session) -> None:
    record_event(conn, "task_change",
                 {"number": row["number"], "kind": row["kind"], "state": row["state"],
                  "fix_rounds": row["fix_rounds"], "verdict": row["verdict"]},
                 now=now, session=session, work=row["work"])


def add_task(conn, work: int, number: int, *, source: str, kind: str = "plan",
             skills_required: list[str] | None = None, now, session=None) -> None:
    if kind not in KINDS:
        raise ValueError(f"tipo di task sconosciuto: {kind}")
    with db.tx(conn):
        try:
            conn.execute("INSERT INTO tasks (work, number, kind, source, state, skills_required) "
                         "VALUES (?, ?, ?, ?, 'pending', ?)",
                         (work, number, kind, source, json.dumps(skills_required or [])))
        except sqlite3.IntegrityError as e:
            raise ValueError(f"task {number} già presente nel lavoro {work}") from e
        _log(conn, get_task(conn, work, number), now=now, session=session)


def task_event(conn, work: int, number: int, event: str, *, now, session=None) -> str:
    if event not in TASK_EVENTS:
        raise ValueError(f"evento di task sconosciuto: {event}")
    with db.tx(conn):
        row = get_task(conn, work, number)
        new = _TRANSITIONS.get((row["state"], event))
        if new is None:
            raise TaskTransitionError(f"task {number}: {event} non ammesso da {row['state']}")
        fix_rounds = row["fix_rounds"] + (1 if event == "fix" else 0)
        verdict = _VERDICT.get(event, row["verdict"])
        conn.execute("UPDATE tasks SET state = ?, fix_rounds = ?, verdict = ? "
                     "WHERE work = ? AND number = ?", (new, fix_rounds, verdict, work, number))
        _log(conn, get_task(conn, work, number), now=now, session=session)
    return new


def add_skill_used(conn, work: int, number: int, skill: str) -> None:
    with db.tx(conn):
        used = json.loads(get_task(conn, work, number)["skills_used"])
        if skill not in used:
            used.append(skill)
            conn.execute("UPDATE tasks SET skills_used = ? WHERE work = ? AND number = ?",
                         (json.dumps(used), work, number))
