# Report Task 6: le fermate dagli hook di AskUserQuestion

Commit 86d5b7b. Status: DONE.

## Implementato
- `bin/tollgate_checks/stops.py` (nuovo): `CHECK` con `pre_question`/`post_question`, `STOP_TEXT_MAX=300`, `MAX_QUESTIONS=4`, `MAX_OPTIONS=4`; `stop_asked` e `stop_answered` come da decisione 4; legge da `event.raw` (D16), tollerante a ogni forma; mai deny né inject; senza domande leggibili nessun evento; `tool_use_id` nullo se assente; `work` da `governing_work`.
- `model.INPUT_EVENTS` (non `CONTROL_EVENTS`), `adapter._PRE`/`_POST` e ramo `PostToolUseFailure`; matcher dei tre hook in `hooks.json`.
- `hooks/run`: `CONTROL=no` per `PreToolUse` di `AskUserQuestion`, dopo la definizione di `json_str` (serve la funzione) e dopo `INPUT="$(cat)"`.
- `runner`: `_asks_user` (regex sulla prima occorrenza di `"tool_name"`), `control` calcolato in testa a `run_hook`; dopo `to_event` vale `event.kind in CONTROL_EVENTS`.
- `session.py`: registra `session_start` con `work` e `data={"source": ...}`.

## Test
- RED: `python3 -B -m unittest tests.test_check_stops tests.test_check_session tests.test_manifest tests.test_wrapper tests.test_hook_engine`: 10 fallimenti e 3 errori (log: `task-6-red.log`).
- GREEN: stesso comando, 148 test OK.
- Suite completa con `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 4284 test OK (skipped=13), python3.13 4284 OK (skipped=11), `exit 0` (`suite-task-6.log`).
- Test nuovi: tutti quelli del brief, più il caso runner con JSON troncato, `_Timeout` ed errore generico (mock di `_off_active`), `test_session_start_without_source`, `test_stop_event_without_work`.

## Scostamenti
Nessuno rispetto al piano. Nota: nel wrapper il blocco `CONTROL=no` sta dopo `json_str`, non subito dopo `INPUT=` (la funzione non è ancora definita lì).

## Dubbi
Nessuno. Un'uscita 2 del programma su AskUserQuestion passa ancora com'è dal wrapper (come da decisione 4); il runner non la produce mai per quel caso.
