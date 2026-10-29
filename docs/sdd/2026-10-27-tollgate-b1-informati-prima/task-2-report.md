# Task 2 - Report

Commit 468b7d7 «tollgate B1: migrazione 6, letture registrate, lavori nati prima del passo».

## Implementato
- `db.py`: `SCHEMA_V6` (tabella `lookups` + indice `lookups_task(work, task)`, `tasks.research_note`, `tasks.research_ok`, `work_items.research`), aggiunta a `MIGRATIONS`.
- `bin/tollgate_core/lookups.py` (nuovo): `KINDS`, `Lookup`, `record`, `for_task`, `set_note`, `note`, `prune`, più `detach_tasks` (usata da `scope.reset_plan`).
- `phases.create_work(..., research=False)`; `start.py` e `adopt.py` passano `research=True`.
- `events.EVENT_TYPES` + `research_note`, `research_reminder`; `DEFAULTS["components"]["research_note"] = True`.
- `scope.reset_plan` mette `lookups.task = NULL` per il lavoro; `housekeeping.run` chiama `lookups.prune` con `retention.events_days` (passo «letture»).
- Decisioni del controller: `prune` per `phase='closed'` e `updated` più vecchio di `days`; `record` non duplica la terna (work, task, kind, target) (confronto con `IS`, valido anche per task NULL); `for_task` senza doppioni.

## Test
Nuovi: `tests/test_lookups.py` (record/for_task, doppioni, kind ignoto, target vuoto, set_note, prune, task None), `test_db.py::MigrationV6Test` (colonne e indice, lavori esistenti fuori con `research=0`/`research_ok=0` e copia `migrazione-6`, DB nuovo senza copia), `test_latest_version_is_6` (rinominato), `test_scope::test_reset_plan_drops_task_lookups`, `test_phases::test_create_work_research_flag`, `test_start::test_new_work_has_research_on`, `test_start::HousekeepingTest::test_prune_lookups_of_closed_works`, `test_adopt::test_adopted_work_has_research_on`, `test_config::test_research_note_component_default_true`.
Ritocco: `MigrationV5Test` aveva `"5"` fisso come versione finale: ora `str(db.latest_version())`.

## TDD
RED (`python3 -B -m unittest tests.test_lookups tests.test_db tests.test_scope tests.test_phases tests.test_config`): `ERROR test_lookups` e `test_scope` (import di `lookups`), `ERROR test_create_work_research_flag`, `ERROR test_research_note_component_default_true`, `FAIL test_latest_version_is_6`, `FAIL test_migration_6_columns`, `FAIL test_migration_keeps_existing_works_outside` (3 failures, 4 errors).
GREEN: stesso comando, `Ran 121 tests ... OK`. Poi `test_start test_adopt test_eval_cases test_layers`: `Ran 232 tests ... OK` (prova a secco degli eval verde).

## Suite completa
`tests/run`, python3.11: 2933 test, 1 fallimento; python3 (3.13.5): 2933 test, lo stesso 1 fallimento. Il fallimento e' `tests.test_cli.CliTest.test_db_restore_interactive_eof_and_ctrl_c [Ctrl-C]` ("nessun output dal pty"): il test passa da solo in primo piano (0,19 s) e fallisce da solo se lanciato in background (30 s), quindi dipende dal fatto che la suite gira in background senza terminale di controllo (Ctrl-C/SIGINT su processo in background), non da questo task (non tocca db restore ne' pty). Tutti gli altri verdi. Da rilanciare in primo piano dal controller se serve conferma.

## Scostamenti dal piano
Nessuno di sostanza. Aggiunta la funzione `lookups.detach_tasks` (non in elenco) per tenere le scritture su `lookups` dentro il suo modulo; `scope.py` importa `lookups` (strato core, ammesso).

## Dubbi
Solo il test pty sopra.
