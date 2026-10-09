import unittest
from types import SimpleNamespace

from tests.helpers import git
from tests.hookkit import T0, Lab
from tollgate_checks._common import locked_docs, orphan_tg
from tollgate_core import phases
from tollgate_hooks.context import ReadDb

SPEC = "docs/superpowers/specs/x.md"
PLAN = "docs/superpowers/plans/x.md"
APPROVAL = "docs/superpowers/reviews/7/spec-approval.md"


class LockedDocsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(level="L2", phase="spec_audit")
        self.lab.conn.execute("UPDATE work_items SET spec_path = ? WHERE id = ?",
                              (SPEC, self.lab.work))
        p = self.lab.wt / APPROVAL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("approvata\n")

    def tearDown(self):
        self.lab.close()

    def row(self):
        return phases.get_work(self.lab.conn, self.lab.work)

    def test_spec_locked_after_approval_in_later_phase(self):
        self.lab.goto("plan")
        self.assertIn(SPEC, locked_docs(self.row()))

    def test_spec_unlocked_in_spec_phase_with_approval_file(self):
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_spec_unlocked_after_reopen_spec_keeps_history_file(self):
        self.lab.goto("plan")
        phases.set_phase(self.lab.conn, self.lab.ts.state, self.lab.work, "spec_audit",
                         "reopen_spec", now=T0)
        self.assertTrue((self.lab.wt / APPROVAL).is_file())
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_blocked_uses_phase_before_block(self):
        self.lab.goto("plan")
        self.lab.conn.execute("UPDATE work_items SET phase = 'blocked', "
                              "phase_before_block = 'spec_audit' WHERE id = ?", (self.lab.work,))
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_plan_locked_after_registration_in_execution(self):
        lab = Lab(level="L1", phase="execution")
        try:
            lab.conn.execute("UPDATE work_items SET plan_path = ?, plan_sha = 'abc' "
                             "WHERE id = ?", (PLAN, lab.work))
            self.assertIn(PLAN, locked_docs(phases.get_work(lab.conn, lab.work)))
        finally:
            lab.close()

    def test_plan_unlocked_after_reopen_plan(self):
        lab = Lab(level="L1", phase="execution")
        try:
            lab.conn.execute("UPDATE work_items SET plan_path = ?, plan_sha = 'abc' "
                             "WHERE id = ?", (PLAN, lab.work))
            phases.set_phase(lab.conn, lab.ts.state, lab.work, "plan", "reopen_plan", now=T0)
            self.assertNotIn(PLAN, locked_docs(phases.get_work(lab.conn, lab.work)))
        finally:
            lab.close()


class OrphanTgTest(unittest.TestCase):
    def test_no_origin_means_no_repo_key_and_no_orphan(self):
        lab = Lab(work=False)
        try:
            git(lab.wt, "remote", "remove", "origin")
            ctx = SimpleNamespace(db=ReadDb(lab.conn))
            self.assertIsNone(orphan_tg(ctx, lab.wt))
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
