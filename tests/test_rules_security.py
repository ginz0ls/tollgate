"""La skill `rules-security` (C2, Task 4): la bozza delle regole del profilo `security`, ognuna con
la sua fonte, e il frammento `templates/profiles/security.toml`; il rapporto delle fonti e la
pagina per l'utente (Task 5); l'approvazione dell'utente del 2026-11-23 (Task 6). `rules()` è
quella di `test_rules_ai`."""
import getpass
import re
import socket
import tempfile
import tomllib
import unittest
from pathlib import Path

from tests.helpers import ROOT, git, make_repo
from tests.test_rules_ai import JUDGED, frontmatter, rules
from tests.test_rules_base import table_rows
from tests.test_rules_frontend import NUMBER_WORDS
from tollgate_analysis import research
from tollgate_core import fragments
from tollgate_core import git as core_git
from tollgate_flow import init

SKILL = ROOT / "skills" / "rules-security" / "SKILL.md"
FRAGMENT = ROOT / "templates" / "profiles" / "security.toml"
PAGE = ROOT / "docs" / "profili" / "security.md"
SOURCES = ROOT / "docs" / "profili" / "verifiche" / "security-fonti.md"
ID = re.compile(r"R-SECURITY-\d{2}")
# Nomi utente generici (container, CI): sono parole comuni nel testo e non identificano nessuno.
GENERIC_NAMES = frozenset({"root", "user", "runner", "ubuntu", "dev", "test", "admin", "github"})
AREA = "security"
DESCRIPTION = ("Regole di tollgate per la sicurezza (accesso, login, token, password, cookie di "
               "sessione, middleware e proxy, segreti): le caricano in automatico gli agenti "
               "dell'area security, non serve invocarla.")
RULE_LINE = re.compile(r"^R-SECURITY-\d{2}( \[blocca\])? \S")
RULE_ID = re.compile(r"^(R-SECURITY-\d{2})( \[blocca\])? \S")
ANY_ID = re.compile(r"R-[A-Z]+-\d{2}")
OVERLAP = "Si sovrappone a:"
# La data dell'approvazione dell'utente (Task 6, Step 1: «Approvo», senza modifiche).
APPROVED = "2026-11-23"

# Una `Fonte:` contiene almeno una di queste forme, oppure il nome di una skill o di un agente
# ammesso e, nella stessa riga, la sua licenza (catalogo 4, decisione 8).
SOURCE_FORMS = ("https://", "progetto di C, sezione", "progetto di B, sezione", "catalogo",
                "spec del nucleo", "idea di OWASP Cheat Sheet", "idea di Trail of Bits")
ALLOWED_SKILLS = {"security-and-hardening": "MIT", "security-auditor": "MIT"}
# Le fonti CC BY-SA 4.0 (OWASP Cheat Sheet Series, Trail of Bits): solo idee, scritte «idea di …».
CC_BY_SA = re.compile(r"(?<!idea di )(?:OWASP|Trail of Bits)")

# Le scelte dell'utente che diventano regole e le parole che la `Fonte:` della regola deve avere.
# Si cerca per id, non per parole. Ci sono **tutte** le regole la cui `Fonte:` cita il progetto
# di C, sezione 11 (le scelte dell'utente del 22/11/2026, «Sicurezza fin dal progetto»).
USER_CHOICE_SOURCE = "progetto di C, sezione 11"
USER_CHOICES = {
    "chi può arrivare al codice cambiato, cosa può fare e quale controllo lo ferma": (
        "R-SECURITY-01", (USER_CHOICE_SOURCE,)),
    "un controllo d'accesso ha il test del caso negato": (
        "R-SECURITY-03", (USER_CHOICE_SOURCE, "catalogo 2.3")),
    "valori predefiniti che rifiutano": ("R-SECURITY-05", (USER_CHOICE_SOURCE,)),
    "nessun segreto nel codice né nei log": ("R-SECURITY-10", (USER_CHOICE_SOURCE,)),
    "input non fidato validato al confine": ("R-SECURITY-12", (USER_CHOICE_SOURCE,)),
}
# La decisione 15: le regole su segreti e input ripetono regole approvate e lo dicono con la riga
# «Si sovrappone a:», con gli id approvati. Nessun'altra regola ha quella riga.
OVERLAPS = {
    "R-SECURITY-10": {"R-BACKEND-07", "R-BACKEND-08", "R-INFRA-05", "R-INFRA-06",
                      "R-DATABASE-13"},
    "R-SECURITY-12": {"R-BACKEND-03", "R-BACKEND-06"},
}

# La decisione 2: i sei pattern, nell'ordine.
PATTERNS = ["**/auth/**", "**/middleware.*", "**/proxy.ts", "**/proxy.js", "**/security/**",
            "**/rls/**"]
# La decisione 4 con l'esito del punto (a) del Task 4, Step 0: i marcatori confermati, in
# quest'ordine. Tolti: `require('bcryptjs')`, `from 'jsonwebtoken'` (nelle due virgolette).
MARKERS = [
    "from 'bcrypt'", 'from "bcrypt"', "require('bcrypt')", 'require("bcrypt")',
    "from 'bcryptjs'", 'from "bcryptjs"',
    "from 'argon2'", 'from "argon2"', "require('argon2')", 'require("argon2")',
    "require('jsonwebtoken')", 'require("jsonwebtoken")',
    "from 'jose'", 'from "jose"',
    "from 'iron-session'", 'from "iron-session"',
    "import bcrypt", "from argon2 import", "from passlib", "import jwt", "from jose import",
]
REMOVED_MARKERS = ("require('bcryptjs')", 'require("bcryptjs")', "from 'jsonwebtoken'",
                   'from "jsonwebtoken"')
# La decisione 10, alla lettera.
CHECKLIST = ("chi arriva al codice cambiato e cosa può fare; accesso negato provato da un test; "
             "nessun segreto nel diff; valori predefiniti che rifiutano")


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def security_rules() -> list[tuple[str, bool, str, str, str]]:
    return rules(skill_text(), AREA)


def overlaps(text: str) -> dict[str, set[str]]:
    """Per ogni regola con una riga «Si sovrappone a: …» (fra la regola e la successiva, o il
    titolo successivo), gli id che la riga nomina."""
    found: dict[str, set[str]] = {}
    current = None
    for line in text.split("\n"):
        if m := RULE_ID.match(line):
            current = m.group(1)
        elif line.startswith("#"):
            current = None
        elif current and line.startswith(OVERLAP):
            found[current] = set(ANY_ID.findall(line))
    return found


def fragment() -> dict:
    return tomllib.loads(FRAGMENT.read_text(encoding="utf-8"))


