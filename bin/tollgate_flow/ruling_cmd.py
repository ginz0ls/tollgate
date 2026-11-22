"""`ruling add [--task K] [--by agent|user]` (C1, decisione 5): registra una decisione presa al posto
dell'utente, sul modello di `research submit` (il testo da stdin in un heredoc a delimitatore
quotato, così apostrofi, `$` e backtick non toccano né la shell né l'analisi dei comandi).

Il testo ha tre campi: una riga che comincia con `cosa:`, `perché:` (anche `perche:` e `perchè:`) o `costo:`
apre un campo, senza distinguere le maiuscole; ogni altra riga continua il campo aperto. Un testo
non vuoto prima del primo campo è un problema. Va nel DB come evento `ruling`; niente su GitHub."""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import NamedTuple

from tollgate_core import clock, db, events, sessions, tasks

OK, REFUSED = 0, 2
RULING_TEXT_MAX = 1000
HEREDOC_END = "RULING_FINE"
BY = ("agent", "user")

_LABEL = re.compile(r"^\s*(cosa|perch[eèé]|costo)\s*:(.*)$", re.IGNORECASE)
_FIELD = {"cosa": "what", "perche": "why", "perché": "why", "perchè": "why",
          "costo": "cost"}
_SHOWN = {"what": "cosa", "why": "perché", "cost": "costo"}


class RulingResult(NamedTuple):
    code: int
    lines: list[str]


def parse_text(text: str) -> tuple[dict[str, str] | None, list[str]]:
    """I tre campi (`what`, `why`, `cost`), oppure i problemi (e nessun campo)."""
    parts: dict[str, list[str]] = {}
    problems: list[str] = []
    current: str | None = None
    leading = False   # già segnalato il testo prima del primo campo
    for line in unicodedata.normalize("NFC", text).splitlines():
        m = _LABEL.match(line)
        if m:
            current = _FIELD[m.group(1).lower()]
            if current in parts:
                problems.append(f"il campo «{_SHOWN[current]}» è ripetuto")
            parts.setdefault(current, [])
            if m.group(2).strip():
                parts[current].append(m.group(2).strip())
        elif current is not None:
            if line.strip():
                parts[current].append(line.strip())
        elif line.strip() and not leading:
            problems.append("c'è del testo prima del primo campo: il testo comincia con la riga "
                            "«cosa:»")
            leading = True   # un solo avviso, anche se il testo iniziale ha più righe
    for key, shown in _SHOWN.items():
        if key not in parts:
            problems.append(f"manca il campo «{shown}:»")
        elif not parts[key]:
            problems.append(f"il campo «{shown}:» è vuoto")
    if problems:
        return None, problems
    return {k: " ".join(v) for k, v in parts.items()}, []


def command(program: str, task: int | None) -> str:
    """Il heredoc da copiare, con il modello dei tre campi."""
    opt = f" --task {task}" if task is not None else ""
    return "\n".join((
        f"{program} ruling add{opt} <<'{HEREDOC_END}'",
        "cosa: <la scelta che hai fatto al posto dell'utente>",
        "perché: <perché l'hai fatta tu e non l'utente>",
        "costo: <cosa costa se la scelta è sbagliata>",
        HEREDOC_END,
    ))


def _refused(*lines: str) -> RulingResult:
    return RulingResult(REFUSED, list(lines))


def add(state, cwd: Path, text: str, *, task: int | None, by: str, now=None) -> RulingResult:
    now = now or clock.now()
    if by not in BY:
        return _refused(f"--by deve essere uno tra {', '.join(BY)}")
    fields, problems = parse_text(text)
    if fields is None:
        return _refused("ruling non registrata:", *(f"- {p}" for p in problems),
                        "Il testo ha tre righe: cosa:, perché:, costo:.")
    long = [_SHOWN[k] for k, v in fields.items() if len(v) > RULING_TEXT_MAX]
    if long:
        return _refused(f"ruling non registrata: il campo «{long[0]}:» supera il limite di "
                        f"{RULING_TEXT_MAX} caratteri")
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        return _refused(str(e))
    try:
        work = sessions.work_for_path(conn, Path(cwd))
        if work is None:
            return _refused("nessun lavoro attivo per questa cartella: lancia il comando dal "
                            "worktree del lavoro")
        if task is not None:
            try:
                tasks.get_task(conn, work["id"], task)
            except ValueError:
                return _refused(f"task {task} inesistente nel lavoro #{work['issue']}")
        seq = events.record_event(conn, "ruling", {**fields, "by": by, "task": task}, now=now,
                                  work=work["id"])
        return RulingResult(OK, [f"ruling registrata (evento {seq})"])
    except sqlite3.Error as e:
        return _refused(f"database non disponibile: {e}")
    finally:
        conn.close()
