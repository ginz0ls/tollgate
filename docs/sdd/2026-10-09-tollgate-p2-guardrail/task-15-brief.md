### Task 15: Controlli su Edit e Write: fasi, scope, coordinatore, file protetti, livello, `plan-check`

**Files:**
- Modify: `bin/tollgate_checks/_common.py` (aggiunge `level_records`, `scope_exempt`)
- Create: `bin/tollgate_checks/writes.py`
- Create: `bin/tollgate_checks/post_edit.py`
- Test: `tests/test_check_writes.py`, `tests/test_check_post_edit.py`

**Interfaces:**
- Consumes: `adapter.edit_path`, `protected.is_protected`, `plan.check_plan`, `level.*`, `profiles.*`, `waivers.unresolved`, `testguard.Violation`, `git.*`, `_common.*`.
- Produces in `_common.py`: `level_records(ctx, work) -> list[Decision]` (ricalcolo del livello sul diff dalla base, decisione 18; L0 che cresce → `phase` con `l0_grew`); `scope_exempt(ctx, work, rel, scope) -> bool` (esenzioni di 7.4: `.md` sotto `docs/superpowers/` non protetti né bloccati, `.superpowers/`, `[scope] always`, lockfile con il manifest nello scope).
- Modulo `writes` (evento `pre_edit`, ordine 20): righe `PreToolUse Edit/Write` di 7.2, 6.6 e 12.4. Lo scope gira solo con il componente `scope_check`.
- Modulo `post_edit` (evento `post_edit`, ordine 20): ricalcolo del livello; `plan-check` sul piano nuovo in fase `plan` con il componente `plan_check`.

- [ ] **Step 1: Test di `pre_edit`**

`tests/test_check_writes.py`:

```python
import unittest

from tests.hookkit import DEFAULT_TOML, Lab
from tollgate_analysis import waivers
from tollgate_core import scope

IMPL = "a-impl"


def with_scope(lab, paths=("src/app.py",)):
    scope.register_plan(lab.conn, lab.ts.state, lab.work, plan_path="docs/superpowers/plans/p.md",
                        plan_sha="s", scope_paths=list(paths), plan_tasks=[(1, [])],
                        advance=False, now=lab.now)


def write_waiver(lab, *items):
    wf = waivers.WaiverFile(7, "tg/7-demo", [
        waivers.Waiver(f"w-7-{i}", t, f, None, [], "c", "w", "k") for i, (t, f) in
        enumerate(items, 1)])
    p = lab.wt / ".tollgate/waivers/7.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(waivers.dumps(wf))


class ExecutionL1Test(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def test_scope(self):
        self.assertEqual(self.lab.pre_edit(self.lab.wt / "src/app.py", agent_id=IMPL).exit, 0)
        r = self.lab.pre_edit(self.lab.wt / "src/altro.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("tollgate waiver add scope src/altro.py", r.stderr)
        write_waiver(self.lab, ("scope", "src/altro.py"))
        self.assertEqual(self.lab.pre_edit(self.lab.wt / "src/altro.py", agent_id=IMPL).exit, 0)

    def test_write_new_dir_out_of_scope(self):
        r = self.lab.pre_edit(self.lab.wt / "src/nuova/cartella/x.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)

    def test_coordinator_cannot_write_code(self):
        r = self.lab.pre_edit(self.lab.wt / "src/app.py")
        self.assertEqual(r.exit, 2)
        self.assertIn("tollgate:execute", r.stderr)
        self.assertEqual(self.lab.pre_edit(self.lab.wt / "docs/superpowers/note.md").exit, 0)

    def test_protected_files(self):
        for rel in ("tollgate.toml", "docs/superpowers/reviews/7/r.md",
                    ".tollgate/waivers/7.toml", ".github/workflows/tollgate-verdict.yml"):
            with self.subTest(rel=rel):
                self.assertEqual(self.lab.pre_edit(self.lab.wt / rel, agent_id=IMPL).exit, 2)
        self.assertEqual(self.lab.pre_edit(self.lab.ts.dir / "tollgate.db").exit, 2)

    def test_main_checkout_is_denied(self):
        r = self.lab.pre_edit(self.lab.main / "src/app.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("checkout principale", r.stderr)

    def test_locked_plan(self):
        p = self.lab.wt / "docs/superpowers/plans/p.md"
        self.assertEqual(self.lab.pre_edit(p).exit, 2)

    def test_scope_component_off(self):
        lab = Lab(toml=DEFAULT_TOML + "[components]\nscope_check = false\n")
        try:
            with_scope(lab)
            self.assertEqual(lab.pre_edit(lab.wt / "src/altro.py", agent_id=IMPL).exit, 0)
        finally:
            lab.close()


class PhasesTest(unittest.TestCase):
    def check(self, level, phase, rel, expected, agent_id=None):
        lab = Lab(level=level, phase=phase)
        try:
            r = lab.pre_edit(lab.wt / rel, agent_id=agent_id)
            self.assertEqual(r.exit, expected, (level, phase, rel, r.stderr))
        finally:
            lab.close()

    def test_plan_phase(self):
        self.check("L1", "plan", "docs/superpowers/plans/p.md", 0)
        self.check("L1", "plan", "src/app.py", 2)
        self.check("L1", "plan", ".superpowers/sdd/x.txt", 0)

    def test_spec_audit_no_plans(self):
        self.check("L2", "spec_audit", "docs/superpowers/specs/s.md", 0)
        self.check("L2", "spec_audit", "docs/superpowers/plans/p.md", 2)

    def test_review_and_pr_open(self):
        self.check("L1", "review", "src/app.py", 2, agent_id=IMPL)
        self.check("L1", "pr_open", "src/app.py", 2, agent_id=IMPL)

    def test_l0_main_session_writes(self):
        self.check("L0", "execution", "src/app.py", 0)


class OrphanTest(unittest.TestCase):
    def test_tg_branch_without_work(self):
        lab = Lab(work=False)
        try:
            r = lab.pre_edit(lab.wt / "src/app.py")
            self.assertEqual(r.exit, 2)
            self.assertIn("/tollgate:adopt #7", r.stderr)
            self.assertEqual(lab.pre_edit(lab.wt / "docs/superpowers/n.md").exit, 0)
        finally:
            lab.close()

    def test_unbound_session_outside_worktree_only_protected(self):
        lab = Lab(bind=False)
        try:
            self.assertEqual(lab.pre_edit(lab.main / "src/app.py", cwd=lab.main,
                                          session_id="altra").exit, 0)
            self.assertEqual(lab.pre_edit(lab.main / "tollgate.toml", cwd=lab.main,
                                          session_id="altra").exit, 2)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Test di `post_edit`**

`tests/test_check_post_edit.py`:

```python
import json
import unittest

