# Report Task 3: la presa della taglia

Commit: 09b4bbb `tollgate C1: la taglia del lavoro, proposta all'avvio e alla registrazione del piano`.

## Implementato
- `bin/tollgate_analysis/worksize.py` (nuovo): `SIZES`, `LABELS`, `MEDIUM_MIN_TASKS`, `MEDIUM_MIN_AREAS`, `Signals`, `Proposal`, `Preview`, `propose`, `areas`, `preview`, più `holds_user_size` (la regola «la taglia dell'utente resta, tranne davanti al sì alle fette», usata anche da `sizes` per decidere `by`, così `preview` e `decide` non divergono).
- `bin/tollgate_core/sizes.py` (nuovo): `CAUSES`, `decide` (rifiuta `act` e cause sconosciute), `set_by_user`. D12: scrive `size`/`size_by` se cambia la taglia applicata o chi decide.
- Chiamate: `start._create` (step «taglia» nei `steps.run`, riga prima di `prossimo passo:`); `post_edit.decide` (livello prima, poi `_plan(..., new_level)`; record `plan` con `level`, `areas`, `slices`; riga nell'iniezione); `apply` (`_level` decide solo se il livello sale, `_plan` decide dopo `register_plan`); `l2acts.approve_plan` (D10, D19: dentro l'`if`, stessa transazione di `register_plan`, riga aggiunta al messaggio); `adopt` (step «taglia» dopo `create_work`, `_Evidence.spec_own`, `_l2_proofs` ora dà anche `own`, `_register_plan` con D9 e dà la riga). `apply._OPS` resta a 29.
- Nessun `tollgate <sottocomando>` nudo nei messaggi (D17); `BareProgramInMessagesTest` verde.

## Test
- Nuovi: `tests/test_worksize.py` (puri), `tests/test_sizes.py`; aggiunti in `test_start.py` (riga di taglia, L2 medio, ripresa senza secondo evento, errore = registrazione incompleta), `test_check_post_edit.py` (i cinque test del brief più riga iniettata = riga decisa, nessun evento senza salita di livello, tetto che abbassa non decide), `test_l2acts.py` (`test_approve_plan_decides_size`, ripetizione dopo interruzione = un solo evento), `test_adopt.py` (`AdoptSizeTest`: avvio, piano, piano L1 a tre fette resta medio, spec propria a tre fette = sì e `large`, fetta successiva senza `approve_spec`, errore = incompleta).
- RED: i file nuovi non importavano (`ModuleNotFoundError`) prima del codice; i test dei punti di chiamata sono stati scritti dopo il codice (per i call site ho scritto prima il codice e poi i test: scostamento dal TDD stretto, dichiarato).
- GREEN: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> `exit 0`: python3.11 4237 test OK (13 skipped), python3 (3.13.5) 4237 OK (11 skipped), nessun «unclosed». Log: `suite-task-3.log`.
- Il primo giro (`suite-task-3-giro1.log`) aveva 20 fallimenti in `tests.test_b1_scripts.FlowScriptTest`: i test copiano il plugin dai file tracciati e `worksize.py`, ancora non tracciato, mancava nella copia (`ImportError`). Dopo `git add` dei file nuovi sono verdi (nessuna modifica al codice).

## Scostamenti dal piano e decisioni mie
- Nel record `plan` dell'hook l'operazione `plan` di `apply` NON è avvolta in `db.tx`: con `advance=True` `register_plan` chiama `set_phase`, che vuole una connessione senza transazione aperta (RuntimeError verificato). Quindi in `apply` `register_plan` e `decide` sono due transazioni; in `approve_plan` e `adopt` (`advance=False`) sono invece una sola, così una ripetizione dopo un'interruzione non perde la taglia.
- La riga della taglia nell'iniezione del piano sta nella stessa iniezione di «piano registrato…»: `fase execution. taglia: … . Prossimo passo: …`.
- Motivi: `propose` scrive «N fette previste», «livello L2», «piano con N task su M aree» (area al singolare con 1), «ancora nessun piano» per il piccolo senza segnali; in `adopt` la riga mostrata è quella dell'ultima decisione (una sola riga `taglia:`), prima di «gli intenti…» e di `prossimo passo:`.
- Forma 2 della riga (strada con la spec L2): vale per ogni livello diverso da L2 (anche L0, dove non si arriva con un piano).

## Autorevisione
Completezza rispetto a brief e `carry.md` (D9, D10, D12, D17, D19) verificata; nessun extra; Review Focus 3 e 4 coperti (`test_l1_plan_with_three_slices_stays_medium`, `test_plan_after_reopen_does_not_shrink`, `test_reopen_plan_on_pre_c1_work`, `test_pre_c1_work_gets_a_size_without_error`).

## Dubbi
Nessuno bloccante. Il Task 4 userà `sizes.set_by_user` e `decide(..., cause="approve_spec", confirmed=True)`.
