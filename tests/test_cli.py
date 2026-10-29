import json
import os
import pty
import select
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.flowkit import SESSION, FlowLab
from tests.helpers import BIN, ROOT, TempState, git, make_repo
from tests.hookkit import sample
from tollgate_analysis import research
from tollgate_core import clock, db, events, paths, phases, tasks

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

    def test_status_points_to_limits(self):
        limits = ROOT / "docs" / "uso" / "limiti.md"
        self.assertTrue(limits.is_file())
        line = f"limiti della garanzia: {limits}"
        self.seed()
        for cwd in (self.repo, self.outside):
            with self.subTest(cwd=cwd.name):
                r = self.run_cli("status", cwd=cwd)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.splitlines()[-1], line)
                self.assertTrue(Path(line.split(": ", 1)[1]).is_absolute())
        # mai nell'uscita strutturata
        self.assertNotIn("limiti della garanzia", self.run_cli("status", "--json").stdout)

    def test_status_without_db_points_to_limits(self):
        line = f"limiti della garanzia: {ROOT / 'docs' / 'uso' / 'limiti.md'}"
        self.assertFalse(self.t.state.db_path.exists())
        r = self.run_cli("status")
        self.assertEqual(r.stdout.splitlines(), ["nessun lavoro attivo", line])
        r = self.run_cli("status", "--json")
        self.assertEqual(r.stdout.strip(), "[]")
        self.assertFalse(self.t.state.db_path.exists())

    def test_status_detect_sentence(self):
        sentence = "in modalità detect il merge non è impedito, solo rilevato"
        conn = db.open_db(self.t.state)
        w = phases.create_work(conn, repo_key="github.com/o/r", issue=5, level="L1", now=T0,
                               gate_mode="detect")
        phases.create_work(conn, repo_key="github.com/o/p", issue=7, level="L1", now=T0,
                           gate_mode="protected")
        conn.close()
        r = self.run_cli("status", cwd=self.repo)
        self.assertEqual(r.stdout.count(sentence), 1)
        self.assertNotIn(sentence, self.run_cli("status", "--json", cwd=self.repo).stdout)
        # nessun lavoro in detect nel repo corrente: la frase non c'è
        protected = make_repo(Path(tempfile.mkdtemp()) / "p")
        git(protected, "remote", "add", "origin", "git@github.com:O/P.git")
        self.assertNotIn(sentence, self.run_cli("status", cwd=protected).stdout)
        # fuori da un repo si guardano tutti i lavori attivi
        self.assertIn(sentence, self.run_cli("status").stdout)
        self.assertIsNotNone(w)

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

    def test_status_without_git_is_message_not_traceback(self):
        self.seed()
        no_git = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, no_git, ignore_errors=True)
        env = {**self.t.env(), "PATH": str(no_git)}
        for args in (("status",), ("status", "--json"), ("stats", "--work", "5")):
            with self.subTest(args=args):
                r = subprocess.run([sys.executable, str(BIN / "tollgate"), *args], cwd=self.repo,
                                   env=env, capture_output=True, text=True,
                                   stdin=subprocess.DEVNULL)
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn("git non disponibile", r.stderr)
                self.assertNotIn("Traceback", r.stderr)

    def corrupt_db_with_backup(self):
        """Un DB guasto e una copia integra con un lavoro dentro."""
        conn = db.open_db(self.t.state)
        phases.create_work(conn, repo_key="github.com/o/r", issue=5, level="L1", now=T0)
        db.backup(conn, self.t.state, "fase")
        conn.close()
        for suffix in ("", "-wal", "-shm"):
            p = self.t.state.db_path.with_name(self.t.state.db_path.name + suffix)
            if p.exists():
                p.unlink()
        self.t.state.db_path.write_bytes(os.urandom(4096))
        return self.t.state.db_path.read_bytes()

    def restore_on_pty(self, answer):
        """`db restore` con stdin e stdout su un pseudo-terminale. `answer` riceve il PID e il
        descrittore principale quando il prompt è comparso; dà (uscita, uscita dei due flussi: il
        prompt di `input()` passa da stderr, perciò stdout e stderr vanno sullo stesso pty)."""
        master, slave = pty.openpty()
        try:
            with subprocess.Popen([sys.executable, str(BIN / "tollgate"), "db", "restore"],
                                  cwd=self.outside, env=self.t.env(), stdin=slave, stdout=slave,
                                  stderr=slave, start_new_session=True) as proc:
                os.close(slave)
                slave = -1
                out = self.read_pty(master, proc, until="[s/N] ")
                answer(proc.pid, master)
                out += self.read_pty(master, proc)
                code = proc.wait(timeout=30)
                return code, out
        finally:
            if slave != -1:
                os.close(slave)
            os.close(master)

    @staticmethod
    def read_pty(master, proc, until=None):
        """Legge dal pty finché compare `until` o il processo chiude (EIO a fine lettura)."""
        out = ""
        while until is None or until not in out:
            ready, _, _ = select.select([master], [], [], 30)
            if not ready:
                proc.kill()
                raise AssertionError(f"nessun output dal pty: {out!r}")
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            out += chunk.decode(errors="replace")
        return out

    def test_db_restore_interactive_eof_and_ctrl_c(self):
        broken = self.corrupt_db_with_backup()
        cases = {"EOF": lambda pid, master: os.write(master, b"\x04"),
                 "Ctrl-C": lambda pid, master: os.kill(pid, signal.SIGINT)}
        for name, answer in cases.items():
            with self.subTest(name):
                code, out = self.restore_on_pty(answer)
                self.assertEqual(code, 1, out)
                self.assertIn("annullato", out)
                self.assertNotIn("Traceback", out)
                self.assertEqual(self.t.state.db_path.read_bytes(), broken)
                self.assertFalse(self.t.state.broken_dir.exists()
                                 and any(self.t.state.broken_dir.iterdir()))

    def test_db_restore_interactive_confirm_from_cli(self):
        self.corrupt_db_with_backup()
        code, out = self.restore_on_pty(lambda pid, master: os.write(master, b"s\n"))
        self.assertEqual(code, 0, out)
        self.assertNotIn("Traceback", out)
        self.assertIn("ripristinata la copia", out)
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)
        self.assertEqual(len(list(self.t.state.broken_dir.rglob("tollgate.db"))), 1)


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


