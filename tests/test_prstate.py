import os
import unittest
from unittest import mock

from tests.flowkit import FlowLab
from tollgate_core import phases
from tollgate_flow import finishcheck, prstate

MERGED_AT = "2026-10-19T12:00:00Z"


def pr(number=3, state="OPEN", merged=None):
    return {"number": number, "headRefName": "tg/7-demo", "state": state,
            "url": f"https://github.com/prova/flow/pull/{number}", "headRefOid": "abc",
            "mergedAt": merged, "body": "", "comments": []}


class PrStateCase(unittest.TestCase):
    def lab(self, *, phase="pr_open", prs=(), pr_number=3, **data):
        fl = FlowLab(issue=7, level="L0", phase="execution")
        self.addCleanup(fl.close)
        fl.goto(phase)
        fl.set_gh(prs=list(prs), **data)
        if pr_number is not None:
            phases.set_pr(fl.conn, fl.work, pr_number, f"https://x/pull/{pr_number}",
                          now=fl.now)
        env = mock.patch.dict(os.environ, fl.env())
        env.start()
        self.addCleanup(env.stop)
        return fl

    def detect(self, fl, session=None):
        work = phases.get_work(fl.conn, fl.work)
        return prstate.detect(fl.ts.state, fl.conn, work, fl.main, now=fl.now, session=session)

    def work(self, fl):
        return phases.get_work(fl.conn, fl.work)


class DetectTest(PrStateCase):
    def test_merged_closes_work(self):
        for phase in ("pr_open", "execution", "review"):
            with self.subTest(phase=phase):
                fl = self.lab(phase=phase, prs=[pr(state="MERGED", merged=MERGED_AT)])
                d = self.detect(fl, session="sess-flow")
                self.assertEqual(d.kind, "merged")
                self.assertEqual(d.pr["number"], 3)
                w = self.work(fl)
                self.assertEqual((w["phase"], w["closed_reason"]), ("closed", "merged"))
                self.assertEqual(fl.events("merge_detected"),
                                 [{"pr": 3, "merged_at": MERGED_AT}])

    def test_merged_blocked_work_is_closed_too(self):
        fl = self.lab(phase="execution", prs=[pr(state="MERGED", merged=MERGED_AT)])
        phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "x", now=fl.now)
        self.assertEqual(self.detect(fl).kind, "merged")
        self.assertEqual(self.work(fl)["phase"], "closed")
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM blocks WHERE closed IS NULL")
                         .fetchone()[0], 0)

    def test_closed_unmerged_returns_closed(self):
        fl = self.lab(prs=[pr(state="CLOSED")])
        d = self.detect(fl)
        self.assertEqual((d.kind, d.pr["number"]), ("closed", 3))
        self.assertEqual(self.work(fl)["phase"], "pr_open")
        self.assertEqual(fl.events("merge_detected"), [])
        self.assertIn("/tollgate:abandon", prstate.CLOSED_HINT)
        self.assertIn("--confirm", prstate.CLOSED_HINT)
        self.assertIn('python3 "', prstate.CLOSED_HINT.replace("'", '"'))

    def test_open_pr(self):
        fl = self.lab(prs=[pr()])
        d = self.detect(fl)
        self.assertEqual((d.kind, d.pr["state"]), ("open", "OPEN"))
        self.assertEqual(self.work(fl)["phase"], "pr_open")

    def test_no_pr_number_asks_nothing(self):
        fl = self.lab(prs=[pr()], pr_number=None)
        d = self.detect(fl)
        self.assertEqual((d.kind, d.pr, d.error), (None, None, None))
        self.assertEqual(fl.gh_calls(), [])

    def test_offline_is_none(self):
        fl = self.lab(prs=[pr()], fail=["pr view"])
        d = self.detect(fl)
        self.assertEqual((d.kind, d.pr), (None, None))
        self.assertIn("pr view", d.error)
        self.assertEqual(self.work(fl)["phase"], "pr_open")


class FinishCheckHookTest(PrStateCase):
    def check(self, fl):
        return finishcheck.check(fl.ts.state, fl.wt, environ=fl.env())

    def test_finish_check_refuses_on_closed_pr(self):
        fl = self.lab(phase="execution", prs=[pr(state="CLOSED")])
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.REFUSED, r.lines)
        text = "\n".join(r.lines)
        self.assertIn("PR #3 chiusa senza merge", text)
        self.assertIn(prstate.CLOSED_HINT, text)
        self.assertEqual(self.work(fl)["phase"], "execution")
        self.assertEqual(fl.events("finish_check"), [])

    def test_finish_check_closes_merged_work_and_refuses(self):
        fl = self.lab(phase="pr_open", prs=[pr(state="MERGED", merged=MERGED_AT)])
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.REFUSED, r.lines)
        self.assertIn("unita", "\n".join(r.lines))
        self.assertEqual(self.work(fl)["phase"], "closed")

    def test_finish_check_offline_warns_and_goes_on(self):
        fl = self.lab(phase="execution", prs=[pr()], fail=["pr view"])
        r = self.check(fl)
        self.assertTrue(any(x.startswith("avviso:") and "PR #3" in x for x in r.lines), r.lines)
        self.assertNotIn("chiusa senza merge", "\n".join(r.lines))


if __name__ == "__main__":
    unittest.main()
