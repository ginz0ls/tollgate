import json
import unittest

from tollgate_analysis import verdicts

SHA, CODE = "abc123", "k1k1k1k1"
GOOD = {"rule": "R-1", "file": "src/app.py", "line": 2, "severity": "major", "text": "manca"}


def verdict(**over):
    data = {"v": 1, "task": 3, "sha": SHA, "code": CODE, "outcome": "approved",
            "spec_compliance": [], "findings": []}
    data.update(over)
    return data


def block(data, before="Ho finito.\n", after=""):
    return f"{before}```json\n{json.dumps(data)}\n```\n{after}"


def parse(text, standard=True):
    return verdicts.parse_task_verdict(text, task=3, sha=SHA, code=CODE, standard=standard)


class ParseTest(unittest.TestCase):
    def test_valid_approved(self):
        v = parse(block(verdict()))
        self.assertTrue(v.valid)
        self.assertEqual((v.outcome, v.declared, v.findings, v.dropped, v.problems),
                         ("approved", "approved", [], 0, []))

    def test_minor_only_changes_becomes_approved_with_standard(self):
        minor = dict(GOOD, severity="minor")
        v = parse(block(verdict(outcome="changes", findings=[minor])))
        self.assertTrue(v.valid)
        self.assertEqual((v.outcome, v.declared), ("approved", "changes"))
        self.assertEqual(v.findings, [minor])

    def test_minor_only_changes_kept_without_standard(self):
        v = parse(block(verdict(outcome="changes", findings=[dict(GOOD, severity="minor")])),
                  standard=False)
        self.assertEqual(v.outcome, "changes")

    def test_blocking_finding_forces_changes_with_standard(self):
        v = parse(block(verdict(outcome="approved", findings=[GOOD])))
        self.assertEqual((v.outcome, v.declared), ("changes", "approved"))

    def test_finding_without_rule_dropped(self):
        bad = {k: v for k, v in GOOD.items() if k != "rule"}
        v = parse(block(verdict(outcome="changes", findings=[bad, GOOD])))
        self.assertEqual((v.findings, v.dropped, v.outcome), ([GOOD], 1, "changes"))

    def test_changes_with_only_dropped_blocking_findings_is_invalid(self):
        """Decisione del controller: un blocker scartato non diventa un approved."""
        for bad in ({k: v for k, v in GOOD.items() if k != "rule"}, dict(GOOD, line="2"),
                    dict(GOOD, severity="critical"), "testo"):
            v = parse(block(verdict(outcome="changes", findings=[bad])))
            self.assertFalse(v.valid, bad)
            self.assertIsNone(v.outcome)
            self.assertIn("rilievo bloccante senza file, riga o regola: riscrivilo",
                          v.problems)
        minor = dict(GOOD, severity="minor")
        v = parse(block(verdict(outcome="changes", findings=[minor, dict(GOOD, rule="")])))
        self.assertFalse(v.valid)

    def test_dropped_minor_finding_does_not_invalidate(self):
        bad_minor = {"severity": "minor", "text": "senza prova"}
        v = parse(block(verdict(outcome="changes", findings=[bad_minor])))
        self.assertEqual((v.valid, v.outcome, v.dropped), (True, "approved", 1))

    def test_dropped_blocker_with_a_valid_blocker_stays_changes(self):
        bad = {k: v for k, v in GOOD.items() if k != "rule"}
        v = parse(block(verdict(outcome="changes", findings=[bad, GOOD])))
        self.assertEqual((v.valid, v.outcome, v.dropped), (True, "changes", 1))

    def test_changes_with_dropped_blocker_kept_without_standard(self):
        bad = {k: v for k, v in GOOD.items() if k != "rule"}
        v = parse(block(verdict(outcome="changes", findings=[bad])), standard=False)
        self.assertEqual((v.valid, v.outcome), (True, "changes"))

    def test_finding_with_bad_severity_or_line_dropped(self):
        for bad in (dict(GOOD, severity="critical"), dict(GOOD, line="2"), dict(GOOD, line=True),
                    dict(GOOD, file=""), "testo"):
            v = parse(block(verdict(findings=[bad])))
            self.assertEqual((v.valid, v.findings, v.dropped), (True, [], 1), bad)

    def test_spec_compliance_forces_changes(self):
        v = parse(block(verdict(spec_compliance=["missing"])))
        self.assertEqual((v.valid, v.outcome), (True, "changes"))

    def test_verdict_validity_matrix(self):
        cases = {
            "sha diverso": block(verdict(sha="altro")),
            "codice diverso": block(verdict(code="altro")),
            "task diverso": block(verdict(task=4)),
            "task non intero": block(verdict(task="3")),
            "json assente": "Tutto a posto, approvo.",
            "testo vuoto": "",
            "json malformato": 'Fine.\n{"outcome": "approved", "task": 3, "sha": ',
            "outcome sconosciuto": block(verdict(outcome="ok")),
            "outcome non stringa": block(verdict(outcome=["approved"])),
            "spec_compliance assente": block({k: v for k, v in verdict().items()
                                              if k != "spec_compliance"}),
            "spec_compliance sconosciuta": block(verdict(spec_compliance=["boh"])),
            "findings non lista": block(verdict(findings="nessuno")),
        }
        for name, text in cases.items():
            with self.subTest(name):
                v = parse(text)
                self.assertFalse(v.valid)
                self.assertIsNone(v.outcome)
                self.assertEqual(v.findings, [])
                self.assertTrue(v.problems)
        self.assertFalse(parse(None).valid)

    def test_invalid_never_approved_even_if_declared(self):
        v = parse(block(verdict(sha="altro", outcome="approved")))
        self.assertEqual((v.valid, v.outcome, v.declared), (False, None, "approved"))

    def test_prose_around_json_is_valid(self):
        v = parse(block(verdict(), before="Ecco il verdetto, con {parentesi} nel testo.\n",
                        after="Fine del messaggio {così}."))
        self.assertTrue(v.valid)

    def test_last_object_wins_over_quoted_example(self):
        example = verdict(sha="di-esempio", outcome="changes")
        text = block(example, before="Il formato è questo:\n") + block(verdict(),
                                                                       before="Il mio:\n")
        self.assertEqual(parse(text).outcome, "approved")
        # al contrario: l'esempio valido citato prima non salva un verdetto finale sbagliato
        text = block(verdict(), before="Prima:\n") + block(verdict(sha="altro"), before="Poi:\n")
        self.assertFalse(parse(text).valid)


if __name__ == "__main__":
    unittest.main()
