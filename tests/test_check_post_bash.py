import unittest

from tests.hookkit import SESSION, Lab
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import acts, phases, subagents, tasks


class PostBashTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab, ("src/app.py", "tests/test_app.py"))

    def tearDown(self):
        self.lab.close()

    def test_new_commit_recorded_and_finish_invalidated(self):
        head0 = git(self.lab.wt, "rev-parse", "HEAD")
        acts.record_act(self.lab.conn, type_="finish", typed_text="/tollgate:finish",
                        session=SESSION, work=self.lab.work, head_sha=head0, now=self.lab.now,
                        ttl_minutes=10)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        subagents.start(self.lab.conn, agent_id="a1", type_="tollgate:implementer",
                        session=SESSION, work=self.lab.work, task=1, base_sha=head0,
                        fingerprint="f", now=self.lab.now)
        (self.lab.wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
        git(self.lab.wt, "commit", "-qam", "ok")
        head1 = git(self.lab.wt, "rev-parse", "HEAD")
        r = self.lab.bash("git commit -qam ok", post=True, agent_id="a1")
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.lab.events("commit"), [{"sha": head1}])
        self.assertEqual(self.lab.conn.execute("SELECT state FROM acts WHERE type='finish'")
                         .fetchone()[0], "expired")
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["commits"],
                         f'["{head1}"]')
        self.lab.bash("git status", post=True, agent_id="a1")
        self.assertEqual(len(self.lab.events("commit")), 1)

    def _finish_state(self):
        return self.lab.conn.execute("SELECT state FROM acts WHERE type='finish'").fetchone()[0]

    def test_head_moved_without_new_commits_invalidates_finish(self):
        (self.lab.wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
        git(self.lab.wt, "commit", "-qam", "ok")
        head1 = git(self.lab.wt, "rev-parse", "HEAD")
        acts.record_act(self.lab.conn, type_="finish", typed_text="/tollgate:finish",
                        session=SESSION, work=self.lab.work, head_sha=head1, now=self.lab.now,
                        ttl_minutes=10)
        self.assertEqual(self.lab.bash("git status", post=True).exit, 0)
        self.assertEqual(self._finish_state(), "pending")
        git(self.lab.wt, "reset", "-q", "--soft", "HEAD~1")
        self.assertEqual(self.lab.bash("git reset --soft HEAD~1", post=True).exit, 0)
        self.assertEqual(self._finish_state(), "expired")

    def test_merge_bringing_deleted_test_opens_needs_you(self):
        git(self.lab.main, "checkout", "-q", "-b", "altro")
        (self.lab.main / "tests/test_app.py").unlink()
        git(self.lab.main, "commit", "-qam", "via il test")
        git(self.lab.main, "checkout", "-q", "main")
        git(self.lab.wt, "merge", "-q", "--no-edit", "altro")
        r = self.lab.bash("git merge altro", post=True)
        self.assertEqual(r.exit, 2)
        w = phases.get_work(self.lab.conn, self.lab.work)
        self.assertEqual(w["phase"], "blocked")
        self.assertEqual(self.lab.conn.execute("SELECT type FROM blocks").fetchone()[0],
                         "needs_you")

    def test_branch_changed_opens_needs_you(self):
        git(self.lab.wt, "checkout", "-q", "-b", "fuga")
        self.lab.bash("git checkout -b fuga", post=True)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")


if __name__ == "__main__":
    unittest.main()
