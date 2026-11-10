"""La skill `rules-backend` (B5, Task 3): la bozza delle regole del profilo `backend`, ognuna con la
sua fonte, e il frammento `templates/profiles/backend.toml`. `rules()` è quella di `test_rules_ai`."""
import re
import tomllib
import unittest

from tests.helpers import ROOT
from tests.test_rules_ai import JUDGED, frontmatter, rules
from tests.test_rules_base import table_rows
from tollgate_analysis import research
from tollgate_core import fragments

SKILL = ROOT / "skills" / "rules-backend" / "SKILL.md"
PAGE = ROOT / "docs" / "profili" / "backend.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "backend-fonti.md"
ID = re.compile(r"R-BACKEND-\d{2}")
FRAGMENT = ROOT / "templates" / "profiles" / "backend.toml"
AREA = "backend"
DESCRIPTION = ("Regole di tollgate per il codice dei server e delle API (anche i Worker di "
               "Cloudflare): le caricano in automatico gli agenti dell'area backend, non serve "
               "invocarla.")
RULE_LINE = re.compile(r"^R-BACKEND-\d{2}( \[blocca\])? \S")

# Una `Fonte:` contiene almeno una di queste forme, oppure il nome di una skill o di un agente
# ammesso e, nella stessa riga, la sua licenza (MIT o Apache-2.0).
SOURCE_FORMS = ("https://", "progetto di B, sezione", "catalogo", "spec del nucleo")
ALLOWED_NAMES = ("api-and-interface-design", "observability-and-instrumentation", "code-reviewer",
                 "python-reviewer", "security-reviewer", "workers-best-practices")
LICENSES = ("MIT", "Apache-2.0")

# Le scelte dell'utente del progetto di B e la regola che ciascuna diventa, con la sezione che la
# sua riga `Fonte:` deve nominare. Si cerca per id, non per parole.
USER_CHOICES = {
    "prima di scrivere un endpoint si leggono i contratti già presenti": (
        "R-BACKEND-01", ("progetto di B, sezione 3.4",)),
    "per le API del runtime e dei framework vale la documentazione ufficiale della versione": (
        "R-BACKEND-02", ("progetto di B, sezione 3.4",)),
    "le prove sui dati di KV, D1 e R2 sono locali": (
        "R-BACKEND-12", ("progetto di B, sezione 12",)),
}

# I sei pattern della decisione 2, nell'ordine.
PATTERNS = ["api/**", "server/**", "backend/**", "functions/**", "**/routes/**", "**/handlers/**"]

# I marcatori della decisione 3, nell'ordine, nelle due forme di virgolette: sono 23, perché
# `export function POST(` è uscito alla verifica delle fonti (nessuna pagina lo mostra).
MARKERS = [
    "cloudflare:workers", "from workers import", "ExportedHandler<",
    "require('express')", 'require("express")', "from 'express'", 'from "express"',
    "from 'fastify'", 'from "fastify"', "require('fastify')", 'require("fastify")',
    "from 'hono'", 'from "hono"',
    "from 'node:http'", 'from "node:http"', "require('node:http')", 'require("node:http")',
    "from fastapi import", "from flask import", "Deno.serve(",
    "export function GET(", "export async function GET(",
    "export async function POST(",
]
BARE_VENDOR_NAMES = {"express", "fastify", "hono", "fastapi", "flask", "deno", "node", "next",
                     "vercel", "cloudflare", "workers", "http", "supabase"}


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def backend_rules() -> list[tuple[str, bool, str, str, str]]:
    return rules(skill_text(), AREA)


def fragment() -> dict:
    return tomllib.loads(FRAGMENT.read_text(encoding="utf-8"))


