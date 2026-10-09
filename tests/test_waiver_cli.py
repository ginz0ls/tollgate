import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.helpers import TempState, git, make_repo
from tollgate_analysis import waivers
from tollgate_core import db, phases, waiver_cli
from tollgate_core.cli import UsageError

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class WaiverCliTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-waiver-"))
        self.wt = make_repo(self.tmp / "wt")
        (self.wt / "a").write_text("x")
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-qm", "x")
        conn = db.open_db(self.ts.state)
        self.work = phases.create_work(conn, repo_key="r", issue=7, level="L1", now=T0,
                                       worktree=str(self.wt), branch="tg/7-x")
        conn.close()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def stored(self):
        return waivers.parse((self.wt / ".tollgate/waivers/7.toml").read_text())

    def test_add_two_waivers(self):
        w1 = waiver_cli.add_waiver(self.ts.state, self.wt / "src", type_="scope", file="src/x.py",
                                   choice="c", why="w", cost="k", now=T0)
        w2 = waiver_cli.add_waiver(self.ts.state, self.wt, type_="test", file="tests/t.py",
                                   tests=["t::a"], choice="c", why="w", cost="k", now=T0)
        self.assertEqual((w1, w2), ("w-7-1", "w-7-2"))
        wf = waivers.parse((self.wt / ".tollgate/waivers/7.toml").read_text())
        self.assertEqual((wf.issue, wf.branch, [w.id for w in wf.waivers]),
                         (7, "tg/7-x", ["w-7-1", "w-7-2"]))
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute("SELECT count(*) FROM events WHERE type="
                                          "'waiver_added'").fetchone()[0], 2)
        finally:
            conn.close()

    def test_errors(self):
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="boh", file="a", choice="c",
                                  why="w", cost="k", now=T0)
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="scope", choice="c", why="w",
                                  cost="k", now=T0)
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.tmp, type_="scope", file="a", choice="c",
                                  why="w", cost="k", now=T0)

    def test_file_is_normalized_relative_to_worktree_root(self):
        sub = self.wt / "sub"
        sub.mkdir()
        waiver_cli.add_waiver(self.ts.state, sub, type_="scope", file="x.py", choice="c",
                              why="w", cost="k", now=T0)
        waiver_cli.add_waiver(self.ts.state, self.wt, type_="scope", file="./a", choice="c",
                              why="w", cost="k", now=T0)
        self.assertEqual([w.file for w in self.stored().waivers], ["sub/x.py", "a"])

    def test_file_outside_worktree_is_rejected(self):
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="scope", file="../fuori.py",
                                  choice="c", why="w", cost="k", now=T0)
        self.assertFalse((self.wt / ".tollgate/waivers/7.toml").exists())

    def test_type_test_requires_test_ids(self):
        with self.assertRaises(UsageError) as cm:
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="test", file="tests/t.py",
                                  choice="c", why="w", cost="k", now=T0)
        self.assertIn("--test", str(cm.exception))
        self.assertFalse((self.wt / ".tollgate/waivers/7.toml").exists())

    def test_block_open(self):
        bid = waiver_cli.open_block_cmd(self.ts.state, self.wt, type_="test_spec_conflict",
                                        reason="il test contraddice la spec", now=T0)
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(phases.get_work(conn, self.work)["phase"], "blocked")
            self.assertEqual(conn.execute("SELECT type FROM blocks WHERE id = ?",
                                          (bid,)).fetchone()[0], "test_spec_conflict")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
