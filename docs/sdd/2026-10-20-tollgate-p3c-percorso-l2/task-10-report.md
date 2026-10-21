# Task 10 - Prossimo passo e tetti dell'audit in `status`

## Implementato
- `bin/tollgate_flow/checkpoint.py`: `next_step` per lavori L2 in `spec_audit`, `plan` (senza task) e `approval` restituisce `audit.peek(conn, item)` (nessuna logica duplicata; il «lancia <programma> audit prepare» arriva da `peek`). Rimosso il testo «arriva con P3c». I lavori L1 in `plan` mantengono il testo di writing-plans.
- `CAPS` ha i quattro prefissi dell'audit (`audits.CAP_REASONS` x3 e `DECLINE_REASON`): «giri avversariali della spec», «giri avversariali del piano», «audit a lenti» (x2). Non in `CAP_PREFIXES`.
- `_cap_step` (D19): per i blocchi riconosciuti da `audits.cap_kind` stampa `audit.STEPS["resolve"]` con `<id>` sostituito dall'id del blocco.
- D18f: `bin/tollgate_checks/post_edit.py` ora dice «Prossimo passo in L2: /tollgate:spec-audit (lancia l'avversario del piano), poi /tollgate:approve plan.»; test in `tests/test_check_post_edit.py::test_l2_plan_only_sets_path`.
- Test (`tests/test_checkpoint.py`, classe `CheckpointL2Case` su `FlowLab(level="L2")`, che committa già `tollgate.toml` nella base): `test_l2_phases_point_to_audit_prepare`, `test_approval_points_to_approve_plan`, `test_audit_caps_in_stopped_by`, `test_audit_cap_step_is_resolve_not_rounds`, `test_steps_use_program_command` (fasi L2). Il vecchio controllo su «P3c» (D10) è tolto dal test L1 e sostituito dai test L2.

## TDD
RED (`python3 -B -m unittest tests.test_checkpoint`, prima del codice): `AssertionError: 'P3c' unexpectedly found in 'fase spec_audit: percorso L2, arriva con P3c'`; `stopped_by` restituiva `[]` invece dei 4 tetti; il passo non conteneva `audit prepare`. 5 fallimenti. Per post_edit: `'/tollgate:spec-audit' not found in ... plan-adversary ...`.
GREEN: `tests.test_checkpoint` + `tests.test_check_post_edit`: 38 OK. `tests/run`: Python 3.11.16 1670 test OK; Python 3.13.5 1670 test OK.

## Scostamenti
- In fase `plan` L2 senza spec registrata `peek` dice «/tollgate:reopen spec» (rifiuto di `prepare`): i test registrano prima la spec con `approve_spec_file`.
- Il test L1 di `test_next_step_in_phases_without_tasks` resta su L1 per `plan`/`execution` (testo L1 invariato); la copertura L2 è nei test nuovi.
