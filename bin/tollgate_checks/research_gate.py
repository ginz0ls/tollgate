"""Passo «informati prima» (B1): la prima modifica di un task senza nota di ricerca valida.

L0, sessione principale: un avviso per lavoro. L1 e L2, implementatore del task: nessuna decisione
con la nota valida; senza, rifiuto se l'interruttore è acceso (`approved` in `rules-base`),
altrimenti un avviso per task. L'avviso è un `inject` a `pre_*` e si registra (`research_reminder`)
a `post_*`, solo se la modifica è riuscita: un rifiuto di un altro controllo non lo consuma."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import bash, research
from tollgate_core import git, lookups
from tollgate_core.paths import program_command
from tollgate_hooks.model import deny, inject, record

from ._common import (_write_paths, edit_target, governing_work, is_docs_md, output_excludes,
                      work_events)

CHECK = {"api": 1, "events": ["pre_edit", "pre_bash", "post_edit", "post_bash"],
         "component": "research_note", "order": 25}
_PRE = ("pre_edit", "pre_bash")


def _counts(ctx, rel: str) -> bool:
    """La modifica di `rel` conta per il passo (decisione 11): non i `.md` di docs/superpowers/,
    non `.superpowers/`, non le cartelle di output."""
    return not (is_docs_md(rel) or rel.startswith(".superpowers/")
                or git.excluded(rel, output_excludes(ctx)))


def _edit_work(event, ctx):
    p = edit_target(event)
    if p is None:
        return None
    work = governing_work(ctx, p)
    if work is None or not work["worktree"]:
        return None
    rel = ctx.rel(p, Path(work["worktree"]).resolve())
    return work if rel is not None and _counts(ctx, rel) else None


def _bash_work(event, ctx):
    """Il lavoro il cui worktree riceve una scrittura non esclusa di un comando Bash."""
    try:
        cmds = bash.parse(str(event.tool_input.get("command") or ""), str(event.cwd))
    except bash.BashParseError:
        return None
    for c in cmds:
        if not c.argv and not c.redirects or bash.restores_from_index(c):
            continue
        try:
            edir = Path(bash.effective_dir(c)).resolve()
            work = governing_work(ctx, edir)
            if work is None or not work["worktree"]:
                continue
            wt = Path(work["worktree"]).resolve()
            for _, p in _write_paths(c, edir, git.toplevel(edir)):
                rel = ctx.rel(p, wt)
                if rel is not None and _counts(ctx, rel):
                    return work
        except git.GitError:
            continue
    return None


def _reminded(ctx, work, task: int | None) -> bool:
    return any(d.get("task") == task for d in work_events(ctx, work["id"], "research_reminder"))


def _rules_enforced(ctx) -> bool:
    try:
        text = (ctx.plugin_root / research.RULES_BASE).read_text(encoding="utf-8",
                                                                 errors="replace")
    except OSError:
        return False
    return research.enforced(text)


def _problems(ctx, work, task: int) -> list[str]:
    notes = [d for d in work_events(ctx, work["id"], "research_note") if d.get("task") == task]
    last = notes[-1].get("problems") if notes else None
    return [str(x) for x in last] if isinstance(last, list) and not notes[-1].get("ok") else []


def _verdict(event, ctx):
    """`(esito, lavoro, task)`: esito `deny` o `remind`, o None se non c'è niente da dire."""
    is_bash = event.kind in ("pre_bash", "post_bash")
    if is_bash and not event.agent_id:
        return None
    if event.kind in ("post_edit", "post_bash") and event.hook_event == "PostToolUseFailure":
        return None   # la modifica non è riuscita: l'avviso non si consuma
    work = _bash_work(event, ctx) if is_bash else _edit_work(event, ctx)
    if work is None or work["phase"] != "execution" \
            or not research.active(work["research"], ctx.component("research_note")):
        return None
    if work["level"] == "L0":
        if event.agent_id or _reminded(ctx, work, None):
            return None
        return "remind", work, None
    if not event.agent_id or ctx.readonly(event.agent_type):
        return None
    owner = lookups.owner(ctx.db, agent_id=event.agent_id, tool=event.tool_name,
                          work=work["id"], now=ctx.now, stale_minutes=ctx.stale_minutes)
    if owner is None:
        return None
    task = owner[1]
    if lookups.note(ctx.db, work["id"], task)[1]:
        return None
    if _rules_enforced(ctx):
        return "deny", work, task
    return ("remind", work, task) if not _reminded(ctx, work, task) else None


def _refusal(ctx, work, task: int) -> str:
    command = research.submit_command(program_command(ctx.plugin_bin), task)
    text = (f"nota di ricerca mancante o non valida per il task {task}: prima di modificare "
            f"file leggi con Read i file del progetto che il task tocca, apri la "
            f"documentazione di ciò che usi, poi consegna la nota:\n{command}")
    problems = _problems(ctx, work, task)
    if problems:
        text += "\nProblemi della consegna precedente:\n- " + "\n- ".join(problems)
    return text


def _warning(ctx, task: int | None) -> str:
    base = ("tollgate: informati prima di modificare. Leggi i file del progetto che tocchi e, "
            "se usi librerie o servizi esterni, la loro documentazione.")
    if task is None:
        return base
    return (f"{base} Poi consegna la nota di ricerca del task {task}:\n"
            f"{research.submit_command(program_command(ctx.plugin_bin), task)}")


def decide(event, ctx):
    v = _verdict(event, ctx)
    if v is None:
        return []
    outcome, work, task = v
    if outcome == "deny":
        return [deny(_refusal(ctx, work, task), rule="research_gate")] \
            if event.kind in _PRE else []
    if event.kind in _PRE:
        return [inject(_warning(ctx, task))]
    return [record("event", type="research_reminder", data={"task": task}, work=work["id"])]
