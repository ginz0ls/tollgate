"""Import in `events` delle accensioni e degli spegnimenti scritti dal wrapper (decisione 5)."""
from __future__ import annotations

import os
import re

from . import clock, db
from .events import record_event
from .paths import State

LOG_NAME = "off.log"
_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z) (off|on)(?: (\d+))?\s*$")


def import_log(conn, state: State) -> int:
    log = state.root / LOG_NAME
    work_file = state.root / f".{LOG_NAME}.{os.getpid()}"
    try:
        log.rename(work_file)   # atomico: due hook insieme non importano due volte
    except FileNotFoundError:
        return 0
    n = 0
    try:
        text = work_file.read_text(encoding="utf-8", errors="replace")
        # Tutte le righe in una transazione: se una scrittura fallisce, il file è già spostato
        # e nessun evento resta a metà.
        with db.tx(conn):
            for line in text.splitlines():
                m = _LINE.match(line)
                if not m:
                    continue
                data = {"until": int(m.group(3))} if m.group(3) else {}
                record_event(conn, m.group(2), data, now=clock.parse(m.group(1)))
                n += 1
    finally:
        work_file.unlink(missing_ok=True)
    return n
