### Task 4: Analisi: pattern, file protetti, profili, `plan-check`

**Files:**
- Create: `bin/tollgate_analysis/__init__.py`
- Create: `bin/tollgate_analysis/globs.py`
- Create: `bin/tollgate_analysis/protected.py`
- Create: `bin/tollgate_analysis/profiles.py`
- Create: `bin/tollgate_analysis/plan.py`
- Modify: `bin/tollgate_core/config.py` (avviso su `profiles.active`)
- Test: `tests/test_globs.py`, `tests/test_protected.py`, `tests/test_profiles.py`, `tests/test_plan.py`, `tests/test_analysis_isolation.py`, `tests/test_config.py`

**Interfaces:**
- Produces:
  - `globs.compile(pattern) -> re.Pattern`; `globs.match(pattern, path) -> bool`; `globs.match_any(patterns, path) -> bool`; `globs.is_pattern(s) -> bool`; `globs.literal_segments(pattern) -> int`.
  - `protected.TOLLGATE_FILES`, `protected.REPO_PROTECTED`; `protected.is_tollgate_file(rel) -> bool`; `protected.is_protected(rel: str | None, abs_path: Path, *, abs_roots: list[Path]) -> bool`.
  - `profiles.vertical_for(path, profiles: dict[str, dict]) -> str | None`; `profiles.active_profiles(files, profiles, always) -> list[str]`; `profiles.task_skills(files, profiles) -> list[str]`; `profiles.min_level(names, profiles) -> str`.
  - `plan.PlanTask(number, title, files, must_haves)`, `plan.MustHave(id, text, tests)`, `plan.PlanCheck(problems, warnings, scope, tasks, must_haves)` con `.ok`; `plan.check_plan(text, *, required_sections, max_scope_files, must_have_tests, level, profiles, active_always) -> PlanCheck`; `plan.TEST_SEP = "— test:"`.

- [ ] **Step 1: Test**

`tests/test_globs.py`:

```python
import unittest

from tollgate_analysis import globs


class GlobsTest(unittest.TestCase):
    def test_gitignore_dialect(self):
        cases = [
            ("**/__tests__/**", "src/__tests__/a.test.js", True),
            ("**/test_*.py", "test_x.py", True),
            ("**/test_*.py", "a/b/test_x.py", True),
            ("web/**", "web/a/b.ts", True),
            ("web/**", "x/web/a.ts", False),
            ("*.md", "docs/a.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/x.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/plans/x.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/plans/x.py", False),
            ("/tollgate.toml", "tollgate.toml", True),
            ("/tollgate.toml", "sub/tollgate.toml", False),
            (".github/workflows/tollgate-*.yml", ".github/workflows/tollgate-verdict.yml", True),
            (".github/workflows/tollgate-*.yml", ".github/workflows/ci.yml", False),
            ("reports/", "reports/junit.xml", True),
            ("**", "qualunque/cosa.txt", True),
            ("**/*.test.*", "src/a.test.ts", True),
            ("scripts/check*", "scripts/check-all.sh", True),
            ("src/[ab].py", "src/a.py", True),
            ("src/[!ab].py", "src/a.py", False),
        ]
        for pattern, path, expected in cases:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(globs.match(pattern, path), expected)

    def test_helpers(self):
        self.assertTrue(globs.is_pattern("src/*.py"))
        self.assertFalse(globs.is_pattern("src/a.py"))
        self.assertEqual(globs.literal_segments("web/admin/**"), 2)
        self.assertEqual(globs.literal_segments("**/*.ts"), 0)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_protected.py`:

