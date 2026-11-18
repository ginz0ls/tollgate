"""La skill `rules-database` (B7, Task 3): la bozza delle regole del profilo `database`, ognuna con
la sua fonte, e il frammento `templates/profiles/database.toml`; il rapporto delle fonti e la
pagina per l'utente (Task 4). `rules()` è quella di `test_rules_ai`."""
import getpass
import re
import socket
import tomllib
import unittest

from tests.helpers import ROOT
from tests.test_rules_ai import JUDGED, frontmatter, rules
from tests.test_rules_base import table_rows
from tests.test_rules_frontend import NUMBER_WORDS, as_number
from tollgate_analysis import research
from tollgate_core import fragments

SKILL = ROOT / "skills" / "rules-database" / "SKILL.md"
PAGE = ROOT / "docs" / "profili" / "database.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "database-fonti.md"
ID = re.compile(r"R-DATABASE-\d{2}")
FRAGMENT = ROOT / "templates" / "profiles" / "database.toml"
AREA = "database"
DESCRIPTION = ("Regole di tollgate per il database (migrazioni, schema, RLS, funzioni del "
               "database, edge function di Supabase): le caricano in automatico gli agenti "
               "dell'area database, non serve invocarla.")
RULE_LINE = re.compile(r"^R-DATABASE-\d{2}( \[blocca\])? \S")

# Una `Fonte:` contiene almeno una di queste forme, oppure il nome di una skill ammessa e, nella
# stessa riga, la sua licenza. `database-reviewer` di everything-claude-code non è una fonte
# (decisione 12): è l'agente di un plugin che l'utente ha disattivato.
SOURCE_FORMS = ("https://", "progetto di B, sezione", "catalogo", "spec del nucleo")
ALLOWED_SKILLS = {"supabase-postgres-best-practices": "MIT", "deprecation-and-migration": "MIT"}
OFFICIAL_PAGES = ("https://supabase.com/docs/", "https://www.postgresql.org/docs/",
                  "https://www.prisma.io/docs/", "https://orm.drizzle.team/docs/")
URL = re.compile(r"https://[^\s,;)]+")

# Le parole che rendono una regola specifica di PostgreSQL o di Supabase (decisione 9): la regola
# lo dice nel suo testo, perché con un'altra base dati il revisore risponde «non si applica».
POSTGRES_WORDS = re.compile(r"\bRLS\b|\bpolicy\b|security definer|concurrently|auth\.uid\(\)"
                            r"|edge function|row level security", re.I)
SCOPE = re.compile(r"[Vv]ale solo per[^.]*\b(PostgreSQL|Supabase)\b")

# Le scelte dell'utente del progetto di B e la regola che ciascuna diventa, con la sezione che la
# sua riga `Fonte:` deve nominare. Si cerca per id, non per parole. Ci sono **tutte** le regole la
# cui `Fonte:` cita il progetto di B.
USER_CHOICES = {
    "lo schema e le migrazioni esistenti si leggono prima di scriverne una": (
        "R-DATABASE-01", ("progetto di B, sezione 3.4",)),
    "la documentazione di Supabase o di PostgreSQL della versione del progetto": (
        "R-DATABASE-02", ("progetto di B, sezione 3.4",)),
    "le edge function di Supabase stanno nel profilo database": (
        "R-DATABASE-14", ("progetto di B, sezione 12",)),
    "nessuna scrittura sul progetto collegato": (
        "R-DATABASE-16", ("progetto di B, sezione 14",)),
}

# La decisione 2: i quattro pattern, nell'ordine. Nessun `exclude` (decisione 8).
PATTERNS = ["supabase/**", "**/migrations/**", "prisma/**", "**/*.sql"]
# La decisione 4: le righe di import delle definizioni di Drizzle, nelle due forme di virgolette.
DRIZZLE_MODULES = ("drizzle-orm/pg-core", "drizzle-kit")
MARKERS = [f"from {q}{m}{q}" for m in DRIZZLE_MODULES for q in ("'", '"')]


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def database_rules() -> list[tuple[str, bool, str, str, str]]:
    return rules(skill_text(), AREA)


def fragment() -> dict:
    return tomllib.loads(FRAGMENT.read_text(encoding="utf-8"))


