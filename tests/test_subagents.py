import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, subagents, tasks

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class SubagentsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                                    session="s1")
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _start(self, now=T0):
        return subagents.start(self.conn, agent_id="a1", type_="tollgate:implementer",
                               session="s1", work=self.w, task=1, base_sha="b0",
                               fingerprint="f0", now=now)

    def test_start_then_resume_keeps_base(self):
        self.assertFalse(self._start())
        subagents.finish(self.conn, "a1", state="done", declared_status="NEEDS_CONTEXT", now=T0)
        resumed = subagents.start(self.conn, agent_id="a1", type_="tollgate:implementer",
                                  session="s1", work=self.w, task=1, base_sha="b9",
                                  fingerprint="f9", now=T0 + timedelta(minutes=1))
        self.assertTrue(resumed)
        row = subagents.get(self.conn, "a1")
        self.assertEqual((row["agent_base_sha"], row["resumes"], row["state"]), ("b0", 1, "running"))
        self.assertIsNone(row["ended"])

    def test_name_before_start_is_merged(self):
        subagents.set_name(self.conn, "a1", "tg-7-t1", session="s1", work=self.w, now=T0)
        self._start()
        self.assertEqual(subagents.by_name(self.conn, "tg-7-t1", work=self.w)["id"], "a1")

    def test_vetoes_and_report(self):
        self._start()
        self.assertEqual(subagents.add_veto(self.conn, "a1"), 1)
        self.assertEqual(subagents.add_veto(self.conn, "a1"), 2)
        subagents.set_report(self.conn, "a1", "testo")
        self.assertEqual(subagents.get(self.conn, "a1")["report"], "testo")

    def test_interrupt_returns_running_task_to_pending(self):
        tasks.task_event(self.conn, self.w, 1, "start", now=T0)
        self._start()
        subagents.interrupt(self.conn, "a1", now=T0 + timedelta(hours=1))
        self.assertEqual(subagents.get(self.conn, "a1")["state"], "interrupted")
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["state"], "pending")
        self.assertEqual(subagents.running(self.conn, work=self.w), [])

    def test_finish_records_event(self):
        self._start()
        subagents.finish(self.conn, "a1", state="done", declared_status="DONE", tokens=123, now=T0)
        ev = self.conn.execute("SELECT data FROM events WHERE type='subagent_stop'").fetchone()
        self.assertIn('"tokens": 123', ev["data"])

    def test_unknown_state_rejected(self):
        self._start()
        with self.assertRaises(ValueError):
            subagents.finish(self.conn, "a1", state="boh", now=T0)


if __name__ == "__main__":
    unittest.main()
