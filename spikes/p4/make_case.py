#!/usr/bin/env python3
"""Casi della prova reale del gate (Task 16 del piano P4): rami, file e corpo della PR di ogni caso.

Nessuna rete. Lo usa `spikes/run-p4-gate.sh`, che spinge i rami, apre le PR con `gh` e aspetta gli stati;
qui si costruisce solo il contenuto, in un clone locale, e si giudica ciò che lo script ha raccolto.

  make_case.py list                          elenco dei casi, con repo, esito atteso e descrizione
  make_case.py baseline <repo> <cartella>    scrive i file del progetto di prova (protected | detect)
  make_case.py build <caso> --clone DIR --issue N --ts TS --out DIR --label L [--extra-issue M]
                                             crea i commit nel clone e scrive <label>-case.json e i corpi delle PR
  make_case.py judge <case.json> --push ID --statuses F --comments F --merge STATO ...
                                             confronta l'ottenuto con l'atteso, stampa la riga del rapporto

Il progetto di prova ha: `src/calc.py` con `tests/test_calc.py` (unittest, report JUnit con
`tools/unittest_junit.py`), un profilo `web` (`web/**`, comando con `|| true`) e un profilo `notes`
(`notes/**`, comando che non esegue test). Gli identificativi dei test sono `classname::name`.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))

from tollgate_analysis import prblock, waivers  # noqa: E402
from tollgate_core import VERSION  # noqa: E402

OWNER = "ginz0ls"
REPOS = {"protected": f"{OWNER}/tollgate-p4-protected", "detect": f"{OWNER}/tollgate-p4-detect"}
BOT = "github-actions[bot]"
SENTINEL_TITLE = "tollgate: merge non verificato"
MARKERS = {"verdict": "<!-- tollgate-verdict", "guard": "<!-- tollgate-guard", "na": "<!-- tollgate-na"}
PLAN_DIR = "docs/superpowers/plans"
SPEC_DIR = "docs/superpowers/specs"
DESCRIPTION_TOKEN = "prova-token-personale-p4"   # uguale a ghguard.STATUS_DESCRIPTION
SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope", "Punti di arresto",
            "Rischi"]

# ---------------------------------------------------------------- il progetto di prova

TOML = """schema_version = 1

[project]
allow_no_tests = {allow}

[gate]
mode = "{mode}"

[commands]
verify = "python3 tools/unittest_junit.py"
gate = ["verify"]
report = "junit:reports/junit.xml"

[profiles.web]
paths = ["web/**"]
gate = ["check"]
report = "junit:reports/web-junit.xml"

[profiles.web.commands]
check = "python3 tools/unittest_junit.py web/tests reports/web-junit.xml || true"

[profiles.notes]
paths = ["notes/**"]
gate = ["lint"]
report = "junit:reports/notes-junit.xml"

[profiles.notes.commands]
lint = "python3 tools/empty_junit.py reports/notes-junit.xml"
"""

CALC = """def somma(a, b):
    return a + b


def sottrai(a, b):
    return a - b
"""
CALC_MOLT = CALC + """

def moltiplica(a, b):
    return a * b
"""

UNITTEST_JUNIT = '''import pathlib
import sys
import unittest
from xml.sax.saxutils import quoteattr


class Result(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.cases = []

    def _add(self, test, kind=None):
        classname, _, name = test.id().rpartition(".")
        self.cases.append((classname, name, kind))

    def addSuccess(self, test):
        super().addSuccess(test); self._add(test)

    def addFailure(self, test, err):
        super().addFailure(test, err); self._add(test, "failure")

    def addError(self, test, err):
        super().addError(test, err); self._add(test, "error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self._add(test, "skipped")


start = sys.argv[1] if len(sys.argv) > 1 else "tests"
report = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "reports/junit.xml")
suite = unittest.defaultTestLoader.discover(start, top_level_dir=".")
res = unittest.TextTestRunner(resultclass=Result, stream=sys.stderr).run(suite)
body = "".join(
    f"<testcase classname={quoteattr(c)} name={quoteattr(n)}>"
    + (f'<{k} message="x"/>' if k else "") + "</testcase>" for c, n, k in res.cases)
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text("<testsuite>" + body + "</testsuite>")
sys.exit(0 if res.wasSuccessful() and res.cases else 1)
'''

EMPTY_JUNIT = '''import pathlib
import sys

report = pathlib.Path(sys.argv[1])
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text("<testsuite></testsuite>")
'''

WEB_TESTS = """import unittest

from web.page import titolo


class WebTest(unittest.TestCase):
    def test_titolo(self):
        self.assertEqual(titolo(), "tollgate")
"""

CI_WORKFLOW = """name: ci
on: workflow_dispatch
permissions:
  contents: read
jobs:
  noop:
    runs-on: ubuntu-latest
    steps:
      - run: echo ci
