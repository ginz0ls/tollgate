### Task 2: Suite indipendente dal percorso, test instabile, CI del plugin

**Files:**
- Modify: `tests/test_check_cli_calls.py`, `tests/test_prstate.py`, `tests/test_taskcmd.py`, `tests/test_db.py` (solo se l'indagine lo richiede)
- Create: `.github/workflows/ci.yml`, `tests/test_ci_workflow.py`

**Interfaces:**
- Consumes: esiti VC1 (decisione 10); `gate/workflows/PINS` non esiste ancora: `ci.yml` nasce con le versioni maggiori e il Task 3 la fissa.
- Produces: `.github/workflows/ci.yml` con il job `suite` e la matrice `python`.

- [ ] **Step 1: Test** dei tre test della decisione 11: ognuno costruisce il percorso con spazi in una cartella temporanea (`tempfile.mkdtemp(prefix="tollgate sp ")`, ripulita con `addCleanup`) o confronta con `paths.program_command(...)`. Controprova: `PYTHONS=python3 tests/run` lanciato da un clone senza spazi (`git clone . /tmp/tollgate-nospace-<pid>`) passa.
- [ ] **Step 2: Indagine** di `BackupRaceTest.test_concurrent_migration_of_v1_db_with_rows` (decisione 12): 50 corse con la macchina carica (un processo `python3 -c` di calcolo per core, avviati dallo script e fermati per PID); esito nel report; correzione con un test che fallisce prima, se si riproduce.
- [ ] **Step 3: Test** `test_ci_workflow.py`: `test_triggers_and_permissions` (`push`, `pull_request`, `permissions` di primo livello `contents: read`, nessuna altra chiave di permesso); `test_matrix_and_timeout` (3.11 e 3.13, `timeout-minutes: 60`); `test_checkout_path_with_space`; `test_suite_step_uses_tests_run` (`tests/run` con `PYTHONWARNINGS=error::ResourceWarning`, o la forma di ripiego della decisione 10); `test_unclosed_database_fails`; `test_no_expressions_in_run_lines` (stessa regola dei workflow del gate); `test_passes_workflow_rules` (`tollgate_analysis.workflows.problems(text) == []`).
- [ ] **Step 4: Fallimento, scrittura di `ci.yml`, `tests/run`, commit** «tollgate P5: suite indipendente dal percorso, CI del plugin».

---

