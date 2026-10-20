import json
import unittest
from datetime import timedelta

from tests.flowkit import SESSION, FlowLab
from tests.hookkit import DEFAULT_TOML
from tests.test_check_acts import expand
from tollgate_core import (acts, clock, config, events, git as core_git, intents, phases,
                          reviews, sessions, subagents, tasks)
from tollgate_flow import actapply, taskcmd

REVIEWER = "tollgate:final-reviewer"


class ApplyCase(unittest.TestCase):
    def make(self, **kw):
        kw.setdefault("issue", 7)
        fl = FlowLab(**kw)
        self.addCleanup(fl.close)
        self.fl = fl
        return fl

    def act(self, name, args, session=SESSION):
        """Registra l'atto con l'hook di UserPromptExpansion e ne dà l'identificativo."""
        r = expand(self.fl.lab, name, args, session=session)
        self.assertEqual(r.exit, 0, r.stderr)
        return self.fl.conn.execute("SELECT act_id FROM acts ORDER BY n DESC").fetchone()[0]

    def apply(self, act_id=None, *, session=SESSION, delta=0):
        now = self.fl.now + timedelta(seconds=delta)
        sessions.note_cli_call(self.fl.ts.state, session, str(self.fl.wt), ["act"], now=now)
        return actapply.apply_act(self.fl.ts.state, self.fl.wt, act_id, now=now)

    def work(self):
        return phases.get_work(self.fl.conn, self.fl.work)

    def state_of(self, act_id):
        return self.fl.conn.execute("SELECT state FROM acts WHERE act_id = ?",
                                    (act_id,)).fetchone()[0]

    def block_task(self):
        fl = self.fl
        tasks.add_task(fl.conn, fl.work, 1, source="piano", now=fl.now)
        tasks.task_event(fl.conn, fl.work, 1, "start", now=fl.now)
        tasks.task_event(fl.conn, fl.work, 1, "report_blocked", now=fl.now)

    def open_reasons(self):
        return [r["reason"] for r in self.fl.conn.execute(
            "SELECT reason FROM blocks WHERE work = ? AND closed IS NULL ORDER BY id",
            (self.fl.work,))]

    def open_block(self, reason="r"):
        return phases.open_block(self.fl.conn, self.fl.ts.state, self.fl.work, "needs_you",
                                 reason, now=self.fl.now)


