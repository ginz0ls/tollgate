import json
import unittest

from tests.flowkit import FlowLab
from tests.hookkit import DEFAULT_TOML
from tests.test_check_post_edit import SECTIONS
from tollgate_core import phases, tasks
from tollgate_flow import taskcmd

PLAN = "docs/superpowers/plans/2026-10-16-somma.md"
FINDING = {"severity": "major", "file": "src/app.py", "line": 2, "rule": "R-1",
           "text": "manca il caso zero"}
WEB_TOML = DEFAULT_TOML + """
[profiles.web]
paths = ["web/**"]
skills = ["ghost-skill", "present-skill", "s3", "s4"]
agent = "probe:web-dev"
reviewer = "probe:web-reviewer"
"""


def plan_text(task2="- Create: `docs/uso.md`"):
    out = []
    for s in SECTIONS:
        body = ("M1. Somma — test: tests.test_app::test_somma\n"
                "M2. Zero — test: tests.test_app::test_zero") if s == "Must-have" else "x"
        out += [f"## {s}", body, ""]
    out += ["### Task 1: Somma", "- Modify: `src/app.py`", "- Test: `tests/test_app.py`",
            "**Must-have**: M1", "", "### Task 2: Pagina", task2, ""]
    return "\n".join(out) + "\n"


class TaskCase(unittest.TestCase):
    def make(self, *, toml=DEFAULT_TOML, plan=None, **kw):
        fl = FlowLab(issue=7, phase="plan", toml=toml, **kw)
        self.addCleanup(fl.close)
        self.fl = fl
        path = fl.wt / PLAN
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan or plan_text())
        r = fl.post_edit(path)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(phases.get_work(fl.conn, fl.work)["phase"], "execution")
        skills = fl.home / ".claude" / "skills" / "present-skill"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("x\n")
        return fl

    def start(self, number=1, *, fix=False):
        return taskcmd.task_start(self.fl.ts.state, self.fl.wt, number, fix=fix,
                                  claude_dir=self.fl.home / ".claude")

    def row(self, number=1):
        return tasks.get_task(self.fl.conn, self.fl.work, number)

    def to_changes(self):
        """Il task torna in review e il revisore chiede modifiche."""
        tasks.task_event(self.fl.conn, self.fl.work, 1, "report_done", now=self.fl.now)
        tasks.set_review_prep(self.fl.conn, self.fl.work, 1, sha="abc", code="K1")
        tasks.set_verdict(self.fl.conn, self.fl.work, 1, outcome="changes",
                          findings=[FINDING], now=self.fl.now)


class TaskStartTest(TaskCase):
    def test_task_start_writes_brief_and_assigns(self):
        fl = self.make()
        path, summary = self.start()
        self.assertEqual(path, fl.wt / ".tollgate-run" / "7" / "task-1.md")
        brief = path.read_text()
        self.assertIn("tg-7-t1", brief)
        self.assertIn("Task 1", brief)
        self.assertIn("tests.test_app::test_somma", brief)
        self.assertNotIn("test_zero", brief)  # la riga Must-have: del task limita i test
        self.assertIn("tests/test_app.py", brief)
        self.assertIn("src/app.py", brief)
        row = self.row()
        self.assertEqual((row["state"], row["pending"], row["implementer"], row["agent_type"],
                          row["reviewer_type"]),
                         ("running", "launch", "tg-7-t1", "tollgate:implementer",
                          "tollgate:task-reviewer"))
        for part in ("tollgate:implementer", "tg-7-t1", "launch"):
            self.assertIn(part, summary)
        self.assertNotIn("\n", summary)
        self.assertNotIn("model: inherit", summary)
        self.assertIn("verify", brief)

    def test_task_without_must_have_line_links_all(self):
        self.make()
        path, _ = self.start(2)
        brief = path.read_text()
        self.assertIn("test_somma", brief)
        self.assertIn("test_zero", brief)

    def test_task_start_only_from_pending(self):
        self.make()
        self.start()
        with self.assertRaisesRegex(taskcmd.TaskError, "pending"):
            self.start()
        with self.assertRaises(taskcmd.TaskError):
            self.start(fix=True)

    def test_unknown_task(self):
        self.make()
        with self.assertRaisesRegex(taskcmd.TaskError, "9"):
            self.start(9)

    def test_l0_refuses(self):
        fl = FlowLab(issue=7, level="L0")
        self.addCleanup(fl.close)
        self.fl = fl
        with self.assertRaisesRegex(taskcmd.TaskError, "in L0 lavora la sessione principale"):
            self.start()

    def test_only_in_execution(self):
        fl = self.make()
        fl.goto("review")
        with self.assertRaisesRegex(taskcmd.TaskError, "execution"):
            self.start()

    def test_outside_a_work_refuses(self):
        fl = self.make()
        with self.assertRaisesRegex(taskcmd.TaskError, "nessun lavoro"):
            taskcmd.task_start(fl.ts.state, fl.main, 1, fix=False,
                               claude_dir=fl.home / ".claude")

    def test_profile_agent_chosen(self):
        self.make(toml=WEB_TOML, plan=plan_text("- Create: `web/page.tsx`"))
        path, summary = self.start(2)
        row = self.row(2)
        self.assertEqual((row["agent_type"], row["reviewer_type"]),
                         ("probe:web-dev", "probe:web-reviewer"))
        self.assertIn("probe:web-dev", summary)
        self.assertIn("tg-7-t2", path.read_text())

    def test_absent_skill_removed_from_required(self):
        self.make(toml=WEB_TOML, plan=plan_text("- Create: `web/page.tsx`"))
        # registrazione del piano: i primi 3 dei profili
        self.assertEqual(json.loads(self.row(2)["skills_required"]),
                         ["ghost-skill", "present-skill", "s3"])
        path, _ = self.start(2)
        brief = path.read_text()
        self.assertEqual(json.loads(self.row(2)["skills_required"]), ["present-skill"])
        self.assertIn("- ghost-skill (assente)", brief)
        self.assertIn("- s3 (assente)", brief)
        self.assertIn("- present-skill\n", brief)
        self.assertNotIn("s4", brief)  # tetto di 3: stesse skill nel brief e in skills_required

    def test_plan_changed_after_registration_refuses(self):
        fl = self.make()
        (fl.wt / PLAN).write_text(plan_text() + "\nmodificato\n")
        with self.assertRaisesRegex(taskcmd.TaskError, "piano diverso dalla versione registrata"):
            self.start()
        self.assertEqual(self.row()["state"], "pending")

    def test_plan_blob_in_object_db_is_used(self):
        fl = self.make()
        old = (fl.wt / PLAN).read_text()
        fl.git("add", PLAN, repo=fl.wt)
        fl.git("commit", "-qm", "piano", repo=fl.wt)  # il blob registrato ora è negli oggetti
        (fl.wt / PLAN).write_text(old + "\nmodificato dopo\n")
        fl.git("commit", "-qam", "piano 2", repo=fl.wt)
        path, _ = self.start()
        self.assertNotIn("modificato dopo", path.read_text())


