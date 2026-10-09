import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import report

GOOD = {"v": 1, "task": 2, "status": "DONE", "done": "fatto", "tests": "verify green",
        "files": ["src/a.py"], "must_have": ["M1"], "concerns": "", "left": "",
        "size_reason": None}
SAMPLES = json.loads((ROOT / "spikes/fixtures/hook-inputs/samples.json").read_text())


class ReportTest(unittest.TestCase):
    def test_last_json_block(self):
        text = "Ecco il lavoro.\n```json\n" + json.dumps(GOOD) + "\n```\n"
        r = report.parse_report(text)
        self.assertTrue(r.valid)
        self.assertEqual(r.status, "DONE")
        r = report.parse_report("prima {\"a\": 1} poi " + json.dumps(GOOD))
        self.assertTrue(r.valid)

    def test_missing_fields(self):
        bad = dict(GOOD)
        del bad["left"], bad["concerns"]
        r = report.parse_report(json.dumps(bad))
        self.assertFalse(r.valid)
        self.assertEqual(r.missing, ["concerns", "left"])
        self.assertFalse(report.parse_report("nessun json").valid)
        self.assertFalse(report.parse_report(None).valid)

    def test_unknown_status_counts_as_done(self):
        r = report.parse_report(json.dumps(dict(GOOD, status="FINITO")))
        self.assertEqual((r.status, r.unknown_status, r.valid), ("DONE", True, True))

    def test_turn_cut_from_real_sample(self):
        cut = SAMPLES["PostToolUse-Agent-maxturns-cut"]["tool_response"]
        normal = SAMPLES["PostToolUse-Agent-foreground-manual"]["tool_response"]
        self.assertTrue(report.is_turn_cut(cut))
        self.assertFalse(report.is_turn_cut(normal))
        fake = dict(normal, content=[{"type": "text",
                                      "text": "NOTE: this agent stopped at its 2-turn limit"}])
        self.assertFalse(report.is_turn_cut(fake))

    def test_transcript_tokens(self):
        lines = [
            {"type": "assistant", "message": {"id": "m1", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 1000, "output_tokens": 3}}},
            {"type": "assistant", "message": {"id": "m1", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 1000, "output_tokens": 3}}},
            {"type": "user", "message": {"content": "x"}},
            "riga non json",
            {"type": "assistant", "message": {"id": "m2", "usage": {"input_tokens": 1,
                                                                     "output_tokens": 1}}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for l in lines:
                f.write((l if isinstance(l, str) else json.dumps(l)) + "\n")
        try:
            self.assertEqual(report.transcript_tokens(f.name), 20)
        finally:
            Path(f.name).unlink()
        self.assertEqual(report.transcript_tokens("/non/esiste.jsonl"), 0)


if __name__ == "__main__":
    unittest.main()
