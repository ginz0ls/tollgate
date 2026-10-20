# Report Task 2

Status: DONE

## Implementato
- `sessions.cli_session(..., argv=None)`: con `argv` la voce vale solo se `entry["argv"] == argv` e viene tolta dal file (`_consume_signal`, tmp + `os.replace`, `OSError` ignorato); senza `argv` lettura che non consuma (C2). Un argv diverso non consuma la voce.
- `cli_calls`: `_SIGNALLED` e `_COORDINATOR_ONLY` estesi; il ramo `BashParseError` nega col testo della decisione 2 (senza nome di sottocomando).
- `checks/acts.py`: `abandon` ha `work = None`.
- `report.MAX_SCAN_CHARS = 65536`, `MAX_DECODES = 500`, `json_candidates` limitato alla coda.
- `git.CACHE_DIRS` e salto in `fingerprint` per qualunque segmento del percorso.
- `start.start` e `actapply.apply_act` ricevono `argv` (parola chiave); `cli.main` passa `argv[argv.index(cmd):]` (helper `_hook_argv`). `FlowLab.cli` invariato (già compatibile: scrive il segnale con lo stesso argv), quindi `tests/flowkit.py` non modificato.

## Test
- RED: `python3 -B -m unittest tests.test_sessions tests.test_check_cli_calls tests.test_check_acts tests.test_report tests.test_git` -> 9 failures, 10 errors (nuovi test).
- GREEN: stesso comando -> 81 test OK. `tests/run`: 1007 test OK con Python 3.11.16 e 3.13.5.
- Test aggiunti: i 8 del brief più `test_signal_without_argv_is_not_consumed` e `test_consume_keeps_other_subcommands` (sessions).

## Scostamenti
Nessuno. `tests/flowkit.py` elencato nel brief ma non serviva toccarlo.
