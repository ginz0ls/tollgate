"""La fotografia dei lavori aperti per il gestionale (C1, decisione 8): sola lettura, JSON con
versione, nessun testo libero (motivi dei blocchi, ruling, domande)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from tollgate_analysis.turn import TurnFacts, waiting_on

from . import clock
from .db import load_json

SNAPSHOT_VERSION = 1


def _blocks(conn, work: int) -> list[dict]:
    return [{"kind": "block", "id": r["id"]} for r in conn.execute(
        "SELECT id FROM blocks WHERE work = ? AND closed IS NULL ORDER BY id", (work,))]


def _effects(conn, work: int) -> list[dict]:
    return [{"kind": "effect", "id": load_json(r["data"], "intents.data", dict).get("id")}
            for r in conn.execute("SELECT data FROM intents WHERE work = ? AND action = 'effect' "
                                  "AND state = 'requested' ORDER BY id", (work,))]


def _answered(conn) -> set:
    """I `tool_use_id` con una `stop_answered`, di tutto il DB: la scansione si fa una volta."""
    return {load_json(r["data"], "events.data", dict).get("tool_use_id")
            for r in conn.execute("SELECT data FROM events WHERE type = 'stop_answered'")}


def _questions(conn, work: int, answered: set) -> list[dict]:
    """Una domanda aspetta se non ha una `stop_answered` con lo stesso `tool_use_id`, è l'ultima
    `stop_asked` della sua sessione e dopo di lei il lavoro non ha né un `act` né un
    `session_start` (decisione 4). Gli eventi dei subagenti e degli hook non la chiudono."""
    out = []
    for r in conn.execute("SELECT seq, session, data FROM events "
                          "WHERE type = 'stop_asked' AND work = ? ORDER BY seq", (work,)):
        tool_use_id = load_json(r["data"], "events.data", dict).get("tool_use_id")
        if not tool_use_id or tool_use_id in answered:
            continue
        later_ask = conn.execute("SELECT 1 FROM events WHERE type = 'stop_asked' AND seq > ? "
                                 "AND session IS ? LIMIT 1", (r["seq"], r["session"])).fetchone()
        closed = conn.execute("SELECT 1 FROM events WHERE work = ? AND seq > ? "
                              "AND type IN ('act', 'session_start') LIMIT 1",
                              (work, r["seq"])).fetchone()
        if later_ask is None and closed is None:
            out.append({"kind": "question", "id": tool_use_id})
    return out


def waiting_items(conn: sqlite3.Connection, work: int, answered: set | None = None) -> list[dict]:
    """Le cose che aspettano una scelta dell'utente: blocchi, effetti, domande, in quest'ordine.
    `answered` (le domande già risposte) si calcola una volta per fotografia, se non è dato."""
    return _blocks(conn, work) + _effects(conn, work) + _questions(
        conn, work, _answered(conn) if answered is None else answered)


def _cost(conn, work: int) -> dict:
    """Per ogni agente conta l'ultimo `cost` (è cumulativo, decisione 3)."""
    last: dict = {}
    for r in conn.execute("SELECT data FROM events WHERE type = 'cost' AND work = ? "
                          "ORDER BY seq", (work,)):
        data = load_json(r["data"], "events.data", dict)
        last[data.get("agent")] = data
    by_task: dict[int, int] = {}
    total = 0
    for data in last.values():
        tokens = data.get("tokens") or 0
        total += tokens
        if data.get("task") is not None:
            by_task[data["task"]] = by_task.get(data["task"], 0) + tokens
    return {"tokens": total, "by_task": dict(sorted(by_task.items()))}


def _work(conn, row, answered: set) -> dict:
    work = row["id"]
    waiting = waiting_items(conn, work, answered)
    turn = waiting_on(TurnFacts(row["phase"], waiting))
    last = conn.execute("SELECT max(at) FROM events WHERE work = ?", (work,)).fetchone()[0]
    return {
        "repo_key": row["repo_key"], "issue": row["issue"], "level": row["level"],
        "level_cap": row["level_cap"], "size": row["size"], "size_by": row["size_by"],
        "slices": row["slices"], "phase": row["phase"],
        "phase_before_block": row["phase_before_block"], "branch": row["branch"],
        "pr_number": row["pr_number"],
        "tasks": {r["state"]: r["n"] for r in conn.execute(
            "SELECT state, count(*) AS n FROM tasks WHERE work = ? GROUP BY state "
            "ORDER BY state", (work,))},
        "turn": turn, "waiting_user": len(waiting) + (1 if turn == "user" else 0),
        "waiting": waiting, "cost": _cost(conn, work),
        "created": row["created"], "updated": row["updated"], "last_event_at": last,
    }


def build(conn: sqlite3.Connection, *, now: datetime, host: str) -> dict:
    rows = conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' ORDER BY id")
    answered = _answered(conn)
    return {"v": SNAPSHOT_VERSION, "at": clock.fmt(now), "host": host,
            "works": [_work(conn, r, answered) for r in rows.fetchall()]}


def dumps(snap: dict) -> str:
    return json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True)
