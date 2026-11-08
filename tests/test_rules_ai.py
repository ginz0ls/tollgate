"""La skill `rules-ai` (B3, Task 5): la bozza delle regole del profilo `ai`, ognuna con la sua fonte,
e il frammento `templates/profiles/ai.toml`. `rules()` è riusata dai test dei Task 6 e 7."""
import re
import tomllib
import unittest

from tests.helpers import ROOT
from tests.test_rules_base import table_rows
from tollgate_analysis import research
from tollgate_core import fragments

SKILL = ROOT / "skills" / "rules-ai" / "SKILL.md"
FRAGMENT = ROOT / "templates" / "profiles" / "ai.toml"
PAGE = ROOT / "docs" / "profili" / "ai.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "ai-fonti.md"
ID = re.compile(r"R-AI-\d{2}")
DESCRIPTION = ("Regole di tollgate per il codice che usa modelli AI: le caricano in automatico "
               "gli agenti dell'area ai, non serve invocarla.")
RULE = re.compile(r"^(R-AI-\d{2})( \[blocca\])? (\S.*)$")
JUDGED = re.compile(r"^Si giudica su: (diff|report|nota)$")
USER_CHOICES_SOURCE = "progetto di B, sezione 9"

# Le scelte dell'utente del progetto di B, sezione 9, e la regola che ciascuna diventa.
# Si cerca per id, non per parole (rinvio 182 del piano principale).
USER_CHOICES = {
    "il nome del modello sta in un solo punto": "R-AI-01",
    "accanto al nome, l'indirizzo della pagina ufficiale e la data della verifica": "R-AI-02",
    "si usa l'ultimo modello della famiglia, stabile": "R-AI-03",
    "un modello in anteprima solo dichiarato con il motivo": "R-AI-04",
    "prima di cambiare modello si leggono le note di migrazione": "R-AI-05",
    "errore chiaro quando un modello non è più disponibile": "R-AI-07",
    "un alias che cambia da solo solo se il report lo dichiara": "R-AI-08",
}

# Le pagine ufficiali che la sezione «Fonti» deve nominare, per fornitore (decisione 13).
OFFICIAL_SOURCES = {
    "Anthropic": "https://platform.claude.com/docs/",
    "Google": "https://ai.google.dev/",
    "OpenAI": "https://developers.openai.com/",
    "OpenRouter": "https://openrouter.ai/docs/",
    "Agno": "https://docs.agno.com/",
    "Supabase": "https://supabase.com/docs/",
}

# `bin/tollgate_analysis/bash.py` contiene questo pacchetto (decisione D11 del controller).
CLAUDE_CODE_PACKAGE = "@anthropic-ai/claude-code"
BARE_VENDOR_NAMES = {"anthropic", "claude", "openai", "gpt", "google", "gemini", "openrouter",
                     "agno", "supabase", "genai", "llm", "ai"}


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    lines = text.split("\n")
    assert lines[0] == "---"
    end = lines.index("---", 1)
    return dict(line.split(": ", 1) for line in lines[1:end] if ": " in line)


def rules(text: str, area: str = "ai") -> list[tuple[str, bool, str, str, str]]:
    """Le regole della pagina dell'area: (id, blocca, testo, fonte, oggetto). La fonte è la riga
    `Fonte: …` e l'oggetto la riga `Si giudica su: diff|report|nota` che seguono la regola,
    prima della regola successiva o del titolo successivo; vuoti se mancano."""
    rule = re.compile(rf"^(R-{area.upper()}-\d{{2}})( \[blocca\])? (\S.*)$")
    found: list[list] = []
    open_rule = False
    for line in text.split("\n"):
        m = rule.match(line)
        if m:
            found.append([m.group(1), bool(m.group(2)), m.group(3).strip(), "", ""])
            open_rule = True
        elif line.startswith("#"):
            open_rule = False
        elif open_rule:
            if not found[-1][3] and line.startswith("Fonte:"):
                found[-1][3] = line[len("Fonte:"):].strip()
            judged = JUDGED.match(line)
            if judged and not found[-1][4]:
                found[-1][4] = judged.group(1)
    return [tuple(r) for r in found]


def fragment() -> dict:
    return tomllib.loads(FRAGMENT.read_text(encoding="utf-8"))


