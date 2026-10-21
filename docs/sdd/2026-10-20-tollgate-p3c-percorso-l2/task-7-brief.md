### Task 7: `approve spec`, `approve plan` e sospensioni da `resolve`

**Files:**
- Create: `bin/tollgate_flow/l2acts.py`
- Modify: `bin/tollgate_flow/actapply.py` (voci di `APPLIERS`, `_resolve` sui tetti dell'audit, testo di `_pick`), `bin/tollgate_core/violations.py` (`locked_docs`, decisione 19)
- Test: `tests/test_l2acts.py`, `tests/test_check_common.py`

**Interfaces:**
- Consumes: `audit.adversarial_ok` (Task 5), `audits.*`, `auditrules.is_clean`, `specdoc.slices`, `specdoc.slice_titles`, `approvals.render_approval`, `approvals.locate_spec_approval`, `scope.register_plan`, `plan.check_plan`, `phases.set_phase` con le cause della decisione 11.
- Produces in `l2acts.py` (firma degli applicatori di P3a: `(conn, state, work, act, args, now, session) -> str`, i rifiuti sollevano `l2acts.Refused(Exception)`, che `actapply.apply_act` converte in `ActApplyError`; `l2acts` non importa `actapply`):
  - `approve_spec(...)` (decisione 9);
  - `approve_plan(...)` (decisione 10);
  - `suspend_on_resolve(conn, work, block_reason: str, *, now) -> str | None` (decisione 7: restituisce l'etichetta della sospensione o `None`). Gira prima di `close_block`, in una transazione sua: se il processo muore tra le due, il blocco resta aperto e un nuovo `resolve` riscrive la stessa sospensione (idempotente).
- Produces in `actapply.APPLIERS`: `("approve", "spec")`, `("approve", "plan")`; `_resolve` chiama `suspend_on_resolve` prima di chiudere il blocco e aggiunge l'etichetta al messaggio; il messaggio di `_pick` senza atto elenca anche `spec`, `plan` e `reopen`.
- Produces in `violations.locked_docs`: la spec bloccata con l'approvazione trovata da `locate_spec_approval` sui file del worktree (decisione 19).

- [ ] **Step 1: Test** `test_l2acts.py::ApproveSpecTest` (`FlowLab` L2, spec scritta, giri simulati con `report_round`):
  - `test_refused_after_dirty_round_accepted_after_clean` (criterio 24);
  - `test_cap_resolve_suspended_then_approve` (criterio 24 e Review Focus 6: quarto giro con `major` → blocco, fase `blocked`, `audit prepare` e `approve spec 1` rifiutano; `resolve` → «avversariale sospeso», fase `spec_audit`; `audit prepare` → «approve spec»; `approve spec 1` → `adversarial: suspended` nel file);
  - `test_suspended_round_then_dirty_round_reblocks` (Review Focus 3);
  - `test_wrong_slice_count_refused` (criterio 24: `approve spec 1` su tre fette → rifiuto con «3»);
  - `test_three_slices_refused_until_lens_closed_or_suspended` (criterio 24);
  - `test_spec_changed_after_last_round_refused` (criterio 24);
  - `test_reopen_without_changes_then_approve_again` (dopo `reopen spec` senza modifiche alla spec l'ultimo giro avversariale sta ancora sul blob: `approve spec` accettato; i giri del piano non contano);
  - `test_open_round_refuses_approve`;
  - `test_adversary_off_lens_closed_then_spec_changed_refused` (tre fette, `spec_adversary = false`, audit a lenti chiuso, spec corretta dopo l'ultimo ciclo → `approve spec 3` rifiutato, `audit prepare` lancia un ciclo di conferma; dopo il ciclo `approve spec 3` accettato);
  - `test_adversary_off_lens_suspended_then_spec_changed` (stesso caso con l'audit sospeso al tetto: ciclo di conferma senza nuovo blocco, poi `approve spec 3` con `lens: suspended`);
  - `test_spec_audit_off_three_slices_accepted` (criterio 35: `lens: off`);
  - `test_spec_adversary_off_accepted_without_rounds` (criterio 18);
  - `test_writes_file_and_moves_to_plan` (`parse_approval` ha `kind`, `path`, `sha` = blob, `slices`, `act_id`; fase `plan`, causa `approve_spec`);
  - `test_three_slices_propose_issues_and_start_spec`.
- [ ] **Step 2: Test** `test_l2acts.py::ApprovePlanTest`:
  - `test_plan_sha_is_the_approved_version` (criterio 37: piano corretto dopo un giro avversariale non pulito, nuovo giro pulito, `approve plan` → `plan_sha` = blob approvato, scope e task registrati, `plan-approval.md` con `spec_sha`, fase `execution`, causa `approve_plan`);
  - `test_refused_outside_approval`;
  - `test_refused_when_spec_changed_after_approval`;
  - `test_refused_when_last_plan_round_on_other_spec_sha`;
  - `test_plan_adversary_off` (criterio 18);
  - `test_repeat_after_interruption_does_not_register_twice`;
  - `test_plan_approval_committable_in_execution` (Review Focus 4: dopo `approve plan`, `git add` di `plan-approval.md` e `git commit` dal coordinatore attraverso `PreToolUse Bash` → ammessi; poi un commit dell'implementatore su un file dello scope → ammesso).
- [ ] **Step 3: Test** `test_check_common.py::LockedDocsTest::test_spec_locked_by_real_approve_spec` (criterio 24 e 37: dopo `approve spec` reale, `PreToolUse Edit` sulla spec in `plan` → `deny`; su `spec-approval.md` → `deny`).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: approve spec, approve plan, sospensioni dei tetti dell'audit».

---