class ResearchCliTest(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab(issue=7, phase="plan")
        self.addCleanup(self.fl.close)
        self.fl.register_plan(1)
        tasks.assign(self.fl.conn, self.fl.work, 1, implementer="impl-1",
                     agent_type="tollgate:implementer", reviewer_type="tollgate:task-reviewer",
                     pending="launch", now=self.fl.now)
        tasks.task_event(self.fl.conn, self.fl.work, 1, "start", now=self.fl.now)
        self.fl.conn.execute("UPDATE work_items SET research = 1")
        self.fl.conn.commit()

    def run_research(self, *argv, stdin=""):
        return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), "research", *argv],
                              cwd=str(self.fl.wt), env=self.fl.env(), input=stdin,
                              capture_output=True, text=True, timeout=120)

    def test_research_submit_reads_stdin(self):
        note = ("## Letto nel progetto\n- src/app.py\n\n## Nessuna fonte esterna\nsolo codice\n\n"
                "## Cosa ho trovato\nniente di strano\n")
        r = self.run_research("submit", "1", stdin=note)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)   # src/app.py non è stato letto
        self.assertIn("src/app.py", r.stderr)
        self.assertEqual(tasks.get_task(self.fl.conn, self.fl.work, 1)["research_note"], note)
        shown = self.run_research("show", "1")
        self.assertEqual(shown.returncode, 1)
        self.assertIn("niente di strano", shown.stdout)
        self.assertTrue(shown.stdout.rstrip().endswith("esito: non valida"))

    def test_research_submit_reads_a_bounded_stdin(self):
        big = "## Cosa ho trovato\n" + "x" * (50 * research.MAX_NOTE_CHARS)
        r = self.run_research("submit", "1", stdin=big)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"nota oltre {research.MAX_NOTE_CHARS} caratteri", r.stderr)
        self.assertEqual(len(tasks.get_task(self.fl.conn, self.fl.work, 1)["research_note"]),
                         research.MAX_NOTE_CHARS)

    def test_research_submit_refused_exit_2(self):
        r = self.run_research("submit", "9", stdin="x")
        self.assertEqual(r.returncode, 2)
        self.assertIn("inesistente", r.stderr)
