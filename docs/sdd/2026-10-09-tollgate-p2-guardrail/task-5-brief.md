### Task 5: Analisi: livello e JUnit

**Files:**
- Create: `bin/tollgate_analysis/level.py`
- Create: `bin/tollgate_analysis/junit.py`
- Test: `tests/test_level.py`, `tests/test_junit.py`

**Interfaces:**
- Consumes: `globs.match_any`.
- Produces:
  - `level.LEVELS`; `level.FileChange(path, added, removed, binary=False, status="M", old_path=None)` (le funzioni accettano qualunque oggetto con gli attributi `path`, `added`, `removed`, `binary`, come `git.Change` del Task 9); `level.max_level(*levels) -> str`; `level.sensitive_in(paths, sensitive_paths) -> list[str]`; `level.diff_level(changes, *, diff_bytes, sensitive_paths, l0_max_files, l0_max_lines, l0_max_bytes) -> str`; `level.labels_level(labels, sensitive_labels) -> str`; `level.next_level(*, current, computed, cap, cap_paths, sensitive_now) -> str`.
  - `junit.JunitError`; `junit.Junit(total, skipped, failed, ids_run, ids_skipped, ids_failed)`; `junit.parse_junit(data: bytes) -> Junit`.

- [ ] **Step 1: Test**

`tests/test_level.py`:

```python
import unittest

from tollgate_analysis.level import FileChange, diff_level, labels_level, max_level, next_level

KW = dict(sensitive_paths=["**/migrations/**", "**/auth/**"], l0_max_files=2,
          l0_max_lines=50, l0_max_bytes=4000)


class LevelTest(unittest.TestCase):
    def test_small_diff_is_l0(self):
        ch = [FileChange("src/a.py", 10, 2)]
        self.assertEqual(diff_level(ch, diff_bytes=500, **KW), "L0")
        self.assertEqual(diff_level([], diff_bytes=0, **KW), "L0")

    def test_thresholds(self):
        self.assertEqual(diff_level([FileChange(f"f{i}", 1, 0) for i in range(3)],
                                    diff_bytes=10, **KW), "L1")
        self.assertEqual(diff_level([FileChange("a", 40, 11)], diff_bytes=10, **KW), "L1")
        self.assertEqual(diff_level([FileChange("a", 1, 0)], diff_bytes=4001, **KW), "L1")

    def test_binary_is_not_l0(self):
        self.assertEqual(diff_level([FileChange("img.png", 0, 0, binary=True)],
                                    diff_bytes=10, **KW), "L1")

    def test_sensitive_is_l2(self):
        self.assertEqual(diff_level([FileChange("db/migrations/1.sql", 1, 0)],
                                    diff_bytes=10, **KW), "L2")

    def test_labels_and_max(self):
        self.assertEqual(labels_level(["bug", "security"], ["security"]), "L2")
        self.assertEqual(labels_level(["bug"], ["security"]), "L0")
        self.assertEqual(max_level("L0", "L2", "L1"), "L2")

    def test_cap_holds_until_new_sensitive_path(self):
        self.assertEqual(next_level(current="L1", computed="L2", cap="L1",
                                    cap_paths=["src/auth/a.py"], sensitive_now=["src/auth/a.py"]),
                         "L1")
        self.assertEqual(next_level(current="L1", computed="L2", cap="L1",
                                    cap_paths=["src/auth/a.py"],
                                    sensitive_now=["src/auth/a.py", "src/auth/b.py"]), "L2")
        self.assertEqual(next_level(current="L2", computed="L0", cap=None, cap_paths=[],
                                    sensitive_now=[]), "L2")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_junit.py`:

