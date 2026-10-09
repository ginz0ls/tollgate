import os
import sqlite3
import unittest
from unittest import mock

from tests.helpers import TempState
from tollgate_core import db, offlog


class OffLogTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _events(self):
        return self.conn.execute("SELECT type, at, data FROM events ORDER BY seq").fetchall()

    def _leftovers(self):
        return sorted(p.name for p in self.ts.dir.glob(".off.log.*"))

    def test_import_keeps_original_times_and_empties_log(self):
        (self.ts.dir / offlog.LOG_NAME).write_text(
            "2026-10-09T08:00:00.000000Z off 1791540000\n"
            "riga rovinata\n"
            "2026-10-09T09:00:00.000000Z on\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 2)
        rows = self._events()
        self.assertEqual([(r[0], r[1]) for r in rows],
                         [("off", "2026-10-09T08:00:00.000000Z"),
                          ("on", "2026-10-09T09:00:00.000000Z")])
        self.assertIn('"until": 1791540000', rows[0][2])
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)
        self.assertEqual(self._leftovers(), [])

    def test_no_log(self):
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)

    def test_invalid_date_line_is_skipped(self):
        (self.ts.dir / offlog.LOG_NAME).write_text(
            "2026-13-09T08:00:00.000000Z off\n"
            "2026-10-09T09:00:00.000000Z on\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 1)
        self.assertEqual([(r[0], r[1]) for r in self._events()],
                         [("on", "2026-10-09T09:00:00.000000Z")])
        self.assertEqual(self._leftovers(), [])

    def test_write_error_keeps_file_and_next_call_imports_once(self):
        (self.ts.dir / offlog.LOG_NAME).write_text(
            "2026-10-09T08:00:00.000000Z off\n"
            "2026-10-09T09:00:00.000000Z on\n")
        real = offlog.record_event
        calls = []

        def flaky(conn, type_, data=None, **kw):
            calls.append(type_)
            if len(calls) == 2:
                raise sqlite3.OperationalError("disco pieno")
            return real(conn, type_, data, **kw)

        with mock.patch.object(offlog, "record_event", side_effect=flaky):
            with self.assertRaises(sqlite3.OperationalError):
                offlog.import_log(self.conn, self.ts.state)
        self.assertEqual(self._events(), [])            # la transazione è stata annullata
        self.assertEqual(len(self._leftovers()), 1)     # il file resta dov'è
        self.assertFalse((self.ts.dir / offlog.LOG_NAME).exists())

        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 2)
        self.assertEqual(len(self._events()), 2)
        self.assertEqual(self._leftovers(), [])
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)
        self.assertEqual(len(self._events()), 2)

    def test_orphan_file_of_dead_process_is_recovered(self):
        # pid 999999999 oltre il massimo del kernel: nessun processo vivo lo ha
        (self.ts.dir / ".off.log.999999999").write_text(
            "2026-10-09T08:00:00.000000Z off\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 1)
        self.assertEqual(len(self._events()), 1)
        self.assertEqual(self._leftovers(), [])

    def test_file_of_live_process_is_not_taken(self):
        # il genitore del test è un processo vivo: il suo file in importazione non si tocca
        live = self.ts.dir / f".off.log.{os.getppid()}"
        live.write_text("2026-10-09T08:00:00.000000Z off\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)
        self.assertTrue(live.exists())
        self.assertEqual(self._events(), [])

    def test_refuses_to_run_inside_transaction(self):
        (self.ts.dir / offlog.LOG_NAME).write_text("2026-10-09T08:00:00.000000Z off\n")
        with db.tx(self.conn):
            with self.assertRaises(RuntimeError):
                offlog.import_log(self.conn, self.ts.state)
        self.assertTrue((self.ts.dir / offlog.LOG_NAME).exists())


if __name__ == "__main__":
    unittest.main()
