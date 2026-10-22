import json
import subprocess
import sys
import unittest
from pathlib import Path

from types import SimpleNamespace

from tests.flowkit import (FAKEGH, GATE_FILES, JUNIT_TOML, ORIGIN_URL, PLAN, SESSION,
                           FlowLab)
from tests.helpers import git
from tollgate_analysis.junit import parse_junit
from tollgate_core import VERSION, git as core_git, phases, sessions
from tollgate_core.paths import repo_key
from tollgate_checks._common import orphan_tg


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
        self.assertEqual(json.loads(self.gh("pr", "list", "--head", "altro", "--json", "number").stdout), [])
        self.assertEqual(len(json.loads(self.gh("pr", "list", "--head", "tg/7-x", "--json", "number").stdout)), 1)
        r = self.gh("api", "repos/{owner}/{repo}/commits/abc/status")
        self.assertEqual(json.loads(r.stdout)["statuses"][0]["state"], "success")
        self.assertEqual(len(self.fl.gh_calls()), 6)

    def test_env_makes_gh_retries_wait_zero(self):
        """I sottoprocessi del banco non dormono tra i ritentativi delle letture di `gh api`."""
        self.assertEqual(self.fl.env()["TOLLGATE_GH_RETRY_DELAYS"], "0,0")

    def test_fakegh_exits_1_when_answer_missing(self):
        self.assertEqual(self.gh("issue", "view", "99", "--json", "title").returncode, 1)
        self.assertEqual(self.gh("api", "repos/o/r/commits/zzz/status").returncode, 1)
        self.assertEqual(self.gh("pr", "list").returncode, 1)
        self.assertEqual(self.gh("repo", "create").returncode, 1)
        self.fl.set_gh(auth=False)
        self.assertEqual(self.gh("auth", "status").returncode, 1)

    def test_work_repo_key_matches_origin_url_and_hook_finds_it(self):
        other = FlowLab(issue=9)
        try:
            row = other.conn.execute("SELECT repo_key FROM work_items").fetchone()
            self.assertEqual(row[0], repo_key(core_git.origin_url(other.main)))
            # il ramo tg/9-* del worktree ha un lavoro attivo per la chiave del repo: non è orfano
            self.assertIsNone(orphan_tg(SimpleNamespace(db=other.conn), other.wt))
            self.assertEqual(other.bash("git status").exit, 0)
        finally:
            other.close()

    def test_issue_param_creates_bound_work(self):
        other = FlowLab(issue=9)
        try:
            self.assertEqual(other.wt.name, "wt 9")
            self.assertEqual(other.bash("git status").exit, 0)
            self.assertIsNotNone(sessions.bound_work(other.conn, SESSION))
        finally:
            other.close()


class FlowKitP3bTest(unittest.TestCase):
    def test_register_plan_moves_to_execution_with_tasks(self):
        fl = FlowLab(issue=7, phase="plan")
        try:
            fl.register_plan()
            row = phases.get_work(fl.conn, fl.work)
            self.assertEqual((row["phase"], row["plan_path"]), ("execution", PLAN))
            self.assertEqual([r["number"] for r in fl.conn.execute(
                "SELECT number FROM tasks WHERE work = ? ORDER BY number", (fl.work,))], [1])
        finally:
            fl.close()

    def test_register_plan_with_three_tasks(self):
        fl = FlowLab(issue=7, phase="plan")
        try:
            fl.register_plan(tasks=3)
            self.assertEqual(fl.conn.execute("SELECT count(*) FROM tasks WHERE work = ?",
                                             (fl.work,)).fetchone()[0], 3)
        finally:
            fl.close()

    def test_commit_records_event_and_close_tasks(self):
        fl = FlowLab(issue=7, phase="plan")
        try:
            fl.register_plan(tasks=2)
            sha = fl.commit("src/app.py", "def somma(a, b):\n    return b + a\n", "somma")
            self.assertEqual(sha, git(fl.wt, "rev-parse", "HEAD"))
            self.assertEqual(git(fl.wt, "log", "-1", "--format=%s"), "somma")
            self.assertEqual(fl.events("commit"), [{"sha": sha}])
            fl.close_tasks()
            rows = fl.conn.execute("SELECT state, verdict FROM tasks").fetchall()
            self.assertEqual([(r["state"], r["verdict"]) for r in rows],
                             [("done", "approved")] * 2)
            fl.close_tasks()      # idempotente
        finally:
            fl.close()

    def test_junit_fake_writes_report_from_ids(self):
        fl = FlowLab(toml=JUNIT_TOML)
        try:
            self.assertTrue((fl.main / "tools" / "junit_fake.py").exists())
            (fl.main / "tests").mkdir(exist_ok=True)
            (fl.main / "tests" / "ids.txt").write_text(
                "tests.test_app::test_somma ok\ntests.test_app::test_zero fail\n")
            r = subprocess.run([sys.executable, "-B", "tools/junit_fake.py"], cwd=fl.main,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stderr)
            junit = parse_junit((fl.main / "reports" / "junit.xml").read_bytes())
            self.assertEqual(junit.ids_run, ["tests.test_app::test_somma",
                                             "tests.test_app::test_zero"])
            self.assertEqual(junit.ids_failed, ["tests.test_app::test_zero"])
            (fl.main / "tests" / "ids.txt").write_text("tests.test_app::test_somma ok\n")
            r = subprocess.run([sys.executable, "-B", "tools/junit_fake.py"], cwd=fl.main,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            fl.close()

    def test_junit_file_only_for_junit_toml(self):
        fl = FlowLab()
        try:
            self.assertFalse((fl.main / "tools").exists())
        finally:
            fl.close()


if __name__ == "__main__":
    unittest.main()
