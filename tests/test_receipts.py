import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import clock, db, phases, receipts

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


def add(conn, work, command, state, at, sha="h1", exit_code=0):
    return receipts.add(conn, work=work, sha=sha, command=command, resolved_command=command,
                        exit_code=exit_code, tests_run=3, tests_skipped=0, duration=1.0,
                        log="/tmp/x.log", produced_by="verify", state=state, now=at)


class ReceiptsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_latest_per_command(self):
        add(self.conn, self.w, "verify", "red", T0)
        add(self.conn, self.w, "verify", "green", T0 + timedelta(seconds=1))
        add(self.conn, self.w, "lint", "green", T0)
        got = {r["command"]: r["state"] for r in receipts.latest(self.conn, self.w, "h1")}
        self.assertEqual(got, {"verify": "green", "lint": "green"})
        ev = self.conn.execute("SELECT count(*) FROM events WHERE type='receipt'").fetchone()[0]
        self.assertEqual(ev, 3)

    def test_any_since(self):
        add(self.conn, self.w, "verify", "red", T0)
        self.assertTrue(receipts.any_since(self.conn, self.w, clock.fmt(T0 - timedelta(1))))
        self.assertFalse(receipts.any_since(self.conn, self.w, clock.fmt(T0 + timedelta(1))))

    def test_unknown_state(self):
        with self.assertRaises(ValueError):
            add(self.conn, self.w, "verify", "boh", T0)


if __name__ == "__main__":
    unittest.main()
