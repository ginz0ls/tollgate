### Task 8: Verdetti della revisione finale a `SubagentStop`

**Files:**
- Create: `bin/tollgate_checks/final_review.py`
- Modify: `bin/tollgate_checks/_common.py` (`awaiting_final`), `bin/tollgate_checks/subagent_stop.py` (salta i revisori finali in attesa), `bin/tollgate_hooks/apply.py`, `bin/tollgate_flow/checkpoint.py` (`CAPS` con `reviews.CAP_REASON` → «cicli di revisione»)
- Test: `tests/test_check_final_review.py`, `tests/test_checkpoint.py`

**Interfaces:**
- Produces in `_common.py`: `awaiting_final(ctx, row) -> tuple[work, cycle, role] | None`: `role = "reviewer"` se `row["type"]` è tra i `reviewers` dell'ultimo ciclo del lavoro in stadio `review` e non ha ancora riportato; `role = "verifier"` se è `tollgate:finding-verifier` e lo stadio è `verify`. Accetta righe `running` o `interrupted` (decisione 7).
- Produces: modulo `final_review` (evento `subagent_stop`, ordine 15, componente `final_review`):
  - impronta cambiata con `readonly_check` acceso → `tampered_records` (criterio 9);
  - revisore: `parse_final_verdict` valido → `record("review_report", work, cycle, source, outcome, findings, rejected)` più `subagent_finish(done)`; non valido o JSON assente → `subagent_finish(done)` e blocco `needs_you` «verdetto del revisore finale non valido: …» (8.6, criterio 9);
  - verificatore: `parse_verifier_results` valido → `record("finding_verify", work, cycle, results)` più `subagent_finish(done)`; non valido → `needs_you`;
  - messaggio da `last_assistant_message` o da `subagents.report` (auto mode, criterio 9).
- Produces in `apply.py`: `review_report` chiama `reviews.add_report` con `blocking_rules` e `known_rules` dei profili attivi e, se lo stadio diventa `verify` senza rilievi da verificare, `reviews.close_cycle`; `finding_verify` chiama `reviews.apply_verification` e, a zero rilievi senza esito, `close_cycle`. `apply.OPS` passa a 27 voci.

- [ ] **Step 1: Test** `test_check_final_review.py` (`hookkit.Lab` in `review` con un ciclo aperto):
  - `test_valid_verdict_registers_findings_and_moves_to_verify`;
  - `test_verdict_without_code_needs_you` (criterio 9);
  - `test_malformed_json_needs_you` (criterio 9);
  - `test_reviewer_that_changed_files_tampered` (criterio 9);
  - `test_handback_report_used_in_auto_mode` (criterio 9);
  - `test_stale_interrupted_reviewer_verdict_counts` (Review Focus 3);
  - `test_verifier_confirms_and_closes_cycle_needs_fix` (fase `execution`; criterio 26);
  - `test_finding_without_rule_rejected_not_sent_to_verifier` (criterio 40);
  - `test_specialist_findings_go_to_same_verifier` (L2; criterio 38);
  - `test_task_reviewer_path_unchanged` (un `tollgate:task-reviewer` in attesa resta di `task_verdict`).
- [ ] **Step 2: Test** `test_checkpoint.py::test_stopped_by_review_cycles` (`status` dice «tetto: cicli di revisione»).
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: verdetti del revisore finale e del verificatore, chiusura del ciclo».

---

