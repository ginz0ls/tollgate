import unittest
from unittest import mock

from tests.flowkit import PLAN, SPEC, ZERO_COUNTS, FlowLab, plan_text
from tests.hookkit import DEFAULT_TOML
from tollgate_analysis import approvals, auditrules
from tollgate_core import audits, git as core_git, phases
from tollgate_flow import audit

ADV = "tollgate:spec-adversary"
LENS = "tollgate:spec-auditor"
PLAN_ADV = "tollgate:plan-adversary"
MAJOR = {"major": 1}
CLEAN: dict = {}


def fixed(key: str) -> str:
    """La parte fissa del passo, prima del primo segnaposto."""
    return audit.STEPS[key].split("<")[0]


class AuditCase(unittest.TestCase):
    def lab(self, phase="spec_audit", toml=DEFAULT_TOML, level="L2"):
        fl = FlowLab(issue=7, level=level, phase=phase, toml=toml)
        self.addCleanup(fl.close)
        self.fl = fl
        return fl

    def off(self, *names):
        return DEFAULT_TOML + "[components]\n" + "".join(f"{n} = false\n" for n in names)

    def prepare(self, confirm=False):
        return audit.prepare(self.fl.ts.state, self.fl.wt, confirm=confirm, now=self.fl.lab.now)

    def text(self, r):
        return "\n".join(r.lines)

    def work(self):
        return phases.get_work(self.fl.conn, self.fl.work)

    def rows(self, kind=None):
        sql, args = "SELECT * FROM spec_audit WHERE work = ?", [self.fl.work]
        if kind:
            sql, args = sql + " AND kind = ?", args + [kind]
        return self.fl.conn.execute(sql + " ORDER BY id", args).fetchall()

    def run_dir(self):
        return self.fl.wt / ".tollgate-run" / "7"

    def lens_closed(self):
        for vp in auditrules.VIEWPOINTS:
            for _ in range(2):
                self.fl.closed_round("spec-lens", CLEAN, viewpoint=vp)

    def plan_lab(self, **kw):
        fl = self.lab("plan", **kw)
        fl.write_spec()
        fl.approve_spec_file()
        return fl


