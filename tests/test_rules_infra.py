"""La skill `rules-infra` (B4, Task 4): la bozza delle regole del profilo `infra`, ognuna con la sua
fonte, e il frammento `templates/profiles/infra.toml`. `rules()` è quella di `test_rules_ai`."""
import re
import tomllib
import unittest

from tests.helpers import ROOT
from tests.test_rules_ai import JUDGED, frontmatter, rules
from tests.test_rules_base import table_rows
from tollgate_analysis import research
from tollgate_core import fragments

SKILL = ROOT / "skills" / "rules-infra" / "SKILL.md"
PAGE = ROOT / "docs" / "profili" / "infra.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "infra-fonti.md"
ID = re.compile(r"R-INFRA-\d{2}")
FRAGMENT = ROOT / "templates" / "profiles" / "infra.toml"
AREA = "infra"
DESCRIPTION = ("Regole di tollgate per la configurazione e il deploy (Vercel, Cloudflare, Docker): "
               "le caricano in automatico gli agenti dell'area infra, non serve invocarla.")
RULE_LINE = re.compile(r"^R-INFRA-\d{2}( \[blocca\])? \S")
USER_CHOICES_SOURCE = "progetto di B, sezione"

# Le scelte dell'utente del progetto di B (3.4 e 11) e la regola che ciascuna diventa, con le
# sezioni che la sua riga `Fonte:` deve nominare. Si cerca per id, non per parole.
USER_CHOICES = {
    "prima di parlare di deploy si leggono i file di deploy già presenti": (
        "R-INFRA-01", ("progetto di B, sezione 3.4", "sezione 11")),
}

# I quattordici pattern del frammento, nell'ordine della decisione 1 più `compose.override.yaml`
# (carry D4); la fonte di ogni nome sta in un commento del frammento.
PATTERNS = ["infra/**", "**/vercel.json", "**/vercel.toml", "**/vercel.ts", "**/wrangler.toml",
            "**/wrangler.json", "**/wrangler.jsonc", "**/Dockerfile*", "**/.dockerignore",
            "**/compose.yaml", "**/compose.yml", "**/compose.override.yaml",
            "**/docker-compose.yaml", "**/docker-compose.yml"]

# Le pagine ufficiali che la sezione «Fonti» deve nominare, per fornitore.
OFFICIAL_SOURCES = {
    "Vercel": "https://vercel.com/docs/",
    "Cloudflare": "https://developers.cloudflare.com/workers/",
    "Docker": "https://docs.docker.com/",
}


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def infra_rules() -> list[tuple[str, bool, str, str, str]]:
    return rules(skill_text(), AREA)


def fragment() -> dict:
    return tomllib.loads(FRAGMENT.read_text(encoding="utf-8"))


