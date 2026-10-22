import tempfile
import textwrap
import unittest
from pathlib import Path

from tollgate_analysis.junit import Junit
from tollgate_core import runner, verify
from tollgate_core.config import load_config_text

TOML = textwrap.dedent('''
    schema_version = 1
    [gate]
    mode = "protected"
    [commands]
    verify = "sh check.sh"
    gate = ["verify"]
    report = "junit:reports/junit.xml"
    [profiles.web]
    paths = ["web/**"]
    commands = { lint = "sh lint.sh", e2e = "sh e2e.sh" }
    gate = ["lint"]
    dod = ["e2e"]
    report = { lint = "junit:reports/lint.xml" }
''')


class ExecutedIdsTest(unittest.TestCase):
    def test_executed_ids(self):
        junit = Junit(total=4, skipped=1, failed=1, ids_run=["t.a", "t.b"],
                      ids_skipped=["t.c"], ids_failed=["t.d"])
        self.assertEqual(runner.executed_ids(junit), {"t.a", "t.b", "t.d"})

    def test_failed_counted_skipped_excluded(self):
        junit = Junit(ids_run=["t.a"], ids_skipped=["t.a", "t.s"], ids_failed=["t.f"])
        self.assertEqual(runner.executed_ids(junit), {"t.f"})
        self.assertEqual(runner.executed_ids(Junit()), set())


class IdsCommandsTest(unittest.TestCase):
    def test_ids_commands_ignore_paths(self):
        cfg = load_config_text(TOML)
        self.assertEqual([c.name for c in runner.ids_commands(cfg)],
                         ["verify", "profile:web:lint"])
        by_name = {c.name: c for c in runner.ids_commands(cfg)}
        self.assertEqual(by_name["profile:web:lint"].command, "sh lint.sh")
        self.assertEqual(by_name["profile:web:lint"].report, "junit:reports/lint.xml")
        # il diff non c'entra: `gate_commands` senza file del profilo non lo include
        self.assertEqual([c.name for c in runner.gate_commands(cfg, ["src/a.py"])], ["verify"])
        self.assertEqual([c.name for c in runner.gate_commands(cfg, ["web/a.ts"])],
                         ["verify", "profile:web:lint"])


class VerifyNamesTest(unittest.TestCase):
    def test_verify_names_still_importable(self):
        from tollgate_core.verify import CommandSpec, gate_commands, dod_commands, counts_green
        self.assertIs(CommandSpec, runner.CommandSpec)
        self.assertIs(gate_commands, runner.gate_commands)
        self.assertIs(dod_commands, runner.dod_commands)
        self.assertIs(counts_green, runner.counts_green)
        self.assertIs(verify._run_one, runner.run_one)
        self.assertIs(verify._report_path, runner.report_path)
        for name in ("receipt_state", "clean_env", "executed_ids", "TIMEOUT_EXIT"):
            self.assertIs(getattr(verify, name), getattr(runner, name))


class RunOneTest(unittest.TestCase):
    def test_run_one_reads_junit_and_state(self):
        with tempfile.TemporaryDirectory(prefix="tollgate runner ") as tmp:
            root, logs = Path(tmp) / "repo", Path(tmp) / "logs"
            root.mkdir()
            logs.mkdir()
            spec = runner.CommandSpec(
                "verify", "mkdir -p r && echo '<testsuite><testcase classname=\"t\" name=\"a\"/>"
                "</testsuite>' > r/j.xml", "junit:r/j.xml")
            resolved, code, junit, duration, state, log = runner.run_one(
                spec, root=root, files=[], env={"PATH": "/usr/bin:/bin"}, timeout_s=20,
                allow_no_tests=False, log_dir=logs, tag="t")
            self.assertEqual((code, state, junit.total), (0, "green", 1))
            self.assertTrue(log.is_file())
            self.assertGreaterEqual(duration, 0)

    def test_bogus_report_encoding_is_a_red_run_not_an_exception(self):
        with tempfile.TemporaryDirectory(prefix="tollgate runner ") as tmp:
            root, logs = Path(tmp) / "repo", Path(tmp) / "logs"
            root.mkdir()
            logs.mkdir()
            spec = runner.CommandSpec(
                "verify", "echo '<?xml version=\"1.0\" encoding=\"bogus\"?><testsuite/>' > j.xml",
                "junit:j.xml")
            _resolved, _code, junit, _dur, state, _log = runner.run_one(
                spec, root=root, files=[], env={"PATH": "/usr/bin:/bin"}, timeout_s=20,
                allow_no_tests=False, log_dir=logs, tag="t")
            self.assertIsNone(junit)
            self.assertEqual(state, "red")

    def test_report_path_refuses_escape(self):
        from tollgate_core.config import ConfigError
        with self.assertRaises(ConfigError):
            runner.report_path("junit:../x.xml")
        self.assertIsNone(runner.report_path(""))
        self.assertEqual(runner.report_path("junit:a/b.xml"), "a/b.xml")


if __name__ == "__main__":
    unittest.main()