class SpecRoundsTest(AuditCase):
    def test_no_spec_refused(self):
        self.lab()
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("nessuna spec", self.text(r))
        self.assertTrue(r.lines[-1].startswith("prossimo passo: " + fixed("write_spec")))
        self.assertEqual(self.rows(), [])

    def test_first_round_registers_spec_path_and_launches_adversary(self):
        fl = self.lab()
        blob = fl.write_spec()
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        self.assertEqual(self.work()["spec_path"], SPEC)
        row, = self.rows()
        self.assertEqual((row["kind"], row["number"], row["stage"], row["sha"], row["spec_sha"]),
                         ("spec-adversarial", 1, "open", blob, blob))
        self.assertEqual([x.agent_type for x in r.launches], [ADV])
        brief = self.run_dir() / "spec-adversarial-1.md"
        self.assertEqual(r.launches[0].brief, brief)
        launch_lines = [x for x in r.lines if x.startswith("agente: ")]
        self.assertEqual(launch_lines, [f'agente: {ADV} brief: "{brief}"'])
        self.assertIn(" ", str(brief))
        text = brief.read_text()
        self.assertIn(row["code"], text)
        self.assertIn(blob, text)
        self.assertTrue(r.lines[-1].startswith("prossimo passo: " + fixed("launch")))
        self.assertNotIn("<programma>", r.lines[-1])

    def test_uncommitted_spec_refused(self):
        fl = self.lab()
        fl.write_spec()
        (fl.wt / SPEC).write_text("modificata\n")
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(f"committa {SPEC}", self.text(r))
        self.assertEqual(self.rows(), [])

    def test_open_round_same_sha_reprinted_same_code(self):
        self.lab().write_spec()
        first = self.prepare()
        again = self.prepare()
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(first.launches[0].brief, again.launches[0].brief)
        code = self.rows()[0]["code"]
        self.assertIn(code, again.launches[0].brief.read_text())
        self.assertIn("già aperto", self.text(again))

    def test_open_round_other_sha_superseded(self):
        fl = self.lab()
        fl.write_spec()
        self.prepare()
        blob = fl.write_spec(note="cambiata")
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        first, second = self.rows()
        self.assertEqual((first["outcome"], first["stage"]), ("superseded", "closed"))
        self.assertEqual((second["number"], second["stage"], second["sha"]), (2, "open", blob))

    def test_dirty_round_same_sha_asks_fix(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round("spec-adversarial", MAJOR)
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertTrue(r.lines[-1].startswith("prossimo passo: " + fixed("fix_spec")))
        self.assertEqual(len(self.rows()), 1)

    def test_fix_spec_refusal_supersedes_open_round_on_other_sha(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round("spec-adversarial", MAJOR)
        audits.open_round(fl.conn, fl.work, kind="spec-lens", sha="0" * 40,
                          spec_sha="0" * 40, viewpoint="executor", code="aaaa0000",
                          now=fl.lab.now)
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(fixed("fix_spec"), r.lines[-1])
        self.assertIsNone(audits.open_round_row(fl.conn, fl.work))
        self.assertEqual(self.rows("spec-lens")[0]["outcome"], "superseded")

    def test_open_round_value_error_is_an_audit_error(self):
        self.lab().write_spec()
        with mock.patch.object(audit.audits, "open_round", side_effect=ValueError("già aperto")):
            with self.assertRaisesRegex(audit.AuditError, "già aperto"):
                self.prepare()

    def test_dirty_round_other_sha_opens_new_round(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round("spec-adversarial", MAJOR)
        fl.write_spec(note="corretta")
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        self.assertEqual([x.agent_type for x in r.launches], [ADV])
        self.assertEqual(self.rows()[-1]["number"], 2)

    def test_clean_round_one_slice_asks_approve_spec(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round("spec-adversarial", CLEAN)
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertEqual(r.lines[-1], "prossimo passo: " + audit.STEPS["approve_spec"]
                         .replace("<fette>", "1"))

    def test_three_slices_lens_needs_confirm_then_executor(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.NEEDS_CONFIRM, []))
        self.assertIn("conferma: audit a lenti: da 16 a 30 cicli di tollgate:spec-auditor",
                      self.text(r))
        self.assertEqual(len(self.rows("spec-lens")), 0)
        r = self.prepare(confirm=True)
        self.assertEqual(r.code, audit.OK)
        self.assertEqual([x.agent_type for x in r.launches], [LENS])
        row = self.rows("spec-lens")[0]
        self.assertEqual((row["viewpoint"], row["number"]), ("executor", 1))
        text = r.launches[0].brief.read_text()
        self.assertIn("executor", text)
        self.assertIn("dimensioni.md", text)

    def test_lens_viewpoints_rotate(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        fl.closed_round("spec-lens", CLEAN, viewpoint="executor")
        r = self.prepare()
        self.assertEqual(self.rows("spec-lens")[-1]["viewpoint"], "user")
        self.assertEqual(r.code, audit.OK)

    def test_lens_closed_then_confirmation_round_if_spec_changed(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        self.lens_closed()
        self.assertIn("approve spec", self.text(self.prepare()))
        fl.write_spec(slices=3, note="corretta dalle lenti")
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [ADV])
        self.assertEqual(self.rows("spec-adversarial")[-1]["number"], 2)

    def test_adversarial_confirmation_after_lens_closed(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        self.lens_closed()
        fl.write_spec(slices=3, note="corretta")
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [ADV])
        audits.close_round(fl.conn, fl.work, kind="spec-adversarial", number=2,
                           counts=ZERO_COUNTS, outcome="empty", report_path="r.md",
                           now=fl.lab.now)
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertIn(fixed("approve_spec"), r.lines[-1])

    def test_lens_corrections_do_not_trigger_adversarial_until_lens_closed(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        fl.closed_round("spec-lens", {"moderate": 2}, viewpoint="executor")
        fl.write_spec(slices=3, note="corretta")
        r = self.prepare(confirm=False)       # le lenti sono già cominciate: niente conferma
        self.assertEqual(r.code, audit.OK)
        self.assertEqual([x.agent_type for x in r.launches], [LENS])
        self.assertEqual(self.rows("spec-lens")[-1]["viewpoint"], "user")
        self.assertEqual(len(self.rows("spec-adversarial")), 1)

    def test_lens_findings_on_same_sha_ask_fix(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        fl.closed_round("spec-lens", {"moderate": 1}, viewpoint="executor")
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(fixed("fix_spec"), r.lines[-1])

    def test_lens_empty_cycle_on_same_sha_goes_on(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        fl.closed_round("spec-lens", CLEAN, viewpoint="executor")
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [LENS])

    def test_suspended_adversarial_goes_to_approve_with_one_slice(self):
        fl = self.lab()
        fl.write_spec()
        n = fl.closed_round("spec-adversarial", MAJOR)
        audits.suspend(fl.conn, fl.work, "spec-adversarial", n, now=fl.lab.now)
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertIn(fixed("approve_spec"), r.lines[-1])

    def test_suspended_adversarial_goes_to_lens_with_three_slices(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        n = fl.closed_round("spec-adversarial", MAJOR)
        audits.suspend(fl.conn, fl.work, "spec-adversarial", n, now=fl.lab.now)
        self.assertEqual(self.prepare().code, audit.NEEDS_CONFIRM)
        r = self.prepare(confirm=True)
        self.assertEqual([x.agent_type for x in r.launches], [LENS])

    def test_suspension_of_an_older_round_does_not_count(self):
        fl = self.lab()
        fl.write_spec()
        n = fl.closed_round("spec-adversarial", MAJOR)
        audits.suspend(fl.conn, fl.work, "spec-adversarial", n, now=fl.lab.now)
        fl.write_spec(note="altro")
        fl.closed_round("spec-adversarial", MAJOR)
        self.assertEqual(self.prepare().code, audit.REFUSED)

    def test_adversary_off_three_slices_reaches_lens(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec(slices=3)
        self.assertEqual(self.prepare().code, audit.NEEDS_CONFIRM)
        r = self.prepare(confirm=True)
        self.assertEqual([x.agent_type for x in r.launches], [LENS])

    def test_lens_confirmation_cycle_with_adversary_off(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec(slices=3)
        self.lens_closed()
        self.assertEqual(self.prepare().launches, [])
        fl.write_spec(slices=3, note="corretta")
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [LENS])
        row = self.rows("spec-lens")[-1]
        self.assertEqual((row["number"], row["viewpoint"]), (17, "executor"))

    def test_superseded_first_lens_cycle_does_not_ask_confirm_again(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        self.prepare(confirm=True)
        fl.write_spec(slices=3, note="cambiata")
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        first, second = self.rows("spec-lens")
        self.assertEqual(first["outcome"], "superseded")
        self.assertEqual((second["number"], second["stage"]), (2, "open"))

    def test_open_round_of_disabled_component_is_superseded(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec()
        audits.open_round(fl.conn, fl.work, kind="spec-adversarial", sha=fl._blob(SPEC),
                          spec_sha=fl._blob(SPEC), viewpoint=None, code="aaaa0000",
                          now=fl.lab.now)
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertEqual(self.rows()[0]["outcome"], "superseded")

    def test_components_off_one_slice_goes_to_approve(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec()
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertIn(fixed("approve_spec"), r.lines[-1])
        self.assertEqual(self.rows(), [])

    def test_lens_off_three_slices_needs_only_adversary(self):
        fl = self.lab(toml=self.off("spec_audit"))
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        r = self.prepare()
        self.assertIn(fixed("approve_spec"), r.lines[-1])
        self.assertIn("3", r.lines[-1])

    def test_models_override_in_launch_line(self):
        fl = self.lab(toml=DEFAULT_TOML + '[review]\nmodels = {"tollgate:spec-adversary" = "opus"}\n')
        fl.write_spec()
        r = self.prepare()
        self.assertEqual(r.launches[0].model, "opus")
        self.assertTrue(any(x.startswith("agente: ") and x.endswith(" model: opus")
                            for x in r.lines))

    def test_quote_in_spec_path_refused(self):
        fl = self.lab()
        fl.commit('docs/superpowers/specs/a"b.md', "x\n", "spec")
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("virgolette", self.text(r))
        self.assertEqual(self.rows(), [])


class DeclineTest(AuditCase):
    def test_decline_opens_block(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        code, lines = audit.decline(fl.ts.state, fl.wt, now=fl.lab.now)
        self.assertEqual(code, audit.OK)
        self.assertEqual(self.work()["phase"], "blocked")
        block = fl.conn.execute("SELECT * FROM blocks WHERE work = ?", (fl.work,)).fetchone()
        self.assertEqual((block["type"], block["reason"]),
                         ("needs_you", audits.DECLINE_REASON))
        self.assertIn(f"/tollgate:resolve {block['id']} ", lines[-1])
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(fixed("resolve") + str(block["id"]), r.lines[-1])

    def test_decline_refused_with_one_slice_lens_off_or_started(self):
        fl = self.lab()
        fl.write_spec()
        self.assertEqual(audit.decline(fl.ts.state, fl.wt)[0], audit.REFUSED)
        fl.write_spec(slices=3)
        fl.closed_round("spec-lens", CLEAN, viewpoint="executor")
        self.assertEqual(audit.decline(fl.ts.state, fl.wt)[0], audit.REFUSED)
        self.assertEqual(self.work()["phase"], "spec_audit")

    def test_decline_refused_when_lens_off(self):
        fl = self.lab(toml=self.off("spec_audit"))
        fl.write_spec(slices=3)
        self.assertEqual(audit.decline(fl.ts.state, fl.wt)[0], audit.REFUSED)

    def test_decline_refused_outside_spec_audit(self):
        self.plan_lab()
        self.assertEqual(audit.decline(self.fl.ts.state, self.fl.wt)[0], audit.REFUSED)


class PlanRoundsTest(AuditCase):
    def test_plan_written_by_bash_is_found(self):
        fl = self.plan_lab()
        fl.commit(PLAN, plan_text(tasks=1), "piano da bash")
        self.assertIsNone(self.work()["plan_path"])
        r = self.prepare()
        self.assertEqual(r.code, audit.OK)
        self.assertEqual(self.work()["plan_path"], PLAN)
        self.assertEqual([x.agent_type for x in r.launches], [PLAN_ADV])
        row, = self.rows()
        self.assertEqual((row["kind"], row["sha"], row["spec_sha"]),
                         ("plan-adversarial", fl._blob(PLAN), fl._blob(SPEC)))
        text = r.launches[0].brief.read_text()
        self.assertIn(fl._blob(PLAN), text)
        self.assertIn("Task 1", text)
        self.assertIn(f'"plan_sha": "{fl._blob(PLAN)}"', text)

    def test_plan_registered_by_hook_launches(self):
        fl = self.plan_lab()
        fl.write_l2_plan(tasks=2)
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [PLAN_ADV])
        self.assertIn("Task 2", r.launches[0].brief.read_text())

    def test_no_plan_refused(self):
        self.plan_lab()
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(fixed("write_plan"), r.lines[-1])

    def test_uncommitted_plan_refused(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        (fl.wt / PLAN).write_text(plan_text(tasks=2))
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(f"committa {PLAN}", self.text(r))

    def test_invalid_plan_refused(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.commit(PLAN, "## Obiettivo\nx\n", "piano guasto")
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("plan-check", self.text(r))

    def test_spec_approval_only_on_disk_refused(self):
        fl = self.lab("plan")
        fl.write_spec()
        path = fl.wt / approvals.approval_paths(7)[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(approvals.render_approval(
            {"kind": "spec-approval", "path": SPEC, "sha": fl._blob(SPEC)}))
        phases.set_spec_path(fl.conn, fl.work, SPEC, now=fl.lab.now)
        fl.write_l2_plan()
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("committa docs/superpowers/reviews/7/spec-approval.md prima del giro "
                      "del piano", self.text(r))
        self.assertEqual(self.rows(), [])

    def test_spec_changed_after_approval_refused(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.write_spec(note="dopo l'approvazione")
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("/tollgate:reopen spec", self.text(r))

    def test_dirty_plan_round_asks_fix_and_changed_plan_reopens(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.closed_round("plan-adversarial", MAJOR)
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(fixed("fix_plan"), r.lines[-1])
        fl.commit(PLAN, plan_text(tasks=2), "piano corretto")
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [PLAN_ADV])
        self.assertEqual(self.rows("plan-adversarial")[-1]["number"], 2)

    def test_plan_round_then_clean_moves_to_approval(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.closed_round("plan-adversarial", CLEAN)
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertEqual(self.work()["phase"], "approval")
        self.assertIn(fixed("approve_plan"), r.lines[-1])
        change = fl.events("phase_change")[-1]
        self.assertEqual((change["from"], change["to"], change["cause"]),
                         ("plan", "approval", "audit_clean"))

    def test_clean_round_on_old_spec_or_plan_does_not_count(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.closed_round("plan-adversarial", CLEAN, sha="0" * 40)
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [PLAN_ADV])
        self.assertEqual(self.work()["phase"], "plan")

    def test_suspended_plan_round_moves_to_approval(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        n = fl.closed_round("plan-adversarial", MAJOR)
        audits.suspend(fl.conn, fl.work, "plan-adversarial", n, now=fl.lab.now)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.work()["phase"], "approval")

    def test_components_off(self):
        fl = self.lab(toml=self.off("spec_adversary", "plan_adversary"))
        fl.write_spec()
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertIn(fixed("approve_spec"), r.lines[-1])
        fl.approve_spec_file()
        fl.goto("plan")
        fl.write_l2_plan()
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertEqual(self.work()["phase"], "approval")
        self.assertEqual(self.rows(), [])

    def test_plan_adversary_off_goes_straight_to_approval(self):
        fl = self.plan_lab(toml=self.off("plan_adversary"))
        fl.write_l2_plan()
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertEqual(self.work()["phase"], "approval")
        self.assertEqual(self.rows(), [])

    def test_plan_adversary_off_supersedes_open_plan_round(self):
        fl = self.plan_lab(toml=self.off("plan_adversary"))
        fl.write_l2_plan()
        audits.open_round(fl.conn, fl.work, kind="plan-adversarial", sha=fl._blob(PLAN),
                          spec_sha=fl._blob(SPEC), viewpoint=None, code="aaaa0000",
                          now=fl.lab.now)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.work()["phase"], "approval")
        self.assertIsNone(audits.open_round_row(fl.conn, fl.work))
        self.assertEqual(self.rows()[0]["outcome"], "superseded")

    def test_fix_plan_refusal_supersedes_stale_open_round(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.closed_round("plan-adversarial", MAJOR)
        audits.open_round(fl.conn, fl.work, kind="plan-adversarial", sha="0" * 40,
                          spec_sha=fl._blob(SPEC), viewpoint=None, code="aaaa0000",
                          now=fl.lab.now)
        self.assertEqual(self.prepare().code, audit.REFUSED)
        self.assertIsNone(audits.open_round_row(fl.conn, fl.work))

    def test_approval_phase_prints_approve_plan(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        fl.goto("approval")
        r = self.prepare()
        self.assertEqual((r.code, r.launches), (audit.OK, []))
        self.assertIn(fixed("approve_plan"), r.lines[-1])

    def test_split_candidate_in_plan_brief(self):
        toml = DEFAULT_TOML + ('[profiles.web]\npaths = ["src/**"]\nagent = "x:implementer-web"\n'
                               '[profiles.docs]\npaths = ["docs/**"]\nagent = "x:implementer-docs"\n')
        fl = self.plan_lab(toml=toml)
        fl.write_l2_plan(tasks=2)
        text = fl.wt.joinpath(PLAN).read_text()
        fl.commit(PLAN, text.replace("- Test: `tests/test_app.py`",
                                     "- Modify: `docs/uso.md`\n- Test: `tests/test_app.py`"),
                  "task a cavallo")
        r = self.prepare()
        self.assertIn("candidato a essere diviso", r.launches[0].brief.read_text().split(
            "## Cosa controllare")[1].split("## Rilievi")[0].split("- Task 1")[1])


class RefusalsTest(AuditCase):
    def test_l1_refused(self):
        fl = self.lab(phase="plan", level="L1")
        fl.write_spec()
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("L1", self.text(r))

    def test_other_phase_refused(self):
        fl = self.plan_lab()
        fl.goto("execution")
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn("execution", self.text(r))

    def test_blocked_refused_with_block_id(self):
        fl = self.lab()
        fl.write_spec()
        block = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "x", now=fl.lab.now)
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED)
        self.assertIn(f"/tollgate:resolve {block} ", r.lines[-1])

    def test_no_work_is_an_error(self):
        fl = self.lab()
        with self.assertRaises(audit.AuditError):
            audit.prepare(fl.ts.state, fl.tmp, confirm=False)

    def test_steps_have_fixed_part_without_placeholder(self):
        self.assertEqual(set(audit.STEPS), {"launch", "fix_spec", "fix_plan", "approve_spec",
                                            "approve_plan", "write_spec", "write_plan",
                                            "resolve"})
        for key, text in audit.STEPS.items():
            self.assertNotIn("tollgate audit", text)
            self.assertTrue(fixed(key).strip(), key)


class PeekTest(AuditCase):
    def test_peek_without_writes(self):
        fl = self.lab()
        fl.write_spec()
        before = fl.conn.execute("SELECT count(*) FROM spec_audit").fetchone()[0]
        step = audit.peek(fl.conn, self.work())
        self.assertIn("audit prepare", step)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM spec_audit").fetchone()[0], before)
        self.assertIsNone(self.work()["spec_path"])

    def test_peek_approve_and_refusals(self):
        fl = self.lab()
        self.assertIn(fixed("write_spec"), audit.peek(fl.conn, self.work()))
        fl.write_spec()
        fl.closed_round("spec-adversarial", CLEAN)
        self.assertIn(fixed("approve_spec"), audit.peek(fl.conn, self.work()))

    def test_peek_never_raises(self):
        fl = self.lab()
        fl.conn.execute("UPDATE work_items SET worktree = ? WHERE id = ?",
                        (str(fl.tmp / "assente"), fl.work))
        fl.conn.commit()
        self.assertIn("audit prepare", audit.peek(fl.conn, self.work()))


class NonUtf8Test(AuditCase):
    """Spec e piano non UTF-8 committati: `peek` non solleva mai (decisione 20) e `prepare` dà un
    rifiuto (`AuditError`), mai un traceback."""

    def commit_bytes(self, fl, path, data: bytes):
        target = fl.wt / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        fl.git("add", "--", path, repo=fl.wt)
        fl.git("commit", "-qm", "non utf-8", repo=fl.wt)

    def test_committed_non_utf8_spec_is_read_with_latin1_fallback(self):
        fl = self.lab()
        self.commit_bytes(fl, SPEC, "# Spec\n\ncaffè «niente»\n".encode("latin-1"))
        self.assertIn("audit prepare", audit.peek(fl.conn, self.work()))
        r = self.prepare()
        self.assertEqual(r.code, audit.OK, self.text(r))
        self.assertEqual([x.agent_type for x in r.launches], [ADV])
        self.assertEqual(self.work()["spec_path"], SPEC)

    def test_committed_non_utf8_plan_is_a_refusal(self):
        fl = self.plan_lab()
        self.commit_bytes(fl, PLAN, plan_text().encode("utf-8") + "\ncaffè\n".encode("latin-1"))
        self.assertIn("audit prepare", audit.peek(fl.conn, self.work()))
        r = self.prepare()
        self.assertEqual(r.code, audit.REFUSED, self.text(r))
        self.assertIn("rifiuto: nessun piano valido nel ramo", self.text(r))
        self.assertEqual(r.launches, [])

    def test_undecodable_read_is_fallback_for_peek_and_refusal_for_prepare(self):
        fl = self.lab()
        fl.write_spec()
        boom = UnicodeDecodeError("utf-8", b"\xe8", 0, 1, "invalid continuation byte")
        with mock.patch.object(core_git, "text_at", side_effect=boom):
            self.assertIn("audit prepare", audit.peek(fl.conn, self.work()))
            with self.assertRaisesRegex(audit.AuditError, "utf-8"):
                self.prepare()
        self.assertEqual(self.rows(), [])
        self.assertIsNone(self.work()["spec_path"])


class AdversarialOkTest(AuditCase):
    def cfg(self):
        from tollgate_core import config
        return config.load_config_at(core_git.main_worktree(self.fl.wt), self.work()["work_base_sha"])

    def test_ok_conditions(self):
        fl = self.lab()
        blob = fl.write_spec()
        self.assertFalse(audit.adversarial_ok(fl.conn, self.work(), self.cfg(), blob))
        n = fl.closed_round("spec-adversarial", MAJOR)
        self.assertFalse(audit.adversarial_ok(fl.conn, self.work(), self.cfg(), blob))
        audits.suspend(fl.conn, fl.work, "spec-adversarial", n, now=fl.lab.now)
        self.assertTrue(audit.adversarial_ok(fl.conn, self.work(), self.cfg(), blob))
        self.assertFalse(audit.adversarial_ok(fl.conn, self.work(), self.cfg(), "altro"))

    def test_clean_and_off(self):
        fl = self.lab()
        blob = fl.write_spec()
        fl.closed_round("spec-adversarial", CLEAN)
        self.assertTrue(audit.adversarial_ok(fl.conn, self.work(), self.cfg(), blob))
        fl.close()
        fl = self.lab(toml=self.off("spec_adversary"))
        self.assertTrue(audit.adversarial_ok(fl.conn, self.work(), self.cfg(), None))


class CliTest(AuditCase):
    def test_cli_prepare_decline_and_refusal_exit_codes(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        fl.closed_round("spec-adversarial", CLEAN)
        r = fl.cli("audit", "prepare", cwd=fl.wt)
        self.assertEqual((r.returncode, "conferma:" in r.stdout), (3, True), r.stderr)
        r = fl.cli("audit", "prepare", "--confirm", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("agente: tollgate:spec-auditor brief:", r.stdout)
        r = fl.cli("audit", "decline", cwd=fl.wt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("rifiuto:", r.stdout)

    def test_cli_without_work_exits_1_with_message(self):
        fl = self.lab()
        r = fl.cli("audit", "prepare", cwd=fl.main)
        self.assertEqual(r.returncode, 1)
        self.assertIn("tollgate: nessun lavoro attivo", r.stderr)

    def test_cli_decline_opens_block(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        r = fl.cli("audit", "decline", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.work()["phase"], "blocked")


if __name__ == "__main__":
    unittest.main()
