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
