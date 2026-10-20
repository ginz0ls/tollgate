"""`tollgate finish check` (spec 6.4, decisione 4): la copia locale minima del gate.

Esegue il gate e i `dod` dei profili, calcola test-guard e scope sul diff della base, i
must-have dal JUnit della stessa esecuzione e i file di approvazione (L2), poi stampa la DoD voce
per voce. Verde: fase `review`. Rosso: la fase resta com'è. P4 sostituisce i pezzi dietro
`check`, che è la stessa interfaccia."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from tollgate_analysis import approvals as approvals_mod, mustcheck, plan as planmod
from tollgate_core import (acts, clock, config, db, dod, events, git, phases, receipts,
                           sessions, verify, violations)
from tollgate_core.paths import program_command

from . import gitw, prstate, taskcmd

OK, RED, REFUSED = 0, 1, 2
SKIP = ("findings", "specialists")      # si valutano dopo la revisione (decisione 15)
MAX_LISTED = 5


@dataclass
class CheckResult:
    code: int
    lines: list[str]
    items: list[dod.DodItem] = field(default_factory=list)


def _refuse(*lines: str) -> CheckResult:
    return CheckResult(REFUSED, [f"rifiuto: {x}" for x in lines])


def _label(key: str) -> str:
    return dod.LABELS.get(key) or f"Voce del profilo {key.removeprefix('profile:')}"


def _line(item: dod.DodItem, details: dict[str, str]) -> str:
    if item.ok is None and item.detail == dod.SKIPPED_DETAIL:
        return f"[dopo la revisione] {item.label}"
    detail = item.detail or details.get(item.key, "")
    return f"[{'sì' if item.ok else 'no'}] {item.label}" + (f": {detail}" if detail else "")


def _next_step(level: str, ok: bool) -> str:
    prog = program_command(db.BIN_PATH)
    if not ok:
        return f"prossimo passo: correggi le voci [no] e rilancia {prog} finish check"
    return f"prossimo passo: {prog} " + ("finish open-pr" if level == "L0" else "review prepare")


def check(state, cwd, *, now=None, environ=None) -> CheckResult:
    now = now or clock.now()
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        return _refuse(str(e))
    try:
        return _check(state, conn, Path(cwd), now, environ)
    except (sqlite3.Error, phases.TransitionError, config.ConfigError, git.GitError,
            OSError) as e:
        return _refuse(str(e))
    finally:
        conn.close()


def _check(state, conn, cwd: Path, now, environ) -> CheckResult:
    work = sessions.work_for_path(conn, cwd)
    if work is None:
        return _refuse("nessun lavoro attivo per questa cartella: lancia il comando dal "
                       "worktree del lavoro")
    wt = Path(work["worktree"])
    seen = prstate.detect(state, conn, work, git.main_worktree(wt), now=now)
    if seen.kind == "merged":
        return _refuse(f"la PR #{seen.pr.get('number')} è stata unita: il lavoro è chiuso")
    if seen.kind == "closed":
        return _refuse(prstate.closed_line(seen.pr))
    if work["phase"] not in ("execution", "review"):
        return _refuse(f"la fase è {work['phase']}: `finish check` si usa in execution (o in "
                       "review, per ripeterlo)")
    sha = git.head(wt)
    if sha is None:
        return _refuse("nessun commit da verificare")
    if work["phase"] == "review" and work["finish_sha"] == sha and work["finish_report"]:
        saved = _saved(work, sha)
        if seen.error:
            saved.lines.insert(0, f"avviso: {seen.error}")
        return saved

    lines: list[str] = [f"avviso: {seen.error}"] if seen.error else []
    if not gitw.fetch(wt):
        lines.append("avviso: git fetch origin non riuscito (senza rete?): si prosegue con i "
                     "riferimenti locali")
    level = work["level"]
    if level != "L0":
        open_tasks = [str(r["number"]) for r in conn.execute(
            "SELECT number, state, verdict FROM tasks WHERE work = ? ORDER BY number",
            (work["id"],)) if r["state"] != "done" or r["verdict"] != "approved"]
        if open_tasks:
            return _refuse("task non chiusi con verdetto approved: " + ", ".join(open_tasks))

    base = work["work_base_sha"] or git.default_ref(wt)
    if base is None:
        return _refuse("nessun riferimento remoto da cui leggere tollgate.toml")
    cfg = config.load_config(state, wt, base, env=environ)
    files = [c.path for c in git.changes(wt, base, head=sha) if c.status != "D"]
    extra = verify.dod_commands(cfg, files)
    required = [s.name for s in verify.gate_commands(cfg, files) + extra]

    run = verify.run_gate(state, cwd, produced_by="finish", extra=extra, now=now,
                          environ=environ)
    if run.sha is None:
        return _refuse(*run.lines)
    sha = run.sha
    lines += run.lines
    wid = work["id"]
    comps = cfg.get("components")
    details: dict[str, str] = {}

    found = [v for v in violations.diff_violations(cfg, conn, work, wt, base, sha,
                                                   git.changes(wt, base, head=sha),
                                                   components=comps)
             if not _own_document(wt, work, v)]
    external = {"guard_scope": not found}
    if found:
        shown = [f"{v.kind} {v.path}" for v in found[:MAX_LISTED]]
        more = len(found) - len(shown)
        details["guard_scope"] = ", ".join(shown) + (f" (+{more})" if more else "")

    manual: list[str] = []
    if level != "L0":
        external["must_have"], manual, details["must_have"] = _must_have(wt, work, cfg, comps,
                                                                         run)
    if level == "L2":
        external["approvals"], details["approvals"] = _approvals(wt, work)

    allow_unverified = acts.has_approval(conn, wid, "unverified-tests")
    allow_no_tests = cfg.get("project.allow_no_tests")
    profile_items, why = profile_receipts(conn, wid, sha, extra, allow_no_tests,
                                          allow_unverified)
    details.update(why)

    items = dod.compute_dod(conn, wid, head_sha=sha, allow_no_tests=allow_no_tests,
                            required_commands=required, external=external,
                            profile_items=profile_items, allow_unverified=allow_unverified,
                            skip=SKIP)
    green = dod.dod_passes([i for i in items if i.key not in SKIP])
    lines += [_line(i, details) for i in items]
    if manual:
        lines.append("da leggere: must-have con test manuale: " + ", ".join(manual))

    if green:
        phases.set_finish(conn, wid, sha, {"items": {i.key: i.ok for i in items},
                                           "manual": manual}, now=now)
        if work["phase"] == "execution":
            phases.set_phase(conn, state, wid, "review", "finish_check_green", now=now)
    events.record_event(conn, "finish_check", {"sha": sha, "ok": green}, now=now, work=wid)
    lines.append(_next_step(level, green))
    return CheckResult(OK if green else RED, lines, items)


def profile_receipts(conn, wid: int, sha: str, extra, allow_no_tests: bool,
                     allow_unverified: bool) -> tuple[dict[str, bool], dict[str, str]]:
    """Le voci `dod` dei profili attive dalle ricevute su `sha` (anche per `open-pr`) e, per
    quelle non verdi, il motivo."""
    items: dict[str, bool] = {}
    details: dict[str, str] = {}
    for spec in extra:
        rows = [r for r in receipts.latest(conn, wid, sha) if r["command"] == spec.name]
        items[spec.name], why = dod.receipt_verdict(rows, sha, allow_no_tests, [spec.name],
                                                    allow_unverified)
        if not spec.command and not items[spec.name]:
            why = (f"il comando «{spec.name.rsplit(':', 1)[-1]}» non è in [commands]: "
                   "dichiaralo, oppure serve /tollgate:approve unverified-tests")
        if why:
            details[spec.name] = why
    return items, details


def _own_document(wt: Path, work, v) -> bool:
    """Esenti dallo scope in un lavoro L2: i file di `reviews/<N>/` (approvazioni e report,
    scritti da CLI e hook) e la spec approvata, cioè con il blob in HEAD uguale allo `sha` di
    `spec-approval.md`. Il piano non è mai esente qui: lo è solo se è il blob registrato
    (`is_registered_plan`, dentro `diff_violations`)."""
    if v.kind != "out_of_scope":
        return False
    if v.path.startswith(f"{approvals_mod.REVIEWS_DIR}/{work['issue']}/"):
        return True
    if not work["spec_path"] or v.path != work["spec_path"]:
        return False
    header = approvals_mod.parse_approval(
        git.text_at(wt, "HEAD", approvals_mod.approval_paths(work["issue"])[0]) or "")
    try:
        blob = git.run(wt, "rev-parse", f"HEAD:{v.path}").strip()
    except git.GitError:
        return False
    return header is not None and header["kind"] == "spec-approval" and header["sha"] == blob


def _saved(work, sha: str) -> CheckResult:
    """Lo stesso SHA in `review`: l'esito salvato, senza rieseguire il gate (criterio 28)."""
    report = json.loads(work["finish_report"])
    items = [dod.DodItem(k, _label(k), ok, dod.SKIPPED_DETAIL if ok is None else "")
             for k, ok in report["items"].items()]
    lines = [f"finish check già verde su {sha[:7]}: esito salvato"]
    lines += [_line(i, {}) for i in items]
    if report.get("manual"):
        lines.append("da leggere: must-have con test manuale: " + ", ".join(report["manual"]))
    lines.append(_next_step(work["level"], True))
    return CheckResult(OK, lines, items)


