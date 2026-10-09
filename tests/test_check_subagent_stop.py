import json
import tempfile
import unittest
from pathlib import Path

from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_analysis import profiles as prof
from tollgate_core import git as tg_git, phases, receipts, scope, subagents, tasks
from tollgate_core.config import load_config_text

IMPL = "tollgate:implementer"


def report(status="DONE", **extra):
    data = {"v": 1, "task": 1, "status": status, "done": "fatto", "tests": "verify green",
            "files": ["src/app.py"], "must_have": [], "concerns": "", "left": "",
            "size_reason": None}
    data.update(extra)
    return "Fine.\n```json\n" + json.dumps(data) + "\n```"


class Base(unittest.TestCase):
    toml = DEFAULT_TOML

    def setUp(self):
        self.lab = Lab(toml=self.toml)
        with_scope(self.lab, ("src/app.py", "tests/test_app.py", "src/big.py"))
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        self.start("a1", IMPL, task=1)

    def tearDown(self):
        self.lab.close()

    def start(self, aid, atype, task=None):
        subagents.start(self.lab.conn, agent_id=aid, type_=atype, session=SESSION,
                        work=self.lab.work, task=task, base_sha=tg_git.head(self.lab.wt),
                        fingerprint=tg_git.fingerprint(self.lab.wt, ["reports/", "coverage/"]),
                        now=self.lab.now)

    def stop(self, aid="a1", atype=IMPL, text=None, transcript=None):
        p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.lab.wt),
                   agent_id=aid, agent_type=atype, last_assistant_message=text,
                   agent_transcript_path=transcript or "/non/esiste.jsonl")
        if text is None:
            p.pop("last_assistant_message")
        return self.lab.hook(p)

    def commit(self, content="def somma(a, b):\n    return b + a\n", path="src/app.py"):
        (self.lab.wt / path).write_text(content)
        git(self.lab.wt, "add", "-A")
        git(self.lab.wt, "commit", "-qm", "lavoro")
        return git(self.lab.wt, "rev-parse", "HEAD")

    def green(self, sha, state="green"):
        receipts.add(self.lab.conn, work=self.lab.work, sha=sha, command="verify",
                     resolved_command="true", exit_code=0, tests_run=0 if state == "empty" else 2,
                     tests_skipped=0, duration=0.1, log=None, produced_by="verify", state=state,
                     now=self.lab.now)

    def task_state(self):
        return tasks.get_task(self.lab.conn, self.lab.work, 1)["state"]


class ReceiptGateTest(Base):
    def test_done_without_receipt_two_vetoes_then_needs_you(self):
        self.commit()
        self.assertEqual(self.stop(text=report()).exit, 2)
        self.assertEqual(self.stop(text=report()).exit, 2)
        r = self.stop(text=report())
        self.assertEqual(r.exit, 0)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")
        self.assertEqual(self.task_state(), "blocked")

    def test_done_with_green_receipt(self):
        self.green(self.commit())
        self.assertEqual(self.stop(text=report()).exit, 0)
        self.assertEqual(self.task_state(), "review")
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "done")

    def test_done_with_changes_but_no_commit(self):
        (self.lab.wt / "src/app.py").write_text("x = 3\n")
        r = self.stop(text=report())
        self.assertEqual(r.exit, 2)
        self.assertIn("committa", r.stderr)

    def test_done_without_changes_passes(self):
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_blocked_with_red_receipt_closes(self):
        self.green(self.commit(), state="red")
        self.assertEqual(self.stop(text=report("BLOCKED", concerns="manca un dato")).exit, 0)
        self.assertEqual(self.task_state(), "blocked")

    def test_needs_context_without_receipt_or_block(self):
        self.assertEqual(self.stop(text=report("NEEDS_CONTEXT")).exit, 2)

    def test_invalid_report(self):
        r = self.stop(text='{"status": "DONE"}')
        self.assertEqual(r.exit, 2)
        self.assertIn("non valido", r.stderr)

    def test_report_from_handback(self):
        self.green(self.commit())
        subagents.set_report(self.lab.conn, "a1", report())
        self.assertEqual(self.stop(text=None).exit, 0)

    def test_internal_and_unknown_ignored(self):
        self.assertEqual(self.stop(aid="mai-visto").exit, 0)
        self.assertEqual(self.stop(atype="").exit, 0)


