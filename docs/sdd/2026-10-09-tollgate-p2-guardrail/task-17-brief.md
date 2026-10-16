### Task 17: `git commit` (test-guard, scope, livello) e `PostToolUse Bash`

**Files:**
- Modify: `bin/tollgate_checks/_common.py` (aggiunge `commit_violations`)
- Create: `bin/tollgate_checks/commit.py`
- Create: `bin/tollgate_checks/post_bash.py`
- Test: `tests/test_check_commit.py`, `tests/test_check_post_bash.py`

**Interfaces:**
- Consumes: `testguard.check`, `testguard.Change`, `waivers.unresolved`, `git.*`, `_common.level_records`, `_common.scope_exempt`.
- Produces:
  - `_common.commit_violations(ctx, work, wt, base_ref, head_ref, changes) -> list[Violation]` (`head_ref=None`: working tree; violazioni non derogate, decisione 9).
  - Modulo `commit` (evento `pre_bash`, ordine 25): `git commit` in un lavoro attivo → test-guard (componente `test_guard`), scope (componente `scope_check`, solo dopo la registrazione dello scope e non in L0), livello; `deny` se mancano deroghe o se il lavoro è uscito da L0.
  - Modulo `post_bash` (evento `post_bash`, ordine 20): commit nuovi registrati come eventi `commit` (con `invalidate_finish`), aggiunti a `tasks.commits` del task dell'implementatore, controllati con test-guard e scope rispetto al genitore; violazioni → blocco `needs_you`; ramo del worktree cambiato → `needs_you`; livello ricalcolato.

- [ ] **Step 1: Test di `commit`**

`tests/test_check_commit.py`:

```python
import unittest

from tests.hookkit import DEFAULT_FILES, Lab
from tests.test_check_writes import with_scope, write_waiver

FILES = dict(DEFAULT_FILES, **{
    "src/__tests__/a.test.js": "describe('a', () => {\n  it('x', () => {\n"
                               "    expect(1).toBe(1)\n  })\n})\n"})
SCOPE = ("src/app.py", "tests/test_app.py", "src/__tests__/a.test.js")
COMMIT = "git add -A && git commit -m lavoro"


class CommitTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(files=FILES)
        with_scope(self.lab, SCOPE)
        self.t = self.lab.wt / "tests/test_app.py"

    def tearDown(self):
        self.lab.close()

    def commit(self):
        return self.lab.bash(COMMIT, agent_id="a1")

    def test_deleted_test(self):
        self.t.unlink()
        self.assertEqual(self.commit().exit, 2)

    def test_deleted_js_test_in_dunder_tests(self):
        (self.lab.wt / "src/__tests__/a.test.js").unlink()
        self.assertEqual(self.commit().exit, 2)

    def test_pytest_skip_added(self):
        self.t.write_text(self.t.read_text().replace(
            "    assert somma(0, 0) == 0", "    pytest.skip('no')\n    assert somma(0, 0) == 0"))
        self.assertEqual(self.commit().exit, 2)

    def test_mark_skip_added(self):
        self.t.write_text(self.t.read_text().replace("def test_zero", "@pytest.mark.skip\n"
                                                                      "def test_zero"))
        self.assertEqual(self.commit().exit, 2)

    def test_assertion_replaced_by_comment(self):
        self.t.write_text(self.t.read_text().replace("    assert somma(0, 0) == 0",
                                                     "    # assert somma(0, 0) == 0\n    pass"))
        r = self.commit()
        self.assertEqual(r.exit, 2)
        self.assertIn("asserzioni diminuite", r.stderr)

    def test_process_exit_is_fine(self):
        js = self.lab.wt / "src/__tests__/a.test.js"
        js.write_text(js.read_text().replace("expect(1).toBe(1)",
                                             "expect(1).toBe(1); process.exit(0)"))
        self.assertEqual(self.commit().exit, 0)

    def test_out_of_scope_then_waiver(self):
        (self.lab.wt / "src/extra.py").write_text("x = 1\n")
        r = self.commit()
        self.assertEqual(r.exit, 2)
        self.assertIn("src/extra.py", r.stderr)
        write_waiver(self.lab, ("scope", "src/extra.py"))
        self.assertEqual(self.commit().exit, 0)

    def test_pending_test_waiver_lets_commit_pass(self):
        self.t.unlink()
        write_waiver(self.lab, ("test", "tests/test_app.py"))
        self.assertEqual(self.commit().exit, 0)

    def test_test_guard_component_off(self):
        lab = Lab(files=FILES, toml="schema_version = 1\n[gate]\nmode = \"protected\"\n"
                                    "[components]\ntest_guard = false\n")
        try:
            with_scope(lab, SCOPE)
            (lab.wt / "tests/test_app.py").unlink()
            self.assertEqual(lab.bash(COMMIT, agent_id="a1").exit, 0)
        finally:
            lab.close()

    def test_l0_growing_blocks_commit(self):
        lab = Lab(level="L0")
        try:
            for i in range(3):
                (lab.wt / f"src/f{i}.py").write_text("x = 1\n")
            r = lab.bash(COMMIT)
            self.assertEqual(r.exit, 2)
            self.assertIn("plan", r.stderr)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Test di `post_bash`**

`tests/test_check_post_bash.py`:

```python
import unittest

