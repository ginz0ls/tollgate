"""`tollgate review prepare` (spec 8.6, 10; decisione 5 di P3b): apre o riprende il ciclo di
revisione finale e scrive i brief del revisore, degli specialisti (L2) e del verificatore.

Lo stadio del ciclo decide cosa serve: `review` i revisori non ancora riportati, `verify` il
verificatore (o la chiusura, se nulla resta da verificare). Un ciclo aperto sullo stesso SHA, o
con lo stesso `patch-id`, si riprende con lo stesso codice (criterio 28)."""
from __future__ import annotations

import json
import secrets
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from tollgate_analysis import brief as briefs, plan as planmod, profiles as prof
from tollgate_core import clock, config, db, git, phases, reviews, scope, sessions
from tollgate_core.paths import program_command

from . import taskcmd

REVIEWER = "tollgate:final-reviewer"
VERIFIER = "tollgate:finding-verifier"


class ReviewError(Exception):
    pass


@dataclass
class Launch:
    agent_type: str
    brief: Path
    model: str | None = None


@dataclass
class PrepareResult:
    lines: list[str] = field(default_factory=list)
    launches: list[Launch] = field(default_factory=list)
    stage: str = "none"


def prepare(state, cwd, *, now=None) -> PrepareResult:
    now = now or clock.now()
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        raise ReviewError(str(e)) from e
    try:
        return _prepare(state, conn, Path(cwd), now)
    except (sqlite3.Error, git.GitError, config.ConfigError, taskcmd.TaskError, OSError) as e:
        raise ReviewError(str(e)) from e
    finally:
        conn.close()


def _next(step: str) -> str:
    return f"prossimo passo: {program_command(db.BIN_PATH)} {step}"


def _done(*lines: str) -> PrepareResult:
    return PrepareResult([*lines, _next("finish open-pr")])


def _launch_line(l: Launch) -> str:
    return (f'agente: {l.agent_type} brief: "{l.brief}"'
            + (f" model: {l.model}" if l.model else ""))


def _area(agent: str) -> str:
    return agent.split(":", 1)[-1].removeprefix("final-")


def _prepare(state, conn, cwd: Path, now) -> PrepareResult:
    work = sessions.work_for_path(conn, cwd)
    if work is None:
        raise ReviewError("nessun lavoro attivo per questa cartella: lancia il comando dal "
                          "worktree del lavoro")
    wt = Path(work["worktree"])
    head = git.head(wt)
    if work["phase"] != "review" or head is None or head != work["finish_sha"]:
        raise ReviewError(f"la revisione finale si prepara in fase review sullo SHA di "
                          f"`finish check` (fase {work['phase']}): rilancia /tollgate:finish")
    if work["level"] == "L0":
        return _done("in L0 non c'è revisione finale")
    main = git.main_worktree(wt)
    base = work["work_base_sha"] or git.default_ref(main)
    cfg = config.load_config(state, main, base)
    if not cfg.get("components").get("final_review", True):
        return _done("revisione finale spenta")
    if work["review_unverified"]:
        return _done("revisione non verificata (approvata dall'utente senza esito)")

    wid = work["id"]
    last = reviews.latest(conn, wid)
    patch = None
    if last is not None:
        patch = git.patch_id(wt, base, head)
        same = last["sha"] == head or (patch is not None and last["patch_id"] == patch)
        if last["stage"] != "closed":
            if same:
                return _resume(state, conn, work, cfg, last, wt, base, head, now)
            reviews.supersede(conn, wid, last["number"], now=now)    # C16
        elif last["outcome"] == "ok" and same:
            return _done(f"revisione già superata (ciclo {last['number']})")
    if reviews.count(conn, wid) >= reviews.MAX_CYCLES:
        raise ReviewError(f"{reviews.MAX_CYCLES} cicli di revisione già fatti: oltre serve "
                          "/tollgate:approve unverified-review")
    return _open(state, conn, work, cfg, wt, base, head, patch, now)


def _profiles(cfg, wt: Path, base: str, head: str) -> list[str]:
    files = [c.path for c in git.changes(wt, base, head=head) if c.status != "D"]
    return prof.active_profiles(files, cfg.profiles, cfg.get("profiles.active"))


def _open(state, conn, work, cfg, wt, base, head, patch, now) -> PrepareResult:
    names = _profiles(cfg, wt, base, head)
    reviewers = [REVIEWER]
    if work["level"] == "L2":
        reviewers += prof.final_specialists(names, cfg.profiles)
    if patch is None:
        patch = git.patch_id(wt, base, head)
    number = reviews.open_cycle(conn, work["id"], sha=head, patch_id=patch,
                                code=secrets.token_hex(4), reviewers=reviewers, now=now)
    return _resume(state, conn, work, cfg, reviews.latest(conn, work["id"]), wt, base, head,
                   now, names=names)


