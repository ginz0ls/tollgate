### Task 6: Rinviati del nucleo e del flusso

**Files:**
- Modify: `bin/tollgate_core/{cli,tasks,reviews,intents,audits}.py`, `bin/tollgate_flow/{finishcheck,openpr,actapply,checkpoint}.py`, test omonimi

- [ ] **Step 1: Test** (P1) `test_cli.py::test_status_without_git_is_message_not_traceback` (`current_repo_key` con `git` assente: `PATH` senza `git` → messaggio e uscita 1); `test_cli.py::test_db_restore_interactive_eof_and_ctrl_c` (EOF e `KeyboardInterrupt` a `input()` → «annullato», uscita 1, DB invariato); `test_cli.py::test_db_restore_interactive_confirm_from_cli` (il ramo interattivo dalla CLI, con un pseudo-terminale `pty`).
- [ ] **Step 2: Test** (P3a 163) `test_tasks.py::test_assign_event_carries_implementer_and_pending`.
- [ ] **Step 3: Test** (P3b) `test_reviews.py::test_close_cycle_requires_verify_stage` (10: un ciclo non in `verify` non si chiude `ok`, `ReviewError`); `test_close_cycle_twice_is_idempotent` (11: la seconda chiusura restituisce l'esito senza toccare fase e blocchi); `test_intents.py::test_request_existing_key_other_work_or_action_refused` (13); `test_finishcheck.py::test_corrupt_finish_report_is_message` (27); `test_openpr.py::test_corrupt_json_fields_are_messages` (44); `test_reviews.py::test_approve_finding_reason_in_event` (54); `test_checkpoint.py::test_review_brief_by_task_number` (74); `test_checkpoint.py::test_all_cap_blocks_listed` (76).
- [ ] **Step 4: Test** (P3c 12) `test_audits.py::test_close_round_rejects_bad_outcome_and_counts`.
- [ ] **Step 5: Verifica** di P3b righe 28 e 66 (chiuse: `git.changes` una volta sola in `finishcheck.py`, nessuna regex `_TG` duplicata): `grep` nel report, nessun codice.
- [ ] **Step 6: Fallimento, implementazione, `tests/run`, commit** «tollgate P5: rinviati del nucleo e del flusso (git assente, db restore, eventi, cicli, intenti, JSON, checkpoint)».

---

