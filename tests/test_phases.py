import itertools
import json
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases
from tollgate_core.phases import TransitionError

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
OPEN_PHASES = ["spec_audit", "plan", "approval", "execution", "review", "pr_open"]
CAUSES = ["advance", "finish_check_green", "needs_fix", "start", "sync", "reopen_spec",
          "reopen_plan", "l0_grew", "merged", "approve_spec", "audit_clean", "approve_plan"]
BACK = {("review", "execution", "needs_fix"), ("review", "execution", "start"),
        ("pr_open", "execution", "start"), ("pr_open", "execution", "sync")}
EXPECTED = {
    "L0": {("execution", "review", "finish_check_green"), ("review", "pr_open", "advance"),
           ("execution", "plan", "l0_grew")} | BACK,
    "L1": {("plan", "execution", "advance"), ("execution", "review", "finish_check_green"),
           ("review", "pr_open", "advance"), ("execution", "plan", "reopen_plan")} | BACK,
    "L2": {("spec_audit", "plan", "approve_spec"), ("plan", "approval", "audit_clean"),
           ("approval", "execution", "approve_plan"), ("execution", "review", "finish_check_green"),
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

    def test_l2_forward_needs_its_cause(self):
        for frm, to in (("spec_audit", "plan"), ("plan", "approval"), ("approval", "execution")):
            with self.assertRaises(TransitionError):
                phases.check_transition("L2", frm, to, "advance")

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

    def test_create_work_research_flag(self):
        a = self.new(issue=11)
        b = self.new(issue=12, research=True)
        self.assertEqual(phases.get_work(self.conn, a)["research"], 0)
        self.assertEqual(phases.get_work(self.conn, b)["research"], 1)

    def test_sessions_and_duplicates(self):
        w = self.new()
        self.assertEqual(json.loads(phases.get_work(self.conn, w)["sessions"]), ["s1"])
        phases.bind_session(self.conn, w, "s2", now=T0)
        phases.bind_session(self.conn, w, "s2", now=T0)
        self.assertEqual(json.loads(phases.get_work(self.conn, w)["sessions"]), ["s1", "s2"])
        with self.assertRaises(phases.WorkExists):
            self.new()
        self.assertEqual(phases.find_active(self.conn, "github.com/o/r", 7)["id"], w)

    def test_set_worktree(self):
        w = self.new("L0", worktree="/tmp/a")
        phases.set_worktree(self.conn, w, "/tmp/b", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["worktree"], "/tmp/b")
        with self.assertRaises(ValueError):
            phases.set_worktree(self.conn, 999, "/tmp/c", now=T0)

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

    def test_bind_and_set_level_refuse_closed(self):
        w = self.new()
        phases.set_phase(self.conn, self.t.state, w, "closed", "abandoned", now=T0)
        with self.assertRaisesRegex(TransitionError, "chiuso"):
            phases.bind_session(self.conn, w, "s2", now=T0)
        with self.assertRaisesRegex(TransitionError, "chiuso"):
            phases.set_level(self.conn, w, "L2", now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((json.loads(row["sessions"]), row["level"]), (["s1"], "L1"))

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

    def test_closing_work_closes_its_open_blocks(self):
        b1 = phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r1", now=T0)
        b2 = phases.open_block(self.conn, self.t.state, self.w, "transient", "r2", now=T0)
        before = len([e for e in events.export_events(self.conn, 0)
                      if e["type"] == "block_closed"])
        phases.set_phase(self.conn, self.t.state, self.w, "closed", "merged", now=T0)
        rows = self.conn.execute("SELECT * FROM blocks WHERE work = ?", (self.w,)).fetchall()
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertIsNotNone(r["closed"])
            self.assertEqual(r["resolution"], "lavoro chiuso: merged")
        self.assertIsNone(phases.get_work(self.conn, self.w)["phase_before_block"])
        closed = [e for e in events.export_events(self.conn, 0) if e["type"] == "block_closed"]
        self.assertEqual(len(closed), before + 2)
        self.assertEqual({e["data"]["id"] for e in closed[before:]}, {b1, b2})

    def test_set_phase_from_blocked_only_to_closed(self):
        phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
        with self.assertRaises(TransitionError):
            phases.set_phase(self.conn, self.t.state, self.w, "review", "finish_check_green",
                             now=T0)
        phases.set_phase(self.conn, self.t.state, self.w, "closed", "merged", now=T0)
        self.assertEqual(self.phase(), "closed")
        with self.assertRaises(TransitionError):
            phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)


class LevelCapTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def new(self, level, phase, issue=1):
        w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=issue, level=level,
                               now=T0)
        seq = phases.SEQUENCES[level]
        while phases.get_work(self.conn, w)["phase"] != phase:
            cur = phases.get_work(self.conn, w)["phase"]
            nxt = seq[seq.index(cur) + 1]
            cause = phases._FORWARD_CONDITION.get((cur, nxt), "advance")
            phases.set_phase(self.conn, self.t.state, w, nxt, cause, now=T0)
        return w

    def level_changes(self):
        return [e["data"] for e in events.export_events(self.conn, 0)
                if e["type"] == "level_change"]

    def test_cap_lowers_level_and_records_paths(self):
        w = self.new("L2", "execution")
        phases.set_level_cap(self.conn, w, "L1", "solo un rinomino", ["src/auth/x.py"],
                             now=T0, session="s1")
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["level"], row["phase"], row["level_cap"], row["level_cap_reason"]),
                         ("L1", "execution", "L1", "solo un rinomino"))
        self.assertEqual(json.loads(row["level_cap_paths"]), ["src/auth/x.py"])
        self.assertEqual(self.level_changes()[-1], {"from": "L2", "to": "L1", "cause": "cap"})

    def test_cap_above_level_keeps_level(self):
        w = self.new("L1", "execution")
        phases.set_level_cap(self.conn, w, "L2", "ok", [], now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["level"], row["level_cap"]), ("L1", "L2"))
        self.assertEqual(self.level_changes(), [])

    def test_cap_refused_when_phase_not_in_target_sequence(self):
        w = self.new("L2", "spec_audit")
        with self.assertRaises(TransitionError):
            phases.set_level_cap(self.conn, w, "L1", "motivo", [], now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["level"], row["level_cap"]), ("L2", None))

    def test_cap_in_blocked_uses_phase_before_block(self):
        w = self.new("L2", "spec_audit")
        phases.open_block(self.conn, self.t.state, w, "needs_you", "r", now=T0)
        with self.assertRaises(TransitionError):
            phases.set_level_cap(self.conn, w, "L1", "motivo", [], now=T0)
        w2 = self.new("L2", "execution", issue=2)
        phases.open_block(self.conn, self.t.state, w2, "needs_you", "r", now=T0)
        phases.set_level_cap(self.conn, w2, "L1", "motivo", [], now=T0)
        row = phases.get_work(self.conn, w2)
        self.assertEqual((row["level"], row["phase"]), ("L1", "blocked"))

    def test_cap_on_closed_work_refused(self):
        w = self.new("L1", "execution")
        phases.set_phase(self.conn, self.t.state, w, "closed", "abandoned", now=T0)
        with self.assertRaises(TransitionError):
            phases.set_level_cap(self.conn, w, "L0", "motivo", [], now=T0)

    def test_unknown_cap_refused(self):
        w = self.new("L1", "execution")
        with self.assertRaises(ValueError):
            phases.set_level_cap(self.conn, w, "L9", "motivo", [], now=T0)


