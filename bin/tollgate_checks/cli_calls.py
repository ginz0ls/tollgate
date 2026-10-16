"""PreToolUse Bash: chiamate al programma `tollgate` (decisioni 2 e 22).

La CLI gira dentro Bash e non riceve il session_id: per `start` e `act`, i soli sottocomandi
che leggono la sessione, il controllo lascia un segnale (operazione `cli_call`). Un subagente
non può lanciare i comandi del coordinatore."""
from __future__ import annotations

import os

from tollgate_analysis import bash
from tollgate_hooks.model import deny, record

CHECK = {"api": 1, "events": ["pre_bash"], "component": None, "order": 5}
_SIGNALLED = ("start", "act")
_COORDINATOR_ONLY = ("start", "task", "act")


def _program_args(c: bash.Cmd, plugin_bin: str) -> list[str] | None:
    """Gli argomenti dopo il programma (`tollgate x` o `python3 <bin/tollgate> x`), oppure None."""
    a = c.argv
    if not a:
        return None
    is_python = os.path.basename(a[0]).startswith("python")
    if is_python and len(a) > 1 and (bash.uses_tollgate_bin(c, plugin_bin)
                                     or os.path.basename(a[1]) == "tollgate"):
        return a[2:]
    if bash.uses_tollgate_bin(c, plugin_bin) or os.path.basename(a[0]) == "tollgate":
        return a[1:]
    return None


def _subcommand(args: list[str]) -> str | None:
    return next((x for x in args if not x.startswith("-")), None)


def decide(event, ctx):
    raw = str(event.tool_input.get("command") or "")
    try:
        cmds = bash.parse(raw, str(event.cwd))
    except bash.BashParseError:
        return []
    out = []
    for c in cmds:
        args = _program_args(c, str(ctx.plugin_bin))
        if args is None:
            continue
        sub = _subcommand(args)
        if event.agent_id:
            if sub in _COORDINATOR_ONLY or (sub == "status" and "--checkpoint" in args):
                return [deny(f"tollgate {sub} è un comando del coordinatore: un subagente non "
                             "lo lancia. Riporta al coordinatore (BLOCKED o NEEDS_CONTEXT).",
                             rule="coordinator_only")]
            continue
        if sub in _SIGNALLED:
            out.append(record("cli_call", cwd=bash.effective_dir(c), argv=args[args.index(sub):]))
    return out
