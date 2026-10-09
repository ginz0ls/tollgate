"""SessionStart (spec 7.2): legame, subagenti di sessioni morte, stato e checkpoint."""
from __future__ import annotations

from pathlib import Path

from tollgate_core import sessions, subagents
from tollgate_hooks.model import inject, record

from ._common import orphan_tg, status_lines

CHECK = {"api": 1, "events": ["session_start"], "component": None, "order": 10}


def decide(event, ctx):
    out = [record("expire_acts")]
    for row in subagents.running(ctx.db):
        if row["session"] and row["session"] != event.session and not sessions.alive(
                ctx.db, row["session"], now=ctx.now, stale_minutes=ctx.stale_minutes):
            out.append(record("subagent_interrupt", agent_id=row["id"]))
    work = ctx.work
    if work is not None and not ctx.bound:
        out.append(record("bind", work=work["id"]))
    if work is None:
        n = orphan_tg(ctx, ctx.repo)
        if n is not None:
            out.append(inject(f"tollgate: ramo tg/{n}-* senza lavoro nel DB (DB perso?). Le "
                              f"scritture sono negate finché l'utente non lancia "
                              f"/tollgate:adopt #{n}."))
        return out
    lines = status_lines(ctx, work)
    if work["worktree"]:
        cp = Path(work["worktree"]) / f"docs/superpowers/reviews/{work['issue']}/checkpoint.md"
        try:
            lines += ["checkpoint:"] + cp.read_text(encoding="utf-8").strip().splitlines()
        except OSError:
            pass
    out.append(inject("\n".join(lines)))
    return out
