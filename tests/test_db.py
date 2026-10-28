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
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],
                str(db.latest_version()))
            cols = {r[1] for r in conn.execute("PRAGMA table_info(subagents)")}
            self.assertTrue({"last_seen", "vetoes", "report"} <= cols)
            self.assertIn("pending", {r[1] for r in conn.execute("PRAGMA table_info(tasks)")})
            self.assertIn("level_cap_paths",
                          {r[1] for r in conn.execute("PRAGMA table_info(work_items)")})
            conn.execute("SELECT session, last_seen FROM session_seen").fetchall()
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-2.db")))


class MigrationV3Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_from_v2_adds_task_columns_keeps_rows_and_backup(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:2]
            conn = db.open_db(self.ts.state)
            insert_work(conn)
            conn.execute("INSERT INTO tasks (work, number, kind, source, state, verdict) "
                         "VALUES (1, 1, 'plan', 'plan', 'review', 'changes')")
            conn.close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],
                str(db.latest_version()))
            cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}
            self.assertTrue({"review_sha", "review_findings", "reserved_at"} <= cols)
            row = conn.execute("SELECT * FROM tasks").fetchone()
            self.assertEqual((row["number"], row["verdict"], row["review_findings"],
                              row["review_sha"], row["reserved_at"]),
                             (1, "changes", "[]", None, None))
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-3.db")))

    def test_fresh_db_makes_no_copy(self):
        db.open_db(self.ts.state).close()
        self.assertEqual(list(self.ts.state.backup_dir.glob("*migrazione-3*")), [])


class MigrationV4Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_latest_version_is_6(self):
        self.assertEqual(db.latest_version(), 6)

    def test_from_v3_adds_columns_keeps_rows_and_backup(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:3]
            conn = db.open_db(self.ts.state)
            insert_work(conn)
            conn.execute("INSERT INTO tasks (work, number, kind, source, state) "
                         "VALUES (1, 1, 'plan', 'plan', 'done')")
            conn.execute("INSERT INTO review_cycles (work, number, sha, outcome) "
                         "VALUES (1, 1, 'abc', 'ok')")
            conn.execute("INSERT INTO findings (id, work, cycle, severity) "
                         "VALUES ('f-1-1', 1, 1, 'major')")
            conn.close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],
                str(db.latest_version()))

            def cols(table):
                return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            self.assertTrue({"pr_number", "pr_url", "finish_sha", "finish_report",
                             "extra_review_cycles", "review_unverified"} <= cols("work_items"))
            self.assertTrue({"code", "stage", "reviewers", "reported", "opened"}
                            <= cols("review_cycles"))
            self.assertTrue({"rule", "blocking"} <= cols("findings"))
            self.assertTrue({"extra_fix_rounds", "task_text"} <= cols("tasks"))
            w = conn.execute("SELECT * FROM work_items").fetchone()
            self.assertEqual((w["issue"], w["extra_review_cycles"], w["review_unverified"],
                              w["pr_number"]), (1, 0, 0, None))
            c = conn.execute("SELECT * FROM review_cycles").fetchone()
            self.assertEqual((c["sha"], c["outcome"], c["reviewers"], c["reported"], c["stage"]),
                             ("abc", "ok", "[]", "{}", None))
            f = conn.execute("SELECT * FROM findings").fetchone()
            self.assertEqual((f["id"], f["severity"], f["blocking"], f["rule"]),
                             ("f-1-1", "major", 1, None))
            t = conn.execute("SELECT * FROM tasks").fetchone()
            self.assertEqual((t["state"], t["extra_fix_rounds"], t["task_text"]),
                             ("done", 0, None))
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-4.db")))

    def test_fresh_db_makes_no_copy(self):
        db.open_db(self.ts.state).close()
        self.assertEqual(list(self.ts.state.backup_dir.glob("*migrazione-4*")), [])


class MigrationV5Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_from_v4_adds_columns_keeps_rows_and_backup(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:4]
            conn = db.open_db(self.ts.state)
            insert_work(conn)
            conn.execute("INSERT INTO spec_audit (work, kind, number, viewpoint, counts, outcome, "
                         "report_path) VALUES (1, 'spec-lens', 1, 'executor', '{}', 'empty', 'r.md')")
            conn.close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],
                str(db.latest_version()))

            def cols(table):
                return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            self.assertTrue({"code", "sha", "spec_sha", "stage", "opened"} <= cols("spec_audit"))
            self.assertIn("audit_suspended", cols("work_items"))
            w = conn.execute("SELECT * FROM work_items").fetchone()
            self.assertEqual((w["issue"], w["audit_suspended"]), (1, "{}"))
            a = conn.execute("SELECT * FROM spec_audit").fetchone()
            self.assertEqual((a["kind"], a["outcome"], a["report_path"], a["stage"], a["code"],
                              a["opened"]), ("spec-lens", "empty", "r.md", "closed", None, None))
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-5.db")))

    def test_fresh_db_makes_no_copy(self):
        db.open_db(self.ts.state).close()
        self.assertEqual(list(self.ts.state.backup_dir.glob("*migrazione-5*")), [])


