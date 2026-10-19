import json
import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, sessions

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class SessionsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_alive_by_last_seen(self):
        sessions.touch(self.conn, "s1", now=T0)
        self.assertTrue(sessions.alive(self.conn, "s1", now=T0 + timedelta(minutes=29),
                                       stale_minutes=30))
        self.assertFalse(sessions.alive(self.conn, "s1", now=T0 + timedelta(minutes=31),
                                        stale_minutes=30))
        self.assertFalse(sessions.alive(self.conn, "mai-vista", now=T0, stale_minutes=30))

    def test_bound_work_and_path(self):
        wt = self.ts.dir / "wt 7"
        (wt / "src").mkdir(parents=True)
        w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                               session="s1", worktree=str(wt))
        self.assertEqual(sessions.bound_work(self.conn, "s1")["id"], w)
        self.assertIsNone(sessions.bound_work(self.conn, "s2"))
        self.assertEqual(sessions.work_for_path(self.conn, wt / "src" / "nuovo.py")["id"], w)
        self.assertIsNone(sessions.work_for_path(self.conn, self.ts.dir / "altro"))

    def test_closed_work_is_not_bound(self):
        w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                               session="s1")
        phases.set_phase(self.conn, self.ts.state, w, "closed", "abandoned", now=T0)
        self.assertIsNone(sessions.bound_work(self.conn, "s1"))

    def test_mark_bound_creates_marker(self):
        sessions.mark_bound(self.ts.state, "s1")
        self.assertTrue((self.ts.dir / sessions.BOUND_DIR / "s1").is_file())
        sessions.mark_bound(self.ts.state, "../fuori")
        self.assertFalse((self.ts.dir / "fuori").exists())


class CliSessionTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.state = self.ts.state
        self.cwd = self.ts.dir / "repo dir"
        self.cwd.mkdir()

    def tearDown(self):
        self.ts.cleanup()

    def note(self, session, sub="start", cwd=None, ago=5):
        sessions.note_cli_call(self.state, session, str(cwd or self.cwd), [sub, "7"],
                               now=T0 - timedelta(seconds=ago))

    def find(self, sub="start", cwd=None, now=T0):
        return sessions.cli_session(self.state, cwd or self.cwd, sub, now=now)

    def test_cli_session_found(self):
        self.note("s1")
        self.assertEqual(self.find(), "s1")
        # la cartella si confronta risolta: un collegamento alla stessa cartella vale
        link = self.ts.dir / "link"
        link.symlink_to(self.cwd)
        self.assertEqual(self.find(cwd=link), "s1")

    def test_cli_session_ambiguous_or_stale_refuses(self):
        self.note("s1")
        self.note("s2")
        with self.assertRaisesRegex(sessions.CliSessionError, "più sessioni"):
            self.find()
        with self.assertRaisesRegex(sessions.CliSessionError, "sessione non riconosciuta"):
            self.find(now=T0 + timedelta(seconds=sessions.CLI_WINDOW_S))
        with self.assertRaisesRegex(sessions.CliSessionError, "sessione non riconosciuta"):
            self.find(sub="act")
        other = self.ts.dir / "altra"
        other.mkdir()
        with self.assertRaisesRegex(sessions.CliSessionError, "sessione non riconosciuta"):
            self.find(cwd=other)

    def test_stale_signal_121_seconds(self):
        self.note("s1", ago=121)
        with self.assertRaisesRegex(sessions.CliSessionError, "sessione non riconosciuta"):
            self.find()

    def test_note_cli_call_rejects_unsafe_session(self):
        self.note("../x")
        self.assertFalse((self.ts.dir / "x.json").exists())
        self.assertFalse((self.ts.dir / sessions.CLI_DIR).exists())

    def test_two_subcommands_of_same_session_both_valid(self):
        self.note("s1", "start")
        self.note("s1", "act")
        self.assertEqual(self.find("start"), "s1")
        self.assertEqual(self.find("act"), "s1")
        data = json.loads((self.ts.dir / "cli" / "s1.json").read_text())
        self.assertEqual(data["start"]["argv"], ["start", "7"])
        self.assertEqual(sorted(data["act"]), ["argv", "at", "cwd"])

    def test_note_never_raises_on_unwritable_state(self):
        (self.ts.dir / sessions.CLI_DIR).write_text("file, non cartella")
        self.note("s1")  # nessuna eccezione

    def test_signal_consumed_once(self):
        self.note("s1")
        self.assertEqual(sessions.cli_session(self.state, self.cwd, "start", now=T0,
                                              argv=["start", "7"]), "s1")
        with self.assertRaisesRegex(sessions.CliSessionError, "sessione non riconosciuta"):
            sessions.cli_session(self.state, self.cwd, "start", now=T0, argv=["start", "7"])

    def test_signal_without_argv_is_not_consumed(self):
        self.note("s1")
        self.assertEqual(self.find(), "s1")
        self.assertEqual(self.find(), "s1")

    def test_consume_keeps_other_subcommands(self):
        self.note("s1", "start")
        self.note("s1", "act")
        sessions.cli_session(self.state, self.cwd, "start", now=T0, argv=["start", "7"])
        data = json.loads((self.ts.dir / "cli" / "s1.json").read_text())
        self.assertEqual(sorted(data), ["act"])
        self.assertEqual(self.find("act"), "s1")

    def test_argv_mismatch_refused(self):
        self.note("s1")
        with self.assertRaisesRegex(sessions.CliSessionError, "sessione non riconosciuta"):
            sessions.cli_session(self.state, self.cwd, "start", now=T0, argv=["start", "8"])
        # il rifiuto non toglie la voce
        self.assertEqual(self.find(), "s1")


if __name__ == "__main__":
    unittest.main()
