### Task 14: Casi lasciati da P3c e rinviati del percorso L2

**Files:**
- Modify: `bin/tollgate_flow/audit.py` (casi (b), m-2, m-4, righe 16 e 29), `bin/tollgate_core/audits.py` (`open_round(min_number=)`), `bin/tollgate_flow/l2acts.py` (m-4), `bin/tollgate_checks/audit_round.py` (riga 19)
- Test: `tests/test_audit_prepare.py`, `tests/test_audits.py`, `tests/test_l2acts.py`, `tests/test_check_audit_round.py`, `tests/test_criteria_p3c.py`, `tests/test_actapply.py`

**Interfaces:**
- Consumes: `l2tree.spec_approval` con il caso (a) (Task 3).
- Produces: `audits.open_round` con la firma attuale più il parametro per parola chiave `min_number: int = 1` (il numero del giro è `max(numero dal DB, min_number)`); `audits.open_round_row` uguale; `audit.prepare` passa `min_number`.

- [ ] **Step 1: Test** `test_audit_prepare.py`: `test_approval_with_plan_adversary_off_and_spec_changed` (caso (b): rifiuto con «/tollgate:reopen spec», uguale ad `approve plan`; `peek` dice lo stesso); `test_numbering_after_lost_db` (caso m-2: `plan-adversarial-1.md` e `-2.md` committati, DB nuovo → il giro aperto è il 3); `test_registered_path_missing_named` (m-4); `test_backtick_path_refused` (riga 16); `test_peek_needs_confirm_says_confirm` (riga 29).
- [ ] **Step 2: Test** `test_check_audit_round.py::test_unreadable_spec_adds_major` (riga 19); `test_criteria_p3c.py::test_plan_cap_chain_to_approve_plan` (riga 22: due giri del piano non puliti → `needs_you`, `resolve` → sospeso, `audit prepare` porta ad `approval`, `approve plan` accettato con `adversarial: suspended`); `test_actapply.py::test_superseded_refusal_leaves_block_and_act` (riga 34: dopo il rifiuto il blocco resta aperto e l'atto è consumato, come dice 8.4); `test_criteria_p3c.py::test_later_slice_with_other_current_approval_end_to_end` (Review Focus 6: `start 12 --spec`, propria approvazione assente, issue 3 superata, issue 9 corrente → `audit prepare` in `plan` apre il giro del piano e `finish check` dà `approvals` vera).
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: casi lasciati da P3c (approvazione corrente, approval con avversario spento, numerazione dopo DB perso) e rinviati del percorso L2».

---