class RulesSecurityTest(unittest.TestCase):
    def test_frontmatter(self):
        """Approvata dall'utente il 2026-11-23 (Task 6): `approved` dopo `version`, e gli agenti
        dell'area la caricano."""
        text = skill_text()
        fm = frontmatter(text)
        self.assertEqual(fm["name"], "rules-security")
        self.assertEqual(fm["description"], DESCRIPTION)
        self.assertEqual(fm["version"], "1")
        self.assertEqual(fm["approved"], APPROVED)
        self.assertEqual(list(fm), ["name", "description", "version", "approved"])
        self.assertTrue(research.enforced(text))

    def test_has_title(self):
        body = skill_text().split("\n---\n", 1)[1].lstrip("\n")
        self.assertEqual(body.split("\n", 1)[0], "# Regole security (versione 1)")

    def test_first_section_is_prima_di_scrivere(self):
        titles = [l for l in skill_text().split("\n") if l.startswith("## ")]
        self.assertTrue(titles, "nessun titolo «## …»")
        self.assertEqual(titles[0], "## Prima di scrivere")
        for title in ("## Mentre lavori", "## Dove informarsi", "## Fonti"):
            self.assertIn(title, titles)

    def test_rule_ids_consecutive(self):
        ids = [l.split(" ")[0] for l in skill_text().split("\n") if l.startswith("R-SECURITY-")]
        self.assertTrue(ids, "nessuna regola R-SECURITY-NN")
        self.assertEqual(ids, [f"R-SECURITY-{n:02d}" for n in range(1, len(ids) + 1)])
        self.assertEqual([r[0] for r in security_rules()], ids)

    def test_area_rules_of_research_match_rules(self):
        parsed = security_rules()
        self.assertTrue(parsed, "nessuna regola R-SECURITY-NN")
        self.assertEqual(research.area_rules(skill_text(), AREA),
                         ({r[0] for r in parsed}, {r[0] for r in parsed if r[1]}))

    def test_every_rule_has_a_source(self):
        found = security_rules()
        self.assertTrue(found, "nessuna regola R-SECURITY-NN")
        for rid, _blocca, text, source, _judged in found:
            with self.subTest(rule=rid):
                self.assertTrue(text)
                self.assertTrue(source, "manca la riga «Fonte: …»")

    def test_every_rule_names_a_source_of_the_allowed_kinds(self):
        found = security_rules()
        self.assertTrue(found, "nessuna regola R-SECURITY-NN")
        for rid, _b, _t, source, _j in found:
            with self.subTest(rule=rid):
                by_form = any(form in source for form in SOURCE_FORMS)
                by_skill = any(name in source and lic in source
                               for name, lic in ALLOWED_SKILLS.items())
                self.assertTrue(by_form or by_skill, "fonte di un tipo non ammesso")

    def test_every_rule_names_what_is_judged(self):
        found = security_rules()
        self.assertTrue(found, "nessuna regola R-SECURITY-NN")
        for rid, *_rest, judged in found:
            with self.subTest(rule=rid):
                self.assertTrue(JUDGED.match(f"Si giudica su: {judged}"),
                                "manca la riga «Si giudica su: diff|report|nota»")

    def test_blocking_rules_judged_on_diff_or_report(self):
        """Nei lavori senza passo la nota non c'è: una regola che blocca si giudica sul diff o
        sul report."""
        blocking = [r for r in security_rules() if r[1]]
        self.assertTrue(blocking, "nessuna regola [blocca]")
        for rid, _blocca, _text, _source, judged in blocking:
            with self.subTest(rule=rid):
                self.assertIn(judged, ("diff", "report"))

    def test_blocca_lines_have_text(self):
        """Una riga `R-SECURITY-NN [blocca]` senza testo sarebbe una regola nota ma non
        bloccante."""
        lines = [l for l in skill_text().split("\n") if l.startswith("R-SECURITY-")]
        self.assertTrue(lines, "nessuna regola R-SECURITY-NN")
        for line in lines:
            with self.subTest(line=line[:30]):
                self.assertRegex(line, RULE_LINE)
        self.assertEqual(len(lines), len(security_rules()))

    def test_at_most_150_lines(self):
        self.assertLessEqual(len(skill_text().split("\n")), 150)

    def test_denied_access_rule_exists(self):
        """Il `dod` del catalogo 2.3 («test dei casi di accesso negato») diventa una regola
        `[blocca]` sul diff (decisione 12)."""
        found = [rid for rid, blocca, text, source, judged in security_rules()
                 if blocca and judged == "diff" and "catalogo 2.3" in source
                 and re.search(r"\bnegat", text) and re.search(r"\btest\b", text)]
        self.assertTrue(found, "manca la regola [blocca] sul diff che chiede il test del caso "
                               "negato, con la fonte «catalogo 2.3»")

    def test_cc_by_sa_sources_are_ideas_only(self):
        """Da OWASP e da Trail of Bits (CC BY-SA 4.0) solo idee, citate «idea di …»; nessuna
        regola cita ASVS (nessuna scheda viene da lì) né `security-review`."""
        sources = [(rid, source) for rid, _b, _t, source, _j in security_rules()]
        self.assertTrue(sources, "nessuna regola R-SECURITY-NN")
        for rid, source in sources:
            with self.subTest(rule=rid):
                self.assertEqual(CC_BY_SA.findall(source), [],
                                 "una fonte OWASP o Trail of Bits non scritta «idea di …»")
                self.assertNotIn("ASVS", source)
                self.assertNotIn("security-review", source)
                for plugin in ("insecure-defaults", "differential-review"):
                    if plugin in source:
                        self.assertIn(f"idea di Trail of Bits `{plugin}`", source)
        cited = " ".join(source for _rid, source in sources)
        self.assertIn("idea di OWASP Cheat Sheet", cited)
        self.assertIn("idea di Trail of Bits", cited)

    def test_where_to_look_names_skills(self):
        """`security-and-hardening` (MIT) si nomina; `security-review` (CC BY-SA) solo «se
        installata»."""
        text = skill_text()
        self.assertIn("\n## Dove informarsi\n", text)
        informarsi = text.split("\n## Dove informarsi\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`security-and-hardening`", informarsi)
        lines = [l for l in informarsi.split("\n") if "security-review" in l]
        self.assertTrue(lines, "«Dove informarsi» non nomina `security-review`")
        for line in lines:
            with self.subTest(line=line[:40]):
                self.assertIn("se installata", line)

    def test_overlaps_name_approved_rules(self):
        """Le regole su segreti e input dicono con quali regole approvate si sovrappongono, con
        gli id della decisione 15; ogni id nominato esiste nella skill approvata dell'area."""
        text = skill_text()
        found = overlaps(text)
        self.assertEqual(found, OVERLAPS)
        for rid, named in found.items():
            for other in sorted(named):
                with self.subTest(rule=rid, other=other):
                    area = other.split("-")[1].lower()
                    approved = (ROOT / "skills" / f"rules-{area}" / "SKILL.md").read_text(
                        encoding="utf-8")
                    self.assertTrue(research.enforced(approved))
                    self.assertTrue(re.search(rf"^{other}( \[blocca\])? \S", approved, re.M),
                                    "id non trovato nella skill approvata")

    def test_user_choices_covered(self):
        by_id = {r[0]: r for r in security_rules()}
        for choice, (rid, needles) in USER_CHOICES.items():
            with self.subTest(choice=choice):
                self.assertIn(rid, by_id)
                for needle in needles:
                    self.assertIn(needle, by_id[rid][3])
        self.assertEqual(len({rid for rid, _ in USER_CHOICES.values()}), len(USER_CHOICES))
        # Nessuna regola che cita le scelte dell'utente del 22/11 resta fuori dalla tabella.
        citing = {rid for rid, r in by_id.items() if USER_CHOICE_SOURCE in r[3]}
        self.assertEqual(citing, {rid for rid, _ in USER_CHOICES.values()})

    def test_supabase_edge_functions_stay_with_database(self):
        """La scelta dell'utente del progetto di B, sezione 12: le edge function e le policy sotto
        `supabase/` alla radice restano a `database`. Non è una regola giudicabile sul diff (la
        applica `exclude` del frammento): la dice l'introduzione, prima di «Prima di scrivere»."""
        text = skill_text()
        self.assertIn("\n## Prima di scrivere\n", text)
        intro = text[:text.index("\n## Prima di scrivere\n")]
        paragraphs = [p for p in intro.split("\n\n") if "progetto di B, sezione 12" in p]
        self.assertEqual(len(paragraphs), 1, "l'introduzione non cita il progetto di B, sezione 12")
        needles = ("edge function", "policy", "`supabase/` alla radice", "regole di `database`")
        for needle in needles:
            with self.subTest(needle=needle):
                self.assertTrue(needle in paragraphs[0], "manca nella frase sul progetto di B, 12")

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
        self.assertEqual(profile["agent"], "tollgate:implementer-security")
        self.assertEqual(profile["reviewer"], "tollgate:reviewer-security")
        self.assertEqual(profile["final_specialist"], "tollgate:final-security")
        self.assertEqual(profile["checklist"], CHECKLIST)
        for key in ("rules", "blocking_rules", "cross"):
            self.assertNotIn(key, profile)
        detect = data["detect"]
        self.assertEqual(set(detect), {"content", "exclude", "keep_paths"})
        self.assertEqual(detect["content"], MARKERS)
        self.assertEqual(detect["exclude"], ["supabase/"])
        self.assertIs(detect["keep_paths"], True)
        for marker in REMOVED_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, detect["content"])

    def test_fragment_loads_through_the_loader(self):
        (found,) = [f for f in fragments.load(ROOT) if f.area == AREA]
        self.assertEqual(found.source, FRAGMENT)
        self.assertEqual(found.skill_path, SKILL)
        self.assertEqual(found.detect, tuple(MARKERS))
        self.assertEqual(found.exclude, ("supabase/",))
        self.assertIs(found.keep_paths, True)
        self.assertEqual(
            found.patterns,
            (fragments.Pattern("folder", "auth"), fragments.Pattern("name", "middleware.*"),
             fragments.Pattern("name", "proxy.ts"), fragments.Pattern("name", "proxy.js"),
             fragments.Pattern("folder", "security"), fragments.Pattern("folder", "rls")))

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

    def test_real_security_markers_skip_tests(self):
        """Con il frammento vero, `detect_files` trova un marcatore nei sorgenti e salta i file
        di test (cartelle e nomi), i documenti e la cartella `supabase/` alla radice
        (`exclude`)."""
        tmp = tempfile.TemporaryDirectory(prefix="tollgate-")
        self.addCleanup(tmp.cleanup)
        repo = make_repo(Path(tmp.name) / "repo")
        files = {
            "src/lib/hash.ts": 'import bcrypt from "bcrypt";\n',
            "app/login.py": "import bcrypt\n",
            "src/lib/hash.test.ts": 'import bcrypt from "bcrypt";\n',
            "src/lib/token.spec.js": "const jwt = require('jsonwebtoken');\n",
            "src/__tests__/token.js": "const jwt = require('jsonwebtoken');\n",
            "tests/test_login.py": "import jwt\n",
            "app/test_hash.py": "from passlib.hash import pbkdf2_sha256\n",
            "app/conftest.py": "from argon2 import PasswordHasher\n",
            "pkg/auth_test.go": 'import jwt "example.com/jwt"\n',
            "supabase/functions/login/index.ts": "import * as jose from 'jose'\n",
            "docs/guida.md": "import jwt\n",
        }
        for rel, body in files.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "prova")
        sizes = core_git.tree_sizes_at(repo, "HEAD")
        (security,) = [f for f in fragments.load(ROOT) if f.area == AREA]
        got = init.detect_files(repo, "HEAD", [security], sizes)
        self.assertEqual(got, {AREA: ["app/login.py", "src/lib/hash.ts"]})


