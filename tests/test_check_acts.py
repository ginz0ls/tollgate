import unittest

from tests.hookkit import SESSION, Lab, sample
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


if __name__ == "__main__":
    unittest.main()