class ResolveTest(ApplyCase):
    def test_resolve_closes_block_and_unblocks_tasks(self):
        fl = self.make()
        self.block_task()
        b = self.open_block("serve una scelta")
        self.assertEqual(self.work()["phase"], "blocked")
        a = self.act("tollgate:resolve", f"{b} procedi con la A")
        msg = self.apply()
        self.assertEqual(self.work()["phase"], "execution")
        row = fl.conn.execute("SELECT closed, resolution FROM blocks WHERE id = ?",
                              (b,)).fetchone()
        self.assertIsNotNone(row["closed"])
        self.assertEqual(row["resolution"], "procedi con la A")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["state"], "pending")
        self.assertEqual(self.state_of(a), "consumed")
        self.assertIn(str(b), msg)

    def test_tasks_stay_blocked_while_another_block_is_open(self):
        fl = self.make()
        self.block_task()
        b1 = self.open_block("uno")
        self.open_block("due")
        self.act("tollgate:resolve", f"{b1} ok")
        self.apply()
        self.assertEqual(self.work()["phase"], "blocked")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["state"], "blocked")

    def test_resolve_refuses_unknown_or_closed_block(self):
        self.make()
        a1 = self.act("tollgate:resolve", "999 nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "blocco"):
            self.apply()
        self.assertEqual(self.state_of(a1), "consumed")
        b = self.open_block()
        self.act("tollgate:resolve", f"{b} nota")
        self.apply()
        a3 = self.act("tollgate:resolve", f"{b} ancora")
        with self.assertRaisesRegex(actapply.ActApplyError, "blocco"):
            self.apply(a3)

    def test_resolve_refuses_non_ascii_digits(self):
        fl = self.make()
        self.open_block()
        a = self.act("tollgate:resolve", "² nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "non è un blocco aperto"):
            self.apply()
        self.assertEqual(self.state_of(a), "consumed")
        self.assertEqual(self.work()["phase"], "blocked")

    def test_resolve_refuses_block_of_other_work(self):
        fl = self.make()
        other = phases.create_work(fl.conn, repo_key="github.com/o/altro", issue=9, level="L1",
                                   now=fl.now)
        phases.set_phase(fl.conn, fl.ts.state, other, "execution", "advance", now=fl.now)
        b = phases.open_block(fl.conn, fl.ts.state, other, "needs_you", "r", now=fl.now)
        self.act("tollgate:resolve", f"{b} nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "blocco"):
            self.apply()
        self.assertEqual(phases.get_work(fl.conn, other)["phase"], "blocked")

    def test_resolve_writer_interrupts(self):
        fl = self.make()
        tasks.add_task(fl.conn, fl.work, 1, source="piano", now=fl.now)
        tasks.task_event(fl.conn, fl.work, 1, "start", now=fl.now)
        for aid, typ in (("ag-impl", "tollgate:implementer"),
                         ("ag-rev", "probe:reviewer-frontend"), ("ag-exp", "Explore")):
            subagents.start(fl.conn, agent_id=aid, type_=typ, session=SESSION, work=fl.work,
                            task=1 if aid == "ag-impl" else None, base_sha=None,
                            fingerprint=None, now=fl.now)
        self.act("tollgate:resolve", "writer")
        self.apply()
        self.assertEqual(subagents.get(fl.conn, "ag-impl")["state"], "interrupted")
        self.assertEqual(subagents.get(fl.conn, "ag-rev")["state"], "running")
        self.assertEqual(subagents.get(fl.conn, "ag-exp")["state"], "running")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["state"], "pending")


class ApproveLevelTest(ApplyCase):
    def test_approve_level_cap_holds_until_new_sensitive_path(self):
        fl = self.make(level="L2", phase="execution")
        old = fl.wt / "src" / "auth" / "old.py"
        old.parent.mkdir(parents=True)
        old.write_text("x = 1\n")
        fl.post_edit(old)
        self.assertEqual(self.work()["level"], "L2")
        a = self.act("tollgate:approve", "level L1 solo un rinomino")
        self.apply()
        w = self.work()
        self.assertEqual((w["level"], w["level_cap"], w["level_cap_reason"]),
                         ("L1", "L1", "solo un rinomino"))
        self.assertEqual(json.loads(w["level_cap_paths"]), ["src/auth/old.py"])
        self.assertEqual(self.state_of(a), "consumed")
        other = fl.wt / "src" / "other.py"
        other.write_text("y = 2\n")
        fl.post_edit(other)
        self.assertEqual(self.work()["level"], "L1")
        new = fl.wt / "src" / "auth" / "x.py"
        new.write_text("z = 3\n")
        fl.post_edit(new)
        self.assertEqual(self.work()["level"], "L2")

    def test_approve_level_refused_outside_target_sequence(self):
        self.make(level="L2", phase="spec_audit")
        a = self.act("tollgate:approve", "level L1 motivo")
        with self.assertRaisesRegex(actapply.ActApplyError, "spec_audit"):
            self.apply()
        self.assertEqual(self.work()["level"], "L2")
        self.assertEqual(self.state_of(a), "consumed")

    def test_cap_paths_exclude_output_dirs(self):
        fl = self.make(level="L2", phase="execution")
        out = fl.wt / "reports" / "auth"
        out.mkdir(parents=True)
        (out / "r.xml").write_text("<x/>\n")
        (fl.wt / "src" / "auth").mkdir(parents=True)
        (fl.wt / "src" / "auth" / "a.py").write_text("a = 1\n")
        self.act("tollgate:approve", "level L1 motivo")
        self.apply()
        self.assertEqual(json.loads(self.work()["level_cap_paths"]), ["src/auth/a.py"])

    def test_cap_paths_include_old_path_of_renames(self):
        fl = self.make(level="L2", phase="execution", files={"src/auth/old.py": "a = 1\n"})
        fl.git("mv", "src/auth/old.py", "src/moved.py", repo=fl.wt)
        self.act("tollgate:approve", "level L1 motivo")
        self.apply()
        self.assertEqual(json.loads(self.work()["level_cap_paths"]), ["src/auth/old.py"])

    def test_approve_level_needs_valid_level_and_reason(self):
        self.make(level="L2", phase="execution")
        self.act("tollgate:approve", "level L9 motivo")
        with self.assertRaisesRegex(actapply.ActApplyError, "livello"):
            self.apply()
        self.act("tollgate:approve", "level L1")
        with self.assertRaisesRegex(actapply.ActApplyError, "motivo"):
            self.apply()
        self.assertEqual(self.work()["level"], "L2")


class ReviewApplyCase(ApplyCase):
    """Cicli di revisione veri, costruiti con le funzioni di `reviews`."""

    def cycle(self, severity="major", *, close=True, findings_n=1):
        fl = self.fl
        n = reviews.open_cycle(fl.conn, fl.work, sha=core_git.head(fl.wt), patch_id=None,
                               code="c0de", reviewers=[REVIEWER], now=fl.now)
        findings = [{"severity": severity, "confidence": 0.9, "file": "src/app.py", "line": 2,
                     "rule": "R-1", "text": "manca il caso zero"}] * findings_n
        reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="needs_fix",
                           findings=findings, rejected=[], blocking_rules=set(),
                           known_rules=set(), now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, n, max_findings=15, now=fl.now)
        reviews.apply_verification(
            fl.conn, fl.work, n,
            [{"id": r["id"], "verification": "confirmed", "reason": "ok"} for r in rows],
            now=fl.now)
        if close:
            reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now)
        return n

    def to_review(self):
        phases.set_phase(self.fl.conn, self.fl.ts.state, self.fl.work, "review",
                         "finish_check_green", now=self.fl.now)

    def cap_reached(self, n=4, last_findings=1):
        """Quattro cicli contati con `needs_fix`: il quarto apre il blocco dei cicli."""
        for i in range(n):
            if i:
                self.to_review()
            self.cycle(findings_n=last_findings if i == n - 1 else 1)
        self.assertEqual(self.open_reasons(), [reviews.CAP_REASON])

    def decision(self, fid):
        return self.fl.conn.execute("SELECT user_decision FROM findings WHERE id = ?",
                                    (fid,)).fetchone()[0]


