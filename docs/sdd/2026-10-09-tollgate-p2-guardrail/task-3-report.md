# Task 3 — Scope, ricevute, effetti, registro di OFF, ricevuta `uncounted` nella DoD

**Status:** DONE
**Commit:** `0093c24` tollgate P2: scope, ricevute, effetti, registro di OFF; uncounted nella DoD
**Ramo / worktree:** `p2-guardrail`, `.claude/worktrees/p2-guardrail`

## Implementato

- `bin/tollgate_core/scope.py`: `paths`, `set_plan_path` (scrive solo se `plan_path` è NULL), `register_plan` (rifiuta con `ValueError` se `plan_sha` è già valorizzato; registra scope, task e evento `scope_registered`; avanza a `execution` se `advance=True`).
- `bin/tollgate_core/receipts.py`: `STATES`, `add` (valida lo stato, evento `receipt`), `latest` (ultima ricevuta per comando), `any_since`.
- `bin/tollgate_core/effects.py`: `effect_key` (sha256 di comando, lavoro, sha), `effect_id` (`e-` + 8 hex), `get`, `executed_at`, `request` (riusa la riga dell'intento e conserva `executed_at`), `mark_executed`.
- `bin/tollgate_core/offlog.py`: `LOG_NAME = "off.log"`, `import_log`. Il file viene spostato con `rename` (atomico), le righe valide diventano eventi `off`/`on` con il timestamp originale; `off` con ore produce `{"until": N}`.
- `bin/tollgate_core/dod.py::_receipt`: legge anche `r.exit`; accetta `uncounted` solo con `allow_no_tests` e uscita 0 (decisione 11). Il resto della funzione è invariato.
- Test: `tests/test_scope.py`, `tests/test_receipts.py`, `tests/test_effects.py`, `tests/test_offlog.py` (nuovi) e `UncountedTest` in `tests/test_dod.py` (con import di `receipts`). Testi dal brief, senza modifiche.

## Test ed esiti

- Baseline prima del lavoro: `tests/run` verde, 138 test.
- Dopo: `tests/run` verde su `python3.11` (3.11.16) e `python3` (3.13.5), 150 test ciascuno (138 + 12 nuovi). Output pulito, nessun `__pycache__` nel repo.
- Test mirati (`tests.test_scope tests.test_receipts tests.test_effects tests.test_offlog tests.test_dod`): 22 OK.

## Evidenza TDD

RED (moduli mancanti, prima di scrivere il codice):
```
python3 -B -m unittest tests.test_scope tests.test_receipts tests.test_effects tests.test_offlog tests.test_dod
...
ImportError: cannot import name 'receipts' from 'tollgate_core'
Ran 5 tests in 0.000s
FAILED (errors=5)
```

RED per la sola modifica di `dod._receipt` (con la versione di HEAD di `dod.py` al posto di quella nuova, poi ripristinata):
```
python3 -B -m unittest tests.test_dod.UncountedTest
FAIL: test_uncounted_ok_only_with_allow_no_tests_and_exit_zero
  self.assertTrue(item.ok)
AssertionError: False is not true
FAILED (failures=1)
```

GREEN: `tests/run` con 150 test OK, come sopra.

## File cambiati

- Nuovi: `bin/tollgate_core/scope.py`, `bin/tollgate_core/receipts.py`, `bin/tollgate_core/effects.py`, `bin/tollgate_core/offlog.py`, `tests/test_scope.py`, `tests/test_receipts.py`, `tests/test_effects.py`, `tests/test_offlog.py`.
- Modificati: `bin/tollgate_core/dod.py`, `tests/test_dod.py`.

## Scostamenti dal piano

1. `offlog.import_log`: le righe vengono scritte in un'unica transazione (`db.tx`) invece che una `record_event` per riga. Motivo: il file è già stato spostato con `rename` prima dell'import; se una scrittura falliva a metà, le righe già importate restavano e le successive andavano perse. Il comportamento osservabile dei test non cambia.

Nessun altro scostamento: firme, tabelle (`receipts`, `intents`, `scope`, `work_items`) e colonne usate corrispondono allo schema delle migrazioni 1 e 2 e alle funzioni del Task 2 (`tasks.add_task`, `phases.set_phase`, `clock`, `events.record_event`).

## Autorevisione

- Completezza rispetto al brief: tutti i moduli e le funzioni dei Produces presenti con le firme indicate; `dod._receipt` con la regola della decisione 11.
- `carry.md`: nessuna voce per il Task 3; le regole C1 (backup in migrazione) e C13/C16 non riguardano questo task.
- Nomi, output dei test puliti, test sul comportamento reale (file su disco, transazioni, eventi nel DB).
- `tests/run` su entrambi gli interpreti, nessun file fuori dal perimetro del task.

## Dubbi

- Nessuno bloccante. In `receipts.add` e in `effects.request` il parametro `session` è passato a `record_event` come da brief; non ho verificato l'uso dei valori di sessione nei Task successivi (Task 12 e seguenti).

## Fix round 1

**Rilievo (Important):** `offlog.py` cancellava il file spostato anche quando l'import falliva (busy timeout su `BEGIN IMMEDIATE`, data non valida passata dalla regex, `sqlite3.Error` a metà), con perdita di eventi.

**Cosa ho cambiato in `bin/tollgate_core/offlog.py`:**
- Il file viene cancellato solo dopo il commit della transazione, fuori da `db.tx`. In caso di eccezione resta sul disco.
- Reclamo con `rename` su un nome unico `.off.log.<pid>-<hex>` (niente sovrascritture). Gli orfani `.off.log.<pid>[-hex]` di processi morti vengono ripresi all'inizio di ogni `import_log`. Un file di un processo vivo non si tocca. Lo snapshot della cartella è preso prima del reclamo del file vivo, così non viene riletto. Un file reclamato dallo stesso processo in una chiamata fallita è trattato come orfano.
- Righe con data non valida (`clock.parse` solleva `ValueError`) saltate con `try/except` per riga.
- `import_log` solleva `RuntimeError` se `conn.in_transaction`, come `set_phase`.

**Test (TDD):** in `tests/test_offlog.py` ho aggiunto 5 test. Prima della modifica 4 falliscono, come atteso:
```
python3 -B -m unittest tests.test_offlog
ERROR: test_invalid_date_line_is_skipped
FAIL: test_orphan_file_of_dead_process_is_recovered
FAIL: test_refuses_to_run_inside_transaction
FAIL: test_write_error_keeps_file_and_next_call_imports_once
Ran 7 tests ... FAILED (failures=3, errors=1)
```
Dopo la modifica: `tests.test_offlog` 7 OK. Il test sul file di un processo vivo (`test_file_of_live_process_is_not_taken`) passa già prima, come guardia di non regressione.

**Esito:** `tests/run` verde su python3.11 (3.11.16) e python3 (3.13.5), 155 test ciascuno (150 + 5 nuovi), output pulito.

**Commit:** `4975975` tollgate P2: offlog non cancella il file se l'import fallisce (fix round 1)

**Limite residuo:** se `unlink` fallisce dopo il commit (raro), il file resta e un import successivo lo riprende, con un doppio import. Non l'ho gestito, perché richiederebbe un marcatore nel DB.
