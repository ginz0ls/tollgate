import contextlib
import io
import os
import shutil
import sqlite3
import tempfile
import textwrap
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.helpers import TempState, git, make_origin_repo
from tollgate_core import config, db, phases, verify
from tollgate_core.git import GitError
from tollgate_core.paths import repo_key
from tollgate_analysis.junit import Junit

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
TOML = textwrap.dedent('''
    schema_version = 1
    [gate]
    mode = "protected"
    [commands]
    verify = "sh check.sh"
    test_related = "sh related.sh {files}"
    gate = ["verify"]
    report = "junit:reports/junit.xml"
    report_related = "junit:reports/junit-related.xml"
    env_allow = ["PATH", "HOME"]
    [profiles.web]
    paths = ["web/**"]
    commands = { lint = "sh lint.sh" }
    gate = ["lint"]
''')
CHECK = textwrap.dedent('''
    mkdir -p reports
    test -n "$SEGRETO" && echo "segreto visibile" && exit 3
    cat > reports/junit.xml <<EOF
    <testsuite><testcase classname="t" name="a"/><testcase classname="t" name="b"><skipped/></testcase></testsuite>
    EOF
''')
# reports/found (file di prova, ignorato da git) decide se il test correlato trova test
RELATED = textwrap.dedent('''
    mkdir -p reports
    if [ -f reports/found ]; then
      echo '<testsuite><testcase classname="t" name="r"/></testsuite>' > reports/junit-related.xml
    else
      echo '<testsuite/>' > reports/junit-related.xml
    fi
''')


class VerifyUnitTest(unittest.TestCase):
    def test_receipt_state(self):
        j = Junit(total=2, skipped=0, failed=0)
        st = verify.receipt_state
        self.assertEqual(st(exit_code=0, report_configured=True, junit=j, allow_no_tests=False),
                         "green")
        self.assertEqual(st(exit_code=1, report_configured=True, junit=j, allow_no_tests=False),
                         "red")
        self.assertEqual(st(exit_code=0, report_configured=True,
                            junit=Junit(total=1, failed=1), allow_no_tests=False), "red")
        self.assertEqual(st(exit_code=0, report_configured=True, junit=Junit(),
                            allow_no_tests=False), "empty")
        self.assertEqual(st(exit_code=0, report_configured=True, junit=None,
                            allow_no_tests=True), "red")
        self.assertEqual(st(exit_code=0, report_configured=False, junit=None,
                            allow_no_tests=True), "uncounted")

    def test_clean_env(self):
        self.assertEqual(verify.clean_env(["PATH"], {"PATH": "/bin", "TOKEN": "x"}),
                         {"PATH": "/bin"})

    def test_gate_commands_with_profiles(self):
        cfg = config.load_config_text(TOML)
        names = [c.name for c in verify.gate_commands(cfg, ["src/a.py"])]
        self.assertEqual(names, ["verify"])
        names = [c.name for c in verify.gate_commands(cfg, ["web/a.ts"])]
        self.assertEqual(names, ["verify", "profile:web:lint"])


class VerifyRunTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-verify-"))
        self.main, _, self.base = make_origin_repo(
            self.tmp, {"check.sh": CHECK, "related.sh": RELATED,
                       ".gitignore": "reports/\n"}, TOML)
        self.wt = self.tmp / "wt"
        git(self.main, "worktree", "add", "-q", "-b", "tg/7-x", str(self.wt))
        conn = db.open_db(self.ts.state)
        self.work = phases.create_work(conn, repo_key=repo_key(str(self.tmp / "origin.git")),
                                       issue=7, level="L1", now=T0, worktree=str(self.wt),
                                       branch="tg/7-x", work_base_sha=self.base)
        conn.close()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _receipts(self):
        conn = db.open_db(self.ts.state)
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM receipts ORDER BY id")]
        finally:
            conn.close()

    def _commit_src(self):
        (self.wt / "src").mkdir(exist_ok=True)
        (self.wt / "src" / "a.py").write_text("x = 1\n")
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-qm", "src")

    def test_green_receipt_and_clean_env(self):
        (self.wt / "reports").mkdir()
        (self.wt / "reports" / "junit.xml").write_text("<vecchio/>")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin", "SEGRETO": "x"})
        self.assertEqual(code, 0, lines)
        r = self._receipts()[0]
        self.assertEqual((r["state"], r["tests_run"], r["tests_skipped"], r["work"], r["sha"]),
                         ("green", 1, 1, self.work, self.base))

    def test_dirty_worktree_refused(self):
        (self.wt / "sporco.txt").write_text("x")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 1)
        self.assertIn("worktree non pulito", " ".join(lines))
        self.assertEqual(self._receipts(), [])

    def test_config_read_from_work_base(self):
        (self.wt / "tollgate.toml").write_text(TOML.replace('verify = "sh check.sh"', ""))
        git(self.wt, "commit", "-qam", "senza verify")
        code, _ = verify.run_verify(self.ts.state, self.wt, now=T0,
                                    environ={"PATH": "/usr/bin:/bin"})
        # la configurazione si legge dalla base del lavoro, non dal working tree (3.2)
        self.assertEqual(self._receipts()[0]["state"], "green")
        self.assertEqual(code, 0)

    def test_missing_command_is_unverified(self):
        cfg = self.tmp / "cfg.toml"
        cfg.write_text(TOML.replace('verify = "sh check.sh"\n', ""))
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin",
                                                 "TOLLGATE_TEST_CONFIG": str(cfg)})
        self.assertEqual(code, 1)
        self.assertEqual(self._receipts()[0]["state"], "unverified")
        self.assertIn("approve unverified-tests", " ".join(lines))

    def test_related_without_files_runs_gate(self):
        code, lines = verify.run_verify(self.ts.state, self.wt, related=True, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual([r["command"] for r in self._receipts()], ["verify"])
        self.assertEqual(code, 0, lines)

    def test_related_with_tests_records_only_related(self):
        self._commit_src()
        (self.wt / "reports").mkdir()
        (self.wt / "reports" / "found").write_text("")
        code, lines = verify.run_verify(self.ts.state, self.wt, related=True, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 0, lines)
        receipts = self._receipts()
        self.assertEqual([r["command"] for r in receipts], ["related"])
        self.assertEqual(receipts[0]["state"], "green")

    def test_related_without_tests_falls_back_to_gate(self):
        # decisione 12: nessun test correlato, si esegue il gate completo
        self._commit_src()
        code, lines = verify.run_verify(self.ts.state, self.wt, related=True, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 0, lines)
        self.assertEqual([r["command"] for r in self._receipts()], ["related", "verify"])
        self.assertIn("gate completo", " ".join(lines))

    def test_work_without_base_sha_uses_default_ref(self):
        # C13: senza work_base_sha non si passa None a git.changes, si usa il ref di base
        conn = db.open_db(self.ts.state)
        with db.tx(conn):
            conn.execute("UPDATE work_items SET work_base_sha = NULL")
        conn.close()
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 0, lines)
        self.assertEqual(self._receipts()[0]["state"], "green")

    def test_git_error_is_reported_not_raised(self):
        with mock.patch("tollgate_core.git.changes", side_effect=GitError("timeout")):
            code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                            environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 1)
        self.assertIn("timeout", " ".join(lines))

    # --- Fix round 1 ---

    def _env(self, text):
        """Ambiente con una configurazione di prova (TOLLGATE_TEST_CONFIG, solo con la sentinella)."""
        p = self.tmp / "cfg.toml"
        p.write_text(text)
        return {"PATH": "/usr/bin:/bin", "TOLLGATE_TEST_CONFIG": str(p)}

    def _cfg(self, verify_cmd, timeout_s=5, extra=""):
        return textwrap.dedent(f'''
            schema_version = 1
            [gate]
            mode = "protected"
            [commands]
            verify = {verify_cmd!r}
            gate = ["verify"]
            report = "junit:reports/junit.xml"
            env_allow = ["PATH"]
            timeout_s = {timeout_s}
            {extra}
        ''')

    def test_timeout_kills_the_whole_process_group(self):
        # un figlio in background non deve sopravvivere al timeout (SIGKILL al gruppo)
        sentinel = self.tmp / "sentinella"
        env = self._env(self._cfg(f'(sleep 2; touch "{sentinel}") & sleep 7', timeout_s=1))
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0, environ=env)
        time.sleep(3)
        self.assertEqual(code, 1, lines)
        self.assertFalse(sentinel.exists(), "il figlio è sopravvissuto al timeout")
        r = self._receipts()[0]
        self.assertEqual((r["state"], r["exit"]), ("red", 124))

    def test_timeout_is_written_to_log(self):
        env = self._env(self._cfg("sleep 7", timeout_s=1))
        verify.run_verify(self.ts.state, self.wt, now=T0, environ=env)
        log = Path(self._receipts()[0]["log"]).read_text()
        self.assertIn("[tollgate] timeout dopo 1 s", log)

    def test_stdin_is_devnull(self):
        # con stdin chiuso `read` fallisce subito (uscita 7) invece di attendere
        # stdin del processo: una pipe aperta senza dati, come un terminale che non risponde
        env = self._env(self._cfg("if read x; then exit 0; else exit 7; fi", timeout_s=5))
        r, w = os.pipe()
        saved = os.dup(0)
        try:
            os.dup2(r, 0)
            code, _ = verify.run_verify(self.ts.state, self.wt, now=T0, environ=env)
        finally:
            os.dup2(saved, 0)
            for fd in (saved, r, w):
                os.close(fd)
        self.assertEqual(code, 1)
        self.assertEqual(self._receipts()[0]["exit"], 7)

    def test_clean_env_never_passes_tollgate_vars(self):
        self.assertEqual(
            verify.clean_env(["PATH", "TOLLGATE_STATE", "TOLLGATE_TEST_CONFIG"],
                             {"PATH": "/bin", "TOLLGATE_STATE": "x",
                              "TOLLGATE_TEST_CONFIG": "y"}),
            {"PATH": "/bin"})

    def test_report_outside_worktree_is_refused(self):
        outside = self.tmp / "fuori.xml"
        outside.write_text("<testsuite><testcase name='a'/></testsuite>")
        for rel in (str(outside), "../fuori.xml"):
            with self.subTest(report=rel):
                env = self._env(textwrap.dedent(f'''
                    schema_version = 1
                    [gate]
                    mode = "protected"
                    [commands]
                    verify = "true"
                    gate = ["verify"]
                    report = "junit:{rel}"
                '''))
                code, lines = verify.run_verify(self.ts.state, self.wt, now=T0, environ=env)
                self.assertEqual(code, 1)
                self.assertIn("report", " ".join(lines))
                self.assertTrue(outside.exists(), "un file fuori dal worktree è stato cancellato")
                self.assertEqual(self._receipts(), [])

    def test_uncounted_related_explains_the_red_verdict(self):
        self._commit_src()
        env = self._env(textwrap.dedent('''
            schema_version = 1
            [gate]
            mode = "protected"
            [commands]
            verify = "sh check.sh"
            test_related = "true {files}"
            gate = ["verify"]
            report = "junit:reports/junit.xml"
            env_allow = ["PATH"]
        '''))
        code, lines = verify.run_verify(self.ts.state, self.wt, related=True, now=T0,
                                        environ=env)
        self.assertEqual(code, 1)
        text = " ".join(lines)
        self.assertIn("uncounted", text)
        self.assertIn("allow_no_tests", text)
        self.assertIn("rosso", text)

    def test_failing_command_without_report_is_red(self):
        env = self._env(self._cfg("exit 3"))
        code, _ = verify.run_verify(self.ts.state, self.wt, now=T0, environ=env)
        self.assertEqual(code, 1)
        r = self._receipts()[0]
        self.assertEqual((r["state"], r["exit"]), ("red", 3))

    def test_old_report_is_removed_before_run(self):
        # Il comando non scrive il report: un report vecchio con test verdi non deve dare green.
        (self.wt / "reports").mkdir()
        (self.wt / "reports" / "junit.xml").write_text(
            '<testsuite><testcase classname="t" name="a"/></testsuite>')
        code, _ = verify.run_verify(self.ts.state, self.wt, now=T0,
                                    environ=self._env(self._cfg("exit 0")))
        self.assertFalse((self.wt / "reports" / "junit.xml").exists())
        self.assertEqual(code, 1)
        self.assertEqual(self._receipts()[0]["state"], "red")

    def test_work_none_leaves_work_null(self):
        # esecuzione dal checkout principale, fuori dal worktree di un lavoro
        code, lines = verify.run_verify(self.ts.state, self.main, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 0, lines)
        r = self._receipts()[0]
        self.assertIsNone(r["work"])
        self.assertEqual(r["state"], "green")

    def test_config_error_is_exit_1(self):
        env = self._env("schema_version = 99\n")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0, environ=env)
        self.assertEqual(code, 1)
        self.assertIn("schema_version", " ".join(lines))
        self.assertEqual(self._receipts(), [])

    def test_sqlite_error_is_reported_not_raised(self):
        with mock.patch("tollgate_core.receipts.add",
                        side_effect=sqlite3.OperationalError("disk I/O error")):
            code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                            environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 1)
        self.assertIn("database", " ".join(lines))


class VerifyCliTest(unittest.TestCase):
    def test_sqlite_error_in_cli_is_exit_1_without_traceback(self):
        from tollgate_core import cli
        ts = TempState()
        try:
            err = io.StringIO()
            with mock.patch.dict(os.environ, {"TOLLGATE_STATE": str(ts.dir)}), \
                    mock.patch("tollgate_core.verify.run_verify",
                               side_effect=sqlite3.OperationalError("disk I/O error")), \
                    contextlib.redirect_stderr(err):
                code = cli.main(["verify"])
            self.assertEqual(code, 1)
            self.assertIn("tollgate:", err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())
        finally:
            ts.cleanup()


if __name__ == "__main__":
    unittest.main()
