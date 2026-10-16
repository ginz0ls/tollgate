### Task 6: Analisi: test-guard

**Files:**
- Create: `bin/tollgate_analysis/scan.py`
- Create: `bin/tollgate_analysis/testids.py`
- Create: `bin/tollgate_analysis/testguard.py`
- Test: `tests/test_testids.py`, `tests/test_testguard.py`

**Interfaces:**
- Consumes: `globs.match_any`.
- Produces:
  - `scan.js_tokens(text)` (generatore di `(tipo, valore)` con tipo `str`, `id`, `p`); `scan.js_code(text) -> str` (codice senza commenti, stringhe come `S`); `scan.py_code(text) -> str | None`.
  - `testids.language(path) -> str | None` (`js`, `py`, `go`, `java`, `rust`); `testids.test_ids(text, rel, *, js_form) -> tuple[dict[str, str], set[str]] | None` (locali attivi → identificativo completo; locali saltati; `None` se il file non si legge).
  - `testguard.DEFAULT_TEST_GLOBS`; `testguard.Violation(kind, path, detail, waiver_type, ids=())`; `testguard.Change(status, path, old_path, base_text, head_text, binary=False)`; `testguard.GuardConfig(test_globs, fixture_globs, ci_globs, verification_globs, verification_watch, skip_markers=(), assert_markers=(), js_form="vitest")`; `testguard.check(changes, cfg) -> GuardResult(violations, watched)`.
  - Tipi di violazione (`kind` → `waiver_type`): `test_deleted` → `test`; `test_id_missing` → `test`; `asserts_decreased` → `test`; `skip_added` → `test`; `unparsable` → `test`; `fixture_changed` → `test`; `ci_changed` → `ci`; `threshold_lowered` → `threshold`; `verification_changed` → `command`. Il Task 15 aggiunge `out_of_scope` → `scope` con la stessa classe.

- [ ] **Step 1: Test**

`tests/test_testids.py`:

```python
import unittest

from tollgate_analysis import scan, testids

JS = """
import { describe, it, expect } from 'vitest'
// it('commentato', () => {})
describe('format', () => {
  it('handles UTC', () => { expect(1).toBe(1) })
  describe("nested", () => {
    test(`deep`, () => {})
  })
  it.skip('saltato', () => {})
})
it('top', () => {})
"""

PY = '''
import pytest, unittest

def test_a():
    assert 1

@pytest.mark.skip
def test_skipped():
    pass

class TestGroup:
    def test_b(self):
        assert "assert dentro una stringa"

class Other(unittest.TestCase):
    def test_c(self):
        self.assertEqual(1, 1)
'''


class TestIdsTest(unittest.TestCase):
    def test_js_vitest_and_jest_forms(self):
        active, skipped = testids.test_ids(JS, "src/date.test.ts", js_form="vitest")
        self.assertEqual(set(active.values()), {
            "src/date.test.ts::format > handles UTC", "src/date.test.ts::format > nested > deep",
            "src/date.test.ts::top"})
        self.assertEqual(skipped, {"format > saltato"})
        active, _ = testids.test_ids(JS, "src/date.test.ts", js_form="jest")
        self.assertIn("src/date.test.ts::format handles UTC", active.values())

    def test_python_pytest_form(self):
        active, skipped = testids.test_ids(PY, "tests/test_x.py", js_form="vitest")
        self.assertEqual(set(active.values()), {"tests.test_x::test_a",
                                                "tests.test_x.TestGroup::test_b",
                                                "tests.test_x.Other::test_c"})
        self.assertEqual(skipped, {"test_skipped"})
        self.assertIn("TestGroup::test_b", active)

    def test_python_syntax_error(self):
        self.assertIsNone(testids.test_ids("def test_a(:\n", "tests/test_x.py", js_form="vitest"))

    def test_go(self):
        active, _ = testids.test_ids("func TestSum(t *testing.T) {}\n", "pkg/sum_test.go",
                                     js_form="vitest")
        self.assertEqual(set(active.values()), {"pkg::TestSum"})

    def test_code_without_comments_and_strings(self):
        self.assertNotIn("commentato", scan.js_code("// it('commentato')\nx = 'testo'"))
        self.assertNotIn("dentro", scan.py_code("x = 'assert dentro'  # assert commento\n"))
        self.assertIsNone(scan.py_code("x = '\n"))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_testguard.py`:

