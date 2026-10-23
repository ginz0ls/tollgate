# Task 4 — report

## Implementato
- `bin/tollgate_gate/model.py`: `CommandResult`, `PrFacts`, `IssueFacts`, `GateInputs`, `Item`, `Evaluation` (`verdict_state`, `attention_state`), costanti `GITHUB`, `LOCAL`, `BASE_FROM_CACHE`, `BASE_FROM_RUN`.
- `bin/tollgate_gate/attention.py`: `GROUPS` (decisione 7 più `task_over_max` info), `READ`, `INFO`, `group`.
- `bin/tollgate_gate/evaluate.py`: `Context` (fatti derivati, una volta) e `FAMILIES = (components_off, commands, base_ids, diff, must_have)`. Il Task 5 aggiunge funzioni `(ctx, ev)` all'elenco e proprietà a `Context`, senza toccare le mie.
- `tollgate_core.git.object_in_history` (D17e, `--find-object`, passa da `_check_ref`).
- `prblock.FIELDS` + `tasks_over`, `skills_absent`; `prblock.DEFAULTS` (liste vuote se mancano nei fatti); `blocking` nei rilievi passa invariato.
- `tests/gatekit.py` (`GateLab`: `inputs`, `block`, `junit`, `commit`, `delete`, `with_pr`), `tests/test_gate_evaluate.py` (55 test), test in `test_git.py` e `test_prblock.py`; `test_openpr.py::test_facts_keys_match_block_fields` ora ammette i campi di `prblock.DEFAULTS` (il Task 13 li riempie e può tornare a un confronto esatto).

## Scelte da rivedere
- Stato di un comando = il peggiore tra quello dichiarato e quello ricalcolato da uscita, report e JUnit (`receipt_state`), così `|| true` con un fallito è rosso anche se `state` dice green. `unverified` resta quello dichiarato.
- `commands` o `base_ids` `None`: su GitHub è `errors` (fail-closed), in locale la famiglia si salta. `base_ids` è letto solo per i comandi richiesti dal diff (profili attivi) e solo se il risultato ha un JUnit.
- `base_path` (D6): oltre alla regola del brief toglie i segmenti finali con iniziale maiuscola (`tests.test_x.TestFoo` → `tests/test_x.py`), altrimenti una deroga `file` non coprirebbe mai i test di classe.
- Chiavi delle voci rosse: `command_red|empty|uncounted|unverified|missing`, `base_id_missing`, `plan_sha_absent`, `plan_absent`, `must_have_missing|failed`, più `Violation.kind` per il diff (`out_of_scope`, `test_deleted`, …). Percorsi, identificativi e diff stanno solo in `Item.data`.
- Deroghe: valide solo con issue valida (decisione 8: aperta, `Closes #N` e blocco coerenti, `issue` del file uguale), e con una PR solo se `branch` è il ramo della PR. Scope non sensibile entro la seconda → `waiver_scope`; oltre, o su file sensibile → `waiver_scope_over_two`; pattern → `waiver_pattern`.
- Ho prodotto già qui `components_off` (generico, tutte le chiavi `false`) perché lo step 2 del brief lo cita; il Task 5 aggiunge solo `audit_*` e il resto. Ho prodotto anche `base_failing_on_head` e `allow_no_tests`. `ci_waived_workflow`, `review_unverified` restano non prodotti: da mettere nell'insieme delle eccezioni di `test_every_group_key_is_produced` (D13 del Task 5) o produrre lì.
- L0: senza `plan_sha` e con diff oltre le soglie (`level.diff_level` != L0) → `plan_absent`. Il giudizio livello dichiarato/minimo resta al Task 5.
- Scope e must-have usano il piano alla versione `plan_sha` (non quello in testa); il diff del piano cambiato (max 200 righe) è in `plan_changed.data`.

## TDD
Ordine non ideale: ho scritto `evaluate` prima dei test. RED verificato dopo, sostituendo `evaluate.py` con uno stub che restituisce `Evaluation()`: `python3 -B -m unittest tests.test_gate_evaluate` → `Ran 55 tests ... FAILED (failures=54, errors=3)`. Ripristinato il codice: un solo fallimento, un errore del mio test (prendeva la voce sbagliata), corretto → `Ran 55 tests ... OK`. I test di `git.object_in_history` e di `prblock` sono stati scritti insieme al codice, senza un RED separato.

## Verifica
`tests/run`: python3.11 `Ran 1884 tests ... OK`; python3 (3.13.5) `Ran 1884 tests ... OK`. Nessun `__pycache__`.

## Dubbi
- `GateLab` non imposta una HOME temporanea: non lancia né `claude` né `gh`, usa solo `git` con `-c` per identità.
- `Context.is_work` in locale senza PR vale `block is not None`: il Task 13 deve passare sempre il blocco.

## Fix round 1
- I-1: `plan_change_is_attention=ctx.is_github` e `plan_changed` prodotta solo su GitHub (`evaluate.py`). In locale il piano cambiato è una violazione di scope (anche per il file del piano) e non c'è `plan_changed`. Test nuovo: `DiffTest.test_plan_changed_is_scope_violation_in_local`.
- I-2: i `setup` si cercano per nome nella configurazione (`setup` e `profile:<p>:setup` con `<p>` tra i profili del predefinito), mai iterando sui nomi dell'artefatto; i nomi sconosciuti si ignorano. I nomi dei comandi richiesti nel testo vengono da `gate_commands`, cioè dalla configurazione. Test: `test_setup_red_is_a_red_command` ora usa `PROFILE_TOML`; nuovo `test_artifact_names_never_reach_item_text` (tre nomi ostili, nessuno in `Item.text`).
- RED: con il codice precedente `python3 -B -m unittest tests.test_gate_evaluate` → `Ran 57 tests ... FAILED (failures=3)` (i due `setup` e il caso locale). GREEN dopo la correzione: `Ran 57 tests ... OK`.
- `tests/run`: python3.11 `Ran 1888 tests ... OK`; python3 (3.13.5) `Ran 1888 tests ... OK`.
