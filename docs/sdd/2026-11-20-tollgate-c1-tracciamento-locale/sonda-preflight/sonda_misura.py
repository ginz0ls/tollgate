"""Sonda Task 8: misura delle copie dello stato negli eval. Copia in una cartella mkdtemp(prefix="tollgate-"),
apre solo le copie (sqlite3 della libreria standard), cancella la cartella alla fine. Mai file del repo aperti."""
import collections, json, shutil, sqlite3, sys, tempfile
from pathlib import Path
W = Path(__file__).resolve().parents[4]
sys.dont_write_bytecode = True
found = sorted((W / "docs/verifiche/evidenze").rglob("tollgate.db"))
tmp = Path(tempfile.mkdtemp(prefix="tollgate-"))
try:
    versions = collections.Counter(); has_events = collections.Counter(); rows = []
    for i, src in enumerate(found):
        dst = tmp / f"{i}.db"
        shutil.copyfile(src, dst)
        # il file potrebbe avere -wal: nelle evidenze non c'è (verificato: nessun tollgate.db-*)
        c = sqlite3.connect(f"file:{dst}?mode=ro", uri=True)
        try:
            try:
                v = c.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
                v = v[0] if v else None
            except sqlite3.Error as e:
                v = f"errore:{e}"
            versions[v] += 1
            tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            has_events[("events" in tables)] += 1
            if "events" in tables:
                n, d, extra = c.execute("SELECT count(*), coalesce(sum(length(data)),0), "
                    "coalesce(sum(length(type)+length(host)+length(at)+coalesce(length(session),0)+coalesce(length(repo_key),0)),0) FROM events").fetchone()
                tipi = collections.Counter(r[0] for r in c.execute("SELECT type FROM events"))
                rows.append((str(src.relative_to(W)).split("/runs/")[0].split("/")[-1], n, d, extra, tipi))
        finally:
            c.close()
    print("copie:", len(found), "versioni schema:", dict(versions), "con tabella events:", dict(has_events))
    tot_n = sum(r[1] for r in rows); tot_d = sum(r[2] for r in rows); tot_e = sum(r[3] for r in rows)
    print("eventi totali:", tot_n, "byte data:", tot_d, "byte altri campi testo:", tot_e)
    if tot_n:
        print("byte medi per evento (data + campi testo, senza busta fissa interi):", round((tot_d + tot_e) / tot_n, 1))
    ns = sorted(r[1] for r in rows)
    print("eventi per stato: min", ns[0], "mediana", ns[len(ns)//2], "max", ns[-1])
    allt = collections.Counter()
    for r in rows: allt.update(r[4])
    print("tipi:", dict(allt.most_common(12)))
    # un evento tipico, la busta intera, in byte JSON
    c = sqlite3.connect(f"file:{tmp / '0.db'}?mode=ro", uri=True); c.row_factory = sqlite3.Row
    r = c.execute("SELECT * FROM events ORDER BY seq LIMIT 1").fetchone()
    env = {k: r[k] for k in r.keys()}
    env["data"] = json.loads(env["data"])
    print("esempio busta (chiavi):", sorted(env), "byte JSON:", len(json.dumps(env, ensure_ascii=False, sort_keys=True)))
    c.close()
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("cartella temporanea rimossa:", not tmp.exists())