class RulesAiTest(unittest.TestCase):
    def test_frontmatter(self):
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-ai")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertEqual(fm["approved"], "2026-11-02")
        self.assertTrue(research.enforced(text))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole ai (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertEqual(titles[0], "## Prima di scrivere")
        for title in ("## Mentre lavori", "## Dove informarsi", "## Fonti"):
            self.assertIn(title, titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if RULE.match(l)]
        self.assertTrue(ids)
        self.assertEqual(ids, [f"R-AI-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in rules(skill_text())], ids)

    def test_area_rules_of_research_match_rules(self):
        parsed = rules(skill_text())
        self.assertEqual(research.area_rules(skill_text(), "ai"),
                         ({r[0] for r in parsed}, {r[0] for r in parsed if r[1]}))

    def test_every_rule_has_a_source(self):
        for rid, _blocca, text, source, _judged in rules(skill_text()):
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_every_rule_names_what_is_judged(self):
        for rid, *_rest, judged in rules(skill_text()):
            with self.subTest(rule=rid):
                self.assertIn(judged, ("diff", "report", "nota"),
                              "manca la riga «Si giudica su: diff|report|nota»")

    def test_some_rules_block(self):
        flags = [r[1] for r in rules(skill_text())]
        self.assertTrue(any(flags))
        self.assertFalse(all(flags))

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_blocking_rules_judged_on_diff_or_report(self):
        """Nei lavori senza passo la nota non c'è (Review Focus 3): una regola che blocca non
        si può giudicare solo sulla nota."""
        for rid, blocca, _text, _source, judged in rules(skill_text()):
            if blocca:
                with self.subTest(rule=rid):
                    self.assertIn(judged, ("diff", "report"))

    def test_user_choices_covered(self):
        by_id = {r[0]: r for r in rules(skill_text())}
        for choice, rid in USER_CHOICES.items():
            with self.subTest(choice=choice):
                self.assertIn(rid, by_id)
                self.assertIn(USER_CHOICES_SOURCE, by_id[rid][3])
        self.assertEqual(len(set(USER_CHOICES.values())), len(USER_CHOICES))

    def test_every_rule_names_a_page_or_the_user_choice(self):
        for rid, _b, _t, source, _j in rules(skill_text()):
            with self.subTest(rule=rid):
                self.assertTrue(USER_CHOICES_SOURCE in source or "https://" in source)

    def test_sources_section(self):
        fonti = skill_text().split("\n## Fonti", 1)[1]
        for vendor, url in OFFICIAL_SOURCES.items():
            with self.subTest(vendor=vendor):
                self.assertIn(vendor, fonti)
                self.assertIn(url, fonti)
        flat = " ".join(fonti.split()).lower()
        self.assertIn("con parole nostre", flat)
        self.assertIn("senza testo copiato", flat)

    def test_where_to_look_names_claude_api_skill(self):
        informarsi = skill_text().split("\n## Dove informarsi", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`claude-api`", informarsi)
        for url in OFFICIAL_SOURCES.values():
            if "supabase" not in url:
                self.assertIn(url, informarsi)

    def test_no_long_quotations(self):
        """Le copie delle fonti non sono nel repo: il controllo del testo copiato è del Task 6.
        Qui si controlla solo che la skill non porti citazioni lunghe tra virgolette."""
        for line in skill_text().split("\n"):
            for quoted in re.findall(r"«([^»]*)»", line):
                with self.subTest(quoted=quoted[:40]):
                    self.assertLessEqual(len(quoted.split()), 12)

    def test_fragment_matches_decisions(self):
        data = fragment()
        self.assertEqual(set(data), {"profile", "detect"})
        profile = data["profile"]
        self.assertEqual(profile["kind"], "vertical")
        self.assertEqual(profile["min_level"], "L1")
        self.assertEqual(profile["paths"],
                         ["**/llm/**", "**/prompts/**", "**/agents/**", "**/ai/**"])
        self.assertEqual(profile["skills"], [])
        self.assertEqual(profile["reviewer_skills"], [])
        self.assertEqual(profile["agent"], "tollgate:implementer-ai")
        self.assertEqual(profile["reviewer"], "tollgate:reviewer-ai")
        self.assertEqual(profile["dod"], [])
        self.assertNotIn("rules", profile)
        self.assertNotIn("blocking_rules", profile)
        self.assertNotIn("final_specialist", profile)
        content = data["detect"]["content"]
        self.assertTrue(content)
        self.assertEqual(len(content), len(set(content)))

    def test_markers_are_pieces_of_lines_not_vendor_names(self):
        for marker in fragment()["detect"]["content"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), BARE_VENDOR_NAMES)
                self.assertRegex(marker, r"[^a-z]", "il solo nome di un fornitore")
                self.assertEqual(marker, marker.strip())
                self.assertNotIn(marker, CLAUDE_CODE_PACKAGE, "pezzo del pacchetto di claude-code")

    def test_markers_cover_every_vendor_of_decision_13(self):
        content = " ".join(fragment()["detect"]["content"])
        for needle in ("anthropic", "genai", "openai", "openrouter", "agno"):
            with self.subTest(vendor=needle):
                self.assertIn(needle, content)

    def test_fragment_loads_through_the_loader(self):
        (found,) = [f for f in fragments.load(ROOT) if f.area == "ai"]
        self.assertEqual(found.source, FRAGMENT)
        self.assertEqual(found.skill_path, SKILL)
        self.assertEqual(found.detect, tuple(fragment()["detect"]["content"]))


class RulesAiPageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (B3, Task 6). Si cercano gli id e i
    nomi, non le frasi (rinvio 182 del piano principale)."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in rules(skill_text())]

    def skip_if_approved(self):
        if "approved" in frontmatter(skill_text()):
            self.skipTest("la skill è approvata: la pagina non è più una proposta")

    def sources_main(self) -> str:
        main, _, removed = SOURCES.read_text(encoding="utf-8").partition("\n## Regole tolte")
        self.assertTrue(removed, "manca la sezione «Regole tolte»")
        return main

    def test_sources_report_covers_every_rule(self):
        ok, named = set(), set()
        for cells in table_rows(self.sources_main()):
            found = ID.findall(cells[0])
            named.update(found)
            if cells[-1].split(":")[0].strip().startswith("ok"):
                ok.update(found)
        self.assertEqual(named - set(self.skill_ids()), set())
        self.assertEqual(set(self.skill_ids()) - ok, set())

    def test_removed_sources_are_not_in_the_skill(self):
        """Ogni riga `no` del rapporto è una fonte uscita: la regola resta coperta da una riga
        `ok` e la skill non la usa più come base (R-AI-06 non rimanda più a R-BASE-04)."""
        sources = {r[0]: r[3] for r in rules(skill_text())}
        self.assertNotIn("R-BASE-04", sources["R-AI-06"])
        rows = table_rows(self.sources_main())
        for cells in rows:
            if ID.fullmatch(cells[0]) and cells[-1].split(":")[0].strip() == "no":
                rid = cells[0]
                with self.subTest(rule=rid, source=cells[1][:40]):
                    self.assertIn(rid, sources)
                    self.assertTrue(any(c[0] == rid and c[-1].split(":")[0].strip().startswith("ok")
                                        for c in rows), "la regola non ha più una fonte ok")
                    for base in re.findall(r"R-BASE-\d{2}", cells[1]):
                        self.assertNotIn(f"segue {base}", sources[rid])
        for cells in rows:
            self.assertNotIn("**", cells[-1], "l'esito si scrive senza grassetto")

    def test_tables_have_one_header(self):
        """Un'intestazione o un filetto ripetuti si leggerebbero come righe di dati."""
        for path in (SOURCES, PAGE):
            tables, current = [], []
            for line in path.read_text(encoding="utf-8").split("\n"):
                if line.startswith("|"):
                    current.append(line)
                elif current:
                    tables.append(current)
                    current = []
            if current:
                tables.append(current)
            for table in tables:
                with self.subTest(file=path.name, header=table[0][:40]):
                    self.assertRegex(table[1], r"^\|[\s:|-]+\|$")
                    for line in table[2:]:
                        self.assertNotRegex(line, r"^\|[\s:|-]+\|$")
                        self.assertNotEqual(line, table[0])

    def test_detect_markers_verified(self):
        ok = set()
        for cells in table_rows(self.sources_main()):
            m = re.fullmatch(r"`(.+)`", cells[0])
            if m and cells[-1].split(":")[0].strip().startswith("ok"):
                ok.add(m.group(1))
        markers = set(fragment()["detect"]["content"])
        self.assertEqual(markers - ok, set())
        self.assertEqual(ok - markers, set(), "il rapporto verifica un marcatore che non c'è più")

    def test_real_markers_not_in_tollgate_bin(self):
        """Ogni progetto riceve `bin/` in `.github/tollgate/`: se vi comparisse un marcatore,
        `init` accenderebbe il profilo dappertutto."""
        markers = fragment()["detect"]["content"]
        files = [p for p in (ROOT / "bin").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        self.assertTrue(files)
        for path in files:
            text = path.read_bytes().decode("utf-8", errors="ignore")
            for marker in markers:
                with self.subTest(file=str(path.relative_to(ROOT)), marker=marker):
                    self.assertNotIn(marker, text)

    def test_page_lists_every_rule(self):
        text = PAGE.read_text(encoding="utf-8")
        ids = [ID.search(cells[0]).group(0) for cells in table_rows(text) if ID.search(cells[0])]
        self.assertEqual(ids, self.skill_ids())

    def test_page_number_matches_id(self):
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            if ID.search(cells[0]):
                with self.subTest(cell=cells[0]):
                    m = re.fullmatch(r"(\d+) \(R-AI-(\d{2})\)", cells[0])
                    self.assertIsNotNone(m)
                    self.assertEqual(int(m.group(1)), int(m.group(2)))

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in rules(skill_text())}
        seen = {}
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            m = ID.search(cells[0])
            if m:
                self.assertIn(cells[2].lower(), ("sì", "no"))
                seen[m.group(0)] = cells[2].lower() == "sì"
        self.assertEqual(seen, blocca)

    def test_page_judged_on_matches_skill(self):
        words = {"diff": "il diff", "report": "il report", "nota": "la nota"}
        seen = {}
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            m = ID.search(cells[0])
            if m:
                seen[m.group(0)] = cells[3]
        self.assertEqual(seen, {r[0]: words[r[4]] for r in rules(skill_text())})

    def test_page_explains_what_changes(self):
        text = " ".join(PAGE.read_text(encoding="utf-8").split())
        low = text.lower()
        # il profilo si accende solo dove `init` lo propone e l'utente copia il blocco, da L1
        self.assertRegex(text, r"`/tollgate:init`[^.]*propone[^.]*\btu copi\b")
        self.assertRegex(text, r"livello L1\b")
        # R-AI-01 guarda il solo diff
        self.assertRegex(text, r"R-AI-01[^.]{0,60}solo diff")
        # «più recente» vuol dire ultimo modello stabile
        self.assertRegex(low, r"«il più recente»[^.]*ultimo modello stabile")
        for folder in ("llm", "prompts", "agents", "ai"):
            with self.subTest(folder=folder):
                self.assertIn(f"`{folder}/`", text)
        for needle in ("anthropic", "openai", "openrouter", "agno", "genai"):
            with self.subTest(import_of=needle):
                self.assertIn(needle, low)

    def test_page_is_a_proposal(self):
        """Vale solo finché `approved` non è nella skill: col Task 7 la pagina è approvata."""
        self.skip_if_approved()
        self.assertNotIn("Approvata dall'utente", PAGE.read_text(encoding="utf-8"))

    def test_page_brings_the_open_choices_to_the_user(self):
        """Vale solo finché `approved` non è nella skill: col Task 7 «Da decidere tu» si chiude."""
        self.skip_if_approved()
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Da decidere tu", 1)[1].split("\n## ", 1)[0]
        for needle in ("R-AI-06", "R-AI-11", "OpenAI", "OpenRouter", 'from "openai"'):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_page_approval_date_matches_skill(self):
        approved = frontmatter(skill_text())["approved"]
        found = re.findall(r"^Approvata dall'utente il (\d{4}-\d{2}-\d{2})\.$",
                           PAGE.read_text(encoding="utf-8"), re.M)
        self.assertEqual(found, [approved])

    def test_approved_skill_leaves_no_pending_decisions(self):
        """Con la skill approvata né la pagina né il rapporto rimandano a «Da decidere tu»
        o dicono che qualcosa va ancora confermato."""
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("Da decidere tu", text)
                self.assertNotRegex(text, r"[Vv]a confermat[ao] dall'utente")

    def test_page_has_removed_section_without_rule_ids(self):
        removed = PAGE.read_text(encoding="utf-8").split("\n## Regole tolte dalla verifica", 1)[1]
        removed = removed.split("\n## ", 1)[0]
        self.assertTrue(removed.strip())
        self.assertFalse(ID.search(removed), "le regole tolte non usano id R-AI-")

    def test_page_has_no_private_data(self):
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