"""


def tests_text(*, sottrai=True, moltiplica=False, cls="CalcTest", skip_sottrai=False) -> str:
    names = "somma, sottrai" + (", moltiplica" if moltiplica else "")
    out = ["import unittest", "", f"from src.calc import {names}", "", "", f"class {cls}(unittest.TestCase):",
           "    def test_somma(self):", "        self.assertEqual(somma(1, 2), 3)",
           "        self.assertEqual(somma(0, 0), 0)"]
    if sottrai:
        out += [""] + (['    @unittest.skip("prova")'] if skip_sottrai else [])
        out += ["    def test_sottrai(self):", "        self.assertEqual(sottrai(5, 3), 2)",
                "        self.assertEqual(sottrai(0, 4), -4)"]
    if moltiplica:
        out += ["", "    def test_moltiplica(self):", "        self.assertEqual(moltiplica(2, 3), 6)",
                "        self.assertEqual(moltiplica(0, 5), 0)"]
    out += ["", "", 'if __name__ == "__main__":', "    unittest.main()", ""]
    return "\n".join(out)


def toml_text(repo: str) -> str:
    return TOML.format(allow="true" if repo == "detect" else "false", mode=repo)


def baseline_files(repo: str) -> dict[str, str]:
    """I file del progetto di prova sul predefinito, prima dell'installazione di tollgate."""
    return {
        "tollgate.toml": toml_text(repo),
        ".gitignore": "reports/\n__pycache__/\n",
        "src/__init__.py": "",
        "src/calc.py": CALC,
        "tests/__init__.py": "",
        "tests/test_calc.py": tests_text(),
        "web/__init__.py": "",
        "web/page.py": 'def titolo():\n    return "tollgate"\n',
        "web/tests/__init__.py": "",
        "web/tests/test_page.py": WEB_TESTS,
        "notes/README.md": "note del progetto di prova\n",
        "tools/unittest_junit.py": UNITTEST_JUNIT,
        "tools/empty_junit.py": EMPTY_JUNIT,
        ".github/workflows/ci.yml": CI_WORKFLOW,
    }


def write_baseline(repo: str, dest: Path) -> list[str]:
    files = baseline_files(repo)
    for rel, text in files.items():
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return sorted(files)


# ---------------------------------------------------------------- i piani, i blocchi, le deroghe

def plan_text(slug: str, *, modify=(), create=(), test=(), must_have: tuple[str, str] | None = None,
              extra: str = "") -> str:
    """Un piano valido per plan-check: un solo task che elenca i file di `modify`, `create` e `test`
    (lo scope); `must_have` è `(identificativo del test, testo)`."""
    mh_id, mh_text = must_have or ("tests.test_calc.CalcTest::test_somma", "La somma resta verde")
    out = [f"# Piano di prova: {slug}", ""]
    for section in SECTIONS:
        if section == "Must-have":
            out += [f"## {section}", f"M1. {mh_text} — test: {mh_id}", ""]
        else:
            out += [f"## {section}", "Nessuno: caso di prova." if section != "Scope" else
                    "I file del task 1.", ""]
    out += [f"### Task 1: {slug}"]
    out += [f"- Modify: `{p}`" for p in modify] + [f"- Create: `{p}`" for p in create]
    out += [f"- Test: `{p}`" for p in test] + ["**Must-have**: M1", ""]
    if extra:
        out += [extra, ""]
    return "\n".join(out) + "\n"


def waiver_file(issue: int, branch: str, items: list[dict]) -> str:
    ws = [waivers.Waiver(id=f"w-{issue}-{k}", type=w["type"], file=w["file"], pattern=None,
                         tests=list(w.get("tests", [])), choice="prova del gate", why="caso di prova",
                         cost="nessuno", declared_by="agent") for k, w in enumerate(items, 1)]
    return waivers.dumps(waivers.WaiverFile(issue=issue, branch=branch, waivers=ws))


# ---------------------------------------------------------------- struttura dei casi

@dataclass(frozen=True)
class Expect:
    """L'esito atteso per uno SHA spinto. `states`: contesto -> `success|failure|error|none|*`
    (`none`: nessuno stato con quel contesto, `*`: non determinato). `comments`: prefissi attesi tra
    i commenti del bot. `merge_state`: `mergeStateStatus` atteso (solo `protected`)."""
    push: str = "last"
    states: dict = field(default_factory=dict)
    comments: tuple = ()
    comments_once: tuple = ()               # prefissi che devono comparire in un solo commento del bot (aggiornato, non duplicato)
    merge_state: str | None = None
    sentinel_issue: bool | None = None      # una sola issue aperta di sentinel (True) o nessuna (False)
    sentinel_comments_min: int | None = None    # commenti almeno tanti sull'issue di sentinel
    note: str = ""


@dataclass(frozen=True)
class Case:
    name: str
    repo: str
    summary: str
    build: object
    expect: tuple
    oracle: bool = True


CASES: dict[str, Case] = {}
SUCCESS, FAILURE, ERROR, NONE, ANY = "success", "failure", "error", "none", "*"


def _states(guard, verdict, attention, **more):
    return {"tollgate/guard": guard, "tollgate/verdict": verdict, "tollgate/attention": attention, **more}


def case(name, repo, summary, *, expect, oracle=True):
    def register(fn):
        CASES[name] = Case(name, repo, summary, fn, tuple(expect), oracle)
        return fn
    return register


def verdict_comment(*extra):
    return (MARKERS["verdict"], *extra)


