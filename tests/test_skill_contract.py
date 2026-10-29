"""Il contratto tra le skill e il codice dei sottocomandi (Task 13 di P3c, lezione del Task 16
di P3b): i codici d'uscita e le righe «prossimo passo» che le skill citano vengono dalle
costanti del codice, e un test li confronta. Nessuna riga di una skill resta indietro."""
import re
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_core import cli, db
from tollgate_flow import audit, finishcheck, start, sync
from tollgate_flow import init as flow_init
from tollgate_gate import attention, install
from tollgate_gate import cli as gate_cli

# (skill, intestazione della sezione o None per tutto il testo, modulo, nomi delle costanti)
CONTRACTS = (
    ("start", "## 1. Avvio", start, ("OK", "REFUSED", "NEEDS_CONFIRM", "INCOMPLETE")),
    ("finish", "## 1. Worktree pulito", finishcheck, ("OK", "RED", "REFUSED")),
    ("sync", None, sync, ("OK", "REFUSED", "BLOCKED", "REVIEW_NEEDED")),
    ("spec-audit", "## Codici d'uscita", audit, ("OK", "REFUSED", "NEEDS_CONFIRM")),
    ("init", "## Codici d'uscita", flow_init, ("OK", "REFUSED")),
)
CODE_LINE = re.compile(r"(?m)^- \*\*(\d+)\b")
CODE_LABEL = re.compile(r"(?m)^- \*\*(\d+), ([^*]*)\*\*")
# Il significato abbinato a ogni codice: la parola che la riga della skill deve contenere.
MEANING = {
    "start": {"OK": "fatto", "REFUSED": "rifiuto", "NEEDS_CONFIRM": "conferma",
              "INCOMPLETE": "incompleta"},
    "finish": {"OK": "verde", "RED": "rosso", "REFUSED": "rifiuto"},
    "sync": {"OK": "riallineato", "REFUSED": "rifiuto", "BLOCKED": "needs_you",
             "REVIEW_NEEDED": "revisione"},
    "spec-audit": {"OK": "avanti", "REFUSED": "rifiuto", "NEEDS_CONFIRM": "conferma"},
    "init": {"OK": "proposta", "REFUSED": "rifiuto"},
}
NOT_TOLLGATE_OPTIONS = {"--force"}      # `git worktree remove --force`, citato per vietarlo
PROGRAM_CALL = re.compile(r"<programma> ([a-z][a-z-]*)(?: ([a-z][a-z-]*))?")


def _subparsers(parser) -> dict:
    return next((a.choices for a in parser._actions
                 if isinstance(getattr(a, "choices", None), dict) and a.dest != "help"), {})


def _options(parser) -> set[str]:
    found = set()
    for action in parser._actions:
        found.update(o for o in action.option_strings if o.startswith("--"))
        for sub in (action.choices.values() if isinstance(getattr(action, "choices", None), dict)
                    else ()):
            found |= _options(sub)
    return found