class ApproveRoundsTest(ReviewApplyCase):
    def test_approve_rounds_one_more_cycle(self):
        fl = self.make(phase="review")
        self.cap_reached()
        self.assertEqual(self.work()["phase"], "blocked")
        a = self.act("tollgate:approve", "rounds 1")
        msg = self.apply()
        w = self.work()
        self.assertEqual((w["phase"], w["extra_review_cycles"]), ("execution", 1))
        self.assertEqual(self.open_reasons(), [])
        self.assertEqual(self.state_of(a), "consumed")
        self.assertIn("1", msg)
        self.to_review()
        self.assertEqual(self.cycle(close=False), 5)

    def test_approve_rounds_over_eight_refused(self):
        self.make(phase="review")
        self.cap_reached()
        a = self.act("tollgate:approve", "rounds 5")           # 4 cicli fatti + 5 > 8
        with self.assertRaisesRegex(actapply.ActApplyError, "8"):
            self.apply()
        self.assertEqual(self.state_of(a), "consumed")
        self.assertEqual(self.work()["extra_review_cycles"], 0)
        self.assertEqual(self.open_reasons(), [reviews.CAP_REASON])
        self.act("tollgate:approve", "rounds 4")               # esattamente fino a 8: ammesso
        self.apply()
        self.assertEqual(self.work()["extra_review_cycles"], 4)

    def test_approve_rounds_on_fix_rounds_cap(self):
        fl = self.make(phase="plan")
        fl.register_plan()
        claude_dir = fl.home / ".claude"

        def start(fix):
            return taskcmd.task_start(fl.ts.state, fl.wt, 1, fix=fix, claude_dir=claude_dir)

        def to_changes():
            tasks.task_event(fl.conn, fl.work, 1, "report_done", now=fl.now)
            tasks.set_review_prep(fl.conn, fl.work, 1, sha="abc", code="K1")
            tasks.set_verdict(fl.conn, fl.work, 1, outcome="changes", findings=[], now=fl.now)

        start(False)
        for _ in range(5):
            to_changes()
            start(True)
        to_changes()
        with self.assertRaisesRegex(taskcmd.TaskError, "giri di correzione esauriti"):
            start(True)
        self.assertEqual(self.open_reasons(), ["giri di correzione esauriti sul task 1"])
        self.act("tollgate:approve", "rounds 2")
        self.apply()
        self.assertEqual(self.open_reasons(), [])
        self.assertEqual(self.work()["phase"], "execution")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["extra_fix_rounds"], 2)
        start(True)                                            # sesto giro
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["fix_rounds"], 6)
        to_changes()
        start(True)                                            # settimo
        to_changes()
        with self.assertRaisesRegex(taskcmd.TaskError, "giri di correzione esauriti"):
            start(True)

    def test_approve_rounds_fix_cap_over_eight_refused(self):
        fl = self.make(phase="execution")
        tasks.add_task(fl.conn, fl.work, 1, source="piano", now=fl.now)
        phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you",
                          "giri di correzione esauriti sul task 1", now=fl.now)
        self.act("tollgate:approve", "rounds 4")               # 5 + 4 > 8
        with self.assertRaisesRegex(actapply.ActApplyError, "8"):
            self.apply()
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["extra_fix_rounds"], 0)
        self.assertEqual(self.work()["phase"], "blocked")

    def test_approve_rounds_with_both_blocks_asks_resolve(self):
        fl = self.make(phase="execution")
        tasks.add_task(fl.conn, fl.work, 1, source="piano", now=fl.now)
        self.open_block(reviews.CAP_REASON)
        self.open_block("giri di correzione esauriti sul task 1")
        self.act("tollgate:approve", "rounds 1")
        with self.assertRaisesRegex(actapply.ActApplyError, "resolve"):
            self.apply()
        self.assertEqual(len(self.open_reasons()), 2)
        self.assertEqual(self.work()["extra_review_cycles"], 0)

    def test_approve_rounds_without_cap_block_or_bad_number_refused(self):
        self.make()
        self.open_block("altro motivo")
        self.act("tollgate:approve", "rounds 1")
        with self.assertRaisesRegex(actapply.ActApplyError, "tetto"):
            self.apply()
        self.open_block(reviews.CAP_REASON)
        for bad in ("0", "-1", "x", "²"):
            self.act("tollgate:approve", f"rounds {bad}")
            with self.assertRaisesRegex(actapply.ActApplyError, "intero"):
                self.apply()
        self.assertEqual(self.work()["extra_review_cycles"], 0)

    def test_resolve_on_cycles_cap_grants_one(self):
        self.make(phase="review")
        self.cap_reached()
        block = self.fl.conn.execute("SELECT id FROM blocks WHERE closed IS NULL").fetchone()[0]
        self.act("tollgate:resolve", f"{block} ancora uno")
        self.apply()
        w = self.work()
        self.assertEqual((w["phase"], w["extra_review_cycles"]), ("execution", 1))

    def test_resolve_on_cycles_cap_refused_after_eight_cycles(self):
        fl = self.make(phase="review")
        for i in range(8):
            n = reviews.open_cycle(fl.conn, fl.work, sha=f"s{i}", patch_id=None, code="c",
                                   reviewers=[REVIEWER], now=fl.now)
            reviews.supersede(fl.conn, fl.work, n, now=fl.now)
        b = self.open_block(reviews.CAP_REASON)
        self.act("tollgate:resolve", f"{b} ancora uno")
        with self.assertRaisesRegex(actapply.ActApplyError, "unverified-review"):
            self.apply()
        self.assertEqual(self.work()["extra_review_cycles"], 0)