class Ctx:
    """Il clone, il caso e le operazioni che lo script farà: spingere SHA, aprire PR, aspettare."""

    def __init__(self, clone: Path, name: str, repo: str, issue: int, ts: str, extra_issue: int | None):
        self.clone, self.name, self.repo, self.issue, self.ts = Path(clone), name, repo, issue, ts
        self.extra_issue = extra_issue
        self.ops: list[dict] = []
        self.bodies: dict[str, str] = {}      # nome del file -> testo
        self.branch: str | None = None
        self.plan_path = self.plan_sha = None
        self._push_n = 0

    # git
    def git(self, *args) -> str:
        r = subprocess.run(["git", "-C", str(self.clone), "-c", "user.name=tollgate-p4-probe",
                            "-c", "user.email=probe@example.invalid", "-c", "commit.gpgsign=false", *args],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def start(self, branch: str, base: str = "origin/main") -> None:
        self.git("switch", "-q", "-c", branch, base)
        self.branch = branch

    def write(self, rel: str, text: str) -> None:
        path = self.clone / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def read(self, rel: str) -> str:
        return (self.clone / rel).read_text()

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.head()

    def commit_files(self, files: dict[str, str], message: str) -> str:
        for rel, text in files.items():
            self.write(rel, text)
        return self.commit(message)

    # piano e blocco
    def register_plan(self, slug: str, **kw) -> str:
        self.plan_path = f"{PLAN_DIR}/2026-10-21-{slug}.md"
        self.write(self.plan_path, plan_text(slug, **kw))
        sha = self.commit("piano")
        self.plan_sha = self.git("rev-parse", f"HEAD:{self.plan_path}")
        return sha

    def block(self, **override) -> dict:
        facts = {
            "schema_version": 1, "tollgate_version": VERSION, "issue": self.issue, "level": "L1",
            "level_minimum": "L1", "level_cap": None, "level_cap_reason": None, "gate_mode": self.repo,
            "plan": self.plan_path, "plan_sha": self.plan_sha, "spec": None, "spec_reviews_dir": None,
            "plan_reviews_dir": None, "spec_audit": {"adversarial": None, "lens": None},
            "head_sha": self.head(),
            "receipts": [{"command": "verify", "state": "green", "tests_run": 2}],
            "waivers_file": f".tollgate/waivers/{self.issue}.toml", "blocks": [], "acts": [],
            "dod": {"L": "L1", "items": {"receipt": True}},
            "verdict": {"outcome": "ok", "cycles": 1, "findings_confirmed": 0, "unverified": False},
            "findings": [], "fix_rounds": {}, "subagents": {"count": 0, "tokens": 0}, "effects": [],
            "components_off": [], "off_periods": [], "tasks_over": [], "skills_absent": []}
        facts.update(override)
        return prblock.build(facts)

    def work_body(self, block_override=None, closes: int | None = None) -> str:
        n = self.issue if closes is None else closes
        return f"Closes #{n}\n\n" + prblock.render(self.block(**(block_override or {}))) + "\n"

    # operazioni
    def push(self, branch: str | None = None, sha: str | None = None) -> str:
        self._push_n += 1
        pid = f"p{self._push_n}"
        self.ops.append({"op": "push", "id": pid, "branch": branch or self.branch, "sha": sha or self.head()})
        return pid

    def open_pr(self, body: str, *, branch: str | None = None, base: str = "main", title: str | None = None,
                key: str | None = None) -> None:
        branch = branch or self.branch
        key = key or branch.replace("/", "-")
        self.bodies[f"body-{key}.md"] = body
        self.ops.append({"op": "pr", "branch": branch, "base": base, "body": f"body-{key}.md",
                         "title": title or f"prova P4: {self.name}"})

    def sleep(self, seconds: int) -> None:
        self.ops.append({"op": "sleep", "s": seconds})

    def wait(self, push: str) -> None:
        self.ops.append({"op": "wait", "push": push})

    def wait_count(self, push: str, context: str, n: int) -> None:
        self.ops.append({"op": "wait_count", "push": push, "context": context, "n": n})

    def edit_pr(self, branch: str, body: str, key: str) -> None:
        self.bodies[f"body-{key}.md"] = body
        self.ops.append({"op": "edit", "branch": branch, "body": f"body-{key}.md"})

    def post_status(self, push: str, context: str, state: str) -> None:
        self.ops.append({"op": "post_status", "push": push, "context": context, "state": state})

    def direct(self, rel: str, text: str) -> str:
        """Un commit nuovo sulla punta di origin/main e il suo push diretto su main (solo detect): lo fa lo script
        al momento giusto, dopo gli eventuali merge."""
        self._push_n += 1
        pid = f"p{self._push_n}"
        self.ops.append({"op": "direct", "id": pid, "file": rel, "text": text})
        return pid

    def merge(self, branch: str, mode: str = "--squash") -> str:
        self._push_n += 1
        pid = f"p{self._push_n}"
        self.ops.append({"op": "merge", "id": pid, "branch": branch, "mode": mode})
        return pid

    def simple_pr(self, body: str, **kw) -> str:
        pid = self.push()
        self.open_pr(body, **kw)
        return pid


# ---------------------------------------------------------------- costruzione di una PR di lavoro

def feature_files(*, sottrai=True, cls="CalcTest", skip_sottrai=False) -> dict[str, str]:
    return {"src/calc.py": CALC_MOLT, "tests/test_calc.py": tests_text(
        sottrai=sottrai, moltiplica=True, cls=cls, skip_sottrai=skip_sottrai)}


def work(ctx: Ctx, slug: str, *, changes: dict[str, str] | None = None, modify=None, create=(), test=None,
         must_have=None, block_override=None, waiver=None, plan_extra: str = "", push=True) -> None:
    """La PR di un lavoro su `tg/<N>-<slug>`: commit del piano, commit dei cambi, e la PR con il blocco.
    Lo scope del piano è l'elenco dei file di `changes` (o di `modify`/`create`/`test`)."""
    default_must_have = ("tests.test_calc.CalcTest::test_somma", "La somma resta verde")
    if changes is None:
        changes = feature_files()
        default_must_have = ("tests.test_calc.CalcTest::test_moltiplica", "Moltiplica")
    ctx.start(f"tg/{ctx.issue}-{slug}")
    files = list(changes)
    modify = [p for p in files if p == "src/calc.py"] if modify is None else list(modify)
    test = [p for p in files if "/tests/" in "/" + p] if test is None else list(test)
    other = [p for p in files if p not in modify and p not in test and p not in create]
    ctx.register_plan(slug, modify=modify + other, create=list(create), test=test, extra=plan_extra,
                      must_have=must_have or default_must_have)
    if waiver:
        changes = {**changes, f".tollgate/waivers/{ctx.issue}.toml":
                   waiver_file(ctx.issue, ctx.branch, waiver)}
    ctx.commit_files(changes, f"cambi del caso {ctx.name}")
    if push:
        ctx.simple_pr(ctx.work_body(block_override))


# ---------------------------------------------------------------- i casi: verdi

@case("verde-pulita", "protected", "PR pulita: moltiplica con il suo test",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, SUCCESS), comments=verdict_comment(), merge_state="CLEAN")])
def _verde_pulita(ctx):
    work(ctx, "pulita")


