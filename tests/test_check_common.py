import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.flowkit import SESSION, SPEC as FLOW_SPEC, FlowLab
from tests.helpers import git
from tests.hookkit import T0, Lab
from tests.test_check_acts import expand
from tollgate_analysis import approvals
from tollgate_checks._common import budget_cut_records, locked_docs, orphan_tg, transcript_cost
from tollgate_core import phases, sessions
from tollgate_flow import actapply
from tollgate_hooks.context import ReadDb

SPEC = "docs/superpowers/specs/x.md"
PLAN = "docs/superpowers/plans/x.md"
APPROVAL = "docs/superpowers/reviews/7/spec-approval.md"


class LockedDocsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(level="L2", phase="spec_audit")
        self.lab.conn.execute("UPDATE work_items SET spec_path = ? WHERE id = ?",
                              (SPEC, self.lab.work))
        p = self.lab.wt / APPROVAL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(approvals.render_approval({"kind": "spec-approval", "path": SPEC,
                                                "sha": "abc", "slices": 1}))

    def tearDown(self):
        self.lab.close()

    def row(self):
        return phases.get_work(self.lab.conn, self.lab.work)

    def test_spec_locked_after_approval_in_later_phase(self):
        self.lab.goto("plan")
        self.assertIn(SPEC, locked_docs(self.row()))

    def test_spec_unlocked_in_spec_phase_with_approval_file(self):
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_spec_unlocked_after_reopen_spec_keeps_history_file(self):
        self.lab.goto("plan")
        phases.set_phase(self.lab.conn, self.lab.ts.state, self.lab.work, "spec_audit",
                         "reopen_spec", now=T0)
        self.assertTrue((self.lab.wt / APPROVAL).is_file())
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_blocked_uses_phase_before_block(self):
        self.lab.goto("plan")
        self.lab.conn.execute("UPDATE work_items SET phase = 'blocked', "
                              "phase_before_block = 'spec_audit' WHERE id = ?", (self.lab.work,))
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_plan_locked_after_registration_in_execution(self):
        lab = Lab(level="L1", phase="execution")
        try:
            lab.conn.execute("UPDATE work_items SET plan_path = ?, plan_sha = 'abc' "
                             "WHERE id = ?", (PLAN, lab.work))
            self.assertIn(PLAN, locked_docs(phases.get_work(lab.conn, lab.work)))
        finally:
            lab.close()

    def test_plan_unlocked_after_reopen_plan(self):
        lab = Lab(level="L1", phase="execution")
        try:
            lab.conn.execute("UPDATE work_items SET plan_path = ?, plan_sha = 'abc' "
                             "WHERE id = ?", (PLAN, lab.work))
            phases.set_phase(lab.conn, lab.ts.state, lab.work, "plan", "reopen_plan", now=T0)
            self.assertNotIn(PLAN, locked_docs(phases.get_work(lab.conn, lab.work)))
        finally:
            lab.close()

    def test_spec_locked_by_approval_of_another_issue(self):
        (self.lab.wt / APPROVAL).unlink()
        other = self.lab.wt / "docs/superpowers/reviews/3/spec-approval.md"
        other.parent.mkdir(parents=True)
        other.write_text(approvals.render_approval({"kind": "spec-approval", "path": SPEC,
                                                    "sha": "abc"}))
        self.lab.goto("plan")
        self.assertIn(SPEC, locked_docs(self.row()))

    def test_spec_not_locked_by_invalid_or_foreign_approval(self):
        (self.lab.wt / APPROVAL).write_text("approvata\n")
        other = self.lab.wt / "docs/superpowers/reviews/3/spec-approval.md"
        other.parent.mkdir(parents=True)
        other.write_text(approvals.render_approval({"kind": "spec-approval",
                                                    "path": "docs/superpowers/specs/y.md",
                                                    "sha": "abc"}))
        self.lab.goto("plan")
        self.assertNotIn(SPEC, locked_docs(self.row()))

    def test_spec_locked_by_real_approve_spec(self):
        fl = FlowLab(issue=7, level="L2", phase="spec_audit")
        self.addCleanup(fl.close)
        fl.write_spec()
        phases.set_spec_path(fl.conn, fl.work, FLOW_SPEC, now=fl.now)
        fl.closed_round("spec-adversarial", {})
        self.assertEqual(fl.pre_edit(fl.wt / FLOW_SPEC).exit, 0)        # ancora in spec_audit
        self.assertEqual(expand(fl.lab, "tollgate:approve", "spec 1", session=SESSION).exit, 0)
        now = fl.now
        sessions.note_cli_call(fl.ts.state, SESSION, str(fl.wt), ["act"], now=now)
        actapply.apply_act(fl.ts.state, fl.wt, None, now=now)
        self.assertEqual(phases.get_work(fl.conn, fl.work)["phase"], "plan")
        r = fl.pre_edit(fl.wt / FLOW_SPEC)
        self.assertEqual(r.exit, 2)
        self.assertIn("bloccato", r.stderr)
        r = fl.pre_edit(fl.wt / approvals.approval_paths(7)[0])
        self.assertEqual(r.exit, 2)


