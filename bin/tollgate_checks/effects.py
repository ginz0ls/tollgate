"""Effetti esterni (spec 8.5): veto con identificativo, una esecuzione per atto."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from tollgate_analysis import bash
from tollgate_core import acts, effects, git
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["pre_bash", "pre_mcp"], "component": None, "order": 30}


def _intent(ctx, event, command: str, reason: str, repo: Path | None, where: Path):
    """Un effetto riconosciuto: (messaggio di veto o None, decisioni se l'atto lo permette)."""
    work = governing_work(ctx, where)
    work_id = work["id"] if work is not None else None
    sha = git.head(repo) if repo else None
    key = effects.effect_key(command, work_id, sha)
    eid = effects.effect_id(key)
    row = effects.get(ctx.db, key)
    prev = effects.executed_at(row)
    act = acts.find_usable(ctx.db, type_="approve", object_="effect", target=eid, work=work_id,
                           session=event.session, now=ctx.now)
    request = record("effect_request", key=key, command=command, work=work_id, sha=sha)
    if act is None:
        msg = (f"effetto esterno ({reason}): {command[:200]}. Per eseguirlo una volta l'utente "
               f"digita /tollgate:approve effect {eid}")
        if prev:
            msg += f". Attenzione: già eseguito alle {prev} su questo SHA"
        return key, msg, [request]
    warn = f" (attenzione: già eseguito alle {prev} su questo SHA)" if prev else ""
    allowed = ([] if row is not None else [request])
    allowed += [record("effect_execute", key=key, act_id=act["act_id"], work=work_id),
                inject(f"tollgate: effetto {eid} permesso una volta dall'atto "
                       f"{act['act_id']}{warn}")]
    return key, None, allowed


def _verdict(intents):
    """Un solo veto per tutta la riga: se un effetto non ha l'atto, nessun atto si consuma
    (la riga non gira). Lo stesso effetto ripetuto nella riga ne consuma uno per volta."""
    seen, out, denied = set(), [], None
    for key, msg, decisions in intents:
        if key in seen and msg is None:
            msg = ("la riga ripete lo stesso effetto: un atto vale una esecuzione, lancia i "
                   "comandi separatamente")
            decisions = []
        seen.add(key)
        if msg is not None and denied is None:
            denied = msg
        out.append((msg, decisions))
    if denied is not None:
        return [deny(denied, rule="effects")] + [d for msg, ds in out if msg is not None
                                                  for d in ds]
    return [d for _, ds in out for d in ds]


def _script_reason(ctx, c: bash.Cmd) -> str | None:
    """Script dentro un repo che non è tracciato nella base (8.5, anche se ignorato da git)."""
    sp = bash.script_path(c)
    if not sp:
        return None
    p = Path(sp)
    repo = git.toplevel(p)
    if repo is None:
        return None
    work = governing_work(ctx, p)
    ref = work["work_base_sha"] if work is not None and work["work_base_sha"] \
        else git.default_ref(repo)
    rel = ctx.rel(p, repo)
    if ref and rel and not git.exists_at(repo, ref, rel):
        return "script nel repo non tracciato nella base"
    return None


def decide(event, ctx):
    if event.kind == "pre_mcp":
        name = event.tool_name or ""
        if any(fnmatch.fnmatchcase(name, pat) for pat in ctx.cfg("external_effects.mcp_allow")):
            return []
        command = f"{name} {json.dumps(event.tool_input, sort_keys=True, ensure_ascii=False)}"
        return _verdict([_intent(ctx, event, command, "strumento MCP non in mcp_allow",
                                 ctx.repo, event.cwd)])
    try:
        cmds = bash.parse(str(event.tool_input.get("command") or ""), str(event.cwd))
    except bash.BashParseError:
        return []
    ee = ctx.cfg("external_effects")
    cfg = bash.EffectsCfg(ee["commands"], ee["project_scripts"], ee["allow"])
    intents = []
    for c in cmds:
        if bash.uses_tollgate_bin(c, str(ctx.plugin_bin)):
            continue
        edir = Path(bash.effective_dir(c))
        reason = bash.effect_reason(c, cfg) or _script_reason(ctx, c)
        if reason:
            repo = git.toplevel(edir) if edir.exists() else None
            intents.append(_intent(ctx, event, bash.normalized(c), reason, repo, edir))
    return _verdict(intents)
