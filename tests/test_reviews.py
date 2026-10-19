import json
import unittest

from tests.helpers import TempState
from tollgate_analysis import verdicts
from tollgate_core import clock, db, events, phases, reviews

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
REVIEWER = "tollgate:final-reviewer"
SPECIALIST = "tollgate:final-web"


def finding(severity="major", rule="R-1", **kw):
    f = {"severity": severity, "confidence": 0.9, "file": "src/app.py", "line": 2, "rule": rule,
         "text": "manca il caso zero"}
    f.update(kw)
    return f


class ReviewsCase(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)
        self.goto("review")

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def goto(self, phase):
        seq = phases.SEQUENCES["L1"]
        while phases.get_work(self.conn, self.w)["phase"] != phase:
            cur = phases.get_work(self.conn, self.w)["phase"]
            nxt = seq[seq.index(cur) + 1]
            cause = phases._FORWARD_CONDITION.get((cur, nxt), "advance")
            phases.set_phase(self.conn, self.t.state, self.w, nxt, cause, now=T0)

    def phase(self):
        return phases.get_work(self.conn, self.w)["phase"]

    def open(self, reviewers=(REVIEWER,), sha="s1"):
        return reviews.open_cycle(self.conn, self.w, sha=sha, patch_id="p1", code="c0de",
                                  reviewers=list(reviewers), now=T0)

    def report(self, cycle, findings=(), *, source=REVIEWER, outcome="ok", rejected=(),
               blocking_rules=frozenset(), known_rules=frozenset()):
        return reviews.add_report(self.conn, self.w, cycle, source=source, outcome=outcome,
                                  findings=list(findings), rejected=list(rejected),
                                  blocking_rules=set(blocking_rules),
                                  known_rules=set(known_rules), now=T0)

    def confirm_all(self, cycle, **kw):
        rows = reviews.to_verify(self.conn, self.w, cycle, max_findings=15, now=T0)
        reviews.apply_verification(
            self.conn, self.w, cycle,
            [{"id": r["id"], "verification": "confirmed", "reason": "ok"} for r in rows], now=T0)

    def counted_cycle(self, n_expected):
        """Un ciclo con un major confermato, chiuso; poi di nuovo in review se serve."""
        c = self.open(sha=f"s{n_expected}")
        self.assertEqual(c, n_expected)
        self.report(c, [finding()], outcome="needs_fix")
        self.confirm_all(c)
        return reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0)

    def finding_row(self, fid):
        return self.conn.execute("SELECT * FROM findings WHERE work = ? AND id = ?",
                                 (self.w, fid)).fetchone()


