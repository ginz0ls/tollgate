# Task 8 - report: `reopen spec|plan`

## Implementato
- `bin/tollgate_core/subagents.py`: `InUse` e `in_use(conn, work, load_config)`, la regola condivisa di `sync._in_use` (task `running`/`review`, task non `done` con commit, implementatore `running` non di sola lettura; la config si carica solo se c'e' un subagente in corso). D5.
- `bin/tollgate_flow/sync.py`: `_in_use` delega a `subagents.in_use`; i due messaggi sono identici a prima (test di sync invariati e verdi).
- `bin/tollgate_flow/l2acts.py`: `reopen(conn, state, work, act, args, now, session)` (decisione 12). Motivo obbligatorio; `_check_ready` ora accetta piu' fasi (blocked rimanda a `/tollgate:resolve <id>`); `reopen spec` solo L2 da plan/approval/execution; `reopen plan` da approval/execution (L1 e L2; L0 rifiutato da `phases.check_transition`, prima di toccare lo stato); rifiuto con task in corso o con commit non chiusi (anche `pending`) e con implementatore (indica `/tollgate:resolve writer`); giro aperto -> `audits.supersede`; `scope.reset_plan` PRIMA di `set_phase` (se muore in mezzo, un secondo `reopen` riparte); poi fase `spec_audit`/`plan` con causa `reopen_spec`/`reopen_plan`.
- `bin/tollgate_flow/actapply.py`: voci `("reopen", "spec")` e `("reopen", "plan")`.
- Sospensioni dell'audit non toccate (decisione 7).

## Test (`tests/test_l2acts.py::ReopenTest`, 9)
test_reopen_spec_from_plan_unlocks_and_requires_new_approval, test_reopen_spec_from_execution_resets_plan_and_supersedes_open_round, test_reopen_needs_reason, test_reopen_refused_with_running_task_or_writer (task running, task pending con commit, implementatore running; poi dopo `finish` il reopen passa), test_reopen_refused_in_other_phases_levels_and_blocked, test_reopen_spec_refused_in_l1_and_reopen_plan_in_l0, test_reopen_plan_l1_from_execution (post_edit registra di nuovo), test_reopen_spec_then_new_approval_end_to_end, test_reopen_plan_then_reapprove_registers_new_scope.
Atti: `UserPromptExpansion` del banco + `actapply` dalla libreria con `now=fl.now`.
- end_to_end spec: hook `pre_edit` (spec bloccata exit 2 / libera exit 0), `audit prepare` dalla libreria, report via hook `SubagentStop`, `approve` dalla libreria, `finish check` dalla CLI del banco (rc 0, nessun `out_of_scope`, nessun `[no]`, fase `review`). La voce `approvals` di P3b regge lo scenario (spec-approval e plan-approval con sha correnti): nessuna asserzione indebolita; il Task 9 la passa a `check_l2`.
- end_to_end plan: `task start 1` e `task start 2` dalla CLI; il brief del task 2 (esiste solo nel piano nuovo) contiene `docs/uso.md`.

## TDD
RED (`python3 -B -m unittest tests.test_l2acts.ReopenTest`, prima del codice): 5 ERROR + 4 FAIL su 9 (il messaggio era «nessun atto da applicare per questa sessione», perche' `reopen` non era in `APPLIERS`):
ERROR test_reopen_plan_l1_from_execution / test_reopen_plan_then_reapprove_registers_new_scope / test_reopen_spec_from_execution_resets_plan_and_supersedes_open_round / test_reopen_spec_from_plan_unlocks_and_requires_new_approval / test_reopen_spec_then_new_approval_end_to_end; FAIL test_reopen_needs_reason / test_reopen_refused_in_other_phases_levels_and_blocked / test_reopen_refused_with_running_task_or_writer / test_reopen_spec_refused_in_l1_and_reopen_plan_in_l0; `FAILED (failures=4, errors=5)`.
GREEN: stesso comando, `Ran 9 tests ... OK`; `tests.test_l2acts tests.test_sync tests.test_actapply`: 119 test OK.
Suite completa: vedi in fondo.

## Scostamenti dal piano
Nessuno nella sostanza. Il messaggio di reopen in L0 viene da `check_transition` (testo: «reopen plan non vale in L0: ...»).

## Dubbi
- `in_use` sta in `subagents` (non in `tasks`) perche' `subagents` importa `tasks` e la regola unisce le due query.

## Suite completa
`tests/run`: Python 3.11.16 e 3.13.5, 1638 test, OK su entrambi, output pulito.

## Fix round 1
Modifiche (`bin/tollgate_flow/l2acts.py`, `tests/test_l2acts.py`):
1. Messaggio di `reopen` dipendente dal livello: L1 `plan` «correggi il piano: si registra da solo con la prossima modifica (post_edit)», senza `audit prepare`; L2 `plan` «correggi il piano, committalo e riparti da <programma> audit prepare per l'avversario del piano»; `spec` «correggi la spec, committala e riparti da ... audit prepare». Asserito in `test_reopen_plan_l1_from_execution`, `test_reopen_plan_then_reapprove_registers_new_scope` e `test_reopen_spec_from_plan_unlocks_and_requires_new_approval`.
2. `test_reopen_keeps_audit_suspensions` (nuovo, guardia: passava gia' prima, `reopen` non tocca `audit_suspended`).
3. La config si carica solo se serve a `subagents.in_use` (`lambda: _cfg(state, work)`); `test_reopen_loads_config_only_for_a_running_subagent` (nuovo): con `work_config` che solleva `ConfigError`, `reopen` senza subagenti riesce, con un implementatore `running` rifiuta «configurazione non valida».
RED (`python3 -B -m unittest tests.test_l2acts.ReopenTest`): ERROR test_reopen_loads_config_only_for_a_running_subagent; FAIL test_reopen_plan_l1_from_execution; FAIL test_reopen_plan_then_reapprove_registers_new_scope; `Ran 11 tests, FAILED (failures=2, errors=1)`.
GREEN: stesso comando, 11 test OK. Suite: `tests/run` Python 3.11.16 e 3.13.5, 1640 test, OK su entrambi.
