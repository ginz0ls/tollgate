"""Avviso e rifiuto alla prima modifica senza nota di ricerca (B1, Task 7)."""
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tollgate_core import events, lookups, phases, scope, subagents, tasks

IMPL = "tollgate:implementer"
REVIEWER = "tollgate:task-reviewer"
WARNING = "tollgate: informati prima di modificare"
REFUSAL = "nota di ricerca mancante o non valida per il task"


def make_root(approved: bool) -> Path:
    """Copia temporanea della radice del plugin (`bin/` compreso) con `rules-base` approvata o no."""
    d = Path(tempfile.mkdtemp(prefix="tollgate root "))
    shutil.copytree(ROOT / "bin", d / "bin", ignore=shutil.ignore_patterns("__pycache__"))
    skill = d / "skills/rules-base/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: rules-base\n" + ("approved: 2026-10-27\n" if approved else "")
                     + "---\n\nRegole.\n")
    return d


def plan(lab, numbers=(1,), paths=("src/app.py",)):
    scope.register_plan(lab.conn, lab.ts.state, lab.work, plan_path="docs/superpowers/plans/p.md",
                        plan_sha="s", scope_paths=list(paths),
                        plan_tasks=[(n, []) for n in numbers], advance=False, now=lab.now)
    for n in numbers:
        tasks.assign(lab.conn, lab.work, n, implementer=f"impl-{n}", agent_type=IMPL,
                     reviewer_type=REVIEWER, pending="launch", now=lab.now)
        tasks.task_event(lab.conn, lab.work, n, "start", now=lab.now)


def start_agent(lab, agent_id, task):
    subagents.start(lab.conn, agent_id=agent_id, type_=IMPL, session=SESSION, work=lab.work,
                    task=task, base_sha=lab.base, fingerprint="f", now=lab.now)


def edit_and_post(lab, rel, **kw):
    """Una modifica riuscita: PreToolUse, scrittura vera e PostToolUse."""
    path = lab.wt / rel
    pre = lab.pre_edit(path, **kw)
    if pre.exit == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")
        lab.post_edit(path, **kw)
    return pre


class Base(unittest.TestCase):
    approved = True
    level = "L1"
    research = True

    def setUp(self):
        self.root = make_root(self.approved)
        self.lab = Lab(level=self.level, research=self.research, plugin_root=self.root)
        if self.level != "L0":
            plan(self.lab)
            start_agent(self.lab, "a1", 1)
        self.app = self.lab.wt / "src/app.py"

    def tearDown(self):
        self.lab.close()
        shutil.rmtree(self.root, ignore_errors=True)

    def note(self, ok, problems=(), task=1):
        lookups.set_note(self.lab.conn, self.lab.work, task, text="n", ok=ok)
        events.record_event(self.lab.conn, "research_note",
                            {"task": task, "ok": ok, "problems": list(problems)},
                            now=self.lab.now, work=self.lab.work)