@case("verde-config", "protected", "ramo tollgate-config/*: solo tollgate.toml cambiato, `attenzione` rosso",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment(), merge_state="CLEAN")])
def _verde_config(ctx):
    ctx.start(f"tollgate-config/p4-{ctx.ts}")
    ctx.commit_files({"tollgate.toml": ctx.read("tollgate.toml") + "\n[acts]\nttl_minutes = 11\n"},
                     "configurazione di prova")
    ctx.simple_pr("Aggiornamento di prova della configurazione di tollgate.\n")


@case("verde-ramo-libero", "protected", "ramo non tg/*: nessun controllo di scope e piano, `attenzione` rosso",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment(), merge_state="CLEAN")])
def _verde_ramo_libero(ctx):
    ctx.start(f"prova/p4-ramo-libero-{ctx.ts}")
    ctx.commit_files(feature_files(), "moltiplica")
    ctx.simple_pr("PR di prova fuori dai rami tg/*.\n")


@case("verde-edit", "protected",
      "PR pulita, poi il corpo modificato (`edited`): il commento del verdetto si aggiorna con PATCH, non si duplica",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, SUCCESS), comments=verdict_comment(),
                     comments_once=verdict_comment(), merge_state="CLEAN")], oracle=False)
def _verde_edit(ctx):
    work(ctx, "edit", push=False)
    body = ctx.work_body()
    pid = ctx.push()
    ctx.open_pr(body)
    ctx.wait(pid)
    ctx.edit_pr(ctx.branch, body + "\nCorpo modificato dopo l'apertura.\n", "edit")
    ctx.wait_count(pid, "tollgate/verdict", 2)


# ---------------------------------------------------------------- i casi: verdict rosso

RED = Expect(states=_states(SUCCESS, FAILURE, SUCCESS), comments=verdict_comment(), merge_state="BLOCKED")


def red(**states):
    return Expect(states={**RED.states, **states}, comments=verdict_comment(), merge_state="BLOCKED")


@case("rosso-test-tolti", "protected", "un test della base tolto dal file di test", expect=[red()])
def _rosso_test_tolti(ctx):
    work(ctx, "test-tolti", changes=feature_files(sottrai=False))


@case("rosso-skip", "protected", "un test della base marcato `unittest.skip`", expect=[red()])
def _rosso_skip(ctx):
    work(ctx, "skip", changes=feature_files(skip_sottrai=True))


@case("rosso-fuori-scope", "protected", "un file non elencato nel piano", expect=[red()])
def _rosso_fuori_scope(ctx):
    changes = feature_files()
    ctx.start(f"tg/{ctx.issue}-fuori-scope")
    ctx.register_plan("fuori-scope", modify=["src/calc.py"], test=["tests/test_calc.py"],
                      must_have=("tests.test_calc.CalcTest::test_moltiplica", "Moltiplica"))
    ctx.commit_files({**changes, "src/extra.py": "EXTRA = 1\n"}, "cambi e un file fuori scope")
    ctx.simple_pr(ctx.work_body())


@case("rosso-base-id", "protected", "la classe dei test rinominata: gli identificativi della base non ci sono",
      expect=[red()])
def _rosso_base_id(ctx):
    work(ctx, "base-id", changes=feature_files(cls="CalcTests"),
         must_have=("tests.test_calc.CalcTests::test_moltiplica", "Moltiplica"))


@case("rosso-or-true", "protected", "comando del profilo web con `|| true` e un test che fallisce",
      expect=[red()])
def _rosso_or_true(ctx):
    text = WEB_TESTS + ("\n    def test_rotto(self):\n"
                        "        self.assertEqual(titolo(), \"altro\")\n")
    work(ctx, "or-true", changes={"web/tests/test_page.py": text}, test=["web/tests/test_page.py"],
         must_have=("web.tests.test_page.WebTest::test_titolo", "Il titolo"))


@case("rosso-livello", "protected", "percorso sensibile (src/auth) con livello L1 senza tetto", expect=[red()])
def _rosso_livello(ctx):
    work(ctx, "livello", changes={"src/auth/token.py": "TOKEN = 1\n"}, create=["src/auth/token.py"],
         modify=[], test=[])