# Le sezioni del rapporto delle fonti (Interfaces del Task 5).
REPORT_SECTIONS = ("Regole e fonti", "Pattern dei percorsi", "Marcatori di contenuto",
                   "Parti dichiarate «scelta nostra»", "Regole tolte dalla verifica")
# Le parti di una `Fonte:` che non chiedono una riga `ok` del rapporto: sono nostre.
OURS = ("scelta nostra", "esempi nostri")
# La voce con esito `no` alla prima verifica (Step 1, `task-5-fonti.md`): la `Fonte:` di
# R-SECURITY-10 non la porta più (corretta nel commit 1749ee8).
REMOVED_SOURCE = ("R-SECURITY-10", "nessun segreto nel codice né nei log")
# Un id di una regola approvata di un'altra area.
APPROVED_ID = re.compile(r"R-(?!SECURITY-)[A-Z]+-\d{2}")
# I termini che la pagina spiega in grassetto: i sei del piano e quelli delle pagine di B7.
TERMS = ("**Autenticazione**", "**Autorizzazione**", "**Token**", "**Sessione**",
         "**Middleware**", "**Specialista finale**", "**Proxy**", "**Hash**", "**Profilo**",
         "**Livello L2**", "**Marcatore**", "**Percorso esatto**", "**`dod`**")
# I casi della tabella delle precedenze (decisione 5) che «Da decidere tu» nomina, dallo Step 3.
# Un intervallo come «S61-S64» vale per ogni caso che contiene.
CHOICE_CASES = ("S4", "S39", "S54", "S49", "S50", "S61", "S62", "S63", "S64", "S53", "S51",
                "S52", "S16", "S9", "S46", "S57", "S59", "S13", "S34", "S19", "S40", "S44",
                "S68", "S69", "S70", "S71", "S11", "S56", "S67")
# La frase in parole semplici del piano per S53 (D14).
S53_PHRASE = ("un file di login dentro una cartella del server va agli agenti di sicurezza; "
              "fuori da una cartella del server resta a quelli del server")
