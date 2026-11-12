"""La skill `rules-frontend` (B6, Task 3): la bozza delle regole del profilo `frontend`, ognuna con
la sua fonte, e il frammento `templates/profiles/frontend.toml`; il rapporto delle fonti e la
pagina per l'utente (Task 4). `rules()` è quella di `test_rules_ai`."""
import getpass
import re
import socket
import tomllib
import unittest

from tests.helpers import ROOT
from tests.test_rules_ai import JUDGED, frontmatter, rules
from tests.test_rules_base import table_rows
from tollgate_analysis import research
from tollgate_core import fragments

SKILL = ROOT / "skills" / "rules-frontend" / "SKILL.md"
PAGE = ROOT / "docs" / "profili" / "frontend.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "frontend-fonti.md"
ID = re.compile(r"R-FRONTEND-\d{2}")
FRAGMENT = ROOT / "templates" / "profiles" / "frontend.toml"
AREA = "frontend"
DESCRIPTION = ("Regole di tollgate per il codice d'interfaccia (componenti, pagine, stili, "
               "accessibilità): le caricano in automatico gli agenti dell'area frontend, non "
               "serve invocarla.")
RULE_LINE = re.compile(r"^R-FRONTEND-\d{2}( \[blocca\])? \S")

# Una `Fonte:` contiene almeno una di queste forme, oppure il nome di una skill ammessa e, nella
# stessa riga, la sua licenza. `ui-ux-pro-max` non è ammessa (decisione 10): niente licenza.
SOURCE_FORMS = ("https://", "progetto di B, sezione", "catalogo", "spec del nucleo")
ALLOWED_SKILLS = {"frontend-ui-engineering": "MIT", "frontend-design": "Apache-2.0"}

# I criteri di WCAG 2.2 che le regole possono citare (pagina del W3C, 12 dicembre 2024), con il
# loro livello: la `Fonte:` di una regola scrive «numero Nome (livello)».
WCAG = {"1.1.1": "A", "1.3.1": "A", "2.1.1": "A", "2.1.2": "A", "2.4.3": "A", "2.4.7": "AA",
        "3.3.2": "A", "4.1.2": "A", "4.1.3": "AA"}
CRITERION = re.compile(r"\b([1-4]\.\d{1,2}\.\d{1,2}) [^()]*\((AAA|AA|A)\)")

# Le scelte dell'utente del progetto di B e la regola che ciascuna diventa, con la sezione che la
# sua riga `Fonte:` deve nominare. Si cerca per id, non per parole. Correzione della decisione 16:
# ci sono **tutte** le regole la cui `Fonte:` cita il progetto di B.
USER_CHOICES = {
    "per ogni libreria UI toccata, la documentazione della versione in package.json": (
        "R-FRONTEND-01", ("progetto di B, sezione 3.4",)),
    "prima di creare un componente si cerca se ne esiste uno simile": (
        "R-FRONTEND-02", ("progetto di B, sezione 3.4",)),
    "i controlli si usano con la tastiera e un elemento nativo": (
        "R-FRONTEND-05", ("progetto di B, sezione 13", "WCAG 2.2")),
    "il nome accessibile e il testo alternativo": (
        "R-FRONTEND-06", ("progetto di B, sezione 13", "WCAG 2.2")),
    "ogni campo ha un'etichetta": ("R-FRONTEND-07", ("progetto di B, sezione 13", "WCAG 2.2")),
    "l'indicatore del focus non si toglie": (
        "R-FRONTEND-08", ("progetto di B, sezione 13", "WCAG 2.2")),
    "i messaggi di stato in una regione": (
        "R-FRONTEND-09", ("progetto di B, sezione 13", "WCAG 2.2")),
    "dialoghi e menu: il focus dentro e di nuovo fuori": (
        "R-FRONTEND-10", ("progetto di B, sezione 13", "WCAG 2.2")),
}

# I nove pattern della decisione 3, nell'ordine.
PATTERNS = ["**/components/**", "web/**", "**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte",
            "**/*.astro", "**/*.css", "**/*.scss"]
# La decisione 7: le cartelle alla radice dei server e di `infra`, più `supabase/`.
EXCLUDE = ["server/", "api/", "backend/", "functions/", "infra/", "supabase/"]
# La decisione 5: le righe di import delle librerie di rotte d'interfaccia, nelle due forme di
# virgolette. Nessun marcatore è stato tolto dalla verifica delle fonti (Step 0).
ROUTER_MODULES = ("@tanstack/react-router", "react-router", "react-router-dom", "@remix-run/react")
MARKERS = [f"from {q}{m}{q}" for m in ROUTER_MODULES for q in ("'", '"')]
TOOL_WORDS = ("services", "hooks", "vite", "tsconfig", "eslint", "html", "app/**", "page")

