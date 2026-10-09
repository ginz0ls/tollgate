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


if __name__ == "__main__":
    unittest.main()
