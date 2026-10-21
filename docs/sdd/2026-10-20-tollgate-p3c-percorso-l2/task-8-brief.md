### Task 8: `reopen spec|plan`

**Files:**
- Modify: `bin/tollgate_flow/l2acts.py` (`reopen`), `bin/tollgate_flow/actapply.py` (voci `("reopen", "spec")`, `("reopen", "plan")`)
- Test: `tests/test_l2acts.py`

**Interfaces:**
- Consumes: `scope.reset_plan`, `phases.set_phase(..., "reopen_spec"|"reopen_plan")`, `subagents.running`, `config.is_readonly`.
- Produces in `l2acts.py`: `reopen(conn, state, work, act, args, now, session) -> str` (decisione 12).

- [ ] **Step 1: Test** `test_l2acts.py::ReopenTest`:
  - `test_reopen_spec_from_plan_unlocks_and_requires_new_approval` (criterio 37);
  - `test_reopen_needs_reason`;
  - `test_reopen_refused_with_running_task_or_writer`;
  - `test_reopen_plan_l1_from_execution` (fase `plan`, scope tolto, `post_edit` del piano corretto registra di nuovo);
  - `test_reopen_spec_then_new_approval_end_to_end` (Review Focus 1: `approve spec`, commit, `reopen spec`, spec corretta e committata, nuovo giro pulito, `approve spec` → `sha` nuovo nel file, spec bloccata in `plan`; poi piano, giro, `approve plan`, task chiuso, `finish check` → voce `approvals` vera e nessun `out_of_scope`);
  - `test_reopen_plan_then_reapprove_registers_new_scope` (Review Focus 2: L2 in `execution`, `reopen plan`, piano con un file in più, giro pulito, `approve plan` → scope con il file nuovo, task `pending`, `task start 1` legge il nuovo `plan_sha`).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: reopen spec e reopen plan».

---

