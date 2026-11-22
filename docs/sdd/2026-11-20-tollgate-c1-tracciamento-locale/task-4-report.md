# Report Task 4: la taglia grande con `approve spec` e l'atto `approve size`

Commit: 7d121f5 "tollgate C1: taglia grande con approve spec e atto approve size". Status: DONE.

## Implementato
- `bin/tollgate_flow/l2acts.py` (`approve_spec`): in un solo `db.tx`, prima di `phases.set_phase` (D10), `UPDATE work_items SET slices` e `sizes.decide(..., Signals(level, n_task_registrati, 0, slices), cause="approve_spec", confirmed=slices > 1)`. La riga della taglia va nell'uscita prima di «Committa ...», fuori dal recinto dei titoli delle fette.
- `bin/tollgate_core/acts.py`: `"size"` in `APPROVE_OBJECTS`. `bin/tollgate_checks/acts.py`: `"size"` in `_TARGET_ARG`.
- `bin/tollgate_flow/actapply.py`: `_approve_size` (parole italiane invertendo `worksize.LABELS`; rifiuto con i tre valori; motivo obbligatorio; poi `sizes.set_by_user`), voce in `APPLIERS`, messaggio di `_pick` aggiornato.
- `skills/approve/SKILL.md` e `docs/uso/comandi.md` insieme (D17): `argument-hint`, descrizione, riga di `size` con esempio, nota sul lavoro grande in `spec`.

## Test
- Nuovi: `test_approve_spec_records_slices_and_large`, `test_approve_spec_single_slice_keeps_size`, `test_approve_spec_on_pre_c1_work` (`tests/test_l2acts.py`); `ApproveSizeTest` con 4 test (atto, verso il basso, valore sconosciuto, senza motivo; l'atto si consuma sempre) in `tests/test_actapply.py`; `test_size_is_target_arg` e `approve size` senza argomento tra i rifiuti in `tests/test_check_acts.py`.
- RED: `python3 -B -m unittest tests.test_check_acts tests.test_actapply.ApproveSizeTest tests.test_l2acts.ApproveSpecTest` -> 4 failures, 4 errors (slices/size nulli, oggetto `size` sconosciuto).
- GREEN mirato: 231 test OK (docs, skill_contract, manifest, check_acts, actapply, l2acts, acts).
- Suite completa: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> python3.11: 4245 test OK (skipped=13); python3 (3.13.5): 4245 test OK (skipped=11); `exit 0`, nessun «unclosed». Log: `suite-task-4.log`.

## Scostamenti dal piano
- Due test esistenti di `approve plan` (`test_approve_plan_decides_size`, `test_size_decided_once_after_an_interrupted_approve_plan`) contavano tutti gli eventi `size_decided`: ora c'e' anche quello di `approve_spec`; li ho adattati a filtrare per causa (`plan`) o ad attendere `["approve_spec", "plan"]`.
- Applicatore e uscita come da D10 (non "dopo `set_phase`" come dice il piano).

## Autorevisione
Completezza rispetto al brief e a carry: ok. Nessun file nuovo, nessun `__pycache__`, file approvati non toccati, strati rispettati (`tollgate_flow` importa `tollgate_core` e `tollgate_analysis`).

## Dubbi
Nessuno. `approve size` non limita la fase: vale in qualunque fase del lavoro (come `approve level`).
