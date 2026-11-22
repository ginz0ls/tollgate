# Report Task 2: la storia che non si cancella

## Implementato
- `config.py`: `retention.events_days` predefinito 0 (= mai), nuova `retention.lookups_days` = 180; `_set_key` rifiuta `retention_days`, `events_days`, `lookups_days` fuori da 0..36500 (D5, `ConfigError` con la chiave nel messaggio).
- `events.py`: `ARCHIVE_DIR = "archive"`, `archive_and_prune(conn, state, now, days) -> (n, Path|None)`: lettura, scrittura (`fsutil.write_atomic` via modulo, D8) e cancellazione in un solo `tx` (BEGIN IMMEDIATE); `archive/` con `mkdir(mode=0o700)`; `(0, None)` senza toccare il disco se non c'e' niente. `prune_events` tolta (D21).
- `housekeeping.py`: archivia solo con `events_days > 0`; le letture usano `lookups_days`.
- Test: config (default, negativo e 36501 per le tre chiavi, estremi ammessi), events (archive_then_prune, dir privata, seq mai riusato, scrittura che fallisce, due volte = no-op, niente da archiviare = niente disco, lucchetto tenuto durante la scrittura; il vecchio test della potatura e' sostituito), start (D1: `test_housekeeping` e `test_malformed_sessions...` con `[retention] events_days = 180` e verifica dell'archivio; `test_housekeeping_never_prunes_with_zero`; `test_lookups_use_lookups_days`; `test_prune_events_error...` su `archive_and_prune`).

## TDD
RED: ripristinato `bin/` a HEAD, `python3 -B -m unittest tests.test_config tests.test_events tests.test_start.HousekeepingTest` -> 65 test, FAILED (failures=9, errors=12). GREEN con il codice: 65 test OK.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> due interpreti, 4193 test ciascuno, OK (skipped=13), `exit 0`, nessun «unclosed» (`suite-task-2.log`).

## Scostamenti dal piano
Nessuno oltre alle decisioni D1, D5, D8, D21 del controller.

## Dubbi
Nessuno. `templates/tollgate.toml` non cambia, come da piano.
