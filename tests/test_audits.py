import json
import unittest
from datetime import timedelta

from tests.helpers import TempState
from tollgate_core import audits, clock, db, events, phases

T0 = clock.parse("2026-10-20T10:00:00.000000Z")
COUNTS = {"blocker": 0, "major": 0, "moderate": 0, "minor": 0}


class AuditsCase(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L2", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def open(self, kind="spec-adversarial", viewpoint=None, sha="s1", at=T0):
        return audits.open_round(self.conn, self.w, kind=kind, sha=sha, spec_sha="s1",
                                 viewpoint=viewpoint, code="abcd1234", now=at)

    def close(self, kind, number, outcome="empty", counts=COUNTS):
        audits.close_round(self.conn, self.w, kind=kind, number=number, counts=counts,
                           outcome=outcome, report_path=f"r/{kind}-{number}.md", now=T0)


class RoundsTest(AuditsCase):
    def test_open_one_at_a_time(self):
        n = self.open()
        self.assertEqual(n, 1)
        row = audits.open_round_row(self.conn, self.w)
        self.assertEqual((row["kind"], row["number"], row["stage"], row["code"], row["sha"],
                          row["spec_sha"], row["opened"]),
                         ("spec-adversarial", 1, "open", "abcd1234", "s1", "s1",
                          clock.fmt(T0)))
        with self.assertRaises(ValueError):
            self.open("spec-lens", "executor")
        self.close("spec-adversarial", 1)
        self.assertIsNone(audits.open_round_row(self.conn, self.w))
        self.assertEqual(self.open("spec-lens", "executor"), 1)

    def test_min_number_raises_the_number(self):
        """`min_number` dà il numero minimo (report già nel ramo): vince il più alto."""
        kw = dict(kind="spec-adversarial", sha="s1", spec_sha="s1", viewpoint=None,
                  code="abcd1234", now=T0)
        self.assertEqual(audits.open_round(self.conn, self.w, min_number=3, **kw), 3)
        self.close("spec-adversarial", 3)
        self.assertEqual(audits.open_round(self.conn, self.w, min_number=2, **kw), 4)
        self.close("spec-adversarial", 4)
        self.assertEqual(audits.open_round(self.conn, self.w, **kw), 5)

    def test_unknown_kind_refused(self):
        with self.assertRaises(ValueError):
            self.open("altro")

    def test_close_and_last_closed_any_kind(self):
        kinds = audits.KINDS
        self.assertIsNone(audits.last_closed(self.conn, self.w, kinds))
        self.open()
        self.assertIsNone(audits.last_closed(self.conn, self.w, kinds))  # aperto: non conta
        self.close("spec-adversarial", 1, "findings", {**COUNTS, "major": 2})
        self.open("spec-lens", "executor")
        self.close("spec-lens", 1)
        last = audits.last_closed(self.conn, self.w, kinds)
        self.assertEqual((last["kind"], last["outcome"], last["report_path"], last["stage"]),
                         ("spec-lens", "empty", "r/spec-lens-1.md", "closed"))
        self.assertEqual(json.loads(last["counts"]), COUNTS)
        only = audits.last_closed(self.conn, self.w, ("spec-adversarial",))
        self.assertEqual((only["kind"], json.loads(only["counts"])["major"]),
                         ("spec-adversarial", 2))
        self.assertIsNone(audits.last_closed(self.conn, self.w, ("plan-adversarial",)))
        self.assertIsNone(audits.last_closed(self.conn, self.w, ()))

    def test_close_emits_event_and_needs_open_round(self):
        self.open("spec-lens", "user")
        self.close("spec-lens", 1, "findings")
        ev = [e for e in events.export_events(self.conn, 0) if e["type"] == "spec_audit_round"]
        self.assertEqual([e["data"] for e in ev], [
            {"kind": "spec-lens", "number": 1, "viewpoint": "user", "outcome": "findings"}])
        with self.assertRaises(ValueError):
            self.close("spec-lens", 1)

    def test_superseded_not_in_rounds(self):
        self.open()
        self.close("spec-adversarial", 1, "findings")
        self.open(sha="s2", at=T0 + timedelta(seconds=5))
        audits.supersede(self.conn, self.w, ("spec-adversarial", 2), now=T0)
        self.assertEqual([r["number"] for r in audits.rounds(self.conn, self.w,
                                                             "spec-adversarial")], [1])
        self.assertIsNone(audits.open_round_row(self.conn, self.w))
        self.assertTrue(audits.any_rows(self.conn, self.w, "spec-adversarial"))
        self.assertFalse(audits.any_rows(self.conn, self.w, "spec-lens"))
        # un giro chiuso non diventa superseded
        audits.supersede(self.conn, self.w, ("spec-adversarial", 1), now=T0)
        self.assertEqual(len(audits.rounds(self.conn, self.w, "spec-adversarial")), 1)

    def test_last_closed_never_returns_superseded(self):
        self.open()
        self.close("spec-adversarial", 1, "findings")
        self.open(sha="s2")
        audits.supersede(self.conn, self.w, ("spec-adversarial", 2), now=T0)
        last = audits.last_closed(self.conn, self.w, ("spec-adversarial",))
        self.assertEqual((last["number"], last["outcome"]), (1, "findings"))

    def test_any_rows_counts_open_row(self):
        self.open("spec-lens", "executor")
        self.assertTrue(audits.any_rows(self.conn, self.w, "spec-lens"))

    def test_numbers_per_kind(self):
        self.assertEqual(self.open(), 1)
        self.close("spec-adversarial", 1)
        self.assertEqual(self.open("spec-lens", "executor"), 1)
        self.close("spec-lens", 1)
        self.assertEqual(self.open(), 2)
        audits.supersede(self.conn, self.w, ("spec-adversarial", 2), now=T0)
        self.assertEqual(self.open(), 3)  # il numero di un giro superato non si riusa

    def test_numbers_are_per_work(self):
        self.open()
        other = phases.create_work(self.conn, repo_key="r", issue=8, level="L2", now=T0)
        self.assertEqual(audits.open_round(self.conn, other, kind="spec-adversarial", sha="x",
                                           spec_sha="x", viewpoint=None, code="c", now=T0), 1)


class SuspendTest(AuditsCase):
    def test_suspend_roundtrip(self):
        self.assertEqual(audits.suspended(self.conn, self.w), {})
        audits.suspend(self.conn, self.w, "spec-adversarial", 4, now=T0)
        audits.suspend(self.conn, self.w, "spec-lens", 0, now=T0)
        got = audits.suspended(self.conn, self.w)
        self.assertEqual(got, {"spec-adversarial": 4, "spec-lens": 0})
        self.assertIn("spec-lens", got)  # il numero 0 è una sospensione vera
        self.assertNotIn("plan-adversarial", got)
        audits.suspend(self.conn, self.w, "spec-adversarial", 6, now=T0)
        self.assertEqual(audits.suspended(self.conn, self.w)["spec-adversarial"], 6)
        with self.assertRaises(ValueError):
            audits.suspend(self.conn, self.w, "altro", 1, now=T0)

    def test_labels_cover_every_kind(self):
        self.assertEqual(set(audits.SUSPENDED_LABELS), set(audits.KINDS))
        self.assertEqual(set(audits.AGENTS), set(audits.KINDS))
        self.assertEqual(set(audits.COMPONENTS), set(audits.KINDS))


class CapReasonTest(unittest.TestCase):
    def test_cap_reason_texts(self):
        self.assertEqual(audits.cap_reason("spec-adversarial", 4),
                         "giri avversariali della spec esauriti (giro 4)")
        self.assertEqual(audits.cap_reason("plan-adversarial", 2),
                         "giri avversariali del piano esauriti (giro 2)")
        self.assertEqual(audits.cap_reason("spec-lens", 30),
                         "audit a lenti: tetto di cicli raggiunto")

    def test_cap_kind_from_reasons(self):
        for kind in audits.KINDS:
            self.assertEqual(audits.cap_kind(audits.cap_reason(kind, 3)), kind)
        self.assertEqual(audits.cap_kind(audits.DECLINE_REASON), "spec-lens")
        self.assertIsNone(audits.cap_kind("un altro motivo"))
        self.assertIsNone(audits.cap_kind(""))


if __name__ == "__main__":
    unittest.main()