from tests.hookkit import SESSION, Lab
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import acts, phases, subagents, tasks


class PostBashTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab, ("src/app.py", "tests/test_app.py"))

    def tearDown(self):
        self.lab.close()

    def test_new_commit_recorded_and_finish_invalidated(self):
        head0 = git(self.lab.wt, "rev-parse", "HEAD")
        acts.record_act(self.lab.conn, type_="finish", typed_text="/tollgate:finish",
                        session=SESSION, work=self.lab.work, head_sha=head0, now=self.lab.now,
                        ttl_minutes=10)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        subagents.start(self.lab.conn, agent_id="a1", type_="tollgate:implementer",
                        session=SESSION, work=self.lab.work, task=1, base_sha=head0,
                        fingerprint="f", now=self.lab.now)
        (self.lab.wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
        git(self.lab.wt, "commit", "-qam", "ok")
        head1 = git(self.lab.wt, "rev-parse", "HEAD")
        r = self.lab.bash("git commit -qam ok", post=True, agent_id="a1")
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.lab.events("commit"), [{"sha": head1}])
        self.assertEqual(self.lab.conn.execute("SELECT state FROM acts WHERE type='finish'")
                         .fetchone()[0], "expired")
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["commits"],
                         f'["{head1}"]')
        self.lab.bash("git status", post=True, agent_id="a1")
        self.assertEqual(len(self.lab.events("commit")), 1)

    def test_merge_bringing_deleted_test_opens_needs_you(self):
        git(self.lab.main, "checkout", "-q", "-b", "altro")
        (self.lab.main / "tests/test_app.py").unlink()
        git(self.lab.main, "commit", "-qam", "via il test")
        git(self.lab.main, "checkout", "-q", "main")
        git(self.lab.wt, "merge", "-q", "--no-edit", "altro")
        r = self.lab.bash("git merge altro", post=True)
        self.assertEqual(r.exit, 2)
        w = phases.get_work(self.lab.conn, self.lab.work)
        self.assertEqual(w["phase"], "blocked")
        self.assertEqual(self.lab.conn.execute("SELECT type FROM blocks").fetchone()[0],
                         "needs_you")

    def test_branch_changed_opens_needs_you(self):
        git(self.lab.wt, "checkout", "-q", "-b", "fuga")
        self.lab.bash("git checkout -b fuga", post=True)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")


if __name__ == "__main__":
    unittest.main()
```

Nota: `tests/test_check_post_bash.py` registra il task 1 con `with_scope` (che crea il task 1 tramite `register_plan`).

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_commit tests.test_check_post_bash -v`
Expected: FAIL.

- [ ] **Step 4: `commit_violations` in `_common.py`**

```python
from tollgate_analysis import testguard
from tollgate_analysis.testguard import Violation
from tollgate_analysis.waivers import unresolved


def commit_violations(ctx, work, wt: Path, base_ref: str, head_ref: str | None,
                      changes) -> list:
    out = []
    paths = [c.path for c in changes]
    if ctx.component("test_guard"):
        tg = []
        for c in changes:
            base_text = None if c.status == "A" else git.text_at(wt, base_ref,
                                                                 c.old_path or c.path)
            if c.status == "D":
                head_text = None
            elif head_ref is None:
                head_text = git.worktree_text(wt, c.path)
            else:
                head_text = git.text_at(wt, head_ref, c.path)
            tg.append(testguard.Change(c.status, c.path, c.old_path, base_text, head_text,
                                       c.binary))
        out += testguard.check(tg, ctx.guard_config(work, paths)).violations
    if ctx.component("scope_check") and work["level"] != "L0" and work["plan_sha"]:
        scope = ctx.scope(work)
        for c in changes:
            if c.path not in scope and not scope_exempt(ctx, work, c.path, scope):
                out.append(Violation("out_of_scope", c.path, "file fuori dallo scope del piano",
                                     "scope"))
    return unresolved(out, ctx.waiver_file(work))
```