@case("rosso-l2-mancante", "protected", "livello L2 dichiarato, senza approvazione né report di L2", expect=[red()])
def _rosso_l2(ctx):
    spec = f"{SPEC_DIR}/2026-10-21-l2-mancante.md"
    ctx.start(f"tg/{ctx.issue}-l2-mancante")
    ctx.commit_files({spec: "# Spec di prova\n\n## Obiettivo\nx\n"}, "spec")
    ctx.register_plan("l2-mancante", modify=["src/calc.py"], test=["tests/test_calc.py"],
                      must_have=("tests.test_calc.CalcTest::test_moltiplica", "Moltiplica"))
    ctx.commit_files(feature_files(), "cambi")
    ctx.simple_pr(ctx.work_body({"level": "L2", "spec": spec,
                                 "spec_reviews_dir": f"docs/superpowers/reviews/{ctx.issue}"}))


@case("rosso-deroga-altra-issue", "protected",
      "un test tolto con la deroga nel file di un'altra issue (non vale)", expect=[red()])
def _rosso_deroga_altra(ctx):
    other = 9999
    ctx.start(f"tg/{ctx.issue}-deroga-altra")
    ctx.register_plan("deroga-altra", modify=["src/calc.py"], test=["tests/test_calc.py"],
                      must_have=("tests.test_calc.CalcTest::test_moltiplica", "Moltiplica"))
    ctx.commit_files({**feature_files(sottrai=False),
                      f".tollgate/waivers/{other}.toml": waiver_file(other, ctx.branch, [
                          {"type": "test", "file": "tests/test_calc.py",
                           "tests": ["tests.test_calc.CalcTest::test_sottrai"]}])}, "cambi e deroga")
    ctx.simple_pr(ctx.work_body())


@case("rosso-zero-test", "protected", "un profilo il cui comando non esegue test, con allow_no_tests = false",
      expect=[red()])
def _rosso_zero_test(ctx):
    work(ctx, "zero-test", changes={"notes/nota.md": "una nota\n"}, create=["notes/nota.md"], modify=[], test=[],
         must_have=("tests.test_calc.CalcTest::test_somma", "La somma resta verde"))


@case("rosso-piano-file-nuovo", "protected",
      "il piano cambiato dopo la registrazione per aggiungere un file: quel file è fuori scope",
      expect=[Expect(states=_states(SUCCESS, FAILURE, FAILURE), comments=verdict_comment(),
                     merge_state="BLOCKED")])
def _rosso_piano_file(ctx):
    work(ctx, "piano-file", push=False)
    ctx.write(ctx.plan_path, ctx.read(ctx.plan_path).replace(
        "**Must-have**: M1\n", "**Must-have**: M1\n\n### Task 2: Extra\n- Create: `src/extra.py`\n", 1))
    ctx.commit_files({"src/extra.py": "EXTRA = 1\n"}, "piano cambiato e file nuovo")
    ctx.simple_pr(ctx.work_body())


# ---------------------------------------------------------------- i casi: guard rosso

GUARD_RED = Expect(states=_states(FAILURE, FAILURE, ANY), comments=(MARKERS["guard"], MARKERS["verdict"]),
                   merge_state="BLOCKED")

WORKFLOWS = {
    "prt": ("on:\n  pull_request_target:\n    types: [opened]\npermissions:\n  contents: read\n",
            "usa pull_request_target"),
    "run": ("on:\n  workflow_run:\n    workflows: [ci]\n    types: [completed]\npermissions:\n  contents: read\n",
            "usa workflow_run"),
    "statuses": ("on: workflow_dispatch\npermissions:\n  contents: read\n  statuses: write\n",
                 "statuses: write"),
    "writeall": ("on: workflow_dispatch\npermissions: write-all\n", "permissions: write-all"),
    "ancora": ("on: workflow_dispatch\npermissions:\n  contents: read\nenv: &base\n  X: \"1\"\n",
               "àncora YAML"),
}


def _guard_workflow(variant):
    head, _ = WORKFLOWS[variant]
    text = f"name: p4-{variant}\n{head}jobs:\n  noop:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo p4\n"
    path = f".github/workflows/p4-{variant}.yml"

    def build(ctx):
        work(ctx, f"guard-wf-{variant}", changes={path: text}, create=[path], modify=[], test=[])
    return build


for _v, (_, _why) in WORKFLOWS.items():
    case(f"guard-wf-{_v}", "protected", f"workflow nuovo del progetto che viola guard: {_why}",
         expect=[GUARD_RED])(_guard_workflow(_v))


@case("guard-toml", "protected", "tollgate.toml cambiato in una PR di lavoro",
      expect=[Expect(states=_states(FAILURE, SUCCESS, ANY), comments=(MARKERS["guard"], MARKERS["verdict"]),
                     merge_state="BLOCKED")])
def _guard_toml(ctx):
    toml = ctx.git("show", "origin/main:tollgate.toml") + "\n\n[acts]\nttl_minutes = 11\n"
    work(ctx, "guard-toml", changes={"tollgate.toml": toml},
         modify=["tollgate.toml"], test=[])


@case("guard-verdict-yml", "protected", "tollgate-verdict.yml modificato in una PR di lavoro", expect=[GUARD_RED])
def _guard_verdict(ctx):
    path = ".github/workflows/tollgate-verdict.yml"
    work(ctx, "guard-verdict", changes={path: ctx.read(path) + "# prova\n"}, modify=[path], test=[])


# ---------------------------------------------------------------- i casi: attenzione

@case("verde-workflow-ci", "protected",
      "workflow ci.yml modificato (contents: read) con la deroga `ci`: `attenzione` rosso",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment(), merge_state="CLEAN")])
