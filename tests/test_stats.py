import unittest
from datetime import timedelta

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases, stats

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


def h(hours):
    return T0 + timedelta(hours=hours)


class StatsTest(unittest.TestCase):
    """Criterio 43: due veti, un needs_you e un'ora di OFF, più tempo per fase e token."""

    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        c, st = self.conn, self.t.state
        self.w = phases.create_work(c, repo_key="github.com/o/r", issue=5, level="L1", now=T0)
        phases.set_phase(c, st, self.w, "execution", "advance", now=h(1))
        events.record_event(c, "veto", {"event": "pre_edit", "rule": "scope", "reason": "x"},
                            now=h(1.5), work=self.w)
        events.record_event(c, "veto", {"event": "pre_bash", "rule": "effects", "reason": "y"},
                            now=h(1.6), work=self.w)
        b = phases.open_block(c, st, self.w, "needs_you", "budget", now=h(2))
        phases.close_block(c, st, b, "diviso", now=h(2.5))
        events.record_event(c, "off", {}, now=h(3))
        events.record_event(c, "on", {}, now=h(4))
        events.record_event(c, "subagent_stop", {"id": "a1", "type": "tollgate:implementer",
                                                 "task": 1, "declared_status": "DONE",
                                                 "tokens": 1000}, now=h(4.5), work=self.w)
        events.record_event(c, "subagent_stop", {"id": "a2", "type": "tollgate:task-reviewer",
                                                 "task": 1, "declared_status": None,
                                                 "tokens": 300}, now=h(4.6), work=self.w)
        for fr in (0, 1, 2):
            events.record_event(c, "task_change", {"number": 1, "kind": "plan",
                                                   "state": "running", "fix_rounds": fr,
                                                   "verdict": None}, now=h(4.7), work=self.w)
        events.record_event(c, "waiver_added", {}, now=h(4.8), work=self.w)
        events.record_event(c, "act", {"act_id": "a-9", "type": "approve", "object": "finding",
                                       "target": "f-1-1", "args": [], "source": "claude-code",
                                       "actor": None}, now=h(4.9), work=self.w)
        events.record_event(c, "review_cycle", {"number": 1, "outcome": "ok",
                                                "findings_confirmed": 0}, now=h(5), work=self.w)
        phases.set_phase(c, st, self.w, "closed", "merged", now=h(6))
        events.record_event(c, "off", {}, now=h(7))

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_work_numbers(self):
        s = stats.compute_stats(self.conn, now=h(10), work=self.w)
        self.assertEqual(s["vetoes"], {"total": 2, "by_rule": {"scope": 1, "effects": 1}})
        self.assertEqual(s["needs_you"], 1)
        self.assertEqual(s["blocks"], 1)
        self.assertEqual(s["off_hours"], 1.0)
        self.assertEqual(s["phase_hours"], {"plan": 1.0, "execution": 4.5, "blocked": 0.5})
        self.assertEqual(s["tokens"], {"total": 1300, "by_agent": {"tollgate:implementer": 1000,
                                                                   "tollgate:task-reviewer": 300}})
        self.assertEqual(s["fix_rounds"], 2)
        self.assertEqual(s["waivers"], 1)
        self.assertEqual(s["finding_overrides"], 1)
        self.assertEqual(s["review_cycles"], 1)

    def test_global_window_counts_open_off(self):
        s = stats.compute_stats(self.conn, now=h(10))
        self.assertEqual(s["off_hours"], 4.0)
        self.assertEqual(s["vetoes"]["total"], 2)

    def test_since(self):
        s = stats.compute_stats(self.conn, now=h(10), since=h(1.55))
        self.assertEqual(s["vetoes"], {"total": 1, "by_rule": {"effects": 1}})
        self.assertEqual(s["off_hours"], 4.0)