```python
import unittest
from pathlib import Path

from tollgate_analysis import protected


class ProtectedTest(unittest.TestCase):
    def test_repo_files(self):
        roots = [Path("/stato"), Path("/home/u/.claude/plugins")]
        for rel in ["tollgate.toml", ".github/workflows/tollgate-gate.yml",
                    ".github/tollgate/cli/x.py", ".tollgate/waivers/7.toml",
                    "docs/superpowers/reviews/7/r.md", ".claude/settings.json",
                    ".claude/settings.local.json"]:
            with self.subTest(rel=rel):
                self.assertTrue(protected.is_protected(rel, Path("/r") / rel, abs_roots=roots))
        self.assertFalse(protected.is_protected("src/a.py", Path("/r/src/a.py"), abs_roots=roots))
        self.assertFalse(protected.is_protected("docs/superpowers/plans/p.md",
                                                Path("/r/docs/superpowers/plans/p.md"),
                                                abs_roots=roots))

    def test_absolute_roots(self):
        roots = [Path("/stato"), Path("/r/.git/hooks")]
        self.assertTrue(protected.is_protected(None, Path("/stato/tollgate.db"), abs_roots=roots))
        self.assertTrue(protected.is_protected(None, Path("/r/.git/hooks/pre-commit"),
                                               abs_roots=roots))
        self.assertFalse(protected.is_protected(None, Path("/altro/x"), abs_roots=roots))

    def test_tollgate_file(self):
        self.assertTrue(protected.is_tollgate_file("tollgate.toml"))
        self.assertFalse(protected.is_tollgate_file(".tollgate/waivers/7.toml"))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_profiles.py`:

```python
import unittest

from tollgate_analysis import profiles

PROFILES = {
    "web": {"kind": "vertical", "paths": ["web/**"], "skills": ["ui-ux-pro-max"],
            "min_level": "L0", "plan_sections": []},
    "admin": {"kind": "vertical", "paths": ["web/admin/**"], "skills": ["a", "b"],
              "min_level": "L1", "plan_sections": []},
    "api": {"kind": "vertical", "paths": ["api/**"], "skills": ["c", "d"],
            "min_level": "L2", "plan_sections": ["Contratti"]},
    "a11y": {"kind": "cross", "paths": ["web/**"], "skills": ["x"], "min_level": "L0",
             "plan_sections": []},
}


class ProfilesTest(unittest.TestCase):
    def test_most_specific_wins(self):
        self.assertEqual(profiles.vertical_for("web/admin/x.ts", PROFILES), "admin")
        self.assertEqual(profiles.vertical_for("web/x.ts", PROFILES), "web")
        self.assertIsNone(profiles.vertical_for("lib/x.ts", PROFILES))

    def test_tie_first_declared(self):
        p = {"uno": {"kind": "vertical", "paths": ["src/**"]},
             "due": {"kind": "vertical", "paths": ["src/**"]}}
        self.assertEqual(profiles.vertical_for("src/a", p), "uno")

    def test_active_and_skills(self):
        self.assertEqual(profiles.active_profiles(["web/a.ts"], PROFILES, ["api"]),
                         ["web", "api", "a11y"])
        self.assertEqual(profiles.task_skills(["web/admin/a.ts", "api/b.py"], PROFILES),
                         ["a", "b", "c", "d"])
        self.assertEqual(profiles.min_level(["web", "admin"], PROFILES), "L1")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_plan.py`:

```python
import unittest

from tollgate_analysis import plan

SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope",
            "Punti di arresto", "Rischi"]


def make(must_have="M1. Somma corretta — test: tests.test_a::test_sum", files=None,
         extra="", drop=None):
    files = files or ["- Create: `src/a.py`", "- Test: `tests/test_a.py:10-20`"]
    out = ["# Piano", ""]
    for s in SECTIONS:
        if s == drop:
            continue
        out.append(f"## {s}")
        if s == "Must-have":
            out.append(must_have)
        out.append("")
    out += ["### Task 1: Somma", "", "**Files:**", *files, "Must-have: M1", "",
            "```markdown", "## Finta sezione in un blocco di codice", "- Create: `x/finto.py`",
            "```", extra]
    return "\n".join(out)


def check(text, level="L1", profiles=None, max_scope=30):
    return plan.check_plan(text, required_sections=SECTIONS, max_scope_files=max_scope,
                           must_have_tests=True, level=level, profiles=profiles or {},
                           active_always=[])


