import re
import unittest

from tests.helpers import ROOT, git
from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML, SESSION, Lab, sample

EID = re.compile(r"approve effect (e-[0-9a-f]{8})")


def approve(lab, eid, *, session=SESSION, cwd=None):
    lab.hook(sample("UserPromptExpansion-none", session_id=session, cwd=str(cwd or lab.wt),
                    command_name="tollgate:approve", command_args=f"effect {eid}",
                    prompt=f"/tollgate:approve effect {eid}"))


def mcp(lab, name, tool_input):
    return lab.hook(lab._base("PreToolUse-Bash", None, None, tool_name=name,
                              tool_input=tool_input))


def run(lab, cmd, **kw):
    """Il comando come lo vive Claude Code: PreToolUse e, se passa, PostToolUse."""
    r = lab.bash(cmd, **kw)
    if r.exit == 0:
        lab.bash(cmd, post=True, **kw)
    return r


TOML = DEFAULT_TOML + '[external_effects]\nallow = ["npm publish --dry-run"]\n' \
                      'mcp_allow = ["mcp__lettura__*"]\n'


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(toml=TOML, files=dict(DEFAULT_FILES, **{"scripts/ok.sh": "echo ok\n"}))

    def tearDown(self):
        self.lab.close()

    def veto_id(self, cmd, **kw):
        r = self.lab.bash(cmd, **kw)
        self.assertEqual(r.exit, 2, r.stderr)
        return EID.search(r.stderr).group(1)

    def test_veto_act_once_then_warning(self):
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        eid = EID.search(r.stderr).group(1)
        approve(self.lab, eid)
        self.assertEqual(self.lab.bash("npm publish").exit, 0)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.lab.bash("npm publish", post=True)
        self.assertEqual(len(self.lab.events("effect_executed")), 1)
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        self.assertIn("già eseguito alle", r.stderr)
        self.assertEqual(EID.search(r.stderr).group(1), eid)

    def test_denied_line_keeps_the_act_valid(self):
        eid = self.veto_id("ssh a")
        approve(self.lab, eid)
        r = self.lab.bash("ssh a && git push origin tg/7-demo")
        self.assertEqual(r.exit, 2)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.assertEqual(self.lab.bash("ssh a").exit, 0)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.lab.bash("ssh a", post=True)
        self.assertEqual(len(self.lab.events("effect_executed")), 1)
        r = self.lab.bash("ssh a")
        self.assertEqual(r.exit, 2)
        self.assertIn("già eseguito alle", r.stderr)

    def intent_state(self):
        return [r["state"] for r in self.lab.conn.execute(
            "SELECT state FROM intents WHERE action = 'effect'")]

    def test_pre_does_not_reopen_an_executed_effect(self):
        eid = self.veto_id("ssh a")
        approve(self.lab, eid)
        run(self.lab, "ssh a")
        self.assertEqual(self.intent_state(), ["executed"])
        self.assertEqual(self.lab.bash("ssh a").exit, 2)
        self.assertEqual(self.intent_state(), ["executed"])
        approve(self.lab, eid)
        self.assertEqual(self.lab.bash("ssh a").exit, 0)
        self.assertEqual(self.intent_state(), ["executed"])

    def test_post_without_act_consumes_nothing(self):
        self.lab.bash("ssh a", post=True)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.assertEqual(self.lab.bash("ssh a").exit, 2)

    def test_post_of_unrelated_command_consumes_nothing(self):
        eid = self.veto_id("ssh a")
        approve(self.lab, eid)
        self.lab.bash("ls", post=True)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.assertEqual(self.lab.bash("ssh a").exit, 0)

    def test_reason_has_no_double_prefix(self):
        r = self.lab.bash("ssh a")
        self.assertNotIn("effetto esterno (effetto esterno", r.stderr)
        self.assertIn("effetto esterno", r.stderr)
        (self.lab.wt / "scripts/nuovo.sh").write_text("echo x\n")
        r = self.lab.bash("bash scripts/nuovo.sh")
        self.assertIn("effetto esterno (script nel repo non tracciato", r.stderr)

    def test_new_sha_is_a_new_effect_without_warning(self):
        eid = self.veto_id("npm publish")
        approve(self.lab, eid)
        self.assertEqual(run(self.lab, "npm publish").exit, 0)
        (self.lab.wt / "nuovo.txt").write_text("x\n")
        git(self.lab.wt, "add", "nuovo.txt")
        git(self.lab.wt, "commit", "-qm", "altro")
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        self.assertNotIn("già eseguito", r.stderr)
        self.assertNotEqual(EID.search(r.stderr).group(1), eid)

    def test_other_effects(self):
        for cmd in ("gh pr edit 3 --title x", "gh api graphql -f query='mutation { x }'",
                    "curl -X POST https://example.invalid", "bash scripts/nuovo.sh",
                    "bash -c 'ssh host ls'", "ssh host ls", "make deploy"):
            with self.subTest(cmd=cmd):
                if cmd.endswith("nuovo.sh"):
                    (self.lab.wt / "scripts/nuovo.sh").write_text("echo x\n")
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 2)

    def test_allowed(self):
        for cmd in ("npm publish --dry-run", "bash scripts/ok.sh", "gh pr view 3",
                    f"'{ROOT}/bin/tollgate' verify", "ls -la", "git status"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 0)

    def test_untracked_ignored_script_is_still_an_effect(self):
        (self.lab.wt / "reports").mkdir()
        (self.lab.wt / "reports/run.sh").write_text("echo x\n")
        self.assertEqual(git(self.lab.wt, "check-ignore", "reports/run.sh"), "reports/run.sh")
        self.assertEqual(self.lab.bash("bash reports/run.sh", agent_id="a1").exit, 2)

    def test_worktree_bin_tollgate_is_not_exempt(self):
        (self.lab.wt / "bin").mkdir()
        (self.lab.wt / "bin/tollgate").write_text("#!/bin/sh\n")
        self.assertEqual(self.lab.bash("./bin/tollgate verify", agent_id="a1").exit, 2)

    def test_second_effect_of_the_line_is_not_skipped(self):
        eid = self.veto_id("ssh a")
        approve(self.lab, eid)
        r = self.lab.bash("ssh a && ssh b")
        self.assertEqual(r.exit, 2)
        self.assertNotEqual(EID.search(r.stderr).group(1), eid)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.assertEqual(run(self.lab, "ssh a").exit, 0)
        self.assertEqual(len(self.lab.events("effect_executed")), 1)

    def test_all_effects_of_the_line_approved(self):
        a, b = self.veto_id("ssh a"), self.veto_id("ssh b")
        approve(self.lab, a)
        approve(self.lab, b)
        self.assertEqual(run(self.lab, "ssh a && ssh b").exit, 0)
        self.assertEqual(len(self.lab.events("effect_executed")), 2)

    def test_same_effect_twice_in_a_line_needs_two_acts(self):
        eid = self.veto_id("ssh a")
        approve(self.lab, eid)
        r = self.lab.bash("ssh a; ssh a")
        self.assertEqual(r.exit, 2)
        self.assertEqual(self.lab.events("effect_executed"), [])
        self.assertEqual(run(self.lab, "ssh a").exit, 0)

    def test_mcp(self):
        self.assertEqual(mcp(self.lab, "mcp__lettura__cerca", {"q": "x"}).exit, 0)
        r = mcp(self.lab, "mcp__srv__scrivi", {"testo": "x"})
        self.assertEqual(r.exit, 2)
        eid = EID.search(r.stderr).group(1)
        approve(self.lab, eid)
        self.assertEqual(mcp(self.lab, "mcp__srv__scrivi", {"testo": "x"}).exit, 0)
        r = mcp(self.lab, "mcp__srv__scrivi", {"testo": "x"})
        self.assertEqual(r.exit, 2)
        self.assertIn("già eseguito alle", r.stderr)
        r = mcp(self.lab, "mcp__srv__scrivi", {"testo": "y"})
        self.assertEqual(r.exit, 2)
        self.assertNotEqual(EID.search(r.stderr).group(1), eid)

    def test_unparsable_command_is_searched_by_text(self):
        self.assertEqual(self.lab.bash("echo 'ciao").exit, 0)
        for cmd in ("echo 'x; ssh host", "echo 'a && psql -c x", "echo 'a; gh pr create --fill",
                    "echo 'a; curl -X POST http://x", "bash <<EOF\nssh host\nEOF"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 2)

    def test_unparsable_effect_follows_the_same_cycle(self):
        cmd = "echo 'x; ssh host"
        eid = self.veto_id(cmd)
        approve(self.lab, eid)
        self.assertEqual(run(self.lab, cmd).exit, 0)
        self.assertEqual(len(self.lab.events("effect_executed")), 1)
        r = self.lab.bash(cmd)
        self.assertEqual(r.exit, 2)
        self.assertIn("già eseguito alle", r.stderr)
        self.assertEqual(EID.search(r.stderr).group(1), eid)


class UnboundSessionTest(unittest.TestCase):
    def test_effect_in_main_checkout(self):
        lab = Lab(bind=False, toml=TOML)
        try:
            r = lab.bash("npm publish", cwd=lab.main, session_id="altra")
            self.assertEqual(r.exit, 2)
            eid = EID.search(r.stderr).group(1)
            approve(lab, eid, session="altra", cwd=lab.main)
            self.assertEqual(run(lab, "npm publish", cwd=lab.main, session_id="altra").exit, 0)
            r = lab.bash("npm publish", cwd=lab.main, session_id="altra")
            self.assertEqual(r.exit, 2)
            self.assertIn("già eseguito alle", r.stderr)
        finally:
            lab.close()

    def test_approval_of_another_session_does_not_count(self):
        lab = Lab(bind=False, toml=TOML)
        try:
            r = lab.bash("npm publish", cwd=lab.main, session_id="altra")
            eid = EID.search(r.stderr).group(1)
            approve(lab, eid, session="terza", cwd=lab.main)
            self.assertEqual(lab.bash("npm publish", cwd=lab.main, session_id="altra").exit, 2)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
