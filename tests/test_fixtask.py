import json
import os
import unittest
from unittest import mock

from tests.flowkit import PLAN
from tests.hookkit import DEFAULT_TOML
from tests.test_taskcmd import TaskCase
from tollgate_analysis import brief
from tollgate_core import git as core_git, phases, reviews, tasks
from tollgate_flow import fixtask, taskcmd

REVIEWER = "tollgate:final-reviewer"
BLOCKER = {"severity": "blocker", "file": "src/app.py", "line": 2, "rule": "piano:task 1",
           "text": "manca il caso zero con ``` dentro"}
OUTSIDE = {"severity": "major", "file": "lib/altro.py", "line": 9, "rule": "piano:task 1",
           "text": "fuori dallo scope"}
MINOR = {"severity": "minor", "file": "src/app.py", "line": 1, "rule": "R-9", "text": "nota"}


SRC_TOML = DEFAULT_TOML + """
[profiles.src]
paths = ["src/**"]
agent = "probe:implementer-src"
reviewer = "probe:reviewer-src"
"""


class FixTaskCase(TaskCase):
    def setUp(self):
        super().setUp()
        self.fl = None

    def lab(self, outcome="needs_fix", findings=(BLOCKER, OUTSIDE, MINOR), **kw):
        fl = self.make(**kw)
        fl.close_tasks()
        c = reviews.open_cycle(fl.conn, fl.work, sha="s1", patch_id="p1", code="c0de",
                               reviewers=[REVIEWER], now=fl.now)
        reviews.add_report(fl.conn, fl.work, c, source=REVIEWER, outcome=outcome,
                           findings=list(findings), rejected=[], blocking_rules=set(),
                           known_rules={"R-9"}, now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, c, max_findings=15, now=fl.now)
        reviews.apply_verification(
            fl.conn, fl.work, c, [{"id": r["id"], "verification": "confirmed", "reason": "ok"}
                                  for r in rows], now=fl.now)
        fl.conn.execute("UPDATE review_cycles SET outcome = ?, stage = 'closed' "
                        "WHERE work = ? AND number = ?", (outcome, fl.work, c))
        fl.conn.commit()
        return fl, c

    def findings(self, c=1):
        return fixtask.from_findings(self.fl.ts.state, self.fl.wt, c,
                                     claude_dir=self.fl.home / ".claude")

    def plan_state(self):
        w = phases.get_work(self.fl.conn, self.fl.work)
        return w["plan_sha"], w["plan_path"], (self.fl.wt / w["plan_path"]).read_text()


