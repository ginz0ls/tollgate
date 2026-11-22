"""Sonda Task 1: le tre ALTER TABLE della decisione 1 su un DB alla versione 6 con un lavoro."""
import sqlite3, sys
from pathlib import Path
W = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(W / "bin")); sys.path.insert(0, str(W))
sys.dont_write_bytecode = True
from tests.helpers import TempState
from tollgate_core import db
SCHEMA_V7 = [
    "ALTER TABLE work_items ADD COLUMN size TEXT CHECK (size IS NULL OR size IN ('small','medium','large'))",
    "ALTER TABLE work_items ADD COLUMN size_by TEXT CHECK (size_by IS NULL OR size_by IN ('rules','user'))",
    "ALTER TABLE work_items ADD COLUMN slices INTEGER",
]
ts = TempState()
try:
    conn = db.open_db(ts.state)
    print("versione di partenza:", db.latest_version())
    conn.execute("INSERT INTO work_items (repo_key, issue, level, phase, sessions, created, updated) "
                 "VALUES ('r', 1, 'L1', 'plan', '[]', 'x', 'x')")
    with db.tx(conn):
        for s in SCHEMA_V7:
            conn.execute(s)
    r = conn.execute("SELECT size, size_by, slices FROM work_items").fetchone()
    print("riga esistente:", tuple(r))
    for sql in ("UPDATE work_items SET size='enorme'", "UPDATE work_items SET size_by='modello'"):
        try:
            conn.execute(sql); print("NESSUN ERRORE:", sql)
        except sqlite3.IntegrityError as e:
            print("IntegrityError:", sql)
    conn.execute("UPDATE work_items SET size='large', size_by='user', slices=3")
    print("ok valori validi:", tuple(conn.execute("SELECT size,size_by,slices FROM work_items").fetchone()))
    print("sqlite", sqlite3.sqlite_version)
    conn.close()
finally:
    ts.cleanup()