```python
import unittest

from tollgate_analysis.testguard import (DEFAULT_TEST_GLOBS, Change, GuardConfig, check)

CFG = GuardConfig(test_globs=DEFAULT_TEST_GLOBS, fixture_globs=["**/fixtures/**/*.json"],
                  ci_globs=[".github/workflows/**"],
                  verification_globs=["**/vitest.config.*", "**/conftest.py"],
                  verification_watch=["**/package.json", "**/pyproject.toml"])

JS_BASE = "describe('a', () => {\n  it('x', () => { expect(1).toBe(1) })\n  it('y', () => {})\n})\n"
PY_BASE = "def test_a():\n    assert 1\n\ndef test_b():\n    assert 2\n"


def kinds(changes):
    return sorted(v.kind for v in check(changes, CFG).violations)


class TestGuardTest(unittest.TestCase):
    def test_deleted_test_file(self):
        self.assertEqual(kinds([Change("D", "src/__tests__/a.test.js", None, JS_BASE, None)]),
                         ["test_deleted"])

    def test_xdescribe_added(self):
        head = JS_BASE.replace("describe(", "xdescribe(")
        self.assertIn("skip_added", kinds([Change("M", "src/a.test.ts", None, JS_BASE, head)]))

    def test_pytest_skip_added(self):
        head = PY_BASE.replace("    assert 2", "    pytest.skip('no')\n    assert 2")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["skip_added"])

    def test_pytest_mark_skip_added(self):
        head = "import pytest\n" + PY_BASE.replace("def test_b", "@pytest.mark.skip\ndef test_b")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["skip_added", "test_id_missing"])

    def test_assertion_replaced_by_comment(self):
        head = PY_BASE.replace("    assert 2", "    # assert 2\n    pass")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["asserts_decreased"])

    def test_missing_id(self):
        head = "def test_a():\n    assert 1\n    assert 2\n"
        v = check([Change("M", "tests/test_x.py", None, PY_BASE, head)], CFG).violations
        self.assertEqual([(x.kind, x.ids) for x in v],
                         [("test_id_missing", ("tests.test_x::test_b",))])

    def test_process_exit_is_fine(self):
        head = JS_BASE.replace("expect(1).toBe(1)", "expect(1).toBe(1); process.exit(0)")
        self.assertEqual(kinds([Change("M", "src/a.test.ts", None, JS_BASE, head)]), [])

    def test_rename_with_same_tests(self):
        self.assertEqual(kinds([Change("R", "tests/test_y.py", "tests/test_x.py",
                                       PY_BASE, PY_BASE)]), [])

    def test_ci_fixture_verification_threshold(self):
        changes = [
            Change("M", ".github/workflows/ci.yml", None, "a", "b"),
            Change("M", "tests/fixtures/data/x.json", None, "{}", "{\"a\": 1}"),
            Change("M", "vitest.config.ts", None, "lines: 90", "lines: 80"),
        ]
        self.assertEqual(kinds(changes), ["ci_changed", "fixture_changed", "threshold_lowered",
                                          "verification_changed"])

    def test_watch_is_info_only(self):
        r = check([Change("M", "package.json", None, "{}", "{\"x\": 1}")], CFG)
        self.assertEqual((r.violations, r.watched), ([], ["package.json"]))

    def test_new_file_with_skip(self):
        head = "def test_a():\n    pytest.skip('x')\n"
        self.assertEqual(kinds([Change("A", "tests/test_new.py", None, None, head)]),
                         ["skip_added"])

    def test_unparsable_head(self):
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, "def (:\n")]),
                         ["unparsable"])

    def test_binary_and_latin1_do_not_crash(self):
        r = check([Change("M", "tests/data.bin", None, None, None, binary=True),
                   Change("M", "tests/test_l.py", None, "x = 'caff\xe8'\n", "x = 'caff\xe8'\n")],
                  CFG)
        self.assertEqual(r.violations, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_testids tests.test_testguard -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `scan.py`**

```python
"""Lettura di codice senza commenti e stringhe (JS/TS e simili, Python)."""
from __future__ import annotations

