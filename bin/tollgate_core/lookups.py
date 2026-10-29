"""Letture registrate per task e nota di ricerca (B1, passo «informati prima»).

Le letture appartengono al task, non al singolo implementatore (decisione 5): un implementatore
nuovo eredita quelle dei giri precedenti. La nota sta in `tasks.research_note`, con l'esito in
`tasks.research_ok`."""
from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path
from typing import NamedTuple

from tollgate_analysis import bash, research

from . import clock, db, subagents

KINDS = ("read", "grep", "bash_read", "fetch", "search", "docs")


class Lookup(NamedTuple):
    kind: str
    target: str


def record(conn, *, work: int, task: int | None, agent_id: str | None, session: str | None,
           kind: str, target: str, now) -> None:
    """Una lettura; la stessa terna (lavoro, task, tipo, bersaglio) non si registra due volte."""
    if kind not in KINDS:
        raise ValueError(f"tipo di lettura sconosciuto: {kind}")
    if not target:
        raise ValueError("bersaglio della lettura vuoto")
    with db.tx(conn):
        # `IS` e non `=`: con task NULL il confronto con `=` non è mai vero.
        if conn.execute("SELECT 1 FROM lookups WHERE work = ? AND task IS ? AND kind = ? "
                        "AND target = ?", (work, task, kind, target)).fetchone():
            return
        conn.execute("INSERT INTO lookups (work, task, agent_id, session, kind, target, at) "
                     "VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (work, task, agent_id, session, kind, target, clock.fmt(now)))


def _resolved(path: str, *, base: str) -> str:
    """Percorso assoluto e risolto (collegamenti compresi): un collegamento nel worktree che
    punta fuori non rende il file «del worktree» (decisione 14)."""
    return str(Path(os.path.join(base, os.path.expanduser(path))).resolve())


def _file_target(path: str, *, cwd: str, worktree: str, must_exist: bool) -> str | None:
    full = _resolved(path, base=cwd)
    if must_exist and not os.path.isfile(full):
        return None
    return research.normalize_path(full, cwd=cwd, worktree=_resolved(".", base=worktree))


def observed(tool: str, tool_input: dict, tool_response: dict | None, *, cwd: str,
             worktree: str) -> list[Lookup]:
    """Cosa registrare per una lettura (decisione 4): una sola regola, per la via breve del
    runner e per il modulo `lookup_rec`. `Grep` conta solo in modo `content` esplicito su un
    file; `WebFetch` con codice di errore, e ogni forma non riconosciuta, non contano."""
    ti = tool_input if isinstance(tool_input, dict) else {}
    if tool == "Read":
        raw = ti.get("file_path")
        rel = _file_target(raw, cwd=cwd, worktree=worktree, must_exist=False) \
            if isinstance(raw, str) and raw else None
        return [Lookup("read", rel)] if rel else []
    if tool == "Grep":
        raw = ti.get("path")
        if ti.get("output_mode") != "content" or not isinstance(raw, str) or not raw:
            return []
        rel = _file_target(raw, cwd=cwd, worktree=worktree, must_exist=True)
        return [Lookup("grep", rel)] if rel else []
    if tool == "WebFetch":
        code = (tool_response or {}).get("code")
        if isinstance(code, int) and not isinstance(code, bool) and code >= 400:
            return []
        raw = ti.get("url")
        url = research.normalize_url(raw) if isinstance(raw, str) else None
        return [Lookup(research.URL_KIND, url)] if url else []
    if tool == "WebSearch":
        query = ti.get("query")
        return [Lookup("search", query.strip())] if isinstance(query, str) and query.strip() \
            else []
    if tool.startswith("mcp__") and research.is_doc_tool(tool):
        library = research.doc_library(ti)
        return [Lookup(research.DOCS_KIND, library)] if library else []
    return []


def observed_bash(command: str, *, cwd: str, worktree: str) -> list[Lookup]:
    """I file che un comando Bash mostra (`bash.read_targets`), ognuno risolto dalla cartella
    effettiva del comando (dopo `cd` o `-C`). Conta solo un file che esiste nel worktree: i
    bersagli possono essere cartelle (`grep -r foo src`) o glob."""
    try:
        cmds = bash.parse(command, cwd)
    except bash.BashParseError:
        return []
    out: list[Lookup] = []
    for c in cmds:
        for t in bash.read_targets(c):
            rel = _file_target(t, cwd=bash.effective_dir(c), worktree=worktree, must_exist=True)
            if rel:
                out.append(Lookup("bash_read", rel))
    return list(dict.fromkeys(out))


def _implementer_task(conn, row) -> int | None:
    """Il task di un subagente che lo sta eseguendo: il suo tipo è l'`agent_type` del task, che
    è `running`. Un revisore (tipo diverso, task in `review`) non lo è."""
    if row is None or row["task"] is None or row["work"] is None:
        return None
    t = conn.execute("SELECT 1 FROM tasks WHERE work = ? AND number = ? AND state = 'running' "
                     "AND agent_type = ?", (row["work"], row["task"], row["type"])).fetchone()
    return row["task"] if t else None


def owner(conn, *, agent_id: str | None, tool: str | None, work: int | None, now,
          stale_minutes: int) -> tuple[int, int] | None:
    """`(lavoro, task)` a cui appartiene una lettura (decisione 5), o None. Con `agent_id`: il
    task dell'implementatore. Senza (sessione principale): nessuno, salvo gli strumenti di
    `research.ATTRIBUTE_UNNAMED_TOOLS`, che vanno all'unico implementatore vivo del lavoro."""
    if work is None:
        return None
    if agent_id:
        row = subagents.get(conn, agent_id)
        task = _implementer_task(conn, row)
        return (work, task) if task is not None and row["work"] == work else None
    if tool not in research.ATTRIBUTE_UNNAMED_TOOLS:
        return None
    live = [r for r in subagents.running(conn, work=work)
            if _implementer_task(conn, r) is not None
            and not subagents.is_stale(r, now=now, stale_minutes=stale_minutes)]
    return (work, live[0]["task"]) if len(live) == 1 else None


def for_task(conn, work: int, task: int) -> list[Lookup]:
    """Le letture del task in ordine di registrazione, senza doppioni."""
    rows = conn.execute("SELECT kind, target FROM lookups WHERE work = ? AND task = ? "
                        "ORDER BY id", (work, task)).fetchall()
    return list(dict.fromkeys(Lookup(r[0], r[1]) for r in rows))


def detach_tasks(conn, work: int) -> None:
    """Dopo `reopen plan` i task si rinumerano: le letture del lavoro non valgono più per un
    numero (decisione 14)."""
    with db.tx(conn):
        conn.execute("UPDATE lookups SET task = NULL WHERE work = ? AND task IS NOT NULL",
                     (work,))


def set_note(conn, work: int, task: int, *, text: str, ok: bool) -> None:
    with db.tx(conn):
        conn.execute("UPDATE tasks SET research_note = ?, research_ok = ? "
                     "WHERE work = ? AND number = ?", (text, int(ok), work, task))


def note(conn, work: int, task: int) -> tuple[str | None, bool]:
    row = conn.execute("SELECT research_note, research_ok FROM tasks WHERE work = ? "
                       "AND number = ?", (work, task)).fetchone()
    if row is None:
        return None, False
    return row[0], bool(row[1])


def last_problems(conn, work: int, task: int) -> list[str]:
    """I problemi dell'ultima consegna della nota del task, se non era valida; vuota se era
    valida o non c'è. Conta solo gli eventi dopo l'ultimo `plan_reset` (dopo `reopen plan` i
    task si rinumerano). `conn` può essere anche la lettura sola del contesto degli hook."""
    reset = conn.execute("SELECT max(seq) FROM events WHERE work = ? AND type = 'plan_reset'",
                         (work,)).fetchone()[0] or 0
    last = None
    for (raw,) in conn.execute("SELECT data FROM events WHERE work = ? AND type = "
                               "'research_note' AND seq > ? ORDER BY seq", (work, reset)):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("task") == task:
            last = data
    problems = last.get("problems") if last and not last.get("ok") else None
    return [str(x) for x in problems] if isinstance(problems, list) else []


def prune(conn, *, now, days: int) -> int:
    """Cancella le letture dei lavori chiusi da più di `days` giorni. Non esiste un'ora di
    chiusura: vale l'ultimo aggiornamento del lavoro chiuso."""
    limit = clock.fmt(now - timedelta(days=days))
    with db.tx(conn):
        return conn.execute(
            "DELETE FROM lookups WHERE work IN "
            "(SELECT id FROM work_items WHERE phase = 'closed' AND updated < ?)",
            (limit,)).rowcount
