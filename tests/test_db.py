import os
import sqlite3
import subprocess
import sys
import textwrap
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.helpers import BIN, TempState
from tollgate_core import db

TABLES = {"meta", "work_items", "scope", "receipts", "blocks", "subagents", "review_cycles",
          "findings", "spec_audit", "acts", "intents", "tasks", "events"}


def insert_work(conn, issue=1, phase="plan", repo="github.com/o/r"):
    conn.execute(
        "INSERT INTO work_items (repo_key, issue, level, phase, created, updated) "
        "VALUES (?, ?, 'L1', ?, 'x', 'x')", (repo, issue, phase))


class OpenTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()

    def tearDown(self):
        self.t.cleanup()

    def test_pragmas_and_tables(self):
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(conn.execute("PRAGMA synchronous").fetchone()[0], 2)
        self.assertEqual(conn.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
        self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(TABLES <= names, TABLES - names)
        self.assertEqual(conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],
            str(db.latest_version()))

    def test_concurrent_first_open(self):
        code = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(BIN)!r})
            from tollgate_core import db
            from tollgate_core.paths import resolve_state
            db.open_db(resolve_state()).close()
        """)
        procs = [subprocess.Popen([sys.executable, "-B", "-c", code], env=self.t.env(),
                                  stderr=subprocess.PIPE, text=True) for _ in range(3)]
        for p in procs:
            _, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, err)
        conn = db.open_db(self.t.state)
        self.assertEqual(conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],
            str(db.latest_version()))
        conn.close()

    def test_fresh_db_makes_no_backup_and_reopen_is_idempotent(self):
        db.open_db(self.t.state).close()
        db.open_db(self.t.state).close()
        self.assertEqual(list(self.t.state.backup_dir.glob("*.db")), [])

    def test_newer_db_is_refused(self):
        conn = db.open_db(self.t.state)
        conn.execute("UPDATE meta SET value='99' WHERE key='schema_version'")
        conn.close()
        with self.assertRaises(db.DbTooNew):
            db.open_db(self.t.state)

    def test_migration_makes_backup_first(self):
        db.open_db(self.t.state).close()
        extra_version = db.latest_version() + 1
        extra = db.MIGRATIONS + [(extra_version, ["CREATE TABLE extra (x INTEGER)"])]
        with mock.patch.object(db, "MIGRATIONS", extra):
            conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        backups = list(self.t.state.backup_dir.glob(f"*migrazione-{extra_version}*.db"))
        self.assertEqual(len(backups), 1)
        old = sqlite3.connect(backups[0])
        self.addCleanup(old.close)
        self.assertIsNone(old.execute(
            "SELECT name FROM sqlite_master WHERE name='extra'").fetchone())
        self.assertIsNotNone(conn.execute(
            "SELECT name FROM sqlite_master WHERE name='extra'").fetchone())

    def test_corrupt_file(self):
        self.t.state.db_path.write_bytes(os.urandom(4096))
        with self.assertRaises(db.DbCorrupt) as cm:
            db.open_db(self.t.state)
        self.assertIn(str(db.BIN_PATH) + " db restore", str(cm.exception))
        self.assertTrue(db.BIN_PATH.is_absolute())

    def test_locked_db_is_not_reported_as_corrupt(self):
        holder = sqlite3.connect(self.t.state.db_path, isolation_level=None)
        holder.execute("BEGIN EXCLUSIVE")
        try:
            with mock.patch.object(db, "BUSY_TIMEOUT_MS", 100):
                with self.assertRaises(db.DbError) as cm:
                    db.open_db(self.t.state)
        finally:
            holder.close()
        self.assertNotIsInstance(cm.exception, db.DbCorrupt)
        self.assertNotIn("db restore", str(cm.exception))
        self.assertIn("OFF", str(cm.exception))

    def test_unique_active_work(self):
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        insert_work(conn, phase="plan")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_work(conn, phase="execution")
        conn.execute("UPDATE work_items SET phase='closed'")
        insert_work(conn, phase="plan")
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 2)


class MigrationV2Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_from_v1_adds_columns_and_backup(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:1]
            db.open_db(self.ts.state).close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "2")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(subagents)")}
            self.assertTrue({"last_seen", "vetoes", "report"} <= cols)
            self.assertIn("pending", {r[1] for r in conn.execute("PRAGMA table_info(tasks)")})
            self.assertIn("level_cap_paths",
                          {r[1] for r in conn.execute("PRAGMA table_info(work_items)")})
            conn.execute("SELECT session, last_seen FROM session_seen").fetchall()
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-2.db")))


_FROZEN = datetime(2026, 10, 9, 12, 0, 0, 123456, tzinfo=timezone.utc)


class BackupRaceTest(unittest.TestCase):
    """C1 della revisione finale: due copie nello stesso istante non si pestano."""

    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.addCleanup(self.t.cleanup)
        self.addCleanup(self.conn.close)

    def test_same_instant_same_name_never_overwrites(self):
        # Simula il perdente della corsa: exists() non vede ancora la copia del vincitore.
        with mock.patch.object(db.clock, "now", return_value=_FROZEN), \
                mock.patch.object(Path, "exists", return_value=False):
            first = db.backup(self.conn, self.t.state, "migrazione-2")
            second = db.backup(self.conn, self.t.state, "migrazione-2")
        self.assertNotEqual(first, second)
        self.assertTrue(first.exists() and second.exists())
        self.assertEqual(sorted(p.name for p in self.t.state.backup_dir.iterdir()),
                         sorted([first.name, second.name]))

    def test_concurrent_backups_with_frozen_clock(self):
        self.conn.close()
        self.conn = db.open_db(self.t.state)
        start = time.time() + 1.5
        code = textwrap.dedent(f"""
            import sys, time
            from datetime import datetime, timezone
            sys.path.insert(0, {str(BIN)!r})
            from unittest import mock
            from tollgate_core import db
            from tollgate_core.paths import resolve_state
            conn = db.open_db(resolve_state())
            while time.time() < {start!r}:
                pass
            frozen = datetime(2026, 10, 9, 12, 0, 0, 123456, tzinfo=timezone.utc)
            with mock.patch.object(db.clock, "now", return_value=frozen):
                for _ in range(8):
                    db.backup(conn, resolve_state(), "migrazione-2")
            conn.close()
        """)
        procs = [subprocess.Popen([sys.executable, "-B", "-c", code], env=self.t.env(),
                                  stderr=subprocess.PIPE, text=True) for _ in range(3)]
        for p in procs:
            _, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, err)
        self.assertEqual(list(self.t.state.backup_dir.glob(".tmp-*")), [])

    def test_concurrent_migration_of_v1_db_with_rows(self):
        self.conn.close()
        self.t.cleanup()
        self.t = TempState()
        self.addCleanup(self.t.cleanup)
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:1]
            conn = db.open_db(self.t.state)
        finally:
            db.MIGRATIONS[:] = saved
        insert_work(conn)
        conn.close()
        self.conn = sqlite3.connect(":memory:")
        code = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(BIN)!r})
            from tollgate_core import db
            from tollgate_core.paths import resolve_state
            db.open_db(resolve_state()).close()
        """)
        procs = [subprocess.Popen([sys.executable, "-B", "-c", code], env=self.t.env(),
                                  stderr=subprocess.PIPE, text=True) for _ in range(4)]
        for p in procs:
            _, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, err)
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("SELECT value FROM meta WHERE key='schema_version'")
                         .fetchone()[0], str(db.latest_version()))
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)
        copies = list(self.t.state.backup_dir.glob("tollgate-*-migrazione-2.db"))
        self.assertTrue(copies)
        for c in copies:
            self.assertTrue(db.integrity_ok(c))


class TxTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_rollback_on_error(self):
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                insert_work(self.conn)
                raise RuntimeError("x")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)

    def test_nested_joins_outer(self):
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                with db.tx(self.conn):
                    insert_work(self.conn)
                raise RuntimeError("x")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)


class TxRollbackTest(unittest.TestCase):
    def test_original_error_survives_manual_rollback(self):
        t = TempState()
        conn = db.open_db(t.state)
        try:
            with self.assertRaises(RuntimeError):
                with db.tx(conn):
                    conn.execute("ROLLBACK")
                    raise RuntimeError("x")
        finally:
            conn.close()
            t.cleanup()


class BackupTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_keeps_last_ten(self):
        paths = [db.backup(self.conn, self.t.state, f"prova-{i}") for i in range(12)]
        left = sorted(p.name for p in self.t.state.backup_dir.glob("*.db"))
        self.assertEqual(len(left), 10)
        self.assertEqual(left[-1], paths[-1].name)
        self.assertNotIn(paths[0].name, left)

    def test_prune_tolerates_vanished_backup(self):
        paths = [db.backup(self.conn, self.t.state, f"p-{i}") for i in range(10)]
        paths[0].unlink()
        db.backup(self.conn, self.t.state, "p-10")
        db.backup(self.conn, self.t.state, "p-11")
        self.assertEqual(len(list(self.t.state.backup_dir.glob("*.db"))), 10)

    def test_failed_copy_leaves_nothing(self):
        before = set(self.t.state.backup_dir.iterdir())
        broken = mock.Mock()
        broken.backup.side_effect = sqlite3.OperationalError("x")
        with self.assertRaises(sqlite3.OperationalError):
            db.backup(broken, self.t.state, "fallita")
        self.assertEqual(set(self.t.state.backup_dir.iterdir()), before)

    def test_integrity_false_for_empty_file(self):
        p = self.t.state.backup_dir / "vuoto.db"
        p.write_bytes(b"")
        self.assertFalse(db.integrity_ok(p))

    def test_backup_is_consistent(self):
        insert_work(self.conn)
        p = db.backup(self.conn, self.t.state, "fase")
        self.assertTrue(db.integrity_ok(p))
        copy = sqlite3.connect(p)
        self.addCleanup(copy.close)
        self.assertEqual(copy.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)


class RestoreTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        conn = db.open_db(self.t.state)
        insert_work(conn)
        db.backup(conn, self.t.state, "fase")
        conn.close()

    def tearDown(self):
        self.t.cleanup()

    def corrupt(self):
        for suffix in ("", "-wal", "-shm"):
            p = self.t.state.db_path.with_name(self.t.state.db_path.name + suffix)
            if p.exists():
                p.unlink()
        self.t.state.db_path.write_bytes(os.urandom(4096))

    def test_refuses_healthy_db(self):
        with self.assertRaisesRegex(db.DbError, "integro"):
            db.restore(self.t.state, interactive=True, confirm=lambda q: True)

    def test_refuses_without_terminal(self):
        self.corrupt()
        with self.assertRaisesRegex(db.DbError, "terminale"):
            db.restore(self.t.state, interactive=False, confirm=lambda q: True)

    def test_cancel(self):
        self.corrupt()
        self.assertEqual(db.restore(self.t.state, interactive=True, confirm=lambda q: False),
                         "annullato")
        self.assertTrue(self.t.state.db_path.exists())
        self.assertFalse(self.t.state.broken_dir.exists() and any(self.t.state.broken_dir.iterdir()))

    def test_restores_last_good_copy(self):
        self.corrupt()
        msg = db.restore(self.t.state, interactive=True, confirm=lambda q: True)
        self.assertIn("ripristinata", msg)
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)
        self.assertEqual(len(list(self.t.state.broken_dir.rglob("tollgate.db"))), 1)

    def test_no_good_copy_gives_empty_db(self):
        for b in self.t.state.backup_dir.glob("*.db"):
            b.write_bytes(os.urandom(4096))
        self.corrupt()
        msg = db.restore(self.t.state, interactive=True, confirm=lambda q: True)
        self.assertIn("/tollgate:adopt", msg)
        conn = db.open_db(self.t.state)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)
