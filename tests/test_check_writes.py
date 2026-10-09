import os
import unittest
from unittest import mock

from tests.helpers import git as g
from tests.hookkit import DEFAULT_TOML, Lab
from tollgate_analysis import waivers
from tollgate_core import git as core_git, phases, scope
from tollgate_core.paths import repo_key

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

    def test_write_new_dir_with_spaces(self):
        lab = Lab()
        try:
            with_scope(lab, ("src/nuova cartella/x y.py",))
            self.assertEqual(lab.pre_edit(lab.wt / "src/nuova cartella/x y.py",
                                          agent_id=IMPL).exit, 0)
            self.assertEqual(lab.pre_edit(lab.wt / "src/nuova cartella/z.py",
                                          agent_id=IMPL).exit, 2)
        finally:
            lab.close()

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

    def test_git_hooks_and_config_are_protected_bound(self):
        for p in (self.lab.main / ".git/hooks/pre-commit", self.lab.main / ".git/config",
                  self.lab.wt / ".git/hooks/pre-commit", self.lab.wt / ".git/config"):
            with self.subTest(path=str(p)):
                r = self.lab.pre_edit(p, agent_id=IMPL)
                self.assertEqual(r.exit, 2, r.stderr)
                self.assertIn("protetto", r.stderr)

    def test_main_checkout_is_denied(self):
        r = self.lab.pre_edit(self.lab.main / "src/app.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("checkout principale", r.stderr)

    def test_other_worktree_inside_main_is_not_main_checkout(self):
        nested = self.lab.main / "nested wt"
        g(self.lab.main, "worktree", "add", "-q", "-b", "altro", str(nested))
        r = self.lab.pre_edit(nested / "src/app.py", agent_id=IMPL)
        self.assertNotIn("checkout principale", r.stderr)

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

    def test_scope_paths_are_literal_names(self):
        lab = Lab()
        try:
            with_scope(lab, ("app/[id]/page.tsx", "src/a*.py"))
            self.assertEqual(lab.pre_edit(lab.wt / "app/[id]/page.tsx", agent_id=IMPL).exit, 0)
            self.assertEqual(lab.pre_edit(lab.wt / "app/i/page.tsx", agent_id=IMPL).exit, 2)
            self.assertEqual(lab.pre_edit(lab.wt / "src/a*.py", agent_id=IMPL).exit, 0)
            self.assertEqual(lab.pre_edit(lab.wt / "src/ab.py", agent_id=IMPL).exit, 2)
        finally:
            lab.close()

    def test_exempt_from_scope(self):
        lab = Lab(toml=DEFAULT_TOML + '[scope]\nalways = ["CHANGELOG.md", "docs/gen/**"]\n')
        try:
            with_scope(lab, ("web/package.json",))
            for rel in ("CHANGELOG.md", "docs/gen/a/b.txt", "web/package-lock.json",
                        "reports/junit.xml", "coverage/lcov.info", ".tollgate-run/out.json",
                        ".superpowers/sdd/x.txt"):
                with self.subTest(rel=rel):
                    self.assertEqual(lab.pre_edit(lab.wt / rel, agent_id=IMPL).exit, 0)
            for rel in ("pnpm-lock.yaml", "other/package-lock.json", "src/zzz.py"):
                with self.subTest(rel=rel):
                    self.assertEqual(lab.pre_edit(lab.wt / rel, agent_id=IMPL).exit, 2)
        finally:
            lab.close()


class NestedRepoTest(unittest.TestCase):
    """Un repo annidato non aggira la protezione: rel si valuta su ogni radice pertinente."""
    CASES = (("docs/superpowers/reviews/7", "r.md"), (".tollgate", "waivers/7.toml"))

    def test_bound_session(self):
        lab = Lab()
        try:
            with_scope(lab)
            for nested, f in self.CASES:
                with self.subTest(nested=nested):
                    (lab.wt / nested).mkdir(parents=True, exist_ok=True)
                    g(lab.wt / nested, "init", "-q")
                    r = lab.pre_edit(lab.wt / nested / f, agent_id=IMPL)
                    self.assertEqual(r.exit, 2, r.stderr)
                    self.assertIn("protetto", r.stderr)
        finally:
            lab.close()

    def test_unbound_session(self):
        lab = Lab(bind=False)
        try:
            for nested, f in self.CASES:
                with self.subTest(nested=nested):
                    (lab.main / nested).mkdir(parents=True, exist_ok=True)
                    g(lab.main / nested, "init", "-q")
                    r = lab.pre_edit(lab.main / nested / f, cwd=lab.main, session_id="altra")
                    self.assertEqual(r.exit, 2, r.stderr)
                    self.assertIn("protetto", r.stderr)
        finally:
            lab.close()


class RoutingTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def test_worktrees_failure_denies(self):
        with mock.patch.object(core_git, "worktrees", side_effect=core_git.GitError("boom")):
            r = self.lab.pre_edit(self.lab.tmp / "fuori.txt", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("worktree", r.stderr)
        self.assertIn("verificare", r.stderr)

    def test_other_active_work_is_denied_but_tmp_is_allowed(self):
        wt8 = self.lab.tmp / "wt 8"
        g(self.lab.main, "worktree", "add", "-q", "-b", "tg/8-altro", str(wt8))
        phases.create_work(self.lab.conn, repo_key=repo_key(str(self.lab.origin)), issue=8,
                           level="L1", now=self.lab.now, branch="tg/8-altro",
                           worktree=str(wt8), work_base_sha=self.lab.base,
                           gate_mode="protected")
        r = self.lab.pre_edit(wt8 / "src/app.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("#8", r.stderr)
        self.assertEqual(self.lab.pre_edit(self.lab.tmp / "fuori.txt", agent_id=IMPL).exit, 0)


class SymlinkTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab, ("src/app.py", "src/dir con spazi/ok.py"))
        self.wt = self.lab.wt

    def tearDown(self):
        self.lab.close()

    def test_symlink_inside_worktree_to_out_of_scope(self):
        (self.wt / "other").mkdir()
        os.symlink(self.wt / "other", self.wt / "src/lnk")
        self.assertEqual(self.lab.pre_edit(self.wt / "src/lnk/x.py", agent_id=IMPL).exit, 2)

    def test_symlink_to_protected_file(self):
        os.symlink(self.wt / "tollgate.toml", self.wt / "src/cfg.py")
        r = self.lab.pre_edit(self.wt / "src/cfg.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("protetto", r.stderr)

    def test_symlink_to_main_checkout(self):
        os.symlink(self.lab.main / "src", self.wt / "src/dir con spazi")
        r = self.lab.pre_edit(self.wt / "src/dir con spazi/ok.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("checkout principale", r.stderr)

    def test_worktree_reached_through_symlink(self):
        link = self.lab.tmp / "via link"
        os.symlink(self.wt, link)
        self.assertEqual(self.lab.pre_edit(link / "src/app.py", agent_id=IMPL).exit, 0)
        self.assertEqual(self.lab.pre_edit(link / "src/nuova/x.py", agent_id=IMPL).exit, 2)
        self.assertEqual(self.lab.pre_edit(link / "src/dir con spazi/ok.py",
                                           agent_id=IMPL).exit, 0)
        self.assertEqual(self.lab.pre_edit(link / "tollgate.toml", agent_id=IMPL).exit, 2)


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

    def test_blocked_uses_phase_before_block(self):
        lab = Lab(level="L2", phase="spec_audit")
        try:
            lab.conn.execute("UPDATE work_items SET phase = 'blocked', "
                             "phase_before_block = 'spec_audit' WHERE id = ?", (lab.work,))
            self.assertEqual(lab.pre_edit(lab.wt / "docs/superpowers/plans/p.md").exit, 2)
            self.assertEqual(lab.pre_edit(lab.wt / "docs/superpowers/specs/s.md").exit, 0)
            self.assertEqual(lab.pre_edit(lab.wt / "src/app.py", agent_id=IMPL).exit, 2)
        finally:
            lab.close()


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

    def test_git_hooks_and_config_unbound(self):
        lab = Lab(bind=False)
        try:
            for p in (lab.main / ".git/hooks/pre-commit", lab.main / ".git/config"):
                with self.subTest(path=str(p)):
                    r = lab.pre_edit(p, cwd=lab.main, session_id="altra")
                    self.assertEqual(r.exit, 2, r.stderr)
        finally:
            lab.close()

    def test_git_hooks_without_any_work(self):
        lab = Lab(work=False)
        try:
            self.assertEqual(lab.pre_edit(lab.main / ".git/hooks/post-commit",
                                          cwd=lab.main).exit, 2)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