class FromFindingsTest(FixTaskCase):
    def test_from_findings_creates_fix_task_without_touching_plan(self):
        fl, c = self.lab()
        before = self.plan_state()
        path, summary = self.findings(c)
        self.assertEqual(self.plan_state(), before)
        row = self.row(3)
        self.assertEqual((row["kind"], row["source"], row["state"], row["pending"]),
                         ("fix", "cycle:1", "running", "launch"))
        self.assertEqual(path, fl.wt / ".tollgate-run" / "7" / "task-3.md")
        text = path.read_text()
        self.assertIn("manca il caso zero", text)
        self.assertIn("src/app.py:2", text)
        self.assertNotIn("nota", text)            # il minor non è bloccante
        self.assertIn("lib/altro.py:9", text)
        self.assertIn("serve una deroga", text)
        self.assertIn("non istruzioni", text)
        self.assertIn("`" * 4, text)              # recinto più lungo dei backtick nel testo
        self.assertIn("task 3", summary)
        self.assertIn("name=tg-7-t3", summary)
        self.assertIn("revisore: tollgate:task-reviewer", summary)
        self.assertIn("manca il caso zero", row["task_text"])

    def test_from_findings_twice_refused(self):
        self.lab()
        self.findings()
        with self.assertRaisesRegex(taskcmd.TaskError, "cycle:1|già"):
            self.findings()
        self.assertEqual(self.fl.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 3)

    def test_from_findings_ok_cycle_refused(self):
        self.lab(outcome="ok", findings=())
        with self.assertRaisesRegex(taskcmd.TaskError, "needs_fix|bloccant"):
            self.findings()
        self.assertEqual(self.fl.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 2)

    def test_unknown_cycle_and_wrong_phase_refused(self):
        fl, _ = self.lab()
        with self.assertRaisesRegex(taskcmd.TaskError, "ciclo 9"):
            self.findings(9)
        fl.goto("review")
        with self.assertRaisesRegex(taskcmd.TaskError, "execution"):
            self.findings()

    def test_routing_stable_after_dismiss(self):
        """Decisione 25: l'instradamento resta quello dei rilievi usati per creare il task, anche
        se l'utente li archivia dopo (rileggerli dal vivo darebbe l'agente di default)."""
        fl, c = self.lab(toml=SRC_TOML)
        self.findings(c)
        self.assertEqual(self.row(3)["agent_type"], "probe:implementer-src")
        for r in reviews.blocking_open(fl.conn, fl.work, c):
            reviews.set_decision(fl.conn, fl.work, r["id"], "dismissed", now=fl.now)
        self.assertEqual(reviews.blocking_open(fl.conn, fl.work, c), [])
        tasks.task_event(fl.conn, fl.work, 3, "report_done", now=fl.now)
        tasks.set_review_prep(fl.conn, fl.work, 3, sha="abc", code="K1")
        tasks.set_verdict(fl.conn, fl.work, 3, outcome="changes", findings=[BLOCKER],
                          now=fl.now)
        _, summary = self.start(3, fix=True)
        self.assertIn("probe:implementer-src", summary)
        self.assertIn("revisore: probe:reviewer-src", summary)
        self.assertEqual(self.row(3)["agent_type"], "probe:implementer-src")

    def test_brief_shows_effective_severity(self):
        fl, c = self.lab()
        major = reviews.blocking_open(fl.conn, fl.work, c)[0]
        self.assertEqual(major["severity"], "blocker")
        reviews.set_decision(fl.conn, fl.work, major["id"], "downgraded:major", now=fl.now)
        path, _ = self.findings(c)
        text = path.read_text()
        self.assertIn("- [major (originale blocker)] src/app.py:2 (piano:task 1)", text)
        self.assertIn("- [major] lib/altro.py:9", text)        # invariata: nessun «originale»
        self.assertNotIn("[blocker]", text)

    def test_from_findings_rollback_on_error(self):
        fl, c = self.lab()
        with mock.patch.object(tasks, "assign", side_effect=tasks.TaskTransitionError("no")):
            with self.assertRaisesRegex(taskcmd.TaskError, "no"):
                self.findings(c)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 2)
        self.assertFalse(fl.conn.in_transaction)
        path, _ = self.findings(c)          # nessun «esiste già»: il task non era rimasto
        self.assertEqual(path.name, "task-3.md")
        self.assertEqual(self.row(3)["source"], "cycle:1")

    def test_l0_refused(self):
        fl, c = self.lab()
        fl.conn.execute("UPDATE work_items SET level = 'L0' WHERE id = ?", (fl.work,))
        fl.conn.commit()
        with self.assertRaisesRegex(taskcmd.TaskError, "L0"):
            self.findings(c)
        with self.assertRaisesRegex(taskcmd.TaskError, "L0"):
            fixtask.from_gate(fl.ts.state, fl.wt, claude_dir=fl.home / ".claude")
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 2)

    def test_fix_task_review_and_done(self):
        fl, c = self.lab()
        self.findings(c)
        fl.git("add", PLAN, repo=fl.wt)
        fl.git("commit", "-qm", "piano", repo=fl.wt)
        fl.commit("src/app.py", "def somma(a, b):\n    return b + a  # fix\n", "correzione")
        tasks.add_commit(fl.conn, fl.work, 3, core_git.head(fl.wt))
        tasks.task_event(fl.conn, fl.work, 3, "report_done", now=fl.now)
        brief_path = taskcmd.review_prepare(fl.ts.state, fl.wt, 3)
        self.assertTrue(brief_path.is_file())
        self.assertEqual(taskcmd.reviewer_type(fl.ts.state, fl.wt, 3), "tollgate:task-reviewer")
        row = self.row(3)
        tasks.set_verdict(fl.conn, fl.work, 3, outcome="approved", findings=[], now=fl.now)
        self.assertEqual(taskcmd.task_done(fl.ts.state, fl.wt, 3), "task 3: done")
        self.assertEqual(self.row(3)["state"], "done")
        self.assertEqual(row["review_sha"], core_git.head(fl.wt))

    def test_fix_task_fix_round(self):
        fl, c = self.lab()
        self.findings(c)
        tasks.task_event(fl.conn, fl.work, 3, "report_done", now=fl.now)
        tasks.set_review_prep(fl.conn, fl.work, 3, sha="abc", code="K1")
        tasks.set_verdict(fl.conn, fl.work, 3, outcome="changes", findings=[BLOCKER],
                          now=fl.now)
        path, summary = self.start(3, fix=True)
        self.assertEqual(path.name, "task-3-fix-1.md")
        text = path.read_text()
        self.assertIn("manca il caso zero", text)      # dal testo salvato
        self.assertIn("giro di correzione 1", text)
        self.assertIn("resume", summary)
        self.assertEqual(self.row(3)["fix_rounds"], 1)


