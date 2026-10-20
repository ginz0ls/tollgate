"""Operazioni `record` dei controlli (decisione 6): ognuna scrive con tollgate_core."""
from __future__ import annotations

import getpass

from pathlib import Path

from tollgate_analysis import profiles as prof
from tollgate_core import (acts, effects, events, git, phases, reviews, scope, sessions,
                           subagents, tasks)


def _actor() -> str | None:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return None


def _bind(conn, state, ctx, d):
    phases.bind_session(conn, d["work"], ctx.event.session, now=ctx.now)
    sessions.mark_bound(state, ctx.event.session)


def _act(conn, state, ctx, d):
    acts.record_act(conn, type_=d["type"], object_=d.get("object"), target=d.get("target"),
                    args=d.get("args"), typed_text=d.get("typed_text", ""), actor=_actor(),
                    session=ctx.event.session, work=d.get("work"), head_sha=d.get("head_sha"),
                    now=ctx.now, ttl_minutes=ctx.cfg("acts.ttl_minutes"))


def _subagent_start(conn, state, ctx, d):
    task = d.get("task")
    if d.get("take_pending") and d.get("work") is not None:
        # Una ripresa sa già di quale task è: cerca solo quello (più task dello stesso tipo).
        resume = bool(d.get("resume"))
        task = tasks.take_pending(conn, d["work"], agent_type=d["type"], resume=resume,
                                  number=task if resume else None) or task
    subagents.start(conn, agent_id=d["agent_id"], type_=d["type"], session=ctx.event.session,
                    work=d.get("work"), task=task, base_sha=d.get("base_sha"),
                    fingerprint=d.get("fingerprint"), now=ctx.now,
                    refresh_fingerprint=bool(d.get("refresh_fingerprint")))


def _commit(conn, state, ctx, d):
    events.record_event(conn, "commit", {"sha": d["sha"]}, now=ctx.now,
                        session=ctx.event.session, work=d["work"])
    acts.invalidate_finish(conn, d["work"], d.get("head") or d["sha"], now=ctx.now,
                           session=ctx.event.session)


def _invalidate_finish(conn, state, ctx, d):
    acts.invalidate_finish(conn, d["work"], d["head"], now=ctx.now, session=ctx.event.session)


def _effect_execute(conn, state, ctx, d):
    act = acts.find_usable(conn, type_="approve", object_="effect",
                           target=effects.effect_id(d["key"]), work=d.get("work"),
                           session=ctx.event.session, now=ctx.now)
    if act is None:
        raise acts.ActError("atto approve effect non più valido")
    acts.consume(conn, act["act_id"], type_="approve", object_="effect",
                 target=effects.effect_id(d["key"]), now=ctx.now, work=d.get("work"),
                 session=ctx.event.session)
    effects.mark_executed(conn, key=d["key"], act_id=act["act_id"], now=ctx.now,
                          session=ctx.event.session)


def _final_rules(ctx, work, sha: str) -> tuple[set[str], set[str]]:
    """Regole `[blocca]` e note dei profili attivi sul diff del ciclo (decisione 8). Se il diff
    non si legge, nessun profilo è attivo: ogni `R-…` blocca (fail-closed)."""
    wt = Path(work["worktree"]) if work["worktree"] else None
    base = work["work_base_sha"]
    files: list[str] = []
    if wt is not None and wt.is_dir() and base:
        try:
            files = [c.path for c in git.changes(wt, base, head=sha) if c.status != "D"]
        except git.GitError:
            files = []
    profs = ctx.config.profiles
    names = prof.active_profiles(files, profs, ctx.cfg("profiles.active"))
    return prof.blocking_rules(names, profs), prof.known_rules(names, profs)


def _review_report(conn, state, ctx, d):
    """Riporto di un revisore finale. Un riporto non più accettabile (ciclo non in stadio
    review, fonte non attesa o già riportata: una corsa) è ignorato, mai un'eccezione."""
    wid, n = d["work"], d["cycle"]
    work = phases.get_work(conn, wid)
    cycle = conn.execute("SELECT sha FROM review_cycles WHERE work = ? AND number = ?",
                         (wid, n)).fetchone()
    if cycle is None:
        return
    blocking, known = _final_rules(ctx, work, cycle["sha"])
    try:
        stage = reviews.add_report(conn, wid, n, source=d["source"], outcome=d["outcome"],
                                   findings=d["findings"], rejected=d["rejected"],
                                   blocking_rules=blocking, known_rules=known, now=ctx.now)
    except ValueError:
        return
    if stage == "verify" and not reviews.unjudged_ids(conn, wid, n):
        reviews.close_cycle(conn, state, wid, n, now=ctx.now, session=ctx.event.session)