def call_problems(text: str) -> list[str]:
    """I sottocomandi e le opzioni di `text` che il parser non conosce (decisione 18a): le righe
    con `<programma> gate …` si verificano contro `tollgate_gate.cli.build_parser()`, le altre
    contro `tollgate_core.cli.build_parser()`."""
    core, gate = cli.build_parser(), gate_cli.build_parser()
    top, gate_top = _subparsers(core), _subparsers(gate)
    problems = []
    for line in text.splitlines():
        calls = PROGRAM_CALL.findall(line)
        on_gate = any(first == "gate" for first, _ in calls)
        for first, second in calls:
            if first == "gate":
                if second not in gate_top:
                    problems.append(f"sottocomando gate sconosciuto: {second!r}")
                continue
            if first not in top:
                problems.append(f"sottocomando sconosciuto: {first!r}")
                continue
            nested = _subparsers(top[first])
            if nested and second and second not in nested:
                problems.append(f"sottocomando sconosciuto: {first} {second!r}")
        known = _options(gate if on_gate else core)
        for opt in set(re.findall(r"(?<![\w-])(--[a-z][a-z-]+)", line)):
            if opt not in known and opt not in NOT_TOLLGATE_OPTIONS:
                problems.append(f"opzione sconosciuta: {opt}")
    return problems


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

    def test_exit_codes_keep_their_meaning(self):
        for name, heading, module, constants in CONTRACTS:
            labels = {int(n): label for n, label in
                      CODE_LABEL.findall(section(skill_text(name), heading))}
            for const in constants:
                with self.subTest(skill=name, const=const):
                    self.assertIn(MEANING[name][const], labels[getattr(module, const)])

    def test_audit_steps_fixed_part_in_spec_audit_skill(self):
        text = squash(skill_text("spec-audit"))
        for key, step in (*audit.STEPS.items(), ("confirm", audit.CONFIRM_STEP)):
            fixed = squash(step.partition("<")[0])
            self.assertTrue(fixed)
            with self.subTest(step=key):
                self.assertIn(fixed, text)
        fixed = squash(audit.STEPS["resolve"].partition("<")[0])
        self.assertIn(fixed + " `<id>`", text)

    def test_setup_proposes_web_permissions(self):
        text = squash(skill_text("setup"))
        for word in ("permissions.allow", "WebFetch", "WebSearch"):
            self.assertIn(word, text)
        self.assertRegex(text, r"le regole le aggiunge l'utente da sé")
        self.assertNotRegex(text, r"(?i)\bsono gratis\b.*non scrivono niente")

    def test_setup_proposes_domain_rules_first_in_the_project(self):
        text = squash(skill_text("setup"))
        by_domain, bare = text.index("WebFetch(domain:"), text.index('"WebFetch"')
        self.assertLess(by_domain, bare)
        self.assertIn(".claude/settings.json` del progetto", text)

    def test_setup_says_the_risk_of_a_free_webfetch(self):
        text = squash(skill_text("setup"))
        self.assertRegex(text, r"un `WebFetch` libero può portare dati fuori nell'URL")
        self.assertIn("tollgate non controlla `WebFetch`", text)
        # il permesso globale resta una scelta dell'utente, con il rischio scritto prima
        self.assertLess(text.index("può portare dati fuori"), text.index('"WebFetch"'))
        self.assertRegex(text, r"(?i)scelta dell'utente")

    def test_caps_section_says_resolve_always_suspends(self):
        text = squash(section(skill_text("spec-audit"), "## I tetti"))
        self.assertIn("In entrambi i casi il `resolve` sospende; per l'audit a lenti la "
                      "sospensione è definitiva", text)

    def test_program_subcommands_exist_in_parser(self):
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                self.assertEqual(
                    [p for p in call_problems(path.read_text()) if "sottocomando" in p], [])

    def test_options_exist_in_parser(self):
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                self.assertEqual(
                    [p for p in call_problems(path.read_text()) if "opzione" in p], [])

    def test_call_check_handles_gate_and_core_calls(self):
        """Il controllo D18a è lo stesso del test reale: `gate` si verifica contro il parser del
        gate, il resto contro quello del nucleo, e un nome inventato viene trovato."""
        self.assertEqual(call_problems(
            "<programma> gate sentinel --event f --publish\n<programma> init --propose "
            "--merges-per-month 3\n<programma> task start --from-gate"), [])
        self.assertEqual(len(call_problems("<programma> gate inventato")), 1)
        self.assertEqual(len(call_problems("<programma> gate sentinel --propose")), 1)
        self.assertEqual(len(call_problems("<programma> init --event f")), 1)
        self.assertEqual(len(call_problems("<programma> inventato")), 1)
        self.assertEqual(len(call_problems("<programma> task inventato")), 1)

    def test_lens_brief_method_file_exists(self):
        """Il percorso di `dimensioni.md` che `audit prepare` scrive nel brief (stessa derivazione
        di `audit._write_brief`) è un file del repo, e accanto c'è `verifica-fatti.md`."""
        method = (Path(db.BIN_PATH).parent.parent / "skills" / "spec-audit" / "references"
                  / "dimensioni.md")
        self.assertEqual(method.resolve(),
                         (ROOT / "skills/spec-audit/references/dimensioni.md").resolve())
        self.assertTrue(method.is_file())
        self.assertTrue((method.parent / "verifica-fatti.md").is_file())

    def test_no_skill_mentions_plan_numbers(self):
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                self.assertNotIn("P3c", path.read_text())
                self.assertIsNone(re.search(r"\bP[0-9][a-z]?\b", path.read_text()))

    def test_finish_separates_attention_lines_from_dod_lines(self):
        """Le righe di `attenzione` («da leggere:», «informative:») non sono voci `[sì]`/`[no]`
        (decisione 21b): la skill le nomina con il prefisso che il codice stampa."""
        text = squash(skill_text("finish"))
        for needle in ("`da leggere:`", "`informative:`", "`[sì]`", "`[no]`", "`rosso:`"):
            self.assertIn(needle, text)
        self.assertIn("Non sono voci `[no]`", text)
        code = Path(finishcheck.__file__).read_text()
        for prefix in ("da leggere", "informative"):
            self.assertIn(f'"{prefix}', code)

    def test_finish_attention_groups_match_the_code(self):
        """Le chiavi di ciascun gruppo nella skill sono quelle di `attention.GROUPS`."""
        text = skill_text("finish")
        for label, group in (("da leggere:", attention.READ), ("informative:", attention.INFO)):
            line = next(x for x in text.splitlines()
                        if x.lstrip().startswith(f"- **Righe `{label}`"))
            with self.subTest(group=label):
                self.assertEqual(set(re.findall(r"`([a-z_]+)`", line.split("**", 2)[2])),
                                 {k for k, v in attention.GROUPS.items() if v == group})

    def test_init_services_in_every_job_that_runs_the_suite(self):
        """Il testo dei servizi nomina tutti i job con un segnaposto (`install.SERVICES_WORKFLOWS`):
        due in `tollgate-run` e uno in `tollgate-base`."""
        self.assertEqual(install.SERVICES_WORKFLOWS, {"run": 2, "base": 1})
        for text in (skill_text("init"), Path(flow_init.__file__).read_text()):
            flat = squash(text).replace('" "', "")
            for needle in ("`head` e `base` di `tollgate-run`", "`ids` di `tollgate-base`"):
                with self.subTest(needle=needle):
                    self.assertIn(needle, flat)

    def test_init_skill_never_copies_or_protects(self):
        text = squash(skill_text("init"))
        for needle in ("--propose", "--update", "--merges-per-month", "--service",
                       "mai copiare i file al posto dell'utente", "mai lanciare `protect.sh`",
                       "non determinata", "tollgate-config/"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
