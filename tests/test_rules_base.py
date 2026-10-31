"""La skill `rules-base` (B2, Task 3): la bozza delle regole di base, ognuna con la sua fonte.
`rules()` è riusata dai test dell'approvazione (Task 4 e 5)."""
import re
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import research

SKILL = ROOT / "skills" / "rules-base" / "SKILL.md"
PAGE = ROOT / "docs" / "profili" / "base.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "base-fonti.md"
DESCRIPTION = ("Regole di base di tollgate per ogni implementatore e revisore: le caricano in "
               "automatico gli agenti di tollgate, non serve invocarla.")
RULE = re.compile(r"^(R-BASE-\d{2})( \[blocca\])? (\S.*)$")


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    lines = text.split("\n")
    assert lines[0] == "---"
    end = lines.index("---", 1)
    return dict(line.split(": ", 1) for line in lines[1:end] if ": " in line)


def rules(text: str) -> list[tuple[str, bool, str, str]]:
    """Le regole della pagina: (id, blocca, testo, fonte). La fonte è la riga `Fonte: …` che
    segue la regola, prima della regola successiva o del titolo successivo; vuota se manca."""
    found: list[list] = []
    open_rule = False
    for line in text.split("\n"):
        m = RULE.match(line)
        if m:
            found.append([m.group(1), bool(m.group(2)), m.group(3).strip(), ""])
            open_rule = True
        elif line.startswith("#"):
            open_rule = False
        elif open_rule and not found[-1][3] and line.startswith("Fonte:"):
            found[-1][3] = line[len("Fonte:"):].strip()
    return [tuple(r) for r in found]


class RulesBaseTest(unittest.TestCase):
    def test_frontmatter(self):
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-base")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertNotIn("approved", fm)
        self.assertFalse(research.enforced(text))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole di base (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertEqual(titles[0], "## Prima di scrivere")
        self.assertIn("## Mentre lavori", titles)
        self.assertIn("## Fonti", titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if RULE.match(l)]
        self.assertTrue(ids)
        self.assertEqual(ids, [f"R-BASE-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in rules(skill_text())], ids)

    def test_every_rule_has_a_source(self):
        for rid, _blocca, text, source in rules(skill_text()):
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_some_rules_block(self):
        flags = [r[1] for r in rules(skill_text())]
        self.assertTrue(any(flags))
        self.assertFalse(all(flags))

    def test_model_name_rule(self):
        hits = [r for r in rules(skill_text())
                if "nome" in r[2] and "modell" in r[2] and "ufficiale" in r[2]
                and "fornitore" in r[2]]
        self.assertEqual(len(hits), 1)

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_licenses_listed(self):
        mit = (ROOT / "LICENSES" / "agent-skills-MIT.txt").read_text(encoding="utf-8")
        self.assertTrue(mit.startswith("MIT License"))
        self.assertIn("Addy Osmani", mit)
        fonti = skill_text().split("\n## Fonti", 1)[1]
        self.assertIn("LICENSES/agent-skills-MIT.txt", fonti)
        self.assertIn("LICENSES/superpowers-MIT.txt", fonti)


ID = re.compile(r"R-BASE-\d{2}")


def table_rows(text: str) -> list[list[str]]:
    """Le righe di dati delle tabelle: le celle senza spazi ai bordi; intestazioni e filetti esclusi."""
    rows = []
    for line in text.split("\n"):
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:] if rows else rows


class RulesBasePageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (B2, Task 4)."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in rules(skill_text())]

    def test_sources_report_covers_every_rule(self):
        text = SOURCES.read_text(encoding="utf-8")
        main, _, removed = text.partition("\n## Regole tolte")
        self.assertTrue(removed, "manca la sezione «Regole tolte»")
        self.assertFalse(ID.search(removed), "le regole tolte non usano id R-BASE-")
        ok, named = set(), set()
        for cells in table_rows(main):
            found = ID.findall(cells[0])
            named.update(found)
            if cells[-1].split(":")[0].strip() == "ok":
                ok.update(found)
        self.assertEqual(named - set(self.skill_ids()), set())
        self.assertEqual(set(self.skill_ids()) - ok, set())

    def test_page_lists_every_rule(self):
        ids = [ID.search(cells[0]).group(0) for cells in table_rows(PAGE.read_text(encoding="utf-8"))
               if ID.search(cells[0])]
        self.assertEqual(ids, self.skill_ids())

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in rules(skill_text())}
        seen = {}
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            m = ID.search(cells[0])
            if m:
                self.assertIn(cells[2].lower(), ("sì", "no"))
                seen[m.group(0)] = cells[2].lower() == "sì"
        self.assertEqual(seen, blocca)

    def test_page_explains_what_changes(self):
        text = " ".join(PAGE.read_text(encoding="utf-8").split()).lower()
        for needle in ("in l1 e l2 la prima modifica senza una nota valida viene rifiutata",
                       "in l0 resta il solo avviso",
                       "anche nei lavori già in corso e nei task già avvisati",
                       "nei lavori veri vale da quando la nuova versione, una volta unita al ramo principale (main), viene installata sul tuo computer"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