class PlanCheckTest(unittest.TestCase):
    def test_complete_plan(self):
        r = check(make())
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.scope, ["src/a.py", "tests/test_a.py"])
        self.assertEqual(r.must_haves[0].tests, ["tests.test_a::test_sum"])
        self.assertEqual([t.number for t in r.tasks], [1])

    def test_missing_section(self):
        r = check(make(drop="Rischi"))
        self.assertFalse(r.ok)
        self.assertIn("## Rischi", " ".join(r.problems))

    def test_pattern_or_dir_rejected(self):
        for bad in ["- Modify: `src/*.py`", "- Create: `src/nuova/`"]:
            with self.subTest(bad=bad):
                self.assertFalse(check(make(files=[bad])).ok)

    def test_must_have_without_test(self):
        self.assertFalse(check(make(must_have="M1. Somma corretta")).ok)
        self.assertTrue(check(make(must_have="M1. Somma corretta"), level="L0").ok)

    def test_manual_test_allowed(self):
        self.assertTrue(check(make(must_have="M1. Colore giusto — test: manuale")).ok)

    def test_too_many_files(self):
        files = [f"- Create: `src/f{i}.py`" for i in range(4)]
        self.assertFalse(check(make(files=files), max_scope=3).ok)

    def test_unknown_must_have_reference(self):
        text = make().replace("Must-have: M1", "Must-have: M1, M9")
        self.assertFalse(check(text).ok)

    def test_more_than_three_skills_is_warning(self):
        prof = {"api": {"kind": "vertical", "paths": ["src/**"], "skills": ["a", "b", "c", "d"],
                        "plan_sections": []}}
        r = check(make(), profiles=prof)
        self.assertTrue(r.ok)
        self.assertTrue(any("4 skill" in w for w in r.warnings))

    def test_profile_sections_required(self):
        prof = {"api": {"kind": "vertical", "paths": ["src/**"], "skills": [],
                        "plan_sections": ["Contratti"]}}
        self.assertFalse(check(make(), profiles=prof).ok)

    def test_no_tasks(self):
        self.assertFalse(check("\n".join(f"## {s}" for s in SECTIONS)).ok)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_analysis_isolation.py`:

```python
import ast
import unittest

from tests.helpers import BIN

FORBIDDEN = ("tollgate_core", "tollgate_hooks", "tollgate_checks")


