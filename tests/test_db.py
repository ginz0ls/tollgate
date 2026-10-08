import os
import sqlite3
import subprocess
import sys
import textwrap
import unittest
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
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(conn.execute("PRAGMA synchronous").fetchone()[0], 2)
        self.assertEqual(conn.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
        self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(TABLES <= names, TABLES - names)
        self.assertEqual(conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "1")

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
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "1")
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
        extra = db.MIGRATIONS + [(2, ["CREATE TABLE extra (x INTEGER)"])]
        with mock.patch.object(db, "MIGRATIONS", extra):
            conn = db.open_db(self.t.state)
        backups = list(self.t.state.backup_dir.glob("*migrazione-2*.db"))
        self.assertEqual(len(backups), 1)
        old = sqlite3.connect(backups[0])
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
        insert_work(conn, phase="plan")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_work(conn, phase="execution")
        conn.execute("UPDATE work_items SET phase='closed'")
        insert_work(conn, phase="plan")
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 2)


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
        self.assertEqual(sqlite3.connect(p).execute("SELECT count(*) FROM work_items").fetchone()[0], 1)


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
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)
        self.assertEqual(len(list(self.t.state.broken_dir.rglob("tollgate.db"))), 1)

    def test_no_good_copy_gives_empty_db(self):
        for b in self.t.state.backup_dir.glob("*.db"):
            b.write_bytes(os.urandom(4096))
        self.corrupt()
        msg = db.restore(self.t.state, interactive=True, confirm=lambda q: True)
        self.assertIn("/tollgate:adopt", msg)
        conn = db.open_db(self.t.state)
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)