class WorkCase(unittest.TestCase):
    """Base senza test propri: DB temporaneo e `new` per le classi di P3b."""

    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def new(self, level="L1", issue=7, **kw):
        return phases.create_work(self.conn, repo_key="github.com/o/r", issue=issue,
                                  level=level, now=T0, session="s1", **kw)


class CreateWorkPhaseTest(WorkCase):
    def test_phase_adopt_in_l2(self):
        w = self.new("L2", phase="execution", cause="adopt")
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "execution")
        e = [x for x in events.export_events(self.conn, 0) if x["type"] == "phase_change"]
        self.assertEqual(e[0]["data"], {"from": None, "to": "execution", "cause": "adopt"})

    def test_default_cause_is_start(self):
        w = self.new("L1")
        e = [x for x in events.export_events(self.conn, 0) if x["type"] == "phase_change"]
        self.assertEqual((e[0]["data"]["to"], e[0]["data"]["cause"]), ("plan", "start"))
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "plan")

    def test_closed_refused(self):
        with self.assertRaises(ValueError):
            self.new("L1", phase="closed")

    def test_phase_outside_sequence_refused(self):
        with self.assertRaises(ValueError):
            self.new("L1", phase="spec_audit")
        with self.assertRaises(ValueError):
            self.new("L0", phase="plan")

    def test_phase_and_approved_spec_are_exclusive(self):
        with self.assertRaises(ValueError):
            self.new("L2", phase="plan", from_approved_spec=True, spec_path="s.md")

    def test_from_approved_spec_requires_spec_path(self):
        with self.assertRaisesRegex(ValueError, "from_approved_spec richiede spec_path"):
            self.new("L2", from_approved_spec=True)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)
        w = self.new("L2", from_approved_spec=True, spec_path="docs/superpowers/specs/s.md")
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "plan")

    def test_set_spec_path_only_once(self):
        w = self.new("L2")
        phases.set_spec_path(self.conn, w, "docs/superpowers/specs/a.md", now=T0)
        phases.set_spec_path(self.conn, w, "docs/superpowers/specs/b.md", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["spec_path"],
                         "docs/superpowers/specs/a.md")

    def test_refused_phase_creates_nothing(self):
        with self.assertRaises(ValueError):
            self.new("L1", phase="closed")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)