# Le parole che i ventidue punti di scelta dell'utente nominano (pagina, «Cosa hai deciso»).
CHOICE_NEEDLES = (
    "`services/`", "`hooks/`", "`.html`", "`.sass`", "`.less`", "`page.js`", "`components/`",
    "`components/ai/`", "`components/routes/`", "`handlers/`", "`app/agents/`", "`ai/routes/`",
    "`react-router-dom`", "`pages/api/`", "SvelteKit", "`route.tsx`", "`.claude/`", "`.github/`",
    "`supabase/`", "`web/`", "`web/routes/`", "`**/*.css`", "R-FRONTEND-01", "R-FRONTEND-02",
    "R-FRONTEND-07", "R-FRONTEND-11", "scelta nostra", "rotte di sole risorse", "+types",
    "marcatore di `backend`", "primo blocco", "`aria-label`", "senza versione", "`dod`",
    "finché non arriva il profilo del database", "`web/api/`", "`index.module.css`",
    "foglio di stile")


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def frontend_rules() -> list[tuple[str, bool, str, str, str]]:
    return rules(skill_text(), AREA)


def fragment() -> dict:
    return tomllib.loads(FRAGMENT.read_text(encoding="utf-8"))


class RulesFrontendTest(unittest.TestCase):
    def test_frontmatter(self):
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-frontend")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertEqual(fm["approved"], "2026-11-11")
        self.assertTrue(research.enforced(text))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole frontend (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertEqual(titles[0], "## Prima di scrivere")
        for title in ("## Mentre lavori", "## Dove informarsi", "## Fonti"):
            self.assertIn(title, titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if l.startswith("R-FRONTEND-")]
        self.assertTrue(ids)
        self.assertEqual(ids, [f"R-FRONTEND-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in frontend_rules()], ids)

    def test_area_rules_of_research_match_rules(self):
        parsed = frontend_rules()
        self.assertEqual(research.area_rules(skill_text(), AREA),
                         ({r[0] for r in parsed}, {r[0] for r in parsed if r[1]}))

    def test_every_rule_has_a_source(self):
        for rid, _blocca, text, source, _judged in frontend_rules():
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_every_rule_names_what_is_judged(self):
        for rid, *_rest, judged in frontend_rules():
            with self.subTest(rule=rid):
                self.assertIn(judged, ("diff", "report", "nota"),
                              "manca la riga «Si giudica su: diff|report|nota»")
        self.assertTrue(all(JUDGED.match(f"Si giudica su: {j}") for *_r, j in frontend_rules()))

    def test_every_rule_names_a_source_of_the_allowed_kinds(self):
        for rid, _b, _t, source, _j in frontend_rules():
            with self.subTest(rule=rid):
                by_form = any(form in source for form in SOURCE_FORMS)
                by_skill = any(name in source and lic in source
                               for name, lic in ALLOWED_SKILLS.items())
                self.assertTrue(by_form or by_skill, source)

    def test_ui_ux_pro_max_is_not_a_source(self):
        """La copia locale non ha licenza (decisione 10): si nomina solo in «Dove informarsi»."""
        for rid, _b, _t, source, _j in frontend_rules():
            with self.subTest(rule=rid):
                self.assertNotIn("ui-ux-pro-max", source)

    def test_extensions_of_the_sources_are_declared_as_our_choice(self):
        """Le parti che vanno oltre le fonti dicono «scelta nostra» nella `Fonte:`: la via
        d'uscita di R-FRONTEND-01, il formato del report di R-FRONTEND-02 e la condizione di
        R-FRONTEND-11. Il rapporto delle fonti le elenca e la pagina dice che l'utente le ha
        approvate in «Cosa hai deciso»."""
        by_id = {r[0]: r[3] for r in frontend_rules()}
        for rid in ("R-FRONTEND-01", "R-FRONTEND-02", "R-FRONTEND-11"):
            with self.subTest(rule=rid):
                self.assertIn("scelta nostra", by_id[rid])

    def test_some_rules_block(self):
        flags = [r[1] for r in frontend_rules()]
        self.assertTrue(any(flags))
        self.assertFalse(all(flags))

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_blocking_rules_judged_on_diff_or_report(self):
        """Nei lavori senza passo la nota non c'è: una regola che blocca non si può giudicare
        solo sulla nota."""
        for rid, blocca, _text, _source, judged in frontend_rules():
            if blocca:
                with self.subTest(rule=rid):
                    self.assertIn(judged, ("diff", "report"))

    def test_blocca_lines_have_text(self):
        """Una riga `R-FRONTEND-NN [blocca]` senza testo sarebbe una regola nota ma non
        bloccante."""
        lines = [l for l in skill_text().split("\n") if l.startswith("R-FRONTEND-")]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line[:30]):
                self.assertRegex(line, RULE_LINE)
        self.assertEqual(len(lines), len(frontend_rules()))

    def test_component_rules_say_how_to_recognize_a_component(self):
        """Il revisore riconosce un componente nel diff da una riga, detta prima delle regole."""
        intro = skill_text().split("\n## Prima di scrivere", 1)[0]
        lines = [l for l in intro.split("\n") if l.startswith("Un componente è")]
        self.assertEqual(len(lines), 1)
        for needle in (".tsx", ".jsx", ".vue", ".svelte", ".astro", "esporta"):
            with self.subTest(needle=needle):
                self.assertIn(needle, lines[0])

    def test_a11y_rules_name_a_wcag_criterion(self):
        """Ogni regola che cita WCAG nomina nella `Fonte:` almeno un criterio con il suo nome e
        il suo livello, e il livello è quello della norma; almeno quattro citano WCAG 2.2."""
        citing = 0
        for rid, _b, _t, source, _j in frontend_rules():
            if "WCAG" not in source:
                continue
            with self.subTest(rule=rid):
                found = CRITERION.findall(source)
                self.assertTrue(found, source)
                for number, level in found:
                    self.assertEqual(WCAG.get(number), level, f"{number} ({level})")
            if "WCAG 2.2" in source:
                citing += 1
        self.assertGreaterEqual(citing, 4)

    def test_wcag_criteria_stay_in_the_verified_set(self):
        """Un criterio che la pagina del W3C non mostra (Step 0) non entra in una regola."""
        for rid, _b, _t, source, _j in frontend_rules():
            for number, _level in CRITERION.findall(source):
                with self.subTest(rule=rid, criterion=number):
                    self.assertIn(number, WCAG)

    def test_using_aria_is_cited_with_its_status(self):
        """«Using ARIA» è una bozza sospesa del W3C: una `Fonte:` che la cita lo dice."""
        for rid, _b, _t, source, _j in frontend_rules():
            if "Using ARIA" in source:
                with self.subTest(rule=rid):
                    self.assertIn("bozza sospesa", source)

    def test_user_choices_covered(self):
        by_id = {r[0]: r for r in frontend_rules()}
        for choice, (rid, sections) in USER_CHOICES.items():
            with self.subTest(choice=choice):
                self.assertIn(rid, by_id)
                for section in sections:
                    self.assertIn(section, by_id[rid][3])
        self.assertEqual(len({rid for rid, _ in USER_CHOICES.values()}), len(USER_CHOICES))
        # Nessuna regola che cita il progetto di B resta fuori dalla tabella.
        citing = {r[0] for r in frontend_rules() if "progetto di B" in r[3]}
        self.assertEqual(citing, {rid for rid, _ in USER_CHOICES.values()})

    def test_sources_section(self):
        fonti = skill_text().split("\n## Fonti", 1)[1]
        flat = " ".join(fonti.split())
        for needle in ("frontend-ui-engineering", "frontend-design", "WCAG 2.2", "W3C",
                       "Next.js", "React Router", "Tailwind"):
            with self.subTest(needle=needle):
                self.assertIn(needle, fonti)
        self.assertTrue(re.search(r"frontend-ui-engineering.{0,80}licenza MIT", flat),
                        "manca un passo atteso nel testo")
        self.assertTrue(re.search(r"frontend-design.{0,80}Apache-2\.0", flat),
                        "manca un passo atteso nel testo")
        self.assertIn("con parole nostre", flat)
        self.assertIn("senza testo copiato", flat)

    def test_where_to_look_names_skills(self):
        informarsi = skill_text().split("\n## Dove informarsi", 1)[1].split("\n## ", 1)[0]
        for name in ("frontend-design", "ui-ux-pro-max", "frontend-ui-engineering"):
            with self.subTest(skill=name):
                self.assertIn(f"`{name}`", informarsi)
        for text in ("https://www.w3.org/TR/WCAG22/", "package.json", "Tailwind"):
            with self.subTest(text=text):
                self.assertIn(text, informarsi)
        for name in ("rules-a11y", "rules-performance", "taste-skill", "anti-ui-slop"):
            with self.subTest(absent=name):  # decisioni 9 e 10
                self.assertNotIn(name, skill_text())

    def test_fragment_matches_decisions(self):
        data = fragment()
        self.assertEqual(set(data), {"profile", "detect"})
        profile = data["profile"]
        self.assertEqual(profile["kind"], "vertical")
        self.assertEqual(profile["min_level"], "L0")
        self.assertEqual(profile["paths"], PATTERNS)
        self.assertEqual(profile["skills"], [])
        self.assertEqual(profile["reviewer_skills"], [])
        self.assertEqual(profile["commands"], {})
        self.assertEqual(profile["dod"], [])
        self.assertEqual(profile["agent"], "tollgate:implementer-frontend")
        self.assertEqual(profile["reviewer"], "tollgate:reviewer-frontend")
        for key in ("rules", "blocking_rules", "final_specialist", "cross"):
            self.assertNotIn(key, profile)
        detect = data["detect"]
        self.assertEqual(set(detect), {"content", "exclude"})
        self.assertEqual(detect["exclude"], EXCLUDE)
        self.assertEqual(detect["content"], MARKERS)

    def test_real_exclude_matches_root_folders_of_other_fragments(self):
        """`exclude` ripete le cartelle alla radice di `backend` e `infra` (decisione 7): se
        cambiano lì, il test dice di cambiarle anche qui."""
        real = {f.area: f for f in fragments.load(ROOT)}
        folders = {f"{p.name}/" for area in ("backend", "infra")
                   for p in real[area].patterns if p.kind == "root_folder"}
        self.assertEqual(set(real["frontend"].exclude) - {"supabase/"}, folders)
        self.assertIn("supabase/", real["frontend"].exclude)

    def test_fragment_leaves_out_tool_configs(self):
        for pattern in fragment()["profile"]["paths"]:
            with self.subTest(pattern=pattern):
                for word in TOOL_WORDS:
                    self.assertNotIn(word, pattern)

    def test_markers_are_router_imports(self):
        content = fragment()["detect"]["content"]
        self.assertEqual(len(content), len(set(content)))
        for marker in content:
            with self.subTest(marker=marker):
                self.assertRegex(marker, r"^from ['\"]")
                self.assertTrue(any(marker[len("from '"):-1] == m for m in ROUTER_MODULES),
                                marker)
                self.assertNotIn(marker, ("from 'react'", 'from "react"', "from 'vue'",
                                          'from "vue"'))
                self.assertNotIn("use client", marker)
                self.assertEqual(marker, marker.strip())

    def test_real_markers_not_in_tollgate_bin(self):
        """Ogni progetto riceve `bin/` in `.github/tollgate/`: se vi comparisse un marcatore,
        `init` accenderebbe il profilo dappertutto."""
        markers = fragment()["detect"]["content"]
        files = [p for p in (ROOT / "bin").rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts]
        self.assertTrue(files)
        for path in files:
            text = path.read_bytes().decode("utf-8", errors="ignore")
            for marker in markers:
                with self.subTest(file=str(path.relative_to(ROOT)), marker=marker):
                    self.assertNotIn(marker, text)

    def test_no_long_quotations(self):
        """Qui si controlla solo che la skill non porti citazioni lunghe tra virgolette."""
        for line in skill_text().split("\n"):
            for quoted in re.findall(r"«([^»]*)»", line):
                with self.subTest(quoted=quoted[:40]):
                    self.assertLessEqual(len(quoted.split()), 12)

    def test_fragment_loads_through_the_loader(self):
        (found,) = [f for f in fragments.load(ROOT) if f.area == AREA]
        self.assertEqual(found.source, FRAGMENT)
        self.assertEqual(found.skill_path, SKILL)
        self.assertEqual(found.detect, tuple(MARKERS))
        self.assertEqual(found.exclude, tuple(EXCLUDE))
        self.assertEqual(len(found.patterns), len(PATTERNS))
        self.assertEqual(found.patterns[0], fragments.Pattern("folder", "components"))
        self.assertEqual(found.patterns[2], fragments.Pattern("ext", "tsx"))


# I numeri scritti in lettere, per i conteggi della pagina (fino a trenta).
NUMBER_WORDS = {"zero": 0, "una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5,
                "sei": 6, "sette": 7, "otto": 8, "nove": 9, "dieci": 10, "undici": 11,
                "dodici": 12, "tredici": 13, "quattordici": 14, "quindici": 15, "sedici": 16,
                "diciassette": 17, "diciotto": 18, "diciannove": 19, "venti": 20,
                "ventuno": 21, "ventidue": 22, "ventitré": 23, "ventiquattro": 24,
                "venticinque": 25, "ventisei": 26, "ventisette": 27, "ventotto": 28,
                "ventinove": 29, "trenta": 30}


def as_number(token: str) -> int:
    """Un numero scritto in cifre o in lettere; un valore fuori dal dizionario è un errore
    esplicito, non un `KeyError`."""
    word = token.lower()
    if word.isdigit():
        return int(word)
    if word not in NUMBER_WORDS:
        raise AssertionError(f"numero «{token}» fuori dal dizionario del test (fino a trenta)")
    return NUMBER_WORDS[word]


class RulesFrontendPageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (B6, Task 4). Si cercano gli id e i
    nomi, non le frasi."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in frontend_rules()]

    def skip_if_approved(self):
        if "approved" in frontmatter(skill_text()):
            self.skipTest("la skill è approvata: la pagina non è più una proposta")

    def sources_text(self) -> str:
        return SOURCES.read_text(encoding="utf-8")

    def section(self, title: str) -> str:
        text = self.sources_text()
        self.assertTrue(f"\n## {title}" in text, "manca un testo atteso")
        return text.split(f"\n## {title}", 1)[1].split("\n## ", 1)[0]

    def page_section(self, title: str) -> str:
        text = PAGE.read_text(encoding="utf-8")
        self.assertTrue(f"\n## {title}" in text, "manca un testo atteso")
        return text.split(f"\n## {title}", 1)[1].split("\n## ", 1)[0]

    def test_sources_report_covers_every_rule(self):
        """Per ogni voce di una `Fonte:` (le parti separate da `;`, tolta quella «scelta
        nostra») la tabella ha una riga `ok` di quella regola la cui cella «Fonte» la contiene."""
        rows = table_rows(self.section("Regole e fonti"))
        named = set()
        for cells in rows:
            self.assertIn(cells[-1], ("ok", "no"), "l'esito è `ok` o `no`, senza grassetto")
            named.update(ID.findall(cells[0]))
        self.assertEqual(named - set(self.skill_ids()), set())
        for rid, _b, _t, source, _j in frontend_rules():
            voci = [" ".join(p.split()) for p in source.split(";") if "scelta nostra" not in p]
            self.assertTrue(voci, rid)
            for voce in voci:
                with self.subTest(rule=rid, voce=voce[:50]):
                    self.assertTrue(
                        any(c[0] == rid and c[-1] == "ok" and voce in " ".join(c[1].split())
                            for c in rows),
                        "nessuna riga `ok` del rapporto per questa voce")

    def test_removed_sources_are_not_in_the_skill(self):
        """Il ciclo vale quando il rapporto avrà righe `no` (una fonte uscita o corretta: la regola
        ha ancora una riga `ok`); oggi, senza righe `no`, contano i quattro `assertNotIn` sulle due
        voci corrette dopo la prima verifica, che non nominano più la parte senza fonte."""
        sources = {r[0]: r[3] for r in frontend_rules()}
        text = {r[0]: r[2] for r in frontend_rules()}
        rows = table_rows(self.section("Regole e fonti"))
        for cells in rows:
            if ID.fullmatch(cells[0]) and cells[-1] == "no":
                with self.subTest(rule=cells[0], source=cells[1][:40]):
                    self.assertTrue(any(c[0] == cells[0] and c[-1] == "ok" for c in rows),
                                    "la regola non ha più una fonte ok")
        self.assertFalse("gerarchia dei caratteri" in sources["R-FRONTEND-04"], "R-04 cita ancora la parte tolta")
        self.assertFalse("caratteri" in text["R-FRONTEND-04"], "R-04 parla ancora di caratteri")
        self.assertFalse("carattere di sistema" in text["R-FRONTEND-12"], "R-12 cita ancora la parte tolta")
        self.assertFalse("Design principles" in sources["R-FRONTEND-12"], "R-12 cita la sezione sbagliata")
        self.assertTrue("scelta nostra" in sources["R-FRONTEND-01"], "R-01 non dichiara la scelta nostra")

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
        ok = set()
        for cells in table_rows(self.section("Pattern dei percorsi")):
            m = re.fullmatch(r"`(.+)`", cells[0])
            self.assertIsNotNone(m, cells[0])
            self.assertIn(cells[-1], ("ok", "no"))
            if cells[-1] == "ok":
                ok.add(m.group(1))
        self.assertEqual(set(fragment()["profile"]["paths"]) - ok, set())
        self.assertEqual(ok - set(fragment()["profile"]["paths"]), set(),
                         "il rapporto verifica un pattern che non c'è più")

    def test_detect_markers_verified(self):
        """Una riga `ok` vale per le due forme di virgolette dello stesso import."""
        ok = set()
        for cells in table_rows(self.section("Marcatori di contenuto")):
            m = re.fullmatch(r"`(.+)`", cells[0])
            self.assertIsNotNone(m, cells[0])
            self.assertIn(cells[-1], ("ok", "no"))
            if cells[-1] == "ok":
                ok.add(m.group(1).replace('"', "'"))
        markers = {m.replace('"', "'") for m in fragment()["detect"]["content"]}
        self.assertEqual(markers - ok, set())
        self.assertEqual(ok - markers, set(), "il rapporto verifica un marcatore che non c'è più")
        self.assertEqual(len(fragment()["detect"]["content"]), 8)

    def test_exclude_verified(self):
        ok = set()
        for cells in table_rows(self.section("Esclusione")):
            m = re.fullmatch(r"`(.+)`", cells[0])
            self.assertIsNotNone(m, cells[0])
            self.assertIn(cells[-1], ("ok", "no"))
            if cells[-1] == "ok":
                ok.add(m.group(1))
        (found,) = [f for f in fragments.load(ROOT) if f.area == AREA]
        self.assertEqual(ok, set(found.exclude))

    def test_page_lists_every_rule(self):
        text = PAGE.read_text(encoding="utf-8")
        ids = [ID.search(cells[0]).group(0) for cells in table_rows(text) if ID.search(cells[0])]
        self.assertEqual(ids, self.skill_ids())

    def test_page_number_matches_id(self):
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            if ID.search(cells[0]):
                with self.subTest(cell=cells[0]):
                    m = re.fullmatch(r"(\d+) \(R-FRONTEND-(\d{2})\)", cells[0])
                    self.assertIsNotNone(m)
                    self.assertEqual(int(m.group(1)), int(m.group(2)))

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in frontend_rules()}
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
        self.assertEqual(seen, {r[0]: words[r[4]] for r in frontend_rules()})

    def test_page_counts_match_skill(self):
        """I numeri della pagina (in lettere o in cifre) per le regole e per quelle che
        bloccano sono quelli della skill."""
        section = " ".join(self.page_section("Cosa sono").split())
        total = re.search(r"\bSono (\w+) regole in più", section)
        self.assertIsNotNone(total, "manca «Sono N regole in più»")
        self.assertEqual(as_number(total.group(1)), len(frontend_rules()))
        block = re.search(r"\b(\w+) di queste bloccano", section)
        self.assertIsNotNone(block, "manca «N di queste bloccano»")
        self.assertEqual(as_number(block.group(1)), sum(1 for r in frontend_rules() if r[1]))

    def test_page_explains_what_changes(self):
        text = " ".join(PAGE.read_text(encoding="utf-8").split())
        # il profilo si accende solo dove `init` lo propone e l'utente copia il blocco; da L1
        self.assertTrue(re.search(r"`/tollgate:init`[^.]*propone[^.]*\btu copi\b", text),
                        "manca un passo atteso nel testo")
        self.assertTrue(re.search(r"livelli? L1 e L2\b", text),
                        "manca un passo atteso nel testo")
        # le estensioni e le cartelle che lo accendono
        for name in (".tsx", ".jsx", ".vue", ".svelte", ".astro", ".css", ".scss", "components/",
                     "web/", "@tanstack/react-router", "react-router", "react-router-dom",
                     "@remix-run/react"):
            with self.subTest(name=name):
                self.assertTrue(f"`{name}`" in text, "manca un testo atteso")
        # i percorsi per estensione perdono contro ogni cartella di un altro profilo
        self.assertTrue(re.search(r"per estensione[^.]*perdono contro ogni cartella di un altro profilo", text),
                        "manca un passo atteso nel testo")
        for example in ("`server/components/Mail.tsx`", "`server/app.tsx`", "`src/main.tsx`",
                        "`src/ai/components/Chat.tsx`", "`prompts/Card.tsx`"):
            with self.subTest(example=example):
                self.assertTrue(example in text, "manca un testo atteso")
        # la cartella `routes/` con i moduli di rotta, un file senza import, il rimedio a mano
        self.assertTrue(re.search(r"libreria di rotte[^.]*`routes/`[^.]*fuori da `backend`", text),
                        "manca un passo atteso nel testo")
        self.assertTrue(re.search(r"senza (alcun )?import[^.]*un test o un foglio di stile[^.]*"
                               r"`routes/`[^.]*resta a `backend`", text),
                        "manca un passo atteso nel testo")
        self.assertTrue(re.search(r"toglier\w+ a mano[^.]*`paths`[^.]*blocco di `backend`", text),
                        "manca un passo atteso nel testo")
        # un file con l'import e un marcatore di `backend`
        self.assertTrue(re.search(r"marcatore di `backend`[^.]*`routes/`[^.]*resta a `backend`"
                               r"[^.]*quel file va a `frontend`", text),
                        "manca un passo atteso nel testo")
        # la riga «lo accendono N file» conta anche i file delle cartelle escluse
        self.assertTrue(re.search(r"«lo accendono N file»[^.]*conta anche[^.]*cartelle escluse", text),
                        "manca un passo atteso nel testo")
        # le regole di accessibilità: WCAG 2.2, qui, nessuna skill a parte
        self.assertTrue("WCAG 2.2" in text, "manca un testo atteso")
        self.assertTrue(re.search(r"accessibilità vengono dalla norma WCAG 2\.2[^.]*stanno qui", text),
                        "manca un passo atteso nel testo")
        # lint, typecheck e test dei componenti a mano in `dod`, senza chiedere, `allow_no_tests`
        for name in ("`dod`", "lint", "typecheck", "test dei componenti"):
            with self.subTest(name=name):
                self.assertTrue(name in text, "manca un testo atteso")
        self.assertTrue(re.search(r"senza chiedere", text.lower()),
                        "manca un passo atteso nel testo")
        self.assertTrue("allow_no_tests = true" in text, "manca un testo atteso")
        self.assertTrue("/tollgate:approve unverified-tests" in text, "manca un testo atteso")

    def test_page_is_a_proposal(self):
        """Vale solo finché `approved` non è nella skill: col Task 5 la pagina è approvata."""
        self.skip_if_approved()
        self.assertFalse("Approvata dall'utente" in PAGE.read_text(encoding="utf-8"),
                         "la pagina dice già che è approvata")

    def test_page_brings_the_open_choices_to_the_user(self):
        """Vale solo finché `approved` non è nella skill: col Task 5 «Da decidere tu» si chiude."""
        self.skip_if_approved()
        section = " ".join(self.page_section("Da decidere tu").split())
        for needle in CHOICE_NEEDLES:
            with self.subTest(needle=needle):
                self.assertTrue(needle in section, "manca un testo atteso")

    def test_page_records_the_choices(self):
        """Con la skill approvata la pagina dice cosa ha deciso l'utente sui ventidue punti."""
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        section = " ".join(self.page_section("Cosa hai deciso").split())
        for needle in CHOICE_NEEDLES:
            with self.subTest(needle=needle):
                self.assertTrue(needle in section, "manca un testo atteso")
        self.assertEqual(len(re.findall(r"Hai approvato: resta la proposta", section)), 22,
                         "ogni punto dice che la proposta è stata approvata")

    def test_page_approval_date_matches_skill(self):
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        approved = frontmatter(skill_text())["approved"]
        found = re.findall(r"^Approvata dall'utente il (\d{4}-\d{2}-\d{2})\.$",
                           PAGE.read_text(encoding="utf-8"), re.M)
        self.assertEqual(found, [approved], "la data della pagina non è quella della skill")

    def test_approved_skill_leaves_no_pending_decisions(self):
        """Con la skill approvata né la pagina né il rapporto rimandano a «Da decidere tu»
        o dicono che qualcosa va ancora confermato."""
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertFalse("Da decidere tu" in text, "resta un rimando a «Da decidere tu»")
                self.assertFalse(re.search(r"[Vv]a confermat[ao] dall'utente", text),
                                 "resta una conferma da avere")

    def test_approved_page_has_no_pending_sections(self):
        """Decisione 16: approvata, la pagina non ha più «Come rispondere» né «Rinvio», e non
        chiede più di approvare."""
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        text = PAGE.read_text(encoding="utf-8")
        self.assertFalse("\n## Come rispondere" in text, "resta la sezione «Come rispondere»")
        self.assertFalse("**Rinvio.**" in text, "resta il rinvio")
        self.assertFalse(re.search(r"finché non le approvi|dopo che avrai approvato", text),
                         "la pagina chiede ancora di approvare")

    def test_page_choices_count_matches_list(self):
        section = self.page_section("Cosa hai deciso")
        count = len(re.findall(r"^\d+\. \*\*", section, re.M))
        self.assertGreaterEqual(count, 18)
        words = {n: w for w, n in NUMBER_WORDS.items() if w != "uno"}
        if count not in words:
            self.fail(f"{count} voci: il dizionario dei numeri arriva a trenta")
        self.assertTrue(f"Su {words[count]} punti" in section, "manca un testo atteso")
        self.assertEqual(len(re.findall(r"Hai approvato: resta la proposta", section)), count,
                         "ogni voce dice che la proposta è stata approvata")

    def test_our_choices_are_named_in_the_choices(self):
        """Ogni obbligo senza fonte ha «scelta nostra» nella `Fonte:` ed è nominato in «Cosa hai
        deciso» (R-FRONTEND-01, 02 e 11)."""
        by_id = {r[0]: r[3] for r in frontend_rules()}
        ours = [rid for rid, source in by_id.items() if "scelta nostra" in source]
        self.assertEqual(ours, ["R-FRONTEND-01", "R-FRONTEND-02", "R-FRONTEND-11"])
        section = self.page_section("Cosa hai deciso")
        for rid in ours:
            with self.subTest(rule=rid):
                self.assertTrue(rid in section, "manca un testo atteso")

    def test_page_explains_the_terms(self):
        text = PAGE.read_text(encoding="utf-8")
        for needle in ("**Componente**", "**Modulo di rotta**", "**Libreria di rotte**",
                       "**Foglio di stile**", "**Token di design**", "**Focus**", "**WCAG**",
                       "**Nome accessibile**", "**Marcatore**", "**Percorso esatto**", "**Profilo**",
                       "**Loader**", "**CDN**", "**Client delle API**", "**Percorso per estensione**",
                       "**`tollgate.toml`**", "**`dod`**", "**Gestore**"):
            with self.subTest(needle=needle):
                self.assertTrue(needle in text, "manca un testo atteso")

    def test_page_rinvio_says_what_stays_on_the_branch(self):
        """Con il rinvio su `main` vanno solo i Task 1 e 2. Vale solo finché `approved` non è nella
        skill: approvata, la pagina non offre più il rinvio."""
        self.skip_if_approved()
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Come rispondere", 1)[1]
        (rinvio,) = re.findall(r"\*\*Rinvio\.\*\*[^\n]*", section)
        rinvio = " ".join(rinvio.split())
        for needle in ("`main`", "`b6-profilo-frontend`", "i Task 1 e 2", "la forma `ext`",
                       "`togli-pagine`", "non vanno su `main`"):
            with self.subTest(needle=needle):
                self.assertTrue(needle in rinvio, "manca un testo atteso")

    def test_page_has_removed_section_without_rule_ids(self):
        removed = PAGE.read_text(encoding="utf-8").split("\n## Regole tolte dalla verifica", 1)[1]
        removed = removed.split("\n## ", 1)[0]
        self.assertTrue(removed.strip())
        self.assertFalse(ID.search(removed), "le regole tolte non usano id R-FRONTEND-")

    def test_page_has_no_private_data(self):
        """Né percorsi della home, né il nome utente o l'host di chi lancia il test (come parola
        intera, se lunghi almeno 4 caratteri), né forme di token. Il valore non si stampa mai."""
        secrets = []
        try:
            secrets.append(getpass.getuser())
        except (OSError, KeyError):
            pass
        secrets.append(socket.gethostname())
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertFalse("/home/" in text, "un percorso della home compare nel testo")
                for secret in secrets:
                    if len(secret) >= 4:
                        self.assertFalse(
                            re.search(rf"\b{re.escape(secret)}\b", text, re.I),
                            "il nome utente o l'host compare nel testo")
                self.assertFalse(re.search(r"sk-ant|ghp_|github_pat_", text),
                                 "una forma di token compare nel testo")


if __name__ == "__main__":
    unittest.main()
