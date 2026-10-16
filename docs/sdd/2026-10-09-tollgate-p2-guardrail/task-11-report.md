# Task 11 — report: sottocomandi `waiver add` e `block open`

**Status:** DONE_WITH_CONCERNS (un punto da confermare, vedi «Dubbi»)
**Commit:** e021f29 — tollgate P2: sottocomandi waiver add e block open

## Implementato

- `bin/tollgate_core/waiver_cli.py` (nuovo):
  - `add_waiver(state, cwd, *, type_, file, pattern, tests, choice, why, cost, now)`: valida tipo (`waivers.TYPES`), presenza di `--test` per `type=test` (C13), file xor pattern; trova il lavoro dal worktree (`sessions.work_for_path` su `git.toplevel`); normalizza `file` (C13); legge `.tollgate/waivers/<N>.toml` con `waivers.parse` se esiste, aggiunge la deroga con `waivers.next_id`, scrive con `waivers.dumps` in file temporaneo + `replace`; registra `waiver_added`. Restituisce l'id.
  - `open_block_cmd(state, cwd, *, type_, reason, now)`: valida il tipo contro `phases.BLOCK_TYPES`, trova il lavoro, chiama `phases.open_block`. Restituisce l'id del blocco.
- `bin/tollgate_core/cli.py`:
  - parser `waiver add <tipo> [<file>] [--pattern G] [--test ID]... --choice --why --cost` e `block open <tipo> --reason`;
  - rami in `main` (prima di `db.open_db`, dentro il `try` esterno, quindi coperti dal `except sqlite3.Error` già presente dopo il Task 10);
  - `phases.TransitionError` aggiunto all'`except (db.DbError, UsageError, ...)`.
- `tests/test_waiver_cli.py` (nuovo): i tre test del brief alla lettera, più tre test C13 e uno per il percorso fuori dal worktree.

## Test ed esiti

**RED** (`python3 -B -m unittest tests.test_waiver_cli -v`, prima dell'implementazione):
```
ImportError: cannot import name 'waiver_cli' from 'tollgate_core' (.../bin/tollgate_core/__init__.py)
FAILED (errors=1)
```

**GREEN** (modulo mirato, dopo l'implementazione):
```
test_add_two_waivers ... ok
test_block_open ... ok
test_errors ... ok
test_file_is_normalized_relative_to_worktree_root ... ok
test_file_outside_worktree_is_rejected ... ok
test_type_test_requires_test_ids ... ok
Ran 6 tests — OK
```

**Suite completa** (`tests/run`, python3.11 e python3.13): `Ran 351 tests ... OK` con entrambi (345 di baseline + 6 nuovi). Output pulito.

**Smoke test del binario** (`bin/tollgate` con `TOLLGATE_STATE` in cartella temporanea con sentinella, lavoro creato da `phases.create_work`):
- `waiver add scope a ...` dal worktree: exit 0, stampa `w-9-1`, file `.tollgate/waivers/9.toml` scritto e rileggibile con `waivers.parse`;
- `waiver add test a ...` senza `--test`: exit 1, `tollgate: una deroga di tipo test richiede almeno un --test ID`;
- `waiver add scope ../x ...`: exit 1, `tollgate: il file è fuori dal worktree: ../x`;
- `block open needs_you --reason ...`: exit 0, stampa l'id del blocco;
- da `/tmp` (fuori da qualsiasi lavoro): exit 1, `tollgate: nessun lavoro attivo in questa cartella: lancialo dal worktree del lavoro`.

## Scostamenti dal brief / dal piano

1. **Normalizzazione di `file` (C13), aggiornata dal ruling del coordinatore (vedi «Fix round 0»):** un `file` relativo si intende relativo alla radice del worktree; uno assoluto si converte in relativo alla radice.
2. **Percorso fuori dal worktree:** rifiutato con `UsageError` («il file è fuori dal worktree»), sia assoluto sia con `..` che esce. Non era nel brief; è la conseguenza della normalizzazione. Test dedicato.
3. **Ordine di validazione:** il controllo `type=test` senza `--test` avviene prima di aprire il DB (come il controllo del tipo). Nessun file viene scritto se la validazione fallisce (testato).
4. **Import di `UsageError`:** `waiver_cli.py` lo importa da `.cli` a livello di modulo, non dentro le funzioni come nel piano. Non c'è ciclo perché `cli.py` importa `waiver_cli` solo dentro `main`.

## Autorevisione

- Completezza rispetto al brief: tutte le firme (`add_waiver`, `open_block_cmd`), parser CLI e rami `main` presenti; `UsageError` su errori d'uso; `sqlite3.Error` coperto dal catch esistente di `main`.
- Riuso: `waivers.parse/dumps/next_id/path_for/TYPES`, `phases.BLOCK_TYPES/open_block`, `sessions.work_for_path`, `git.toplevel`, `events.record_event`. Nessun TOML scritto a mano.
- Nessun `__pycache__` nel repo (`-B`); commit senza `--no-verify` né amend.

## Dubbi

1. ~~Base della normalizzazione~~ — risolto dal ruling del coordinatore: relativo = radice del worktree (vedi «Fix round 0»).
2. `sqlite3.Error` ha un catch in `main` ma nessun test diretto: l'ho verificato leggendo il codice, non con un test che forza l'errore.
3. `block open` consente più blocchi aperti sullo stesso lavoro (la fase resta `blocked`). È il comportamento di `phases.open_block` già esistente, non l'ho modificato.

## Fix round 0 (ruling)

Ruling del coordinatore: un `--file` relativo si intende relativo alla radice del worktree, non alla cartella di lancio. Un percorso assoluto si converte in relativo alla radice. Un percorso fuori dal worktree (assoluto o con `..` che esce) si rifiuta con messaggio in italiano.

Modifiche:
- `bin/tollgate_core/waiver_cli.py`: `_root_relative(file, worktree)` (non riceve più `cwd`). Risolve il file dalla radice, lo rende relativo con `as_posix()`, rifiuta l'uscita dal worktree e il caso `.` (la radice stessa, che non è un file).
- `tests/test_waiver_cli.py`:
  - `test_add_two_waivers` controlla ora il campo salvato: `["src/x.py", "tests/t.py"]`. RED: `['src/src/x.py', 'tests/t.py'] != ['src/x.py', 'tests/t.py']`.
  - `test_relative_file_is_relative_to_worktree_root` (sostituisce `test_file_is_normalized_relative_to_worktree_root`): da `sub/` con `x.py` salva `x.py`, non `sub/x.py`. RED: `['sub/x.py', 'a'] != ['x.py', 'a']`.
  - nuovo `test_absolute_file_inside_worktree_is_made_relative`: percorso assoluto `wt/src/y.py` salvato come `src/y.py`. Nota: questo test passava già con la vecchia logica, perché per i percorsi assoluti `cwd` non conta. È una regressione, non un RED.
  - `test_file_outside_worktree_is_rejected` (esteso): `../fuori.py` e percorso assoluto fuori dal worktree vengono rifiutati con «fuori dal worktree»; il file di deroga non viene creato.

Test ed esiti:
- RED: `python3 -B -m unittest tests.test_waiver_cli`: `FAILED (failures=2)` sui due test sopra.
- GREEN modulo: `Ran 7 tests ... OK`.
- `tests/run`: python3.11 `Ran 352 tests ... OK`; python3.13 `Ran 352 tests ... OK`.
- Commit: d77435d — tollgate P2: waiver file relativo alla radice del worktree (ruling).