class ApproveFindingTest(ReviewApplyCase):
    def test_approve_finding_dismiss_turns_cycle_ok(self):
        fl = self.make(phase="review")
        self.cycle()
        self.assertEqual(self.work()["phase"], "execution")
        self.assertEqual(reviews.latest(fl.conn, fl.work)["outcome"], "needs_fix")
        a = self.act("tollgate:approve", "finding f-1-1 dismiss falso positivo")
        self.apply()
        row = reviews.latest(fl.conn, fl.work)
        self.assertEqual((row["outcome"], row["stage"]), ("ok", "closed"))
        self.assertEqual(self.decision("f-1-1"), "dismissed")
        self.assertEqual(self.work()["phase"], "execution")      # nessun close_cycle: fase ferma
        self.assertEqual(self.state_of(a), "consumed")
        self.assertEqual(reviews.counted(fl.conn, fl.work), 1)
        ev = [e for e in events.export_events(fl.conn, 0) if e["type"] == "review_cycle"]
        self.assertEqual(ev[-1]["data"]["outcome"], "ok")

    def test_approve_finding_downgrade_turns_cycle_ok(self):
        fl = self.make(phase="review")
        self.cycle()
        self.act("tollgate:approve", "finding f-1-1 minor solo uno stile")
        self.apply()
        self.assertEqual(self.decision("f-1-1"), "downgraded:minor")
        self.assertEqual(reviews.latest(fl.conn, fl.work)["outcome"], "ok")

    def test_approve_finding_keeps_needs_fix_if_blocker_remains(self):
        fl = self.make(phase="review")
        n = self.cycle(close=False)
        reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now)
        fl.conn.execute("INSERT INTO findings (id, work, cycle, source, severity, confidence, "
                        "file, line, text, verification, rule, blocking) VALUES "
                        "('f-1-9', ?, 1, ?, 'blocker', 0.9, 'a', 1, 't', 'confirmed', 'R-1', 1)",
                        (fl.work, REVIEWER))
        self.act("tollgate:approve", "finding f-1-1 dismiss no")
        self.apply()
        self.assertEqual(reviews.latest(fl.conn, fl.work)["outcome"], "needs_fix")

    def test_approve_finding_closes_cap_block_when_cycle_turns_ok(self):
        fl = self.make(phase="review")
        self.cap_reached()
        last = reviews.latest(fl.conn, fl.work)["number"]
        self.act("tollgate:approve", f"finding f-{last}-1 dismiss ok")
        self.apply()
        self.assertEqual(self.open_reasons(), [])
        self.assertEqual(self.work()["phase"], "execution")
        self.assertEqual(reviews.latest(fl.conn, fl.work)["outcome"], "ok")

    def test_approve_finding_closes_cap_block_even_if_still_needs_fix(self):
        fl = self.make(phase="review")
        self.cap_reached(last_findings=2)
        last = reviews.latest(fl.conn, fl.work)["number"]
        self.assertEqual(self.work()["phase"], "blocked")
        self.act("tollgate:approve", f"finding f-{last}-1 dismiss uno è un falso positivo")
        self.apply()
        self.assertEqual(self.open_reasons(), [])
        self.assertEqual(reviews.latest(fl.conn, fl.work)["outcome"], "needs_fix")
        self.assertEqual(self.work()["phase"], "execution")       # com'era prima del blocco

    def test_approve_finding_needs_reason_and_confirmed(self):
        fl = self.make(phase="review")
        self.cycle()
        n = self.cycle_open_unjudged()
        for args, pattern in (("finding f-1-1 dismiss", "motivo"),
                              ("finding f-1-1 sgrava un motivo", "gravità"),
                              ("finding f-9-9 dismiss motivo", "inesistente"),
                              (f"finding f-{n}-1 dismiss motivo", "non è confermato")):
            self.act("tollgate:approve", args)
            with self.assertRaisesRegex(actapply.ActApplyError, pattern):
                self.apply()
        self.assertIsNone(self.decision("f-1-1"))
        self.assertEqual(reviews.latest(fl.conn, fl.work)["outcome"], None)

    def cycle_open_unjudged(self):
        """Un secondo ciclo con un rilievo senza esito."""
        fl = self.fl
        self.to_review()
        n = reviews.open_cycle(fl.conn, fl.work, sha="s2", patch_id=None, code="c",
                               reviewers=[REVIEWER], now=fl.now)
        reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="needs_fix",
                           findings=[{"severity": "major", "confidence": 0.9, "file": "a",
                                      "line": 1, "rule": "R-1", "text": "t"}],
                           rejected=[], blocking_rules=set(), known_rules=set(), now=fl.now)
        return n


