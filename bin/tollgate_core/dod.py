"""Definition of Done per livello (spec 8.7): ogni voce viene da un dato, mai da un giudizio."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping

from .phases import get_work

EXTERNAL_KEYS = ("guard_scope", "must_have", "approvals", "specialists")
ITEMS_BY_LEVEL = {
    "L0": ("receipt", "guard_scope"),
    "L1": ("receipt", "guard_scope", "tasks_approved", "findings", "must_have", "skills"),
    "L2": ("receipt", "guard_scope", "tasks_approved", "findings", "must_have", "skills",
           "approvals", "specialists"),
}
LABELS = {
    "receipt": "Ricevuta green sullo SHA",
    "guard_scope": "test-guard e scope senza violazioni non derogate",
    "tasks_approved": "Ogni task done con verdetto approved",
    "findings": "Nessun rilievo blocker o major confermato senza approve finding",
    "must_have": "Ogni must-have ha i suoi test eseguiti e verdi",
    "skills": "Skill dei profili usate",
    "approvals": "Spec e piano approvati, report avversariali presenti",
    "specialists": "Specialisti finali passati",
}


@dataclass(frozen=True)
class DodItem:
    key: str
    label: str
    ok: bool | None
    detail: str = ""


def _receipt(conn, work: int, head_sha: str, allow_no_tests: bool) -> tuple[bool, str]:
    rows = conn.execute(
        "SELECT r.command, r.state FROM receipts r WHERE r.work = ? AND r.sha = ? AND r.id = "
        "(SELECT max(id) FROM receipts x WHERE x.work = r.work AND x.sha = r.sha "
        "AND x.command = r.command) ORDER BY r.command", (work, head_sha)).fetchall()
    if not rows:
        return False, f"nessuna ricevuta su {head_sha}"
    bad = [f"{r['command']}={r['state']}" for r in rows
           if not (r["state"] == "green" or (r["state"] == "empty" and allow_no_tests))]
    return (not bad), ", ".join(bad)


def _tasks(conn, work: int) -> tuple[bool, str]:
    rows = conn.execute("SELECT number, state, verdict FROM tasks WHERE work = ? ORDER BY number",
                        (work,)).fetchall()
    if not rows:
        return False, "nessun task"
    bad = [str(r["number"]) for r in rows if r["state"] != "done" or r["verdict"] != "approved"]
    return (not bad), ("task non chiusi: " + ", ".join(bad)) if bad else ""


def _findings(conn, work: int) -> tuple[bool, str]:
    rows = conn.execute(
        "SELECT id FROM findings WHERE work = ? AND severity IN ('blocker', 'major') "
        "AND verification = 'confirmed' AND user_decision IS NULL ORDER BY id",
        (work,)).fetchall()
    return (not rows), ", ".join(r["id"] for r in rows)


def _skills(conn, work: int) -> tuple[bool, str]:
    missing = []
    for r in conn.execute("SELECT number, skills_required, skills_used FROM tasks "
                          "WHERE work = ? ORDER BY number", (work,)):
        lack = [s for s in json.loads(r["skills_required"])
                if s not in json.loads(r["skills_used"])]
        if lack:
            missing.append(f"task {r['number']}: {', '.join(lack)}")
    return (not missing), "; ".join(missing)


def compute_dod(conn, work: int, *, head_sha: str, allow_no_tests: bool,
                external: Mapping[str, bool | None] | None = None,
                profile_items: Mapping[str, bool | None] | None = None) -> list[DodItem]:
    external = external or {}
    level = get_work(conn, work)["level"]
    computed = {
        "receipt": lambda: _receipt(conn, work, head_sha, allow_no_tests),
        "tasks_approved": lambda: _tasks(conn, work),
        "findings": lambda: _findings(conn, work),
        "skills": lambda: _skills(conn, work),
    }
    items = []
    for key in ITEMS_BY_LEVEL[level]:
        if key in computed:
            ok, detail = computed[key]()
        else:
            ok = external.get(key)
            detail = "non calcolata" if ok is None else ""
        items.append(DodItem(key, LABELS[key], ok, detail))
    for key, ok in (profile_items or {}).items():
        items.append(DodItem(key, f"Voce del profilo {key.removeprefix('profile:')}", ok,
                             "non calcolata" if ok is None else ""))
    return items


def dod_passes(items: list[DodItem]) -> bool:
    return all(i.ok is True for i in items)
