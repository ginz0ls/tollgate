import json
import unittest

from tollgate_analysis import prblock

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
        "effects": [], "components_off": [], "off_periods": [], "extra": "ignorato"}
    data.update(kw)
    return data


class BuildTest(unittest.TestCase):
    def test_build_has_all_fields_in_order(self):
        block = prblock.build(facts())
        self.assertEqual(list(block), SPEC_ORDER)
        self.assertEqual(list(prblock.FIELDS), SPEC_ORDER)
        self.assertEqual(prblock.SCHEMA_VERSION, 1)
        self.assertNotIn("extra", block)

    def test_new_fields_default_to_empty_lists(self):
        block = prblock.build(facts())
        self.assertEqual((block["tasks_over"], block["skills_absent"]), ([], []))
        block = prblock.build(facts(tasks_over=[{"task": 2, "lines": 300, "size_reason": "x"}],
                                    skills_absent=[{"task": 1, "skills": ["a"]}]))
        self.assertEqual(block["tasks_over"][0]["lines"], 300)
        self.assertEqual(block["skills_absent"], [{"task": 1, "skills": ["a"]}])
        self.assertEqual(prblock.parse(prblock.render(block)), block)

    def test_findings_carry_blocking_field(self):
        finding = {"id": "f-1-1", "severity": "major", "confidence": 0.9,
                   "verification": "confirmed", "user_decision": None, "blocking": False}
        block = prblock.build(facts(findings=[finding]))
        self.assertEqual(prblock.parse(prblock.render(block))["findings"], [finding])

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
