import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, scope, tasks

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_register_plan_l1_advances(self):
        scope.register_plan(self.conn, self.ts.state, self.w,
                            plan_path="docs/superpowers/plans/p.md", plan_sha="s1",
                            scope_paths=["src/a.py", "tests/test_a.py"],
                            plan_tasks=[(1, ["tdd"]), (2, [])], advance=True, now=T0)
        self.assertEqual(scope.paths(self.conn, self.w), {"src/a.py", "tests/test_a.py"})
        w = phases.get_work(self.conn, self.w)
        self.assertEqual((w["phase"], w["plan_path"], w["plan_sha"]),
                         ("execution", "docs/superpowers/plans/p.md", "s1"))
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["skills_required"], '["tdd"]')
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM events WHERE type='scope_registered'").fetchone()[0], 1)

    def test_register_twice_rejected_and_scope_unchanged(self):
        scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md", plan_sha="s1",
                            scope_paths=["a"], plan_tasks=[(1, [])], advance=False, now=T0)
        with self.assertRaises(ValueError):
            scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md",
                                plan_sha="s2", scope_paths=["a", "b"], plan_tasks=[(1, [])],
                                advance=False, now=T0)
        self.assertEqual(scope.paths(self.conn, self.w), {"a"})

    def test_set_plan_path_only_once(self):
        scope.set_plan_path(self.conn, self.w, "p.md", now=T0)
        scope.set_plan_path(self.conn, self.w, "altro.md", now=T0)
        self.assertEqual(phases.get_work(self.conn, self.w)["plan_path"], "p.md")


if __name__ == "__main__":
    unittest.main()