class SetBaseTest(WorkCase):
    def test_set_base_records_event(self):
        w = self.new("L1", work_base_sha="aaa")
        phases.set_base(self.conn, w, "bbb", cause="sync", now=T0, session="s1")
        self.assertEqual(phases.get_work(self.conn, w)["work_base_sha"], "bbb")
        e = [x for x in events.export_events(self.conn, 0) if x["type"] == "base_realigned"]
        self.assertEqual(e[0]["data"], {"from": "aaa", "to": "bbb", "cause": "sync"})
        self.assertEqual(e[0]["session"], "s1")


class ClosingDataTest(WorkCase):
    def test_set_pr_and_reset(self):
        w = self.new("L1")
        phases.set_pr(self.conn, w, 12, "https://github.com/o/r/pull/12", now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["pr_number"], row["pr_url"]),
                         (12, "https://github.com/o/r/pull/12"))
        phases.set_pr(self.conn, w, None, None, now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["pr_number"], row["pr_url"]), (None, None))

    def test_set_finish_stores_report_as_json(self):
        w = self.new("L1")
        phases.set_finish(self.conn, w, "abc", {"receipt": True, "findings": None}, now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual(row["finish_sha"], "abc")
        self.assertEqual(json.loads(row["finish_report"]), {"receipt": True, "findings": None})
        phases.set_finish(self.conn, w, None, None, now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["finish_sha"], row["finish_report"]), (None, None))

    def test_add_extra_cycles_returns_total(self):
        w = self.new("L1")
        self.assertEqual(phases.add_extra_cycles(self.conn, w, 2, now=T0), 2)
        self.assertEqual(phases.add_extra_cycles(self.conn, w, 1, now=T0), 3)
        self.assertEqual(phases.get_work(self.conn, w)["extra_review_cycles"], 3)

    def test_set_review_unverified(self):
        w = self.new("L1")
        self.assertEqual(phases.get_work(self.conn, w)["review_unverified"], 0)
        phases.set_review_unverified(self.conn, w, now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["review_unverified"], 1)

    def test_unknown_work_refused(self):
        with self.assertRaises(ValueError):
            phases.set_pr(self.conn, 99, 1, "u", now=T0)