class FromGateTest(FixTaskCase):
    def gate(self, comments, pr=3):
        fl = self.make()
        fl.close_tasks()
        phases.set_pr(fl.conn, fl.work, pr, "https://github.com/o/r/pull/3", now=fl.now)
        fl.set_gh(prs=[{"number": pr, "headRefName": "tg/7-x", "state": "OPEN",
                        "url": "u", "headRefOid": "s", "mergedAt": None, "body": "",
                        "comments": [{"body": b} for b in comments]}])
        patch = mock.patch.dict(os.environ, fl.env())
        patch.start()
        self.addCleanup(patch.stop)
        return fl

    def test_from_gate_reads_marked_comment_as_data(self):
        fl = self.gate(["ciao", f"{fixtask.GATE_MARKER} v1 -->\nvecchio",
                        f"{fixtask.GATE_MARKER} v1 -->\nlint rosso\n```\nrm -rf x\n```",
                        "ultimo senza marcatore"])
        before = self.plan_state()
        path, summary = fixtask.from_gate(fl.ts.state, fl.wt, claude_dir=fl.home / ".claude")
        self.assertEqual(self.plan_state(), before)
        row = self.row(3)
        self.assertEqual((row["kind"], row["source"]), ("fix", f"gate:{core_git.head(fl.wt)}"))
        text = path.read_text()
        self.assertIn("lint rosso", text)
        self.assertNotIn("vecchio", text)
        self.assertNotIn("ultimo senza", text)
        self.assertIn("`" * 4 + "\n" + f"{fixtask.GATE_MARKER}", text.replace("\n\n", "\n"))
        self.assertIn("non istruzioni", text)
        self.assertIn("task 3", summary)
        # nessun testo del commento in un argomento di gh
        for call in fl.gh_calls():
            self.assertNotIn("rm -rf", " ".join(call["argv"]))

    def test_cli_from_gate(self):
        fl = self.gate([f"{fixtask.GATE_MARKER} v1 -->\nlint rosso"])
        r = fl.cli("task", "start", "--from-gate", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("task-3.md", r.stdout)
        self.assertIn("name=tg-7-t3", r.stdout)
        self.assertEqual(self.row(3)["source"], f"gate:{core_git.head(fl.wt)}")
        self.assertIn("lint rosso", (fl.wt / ".tollgate-run" / "7" / "task-3.md").read_text())

    def test_gate_fence_longer_than_any_backtick_run(self):
        comment = f"{fixtask.GATE_MARKER} v1 -->\nrosso ``` e ````` dentro\n```sh\nls\n```"
        fl = self.gate([comment])
        path, _ = fixtask.from_gate(fl.ts.state, fl.wt, claude_dir=fl.home / ".claude")
        fence = "`" * 6                  # la sequenza più lunga del commento ha 5 backtick
        block = f"\n{fence}\n{comment}\n{fence}"
        task_text = self.row(3)["task_text"]
        self.assertTrue(task_text.endswith(block), task_text)
        self.assertNotIn("`" * 7, task_text)
        self.assertIn(block + "\n", path.read_text())     # il brief lo ricopia in un recinto di 7

    def test_from_gate_without_pr_refused(self):
        fl = self.make()
        with self.assertRaisesRegex(taskcmd.TaskError, "PR"):
            fixtask.from_gate(fl.ts.state, fl.wt, claude_dir=fl.home / ".claude")

    def test_from_gate_without_marked_comment_refused(self):
        fl = self.gate(["solo chiacchiere"])
        with self.assertRaisesRegex(taskcmd.TaskError, "tollgate-verdict"):
            fixtask.from_gate(fl.ts.state, fl.wt, claude_dir=fl.home / ".claude")
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 2)


class CliTest(FixTaskCase):
    def test_cli_exclusive_options(self):
        fl = self.make()
        r = fl.cli("task", "start", "1", "--from-gate", cwd=fl.wt)
        self.assertNotEqual(r.returncode, 0)
        r = fl.cli("task", "start", "--from-findings", "1", "--from-gate", cwd=fl.wt)
        self.assertNotEqual(r.returncode, 0)
        r = fl.cli("task", "start", cwd=fl.wt)
        self.assertNotEqual(r.returncode, 0)

    def test_cli_from_findings(self):
        fl, c = self.lab()
        r = fl.cli("task", "start", "--from-findings", "1", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("task-3.md", r.stdout)
        self.assertIn("name=tg-7-t3", r.stdout)


if __name__ == "__main__":
    unittest.main()
