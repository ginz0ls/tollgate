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
# File di configurazione di copertura noti: le soglie vi si controllano ovunque nel repo (8.2).
COVERAGE_CONFIG_GLOBS = ("**/.nycrc", "**/.nycrc.json", "**/.nycrc.yml", "**/.coveragerc",
                         "**/jest.config.*", "**/vitest.config.*", "**/pyproject.toml",
                         "**/setup.cfg", "**/package.json")
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
           r"\bunittest\s*\.\s*skip\w*", r"\bskipIf\b", r"\bskipUnless\b",
           r"\.\s*skipTest\s*\(", r"\bSkipTest\b", r"\bpytest\s*\.\s*importorskip\s*\("],
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


def _code(text: str | None, lang: str, rel: str) -> str | None:
    """Codice senza commenti né stringhe; None se lo scanner non lo legge."""
    if text is None:
        return ""
    if lang == "py":
        return py_code(text)
    return js_code(text, jsx=rel.endswith((".jsx", ".tsx")))


def _literal(marker: str) -> str:
    rx = re.escape(marker)
    if marker[:1].isalnum() or marker[:1] == "_":
        rx = r"\b" + rx
    if marker[-1:].isalnum() or marker[-1:] == "_":
        rx += r"\b"
    return rx


def _count(code: str, patterns) -> int:
    return sum(len(re.findall(p, code)) for p in patterns)


def _strip_comments(text: str) -> str:
    """Toglie i commenti (//, /* */, #, ; a inizio riga) rispettando le stringhe, che non
    attraversano le righe."""
    out, i, n, quote, line_start = [], 0, len(text), None, True
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == quote or c == "\n":
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            line_start = False
            continue
        if text.startswith("//", i) or c == "#" or (c == ";" and line_start):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        line_start = c == "\n" or (line_start and c in " \t")
        i += 1
    return "".join(out)


def _thresholds(text: str | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, val in _THRESH.findall(_strip_comments(text or "")):
        k = key.lower().replace("-", "_")
        out[k] = min(out.get(k, float("inf")), float(val))
    return out


def _lowered(base_text: str, head_text: str | None) -> list[str]:
    """Soglie della base abbassate o rimosse nella testa (una chiave assente vale 0)."""
    base_t, head_t = _thresholds(base_text), _thresholds(head_text)
    return sorted(k for k, v in base_t.items() if k not in head_t or head_t[k] < v)


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
    base_code = _code(c.base_text, lang, old)
    head_code = _code(c.head_text, lang, c.path)
    if head_code is None:
        out.append(Violation("unparsable", c.path, "file di test non analizzabile", "test"))
    # Rete di sicurezza fail-closed: ogni conteggio vale sia sul codice ripulito sia sul testo
    # grezzo; si tiene il caso peggiore (diminuzione massima per le asserzioni, aumento
    # massimo per i salti). Un errore dello scanner non nasconde mai un indebolimento.
    asserts = _ASSERTS[lang] + [_literal(m) for m in cfg.assert_markers]
    skips = _SKIPS[lang] + [_literal(m) for m in cfg.skip_markers]
    b_raw, h_raw = c.base_text or "", c.head_text or ""
    drops = [_count(b_raw, asserts) - _count(h_raw, asserts)]
    rises = [_count(h_raw, skips) - _count(b_raw, skips)]
    if base_code is not None and head_code is not None:
        drops.append(_count(base_code, asserts) - _count(head_code, asserts))
        rises.append(_count(head_code, skips) - _count(base_code, skips))
    if max(drops) > 0:
        out.append(Violation("asserts_decreased", c.path, "asserzioni diminuite", "test"))
    if max(rises) > 0:
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
        coverage = any(globs.match_any(COVERAGE_CONFIG_GLOBS, p) for p in paths)
        if (verification or watched or coverage) and not c.binary and c.base_text is not None:
            lowered = _lowered(c.base_text, c.head_text)
            if lowered:
                r.violations.append(Violation("threshold_lowered", c.path,
                                              "soglie abbassate o rimosse: "
                                              + ", ".join(lowered), "threshold"))
    return r
