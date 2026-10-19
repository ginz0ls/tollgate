### Task 12: Minori rinviati del motore

**Files:**
- Modify: `bin/tollgate_core/phases.py`, `bin/tollgate_core/verify.py`, `bin/tollgate_checks/_common.py`, `bin/tollgate_checks/bash_rules.py`
- Test: `tests/test_phases.py`, `tests/test_verify.py`, `tests/test_check_bash.py`, `tests/test_check_common.py`

**Interfaces:**
- `phases.bind_session` e `phases.set_level` su un lavoro `closed` → `TransitionError("il lavoro è chiuso")`. Il runner già trasforma questo errore in un avviso.
- `verify._run_one`: `os.killpg` del gruppo anche a fine normale, ignorando `ProcessLookupError`, così nessun figlio in background sopravvive.
- `_common.waiver_hint(v)` ed `explain(violations)` senza il parametro `issue`, con i chiamanti aggiornati.
- `bash_rules`: il messaggio di `rm -rf` fuori dal repo aggiunge «usa `rm -r` senza `-f`, oppure un percorso dentro il worktree».

- [ ] **Step 1: Test**:
  - `test_phases.py::ClosedWorkTest::test_bind_and_set_level_refuse_closed`;
  - `test_verify.py::VerifyRunTest::test_background_child_killed_after_success` (comando `sleep 30 & echo ok` con report vuoto → dopo `verify` il pid del figlio non esiste);
  - `test_check_bash.py::test_rm_rf_outside_message_suggests_alternative`.
- [ ] **Steps 2-4**: fallimento, correzioni, `tests/run`, commit «tollgate P3a: minori rinviati (lavori chiusi, killpg, messaggi)».

---

