"""`tollgate task start <k> [--fix]` (spec 6.3): brief dell'implementatore e assegnazione.

Il coordinatore lancia l'implementatore con il nome e il tipo che questo comando ha scritto in
`tasks`; `SubagentStart` associa poi il subagente al task (`tasks.take_pending`)."""
from __future__ import annotations

import json
import shlex
import sqlite3
from pathlib import Path

from tollgate_analysis import brief as briefs, naming, plan as planmod, profiles as prof
from tollgate_core import clock, config, db, git, phases, sessions, tasks

from . import prereq

MAX_FIX_ROUNDS = 5
MODEL_HINT = "inherit"


class TaskError(Exception):
    pass


def _plan_text(wt: Path, work) -> str:
    """Decisione 20: il piano a `plan_sha`. Il blob può non essere negli oggetti di git (lo SHA
    viene da `hash-object` senza scrivere): allora vale il file del worktree, ma solo se ha
    lo stesso SHA."""
    sha, rel = work["plan_sha"], work["plan_path"]
    if not sha or not rel:
        raise TaskError("piano non registrato: manca il piano del lavoro")
    text = git.blob_text(wt, sha)
    if text is None:
        try:
            same = git.blob_sha(wt, rel) == sha
        except git.GitError:
            same = False
        text = git.worktree_text(wt, rel) if same else None
    if text is None:
        raise TaskError(f"piano diverso dalla versione registrata ({rel}): il piano è bloccato "
                        "dopo la registrazione")
    return text


def _check_state(row, number: int, fix: bool) -> None:
    if not fix:
        if row["state"] != "pending":
            raise TaskError(f"task {number} è {row['state']}, non pending: `task start` parte "
                            "solo da pending (per una correzione usa --fix)")
        return
    if row["state"] != "review":
        raise TaskError(f"task {number} è {row['state']}, non in review: --fix serve dopo un "
                        "verdetto del revisore")
    if row["verdict"] != "changes":
        raise TaskError(f"task {number}: serve un verdetto «changes» del revisore "
                        f"(verdetto attuale: {row['verdict'] or 'nessuno'})")
    if row["review_sha"] is None:
        raise TaskError(f"task {number}: il verdetto è di una revisione già superata, serve "
                        "un nuovo verdetto del revisore")


def _related_tests(task, must_haves: list[planmod.MustHave]) -> list[str]:
    out = list(task.test_files)
    out += [t for m in must_haves for t in m.tests if t != "manuale"]
    return list(dict.fromkeys(out))


def task_start(state, cwd: Path, number: int, *, fix: bool, claude_dir: Path,
               now=None) -> tuple[Path, str]:
    now = now or clock.now()
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        raise TaskError(str(e)) from e
    try:
        return _task_start(state, conn, Path(cwd), number, fix=fix, claude_dir=Path(claude_dir),
                           now=now)
    except (sqlite3.Error, tasks.TaskTransitionError, phases.TransitionError,
            git.GitError) as e:
        raise TaskError(str(e)) from e
    finally:
        conn.close()


def _task_start(state, conn, cwd: Path, number: int, *, fix: bool, claude_dir: Path,
                now) -> tuple[Path, str]:
    work = sessions.work_for_path(conn, cwd)
    if work is None:
        raise TaskError("nessun lavoro attivo per questa cartella: lancia il comando dal "
                        "worktree del lavoro")
    if work["level"] == "L0":
        raise TaskError("in L0 lavora la sessione principale: non ci sono task da assegnare")
    if work["phase"] != "execution":
        raise TaskError(f"la fase è {work['phase']}: `task start` si usa in execution")
    try:
        row = tasks.get_task(conn, work["id"], number)
    except ValueError as e:
        raise TaskError(f"task {number} inesistente nel lavoro #{work['issue']}") from e
    _check_state(row, number, fix)
    if fix and row["fix_rounds"] >= MAX_FIX_ROUNDS:
        reason = f"giri di correzione esauriti sul task {number}"
        phases.open_block(conn, state, work["id"], "needs_you", reason, now=now)
        raise TaskError(f"{reason}: serve una decisione dell'utente (aperto un blocco needs_you)")

    wt = Path(work["worktree"])
    main = git.main_worktree(wt)
    base = work["work_base_sha"] or git.default_ref(main)
    try:
        cfg = config.load_config(state, main, base)
    except config.ConfigError as e:
        raise TaskError(f"configurazione non valida: {e}") from e
    plan_text = _plan_text(wt, work)
    check = planmod.check_plan(
        plan_text, required_sections=cfg.get("plan.required_sections"),
        max_scope_files=cfg.get("plan.max_scope_files"),
        must_have_tests=bool(cfg.data["components"].get("must_have_tests", True)),
        level=work["level"], profiles=cfg.profiles, active_always=cfg.get("profiles.active"))
    text = planmod.task_text(plan_text, number)
    task = next((t for t in check.tasks if t.number == number), None)
    if text is None or task is None:
        raise TaskError(f"task {number} non è nel piano {work['plan_path']}")
    refs = task.must_haves
    must_haves = [m for m in check.must_haves if refs is None or m.id in refs]

    routing = prof.task_routing(task.files, cfg.profiles)
    absent = [s for s in routing.skills
              if not prereq.skill_installed(s, claude_dir=claude_dir, worktree=wt)]
    present = [s for s in routing.skills if s not in absent]

    round_ = row["fix_rounds"] + 1 if fix else 0
    renamed = fix and round_ >= naming.RENAMED_FROM_ROUND
    if fix and not renamed:
        name, pending = row["implementer"] or naming.implementer_name(work["issue"], number), \
            "resume"
    else:
        name, pending = naming.implementer_name(work["issue"], number, round_), "launch"
    hint = MODEL_HINT if renamed else None

    impl_brief = briefs.ImplBrief(
        issue=work["issue"], task=number, name=name, agent_type=routing.implementer,
        model_hint=hint, task_text=text, scope=task.files,
        related_tests=_related_tests(task, must_haves), must_haves=must_haves, skills=present,
        absent_skills=absent, verify_cmd=f"{shlex.quote(str(db.BIN_PATH))} verify",
        fix_findings=json.loads(row["review_findings"]) if fix else [], fix_round=round_)
    file_name = f"task-{number}-fix-{round_}.md" if fix else f"task-{number}.md"
    path = wt / ".tollgate-run" / str(work["issue"]) / file_name
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(briefs.implementer_brief(impl_brief), encoding="utf-8")
    except OSError as e:
        raise TaskError(f"scrittura del brief {path} non riuscita: {e}") from e

    tasks.set_skills_required(conn, work["id"], number, present)
    tasks.task_event(conn, work["id"], number, "fix" if fix else "start", now=now)
    tasks.assign(conn, work["id"], number, implementer=name, agent_type=routing.implementer,
                 pending=pending, reviewer_type=routing.reviewer, now=now)
    summary = (f"task {number}: {routing.implementer} name={name}"
               + (f" model: {hint}" if hint else "") + f" {pending}")
    return path, summary
