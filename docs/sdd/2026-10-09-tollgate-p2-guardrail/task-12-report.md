# Report Task 12: motore degli hook

Commit: 0db2c8d "tollgate P2: motore degli hook (adattatore, contesto, registro, runner) e tollgate hook".

## Implementato
- `bin/tollgate_hooks/` (`__init__`, `model`, `adapter`, `context`, `registry`, `apply`, `runner`), `bin/tollgate_checks/__init__.py`, sottocomando `tollgate hook <evento>` in `bin/tollgate_core/cli.py`, `tests/hookkit.py`, `tests/test_hook_engine.py`. Nomi e firme dei «Produces» come da brief.
- Codice del piano preso alla lettera, più le voci di carry.md e i ritocchi sotto.

## Voci di carry.md
- `prompt_submit` (`UserPromptSubmit`): in `INPUT_EVENTS` e `_PLAIN`; informativo. Il runner scarta ogni `deny` su questo evento (lo scrive nel log) e non esce mai con 2; input malformato -> 0.
- `INJECT_MODE`: `context` per SessionStart, UserPromptExpansion, UserPromptSubmit, PreToolUse, PostToolUse, SubagentStart; `SubagentStop` = `log`. `adapter.NO_INJECT_KINDS = {subagent_stop, subagent_handback}`: il runner scrive l'`inject` di questi eventi in `<stato>/hooks.log` (`runner.HOOKS_LOG`) e non lo rende. Il veto di SubagentStop resta uscita 2 + stderr (testato).
- C10: con `session_id` vuoto il segnalino `bound/<session>` è ignorato (e un session_id non sicuro secondo `sessions._SAFE` non forma un percorso).
- C11: `test_malformed_input_missing_fields` asserisce `2`; aggiunto `test_database_error_during_operations` (modulo di prova che alza `sqlite3.DatabaseError` in `decide`: 2 con suggerimento `db restore` per pre_send_message, 0 per post_skill).
- C3: `Ctx.repo` = toplevel del cwd, altrimenti worktree del lavoro; `protected_roots(repo)` riceve quel repo (test su `.git/hooks` e `.git/config` del repo comune).

## Scostamenti dal piano (minimi)
1. `runner`: `tool_input` di un `pre_edit` senza `file_path` -> `_fail` (2, «tool_input privo di file_path», con `touch .../OFF`). Con i moduli finti del piano il 2 veniva solo dal modulo `due` rotto: il Review Focus (2) chiede che sia il motore a rifiutare. Testato con `checks=([], [])`.
2. `runner`: `except sqlite3.Error` (non solo `DatabaseError`) e, nel ciclo dei moduli, `sqlite3.Error` si rilancia invece di diventare «controllo in errore», altrimenti il ramo DB del runner non sarebbe raggiungibile da un modulo. Un `DatabaseError` senza codice di corruzione porta anch'esso il suggerimento `db restore`; un `OperationalError` (locked) no.
3. `ReadDb`, `Ctx`, `registry`, `apply` invariati rispetto al piano.

## TDD
- RED: `python3 -B -m unittest tests.test_hook_engine` con `bin/tollgate_hooks` spostata fuori: `FAILED (errors=1)` (ModuleNotFoundError su `tollgate_hooks`).
- GREEN: `python3 -B -m unittest tests.test_hook_engine` -> `Ran 20 tests ... OK` (poi 21 con `CliHookTest`).
- Suite: `tests/run` -> 373 test OK con python3.11 e python3 (3.13.5), output pulito.
- Test aggiunti oltre al piano: prompt_submit (mapping, mai blocca), inject su subagent_stop/handback nel log, sessione vuota, DatabaseError, `ReadDb` solo SELECT, `protected_roots`, sottocomando `tollgate hook` via subprocess. `test_concurrent_hooks` (4 processi spawn) passa: nessun `database is locked`.

## Fix round 1
Commit 69dde89.
- I1: un controllo non caricato o in errore su un evento non di controllo non produce più `deny`: avviso in `injects` (quindi secondo `INJECT_MODE`/`hooks.log`) e uscita 0. I `deny` deliberati dei moduli restano 2.
- I2: i rifiuti generati dal motore («non caricato», «in errore») portano `_footer` (percorso di `bin/tollgate`, `touch <stato>/OFF`).
- I3: `_off_active` subito dopo `resolve_state`, prima del parsing: con OFF anche un input malformato su PreToolUse esce 0.
- Minor: `registry._validate` richiede eventi `str` (`events: [["x"]]` rompe solo quel modulo); `_Timeout` deriva da `BaseException`; `test_internal_timeout` verifica «scadenza».
- Test nuovi: `test_broken_module_on_informative_events_warns_and_exits_0`, `test_module_error_control_denies_with_footer_informative_warns`, `test_registry_isolates_non_string_events`, `test_timeout_is_not_swallowed_by_module`, `test_off_wins_over_malformed_input`, più asserzioni sul footer.
- Onestà sul TDD: ho scritto prima la correzione e poi i test. Per il RED ho ripristinato `bin/` e rilanciato `python3 -B -m unittest tests.test_hook_engine`: `FAILED (errors=1)` (setUpClass crolla in `registry.load` con `events: [["x"]]`, il che maschera gli altri test). Ripristinata la correzione: 26 test OK.
- Suite: `tests/run` -> 378 test OK su python3.11 e python3.

## Dubbi
- Il «log degli hook» non esisteva: l'ho definito come `hooks.log` nella cartella di stato (riga `timestamp testo`, append, errori di I/O ignorati). Da riconfermare se i Task successivi si aspettano un altro nome/luogo.
- Un `deny` di un modulo su un evento non di controllo non-PreToolUse (es. PostToolUse, via controllo rotto in `registry`) esce ancora 2 come nel piano; l'unica eccezione è `prompt_submit`.
