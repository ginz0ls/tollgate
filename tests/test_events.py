import json
import os
import stat
import subprocess
import sys
import textwrap
import unittest
from datetime import timedelta
from unittest import mock

from tests.helpers import BIN, TempState
from tollgate_core import clock, db, events, fsutil

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

    def test_new_event_types_recorded(self):
        for type_ in ("size_decided", "ruling", "stop_asked", "stop_answered", "cost"):
            with self.subTest(type_):
                seq = events.record_event(self.conn, type_, {"x": 1}, now=T0, work=self.work)
                e = [x for x in events.export_events(self.conn, 0) if x["seq"] == seq][0]
                self.assertEqual((e["type"], e["v"]), (type_, 1))

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

    def old_and_new(self, old=3, new=2):
        old_at = T0 - timedelta(days=60)
        olds = [events.record_event(self.conn, "commit", {"i": i}, now=old_at)
                for i in range(old)]
        news = [events.record_event(self.conn, "commit", {"i": 10 + i}, now=T0)
                for i in range(new)]
        return olds, news

    def test_archive_then_prune(self):
        olds, news = self.old_and_new()
        expected = events.to_jsonl([e for e in events.export_events(self.conn, 0)
                                    if e["seq"] in olds])
        n, path = events.archive_and_prune(self.conn, self.t.state, T0, 30)
        self.assertEqual(n, 3)
        self.assertEqual(path, self.t.state.root / events.ARCHIVE_DIR
                         / f"events-{olds[0]}-{olds[-1]}.jsonl")
        self.assertEqual(path.read_text(encoding="utf-8"), expected)
        self.assertEqual(len(expected.splitlines()), 3)
        self.assertEqual([e["seq"] for e in events.export_events(self.conn, 0)], news)

    def test_archive_dir_is_private(self):
        self.old_and_new()
        events.archive_and_prune(self.conn, self.t.state, T0, 30)
        mode = (self.t.state.root / events.ARCHIVE_DIR).stat().st_mode & 0o777
        self.assertEqual(mode & 0o077, 0)

    def test_archive_seq_never_reused(self):
        olds, _ = self.old_and_new()
        events.archive_and_prune(self.conn, self.t.state, T0, 30)
        self.conn.execute("DELETE FROM events")
        new = events.record_event(self.conn, "commit", {}, now=T0)
        self.assertGreater(new, olds[-1] + 1)

    def test_archive_write_failure_deletes_nothing(self):
        self.old_and_new()
        with mock.patch.object(fsutil, "write_atomic", side_effect=OSError("disco pieno")):
            with self.assertRaises(OSError):
                events.archive_and_prune(self.conn, self.t.state, T0, 30)
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(len(events.export_events(self.conn, 0)), 5)

    def test_archive_is_fsynced_before_the_delete(self):
        """Riga 2: l'archivio (file e cartella) è sul disco prima del `DELETE`."""
        self.old_and_new()
        real = os.fsync
        seen = []

        def spy(fd):
            seen.append((stat.S_ISDIR(os.fstat(fd).st_mode),
                         len(events.export_events(self.conn, 0))))
            real(fd)

        with mock.patch("os.fsync", side_effect=spy):
            events.archive_and_prune(self.conn, self.t.state, T0, 30)
        self.assertEqual(sorted(kind for kind, _ in seen), [False, True])   # file e cartella
        self.assertEqual({left for _, left in seen}, {5})                   # nessun DELETE ancora
        self.assertEqual(len(events.export_events(self.conn, 0)), 2)

    def test_write_atomic_itself_does_not_fsync(self):
        """Gli altri chiamanti dell'helper non cambiano comportamento."""
        target = self.t.state.root / "x" / "f.txt"
        with mock.patch("os.fsync") as fs:
            fsutil.write_atomic(target, "ciao")
        self.assertEqual(fs.call_count, 0)

    def test_archive_twice_is_noop(self):
        self.old_and_new()
        self.assertEqual(events.archive_and_prune(self.conn, self.t.state, T0, 30)[0], 3)
        self.assertEqual(events.archive_and_prune(self.conn, self.t.state, T0, 30), (0, None))
        self.assertEqual(len(list((self.t.state.root / events.ARCHIVE_DIR).iterdir())), 1)

    def test_archive_nothing_old_touches_no_disk(self):
        events.record_event(self.conn, "commit", {}, now=T0)
        self.assertEqual(events.archive_and_prune(self.conn, self.t.state, T0, 30), (0, None))
        self.assertFalse((self.t.state.root / events.ARCHIVE_DIR).exists())

    def test_archive_holds_write_lock(self):
        self.old_and_new()
        seen = []
        real = fsutil.write_atomic

        def spy(path, text):
            seen.append(self.conn.in_transaction)
            real(path, text)

        with mock.patch.object(fsutil, "write_atomic", spy):
            events.archive_and_prune(self.conn, self.t.state, T0, 30)
        self.assertEqual(seen, [True])

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
