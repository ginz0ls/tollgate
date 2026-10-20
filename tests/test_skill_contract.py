"""Il contratto tra le skill e il codice dei sottocomandi (Task 13 di P3c, lezione del Task 16
di P3b): i codici d'uscita e le righe «prossimo passo» che le skill citano vengono dalle
costanti del codice, e un test li confronta. Nessuna riga di una skill resta indietro."""
import re
import unittest

from tests.helpers import ROOT
from tollgate_core import cli
from tollgate_flow import audit, finishcheck, start, sync

# (skill, intestazione della sezione o None per tutto il testo, modulo, nomi delle costanti)
CONTRACTS = (
    ("start", "## 1. Avvio", start, ("OK", "REFUSED", "NEEDS_CONFIRM", "INCOMPLETE")),
    ("finish", "## 1. Worktree pulito", finishcheck, ("OK", "RED", "REFUSED")),
    ("sync", None, sync, ("OK", "REFUSED", "BLOCKED", "REVIEW_NEEDED")),
    ("spec-audit", "## Codici d'uscita", audit, ("OK", "REFUSED", "NEEDS_CONFIRM")),
)
CODE_LINE = re.compile(r"(?m)^- \*\*(\d+)\b")
PROGRAM_CALL = re.compile(r"<programma> ([a-z][a-z-]*)(?: ([a-z][a-z-]*))?")


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


def section(text: str, heading: str | None) -> str:
    if heading is None:
        return text
    start_at = text.index(heading)
    end = re.search(r"(?m)^## ", text[start_at + len(heading):])
    return text[start_at:] if end is None else text[start_at:start_at + len(heading) + end.start()]


def squash(text: str) -> str:
    return " ".join(text.split())


class SkillContractTest(unittest.TestCase):
    def test_exit_codes_match_constants(self):
        for name, heading, module, constants in CONTRACTS:
            with self.subTest(skill=name):
                documented = {int(n) for n in CODE_LINE.findall(section(skill_text(name),
                                                                         heading))}
                self.assertEqual(documented, {getattr(module, c) for c in constants})

    def test_audit_steps_fixed_part_in_spec_audit_skill(self):
        text = squash(skill_text("spec-audit"))
        for key, step in (*audit.STEPS.items(), ("confirm", audit.CONFIRM_STEP)):
            fixed = squash(step.partition("<")[0])
            self.assertTrue(fixed)
            with self.subTest(step=key):
                self.assertIn(fixed, text)
        self.assertIn("<id>", skill_text("spec-audit"))

    def test_program_subcommands_exist_in_parser(self):
        parser = cli.build_parser()
        top = next(a for a in parser._actions if a.dest == "cmd").choices
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            for first, second in PROGRAM_CALL.findall(path.read_text()):
                with self.subTest(skill=path.parent.name, call=f"{first} {second}".strip()):
                    self.assertIn(first, top)
                    nested = next((a for a in top[first]._actions
                                   if getattr(a, "choices", None) and a.dest != "help"), None)
                    if nested is not None and second:
                        self.assertIn(second, nested.choices)

    def test_no_skill_mentions_plan_numbers(self):
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                self.assertNotIn("P3c", path.read_text())


if __name__ == "__main__":
    unittest.main()