class MigrationV6Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_migration_6_columns(self):
        conn = db.open_db(self.ts.state)
        try:
            def cols(table):
                return {r[1]: r for r in conn.execute(f"PRAGMA table_info({table})")}
            self.assertEqual(list(cols("lookups")), ["id", "work", "task", "agent_id", "session",
                                                     "kind", "target", "at"])
            self.assertIn("research_note", cols("tasks"))
            self.assertIn("research_ok", cols("tasks"))
            self.assertIn("research", cols("work_items"))
            idx = [(r[1], [c[2] for c in conn.execute(f"PRAGMA index_info({r[1]})")])
                   for r in conn.execute("PRAGMA index_list(lookups)")]
            self.assertIn(("lookups_task", ["work", "task"]), idx)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO lookups (work, kind, target, at) "
                             "VALUES (1, 'write', 'x', 'x')")
        finally:
            conn.close()

    def test_migration_keeps_existing_works_outside(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:5]
            conn = db.open_db(self.ts.state)
            insert_work(conn, phase="execution")
            conn.execute("INSERT INTO tasks (work, number, kind, source, state) "
                         "VALUES (1, 1, 'plan', 'plan', 'running')")
            conn.close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "6")
            w = conn.execute("SELECT * FROM work_items").fetchone()
            self.assertEqual((w["phase"], w["research"]), ("execution", 0))
            t = conn.execute("SELECT * FROM tasks").fetchone()
            self.assertEqual((t["state"], t["research_ok"], t["research_note"]),
                             ("running", 0, None))
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-6.db")))

    def test_fresh_db_makes_no_copy(self):
        db.open_db(self.ts.state).close()
        self.assertEqual(list(self.ts.state.backup_dir.glob("*migrazione-6*")), [])


_FROZEN = datetime(2026, 10, 9, 12, 0, 0, 123456, tzinfo=timezone.utc)


class BackupRaceTest(unittest.TestCase):
    """C1 della revisione finale: due copie nello stesso istante non si pestano."""

    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.addCleanup(self.t.cleanup)
        self.addCleanup(lambda: self.conn.close())

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

    def migrate_v1_db_with_rows_concurrently(self, *, newer_copies=0):
        """Migra un DB v1 con una riga da 4 processi; `newer_copies` copie valide, con nomi
        che ordinano dopo ogni copia reale, sono già nella cartella dei backup."""
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
        for n in range(newer_copies):
            dst = sqlite3.connect(self.t.state.backup_dir / f"tollgate-99990101T0000{n:02d}-x.db")
            conn.backup(dst)
            dst.close()
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
        return sorted(self.t.state.backup_dir.glob("tollgate-*.db"))

    def assert_pre_migration_copy(self, copies):
        """Esiste la copia di `migrazione-2`: integra, con la riga, allo schema 1."""
        pre = [c for c in copies if c.name.endswith("-migrazione-2.db")]
        self.assertTrue(pre, [c.name for c in copies])
        for c in pre:
            self.assertTrue(db.integrity_ok(c))
            copy = sqlite3.connect(f"file:{c}?mode=ro", uri=True)
            try:
                self.assertEqual(copy.execute("SELECT value FROM meta WHERE key='schema_version'")
                                 .fetchone()[0], "1")
                self.assertEqual(copy.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)
            finally:
                copy.close()

    def test_concurrent_migration_of_v1_db_with_rows(self):
        copies = self.migrate_v1_db_with_rows_concurrently()
        self.assert_pre_migration_copy(copies)
        # la copia si fa sotto il lucchetto, solo per il passo che si applica davvero: una per passo
        steps = [n for n, _ in db.MIGRATIONS if n > 1]
        self.assertEqual(sorted(c.name.split("migrazione-")[1] for c in copies),
                         [f"{n}.db" for n in steps], [c.name for c in copies])

    def test_retention_never_prunes_the_pre_migration_copy(self):
        """Con KEEP_BACKUPS copie più recenti già presenti la copia pre-migrazione resta."""
        copies = self.migrate_v1_db_with_rows_concurrently(newer_copies=db.KEEP_BACKUPS)
        self.assert_pre_migration_copy(copies)
        others = [c for c in copies if "-migrazione-" not in c.name]
        self.assertEqual(len(others), db.KEEP_BACKUPS)


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