```python
import unittest

from tollgate_analysis.junit import JunitError, parse_junit

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites><testsuite name="s">
  <testcase classname="src/a.test.ts" name="g &gt; passes"/>
  <testcase classname="src/a.test.ts" name="g &gt; skipped"><skipped/></testcase>
  <testcase classname="tests.test_x" name="test_fail"><failure message="x"/></testcase>
  <testcase classname="tests.test_x" name="test_err"><error message="y"/></testcase>
</testsuite></testsuites>"""


class JunitTest(unittest.TestCase):
    def test_counts_and_ids(self):
        j = parse_junit(XML)
        self.assertEqual((j.total, j.skipped, j.failed), (4, 1, 2))
        self.assertEqual(j.ids_run, ["src/a.test.ts::g > passes", "tests.test_x::test_fail",
                                     "tests.test_x::test_err"])
        self.assertEqual(j.ids_skipped, ["src/a.test.ts::g > skipped"])
        self.assertEqual(j.ids_failed, ["tests.test_x::test_fail", "tests.test_x::test_err"])

    def test_entities_rejected(self):
        bad = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><testsuite/>'
        with self.assertRaises(JunitError):
            parse_junit(bad)

    def test_malformed(self):
        with self.assertRaises(JunitError):
            parse_junit(b"<testsuite><testcase")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_level tests.test_junit -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `level.py`**

```python
"""Livello del lavoro (spec 5): il massimo tra diff, etichette e scelta dell'utente."""
from __future__ import annotations

from dataclasses import dataclass

from . import globs

LEVELS = ("L0", "L1", "L2")


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    removed: int
    binary: bool = False
    status: str = "M"
    old_path: str | None = None


def max_level(*levels: str) -> str:
    return max(levels, key=LEVELS.index) if levels else "L0"


def sensitive_in(paths, sensitive_paths) -> list[str]:
    return sorted({p for p in paths if globs.match_any(sensitive_paths, p)})


def diff_level(changes, *, diff_bytes: int, sensitive_paths, l0_max_files: int,
               l0_max_lines: int, l0_max_bytes: int) -> str:
    changes = list(changes)
    paths = [c.path for c in changes] + [c.old_path for c in changes if c.old_path]
    if sensitive_in(paths, sensitive_paths):
        return "L2"
    lines = sum(c.added + c.removed for c in changes)
    if (len(changes) > l0_max_files or lines > l0_max_lines or diff_bytes > l0_max_bytes
            or any(c.binary for c in changes)):
        return "L1"
    return "L0"


def labels_level(labels, sensitive_labels) -> str:
    return "L2" if set(labels) & set(sensitive_labels) else "L0"


def next_level(*, current: str, computed: str, cap: str | None, cap_paths,
               sensitive_now) -> str:
    """Lo script alza soltanto; il tetto vale finché non compare un percorso sensibile nuovo."""
    if cap and set(sensitive_now) <= set(cap_paths):
        computed = min(computed, cap, key=LEVELS.index)
    return max_level(current, computed)
```

- [ ] **Step 4: `junit.py`**

```python
"""Lettura del report JUnit (spec 7.5, 8.1): identificativi classname::name, niente entità."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_DANGER = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


class JunitError(ValueError):
    pass


@dataclass
class Junit:
    total: int = 0
    skipped: int = 0
    failed: int = 0
    ids_run: list[str] = field(default_factory=list)
    ids_skipped: list[str] = field(default_factory=list)
    ids_failed: list[str] = field(default_factory=list)


def parse_junit(data: bytes) -> Junit:
    if _DANGER.search(data):
        raise JunitError("XML con DOCTYPE o entità: report rifiutato")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise JunitError(f"XML non valido: {e}") from e
    j = Junit()
    for case in root.iter("testcase"):
        tid = f"{case.get('classname', '')}::{case.get('name', '')}"
        j.total += 1
        if case.find("skipped") is not None:
            j.skipped += 1
            j.ids_skipped.append(tid)
            continue
        j.ids_run.append(tid)
        if case.find("failure") is not None or case.find("error") is not None:
            j.failed += 1
            j.ids_failed.append(tid)
    return j
```

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_analysis/level.py bin/tollgate_analysis/junit.py tests/test_level.py tests/test_junit.py
git commit -m "tollgate P2: analisi del livello e lettura sicura del JUnit"
```

---

