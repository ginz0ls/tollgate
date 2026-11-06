### Task 5: I test smettono di lasciare cartelle in `/tmp`

**Files:**
- Modify: `tests/run`, `tests/test_gh.py:20`, `tests/test_statusline.py:26`, `tests/test_hook_engine.py:196`
- Create: `tests/test_run_script.py`

**Interfaces:**
- Produces: `tests/run` con `TMPDIR` per corsa (decisione 10).

- [ ] **Step 1: I test che falliscono** (`tests/test_run_script.py`):
  - `test_run_sets_and_removes_tmpdir`: lancia `tests/run -k test_tmpdir_probe` con `PYTHONS` uguale a `sys.executable` e la variabile `RUN_TMP_PROBE` che nomina un file in una cartella del test; la sonda `test_tmpdir_probe` (nello stesso file, saltata senza `RUN_TMP_PROBE`) scrive lì `tempfile.gettempdir()`. Atteso: uscita 0; la cartella scritta comincia con `tollgate-run-`, sta sotto la `TMPDIR` di partenza, e dopo la corsa non esiste più.
  - `test_run_removes_tmpdir_on_failure`: stessa cosa con la sonda che fallisce apposta (`RUN_TMP_PROBE_FAIL=1`): uscita diversa da 0 e cartella tolta.
  - `test_known_leaks_closed`: per `tests.test_gh.FakeGhCase` e le classi di `test_statusline.py:26` e `test_hook_engine.py:196`, dopo `setUp` e i `cleanup` (o `setUpClass`/`tearDownClass`) la cartella creata non esiste più.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** In `tests/run`, prima del ciclo: `RUN_TMP="$(mktemp -d "${TMPDIR:-/tmp}/tollgate-run-XXXXXX")"`, `trap 'rm -rf "$RUN_TMP"' EXIT`, `export TMPDIR="$RUN_TMP"`. Nelle tre classi, `addCleanup(shutil.rmtree, <cartella>, ignore_errors=True)` (o `tearDownClass`).
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_run_script tests.test_p4_ghguard tests.test_gh`: PASS (la guardia di P4 accetta il `TMPDIR` della corsa). `tests/run`: verde, e dopo la corsa `ls -d /tmp/tollgate*` non ha cartelle nuove create dalla corsa.
- [ ] **Step 5: Commit** «tollgate B3-bis: i test non lasciano più cartelle in /tmp».

---