import io
import tokenize


def js_tokens(text: str):
    """Token di linguaggi con la sintassi del C: ('str', valore), ('id', nome), ('p', carattere)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "'\"`":
            j, buf = i + 1, []
            while j < n and text[j] != c:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                buf.append(text[j])
                j += 1
            yield ("str", "".join(buf))
            i = j + 1
            continue
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (text[j].isalnum() or text[j] in "_$"):
                j += 1
            yield ("id", text[i:j])
            i = j
            continue
        if not c.isspace():
            yield ("p", c)
        i += 1


def js_code(text: str) -> str:
    return " ".join("S" if k == "str" else v for k, v in js_tokens(text))


def py_code(text: str) -> str | None:
    """Codice Python senza commenti né stringhe; None se il file non si legge."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            name = tokenize.tok_name[tok.type]
            if name == "ERRORTOKEN" and not tok.string.isspace():
                return None   # Python 3.11 non solleva su una stringa non chiusa
            if "STRING" in name or name in ("COMMENT", "NL", "NEWLINE", "INDENT", "DEDENT",
                                            "ENDMARKER"):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return " ".join(out)
```

- [ ] **Step 4: `testids.py`**

```python
"""Identificativi dei test per analisi statica, nella forma del JUnit di ogni strumento (7.5)."""
from __future__ import annotations

import ast
import posixpath
import re

from .scan import js_tokens

JS_EXT = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts")
_GROUPS = {"describe", "suite", "context", "xdescribe"}
_CASES = {"it", "test", "xit", "xtest"}
_SKIP_MODS = {"skip", "todo", "fixme"}
_GO_TEST = re.compile(r"^func\s+(Test\w+)\s*\(", re.MULTILINE)


def language(path: str) -> str | None:
    if path.endswith(JS_EXT):
        return "js"
    if path.endswith(".py"):
        return "py"
    if path.endswith(".go"):
        return "go"
    if path.endswith((".java", ".kt")):
        return "java"
    if path.endswith(".rs"):
        return "rust"
    return None


def _js(text: str, rel: str, joiner: str):
    toks = list(js_tokens(text))
    active: dict[str, str] = {}
    skipped: set[str] = set()
    frames: list[tuple[str, int, bool]] = []
    depth, i = 0, 0
    while i < len(toks):
        kind, val = toks[i]
        if kind == "p":
            if val == "{":
                depth += 1
            elif val == "}":
                depth -= 1
                while frames and frames[-1][1] >= depth:
                    frames.pop()
            i += 1
            continue
        if kind == "id" and (val in _GROUPS or val in _CASES):
            j, mods = i + 1, []
            while j + 1 < len(toks) and toks[j] == ("p", ".") and toks[j + 1][0] == "id":
                mods.append(toks[j + 1][1])
                j += 2
            if j + 1 < len(toks) and toks[j] == ("p", "(") and toks[j + 1][0] == "str":
                title = toks[j + 1][1]
                skip = (val.startswith("x") or any(m in _SKIP_MODS for m in mods)
                        or any(f[2] for f in frames))
                if val in _GROUPS:
                    frames.append((title, depth, skip))
                else:
                    local = joiner.join([f[0] for f in frames] + [title])
                    if skip:
                        skipped.add(local)
                    else:
                        active[local] = f"{rel}::{local}"
                i = j + 2
                continue
        i += 1
    return active, skipped


def _is_skip(decorators) -> bool:
    return any(re.search(r"skip|xfail", ast.unparse(d)) for d in decorators)


def _py(text: str, rel: str):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    module = rel[:-3].replace("/", ".")
    active: dict[str, str] = {}
    skipped: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            if _is_skip(node.decorator_list):
                skipped.add(node.name)
            else:
                active[node.name] = f"{module}::{node.name}"
        elif isinstance(node, ast.ClassDef):
            bases = {ast.unparse(b) for b in node.bases}
            if not (node.name.startswith("Test") or any(b.endswith("TestCase") for b in bases)):
                continue
            cls_skip = _is_skip(node.decorator_list)
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith("test"):
                    local = f"{node.name}::{m.name}"
                    if cls_skip or _is_skip(m.decorator_list):
                        skipped.add(local)
                    else:
                        active[local] = f"{module}.{node.name}::{m.name}"
    return active, skipped


