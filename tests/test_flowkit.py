import json
import subprocess
import unittest
from pathlib import Path

from tests.flowkit import FAKEGH, GATE_FILES, ORIGIN_URL, SESSION, FlowLab
from tests.helpers import git
from tollgate_core import VERSION, sessions


class FlowLabTest(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab()

    def tearDown(self):
        self.fl.close()

    def gh(self, *args):
        return subprocess.run([str(FAKEGH), *args], capture_output=True, text=True,
                              env=self.fl.env())

    def test_origin_has_gate_files_and_fake_url(self):
        self.assertIn(" ", str(self.fl.main))
        self.assertEqual(git(self.fl.main, "config", "--get", "remote.origin.url"), ORIGIN_URL)
        tree = git(self.fl.main, "ls-tree", "-r", "--name-only", "origin/main").splitlines()
        for name in GATE_FILES:
            self.assertIn(name, tree)
        self.assertEqual(git(self.fl.main, "show", "origin/main:.github/tollgate/VERSION"),
                         VERSION)

    def test_fetch_goes_to_local_bare_repo(self):
        git(self.fl.main, "fetch", "origin")  # nessuna rete: insteadOf sul repo nudo

    def test_gate_false_has_no_workflows(self):
        other = FlowLab(gate=False)
        try:
            tree = git(other.main, "ls-tree", "-r", "--name-only", "origin/main")
            self.assertNotIn(".github", tree)
        finally:
            other.close()

    def test_home_declares_superpowers(self):
        reg = json.loads((self.fl.home / ".claude/plugins/installed_plugins.json").read_text())
        self.assertEqual(reg["plugins"]["superpowers@claude-plugins-official"][0]["version"],
                         "7.0.0")
        self.assertNotEqual(self.fl.home, Path.home())

    def test_cli_writes_signal_then_runs_binary(self):
        r = self.fl.cli("status")
        self.assertEqual(r.returncode, 0, r.stderr)
        sig = json.loads((self.fl.ts.dir / "cli" / f"{SESSION}.json").read_text())
        self.assertEqual(sig["status"]["cwd"], str(self.fl.main))
        self.assertEqual(sessions.cli_session(self.fl.ts.state, self.fl.main, "status",
                                              now=sessions.clock.now()), SESSION)

    def test_fakegh_answers_from_data_and_logs(self):
        self.fl.set_gh(auth=True, issues={"7": {"number": 7, "title": "T", "body": "B"}},
                       issue_list=[{"number": 7}], prs=[{"headRefName": "tg/7-x", "number": 1}],
                       statuses={"abc": {"statuses": [{"context": "tollgate/guard",
                                                       "state": "success"}]}})
        self.assertEqual(self.gh("auth", "status").returncode, 0)
        r = self.gh("issue", "view", "7", "--json", "title,body")
        self.assertEqual(json.loads(r.stdout), {"title": "T", "body": "B"})
        self.assertEqual(json.loads(self.gh("issue", "list", "--json", "number").stdout),
                         [{"number": 7}])
        self.assertEqual(json.loads(self.gh("pr", "list", "--head", "altro").stdout), [])
        self.assertEqual(len(json.loads(self.gh("pr", "list", "--head", "tg/7-x").stdout)), 1)
        r = self.gh("api", "repos/{owner}/{repo}/commits/abc/status")
        self.assertEqual(json.loads(r.stdout)["statuses"][0]["state"], "success")
        self.assertEqual(len(self.fl.gh_calls()), 6)

    def test_fakegh_exits_1_when_answer_missing(self):
        self.assertEqual(self.gh("issue", "view", "99", "--json", "title").returncode, 1)
        self.assertEqual(self.gh("api", "repos/o/r/commits/zzz/status").returncode, 1)
        self.assertEqual(self.gh("pr", "list").returncode, 1)
        self.assertEqual(self.gh("repo", "create").returncode, 1)
        self.fl.set_gh(auth=False)
        self.assertEqual(self.gh("auth", "status").returncode, 1)

    def test_issue_param_creates_bound_work(self):
        other = FlowLab(issue=9)
        try:
            self.assertEqual(other.wt.name, "wt 9")
            self.assertEqual(other.bash("git status").exit, 0)
            self.assertIsNotNone(sessions.bound_work(other.conn, SESSION))
        finally:
            other.close()


if __name__ == "__main__":
    unittest.main()
