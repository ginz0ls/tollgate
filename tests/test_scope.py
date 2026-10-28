import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, events, lookups, phases, scope, tasks

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


class ResetPlanTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L2", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def register(self, sha, paths=("a",), n=2):
        scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md", plan_sha=sha,
                            scope_paths=list(paths), plan_tasks=[(i, []) for i in range(1, n + 1)],
                            advance=False, now=T0)

    def test_reset_then_register_again(self):
        self.register("s1", ("a", "b"))
        self.conn.execute("INSERT INTO scope (work, path, origin, registered_at) "
                          "VALUES (?, 'extra', 'waiver', 'x')", (self.w,))
        self.conn.execute("INSERT INTO subagents (id, type, work, task, state, report) "
                          "VALUES ('ag1', 'impl', ?, 1, 'done', 'vecchio')", (self.w,))
        self.assertEqual(scope.reset_plan(self.conn, self.w, now=T0), [1, 2])
        row = phases.get_work(self.conn, self.w)
        self.assertEqual((row["plan_sha"], row["plan_path"]), (None, "p.md"))
        self.assertEqual(scope.paths(self.conn, self.w), {"extra"})
        self.assertEqual(self.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 0)
        ev = [e for e in events.export_events(self.conn, 0) if e["type"] == "plan_reset"]
        self.assertEqual([e["data"] for e in ev], [{"plan_sha": "s1", "tasks": [1, 2]}])
        # la riga storica del subagente non si aggancia ai task rinumerati del piano nuovo
        self.assertIsNone(self.conn.execute("SELECT task FROM subagents").fetchone()[0])
        self.register("s2", ("c",), n=3)
        self.assertEqual(scope.paths(self.conn, self.w), {"extra", "c"})
        self.assertEqual(self.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 3)
        self.assertEqual(phases.get_work(self.conn, self.w)["plan_sha"], "s2")

    def test_reset_plan_drops_task_lookups(self):
        self.register("s1", ("a",))
        lookups.record(self.conn, work=self.w, task=2, agent_id="ag", session="s",
                       kind="read", target="src/a.py", now=T0)
        self.assertEqual(len(lookups.for_task(self.conn, self.w, 2)), 1)
        scope.reset_plan(self.conn, self.w, now=T0)
        self.assertEqual(lookups.for_task(self.conn, self.w, 2), [])
        self.register("s2", ("a",))
        self.assertEqual(lookups.for_task(self.conn, self.w, 2), [])

    def test_reset_without_plan_is_noop_without_event(self):
        self.assertEqual(scope.reset_plan(self.conn, self.w, now=T0), [])
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM events WHERE type='plan_reset'").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