from tests.hookkit import Lab
from tollgate_core import phases, scope, tasks

SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope",
            "Punti di arresto", "Rischi"]


def plan_text(must_have="M1. Somma — test: tests.test_app::test_somma",
              files=("- Modify: `src/app.py`", "- Test: `tests/test_app.py`")):
    out = []
    for s in SECTIONS:
        out += [f"## {s}", must_have if s == "Must-have" else "x", ""]
    out += ["### Task 1: Somma", *files, "", "### Task 2: Doc", "- Create: `docs/uso.md`"]
    return "\n".join(out) + "\n"


class LevelTest(unittest.TestCase):
    def test_l0_grows_to_l1_and_plan(self):
        lab = Lab(level="L0", phase="execution")
        try:
            for i in range(3):
                (lab.wt / f"src/f{i}.py").write_text("x = 1\n")
            r = lab.post_edit(lab.wt / "src/f2.py")
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["phase"]), ("L1", "plan"))
            self.assertIn("L1", r.stdout)
        finally:
            lab.close()

    def test_sensitive_path_goes_l2(self):
        lab = Lab()
        try:
            (lab.wt / "src/auth").mkdir()
            (lab.wt / "src/auth/x.py").write_text("x = 1\n")
            lab.post_edit(lab.wt / "src/auth/x.py", agent_id="a1")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L2")
        finally:
            lab.close()


class PlanCheckHookTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(phase="plan")
        self.plan = self.lab.wt / "docs/superpowers/plans/2026-10-09-somma.md"
        self.plan.parent.mkdir(parents=True)

    def tearDown(self):
        self.lab.close()

    def test_complete_plan_registers_scope(self):
        self.plan.write_text(plan_text())
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        w = phases.get_work(self.lab.conn, self.lab.work)
        self.assertEqual((w["phase"], w["plan_path"]),
                         ("execution", "docs/superpowers/plans/2026-10-09-somma.md"))
        self.assertEqual(scope.paths(self.lab.conn, self.lab.work),
                         {"src/app.py", "tests/test_app.py", "docs/uso.md"})
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 2)["state"], "pending")

    def test_incomplete_plan_vetoed_and_not_registered(self):
        self.plan.write_text(plan_text().replace("## Rischi", "## Altro"))
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 2)
        self.assertIn("## Rischi", r.stderr)
        self.assertEqual(scope.paths(self.lab.conn, self.lab.work), set())
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "plan")

    def test_pattern_and_must_have_without_test(self):
        for text in (plan_text(files=("- Modify: `src/*.py`",)),
                     plan_text(must_have="M1. Somma senza test")):
            with self.subTest(text=text[-60:]):
                self.plan.write_text(text)
                self.assertEqual(self.lab.post_edit(self.plan).exit, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_writes tests.test_check_post_edit -v`
Expected: FAIL (le scritture passano tutte, livello e scope non cambiano).

- [ ] **Step 4: Aiuti in `_common.py`**

In fondo a `bin/tollgate_checks/_common.py`:

```python
import json
import posixpath

from tollgate_analysis import globs, level as lv, profiles as prof
from tollgate_hooks.model import inject, record


def scope_exempt(ctx, work, rel: str, scope: set[str]) -> bool:
    if rel.startswith(".superpowers/") or rel == f".tollgate/waivers/{work['issue']}.toml":
        return True
    if is_docs_md(rel) and not rel.startswith("docs/superpowers/reviews/") \
            and rel not in locked_docs(work):
        return True
    if globs.match_any(ctx.cfg("scope.always"), rel):
        return True
    manifest = ctx.cfg("scope.lockfiles").get(posixpath.basename(rel))
    if manifest and posixpath.join(posixpath.dirname(rel), manifest) in scope:
        return True
    return False


def level_records(ctx, work) -> list:
    wt = Path(work["worktree"])
    base = work["work_base_sha"]
    if not base or not wt.is_dir():
        return []
    changes = git.changes(wt, base)
    cfg = ctx.cfg("levels")
    paths = [c.path for c in changes] + [c.old_path for c in changes if c.old_path]
    computed = lv.diff_level(changes, diff_bytes=git.diff_size(wt, base),
                             sensitive_paths=cfg["sensitive_paths"],
                             l0_max_files=cfg["l0_max_files"], l0_max_lines=cfg["l0_max_lines"],
                             l0_max_bytes=cfg["l0_max_bytes"])
    profs = ctx.config.profiles
    computed = lv.max_level(computed, prof.min_level(
        prof.active_profiles(paths, profs, ctx.cfg("profiles.active")), profs))
    new = lv.next_level(current=work["level"], computed=computed, cap=work["level_cap"],
                        cap_paths=json.loads(work["level_cap_paths"] or "[]"),
                        sensitive_now=lv.sensitive_in(paths, cfg["sensitive_paths"]))
    if new == work["level"]:
        return []
    out = []
    if work["level"] == "L0" and work["phase"] == "execution":
        out.append(record("phase", work=work["id"], to="plan", cause="l0_grew"))
        if new == "L2":
            out.append(record("level", work=work["id"], level="L2"))
        out.append(inject(f"tollgate: il diff supera le soglie di L0: il lavoro sale a {new} e "
                          f"torna in fase plan. Serve un piano (writing-plans)."))
    else:
        out.append(record("level", work=work["id"], level=new))
        out.append(inject(f"tollgate: il lavoro sale a {new} (percorsi sensibili o soglie)."))
    return out
```

- [ ] **Step 5: `writes.py`**

```python
"""PreToolUse Edit/Write/NotebookEdit/MultiEdit (spec 7.2, 6.6, 12.4)."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis.protected import is_protected
from tollgate_analysis.testguard import Violation
from tollgate_analysis.waivers import unresolved
from tollgate_core import git
from tollgate_hooks.adapter import edit_path
from tollgate_hooks.model import deny

from ._common import (explain, governing_work, is_docs_md, locked_docs, orphan_tg,
                      scope_exempt)

CHECK = {"api": 1, "events": ["pre_edit"], "component": None, "order": 20}
_DOCS_ONLY = ("spec_audit", "plan", "approval", "blocked", "review", "pr_open")


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def decide(event, ctx):
    raw = edit_path(event)
    if not raw:
        return []
    p = Path(raw)
    if not p.is_absolute():
        p = event.cwd / p
    p = p.resolve()
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
    wt = Path(work["worktree"]).resolve() if work["worktree"] else None
    rel_w = ctx.rel(p, wt) if wt else None
    if rel_w is None:
        if wt is not None and repo is not None and _inside(p, git.main_worktree(wt)) \
                and not _inside(p, wt):
            return [deny(f"scrittura nel checkout principale negata durante il lavoro "
                         f"#{work['issue']}: si lavora nel worktree {wt} (6.6)",
                         rule="main_checkout")]
        return []
    if rel_w in locked_docs(work):
        return [deny(f"{rel_w} è approvato e bloccato: per cambiarlo serve "
                     f"/tollgate:reopen spec|plan <motivo> (6.2)", rule="locked")]
    md_ok = is_docs_md(rel_w) or rel_w.startswith(".superpowers/")
    phase = work["phase"]
    if phase in _DOCS_ONLY:
        if phase in ("spec_audit", "approval") and rel_w.startswith("docs/superpowers/plans/"):
            return [deny(f"in fase {phase} non si scrivono piani: prima l'audit e "
                         f"/tollgate:approve spec (6.2)", rule="phase")]
        if md_ok:
            return []
        hint = (" Per correggere il codice dopo finish: /tollgate:start." if phase in
                ("review", "pr_open") else "")
        return [deny(f"in fase {phase} si scrivono solo i .md sotto docs/superpowers/."
                     + hint, rule="phase")]
    if md_ok or work["level"] == "L0":
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
```

- [ ] **Step 6: `post_edit.py`**

```python
"""PostToolUse Edit/Write (spec 7.2): livello e plan-check (7.5)."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import plan as planmod, profiles as prof
from tollgate_core import git
from tollgate_hooks.adapter import edit_path
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work, level_records

CHECK = {"api": 1, "events": ["post_edit"], "component": None, "order": 20}


def _plan(ctx, work, wt: Path, rel: str):
    if not (rel.startswith("docs/superpowers/plans/") and rel.endswith(".md")):
        return []
    if work["phase"] != "plan" or not ctx.component("plan_check") or work["plan_sha"]:
        return []
    if work["plan_path"] not in (None, rel) or git.exists_at(wt, work["work_base_sha"], rel):
        return []
    try:
        text = (wt / rel).read_text(encoding="utf-8")
    except OSError:
        return []
    r = planmod.check_plan(text, required_sections=ctx.cfg("plan.required_sections"),
                           max_scope_files=ctx.cfg("plan.max_scope_files"),
                           must_have_tests=ctx.component("must_have_tests"),
                           level=work["level"], profiles=ctx.config.profiles,
                           active_always=ctx.cfg("profiles.active"))
    if not r.ok:
        return [deny("piano incompleto, non registrato:\n- " + "\n- ".join(r.problems),
                     rule="plan_check")]
    out = [inject("tollgate: " + w) for w in r.warnings]
    if work["level"] == "L1":
        plan_tasks = [(t.number, prof.task_skills(t.files, ctx.config.profiles)[:3])
                      for t in r.tasks]
        out += [record("plan", work=work["id"], plan_path=rel, plan_sha=git.blob_sha(wt, rel),
                       scope=r.scope, tasks=plan_tasks, advance=True),
                inject(f"tollgate: piano registrato, scope di {len(r.scope)} file; fase "
                       f"execution. Prossimo passo: /tollgate:execute.")]
    else:
        out += [record("plan_path", work=work["id"], plan_path=rel),
                inject("tollgate: piano valido. Prossimi passi in L2: plan-adversary, poi "
                       "/tollgate:approve plan.")]
    return out


def decide(event, ctx):
    raw = edit_path(event)
    if not raw:
        return []
    p = Path(raw) if Path(raw).is_absolute() else event.cwd / raw
    work = governing_work(ctx, p)
    if work is None or not work["worktree"]:
        return []
    wt = Path(work["worktree"]).resolve()
    rel = ctx.rel(p, wt)
    if rel is None:
        return []
    return level_records(ctx, work) + _plan(ctx, work, wt, rel)
```

- [ ] **Step 7: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 8: Commit**

```bash
git add bin/tollgate_checks/_common.py bin/tollgate_checks/writes.py bin/tollgate_checks/post_edit.py tests/test_check_writes.py tests/test_check_post_edit.py
git commit -m "tollgate P2: controlli su Edit e Write (fasi, scope, coordinatore, protetti, livello, plan-check)"
```

---
