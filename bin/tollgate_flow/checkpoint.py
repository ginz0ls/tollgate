"""`tollgate status --checkpoint` (spec 6.3, 12.4): punto di ripresa nel worktree.

Il file `docs/superpowers/reviews/<N>/checkpoint.md` è ignorato da git (info/exclude): non sporca
il worktree. `SessionStart` ne inietta le ultime righe, perciò il prossimo passo è l'ultima."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from tollgate_core import clock, db, reviews, sessions
from tollgate_core.paths import program_command
from tollgate_core.tasks import STATES

from . import gitw

# Prefisso del motivo del blocco -> nome del tetto.
CAPS = {"budget superato": "budget del task", "giri di correzione esauriti": "giri di correzione",
        reviews.CAP_REASON: "cicli di revisione"}
MAX_NOTES = 5
EXCLUDE = "docs/superpowers/reviews/*/checkpoint.md"
NOTES_HEADER = "## Note"
NEXT_PREFIX = "prossimo passo:"


class CheckpointError(Exception):
    pass


def stopped_by(conn, work: int) -> list[str]:
    out = []
    for b in conn.execute("SELECT id, reason FROM blocks WHERE work = ? AND closed IS NULL "
                          "ORDER BY id", (work,)):
        for prefix, name in CAPS.items():
            if b["reason"].startswith(prefix):
                out.append(f"tetto: {name} (blocco {b['id']})")
                break
    return out


def next_step(conn, work: int) -> str:
    row = conn.execute("SELECT * FROM tasks WHERE work = ? AND state <> 'done' "
                       "ORDER BY number LIMIT 1", (work,)).fetchone()
    if row is None:
        phase = conn.execute("SELECT phase FROM work_items WHERE id = ?", (work,)).fetchone()[0]
        if phase == "plan":
            return ("scrivi il piano con superpowers:writing-plans (intestazioni di 7.5), "
                    "committalo, poi /tollgate:execute")
        if phase in ("spec_audit", "approval"):
            return f"fase {phase}: percorso L2, arriva con P3c"
        return "/tollgate:finish"
    k, state = row["number"], row["state"]
    prog = program_command(db.BIN_PATH)
    if state == "pending":
        return f"task {k} pending: {prog} task start {k}"
    if state == "running":
        who = row["implementer"] or "del task"
        return f"task {k} running: attendi o riprendi l'implementatore {who}"
    if state == "blocked":
        return f"task {k} blocked: /tollgate:resolve"
    if row["verdict"] == "approved":
        return f"task {k} in review, approvato: {prog} task done {k}"
    if row["verdict"] == "changes" and row["review_sha"] is not None:
        return f"task {k} in review, da correggere: {prog} task start {k} --fix"
    return f"task {k} in review: {prog} task review-prepare {k}"


def _previous_notes(path: Path) -> list[list[str]]:
    """Le note già scritte: una voce inizia con «- », le righe che seguono sono rientrate."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    notes: list[list[str]] = []
    inside = False
    for ln in lines:
        if ln == NOTES_HEADER:
            inside = True
        elif inside and ln.startswith("- "):
            notes.append([ln])
        elif inside and ln.startswith("  ") and notes:
            notes[-1].append(ln)
        elif inside:
            break
    return notes


def _note_lines(note: str, now) -> list[str]:
    parts = [p.rstrip() for p in note.strip().splitlines()] or [""]
    return [f"- {clock.fmt(now)} {parts[0]}"] + [f"  {p}" for p in parts[1:]]


def write_checkpoint(state, cwd, *, note: str | None, now=None) -> Path:
    now = now or clock.now()
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        raise CheckpointError(str(e)) from e
    try:
        work = sessions.work_for_path(conn, cwd)
        if work is None:
            raise CheckpointError("nessun lavoro attivo per questa cartella: lancia il comando "
                                  "dal worktree del lavoro")
        counts = {r["state"]: r["n"] for r in conn.execute(
            "SELECT state, count(*) AS n FROM tasks WHERE work = ? GROUP BY state",
            (work["id"],))}
        stops, step = stopped_by(conn, work["id"]), next_step(conn, work["id"])
    except sqlite3.Error as e:
        raise CheckpointError(str(e)) from e
    finally:
        conn.close()

    wt = Path(work["worktree"])
    path = wt / "docs" / "superpowers" / "reviews" / str(work["issue"]) / "checkpoint.md"
    notes = _previous_notes(path)
    if note and note.strip():
        notes.append(_note_lines(note, now))
    notes = notes[-MAX_NOTES:]

    plan = (f"{work['plan_path']} (plan_sha {work['plan_sha']})" if work["plan_path"]
            else "nessuno")
    tasks_line = ", ".join(f"{counts[s]} {s}" for s in STATES if s in counts) or "nessuno"
    lines = [f"# Checkpoint #{work['issue']}", f"fase: {work['phase']}, livello {work['level']}",
             f"piano: {plan}", f"task: {tasks_line}", *stops, NOTES_HEADER,
             *[ln for n in notes for ln in n], f"{NEXT_PREFIX} {step}"]
    try:
        gitw.add_excludes(wt, [EXCLUDE])
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except (OSError, gitw.GitWriteError) as e:
        raise CheckpointError(f"scrittura del checkpoint non riuscita: {e}") from e
    return path
