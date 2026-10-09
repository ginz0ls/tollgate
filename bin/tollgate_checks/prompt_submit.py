"""UserPromptSubmit (spec 6.3, 7.2): taglio di maxTurns in background e alla ripresa.

Non c'è SubagentStop: il taglio arriva come `<task-notification>` nel prompt (P2 E7, E8)."""
from __future__ import annotations

import re

from ._common import budget_cut_records

CHECK = {"api": 1, "events": ["prompt_submit"], "component": "task_budget", "order": 20}

_CUT = re.compile(r"stopped at its \d+-turn limit")
_TASK_ID = re.compile(r"<task-id>\s*([^<\s]+)\s*</task-id>")
_TOKENS = re.compile(r"<subagent_tokens>\s*(\d+)\s*</subagent_tokens>")


def decide(event, ctx):
    prompt = event.raw.get("prompt")
    if not isinstance(prompt, str) or "<task-notification>" not in prompt \
            or not _CUT.search(prompt):
        return []
    agent = _TASK_ID.search(prompt)
    if agent is None:
        return []
    tokens = _TOKENS.search(prompt)
    return budget_cut_records(ctx, agent.group(1), int(tokens.group(1)) if tokens else None)
