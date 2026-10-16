# Task 2 - Migrazione 2, sessioni, subagenti, assegnazione dei task

**Status:** DONE
**Commit:** `82e6e16` tollgate P2: migrazione 2, sessioni, subagenti, assegnazione dei task
**Ramo:** `p2-guardrail` (worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p2-guardrail`)

## Implementato

- `bin/tollgate_core/db.py`: `SCHEMA_V2` (tabella `session_seen`; colonne `subagents.last_seen`, `vetoes`, `report`; `tasks.pending` con CHECK; `work_items.level_cap_paths`; indice `subagents_work`) e `MIGRATIONS = [(1, SCHEMA_V1), (2, SCHEMA_V2)]`. `latest_version()` restituisce 2.
- Correzione C1 di `carry.md` in `_migrate`: `fresh = current == 0` letto prima del ciclo; il backup `migrazione-N` si fa solo se `not fresh`. Un DB creato nella stessa apertura non produce più una copia della v1.
- `bin/tollgate_core/sessions.py` (nuovo): `touch`, `alive`, `bound_work`, `work_for_path`, `mark_bound`, `BOUND_DIR`.
- `bin/tollgate_core/subagents.py` (nuovo): `STATES`, `get`, `start` (con ripresa che conserva `agent_base_sha`), `touch`, `set_name`, `set_report`, `add_veto`, `finish`, `by_name`, `running`, `is_stale` (C16), `interrupt`.
- `bin/tollgate_core/tasks.py`: `PENDING`, `assign`, `take_pending`, `add_commit` (con deduplica).
- Test: `tests/test_sessions.py` (4 test), `tests/test_subagents.py` (6 test), `tests/test_tasks.py` (`AssignTest`, 3 test), `tests/test_db.py` (`MigrationV2Test`, versioni attese con `str(db.latest_version())`, `test_migration_makes_backup_first` aggiornato secondo C1).

## Test ed esiti

Suite completa, `tests/run`:

```
== Python 3.11.16
Ran 138 tests in 3.484s
OK
== Python 3.13.5
Ran 138 tests in 3.721s
OK
```

138 = 124 di partenza + 14 nuovi.

## Evidenza TDD

- RED (tests/test_sessions, test_subagents, test_tasks prima del codice):
  ```
  ImportError: Failed to import test module: test_sessions
  ImportError: cannot import name 'sessions' from 'tollgate_core'
  ImportError: Failed to import test module: test_subagents
  ImportError: cannot import name 'subagents' from 'tollgate_core'
  AttributeError: module 'tollgate_core.tasks' has no attribute 'add_commit'
  AttributeError: module 'tollgate_core.tasks' has no attribute 'assign'
  Ran 11 tests ... FAILED (errors=5)
  ```
- RED migrazione: `MigrationV2Test.test_from_v1_adds_columns_and_backup` fallisce con `db.py` di HEAD (`FAILED (failures=1)`). Il test è stato scritto dopo la modifica di `db.py`, quindi il RED è stato verificato a posteriori ripristinando temporaneamente il file di HEAD; la versione nuova è stata poi ripristinata e il test passa.
- GREEN: `tests.test_tasks tests.test_db tests.test_sessions tests.test_subagents`: `Ran 41 tests ... OK`; poi `tests/run` come sopra.

## File cambiati

- `bin/tollgate_core/db.py`
- `bin/tollgate_core/tasks.py`
- `bin/tollgate_core/sessions.py` (nuovo)
- `bin/tollgate_core/subagents.py` (nuovo)
- `tests/test_db.py`
- `tests/test_tasks.py`
- `tests/test_sessions.py` (nuovo)
- `tests/test_subagents.py` (nuovo)

## Scostamenti dal piano e perché

1. `_migrate` con `fresh` (C1 di `carry.md`): decisione del controller, applicata. `test_migration_makes_backup_first` ora usa `db.latest_version() + 1` e cerca `*migrazione-3*.db`, come richiesto.
2. `tasks.assign`: il piano chiama `_log(conn, row, ...)` con la riga letta prima dell'UPDATE. Ho preferito rileggere la riga dopo l'UPDATE, così l'evento `task_change` riporta lo stato scritto. Nessun effetto sui test; è una differenza di sostanza minima.
3. `sessions.work_for_path`: ho tolto l'annotazione di ritorno `-> object | None` del piano (inutile, e `sqlite3.Row | None` non è esprimibile in modo utile qui).

## Autorevisione

- Completezza rispetto al brief: tutte le firme della sezione "Produces" sono presenti, compresi `subagents.is_stale` (C16) e `subagents.STATES`.
- Nessuna scrittura fuori dal DB di test: tutti i test usano `TempState`; nessun `~/.local/state/tollgate`, nessuna rete, nessun `claude`.
- Nessun `__pycache__` nel repo (`-B`).
- Il working tree è pulito dopo il commit.

## Dubbi

1. Attribution del commit: `implementer-rules.md` chiede `Co-Authored-By: Claude Opus 5.5`, mentre il promemoria di attribuzione di sessione chiede `Claude Haiku 5.5`, che è il modello effettivo di questa sessione. Ho usato Haiku 5.5. Se serve la riga Opus, il commit va corretto con un commit nuovo (non amend, per le regole di git safety).
2. `subagents.is_stale` e `subagents.interrupt` non hanno ancora un chiamante: serviranno ai Task 18 e P3. `interrupt` avanza il task solo se è in stato `running`, per non sollevare `TaskTransitionError` su task già in altro stato.
3. `sessions.bound_work` considera legato anche un lavoro in fase `blocked` (esclude solo `closed`), come da brief.
