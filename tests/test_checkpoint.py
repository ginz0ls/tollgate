import unittest

from tests.flowkit import FlowLab
from tests.hookkit import T0
from tests.test_check_session import context_of, start_payload
from tollgate_core import phases, tasks
from tollgate_flow import checkpoint


class CheckpointCase(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab(issue=7)
        self.addCleanup(self.fl.close)
        self.conn, self.work = self.fl.conn, self.fl.work

    def add(self, number, *events):
        tasks.add_task(self.conn, self.work, number, source="plan", now=T0)
        for e in events:
            tasks.task_event(self.conn, self.work, number, e, now=T0)

    def cp_path(self):
        return self.fl.wt / "docs/superpowers/reviews/7/checkpoint.md"

    def write(self, note=None):
        return checkpoint.write_checkpoint(self.fl.ts.state, self.fl.wt, note=note, now=T0)

    def set_task(self, number, **cols):
        sets = ", ".join(f"{c} = ?" for c in cols)
        self.conn.execute(f"UPDATE tasks SET {sets} WHERE work = ? AND number = ?",
                          (*cols.values(), self.work, number))
        self.conn.commit()

    def test_checkpoint_written_and_ignored_by_git(self):
        self.add(1, "start")
        path = self.write("a mano")
        self.assertEqual(path, self.cp_path())
        text = path.read_text(encoding="utf-8")
        for needle in ("execution", "L1", "1 running", "a mano", "prossimo passo"):
            self.assertIn(needle, text)
        self.assertEqual(self.fl.git("status", "--porcelain", repo=self.fl.wt).strip(), "")
        self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_cli_checkpoint_prints_only_path(self):
        self.add(1, "start")
        r = self.fl.cli("status", "--checkpoint", "--note", "da cli", cwd=self.fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), f"checkpoint scritto: {self.cp_path()}")
        self.assertIn("da cli", self.cp_path().read_text(encoding="utf-8"))

    def test_cli_checkpoint_outside_work_refused(self):
        r = self.fl.cli("status", "--checkpoint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("nessun lavoro attivo", r.stderr)

    def test_next_step_sequence(self):
        def step():
            return checkpoint.next_step(self.conn, self.work)

        self.add(1)
        self.add(2)
        self.assertIn("task start 1", step())
        self.assertNotIn("--fix", step())
        tasks.task_event(self.conn, self.work, 1, "start", now=T0)
        self.set_task(1, implementer="impl-7-1")
        self.assertIn("impl-7-1", step())
        tasks.task_event(self.conn, self.work, 1, "report_done", now=T0)
        self.assertIn("task review-prepare 1", step())
        self.set_task(1, verdict="changes", review_sha="abc")
        self.assertIn("task start 1 --fix", step())
        self.set_task(1, review_sha=None)
        self.assertIn("task review-prepare 1", step())
        self.set_task(1, verdict="approved", review_sha="abc")
        self.assertIn("task done 1", step())
        tasks.task_event(self.conn, self.work, 1, "approved", now=T0)
        self.assertIn("task start 2", step())
        tasks.task_event(self.conn, self.work, 2, "start", now=T0)
        tasks.task_event(self.conn, self.work, 2, "report_blocked", now=T0)
        self.assertIn("/tollgate:resolve", step())
        tasks.task_event(self.conn, self.work, 2, "unblocked", now=T0)
        tasks.task_event(self.conn, self.work, 2, "start", now=T0)
        tasks.task_event(self.conn, self.work, 2, "report_done", now=T0)
        self.set_task(2, verdict="approved", review_sha="abc")
        tasks.task_event(self.conn, self.work, 2, "approved", now=T0)
        self.assertIn("/tollgate:finish", step())

    def test_notes_kept_last_five(self):
        self.add(1)
        for i in range(1, 8):
            self.write(f"nota {i}\nseconda riga {i}")
        text = self.cp_path().read_text(encoding="utf-8")
        for i in (3, 4, 5, 6, 7):
            self.assertIn(f"nota {i}\n", text)
        for i in (1, 2):
            self.assertNotIn(f"nota {i}\n", text)
        self.assertTrue(text.rstrip().splitlines()[-1].startswith("prossimo passo"))
        self.write()
        self.assertIn("nota 7", self.cp_path().read_text(encoding="utf-8"))

    def test_stopped_by_budget_and_rounds(self):
        self.add(1)
        st = self.fl.ts.state
        b1 = phases.open_block(self.conn, st, self.work, "needs_you",
                               "budget superato: 9000 token oltre il tetto sul task 1", now=T0)
        b2 = phases.open_block(self.conn, st, self.work, "needs_you",
                               "giri di correzione esauriti sul task 1", now=T0)
        phases.open_block(self.conn, st, self.work, "needs_you", "altro motivo", now=T0)
        got = checkpoint.stopped_by(self.conn, self.work)
        self.assertEqual(got, [f"tetto: budget del task (blocco {b1})",
                               f"tetto: giri di correzione (blocco {b2})"])
        self.assertIn(got[0], self.write().read_text(encoding="utf-8"))

    def test_session_start_injects_checkpoint(self):
        self.add(1)
        for i in range(5):
            self.write(f"nota {i}\nseconda riga {i}")
        r = self.fl.hook(start_payload(self.fl.lab, "sess-flow", cwd=self.fl.wt))
        ctx = context_of(r)
        self.assertTrue(ctx.splitlines()[-1].startswith("prossimo passo"), ctx)
        self.assertLessEqual(len(ctx.splitlines()), 10)
        self.assertLessEqual(len(ctx), 1500)


if __name__ == "__main__":
    unittest.main()
