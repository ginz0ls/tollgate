import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.flowkit import SESSION, FlowLab
from tests.helpers import BIN, ROOT, TempState, git, make_repo
from tests.hookkit import sample
from tollgate_core import clock, db, events, paths, phases

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


class CliBase(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.repo = make_repo(Path(tempfile.mkdtemp()) / "r")
        git(self.repo, "remote", "add", "origin", "git@github.com:O/R.git")
        self.outside = Path(tempfile.mkdtemp())

    def tearDown(self):
        self.t.cleanup()

    def run_cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(BIN / "tollgate"), *args],
                              cwd=cwd or self.outside, env=self.t.env(), capture_output=True,
                              text=True, stdin=subprocess.DEVNULL)

    def seed(self):
        conn = db.open_db(self.t.state)
        w = phases.create_work(conn, repo_key="github.com/o/r", issue=5, level="L1", now=T0)
        phases.create_work(conn, repo_key="github.com/o/altro", issue=6, level="L0", now=T0)
        phases.open_block(conn, self.t.state, w, "needs_you", "budget del task 2", now=T0)
        conn.close()
        return w


class CliTest(CliBase):
    def test_no_args_prints_help(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertIn("status", r.stdout)

    def test_help_names_gate(self):
        r = self.run_cli("-h")
        self.assertEqual(r.returncode, 0)
        self.assertIn("gate -h", r.stdout)

    def test_gate_is_dispatched_before_the_core_cli(self):
        r = self.run_cli("gate", "-h")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("base-ids", r.stdout)
        self.assertNotEqual(self.run_cli("gate").returncode, 0)
        self.assertFalse((self.t.dir / "tollgate.db").exists())

    def test_status_filters_by_repo(self):
        self.seed()
        r = self.run_cli("status", cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("#5 github.com/o/r", r.stdout)
        self.assertIn("blocco", r.stdout)
        self.assertIn("budget del task 2", r.stdout)
        self.assertNotIn("#6", r.stdout)
        everywhere = self.run_cli("status")
        self.assertIn("#6", everywhere.stdout)

    def test_status_json(self):
        self.seed()
        r = self.run_cli("status", "--json", cwd=self.repo)
        (item,) = json.loads(r.stdout)
        self.assertEqual((item["issue"], item["phase"], item["phase_before_block"]),
                         (5, "blocked", "plan"))
        self.assertEqual(item["blocks"][0]["type"], "needs_you")

    def test_events_after_seq(self):
        conn = db.open_db(self.t.state)
        for i in range(3):
            events.record_event(conn, "commit", {"i": i}, now=T0)
        conn.close()
        r = self.run_cli("events", "--after-seq", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([json.loads(x)["seq"] for x in r.stdout.splitlines()], [2, 3])

    def test_events_broken_pipe_is_silent(self):
        conn = db.open_db(self.t.state)
        for i in range(200):
            events.record_event(conn, "commit", {"i": i, "pad": "x" * 500}, now=T0)
        conn.close()
        script = (f"{shlex.quote(sys.executable)} {shlex.quote(str(BIN / 'tollgate'))} "
                  "events --after-seq 0 | head -1")
        r = subprocess.run(["sh", "-c", script], env=self.t.env(), capture_output=True,
                           text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(len(r.stdout.splitlines()), 1)
        self.assertEqual(r.stderr, "")

    def test_stats_work(self):
        self.seed()
        r = self.run_cli("stats", "--work", "5", cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["needs_you"], 1)
        missing = self.run_cli("stats", "--work", "99", cwd=self.repo)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("nessun lavoro", missing.stderr)
        outside = self.run_cli("stats", "--work", "5")
        self.assertEqual(outside.returncode, 1)
        self.assertEqual(self.run_cli("stats", "--since", "ieri").returncode, 2)

    def test_corrupt_db(self):
        self.t.state.db_path.write_bytes(os.urandom(4096))
        r = self.run_cli("status")
        self.assertEqual(r.returncode, 1)
        self.assertIn("db restore", r.stderr)
        r = self.run_cli("db", "restore")
        self.assertEqual(r.returncode, 1)
        self.assertIn("terminale", r.stderr)

    def test_restore_refuses_healthy_db(self):
        db.open_db(self.t.state).close()
        r = self.run_cli("db", "restore")
        self.assertEqual(r.returncode, 1)
        self.assertIn("integro", r.stderr)


class StatusReadOnlyTest(CliBase):
    def test_status_without_db_creates_nothing(self):
        before = sorted(p.name for p in self.t.dir.iterdir())
        r = self.run_cli("status", cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nessun lavoro attivo", r.stdout)
        self.assertEqual(sorted(p.name for p in self.t.dir.iterdir()), before)
        self.assertFalse(self.t.state.db_path.exists())
        j = self.run_cli("status", "--json", cwd=self.repo)
        self.assertEqual(json.loads(j.stdout), [])
        self.assertFalse(self.t.state.db_path.exists())

    def test_status_reports_stopped_by(self):
        w = self.seed()
        conn = db.open_db(self.t.state)
        phases.open_block(conn, self.t.state, w, "needs_you",
                          "giri di correzione esauriti sul task 2", now=T0)
        conn.close()
        r = self.run_cli("status", cwd=self.repo)
        self.assertIn("tetto: giri di correzione", r.stdout)
        (item,) = json.loads(self.run_cli("status", "--json", cwd=self.repo).stdout)
        self.assertEqual(len(item["stopped_by"]), 1)

    def test_note_requires_checkpoint(self):
        r = self.run_cli("status", "--note", "x", cwd=self.repo)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--note si usa con --checkpoint", r.stderr)

    def test_checkpoint_without_db_creates_nothing(self):
        before = sorted(p.name for p in self.t.dir.iterdir())
        r = self.run_cli("status", "--checkpoint", cwd=self.repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nessun lavoro attivo", r.stderr)
        self.assertEqual(sorted(p.name for p in self.t.dir.iterdir()), before)
        self.assertFalse(self.t.state.db_path.exists())


class ArgvSignalTest(unittest.TestCase):
    """Il passaggio reale di argv da `cli.main`: il segnale lo scrive l'hook di PreToolUse
    (hooks/run) e vale per un solo lancio con gli stessi argomenti."""

    def setUp(self):
        self.fl = FlowLab()
        self.addCleanup(self.fl.close)
        sha = self.fl.git("rev-parse", "origin/main")
        self.fl.set_gh(
            auth=True, prs=[], issue_list=[],
            issues={"7": {"number": 7, "title": "Aggiungi export CSV", "body": "b",
                          "state": "open", "labels": [], "author_association": "OWNER"}},
            statuses={sha: {"statuses": [{"context": "tollgate/guard", "state": "success"},
                                         {"context": "tollgate/verdict", "state": "success"}]}})

    def signal(self, *argv):
        """PreToolUse Bash attraverso hooks/run: scrive il segnale per `argv`."""
        command = f"{paths.program_command(BIN / 'tollgate')} {' '.join(argv)}"
        r = subprocess.run([str(ROOT / "hooks" / "run"), "PreToolUse"], env=self.fl.env(),
                           input=json.dumps(sample("PreToolUse-Bash", session_id=SESSION,
                                                   cwd=str(self.fl.main),
                                                   tool_input={"command": command})),
                           capture_output=True, text=True, timeout=60)
        self.assertEqual((r.returncode, r.stderr), (0, ""), r.stdout)

    def run_start(self, *argv):
        return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), "start", *argv],
                              cwd=str(self.fl.main), env=self.fl.env(), capture_output=True,
                              text=True, timeout=120)

    def test_second_start_without_new_signal_refused(self):
        self.signal("start", "7")
        first = self.run_start("7")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        second = self.run_start("7")                        # la voce è consumata
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertIn("sessione non riconosciuta", second.stdout + second.stderr)

    def test_level_option_in_argv_matches(self):
        self.signal("start", "7", "--level", "L1")
        r = self.run_start("7", "--level", "L1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("sessione non riconosciuta", r.stdout + r.stderr)