def _verde_workflow_ci(ctx):
    path = ".github/workflows/ci.yml"
    work(ctx, "workflow-ci", changes={path: CI_WORKFLOW + "      - run: echo ancora ci\n"}, modify=[path], test=[],
         waiver=[{"type": "ci", "file": path}])


@case("attenzione-deroga-test", "protected", "un test tolto con la deroga `test` che lo elenca",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment(), merge_state="CLEAN")])
def _attenzione_deroga_test(ctx):
    work(ctx, "deroga-test", changes=feature_files(sottrai=False),
         waiver=[{"type": "test", "file": "tests/test_calc.py",
                  "tests": ["tests.test_calc.CalcTest::test_sottrai"]}])


@case("attenzione-piano-testo", "protected", "piano cambiato solo nel testo, senza file nuovi: `plan_changed`",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment(), merge_state="CLEAN")])
def _attenzione_piano_testo(ctx):
    work(ctx, "piano-testo", push=False)
    ctx.write(ctx.plan_path, ctx.read(ctx.plan_path).replace("## Rischi\nNessuno: caso di prova.",
                                                            "## Rischi\nRiscritto dopo la registrazione."))
    ctx.commit("piano riscritto")
    ctx.simple_pr(ctx.work_body())


@case("attenzione-tetto-livello", "protected", "percorso sensibile con livello L1 e un tetto dichiarato",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment(), merge_state="CLEAN")])
def _attenzione_tetto(ctx):
    work(ctx, "tetto", changes={"src/auth/token.py": "TOKEN = 1\n"}, create=["src/auth/token.py"], modify=[],
         test=[], block_override={"level_cap": "L1", "level_cap_reason": "prova del tetto di livello"})


@case("attenzione-zero-test", "detect",
      "profilo senza test con allow_no_tests = true (solo sul repo detect): `no_tests_counted`",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, FAILURE), comments=verdict_comment())])
def _attenzione_zero_test(ctx):
    work(ctx, "zero-test", changes={"notes/nota.md": "una nota\n"}, create=["notes/nota.md"], modify=[], test=[],
         must_have=("tests.test_calc.CalcTest::test_somma", "La somma resta verde"))


# ---------------------------------------------------------------- i casi: error e non applicabile (non modellati)

ERR = Expect(states=_states(ERROR, ERROR, ERROR), merge_state="BLOCKED")


@case("error-dotdot", "protected",
      "un report di results.json con `..`: il ramo cambia la copia di gate run installata in .github/tollgate",
      expect=[Expect(states=_states(FAILURE, ERROR, ERROR), comments=(MARKERS["guard"],), merge_state="BLOCKED")],
      oracle=False)
def _error_dotdot(ctx):
    path = ".github/tollgate/bin/tollgate_gate/run.py"
    text = ctx.read(path)
    old = 'report = f"junit/{i}.xml"'
    assert old in text, "run.py non contiene più la riga del percorso del report"
    work(ctx, "error-dotdot", changes={path: text.replace(old, 'report = f"junit/../{i}.xml"')},
         modify=[path], test=[])


@case("error-entita", "protected",
      "un report JUnit con un'entità XML copiato negli artefatti (la copia di gate run cambiata nel ramo)",
      expect=[Expect(states=_states(FAILURE, ERROR, ERROR), comments=(MARKERS["guard"],), merge_state="BLOCKED")],
      oracle=False)
def _error_entita(ctx):
    path = ".github/tollgate/bin/tollgate_gate/run.py"
    text = ctx.read(path)
    old = '        (out / "results.json").write_text('
    assert text.count(old) == 1, "run.py non contiene più la riga di results.json"
    evil = ('        if applicable:\n            (out / "junit" / "evil.xml").write_text(\n'
            '                \'<!DOCTYPE a [<!ENTITY b "c">]><testsuite><testcase classname="a" name="&b;"/></testsuite>\')\n')
    work(ctx, "error-entita", changes={path: text.replace(old, evil + old)}, modify=[path], test=[])


@case("rosso-entita-tools", "protected",
      "un report JUnit con un'entità scritto da tools/unittest_junit.py: il report è rifiutato, il comando è rosso",
      expect=[red()])
def _rosso_entita_tools(ctx):
    text = UNITTEST_JUNIT.replace(
        'report.write_text("<testsuite>" + body + "</testsuite>")',
        'report.write_text(\'<!DOCTYPE a [<!ENTITY b "c">]><testsuite>\' + body + "</testsuite>")')
    assert text != UNITTEST_JUNIT
    work(ctx, "entita-tools", changes={"tools/unittest_junit.py": text}, modify=["tools/unittest_junit.py"],
         test=[])


@case("error-sha-superato", "protected", "un secondo push mentre `tollgate-run` gira: lo SHA giudicato è superato",
      expect=[Expect(push="p1", states=_states(ANY, ERROR, ERROR),
                     note="verdict su A: error se la testa è già B; success se il run di A ha finito prima del push"),
              Expect(push="p2", states=_states(SUCCESS, SUCCESS, SUCCESS), comments=verdict_comment(),
                     merge_state="CLEAN")], oracle=False)
def _error_sha_superato(ctx):
    work(ctx, "sha-superato", push=False)
    first = ctx.push()
    ctx.open_pr(ctx.work_body())
    ctx.sleep(15)
    ctx.write("src/calc.py", ctx.read("src/calc.py") + "\n# secondo push\n")
    ctx.commit("secondo push durante il run")
    ctx.push()


