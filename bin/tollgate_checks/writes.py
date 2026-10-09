"""PreToolUse Edit/Write/NotebookEdit/MultiEdit (spec 7.2, 6.6, 12.4)."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis.protected import is_protected
from tollgate_analysis.testguard import Violation
from tollgate_analysis.waivers import unresolved
from tollgate_core import git
from tollgate_hooks.model import deny

from ._common import (_inside, edit_target, explain, governing_work, is_docs_md, locked_docs,
                      orphan_tg, scope_exempt)

CHECK = {"api": 1, "events": ["pre_edit"], "component": None, "order": 20}
_DOCS_ONLY = ("spec_audit", "plan", "approval", "blocked", "review", "pr_open")
_NO_PLANS = ("spec_audit", "approval")


def _in_main_checkout(p: Path, wt: Path) -> bool:
    """Nel checkout principale, ma non in un altro worktree che sta dentro di esso."""
    try:
        trees = [t for t, _ in git.worktrees(wt)]
    except git.GitError:
        return False
    return _inside(p, trees[0]) and not any(_inside(p, t) for t in trees[1:])


def decide(event, ctx):
    p = edit_target(event)
    if p is None:
        return []
    repo = git.toplevel(p)
    rel = ctx.rel(p, repo) if repo else None
    if is_protected(rel, p, abs_roots=ctx.protected_roots(repo)):
        return [deny(f"{p} è un file protetto: lo scrivono solo la CLI e gli hook di tollgate "
                     f"(7.4)", rule="protected")]
    work = governing_work(ctx, p)
    if work is None:
        n = orphan_tg(ctx, repo)
        if n is not None and not is_docs_md(rel):
            return [deny(f"ramo tg/{n}-* senza lavoro nel DB: scritture negate tranne i .md "
                         f"sotto docs/superpowers/. L'utente deve lanciare /tollgate:adopt #{n} "
                         f"(12.4)", rule="adopt")]
        return []
    if not work["worktree"]:
        return []
    wt = Path(work["worktree"]).resolve()
    rel_w = ctx.rel(p, wt)
    if rel_w is None:
        if _in_main_checkout(p, wt):
            return [deny(f"scrittura nel checkout principale negata durante il lavoro "
                         f"#{work['issue']}: si lavora nel worktree {wt} (6.6)",
                         rule="main_checkout")]
        return []
    if rel_w in locked_docs(work):
        return [deny(f"{rel_w} è approvato e bloccato: per cambiarlo serve "
                     f"/tollgate:reopen spec|plan <motivo> (6.2)", rule="locked")]
    docs_ok = is_docs_md(rel_w) or rel_w.startswith(".superpowers/")
    phase = work["phase_before_block"] if work["phase"] == "blocked" else work["phase"]
    if work["phase"] in _DOCS_ONLY:
        if phase in _NO_PLANS and rel_w.startswith("docs/superpowers/plans/"):
            return [deny(f"in fase {phase} non si scrivono piani: prima l'audit e "
                         f"/tollgate:approve spec (6.2)", rule="phase")]
        if docs_ok:
            return []
        hint = (" Per correggere il codice dopo finish: /tollgate:start."
                if phase in ("review", "pr_open") else "")
        return [deny(f"in fase {work['phase']} si scrivono solo i .md sotto "
                     f"docs/superpowers/.{hint}", rule="phase")]
    if docs_ok or work["level"] == "L0":
        return []
    if event.agent_id is None:
        return [deny(f"in {work['level']} il codice lo scrivono gli implementatori: usa "
                     f"/tollgate:execute (6.3)", rule="coordinator")]
    if ctx.component("scope_check"):
        scope = ctx.scope(work)
        if rel_w not in scope and not scope_exempt(ctx, work, rel_w, scope):
            v = Violation("out_of_scope", rel_w, "file fuori dallo scope del piano", "scope")
            left = unresolved([v], ctx.waiver_file(work))
            if left:
                return [deny("file fuori scope:\n" + explain(left, work["issue"]), rule="scope")]
    return []
