# Ri-revisione giro di correzione 1, Task 5 (tests/test_run_script.py)

### Verdetti sui rilievi
1. **Ambiente del figlio senza MODEL_KEY_VARS**: INDIRIZZATO. `tests/test_run_script.py:40-43` parte da `os.environ`, esclude `MODEL_KEY_VARS` (import da `tests/helpers.py:24-29`, stesso elenco usato da `helpers.py:49`) e `PYTHONWARNINGS`, poi aggiunge TMPDIR, PYTHONS, RUN_TMP_PROBE e gli extra. Togliere `PYTHONWARNINGS` e' giustificato: il figlio esegue solo la sonda `-k test_tmpdir_probe` per verificare TMPDIR/pulizia, non il comportamento sotto ResourceWarning; la verifica reale di `tests/run` con `PYTHONWARNINGS=error::ResourceWarning` e' fatta dalla CI (`.github/workflows/ci.yml:31`) e dal test di testo `tests/test_ci_workflow.py:10` / `test_p5_scripts.py:624`, che non passano da questo figlio. Senza la rimozione, un ResourceWarning del figlio annidato renderebbe fragile il test senza dare copertura in piu'. Nessuna perdita.
2. **tearDownClass anche se un'asserzione fallisce**: INDIRIZZATO. `test_run_script.py` (diff, hunk finale): `self.addCleanup(RunnerTest.tearDownClass)` subito dopo `setUpClass()`, e `self.doCleanups()` al posto della chiamata diretta; il cleanup si consuma una volta (nessun doppio giro) e se `assertTrue(folder.exists())` fallisce gira a fine test.
3. **Confronto dei percorsi dopo resolve()**: INDIRIZZATO. `seen.parent.resolve()` contro `self.base.resolve()` nel test `test_run_sets_and_removes_tmpdir`.
4. **skipIf root sul test sigillato**: INDIRIZZATO. `@unittest.skipIf(os.geteuid() == 0, ...)` su `test_run_removes_sealed_dirs_and_keeps_exit_code`.

Verifica mirata: `python3 -B -m unittest tests.test_run_script` -> Ran 5, OK (skipped=1; uid 1000, il salto e' quello della sonda).

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