class CycleTest(ReviewsCase):
    def test_open_and_report_moves_to_verify(self):
        self.assertIsNone(reviews.latest(self.conn, self.w))
        c = self.open(reviewers=[REVIEWER, SPECIALIST])
        self.assertEqual((c, reviews.count(self.conn, self.w), reviews.counted(self.conn, self.w)),
                         (1, 1, 0))
        row = reviews.latest(self.conn, self.w)
        self.assertEqual((row["stage"], row["code"], row["sha"], row["patch_id"]),
                         ("review", "c0de", "s1", "p1"))
        self.assertEqual(json.loads(row["reviewers"]), [REVIEWER, SPECIALIST])
        self.assertEqual(self.report(c, [finding()], outcome="needs_fix"), "review")
        self.assertEqual(self.report(c, [finding("minor", "R-2")], source=SPECIALIST), "verify")
        row = reviews.latest(self.conn, self.w)
        self.assertEqual(row["stage"], "verify")
        self.assertEqual(json.loads(row["reported"]), {REVIEWER: "needs_fix", SPECIALIST: "ok"})
        ids = [r["id"] for r in self.conn.execute(
            "SELECT id FROM findings WHERE work = ? ORDER BY rowid", (self.w,))]
        self.assertEqual(ids, ["f-1-1", "f-1-2"])
        self.assertEqual(self.finding_row("f-1-2")["source"], SPECIALIST)

    def test_cycle_numbers_increase(self):
        self.assertEqual(self.open(), 1)
        reviews.supersede(self.conn, self.w, 1, now=T0)
        self.assertEqual(self.open(sha="s2"), 2)
        self.assertEqual(reviews.latest(self.conn, self.w)["number"], 2)

    def test_report_from_unexpected_or_repeated_source_refused(self):
        c = self.open()
        with self.assertRaises(ValueError):
            self.report(c, source="tollgate:altro")
        self.report(c)
        with self.assertRaises(ValueError):
            self.report(c)

    def test_report_on_closed_cycle_refused(self):
        c = self.open()
        self.report(c)
        reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0)
        with self.assertRaises(ValueError):
            self.report(c)

    def test_rejected_without_proof(self):
        c = self.open()
        self.report(c, [], rejected=[{"severity": "major", "text": "vago"}])
        row = self.finding_row("f-1-1")
        self.assertEqual(row["verification"], "rejected")
        self.assertIn("senza prova", row["verification_reason"])
        self.assertIsNone(row["rule"])
        self.assertEqual(reviews.to_verify(self.conn, self.w, c, max_findings=15, now=T0), [])

    def test_rejected_are_normalized(self):
        c = self.open()
        self.report(c, [], rejected=[
            {"severity": "critical", "line": "2", "file": 3, "rule": ["x"], "text": "t" * 5000},
            {"severity": "minor", "line": True, "file": "a.py", "rule": "R-1", "text": "ok"}])
        a, b = self.finding_row("f-1-1"), self.finding_row("f-1-2")
        self.assertEqual((a["severity"], a["line"], a["file"], a["rule"]),
                         (None, None, None, None))
        self.assertEqual(len(a["text"]), 2000)
        self.assertEqual((b["severity"], b["line"], b["file"], b["rule"], b["text"]),
                         ("minor", None, "a.py", "R-1", "ok"))

    def test_blocking_flag_follows_rules(self):
        c = self.open()
        self.report(c, [finding(rule="R-WEB-2"), finding(rule="R-WEB-1"),
                        finding(rule="Task 2 passo 3"), finding(rule="R-ZZ")],
                    blocking_rules={"R-WEB-1"}, known_rules={"R-WEB-1", "R-WEB-2"})
        flags = [self.finding_row(f"f-1-{i}")["blocking"] for i in (1, 2, 3, 4)]
        self.assertEqual(flags, [0, 1, 1, 1])
        self.assertEqual(self.finding_row("f-1-1")["rule"], "R-WEB-2")

    def test_beyond_max_findings_unverified(self):
        c = self.open()
        sev = ["minor"] * 8 + ["moderate"] * 4 + ["major"] * 3 + ["blocker"] * 2
        self.report(c, [finding(s) for s in sev])
        rows = reviews.to_verify(self.conn, self.w, c, max_findings=15, now=T0)
        self.assertEqual(len(rows), 15)
        self.assertEqual([r["severity"] for r in rows[:2]], ["blocker", "blocker"])
        left = self.conn.execute("SELECT severity, verification_reason FROM findings "
                                 "WHERE verification = 'unverified'").fetchall()
        self.assertEqual(len(left), 2)
        self.assertEqual({r["severity"] for r in left}, {"minor"})
        self.assertIn("oltre max_findings", left[0]["verification_reason"])
        # una seconda chiamata non cambia nulla
        again = reviews.to_verify(self.conn, self.w, c, max_findings=15, now=T0)
        self.assertEqual([r["id"] for r in again], [r["id"] for r in rows])

    def test_apply_verification_counts_missing(self):
        c = self.open()
        self.report(c, [finding(), finding("minor"), finding("moderate")])
        reviews.to_verify(self.conn, self.w, c, max_findings=15, now=T0)
        left = reviews.apply_verification(self.conn, self.w, c, [
            {"id": "f-1-1", "verification": "confirmed", "reason": "c'è"},
            {"id": "f-1-2", "verification": "rejected", "reason": "no"},
            {"id": "f-9-9", "verification": "confirmed", "reason": "sconosciuto"},
            {"id": "f-1-3", "verification": "forse", "reason": "valore non valido"}], now=T0)
        self.assertEqual(left, 1)
        self.assertEqual(self.finding_row("f-1-1")["verification"], "confirmed")
        self.assertEqual(self.finding_row("f-1-2")["verification_reason"], "no")
        self.assertIsNone(self.finding_row("f-1-3")["verification"])

    def test_superseded_not_counted(self):
        c = self.open()
        reviews.supersede(self.conn, self.w, c, now=T0)
        row = reviews.latest(self.conn, self.w)
        self.assertEqual((row["outcome"], row["stage"], row["counted"]), ("superseded", "closed", 0))
        self.assertEqual((reviews.count(self.conn, self.w), reviews.counted(self.conn, self.w)),
                         (1, 0))
        with self.assertRaises(ValueError):
            reviews.supersede(self.conn, self.w, c, now=T0)


