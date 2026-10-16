### Task 8: Analisi: deroghe e report dell'implementatore

**Files:**
- Create: `bin/tollgate_analysis/waivers.py`
- Create: `bin/tollgate_analysis/report.py`
- Test: `tests/test_waivers.py`, `tests/test_report.py`

**Interfaces:**
- Consumes: `globs.match`, `testguard.Violation`.
- Produces:
  - `waivers.TYPES`; `waivers.Waiver(id, type, file, pattern, tests, choice, why, cost, declared_by)`; `waivers.WaiverFile(issue, branch, waivers, schema_version=1)`; `waivers.parse(text) -> WaiverFile` (`ValueError` se non valido); `waivers.dumps(wf) -> str`; `waivers.next_id(wf) -> str`; `waivers.status(wf, *, approved_ids, sensitive) -> dict[str, str]` (`valid` | `pending`); `waivers.covers(w, v) -> bool`; `waivers.unresolved(violations, wf) -> list[Violation]`; `waivers.path_for(issue) -> str` (`.tollgate/waivers/<N>.toml`).
  - `report.STATUSES`, `report.REQUIRED`; `report.ImplReport(status, data, missing, unknown_status)` con `.valid`; `report.parse_report(text) -> ImplReport`; `report.is_turn_cut(tool_response) -> bool`; `report.transcript_tokens(path) -> int`.

- [ ] **Step 1: Test**

`tests/test_waivers.py`:

```python
import unittest

from tollgate_analysis import waivers
from tollgate_analysis.testguard import Violation


def wf(*items):
    return waivers.WaiverFile(issue=7, branch="tg/7-x", waivers=list(items))


def w(n, type_, file=None, pattern=None, tests=()):
    return waivers.Waiver(f"w-7-{n}", type_, file, pattern, list(tests), "scelta", "perché",
                          "costo", "agent")


class WaiversTest(unittest.TestCase):
    def test_roundtrip_with_tricky_text(self):
        f = wf(waivers.Waiver("w-7-1", "scope", "src/a.py", None, [], 'virgolette " e \\',
                              "```\n@utente", "c", "agent"))
        back = waivers.parse(waivers.dumps(f))
        self.assertEqual(back, f)

    def test_parse_rejects_bad(self):
        with self.assertRaises(ValueError):
            waivers.parse('schema_version = 1\nissue = 7\nbranch = "b"\n[[waiver]]\nid = "x"\n'
                          'type = "boh"\nfile = "a"\nchoice = ""\nwhy = ""\ncost = ""\n')

    def test_next_id(self):
        self.assertEqual(waivers.next_id(wf()), "w-7-1")
        self.assertEqual(waivers.next_id(wf(w(1, "scope", "a"), w(4, "scope", "b"))), "w-7-5")

    def test_status_rules(self):
        f = wf(w(1, "scope", "a"), w(2, "scope", "b"), w(3, "scope", "c"),
               w(4, "test", "t", tests=["x"]), w(5, "command", "cfg"),
               w(6, "scope", pattern="src/**"), w(7, "scope", "auth/x"))
        st = waivers.status(f, approved_ids={"w-7-4"}, sensitive=lambda p: p.startswith("auth/"))
        self.assertEqual(st, {"w-7-1": "valid", "w-7-2": "valid", "w-7-3": "pending",
                              "w-7-4": "valid", "w-7-5": "valid", "w-7-6": "pending",
                              "w-7-7": "pending"})

    def test_covers(self):
        v_scope = Violation("out_of_scope", "src/x.py", "", "scope")
        v_ids = Violation("test_id_missing", "t.py", "", "test", ("t::a", "t::b"))
        self.assertTrue(waivers.covers(w(1, "scope", "src/x.py"), v_scope))
        self.assertTrue(waivers.covers(w(1, "scope", pattern="src/**"), v_scope))
        self.assertFalse(waivers.covers(w(1, "test", "src/x.py"), v_scope))
        self.assertFalse(waivers.covers(w(1, "test", "t.py", tests=["t::a"]), v_ids))
        self.assertTrue(waivers.covers(w(1, "test", "t.py", tests=["t::a", "t::b"]), v_ids))
        self.assertEqual(waivers.unresolved([v_scope, v_ids], wf(w(1, "scope", "src/x.py"))),
                         [v_ids])
        self.assertEqual(waivers.unresolved([v_scope], None), [v_scope])


if __name__ == "__main__":
    unittest.main()
```

`tests/test_report.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import report

GOOD = {"v": 1, "task": 2, "status": "DONE", "done": "fatto", "tests": "verify green",
        "files": ["src/a.py"], "must_have": ["M1"], "concerns": "", "left": "",
        "size_reason": None}
SAMPLES = json.loads((ROOT / "spikes/fixtures/hook-inputs/samples.json").read_text())


