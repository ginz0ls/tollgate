import json
import unittest
from datetime import timedelta

from tests.flowkit import FlowLab
from tollgate_analysis import prblock
from tollgate_core import config, git as core_git, phases, reviews
from tollgate_flow import openpr

SPEC_ORDER = [
    "schema_version", "tollgate_version", "issue", "level", "level_minimum", "level_cap",
    "level_cap_reason", "gate_mode", "plan", "plan_sha", "spec", "spec_reviews_dir",
    "plan_reviews_dir", "spec_audit", "head_sha", "receipts", "waivers_file", "blocks", "acts",
    "dod", "verdict", "findings", "fix_rounds", "subagents", "effects", "components_off",
    "off_periods", "tasks_over", "skills_absent"]


def facts(**kw):
    data = {
        "schema_version": 1, "tollgate_version": "0.1.0", "issue": 42, "level": "L1",
        "level_minimum": "L1", "level_cap": None, "level_cap_reason": None,
        "gate_mode": "protected", "plan": "docs/superpowers/plans/x.md", "plan_sha": "abc",
        "spec": None, "spec_reviews_dir": None, "plan_reviews_dir": None,
        "spec_audit": {"adversarial": None, "lens": None}, "head_sha": "def",
        "receipts": [{"command": "verify", "state": "green", "tests_run": 120}],
        "waivers_file": ".tollgate/waivers/42.toml", "blocks": [], "acts": [],
        "dod": {"L": "L1", "items": {"receipt": True}},
        "verdict": {"outcome": "ok", "cycles": 1, "findings_confirmed": 0, "unverified": False},
        "findings": [], "fix_rounds": {}, "subagents": {"count": 0, "tokens": 0},
        "effects": [], "components_off": [], "off_periods": [], "tasks_over": [],
        "skills_absent": [], "extra": "ignorato"}
    data.update(kw)
    return data


class BuildTest(unittest.TestCase):
    def test_build_has_all_fields_in_order(self):
        block = prblock.build(facts())
        self.assertEqual(list(block), SPEC_ORDER)
        self.assertEqual(list(prblock.FIELDS), SPEC_ORDER)
        self.assertEqual(prblock.SCHEMA_VERSION, 1)
        self.assertNotIn("extra", block)

    def test_fields_order_with_new_fields(self):
        """Decisione 21: `tasks_over` e `skills_absent` sono le ultime due voci; un blocco
        scritto prima di P4, senza le due voci, si legge ancora."""
        self.assertEqual(list(prblock.FIELDS[-2:]), ["tasks_over", "skills_absent"])
        block = prblock.build(facts(tasks_over=[{"task": 2, "lines": 300, "size_reason": None}],
                                    skills_absent=[{"task": 1, "skills": ["a"]}]))
        self.assertEqual(list(block)[-2:], ["tasks_over", "skills_absent"])
        old = {k: v for k, v in block.items() if k not in prblock.DEFAULTS}
        parsed = prblock.parse(prblock.render(old))
        self.assertEqual(parsed, old)
        self.assertNotIn("tasks_over", parsed)
        self.assertEqual(prblock.build({**old})["skills_absent"], [])

    def test_new_fields_default_to_empty_lists(self):
        block = prblock.build(facts())
        self.assertEqual((block["tasks_over"], block["skills_absent"]), ([], []))
        block = prblock.build(facts(tasks_over=[{"task": 2, "lines": 300, "size_reason": "x"}],
                                    skills_absent=[{"task": 1, "skills": ["a"]}]))
        self.assertEqual(block["tasks_over"][0]["lines"], 300)
        self.assertEqual(block["skills_absent"], [{"task": 1, "skills": ["a"]}])
        self.assertEqual(prblock.parse(prblock.render(block)), block)

    def test_findings_carry_blocking_field(self):
        """I rilievi del blocco li scrive `open-pr` dal DB: `blocking` è un booleano per rilievo
        (una regola `piano:*` blocca, una nota di regola nota no) e sopravvive a render e parse."""
        fl = FlowLab(issue=7)
        self.addCleanup(fl.close)
        fl.commit("src/app.py", "def somma(a, b):\n    return b + a\n", "somma")
        head = core_git.head(fl.wt)
        n = reviews.open_cycle(fl.conn, fl.work, sha=head, patch_id=None, code="c1",
                               reviewers=["tollgate:final-reviewer"], now=fl.now)
        reviews.add_report(
            fl.conn, fl.work, n, source="tollgate:final-reviewer", outcome="ok", findings=[
                {"severity": "major", "confidence": 0.9, "file": "src/app.py", "line": 2,
                 "rule": "R-1", "text": "nota"},
                {"severity": "major", "confidence": 0.9, "file": "src/app.py", "line": 2,
                 "rule": "piano:task 1", "text": "blocca"}],
            rejected=[], blocking_rules=set(), known_rules={"R-1"}, now=fl.now)
        work = phases.get_work(fl.conn, fl.work)
        cfg = config.load_config(fl.ts.state, fl.wt, work["work_base_sha"])
        data = openpr.facts(fl.conn, fl.ts.state, work, cfg, fl.wt, head,
                            now=fl.now + timedelta(hours=1))
        parsed = prblock.parse(prblock.render(prblock.build(data)))
        self.assertEqual([f["blocking"] for f in parsed["findings"]], [False, True])
        for finding in parsed["findings"]:
            self.assertEqual(sorted(finding), ["blocking", "confidence", "id", "severity",
                                               "user_decision", "verification"])

    def test_missing_field_is_keyerror(self):
        data = facts()
        del data["verdict"]
        with self.assertRaises(KeyError):
            prblock.build(data)


class RenderParseTest(unittest.TestCase):
    def test_render_never_contains_comment_close(self):
        hostile = "a --> b <!-- c --> & <script>"
        block = prblock.build(facts(plan=hostile, level_cap_reason="-->"))
        text = prblock.render(block)
        self.assertTrue(text.startswith("<!-- tollgate {"))
        self.assertTrue(text.endswith("} -->"))
        self.assertEqual(text.count("-->"), 1)
        self.assertEqual(text.count("<!--"), 1)
        for ch in "<>&":
            self.assertNotIn(ch, text[len("<!-- tollgate "):-len(" -->")])
        self.assertEqual(prblock.parse(text), block)

    def test_non_ascii_roundtrip(self):
        block = prblock.build(facts(level_cap_reason="così è già qui 日本"))
        self.assertEqual(prblock.parse(prblock.render(block)), block)

    def test_parse_last_block_and_garbage(self):
        first = prblock.render(prblock.build(facts(issue=1)))
        second = prblock.render(prblock.build(facts(issue=2)))
        self.assertEqual(prblock.parse(f"testo\n{first}\naltro\n{second}\n")["issue"], 2)
        self.assertIsNone(prblock.parse(f"{first}\n<!-- tollgate {{rotto -->"))
        self.assertIsNone(prblock.parse("nessun blocco"))
        self.assertIsNone(prblock.parse(f"<!-- tollgate {json.dumps([1, 2])} -->"))
        self.assertIsNone(prblock.parse("<!-- tollgate {\"a\": 1}"))


if __name__ == "__main__":
    unittest.main()