def _launch(cfg, agent: str, path: Path) -> Launch:
    return Launch(agent, path, cfg.get("review.models").get(agent))


def _resume(state, conn, work, cfg, cycle, wt: Path, base, head, now, names=None
            ) -> PrepareResult:
    wid, n = work["id"], cycle["number"]
    run_dir = wt / ".tollgate-run" / str(work["issue"])
    run_dir.mkdir(parents=True, exist_ok=True)
    diff = run_dir / f"final-{n}.diff"
    diff.write_text(taskcmd._diff_text(wt, base, head), encoding="utf-8", errors="replace")
    prog = program_command(db.BIN_PATH)
    result = PrepareResult(stage=cycle["stage"])
    if cycle["stage"] == "review":
        names = names if names is not None else _profiles(cfg, wt, base, head)
        reported = json.loads(cycle["reported"])
        pending = [r for r in json.loads(cycle["reviewers"]) if r not in reported]
        result.lines.append(f"ciclo {n} della revisione finale (stadio review, SHA "
                            f"{cycle['sha'][:7]})")
        for agent in pending:
            path = run_dir / (f"final-{n}.md" if agent == REVIEWER
                              else f"final-{n}-{_area(agent)}.md")
            path.write_text(briefs.final_review_brief(
                _final_brief(conn, work, cfg, cycle, wt, base, head, diff, run_dir, agent,
                             names)), encoding="utf-8")
            result.launches.append(_launch(cfg, agent, path))
        result.lines += [_launch_line(l) for l in result.launches]
        result.lines.append("prossimo passo: lancia i revisori qui sopra (anche in parallelo); "
                            f"quando hanno riportato, rilancia {prog} review prepare")
        return result
    # stadio verify
    rows = reviews.to_verify(conn, wid, n, max_findings=cfg.get("review.max_findings"), now=now)
    if rows:
        path = run_dir / f"verify-{n}.md"
        path.write_text(briefs.verifier_brief(briefs.VerifierBrief(
            issue=work["issue"], cycle=n, sha=cycle["sha"], code=cycle["code"],
            diff_path=str(diff), findings=[dict(r) for r in rows])), encoding="utf-8")
        result.launches.append(_launch(cfg, VERIFIER, path))
        result.lines += [f"ciclo {n} della revisione finale (stadio verify): {len(rows)} "
                         "rilievi da verificare", _launch_line(result.launches[0]),
                         "prossimo passo: lancia il verificatore qui sopra; quando ha "
                         f"riportato, rilancia {prog} review prepare"]
        return result
    outcome = reviews.close_cycle(conn, state, wid, n, now=now)        # M1
    result.stage = "closed"
    result.lines.append(f"ciclo {n} chiuso: {outcome}")
    result.lines.append(_closing_step(outcome))
    return result


def _closing_step(outcome: str) -> str:
    prog = program_command(db.BIN_PATH)
    if outcome == "ok":
        return _next("finish open-pr")
    if outcome == "needs_fix":
        return ("prossimo passo: correggi i rilievi confermati (task di correzione), poi "
                f"{prog} finish check")
    return "prossimo passo: serve una decisione dell'utente (blocco needs_you): /tollgate:resolve"


def _final_brief(conn, work, cfg, cycle, wt, base, head, diff, run_dir, agent, names):
    try:
        plan_text = taskcmd._plan_text(wt, work)
        must_haves = planmod.check_plan(
            plan_text, required_sections=cfg.get("plan.required_sections"),
            max_scope_files=cfg.get("plan.max_scope_files"), must_have_tests=True,
            level=work["level"], profiles=cfg.profiles,
            active_always=cfg.get("profiles.active")).must_haves
    except taskcmd.TaskError:
        must_haves = []
    if agent == REVIEWER:
        mine = names
    else:
        mine = [n for n in names if cfg.profiles[n].get("final_specialist") == agent]
    checklists = [cfg.profiles[n]["checklist"] for n in mine if cfg.profiles[n].get("checklist")]
    return briefs.FinalBrief(
        issue=work["issue"], cycle=cycle["number"], sha=cycle["sha"], code=cycle["code"],
        base=base, head=head, diff_path=str(diff), plan_path=work["plan_path"] or "",
        plan_sha=work["plan_sha"] or "", must_haves=must_haves,
        scope=sorted(scope.paths(conn, work["id"])), checklists=checklists,
        severity=cfg.get("severity"), issue_file=str(run_dir / "issue.md"), role=agent)
