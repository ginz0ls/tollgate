import json
import unittest

from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.test_check_writes import with_scope
from tests.test_verdicts import GOOD
from tollgate_core import git as tg_git, subagents, tasks

IMPL = "tollgate:implementer"
REVIEWER = "tollgate:task-reviewer"
CODE = "c0de1234"


class Base(unittest.TestCase):
    toml = DEFAULT_TOML

    def setUp(self):
        self.lab = Lab(toml=self.toml)
        with_scope(self.lab)
        c, w = self.lab.conn, self.lab.work
        tasks.task_event(c, w, 1, "start", now=self.lab.now)
        tasks.assign(c, w, 1, implementer="tg-7-t1", agent_type=IMPL, pending="launch",
                     reviewer_type=REVIEWER, now=self.lab.now)
        tasks.task_event(c, w, 1, "report_done", now=self.lab.now)
        self.sha = tg_git.head(self.lab.wt)
        tasks.set_review_prep(c, w, 1, sha=self.sha, code=CODE)
        self.start("r1", REVIEWER)

    def tearDown(self):
        self.lab.close()

    def start(self, aid, atype):
        subagents.start(self.lab.conn, agent_id=aid, type_=atype, session=SESSION,
                        work=self.lab.work, task=None, base_sha=tg_git.head(self.lab.wt),
                        fingerprint=tg_git.fingerprint(self.lab.wt, ["reports/", "coverage/"]),
                        now=self.lab.now)

    def verdict(self, **over):
        data = {"v": 1, "task": 1, "sha": self.sha, "code": CODE, "outcome": "approved",
                "spec_compliance": [], "findings": []}
        data.update(over)
        return "Verdetto.\n```json\n" + json.dumps(data) + "\n```"

    def stop(self, aid="r1", atype=REVIEWER, text=None):
        p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.lab.wt),
                   agent_id=aid, agent_type=atype, last_assistant_message=text,
                   agent_transcript_path="/non/esiste.jsonl")
        if text is None:
            p.pop("last_assistant_message")
        return self.lab.hook(p)

    def minor(self):
        return self.verdict(outcome="changes", findings=[dict(GOOD, severity="minor")])

    def task(self):
        return tasks.get_task(self.lab.conn, self.lab.work, 1)

    def sub(self, aid="r1"):
        return subagents.get(self.lab.conn, aid)

    def open_blocks(self):
        return [r[0] for r in self.lab.conn.execute(
            "SELECT type FROM blocks WHERE work = ? AND closed IS NULL", (self.lab.work,))]