class ApproveUnverifiedReviewTest(ReviewApplyCase):
    def eight_cycles(self, n):
        fl = self.fl
        for i in range(n):
            c = reviews.open_cycle(fl.conn, fl.work, sha=f"s{i}", patch_id=None, code="c",
                                   reviewers=[REVIEWER], now=fl.now)
            reviews.supersede(fl.conn, fl.work, c, now=fl.now)

    def test_unverified_review_only_after_eight(self):
        fl = self.make(phase="review")
        self.eight_cycles(7)
        a = self.act("tollgate:approve", "unverified-review")
        with self.assertRaisesRegex(actapply.ActApplyError, "8"):
            self.apply()
        self.assertEqual(self.work()["review_unverified"], 0)
        self.assertEqual(self.state_of(a), "consumed")
        self.eight_cycles(1)
        self.open_block(reviews.CAP_REASON)
        self.assertEqual(self.work()["phase"], "blocked")
        self.act("tollgate:approve", "unverified-review")
        self.apply()
        w = self.work()
        self.assertEqual((w["review_unverified"], w["phase"]), (1, "review"))
        self.assertEqual(self.open_reasons(), [])

    def test_findings_without_outcome_become_unverified(self):
        fl = self.make(phase="review")
        self.eight_cycles(7)
        n = reviews.open_cycle(fl.conn, fl.work, sha="s8", patch_id=None, code="c",
                               reviewers=[REVIEWER], now=fl.now)
        reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="needs_fix",
                           findings=[{"severity": "major", "confidence": 0.9, "file": "a",
                                      "line": 1, "rule": "R-1", "text": "t"}],
                           rejected=[], blocking_rules=set(), known_rules=set(), now=fl.now)
        self.assertEqual(n, 8)
        self.open_block(reviews.CAP_REASON)
        self.act("tollgate:approve", "unverified-review")
        self.apply()
        row = fl.conn.execute("SELECT verification, verification_reason FROM findings "
                              "WHERE work = ? AND id = 'f-8-1'", (fl.work,)).fetchone()
        self.assertEqual(tuple(row), ("unverified", "revisione non verificata"))
        self.assertEqual(reviews.unjudged_ids(fl.conn, fl.work, 8), [])