class RulesBackendTest(unittest.TestCase):
    def test_frontmatter(self):
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-backend")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertEqual(fm["approved"], "2026-11-10")
        self.assertTrue(research.enforced(text))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole backend (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertEqual(titles[0], "## Prima di scrivere")
        for title in ("## Mentre lavori", "## Dove informarsi", "## Fonti"):
            self.assertIn(title, titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if l.startswith("R-BACKEND-")]
        self.assertTrue(ids)
        self.assertEqual(ids, [f"R-BACKEND-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in backend_rules()], ids)

    def test_area_rules_of_research_match_rules(self):
        parsed = backend_rules()
        self.assertEqual(research.area_rules(skill_text(), AREA),
                         ({r[0] for r in parsed}, {r[0] for r in parsed if r[1]}))

    def test_every_rule_has_a_source(self):
        for rid, _blocca, text, source, _judged in backend_rules():
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_every_rule_names_what_is_judged(self):
        for rid, *_rest, judged in backend_rules():
            with self.subTest(rule=rid):
                self.assertIn(judged, ("diff", "report", "nota"),
                              "manca la riga «Si giudica su: diff|report|nota»")
        self.assertTrue(all(JUDGED.match(f"Si giudica su: {j}") for *_r, j in backend_rules()))

    def test_every_rule_names_a_source_of_the_allowed_kinds(self):
        for rid, _b, _t, source, _j in backend_rules():
            with self.subTest(rule=rid):
                by_form = any(form in source for form in SOURCE_FORMS)
                by_skill = (any(name in source for name in ALLOWED_NAMES)
                            and any(lic in source for lic in LICENSES))
                self.assertTrue(by_form or by_skill, source)

    def test_extensions_of_the_sources_are_declared_as_our_choice(self):
        """R-BACKEND-05 (il task chiede il cambiamento) e R-BACKEND-09 (un caso d'errore per ogni
        input e risorsa) vanno oltre le fonti: la `Fonte:` lo dice, come R-BACKEND-02."""
        by_id = {r[0]: r[3] for r in backend_rules()}
        for rid in ("R-BACKEND-02", "R-BACKEND-05", "R-BACKEND-09", "R-BACKEND-12"):
            with self.subTest(rule=rid):
                self.assertIn("scelta nostra", by_id[rid])

    def test_some_rules_block(self):
        flags = [r[1] for r in backend_rules()]
        self.assertTrue(any(flags))
        self.assertFalse(all(flags))

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_blocking_rules_judged_on_diff_or_report(self):
        """Nei lavori senza passo la nota non c'è: una regola che blocca non si può giudicare
        solo sulla nota."""
        for rid, blocca, _text, _source, judged in backend_rules():
            if blocca:
                with self.subTest(rule=rid):
                    self.assertIn(judged, ("diff", "report"))

    def test_blocca_lines_have_text(self):
        """Una riga `R-BACKEND-NN [blocca]` senza testo sarebbe una regola nota ma non
        bloccante."""
        lines = [l for l in skill_text().split("\n") if l.startswith("R-BACKEND-")]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line[:30]):
                self.assertRegex(line, RULE_LINE)
        self.assertEqual(len(lines), len(backend_rules()))

    def test_endpoint_rules_say_how_to_recognize_an_endpoint(self):
        """Il revisore riconosce un endpoint nel diff da tre forme, dette prima delle regole."""
        intro = skill_text().split("\n## Prima di scrivere", 1)[0]
        lines = [l for l in intro.split("\n") if l.startswith("Un endpoint è")]
        self.assertEqual(len(lines), 1)
        for needle in ("registrata come rotta", "gestore esportato", "gestore `fetch`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, lines[0])

    def test_user_choices_covered(self):
        by_id = {r[0]: r for r in backend_rules()}
        for choice, (rid, sections) in USER_CHOICES.items():
            with self.subTest(choice=choice):
                self.assertIn(rid, by_id)
                for section in sections:
                    self.assertIn(section, by_id[rid][3])
        self.assertEqual(len({rid for rid, _ in USER_CHOICES.values()}), len(USER_CHOICES))

    def test_sources_section(self):
        fonti = skill_text().split("\n## Fonti", 1)[1]
        flat = " ".join(fonti.split())
        for needle in ("api-and-interface-design", "observability-and-instrumentation",
                       "everything-claude-code", "workers-best-practices",
                       "https://developers.cloudflare.com/workers/"):
            with self.subTest(needle=needle):
                self.assertIn(needle, fonti)
        self.assertRegex(flat, r"agent-skills.{0,40}licenza MIT")
        self.assertRegex(flat, r"everything-claude-code.{0,40}licenza MIT")
        self.assertRegex(flat, r"workers-best-practices.{0,40}Apache-2\.0")
        self.assertIn("con parole nostre", flat)
        self.assertIn("senza testo copiato", flat)

    def test_where_to_look_names_skills(self):
        informarsi = skill_text().split("\n## Dove informarsi", 1)[1].split("\n## ", 1)[0]
        for name in ("api-and-interface-design", "observability-and-instrumentation",
                     "workers-best-practices", "cloudflare"):
            with self.subTest(skill=name):
                self.assertIn(f"`{name}`", informarsi)
        self.assertNotIn("rules-performance", skill_text())  # decisione 9

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
        self.assertEqual(profile["agent"], "tollgate:implementer-backend")
        self.assertEqual(profile["reviewer"], "tollgate:reviewer-backend")
        for key in ("rules", "blocking_rules", "final_specialist"):
            self.assertNotIn(key, profile)
        detect = data["detect"]
        self.assertEqual(set(detect), {"content", "exclude"})
        self.assertEqual(detect["exclude"], ["supabase/"])
        self.assertEqual(detect["content"], MARKERS)

    def test_fragment_leaves_out_services_and_supabase(self):
        for pattern in fragment()["profile"]["paths"]:
            with self.subTest(pattern=pattern):
                for word in ("services", "supabase", ".github", "wrangler", "vercel"):
                    self.assertNotIn(word, pattern)

    def test_markers_are_pieces_of_lines_not_vendor_names(self):
        content = fragment()["detect"]["content"]
        self.assertEqual(len(content), len(set(content)))
        for marker in content:
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), BARE_VENDOR_NAMES)
                self.assertRegex(marker, r"[^a-z]", "il solo nome di un fornitore")
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
        self.assertEqual(found.exclude, ("supabase/",))
        self.assertEqual(len(found.patterns), len(PATTERNS))
        self.assertEqual(found.patterns[0], fragments.Pattern("root_folder", "api"))


class RulesBackendPageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (B5, Task 4). Si cercano gli id e i
    nomi, non le frasi."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in backend_rules()]

    def skip_if_approved(self):
        if "approved" in frontmatter(skill_text()):
            self.skipTest("la skill è approvata: la pagina non è più una proposta")

    def sources_text(self) -> str:
        return SOURCES.read_text(encoding="utf-8")

    def section(self, title: str) -> str:
        text = self.sources_text()
        self.assertIn(f"\n## {title}", text)
        return text.split(f"\n## {title}", 1)[1].split("\n## ", 1)[0]

    def test_sources_report_covers_every_rule(self):
        ok, named = set(), set()
        for cells in table_rows(self.section("Regole e fonti")):
            found = ID.findall(cells[0])
            named.update(found)
            if cells[-1].split(":")[0].strip() == "ok":
                ok.update(found)
        self.assertEqual(named - set(self.skill_ids()), set())
        self.assertEqual(set(self.skill_ids()) - ok, set())

    def test_removed_sources_are_not_in_the_skill(self):
        """Ogni riga `no` del rapporto è una fonte uscita o corretta: la regola resta coperta da
        una riga `ok` e la `Fonte:` della skill non rimanda più alla sezione che non la regge."""
        sources = {r[0]: r[3] for r in backend_rules()}
        rows = table_rows(self.section("Regole e fonti"))
        for cells in rows:
            self.assertIn(cells[-1].split(":")[0].strip(), ("ok", "no"),
                          "l'esito è `ok` o `no`, senza grassetto")
            if ID.fullmatch(cells[0]) and cells[-1] == "no":
                rid = cells[0]
                with self.subTest(rule=rid, source=cells[1][:40]):
                    self.assertIn(rid, sources)
                    self.assertTrue(any(c[0] == rid and c[-1] == "ok" for c in rows),
                                    "la regola non ha più una fonte ok")
        self.assertNotIn("Contract First", sources["R-BACKEND-01"])
        self.assertNotIn("Verification", sources["R-BACKEND-09"])
        self.assertIn("Fail Securely", sources["R-BACKEND-08"])
        self.assertIn("scelta nostra", sources["R-BACKEND-12"])
        self.assertIn("workers/configuration/secrets", sources["R-BACKEND-07"])

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
        self.assertEqual(len(fragment()["detect"]["content"]), 23)

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
                    m = re.fullmatch(r"(\d+) \(R-BACKEND-(\d{2})\)", cells[0])
                    self.assertIsNotNone(m)
                    self.assertEqual(int(m.group(1)), int(m.group(2)))

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in backend_rules()}
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
        self.assertEqual(seen, {r[0]: words[r[4]] for r in backend_rules()})

    def test_page_explains_what_changes(self):
        text = " ".join(PAGE.read_text(encoding="utf-8").split())
        low = text.lower()
        # il profilo si accende solo dove `init` lo propone e l'utente copia il blocco, da L1
        self.assertRegex(text, r"`/tollgate:init`[^.]*propone[^.]*\btu copi\b")
        self.assertRegex(text, r"livelli? L1 e L2\b")
        # le cartelle e le righe di import che lo accendono
        for name in ("api/", "server/", "backend/", "functions/", "routes/", "handlers/",
                     "cloudflare:workers", "from workers import", "express", "fastify", "hono",
                     "node:http", "from fastapi import", "from flask import", "Deno.serve(",
                     "export function GET(", "export async function POST("):
            with self.subTest(name=name):
                self.assertIn(f"`{name}", text)
        # `services/` non lo accende (progetto 12)
        self.assertRegex(text, r"`services/`[^.]*non (lo )?accend")
        # le edge function di Supabase sono di `database`, la configurazione di `infra`
        self.assertRegex(text, r"`supabase/`[^.]*`database`")
        self.assertRegex(low, r"configurazione di wrangler e di vercel[^.]*`infra`")
        # il Worker senza import da `cloudflare:workers` e senza il tipo non si trova da solo
        self.assertRegex(text, r"senza import da `cloudflare:workers`")
        self.assertIn("`ExportedHandler`", text)
        self.assertIn("`workers/`", text)
        # le scritture di Wrangler su KV, R2 e D1 (progetto 12)
        self.assertRegex(text, r"KV e R2[^.]*`--local`")
        self.assertRegex(text, r"D1[^.]*`--remote`")
        # un typecheck o i test delle API aggiunti a mano in `dod`, e `allow_no_tests` (decisione 8)
        self.assertIn("`dod`", text)
        self.assertRegex(low, r"senza chiedere")
        self.assertIn("allow_no_tests = true", text)
        self.assertIn("/tollgate:approve unverified-tests", text)
        # il marcatore uscito
        self.assertIn("`export function POST(`", text)

    def test_page_rinvio_says_what_stays_on_the_branch(self):
        """Decisione 15: con il rinvio su `main` va solo la parte dei Task 1-2. Vale solo finché
        `approved` non è nella skill: approvata, la pagina non offre più il rinvio."""
        self.skip_if_approved()
        text = PAGE.read_text(encoding="utf-8")
        section = " ".join(text.split("\n## Come rispondere", 1)[1].split())
        (rinvio,) = re.findall(r"\*\*Rinvio\.\*\*[^\n]*", section)
        for needle in ("`main`", "`b5-profilo-backend`", "esclusione per frammento",
                       "scritture di Wrangler", "script nei monorepo", "non vanno su `main`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, rinvio)

    def test_page_explains_the_terms(self):
        text = PAGE.read_text(encoding="utf-8")
        for needle in ("**Edge function**", "**`tollgate.toml`**", "namespace", "bucket",
                       "lanciatore (", "orchestratore di monorepo (", "**Gestore**"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_page_is_a_proposal(self):
        """Vale solo finché `approved` non è nella skill: col Task 5 la pagina è approvata."""
        self.skip_if_approved()
        self.assertNotIn("Approvata dall'utente", PAGE.read_text(encoding="utf-8"))

    def test_page_brings_the_open_choices_to_the_user(self):
        """Vale solo finché `approved` non è nella skill: col Task 5 «Da decidere tu» si chiude."""
        self.skip_if_approved()
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Da decidere tu", 1)[1].split("\n## ", 1)[0]
        for needle in ("R-BACKEND-02", "R-BACKEND-05", "R-BACKEND-09", "R-BACKEND-12",
                       "scelta nostra", "`routes/`", "`handlers/`", "`ExportedHandler`",
                       "senza import", "alla radice", "`dod`", "monorepo", "`supabase/`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_page_choices_count_matches_list(self):
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Cosa hai deciso", 1)[1].split("\n## ", 1)[0]
        count = len(re.findall(r"^\d+\. \*\*", section, re.M))
        words = {6: "sei", 7: "sette", 8: "otto", 9: "nove", 10: "dieci", 11: "undici"}
        self.assertIn(f"Su {words[count]} punti", section)

    def test_page_records_the_choices(self):
        """Con la skill approvata la pagina dice cosa ha deciso l'utente sui nove punti."""
        if "approved" not in frontmatter(skill_text()):
            self.skipTest("la skill non è approvata")
        text = PAGE.read_text(encoding="utf-8")
        section = text.split("\n## Cosa hai deciso", 1)[1].split("\n## ", 1)[0]
        for needle in ("R-BACKEND-02", "R-BACKEND-05", "R-BACKEND-09", "R-BACKEND-12",
                       "scelta nostra", "`routes/`", "`handlers/`", "`ExportedHandler`",
                       "senza import", "alla radice", "`dod`", "monorepo", "`supabase/`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)
        self.assertEqual(len(re.findall(r"Hai approvato: resta la proposta", section)), 9)

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
        self.assertFalse(ID.search(removed), "le regole tolte non usano id R-BACKEND-")

    def test_page_has_no_private_data(self):
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
