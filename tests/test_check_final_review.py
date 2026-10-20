import json
import unittest
from datetime import timedelta
from types import SimpleNamespace

from tests.helpers import git
from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.test_check_task_verdict import CODE as TASK_CODE
from tests.test_verdicts import GOOD
from tollgate_core import config, git as tg_git, reviews, subagents, tasks
from tollgate_hooks import apply

REVIEWER = "tollgate:final-reviewer"
VERIFIER = "tollgate:finding-verifier"
SPEC = "probe:final-security"
CODE = "f1na1c0d"
SEC_TOML = DEFAULT_TOML + """
[profiles.security]
paths = ["src/**"]
final_specialist = "probe:final-security"
"""
RULES_TOML = DEFAULT_TOML + """
[profiles.sec]
paths = ["src/**"]
rules = ["R-SEC-1", "R-SEC-2"]
blocking_rules = ["R-SEC-1"]
"""


class Base(unittest.TestCase):
    toml = DEFAULT_TOML
    level = "L1"
    reviewers = (REVIEWER,)

    def setUp(self):
        self.lab = Lab(level=self.level, phase="review", toml=self.toml)
        wt = self.lab.wt
        (wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
        git(wt, "add", "-A")
        git(wt, "commit", "-q", "-m", "somma")
        self.sha = tg_git.head(wt)
        reviews.open_cycle(self.lab.conn, self.lab.work, sha=self.sha, patch_id=None, code=CODE,
                           reviewers=list(self.reviewers), now=self.lab.now)
        for i, t in enumerate(self.reviewers):
            self.start(f"a{i}", t)

    def tearDown(self):
        self.lab.close()

    def start(self, aid, atype):
        subagents.start(self.lab.conn, agent_id=aid, type_=atype, session=SESSION,
                        work=self.lab.work, task=None, base_sha=tg_git.head(self.lab.wt),
                        fingerprint=tg_git.fingerprint(self.lab.wt, ["reports/", "coverage/"]),
                        now=self.lab.now)

    def verdict(self, **over):
        data = {"v": 1, "sha": self.sha, "code": CODE, "outcome": "needs_fix",
                "findings": [GOOD]}
        data.update(over)
        return "Verdetto.\n```json\n" + json.dumps(data) + "\n```"

    def results(self, *pairs, **over):
        data = {"v": 1, "sha": self.sha, "code": CODE,
                "results": [{"id": i, "verification": v, "reason": "visto"} for i, v in pairs]}
        data.update(over)
        return "Esiti.\n```json\n" + json.dumps(data) + "\n```"

    def stop(self, aid="a0", atype=REVIEWER, text=None):
        p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.lab.wt),
                   agent_id=aid, agent_type=atype, last_assistant_message=text,
                   agent_transcript_path="/non/esiste.jsonl")
        if text is None:
            p.pop("last_assistant_message")
        return self.lab.hook(p)

    def cycle(self):
        return reviews.latest(self.lab.conn, self.lab.work)

    def sub(self, aid="a0"):
        return subagents.get(self.lab.conn, aid)

    def findings(self):
        return self.lab.conn.execute("SELECT * FROM findings WHERE work = ? ORDER BY rowid",
                                     (self.lab.work,)).fetchall()

    def phase(self):
        return self.lab.conn.execute("SELECT phase FROM work_items WHERE id = ?",
                                     (self.lab.work,)).fetchone()[0]

    def open_blocks(self):
        return [r[0] for r in self.lab.conn.execute(
            "SELECT reason FROM blocks WHERE work = ? AND closed IS NULL", (self.lab.work,))]

    def report_verifier(self, text):
        self.start("v1", VERIFIER)
        return self.stop(aid="v1", atype=VERIFIER, text=text)