class ApproveRebaseTest(ApplyCase):
    def conflict(self, phase):
        fl = self.make(phase=phase)
        fl.commit("src/app.py", "def somma(a, b):\n    return b + a\n", "uno")
        phases.set_base(fl.conn, fl.work, core_git.head(fl.wt), cause="test", now=fl.now)
        self.open_block(intents.SYNC_CONFLICT_REASON + " (src/app.py)")
        return fl

    def forces(self):
        return self.fl.conn.execute("SELECT state FROM intents WHERE work = ? "
                                    "AND action = 'force_push'", (self.fl.work,)).fetchall()

    def test_approve_rebase_realigns_base_and_authorizes_force(self):
        fl = self.conflict("pr_open")
        self.assertEqual(self.work()["phase"], "blocked")
        expected = fl.git("merge-base", "HEAD", core_git.default_ref(fl.main), repo=fl.wt)
        a = self.act("tollgate:approve", "rebase")
        self.apply()
        w = self.work()
        self.assertEqual((w["work_base_sha"], w["phase"]), (expected, "execution"))
        self.assertEqual(self.open_reasons(), [])
        self.assertEqual([r["state"] for r in self.forces()], ["authorized"])
        self.assertEqual(self.state_of(a), "consumed")
        ev = [e for e in events.export_events(fl.conn, 0) if e["type"] == "base_realigned"]
        self.assertEqual(ev[-1]["data"]["to"], expected)

    def test_approve_rebase_force_carries_remote_tip_as_lease(self):
        fl = self.conflict("pr_open")
        remote = core_git.head(fl.wt)
        fl.git("push", "-q", "origin", f"{remote}:refs/heads/tg/7-demo", repo=fl.wt)
        self.act("tollgate:approve", "rebase")
        self.apply()
        self.assertEqual(intents.force_lease(fl.conn, fl.work), remote)

    def test_approve_rebase_keeps_execution_phase(self):
        fl = self.conflict("execution")
        expected = fl.git("merge-base", "HEAD", core_git.default_ref(fl.main), repo=fl.wt)
        self.act("tollgate:approve", "rebase")
        self.apply()
        w = self.work()
        self.assertEqual((w["work_base_sha"], w["phase"]), (expected, "execution"))
        self.assertEqual(len(self.forces()), 1)
        causes = [e["data"]["cause"] for e in events.export_events(fl.conn, 0)
                  if e["type"] == "phase_change"]
        self.assertNotIn("sync", causes)

    def test_approve_rebase_needs_the_sync_conflict_block(self):
        fl = self.make(phase="pr_open")
        self.open_block("un altro motivo")
        self.act("tollgate:approve", "rebase")
        with self.assertRaisesRegex(actapply.ActApplyError, "conflitto"):
            self.apply()
        self.assertEqual(self.work()["work_base_sha"], fl.base)
        self.assertEqual(self.forces(), [])