@case("error-due-pr", "protected", "due PR aperte sulla stessa testa (due rami allo stesso commit)",
      expect=[Expect(push="p1", states=_states(ERROR, ERROR, ERROR), merge_state="BLOCKED")], oracle=False)
def _error_due_pr(ctx):
    work(ctx, "due-pr", push=False)
    ctx.git("branch", f"tg/{ctx.issue}-due-pr-bis")
    first = ctx.push()
    ctx.open_pr(ctx.work_body(), key="a", title=f"prova P4: {ctx.name} (A)")
    ctx.push(branch=f"tg/{ctx.issue}-due-pr-bis", sha=ctx.head())
    ctx.open_pr(ctx.work_body(), branch=f"tg/{ctx.issue}-due-pr-bis", key="b", title=f"prova P4: {ctx.name} (B)")


@case("non-applicabile", "protected", "PR verso il ramo `other`: nessuno stato tollgate/*, solo il commento",
      expect=[Expect(states=_states(NONE, NONE, NONE), comments=(MARKERS["guard"], MARKERS["na"]))], oracle=False)
def _non_applicabile(ctx):
    ctx.start(f"prova/p4-non-applicabile-{ctx.ts}")
    ctx.commit_files(feature_files(), "moltiplica")
    ctx.ops.append({"op": "push", "id": "p0", "branch": "other", "sha": ctx.git("rev-parse", "origin/main")})
    ctx.simple_pr("PR di prova verso other.\n", base="other")


@case("token-personale", "protected",
      "lo stato tollgate/verdict pubblicato con il token personale su una PR rossa: la PR resta BLOCKED",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, SUCCESS), merge_state="BLOCKED",
                     note="verdict: l'ultimo stato è quello dell'utente (success), ma non vale per la protezione")],
      oracle=False)
def _token_personale(ctx):
    work(ctx, "token-personale", changes=feature_files(sottrai=False), push=False)
    pid = ctx.push()
    ctx.open_pr(ctx.work_body())
    ctx.wait(pid)
    ctx.post_status(pid, "tollgate/verdict", "success")


# ---------------------------------------------------------------- i casi del repo detect (Step 4)

@case("detect-pulita", "detect", "PR pulita sul repo detect: stati guard e verdict verdi",
      expect=[Expect(states=_states(SUCCESS, SUCCESS, SUCCESS), comments=verdict_comment())])
def _detect_pulita(ctx):
    work(ctx, "detect-pulita")


@case("detect-closes", "detect", "tg/N-x con «Closes #M» di un'issue chiusa: `closes_mismatch`",
      expect=[Expect(states=_states(SUCCESS, FAILURE, SUCCESS), comments=verdict_comment())], oracle=False)
def _detect_closes(ctx):
    assert ctx.extra_issue, "serve --extra-issue (un'issue chiusa)"
    work(ctx, "detect-closes", push=False)
    ctx.simple_pr(ctx.work_body(closes=ctx.extra_issue))


@case("detect-push-diretto", "detect", "push diretto su main: tollgate/sentinel rosso e issue",
      expect=[Expect(push="p1", states={"tollgate/sentinel": FAILURE}, sentinel_issue=True)], oracle=False)
def _detect_push_diretto(ctx):
    ctx.direct(f"notes/diretto-{ctx.ts}.md", "push diretto di prova")


@case("detect-merge-rosso", "detect",
      "(ultimo caso detect: degrada la base di detect, i casi detect lanciati dopo partono da una base senza test_sottrai) PR con verdict rosso unita: tollgate/sentinel rosso e issue; poi un push diretto su main: stesso esito, "
      "commento sulla stessa issue",
      expect=[Expect(push="p1", states=_states(SUCCESS, FAILURE, SUCCESS), comments=verdict_comment()),
              Expect(push="p2", states={"tollgate/sentinel": FAILURE}, sentinel_issue=True),
              Expect(push="p3", states={"tollgate/sentinel": FAILURE}, sentinel_issue=True,
                     sentinel_comments_min=1)], oracle=False)
def _detect_merge_rosso(ctx):
    work(ctx, "detect-merge-rosso", changes=feature_files(sottrai=False))
    ctx.wait("p1")
    ctx.merge(ctx.branch)
    ctx.direct(f"notes/diretto-{ctx.ts}.md", "push diretto di prova")


# ---------------------------------------------------------------- uso

