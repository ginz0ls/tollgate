# Task 12 - Minori rinviati del motore

## Implementato
- `phases.bind_session` e `phases.set_level`: `TransitionError("il lavoro è chiuso")` sui lavori `closed`.
- `verify._run_one`: `os.killpg` anche a fine normale (finally), ignorando `ProcessLookupError`.
- `_common.waiver_hint(v)` / `explain(violations)` senza `issue`; chiamanti aggiornati: `commit.py`, `post_bash.py`, `writes.py` (grep: nessun altro).
- `bash_rules._rm_rf`: messaggio con «usa un percorso dentro il worktree, oppure chiedi all'utente di eseguirlo» (carry C15; non suggerisce `rm -r` senza `-f`).

## TDD
RED (3 test nuovi): `TransitionError not raised`; `ProcessLookupError not raised` (il figlio sopravviveva); messaggio senza la frase attesa.
Test: `WorkTest.test_bind_and_set_level_refuse_closed`, `VerifyRunTest.test_background_child_killed_after_success` (uccide solo il PID che ha avviato), `BoundSessionTest.test_rm_rf_outside_message_suggests_alternative`.
GREEN: `tests/run` con python3.11 e python3, 974 test per interprete, OK.

## Scostamenti dal piano
Il test di `rm -rf` controlla la frase di carry C15 invece di «usa rm -r senza -f». `test_bind_and_set_level_refuse_closed` sta in `WorkTest` (non esiste `ClosedWorkTest`).
