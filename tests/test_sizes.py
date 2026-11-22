import json
import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_analysis import worksize
from tollgate_analysis.worksize import Signals
from tollgate_core import db, phases, sizes

T0 = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)


class SizesTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def row(self):
        return phases.get_work(self.conn, self.w)

    def events(self):
        return [json.loads(r[0]) for r in self.conn.execute(
            "SELECT data FROM events WHERE type = 'size_decided' ORDER BY seq")]

    def decide(self, signals, **kw):
        return sizes.decide(self.conn, self.w, signals, now=T0, **kw)

    def test_decide_records_event_and_sets_size(self):
        self.decide(Signals("L1", 0, 0, 1), cause="start")
        row = self.row()
        self.assertEqual((row["size"], row["size_by"]), ("small", "rules"))
        (ev,) = self.events()
        self.assertEqual((ev["proposed"], ev["applied"], ev["cause"], ev["by"]),
                         ("small", "small", "start", "rules"))
        self.assertIsNone(ev["previous"])
        self.assertIsNone(ev["confirmed"])
        self.assertEqual(ev["signals"], {"level": "L1", "tasks": 0, "areas": 0, "slices": 1})

    def test_never_goes_down(self):
        self.decide(Signals("L1", 5, 1, 1), cause="plan")
        self.decide(Signals("L1", 1, 1, 1), cause="plan")
        self.assertEqual(self.row()["size"], "medium")
        ev = self.events()[-1]
        self.assertEqual((ev["applied"], ev["proposed"], ev["previous"]),
                         ("medium", "small", "medium"))

    def test_large_needs_a_yes(self):
        line = self.decide(Signals("L1", 1, 1, 3), cause="plan")
        self.assertEqual(self.row()["size"], "medium")
        self.assertIn("/tollgate:approve spec", line)
        self.decide(Signals("L1", 0, 0, 3), cause="approve_spec", confirmed=True)
        self.assertEqual(self.row()["size"], "large")
        self.assertIs(self.events()[-1]["confirmed"], True)

    def test_user_size_is_fixed(self):
        self.decide(Signals("L1", 5, 1, 1), cause="plan")
        sizes.set_by_user(self.conn, self.w, "small", "motivo", now=T0)
        row = self.row()
        self.assertEqual((row["size"], row["size_by"]), ("small", "user"))
        ev = self.events()[-1]
        self.assertEqual((ev["cause"], ev["by"], ev["confirmed"]), ("act", "user", True))
        self.decide(Signals("L1", 5, 1, 1), cause="plan")
        self.assertEqual(self.row()["size"], "small")
        ev = self.events()[-1]
        self.assertEqual((ev["proposed"], ev["applied"], ev["by"]), ("medium", "small", "user"))
        self.decide(Signals("L2", 0, 0, 3), cause="approve_spec", confirmed=True)
        self.assertEqual(self.row()["size"], "large")

    def test_yes_on_slices_returns_user_size_to_rules(self):
        sizes.set_by_user(self.conn, self.w, "large", "motivo", now=T0)
        self.assertEqual(self.row()["size_by"], "user")
        self.decide(Signals("L2", 0, 0, 2), cause="approve_spec", confirmed=True)
        row = self.row()
        self.assertEqual((row["size"], row["size_by"]), ("large", "rules"))
        ev = self.events()[-1]
        self.assertEqual((ev["by"], ev["confirmed"]), ("rules", True))

    def test_decide_rejects_unknown_cause(self):
        for cause in ("altro", "act"):
            with self.assertRaises(ValueError):
                self.decide(Signals("L1", 0, 0, 1), cause=cause)
        self.assertEqual(self.events(), [])

    def test_set_by_user_rejects_unknown_size(self):
        with self.assertRaises(ValueError):
            sizes.set_by_user(self.conn, self.w, "enorme", "x", now=T0)

    def test_decide_line_equals_preview(self):
        cases = [(Signals("L1", 0, 0, 1), "start"), (Signals("L1", 1, 1, 3), "plan"),
                 (Signals("L2", 5, 2, 1), "level")]
        for signals, cause in cases:
            row = self.row()
            expected = worksize.preview(signals, row["size"], row["size_by"], cause=cause).line
            self.assertEqual(self.decide(signals, cause=cause), expected)

    def test_pre_c1_work_gets_a_size_without_error(self):
        self.assertIsNone(self.row()["size"])
        self.decide(Signals("L1", 2, 1, 1), cause="plan")
        self.assertEqual(self.row()["size"], "small")
        self.assertIsNone(self.events()[0]["previous"])


if __name__ == "__main__":
    unittest.main()
