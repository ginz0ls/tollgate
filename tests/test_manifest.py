import json
import os
import unittest

from tests.helpers import ROOT


class ManifestTest(unittest.TestCase):
    def test_hooks_json(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptExpansion", "UserPromptSubmit",
                                      "PreToolUse", "PostToolUse", "PostToolUseFailure",
                                      "SubagentStart", "SubagentStop"})
        pre = hooks["PreToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "Agent", "SendMessage"):
            self.assertRegex(tool, f"^(?:{pre})$")
        self.assertRegex("mcp__srv__x", f"^(?:{pre})$")
        self.assertNotRegex("Read", f"^(?:{pre})$")
        post = hooks["PostToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "Bash", "Agent", "Skill", "SubagentHandback"):
            self.assertRegex(tool, f"^(?:{post})$")
        fail = hooks["PostToolUseFailure"][0]["matcher"]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash"):
            self.assertRegex(tool, f"^(?:{fail})$")
        for tool in ("Read", "Agent", "Skill"):
            self.assertNotRegex(tool, f"^(?:{fail})$")
        self.assertNotIn("matcher", hooks["UserPromptSubmit"][0])
        for event, groups in hooks.items():
            for h in groups[0]["hooks"]:
                self.assertEqual(h["command"], f'"${{CLAUDE_PLUGIN_ROOT}}/hooks/run" {event}')
                self.assertEqual(h["timeout"], 90)

    def test_plugin_json(self):
        p = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(p["name"], "tollgate")
        from tollgate_core import VERSION
        self.assertEqual(p["version"], VERSION)
        dep = p["dependencies"][0]
        self.assertEqual((dep["name"], dep["marketplace"]),
                         ("superpowers", "claude-plugins-official"))
        self.assertNotIn("version", dep)

    def test_off_on_skills_user_only(self):
        for name in ("off", "on"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
            self.assertRegex(text, rf"(?m)^name: {name}$")

    def test_wrapper_executable(self):
        self.assertTrue(os.access(ROOT / "hooks" / "run", os.X_OK))


if __name__ == "__main__":
    unittest.main()