def _finding_verify(conn, state, ctx, d):
    """Esiti del verificatore. A zero rilievi senza esito chiude il ciclo; altrimenti conta il
    riporto incompleto (dal secondo, `needs_you`)."""
    wid, n = d["work"], d["cycle"]
    cycle = conn.execute("SELECT stage FROM review_cycles WHERE work = ? AND number = ?",
                         (wid, n)).fetchone()
    if cycle is None or cycle["stage"] != "verify":
        return
    left = reviews.apply_verification(conn, wid, n, d["results"], now=ctx.now)
    if left == 0:
        reviews.close_cycle(conn, state, wid, n, now=ctx.now, session=ctx.event.session)
    else:
        reviews.verifier_incomplete(conn, state, wid, n, now=ctx.now, session=ctx.event.session)


_OPS = {
    "event": lambda c, s, x, d: events.record_event(c, d["type"], d.get("data"), now=x.now,
                                                    session=x.event.session, work=d.get("work")),
    "bind": _bind,
    "cli_call": lambda c, s, x, d: sessions.note_cli_call(s, x.event.session, d["cwd"],
                                                          d["argv"], now=x.now),
    "act": _act,
    "expire_acts": lambda c, s, x, d: acts.expire_stale(c, now=x.now, session=x.event.session),
    "block": lambda c, s, x, d: phases.open_block(c, s, d["work"], d["type"], d["reason"],
                                                  now=x.now, session=x.event.session),
    "level": lambda c, s, x, d: phases.set_level(c, d["work"], d["level"], now=x.now,
                                                 session=x.event.session),
    "phase": lambda c, s, x, d: phases.set_phase(c, s, d["work"], d["to"], d["cause"],
                                                 now=x.now, session=x.event.session),
    "plan": lambda c, s, x, d: scope.register_plan(
        c, s, d["work"], plan_path=d["plan_path"], plan_sha=d["plan_sha"],
        scope_paths=d["scope"], plan_tasks=[tuple(t) for t in d["tasks"]],
        advance=d["advance"], now=x.now, session=x.event.session),
    "plan_path": lambda c, s, x, d: scope.set_plan_path(c, d["work"], d["plan_path"], now=x.now),
    "subagent_start": _subagent_start,
    "subagent_name": lambda c, s, x, d: subagents.set_name(c, d["agent_id"], d["name"],
                                                           session=x.event.session,
                                                           work=d.get("work"), now=x.now),
    "subagent_report": lambda c, s, x, d: subagents.set_report(c, d["agent_id"], d["text"]),
    "subagent_veto": lambda c, s, x, d: subagents.add_veto(c, d["agent_id"]),
    "subagent_finish": lambda c, s, x, d: subagents.finish(
        c, d["agent_id"], state=d["state"], declared_status=d.get("declared_status"),
        tokens=d.get("tokens"), now=x.now, session=x.event.session),
    "subagent_interrupt": lambda c, s, x, d: subagents.interrupt(c, d["agent_id"], now=x.now,
                                                                 session=x.event.session),
    "task": lambda c, s, x, d: tasks.task_event(c, d["work"], d["number"], d["event"],
                                                now=x.now, session=x.event.session),
    "task_reserve": lambda c, s, x, d: tasks.reserve(c, d["work"], d["number"], now=x.now),
    "task_verdict": lambda c, s, x, d: tasks.set_verdict(
        c, d["work"], d["number"], outcome=d["outcome"], findings=d["findings"], now=x.now,
        session=x.event.session, dropped=d.get("dropped", 0)),
    "task_commit": lambda c, s, x, d: tasks.add_commit(c, d["work"], d["number"], d["sha"]),
    "skill_used": lambda c, s, x, d: tasks.add_skill_used(c, d["work"], d["number"], d["skill"]),
    "commit": _commit,
    "invalidate_finish": _invalidate_finish,
    "effect_request": lambda c, s, x, d: effects.request(
        c, key=d["key"], command=d["command"], work=d.get("work"), sha=d.get("sha"), now=x.now,
        session=x.event.session),
    "effect_execute": _effect_execute,
    "review_report": _review_report,
    "finding_verify": _finding_verify,
}
OPS = frozenset(_OPS)


def apply(conn, state, ctx, decision) -> None:
    fn = _OPS.get(decision.op)
    if fn is None:
        raise ValueError(f"operazione record sconosciuta: {decision.op}")
    fn(conn, state, ctx, decision.data)