class ReviewerTest(Base):
    def test_valid_verdict_registers_findings_and_moves_to_verify(self):
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        c = self.cycle()
        self.assertEqual((c["stage"], json.loads(c["reported"])), ("verify", {REVIEWER: "needs_fix"}))
        f = self.findings()
        self.assertEqual([(x["id"], x["source"], x["verification"], x["blocking"]) for x in f],
                         [("f-1-1", REVIEWER, None, 1)])
        self.assertEqual((self.sub()["state"], self.sub()["declared_status"]),
                         ("done", "needs_fix"))
        self.assertEqual(self.open_blocks(), [])

    def test_verdict_without_code_needs_you(self):
        text = self.verdict(code="altro")
        self.assertEqual(self.stop(text=text).exit, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.cycle()["stage"], "review")
        self.assertEqual(self.findings(), [])
        [reason] = self.open_blocks()
        self.assertIn("verdetto del revisore finale non valido", reason)
        self.assertIn("code", reason)

    def test_malformed_json_needs_you(self):
        self.assertEqual(self.stop(text="Tutto a posto, niente JSON.").exit, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.cycle()["stage"], "review")
        self.assertIn("verdetto del revisore finale non valido", self.open_blocks()[0])
        self.assertEqual(self.stop(aid="a0", text="{").exit, 0)    # già chiuso: nulla di nuovo
        self.assertEqual(len(self.open_blocks()), 1)

    def test_reviewer_that_changed_files_tampered(self):
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.sub()["state"], "tampered")
        self.assertEqual(self.findings(), [])
        self.assertEqual(self.cycle()["stage"], "review")
        self.assertIn("ha cambiato file", self.open_blocks()[0])

    def test_interrupted_reviewer_that_changed_files_tampered(self):
        subagents.interrupt(self.lab.conn, "a0", now=self.lab.now + timedelta(minutes=30))
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.sub()["state"], "tampered")
        self.assertEqual(self.findings(), [])
        self.assertEqual(self.cycle()["stage"], "review")
        self.assertIn("ha cambiato file", self.open_blocks()[0])

    def test_rejected_report_leaves_trace(self):
        """Un riporto non più accettabile (qui: il ciclo non è più in stadio review) non si
        applica, ma lascia l'evento `veto` con il motivo."""
        conn = self.lab.conn
        reviews.supersede(conn, self.lab.work, 1, now=self.lab.now)
        main = tg_git.main_worktree(self.lab.wt)
        ctx = SimpleNamespace(
            config=config.load_config(self.lab.ts.state, main, "origin/main"),
            now=self.lab.now, event=SimpleNamespace(session=SESSION),
            cfg=lambda k: config.load_config(self.lab.ts.state, main, "origin/main").get(k))
        apply._review_report(conn, self.lab.ts.state, ctx, {
            "work": self.lab.work, "cycle": 1, "source": REVIEWER, "outcome": "needs_fix",
            "findings": [GOOD], "rejected": []})
        (veto,) = self.lab.events("veto")
        self.assertEqual((veto["rule"], veto["event"]), ("final_review", "subagent_stop"))
        self.assertIn("review", veto["reason"])
        self.assertEqual(self.findings(), [])

    def test_handback_report_used_in_auto_mode(self):
        subagents.set_report(self.lab.conn, "a0", self.verdict())
        self.assertEqual(self.stop(text=None).exit, 0)
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertEqual(len(self.findings()), 1)

    def test_stale_interrupted_reviewer_verdict_counts(self):
        subagents.interrupt(self.lab.conn, "a0", now=self.lab.now + timedelta(minutes=30))
        self.assertEqual(self.sub()["state"], "interrupted")
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertEqual(len(self.findings()), 1)

    def test_reviewer_clean_ok_closes_cycle_without_verifier(self):
        self.assertEqual(self.stop(text=self.verdict(outcome="ok", findings=[])).exit, 0)
        c = self.cycle()
        self.assertEqual((c["stage"], c["outcome"], c["counted"]), ("closed", "ok", 0))
        self.assertEqual(self.phase(), "review")

    def test_declared_outcome_does_not_decide_the_cycle(self):
        """Un `needs_fix` dichiarato senza rilievi validi chiude `ok` (decisione 6)."""
        bad = {"severity": "minor", "text": "senza prova"}
        self.assertEqual(self.stop(text=self.verdict(findings=[bad])).exit, 0)
        c = self.cycle()
        self.assertEqual((c["stage"], c["outcome"]), ("closed", "ok"))
        self.assertEqual([x["verification"] for x in self.findings()], ["rejected"])

    def test_declared_needs_you_opens_block(self):
        self.stop(text=self.verdict(outcome="needs_you", findings=[]))
        c = self.cycle()
        self.assertEqual((c["stage"], c["outcome"]), ("closed", "needs_you"))
        self.assertIn("il revisore finale chiede una decisione", self.open_blocks()[0])

    def test_finding_without_rule_rejected_not_sent_to_verifier(self):
        no_rule = {k: v for k, v in GOOD.items() if k != "rule"}
        self.stop(text=self.verdict(findings=[no_rule, GOOD]))
        f = self.findings()
        self.assertEqual([(x["verification"], x["verification_reason"]) for x in f],
                         [(None, None), ("rejected", reviews.NO_PROOF)])
        self.assertEqual(reviews.unjudged_ids(self.lab.conn, self.lab.work, 1), ["f-1-1"])
        self.assertEqual(self.cycle()["stage"], "verify")

    def test_second_report_from_same_reviewer_ignored(self):
        self.stop(text=self.verdict(outcome="ok", findings=[]))
        self.start("a9", REVIEWER)
        self.assertEqual(self.stop(aid="a9", text=self.verdict()).exit, 0)
        self.assertEqual(self.findings(), [])
        self.assertEqual(self.sub("a9")["state"], "done")     # non più in attesa: lo chiude subagent_stop

    def test_task_reviewer_path_unchanged(self):
        c, w = self.lab.conn, self.lab.work
        tasks.add_task(c, w, 1, source="plan", now=self.lab.now)
        c.execute("UPDATE tasks SET state = 'review', reviewer_type = ?, review_code = ?, "
                  "review_sha = ? WHERE work = ? AND number = 1",
                  ("tollgate:task-reviewer", TASK_CODE, self.sha, w))
        c.commit()
        self.start("t1", "tollgate:task-reviewer")
        data = {"v": 1, "task": 1, "sha": self.sha, "code": TASK_CODE, "outcome": "approved",
                "spec_compliance": [], "findings": []}
        r = self.stop(aid="t1", atype="tollgate:task-reviewer",
                      text="```json\n" + json.dumps(data) + "\n```")
        self.assertEqual(r.exit, 0)
        self.assertEqual(tasks.get_task(c, w, 1)["verdict"], "approved")
        self.assertEqual(self.cycle()["stage"], "review")
        self.assertEqual(self.findings(), [])