# Gli altri punti di «Da decidere tu» (Step 3 e decisioni del controller), cercati punto per
# punto (rilievo m-9 della revisione): un punto vale se il suo titolo in grassetto ha tutte le
# parole della seconda colonna e il punto intero tutte quelle della terza. Un id di regola si
# cerca nel titolo, perché il punto «scelta nostra» li nomina tutti.
CHOICE_POINTS = (
    ("codice di terzi, immagini, testi tradotti, middleware.yaml (decisione 1)", (),
     ("`vendor/", "`public/auth/`", "`i18n/auth/`", "`middleware.yaml`")),
    ("proxy.ts e proxy.js aggiunti al catalogo", ("`**/proxy.ts`",), ()),
    ("le forme fuori della decisione 1", ("restano fuori",),
     ("`middleware/`", "`Auth/`", "`proxy.page.ts`", "`_middleware.ts`")),
    ("marcatore import jwt, anche jwt-decode (D10)", ("`import jwt`",), ("jwt-decode",)),
    ("marcatore jose", ("`jose`",), ()),
    ("iron-session al confine con «niente session»", ("`iron-session`",), ("session",)),
    ("marcatori tolti", ("marcatori tolti",), ("require('bcryptjs')", "from 'jsonwebtoken'")),
    ("supabase/ escluso alla radice, non annidata, rimedio di S67", ("`supabase/`",),
     ("annidat", "`supabase/functions/auth/**`")),
    ("keep_paths anche sui nomi, scelta nostra", (), ("`keep_paths`", "scelta nostra")),
    ("dod vuoto", ("`dod`",), ()),
    ("sovrapposizione di R-SECURITY-10", ("R-SECURITY-10", "ripete"), ()),
    ("sovrapposizione di R-SECURITY-12", ("R-SECURITY-12", "ripete"), ()),
    ("R-SECURITY-08 blocca o no", ("R-SECURITY-08", "blocca"), ()),
    ("esempi nostri di R-SECURITY-08", ("R-SECURITY-08", "esempi"),
     ("`hmac.compare_digest`", "`crypto.timingSafeEqual`")),
    ("R-SECURITY-01 e R-SECURITY-16 vicine", ("R-SECURITY-01", "R-SECURITY-16", "vicine"), ()),
    ("le due forme di R-SECURITY-09", ("R-SECURITY-09", "forme"), ()),
    ("R-SECURITY-15 non blocca e si giudica sul report", ("R-SECURITY-15", "report"), ()),
    ("un .tsx dentro auth/ fuori da components/ (D8, N4)", (), ("`.tsx`", "`components/`")),
    ("un task con un percorso esatto di un altro profilo e un file di auth/ (D8, N9)", (),
     ("agenti generici", "test")),
)
# Il punto che nomina le regole con «scelta nostra» nella `Fonte:`.
OUR_CHOICES_TITLE = "scelta nostra"
# Il rinvio (decisione 19): cosa va su `main` e cosa resta sul ramo.
RINVIO_NEEDLES = ("`main`", "`c2-profilo-security`", "`c2-parziale`", "i Task 1, 2 e 3",
                  "modelli", "sicurezza fin dal progetto", "`keep_paths`", "non vanno su `main`")
# Il testo della proposta di ognuno dei trentuno punti, come nel Task 5: l'utente li ha approvati
# tutti il 2026-11-23 (copiato da `task-5-proposte.md`, che non sta nel repo).
PROPOSALS = (
    "lasciare così, perché un modulo di login tratta password. Chi non lo vuole toglie quel percorso dal blocco prima di copiarlo: il file torna agli agenti di `frontend`, senza queste regole e senza lo specialista, ma il lavoro resta L2 perché sta sotto `auth/`.",
    "lasciare così.",
    "lasciare così.",
    "lasciare così; se capita spesso in un progetto, togli dal blocco uno dei due percorsi.",
    "lasciare così: un file di login lo scrive chi ha caricate le regole di sicurezza.",
    "tenere l'estensione; senza, in questi casi `security` non si accenderebbe affatto.",
    "lasciare così.",
    "lasciare così, perché nella maggior parte dei progetti quel nome è davvero il controllo del login; chi ha un caso toglie il percorso dal blocco.",
    "tenerli.",
    "lasciare così. Il rimedio è gratuito: togli quel percorso dal blocco proposto prima di copiarlo nel `tollgate.toml`. Sotto `auth/` toglie gli agenti di sicurezza e lo specialista, non il livello L2; per `middleware.yaml` e per `security/` toglie anche quello.",
    "lasciarle fuori per ora; chi ne ha le aggiunge a mano al blocco, e si riprendono alla prossima revisione delle regole.",
    "lasciare così; chi tiene le policy in una cartella `rls/` può togliere quel percorso dal blocco.",
    "lasciare così, sono comunque file che parlano di accessi.",
    "lasciare così.",
    "lasciare così.",
    "tenerlo; un file che legge un token merita comunque queste regole.",
    "tenerlo.",
    "tenerla; se in un progetto pesa, togli quei percorsi dal blocco.",
    "lasciarli fuori. Se li vuoi, dimmelo: si rimettono, dichiarati come scelta tua.",
    "lasciare così, è la tua scelta del progetto di B.",
    "tenerla; senza, un file di login che va a `security` non avrebbe nessuna regola sui segreti caricata.",
    "tenerla, per lo stesso motivo.",
    "lasciarla così. Se la vuoi tra le sovrapposizioni, è un cambio di una riga.",
    "lasciarlo vuoto, come negli altri profili.",
    "farla bloccare, perché correggerlo costa una riga.",
    "tenerli, perché dicono a chi scrive cosa usare. In alternativa si tolgono senza toccare la regola.",
    "tenerle separate: sono due domande diverse e la prima blocca, la seconda no. Se le trovi doppie, si uniscono nella prima.",
    "tenere la forma scritta, per non fermare codice corretto.",
    "lasciarla così.",
    "tenere questa divisione; puoi spostare ogni regola dicendomi il numero.",
    "tenerle tutte.",
)
# I due ritocchi del Task 6 (minori rinviati dalla ri-revisione del Task 5, decisione del
# controller): il rimedio dei punti 1 e 10 toglie lo specialista solo se il lavoro non tocca altri
# file del profilo. (punto, testo del Task 5, testo approvato).
SPECIALIST_CAVEAT = " (se il lavoro non tocca altri file del profilo)"
RETOUCHES = (
    (1, "senza queste regole e senza lo specialista,",
     f"senza queste regole e senza lo specialista{SPECIALIST_CAVEAT},"),
    (10, "toglie gli agenti di sicurezza e lo specialista,",
     f"toglie gli agenti di sicurezza e lo specialista{SPECIALIST_CAVEAT},"),
)


