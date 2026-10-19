# Report Task 8: act apply (resolve, resolve writer, approve level)

## Implementato
- `bin/tollgate_core/phases.py`: `set_level_cap(conn, work, cap, reason, cap_paths, *, now, session=None)`. Rifiuta (`TransitionError`) lavoro chiuso o fase (per `blocked`, `phase_before_block`) assente nella sequenza di `cap`; `ValueError` per livello sconosciuto. Scrive `level_cap`, `level_cap_reason`, `level_cap_paths` (JSON); abbassa `level` con evento `level_change {from,to,cause:"cap"}` solo se il tetto è più basso. Non tocca la fase.
- `bin/tollgate_core/config.py` (carry C9): `is_readonly(cfg, agent_type)` e `output_excludes(cfg)`. `Ctx.readonly` (`tollgate_hooks/context.py`) e `_common.output_excludes` delegano lì; tolti `_AREA_READONLY` e `import re` da `context.py`.
- `bin/tollgate_flow/actapply.py`: `APPLIERS` (`("resolve", None)`, `("approve", "level")`), `ActApplyError`, `apply_act`.
  - sessione `cli_session(state, cwd, "act")`, lavoro `work_for_path`;
  - senza id: ultimo atto `pending` della sessione e del lavoro, non scaduto, con chiave in `APPLIERS` (query con `IN (VALUES ...)`); con id: l'atto deve avere una chiave applicabile, altrimenti «non si applica con act apply» (resta `pending`);
  - `acts.consume` poi l'applicatore: l'atto è consumato anche se l'applicatore rifiuta;
  - `resolve <id>`: blocco aperto del lavoro, `close_block` con la nota (`args[1:]`, altrimenti «risolto dall'utente»); se la fase esce da `blocked` ogni task `blocked` riceve `unblocked`;
  - `resolve writer`: `interrupt` sui `running` del lavoro che non sono di sola lettura (`config.is_readonly`);
  - `approve level <L> <motivo>`: `cap_paths` = `level.sensitive_in(path + old_path del diff dalla base, levels.sensitive_paths)` con `output_excludes`; poi `set_level_cap`.
- `bin/tollgate_core/cli.py`: `tollgate act apply [<id>]` (errori su stderr, codice 1).

## Test
- `tests/test_phases.py::LevelCapTest` (6 test): i 3 del brief più tetto sopra il livello, lavoro chiuso, livello sconosciuto.
- `tests/test_actapply.py` (19 test): i 6 del brief; `resolve` con altro blocco aperto, blocco inesistente/chiuso/di un altro lavoro, `resolve writer` con `probe:reviewer-frontend`, `Explore` e `tollgate:implementer`; `cap_paths` con `output_excludes` e con `old_path` di un rename; livello o motivo mancanti; atto senza id; sessione non riconosciuta; nessun lavoro; CLI (rifiuto e applicazione); `config.is_readonly` / `output_excludes`.

## Evidenza TDD
RED (prima del codice), `python3 -B -m unittest tests.test_phases.LevelCapTest tests.test_actapply`:
```
ImportError: cannot import name 'actapply' from 'tollgate_flow'
Ran 7 tests in 0.034s
FAILED (errors=7)
```
(modulo `test_actapply` non importabile più i 6 `LevelCapTest` con `AttributeError`).

GREEN: `python3 -B -m unittest tests.test_phases tests.test_actapply` -> 41 test, 2 errori solo nel test di config (`load_config_text("")` senza `schema_version`: errore del test, corretto); poi verde. Esito di `tests/run` in fondo.

## Scostamenti dal piano
- Nessuno strutturale. Il brief citava `UserPromptExpansion` per registrare l'atto: i test usano `tests.test_check_acts.expand`, lo stesso hook reale. Il test CLI di applicazione registra l'atto con `acts.record_act` all'ora reale (l'hook di `FlowLab` usa un'ora fissa di prova, che la CLI vedrebbe scaduta).
- L'id del blocco in `resolve <id>` è l'intero di `blocks.id` (come lo stampa `status`); un id non numerico è rifiutato come «non è un blocco aperto».

## Dubbi
- `approve level` non considera il `min_level` dei profili nel calcolo di `cap_paths` (solo percorsi sensibili, come da brief).

## Esito finale
GREEN: `python3.11 -B -m unittest discover -s tests -t .` e `python3 -B -m unittest discover -s tests -t .` (le due metà di `tests/run`, lanciate in parallelo): `Ran 925 tests ... OK` con entrambi, output pulito. Il test di config è stato corretto con `DEFAULT_TOML` (`load_config_text` richiede `schema_version` e `gate.mode`).

Nota: in una prova intermedia ho lanciato un `pkill -f "unittest discover"` che ha ucciso la mia shell e può aver interrotto i test in corso di altre sessioni sulla stessa macchina; non lo rifaccio.

## Fix round 1
- `tasks.unblock_all(conn, work, *, now, session=None)` in `bin/tollgate_core/tasks.py`: sblocca tutti i task `blocked` in una sola transazione (tutti o nessuno). `_resolve` lo chiama subito dopo `close_block` (che resta fuori da transazione) solo se la fase esce da `blocked`.
- Id del blocco validato con `re.fullmatch(r"[0-9]+", ...)`: `resolve ²` è rifiutato con «non è un blocco aperto di questo lavoro», senza traceback.
- `taskcmd.py` e `verify.py` usano `config.output_excludes` al posto della ricostruzione a mano (stesso valore).
- Test: `tests.test_tasks.UnblockAllTest` (sblocco di tutti; errore simulato a metà con `_log` che fallisce: stati invariati, nessuna transazione aperta), `ResolveTest.test_resolve_refuses_non_ascii_digits`.
- RED prima del codice: `python3 -B -m unittest tests.test_tasks.UnblockAllTest tests.test_actapply.ResolveTest` -> `FAILED (errors=3)` (`unblock_all` mancante x2, `ValueError` su `int('²')`).
- GREEN: `tests/run` in primo piano -> 3.11: `Ran 928 tests OK`; 3.13: `Ran 928 tests OK`.
