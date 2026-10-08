import itertools
import json
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases
from tollgate_core.phases import TransitionError

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
OPEN_PHASES = ["spec_audit", "plan", "approval", "execution", "review", "pr_open"]
CAUSES = ["advance", "finish_check_green", "needs_fix", "start", "sync", "reopen_spec",
          "reopen_plan", "l0_grew", "merged"]
BACK = {("review", "execution", "needs_fix"), ("review", "execution", "start"),
        ("pr_open", "execution", "start"), ("pr_open", "execution", "sync")}
EXPECTED = {
    "L0": {("execution", "review", "finish_check_green"), ("review", "pr_open", "advance"),
           ("execution", "plan", "l0_grew")} | BACK,
    "L1": {("plan", "execution", "advance"), ("execution", "review", "finish_check_green"),
           ("review", "pr_open", "advance"), ("execution", "plan", "reopen_plan")} | BACK,
    "L2": {("spec_audit", "plan", "advance"), ("plan", "approval", "advance"),
           ("approval", "execution", "advance"), ("execution", "review", "finish_check_green"),
           ("review", "pr_open", "advance"),
           ("plan", "spec_audit", "reopen_spec"), ("approval", "spec_audit", "reopen_spec"),
           ("execution", "spec_audit", "reopen_spec"),
           ("approval", "plan", "reopen_plan"), ("execution", "plan", "reopen_plan")} | BACK,
}


class CheckTransitionTest(unittest.TestCase):
    """Criterio 25: ogni transizione fuori da 12.3 è rifiutata."""

    def test_table_is_exact(self):
        for level, expected in EXPECTED.items():
            allowed = set()
            for frm, to, cause in itertools.product(OPEN_PHASES, OPEN_PHASES, CAUSES):
                try:
                    phases.check_transition(level, frm, to, cause)
                    allowed.add((frm, to, cause))
                except TransitionError:
                    pass
            with self.subTest(level=level):
                self.assertEqual(allowed, expected)

    def test_closed(self):
        for frm in OPEN_PHASES + ["blocked"]:
            for cause in ("merged", "closed_unmerged", "abandoned"):
                phases.check_transition("L1", frm, "closed", cause)
            with self.assertRaises(TransitionError):
                phases.check_transition("L1", frm, "closed", "advance")
        with self.assertRaises(TransitionError):
            phases.check_transition("L1", "closed", "plan", "start")

    def test_blocked_only_through_blocks(self):
        with self.assertRaises(TransitionError):
            phases.check_transition("L1", "plan", "blocked", "advance")
        with self.assertRaises(TransitionError):
            phases.check_transition("L1", "blocked", "plan", "advance")


class WorkTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def new(self, level="L1", issue=7, **kw):
        return phases.create_work(self.conn, repo_key="github.com/o/r", issue=issue,
                                  level=level, now=T0, session="s1", **kw)

    def backups(self):
        return len(list(self.t.state.backup_dir.glob("*.db")))

    def test_initial_phases(self):
        self.assertEqual(phases.get_work(self.conn, self.new("L0", 1))["phase"], "execution")
        self.assertEqual(phases.get_work(self.conn, self.new("L1", 2))["phase"], "plan")
        self.assertEqual(phases.get_work(self.conn, self.new("L2", 3))["phase"], "spec_audit")
        w = self.new("L2", 4, spec_path="docs/s.md", from_approved_spec=True)
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "plan")
        first = events.export_events(self.conn, 0)[0]
        self.assertEqual(first["type"], "phase_change")
        self.assertEqual(first["data"], {"from": None, "to": "execution", "cause": "start"})

    def test_sessions_and_duplicates(self):
        w = self.new()
        self.assertEqual(json.loads(phases.get_work(self.conn, w)["sessions"]), ["s1"])
        phases.bind_session(self.conn, w, "s2", now=T0)
        phases.bind_session(self.conn, w, "s2", now=T0)
        self.assertEqual(json.loads(phases.get_work(self.conn, w)["sessions"]), ["s1", "s2"])
        with self.assertRaises(phases.WorkExists):
            self.new()
        self.assertEqual(phases.find_active(self.conn, "github.com/o/r", 7)["id"], w)

    def test_set_phase_records_and_backs_up(self):
        w = self.new()
        phases.set_phase(self.conn, self.t.state, w, "execution", "advance", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "execution")
        self.assertEqual(self.backups(), 1)
        last = events.export_events(self.conn, 0)[-1]
        self.assertEqual(last["data"], {"from": "plan", "to": "execution", "cause": "advance"})
        with self.assertRaises(TransitionError):
            phases.set_phase(self.conn, self.t.state, w, "pr_open", "advance", now=T0)
        self.assertEqual(self.backups(), 1)

    def test_set_phase_refuses_open_transaction(self):
        w = self.new()
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                phases.set_phase(self.conn, self.t.state, w, "execution", "advance", now=T0)

    def test_l0_grew(self):
        w = self.new("L0")
        phases.set_phase(self.conn, self.t.state, w, "plan", "l0_grew", now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["phase"], row["level"]), ("plan", "L1"))
        types = [e["type"] for e in events.export_events(self.conn, 0)]
        self.assertIn("level_change", types)

    def test_set_level_only_up(self):
        w = self.new("L1")
        phases.set_level(self.conn, w, "L2", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["level"], "L2")
        with self.assertRaises(TransitionError):
            phases.set_level(self.conn, w, "L1", now=T0)

    def test_closed_then_new_work(self):
        w = self.new()
        phases.set_phase(self.conn, self.t.state, w, "closed", "abandoned", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["closed_reason"], "abandoned")
        self.assertIsNone(phases.find_active(self.conn, "github.com/o/r", 7))
        w2 = self.new()
        self.assertEqual(phases.find_latest(self.conn, "github.com/o/r", 7)["id"], w2)


class BlockTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)
        phases.set_phase(self.conn, self.t.state, self.w, "execution", "advance", now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def phase(self):
        return phases.get_work(self.conn, self.w)["phase"]

    def test_two_blocks_restore_previous_phase(self):
        b1 = phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r1", now=T0)
        b2 = phases.open_block(self.conn, self.t.state, self.w, "transient", "r2", now=T0)
        self.assertEqual(self.phase(), "blocked")
        self.assertEqual(phases.close_block(self.conn, self.t.state, b1, "ok", now=T0), "blocked")
        self.assertEqual(phases.close_block(self.conn, self.t.state, b2, "ok", now=T0),
                         "execution")
        self.assertIsNone(phases.get_work(self.conn, self.w)["phase_before_block"])
        opened = [e for e in events.export_events(self.conn, 0) if e["type"] == "block_opened"]
        self.assertEqual(opened[0]["data"], {"id": b1, "type": "needs_you"})

    def test_close_twice_and_bad_type(self):
        b = phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
        phases.close_block(self.conn, self.t.state, b, "ok", now=T0)
        with self.assertRaises(TransitionError):
            phases.close_block(self.conn, self.t.state, b, "ok", now=T0)
        with self.assertRaises(ValueError):
            phases.open_block(self.conn, self.t.state, self.w, "boh", "r", now=T0)

    def test_set_phase_from_blocked_only_to_closed(self):
        phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
        with self.assertRaises(TransitionError):
            phases.set_phase(self.conn, self.t.state, self.w, "review", "finish_check_green",
                             now=T0)
        phases.set_phase(self.conn, self.t.state, self.w, "closed", "merged", now=T0)
        self.assertEqual(self.phase(), "closed")
        with self.assertRaises(TransitionError):
            phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