def build_case(name: str, clone: Path, issue: int, ts: str, out: Path, label: str,
               extra_issue: int | None = None) -> dict:
    spec = CASES[name]
    ctx = Ctx(clone, name, spec.repo, issue, ts, extra_issue)
    spec.build(ctx)
    out.mkdir(parents=True, exist_ok=True)
    for fname, text in ctx.bodies.items():
        (out / f"{label}-{fname}").write_text(text)
    ops = []
    for op in ctx.ops:
        op = dict(op)
        if "body" in op:
            op["body_file"] = str(out / f"{label}-{op.pop('body')}")
        ops.append(op)
    pushes = [o["id"] for o in ops if o["op"] in ("push", "merge")]
    expect = []
    for e in spec.expect:
        item = {"push": pushes[-1] if e.push == "last" else e.push, "states": e.states,
                "comments": list(e.comments), "comments_once": list(e.comments_once), "merge_state": e.merge_state,
                "sentinel_issue": e.sentinel_issue, "sentinel_comments_min": e.sentinel_comments_min,
                "note": e.note}
        expect.append(item)
    data = {"name": name, "repo": spec.repo, "summary": spec.summary, "issue": issue, "ops": ops,
            "expect": expect, "branch": ctx.branch}
    (out / f"{label}-case.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def latest_states(lines: list[dict]) -> dict:
    """Per contesto lo stato più recente (l'API li dà dal più recente), con autore e descrizione."""
    out: dict = {}
    for s in lines:
        out.setdefault(s["context"], {"state": s["state"], "creator": s.get("creator"),
                                      "description": s.get("description", "")})
    return out


def _jsonl(path: str | None) -> list[dict]:
    if not path or not Path(path).is_file():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def judge(data: dict, push: str, *, statuses: list[dict], comments: list[dict], merge_state: str | None,
          sentinel_issues: int | None, pr: str, sha: str,
          sentinel_comments: int | None = None) -> tuple[bool, str]:
    exp = next((e for e in data["expect"] if e["push"] == push), None)
    if exp is None:
        return True, f"| {data['name']} | {pr} | {sha[:10]} | non giudicato (nessuna attesa per {push}) | | | |"
    got = latest_states(statuses)
    problems, shown, wanted = [], [], []
    contexts = list(exp["states"])
    for ctxname in contexts:
        want = exp["states"][ctxname]
        have = got.get(ctxname)
        wanted.append(f"{ctxname.split('/')[-1]}={want}")
        shown.append(f"{ctxname.split('/')[-1]}={have['state'] if have else 'none'}"
                     + (f" ({have['creator']})" if have else ""))
        if want == ANY:
            continue
        actual = have["state"] if have else NONE
        if actual != want:
            problems.append(f"{ctxname}: atteso {want}, ottenuto {actual}")
    bots = [c.get("body", "").lstrip() for c in comments if c.get("user") == BOT]
    for prefix in exp["comments"]:
        if not any(b.startswith(prefix) for b in bots):
            problems.append(f"manca il commento del bot «{prefix}»")
    for prefix in exp.get("comments_once", ()):
        n = sum(1 for b in bots if b.startswith(prefix))
        wanted.append(f"un solo commento «{prefix}»")
        shown.append(f"commenti «{prefix}»={n}")
        if n != 1:
            problems.append(f"commenti del bot «{prefix}»: {n} invece di uno (duplicato o mancante)")
    if exp["merge_state"] is not None:
        wanted.append(f"merge={exp['merge_state']}")
        shown.append(f"merge={merge_state}")
        if merge_state != exp["merge_state"]:
            problems.append(f"mergeStateStatus: atteso {exp['merge_state']}, ottenuto {merge_state}")
    if exp.get("sentinel_issue") is not None:
        wanted.append(f"issue sentinel={'1' if exp['sentinel_issue'] else '0'}")
        shown.append(f"issue sentinel={sentinel_issues}")
        if (sentinel_issues or 0) != (1 if exp["sentinel_issue"] else 0):
            problems.append(f"issue di sentinel aperte: ottenute {sentinel_issues}")
    if exp.get("sentinel_comments_min") is not None:
        wanted.append(f"commenti sull'issue >= {exp['sentinel_comments_min']}")
        shown.append(f"commenti sull'issue={sentinel_comments}")
        if (sentinel_comments or 0) < exp["sentinel_comments_min"]:
            problems.append(f"commenti sull'issue di sentinel: ottenuti {sentinel_comments}")
    ok = not problems
    verdict = "riuscito" if ok else "non riuscito: " + "; ".join(problems)
    note = f" ({exp['note']})" if exp.get("note") else ""
    row = (f"| {data['name']} | {pr} | {sha[:10]} | {', '.join(shown)} | {', '.join(wanted)}{note} | {verdict} | |")
    return ok, row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    b = sub.add_parser("baseline")
    b.add_argument("repo", choices=sorted(REPOS))
    b.add_argument("dest")
    c = sub.add_parser("build")
    c.add_argument("case", choices=sorted(CASES))
    c.add_argument("--clone", required=True)
    c.add_argument("--issue", type=int, required=True)
    c.add_argument("--extra-issue", type=int)
    c.add_argument("--ts", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--label", required=True)
    j = sub.add_parser("judge")
    j.add_argument("case_json")
    j.add_argument("--push", required=True)
    j.add_argument("--statuses")
    j.add_argument("--comments")
    j.add_argument("--merge")
    j.add_argument("--sentinel-issues", type=int)
    j.add_argument("--sentinel-comments", type=int)
    j.add_argument("--pr", default="-")
    j.add_argument("--sha", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for name, spec in CASES.items():
            exp = spec.expect[-1]
            states = ", ".join(f"{k.split('/')[-1]}={v}" for k, v in exp.states.items())
            print(f"{name}\t{spec.repo}\t{states}\t{spec.summary}")
        return 0
    if args.cmd == "baseline":
        for rel in write_baseline(args.repo, Path(args.dest)):
            print(rel)
        return 0
    if args.cmd == "build":
        data = build_case(args.case, Path(args.clone), args.issue, args.ts, Path(args.out), args.label,
                          args.extra_issue)
        print(json.dumps({"ops": len(data["ops"]), "branch": data["branch"]}))
        return 0
    data = json.loads(Path(args.case_json).read_text())
    ok, row = judge(data, args.push, statuses=_jsonl(args.statuses), comments=_jsonl(args.comments),
                    merge_state=args.merge, sentinel_issues=args.sentinel_issues, pr=args.pr, sha=args.sha,
                    sentinel_comments=args.sentinel_comments)
    print(row)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
