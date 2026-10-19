import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_active_profile_not_declared_warns(self):
        cfg = load_config_text(
            'schema_version = 1\n[gate]\nmode = "protected"\n'
            '[profiles]\nactive = ["web"]\n')
        self.assertIn("profilo attivo non dichiarato: web", cfg.warnings)

    def test_active_profile_declared_gives_no_warning(self):
        cfg = load_config_text(
            'schema_version = 1\n[gate]\nmode = "protected"\n'
            '[profiles]\nactive = ["web"]\n[profiles.web]\npaths = ["web/**"]\n')
        self.assertEqual(cfg.warnings, [])


class ProfileNamesTest(unittest.TestCase):
    def prof(self, body):
        return load_config_text(MIN + "[profiles.web]\n" + body)

    def test_bad_reviewer_name_falls_back_with_warning(self):
        c = self.prof('reviewer = "acme:code-review"\n')
        self.assertEqual(c.profiles["web"]["reviewer"], "")
        self.assertIn("profilo web: reviewer «acme:code-review» non ha la forma "
                      "<plugin>:reviewer-<area>: uso l'agente generico", c.warnings)

    def test_each_key_has_its_own_form(self):
        c = self.prof('agent = "acme:reviewer-web"\nfinal_specialist = "acme:implementer-web"\n')
        self.assertEqual((c.profiles["web"]["agent"], c.profiles["web"]["final_specialist"]),
                         ("", ""))
        self.assertEqual(len(c.warnings), 2)

    def test_good_names_kept(self):
        c = self.prof('agent = "acme:implementer-web"\nreviewer = "acme:reviewer-web-ui"\n'
                      'final_specialist = "acme:final-web"\n')
        w = c.profiles["web"]
        self.assertEqual((w["agent"], w["reviewer"], w["final_specialist"]),
                         ("acme:implementer-web", "acme:reviewer-web-ui", "acme:final-web"))
        self.assertEqual(c.warnings, [])

    def test_blocking_rules_type(self):
        with self.assertRaisesRegex(ConfigError, "profiles.web.blocking_rules"):
            self.prof('blocking_rules = "R-WEB-1"\n')

    def test_blocking_rule_must_be_known(self):
        with self.assertRaisesRegex(ConfigError, "R-X-1"):
            self.prof('blocking_rules = ["R-X-1"]\n')
        c = self.prof('rules = ["R-X-1", "R-X-2"]\nblocking_rules = ["R-X-1"]\n')
        self.assertEqual(c.profiles["web"]["blocking_rules"], ["R-X-1"])


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

    def test_accented_text_round_trips(self):
        (self.repo / "tollgate.toml").write_text(
            MIN + '[severity]\nminor = "redazionalità"\n', encoding="utf-8")
        git(self.repo, "commit", "-qam", "accenti")
        self.assertEqual(load_config_at(self.repo, "HEAD").get("severity.minor"), "redazionalità")

    def test_invalid_utf8_committed_is_config_error(self):
        (self.repo / "tollgate.toml").write_bytes(MIN.encode() + b'[severity]\nminor = "\xff\xfe"\n')
        git(self.repo, "commit", "-qam", "bytes")
        with self.assertRaises(ConfigError):
            load_config_at(self.repo, "HEAD")

    def test_unknown_ref_is_plain_config_error(self):
        with self.assertRaises(ConfigError) as cm:
            load_config_at(self.repo, "nonesiste")
        self.assertIs(type(cm.exception), ConfigError)

    def test_git_missing_is_config_error(self):
        with mock.patch("tollgate_core.config.subprocess.run", side_effect=FileNotFoundError("git")):
            with self.assertRaisesRegex(ConfigError, "git non disponibile"):
                load_config_at(self.repo, "HEAD")

    def test_invalid_utf8_override_is_config_error(self):
        t = TempState()
        try:
            f = t.dir / "test.toml"
            f.write_bytes(MIN.encode() + b'[severity]\nminor = "\xff\xfe"\n')
            env = {"TOLLGATE_STATE": str(t.dir), "TOLLGATE_TEST_CONFIG": str(f)}
            with self.assertRaises(ConfigError):
                load_config(t.state, self.repo, "HEAD", env)
        finally:
            t.cleanup()

    def test_missing_override_is_config_error(self):
        t = TempState()
        try:
            f = t.dir / "non-esiste.toml"
            env = {"TOLLGATE_STATE": str(t.dir), "TOLLGATE_TEST_CONFIG": str(f)}
            with self.assertRaisesRegex(ConfigError, "non-esiste.toml"):
                load_config(t.state, self.repo, "HEAD", env)
        finally:
            t.cleanup()

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
