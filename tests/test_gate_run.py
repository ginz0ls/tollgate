import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from tests.gatekit import GateLab
from tests.helpers import BIN, TempState, git
from tollgate_core.config import ConfigError
from tollgate_core.ghcli import GhError
from tollgate_core.git import GitError
from tollgate_gate import baseids, cli
from tollgate_gate import run as gate_run

PROGRAM = BIN / "tollgate"
CHECK = ("mkdir -p reports\n"
         "printf '<testsuite><testcase classname=\"t\" name=\"a\"/>"
         "<testcase classname=\"t\" name=\"b\"/></testsuite>' > reports/junit.xml\n"
         "echo ran >> ran.txt\n")
TOML = """schema_version = 1
[gate]
mode = "protected"
[commands]
verify = "sh check.sh"
gate = ["verify"]
report = "junit:reports/junit.xml"
"""
EVENT = {"pull_request": {"base": {"ref": "main"}, "head": {"ref": "tg/7-x"}},
         "repository": {"default_branch": "main"}}


class GateRunBase(unittest.TestCase):
    toml = TOML

    def setUp(self):
        self.lab = GateLab(toml=self.toml,
                           files={"check.sh": CHECK, ".gitignore": "ran.txt\nreports/\n"})
        self.out = Path(tempfile.mkdtemp(prefix="tollgate out ")) / "art"
        self.ts = TempState()
        self.home = Path(tempfile.mkdtemp(prefix="tollgate home "))
        self.addCleanup(self.ts.cleanup)
        self.addCleanup(shutil.rmtree, self.out.parent, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def tearDown(self):
        self.lab.close()

    def event(self, **pr_base):
        data = json.loads(json.dumps(EVENT))
        data["pull_request"]["base"].update(pr_base)
        path = self.out.parent / "event.json"
        path.write_text(json.dumps(data))
        return path

    def results(self):
        return json.loads((self.out / "results.json").read_text())

    def tollgate(self, *args, cwd=None, **env):
        e = {**self.ts.env(), "HOME": str(self.home), **env}
        e.pop("GITHUB_ACTIONS", None) if "GITHUB_ACTIONS" not in env else None
        return subprocess.run([sys.executable, "-B", str(PROGRAM), *args],
                              cwd=cwd or self.lab.repo, env=e, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=120)

    def run_gate(self, **kw):
        values = dict(config_sha=self.lab.base, base_sha=self.lab.base, out=self.out,
                      environ=os.environ, applicable=True)
        values.update(kw)
        return gate_run.run(self.lab.repo, **values)


class GateRunTest(GateRunBase):
    def test_results_shape(self):
        self.lab.commit("src/new.py", "x = 1\n")
        self.assertEqual(self.run_gate(), 0)
        res = self.results()
        self.assertEqual((res["v"], res["applicable"], res["sha"], res["config_sha"]),
                         (1, True, self.lab.head, self.lab.base))
        self.assertEqual(res["commands"], [{
            "name": "verify", "state": "green", "exit": 0, "tests_run": 2, "tests_skipped": 0,
            "report": "junit/0.xml"}])
        self.assertIn("<testsuite>", (self.out / "junit" / "0.xml").read_text())
        self.assertTrue(any((self.out / "logs").iterdir()))

    def test_not_applicable_runs_nothing(self):
        self.assertEqual(self.run_gate(applicable=False), 0)
        res = self.results()
        self.assertEqual((res["applicable"], res["commands"]), (False, []))
        self.assertFalse((self.lab.repo / "ran.txt").exists())

    def test_unwritable_out_returns_1(self):
        blocker = self.out.parent / "file"
        blocker.write_text("")
        buf = io.StringIO()
        with redirect_stderr(buf):
            self.assertEqual(self.run_gate(out=blocker / "art"), 1)
        self.assertIn("gate run", buf.getvalue())

    def test_config_from_default_tip_not_head(self):
        self.lab.commit("tollgate.toml", self.toml.replace("sh check.sh", "echo head > head.txt"))
        self.lab.commit("src/new.py", "x = 1\n")
        event = self.event()
        r = self.tollgate("gate", "run", "--event", str(event), "--out", str(self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.results()["config_sha"], self.lab.base)
        self.assertTrue((self.lab.repo / "ran.txt").exists())
        self.assertFalse((self.lab.repo / "head.txt").exists())

    def test_cli_base_not_default_is_not_applicable(self):
        event = self.event(ref="release")
        r = self.tollgate("gate", "run", "--event", str(event), "--out", str(self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.results()["applicable"])
        self.assertFalse((self.lab.repo / "ran.txt").exists())

    def test_no_state_created(self):
        event = self.event()
        before = sorted(p.relative_to(self.ts.dir).as_posix() for p in self.ts.dir.rglob("*"))
        r = self.tollgate("gate", "run", "--event", str(event), "--out", str(self.out),
                          PYTHONVERBOSE="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        loaded = re.findall(r"^import '([\w.]+)'", r.stderr, re.M)
        self.assertIn("tollgate_gate.cli", loaded)
        for module in ("tollgate_core.db", "tollgate_core.cli", "sqlite3"):
            self.assertNotIn(module, loaded)
        after = sorted(p.relative_to(self.ts.dir).as_posix() for p in self.ts.dir.rglob("*"))
        self.assertEqual(before, after)
        self.assertEqual(list(self.home.iterdir()), [])


class SetupTest(GateRunBase):
    toml = TOML.replace('[commands]\n', '[commands]\nsetup = "echo global >> order.txt"\n') + """
[profiles.web]
paths = ["web/**"]
setup = "echo web >> order.txt"
commands = { lint = "echo lint >> order.txt" }
gate = ["lint"]
"""

    def order(self):
        return (self.lab.repo / "order.txt").read_text().split()

    def test_setup_runs_before_gate_for_active_profiles_only(self):
        self.lab.commit("src/new.py", "x = 1\n")
        self.assertEqual(self.run_gate(), 0)
        names = [c["name"] for c in self.results()["commands"]]
        self.assertEqual(names, ["setup", "verify"])
        self.assertEqual(self.order(), ["global"])
        out2 = self.out.parent / "art2"
        self.lab.commit("web/a.ts", "x\n")
        self.assertEqual(self.run_gate(out=out2), 0)
        names = [c["name"] for c in json.loads((out2 / "results.json").read_text())["commands"]]
        self.assertEqual(names, ["setup", "profile:web:setup", "verify", "profile:web:lint"])
        self.assertEqual(self.order()[1:], ["global", "web", "lint"])

    def test_failed_setup_is_red_and_gate_does_not_run(self):
        toml = self.toml.replace("echo global >> order.txt", "echo global >> order.txt; exit 3")
        self.lab.commit("tollgate.toml", toml)
        git(self.lab.repo, "push", "-q", "origin", "HEAD:main")
        self.lab.commit("src/new.py", "x = 1\n")
        sha = git(self.lab.repo, "rev-parse", "origin/main")
        self.assertEqual(self.run_gate(config_sha=sha), 0)
        commands = self.results()["commands"]
        self.assertEqual([(c["name"], c["state"]) for c in commands],
                         [("setup", "red"), ("verify", "red")])
        self.assertEqual(commands[0]["exit"], 3)
        self.assertIsNone(commands[1]["exit"])
        self.assertIn("setup", commands[1]["reason"])
        self.assertFalse((self.lab.repo / "ran.txt").exists())

    def test_failed_profile_setup_is_named_after_the_profile(self):
        toml = self.toml.replace("echo web >> order.txt", "exit 1")
        self.lab.commit("tollgate.toml", toml)
        git(self.lab.repo, "push", "-q", "origin", "HEAD:main")
        self.lab.commit("web/a.ts", "x\n")
        sha = git(self.lab.repo, "rev-parse", "origin/main")
        self.assertEqual(self.run_gate(config_sha=sha), 0)
        states = {c["name"]: c["state"] for c in self.results()["commands"]}
        self.assertEqual(states["profile:web:setup"], "red")
        self.assertEqual(states["verify"], "red")


class BaseIdsTest(GateRunBase):
    def test_base_ids_format_and_tree(self):
        result = baseids.compute(self.lab.repo, config_sha=self.lab.base, sha=self.lab.base,
                                 out=self.out, environ=os.environ)
        tree = git(self.lab.repo, "rev-parse", f"{self.lab.base}^{{tree}}")
        self.assertEqual(result, {"v": 1, "tree": tree, "sha": self.lab.base,
                                  "ids": {"verify": ["t::a", "t::b"]},
                                  "commands": {"verify": "green"}})
        self.assertEqual(json.loads((self.out / "ids.json").read_text()), result)
        self.assertEqual(baseids.load(self.out / "ids.json", tree=tree),
                         {"verify": {"t::a", "t::b"}})

    def test_load_rejects_other_tree(self):
        baseids.compute(self.lab.repo, config_sha=self.lab.base, sha=self.lab.base, out=self.out,
                        environ=os.environ)
        self.assertIsNone(baseids.load(self.out / "ids.json", tree="0" * 40))

    def test_load_rejects_deeply_nested_json(self):
        path = self.out.parent / "ids.json"
        path.write_text("[" * 100000)
        self.assertIsNone(baseids.load(path, tree="t"))

    def test_load_returns_none_on_any_exception(self):
        path = self.out.parent / "ids.json"
        path.write_text("{}")
        with mock.patch.object(Path, "read_text", side_effect=RuntimeError("boom")):
            self.assertIsNone(baseids.load(path, tree="t"))

    def test_load_rejects_unreadable_and_malformed(self):
        path = self.out.parent / "ids.json"
        self.assertIsNone(baseids.load(path, tree="t"))
        for text in ("{", "[]", json.dumps({"v": 2, "tree": "t", "ids": {}}),
                     json.dumps({"v": 1, "tree": "t", "ids": []}),
                     json.dumps({"v": 1, "tree": "t", "ids": {"c": "x"}}),
                     json.dumps({"v": 1, "tree": "t", "ids": {"c": [1]}})):
            path.write_text(text)
            with self.subTest(text=text):
                self.assertIsNone(baseids.load(path, tree="t"))

    def test_skipped_ids_are_not_recorded(self):
        script = ("mkdir -p reports\nprintf '<testsuite><testcase classname=\"t\" name=\"a\"/>"
                  "<testcase classname=\"t\" name=\"s\"><skipped/></testcase></testsuite>' "
                  "> reports/junit.xml\n")
        self.lab.commit("check.sh", script)
        result = baseids.compute(self.lab.repo, config_sha=self.lab.base, sha=self.lab.head,
                                 out=self.out, environ=os.environ)
        self.assertEqual(result["ids"], {"verify": ["t::a"]})

    def test_cli_root_is_the_tree_config_is_the_default_tip(self):
        # `--root` è il checkout della base, la CLI gira dal checkout del predefinito (D8)
        root = self.out.parent / "root"
        git(self.lab.repo, "worktree", "add", "-q", "--detach", str(root), self.lab.base)
        self.lab.commit("tollgate.toml", self.toml.replace("sh check.sh", "echo head > head.txt"))
        self.lab.commit("src/new.py", "x = 1\n")
        r = self.tollgate("gate", "base-ids", "--sha", self.lab.base, "--out", str(self.out),
                          "--root", str(root), "--event", str(self.event()))
        self.assertEqual(r.returncode, 0, r.stderr)
        tree = git(self.lab.repo, "rev-parse", f"{self.lab.base}^{{tree}}")
        data = json.loads((self.out / "ids.json").read_text())
        self.assertEqual((data["tree"], data["sha"]), (tree, self.lab.base))
        self.assertTrue((root / "ran.txt").exists())
        self.assertFalse((self.lab.repo / "ran.txt").exists())
        self.assertFalse((self.lab.repo / "head.txt").exists())

    def test_publish_refused_outside_actions(self):
        for env in ({}, {"GITHUB_ACTIONS": "false"}, {"GITHUB_ACTIONS": "1"}):
            with self.subTest(env=env):
                r = self.tollgate("gate", "base-ids", "--sha", self.lab.base, "--out",
                                  str(self.out), "--event", str(self.event()), "--publish", **env)
                self.assertEqual(r.returncode, 2)       # `base-ids` non pubblica più (C-1)
        for env in ({}, {"GITHUB_ACTIONS": "false"}, {"GITHUB_ACTIONS": "1"}):
            with self.subTest(publish_env=env):
                r = self.tollgate("gate", "base-publish", "--ids", str(self.out), "--event",
                                  str(self.event()), "--publish", **env)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("GitHub Actions", r.stderr)

    def test_abbreviated_option_is_an_argument_error(self):
        for opt in ("--publ", "--pub", "--pu"):
            with self.subTest(opt=opt):
                r = self.tollgate("gate", "base-ids", "--sha", self.lab.base, "--out",
                                  str(self.out), "--event", str(self.event()), opt,
                                  GITHUB_ACTIONS="true")
                self.assertEqual(r.returncode, 2)
                self.assertFalse((self.out / "ids.json").exists())

    def test_base_ids_no_state_created(self):
        before = sorted(p.relative_to(self.ts.dir).as_posix() for p in self.ts.dir.rglob("*"))
        r = self.tollgate("gate", "base-ids", "--sha", self.lab.base, "--out", str(self.out),
                          "--event", str(self.event()), PYTHONVERBOSE="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        loaded = re.findall(r"^import '([\w.]+)'", r.stderr, re.M)
        self.assertIn("tollgate_gate.cli", loaded)
        for module in ("tollgate_core.db", "tollgate_core.cli", "sqlite3"):
            self.assertNotIn(module, loaded)
        after = sorted(p.relative_to(self.ts.dir).as_posix() for p in self.ts.dir.rglob("*"))
        self.assertEqual(before, after)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_base_publish_abbreviations_are_argument_errors(self):
        for opt in ("--publ", "--pub", "--pu"):
            with self.subTest(opt=opt):
                r = self.tollgate("gate", "base-publish", "--ids", str(self.out), "--event",
                                  str(self.event()), opt, GITHUB_ACTIONS="true")
                self.assertEqual(r.returncode, 2)


class BaseIdsComponentOffTest(GateRunBase):
    """M-2, decisione 12: con `base_test_ids = false` la suite della base non gira."""
    toml = TOML + "[components]\nbase_test_ids = false\n"

    def test_nothing_runs_and_ids_json_is_valid_and_empty(self):
        r = self.tollgate("gate", "base-ids", "--sha", self.lab.base, "--out", str(self.out),
                          "--event", str(self.event()))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.lab.repo / "ran.txt").exists())
        tree = git(self.lab.repo, "rev-parse", f"{self.lab.base}^{{tree}}")
        self.assertEqual(json.loads((self.out / "ids.json").read_text()),
                         {"v": 1, "tree": tree, "sha": self.lab.base, "ids": {},
                          "commands": {}})
        self.assertEqual(baseids.load(self.out / "ids.json", tree=tree), {})
        self.assertEqual(baseids.publish_from(self.lab.repo, config_sha=self.lab.base,
                                              sha=self.lab.base, ids_dir=self.out,
                                              environ=os.environ, publish=True), 0)


class MainErrorsTest(unittest.TestCase):
    def failing(self, exc):
        buf = io.StringIO()
        with mock.patch.dict(cli.HANDLERS, {"run": mock.Mock(side_effect=exc)}), \
                redirect_stderr(buf):
            code = cli.main(["run", "--event", "e.json", "--out", "o"])
        self.assertEqual(code, 1)
        self.assertIn("gate run:", buf.getvalue())
        self.assertIn("boom", buf.getvalue())
        self.assertNotIn("Traceback", buf.getvalue())

    def test_gh_error(self):
        self.failing(GhError("boom"))

    def test_git_error(self):
        self.failing(GitError("boom"))

    def test_config_error(self):
        self.failing(ConfigError("boom"))

    def test_os_error(self):
        self.failing(OSError("boom"))

    def test_value_error(self):
        self.failing(ValueError("boom"))

    def test_message_cannot_start_a_workflow_command(self):
        # M-8: il testo dell'eccezione passa da `json.dumps`, una riga sola
        buf = io.StringIO()
        exc = ValueError("boom\n::error::x")
        with mock.patch.dict(cli.HANDLERS, {"run": mock.Mock(side_effect=exc)}), \
                redirect_stderr(buf):
            self.assertEqual(cli.main(["run", "--event", "e.json", "--out", "o"]), 1)
        self.assertEqual(buf.getvalue().count("\n"), 1)
        self.assertIn("::error::x", buf.getvalue())
        self.assertFalse(any(line.startswith("::") for line in buf.getvalue().splitlines()))

    def test_bad_event_file_is_a_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "e.json"
            bad.write_text("{")
            buf = io.StringIO()
            with redirect_stderr(buf):
                self.assertEqual(cli.main(["run", "--event", str(bad), "--out", tmp]), 1)
            self.assertNotIn("Traceback", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