def approved_proposals() -> list[str]:
    """Le proposte del Task 5 con i due ritocchi del Task 6: il testo che la pagina porta."""
    found = list(PROPOSALS)
    for number, old, new in RETOUCHES:
        assert found[number - 1].count(old) == 1, f"ritocco del punto {number} non applicabile"
        found[number - 1] = found[number - 1].replace(old, new)
    return found


# Oltre trenta: i punti di «Da decidere tu» sono quasi trenta.
NUMBERS = {**NUMBER_WORDS, "trentuno": 31, "trentadue": 32, "trentatré": 33,
           "trentaquattro": 34, "trentacinque": 35, "trentasei": 36, "trentasette": 37,
           "trentotto": 38, "trentanove": 39, "quaranta": 40}


def normal(text: str) -> str:
    return " ".join(text.split())


def as_number(token: str) -> int:
    """Un numero in cifre o in lettere, fino a quaranta; fuori, un errore esplicito."""
    word = token.lower()
    if word.isdigit():
        return int(word)
    if word not in NUMBERS:
        raise AssertionError(f"numero «{token}» fuori dal dizionario del test (fino a quaranta)")
    return NUMBERS[word]


def voci(source: str) -> list[str]:
    """Le voci di una `Fonte:`: le parti separate da `;` fuori dalle parentesi, senza quelle
    nostre («scelta nostra», «esempi nostri»), e dentro una parte le voci unite da « e » (due
    indirizzi, due skill di agent-skills) come voci distinte, senza la virgola che le separa."""
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
        if any(word in part for word in OURS):
            continue
        found.extend(normal(v) for v in
                     re.split(r",? e (?=https://|spec del nucleo|\d\.\d |`security-)", part))
    return [v for v in found if v]


def choice_points(section: str) -> list[tuple[str, str]]:
    """I punti di «Da decidere tu»: (titolo in grassetto, testo intero), spazi normalizzati."""
    found = []
    for item in re.split(r"^(?=\d+\. \*\*)", section, flags=re.M)[1:]:
        # il grassetto si chiude su `**` seguito da uno spazio: `**/proxy.ts` non lo chiude
        m = re.match(r"\d+\. \*\*(.+?)\*\*(?=\s|$)", item, re.S)
        if m:
            found.append((normal(m.group(1)), normal(item)))
    return found


def cases_named(text: str) -> set[str]:
    """I casi «S<N>» nominati nel testo, con gli intervalli «S61-S64» espansi."""
    found = set(re.findall(r"\bS\d+\b", text))
    for first, last in re.findall(r"\bS(\d+)\s*[-–]\s*S(\d+)\b", text):
        found.update(f"S{n}" for n in range(int(first), int(last) + 1))
    return found