def _must_have(wt: Path, work, cfg, comps, run) -> tuple[bool, list[str], str]:
    if not comps.get("must_have_tests", True):
        return True, [], "componente must_have_tests spento"
    try:
        text = taskcmd._plan_text(wt, work)
    except taskcmd.TaskError as e:
        return False, [], str(e)
    must_haves = planmod.check_plan(
        text, required_sections=cfg.get("plan.required_sections"),
        max_scope_files=cfg.get("plan.max_scope_files"), must_have_tests=True,
        level=work["level"], profiles=cfg.profiles,
        active_always=cfg.get("profiles.active")).must_haves
    ids_run: set[str] = set()
    ids_failed: set[str] = set()
    for junit in run.junits.values():
        if junit is not None:
            ids_run.update(junit.ids_run)
            ids_failed.update(junit.ids_failed)
    res = mustcheck.check(must_haves, ids_run | ids_failed, ids_failed)
    parts = []
    if res.missing:
        parts.append("test assenti dal report: " + "; ".join(res.missing))
    if res.failed:
        parts.append("test falliti: " + "; ".join(res.failed))
    return res.ok, res.manual, " | ".join(parts)


def _approvals(wt: Path, work) -> tuple[bool, str]:
    """Spec e piano approvati: i due file esistono in HEAD con `sha` uguale al blob del
    documento in HEAD. I report avversariali sono di P3c."""
    spec_approval, plan_approval = approvals_mod.approval_paths(work["issue"])
    problems = []
    for kind, doc, path in (("spec-approval", work["spec_path"], spec_approval),
                            ("plan-approval", work["plan_path"], plan_approval)):
        if not doc:
            problems.append(f"{kind}: il lavoro non ha {'la spec' if kind[0] == 's' else 'il piano'}")
            continue
        header = approvals_mod.parse_approval(git.text_at(wt, "HEAD", path) or "")
        if header is None or header["kind"] != kind:
            problems.append(f"{path} mancante o non valido in HEAD")
            continue
        try:
            blob = git.run(wt, "rev-parse", f"HEAD:{doc}").strip()
        except git.GitError:
            problems.append(f"{doc} assente in HEAD")
            continue
        if not approvals_mod.is_current(header, blob):
            problems.append(f"{path}: sha diverso da {doc} in HEAD (approvazione superata)")
    return not problems, "; ".join(problems)
