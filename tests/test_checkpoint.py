import re
import unittest

from tests.flowkit import FlowLab
from tests.hookkit import T0
from tests.test_check_session import context_of, start_payload
from tollgate_core import db, phases, reviews, tasks
from tollgate_core.paths import program_command
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
        self.assertIn(f"{program_command(db.BIN_PATH)} task start 1", step())
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

    def test_next_step_in_phases_without_tasks(self):
        def step(phase):
            self.conn.execute("UPDATE work_items SET phase = ? WHERE id = ?", (phase, self.work))
            self.conn.commit()
            return checkpoint.next_step(self.conn, self.work)

        got = step("plan")
        for needle in ("superpowers:writing-plans", "7.5", "committalo", "/tollgate:execute"):
            self.assertIn(needle, got)
        for phase in ("spec_audit", "approval"):
            self.assertIn("P3c", step(phase))
        self.assertIn("/tollgate:finish", step("execution"))

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

    def test_stopped_by_review_cycles(self):
        self.add(1)
        b = phases.open_block(self.conn, self.fl.ts.state, self.work, "needs_you",
                              reviews.CAP_REASON, now=T0)
        got = checkpoint.stopped_by(self.conn, self.work)
        self.assertEqual(got, [f"tetto: cicli di revisione (blocco {b})"])
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


    # --- fasi di chiusura (P3b, Task 15) ---

    def set_phase(self, phase):
        self.conn.execute("UPDATE work_items SET phase = ? WHERE id = ?", (phase, self.work))
        self.conn.commit()

    def step(self):
        return checkpoint.next_step(self.conn, self.work)

    def open_cycle(self, *, stage="review", outcome=None):
        n = reviews.open_cycle(self.conn, self.work, sha="a" * 40, patch_id=None, code="c0de",
                               reviewers=["tollgate:final-reviewer"], now=T0)
        self.conn.execute("UPDATE review_cycles SET stage = ?, outcome = ? WHERE work = ? "
                          "AND number = ?", (stage, outcome, self.work, n))
        self.conn.commit()
        return n

    def test_steps_use_program_command(self):
        prog = program_command(db.BIN_PATH)
        subcommands = re.compile(r"(task (?:start|done|review-prepare)|finish open-pr|review prepare)")
        steps = []
        self.add(1)
        steps.append(self.step())
        self.set_task(1, state="review")
        steps.append(self.step())
        self.set_task(1, state="done")
        self.set_phase("review")
        steps.append(self.step())
        n = self.open_cycle(stage="verify")
        steps.append(self.step())
        self.conn.execute("UPDATE review_cycles SET stage = 'closed', outcome = 'ok'")
        steps.append(self.step())
        self.conn.execute("UPDATE review_cycles SET outcome = 'needs_fix'")
        self.add_finding(n)
        steps.append(self.step())
        self.assertEqual(len(steps), 6)
        for st in steps:
            hits = subcommands.findall(st)
            self.assertTrue(hits, st)
            self.assertEqual(st.count(f"{prog} "), len(hits), st)
            self.assertNotIn(str(db.BIN_PATH), st.replace(prog, ""))

    def test_prepared_review_not_reprepared(self):
        self.add(1, "start", "report_done")
        self.assertIn("task review-prepare 1", self.step())
        run = self.fl.wt / ".tollgate-run/7"
        run.mkdir(parents=True)
        (run / "review-1.md").write_text("b", encoding="utf-8")
        (run / "review-2.md").write_text("b", encoding="utf-8")
        self.set_task(1, review_sha="abc", review_code="c0de", reviewer_type="tollgate:task-reviewer")
        got = self.step()
        self.assertNotIn("review-prepare", got)
        for needle in ("revisione preparata", "tollgate:task-reviewer", str(run / "review-2.md")):
            self.assertIn(needle, got)

    def test_fix_rounds_cap_asks_user(self):
        self.add(1, "start", "report_done")
        b = phases.open_block(self.conn, self.fl.ts.state, self.work, "needs_you",
                              "giri di correzione esauriti sul task 1", now=T0)
        got = self.step()
        for needle in ("giri di correzione esauriti sul task 1", "/tollgate:approve rounds <n>",
                       f"/tollgate:resolve {b}", "/tollgate:abandon #7"):
            self.assertIn(needle, got)

    def test_review_cycles_cap_asks_user(self):
        self.add(1, "start", "report_done")
        b = phases.open_block(self.conn, self.fl.ts.state, self.work, "needs_you",
                              reviews.CAP_REASON, now=T0)
        got = self.step()
        for needle in (reviews.CAP_REASON, "/tollgate:approve rounds <n>",
                       f"/tollgate:resolve {b}", "/tollgate:abandon #7"):
            self.assertIn(needle, got)

    def test_review_phase_steps(self):
        prog = program_command(db.BIN_PATH)
        self.set_phase("review")
        self.assertEqual(self.step(), f"revisione finale da preparare: {prog} review prepare")
        n = self.open_cycle(stage="review")
        self.assertIn(f"{prog} review prepare", self.step())
        self.assertIn("stadio review", self.step())
        self.conn.execute("UPDATE review_cycles SET stage = 'verify' WHERE number = ?", (n,))
        self.conn.commit()
        self.assertIn("stadio verify", self.step())
        self.assertIn(f"{prog} review prepare", self.step())
        self.conn.execute("UPDATE review_cycles SET stage = 'closed', outcome = 'ok' "
                          "WHERE number = ?", (n,))
        self.conn.commit()
        self.assertEqual(self.step(), f"{prog} finish open-pr")
        self.conn.execute("UPDATE review_cycles SET outcome = 'superseded' WHERE number = ?", (n,))
        self.conn.commit()
        self.assertIn("review prepare", self.step())

    def test_pr_open_step(self):
        self.set_phase("pr_open")
        self.conn.execute("UPDATE work_items SET pr_number = 12 WHERE id = ?", (self.work,))
        self.conn.commit()
        got = self.step()
        for needle in ("PR #12 aperta: attendi il gate", "/tollgate:start #7 --reopen-execution",
                       "/tollgate:sync"):
            self.assertIn(needle, got)

    def test_pr_open_without_pr_step(self):
        self.set_phase("pr_open")
        got = self.step()
        for needle in ("PR chiusa senza merge", "/tollgate:start #7 --reopen-execution",
                       "/tollgate:finish", "/tollgate:abandon #7"):
            self.assertIn(needle, got)

    def add_finding(self, cycle):
        self.conn.execute("INSERT INTO findings (id, work, cycle, severity, verification, "
                          "blocking) VALUES ('f1', ?, ?, 'major', 'confirmed', 1)",
                          (self.work, cycle))
        self.conn.commit()

    def test_needs_fix_points_to_from_findings(self):
        prog = program_command(db.BIN_PATH)
        n = self.open_cycle(stage="closed", outcome="needs_fix")
        self.add_finding(n)
        self.set_phase("review")
        self.assertEqual(self.step(), f"{prog} task start --from-findings {n}")
        self.set_phase("execution")
        self.assertEqual(self.step(), f"{prog} task start --from-findings {n}")
        tasks.add_task(self.conn, self.work, 1, source=f"cycle:{n}", kind="fix", now=T0)
        self.set_task(1, state="done")
        self.assertEqual(self.step(), "/tollgate:finish")

    def test_ok_cycle_after_dismiss_points_to_finish(self):
        self.open_cycle(stage="closed", outcome="ok")
        self.assertEqual(self.step(), "/tollgate:finish")


if __name__ == "__main__":
    unittest.main()
