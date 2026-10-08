import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import BIN, TempState, git, make_repo
from tollgate_core import clock, db, events, phases

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


class CliTest(unittest.TestCase):
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

    def test_no_args_prints_help(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertIn("status", r.stdout)

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