class RefusalTest(ApplyCase):
    def test_act_of_other_session_or_expired_refused(self):
        self.make()
        b = self.open_block()
        other = self.act("tollgate:resolve", f"{b} nota", session="altra")
        with self.assertRaisesRegex(actapply.ActApplyError, "atto"):
            self.apply(other)
        with self.assertRaisesRegex(actapply.ActApplyError, "nessun atto"):
            self.apply()
        mine = self.act("tollgate:resolve", f"{b} nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "atto"):
            self.apply(mine, delta=3600)
        self.assertEqual(self.work()["phase"], "blocked")

    def test_act_consumed_once(self):
        self.make()
        b = self.open_block()
        a = self.act("tollgate:resolve", f"{b} nota")
        self.apply(a)
        with self.assertRaisesRegex(actapply.ActApplyError, "atto"):
            self.apply(a)

    def test_unknown_act_type_refused(self):
        self.make()
        a = self.act("tollgate:approve", "waiver w-7-1")
        with self.assertRaisesRegex(actapply.ActApplyError, "non si applica con act apply"):
            self.apply(a)
        self.assertEqual(self.state_of(a), "pending")

    def test_without_id_takes_last_applicable_pending(self):
        self.make()
        b = self.open_block()
        a1 = self.act("tollgate:resolve", f"{b} nota")
        a2 = self.act("tollgate:approve", "waiver w-7-1")
        self.apply()
        self.assertEqual((self.state_of(a1), self.state_of(a2)), ("consumed", "pending"))

    def test_session_not_recognised(self):
        fl = self.make()
        with self.assertRaisesRegex(actapply.ActApplyError, "sessione non riconosciuta"):
            actapply.apply_act(fl.ts.state, fl.wt, None, now=fl.now)

    def test_no_work_for_directory(self):
        fl = self.make()
        sessions.note_cli_call(fl.ts.state, SESSION, str(fl.main), ["act"], now=fl.now)
        with self.assertRaisesRegex(actapply.ActApplyError, "nessun lavoro"):
            actapply.apply_act(fl.ts.state, fl.main, None, now=fl.now)


class CliTest(ApplyCase):
    def test_cli_refuses_with_message_and_exit_1(self):
        fl = self.make()
        self.open_block()
        r = fl.cli("act", "apply", cwd=fl.wt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("tollgate:", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_applies_act_recorded_now(self):
        fl = self.make()
        b = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "r", now=clock.now())
        acts.record_act(fl.conn, type_="resolve", target=str(b), args=[str(b), "fatto"],
                        typed_text="/tollgate:resolve", session=SESSION, work=fl.work,
                        now=clock.now(), ttl_minutes=10)
        r = fl.cli("act", "apply", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.work()["phase"], "execution")


class ConfigTest(unittest.TestCase):
    def test_is_readonly(self):
        cfg = config.load_config_text(DEFAULT_TOML)
        for t in ("tollgate:task-reviewer", "Explore", "probe:reviewer-frontend",
                  "probe:final-x"):
            self.assertTrue(config.is_readonly(cfg, t), t)
        for t in ("tollgate:implementer", "general-purpose", None, ""):
            self.assertFalse(config.is_readonly(cfg, t), t)

    def test_output_excludes(self):
        out = config.output_excludes(config.load_config_text(DEFAULT_TOML))
        self.assertEqual(out, ["reports/", "coverage/", ".tollgate-run/"])
