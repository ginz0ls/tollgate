import unittest

from tests.helpers import TempState
from tollgate_core import db, offlog


class OffLogTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_import_keeps_original_times_and_empties_log(self):
        (self.ts.dir / offlog.LOG_NAME).write_text(
            "2026-10-09T08:00:00.000000Z off 1791540000\n"
            "riga rovinata\n"
            "2026-10-09T09:00:00.000000Z on\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 2)
        rows = self.conn.execute("SELECT type, at, data FROM events ORDER BY seq").fetchall()
        self.assertEqual([(r[0], r[1]) for r in rows],
                         [("off", "2026-10-09T08:00:00.000000Z"),
                          ("on", "2026-10-09T09:00:00.000000Z")])
        self.assertIn('"until": 1791540000', rows[0][2])
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)

    def test_no_log(self):
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)


if __name__ == "__main__":
    unittest.main()
