import json
import tempfile
import time
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

    def test_unknown_status_is_invalid(self):
        # Fail-closed (spec 18.5): uno stato fuori dai quattro valori rende il report non valido.
        r = report.parse_report(json.dumps(dict(GOOD, status="FINITO")))
        self.assertEqual((r.unknown_status, r.valid), (True, False))

    def test_status_is_normalized(self):
        r = report.parse_report(json.dumps(dict(GOOD, status=" blocked ")))
        self.assertEqual((r.status, r.unknown_status, r.valid), ("BLOCKED", False, True))

    def test_prefers_object_with_all_required_fields(self):
        text = json.dumps(dict(GOOD, extra={"status": "BLOCKED"}))
        r = report.parse_report(text)
        self.assertEqual((r.status, r.valid), ("DONE", True))

    def test_turn_cut_requires_int_count_and_prefix(self):
        cut = SAMPLES["PostToolUse-Agent-maxturns-cut"]["tool_response"]
        other = dict(cut, content=[{"type": "text", "text": "questo è altro"}])
        self.assertFalse(report.is_turn_cut(other))
        self.assertFalse(report.is_turn_cut(dict(cut, harnessNoteCount=True)))

    def test_turn_cut_from_real_sample(self):
        cut = SAMPLES["PostToolUse-Agent-maxturns-cut"]["tool_response"]
        normal = SAMPLES["PostToolUse-Agent-foreground-manual"]["tool_response"]
        self.assertTrue(report.is_turn_cut(cut))
        self.assertFalse(report.is_turn_cut(normal))
        fake = dict(normal, content=[{"type": "text",
                                      "text": "NOTE: this agent stopped at its 2-turn limit"}])
        self.assertFalse(report.is_turn_cut(fake))

    def test_new_tokens_leaves_cache_read_out(self):
        use = {"input": 1, "cache_creation": 2, "cache_read": 1000, "output": 4}
        self.assertEqual(report.new_tokens(use), 7)

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

    def test_transcript_usage_by_model(self):
        def use(i, o, cc, cr):
            return {"input_tokens": i, "output_tokens": o, "cache_creation_input_tokens": cc,
                    "cache_read_input_tokens": cr}
        lines = [
            {"type": "assistant", "message": {"id": "m1", "model": "claude-sonnet-5-5",
                                              "usage": use(10, 3, 5, 1000)}},
            {"type": "assistant", "message": {"id": "m1", "model": "claude-sonnet-5-5",
                                              "usage": use(10, 3, 5, 1000)}},
            {"type": "assistant", "message": {"id": "m2", "model": "claude-sonnet-5-5",
                                              "usage": use(1, 1, 0, 7)}},
            {"type": "assistant", "message": {"id": "m3", "usage": use(2, 2, 2, 2)}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for l in lines:
                f.write(json.dumps(l) + "\n")
        self.addCleanup(Path(f.name).unlink)
        got = report.transcript_usage(f.name)
        self.assertEqual(set(got), {"claude-sonnet-5-5", "sconosciuto"})
        self.assertEqual(got["claude-sonnet-5-5"], {"input": 11, "cache_creation": 5,
                                                     "cache_read": 1007, "output": 4})
        self.assertEqual(got["sconosciuto"], {"input": 2, "cache_creation": 2, "cache_read": 2,
                                              "output": 2})
        total = sum(u["input"] + u["cache_creation"] + u["output"] for u in got.values())
        self.assertEqual(total, report.transcript_tokens(f.name))

    def test_transcript_usage_missing_file(self):
        self.assertEqual(report.transcript_usage("/non/esiste.jsonl"), {})

    def test_transcript_tokens_skips_malformed_usage(self):
        raw = [
            '{"type":"assistant","message":{"id":"m3","usage":{"input_tokens":"abc",'
            '"output_tokens":[1],"cache_creation_input_tokens":1e999,"x":true}}}',
            '{"type":"assistant","message":{"id":"m4","usage":{"input_tokens":2,'
            '"output_tokens":true}}}',
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write("\n".join(raw) + "\n")
        try:
            self.assertEqual(report.transcript_tokens(f.name), 2)
        finally:
            Path(f.name).unlink()

    def test_json_candidates_capped(self):
        good = json.dumps(GOOD)
        t0 = time.monotonic()
        found = report.json_candidates("{" * 200000 + good, "status")
        self.assertLess(time.monotonic() - t0, 1.0)
        self.assertEqual(found, [GOOD])
        self.assertEqual(report.json_candidates(good + "x" * 70000, "status"), [])


if __name__ == "__main__":
    unittest.main()