class RulesInfraTest(unittest.TestCase):
    def test_frontmatter(self):
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-infra")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertEqual(fm["approved"], "2026-11-07")
        self.assertTrue(research.enforced(text))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole infra (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertEqual(titles[0], "## Prima di scrivere")
        for title in ("## Mentre lavori", "## Dove informarsi", "## Fonti"):
            self.assertIn(title, titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if l.startswith("R-INFRA-")]
        self.assertTrue(ids)
        self.assertEqual(ids, [f"R-INFRA-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in infra_rules()], ids)

    def test_area_rules_of_research_match_rules(self):
        parsed = infra_rules()
        self.assertEqual(research.area_rules(skill_text(), AREA),
                         ({r[0] for r in parsed}, {r[0] for r in parsed if r[1]}))

    def test_every_rule_has_a_source(self):
        for rid, _blocca, text, source, _judged in infra_rules():
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_every_rule_names_what_is_judged(self):
        for rid, *_rest, judged in infra_rules():
            with self.subTest(rule=rid):
                self.assertIn(judged, ("diff", "report", "nota"),
                              "manca la riga «Si giudica su: diff|report|nota»")
        self.assertTrue(all(JUDGED.match(f"Si giudica su: {j}") for *_r, j in infra_rules()))

    def test_every_rule_names_a_page_or_the_user_choice(self):
        for rid, _b, _t, source, _j in infra_rules():
            with self.subTest(rule=rid):
                self.assertTrue(USER_CHOICES_SOURCE in source or "https://" in source)

    def test_some_rules_block(self):
        flags = [r[1] for r in infra_rules()]
        self.assertTrue(any(flags))
        self.assertFalse(all(flags))

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_blocking_rules_judged_on_diff_or_report(self):
        """Nei lavori senza passo la nota non c'è (Review Focus 3): una regola che blocca non
        si può giudicare solo sulla nota."""
        for rid, blocca, _text, _source, judged in infra_rules():
            if blocca:
                with self.subTest(rule=rid):
                    self.assertIn(judged, ("diff", "report"))

    def test_blocca_lines_have_text(self):
        """Decisione 10: una riga `R-INFRA-NN [blocca]` senza testo sarebbe una regola nota ma
        non bloccante."""
        lines = [l for l in skill_text().split("\n") if l.startswith("R-INFRA-")]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line[:30]):
                self.assertRegex(line, RULE_LINE)
        self.assertEqual(len(lines), len(infra_rules()))

    def test_secret_rules_allow_example_files(self):
        """La regola sui file dei segreti locali non vieta i file d'esempio (review-focus 4)."""
        found = [r for r in infra_rules() if ".dev.vars" in r[2]]
        self.assertTrue(found)
        for rid, _b, text, _s, _j in found:
            with self.subTest(rule=rid):
                for suffix in (".example", ".sample", ".template"):
                    self.assertIn(suffix, text)

    def test_user_choices_covered(self):
        by_id = {r[0]: r for r in infra_rules()}
        for choice, (rid, sections) in USER_CHOICES.items():
            with self.subTest(choice=choice):
                self.assertIn(rid, by_id)
                for section in sections:
                    self.assertIn(section, by_id[rid][3])
        self.assertEqual(len({rid for rid, _ in USER_CHOICES.values()}), len(USER_CHOICES))

    def test_sources_section(self):
        fonti = skill_text().split("\n## Fonti", 1)[1]
        for vendor, url in OFFICIAL_SOURCES.items():
            with self.subTest(vendor=vendor):
                self.assertIn(vendor, fonti)
                self.assertIn(url, fonti)
        self.assertIn("`wrangler`", fonti)
        self.assertIn("Apache-2.0", fonti)
        flat = " ".join(fonti.split()).lower()
        self.assertIn("con parole nostre", flat)
        self.assertIn("senza testo copiato", flat)

    def test_where_to_look_names_skills(self):
        informarsi = skill_text().split("\n## Dove informarsi", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`wrangler`", informarsi)
        self.assertIn("`cloudflare`", informarsi)
        self.assertNotIn("workers-best-practices", informarsi)  # decisione 8
        for url in OFFICIAL_SOURCES.values():
            self.assertIn(url.rsplit("/", 2)[0], informarsi)

    def test_no_long_quotations(self):
        """Le copie delle fonti non sono nel repo: il controllo del testo copiato è del Task 5.
        Qui si controlla solo che la skill non porti citazioni lunghe tra virgolette."""
        for line in skill_text().split("\n"):
            for quoted in re.findall(r"«([^»]*)»", line):
                with self.subTest(quoted=quoted[:40]):
                    self.assertLessEqual(len(quoted.split()), 12)

    def test_fragment_matches_decisions(self):
        data = fragment()
        self.assertEqual(set(data), {"profile"})  # nessuna tabella [detect] (decisione 5)
        profile = data["profile"]
        self.assertEqual(profile["kind"], "vertical")
        self.assertEqual(profile["min_level"], "L1")
        self.assertEqual(profile["paths"], PATTERNS)
        self.assertEqual(profile["skills"], [])
        self.assertEqual(profile["reviewer_skills"], [])
        self.assertEqual(profile["commands"], {})
        self.assertEqual(profile["dod"], [])
        self.assertEqual(profile["agent"], "tollgate:implementer-infra")
        self.assertEqual(profile["reviewer"], "tollgate:reviewer-infra")
        for key in ("rules", "blocking_rules", "final_specialist"):
            self.assertNotIn(key, profile)

    def test_fragment_leaves_out_ci_and_workers(self):
        for pattern in fragment()["profile"]["paths"]:
            with self.subTest(pattern=pattern):
                for word in (".github", "workflows", "workers"):
                    self.assertNotIn(word, pattern)

    def test_fragment_loads_through_the_loader(self):
        (found,) = [f for f in fragments.load(ROOT) if f.area == AREA]
        self.assertEqual(found.source, FRAGMENT)
        self.assertEqual(found.skill_path, SKILL)
        self.assertEqual(found.detect, ())
        self.assertEqual(len(found.patterns), len(PATTERNS))
        self.assertEqual(found.patterns[0], fragments.Pattern("root_folder", "infra"))
        self.assertEqual(found.patterns[7], fragments.Pattern("name", "Dockerfile*"))


class RulesInfraPageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (B4, Task 5). Si cercano gli id e i
    nomi, non le frasi."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in infra_rules()]

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
            if cells[-1].split(":")[0].strip() == "ok":
                ok.update(found)
        self.assertEqual(named - set(self.skill_ids()), set())
        self.assertEqual(set(self.skill_ids()) - ok, set())

    def test_removed_sources_are_not_in_the_skill(self):
        """Ogni riga `no` del rapporto è una fonte uscita o corretta: la regola resta coperta da
        una riga `ok` e la `Fonte:` della skill non rimanda più alla sezione che non la regge."""
        sources = {r[0]: r[3] for r in infra_rules()}
        rows = table_rows(self.sources_main())
        for cells in rows:
            self.assertIn(cells[-1].split(":")[0].strip(), ("ok", "no", "Esito"),
                          "l'esito è `ok` o `no`, senza grassetto")
            if ID.fullmatch(cells[0]) and cells[-1] == "no":
                rid = cells[0]
                with self.subTest(rule=rid, source=cells[1][:40]):
                    self.assertIn(rid, sources)
                    self.assertTrue(any(c[0] == rid and c[-1] == "ok" for c in rows),
                                    "la regola non ha più una fonte ok")
        # R-INFRA-03: la sezione 3.4 esce dalla `Fonte:`; R-INFRA-12: `secret` si attribuisce
        # alla pagina dei segreti
        self.assertNotIn("sezione 3.4", sources["R-INFRA-03"])
        self.assertIn("https://developers.cloudflare.com/workers/configuration/secrets/",
                      sources["R-INFRA-12"])
        for rid in ("R-INFRA-01", "R-INFRA-02"):
            self.assertIn("scelta nostra", sources[rid])

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

    def test_path_patterns_verified(self):
        text = SOURCES.read_text(encoding="utf-8")
        self.assertIn("\n## Pattern dei percorsi", text)
        section = text.split("\n## Pattern dei percorsi", 1)[1].split("\n## ", 1)[0]
        ok = set()
        for cells in table_rows(section):
            m = re.fullmatch(r"`(.+)`", cells[0])
            self.assertIsNotNone(m, cells[0])
            self.assertIn(cells[-1], ("ok", "no"))
            if cells[-1] == "ok":
                ok.add(m.group(1))
        self.assertEqual(set(fragment()["profile"]["paths"]) - ok, set())
        self.assertEqual(ok - set(fragment()["profile"]["paths"]), set(),
                         "il rapporto verifica un pattern che non c'è più")

    def test_page_lists_every_rule(self):
        text = PAGE.read_text(encoding="utf-8")
        ids = [ID.search(cells[0]).group(0) for cells in table_rows(text) if ID.search(cells[0])]
        self.assertEqual(ids, self.skill_ids())

    def test_page_number_matches_id(self):
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            if ID.search(cells[0]):
                with self.subTest(cell=cells[0]):
                    m = re.fullmatch(r"(\d+) \(R-INFRA-(\d{2})\)", cells[0])
                    self.assertIsNotNone(m)
                    self.assertEqual(int(m.group(1)), int(m.group(2)))

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in infra_rules()}
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
        self.assertEqual(seen, {r[0]: words[r[4]] for r in infra_rules()})

    def test_page_explains_what_changes(self):
        text = " ".join(PAGE.read_text(encoding="utf-8").split())
        low = text.lower()
        # il profilo si accende solo dove `init` lo propone e l'utente copia il blocco, da L1
        self.assertRegex(text, r"`/tollgate:init`[^.]*propone[^.]*\btu copi\b")
        self.assertRegex(text, r"livello L1\b")
        # quali nomi di file e quale cartella lo accendono
        for name in ("vercel.json", "vercel.toml", "vercel.ts", "wrangler.toml", "wrangler.json",
                     "wrangler.jsonc", "Dockerfile", ".dockerignore", "compose.yaml",
                     "compose.yml", "compose.override.yaml", "docker-compose.yaml",
                     "docker-compose.yml", "infra/"):
            with self.subTest(name=name):
                self.assertIn(f"`{name}", text)
        # i workflow di GitHub e il codice dei Worker non sono `infra` (progetto 11)
        self.assertRegex(text, r"`\.github/workflows/`[^.]*non accend")
        self.assertRegex(low, r"codice dei worker[^.]*`backend`")
        # le forme di Docker che non lo accendono, e `.vercel/` che non è un file del repo
        self.assertIn("`app.Dockerfile`", text)
        self.assertRegex(text, r"`<nome del Dockerfile>\.dockerignore`")
        self.assertRegex(text, r"`\.vercel/`[^.]*non è un file del repo")
        # un comando di prova del deploy che non pubblica, aggiunto a mano in `dod` (decisione 7)
        self.assertIn("`dod`", text)
        self.assertIn("--dry-run", text)
        self.assertRegex(low, r"senza chiedere")
        self.assertIn("allow_no_tests = true", text)
        self.assertIn("/tollgate:approve unverified-tests", text)
        # i comandi dei servizi, anche con `npx`, chiedono l'approvazione (decisione 17)
        self.assertRegex(text, r"`npx`[^.]*approvazione|approvazione[^.]*`npx`")
        self.assertIn("Supabase", text)
        self.assertIn("B7", text)
        self.assertIn("`npx vitest run vercel`", text)
        self.assertIn("`npm docs", text)
        # un valore `"@nome"` in `env` di Vercel è un riferimento a un segreto
        self.assertIn('"@nome"', text)

    def test_secret_reference_exception_matches_skill(self):
        """Se la pagina ammette `"@nome"` in `env` di Vercel, lo ammette anche R-INFRA-05 della
        skill (quella che legge il revisore), con la fonte nel rapporto delle fonti."""
        page = " ".join(PAGE.read_text(encoding="utf-8").split())
        rule = {r[0]: r for r in infra_rules()}["R-INFRA-05"]
        self.assertIn('"@nome"', page)
        self.assertIn('"@nome"', rule[2])
        self.assertIn("riferimento a un segreto", rule[2])
        self.assertIn("segreto salvato su Vercel", rule[3])
        rows = [c for c in table_rows(self.sources_main())
                if c[0] == "R-INFRA-05" and "project-configuration/vercel-json" in c[1]
                and "my-secret-name" in c[2]]
        self.assertTrue(rows and all(c[-1] == "ok" for c in rows))

    def test_page_choices_count_matches_list(self):
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Cosa hai deciso", 1)[1].split("\n## ", 1)[0]
        count = len(re.findall(r"^\d+\. \*\*", section, re.M))
        words = {6: "sei", 7: "sette"}
        self.assertIn(f"Su {words[count]} punti", section)

    def test_page_records_the_choices(self):
        """Con la skill approvata la pagina dice cosa ha deciso l'utente sui sette punti."""
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Cosa hai deciso", 1)[1].split("\n## ", 1)[0]
        for needle in ("R-INFRA-01", "R-INFRA-02", "R-INFRA-05", "R-INFRA-06", ".example",
                       "`prompts/`", "`ai`", "`txt`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_page_is_a_proposal(self):
        """Vale solo finché `approved` non è nella skill: col Task 6 la pagina è approvata."""
        self.skip_if_approved()
        self.assertNotIn("Approvata dall'utente", PAGE.read_text(encoding="utf-8"))

    def test_page_brings_the_open_choices_to_the_user(self):
        """Vale solo finché `approved` non è nella skill: col Task 6 «Da decidere tu» si chiude."""
        self.skip_if_approved()
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Da decidere tu", 1)[1].split("\n## ", 1)[0]
        for needle in ("R-INFRA-01", "R-INFRA-02", "R-INFRA-05", "R-INFRA-06", ".example",
                       "`prompts/`", "`ai`", "`txt`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_page_approval_date_matches_skill(self):
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
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
        self.assertFalse(ID.search(removed), "le regole tolte non usano id R-INFRA-")

    def test_page_has_no_private_data(self):
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
