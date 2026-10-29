"""`tollgate research submit|show <k>` (B1, decisioni 1, 2, 3): la nota di ricerca dell'implementatore.

`submit` confronta la nota con le letture registrate del task (`lookups.for_task`), salva il testo
in `tasks.research_note` con l'esito in `tasks.research_ok` e lo copia in
`.tollgate-run/<N>/research-<k>.md` (già fuori da git, spec 6.3), con una riga finale `esito:`."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import NamedTuple

from tollgate_analysis import research
from tollgate_core import clock, config, db, events, git, lookups, sessions, tasks

OK, INVALID, REFUSED = 0, 1, 2
RUN_DIR = ".tollgate-run"
VALID, NOT_VALID = "esito: valida", "esito: non valida"


class SubmitResult(NamedTuple):
    code: int
    lines: list[str]
    path: Path | None


def note_path(worktree: Path, issue: int, number: int) -> Path:
    """L'unico punto che compone il percorso del file della nota (decisione 1)."""
    return Path(worktree) / RUN_DIR / str(issue) / f"research-{number}.md"


def _refused(*lines: str) -> SubmitResult:
    return SubmitResult(REFUSED, list(lines), None)


def _write_atomic(path: Path, text: str) -> None:
    """File temporaneo accanto e `os.replace`, come `apply._write_atomic` (lo strato `flow` non
    importa `hooks`); in ogni caso il temporaneo non resta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except (OSError, ValueError):
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _component_on(state, work) -> bool:
    wt = Path(work["worktree"])
    main = git.main_worktree(wt)
    base = work["work_base_sha"] or git.default_ref(main)
    return bool(config.load_config(state, main, base).get("components.research_note"))


def _open(state, cwd: Path):
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        return None, None, _refused(str(e))
    work = sessions.work_for_path(conn, cwd)
    if work is None:
        conn.close()
        return None, None, _refused("nessun lavoro attivo per questa cartella: lancia il "
                                    "comando dal worktree del lavoro")
    return conn, work, None


def _task(conn, work, number: int):
    try:
        return tasks.get_task(conn, work["id"], number), None
    except ValueError:
        return None, _refused(f"task {number} inesistente nel lavoro #{work['issue']}")


def submit(state, cwd: Path, number: int, text: str, *, now=None) -> SubmitResult:
    now = now or clock.now()
    conn, work, refusal = _open(state, Path(cwd))
    if refusal:
        return refusal
    try:
        if work["level"] == "L0":
            return _refused("in L0 lavora la sessione principale: non c'è nessuna nota di "
                            "ricerca da consegnare")
        if work["phase"] != "execution":
            return _refused(f"la fase è {work['phase']}: la nota si consegna in execution")
        if not work["research"]:
            return _refused("lavoro iniziato prima del passo informati prima: non richiede "
                            "la nota di ricerca")
        try:
            if not _component_on(state, work):
                return _refused("componente research_note spento: non richiede la nota di "
                                "ricerca")
        except (config.ConfigError, git.GitError) as e:
            return _refused(f"configurazione non leggibile: {e}")
        row, refusal = _task(conn, work, number)
        if refusal:
            return refusal
        if row["state"] != "running":
            return _refused(f"task {number} è {row['state']}, non running: la nota si "
                            "consegna mentre il task è in corso")
        wt = Path(work["worktree"])
        found = [(x.kind, x.target) for x in lookups.for_task(conn, work["id"], number)]
        problems = research.check_note(research.parse_note(text), found, worktree=str(wt))
        ok = not problems
        path = note_path(wt, work["issue"], number)
        body = text if text.endswith("\n") else text + "\n"
        try:
            _write_atomic(path, f"{body}{VALID if ok else NOT_VALID}\n")
        except (OSError, ValueError) as e:
            return _refused(f"nota non scritta in {path}: {e}")
        lookups.set_note(conn, work["id"], number, text=text, ok=ok)
        events.record_event(conn, "research_note",
                            {"task": number, "ok": ok, "problems": problems}, now=now,
                            work=work["id"])
        if ok:
            return SubmitResult(OK, [f"nota di ricerca valida (task {number}): {path}"], path)
        return SubmitResult(INVALID, [f"nota di ricerca salvata ma non valida (task {number}):",
                                      *(f"- {p}" for p in problems),
                                      "Correggi (o leggi quello che manca) e consegna di nuovo "
                                      "la nota."], path)
    except sqlite3.Error as e:
        return _refused(f"database non disponibile: {e}")
    finally:
        conn.close()


def show(state, cwd: Path, number: int) -> SubmitResult:
    conn, work, refusal = _open(state, Path(cwd))
    if refusal:
        return refusal
    try:
        _, refusal = _task(conn, work, number)
        if refusal:
            return refusal
        text, ok = lookups.note(conn, work["id"], number)
        if text is None:
            return _refused(f"task {number}: nessuna nota di ricerca consegnata")
        path = note_path(Path(work["worktree"]), work["issue"], number)
        return SubmitResult(OK if ok else INVALID,
                            [*text.rstrip("\n").splitlines(), VALID if ok else NOT_VALID],
                            path if path.is_file() else None)
    except sqlite3.Error as e:
        return _refused(f"database non disponibile: {e}")
    finally:
        conn.close()