class IsolationTest(unittest.TestCase):
    def test_analysis_imports_only_stdlib_and_itself(self):
        for path in sorted((BIN / "tollgate_analysis").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for n in names:
                    with self.subTest(file=path.name, module=n):
                        self.assertFalse(n.split(".")[0] in FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
```

In `tests/test_config.py` aggiungere un test (usare il testo minimo che il file già usa negli altri test, con `[gate] mode = "protected"`):

```python
    def test_active_profile_not_declared_warns(self):
        cfg = config.load_config_text(
            'schema_version = 1\n[gate]\nmode = "protected"\n'
            '[profiles]\nactive = ["web"]\n')
        self.assertIn("profilo attivo non dichiarato: web", cfg.warnings)
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_globs tests.test_protected tests.test_profiles tests.test_plan tests.test_analysis_isolation tests.test_config -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_analysis'` e il test di config che non trova l'avviso.

- [ ] **Step 3: `__init__.py` e `globs.py`**

`bin/tollgate_analysis/__init__.py`:

```python
"""Analisi pure di tollgate: niente DB, niente rete, niente tollgate_core (usate anche dal gate)."""
```

`bin/tollgate_analysis/globs.py`:

```python
"""Pattern nel dialetto di .gitignore (spec 3.2), su percorsi relativi alla radice del repo."""
from __future__ import annotations

import re
from functools import lru_cache

_GLOB_CHARS = set("*?[")


def is_pattern(s: str) -> bool:
    return any(c in _GLOB_CHARS for c in s)


def literal_segments(pattern: str) -> int:
    return sum(1 for seg in pattern.strip("/").split("/") if seg and not is_pattern(seg))


@lru_cache(maxsize=1024)
def compile(pattern: str) -> re.Pattern:  # noqa: A001 - nome voluto, come re.compile
    p = pattern
    dir_only = p.endswith("/")
    p = p.rstrip("/")
    anchored = p.startswith("/") or "/" in p
    p = p.lstrip("/")
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif p.startswith("/**", i) and i + 3 == len(p):
            out.append("/.*")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "[":
            j = p.find("]", i + 1)
            if j == -1:
                out.append(re.escape("["))
                i += 1
            else:
                body = p[i + 1:j]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append("[" + body.replace("\\", "\\\\") + "]")
                i = j + 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    prefix = "" if anchored else "(?:.*/)?"
    suffix = "/.*" if dir_only else "(?:/.*)?"
    return re.compile("^" + prefix + "".join(out) + suffix + "$")


def match(pattern: str, path: str) -> bool:
    return compile(pattern).match(path[2:] if path.startswith("./") else path) is not None


def match_any(patterns, path: str) -> bool:
    return any(match(p, path) for p in patterns)
```

- [ ] **Step 4: `protected.py`**

```python
"""File di tollgate e file protetti (spec 0, 7.4)."""
from __future__ import annotations

from pathlib import Path

from . import globs

TOLLGATE_FILES = ["/tollgate.toml", ".github/workflows/tollgate-*.yml",
                  ".github/actions/tollgate-*/**", ".github/tollgate/**"]
REPO_PROTECTED = TOLLGATE_FILES + [
    ".tollgate/waivers/**", "docs/superpowers/reviews/**",
    ".claude/settings.json", ".claude/settings.local.json",
    ".git/hooks/**", ".git/config",
]


def is_tollgate_file(rel: str) -> bool:
    return globs.match_any(TOLLGATE_FILES, rel)


def is_protected(rel: str | None, abs_path: Path, *, abs_roots: list[Path]) -> bool:
    """`rel` è il percorso nel repo (None fuori da un repo); `abs_roots` sono cartelle o file
    protetti per percorso assoluto: cartella di stato, plugin installati, impostazioni utente,
    `.git/hooks` e `.git/config` della cartella comune di git."""
    if rel is not None and globs.match_any(REPO_PROTECTED, rel):
        return True
    p = Path(abs_path)
    return any(p == r or r in p.parents for r in abs_roots)
```

- [ ] **Step 5: `profiles.py`**

```python
"""Profili: verticale di un file, profili attivi, skill di un task (spec 6.3, 9.2, 11.4)."""
from __future__ import annotations

from . import globs

_LEVELS = ("L0", "L1", "L2")


def _score(path: str, patterns) -> int | None:
    scores = [globs.literal_segments(p) for p in patterns if globs.match(p, path)]
    return max(scores) if scores else None


def vertical_for(path: str, profiles: dict[str, dict]) -> str | None:
    """Vince il pattern con più segmenti letterali; a parità il primo dichiarato."""
    best, best_score = None, -1
    for name, prof in profiles.items():
        if prof.get("kind", "vertical") != "vertical":
            continue
        s = _score(path, prof.get("paths", []))
        if s is not None and s > best_score:
            best, best_score = name, s
    return best


def active_profiles(files, profiles: dict[str, dict], always) -> list[str]:
    files = list(files)
    return [name for name, prof in profiles.items()
            if name in always or any(globs.match_any(prof.get("paths", []), f) for f in files)]


def task_skills(files, profiles: dict[str, dict]) -> list[str]:
    skills: list[str] = []
    for f in files:
        name = vertical_for(f, profiles)
        if name:
            for s in profiles[name].get("skills", []):
                if s not in skills:
                    skills.append(s)
    return skills


def min_level(names, profiles: dict[str, dict]) -> str:
    level = "L0"
    for n in names:
        lv = profiles.get(n, {}).get("min_level", "L0")
        if lv in _LEVELS and _LEVELS.index(lv) > _LEVELS.index(level):
            level = lv
    return level
```

- [ ] **Step 6: `plan.py`**

```python
"""plan-check (spec 7.5): intestazioni, scope dai task, must-have legati ai test."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import globs, profiles as prof

TEST_SEP = "— test:"
SKILL_CAP = 3
_SECTION = re.compile(r"^## (.+?)\s*$")
_TASK = re.compile(r"^### Task (\d+)\b[:.]?\s*(.*)$")
_FILE = re.compile(r"^\s*[-*]\s*(Create|Modify|Test):\s*(.+?)\s*$")
_TASK_MH = re.compile(r"^\s*\**Must-have\**:\**\s*(.+?)\s*$")
_MH = re.compile(r"^\s*(?:[-*]\s*)?(M\d+)\.\s*(.+?)\s*$")
_RANGE = re.compile(r":\d+(?:-\d+)?$")
_TICK = re.compile(r"`([^`]+)`")


@dataclass
class PlanTask:
    number: int
    title: str
    files: list[str] = field(default_factory=list)
    must_haves: list[str] | None = None


@dataclass
class MustHave:
    id: str
    text: str
    tests: list[str]


@dataclass
class PlanCheck:
    problems: list[str]
    warnings: list[str]
    scope: list[str]
    tasks: list[PlanTask]
    must_haves: list[MustHave]

    @property
    def ok(self) -> bool:
        return not self.problems


def _file_value(raw: str) -> str:
    m = _TICK.search(raw)
    value = (m.group(1) if m else raw.split()[0]).strip()
    value = _RANGE.sub("", value)
    return value[2:] if value.startswith("./") else value


def _parse(text: str):
    sections: list[str] = []
    tasks: list[PlanTask] = []
    mh_lines: list[str] = []
    current_section, task = None, None
    fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = _SECTION.match(line)
        if m:
            current_section, task = m.group(1), None
            sections.append(current_section)
            continue
        m = _TASK.match(line)
        if m:
            task = PlanTask(int(m.group(1)), m.group(2).strip())
            tasks.append(task)
            continue
        if line.startswith("### "):
            task = None
            continue
        if task is not None:
            fm = _FILE.match(line)
            if fm:
                task.files.append(_file_value(fm.group(2)))
                continue
            mm = _TASK_MH.match(line)
            if mm:
                task.must_haves = [x.strip() for x in mm.group(1).split(",") if x.strip()]
                continue
        if current_section == "Must-have" and task is None:
            mh_lines.append(line)
    return sections, tasks, mh_lines


def _must_haves(lines: list[str]) -> list[MustHave]:
    out = []
    for line in lines:
        m = _MH.match(line)
        if not m:
            continue
        body = m.group(2)
        if TEST_SEP in body:
            text, tests = body.split(TEST_SEP, 1)
            ids = [t.strip().strip("`") for t in tests.split(",") if t.strip()]
        else:
            text, ids = body, []
        out.append(MustHave(m.group(1), text.strip(), ids))
    return out


def check_plan(text: str, *, required_sections, max_scope_files: int, must_have_tests: bool,
               level: str, profiles: dict[str, dict], active_always) -> PlanCheck:
    problems: list[str] = []
    warnings: list[str] = []
    sections, tasks, mh_lines = _parse(text)
    scope = list(dict.fromkeys(f for t in tasks for f in t.files))
    active = prof.active_profiles(scope, profiles, active_always)
    needed = list(required_sections) + [s for n in active
                                         for s in profiles[n].get("plan_sections", [])]
    for s in dict.fromkeys(needed):
        if s not in sections:
            problems.append(f"manca la sezione «## {s}»")
    if not tasks:
        problems.append("nessun task (intestazioni «### Task N»)")
    for f in scope:
        if globs.is_pattern(f) or f.endswith("/"):
            problems.append(f"pattern o cartella non ammessi nello scope: {f}")
    if len(scope) > max_scope_files:
        problems.append(f"scope di {len(scope)} file, oltre il massimo di {max_scope_files}")
    must_haves = _must_haves(mh_lines)
    if must_have_tests and level in ("L1", "L2"):
        if not must_haves:
            problems.append("nessun must-have nella sezione «## Must-have»")
        for mh in must_haves:
            if not mh.tests:
                problems.append(f"{mh.id} senza test: scrivi «{TEST_SEP} <classname::name>» "
                                f"oppure «{TEST_SEP} manuale»")
    known = {mh.id for mh in must_haves}
    for t in tasks:
        for ref in t.must_haves or []:
            if ref not in known:
                problems.append(f"task {t.number}: must-have {ref} inesistente")
        skills = prof.task_skills(t.files, profiles)
        if len(skills) > SKILL_CAP:
            warnings.append(f"task {t.number}: {len(skills)} skill dai profili (massimo "
                            f"{SKILL_CAP}): {', '.join(skills)}; il task va diviso")
    return PlanCheck(problems, warnings, scope, tasks, must_haves)
```

- [ ] **Step 7: Avviso su `profiles.active`**

In `bin/tollgate_core/config.py`, in `load_config_text`, subito prima di `if not data["gate"]["mode"]:`:

```python
    declared = {k for k in data["profiles"] if k != "active"}
    for name in data["profiles"]["active"]:
        if name not in declared:
            warnings.append(f"profilo attivo non dichiarato: {name}")
```

- [ ] **Step 8: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 9: Commit**

```bash
git add bin/tollgate_analysis tests/test_globs.py tests/test_protected.py tests/test_profiles.py tests/test_plan.py tests/test_analysis_isolation.py bin/tollgate_core/config.py tests/test_config.py
git commit -m "tollgate P2: analisi di pattern, file protetti, profili e plan-check"
```

---
