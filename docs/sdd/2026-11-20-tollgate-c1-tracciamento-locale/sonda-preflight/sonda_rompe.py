"""Sonda: quali test di oggi cambiano esito con (a) events_days predefinito 0 e (b) uno schema 7 in coda a MIGRATIONS.
Le due modifiche sono fatte in-process (nessun file del repo cambia) e si lanciano solo test mirati."""
import sys, unittest
from pathlib import Path
W = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(W / "bin")); sys.path.insert(0, str(W))
sys.dont_write_bytecode = True
from tollgate_core import config, db
config.DEFAULTS["retention"]["events_days"] = 0            # (a) decisione 7
from tollgate_core import events
_orig = events.prune_events
events.prune_events = lambda conn, now, days: 0 if days == 0 else _orig(conn, now, days)  # 0 = mai, come farà housekeeping
db.MIGRATIONS.append((7, [                                   # (b) decisione 1
    "ALTER TABLE work_items ADD COLUMN size TEXT CHECK (size IS NULL OR size IN ('small','medium','large'))",
    "ALTER TABLE work_items ADD COLUMN size_by TEXT CHECK (size_by IS NULL OR size_by IN ('rules','user'))",
    "ALTER TABLE work_items ADD COLUMN slices INTEGER"]))
names = [
    "tests.test_config.LoadTextTest.test_minimal_gets_defaults",
    "tests.test_events.EventsTest.test_prune_keeps_recent_and_seq_never_reused",
    "tests.test_start.HousekeepingTest.test_housekeeping",
    "tests.test_start.HousekeepingTest.test_prune_lookups_of_closed_works",
    "tests.test_start.HousekeepingTest.test_housekeeping_without_directories",
    "tests.test_start.HousekeepingTest.test_malformed_sessions_do_not_skip_other_cleanups",
    "tests.test_start.HousekeepingTest.test_prune_events_error_does_not_skip_prune_bound",
    "tests.test_db.MigrationV4Test.test_latest_version_is_6",
    "tests.test_db.MigrationV6Test.test_migration_keeps_existing_works_outside",
    "tests.test_db.MigrationV6Test.test_fresh_db_makes_no_copy",
    "tests.test_db.MigrationV2Test.test_from_v1_adds_columns_and_backup",
    "tests.test_db.OpenTest.test_pragmas_and_tables",
]
loader = unittest.TestLoader()
suite = unittest.TestSuite()
missing = []
for n in names:
    try:
        suite.addTests(loader.loadTestsFromName(n))
    except Exception as e:
        missing.append((n, str(e)[:80]))
res = unittest.TextTestRunner(stream=open("/dev/null", "w"), verbosity=0).run(suite)
bad = {str(t[0]).split(" ")[0] + " " + str(t[0]).split(" ")[1] for t in res.failures + res.errors}
print("eseguiti:", res.testsRun, "falliti/errori:", len(res.failures) + len(res.errors))
for t, tb in res.failures + res.errors:
    last = [l for l in tb.strip().splitlines() if l.strip()][-1][:110]
    print("  ROSSO", t.id().replace("tests.", ""), "->", last)
for n, e in missing:
    print("  NON TROVATO", n, e)
