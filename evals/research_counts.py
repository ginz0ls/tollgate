#!/usr/bin/env python3
"""Conteggi del passo «informati prima» nelle corse copiate da `evals/run.sh` (decisione 10 di B8).

  research_counts.py <cartella d'uscita>   una tabella Markdown con una riga per ogni corsa di `<uscita>/runs/`

Per ogni corsa si legge lo stato di tollgate copiato (`<corsa>/home/.local/state/tollgate/tollgate.db`) senza scriverci e
senza creare file accanto: connessione `mode=ro&immutable=1` (con `mode=ro` da solo SQLite crea `-shm` e `-wal`). Un `-wal`
accanto al database vuol dire che i suoi frame non si vedrebbero con `immutable=1`: si rifiuta (l'anonimizzazione di
`evals/scrub.py` fa già il checkpoint). Una corsa senza `tollgate.db` si salta e la tabella lo dice; ma lo scaffold crea lo stato anche nel braccio senza plugin, che
compare quindi con righe a zero (la tabella non distingue i bracci).
Solo libreria standard."""
from __future__ import annotations

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.dont_write_bytecode = True

DB_RELATIVE = Path("home") / ".local" / "state" / "tollgate" / "tollgate.db"
GATE_RULE = "research_gate"
LOOKUP_KINDS = ("read", "grep", "bash_read", "fetch", "search", "docs")   # il CHECK di `lookups.kind` (bin/tollgate_core/db.py)
COLUMNS = ("note_ok", "note_ko", "reminders", "switch_unreadable", "research_vetoes",
           *(f"lookups_{k}" for k in LOOKUP_KINDS))
HEADINGS = ("Note valide", "Note rifiutate", "Promemoria", "Cambio illeggibile", "Veti della nota",
            *(f"Letture {k}" for k in LOOKUP_KINDS))


class WalError(RuntimeError):
    """Accanto al database c'è un `-wal`: il conteggio con `immutable=1` sarebbe incompleto."""


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _data(raw) -> dict:
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def count(run_dir: Path) -> dict[str, int]:
    """I conteggi di una corsa (`<uscita>/runs/<corsa>`): le chiavi di `COLUMNS`. Uno stato senza la tabella `events` o
    `lookups` (come quelli di P5, di prima di B1) dà zero. `WalError` se accanto al database c'è un `-wal`;
    `FileNotFoundError` se il database manca."""
    db = Path(run_dir).resolve() / DB_RELATIVE      # `as_uri` non accetta un percorso relativo
    if not db.is_file():
        raise FileNotFoundError(db)
    if Path(f"{db}-wal").exists():
        raise WalError(f"{db.name}-wal presente: fai prima il checkpoint (evals/scrub.py anonymize)")
    out = dict.fromkeys(COLUMNS, 0)
    with closing(sqlite3.connect(f"{db.as_uri()}?mode=ro&immutable=1", uri=True)) as conn:
        if _has_table(conn, "events"):
            for kind, raw in conn.execute("SELECT type, data FROM events WHERE type IN "
                                          "('research_note', 'research_reminder', 'research_switch_unreadable', 'veto')"):
                if kind == "research_note":
                    out["note_ok" if _data(raw).get("ok") is True else "note_ko"] += 1
                elif kind == "research_reminder":
                    out["reminders"] += 1
                elif kind == "research_switch_unreadable":
                    out["switch_unreadable"] += 1
                elif _data(raw).get("rule") == GATE_RULE:
                    out["research_vetoes"] += 1
        if _has_table(conn, "lookups"):
            for kind, n in conn.execute("SELECT kind, COUNT(*) FROM lookups GROUP BY kind"):
                if f"lookups_{kind}" in out:
                    out[f"lookups_{kind}"] = n
    return out


def table(out_dir: Path) -> str:
    """La tabella Markdown di tutte le corse di `<out_dir>/runs/`."""
    lines = ["| Corsa | " + " | ".join(HEADINGS) + " |", "| :- | " + " | ".join("-:" for _ in HEADINGS) + " |"]
    runs_dir = Path(out_dir) / "runs"
    runs = sorted(p for p in runs_dir.glob("*") if p.is_dir()) if runs_dir.is_dir() else []
    skipped = []
    for run in runs:
        if not (run / DB_RELATIVE).is_file():
            skipped.append(run.name)
            continue
        counts = count(run)
        lines.append(f"| {run.name} | " + " | ".join(str(counts[c]) for c in COLUMNS) + " |")
    text = "\n".join(lines) + "\n"
    if skipped:
        text += "\nSenza stato di tollgate, saltate (il braccio senza plugin non ne ha): " + ", ".join(skipped) + "\n"
    return text


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        sys.stdout.write(table(Path(argv[0])))
    except (WalError, OSError, sqlite3.Error) as exc:
        print(f"conteggi non fatti: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
