# Task 9 — report

## Implementato
- `bin/tollgate_flow/checkpoint.py`: `CAPS`, `stopped_by`, `next_step` (mappa completa di carry C12; `--fix` solo con verdetto `changes` e `review_sha` non nullo), `write_checkpoint` (tmp + `os.replace`, ultime 5 note, note prima e «prossimo passo:» ultima riga; aggiunge anche l'exclude in info/exclude, idempotente).
- `bin/tollgate_core/cli.py`: `status --checkpoint [--note]`; `--note` senza `--checkpoint` è errore di uso; `stopped_by` nel JSON e nel testo; senza DB «nessun lavoro attivo» (`[]` con `--json`) senza creare nulla.
- `bin/tollgate_core/stats.py`: i conteggi globali usano tutti gli eventi (anche con `work` nullo); `phase_hours` resta per lavoro.
- `tests/test_cli.py`: `CliTest` spezzata in `CliBase` + `CliTest`, per non rieseguire i test ereditati in `StatusReadOnlyTest`.

## RED (prima del codice)
Comando: `python3 -B -m unittest tests.test_checkpoint tests.test_cli tests.test_stats`

    ERROR: test_checkpoint (unittest.loader._FailedTest.test_checkpoint)
    FAIL: test_status_reports_stopped_by (tests.test_cli.StatusReadOnlyTest...)
    FAIL: test_status_without_db_creates_nothing (tests.test_cli.StatusReadOnlyTest...)
    FAIL: test_vetoes_without_work_counted (tests.test_stats.GlobalTest...)
    Ran 30 tests ... FAILED (failures=3, errors=1)

## GREEN
Mirati: 26 test OK. `tests/run`: python3.11 937 test OK; python3 (3.13.5) 937 test OK. Nessun `__pycache__`.

## Scostamenti dal piano
Nessuno di sostanza. `write_checkpoint` scrive anche l'exclude, così il checkpoint non sporca il worktree anche se `start` non l'ha fatto (lavori adottati).

## Fix round 1
- `cli.py`: nel ramo `status` il controllo `state.db_path.exists()` viene prima di tutto. Senza DB, `--checkpoint` rifiuta («nessun lavoro attivo per questa cartella...», exit 1) senza creare nulla; `status` semplice resta in sola lettura. Dopo `--checkpoint` il comando fa `return 0` e stampa solo «checkpoint scritto: <percorso>» (niente status completo).
- Test: `test_cli.py::StatusReadOnlyTest::test_checkpoint_without_db_creates_nothing`; `test_note_requires_checkpoint` ora asserisce il messaggio; `test_checkpoint.py::test_cli_checkpoint_prints_only_path` (via bin/tollgate con FlowLab, stdout uguale al solo percorso, nota scritta), `test_cli_checkpoint_outside_work_refused` (fuori dal worktree: exit 1 e messaggio), `test_session_start_injects_checkpoint` verifica che «prossimo passo» sia l'ultima riga del contesto.
- RED (cli.py di HEAD, test nuovi): `python3 -B -m unittest tests.test_checkpoint tests.test_cli` -> FAIL `test_cli_checkpoint_prints_only_path`, FAIL `test_checkpoint_without_db_creates_nothing` (Ran 19, failures=2).
- GREEN: stesso comando, 19 test OK. `tests/run`: python3.11 e python3 (3.13.5), 940 test OK.
