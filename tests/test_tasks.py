import itertools
import json
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases, tasks
from tollgate_core.tasks import TaskTransitionError

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
EXPECTED = {
    ("pending", "start"): "running", ("running", "report_done"): "review",
    ("running", "report_blocked"): "blocked", ("running", "needs_context"): "running",
    ("running", "budget_exceeded"): "blocked", ("running", "interrupted"): "pending",
    ("review", "fix"): "running", ("review", "approved"): "done",
    ("blocked", "unblocked"): "pending",
}


class TasksTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def force(self, number, state):
        self.conn.execute("UPDATE tasks SET state = ? WHERE work = ? AND number = ?",
                          (state, self.w, number))

    def test_table_is_exact(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        allowed = {}
        for state, event in itertools.product(tasks.STATES, tasks.TASK_EVENTS):
            self.force(1, state)
            try:
                allowed[(state, event)] = tasks.task_event(self.conn, self.w, 1, event, now=T0)
            except TaskTransitionError:
                pass
        self.assertEqual(allowed, EXPECTED)

    def test_fix_rounds_counted_by_cli(self):
        tasks.add_task(self.conn, self.w, 2, source="plan:2", now=T0)
        tasks.task_event(self.conn, self.w, 2, "start", now=T0)
        for _ in range(3):
            tasks.task_event(self.conn, self.w, 2, "report_done", now=T0)
            tasks.task_event(self.conn, self.w, 2, "fix", now=T0)
        tasks.task_event(self.conn, self.w, 2, "needs_context", now=T0)
        tasks.task_event(self.conn, self.w, 2, "interrupted", now=T0)
        row = tasks.get_task(self.conn, self.w, 2)
        self.assertEqual((row["fix_rounds"], row["state"], row["verdict"]), (3, "pending", "changes"))

    def test_start_only_from_pending(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        tasks.task_event(self.conn, self.w, 1, "start", now=T0)
        with self.assertRaises(TaskTransitionError):
            tasks.task_event(self.conn, self.w, 1, "start", now=T0)

    def test_approved_sets_verdict_and_event(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", skills_required=["a"], now=T0)
        for e in ("start", "report_done", "approved"):
            tasks.task_event(self.conn, self.w, 1, e, now=T0)
        row = tasks.get_task(self.conn, self.w, 1)
        self.assertEqual((row["state"], row["verdict"]), ("done", "approved"))
        self.assertEqual(json.loads(row["skills_required"]), ["a"])
        last = [e for e in events.export_events(self.conn, 0) if e["type"] == "task_change"][-1]
        self.assertEqual(last["data"], {"number": 1, "kind": "plan", "state": "done",
                                        "fix_rounds": 0, "verdict": "approved"})

    def test_numbers_duplicates_unknowns(self):
        self.assertEqual(tasks.next_number(self.conn, self.w), 1)
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        self.assertEqual(tasks.next_number(self.conn, self.w), 2)
        with self.assertRaises(ValueError):
            tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        with self.assertRaises(ValueError):
            tasks.add_task(self.conn, self.w, 3, source="x", kind="altro", now=T0)
        with self.assertRaises(ValueError):
            tasks.task_event(self.conn, self.w, 1, "boh", now=T0)
        with self.assertRaises(ValueError):
            tasks.get_task(self.conn, self.w, 99)

    def test_skills_used(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        tasks.add_skill_used(self.conn, self.w, 1, "tdd")
        tasks.add_skill_used(self.conn, self.w, 1, "tdd")
        self.assertEqual(json.loads(tasks.get_task(self.conn, self.w, 1)["skills_used"]), ["tdd"])


class AssignTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_assign_and_take_launch(self):
        tasks.assign(self.conn, self.w, 1, implementer="tg-7-t1", agent_type="tollgate:implementer",
                     pending="launch", now=T0)
        self.assertIsNone(tasks.take_pending(self.conn, self.w, agent_type="general-purpose",
                                             resume=False))
        self.assertIsNone(tasks.take_pending(self.conn, self.w, agent_type="tollgate:implementer",
                                             resume=True))
        self.assertEqual(tasks.take_pending(self.conn, self.w, agent_type="tollgate:implementer",
                                            resume=False), 1)
        self.assertIsNone(tasks.get_task(self.conn, self.w, 1)["pending"])

    def test_assign_rejects_unknown_pending(self):
        with self.assertRaises(ValueError):
            tasks.assign(self.conn, self.w, 1, implementer="x", agent_type="y", pending="boh",
                         now=T0)

    def test_add_commit_dedup(self):
        tasks.add_commit(self.conn, self.w, 1, "abc")
        tasks.add_commit(self.conn, self.w, 1, "abc")
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["commits"], '["abc"]')