class CloseTest(ReviewsCase):
    def test_close_needs_fix_goes_execution(self):
        c = self.open()
        self.report(c, [finding()], outcome="needs_fix")
        self.confirm_all(c)
        self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0),
                         "needs_fix")
        self.assertEqual(self.phase(), "execution")
        self.assertEqual(reviews.counted(self.conn, self.w), 1)
        row = reviews.latest(self.conn, self.w)
        self.assertEqual((row["outcome"], row["stage"], row["findings_confirmed"]),
                         ("needs_fix", "closed", 1))
        cause = [e["data"]["cause"] for e in events.export_events(self.conn, 0)
                 if e["type"] == "phase_change"][-1]
        self.assertEqual(cause, "needs_fix")
        ev = [e for e in events.export_events(self.conn, 0) if e["type"] == "review_cycle"]
        self.assertEqual(ev[-1]["data"], {"number": 1, "outcome": "needs_fix",
                                          "findings_confirmed": 1})

    def test_cycle_without_confirmed_not_counted(self):
        c = self.open()
        self.report(c, [], rejected=[{"text": "senza prova"}])
        self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0), "ok")
        self.assertEqual(self.phase(), "review")
        self.assertEqual((reviews.count(self.conn, self.w), reviews.counted(self.conn, self.w)),
                         (1, 0))

    def test_close_is_resumable(self):
        c = self.open()
        self.report(c, [finding()], outcome="needs_fix")
        self.confirm_all(c)
        reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0)
        self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0),
                         "needs_fix")
        self.assertEqual(self.phase(), "execution")
        self.assertEqual(reviews.counted(self.conn, self.w), 1)

    def test_fourth_counted_cycle_opens_needs_you(self):
        for n in (1, 2, 3):
            self.assertEqual(self.counted_cycle(n), "needs_fix")
            self.assertEqual(self.phase(), "execution")
            self.assertEqual(self.open_blocks(), [])
            self.goto("review")
        self.assertEqual(self.counted_cycle(4), "needs_fix")
        blocks = self.open_blocks()
        self.assertEqual([(b["type"], b["reason"]) for b in blocks],
                         [("needs_you", reviews.CAP_REASON)])
        self.assertEqual(self.phase(), "blocked")
        self.assertEqual(phases.get_work(self.conn, self.w)["phase_before_block"], "execution")

    def test_extra_cycles_move_the_cap(self):
        phases.add_extra_cycles(self.conn, self.w, 1, now=T0)
        for n in (1, 2, 3, 4):
            self.counted_cycle(n)
            self.goto("review")
        self.assertEqual(self.open_blocks(), [])
        self.counted_cycle(5)
        self.assertEqual(len(self.open_blocks()), 1)

    def test_uncounted_cycles_do_not_reach_cap(self):
        for n in range(1, 6):
            c = self.open(sha=f"s{n}")
            self.report(c)
            self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0),
                             "ok")
        self.assertEqual(self.open_blocks(), [])

    def test_reviewer_needs_you_opens_block(self):
        c = self.open()
        self.report(c, [], outcome="needs_you")
        self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0),
                         "needs_you")
        blocks = self.open_blocks()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "needs_you")
        self.assertEqual(self.phase(), "blocked")
        self.assertEqual(reviews.latest(self.conn, self.w)["outcome"], "needs_you")

    def test_non_blocking_rule_is_note(self):
        c = self.open()
        self.report(c, [finding("major", "R-WEB-2")], outcome="needs_fix",
                    blocking_rules={"R-WEB-1"}, known_rules={"R-WEB-1", "R-WEB-2"})
        self.confirm_all(c)
        self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0), "ok")
        self.assertEqual(self.phase(), "review")
        self.assertEqual(reviews.counted(self.conn, self.w), 1)
        self.assertEqual(reviews.blocking_open(self.conn, self.w), [])

    def test_unconfirmed_major_does_not_block(self):
        c = self.open()
        self.report(c, [finding("blocker")], outcome="needs_fix")
        reviews.to_verify(self.conn, self.w, c, max_findings=0, now=T0)
        self.assertEqual(reviews.close_cycle(self.conn, self.t.state, self.w, c, now=T0), "ok")

    def open_blocks(self):
        return self.conn.execute("SELECT * FROM blocks WHERE work = ? AND closed IS NULL",
                                 (self.w,)).fetchall()


