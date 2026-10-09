import json
import unittest

from tests.hookkit import DROP, SESSION, Lab, sample
from tollgate_core import git


def expand(lab, name, args, session=SESSION, cwd=None):
    return lab.hook(sample("UserPromptExpansion-none", session_id=session,
                           cwd=str(cwd or lab.wt), command_name=name, command_args=args,
                           prompt=f"/{name} {args}".strip()))


class ActsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def acts(self):
        return [dict(r) for r in self.lab.conn.execute("SELECT * FROM acts ORDER BY n")]

    def test_approve_waiver(self):
        r = expand(self.lab, "tollgate:approve", "waiver w-7-1")
        self.assertEqual(r.exit, 0)
        a = self.acts()[0]
        self.assertEqual((a["type"], a["object"], a["target"], a["work"], a["session"]),
                         ("approve", "waiver", "w-7-1", self.lab.work, SESSION))
        self.assertEqual(a["typed_text"], "/tollgate:approve waiver w-7-1")

    def test_finish_bound_to_head(self):
        expand(self.lab, "tollgate:finish", "")
        a = self.acts()[0]
        self.assertEqual((a["type"], a["head_sha"]), ("finish", git.head(self.lab.wt)))

    def test_approve_pr_targets_head(self):
        expand(self.lab, "tollgate:approve", "pr")
        self.assertEqual(self.acts()[0]["target"], git.head(self.lab.wt))

    def test_invalid_object_not_recorded(self):
        r = expand(self.lab, "tollgate:approve", "boh 3")
        self.assertEqual(self.acts(), [])
        self.assertIn("non registrato", r.stdout)

    def test_adopt_from_unbound_session(self):
        expand(self.lab, "tollgate:adopt", "#9", session="altra", cwd=self.lab.main)
        a = self.acts()[0]
        self.assertEqual((a["type"], a["target"], a["work"]), ("adopt", "9", None))

    def test_non_tollgate_and_status_are_not_acts(self):
        expand(self.lab, "superpowers:brainstorming", "")
        expand(self.lab, "tollgate:status", "")
        self.assertEqual(self.acts(), [])

    def test_skill_tool_does_not_create_acts(self):
        p = sample("PostToolUse-Skill", session_id=SESSION, cwd=str(self.lab.wt),
                   tool_name="Skill", tool_input={"skill": "tollgate:approve",
                                                  "args": "waiver w-7-1"},
                   tool_response={"success": True})
        self.lab.hook(p)
        self.assertEqual(self.acts(), [])

    def test_decision15_object_and_target(self):
        cases = [
            ("tollgate:approve", "effect e-1", ("approve", "effect", "e-1")),
            ("tollgate:approve", "finding f-1 minor motivo", ("approve", "finding", "f-1")),
            ("tollgate:approve", "level L1 motivo", ("approve", "level", "L1")),
            ("tollgate:approve", "rounds 3", ("approve", "rounds", "3")),
            ("tollgate:approve", "spec 2", ("approve", "spec", "2")),
            ("tollgate:approve", "plan", ("approve", "plan", None)),
            ("tollgate:approve", "rebase", ("approve", "rebase", None)),
            ("tollgate:approve", "unverified-tests", ("approve", "unverified-tests", None)),
            ("tollgate:reopen", "spec ripensato", ("reopen", "spec", None)),
            ("tollgate:reopen", "plan motivo", ("reopen", "plan", None)),
            ("tollgate:resolve", "r-1 nota", ("resolve", None, "r-1")),
            ("tollgate:resolve", "writer nota", ("resolve", None, "writer")),
            ("tollgate:abandon", "#7", ("abandon", None, "7")),
        ]
        for name, args, _ in cases:
            expand(self.lab, name, args)
        self.assertEqual([(a["type"], a["object"], a["target"]) for a in self.acts()],
                         [expected for _, _, expected in cases])

    def test_refused_forms_are_not_recorded(self):
        for name, args in [("tollgate:approve", "spec"), ("tollgate:approve", "waiver"),
                           ("tollgate:approve", "effect"), ("tollgate:reopen", ""),
                           ("tollgate:reopen", "foo motivo"), ("tollgate:resolve", ""),
                           ("tollgate:adopt", "abc"), ("tollgate:abandon", "x")]:
            expand(self.lab, name, args)
        self.assertEqual(self.acts(), [])

    def test_unbound_session_cannot_finish_or_approve_pr(self):
        expand(self.lab, "tollgate:finish", "", session="altra", cwd=self.lab.main)
        expand(self.lab, "tollgate:approve", "pr", session="altra", cwd=self.lab.main)
        self.assertEqual(self.acts(), [])

    def test_quoted_args_stay_whole(self):
        expand(self.lab, "tollgate:approve", 'finding f-1 minor "motivo con spazi"')
        a = self.acts()[0]
        self.assertEqual(json.loads(a["args"]),
                         ["finding", "f-1", "minor", "motivo con spazi"])
        self.assertEqual(a["target"], "f-1")

    def test_cleanup_has_no_work(self):
        expand(self.lab, "tollgate:cleanup", "")
        a = self.acts()[0]
        self.assertEqual((a["type"], a["work"]), ("cleanup", None))

    def test_slash_command_expansion_type_required_when_present(self):
        p = sample("UserPromptExpansion-none", session_id=SESSION, cwd=str(self.lab.wt),
                   command_name="tollgate:approve", command_args="pr",
                   expansion_type="other", prompt="/tollgate:approve pr")
        self.lab.hook(p)
        self.assertEqual(self.acts(), [])

    def test_missing_expansion_type_is_accepted(self):
        p = sample("UserPromptExpansion-none", session_id=SESSION, cwd=str(self.lab.wt),
                   command_name="tollgate:approve", command_args="pr",
                   expansion_type=DROP, prompt="/tollgate:approve pr")
        self.lab.hook(p)
        self.assertEqual(len(self.acts()), 1)

    def test_recorded_act_is_announced_as_received(self):
        r = expand(self.lab, "tollgate:approve", "waiver w-7-1")
        text = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("atto ricevuto (approve waiver w-7-1)", text)
        self.assertNotIn("registrato", text)


if __name__ == "__main__":
    unittest.main()
