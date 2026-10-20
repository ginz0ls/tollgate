### Task 2: Segnale per i sottocomandi di P3b, atti, tetto di `json_candidates`, impronta senza cache

**Files:**
- Modify: `bin/tollgate_core/sessions.py`, `bin/tollgate_checks/cli_calls.py`, `bin/tollgate_checks/acts.py`, `bin/tollgate_analysis/report.py`, `bin/tollgate_core/git.py`, `bin/tollgate_core/cli.py` (passa `argv` a `cli_session` per `start` e `act`), `bin/tollgate_flow/start.py`, `bin/tollgate_flow/actapply.py`, `tests/flowkit.py`
- Test: `tests/test_sessions.py`, `tests/test_check_cli_calls.py`, `tests/test_check_acts.py`, `tests/test_report.py`, `tests/test_git.py`

**Interfaces:**
- Produces: `sessions.cli_session(state, cwd, subcommand: str, *, now, argv: list[str] | None = None) -> str`. Con `argv` la voce vale solo se `entry["argv"] == argv`; la voce trovata si toglie dal file (scrittura atomica come `note_cli_call`). `start.start` e `actapply.apply_act` ricevono `argv: list[str] | None = None` per parola chiave e lo passano; `cli.main` passa `argv` (gli argomenti dal sottocomando in poi). `FlowLab.cli` resta compatibile.
- Produces: in `cli_calls`, `_SIGNALLED = ("start", "act", "finish", "sync", "adopt", "cleanup", "abandon")`, `_COORDINATOR_ONLY = ("start", "task", "act", "finish", "review", "sync", "adopt", "cleanup", "abandon")`. Il ramo `BashParseError` nega con il testo della decisione 2 (senza nome di sottocomando).
- Produces: in `checks/acts.py` `abandon` ha `work_id = None`, come `adopt` e `cleanup` (decisione 3).
- Produces: `report.MAX_SCAN_CHARS = 65536`, `report.MAX_DECODES = 500`; `json_candidates` esamina solo la coda e si ferma al tetto (decisione 23).
- Produces: `git.CACHE_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")`; `git.fingerprint` salta un file se un segmento del percorso è in `CACHE_DIRS` (decisione 22).

- [ ] **Step 1: Test che falliscono**
  - `test_sessions.py::CliSessionTest::test_signal_consumed_once` (seconda `cli_session` con lo stesso segnale → `CliSessionError`);
  - `test_sessions.py::CliSessionTest::test_argv_mismatch_refused` (segnale `["start", "7"]`, `argv=["start", "8"]` → errore);
  - `test_check_cli_calls.py::test_p3b_subcommands_signalled` (dalla sessione principale `finish open-pr`, `sync`, `adopt 7`, `cleanup --confirm`, `abandon 7` → voce nel file del segnale; anche `finish check` lascia la voce `finish`, innocua perché non la legge; `review prepare` → comando ammesso, nessuna voce);
  - `test_check_cli_calls.py::test_subagent_denied_p3b_commands` (con `agent_id`: `finish check`, `review prepare`, `sync` → 2);
  - `test_check_cli_calls.py::test_parse_failure_message_explains` (comando con virgolette aperte che nomina `tollgate task` da un subagente → 2 e il testo contiene «modo letterale»);
  - `test_check_acts.py::ActsTest::test_abandon_act_has_no_work` (sessione legata al lavoro 7, `/tollgate:abandon #9` → atto con `work` nullo e `target == "9"`);
  - `test_report.py::ReportTest::test_json_candidates_capped` (testo di 200.000 `{` seguito dal JSON valido → trovato in meno di 1 s; JSON valido seguito da 70.000 caratteri → non trovato);
  - `test_git.py::FingerprintTest::test_cache_dirs_ignored` (repo senza `.gitignore`, `tests/__pycache__/x.pyc` creato → impronta invariata; `src/a.py` cambiato → cambia).
- [ ] **Step 2: Verificare il fallimento**: `python3 -B -m unittest tests.test_sessions tests.test_check_cli_calls tests.test_check_acts tests.test_report tests.test_git`.
- [ ] **Step 3: Implementare** le firme sopra.
- [ ] **Step 4: Verificare**: stesso comando, poi `tests/run`.
- [ ] **Step 5: Commit** «tollgate P3b: segnale per i sottocomandi di chiusura, abandon senza lavoro, tetto di json_candidates, impronta senza cache».

---

