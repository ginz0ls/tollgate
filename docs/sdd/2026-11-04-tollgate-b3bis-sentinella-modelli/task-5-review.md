# Revisione Task 5 (152a373)

### Aderenza
- ✅ `tests/run:5-8`: `mktemp -d "${TMPDIR:-/tmp}/tollgate-run-XXXXXX"` sotto la `TMPDIR` di partenza (resta sotto /tmp, guardia P4 salva), `export TMPDIR`, trap D1 identico alla lettera. Con `set -e` un mktemp fallito esce prima del trap; i `|| true` lasciano il codice d'uscita dei test (in bash lo stato originale sopravvive a un trap EXIT che non chiama `exit`).
- ✅ Codice d'uscita con test rosso: `test_run_removes_tmpdir_on_failure` (`tests/test_run_script.py:61`) verifica uscita != 0 e cartella tolta.
- ✅ D1: `test_run_removes_sealed_dirs_and_keeps_exit_code` (`:67`) con 0o500 + sottocartella 0: uscita 0, cartella tolta; discrimina davvero il `chmod` (senza, `rm -rf` non svuoterebbe la cartella).
- ✅ Perdite chiuse: `tests/test_gh.py:24`, `tests/test_statusline.py:27`, `tests/test_hook_engine.py:200-203`.
- ✅ D13: `PrReadTest` (sottoclasse con test di `FakeGhCase`), `CtxTest`, e `setUpClass`/`tearDownClass` a mano per `RunnerTest`.
- ✅ Nessuna ricorsione: nel figlio `-k test_tmpdir_probe` seleziona solo la sonda (nessun altro id contiene la stringa); nella corsa normale la sonda è saltata senza `RUN_TMP_PROBE` (evidenza: skipped +1).
- ✅ CI (`.github/workflows/ci.yml:31`, `PYTHONS=python ... tests/run`) invariata e compatibile; `/tmp/tollgate*` prima/dopo identici (1566 righe, `diff` vuoto); suite 3545 OK su 3.11 e 3.13, EXIT=0.
- ✅ Scostamento su `sys.modules` (`test_hook_engine.py:197-199`): giusto. `registry.load("finti_checks")` lascia i moduli in cache; `fake_checks` toglie solo il path da `sys.path`, quindi una seconda `setUpClass` nello stesso processo (quella di `test_known_leaks_closed`) riusava moduli di una cartella cancellata. Il filtro (`== finti_checks` o prefisso `finti_checks.`) è stretto, nessun altro usa quel nome (grep). Non nasconde un problema, ripulisce uno stato che la classe stessa crea.
- ⚠️ Non rilanciata la suite (regole); mi fido delle evidenze, coerenti con il diff.

### Punti di forza
- Trap robusto (chmod prima di rm), diff minimo, un solo punto che sceglie la cartella.
- Test del figlio hermetici sul percorso: `TMPDIR` di partenza controllato, `PYTHONS=sys.executable`, pulizia con chmod nel `_rm`.
- Lo scostamento è dichiarato con la causa reale.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `tests/test_run_script.py:38-41` (`launch`): l'ambiente del figlio è `os.environ` intero, quindi inoltra eventuali chiavi API alla corsa figlia. Gira solo la sonda e nessun test fa rete, quindi non c'è un'uscita reale, ma "senza chiavi" non è garantito per costruzione. Correggere: partire da un ambiente ridotto (PATH, HOME, TMPDIR, PYTHONS, RUN_TMP_*).
2. `tests/test_run_script.py:73-93`: se un'asserzione fallisce a metà di `test_known_leaks_closed`, le risorse successive (`RunnerTest.tmp`) restano e `tearDownClass` non gira; usare `try/finally` o `addCleanup(RunnerTest.tearDownClass)`.
3. `tests/test_run_script.py:56`: `assertEqual(seen.parent, self.base)` può fallire dove `gettempdir()` risolve symlink (macOS); qui verde. Confrontare con `.resolve()`.
4. Il test della cartella sigillata non discrimina se la suite gira da root (root scavalca i permessi); accettabile, ma uno `skipIf(os.geteuid()==0)` direbbe la verità.
5. Un SIGKILL del runner lascia comunque `tollgate-run-*`: coperto dalla pulizia del Task 7 (>24 h).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e decisioni D1/D13 rispettati alla lettera, evidenze coerenti (suite verde, /tmp invariato, CI compatibile), scostamento su `sys.modules` corretto e necessario; solo rifiniture Minor.
