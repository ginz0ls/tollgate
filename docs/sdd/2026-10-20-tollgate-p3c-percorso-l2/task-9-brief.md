### Task 9: Fette successive, `approvals` nella DoD, cartelle 18.1, `adopt` di L2

**Files:**
- Modify: `bin/tollgate_flow/start.py` (`spec`), `bin/tollgate_core/cli.py` (`start --spec PERCORSO`), `bin/tollgate_flow/finishcheck.py` (`_approvals` con `check_l2`, `_own_document` con `locate_spec_approval`), `bin/tollgate_flow/openpr.py` (`facts`), `bin/tollgate_flow/adopt.py` (`_gather`, decisione 16)
- Test: `tests/test_start.py`, `tests/test_finishcheck.py`, `tests/test_openpr.py`, `tests/test_adopt.py`, `tests/test_criteria_p3c.py` (classe `LaterSliceTest`). Test esistenti da riscrivere, perché il comportamento cambia per decisione: `tests/test_finishcheck.py` (i test L2 delle approvazioni intorno a `test_l2_approvals_follow_the_files`, che oggi non hanno `spec_sha` né report) e `tests/test_adopt.py` (il caso L2 con piano e senza `plan-approval.md`: la fase attesa passa da `approval` a `plan`, decisione 16).

**Interfaces:**
- Produces in `start.py`: `start(..., spec: str | None = None)` (decisione 14); il riepilogo di un lavoro nuovo con `--spec` dice «spec approvata: <percorso> (approvazione in <cartella>)».
- Produces in `finishcheck.py`: `_approvals(wt, work) -> tuple[bool, str]` calcolato con `approvals.check_l2` sui file di `git.ls_files_at(wt, "HEAD", REVIEWS_DIR)`.
- Produces in `openpr.facts`: `spec_reviews_dir`, `plan_reviews_dir`, `spec_audit` della decisione 15.
- Produces in `adopt.py`: fase L2 della decisione 16.

- [ ] **Step 1: Test** `test_start.py::StartSpecTest`:
  - `test_approved_spec_starts_in_plan` (criterio 24: spec e approvazione dell'issue 3 sul predefinito, `start 9 --spec <percorso>` → L2, fase `plan`, `spec_path`);
  - `test_without_approval_refused` (criterio 24);
  - `test_changed_spec_needs_confirm_then_spec_audit`;
  - `test_bad_path_refused` (assoluto, `..`, fuori da `docs/superpowers/specs/`, assente sul predefinito);
  - `test_spec_ignored_on_resume_with_warning`;
  - `test_cli_passes_spec` (argomento della CLI fino a `start.start`).
- [ ] **Step 2: Test** `test_finishcheck.py::L2ApprovalsTest`: `test_reports_required` (senza `spec-adversarial-*.md` → `approvals` falsa con il problema); `test_complete_l2_is_green`; `test_kind_mismatch_is_false` e `test_must_have_tests_off` (triage 31: con `must_have_tests = false` la voce `must_have` non blocca).
- [ ] **Step 3: Test** `test_openpr.py::L2FactsTest::test_dirs_and_spec_audit_from_located_approval` (lavoro con la propria approvazione → la propria cartella; fetta successiva → cartella dell'issue della prima fetta, `spec_audit` da quell'approvazione).
- [ ] **Step 4: Test** `test_adopt.py::AdoptL2Test`: `test_later_slice_with_plan_approval_goes_execution`, `test_later_slice_without_plan_approval_goes_spec_audit`, `test_plan_without_approval_goes_plan_with_adversary_on` e `test_plan_without_approval_goes_approval_with_adversary_off` (decisione 16).
- [ ] **Step 5: Test** `test_criteria_p3c.py::LaterSliceTest::test_later_slice_end_to_end` (Review Focus 5: issue 3 approvata e unita sul predefinito; `start 9 --spec` attraverso `hooks/run` e `bin/tollgate`; Edit sulla spec → `deny`; piano, giro del piano, `approve plan`; un task chiuso; `finish check` verde con `approvals`; `open-pr` con `spec_reviews_dir` dell'issue 3; DB cancellato e `adopt 9` → fase `execution`).
- [ ] **Step 6: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: start --spec, voce approvals con i report, cartelle 18.1 e adopt delle fette successive».

---

