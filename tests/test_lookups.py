import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import clock, db, lookups, phases

T0 = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)


class LookupsCase(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                                    research=True)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def rec(self, kind="read", target="src/a.py", task=1, work=None, **kw):
        lookups.record(self.conn, work=work or self.w, task=task, agent_id=kw.get("agent_id", "ag"),
                       session="s1", kind=kind, target=target, now=T0)


class RecordTest(LookupsCase):
    def test_record_and_for_task(self):
        self.rec("read", "src/a.py")
        self.rec("fetch", "https://example.org/doc")
        self.rec("read", "src/altro.py", task=2)
        self.assertEqual(lookups.for_task(self.conn, self.w, 1),
                         [lookups.Lookup("read", "src/a.py"),
                          lookups.Lookup("fetch", "https://example.org/doc")])
        self.assertEqual(lookups.for_task(self.conn, self.w, 2),
                         [lookups.Lookup("read", "src/altro.py")])

    def test_for_task_without_duplicates(self):
        self.rec("read", "src/a.py")
        self.rec("read", "src/a.py", agent_id="altro")
        self.rec("grep", "src/a.py")
        self.assertEqual(lookups.for_task(self.conn, self.w, 1),
                         [lookups.Lookup("read", "src/a.py"), lookups.Lookup("grep", "src/a.py")])
        self.assertEqual(self.conn.execute("SELECT count(*) FROM lookups").fetchone()[0], 2)

    def test_unknown_kind_rejected(self):
        with self.assertRaises(ValueError):
            self.rec("write", "src/a.py")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM lookups").fetchone()[0], 0)

    def test_empty_target_rejected(self):
        with self.assertRaises(ValueError):
            self.rec("read", "")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM lookups").fetchone()[0], 0)

    def test_kinds(self):
        self.assertEqual(set(lookups.KINDS),
                         {"read", "grep", "bash_read", "fetch", "search", "docs"})

    def test_task_none_is_recorded_but_not_listed(self):
        self.rec("read", "src/a.py", task=None)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM lookups").fetchone()[0], 1)
        self.assertEqual(lookups.for_task(self.conn, self.w, 1), [])


class NoteTest(LookupsCase):
    def test_set_note_roundtrip(self):
        from tollgate_core import tasks
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)
        self.assertEqual(lookups.note(self.conn, self.w, 1), (None, False))
        lookups.set_note(self.conn, self.w, 1, text="nota", ok=True)
        self.assertEqual(lookups.note(self.conn, self.w, 1), ("nota", True))
        lookups.set_note(self.conn, self.w, 1, text="altra", ok=False)
        self.assertEqual(lookups.note(self.conn, self.w, 1), ("altra", False))


class PruneTest(LookupsCase):
    def test_prune_closed_works_older_than_days(self):
        old = T0 - timedelta(days=200)
        self.conn.execute("UPDATE work_items SET phase = 'closed', updated = ? WHERE id = ?",
                          (clock.fmt(old), self.w))
        self.rec("read", "src/a.py")
        other = phases.create_work(self.conn, repo_key="r", issue=8, level="L1", now=T0,
                                   research=True)
        self.rec("read", "src/b.py", work=other)
        recent = phases.create_work(self.conn, repo_key="r", issue=9, level="L1", now=T0,
                                    research=True)
        self.conn.execute("UPDATE work_items SET phase = 'closed' WHERE id = ?", (recent,))
        self.rec("read", "src/c.py", work=recent)
        self.assertEqual(lookups.prune(self.conn, now=T0, days=180), 1)
        self.assertEqual([r[0] for r in self.conn.execute("SELECT work FROM lookups ORDER BY id")],
                         [other, recent])
        self.assertEqual(lookups.prune(self.conn, now=T0, days=180), 0)


if __name__ == "__main__":
    unittest.main()
