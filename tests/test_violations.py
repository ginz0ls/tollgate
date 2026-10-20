import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import ROOT, git
from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML, Lab
from tests.test_check_writes import with_scope, write_waiver
from tollgate_checks._common import commit_violations
from tollgate_core import git as core_git, phases, scope, violations
from tollgate_core.config import load_config_text
from tollgate_hooks import adapter
from tollgate_hooks.context import Ctx, ReadDb

SCOPE = ("src/app.py", "tests/test_app.py")


class ReviewsExemptTest(unittest.TestCase):
    def test_own_reviews_dir_exempt_other_issue_not(self):
        lab = Lab()
        try:
            with_scope(lab, SCOPE)
            cfg = load_config_text(DEFAULT_TOML)
            for rel in ("docs/superpowers/reviews/7/plan-approval.md",
                        "docs/superpowers/reviews/8/plan-approval.md"):
                (lab.wt / rel).parent.mkdir(parents=True, exist_ok=True)
                (lab.wt / rel).write_text("x\n")
            work = phases.get_work(lab.conn, lab.work)
            self.assertEqual(work["issue"], 7)
            changes = core_git.changes(lab.wt, lab.base)
            got = violations.diff_violations(cfg, lab.conn, work, lab.wt, lab.base, None,
                                             changes, components={})
            self.assertEqual([v.path for v in got],
                             ["docs/superpowers/reviews/8/plan-approval.md"])
        finally:
            lab.close()


class ActiveProfileNamesTest(unittest.TestCase):
    TOML = DEFAULT_TOML + """
[profiles.web]
paths = ["web/**"]
"""

    def test_no_commit_gives_no_profiles_and_never_reads_the_working_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "senza commit"
            repo.mkdir()
            git(repo, "init", "-q")
            (repo / "web").mkdir()
            (repo / "web" / "page.tsx").write_text("x\n")        # non tracciato: non conta
            cfg = load_config_text(self.TOML)
            work = {"work_base_sha": "0" * 40}
            self.assertIsNone(core_git.head(repo))
            with mock.patch.object(core_git, "changes") as changes:
                self.assertEqual(violations.active_profile_names(cfg, repo, work), [])
                self.assertEqual(violations.active_profile_names(cfg, repo, work, head=None), [])
            changes.assert_not_called()

    def test_with_head_profiles_come_from_the_diff(self):
        lab = Lab(toml=self.TOML)
        try:
            (lab.wt / "web").mkdir()
            (lab.wt / "web" / "page.tsx").write_text("x\n")
            git(lab.wt, "add", "-A")
            git(lab.wt, "commit", "-qm", "web")
            cfg = load_config_text(self.TOML)
            work = phases.get_work(lab.conn, lab.work)
            self.assertEqual(violations.active_profile_names(cfg, lab.wt, work), ["web"])
        finally:
            lab.close()


class DiffViolationsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.cfg = load_config_text(DEFAULT_TOML)
        with_scope(self.lab, SCOPE)

    def tearDown(self):
        self.lab.close()

    def work(self):
        return phases.get_work(self.lab.conn, self.lab.work)

    def commit_changes(self):
        git(self.lab.wt, "add", "-A")
        git(self.lab.wt, "commit", "-qm", "lavoro")
        sha = core_git.head(self.lab.wt)
        return sha, core_git.commit_changes(self.lab.wt, sha)

    def diff(self, sha, changes, **kw):
        return violations.diff_violations(
            self.cfg, self.lab.conn, self.work(), self.lab.wt, self.lab.base, sha, changes,
            components=kw.get("components", {}))

    def delete_test_and_add_stray(self):
        (self.lab.wt / "tests/test_app.py").unlink()
        (self.lab.wt / "src/extra.py").write_text("x = 1\n")
        return self.commit_changes()

    def test_same_result_as_hook(self):
        sha, changes = self.delete_test_and_add_stray()
        got = self.diff(sha, changes)
        self.assertEqual(sorted((v.path, v.kind, v.waiver_type) for v in got),
                         [("src/extra.py", "out_of_scope", "scope"),
                          ("tests/test_app.py", "test_deleted", "test")])
        ev = adapter.to_event("PreToolUse", self.lab._base("PreToolUse-Bash", None, None))
        ctx = Ctx(ev, self.lab.ts.state, ReadDb(self.lab.conn), self.cfg, self.lab.wt,
                  self.work(), False, self.lab.now, ROOT)
        hook = commit_violations(ctx, self.work(), self.lab.wt, self.lab.base, sha, changes)
        self.assertEqual(hook, got)

    def test_waiver_resolves(self):
        sha, changes = self.delete_test_and_add_stray()
        write_waiver(self.lab, ("scope", "src/extra.py"))
        got = self.diff(sha, changes)
        self.assertEqual([v.path for v in got], ["tests/test_app.py"])

    def test_registered_plan_committed_is_exempt(self):
        lab = Lab()
        try:
            plan = "docs/superpowers/plans/p.md"
            (lab.wt / plan).parent.mkdir(parents=True)
            (lab.wt / plan).write_text("# piano\n")
            sha_blob = git(lab.wt, "hash-object", "--", plan)
            scope.register_plan(lab.conn, lab.ts.state, lab.work, plan_path=plan,
                                plan_sha=sha_blob, scope_paths=["src/app.py"],
                                plan_tasks=[(1, [])], advance=False, now=lab.now)
            git(lab.wt, "add", "-A")
            git(lab.wt, "commit", "-qm", "piano")
            sha = core_git.head(lab.wt)
            work = phases.get_work(lab.conn, lab.work)
            got = violations.diff_violations(
                self.cfg, lab.conn, work, lab.wt, lab.base, sha,
                core_git.commit_changes(lab.wt, sha), components={})
            self.assertEqual(got, [])
        finally:
            lab.close()

    def test_components_off(self):
        sha, changes = self.delete_test_and_add_stray()
        got = self.diff(sha, changes, components={"scope_check": False, "test_guard": False})
        self.assertEqual(got, [])

    def test_missing_component_defaults_on(self):
        sha, changes = self.delete_test_and_add_stray()
        self.assertEqual(len(self.diff(sha, changes, components={})), 2)


if __name__ == "__main__":
    unittest.main()
