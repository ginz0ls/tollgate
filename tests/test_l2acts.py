import json
import unittest
from unittest import mock

import tests.test_audit_prepare as tap
from tests.flowkit import PLAN, SESSION, SPEC, FlowLab, plan_text, spec_text
from tests.test_finishcheck import TOML as FINISH_TOML
from tests.test_actapply import ApplyCase
from tollgate_analysis import approvals, brief as briefs
from tollgate_core import audits, config, phases, scope, subagents, tasks, violations
from tollgate_flow import actapply, audit, l2acts

ADV, LENS, PLAN_ADV = "spec-adversarial", "spec-lens", "plan-adversarial"
MAJOR = {"major": 1}
CLEAN: dict = {}
SPEC_APPROVAL, PLAN_APPROVAL = approvals.approval_paths(7)


class L2Case(tap.AuditCase, ApplyCase):
    """Banco L2 con gli atti dell'utente: l'atto si registra come digitato (hook
    `UserPromptExpansion`) e si applica dalla libreria con l'ora del banco (D20); `audit prepare`
    passa dalla CLI quando il test attraversa i comandi."""

    def cli_prepare(self, *extra):
        return self.fl.cli("audit", "prepare", *extra, cwd=self.fl.wt)

    def approve(self, what: str):
        self.act("tollgate:approve", what)
        return self.apply()

    def refused(self, what: str) -> str:
        with self.assertRaises(actapply.ActApplyError) as cm:
            self.approve(what)
        return str(cm.exception)

    def header(self, rel):
        return approvals.parse_approval((self.fl.wt / rel).read_text())

    def phase(self):
        return self.work()["phase"]

    def causes(self):
        return [e["cause"] for e in self.fl.events("phase_change")]

    def spec_round(self, counts=CLEAN):
        """Un giro avversariale aperto da `audit prepare` e chiuso dal report dell'agente."""
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.fl.report_round(counts=counts).returncode, 0)

    def open_blocks(self):
        return [(r["id"], r["reason"]) for r in self.fl.conn.execute(
            "SELECT id, reason FROM blocks WHERE work = ? AND closed IS NULL ORDER BY id",
            (self.fl.work,))]

    def resolve(self, block_id):
        self.act("tollgate:resolve", f"{block_id} deciso")
        return self.apply()

    def to_four_dirty_rounds(self):
        """Quattro giri avversariali con `major` (il tetto): il quarto apre il blocco."""
        fl = self.lab()
        fl.write_spec()
        for n in range(4):
            if n:
                fl.write_spec(note=f"correzione {n}")
            self.spec_round(MAJOR)
        return fl

    def commit_file(self, rel):
        self.fl.git("add", "--", rel, repo=self.fl.wt)
        self.fl.git("commit", "-q", "-m", f"approvazione {rel}", repo=self.fl.wt)

    def to_approval(self, **lab_kw):
        """Spec approvata e committata, piano scritto, giro dell'avversario pulito, fase
        `approval` (con `plan_adversary` spento `audit prepare` avanza da solo)."""
        fl = self.lab(**lab_kw)
        fl.write_spec()
        self.spec_round()
        self.approve("spec 1")
        self.commit_file(SPEC_APPROVAL)
        self.assertEqual(self.phase(), "plan")
        fl.write_l2_plan()
        if "plan_adversary" not in lab_kw.get("toml", ""):
            self.assertEqual(self.prepare().code, audit.OK)
            self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.phase(), "approval")
        return fl


