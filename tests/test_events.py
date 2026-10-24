import json
import subprocess
import sys
import textwrap
import unittest
from datetime import timedelta

from tests.helpers import BIN, TempState
from tollgate_core import clock, db, events

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
KEYS = {"v", "seq", "at", "host", "session", "work", "repo_key", "issue", "type", "data"}


class EventsTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.conn.execute(
            "INSERT INTO work_items (repo_key, issue, level, phase, created, updated) "
            "VALUES ('github.com/o/r', 42, 'L1', 'plan', 'x', 'x')")
        self.work = self.conn.execute("SELECT id FROM work_items").fetchone()[0]

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_known_commits_corrupt_data_is_dberror(self):
        events.record_event(self.conn, "commit", {"sha": "abc"}, now=T0, work=self.work)
        self.assertEqual(events.known_commits(self.conn, self.work), {"abc"})
        self.conn.execute("INSERT INTO events (v, at, host, work, type, data) "
                          "VALUES (1, 'x', 'h', ?, 'commit', '{guasto')", (self.work,))
        with self.assertRaisesRegex(db.DbError, "events.data"):
            events.known_commits(self.conn, self.work)

    def test_envelope(self):
        seq = events.record_event(self.conn, "veto", {"rule": "scope", "event": "pre_edit",
                                                      "reason": "fuori scope"},
                                  now=T0, session="s1", work=self.work, host="h")
        (e,) = events.export_events(self.conn, 0)
        self.assertEqual(set(e), KEYS)
        self.assertEqual(e["seq"], seq)
        self.assertEqual(e["v"], 1)
        self.assertEqual(e["at"], "2026-10-08T10:00:00.000000Z")
        self.assertEqual((e["repo_key"], e["issue"], e["work"]), ("github.com/o/r", 42, self.work))
        self.assertEqual(e["data"]["rule"], "scope")

    def test_without_work(self):
        events.record_event(self.conn, "off", {}, now=T0)
        (e,) = events.export_events(self.conn, 0)
        self.assertIsNone(e["work"])
        self.assertIsNone(e["repo_key"])
        self.assertTrue(e["host"])

    def test_rejects_unknown_type_and_work(self):
        with self.assertRaises(ValueError):
            events.record_event(self.conn, "boh", {}, now=T0)
        with self.assertRaises(ValueError):
            events.record_event(self.conn, "veto", {}, now=T0, work=999)

    def test_export_after_seq_and_jsonl(self):
        seqs = [events.record_event(self.conn, "commit", {"i": i}, now=T0) for i in range(5)]
        got = events.export_events(self.conn, seqs[1])
        self.assertEqual([e["seq"] for e in got], seqs[2:])
        lines = events.to_jsonl(got).splitlines()
        self.assertEqual([json.loads(x)["data"]["i"] for x in lines], [2, 3, 4])

    def test_prune_keeps_recent_and_seq_never_reused(self):
        old = T0 - timedelta(days=200)
        events.record_event(self.conn, "commit", {}, now=old)
        last_old = events.record_event(self.conn, "commit", {}, now=old)
        events.record_event(self.conn, "commit", {}, now=T0)
        self.assertEqual(events.prune_events(self.conn, T0, 180), 2)
        self.assertEqual(len(events.export_events(self.conn, 0)), 1)
        self.conn.execute("DELETE FROM events")
        new = events.record_event(self.conn, "commit", {}, now=T0)
        self.assertGreater(new, last_old + 1)

    def test_joins_caller_transaction(self):
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                events.record_event(self.conn, "commit", {}, now=T0)
                raise RuntimeError("x")
        self.assertEqual(events.export_events(self.conn, 0), [])


class ConcurrencyTest(unittest.TestCase):
    """Più processi (hook) che creano e scrivono lo stesso DB nello stesso momento."""

    def setUp(self):
        self.t = TempState()

    def tearDown(self):
        self.t.cleanup()

    def test_three_writers(self):
        code = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(BIN)!r})
            from tollgate_core import clock, db, events
            from tollgate_core.paths import resolve_state
            conn = db.open_db(resolve_state())
            for i in range(100):
                events.record_event(conn, "commit", {{"i": i}}, now=clock.now(), session=sys.argv[1])
        """)
        procs = [subprocess.Popen([sys.executable, "-B", "-c", code, f"s{n}"],
                                  env=self.t.env(), stderr=subprocess.PIPE, text=True)
                 for n in range(3)]
        for p in procs:
            _, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, err)
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        got = events.export_events(conn, 0)
        self.assertEqual(len(got), 300)
        seqs = [e["seq"] for e in got]
        self.assertEqual(seqs, sorted(set(seqs)))
        for s in ("s0", "s1", "s2"):
            mine = [e["data"]["i"] for e in got if e["session"] == s]
            self.assertEqual(mine, list(range(100)))