def _go(text: str, rel: str):
    pkg = posixpath.dirname(rel) or "."
    return {name: f"{pkg}::{name}" for name in _GO_TEST.findall(text)}, set()


def test_ids(text: str, rel: str, *, js_form: str):
    lang = language(rel)
    if lang == "js":
        return _js(text, rel, " > " if js_form == "vitest" else " ")
    if lang == "py":
        return _py(text, rel)
    if lang == "go":
        return _go(text, rel)
    return {}, set()
```

- [ ] **Step 5: `testguard.py`**

```python
"""test-guard (spec 8.2): test tolti, identificativi mancanti, asserzioni, salti, CI e soglie."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import globs
from .scan import js_code, py_code
from .testids import language, test_ids

DEFAULT_TEST_GLOBS = ("**/__tests__/**", "**/test/**", "**/tests/**", "**/e2e/**",
                      "**/*_test.py", "**/test_*.py", "**/*.test.*", "**/*.spec.*",
                      "**/*_test.go", "**/src/test/**")
_ASSERTS = {
    "js": [r"\bexpect\s*\(", r"\bassert\w*\b", r"\.\s*should\b"],
    "py": [r"\bassert\w*", r"\bpytest\s*\.\s*raises\b"],
    "go": [r"\bt\s*\.\s*(?:Error|Errorf|Fatal|Fatalf)\b", r"\b(?:assert|require)\s*\.\s*\w+"],
    "java": [r"\bassert\w*"], "rust": [r"\bassert\w*"],
}
_SKIPS = {
    "js": [r"\bxit\b", r"\bxdescribe\b", r"\bxtest\b", r"\.\s*skip\b", r"\.\s*only\b",
           r"\.\s*todo\b", r"\.\s*fixme\b", r"\.\s*skipIf\b", r"\.\s*runIf\s*\(\s*false\s*\)",
           r"\.\s*fails\b"],
    "py": [r"\bpytest\s*\.\s*skip\s*\(", r"\bpytest\s*\.\s*mark\s*\.\s*skip\w*", r"\bxfail\b",
           r"\bunittest\s*\.\s*skip\w*", r"\bskipIf\b", r"\bskipUnless\b"],
    "go": [r"\bt\s*\.\s*Skip\w*"],
    "java": [r"@\s*Disabled\b", r"@\s*Ignore\b"],
    "rust": [r"#\s*\[\s*ignore\s*\]"],
}
_THRESH = re.compile(r"(?i)\b(branches|functions|lines|statements|fail[_-]under|"
                     r"cov-fail-under|minimum_coverage|threshold)\b[\"']?\s*[:=]?\s*[\"']?"
                     r"(\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class Violation:
    kind: str
    path: str
    detail: str
    waiver_type: str
    ids: tuple = ()


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None
    base_text: str | None
    head_text: str | None
    binary: bool = False


@dataclass(frozen=True)
class GuardConfig:
    test_globs: tuple | list
    fixture_globs: tuple | list
    ci_globs: tuple | list
    verification_globs: tuple | list
    verification_watch: tuple | list
    skip_markers: tuple | list = ()
    assert_markers: tuple | list = ()
    js_form: str = "vitest"


@dataclass
class GuardResult:
    violations: list[Violation] = field(default_factory=list)
    watched: list[str] = field(default_factory=list)


def _code(text: str | None, lang: str) -> str | None:
    if text is None:
        return ""
    return py_code(text) if lang == "py" else js_code(text)


def _literal(marker: str) -> str:
    rx = re.escape(marker)
    if marker[:1].isalnum() or marker[:1] == "_":
        rx = r"\b" + rx
    if marker[-1:].isalnum() or marker[-1:] == "_":
        rx += r"\b"
    return rx


def _count(code: str, patterns) -> int:
    return sum(len(re.findall(p, code)) for p in patterns)


def _thresholds(text: str | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, val in _THRESH.findall(text or ""):
        k = key.lower().replace("-", "_")
        out[k] = min(out.get(k, float("inf")), float(val))
    return out


def _test_file(c: Change, cfg: GuardConfig, out: list[Violation]) -> None:
    lang = language(c.path if c.status != "D" else (c.old_path or c.path))
    if lang is None:
        return
    old = c.old_path or c.path
    if c.status == "D":
        base = test_ids(c.base_text or "", old, js_form=cfg.js_form)
        ids = tuple(sorted(base[0].values())) if base else ()
        out.append(Violation("test_deleted", old, "file di test cancellato", "test", ids))
        return
    head = test_ids(c.head_text or "", c.path, js_form=cfg.js_form)
    if head is None:
        out.append(Violation("unparsable", c.path, "file di test non leggibile", "test"))
        return
    if c.base_text is not None and c.status != "A":
        base = test_ids(c.base_text, old, js_form=cfg.js_form)
        if base is not None:
            missing = tuple(sorted(full for local, full in base[0].items()
                                   if local not in head[0]))
            if missing:
                out.append(Violation("test_id_missing", c.path,
                                     "test della base assenti o saltati: " + ", ".join(missing),
                                     "test", missing))
    base_code, head_code = _code(c.base_text, lang), _code(c.head_text, lang)
    if base_code is None or head_code is None:
        return
    asserts = _ASSERTS[lang] + [_literal(m) for m in cfg.assert_markers]
    if c.status != "A" and _count(head_code, asserts) < _count(base_code, asserts):
        out.append(Violation("asserts_decreased", c.path, "asserzioni diminuite", "test"))
    skips = _SKIPS[lang] + [_literal(m) for m in cfg.skip_markers]
    if _count(head_code, skips) > _count(base_code, skips):
        out.append(Violation("skip_added", c.path, "marcatori di salto aggiunti", "test"))


def check(changes, cfg: GuardConfig) -> GuardResult:
    r = GuardResult()
    for c in changes:
        paths = [p for p in (c.path, c.old_path) if p]
        if c.binary:
            if c.status == "D" and globs.match_any(cfg.test_globs, paths[-1]) \
                    and language(paths[-1]):
                r.violations.append(Violation("test_deleted", paths[-1],
                                              "file di test cancellato", "test"))
        elif any(globs.match_any(cfg.test_globs, p) for p in paths):
            _test_file(c, cfg, r.violations)
        if any(globs.match_any(cfg.ci_globs, p) for p in paths):
            r.violations.append(Violation("ci_changed", c.path, "CI modificata", "ci"))
        if any(globs.match_any(cfg.fixture_globs, p) for p in paths):
            r.violations.append(Violation("fixture_changed", c.path,
                                          "snapshot o fixture aggiornati", "test"))
        verification = any(globs.match_any(cfg.verification_globs, p) for p in paths)
        watched = any(globs.match_any(cfg.verification_watch, p) for p in paths)
        if verification:
            r.violations.append(Violation("verification_changed", c.path,
                                          "configurazione di test o copertura modificata",
                                          "command"))
        if watched:
            r.watched.append(c.path)
        if (verification or watched) and not c.binary and c.base_text and c.head_text:
            base_t, head_t = _thresholds(c.base_text), _thresholds(c.head_text)
            lowered = [k for k in base_t if k in head_t and head_t[k] < base_t[k]]
            if lowered:
                r.violations.append(Violation("threshold_lowered", c.path,
                                              "soglie abbassate: " + ", ".join(sorted(lowered)),
                                              "threshold"))
    return r
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK. Se `test_pytest_mark_skip_added` fallisce perché l'ordine dei `kind` differisce, il test usa `sorted`: correggere il codice, non il test.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_analysis/scan.py bin/tollgate_analysis/testids.py bin/tollgate_analysis/testguard.py tests/test_testids.py tests/test_testguard.py
git commit -m "tollgate P2: test-guard con identificativi statici per linguaggio"
```

---

