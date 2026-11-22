"""Registro degli eventi (spec 18.4): sola aggiunta, seq monotono, archivio prima della potatura."""
from __future__ import annotations

import json
import os
import socket
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from . import clock, fsutil, git
from .db import load_json, tx

ENVELOPE_VERSION = 1
ARCHIVE_DIR = "archive"
EVENT_TYPES = frozenset({
    "session_start", "act", "phase_change", "level_change", "scope_registered", "waiver_added",
    "block_opened", "block_closed", "commit", "receipt", "subagent_start", "subagent_stop",
    "veto", "effect_requested", "effect_executed", "review_cycle", "pr_opened", "pr_updated",
    "merge_detected", "sentinel_alert", "spec_audit_round", "act_expired", "task_change",
    "finding", "off", "on", "finish_check", "base_realigned", "plan_reset", "skills_absent",
    "research_note", "research_reminder", "research_switch_unreadable",
    "size_decided", "ruling", "stop_asked", "stop_answered", "cost",
})
_COLUMNS = "seq, v, at, host, session, work, repo_key, issue, type, data"


def record_event(conn: sqlite3.Connection, type_: str, data: dict | None = None, *,
                 now: datetime, session: str | None = None, work: int | None = None,
                 host: str | None = None) -> int:
    if type_ not in EVENT_TYPES:
        raise ValueError(f"tipo di evento sconosciuto: {type_}")
    with tx(conn):
        repo_key = issue = None
        if work is not None:
            row = conn.execute("SELECT repo_key, issue FROM work_items WHERE id = ?",
                               (work,)).fetchone()
            if row is None:
                raise ValueError(f"lavoro {work} inesistente")
            repo_key, issue = row[0], row[1]
        cur = conn.execute(
            "INSERT INTO events (v, at, host, session, work, repo_key, issue, type, data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ENVELOPE_VERSION, clock.fmt(now), host or socket.gethostname(), session, work,
             repo_key, issue, type_, json.dumps(data or {}, ensure_ascii=False, sort_keys=True)))
        return cur.lastrowid


def known_commits(conn: sqlite3.Connection, work: int) -> set[str]:
    return {load_json(r[0], "events.data", dict).get("sha") for r in conn.execute(
        "SELECT data FROM events WHERE type = 'commit' AND work = ?", (work,))}


def record_commits(conn: sqlite3.Connection, work: int, wt, base: str, *, now,
                   session: str | None = None) -> int:
    """Gli eventi `commit` dei commit di `base..HEAD` non ancora noti (rebase, integrazioni):
    PostToolUse Bash non li tratta come nuovi del lavoro. Dà quanti ne ha registrati."""
    known = known_commits(conn, work)
    new = [s for s in git.rev_list(wt, base, git.head(wt)) if s not in known]
    for sha in new:
        record_event(conn, "commit", {"sha": sha}, now=now, session=session, work=work)
    return len(new)


def _as_dict(row) -> dict:
    d = {k: row[k] for k in ("seq", "v", "at", "host", "session", "work", "repo_key", "issue",
                             "type")}
    d["data"] = load_json(row["data"], "events.data")
    return d


def export_events(conn: sqlite3.Connection, after_seq: int) -> list[dict]:
    rows = conn.execute(f"SELECT {_COLUMNS} FROM events WHERE seq > ? ORDER BY seq",
                        (after_seq,)).fetchall()
    return [_as_dict(r) for r in rows]


def to_jsonl(items: list[dict]) -> str:
    return "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in items)


def _fsync_path(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def archive_and_prune(conn: sqlite3.Connection, state, now: datetime,
                      days: int) -> tuple[int, Path | None]:
    """Scrive in `<stato>/archive/events-<primo seq>-<ultimo seq>.jsonl` gli eventi più vecchi di
    `days` giorni (con `fsync` del file e della cartella), poi cancella solo quelli. Lettura, scrittura e cancellazione stanno in una
    transazione con il lucchetto di scrittura: un secondo processo aspetta e non riarchivia gli
    stessi eventi; se la scrittura fallisce l'errore risale e non si cancella niente.
    Dà (eventi cancellati, file d'archivio), o (0, None) se non c'è niente da archiviare."""
    limit = clock.fmt(now - timedelta(days=days))
    with tx(conn):
        rows = conn.execute(
            f"SELECT {_COLUMNS} FROM events WHERE at < ? ORDER BY seq", (limit,)).fetchall()
        if not rows:
            return 0, None
        first, last = rows[0]["seq"], rows[-1]["seq"]
        directory = state.root / ARCHIVE_DIR
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = directory / f"events-{first}-{last}.jsonl"
        fsutil.write_atomic(path, to_jsonl([_as_dict(r) for r in rows]))
        # Su disco prima del DELETE: dopo un'interruzione di corrente l'archivio non può mancare
        # con la cancellazione già durevole (`write_atomic` degli altri chiamanti non cambia).
        _fsync_path(path)
        _fsync_path(directory)
        deleted = conn.execute("DELETE FROM events WHERE seq <= ? AND at < ?",
                               (last, limit)).rowcount
        return deleted, path