class DecisionTest(ReviewsCase):
    def confirmed(self, severity="major"):
        c = self.open()
        self.report(c, [finding(severity)], outcome="needs_fix")
        self.confirm_all(c)
        return c

    def test_is_blocking(self):
        blocking, known = {"R-WEB-1"}, {"R-WEB-1", "R-WEB-2"}
        for rule, expected in (("Task 2 passo 3", True), ("R-WEB-1", True), ("R-WEB-2", False),
                               ("R-NUOVA", True), (None, True), ("", True)):
            with self.subTest(rule=rule):
                self.assertIs(verdicts.is_blocking({"rule": rule}, blocking, known), expected)
        self.assertIs(verdicts.is_blocking({"rule": "R-WEB-2"}, set(), set()), True)
        self.assertIs(verdicts.is_blocking({}, blocking, known), True)

    def test_effective_severity(self):
        self.confirmed("blocker")
        row = self.finding_row("f-1-1")
        self.assertEqual(reviews.effective_severity(row), "blocker")
        reviews.set_decision(self.conn, self.w, "f-1-1", "downgraded:major", now=T0)
        self.assertEqual(reviews.effective_severity(self.finding_row("f-1-1")), "major")
        self.assertEqual(len(reviews.blocking_open(self.conn, self.w)), 1)

    def test_downgrade_and_dismiss(self):
        c = self.open()
        self.report(c, [finding("major"), finding("major")], outcome="needs_fix",
                    rejected=[{"text": "senza prova"}])
        reviews.apply_verification(self.conn, self.w, c, [
            {"id": "f-1-1", "verification": "confirmed", "reason": "c"},
            {"id": "f-1-2", "verification": "confirmed", "reason": "c"}], now=T0)
        with self.subTest("rilievo rejected"):
            with self.assertRaises(ValueError):
                reviews.set_decision(self.conn, self.w, "f-1-3", "dismissed", now=T0)
        with self.subTest("decisione non valida"):
            with self.assertRaises(ValueError):
                reviews.set_decision(self.conn, self.w, "f-1-1", "downgraded:grave", now=T0)
            with self.assertRaises(ValueError):
                reviews.set_decision(self.conn, self.w, "f-9-9", "dismissed", now=T0)
        with self.subTest("declassamento e archiviazione"):
            self.assertEqual(len(reviews.blocking_open(self.conn, self.w)), 2)
            reviews.set_decision(self.conn, self.w, "f-1-1", "downgraded:minor", now=T0)
            self.assertEqual([r["id"] for r in reviews.blocking_open(self.conn, self.w)],
                             ["f-1-2"])
            reviews.set_decision(self.conn, self.w, "f-1-2", "dismissed", now=T0)
            self.assertEqual(reviews.blocking_open(self.conn, self.w), [])
        ev = [e["data"] for e in events.export_events(self.conn, 0) if e["type"] == "finding"
              and e["data"]["user_decision"]]
        self.assertEqual([(d["id"], d["user_decision"]) for d in ev],
                         [("f-1-1", "downgraded:minor"), ("f-1-2", "dismissed")])

    def test_blocking_open_filters_by_cycle(self):
        self.confirmed()
        self.assertEqual(len(reviews.blocking_open(self.conn, self.w, 1)), 1)
        self.assertEqual(reviews.blocking_open(self.conn, self.w, 2), [])


if __name__ == "__main__":
    unittest.main()
