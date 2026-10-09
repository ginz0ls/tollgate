"""Criteri di accettazione di P2 dal wrapper vero (spec 15): hooks/run come lo lancia Claude Code."""
import json
import subprocess
import unittest

from tests.hookkit import SESSION, Lab, sample
from tests.helpers import ROOT

RUN = ROOT / "hooks" / "run"


def run(lab, event, payload):
    return subprocess.run([str(RUN), event], input=json.dumps(payload), capture_output=True,
                          text=True, env=lab.ts.env(), timeout=60)


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def test_push_denied_in_bound_session(self):              # criterio 7
        r = run(self.lab, "PreToolUse", sample(
            "PreToolUse-Bash", session_id=SESSION, cwd=str(self.lab.wt),
            tool_input={"command": "git push origin tg/7-demo"}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("open-pr", r.stderr)

    def test_session_start_injects_state(self):              # criterio 19
        r = run(self.lab, "SessionStart", sample("SessionStart-none", session_id=SESSION,
                                                 cwd=str(self.lab.wt)))
        self.assertEqual(r.returncode, 0)
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(ctx), 1500)

    def test_general_purpose_denied(self):                  # criterio 4, eval 9
        r = run(self.lab, "PreToolUse", sample(
            "PreToolUse-Agent", session_id=SESSION, cwd=str(self.lab.wt),
            tool_input={"description": "d", "prompt": "p", "subagent_type": "general-purpose"}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("/tollgate:execute", r.stderr)

    def test_read_tool_not_routed(self):
        r = run(self.lab, "PreToolUse", sample("PreToolUse-Read", session_id=SESSION,
                                               cwd=str(self.lab.wt)))
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
