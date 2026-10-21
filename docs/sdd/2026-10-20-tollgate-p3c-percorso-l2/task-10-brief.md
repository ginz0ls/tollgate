### Task 10: Prossimo passo e tetti dell'audit in `status`

**Files:**
- Modify: `bin/tollgate_flow/checkpoint.py`
- Test: `tests/test_checkpoint.py`

**Interfaces:**
- Consumes: `audit.peek`, `audits.CAP_REASONS`, `audits.DECLINE_REASON`.
- Produces: `next_step` per `spec_audit`, `plan` di L2 senza task e `approval` (decisione 20); `CAPS` con i tre tetti dell'audit e il rifiuto del costo (non `CAP_PREFIXES`); `_cap_step` dice `audit.STEPS["resolve"]` per quei blocchi.

- [ ] **Step 1: Test** `test_checkpoint.py`: `test_l2_phases_point_to_audit_prepare` (sostituisce il test che cercava «P3c»); `test_approval_points_to_approve_plan`; `test_audit_caps_in_stopped_by` (`status` dice «tetto: giri avversariali della spec»); `test_audit_cap_step_is_resolve_not_rounds` (decisione 20); `test_steps_use_program_command` esteso alle fasi L2.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: prossimo passo nelle fasi L2 e tetti dell'audit».

---

