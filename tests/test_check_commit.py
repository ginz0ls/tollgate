import unittest

from tests.helpers import git
from tests.hookkit import DEFAULT_FILES, Lab
from tests.test_check_writes import with_scope, write_waiver
from tollgate_analysis import waivers
from tollgate_core import phases, scope

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
        wf = waivers.WaiverFile(7, "tg/7-demo", [waivers.Waiver(
            "w-7-1", "test", "tests/test_app.py", None,
            ["tests.test_app::test_somma", "tests.test_app::test_zero"], "c", "w", "k")])
        p = self.lab.wt / ".tollgate/waivers/7.toml"
        p.parent.mkdir(parents=True)
        p.write_text(waivers.dumps(wf))
        self.assertEqual(self.commit().exit, 0)

    def test_waiver_missing_a_test_id_does_not_cover(self):
        self.t.unlink()
        write_waiver(self.lab, ("test", "tests/test_app.py"))
        self.assertEqual(self.commit().exit, 2)

    def test_output_dir_and_run_dir_excluded(self):
        (self.lab.wt / "coverage").mkdir()
        (self.lab.wt / "coverage/lcov.info").write_text("x\n")
        (self.lab.wt / ".tollgate-run").mkdir()
        (self.lab.wt / ".tollgate-run/out.json").write_text("{}\n")
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


class RegisteredPlanCommitTest(unittest.TestCase):
    """Il piano registrato è bloccato (6.2), ma committarlo tale e quale non lo modifica: la skill
    `start` fa committare il piano al coordinatore dopo la registrazione."""
    PLAN = "docs/superpowers/plans/p.md"

    def setUp(self):
        self.lab = Lab(files=FILES)
        self.plan = self.lab.wt / self.PLAN
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text("# piano\n")
        sha = git(self.lab.wt, "hash-object", "--", self.PLAN)
        scope.register_plan(self.lab.conn, self.lab.ts.state, self.lab.work, plan_path=self.PLAN,
                            plan_sha=sha, scope_paths=["src/app.py"], plan_tasks=[(1, [])],
                            advance=False, now=self.lab.now)

    def tearDown(self):
        self.lab.close()

    def test_unchanged_registered_plan_can_be_committed(self):
        self.assertEqual(self.lab.bash(COMMIT).exit, 0)

    def test_changed_registered_plan_is_out_of_scope(self):
        self.plan.write_text("# piano cambiato\n")
        r = self.lab.bash(COMMIT)
        self.assertEqual(r.exit, 2)
        self.assertIn(self.PLAN, r.stderr)

    def commit_plan(self):
        git(self.lab.wt, "add", "-A")
        git(self.lab.wt, "commit", "-qm", "piano")

    def test_deleted_registered_plan_is_denied(self):
        self.commit_plan()
        self.plan.unlink()
        self.assertEqual(self.lab.bash(COMMIT).exit, 2)

    def test_renamed_registered_plan_is_denied(self):
        self.commit_plan()
        moved = self.lab.wt / "docs/superpowers/plans/rinominato.md"
        self.plan.rename(moved)
        r = self.lab.bash(COMMIT)
        self.assertEqual(r.exit, 2)
        self.assertIn(self.PLAN, r.stderr)

    def test_symlink_in_place_of_registered_plan_is_denied(self):
        target = self.lab.wt / "altro.md"
        target.write_text("# piano\n")
        self.plan.unlink()
        self.plan.symlink_to(target)
        r = self.lab.bash(COMMIT)
        self.assertEqual(r.exit, 2)
        self.assertIn(self.PLAN, r.stderr)

    def test_committed_registered_plan_does_not_open_a_block(self):
        git(self.lab.wt, "add", "-A")
        git(self.lab.wt, "commit", "-qm", "piano")
        r = self.lab.bash("git commit -qm piano", post=True)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "execution")


if __name__ == "__main__":
    unittest.main()
