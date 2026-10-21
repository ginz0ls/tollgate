### Task 11: Rinviati di P3b in core, analisi e hook

**Files:**
- Modify: `bin/tollgate_core/config.py` (riga 21), `bin/tollgate_checks/task_verdict.py`, `bin/tollgate_flow/taskcmd.py`, `bin/tollgate_checks/post_bash.py`, `bin/tollgate_core/git.py` (riga 23), `bin/tollgate_analysis/verdicts.py` (riga 25), `bin/tollgate_flow/finishcheck.py` (riga 32), `bin/tollgate_core/violations.py`, `bin/tollgate_hooks/apply.py` e `bin/tollgate_flow/finalreview.py` (righe 38, 39)
- Test: `tests/test_cli.py`, `tests/test_config.py`, `tests/test_check_task_verdict.py`, `tests/test_verdicts.py`, `tests/test_profiles.py`, `tests/test_check_final_review.py`, `tests/test_finishcheck.py`

**Interfaces:**
- Produces in `git.py`: `range_base(repo, first_commit: str) -> str` (`resolve_ref(<c>^)` o l'albero vuoto), usata da `taskcmd._range`, `task_verdict._task_files` e `post_bash` (riga 23).
- Produces in `violations.py` (`tollgate_core`, perché né `tollgate_hooks` né `tollgate_checks` importano `tollgate_flow`): `active_profile_names(cfg, wt, work) -> list[str]` (profili attivi sul diff del lavoro, con il ripiego `default_ref` per la base), usata da `finalreview` e da `apply._final_rules` (riga 38).

Ogni riga del triage, con il suo test (righe di `docs/sdd/2026-10-19-tollgate-p3b-chiusura/deferred-minors.md`):

- [ ] **Step 1 (riga 5):** `test_cli.py::ArgvSignalTest`: `test_second_start_without_new_signal_refused` (stessa voce consumata) e `test_level_option_in_argv_matches` (`start 7 --level L1` col segnale `["start", "7", "--level", "L1"]` → accettato), con `FlowLab` e `hooks/run`.
- [ ] **Step 2 (riga 21):** `config.py` usa `re.fullmatch`; `test_config.py::ProfileNamesTest::test_trailing_newline_name_falls_back`.
- [ ] **Step 3 (righe 22, 23):** `test_check_task_verdict.py::TaskFilesTest`: profilo attivato solo da `paths` sul diff del task (regole `[blocca]` di quel profilo applicate) e diff illeggibile (nessun profilo, fail-closed come oggi: ogni `R-…` bloccante); `range_base` con un test in `test_git.py`; `import json` nel gruppo della libreria standard.
- [ ] **Step 4 (riga 24):** in `test_verdicts.py` e `test_profiles.py` le classi dopo `unittest.main()` vanno sopra il blocco `if __name__ == "__main__"`; `python3 -B tests/test_verdicts.py` le esegue (stesso numero di test della scoperta).
- [ ] **Step 5 (riga 25):** `parse_verifier_results` riporta «ogni risultato ha un id» una volta sola; `test_verdicts.py::VerifierResultsTest::test_missing_id_problem_once`.
- [ ] **Step 6 (riga 32):** docstring di `finishcheck._own_document`: l'esenzione di `reviews/<N>/` vale a ogni livello (testo, nessun test).
- [ ] **Step 7 (righe 38, 39, 40):** `apply._final_rules` e `finalreview` usano `violations.active_profile_names` (stesso risultato con `default_ref` come ripiego: `test_check_final_review.py::RulesTest::test_rules_with_default_ref_fallback`); `apply._review_report` con `ValueError` registra l'evento `veto` {rule: "final_review", reason} invece di un `return` muto (`test_rejected_report_leaves_trace`); `test_check_final_review.py::ReviewerTest::test_interrupted_reviewer_that_changed_files_tampered`.
- [ ] **Step 8: Verifica** dei moduli toccati e `tests/run`; **commit** «tollgate P3c: rinviati di P3b in core, analisi e hook (righe 5, 21-25, 32, 38-40)».

---

