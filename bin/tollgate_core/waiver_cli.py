"""tollgate waiver add, tollgate block open (spec 8.3): li usa l'agente, dal worktree."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import waivers

from . import clock, db, git, phases, sessions
from .cli import UsageError
from .events import record_event
from .paths import State


def _work(conn, cwd):
    root = git.toplevel(cwd)
    work = sessions.work_for_path(conn, root or cwd)
    if work is None:
        raise UsageError("nessun lavoro attivo in questa cartella: lancialo dal worktree "
                         "del lavoro")
    return work


def _root_relative(cwd, file: str, worktree: str) -> str:
    """Il file si risolve dalla cartella di lancio (come ogni percorso da riga di comando) e
    si salva relativo alla radice del worktree, con '/' come separatore."""
    root = Path(worktree).resolve()
    try:
        return (Path(cwd) / file).resolve().relative_to(root).as_posix()
    except ValueError as e:
        raise UsageError(f"il file è fuori dal worktree: {file}") from e


def add_waiver(state: State, cwd, *, type_: str, file: str | None = None,
               pattern: str | None = None, tests=(), choice: str, why: str, cost: str,
               now=None) -> str:
    if type_ not in waivers.TYPES:
        raise UsageError(f"tipo di deroga sconosciuto: {type_} (ammessi: "
                         f"{', '.join(waivers.TYPES)})")
    if type_ == "test" and not tests:
        raise UsageError("una deroga di tipo test richiede almeno un --test ID")
    if (file is None) == (pattern is None):
        raise UsageError("indica un file oppure --pattern, non entrambi")
    now = now or clock.now()
    conn = db.open_db(state)
    try:
        work = _work(conn, cwd)
        if file is not None:
            file = _root_relative(cwd, file, work["worktree"])
        path = Path(work["worktree"]) / waivers.path_for(work["issue"])
        if path.exists():
            try:
                wf = waivers.parse(path.read_text(encoding="utf-8"))
            except ValueError as e:
                raise UsageError(f"{path}: {e}") from e
        else:
            wf = waivers.WaiverFile(work["issue"], work["branch"] or "", [])
        wid = waivers.next_id(wf)
        wf.waivers.append(waivers.Waiver(wid, type_, file, pattern, list(tests), choice, why,
                                         cost, "agent"))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(waivers.dumps(wf), encoding="utf-8")
        tmp.replace(path)
        record_event(conn, "waiver_added", {"id": wid, "type": type_}, now=now,
                     work=work["id"])
        return wid
    finally:
        conn.close()


def open_block_cmd(state: State, cwd, *, type_: str, reason: str, now=None) -> int:
    if type_ not in phases.BLOCK_TYPES:
        raise UsageError(f"tipo di blocco sconosciuto: {type_}")
    conn = db.open_db(state)
    try:
        work = _work(conn, cwd)
        return phases.open_block(conn, state, work["id"], type_, reason, now=now or clock.now())
    finally:
        conn.close()