class FixRoundsTest(TaskCase):
    def test_fix_rounds_counted(self):
        self.make()
        self.start()
        for i in (1, 2, 3):
            self.to_changes()
            path, summary = self.start(fix=True)
            row = self.row()
            self.assertEqual((row["fix_rounds"], row["state"], row["pending"],
                              row["implementer"]), (i, "running", "resume", "tg-7-t1"))
            self.assertEqual(path.name, f"task-1-fix-{i}.md")
            self.assertIn("manca il caso zero", path.read_text())
            self.assertIn("resume", summary)
            self.assertNotIn("model: inherit", summary)
            tasks.take_pending(self.fl.conn, self.fl.work, agent_type="tollgate:implementer",
                               resume=True)

    def test_rounds_four_five_new_implementer(self):
        self.make()
        self.start()
        for _ in (1, 2, 3):
            self.to_changes()
            self.start(fix=True)
        for i, name in ((4, "tg-7-t1-r4"), (5, "tg-7-t1-r5")):
            self.to_changes()
            path, summary = self.start(fix=True)
            row = self.row()
            self.assertEqual((row["fix_rounds"], row["implementer"], row["pending"]),
                             (i, name, "launch"))
            self.assertIn("model: inherit", summary)
            self.assertIn(name, summary)
            self.assertIn("model: inherit", path.read_text())
            self.assertIn(f"`{name}`", path.read_text())

    def test_sixth_fix_opens_needs_you(self):
        fl = self.make()
        self.start()
        for _ in range(5):
            self.to_changes()
            self.start(fix=True)
        self.to_changes()
        with self.assertRaisesRegex(taskcmd.TaskError, "giri di correzione esauriti"):
            self.start(fix=True)
        block = fl.conn.execute("SELECT * FROM blocks WHERE closed IS NULL").fetchone()
        self.assertEqual(block["type"], "needs_you")
        self.assertIn("task 1", block["reason"])
        self.assertEqual(phases.get_work(fl.conn, fl.work)["phase"], "blocked")
        self.assertEqual(self.row()["fix_rounds"], 5)

    def test_fix_needs_changes_verdict_and_a_fresh_one_each_round(self):
        self.make()
        self.start()
        tasks.task_event(self.fl.conn, self.fl.work, 1, "report_done", now=self.fl.now)
        with self.assertRaisesRegex(taskcmd.TaskError, "verdetto"):
            self.start(fix=True)
        tasks.set_review_prep(self.fl.conn, self.fl.work, 1, sha="abc", code="K1")
        tasks.set_verdict(self.fl.conn, self.fl.work, 1, outcome="approved", findings=[],
                          now=self.fl.now)
        with self.assertRaisesRegex(taskcmd.TaskError, "changes"):
            self.start(fix=True)
        tasks.set_verdict(self.fl.conn, self.fl.work, 1, outcome="changes",
                          findings=[FINDING], now=self.fl.now)
        self.start(fix=True)
        # dopo --fix e un nuovo report_done il vecchio verdetto non vale più
        tasks.task_event(self.fl.conn, self.fl.work, 1, "report_done", now=self.fl.now)
        with self.assertRaisesRegex(taskcmd.TaskError, "verdetto"):
            self.start(fix=True)
        self.assertEqual(self.row()["fix_rounds"], 1)


class CliTest(TaskCase):
    def test_cli_task_start(self):
        fl = self.make()
        r = fl.cli("task", "start", "1", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertIn(str(fl.wt / ".tollgate-run" / "7" / "task-1.md"), lines[0])
        self.assertIn("tg-7-t1", r.stdout)
        self.assertEqual(self.row()["state"], "running")

    def test_cli_error_exits_1(self):
        fl = self.make()
        self.assertEqual(fl.cli("task", "start", "1", cwd=fl.wt).returncode, 0)
        r = fl.cli("task", "start", "1", cwd=fl.wt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("pending", r.stderr)
        self.assertEqual(fl.cli("task", "start", "1", "--fix", cwd=fl.wt).returncode, 1)


if __name__ == "__main__":
    unittest.main()