class BudgetAndSizeTest(Base):
    def test_tokens_over_cap_block_even_with_green(self):
        self.green(self.commit())
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tr = Path(tmp.name) / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {
            "id": "m", "usage": {"input_tokens": 500000, "output_tokens": 1}}}) + "\n")
        self.assertEqual(self.stop(text=report(), transcript=str(tr)).exit, 0)
        self.assertEqual(self.task_state(), "blocked")
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "budget")

    def test_size_reason_required_over_max(self):
        sha = self.commit("".join(f"x{i} = {i}\n" for i in range(600)), path="src/big.py")
        self.green(sha)
        self.assertEqual(self.stop(text=report()).exit, 2)
        self.assertEqual(self.stop(text=report(size_reason="generato da uno schema")).exit, 0)


class AllowNoTestsTest(Base):
    toml = DEFAULT_TOML + "[project]\nallow_no_tests = true\n"

    def test_empty_receipt_counts(self):
        self.green(self.commit(), state="empty")
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReceiptGateOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nsubagent_receipt_gate = false\n"

    def test_done_without_receipt_passes(self):
        self.commit()
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReadonlyTest(Base):
    def test_tampering_reviewer(self):
        self.start("r1", "tollgate:task-reviewer")
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(aid="r1", atype="tollgate:task-reviewer", text="ok").exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "r1")["state"], "tampered")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")

    def test_clean_reviewer(self):
        self.start("r2", "tollgate:task-reviewer")
        self.stop(aid="r2", atype="tollgate:task-reviewer", text="ok")
        self.assertEqual(subagents.get(self.lab.conn, "r2")["state"], "done")


class ExtraTest(Base):
    def receipt(self, sha, command, state, exit_code=0):
        receipts.add(self.lab.conn, work=self.lab.work, sha=sha, command=command,
                     resolved_command="true", exit_code=exit_code,
                     tests_run=0 if state == "empty" else 2, tests_skipped=0, duration=0.1,
                     log=None, produced_by="verify", state=state, now=self.lab.now)

    def test_cut_row_is_not_rewritten(self):
        self.green(self.commit())
        subagents.finish(self.lab.conn, "a1", state="cut", now=self.lab.now)
        self.assertEqual(self.stop(text=report()).exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "cut")
        self.assertEqual(self.task_state(), "running")

    def test_closed_row_is_ignored_even_without_report(self):
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        self.assertEqual(self.stop(text="niente").exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["vetoes"], 0)

    def test_related_green_suffices_over_red_gate(self):
        sha = self.commit()
        self.receipt(sha, "verify", "red", 1)
        self.receipt(sha, "related", "green")
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_empty_related_does_not_weigh_on_green_gate(self):
        sha = self.commit()
        self.receipt(sha, "related", "empty")
        self.receipt(sha, "verify", "green")
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_red_related_alone_vetoes(self):
        self.receipt(self.commit(), "related", "red", 1)
        self.assertEqual(self.stop(text=report()).exit, 2)

    def test_unknown_status_is_invalid(self):
        r = self.stop(text=report("FATTO"))
        self.assertEqual(r.exit, 2)
        self.assertIn("status sconosciuto", r.stderr)

    def test_veto_counts_and_names_the_limit(self):
        self.commit()
        r = self.stop(text=report())
        self.assertIn("veto 1 di 2", r.stderr)
        self.stop(text=report())
        self.assertEqual(subagents.get(self.lab.conn, "a1")["vetoes"], 2)

    def test_done_with_concerns_needs_receipt(self):
        self.commit()
        self.assertEqual(self.stop(text=report("DONE_WITH_CONCERNS")).exit, 2)

    def test_required_skill_missing_vetoes(self):
        self.green(self.commit())
        self.lab.conn.execute("UPDATE tasks SET skills_required = ? WHERE work = ? AND number = 1",
                              (json.dumps(["superpowers:test-driven-development"]),
                               self.lab.work))
        self.lab.conn.commit()
        r = self.stop(text=report())
        self.assertEqual(r.exit, 2)
        self.assertIn("test-driven-development", r.stderr)
        tasks.add_skill_used(self.lab.conn, self.lab.work, 1, "test-driven-development")
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_report_blocked_opens_needs_you_without_receipt_gate_veto(self):
        self.lab.conn.execute("INSERT INTO blocks (work, type, reason, opened) "
                              "VALUES (?, 'test_spec_conflict', 'x', '2026-10-09T10:00:00Z')",
                              (self.lab.work,))
        self.lab.conn.commit()
        self.assertEqual(self.stop(text=report("BLOCKED", concerns="conflitto")).exit, 0)
        self.assertEqual(self.task_state(), "blocked")


class ReadonlyOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nreadonly_check = false\n"

    def test_tampering_ignored_when_component_off(self):
        self.start("r1", "tollgate:task-reviewer")
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.stop(aid="r1", atype="tollgate:task-reviewer", text="ok")
        self.assertEqual(subagents.get(self.lab.conn, "r1")["state"], "done")


class GateCompletenessTest(Base):
    toml = DEFAULT_TOML.replace('gate = ["verify"]', 'gate = ["verify", "lint"]\nlint = "true"')

    def rec(self, sha, command, state="green", exit_code=0):
        receipts.add(self.lab.conn, work=self.lab.work, sha=sha, command=command,
                     resolved_command="true", exit_code=exit_code, tests_run=2,
                     tests_skipped=0, duration=0.1, log=None, produced_by="verify", state=state,
                     now=self.lab.now)

    def test_partial_gate_vetoes(self):
        self.rec(self.commit(), "verify")
        self.assertEqual(self.stop(text=report()).exit, 2)

    def test_foreign_command_does_not_complete_the_gate(self):
        self.rec(self.commit(), "profile:x:test")
        self.assertEqual(self.stop(text=report()).exit, 2)

    def test_full_gate_passes(self):
        sha = self.commit()
        self.rec(sha, "verify")
        self.rec(sha, "lint")
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_related_green_still_suffices(self):
        self.rec(self.commit(), "related")
        self.assertEqual(self.stop(text=report()).exit, 0)


class ResumeTest(Base):
    def hook_start(self, aid, atype):
        return self.lab.hook(sample("SubagentStart-none", session_id=SESSION,
                                    cwd=str(self.lab.wt), agent_id=aid, agent_type=atype))

    def test_resumed_reviewer_is_not_tampered_by_others_commits(self):
        self.hook_start("r1", "tollgate:task-reviewer")
        self.commit("def somma(a, b):\n    return a + b + 0\n")
        self.hook_start("r1", "tollgate:task-reviewer")
        self.stop(aid="r1", atype="tollgate:task-reviewer", text="ok")
        self.assertEqual(subagents.get(self.lab.conn, "r1")["state"], "done")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "execution")

    def test_resume_keeps_base_sha(self):
        self.hook_start("r1", "tollgate:task-reviewer")
        base = subagents.get(self.lab.conn, "r1")["agent_base_sha"]
        self.commit()
        self.hook_start("r1", "tollgate:task-reviewer")
        self.assertEqual(subagents.get(self.lab.conn, "r1")["agent_base_sha"], base)

    def test_resume_resets_vetoes(self):
        self.commit()
        self.stop(text=report())
        self.assertEqual(subagents.get(self.lab.conn, "a1")["vetoes"], 1)
        self.hook_start("a1", IMPL)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["vetoes"], 0)


class WebProfileSkillTest(Base):
    """Criterio 38: la skill di un profilo arriva al task dal piano e blocca il DONE (6.3)."""
    toml = DEFAULT_TOML + '[profiles.web]\npaths = ["web/**"]\nskills = ["ui-ux-pro-max"]\n'

    def setUp(self):
        self.lab = Lab(toml=self.toml)
        self.lab.wt.joinpath("web").mkdir()
        skills = prof.task_skills(["web/app.ts"], load_config_text(self.toml).profiles)
        scope.register_plan(self.lab.conn, self.lab.ts.state, self.lab.work,
                            plan_path="docs/superpowers/plans/p.md", plan_sha="s",
                            scope_paths=["web/app.ts"], plan_tasks=[(1, skills)],
                            advance=False, now=self.lab.now)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        self.start("a1", IMPL, task=1)

    def test_done_without_profile_skill_vetoes(self):
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["skills_required"],
                         '["ui-ux-pro-max"]')
        self.green(self.commit(path="web/app.ts"))
        r = self.stop(text=report())
        self.assertEqual(r.exit, 2)
        self.assertIn("ui-ux-pro-max", r.stderr)
        tasks.add_skill_used(self.lab.conn, self.lab.work, 1, "ui-ux-pro-max")
        self.assertEqual(self.stop(text=report()).exit, 0)


if __name__ == "__main__":
    unittest.main()