class RulesTest(Base):
    toml = RULES_TOML

    def blocking_of(self, rule):
        self.stop(text=self.verdict(findings=[dict(GOOD, rule=rule)]))
        (row,) = self.lab.conn.execute("SELECT blocking FROM findings WHERE work = ?",
                                       (self.lab.work,)).fetchall()
        return row[0]

    def test_profile_rules_apply_on_work_diff(self):
        self.assertEqual(self.blocking_of("R-SEC-2"), 0)          # nota e non `[blocca]`

    def test_rules_with_default_ref_fallback(self):
        """Senza `work_base_sha` la base è `origin/main` (come in `review prepare`): il
        profilo si attiva lo stesso e la regola nota non blocca."""
        self.lab.conn.execute("UPDATE work_items SET work_base_sha = NULL WHERE id = ?",
                              (self.lab.work,))
        self.lab.conn.commit()
        self.assertEqual(self.blocking_of("R-SEC-2"), 0)

    def test_unreadable_diff_blocks_every_r_rule(self):
        self.sha = "0" * 40                                   # la punta del ciclo non esiste
        self.lab.conn.execute("UPDATE review_cycles SET sha = ? WHERE work = ?",
                              (self.sha, self.lab.work))
        self.lab.conn.commit()
        self.assertEqual(self.blocking_of("R-SEC-2"), 1)          # fail-closed