class VerdictTest(Base):
    def test_approved_recorded_and_row_closed(self):
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        t = self.task()
        self.assertEqual((t["verdict"], t["state"], json.loads(t["review_findings"])),
                         ("approved", "review", []))
        self.assertEqual((self.sub()["state"], self.sub()["declared_status"]),
                         ("done", "approved"))
        self.assertEqual(self.open_blocks(), [])

    def test_changes_recorded_with_valid_findings(self):
        text = self.verdict(outcome="changes", findings=[GOOD, {"text": "senza prova"}])
        self.assertEqual(self.stop(text=text).exit, 0)
        t = self.task()
        self.assertEqual((t["verdict"], json.loads(t["review_findings"])), ("changes", [GOOD]))

    def test_invalid_verdict_vetoes_twice_then_needs_you(self):
        bad = self.verdict(sha="altro")
        for n in (1, 2):
            r = self.stop(text=bad)
            self.assertEqual(r.exit, 2)
            self.assertIn("sha", r.stderr)
            self.assertEqual((self.sub()["state"], self.sub()["vetoes"]), ("running", n))
        self.assertEqual(self.stop(text=bad).exit, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.open_blocks(), ["needs_you"])
        self.assertIsNone(self.task()["verdict"])
        reason = self.lab.conn.execute("SELECT reason FROM blocks").fetchone()[0]
        self.assertIn("verdetto del revisore non valido", reason)

    def test_standard_on_minor_only_approved(self):
        self.stop(text=self.minor())
        self.assertEqual(self.task()["verdict"], "approved")

    def test_dropped_blocker_vetoes_and_dropped_count_in_event(self):
        bad = {"severity": "blocker", "file": "src/app.py", "text": "senza riga e regola"}
        r = self.stop(text=self.verdict(outcome="changes", findings=[bad]))
        self.assertEqual(r.exit, 2)
        self.assertIn("rilievo bloccante senza file, riga o regola", r.stderr)
        self.assertIsNone(self.task()["verdict"])
        self.assertEqual(self.stop(text=self.verdict(
            outcome="changes", findings=[dict(GOOD, severity="minor"), {"severity": "minor", "text": "x"}])).exit, 0)
        changes = [e for e in self.lab.events("task_change") if e["verdict"] == "approved"]
        self.assertEqual(changes[-1]["dropped"], 1)

    def test_valid_verdict_after_a_veto(self):
        self.assertEqual(self.stop(text="approvo, tutto a posto").exit, 2)
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.task()["verdict"], "approved")

    def test_tampering_reviewer_verdict_ignored(self):
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.sub()["state"], "tampered")
        self.assertEqual(self.open_blocks(), ["needs_you"])
        self.assertIsNone(self.task()["verdict"])

    def test_implementer_cannot_deliver_verdict(self):
        self.start("i1", IMPL)
        self.stop(aid="i1", atype=IMPL, text=self.verdict())
        self.assertIsNone(self.task()["verdict"])
        self.assertEqual(self.task()["state"], "review")

    def test_handback_report_used_in_auto_mode(self):
        subagents.set_report(self.lab.conn, "r1", self.verdict())
        self.assertEqual(self.stop(text=None).exit, 0)
        self.assertEqual(self.task()["verdict"], "approved")

    def test_not_awaiting_after_fix_without_new_prepare(self):
        """C10: dopo un --fix e un nuovo report_done il revisore non è in attesa."""
        c, w = self.lab.conn, self.lab.work
        tasks.set_verdict(c, w, 1, outcome="changes", findings=[GOOD], now=self.lab.now)
        tasks.task_event(c, w, 1, "fix", now=self.lab.now)
        tasks.task_event(c, w, 1, "report_done", now=self.lab.now)
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        t = self.task()
        self.assertEqual((t["verdict"], json.loads(t["review_findings"])), ("changes", [GOOD]))
        self.assertEqual(self.sub()["state"], "done")

    def test_other_reviewer_type_is_not_awaited(self):
        self.start("r2", "tollgate:task-reviewer-other")
        self.stop(aid="r2", atype="tollgate:task-reviewer-other", text=self.verdict())
        self.assertIsNone(self.task()["verdict"])


class BlockingRulesTest(Base):
    toml = DEFAULT_TOML + """
[profiles]
active = ["web"]
[profiles.web]
paths = ["**"]
rules = ["R-WEB-1", "R-WEB-2"]
blocking_rules = ["R-WEB-1"]
"""

    def test_profile_rule_not_blocking(self):
        f = dict(GOOD, rule="R-WEB-2")
        self.assertEqual(self.stop(text=self.verdict(outcome="changes", findings=[f])).exit, 0)
        self.assertEqual(self.task()["verdict"], "approved")

    def test_profile_blocking_rule_blocks(self):
        f = dict(GOOD, rule="R-WEB-1")
        self.stop(text=self.verdict(outcome="approved", findings=[f]))
        self.assertEqual(self.task()["verdict"], "changes")


class StandardOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nreviewer_standard = false\n"

    def test_reviewer_standard_component_off(self):
        self.stop(text=self.minor())
        self.assertEqual(self.task()["verdict"], "changes")


class ReadonlyOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nreadonly_check = false\n"

    def test_tampering_ignored_when_component_off(self):
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(text=self.verdict()).exit, 0)
        self.assertEqual(self.task()["verdict"], "approved")
        self.assertEqual(self.sub()["state"], "done")


if __name__ == "__main__":
    unittest.main()