class RulesDatabaseTest(unittest.TestCase):
    def test_frontmatter(self):
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-database")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertEqual(fm["approved"], "2026-11-17")

    def test_approved_skill_is_enforced(self):
        """Approvata il 2026-11-17 (Task 5): gli agenti dell'area la caricano."""
        self.assertTrue(research.enforced(skill_text()))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole database (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertEqual(titles[0], "## Prima di scrivere")
        for title in ("## Mentre lavori", "## Dove informarsi", "## Fonti"):
            self.assertIn(title, titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if l.startswith("R-DATABASE-")]
        self.assertTrue(ids)
        self.assertEqual(ids, [f"R-DATABASE-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in database_rules()], ids)

    def test_area_rules_of_research_match_rules(self):
        parsed = database_rules()
        self.assertEqual(research.area_rules(skill_text(), AREA),
                         ({r[0] for r in parsed}, {r[0] for r in parsed if r[1]}))

    def test_every_rule_has_a_source(self):
        for rid, _blocca, text, source, _judged in database_rules():
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_every_rule_names_what_is_judged(self):
        found = database_rules()
        for rid, *_rest, judged in found:
            with self.subTest(rule=rid):
                self.assertTrue(JUDGED.match(f"Si giudica su: {judged}"),
                                "manca la riga «Si giudica su: diff|report|nota»")

    def test_every_rule_names_a_source_of_the_allowed_kinds(self):
        for rid, _b, _t, source, _j in database_rules():
            with self.subTest(rule=rid):
                by_form = any(form in source for form in SOURCE_FORMS)
                by_skill = any(name in source and lic in source
                               for name, lic in ALLOWED_SKILLS.items())
                self.assertTrue(by_form or by_skill, source)

    def test_database_reviewer_is_not_a_source(self):
        """L'agente di un plugin disattivato non è una fonte (decisione 12)."""
        for rid, _b, _t, source, _j in database_rules():
            with self.subTest(rule=rid):
                self.assertNotIn("database-reviewer", source)
                self.assertNotIn("everything-claude-code", source)

    def test_urls_are_official_pages(self):
        """Ogni indirizzo di una `Fonte:` è una pagina di Supabase, PostgreSQL, Prisma o
        Drizzle."""
        seen = 0
        for rid, _b, _t, source, _j in database_rules():
            for url in URL.findall(source):
                seen += 1
                with self.subTest(rule=rid, url=url):
                    self.assertTrue(url.startswith(OFFICIAL_PAGES), url)
        self.assertGreater(seen, 10)

    def test_some_rules_block(self):
        flags = [r[1] for r in database_rules()]
        self.assertTrue(any(flags))
        self.assertFalse(all(flags))

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_blocking_rules_judged_on_diff_or_report(self):
        """Nei lavori senza passo la nota non c'è: una regola che blocca non si può giudicare
        solo sulla nota."""
        for rid, blocca, _text, _source, judged in database_rules():
            if blocca:
                with self.subTest(rule=rid):
                    self.assertIn(judged, ("diff", "report"))

    def test_blocca_lines_have_text(self):
        """Una riga `R-DATABASE-NN [blocca]` senza testo sarebbe una regola nota ma non
        bloccante."""
        lines = [l for l in skill_text().split("\n") if l.startswith("R-DATABASE-")]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line[:30]):
                self.assertRegex(line, RULE_LINE)
        self.assertEqual(len(lines), len(database_rules()))

    def test_migration_rules_say_how_to_recognize_a_migration(self):
        """Il revisore riconosce una migrazione, una policy e una edge function nel diff da una
        riga, detta prima delle regole."""
        intro = skill_text().split("\n## Prima di scrivere", 1)[0]
        lines = [l for l in intro.split("\n") if l.startswith("Nel diff si riconosce")]
        self.assertEqual(len(lines), 1)
        for needle in ("`supabase/migrations/`", "`migrations/`", "`.sql`", "`create`", "`alter`",
                       "`drop`", "policy", "edge function", "`supabase/functions/<nome>/`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, lines[0])

    def test_postgres_rules_say_their_scope(self):
        """Ogni regola che nomina RLS, policy, `security definer`, `concurrently`, `auth.uid()`
        o le edge function dice nel testo che vale solo per PostgreSQL o per Supabase."""
        checked = 0
        for rid, _b, text, _s, _j in database_rules():
            if POSTGRES_WORDS.search(text):
                checked += 1
                with self.subTest(rule=rid):
                    self.assertTrue(SCOPE.search(text), "manca «Vale solo per PostgreSQL…»")
        self.assertGreaterEqual(checked, 8)

    def test_general_rules_do_not_claim_a_scope(self):
        """Le regole per ogni base dati (01, 03, 04, 05) non si dichiarano di PostgreSQL."""
        by_id = {r[0]: r[2] for r in database_rules()}
        for rid in ("R-DATABASE-01", "R-DATABASE-03", "R-DATABASE-04", "R-DATABASE-05"):
            with self.subTest(rule=rid):
                self.assertFalse(SCOPE.search(by_id[rid]))

    def test_intro_names_the_other_databases(self):
        """La riga dell'ambito dice che la cartella `migrations/` può essere di un'altra base
        dati e che il revisore risponde «non si applica»."""
        intro = skill_text().split("\n## Prima di scrivere", 1)[0]
        flat = " ".join(intro.split())
        self.assertTrue(re.search(r"valgono solo per PostgreSQL e Supabase", flat),
                        "manca l'ambito di PostgreSQL e Supabase")
        for needle in ("SQLite", "MySQL", "Django", "non si applica"):
            with self.subTest(needle=needle):
                self.assertIn(needle, flat)

    def test_extensions_of_the_sources_are_declared_as_our_choice(self):
        """Le parti che vanno oltre le fonti dicono «scelta nostra» nella `Fonte:`: il percorso
        nel report di R-01, la via d'uscita di R-02, il report di R-04, R-06 e R-15, l'eccezione
        di R-05."""
        by_id = {r[0]: r[3] for r in database_rules()}
        for rid in ("R-DATABASE-01", "R-DATABASE-02", "R-DATABASE-04", "R-DATABASE-05",
                    "R-DATABASE-06", "R-DATABASE-15"):
            with self.subTest(rule=rid):
                self.assertIn("scelta nostra", by_id[rid])

    def test_user_choices_covered(self):
        by_id = {r[0]: r for r in database_rules()}
        for choice, (rid, sections) in USER_CHOICES.items():
            with self.subTest(choice=choice):
                self.assertIn(rid, by_id)
                for section in sections:
                    self.assertIn(section, by_id[rid][3])
        self.assertEqual(len({rid for rid, _ in USER_CHOICES.values()}), len(USER_CHOICES))
        # Nessuna regola che cita il progetto di B resta fuori dalla tabella.
        citing = {r[0] for r in database_rules() if "progetto di B" in r[3]}
        self.assertEqual(citing, {rid for rid, _ in USER_CHOICES.values()})

    def test_sources_section(self):
        fonti = skill_text().split("\n## Fonti", 1)[1]
        flat = " ".join(fonti.split())
        for needle in ("supabase-postgres-best-practices", "deprecation-and-migration",
                       "PostgreSQL", "Prisma", "Drizzle"):
            with self.subTest(needle=needle):
                self.assertIn(needle, fonti)
        self.assertTrue(re.search(r"supabase-postgres-best-practices.{0,80}licenza MIT", flat),
                        "manca la licenza della prima skill")
        self.assertTrue(re.search(r"deprecation-and-migration.{0,80}licenza MIT", flat),
                        "manca la licenza della seconda skill")
        self.assertIn("con parole nostre", flat)
        self.assertIn("senza testo copiato", flat)

    def test_where_to_look_names_skills(self):
        informarsi = skill_text().split("\n## Dove informarsi", 1)[1].split("\n## ", 1)[0]
        for name in ("supabase-postgres-best-practices", "deprecation-and-migration"):
            with self.subTest(skill=name):
                self.assertIn(f"`{name}`", informarsi)
        for text in ("https://supabase.com/docs/", "https://www.postgresql.org/docs/current/",
                     "R-DATABASE-01"):
            with self.subTest(text=text):
                self.assertIn(text, informarsi)
        self.assertNotIn("database-reviewer", skill_text())

    def test_no_long_quotations(self):
        """Qui si controlla solo che la skill non porti citazioni lunghe tra virgolette."""
        for line in skill_text().split("\n"):
            for quoted in re.findall(r"«([^»]*)»", line):
                with self.subTest(quoted=quoted[:40]):
                    self.assertLessEqual(len(quoted.split()), 12)

    def test_fragment_matches_decisions(self):
        data = fragment()
        self.assertEqual(set(data), {"profile", "detect"})
        profile = data["profile"]
        self.assertEqual(profile["kind"], "vertical")
        self.assertEqual(profile["min_level"], "L2")
        self.assertEqual(profile["paths"], PATTERNS)
        self.assertEqual(profile["skills"], [])
        self.assertEqual(profile["reviewer_skills"], [])
        self.assertEqual(profile["commands"], {})
        self.assertEqual(profile["dod"], [])
        self.assertEqual(profile["agent"], "tollgate:implementer-database")
        self.assertEqual(profile["reviewer"], "tollgate:reviewer-database")
        self.assertEqual(profile["final_specialist"], "tollgate:final-database")
        self.assertTrue(profile["checklist"].strip())
        for word in ("reversibili", "dati esistenti", "RLS", "indici"):
            with self.subTest(word=word):
                self.assertIn(word, profile["checklist"])
        for key in ("rules", "blocking_rules", "cross"):
            self.assertNotIn(key, profile)
        detect = data["detect"]
        self.assertEqual(set(detect), {"content"})
        self.assertEqual(detect["content"], MARKERS)

    def test_markers_are_drizzle_imports(self):
        content = fragment()["detect"]["content"]
        self.assertEqual(len(content), len(set(content)))
        for marker in content:
            with self.subTest(marker=marker):
                self.assertRegex(marker, r"^from ['\"]")
                self.assertIn(marker[len("from '"):-1], DRIZZLE_MODULES)
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

    def test_fragment_loads_through_the_loader(self):
        (found,) = [f for f in fragments.load(ROOT) if f.area == AREA]
        self.assertEqual(found.source, FRAGMENT)
        self.assertEqual(found.skill_path, SKILL)
        self.assertEqual(found.detect, tuple(MARKERS))
        self.assertEqual(found.exclude, ())
        self.assertEqual(
            found.patterns,
            (fragments.Pattern("root_folder", "supabase"),
             fragments.Pattern("folder", "migrations"),
             fragments.Pattern("root_folder", "prisma"), fragments.Pattern("ext", "sql")))


# Le parole che i punti di «Cosa hai deciso» nominano (pagina), con la proposta di ognuno.
CHOICE_NEEDLES = (
    "`**/migrations/**`", "`src/components/migrations/`", "`app/migrations/`",
    "`docs/migrations/`", "`**/schema.*`", "`apps/web/supabase/`", "`packages/db/prisma/`",
    "`web/supabase/`", "`server/prisma/`", "`apps/api/supabase/`", "`drizzle-orm/pg-core`",
    "primo blocco", "`supabase/functions/agents/`", "`supabase/functions/chat/prompts/`",
    "`prisma/seed.ts`", "`prisma/ai/`", "`src/prisma/contract.prisma`", "Prisma 8",
    "`database/migrations/`", "`blog/migrations/`", "D1", "Laravel", "Django", "non si applicano",
    "`supabase/functions/Dockerfile`", "`supabase/docker/docker-compose.yml`",
    "`server/db/schema.sql`", "`src/ai/queries.sql`", "`tests/fixtures/schema.sql`",
    "`tests/migrations/`", "`prisma migrate dev`", "`database-reviewer`", "`dod`", "Alembic",
    "Rails", "R-DATABASE-01", "R-DATABASE-02", "R-DATABASE-04", "R-DATABASE-05",
    "R-DATABASE-06", "R-DATABASE-15", "scelta nostra")
# Le regole con «scelta nostra» nella `Fonte:`: la pagina le nomina in «Cosa hai deciso».
OUR_CHOICES = ["R-DATABASE-01", "R-DATABASE-02", "R-DATABASE-04", "R-DATABASE-05",
               "R-DATABASE-06", "R-DATABASE-15"]

# Il testo della proposta di ognuno dei diciassette punti, come nel Task 4: l'utente li ha
# approvati tutti il 2026-11-17 (copiato da `task-4-proposte.md`, che non sta nel repo).
PROPOSALS = (
    'tenerlo largo, perché il catalogo lo chiede e copre le migrazioni di tutti gli strumenti. Chi ha un caso toglie la riga dal blocco a mano.',
    'lasciare così.',
    'lasciarlo fuori.',
    'lasciare così; chi ha un monorepo aggiunge a mano la sua cartella al blocco.',
    'lasciare così.',
    'lasciare così (è codice che parla con un modello, quindi difendibile) e rimandare il rimedio.',
    'lasciare così.',
    'lasciare così e riprendere il caso quando Prisma 8 esce e un tuo progetto lo usa.',
    'tenere così, perché sono comunque schema.',
    'lasciare così.',
    'lasciare così.',
    'lasciare così; chi non lo vuole toglie il file o la cartella dal blocco.',
    'tenerlo così, dalla parte sicura.',
    'non citarlo.',
    'lasciarlo vuoto, come `infra`, `backend` e `frontend`.',
    'lasciarle fuori; chi ne ha le aggiunge a mano.',
    'tenerle tutte e sei.',
)
# Le voci della `Fonte:` con esito `no` alla prima verifica (Step 1): la skill non le porta più.
WORDS_OF_REMOVED_SOURCES = ("DATABASE_URL", "lavorano sul progetto collegato")


def normal(text: str) -> str:
    return " ".join(text.split())


def voci(source: str) -> list[str]:
    """Le voci di una `Fonte:`: le parti separate da `;` fuori dalle parentesi, senza quelle
    «scelta nostra», e dentro una parte le voci unite da « e » (due indirizzi, la spec del
    nucleo, la sezione 2.3 del catalogo) come voci distinte."""
    parts, depth, current = [], 0, ""
    for char in source:
        depth += (char == "(") - (char == ")")
        if char == ";" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    found = []
    for part in parts:
        if "scelta nostra" in part:
            continue
        found.extend(normal(v) for v in re.split(r" e (?=https://|spec del nucleo|\d\.\d )", part))
    return found


class RulesDatabasePageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (B7, Task 4). Si cercano gli id e i
    nomi, non le frasi."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in database_rules()]

    def section(self, title: str) -> str:
        text = SOURCES.read_text(encoding="utf-8")
        self.assertTrue(f"\n## {title}" in text, "manca una sezione del rapporto")
        return text.split(f"\n## {title}", 1)[1].split("\n## ", 1)[0]

    def page_section(self, title: str) -> str:
        text = PAGE.read_text(encoding="utf-8")
        self.assertTrue(f"\n## {title}" in text, "manca una sezione della pagina")
        return text.split(f"\n## {title}", 1)[1].split("\n## ", 1)[0]

    def page_text(self) -> str:
        return normal(PAGE.read_text(encoding="utf-8"))

    def test_sources_report_covers_every_rule(self):
        """Per ogni voce di una `Fonte:` (tolte le parti «scelta nostra», con i due indirizzi
        uniti da « e » presi come voci distinte) la tabella ha una riga `ok` di quella regola la cui
        cella «Fonte» la contiene."""
        rows = table_rows(self.section("Regole e fonti"))
        named = set()
        for cells in rows:
            self.assertIn(cells[-1], ("ok", "no"), "l'esito è `ok` o `no`, senza grassetto")
            named.update(ID.findall(cells[0]))
        self.assertEqual(named - set(self.skill_ids()), set())
        for rid, _b, _t, source, _j in database_rules():
            found = voci(source)
            self.assertTrue(found, rid)
            for voce in found:
                with self.subTest(rule=rid, voce=voce[:50]):
                    self.assertTrue(
                        any(c[0] == rid and c[-1] == "ok" and voce in normal(c[1])
                            for c in rows),
                        "nessuna riga `ok` del rapporto per questa voce")

    def test_removed_sources_are_not_in_the_skill(self):
        """Una riga `no` del rapporto è una voce uscita dalla `Fonte:`: la skill non la porta
        più e la regola ha ancora una riga `ok`. Il rapporto ha le due righe `no` della prima
        verifica (R-DATABASE-16), e la skill non porta più le loro parole."""
        sources = {r[0]: normal(r[3]) for r in database_rules()}
        rows = table_rows(self.section("Regole e fonti"))
        removed = [c for c in rows if c[-1] == "no"]
        self.assertEqual([c[0] for c in removed], ["R-DATABASE-16", "R-DATABASE-16"])
        for cells in removed:
            with self.subTest(rule=cells[0], source=cells[1][:40]):
                self.assertNotIn(normal(cells[1]), sources[cells[0]])
                self.assertTrue(any(c[0] == cells[0] and c[-1] == "ok" for c in rows),
                                "la regola non ha più una fonte ok")
        for word in WORDS_OF_REMOVED_SOURCES:
            with self.subTest(word=word):
                self.assertFalse(word in sources["R-DATABASE-16"],
                                 "R-DATABASE-16 porta ancora una parte uscita")

    def test_skill_carries_the_corrections_of_the_verification(self):
        """Le correzioni dopo la verifica: gli indirizzi di R-02 e R-16, i testi di R-03 e R-06
        e la riga dell'introduzione che dice come si riconosce uno schema nel diff, con il
        criterio `create table` dichiarato «scelta nostra»."""
        by_id = {r[0]: r for r in database_rules()}
        msg = "manca una correzione della verifica nella skill"
        checks = (
            ("https://supabase.com/docs/guides/local-development/cli/config", "R-DATABASE-02", 3),
            ("https://supabase.com/docs/guides/functions/deploy", "R-DATABASE-16", 3),
            ("https://supabase.com/docs/guides/functions/secrets", "R-DATABASE-16", 3),
            ("database configurato", "R-DATABASE-16", 3),
            ("esisteva prima del lavoro", "R-DATABASE-03", 2),
            ("che il diff non crea", "R-DATABASE-06", 2))
        for needle, rid, column in checks:
            with self.subTest(rule=rid, needle=needle):
                self.assertTrue(needle in by_id[rid][column], msg)
        for needle, rid, column in (("già presente nel repo", "R-DATABASE-03", 2),
                                    ("che ha già dati", "R-DATABASE-06", 2)):
            with self.subTest(rule=rid, needle=needle):
                self.assertFalse(needle in by_id[rid][column], msg)
        intro = skill_text().split("\n## Prima di scrivere", 1)[0]
        lines = [l for l in intro.split("\n") if l.startswith("Uno schema si riconosce")]
        self.assertEqual(len(lines), 1)
        for needle in ("`schema.prisma`", "`create table`", "`drizzle-orm/pg-core`",
                       "scelta nostra"):
            with self.subTest(needle=needle):
                self.assertTrue(needle in lines[0], msg)

    def test_sources_report_covers_the_introduction(self):
        """La riga dell'introduzione sullo schema ha nel rapporto una riga `ok` per
        `schema.prisma` e una per l'import di `drizzle-orm/pg-core`, e `create table` sta tra le
        parti «scelta nostra»."""
        rows = [c for c in table_rows(self.section("Regole e fonti")) if c[0] == "Introduzione"]
        for needle in ("schema.prisma", "drizzle-orm/pg-core"):
            with self.subTest(needle=needle):
                self.assertTrue(any(needle in c[1] and c[-1] == "ok" for c in rows),
                                "manca la riga dell'introduzione nel rapporto")
        self.assertFalse(any("create table" in c[1] for c in rows),
                         "create table è una scelta nostra, non ha una riga ok")
        self.assertTrue("`create table`" in self.section("Parti dichiarate «scelta nostra»"),
                        "create table non è tra le parti «scelta nostra»")

    def test_sources_report_records_the_second_pass(self):
        """Il rapporto dice che il verificatore ha riletto le voci cambiate, con la data, e non
        dice più che resta da rileggere."""
        text = normal(SOURCES.read_text(encoding="utf-8"))
        self.assertTrue(re.search(r"[Ss]econdo passaggio[^.]*\d{4}-\d{2}-\d{2}", text),
                        "manca il secondo passaggio con la data")
        self.assertFalse(re.search(r"rilegg\w+ dopo il commit", text),
                         "il rapporto dice ancora che il verificatore deve rileggere")

    def test_sources_quotations_are_one_line(self):
        """Ogni citazione tra «» del rapporto sta su una riga e non supera trenta parole."""
        text = SOURCES.read_text(encoding="utf-8")
        found = re.findall(r"«([^»]*)»", text)
        self.assertGreater(len(found), 30)
        for quoted in found:
            with self.subTest(quoted=quoted[:40]):
                self.assertNotIn("\n", quoted)
                self.assertLessEqual(len(quoted.split()), 30)

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
        self.assertEqual(len(fragment()["detect"]["content"]), 4)

    def test_page_lists_every_rule(self):
        text = PAGE.read_text(encoding="utf-8")
        ids = [ID.search(cells[0]).group(0) for cells in table_rows(text) if ID.search(cells[0])]
        self.assertEqual(ids, self.skill_ids())

    def test_page_number_matches_id(self):
        for cells in table_rows(PAGE.read_text(encoding="utf-8")):
            if ID.search(cells[0]):
                with self.subTest(cell=cells[0]):
                    m = re.fullmatch(r"(\d+) \(R-DATABASE-(\d{2})\)", cells[0])
                    self.assertIsNotNone(m)
                    self.assertEqual(int(m.group(1)), int(m.group(2)))

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in database_rules()}
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
        self.assertEqual(seen, {r[0]: words[r[4]] for r in database_rules()})

    def test_page_counts_match_skill(self):
        """I numeri della pagina (in lettere o in cifre) per le regole e per quelle che
        bloccano sono quelli della skill."""
        section = normal(self.page_section("Cosa sono"))
        total = re.search(r"\bSono (\w+) regole in più", section)
        self.assertIsNotNone(total, "manca «Sono N regole in più»")
        self.assertEqual(as_number(total.group(1)), len(database_rules()))
        block = re.search(r"\b(\w+) di queste bloccano", section)
        self.assertIsNotNone(block, "manca «N di queste bloccano»")
        self.assertEqual(as_number(block.group(1)), sum(1 for r in database_rules() if r[1]))

    def test_page_explains_what_changes(self):
        text = self.page_text()
        # il profilo si accende solo dove `init` lo propone e l'utente copia il blocco
        self.assertTrue(re.search(r"`/tollgate:init`[^.]*propone[^.]*\btu copi\b", text),
                        "manca il passo «init propone, tu copi»")
        # L2: il livello minimo, il lavoro che sale, il gate della PR (D14), lo specialista
        for needle in ("`min_level = \"L2\"`", "`level_below_minimum`", "`final-database`",
                       "`/tollgate:finish`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        self.assertTrue(re.search(r"lavoro[^.]*\bL2\b[^.]*spec[^.]*piano", text),
                        "manca il passaggio a L2 con spec e piano da approvare")
        self.assertTrue(re.search(r"specialista finale[^.]*\bL2\b", text),
                        "manca lo specialista finale in L2")
        # un blocco già dichiarato a mano (D12)
        for needle in ("`[profiles.database]`", "`checklist`", "`init --update`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        # `dod` vuoto con l'esempio, e i comandi del `dod` senza veto
        for needle in ("`dod`", "db_reset = \"supabase db reset --local\"",
                       "db_test = \"supabase test db\"", "`--remote`", "`--linked`",
                       "`--db-url`", "senza chiedere"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        # gli effetti di Supabase della scelta del 12 novembre e i loro costi
        for needle in ("`db push`", "`--local`", "`functions deploy`", "`secrets set`",
                       "`npx eslint supabase --fix`", "`storage ls`", "`unlink`", "`bootstrap`",
                       "`login`", "`logout`", "CLI 2", "`db dump`", "`migration list`",
                       "`inspect db`", "`functions list`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        # Prisma e Drizzle: chiedono, anche in locale; un'opzione prima del sottocomando no
        for needle in ("`prisma migrate dev`", "`prisma db push`", "`drizzle-kit push`",
                       "`push:pg`", "`prisma db init`", "`prisma db migrate`",
                       "`prisma generate`", "`drizzle-kit generate`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        self.assertTrue(re.search(r"opzione di `prisma` prima del sottocomando[^.]*senza", text),
                        "manca il costo dell'opzione prima del sottocomando")
        # un `.sql` dentro la cartella di un altro profilo resta a quel profilo
        self.assertTrue(
            re.search(r"`\.sql`[^.]*cartella di un altro profilo[^.]*resta a quel profilo", text),
            "manca la regola dei `.sql` degli altri profili")
        # una cartella `supabase/` con un `.tsx` va a `database` (P14 di B6)
        self.assertIn("`supabase/functions/og/index.tsx`", text)
        # un file di un altro profilo rende attivo `database` e il lavoro sale a L2
        self.assertTrue(re.search(r"attivo[^.]*\bL2\b", text), "manca «database attivo, lavoro L2»")

    def test_page_approval_date_matches_skill(self):
        approved = frontmatter(skill_text())["approved"]
        found = re.findall(r"^Approvata dall'utente il (\d{4}-\d{2}-\d{2})\.$",
                           PAGE.read_text(encoding="utf-8"), re.M)
        self.assertEqual(found, [approved], "la data della pagina non è quella della skill")

    def test_approved_skill_leaves_no_pending_decisions(self):
        """Né la pagina né il rapporto rimandano a «Da decidere tu» o dicono che qualcosa va
        ancora confermato."""
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertFalse("Da decidere tu" in text, "resta un rimando a «Da decidere tu»")
                self.assertFalse(re.search(r"[Vv]a confermat[ao] dall'utente", text),
                                 "resta una conferma da avere")

    def test_approved_page_has_no_pending_sections(self):
        """Approvata, la pagina non ha più «Come rispondere» né «Rinvio», e non chiede più di
        approvare."""
        text = PAGE.read_text(encoding="utf-8")
        self.assertFalse("\n## Come rispondere" in text, "resta la sezione «Come rispondere»")
        self.assertFalse("**Rinvio.**" in text, "resta il rinvio")
        self.assertFalse(re.search(r"finché non le approvi|dopo che avrai approvato", text),
                         "la pagina chiede ancora di approvare")

    def test_page_records_the_choices(self):
        """«Cosa hai deciso» porta il testo di ognuna delle diciassette proposte, uguale a quello
        del Task 4, e dice che l'utente le ha approvate."""
        section = normal(self.page_section("Cosa hai deciso"))
        for needle in CHOICE_NEEDLES:
            with self.subTest(needle=needle):
                self.assertTrue(needle in section, "manca un testo atteso")
        self.assertEqual(len(PROPOSALS), 17)
        for number, proposal in enumerate(PROPOSALS, 1):
            with self.subTest(point=number):
                self.assertTrue(f"Proposta: {proposal}" in section,
                                "il testo della proposta non è quello approvato")

    def test_page_records_the_introduction_as_our_choice(self):
        """Il punto 17 dice anche che l'introduzione della skill (il `create table` in un
        `.sql`) è una scelta nostra, e la skill la dichiara tale."""
        section = normal(self.page_section("Cosa hai deciso"))
        point = section.split(" 17. ", 1)[1]
        for needle in ("introduzione della skill", "create table", "scelta nostra"):
            with self.subTest(needle=needle):
                self.assertTrue(needle in point, "manca un testo atteso nel punto 17")
        intro = normal(skill_text().split("\n# Regole database", 1)[1]).split("Nel diff", 1)[0]
        self.assertTrue("create table" in intro and "scelta nostra" in intro,
                        "l'introduzione della skill non dichiara la scelta")

    def test_page_choices_count_matches_list(self):
        """Il numero scritto in «Su N punti» è quello dei punti, e ogni punto ha il suo costo e
        la sua proposta."""
        section = self.page_section("Cosa hai deciso")
        items = re.split(r"^(?=\d+\. \*\*)", section, flags=re.M)[1:]
        count = len(items)
        self.assertGreaterEqual(count, 15)
        words = {n: w for w, n in NUMBER_WORDS.items() if w != "uno"}
        if count not in words:
            self.fail(f"{count} punti: il dizionario dei numeri arriva a trenta")
        self.assertTrue(f"Su {words[count]} punti" in section, "manca «Su N punti»")
        self.assertEqual(len(re.findall(r"^\s+Hai approvato la proposta\.$", section, re.M)), count,
                         "ogni punto dice che la proposta è stata approvata")
        for item in items:
            number = item.split(".", 1)[0]
            with self.subTest(point=number):
                self.assertTrue("Costo: " in item, "il punto non ha il suo «Costo:»")
                self.assertEqual(len(re.findall(r"^\s+Proposta: ", item, re.M)), 1,
                                 "il punto non ha la sua proposta")

    def test_page_intro_numbers_match_skill(self):
        """«N regole su sedici» (solo PostgreSQL e Supabase) e «N punti» dell'introduzione sono
        quelli della skill e dell'elenco di «Cosa hai deciso»."""
        text = self.page_text()
        scoped = sum(1 for r in database_rules() if SCOPE.search(r[2]))
        found = re.search(r"\b(\w+) regole su (\w+)\b[^.]*riguardano solo PostgreSQL", text)
        self.assertIsNotNone(found, "manca «N regole su M riguardano solo PostgreSQL»")
        self.assertEqual(as_number(found.group(1)), scoped)
        self.assertEqual(as_number(found.group(2)), len(database_rules()))
        intro = text.split("## Cosa sono", 1)[0]
        points = re.search(r"su (\w+) punti dubbi", intro)
        self.assertIsNotNone(points, "manca «su N punti dubbi»")
        listed = len(re.findall(r"^\d+\. \*\*", self.page_section("Cosa hai deciso"), re.M))
        self.assertEqual(as_number(points.group(1)), listed)

    def test_our_choices_are_named_in_the_choices(self):
        """Ogni obbligo con «scelta nostra» nella `Fonte:` è nominato in «Cosa hai deciso»."""
        by_id = {r[0]: r[3] for r in database_rules()}
        ours = [rid for rid, source in by_id.items() if "scelta nostra" in source]
        self.assertEqual(ours, OUR_CHOICES)
        section = self.page_section("Cosa hai deciso")
        for rid in ours:
            with self.subTest(rule=rid):
                self.assertTrue(rid in section, "manca la regola in «Cosa hai deciso»")

    def test_page_explains_the_terms(self):
        text = PAGE.read_text(encoding="utf-8")
        for needle in ("**Migrazione**", "**RLS**", "**Policy**", "**Edge function**",
                       "**Specialista finale**", "**Schema**", "**Supabase**", "**PostgreSQL**",
                       "**Prisma**", "**Drizzle**", "**Profilo**", "**Livello L2**",
                       "**CLI**", "**Percorso esatto**", "**Percorso per estensione**",
                       "**Marcatore**",
                       "**Progetto collegato**", "**`tollgate.toml`**", "**`dod`**",
                       "**Indice**", "**Chiave esterna**", "**Vista**"):
            with self.subTest(needle=needle):
                self.assertTrue(needle in text, "manca un termine spiegato")

    def test_page_has_removed_section_without_rule_ids(self):
        removed = self.page_section("Regole tolte dalla verifica")
        self.assertTrue(removed.strip())
        self.assertFalse(ID.search(removed), "le regole tolte non usano id R-DATABASE-")

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
