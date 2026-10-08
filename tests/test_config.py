import tempfile
import unittest
from pathlib import Path

from tests.helpers import TempState, git, make_repo
from tollgate_core.config import (
    ConfigError, ConfigNotFound, load_config, load_config_at, load_config_text,
)

MIN = 'schema_version = 1\n[gate]\nmode = "detect"\n'


class LoadTextTest(unittest.TestCase):
    def test_minimal_gets_defaults(self):
        c = load_config_text(MIN)
        self.assertEqual(c.get("gate.mode"), "detect")
        self.assertEqual(c.get("tasks.max_turns"), 60)
        self.assertEqual(c.get("tasks.max_tokens"), {"L0": 0, "L1": 400000, "L2": 800000})
        self.assertEqual(c.get("acts.ttl_minutes"), 10)
        self.assertEqual(c.get("review.stale_minutes"), 30)
        self.assertEqual(c.get("retention.events_days"), 180)
        self.assertTrue(c.get("components.must_have_tests"))
        self.assertEqual(c.warnings, [])
        self.assertEqual(c.profiles, {})

    def test_missing_schema_version(self):
        with self.assertRaisesRegex(ConfigError, "schema_version"):
            load_config_text('[gate]\nmode = "detect"\n')

    def test_newer_schema_version(self):
        with self.assertRaisesRegex(ConfigError, "aggiornare"):
            load_config_text('schema_version = 2\n[gate]\nmode = "detect"\n')

    def test_missing_mode(self):
        with self.assertRaisesRegex(ConfigError, "gate.mode"):
            load_config_text("schema_version = 1\n")

    def test_bad_mode(self):
        with self.assertRaisesRegex(ConfigError, "gate.mode"):
            load_config_text('schema_version = 1\n[gate]\nmode = "strict"\n')

    def test_invalid_toml(self):
        with self.assertRaisesRegex(ConfigError, "TOML non valido"):
            load_config_text("schema_version = \n")

    def test_unknown_section_and_key_warn(self):
        c = load_config_text(MIN + "[nuova]\nx = 1\n[tasks]\nfoo = 2\nmax_turns = 40\n")
        self.assertIn("sezione sconosciuta: nuova", c.warnings)
        self.assertIn("chiave sconosciuta: tasks.foo", c.warnings)
        self.assertEqual(c.get("tasks.max_turns"), 40)

    def test_wrong_type_is_error(self):
        with self.assertRaisesRegex(ConfigError, "tasks.max_turns"):
            load_config_text(MIN + '[tasks]\nmax_turns = "60"\n')

    def test_bool_where_int_is_error(self):
        with self.assertRaisesRegex(ConfigError, "tasks.max_turns"):
            load_config_text(MIN + "[tasks]\nmax_turns = true\n")

    def test_int_where_bool_is_error(self):
        with self.assertRaisesRegex(ConfigError, "project.allow_no_tests"):
            load_config_text(MIN + "[project]\nallow_no_tests = 1\n")

    def test_list_of_wrong_items_is_error(self):
        with self.assertRaisesRegex(ConfigError, "commands.gate"):
            load_config_text(MIN + "[commands]\ngate = [1]\n")

    def test_open_commands_and_components(self):
        c = load_config_text(MIN + '[commands]\nlint = "npm run lint"\n'
                                   "[components]\nnuovo = false\n")
        self.assertEqual(c.get("commands.lint"), "npm run lint")
        self.assertIs(c.get("components.nuovo"), False)
        with self.assertRaisesRegex(ConfigError, "commands.lint"):
            load_config_text(MIN + "[commands]\nlint = 3\n")
        with self.assertRaisesRegex(ConfigError, "components.nuovo"):
            load_config_text(MIN + '[components]\nnuovo = "no"\n')

    def test_report_string_or_map(self):
        a = load_config_text(MIN + '[commands]\nreport = "junit:r.xml"\n')
        self.assertEqual(a.get("commands.report"), "junit:r.xml")
        b = load_config_text(MIN + '[commands]\nreport = { verify = "junit:r.xml" }\n')
        self.assertEqual(b.get("commands.report"), {"verify": "junit:r.xml"})
        with self.assertRaisesRegex(ConfigError, "commands.report"):
            load_config_text(MIN + "[commands]\nreport = { verify = 1 }\n")

    def test_max_tokens_map_of_ints(self):
        with self.assertRaisesRegex(ConfigError, "tasks.max_tokens"):
            load_config_text(MIN + '[tasks]\nmax_tokens = { L1 = "molti" }\n')

    def test_profiles(self):
        c = load_config_text(MIN + '[profiles]\nactive = ["web"]\n'
                                   '[profiles.web]\npaths = ["web/**"]\nskills = ["ui-ux-pro-max"]\nextra = 1\n')
        self.assertEqual(c.get("profiles.active"), ["web"])
        web = c.profiles["web"]
        self.assertEqual(web["paths"], ["web/**"])
        self.assertEqual(web["kind"], "vertical")
        self.assertEqual(web["min_level"], "L0")
        self.assertIn("chiave sconosciuta: profiles.web.extra", c.warnings)
        with self.assertRaisesRegex(ConfigError, "profiles.web.kind"):
            load_config_text(MIN + '[profiles.web]\nkind = "orizzontale"\n')
        with self.assertRaisesRegex(ConfigError, "profiles.web.min_level"):
            load_config_text(MIN + '[profiles.web]\nmin_level = "L3"\n')
        with self.assertRaisesRegex(ConfigError, "profiles.web"):
            load_config_text(MIN + "[profiles]\nweb = 3\n")


class LoadFromGitTest(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo(Path(tempfile.mkdtemp()) / "r")
        (self.repo / "tollgate.toml").write_text(MIN + "[tasks]\nmax_turns = 41\n")
        git(self.repo, "add", "tollgate.toml")
        git(self.repo, "commit", "-qm", "c")
        (self.repo / "tollgate.toml").write_text(MIN + "[tasks]\nmax_turns = 99\n")

    def test_reads_ref_not_working_tree(self):
        self.assertEqual(load_config_at(self.repo, "HEAD").get("tasks.max_turns"), 41)

    def test_missing_file(self):
        git(self.repo, "rm", "-q", "--cached", "tollgate.toml")
        git(self.repo, "commit", "-qm", "rm")
        with self.assertRaises(ConfigNotFound):
            load_config_at(self.repo, "HEAD")

    def test_test_config_override_only_in_test_mode(self):
        t = TempState()
        try:
            f = t.dir / "test.toml"
            f.write_text(MIN + "[tasks]\nmax_turns = 7\n")
            env = {"TOLLGATE_STATE": str(t.dir), "TOLLGATE_TEST_CONFIG": str(f)}
            self.assertEqual(load_config(t.state, self.repo, "HEAD", env).get("tasks.max_turns"), 7)
            from tollgate_core.paths import State
            real = State(t.dir, False)
            self.assertEqual(load_config(real, self.repo, "HEAD", env).get("tasks.max_turns"), 41)
        finally:
            t.cleanup()
