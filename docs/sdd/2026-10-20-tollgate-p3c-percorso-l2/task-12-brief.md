### Task 12: Rinviati di P3b nel flusso e nei test

**Files:**
- Modify: `bin/tollgate_analysis/brief.py` (righe 34, 36, 72), `bin/tollgate_flow/finalreview.py` (34, 36), `bin/tollgate_flow/actapply.py` (49, 50), `bin/tollgate_flow/taskcmd.py` (71), `bin/tollgate_flow/adopt.py` (60, 62)
- Test: `tests/test_brief.py`, `tests/test_finalreview.py`, `tests/test_actapply.py`, `tests/test_taskcmd.py`, `tests/test_sync.py`, `tests/test_adopt.py`, `tests/test_closing.py`, `tests/test_fixtask.py`, `tests/test_criteria_p3b.py`

- [ ] **Step 1 (righe 34, 36):** `FinalBrief` dice, quando `sha` del ciclo e HEAD differiscono per un rebase con lo stesso `patch-id`, «il ciclo è stato aperto su <sha>; HEAD è <head> dopo un rebase senza modifiche di contenuto: rivedi il diff di HEAD»; `issue_file` è `None` se `.tollgate-run/<N>/issue.md` non esiste e il brief non lo nomina. Test in `test_brief.py` e `test_finalreview.py`.
- [ ] **Step 2 (righe 49, 50):** `approve finding` su un rilievo confermato di un ciclo non ultimo chiude il blocco dei cicli se aperto (decisione 25); `recompute_outcome` che solleva `ValueError` (ultimo ciclo `superseded`) diventa un rifiuto con il messaggio, dopo che la decisione è scritta. Test `test_actapply.py::ApproveFindingTest::test_old_cycle_finding_closes_cycles_block` e `test_superseded_last_cycle_is_a_refusal`.
- [ ] **Step 3 (riga 51):** `test_taskcmd.py::FixRoundsTest::test_sixth_round_name_launch_inherit` (dopo `approve rounds 1`: nome `tg-7-t1-r6`, `pending = launch`, `model: inherit` nel brief).
- [ ] **Step 4 (riga 55):** `test_sync.py::SyncEdgeTest`: `test_intent_recorded_before_rebase`; `test_rebase_in_progress_at_start_refused`; `test_ff_only_failure_blocks`; `test_finish_check_red_after_rebase` (il messaggio è il rosso, non il rifiuto, m4).
- [ ] **Step 5 (righe 60, 62):** `adopt` con ramo locale e remoto su punte diverse avvisa «ramo locale e remoto diversi: uso la punta locale <sha>»; `sqlite3.Error` in `acts.consume` dopo `create_work` dà codice 4 «lavoro creato, atto non consumato: …», come `start`. Test in `test_adopt.py`.
- [ ] **Step 6 (riga 67):** `test_closing.py`: `test_cleanup_from_inside_worktree`; `test_cleanup_with_missing_worktree_dir`; `test_start_confirm_closed_pr_with_other_confirmations`.
- [ ] **Step 7 (righe 71, 72, 73):** `taskcmd._fix_files` instrada sui file di tutti i rilievi del ciclo usati per creare il task, senza filtrare per decisione dell'utente; `brief._finding` stampa la gravità effettiva (`reviews.effective_severity` se la riga la ha, altrimenti quella dichiarata) con l'originale tra parentesi se diversa. Test in `test_fixtask.py`: `test_routing_stable_after_dismiss`, `test_brief_shows_effective_severity`, `test_from_findings_rollback_on_error`, `test_l0_refused`, `test_cli_from_gate`, `test_gate_fence_longer_than_any_backtick_run` (asserzione esatta sul recinto).
- [ ] **Step 8 (riga 82):** in `test_criteria_p3b.py` il test del criterio 26 asserisce il codice e la riga «rifiuto:» di `open-pr`, l'helper si chiama `prepare_needs_fix_cycle`, e un test nuovo `test_second_finish_is_new_cycle` porta dal programma vero il ciclo 2 a `ok` e `open-pr` a 0.
- [ ] **Step 9: Verifica, `tests/run`, commit** «tollgate P3c: rinviati di P3b nel flusso e nei test (righe 34-82)».

---