class VerifierTest(Base):
    def verify_stage(self, findings=None):
        self.stop(text=self.verdict(findings=findings or [GOOD]))
        self.assertEqual(self.cycle()["stage"], "verify")

    def test_verifier_confirms_and_closes_cycle_needs_fix(self):
        self.verify_stage()
        self.assertEqual(self.phase(), "review")
        self.assertEqual(self.report_verifier(self.results(("f-1-1", "confirmed"))).exit, 0)
        c = self.cycle()
        self.assertEqual((c["stage"], c["outcome"], c["counted"], c["findings_confirmed"]),
                         ("closed", "needs_fix", 1, 1))
        self.assertEqual(self.phase(), "execution")
        self.assertEqual(self.sub("v1")["state"], "done")
        self.assertEqual(self.open_blocks(), [])

    def test_verifier_rejects_all_closes_ok(self):
        self.verify_stage()
        self.report_verifier(self.results(("f-1-1", "rejected")))
        self.assertEqual((self.cycle()["outcome"], self.phase()), ("ok", "review"))

    def test_invalid_verifier_report_needs_you(self):
        self.verify_stage()
        self.report_verifier(self.results(("f-1-1", "confirmed"), code="altro"))
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertEqual(self.sub("v1")["state"], "done")
        self.assertIn("risultati del verificatore non valido", self.open_blocks()[0])

    def test_verifier_tampered(self):
        self.verify_stage()
        self.start("v1", VERIFIER)
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.stop(aid="v1", atype=VERIFIER, text=self.results(("f-1-1", "confirmed")))
        self.assertEqual(self.sub("v1")["state"], "tampered")
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertIsNone(self.findings()[0]["verification"])

    def test_verifier_not_awaited_in_review_stage(self):
        self.start("v1", VERIFIER)
        self.stop(aid="v1", atype=VERIFIER, text=self.results(("f-1-1", "confirmed")))
        self.assertEqual(self.open_blocks(), [])
        self.assertEqual(self.cycle()["stage"], "review")

    def test_verifier_omits_ids_twice_needs_you(self):
        three = [GOOD, dict(GOOD, line=3), dict(GOOD, line=4)]
        self.verify_stage(three)
        self.report_verifier(self.results(("f-1-1", "confirmed")))
        self.assertEqual(self.open_blocks(), [])          # primo riporto: si rilancia
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertEqual(json.loads(self.cycle()["reported"])[VERIFIER], 1)
        self.start("v2", VERIFIER)
        self.stop(aid="v2", atype=VERIFIER, text=self.results(("f-1-2", "confirmed")))
        self.assertEqual(self.open_blocks(), ["verificatore senza esito su: f-1-3"])
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertEqual([x["verification"] for x in self.findings()],
                         ["confirmed", "confirmed", None])

    def test_verifier_completes_on_second_run(self):
        two = [GOOD, dict(GOOD, line=3)]
        self.verify_stage(two)
        self.report_verifier(self.results(("f-1-1", "rejected")))
        self.start("v2", VERIFIER)
        self.stop(aid="v2", atype=VERIFIER, text=self.results(("f-1-2", "rejected")))
        self.assertEqual((self.cycle()["stage"], self.cycle()["outcome"]), ("closed", "ok"))
        self.assertEqual(self.open_blocks(), [])


class ComponentOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nfinal_review = false\n"

    def test_final_review_component_off_ignores_verdict(self):      # criterio 18
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.findings(), [])
        self.assertEqual((self.cycle()["stage"], self.cycle()["reported"]), ("review", "{}"))
        self.assertEqual(self.open_blocks(), [])


class SpecialistTest(Base):
    toml = SEC_TOML
    level = "L2"
    reviewers = (REVIEWER, SPEC)

    def test_specialist_findings_go_to_same_verifier(self):
        self.stop(aid="a0", atype=REVIEWER, text=self.verdict(findings=[GOOD]))
        self.assertEqual(self.cycle()["stage"], "review")        # manca lo specialista
        self.assertEqual(self.open_blocks(), [])
        self.stop(aid="a1", atype=SPEC,
                  text=self.verdict(findings=[dict(GOOD, rule="R-SEC-1", line=5)]))
        self.assertEqual(self.cycle()["stage"], "verify")
        self.assertEqual(sorted(json.loads(self.cycle()["reported"])), sorted([REVIEWER, SPEC]))
        self.assertEqual([(x["id"], x["source"]) for x in self.findings()],
                         [("f-1-1", REVIEWER), ("f-1-2", SPEC)])
        self.assertEqual(reviews.unjudged_ids(self.lab.conn, self.lab.work, 1),
                         ["f-1-1", "f-1-2"])
        self.report_verifier(self.results(("f-1-1", "confirmed"), ("f-1-2", "rejected")))
        self.assertEqual((self.cycle()["outcome"], self.phase()), ("needs_fix", "execution"))


if __name__ == "__main__":
    unittest.main()