- [ ] **Step 5: `commit.py`**

```python
"""git commit in un lavoro attivo (spec 7.4): test-guard, scope e livello su working tree e indice."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import bash
from tollgate_core import git
from tollgate_hooks.model import deny

from ._common import commit_violations, explain, governing_work, level_records

CHECK = {"api": 1, "events": ["pre_bash"], "component": None, "order": 25}


def decide(event, ctx):
    try:
        cmds = bash.parse(str(event.tool_input.get("command") or ""), str(event.cwd))
    except bash.BashParseError:
        return []
    for c in cmds:
        if not bash.is_commit(c):
            continue
        edir = Path(bash.effective_dir(c)).resolve()
        work = governing_work(ctx, edir)
        if work is None or not work["worktree"]:
            continue
        wt = Path(work["worktree"]).resolve()
        if not (edir == wt or wt in edir.parents):
            continue
        head = git.head(wt)
        if head is None:
            continue
        out = level_records(ctx, work)
        if any(d.kind == "record" and d.op == "phase" for d in out):
            return out + [deny("il diff ha superato le soglie di L0: il lavoro torna in fase "
                               "plan e serve un piano prima del commit", rule="level")]
        left = commit_violations(ctx, work, wt, head, None, git.changes(wt, head))
        if left:
            return out + [deny("commit negato, violazioni senza deroga:\n"
                               + explain(left, work["issue"]), rule="commit")]
        return out
    return []
```

- [ ] **Step 6: `post_bash.py`**

```python
"""PostToolUse Bash (spec 7.2): commit nuovi, ramo cambiato; il controllo a valle di 7.4."""
from __future__ import annotations

import json
from pathlib import Path

from tollgate_core import git, subagents
from tollgate_core.git import EMPTY_TREE
from tollgate_hooks.model import deny, record

from ._common import commit_violations, explain, governing_work, level_records

CHECK = {"api": 1, "events": ["post_bash"], "component": None, "order": 20}


def decide(event, ctx):
    work = governing_work(ctx, event.cwd)
    if work is None or not work["worktree"] or not Path(work["worktree"]).is_dir():
        return []
    wt = Path(work["worktree"]).resolve()
    out = []
    br = git.branch(wt)
    if work["branch"] and br != work["branch"]:
        out.append(record("block", work=work["id"], type="needs_you",
                          reason=f"il ramo del worktree è {br or '(staccato)'}, atteso "
                                 f"{work['branch']}: rimettilo o decidi come procedere"))
    head, base = git.head(wt), work["work_base_sha"]
    if not head or not base:
        return out
    known = {json.loads(r[0]).get("sha") for r in ctx.db.execute(
        "SELECT data FROM events WHERE type = 'commit' AND work = ?", (work["id"],))}
    new = [s for s in git.rev_list(wt, base, head) if s not in known]
    if not new:
        return out
    task = None
    if event.agent_id:
        row = subagents.get(ctx.db, event.agent_id)
        task = row["task"] if row is not None else None
    problems = []
    for sha in new:
        out.append(record("commit", work=work["id"], sha=sha, head=head))
        if task is not None:
            out.append(record("task_commit", work=work["id"], number=task, sha=sha))
        parent = git.resolve_ref(wt, f"{sha}^") or EMPTY_TREE
        left = commit_violations(ctx, work, wt, parent, sha, git.commit_changes(wt, sha))
        if left:
            problems.append(f"commit {sha[:10]}:\n" + explain(left, work["issue"]))
    out = level_records(ctx, work) + out
    if problems:
        text = "\n".join(problems)
        out += [record("block", work=work["id"], type="needs_you",
                       reason=("commit con violazioni senza deroga: " + text)[:1000]),
                deny("commit registrati con violazioni senza deroga; aperto un blocco "
                     "needs_you:\n" + text, rule="post_bash")]
    return out
```

- [ ] **Step 7: Verificare che passino**

Run: `tests/run`
Expected: OK. Nota: in `test_merge_bringing_deleted_test_opens_needs_you` il commit di merge si confronta con il primo genitore, che ha ancora il test: la cancellazione deve risultare.

- [ ] **Step 8: Commit**

```bash
git add bin/tollgate_checks/_common.py bin/tollgate_checks/commit.py bin/tollgate_checks/post_bash.py tests/test_check_commit.py tests/test_check_post_bash.py
git commit -m "tollgate P2: controllo di git commit e PostToolUse Bash"
```

---