class ReportTest(unittest.TestCase):
    def test_last_json_block(self):
        text = "Ecco il lavoro.\n```json\n" + json.dumps(GOOD) + "\n```\n"
        r = report.parse_report(text)
        self.assertTrue(r.valid)
        self.assertEqual(r.status, "DONE")
        r = report.parse_report("prima {\"a\": 1} poi " + json.dumps(GOOD))
        self.assertTrue(r.valid)

    def test_missing_fields(self):
        bad = dict(GOOD)
        del bad["left"], bad["concerns"]
        r = report.parse_report(json.dumps(bad))
        self.assertFalse(r.valid)
        self.assertEqual(r.missing, ["concerns", "left"])
        self.assertFalse(report.parse_report("nessun json").valid)
        self.assertFalse(report.parse_report(None).valid)

    def test_unknown_status_counts_as_done(self):
        r = report.parse_report(json.dumps(dict(GOOD, status="FINITO")))
        self.assertEqual((r.status, r.unknown_status, r.valid), ("DONE", True, True))

    def test_turn_cut_from_real_sample(self):
        cut = SAMPLES["PostToolUse-Agent-maxturns-cut"]["tool_response"]
        normal = SAMPLES["PostToolUse-Agent-foreground-manual"]["tool_response"]
        self.assertTrue(report.is_turn_cut(cut))
        self.assertFalse(report.is_turn_cut(normal))
        fake = dict(normal, content=[{"type": "text",
                                      "text": "NOTE: this agent stopped at its 2-turn limit"}])
        self.assertFalse(report.is_turn_cut(fake))

    def test_transcript_tokens(self):
        lines = [
            {"type": "assistant", "message": {"id": "m1", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 1000, "output_tokens": 3}}},
            {"type": "assistant", "message": {"id": "m1", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 1000, "output_tokens": 3}}},
            {"type": "user", "message": {"content": "x"}},
            "riga non json",
            {"type": "assistant", "message": {"id": "m2", "usage": {"input_tokens": 1,
                                                                     "output_tokens": 1}}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for l in lines:
                f.write((l if isinstance(l, str) else json.dumps(l)) + "\n")
        try:
            self.assertEqual(report.transcript_tokens(f.name), 20)
        finally:
            Path(f.name).unlink()
        self.assertEqual(report.transcript_tokens("/non/esiste.jsonl"), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_waivers tests.test_report -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `waivers.py`**

```python
"""Deroghe in .tollgate/waivers/<N>.toml (spec 8.3, 18.2)."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from typing import Callable

from . import globs

TYPES = ("scope", "test", "ci", "threshold", "command")
_ID = re.compile(r"^w-(\d+)-(\d+)$")
IMMEDIATE_SCOPE = 2


@dataclass
class Waiver:
    id: str
    type: str
    file: str | None
    pattern: str | None
    tests: list[str]
    choice: str
    why: str
    cost: str
    declared_by: str = "agent"


@dataclass
class WaiverFile:
    issue: int
    branch: str
    waivers: list[Waiver] = field(default_factory=list)
    schema_version: int = 1


def path_for(issue: int) -> str:
    return f".tollgate/waivers/{issue}.toml"


def _str(d: dict, k: str, required=True) -> str | None:
    v = d.get(k)
    if v is None and not required:
        return None
    if not isinstance(v, str):
        raise ValueError(f"campo {k} mancante o non stringa")
    return v


def parse(text: str) -> WaiverFile:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"TOML non valido: {e}") from e
    if raw.get("schema_version") != 1:
        raise ValueError("schema_version mancante o non supportata")
    issue, branch = raw.get("issue"), raw.get("branch")
    if not isinstance(issue, int) or isinstance(issue, bool) or not isinstance(branch, str):
        raise ValueError("issue o branch non validi")
    out = []
    for item in raw.get("waiver", []):
        if not isinstance(item, dict):
            raise ValueError("[[waiver]] non è una tabella")
        wid, type_ = _str(item, "id"), _str(item, "type")
        if not _ID.match(wid) or type_ not in TYPES:
            raise ValueError(f"deroga non valida: {wid} {type_}")
        file, pattern = _str(item, "file", False), _str(item, "pattern", False)
        if (file is None) == (pattern is None):
            raise ValueError(f"{wid}: serve file oppure pattern")
        tests = item.get("tests", [])
        if not isinstance(tests, list) or not all(isinstance(t, str) for t in tests):
            raise ValueError(f"{wid}: tests deve essere una lista di stringhe")
        out.append(Waiver(wid, type_, file, pattern, tests, _str(item, "choice"),
                          _str(item, "why"), _str(item, "cost"),
                          _str(item, "declared_by", False) or "agent"))
    return WaiverFile(issue, branch, out, 1)


def _q(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def dumps(wf: WaiverFile) -> str:
    lines = [f"schema_version = {wf.schema_version}", f"issue = {wf.issue}",
             f"branch = {_q(wf.branch)}"]
    for w in wf.waivers:
        lines += ["", "[[waiver]]", f"id = {_q(w.id)}", f"type = {_q(w.type)}"]
        lines.append(f"file = {_q(w.file)}" if w.file is not None
                     else f"pattern = {_q(w.pattern)}")
        lines.append("tests = [" + ", ".join(_q(t) for t in w.tests) + "]")
        for k in ("choice", "why", "cost", "declared_by"):
            lines.append(f"{k} = {_q(getattr(w, k))}")
    return "\n".join(lines) + "\n"


def next_id(wf: WaiverFile) -> str:
    nums = [int(m.group(2)) for w in wf.waivers if (m := _ID.match(w.id))]
    return f"w-{wf.issue}-{max(nums, default=0) + 1}"


def status(wf: WaiverFile, *, approved_ids, sensitive: Callable[[str], bool]) -> dict[str, str]:
    """Le prime 2 deroghe scope su file non sensibili valgono subito; command vale subito;
    il resto (test, ci, threshold, pattern, scope oltre la seconda) aspetta approve waiver."""
    out: dict[str, str] = {}
    scope_seen = 0
    for w in wf.waivers:
        immediate = False
        if w.type == "scope" and w.pattern is None and not sensitive(w.file):
            scope_seen += 1
            immediate = scope_seen <= IMMEDIATE_SCOPE
        elif w.type == "command" and w.pattern is None:
            immediate = True
        out[w.id] = "valid" if (immediate or w.id in approved_ids) else "pending"
    return out


def covers(w: Waiver, v) -> bool:
    if w.type != v.waiver_type:
        return False
    ok = globs.match(w.pattern, v.path) if w.pattern is not None else w.file == v.path
    if not ok:
        return False
    if v.kind == "test_id_missing":
        return set(v.ids) <= set(w.tests)
    return True


def unresolved(violations, wf: WaiverFile | None) -> list:
    if wf is None:
        return list(violations)
    return [v for v in violations if not any(covers(w, v) for w in wf.waivers)]
```

- [ ] **Step 4: `report.py`**

```python
"""Report dell'implementatore (spec 18.5), taglio di maxTurns (6.3), token dal transcript."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

STATUSES = ("DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT")
REQUIRED = ("v", "task", "status", "done", "tests", "files", "concerns", "left")
CUT_PREFIX = "NOTE: this agent stopped at its"


@dataclass
class ImplReport:
    status: str
    data: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    unknown_status: bool = False

    @property
    def valid(self) -> bool:
        return not self.missing


def _last_json(text: str) -> dict | None:
    dec = json.JSONDecoder()
    pos = text.rfind("{")
    while pos >= 0:
        try:
            obj, _ = dec.raw_decode(text, pos)
            if isinstance(obj, dict) and "status" in obj:
                return obj
        except json.JSONDecodeError:
            pass
        pos = text.rfind("{", 0, pos)
    return None


def parse_report(text: str | None) -> ImplReport:
    data = _last_json(text or "")
    if data is None:
        return ImplReport("DONE", {}, list(REQUIRED))
    missing = [k for k in REQUIRED if k not in data]
    status = data.get("status")
    unknown = status not in STATUSES
    return ImplReport("DONE" if unknown else status, data, missing, unknown)


def is_turn_cut(tool_response: dict | None) -> bool:
    """Il blocco lo scrive Claude Code, separato dall'output del subagente (P0, E6)."""
    if not isinstance(tool_response, dict):
        return False
    if not isinstance(tool_response.get("harnessNoteCount"), int) \
            or tool_response["harnessNoteCount"] < 1:
        return False
    content = tool_response.get("content")
    if not isinstance(content, list) or not content or not isinstance(content[0], dict):
        return False
    return str(content[0].get("text", "")).startswith(CUT_PREFIX)


def transcript_tokens(path) -> int:
    """Token nuovi del subagente: input + cache_creation + output, una volta per messaggio
    (decisione 20). cache_read resta fuori perché riconta il contesto a ogni turno."""
    seen: dict[str, int] = {}
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return 0
    with fh:
        for n, line in enumerate(fh):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = row.get("message") if isinstance(row, dict) else None
            usage = msg.get("usage") if isinstance(msg, dict) else None
            if not isinstance(usage, dict):
                continue
            total = sum(int(usage.get(k) or 0) for k in
                        ("input_tokens", "cache_creation_input_tokens", "output_tokens"))
            seen[str(msg.get("id") or f"riga-{n}")] = total
    return sum(seen.values())
```

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK. Nota: se `PostToolUse-Agent-maxturns-cut` in `samples.json` non ha `content[0].text` che comincia con `NOTE: this agent stopped at its`, fermarsi e leggere il campione: il test usa l'input reale e prevale sul codice.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_analysis/waivers.py bin/tollgate_analysis/report.py tests/test_waivers.py tests/test_report.py
git commit -m "tollgate P2: deroghe e report dell'implementatore"
```

---