class EnforcedTest(Base):
    def test_l1_without_note_denied_when_enforced(self):
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn(REFUSAL + " 1", r.stderr)
        self.assertIn("research submit 1", r.stderr)

    def test_valid_note_passes(self):
        self.note(True)
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertEqual(r.exit, 0)
        self.assertNotIn("informati prima", r.stdout)

    def test_invalid_note_denied_with_problems(self):
        self.note(False, ["il file «src/app.py» è nella nota ma non l'hai letto in questo task",
                          "nessuna fonte esterna senza motivo"])
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn("non l'hai letto", r.stderr)
        self.assertIn("nessuna fonte esterna senza motivo", r.stderr)

    def test_refusal_ignores_problems_before_plan_reset(self):
        self.note(False, ["problema del vecchio piano"])
        scope.reset_plan(self.lab.conn, self.lab.work, now=self.lab.now)
        plan(self.lab)
        start_agent(self.lab, "a2", 1)
        r = self.lab.pre_edit(self.app, agent_id="a2")
        self.assertEqual(r.exit, 2)
        self.assertIn(REFUSAL, r.stderr)
        self.assertNotIn("problema del vecchio piano", r.stderr)

    def test_round4_new_implementer_keeps_valid_note(self):
        self.note(True)
        start_agent(self.lab, "a4", 1)
        self.assertEqual(self.lab.pre_edit(self.app, agent_id="a4").exit, 0)

    def test_resubmitted_invalid_note_blocks_again(self):
        self.note(True)
        self.assertEqual(self.lab.pre_edit(self.app, agent_id="a1").exit, 0)
        self.note(False, ["manca la sezione «Cosa ho trovato»"])
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn("manca la sezione", r.stderr)

    def test_docs_and_run_files_exempt(self):
        for rel in ("docs/superpowers/plans/x.md", ".tollgate-run/1/x", ".superpowers/x",
                    "reports/junit.xml"):
            with self.subTest(rel=rel):
                r = self.lab.pre_edit(self.lab.wt / rel, agent_id="a1")
                self.assertNotIn(REFUSAL, r.stderr)
                self.assertNotIn("informati prima", r.stdout)

    def test_legacy_work_never_reminded(self):
        lab = Lab(research=False, plugin_root=self.root)
        try:
            plan(lab)
            start_agent(lab, "a1", 1)
            r = lab.pre_edit(lab.wt / "src/app.py", agent_id="a1")
            self.assertEqual(r.exit, 0)
            self.assertNotIn("informati prima", r.stdout)
            lab.post_edit(lab.wt / "src/app.py", agent_id="a1")
            self.assertEqual(lab.events("research_reminder"), [])
        finally:
            lab.close()

    def test_bash_write_by_implementer_denied(self):
        r = self.lab.bash("sed -i s/a/b/ src/app.py", agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn(REFUSAL, r.stderr)

    def test_bash_read_not_denied(self):
        r = self.lab.bash("cat src/app.py", agent_id="a1")
        self.assertEqual(r.exit, 0)
        self.assertNotIn(REFUSAL, r.stderr)

    def test_bash_restore_not_denied(self):
        r = self.lab.bash("git checkout -- src/app.py", agent_id="a1")
        self.assertNotIn(REFUSAL, r.stderr)
        self.assertEqual(r.exit, 0, r.stderr)

    def test_bash_relative_target_resolved(self):
        r = self.lab.bash("sed -i s/a/b/ app.py", agent_id="a1", cwd=self.lab.wt / "src")
        self.assertEqual(r.exit, 2)
        self.assertIn(REFUSAL, r.stderr)
        r = self.lab.bash("echo x > ../docs/superpowers/n.md", agent_id="a1",
                          cwd=self.lab.wt / "src")
        self.assertNotIn(REFUSAL, r.stderr)

    def test_bash_exempt_targets_not_gated(self):
        for target in ("docs/superpowers/plans/x.md", ".superpowers/x", ".tollgate-run/1/x",
                       "reports/junit.xml"):
            with self.subTest(target=target):
                r = self.lab.bash(f"echo x > {target}", agent_id="a1")
                self.assertNotIn(REFUSAL, r.stderr)

    def test_other_phase_not_gated(self):
        phases.set_phase(self.lab.conn, self.lab.ts.state, self.lab.work, "review",
                         "finish_check_green", now=self.lab.now)
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertNotIn(REFUSAL, r.stderr)
        self.assertNotIn("informati prima", r.stdout)

    def test_bash_main_session_not_gated(self):
        r = self.lab.bash("sed -i s/a/b/ src/app.py")
        self.assertNotIn(REFUSAL, r.stderr)

    def test_scope_denial_wins(self):
        r = self.lab.pre_edit(self.lab.wt / "src/altro.py", agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn("fuori scope", r.stderr)
        self.assertNotIn(REFUSAL, r.stderr)

    def test_reviewer_not_gated(self):
        subagents.start(self.lab.conn, agent_id="rev", type_=REVIEWER, session=SESSION,
                        work=self.lab.work, task=1, base_sha=self.lab.base, fingerprint="f",
                        now=self.lab.now)
        r = self.lab.pre_edit(self.app, agent_id="rev", agent_type=REVIEWER)
        self.assertNotIn(REFUSAL, r.stderr)

    def test_l0_grown_to_l1_blocks(self):
        lab = Lab(level="L0", research=True, plugin_root=self.root)
        try:
            self.assertEqual(edit_and_post(lab, "src/app.py").exit, 0)
            self.assertEqual(len(lab.events("research_reminder")), 1)
            phases.set_level(lab.conn, lab.work, "L1", now=lab.now)
            plan(lab)
            start_agent(lab, "a1", 1)
            r = lab.pre_edit(lab.wt / "src/app.py", agent_id="a1")
            self.assertEqual(r.exit, 2)
            self.assertIn(REFUSAL, r.stderr)
        finally:
            lab.close()


class NotEnforcedTest(Base):
    approved = False

    def test_l1_without_note_warned_when_not_enforced(self):
        r = edit_and_post(self.lab, "src/app.py", agent_id="a1")
        self.assertEqual(r.exit, 0)
        self.assertIn(WARNING, r.stdout)
        self.assertIn("research submit 1", r.stdout)
        self.assertEqual(self.lab.events("research_reminder"), [{"task": 1}])
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertEqual(r.exit, 0)
        self.assertNotIn(WARNING, r.stdout)

    def test_reminder_again_after_plan_reset(self):
        edit_and_post(self.lab, "src/app.py", agent_id="a1")
        scope.reset_plan(self.lab.conn, self.lab.work, now=self.lab.now)
        plan(self.lab)
        start_agent(self.lab, "a2", 1)
        r = self.lab.pre_edit(self.app, agent_id="a2")
        self.assertIn(WARNING, r.stdout)

    def test_reminder_again_after_invalid_redelivery(self):
        """Decisione 14: una consegna non valida riporta il task a «avviso alla modifica
        successiva», anche se era già stato avvisato."""
        edit_and_post(self.lab, "src/app.py", agent_id="a1")
        self.assertNotIn(WARNING, self.lab.pre_edit(self.app, agent_id="a1").stdout)
        self.note(False, ["manca la sezione «Cosa ho trovato»"])
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertIn(WARNING, r.stdout)
        self.lab.post_edit(self.app, agent_id="a1")
        self.assertEqual(self.lab.events("research_reminder"), [{"task": 1}, {"task": 1}])
        self.assertNotIn(WARNING, self.lab.pre_edit(self.app, agent_id="a1").stdout)

    def test_reminder_of_other_task_not_reset_by_a_note(self):
        scope.reset_plan(self.lab.conn, self.lab.work, now=self.lab.now)
        plan(self.lab, numbers=(1, 2))
        start_agent(self.lab, "a1", 1)
        start_agent(self.lab, "a2", 2)
        edit_and_post(self.lab, "src/app.py", agent_id="a1")
        self.note(False, ["x"], task=2)
        self.assertNotIn(WARNING, self.lab.pre_edit(self.app, agent_id="a1").stdout)

    def test_reminder_per_task(self):
        scope.reset_plan(self.lab.conn, self.lab.work, now=self.lab.now)
        plan(self.lab, numbers=(1, 2))
        start_agent(self.lab, "a1", 1)
        start_agent(self.lab, "a2", 2)
        edit_and_post(self.lab, "src/app.py", agent_id="a1")
        self.assertIn(WARNING, self.lab.pre_edit(self.app, agent_id="a2").stdout)

    def test_reminder_not_consumed_by_other_deny(self):
        r = self.lab.pre_edit(self.lab.wt / "src/altro.py", agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertEqual(self.lab.events("research_reminder"), [])
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertIn(WARNING, r.stdout)
        self.assertEqual(self.lab.events("research_reminder"), [])
        self.lab.post_edit(self.app, agent_id="a1")
        self.assertEqual(self.lab.events("research_reminder"), [{"task": 1}])

    def test_failed_edit_does_not_consume_reminder(self):
        self.lab.pre_edit(self.app, agent_id="a1")
        self.lab.hook(sample(
            "PostToolUseFailure-Write", session_id=SESSION, cwd=str(self.lab.wt),
            agent_id="a1", agent_type=IMPL, tool_name="Write",
            tool_input={"file_path": str(self.app), "content": "x"}))
        self.assertEqual(self.lab.events("research_reminder"), [])

    def test_failed_bash_does_not_consume_reminder(self):
        self.lab.bash("sed -i s/a/b/ src/app.py", agent_id="a1")
        self.lab.bash("sed -i s/a/b/ src/app.py", post=True, agent_id="a1",
                      hook_event_name="PostToolUseFailure")
        self.assertEqual(self.lab.events("research_reminder"), [])

    def test_bash_write_warns_and_records(self):
        r = self.lab.bash("sed -i s/a/b/ src/app.py", agent_id="a1")
        self.assertEqual(r.exit, 0)
        self.assertIn(WARNING, r.stdout)
        self.lab.bash("sed -i s/a/b/ src/app.py", post=True, agent_id="a1")
        self.assertEqual(self.lab.events("research_reminder"), [{"task": 1}])


class L2Test(unittest.TestCase):
    """Un lavoro L2 in execution ha lo stesso blocco di L1 (decisione 3)."""

    def setUp(self):
        self.root = make_root(True)
        self.lab = Lab(level="L2", phase="execution", research=True, plugin_root=self.root)
        plan(self.lab)
        start_agent(self.lab, "a1", 1)
        self.app = self.lab.wt / "src/app.py"

    def tearDown(self):
        self.lab.close()
        shutil.rmtree(self.root, ignore_errors=True)

    def test_l2_without_note_denied(self):
        r = self.lab.pre_edit(self.app, agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn(REFUSAL + " 1", r.stderr)

    def test_l2_valid_note_passes(self):
        lookups.set_note(self.lab.conn, self.lab.work, 1, text="n", ok=True)
        self.assertEqual(self.lab.pre_edit(self.app, agent_id="a1").exit, 0)


class L0Test(Base):
    level = "L0"

    def test_l0_warns_once(self):
        r = edit_and_post(self.lab, "src/app.py")
        self.assertEqual(r.exit, 0)
        self.assertIn(WARNING, r.stdout)
        self.assertEqual(self.lab.events("research_reminder"), [{"task": None}])
        r = self.lab.pre_edit(self.app)
        self.assertEqual(r.exit, 0)
        self.assertNotIn(WARNING, r.stdout)

    def test_docs_exempt_in_l0(self):
        for rel in ("docs/superpowers/plans/x.md", ".tollgate-run/1/x", ".superpowers/x",
                    "reports/junit.xml"):
            with self.subTest(rel=rel):
                self.assertNotIn(WARNING, self.lab.pre_edit(self.lab.wt / rel).stdout)

    def test_l0_bash_not_gated(self):
        self.assertNotIn(WARNING, self.lab.bash("sed -i s/a/b/ src/app.py").stdout)


class ComponentOffTest(unittest.TestCase):
    def test_component_off(self):
        root = make_root(True)
        lab = Lab(research=True, plugin_root=root,
                  toml=DEFAULT_TOML + "[components]\nresearch_note = false\n")
        try:
            plan(lab)
            start_agent(lab, "a1", 1)
            r = lab.pre_edit(lab.wt / "src/app.py", agent_id="a1")
            self.assertEqual(r.exit, 0)
            self.assertNotIn("informati prima", r.stdout)
        finally:
            lab.close()
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
