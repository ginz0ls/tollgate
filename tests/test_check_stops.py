import json
import unittest

from tests.hookkit import DROP, Lab, sample
from tollgate_checks import stops

TUID = "toolu_01DOMANDA"


def questions(n=2, opts=3):
    return [{"header": f"D{i}", "question": f"D{i}?", "multiSelect": False,
             "options": [{"label": f"o{j}", "description": f"d{j}"} for j in range(opts)]}
            for i in range(1, n + 1)]


def pre(lab, **changes):
    extra = {"session_id": lab.session, "cwd": str(lab.wt), "agent_id": DROP,
             "agent_type": DROP, "tool_use_id": TUID,
             "tool_input": {"questions": questions()}}
    extra.update(changes)
    return sample("PreToolUse-AskUserQuestion", **extra)


def post(lab, hook_event="PostToolUse", **changes):
    extra = {"session_id": lab.session, "cwd": str(lab.wt), "agent_id": DROP,
             "agent_type": DROP, "tool_use_id": TUID, "hook_event_name": hook_event,
             "tool_input": {"questions": questions()}, "tool_response": DROP}
    extra.update(changes)
    return sample("PostToolUse-AskUserQuestion", **extra)


def stop_events(lab, type_):
    return [json.loads(r["data"]) for r in lab.conn.execute(
        "SELECT data FROM events WHERE type = ? ORDER BY seq", (type_,))]


class StopsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.addCleanup(self.lab.close)

    def test_constants(self):
        self.assertEqual((stops.STOP_TEXT_MAX, stops.MAX_QUESTIONS, stops.MAX_OPTIONS),
                         (300, 4, 4))

    def test_stop_asked_recorded(self):
        r = self.lab.hook(pre(self.lab))
        self.assertEqual((r.exit, r.stdout, r.stderr), (0, "", ""))
        [data] = stop_events(self.lab, "stop_asked")
        self.assertEqual(data["tool_use_id"], TUID)
        self.assertEqual([q["header"] for q in data["questions"]], ["D1", "D2"])
        self.assertEqual(data["questions"][0],
                         {"header": "D1", "question": "D1?", "options": ["o0", "o1", "o2"]})

    def test_stop_answered_from_tool_response(self):
        self.lab.hook(post(self.lab, tool_response={"questions": questions(),
                                                    "answers": {"D1?": "Sì"}}))
        [data] = stop_events(self.lab, "stop_answered")
        self.assertEqual((data["tool_use_id"], data["answers"], data["source"]),
                         (TUID, {"D1?": "Sì"}, "tool_response"))

    def test_stop_answered_from_tool_input(self):
        self.lab.hook(post(self.lab, tool_input={"questions": questions(),
                                                 "answers": {"D1?": "No"}}))
        [data] = stop_events(self.lab, "stop_answered")
        self.assertEqual((data["answers"], data["source"]), ({"D1?": "No"}, "tool_input"))

    def test_stop_answered_without_answers(self):
        self.lab.hook(post(self.lab))
        [data] = stop_events(self.lab, "stop_answered")
        self.assertEqual((data["answers"], data["source"]), (None, "none"))

    def test_stop_answered_on_failure(self):
        r = self.lab.hook(post(self.lab, "PostToolUseFailure"))
        self.assertEqual(r.exit, 0)
        [data] = stop_events(self.lab, "stop_answered")
        self.assertEqual((data["answers"], data["source"]), (None, "failure"))

    def test_stop_texts_truncated(self):
        qs = questions(6, 6)
        qs[0]["question"] = "x" * 5000
        qs[0]["header"] = "h" * 5000
        qs[0]["options"][0]["label"] = "l" * 5000
        self.lab.hook(pre(self.lab, tool_input={"questions": qs}))
        self.lab.hook(post(self.lab, tool_response={"answers": {"k" * 5000: "v" * 5000}}))
        [asked] = stop_events(self.lab, "stop_asked")
        self.assertEqual(len(asked["questions"]), 4)
        q = asked["questions"][0]
        self.assertEqual(len(q["question"]), 300)
        self.assertEqual(len(q["header"]), 300)
        self.assertEqual(len(q["options"]), 4)
        self.assertEqual(len(q["options"][0]), 300)
        [answered] = stop_events(self.lab, "stop_answered")
        [(k, v)] = answered["answers"].items()
        self.assertEqual((len(k), len(v)), (300, 300))

    def test_stops_never_deny_or_raise(self):
        bad = [DROP, "boh", 7, [], ["x", 3, None], {"a": 1}, [{"header": 5, "options": "x"}],
               [{"question": "q", "options": [1, None, {"label": "ok"}, "s"]}]]
        for qs in bad:
            ti = {} if qs is DROP else {"questions": qs}
            with self.subTest(questions=repr(qs)[:40]):
                self.assertEqual(self.lab.hook(pre(self.lab, tool_input=ti)).exit, 0)
        for tr in ("testo", ["a"], 5, {"answers": "x"}, {"answers": ["a"]}, {"answers": {1: 2}}):
            with self.subTest(response=repr(tr)[:40]):
                self.assertEqual(self.lab.hook(post(self.lab, tool_response=tr)).exit, 0)
        self.assertEqual(self.lab.hook(pre(self.lab, tool_input="stringa")).exit, 0)
        self.assertEqual(self.lab.hook(pre(self.lab, tool_input=DROP)).exit, 0)
        self.assertEqual(self.lab.conn.execute(
            "SELECT COUNT(*) FROM events WHERE type = 'veto'").fetchone()[0], 0)

    def test_unreadable_questions_record_nothing(self):
        for ti in ({}, {"questions": "boh"}, {"questions": []}, {"questions": ["x", 3]}):
            self.lab.hook(pre(self.lab, tool_input=ti))
        self.assertEqual(stop_events(self.lab, "stop_asked"), [])

    def test_no_tool_use_id(self):
        self.lab.hook(pre(self.lab, tool_use_id=DROP))
        [data] = stop_events(self.lab, "stop_asked")
        self.assertIsNone(data["tool_use_id"])

    def test_stop_event_has_work_when_bound(self):
        self.lab.hook(pre(self.lab))
        row = self.lab.conn.execute(
            "SELECT work FROM events WHERE type = 'stop_asked'").fetchone()
        self.assertEqual(row["work"], self.lab.work)

    def test_stop_event_without_work(self):
        lab = Lab(work=False)
        self.addCleanup(lab.close)
        lab.hook(pre(lab))
        row = lab.conn.execute("SELECT work FROM events WHERE type = 'stop_asked'").fetchone()
        self.assertIsNone(row["work"])


if __name__ == "__main__":
    unittest.main()
