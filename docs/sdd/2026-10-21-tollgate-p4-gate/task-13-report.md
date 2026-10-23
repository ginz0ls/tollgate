# Task 13 — report

Commit: `c63f8a0` «tollgate P4: finish check usa il calcolo del gate; campi nuovi del blocco; marcatore letto da --from-gate».
Stato: DONE_WITH_CONCERNS (vedi Dubbi).

## Implementato

- `finishcheck._check`: dopo `verify.run_gate` costruisce `GateInputs(where="local")` con `_gate_inputs(state, conn, work, cfg, wt, sha, run, *, now, environ, warnings=None)` e chiama `evaluate.evaluate`. `guard_scope` = nessuna voce rossa della famiglia `diff`; `must_have` = famiglia `must_have` (solo L1/L2); `approvals` = famiglia `l2` senza rossi e senza `approval_stale` (solo L2, decisione 10, rilievo I-4). Verde = DoD verde e `ev.red` vuoto. Le voci rosse delle altre famiglie (livello, file di tollgate, comandi) si stampano `rosso: ...`; quelle di `attenzione` `da leggere: ...` o `informative: ...`. `finish_report` = `{"items", "manual", "gate": {"red", "attention"}}`; `_saved` ristampa le chiavi di `attenzione` del report. Firma, codici e `CheckResult` invariati. Spariti `_approved_spec_blob`, `_must_have`, `_approvals` (il gate calcola spec approvata, scope, must-have e approvazioni).
- `_gate_inputs`: configurazione della base, blocco = `parse(render(build(openpr.facts(...))))` (import nella funzione), comandi dalle ricevute di questa esecuzione (`receipts.latest`, con i JUnit di `run.junits`), issue da `openpr.issue_labels` (D17d, funzione pubblica; senza etichette `issue=None` e l'avviso va in `lines`), `waiver_text` dalla testa.
- `openpr.facts`: `findings[].blocking`, `tasks_over` (righe `size.task_lines` dal primo all'ultimo commit del task, oltre `task_lines_warn`, `size_reason` = ultimo non nullo tra gli eventi `subagent_stop` del task), `skills_absent` (ultimo evento per task). `openpr.issue_labels` pubblica (era `_labels`).
- `events.EVENT_TYPES` + `skills_absent`; `taskcmd` lo registra quando toglie skill assenti.
- `subagents.finish(..., size_reason=None)` → evento `subagent_stop` con `size_reason` (sempre presente, `None` se manca); `apply` (`subagent_finish`) e `subagent_stop` (`_size_reason`, tagliato a 500) lo passano.
- `fixtask._gate`: solo commenti con `author.login` in `ghcli.BOT_LOGINS` e prefisso `GATE_MARKER`; lo SHA è `comment.marker_sha` del commento scelto, `source = gate:<sha del marcatore>`; senza SHA rifiuto «commento del gate senza SHA».

## Test (TDD)

RED (prima del codice), `python3.11 -B -m unittest tests.test_check_subagent_stop tests.test_subagents tests.test_taskcmd tests.test_prblock tests.test_fixtask tests.test_openpr tests.test_finishcheck tests.test_criteria_p4`:
`Ran 219 tests ... FAILED (failures=16, errors=8)`. Errori per il motivo atteso: `KeyError: 'size_reason'`, `TypeError: finish() got an unexpected keyword argument 'size_reason'`, `ValueError: tipo di evento sconosciuto: skills_absent`, e `ValueError: not enough values to unpack (expected 1, got 0)` negli `AgreementTest` (`evaluate` mai chiamato da `finish check`). Fallimenti: i test nuovi di `GateFamiliesTest` (livello, file di tollgate, attenzione, avviso issue, approvazione superata, contratto con `gate`), `FromGateTest` (marcatore, autore, SHA), `test_facts_keys_match_block_fields`, `test_absent_skills_recorded_as_event`.

GREEN (stessi moduli, dopo il codice): `Ran 219 tests ... OK` (un solo test esistente da riscrivere, vedi sotto).
Suite completa: `PATH=<trappola gh>:$PATH tests/run` → python3.11 `Ran 2308 tests ... OK`, python3 (3.13.5) `Ran 2308 tests ... OK`, exit 0. Con un `gh` trappola davanti nel `PATH` (scrive un file se invocato): nessuna invocazione, nessun `gh` vero.

Test nuovi: `test_finishcheck.GateFamiliesTest` (`test_contract_unchanged`, `test_level_below_minimum_is_red`, `test_level_cap_is_attention_not_red`, `test_tollgate_file_changed_is_red`, `test_attention_printed_in_groups`, `test_issue_unreadable_warns_and_continues`, `test_stale_approval_still_fails_dod_locally`); `test_check_subagent_stop::test_size_reason_in_event` (+ `..._carries_null`); `test_subagents::test_finish_records_size_reason_in_event`; `test_taskcmd::test_absent_skills_recorded_as_event`; `test_openpr::test_block_new_fields`, `test_tasks_over_only_above_warn_and_without_commits_skipped`; `test_prblock::test_fields_order_with_new_fields` (e `facts()` con i due campi); `test_fixtask` (`test_from_gate_uses_marker_sha_and_bot_author`, `test_marker_without_sha_refused`, `..._accepts_both_bot_logins`, `test_comment_by_other_author_only_is_refused`; i test esistenti usano commenti del bot con marcatore e SHA); `test_criteria_p4.py` (`AgreementTest`: `test_finish_check_and_gate_agree`, `test_plan_change_is_the_only_difference`; `BlockFeedsGateTest.test_open_pr_block_feeds_gate`).

## Scostamenti dal piano / dal brief

1. `test_openpr.py::test_facts_keys_match_block_fields` torna al confronto esatto (`set(data) == set(prblock.FIELDS)`).
2. `test_level_minimum_from_issue_labels` riscritto (D11): con l'etichetta `security` fin dall'inizio `finish check` ora è rosso (livello L1 sotto il minimo L2, decisione 20, costo dichiarato); l'etichetta arriva dopo `finish check`, prima di `open-pr`.
3. I test che chiamano `finishcheck.check` direttamente patchano `os.environ` con il `gh` finto (`FinishCheckCase.lab`): `finish check` ora legge l'issue con `gh`, e `ghcli` legge `TOLLGATE_GH` da `os.environ`, non da `environ`.
4. `_gate_inputs` ha un parametro opzionale in più (`warnings`), dopo gli argomenti del brief: serve a portare l'avviso sulle etichette in `lines` senza cambiare il tipo di ritorno.
5. `AgreementTest` osserva l'`Evaluation` locale intercettando `evaluate.evaluate` (in-process, sullo stesso banco) e lancia anche il programma vero (`fl.cli("finish", "check")`) per uscita e righe: le chiavi rosse non sono nell'uscita del programma, e `CheckResult` non può cambiare.

## Dubbi

- `IssueFacts(number, "open", labels)` in locale: lo stato dell'issue non si legge (la funzione per le etichette dà solo le etichette, D17d). Conta solo per `waiver_issue` (deroghe di un'issue chiusa): in locale non si controlla.
- Il parametro `environ` di `_gate_inputs` è nella firma del brief ma non serve (`gh` legge l'ambiente del processo).
- `_tasks_over` salta (senza errore) un task i cui commit non sono più nella storia (sync/rebase): il campo è informativo e un errore bloccherebbe `finish check`.
- Per i dettagli di `approvals` si usano le prime righe (al più 5 per voce) del dato di `l2_missing` e `approval_stale`: nel caso `approval_stale` il dato contiene anche i diff dei documenti, quindi con molte righe di problema i diff possono entrare nel dettaglio.
- Output di `tests/run`: nella corsa con python3 compare una riga di `guard.py` («guard: la PR è avanzata dopo l'evento…»), stampata da un test dei Task 9/10, non toccato qui.

## File cambiati

`bin/tollgate_checks/subagent_stop.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/subagents.py`, `bin/tollgate_flow/{finishcheck,fixtask,openpr,taskcmd}.py`, `bin/tollgate_hooks/apply.py`; test: `tests/test_{check_subagent_stop,subagents,taskcmd,prblock,fixtask,openpr,finishcheck}.py`, `tests/test_criteria_p4.py` (nuovo). `prblock.py` non è stato toccato (aveva già `FIELDS` e `DEFAULTS` dal Task 4).
