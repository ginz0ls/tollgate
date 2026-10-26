# Ri-revisione Task 11, giro 3 (70aa3c4..bb519ec)

### Verdetti sui rilievi
- **D1 (test sul registro vero rosso con riga `?` o tetto esaurito)**: INDIRIZZATO. `tests/test_eval_run.py` `test_dry_run_reads_real_registry`: calcola `cost.py remaining`, `exhausted` se uscita != 0, vuoto o < 0,01; in quel caso asserisce `returncode == 1`, claude non lanciato, registro e cartella invariati. Ramo `?`/residuo 0 asserito anche in `test_dry_run_touches_nothing` (riga `?` -> uscita 1, registro invariato; `write_budget(80)` -> 1).
- **D2 (HOME dei test nel bersaglio / non ignorata)**: INDIRIZZATO. `.gitignore:2`, `evals/_kit/target.py` `SKIP_PREFIXES` applicato in `build`; test `test_target_skips_test_home_dirs`.
- **D3 (suite che ricostruisce il bersaglio durante una corsa vera)**: INDIRIZZATO. `lock_held` (`os.open` O_RDONLY, file assente -> False senza crearlo, `flock` non bloccante) e `skipTest` in testa; `test_lock_held_detection` e `test_held_lock_gives_skip_not_error` coprono rilevazione, non-creazione e skip (SkipTest, non errore).
- Eseguiti da me `DryRunRealRegistryTest` e `TargetTest`: 7 test OK. `git status` pulito.

### Danni nuovi nel diff della correzione
Nessuno. Verificato: il controllo del lock non crea il file; con lock tenuto si ha skip; `--a-secco` non prende il lock (`run.sh:6`, `dry` salta il flock a riga ~103); `SKIP_PREFIXES` esclude solo `.tollgate-test-home-*`, nessuna cartella necessaria al bersaglio.

### Osservazioni fuori ambito
Nessuna. (Minima: `float(remaining)` nel test solleverebbe ValueError se `cost.py remaining` stampasse testo non numerico con uscita 0; non accade.)

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
