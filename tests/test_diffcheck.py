import unittest

from tests.flowkit import PLAN, SPEC, FlowLab, plan_text
from tests.hookkit import DEFAULT_TOML
from tollgate_core import diffcheck, git as core_git, phases, scope, violations
from tollgate_core.config import load_config_text

REVIEW = "docs/superpowers/reviews/7/spec-adversarial-1.md"


class DiffcheckCase(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab(issue=7, phase="plan")
        self.addCleanup(self.fl.lab.close)
        self.cfg = load_config_text(DEFAULT_TOML)
        self.fl.register_plan(tasks=1)
        self.fl.commit(PLAN, plan_text(tasks=1), "piano")

    @property
    def work(self):
        return phases.get_work(self.fl.conn, self.fl.work)

    def changes(self):
        return core_git.changes(self.fl.wt, self.fl.base, head="HEAD")

    def findings(self, **over):
        work = self.work
        args = dict(repo=self.fl.wt, issue=work["issue"], level=work["level"],
                    base_ref=self.fl.base, head_ref="HEAD", changes=self.changes(),
                    scope=scope.paths(self.fl.conn, work["id"]),
                    locked=violations.locked_docs(work),
                    registered_plan=(work["plan_path"], work["plan_sha"]), approved_spec=None,
                    waiver_file=None, components={})
        args.update(over)
        return diffcheck.diff_findings(self.cfg, **args)


class DiffcheckTest(DiffcheckCase):
    def test_same_result_as_diff_violations(self):
        self.fl.commit("src/stray.py", "x = 1\n", "fuori scope")
        self.fl.commit(REVIEW, "r\n", "report")
        self.fl.commit("src/app.py", "y = 2\n", "in scope")
        work = self.work
        want = violations.diff_violations(self.cfg, self.fl.conn, work, self.fl.wt, self.fl.base,
                                          "HEAD", self.changes(), components={})
        self.assertEqual([(v.kind, v.path) for v in want], [("out_of_scope", "src/stray.py")])
        self.assertEqual(self.findings(), want)

    def test_diff_check_reports_watched_files(self):
        self.fl.commit("package.json", "{}\n", "manifest")
        got = diffcheck.diff_check(self.cfg, repo=self.fl.wt, issue=7, level="L1",
                                   base_ref=self.fl.base, head_ref="HEAD",
                                   changes=self.changes(), scope=set(), locked=set(),
                                   registered_plan=None, approved_spec=None, waiver_file=None,
                                   components={})
        self.assertEqual(got.watched, ["package.json"])
        self.assertIn("package.json", [v.path for v in got.violations])
        again = diffcheck.diff_findings(self.cfg, repo=self.fl.wt, issue=7, level="L1",
                                        base_ref=self.fl.base, head_ref="HEAD",
                                        changes=self.changes(), scope=set(), locked=set(),
                                        registered_plan=None, approved_spec=None,
                                        waiver_file=None, components={})
        self.assertEqual(again, got.violations)

    def test_scope_none_skips_scope(self):
        self.fl.commit("src/stray.py", "x = 1\n", "fuori scope")
        self.assertEqual([v.path for v in self.findings()], ["src/stray.py"])
        self.assertEqual(self.findings(scope=None), [])

    def test_l0_and_component_off_skip_scope(self):
        self.fl.commit("src/stray.py", "x = 1\n", "fuori scope")
        self.assertEqual(self.findings(level="L0"), [])
        self.assertEqual(self.findings(components={"scope_check": False}), [])

    def test_approved_spec_exempt_only_on_same_blob(self):
        blob = self.fl.write_spec()
        kw = dict(locked={SPEC}, registered_plan=None)
        self.assertEqual([v.path for v in self.findings(**kw)], [SPEC])
        self.assertEqual(self.findings(approved_spec=(SPEC, blob), **kw), [])
        self.assertEqual([v.path for v in self.findings(approved_spec=(SPEC, "0" * 40), **kw)],
                         [SPEC])
        self.assertEqual([v.path for v in self.findings(approved_spec=("altro.md", blob), **kw)],
                         [SPEC])

    def test_plan_change_is_attention_flag(self):
        self.assertEqual(self.findings(), [])           # il piano registrato, tale e quale
        self.fl.commit(PLAN, plan_text(tasks=1) + "\nuna riga in più\n", "piano cambiato")
        self.assertEqual([(v.kind, v.path) for v in self.findings()],
                         [("out_of_scope", PLAN)])
        self.assertEqual([(v.kind, v.path) for v in self.findings(plan_change_is_attention=False)],
                         [("out_of_scope", PLAN)])
        self.assertEqual(self.findings(plan_change_is_attention=True), [])
        # un file nuovo resta fuori scope anche con il flag
        self.fl.commit("src/stray.py", "x = 1\n", "fuori scope")
        self.assertEqual([v.path for v in self.findings(plan_change_is_attention=True)],
                         ["src/stray.py"])

    def test_working_tree_blob_for_registered_plan(self):
        got = self.findings(head_ref=None, changes=core_git.changes(self.fl.wt, self.fl.base))
        self.assertEqual(got, [])
        (self.fl.wt / PLAN).write_text("cambiato\n")
        got = self.findings(head_ref=None, changes=core_git.changes(self.fl.wt, self.fl.base))
        self.assertEqual([v.path for v in got], [PLAN])

    def test_scope_exempt_rel(self):
        ex = lambda rel, **kw: diffcheck.scope_exempt_rel(  # noqa: E731
            self.cfg, issue=7, rel=rel, scope=kw.get("scope", set()), locked=kw.get("locked", set()))
        self.assertTrue(ex(".superpowers/x"))
        self.assertTrue(ex(".tollgate/waivers/7.toml"))
        self.assertFalse(ex(".tollgate/waivers/8.toml"))
        self.assertTrue(ex("docs/superpowers/reviews/7/a.md"))
        self.assertFalse(ex("docs/superpowers/reviews/8/a.md"))
        self.assertTrue(ex("docs/superpowers/notes/a.md"))
        self.assertFalse(ex("docs/superpowers/notes/a.md", locked={"docs/superpowers/notes/a.md"}))
        self.assertFalse(ex("src/new.py"))

    def test_moved_names_importable_from_violations(self):
        self.assertIs(violations.guard_config, diffcheck.guard_config)
        self.assertIs(violations.is_docs_md, diffcheck.is_docs_md)


if __name__ == "__main__":
    unittest.main()