class OrphanTgTest(unittest.TestCase):
    def test_no_origin_means_no_repo_key_and_no_orphan(self):
        lab = Lab(work=False)
        try:
            git(lab.wt, "remote", "remove", "origin")
            ctx = SimpleNamespace(db=ReadDb(lab.conn))
            self.assertIsNone(orphan_tg(ctx, lab.wt))
        finally:
            lab.close()


class TranscriptCostTest(unittest.TestCase):
    def event(self, lines=None, *, path=None):
        """Un evento con una trascrizione finta (le righe date) o con il percorso dato."""
        if lines is not None:
            tmp = tempfile.TemporaryDirectory(prefix="tollgate-")
            self.addCleanup(tmp.cleanup)
            path = Path(tmp.name) / "t.jsonl"
            path.write_text("\n".join(lines) + "\n")
        return SimpleNamespace(raw={"agent_transcript_path": str(path)})

    def test_missing_file_has_no_usage(self):
        self.assertEqual(transcript_cost(self.event(path="/non/esiste.jsonl")), (0, None))
        self.assertEqual(transcript_cost(SimpleNamespace(raw={})), (0, None))

    def test_unreadable_path_has_no_usage(self):
        tmp = tempfile.TemporaryDirectory(prefix="tollgate-")
        self.addCleanup(tmp.cleanup)
        self.assertEqual(transcript_cost(self.event(path=tmp.name)), (0, None))

    def test_transcript_without_usage_rows_has_no_usage(self):
        ev = self.event(["riga non json", json.dumps({"type": "user", "message": {"content": "x"}})])
        self.assertEqual(transcript_cost(ev), (0, None))

    def test_usage_and_tokens_from_one_reading(self):
        row = {"type": "assistant", "message": {"id": "m1", "model": "claude-sonnet-5-5", "usage": {
            "input_tokens": 10, "cache_creation_input_tokens": 5,
            "cache_read_input_tokens": 1000, "output_tokens": 3}}}
        tokens, usage = transcript_cost(self.event([json.dumps(row)]))
        self.assertEqual(tokens, 18)
        self.assertEqual(usage, {"claude-sonnet-5-5": {"input": 10, "cache_creation": 5,
                                                        "cache_read": 1000, "output": 3}})


class BudgetCutCostTest(unittest.TestCase):
    def test_budget_cut_has_no_cost(self):
        lab = Lab()
        try:
            from tollgate_core import subagents
            subagents.start(lab.conn, agent_id="a1", type_="tollgate:implementer",
                            session=SESSION, work=lab.work, task=None, base_sha="b0",
                            fingerprint="f0", now=T0)
            ctx = SimpleNamespace(db=ReadDb(lab.conn), component=lambda name: False)
            out = budget_cut_records(ctx, "a1", 1234)
            [fin] = [d for d in out if d.op == "subagent_finish"]
            self.assertEqual((fin.data["state"], fin.data["tokens"]), ("cut", 1234))
            self.assertIsNone(fin.data.get("usage"))
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