class ApproveSpecTest(L2Case):
    def test_refused_after_dirty_round_accepted_after_clean(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round(MAJOR)
        msg = self.refused("spec 1")
        self.assertIn("blocker o major", msg)
        tap.assert_program_before_prepare(self, msg)
        self.assertEqual(self.phase(), "spec_audit")
        fl.write_spec(note="corretta")
        self.spec_round(CLEAN)
        msg = self.approve("spec 1")
        self.assertIn("spec approvata", msg)
        self.assertEqual(self.header(SPEC_APPROVAL)["adversarial"], "closed")

    def test_cap_resolve_suspended_then_approve(self):
        fl = self.to_four_dirty_rounds()
        (block, reason), = self.open_blocks()
        self.assertEqual(reason, audits.cap_reason(ADV, 4))
        self.assertEqual(self.phase(), "blocked")
        r = self.cli_prepare()
        self.assertEqual(r.returncode, audit.REFUSED, r.stdout)
        self.assertIn("bloccato", r.stdout)
        self.assertIn("/tollgate:resolve", self.refused("spec 1"))
        self.assertIn("avversariale sospeso", self.resolve(block))
        self.assertEqual(self.phase(), "spec_audit")
        self.assertEqual(audits.suspended(fl.conn, fl.work), {ADV: 4})
        r = self.cli_prepare()
        self.assertEqual(r.returncode, audit.OK, r.stdout)
        self.assertTrue(r.stdout.strip().splitlines()[-1].startswith(
            "prossimo passo: " + tap.fixed("approve_spec")), r.stdout)
        self.assertEqual(len(self.rows()), 4)
        self.approve("spec 1")
        self.assertEqual(self.header(SPEC_APPROVAL)["adversarial"], "suspended")

    def test_suspended_round_then_dirty_round_reblocks(self):
        fl = self.to_four_dirty_rounds()
        self.resolve(self.open_blocks()[0][0])
        fl.write_spec(note="ancora")
        self.spec_round(MAJOR)                          # il quinto, sopra il tetto
        (block, reason), = self.open_blocks()
        self.assertEqual(reason, audits.cap_reason(ADV, 5))
        self.assertEqual(self.phase(), "blocked")
        self.assertIn("/tollgate:resolve", self.refused("spec 1"))
        self.assertIn("avversariale sospeso", self.resolve(block))
        self.assertEqual(audits.suspended(fl.conn, fl.work), {ADV: 5})
        self.approve("spec 1")
        self.assertEqual(self.phase(), "plan")

    def test_wrong_slice_count_refused(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        self.spec_round()
        self.assertIn("la spec prevede 3 fette: /tollgate:approve spec 3", self.refused("spec 1"))
        self.assertIn("la spec prevede 3 fette: /tollgate:approve spec 3", self.refused("spec 2"))
        self.assertEqual(self.phase(), "spec_audit")

    def test_three_slices_refused_until_lens_closed_or_suspended(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        self.spec_round()
        self.assertIn("lenti", self.refused("spec 3"))
        self.lens_closed()
        self.approve("spec 3")
        head = self.header(SPEC_APPROVAL)
        self.assertEqual((head["lens"], head["slices"]), ("closed", 3))

    def test_three_slices_lens_suspended_accepted(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        self.spec_round()
        fl.closed_round(LENS, MAJOR, viewpoint="executor")
        audits.suspend(fl.conn, fl.work, LENS, 1, now=fl.lab.now)
        self.approve("spec 3")
        self.assertEqual(self.header(SPEC_APPROVAL)["lens"], "suspended")

    def test_spec_changed_after_last_round_refused(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round()
        fl.write_spec(note="cambiata dopo il giro")
        self.assertIn("cambiata", self.refused("spec 1"))
        self.assertEqual(self.phase(), "spec_audit")

    def test_reopen_without_changes_then_approve_again(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round()
        self.approve("spec 1")
        first = self.header(SPEC_APPROVAL)
        fl.write_l2_plan()
        fl.closed_round(PLAN_ADV, MAJOR)                # i giri del piano non contano
        phases.set_phase(fl.conn, fl.ts.state, fl.work, "spec_audit", "reopen_spec",
                         now=fl.lab.now)
        self.approve("spec 1")
        again = self.header(SPEC_APPROVAL)
        self.assertEqual(again["sha"], first["sha"])
        self.assertNotEqual(again["act_id"], first["act_id"])
        self.assertEqual(self.phase(), "plan")

    def test_open_round_refuses_approve(self):
        self.lab().write_spec()
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertIn("ancora aperto", self.refused("spec 1"))
        self.assertFalse((self.fl.wt / SPEC_APPROVAL).exists())

    def test_adversary_off_lens_closed_then_spec_changed_refused(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec(slices=3)
        self.assertEqual(self.prepare().code, audit.NEEDS_CONFIRM)      # registra la spec
        self.lens_closed()
        fl.write_spec(slices=3, note="corretta dopo l'ultimo ciclo")
        self.assertIn("cambiata", self.refused("spec 3"))
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        self.assertEqual([x.agent_type for x in r.launches], [tap.LENS])
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.approve("spec 3")
        head = self.header(SPEC_APPROVAL)
        self.assertEqual((head["adversarial"], head["lens"]), ("off", "closed"))

    def test_adversary_off_lens_suspended_then_spec_changed(self):
        toml = self.off("spec_adversary") + "[spec_audit]\nspec_audit_cycles = 2\n"
        fl = self.lab(toml=toml)
        fl.write_spec(slices=3)
        self.assertEqual(self.prepare().code, audit.NEEDS_CONFIRM)      # registra la spec
        fl.closed_round(LENS, MAJOR, viewpoint="executor")
        fl.closed_round(LENS, MAJOR, viewpoint="user")
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you",
                                  audits.cap_reason(LENS, 2), now=fl.lab.now)
        self.assertIn("audit a lenti sospeso", self.resolve(block))
        fl.write_spec(slices=3, note="corretta")
        self.assertIn("cambiata", self.refused("spec 3"))
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.open_blocks(), [])
        self.assertEqual(self.phase(), "spec_audit")
        self.approve("spec 3")
        self.assertEqual(self.header(SPEC_APPROVAL)["lens"], "suspended")

    def test_decline_resolve_then_approve(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        self.spec_round()
        r = self.cli_prepare()
        self.assertEqual(r.returncode, audit.NEEDS_CONFIRM, r.stdout)
        r = fl.cli("audit", "decline", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (block, reason), = self.open_blocks()
        self.assertEqual(reason, audits.DECLINE_REASON)
        self.assertIn("audit a lenti sospeso", self.resolve(block))
        self.assertIn(LENS, audits.suspended(fl.conn, fl.work))
        self.assertEqual(audits.suspended(fl.conn, fl.work)[LENS], 0)
        r = self.cli_prepare()
        self.assertEqual(r.returncode, audit.OK, r.stdout)
        self.assertTrue(r.stdout.strip().splitlines()[-1].startswith(
            "prossimo passo: " + tap.fixed("approve_spec")), r.stdout)
        self.approve("spec 3")
        self.assertEqual(self.header(SPEC_APPROVAL)["lens"], "suspended")

    def test_spec_audit_off_three_slices_accepted(self):
        fl = self.lab(toml=self.off("spec_audit"))
        fl.write_spec(slices=3)
        self.spec_round()
        self.approve("spec 3")
        self.assertEqual(self.header(SPEC_APPROVAL)["lens"], "off")

    def test_spec_adversary_off_accepted_without_rounds(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec()
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.rows(), [])
        self.approve("spec 1")
        head = self.header(SPEC_APPROVAL)
        self.assertEqual((head["adversarial"], head["lens"]), ("off", None))

    def test_writes_file_and_moves_to_plan(self):
        fl = self.lab()
        blob = fl.write_spec()
        self.spec_round()
        act_id = self.act("tollgate:approve", "spec 1")
        self.apply()
        head = self.header(SPEC_APPROVAL)
        self.assertEqual((head["kind"], head["path"], head["sha"], head["slices"],
                          head["act_id"]), ("spec-approval", SPEC, blob, 1, act_id))
        self.assertEqual(self.phase(), "plan")
        self.assertEqual(self.causes()[-1], "approve_spec")
        self.assertEqual(self.state_of(act_id), "consumed")

    def test_three_slices_propose_issues_and_start_spec(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        self.spec_round()
        self.lens_closed()
        msg = self.approve("spec 3")
        self.assertIn("fetta 2/3 di 2026-10-20-prova.md: Fetta 2", msg)
        self.assertIn("fetta 3/3 di 2026-10-20-prova.md: Fetta 3", msg)
        self.assertNotIn("fetta 1/3", msg)
        self.assertIn("/tollgate:start #", msg)
        self.assertIn(f'--spec "{SPEC}"', msg)
        self.assertIn(briefs.DATA_NOTE, msg)
        self.assertIn("/tollgate:approve effect", msg)
        self.assertIn(f"Committa {SPEC_APPROVAL}", msg)
        self.assertEqual(fl.gh_calls(), [])

    def test_untrusted_slice_titles_stay_in_a_longer_fence(self):
        fl = self.lab()
        hostile = "``````` $(rm -rf ~) `x`"
        fl.commit(SPEC, spec_text(2).replace("2. Fetta 2", f"2. {hostile}"), "spec")
        self.spec_round()
        self.lens_closed()
        msg = self.approve("spec 2")
        lines = msg.splitlines()
        i = next(n for n, x in enumerate(lines) if hostile in x)
        fence = lines[i - 1]
        self.assertTrue(set(fence) == {"`"} and len(fence) > 7, fence)
        self.assertEqual(lines[i + 3], fence)
        self.assertEqual(fl.gh_calls(), [])

    def test_blocked_refused_pointing_to_resolve(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round()
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "serve una scelta",
                                  now=fl.lab.now)
        msg = self.refused("spec 1")
        self.assertIn(f"/tollgate:resolve {block}", msg)
        self.assertFalse((fl.wt / SPEC_APPROVAL).exists())

    def test_uncommitted_spec_refused(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round()
        (fl.wt / SPEC).write_text(spec_text(1, note="non committata"))
        self.assertIn(f"committa {SPEC}", self.refused("spec 1"))
        self.assertEqual(self.phase(), "spec_audit")

    def test_wrong_phase_refused(self):
        self.lab("plan").write_spec()
        self.assertIn("spec_audit", self.refused("spec 1"))


class ApprovePlanTest(L2Case):
    def test_plan_sha_is_the_approved_version(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round()
        self.approve("spec 1")
        self.commit_file(SPEC_APPROVAL)
        first = fl.write_l2_plan()
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=MAJOR).returncode, 0)
        blob = fl.write_l2_plan(tasks=2)                  # il piano corretto
        self.assertNotEqual(blob, first)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.phase(), "approval")
        self.assertIsNone(self.work()["plan_sha"])
        self.approve("plan")
        work = self.work()
        self.assertEqual((work["plan_sha"], work["plan_path"], work["phase"]),
                         (blob, PLAN, "execution"))
        self.assertEqual(scope.paths(fl.conn, fl.work), {"src/app.py", "tests/test_app.py",
                                                         "docs/uso.md"})
        self.assertEqual([r["state"] for r in fl.conn.execute(
            "SELECT state FROM tasks WHERE work = ? ORDER BY number", (fl.work,))],
            ["pending", "pending"])
        head = self.header(PLAN_APPROVAL)
        self.assertEqual((head["kind"], head["path"], head["sha"], head["spec_sha"],
                          head["adversarial"]),
                         ("plan-approval", PLAN, blob, self.header(SPEC_APPROVAL)["sha"],
                          "closed"))
        self.assertEqual(self.causes()[-1], "approve_plan")

    def test_refused_outside_approval(self):
        fl = self.lab("plan")
        fl.write_spec()
        fl.approve_spec_file()
        fl.write_l2_plan()
        self.assertIn("approval", self.refused("plan"))
        self.assertIsNone(self.work()["plan_sha"])

    def test_refused_when_spec_changed_after_approval(self):
        fl = self.to_approval()
        fl.write_spec(note="cambiata dopo approve spec")
        self.assertIn("spec cambiata dopo approve spec", self.refused("plan"))
        self.assertEqual(self.phase(), "approval")
        self.assertIsNone(self.work()["plan_sha"])

    def test_spec_approval_on_disk_but_not_in_head_refused(self):
        fl = self.lab()
        fl.write_spec()
        self.spec_round()
        self.approve("spec 1")                  # scritta ma non committata
        fl.write_l2_plan()
        phases.set_phase(fl.conn, fl.ts.state, fl.work, "approval", "audit_clean",
                         now=fl.lab.now)
        self.assertEqual(self.refused("plan"), f"committa {SPEC_APPROVAL} prima di approve plan")

    def test_refused_when_last_plan_round_on_other_spec_sha(self):
        fl = self.to_approval()
        fl.write_spec(note="spec corretta")
        fl.approve_spec_file()                  # approvazione sul nuovo sha della spec
        self.assertIn("cambiati dopo l'ultimo giro", self.refused("plan"))
        self.assertIsNone(self.work()["plan_sha"])

    def test_plan_adversary_off(self):
        fl = self.to_approval(toml=self.off("plan_adversary"))
        self.assertEqual(self.rows(PLAN_ADV), [])
        self.approve("plan")
        self.assertEqual(self.header(PLAN_APPROVAL)["adversarial"], "off")
        self.assertEqual(self.phase(), "execution")

    def test_blocked_refused_pointing_to_resolve(self):
        fl = self.to_approval()
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "serve una scelta",
                                  now=fl.lab.now)
        self.assertIn(f"/tollgate:resolve {block}", self.refused("plan"))
        self.assertIsNone(self.work()["plan_sha"])

    def test_later_slice_approval_with_current_sha_wins_over_stale_lower_issue(self):
        fl = self.lab("plan")
        blob = fl.write_spec()
        phases.set_spec_path(fl.conn, fl.work, SPEC, now=fl.lab.now)
        for issue, sha in ((3, "0" * 40), (5, blob)):
            fields = {"kind": "spec-approval", "path": SPEC, "sha": sha, "slices": 3}
            fl.commit(approvals.approval_paths(issue)[0], approvals.render_approval(fields),
                      f"approvazione {issue}")
        fl.write_l2_plan()
        fl.closed_round(PLAN_ADV, CLEAN)
        phases.set_phase(fl.conn, fl.ts.state, fl.work, "approval", "audit_clean",
                         now=fl.lab.now)
        self.approve("plan")
        self.assertEqual(self.phase(), "execution")

    def test_dirty_plan_round_refused(self):
        fl = self.to_approval()
        fl.closed_round(PLAN_ADV, MAJOR)
        msg = self.refused("plan")
        self.assertIn("blocker o major", msg)
        tap.assert_program_before_prepare(self, msg)

    def test_plan_changed_after_last_round_points_to_reopen_plan(self):
        fl = self.to_approval()
        fl.commit(PLAN, plan_text(tasks=2), "piano cambiato fuori dai guardrail")
        msg = self.refused("plan")
        self.assertIn("cambiati dopo l'ultimo giro", msg)
        self.assertIn("/tollgate:reopen plan", msg)
        tap.assert_program_before_prepare(self, msg)

    def test_later_slice_prepare_and_approve_plan_agree(self):
        fl = self.lab("plan")
        blob = fl.write_spec()
        phases.set_spec_path(fl.conn, fl.work, SPEC, now=fl.lab.now)
        for issue, sha in ((3, "0" * 40), (5, blob)):
            fields = {"kind": "spec-approval", "path": SPEC, "sha": sha, "slices": 3}
            fl.commit(approvals.approval_paths(issue)[0], approvals.render_approval(fields),
                      f"approvazione {issue}")
        fl.write_l2_plan()
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.phase(), "approval")
        self.approve("plan")
        self.assertEqual(self.phase(), "execution")

    def test_open_round_refused(self):
        fl = self.to_approval()
        audits.open_round(fl.conn, fl.work, kind=PLAN_ADV, sha="0" * 40, spec_sha="0" * 40,
                          viewpoint=None, code="aaaa0000", now=fl.lab.now)
        self.assertIn("ancora aperto", self.refused("plan"))

    def test_repeat_after_interruption_does_not_register_twice(self):
        fl = self.to_approval()
        with mock.patch.object(l2acts.phases, "set_phase",
                               side_effect=phases.TransitionError("interrotto")):
            self.assertIn("interrotto", self.refused("plan"))
        self.assertEqual(self.phase(), "approval")
        registered = self.work()["plan_sha"]
        self.assertIsNotNone(registered)
        self.approve("plan")
        self.assertEqual(self.phase(), "execution")
        self.assertEqual(self.work()["plan_sha"], registered)
        self.assertEqual(len(fl.events("scope_registered")), 1)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM tasks WHERE work = ?",
                                         (fl.work,)).fetchone()[0], 1)

    def test_plan_approval_committable_in_execution(self):
        fl = self.to_approval()
        self.approve("plan")
        self.assertEqual(self.phase(), "execution")
        self.assertEqual(fl.bash(f"git add {PLAN_APPROVAL}").exit, 0)
        fl.git("add", "--", PLAN_APPROVAL, repo=fl.wt)
        r = fl.bash("git commit -m 'approvazione del piano'")
        self.assertEqual(r.exit, 0, r.stderr)
        fl.git("commit", "-q", "-m", "approvazione del piano", repo=fl.wt)
        (fl.wt / "src").mkdir(exist_ok=True)
        (fl.wt / "src" / "app.py").write_text("def somma(a, b):\n    return a + b\n")
        fl.git("add", "--", "src/app.py", repo=fl.wt)
        r = fl.bash("git commit -m 'somma'", agent_id="a-impl-1")
        self.assertEqual(r.exit, 0, r.stderr)

    def test_plan_checked_again_at_approval(self):
        fl = self.to_approval()
        fl.commit(PLAN, "# Piano senza sezioni\n", "piano rovinato")
        self.assertIn("plan-check", self.refused("plan"))
        self.assertIsNone(self.work()["plan_sha"])


class ReopenTest(L2Case):
    def reopen(self, what: str, reason: str = "il motivo"):
        self.act("tollgate:reopen", f"{what} {reason}".strip())
        return self.apply()

    def refused_reopen(self, what: str, reason: str = "il motivo") -> str:
        with self.assertRaises(actapply.ActApplyError) as cm:
            self.reopen(what, reason)
        return str(cm.exception)

    def to_execution(self, **lab_kw):
        fl = self.to_approval(**lab_kw)
        self.approve("plan")
        self.commit_file(PLAN_APPROVAL)
        self.assertEqual(self.phase(), "execution")
        return fl

    def locked(self):
        return violations.locked_docs(self.work())

    def test_reopen_spec_from_plan_unlocks_and_requires_new_approval(self):
        fl = self.to_approval()
        self.assertIn(SPEC, self.locked())
        msg = self.reopen("spec", "manca un caso")
        self.assertIn("spec_audit", msg)
        self.assertIn("audit prepare", msg)
        self.assertNotIn("si registra da solo", msg)
        self.assertEqual((self.phase(), self.causes()[-1]), ("spec_audit", "reopen_spec"))
        self.assertNotIn(SPEC, self.locked())
        self.assertEqual(fl.pre_edit(fl.wt / SPEC).exit, 0)
        self.assertIn("vale in fase approval", self.refused("plan"))
        self.assertTrue((fl.wt / SPEC_APPROVAL).is_file())          # lo storico resta

    def test_reopen_spec_from_execution_resets_plan_and_supersedes_open_round(self):
        fl = self.to_execution()
        self.assertTrue(scope.paths(fl.conn, fl.work))
        audits.open_round(fl.conn, fl.work, kind=PLAN_ADV, sha="0" * 40, spec_sha="0" * 40,
                          viewpoint=None, code="aaaa0000", now=fl.lab.now)
        self.reopen("spec")
        work = self.work()
        self.assertEqual((work["phase"], work["plan_sha"], work["plan_path"]),
                         ("spec_audit", None, PLAN))
        self.assertEqual(scope.paths(fl.conn, fl.work), set())
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM tasks WHERE work = ?",
                                         (fl.work,)).fetchone()[0], 0)
        self.assertEqual(len(fl.events("plan_reset")), 1)
        self.assertIsNone(audits.open_round_row(fl.conn, fl.work))
        last = fl.conn.execute("SELECT outcome FROM spec_audit WHERE work = ? AND kind = ? "
                               "ORDER BY id DESC", (fl.work, PLAN_ADV)).fetchone()
        self.assertEqual(last["outcome"], "superseded")

    def test_reopen_keeps_audit_suspensions(self):
        fl = self.to_execution()
        audits.suspend(fl.conn, fl.work, ADV, 4, now=fl.lab.now)
        audits.suspend(fl.conn, fl.work, LENS, 0, now=fl.lab.now)
        before = audits.suspended(fl.conn, fl.work)
        self.reopen("plan")
        self.assertEqual(audits.suspended(fl.conn, fl.work), before)
        fl.conn.execute("UPDATE work_items SET phase = 'approval' WHERE id = ?", (fl.work,))
        self.reopen("spec")
        self.assertEqual(audits.suspended(fl.conn, fl.work), before)
        self.assertEqual(before, {ADV: 4, LENS: 0})

    def test_reopen_loads_config_only_for_a_running_subagent(self):
        fl = self.to_execution()
        bad = mock.patch.object(l2acts.audit, "work_config",
                                side_effect=config.ConfigError("rotta"))
        with bad:
            self.reopen("plan")                          # nessun subagente: la config non serve
        self.assertEqual(self.phase(), "plan")
        fl.conn.execute("UPDATE work_items SET phase = 'approval' WHERE id = ?", (fl.work,))
        subagents.start(fl.conn, agent_id="a-w", type_="tollgate:implementer", session=SESSION,
                        work=fl.work, task=None, base_sha=None, fingerprint=None, now=fl.lab.now)
        with bad:
            self.assertIn("configurazione non valida", self.refused_reopen("spec"))
        self.assertEqual(self.phase(), "approval")

    def test_reopen_needs_reason(self):
        self.to_approval()
        for args in ("spec", "spec   "):
            self.act("tollgate:reopen", args)
            with self.assertRaises(actapply.ActApplyError) as cm:
                self.apply()
            self.assertIn("motivo", str(cm.exception))
        self.assertEqual(self.phase(), "approval")

    def test_reopen_refused_with_running_task_or_writer(self):
        fl = self.to_execution()
        self.assertEqual(fl.cli("task", "start", "1", cwd=fl.wt).returncode, 0)
        for kind in ("spec", "plan"):
            self.assertIn("task 1 è in corso", self.refused_reopen(kind))
        self.assertEqual(self.phase(), "execution")
        self.assertIsNotNone(self.work()["plan_sha"])
        fl.conn.execute("UPDATE tasks SET state = 'pending' WHERE work = ?", (fl.work,))
        tasks.add_commit(fl.conn, fl.work, 1, "a" * 40)              # pending, ma con un commit
        self.assertIn("task 1 è in corso o ha commit non chiusi", self.refused_reopen("plan"))
        fl.conn.execute("UPDATE tasks SET commits = '[]' WHERE work = ?", (fl.work,))
        subagents.start(fl.conn, agent_id="a-w", type_="tollgate:implementer", session=SESSION,
                        work=fl.work, task=None, base_sha=None, fingerprint=None, now=fl.lab.now)
        self.assertIn("/tollgate:resolve writer", self.refused_reopen("spec"))
        subagents.finish(fl.conn, "a-w", state="done", now=fl.lab.now)
        self.reopen("plan")
        self.assertEqual(self.phase(), "plan")

    def test_reopen_refused_in_other_phases_levels_and_blocked(self):
        fl = self.lab()
        self.assertIn("reopen spec vale in fase", self.refused_reopen("spec"))
        self.assertIn("reopen plan vale in fase", self.refused_reopen("plan"))
        fl = self.to_approval()
        self.reopen("plan")                                          # approval -> plan
        self.assertEqual(self.phase(), "plan")
        self.assertIn("reopen plan vale in fase", self.refused_reopen("plan"))
        fl.conn.execute("UPDATE work_items SET phase = 'approval' WHERE id = ?", (fl.work,))
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "serve",
                                  now=fl.lab.now)
        self.assertIn(f"/tollgate:resolve {block}", self.refused_reopen("spec"))

    def test_reopen_spec_refused_in_l1_and_reopen_plan_in_l0(self):
        fl = self.make(phase="plan")
        fl.register_plan()
        self.assertIn("solo in L2", self.refused_reopen("spec"))
        self.assertEqual(self.phase(), "execution")
        fl.conn.execute("UPDATE work_items SET level = 'L0' WHERE id = ?", (fl.work,))
        self.assertIn("L0", self.refused_reopen("plan"))
        self.assertEqual(self.phase(), "execution")

    def test_reopen_plan_l1_from_execution(self):
        fl = self.make(phase="plan")
        fl.register_plan(tasks=1)
        first = self.work()["plan_sha"]
        self.assertTrue(scope.paths(fl.conn, fl.work))
        msg = self.reopen("plan", "serve una pagina")
        self.assertIn("si registra da solo", msg)
        self.assertNotIn("audit prepare", msg)
        work = self.work()
        self.assertEqual((work["phase"], work["plan_sha"], work["plan_path"]),
                         ("plan", None, PLAN))
        self.assertEqual((scope.paths(fl.conn, fl.work), self.causes()[-1]),
                         (set(), "reopen_plan"))
        self.assertEqual(self.fl.pre_edit(fl.wt / PLAN).exit, 0)
        (fl.wt / PLAN).write_text(plan_text(tasks=2))
        self.assertEqual(fl.post_edit(fl.wt / PLAN).exit, 0)        # il piano corretto si registra
        work = self.work()
        self.assertEqual(work["phase"], "execution")
        self.assertNotEqual(work["plan_sha"], first)
        self.assertIn("docs/uso.md", scope.paths(fl.conn, fl.work))

    def test_reopen_spec_then_new_approval_end_to_end(self):
        fl = self.lab(toml=FINISH_TOML)
        fl.write_spec()
        self.spec_round()
        self.approve("spec 1")
        first = self.header(SPEC_APPROVAL)["sha"]
        self.commit_file(SPEC_APPROVAL)
        self.assertEqual(self.phase(), "plan")
        self.assertEqual(fl.pre_edit(fl.wt / SPEC).exit, 2)         # bloccata dopo l'approvazione
        self.reopen("spec", "la spec dimentica un caso")
        self.assertEqual(self.phase(), "spec_audit")
        self.assertEqual(fl.pre_edit(fl.wt / SPEC).exit, 0)
        blob = fl.write_spec(note="corretta")
        self.spec_round()
        self.approve("spec 1")
        header = self.header(SPEC_APPROVAL)
        self.assertEqual(header["sha"], blob)
        self.assertNotEqual(header["sha"], first)
        self.assertEqual(self.phase(), "plan")
        self.assertEqual(fl.pre_edit(fl.wt / SPEC).exit, 2)         # di nuovo bloccata
        fl.git("add", "--", "docs/superpowers/reviews/7", repo=fl.wt)
        fl.git("commit", "-q", "-m", "approvazione e report", repo=fl.wt)
        fl.write_l2_plan()
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.phase(), "approval")
        self.approve("plan")
        fl.git("add", "--", "docs/superpowers/reviews/7", repo=fl.wt)
        fl.git("commit", "-q", "-m", "approvazione del piano e report", repo=fl.wt)
        fl.commit("tests/ids.txt", "tests.test_app::test_somma ok\ntests.test_app::test_zero ok\n",
                  "ids")
        fl.commit("src/app.py", "def somma(a, b):\n    return b + a\n", "somma")
        fl.close_tasks()
        r = fl.cli("finish", "check", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("out_of_scope", r.stdout)
        self.assertNotIn("[no]", r.stdout)
        self.assertEqual(self.phase(), "review")

    def test_reopen_plan_then_reapprove_registers_new_scope(self):
        fl = self.to_execution()
        first = self.work()["plan_sha"]
        self.assertEqual(scope.paths(fl.conn, fl.work), {"src/app.py", "tests/test_app.py"})
        msg = self.reopen("plan", "serve la pagina")
        self.assertIn("audit prepare", msg)
        self.assertIn("avversario del piano", msg)
        self.assertNotIn("si registra da solo", msg)
        self.assertEqual((self.phase(), self.work()["plan_sha"]), ("plan", None))
        self.assertEqual(scope.paths(fl.conn, fl.work), set())
        self.assertEqual(fl.pre_edit(fl.wt / PLAN).exit, 0)
        blob = fl.write_l2_plan(tasks=2)
        self.assertNotEqual(blob, first)
        self.assertIsNone(self.work()["plan_sha"])                  # in L2 post_edit non registra
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.phase(), "approval")
        self.approve("plan")
        work = self.work()
        self.assertEqual((work["phase"], work["plan_sha"]), ("execution", blob))
        self.assertEqual(scope.paths(fl.conn, fl.work),
                         {"src/app.py", "tests/test_app.py", "docs/uso.md"})
        self.assertEqual([r["state"] for r in fl.conn.execute(
            "SELECT state FROM tasks WHERE work = ? ORDER BY number", (fl.work,))],
            ["pending", "pending"])
        self.assertEqual(self.header(PLAN_APPROVAL)["sha"], blob)
        self.commit_file(PLAN_APPROVAL)
        r = fl.cli("task", "start", "1", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = fl.cli("task", "start", "2", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("docs/uso.md", (fl.wt / ".tollgate-run" / "7" / "task-2.md").read_text())


class SuspendOnResolveTest(L2Case):
    def test_block_opened_by_hand_without_rounds_is_not_suspended(self):
        fl = self.lab()
        for reason in (audits.cap_reason(ADV, 4), audits.cap_reason(PLAN_ADV, 2),
                       audits.cap_reason(LENS, 30)):
            block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", reason,
                                      now=fl.lab.now)
            msg = self.resolve(block)
            self.assertNotIn("sospeso", msg)
            self.assertEqual(audits.suspended(fl.conn, fl.work), {})
            self.assertEqual(self.phase(), "spec_audit")

    def test_resolve_without_worktree_falls_back_to_default_caps(self):
        fl = self.lab()
        fl.write_spec()
        for _ in range(4):
            fl.closed_round(ADV, MAJOR)
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you",
                                  audits.cap_reason(ADV, 4), now=fl.lab.now)
        fl.conn.execute("UPDATE work_items SET worktree = NULL WHERE id = ?", (fl.work,))
        act = {"target": str(block)}
        msg = actapply._resolve(fl.conn, fl.ts.state, self.work(), act, [str(block), "ok"],
                                fl.now, SESSION)
        self.assertIn("avversariale sospeso", msg)

    def test_below_the_cap_not_suspended(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round(ADV, MAJOR)
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you",
                                  audits.cap_reason(ADV, 1), now=fl.lab.now)
        self.assertNotIn("sospeso", self.resolve(block))
        self.assertEqual(audits.suspended(fl.conn, fl.work), {})

    def test_clean_last_round_not_suspended(self):
        fl = self.lab()
        fl.write_spec()
        for counts in (MAJOR, MAJOR, MAJOR, CLEAN):
            fl.closed_round(ADV, counts)
        self.assertIsNone(l2acts.suspend_on_resolve(
            fl.conn, fl.work, audits.cap_reason(ADV, 4), now=fl.lab.now))
        self.assertEqual(audits.suspended(fl.conn, fl.work), {})

    def test_other_reason_gives_none(self):
        fl = self.lab()
        self.assertIsNone(l2acts.suspend_on_resolve(fl.conn, fl.work, "altro motivo",
                                                    now=fl.lab.now))

    def test_idempotent_when_repeated(self):
        fl = self.lab()
        fl.write_spec()
        for _ in range(4):
            fl.closed_round(ADV, MAJOR)
        reason = audits.cap_reason(ADV, 4)
        for _ in range(2):
            self.assertEqual(l2acts.suspend_on_resolve(fl.conn, fl.work, reason,
                                                       now=fl.lab.now),
                             "avversariale sospeso")
        self.assertEqual(audits.suspended(fl.conn, fl.work), {ADV: 4})

    def test_plan_cap_uses_configured_threshold(self):
        fl = self.lab("plan")
        fl.write_spec()
        fl.approve_spec_file()
        fl.write_l2_plan()
        fl.closed_round(PLAN_ADV, MAJOR)
        cfg = config.load_config_text(
            "schema_version = 1\n[gate]\nmode = \"protected\"\n[spec_audit]\nplan_rounds = 1\n")
        label = l2acts.suspend_on_resolve(fl.conn, fl.work, audits.cap_reason(PLAN_ADV, 1),
                                          now=fl.lab.now, cfg=cfg)
        self.assertEqual(label, "avversario del piano sospeso")
        self.assertEqual(audits.suspended(fl.conn, fl.work), {PLAN_ADV: 1})


class PickMessageTest(ApplyCase):
    def test_no_act_message_lists_spec_plan_and_reopen(self):
        self.make(level="L2", phase="spec_audit")
        with self.assertRaises(actapply.ActApplyError) as cm:
            self.apply()
        for word in ("spec", "plan", "reopen"):
            self.assertIn(word, str(cm.exception))


if __name__ == "__main__":
    unittest.main()
