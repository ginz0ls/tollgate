"""Letture dei subagenti (B1, «informati prima»): cosa ha letto l'implementatore di un task.

Una lettura appartiene al task (decisione 5) e si registra con `record("lookup", …)`. Nel
percorso vero degli hook `post_lookup` non passa di qui (la via breve del runner usa la stessa
`lookups.observed`); questo modulo serve `post_bash`, i file che un comando mostra."""
from __future__ import annotations

from tollgate_core import lookups
from tollgate_hooks.model import record

from ._common import lookup_owner

CHECK = {"api": 1, "events": ["post_lookup", "post_bash"], "component": "research_note",
         "order": 40}


def decide(event, ctx):
    if event.kind == "post_bash" and event.hook_event == "PostToolUseFailure":
        return []   # un comando fallito non ha mostrato niente
    work = lookups.tracked_work(ctx.db, agent_id=event.agent_id, cwd=event.cwd)
    if work is None:
        return []
    owner = lookup_owner(ctx, event, work)
    if owner is None:
        return []
    wt, cwd = str(work["worktree"]), str(event.cwd)
    if event.kind == "post_bash":
        found = lookups.observed_bash(str(event.tool_input.get("command") or ""), cwd=cwd,
                                      worktree=wt)
    else:
        found = lookups.observed(event.tool_name or "", event.tool_input, event.tool_response,
                                 cwd=cwd, worktree=wt)
    return [record("lookup", work=owner[0], task=owner[1], agent_id=event.agent_id, kind=k,
                   target=t) for k, t in found]
