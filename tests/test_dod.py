import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, dod, phases, receipts, tasks

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
EXT_OK = {"guard_scope": True, "must_have": True, "approvals": True, "specialists": True}


class DodTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def work(self, level, issue=1):
        return phases.create_work(self.conn, repo_key="github.com/o/r", issue=issue,
                                  level=level, now=T0)

    def receipt(self, w, state, command="verify", sha="h1"):
        self.conn.execute(
            "INSERT INTO receipts (work, sha, command, produced_by, state, at) "
            "VALUES (?, ?, ?, 'verify', ?, 'x')", (w, sha, command, state))

    def done_task(self, w, n, required=(), used=()):
        tasks.add_task(self.conn, w, n, source=f"plan:{n}", skills_required=list(required),
                       now=T0)
        for s in used:
            tasks.add_skill_used(self.conn, w, n, s)
        for e in ("start", "report_done", "approved"):
            tasks.task_event(self.conn, w, n, e, now=T0)

    def finding(self, w, fid, severity, verification, decision=None):
        self.conn.execute(
            "INSERT INTO findings (id, work, severity, verification, user_decision) "
            "VALUES (?, ?, ?, ?, ?)", (fid, w, severity, verification, decision))

    def items(self, w, **kw):
        base = dict(head_sha="h1", allow_no_tests=False, external=EXT_OK,
                    required_commands=["verify"])
        base.update(kw)
        return {i.key: i for i in dod.compute_dod(self.conn, w, **base)}

    def test_items_per_level(self):
        self.assertEqual(set(self.items(self.work("L0", 1))), {"receipt", "guard_scope"})
        self.assertEqual(set(self.items(self.work("L1", 2))),
                         {"receipt", "guard_scope", "tasks_approved", "findings", "must_have",
                          "skills"})
        self.assertEqual(set(self.items(self.work("L2", 3))),
                         {"receipt", "guard_scope", "tasks_approved", "findings", "must_have",
                          "skills", "approvals", "specialists"})

    def test_receipt_rules(self):
        w = self.work("L0")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.receipt(w, "red")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.receipt(w, "green")
        self.assertTrue(self.items(w)["receipt"].ok)
        self.receipt(w, "red", command="web.lint")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.assertIn("web.lint", self.items(w)["receipt"].detail)
        self.assertFalse(self.items(w, head_sha="h2")["receipt"].ok)

    def test_empty_needs_allow_no_tests(self):
        w = self.work("L0")
        self.receipt(w, "empty")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.assertTrue(self.items(w, allow_no_tests=True)["receipt"].ok)

    def test_tasks_findings_skills(self):
        w = self.work("L1")
        self.assertFalse(self.items(w)["tasks_approved"].ok)
        self.done_task(w, 1, required=["tdd"], used=["tdd"])
        self.assertTrue(self.items(w)["tasks_approved"].ok)
        self.assertTrue(self.items(w)["skills"].ok)
        tasks.add_task(self.conn, w, 2, source="plan:2", skills_required=["a"], now=T0)
        self.assertFalse(self.items(w)["tasks_approved"].ok)
        self.assertFalse(self.items(w)["skills"].ok)
        self.assertIn("a", self.items(w)["skills"].detail)
        self.finding(w, "f-1-1", "major", "confirmed")
        self.assertFalse(self.items(w)["findings"].ok)
        self.conn.execute("UPDATE findings SET user_decision = 'downgraded:minor'")
        self.assertTrue(self.items(w)["findings"].ok)
        self.finding(w, "f-1-2", "blocker", "rejected")
        self.finding(w, "f-1-3", "moderate", "confirmed")
        self.assertTrue(self.items(w)["findings"].ok)

    def test_external_missing_counts_as_failing(self):
        w = self.work("L0")
        self.receipt(w, "green")
        items = dod.compute_dod(self.conn, w, head_sha="h1", allow_no_tests=False,
                                required_commands=["verify"])
        guard = [i for i in items if i.key == "guard_scope"][0]
        self.assertIsNone(guard.ok)
        self.assertFalse(dod.dod_passes(items))

    def test_profile_items_and_pass(self):
        w = self.work("L1")
        self.receipt(w, "green")
        self.done_task(w, 1)
        items = dod.compute_dod(self.conn, w, head_sha="h1", allow_no_tests=False,
                                external=EXT_OK, required_commands=["verify"],
                                profile_items={"profile:web.a11y": True})
        self.assertIn("profile:web.a11y", [i.key for i in items])
        self.assertTrue(dod.dod_passes(items))
        items = dod.compute_dod(self.conn, w, head_sha="h1", allow_no_tests=False,
                                external=EXT_OK, required_commands=["verify"],
                                profile_items={"profile:web.a11y": False})
        self.assertFalse(dod.dod_passes(items))

    def test_receipt_requires_all_required_commands(self):
        w = self.work("L0")
        self.receipt(w, "green", command="test_related")
        r = self.items(w, required_commands=["verify"])["receipt"]
        self.assertFalse(r.ok)
        self.assertIn("mancano", r.detail)
        self.assertIn("verify", r.detail)
        self.assertTrue(self.items(w, required_commands=["test_related"])["receipt"].ok)

    def test_receipt_no_required_commands_is_not_dod(self):
        w = self.work("L0")
        self.receipt(w, "green")
        r = self.items(w, required_commands=[])["receipt"]
        self.assertFalse(r.ok)
        self.assertIn("nessun comando richiesto", r.detail)

    def test_receipt_last_one_counts(self):
        w = self.work("L0")
        self.receipt(w, "green")
        self.receipt(w, "red")
        self.assertFalse(self.items(w)["receipt"].ok)

    def test_dod_passes_empty_is_false(self):
        self.assertFalse(dod.dod_passes([]))


class UncountedTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=1, level="L0", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _receipt(self, exit_code):
        receipts.add(self.conn, work=self.w, sha="h", command="verify", resolved_command="x",
                     exit_code=exit_code, tests_run=None, tests_skipped=None, duration=0.1,
                     log=None, produced_by="verify", state="uncounted", now=T0)

    def test_uncounted_ok_only_with_allow_no_tests_and_exit_zero(self):
        self._receipt(0)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=True,
                               required_commands=["verify"])[0]
        self.assertTrue(item.ok)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=False,
                               required_commands=["verify"])[0]
        self.assertFalse(item.ok)

    def test_uncounted_with_failure_is_red(self):
        self._receipt(1)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=True,
                               required_commands=["verify"])[0]
        self.assertFalse(item.ok)