class RulesSecurityPageTest(unittest.TestCase):
    """Il rapporto delle fonti e la pagina per l'utente (C2, Task 5), sul modello di
    `RulesDatabasePageTest`; dopo l'approvazione (Task 6) «Da decidere tu» diventa «Cosa hai
    deciso». Si cercano gli id e i nomi, non le frasi; conteggi ed elenchi vengono dalla skill e
    dal frammento."""

    def skill_ids(self) -> list[str]:
        return [r[0] for r in security_rules()]

    def skip_if_approved(self):
        if "approved" in frontmatter(skill_text()):
            self.skipTest("la skill è approvata: la pagina non è più una proposta")

    def section(self, title: str) -> str:
        text = SOURCES.read_text(encoding="utf-8")
        self.assertTrue(f"\n## {title}\n" in text, "manca una sezione del rapporto")
        return text.split(f"\n## {title}\n", 1)[1].split("\n## ", 1)[0]

    def page_section(self, title: str) -> str:
        text = PAGE.read_text(encoding="utf-8")
        self.assertTrue(f"\n## {title}\n" in text, "manca una sezione della pagina")
        return text.split(f"\n## {title}\n", 1)[1].split("\n## ", 1)[0]

    def page_text(self) -> str:
        return normal(PAGE.read_text(encoding="utf-8"))

    def rule_rows(self) -> list[list[str]]:
        """Le righe della tabella delle regole (sezione «Le regole»)."""
        rows = [c for c in table_rows(self.page_section("Le regole")) if ID.search(c[0])]
        self.assertTrue(rows, "la tabella delle regole è vuota")
        return rows

    def test_sources_report_covers_every_rule(self):
        """Il rapporto ha le sue cinque sezioni. Per ogni voce di una `Fonte:` (tolte le parti
        nostre, con le voci unite da « e » prese come distinte) la tabella «Regole e fonti» ha
        una riga `ok` di quella regola la cui cella «Fonte» la contiene; ogni regola con «scelta
        nostra» nella `Fonte:` sta tra le parti dichiarate «scelta nostra»."""
        text = SOURCES.read_text(encoding="utf-8")
        for title in REPORT_SECTIONS:
            with self.subTest(section=title):
                self.assertTrue(f"\n## {title}\n" in text, "manca una sezione del rapporto")
        rows = table_rows(self.section("Regole e fonti"))
        self.assertTrue(rows, "la tabella «Regole e fonti» è vuota")
        named = set()
        for cells in rows:
            self.assertIn(cells[-1], ("ok", "no"), "l'esito è `ok` o `no`, senza altro testo")
            named.update(ID.findall(cells[0]))
        self.assertEqual(named - set(self.skill_ids()), set())
        found_rules = security_rules()
        self.assertTrue(found_rules, "nessuna regola R-SECURITY-NN")
        for rid, _b, _t, source, _j in found_rules:
            found = voci(source)
            self.assertTrue(found, rid)
            for voce in found:
                with self.subTest(rule=rid, voce=voce[:50]):
                    self.assertTrue(
                        any(c[0] == rid and c[-1] == "ok" and voce in normal(c[1])
                            for c in rows),
                        "nessuna riga `ok` del rapporto per questa voce")
        ours = self.section("Parti dichiarate «scelta nostra»")
        for rid, _b, _t, source, _j in found_rules:
            if "scelta nostra" in source:
                with self.subTest(rule=rid):
                    self.assertTrue(rid in ours, "manca tra le parti dichiarate «scelta nostra»")

    def test_removed_sources_are_not_in_the_skill(self):
        """Una riga `no` del rapporto è una voce uscita dalla `Fonte:`: la skill non la porta
        più e la regola ha ancora una riga `ok`. Il rapporto ha la sola riga `no` della prima
        verifica (R-SECURITY-10), e la skill non porta più le sue parole."""
        sources = {r[0]: normal(r[3]) for r in security_rules()}
        rows = table_rows(self.section("Regole e fonti"))
        removed = [c for c in rows if c[-1] == "no"]
        rid, words = REMOVED_SOURCE
        self.assertEqual([c[0] for c in removed], [rid])
        for cells in removed:
            with self.subTest(rule=cells[0], source=cells[1][:40]):
                self.assertTrue(words in normal(cells[1]), "la riga `no` non è la voce uscita")
                self.assertFalse(normal(cells[1]) in sources[cells[0]],
                                 "la skill porta ancora la voce uscita")
                self.assertTrue(any(c[0] == cells[0] and c[-1] == "ok" for c in rows),
                                "la regola non ha più una fonte ok")
        self.assertFalse(words in sources[rid], "R-SECURITY-10 porta ancora la parte uscita")

    def test_path_patterns_verified(self):
        """Ogni pattern del frammento ha una riga `ok`, e nessuna riga `ok` è di un pattern che
        il frammento non ha più."""
        rows = table_rows(self.section("Pattern dei percorsi"))
        self.assertTrue(rows, "la tabella «Pattern dei percorsi» è vuota")
        ok = set()
        for cells in rows:
            m = re.fullmatch(r"`(.+)`", cells[0])
            self.assertIsNotNone(m, cells[0])
            self.assertIn(cells[-1], ("ok", "no"))
            if cells[-1] == "ok":
                ok.add(m.group(1))
        paths = set(fragment()["profile"]["paths"])
        self.assertTrue(paths)
        self.assertEqual(paths - ok, set())
        self.assertEqual(ok - paths, set(), "il rapporto verifica un pattern che non c'è più")

    def test_detect_markers_verified(self):
        """Una riga `ok` vale per le due forme di virgolette dello stesso import; una riga `no`
        è di un marcatore che il frammento non ha."""
        rows = table_rows(self.section("Marcatori di contenuto"))
        self.assertTrue(rows, "la tabella «Marcatori di contenuto» è vuota")
        ok, no = set(), set()
        for cells in rows:
            m = re.fullmatch(r"`(.+)`", cells[0])
            self.assertIsNotNone(m, cells[0])
            self.assertIn(cells[-1], ("ok", "no"))
            (ok if cells[-1] == "ok" else no).add(m.group(1).replace('"', "'"))
        markers = {m.replace('"', "'") for m in fragment()["detect"]["content"]}
        self.assertTrue(markers)
        self.assertEqual(markers - ok, set())
        self.assertEqual(ok - markers, set(), "il rapporto verifica un marcatore che non c'è più")
        self.assertEqual(no & markers, set(), "un marcatore `no` è ancora nel frammento")

    def test_no_long_quotations(self):
        """La skill non porta citazioni tra «» di più di dodici parole. Nel rapporto e nella
        pagina ogni citazione tra «» sta su una riga e non supera trenta parole. La pagina non
        riporta nessuna citazione di più di dieci parole che il rapporto prende da una fonte di
        terzi (una riga la cui cella «Fonte» non è il progetto, il catalogo o la spec)."""
        for line in skill_text().split("\n"):
            for quoted in re.findall(r"«([^»]*)»", line):
                with self.subTest(file="SKILL.md", quoted=quoted[:40]):
                    self.assertLessEqual(len(quoted.split()), 12)
        for path in (SOURCES, PAGE):
            found = re.findall(r"«([^»]*)»", path.read_text(encoding="utf-8"))
            self.assertTrue(found, "nessuna citazione tra «»")
            for quoted in found:
                with self.subTest(file=path.name, quoted=quoted[:40]):
                    self.assertNotIn("\n", quoted)
                    self.assertLessEqual(len(quoted.split()), 30)
        ours = ("progetto di", "catalogo", "spec del nucleo")
        third = []
        for title in ("Regole e fonti", "Pattern dei percorsi", "Marcatori di contenuto"):
            for cells in table_rows(self.section(title)):
                if len(cells) > 3 and not cells[1].startswith(ours):
                    third.extend(q for q in re.findall(r"«([^»]*)»", "|".join(cells[2:-1]))
                                 if len(q.split()) > 10)
        self.assertTrue(third, "nessuna citazione lunga di terzi nel rapporto")
        page = self.page_text().lower()
        for quoted in third:
            with self.subTest(quoted=quoted[:40]):
                self.assertFalse(normal(quoted).lower() in page,
                                 "la pagina riporta una citazione di una fonte di terzi")

    def test_page_lists_every_rule(self):
        """La tabella di «Le regole» ha una riga per regola, nell'ordine, e la cella «N.» è
        «<numero> (R-SECURITY-<numero>)»."""
        rows = self.rule_rows()
        ids = [ID.search(cells[0]).group(0) for cells in rows]
        self.assertEqual(ids, self.skill_ids())
        for cells in rows:
            with self.subTest(cell=cells[0]):
                m = re.fullmatch(r"(\d+) \(R-SECURITY-(\d{2})\)", cells[0])
                self.assertIsNotNone(m)
                self.assertEqual(int(m.group(1)), int(m.group(2)))

    def test_page_blocca_matches_skill(self):
        blocca = {r[0]: r[1] for r in security_rules()}
        self.assertTrue(blocca, "nessuna regola R-SECURITY-NN")
        seen = {}
        for cells in self.rule_rows():
            self.assertIn(cells[2].lower(), ("sì", "no"))
            seen[ID.search(cells[0]).group(0)] = cells[2].lower() == "sì"
        self.assertEqual(seen, blocca)

    def test_page_judged_on_matches_skill(self):
        words = {"diff": "il diff", "report": "il report", "nota": "la nota"}
        expected = {r[0]: words[r[4]] for r in security_rules()}
        self.assertTrue(expected, "nessuna regola R-SECURITY-NN")
        seen = {ID.search(cells[0]).group(0): cells[3] for cells in self.rule_rows()}
        self.assertEqual(seen, expected)

    def test_page_explains_what_changes(self):
        """Come si accende («Quando si accende»); nella sezione «Cosa cambia nei tuoi
        progetti»: L2 e lo specialista, `dod` vuoto con l'esempio, i modelli degli agenti, la
        sicurezza fin dal progetto, `supabase/` escluso, `keep_paths`."""
        # il profilo si accende solo dove `init` lo propone e l'utente copia il blocco
        self.assertTrue(re.search(r"`/tollgate:init`[^.]*propone[^.]*\btu copi\b",
                                  normal(self.page_section("Quando si accende"))),
                        "manca «init propone, tu copi» in «Quando si accende»")
        # il resto si cerca nella sezione «Cosa cambia nei tuoi progetti» (rilievo m-9)
        text = normal(self.page_section("Cosa cambia nei tuoi progetti"))
        checks = (
            # L2: il livello minimo, il lavoro che sale, il gate della PR, lo specialista
            (r"lavoro[^.]*\bL2\b[^.]*spec[^.]*piano", "manca il passaggio a L2 con spec e piano"),
            (r"specialista finale[^.]*\bL2\b", "manca lo specialista finale in L2"),
            # un file di un altro profilo rende attivo `security` e il lavoro sale a L2
            (r"attivo[^.]*\bL2\b", "manca «security attivo, lavoro L2»"),
            # i modelli degli agenti (decisione 14)
            (r"\bopus\b", "manca il modello di chi scrive"),
            (r"(?i)\bfable\b", "manca il modello di chi rivede"),
            # la sicurezza fin dal progetto in ogni lavoro (decisione 20)
            (r"(?i)sicurezza fin dal progetto", "manca la sicurezza fin dal progetto"),
            # `supabase/` escluso alla radice (decisione 3)
            (r"`supabase/`[^.]*alla radice|alla radice[^.]*`supabase/`",
             "manca `supabase/` escluso alla radice"),
        )
        for pattern, message in checks:
            with self.subTest(pattern=pattern):
                self.assertTrue(re.search(pattern, text), message)
        needles = (
            "`min_level = \"L2\"`", "`level_below_minimum`", "`final-security`",
            "`/tollgate:finish`", "`implementer-security`", "`reviewer-security`",
            "`Sicurezza:`", "`keep_paths`", "`dod`",
            'denied = "python3 -m unittest discover -s tests -k denied"',
            "credenziali vere", "senza chiedere")
        for needle in needles:
            with self.subTest(needle=needle):
                self.assertTrue(needle in text, "manca un testo atteso in «Cosa cambia»")

    def test_page_lists_overlaps(self):
        """«Regole che si sovrappongono» ha una riga per ogni sovrapposizione della skill (righe
        «Si sovrappone a:», decisione 15): la regola di `security`, l'id approvato e la
        differenza. Nessuna riga in più."""
        expected = {(rid, other) for rid, named in overlaps(skill_text()).items()
                    for other in named}
        self.assertTrue(expected, "la skill non ha righe «Si sovrappone a:»")
        rows = table_rows(self.page_section("Regole che si sovrappongono"))
        self.assertTrue(rows, "la tabella delle sovrapposizioni è vuota")
        seen = []
        for cells in rows:
            with self.subTest(row=cells[0][:30]):
                self.assertEqual(len(cells), 3, "la riga non ha tre colonne")
                ours, approved = ID.findall(cells[0]), APPROVED_ID.findall(cells[1])
                self.assertEqual(len(ours), 1, "la prima colonna ha una sola regola di security")
                self.assertEqual(len(approved), 1, "la seconda colonna ha un solo id approvato")
                self.assertTrue(cells[2].strip(), "manca la differenza")
                seen.append((ours[0], approved[0]))
        self.assertEqual(len(seen), len(set(seen)), "una sovrapposizione ripetuta")
        self.assertEqual(set(seen), expected)

    def test_page_brings_the_open_choices_to_the_user(self):
        """Vale solo prima dell'approvazione: «Da decidere tu» nomina ogni punto aperto dello
        Step 3 e delle decisioni del controller, e ogni regola con «scelta nostra» nella
        `Fonte:`."""
        self.skip_if_approved()
        self.check_choice_points(self.page_section("Da decidere tu"))

    def check_choice_points(self, raw: str):
        """I punti dello Step 3 e delle decisioni del controller, in «Da decidere tu» prima
        dell'approvazione e in «Cosa hai deciso» dopo."""
        section = normal(raw)
        missing = sorted(set(CHOICE_CASES) - cases_named(section), key=lambda s: int(s[1:]))
        with self.subTest(point="casi della tabella delle precedenze"):
            self.assertEqual(missing, [], "mancano dei casi della tabella tra i punti")
        with self.subTest(point="S53 in parole semplici (D14)"):
            self.assertTrue(S53_PHRASE in section.lower(),
                            "manca la frase in parole semplici del piano per S53")
        points = choice_points(raw)
        self.assertTrue(points, "la sezione non ha punti «<n>. **…**»")
        for point, in_title, in_point in CHOICE_POINTS:
            with self.subTest(point=point):
                self.assertTrue(
                    any(all(w in title for w in in_title) and all(w in body for w in in_point)
                        for title, body in points),
                    f"manca il punto «{point}»")
        ours = [r[0] for r in security_rules() if "scelta nostra" in r[3]]
        self.assertTrue(ours, "nessuna regola con «scelta nostra»")
        bodies = [body for title, body in points if OUR_CHOICES_TITLE in title]
        self.assertEqual(len(bodies), 1, "manca il punto «I temi «scelta nostra»»")
        for rid in ours:
            with self.subTest(rule=rid):
                self.assertTrue(rid in bodies[0], "manca una regola «scelta nostra»")

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
        """Approvata, la pagina non ha più «Come rispondere» né «Rinvio», non chiede più di
        approvare o di decidere e non dice più che le regole sono una bozza."""
        text = PAGE.read_text(encoding="utf-8")
        self.assertFalse("\n## Come rispondere" in text, "resta la sezione «Come rispondere»")
        self.assertFalse("**Rinvio.**" in text, "resta il rinvio")
        self.assertFalse(re.search(r"finché non (le )?approvi|dopo che avrai approvato", text),
                         "la pagina chiede ancora di approvare")
        self.assertFalse(re.search(r"devi decidere|[Ss]e hai poco tempo|se non dici altro",
                                   text), "la pagina chiede ancora di decidere")
        self.assertFalse(re.search(r"sono una bozza", text), "la pagina parla ancora di bozza")

    def test_page_records_the_choices(self):
        """«Cosa hai deciso» porta i trentuno punti: per ognuno il costo, la proposta (il testo
        del Task 5 con i due ritocchi del Task 6) e che l'utente l'ha approvata. Ci sono ancora
        tutti i punti dello Step 3, e i numeri dell'introduzione e della sezione sono quelli dei
        punti."""
        raw = self.page_section("Cosa hai deciso")
        self.check_choice_points(raw)
        items = re.split(r"^(?=\d+\. \*\*)", raw, flags=re.M)[1:]
        proposals = approved_proposals()
        self.assertEqual(len(proposals), 31)
        self.assertEqual(len(items), len(proposals), "i punti non sono trentuno")
        for number, (item, proposal) in enumerate(zip(items, proposals), 1):
            with self.subTest(point=number):
                self.assertEqual(int(item.split(".", 1)[0]), number, "punti fuori ordine")
                self.assertTrue("Costo: " in item, "il punto non ha il suo «Costo:»")
                found = re.findall(r"^\s+Proposta: (.+)$", item, re.M)
                self.assertEqual(len(found), 1, "il punto non ha una sola proposta")
                self.assertTrue(normal(found[0]) == proposal,
                                "il testo della proposta non è quello approvato")
                self.assertEqual(len(re.findall(r"^\s+Hai approvato la proposta\.$", item,
                                                re.M)), 1,
                                 "il punto non dice che la proposta è stata approvata")
        section = normal(raw)
        self.assertTrue("Su trentuno punti" in section, "manca «Su trentuno punti»")
        self.assertTrue("tutti e trentuno" in section, "manca «tutti e trentuno»")
        intro = self.page_text().split("## Cosa sono", 1)[0]
        points = re.search(r"cosa hai deciso su (\w+) punti dubbi", intro)
        self.assertIsNotNone(points, "manca «cosa hai deciso su N punti dubbi»")
        self.assertEqual(as_number(points.group(1)), len(items))
        self.assertTrue("Le regole sono approvate e il profilo si può accendere." in intro,
                        "l'introduzione non dice che le regole sono approvate")

    def test_page_retouches_of_task_6(self):
        """I due ritocchi del Task 6: il rimedio dei punti 1 e 10 toglie lo specialista solo se
        il lavoro non tocca altri file del profilo; la voce «Attivo» del glossario dice che
        girano i comandi di gate e di `dod` del profilo (vuoti per `security`)."""
        text = PAGE.read_text(encoding="utf-8")
        self.assertEqual(text.count(SPECIALIST_CAVEAT), 2, "i ritocchi dei punti 1 e 10")
        active = [l for l in text.split("\n") if l.startswith("- **Attivo**: ")]
        self.assertEqual(len(active), 1, "manca la voce «Attivo» del glossario")
        for needle in ("gate", "`dod`", "vuoti"):
            with self.subTest(needle=needle):
                self.assertTrue(needle in active[0], "manca un testo atteso nella voce «Attivo»")

    def test_commands_page_says_approved(self):
        """`docs/uso/comandi.md`: la sezione di `/tollgate:rules-security` dice che le regole
        sono approvate, con la data, nella forma delle altre sezioni `rules-*`."""
        text = (ROOT / "docs" / "uso" / "comandi.md").read_text(encoding="utf-8")
        section = text.split("\n### `/tollgate:rules-security`\n", 1)[1].split("\n#", 1)[0]
        self.assertTrue(f"Le regole sono approvate dall'utente ({APPROVED}): `init` propone il "
                        "profilo `security`" in normal(section), "manca la data dell'approvazione")
        self.assertFalse("bozza" in section, "la sezione parla ancora di bozza")

    def test_page_choices_count_matches_list(self):
        """Vale solo prima dell'approvazione: il numero scritto in «Su N punti» e quello
        dell'introduzione («su quali N punti») sono quelli dei punti, e ogni punto ha il suo
        costo e la sua proposta."""
        self.skip_if_approved()
        section = self.page_section("Da decidere tu")
        items = re.split(r"^(?=\d+\. \*\*)", section, flags=re.M)[1:]
        count = len(items)
        self.assertGreaterEqual(count, 20, "i punti dello Step 3 sono più di venti")
        words = {n: w for w, n in NUMBERS.items() if w != "uno"}
        if count not in words:
            self.fail(f"{count} punti: il dizionario dei numeri arriva a quaranta")
        self.assertTrue(f"Su {words[count]} punti" in normal(section), "manca «Su N punti»")
        for item in items:
            number = item.split(".", 1)[0]
            with self.subTest(point=number):
                self.assertTrue("Costo: " in item, "il punto non ha il suo «Costo:»")
                self.assertEqual(len(re.findall(r"^\s+Proposta: ", item, re.M)), 1,
                                 "il punto non ha la sua proposta")
        intro = self.page_text().split("## Cosa sono", 1)[0]
        points = re.search(r"su quali (\w+) punti\b", intro)
        self.assertIsNotNone(points, "manca «su quali N punti» nell'introduzione")
        self.assertEqual(as_number(points.group(1)), count)

    def test_page_counts_match_skill(self):
        """I numeri della pagina (in lettere o in cifre) per le regole e per quelle che
        bloccano sono quelli della skill: in «Cosa sono» e, prima dell'approvazione, nel punto
        di «Da decidere tu» che li porta all'utente."""
        found = security_rules()
        self.assertTrue(found, "nessuna regola R-SECURITY-NN")
        total, blocking = len(found), sum(1 for r in found if r[1])
        section = normal(self.page_section("Cosa sono"))
        m = re.search(r"\bSono (\w+) regole in più", section)
        self.assertIsNotNone(m, "manca «Sono N regole in più»")
        self.assertEqual(as_number(m.group(1)), total)
        m = re.search(r"\b(\w+) di queste bloccano", section)
        self.assertIsNotNone(m, "manca «N di queste bloccano»")
        self.assertEqual(as_number(m.group(1)), blocking)
        if "approved" in frontmatter(skill_text()):
            return
        choices = normal(self.page_section("Da decidere tu"))
        m = re.search(r"\b(\w+) regole, di cui (\w+) bloccano", choices)
        self.assertIsNotNone(m, "manca «N regole, di cui M bloccano» in «Da decidere tu»")
        self.assertEqual((as_number(m.group(1)), as_number(m.group(2))), (total, blocking))

    def test_page_explains_the_terms(self):
        text = PAGE.read_text(encoding="utf-8")
        for needle in TERMS:
            with self.subTest(needle=needle):
                self.assertTrue(needle in text, "manca un termine spiegato")

    def test_page_has_no_private_data(self):
        """Né percorsi della home, né il nome utente o l'host di chi lancia il test (come parola
        intera, se lunghi almeno 4 caratteri e non generici: `root`, `user`, `runner`… compaiono
        nel testo come parole comuni e non identificano nessuno; revisione finale di C2, F2), né
        forme di token o di chiave. Il valore non si stampa mai: le asserzioni guardano `is None`,
        non l'oggetto `Match`."""
        secrets = []
        try:
            secrets.append(getpass.getuser())
        except (OSError, KeyError):
            pass
        secrets.append(socket.gethostname())
        tokens = re.compile(r"sk-ant|ghp_|github_pat_|eyJ[A-Za-z0-9_-]{10,}|-----BEGIN")
        for path in (PAGE, SOURCES):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertFalse("/home/" in text, "un percorso della home compare nel testo")
                for secret in secrets:
                    if len(secret) >= 4 and secret.lower() not in GENERIC_NAMES:
                        self.assertTrue(
                            re.search(rf"\b{re.escape(secret)}\b", text, re.I) is None,
                            "il nome utente o l'host compare nel testo")
                self.assertTrue(tokens.search(text) is None,
                                 "una forma di token o di chiave compare nel testo")

    def test_page_rinvio_says_what_stays_on_the_branch(self):
        """Prima dell'approvazione la pagina offre il rinvio (decisione 19): su `main` vanno
        solo i Task 1, 2 e 3 (modelli, sicurezza fin dal progetto, `keep_paths`), dal ramo
        `c2-parziale`; il resto resta sul ramo `c2-profilo-security`."""
        self.skip_if_approved()
        section = self.page_section("Come rispondere")
        found = re.findall(r"^\*\*Rinvio\.\*\*[^\n]*", section, re.M)
        self.assertEqual(len(found), 1, "manca il paragrafo «**Rinvio.**» in «Come rispondere»")
        rinvio = normal(found[0])
        for needle in RINVIO_NEEDLES:
            with self.subTest(needle=needle):
                self.assertTrue(needle in rinvio, "manca un testo atteso nel rinvio")


if __name__ == "__main__":
    unittest.main()
