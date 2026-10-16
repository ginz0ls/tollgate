# Task 10: sottocomando `verify` (8.1)

**Status:** DONE

**Commit:** `2751b94` tollgate P2: sottocomando verify con ricevute e ambiente ripulito (ramo `p2-guardrail`)

## Implementato

- `bin/tollgate_core/verify.py` (nuovo): `CommandSpec`, `gate_commands`, `receipt_state`, `clean_env`, `counts_green`, `run_verify`.
- `bin/tollgate_core/cli.py`: sottocomando `verify [--related]`. Uscita 0 se ogni ricevuta vale verde, 1 altrimenti. L'import di `verify` sta al livello del modulo, come gli altri.
- `tests/helpers.py`: `make_origin_repo(root, files, toml)`, come da brief.
- `tests/test_verify.py` (nuovo): 12 test, quelli del brief più 4 aggiunti (vedi scostamenti).

## Test ed esiti

Il controller ha fissato il valore 322 come base. Con i 12 test nuovi la suite è a 334.

- RED (`python3 -B -m unittest tests.test_verify`, prima del modulo):
  ```
  ERROR: test_verify (unittest.loader._FailedTest.test_verify)
  ImportError: cannot import name 'verify' from 'tollgate_core'
  FAILED (errors=1)
  ```
- GREEN (`tests.test_verify`): `Ran 12 tests in 0.736s` / `OK`.
- `tests/run`, entrambi gli interpreti: `Python 3.11.16` e `Python 3.13.5`, `Ran 334 tests` / `OK`, output pulito.
- `python3 -B bin/tollgate verify --help` mostra `--related`.

## Scostamenti dal brief e perché

1. **C13 implementata.** `base = work.work_base_sha oppure git.default_ref(root)`. Il brief usava `ref` per la configurazione ma `base = work["work_base_sha"]` per `git.changes`, che avrebbe passato `None`. Ora un solo valore serve sia alla configurazione sia al diff. Test: `test_work_without_base_sha_uses_default_ref` (azzera `work_base_sha` nel DB).
2. **Decisione 12 implementata.** Il brief non ripiegava sul gate quando `--related` non trova test. Ora: se `test_related` dà `empty`, la ricevuta `related` viene registrata e si eseguono i comandi del gate, e il verdetto è quello del gate. Se `test_related` dà un esito diverso (verde o rosso) il verdetto è il suo. Senza file cambiati o senza `test_related`, si esegue il gate. Test: `test_related_with_tests_records_only_related`, `test_related_without_tests_falls_back_to_gate`.
3. **Errori git.** `run_verify` cattura `git.GitError` (compreso il timeout di 10 s) e restituisce uscita 1 con il messaggio. Prima sarebbe stata un'eccezione non gestita. Test: `test_git_error_is_reported_not_raised`.
4. **Nessun HEAD.** Se `git.head` restituisce `None` (repo senza commit) si esce con 1 e un messaggio.
5. **Timeout di un comando.** Il processo scaduto dà uscita `124` (costante `TIMEOUT_EXIT`), che la ricevuta registra come rossa.
6. **`allow_no_tests` passato davvero.** `_run_one` riceve `allow_no_tests` e lo passa a `receipt_state`. La funzione non lo usa nel calcolo dello stato (il conteggio verde è in `counts_green`), ma la firma resta come da brief.

## File cambiati

- `bin/tollgate_core/verify.py` (nuovo)
- `bin/tollgate_core/cli.py`
- `tests/helpers.py`
- `tests/test_verify.py` (nuovo)

## Dubbi per la revisione

- Con il ripiego, la ricevuta `related` `empty` resta nel DB accanto alle ricevute del gate. Il controllo di `SubagentStop` cerca una ricevuta `green` sull'ultimo commit, quindi conta quella del gate. Va verificato in revisione.
- `receipt_state` tratta come rosso un report configurato e assente (8.1: `uncounted` vale verde solo senza report configurato). È coerente con la spec, ma è una scelta da confermare.
- Il ripiego usa `empty` come segnale di «nessun test correlato». Un `test_related` che non produce alcun report (`uncounted`, quindi rosso) non attiva il gate completo. Il comportamento segue la spec, ma va tenuto presente.

## Fix round 1

Rilievi del controller: timeout che lascia vivi i figli, e sei punti minori. Ogni punto ha prima il suo test (RED), poi la correzione (GREEN).

### Importante: timeout sull'intero gruppo di processi
- Prima: `subprocess.run(timeout=...)` uccideva solo `/bin/sh`; i figli in background restavano vivi.
- Ora: `Popen(..., start_new_session=True, stdin=DEVNULL)`, poi `communicate(timeout=...)`. Allo scadere: `os.killpg(pid, SIGKILL)` e `proc.wait()`, uscita 124.
- RED: `test_timeout_kills_the_whole_process_group` fallisce con `True is not false : il figlio è sopravvissuto al timeout`. Il figlio `(sleep 2; touch sentinella) & sleep 7` con timeout 1 scrive il file dopo il timeout.
- GREEN: il sentinella non compare dopo 3 s, e la ricevuta è `red` con uscita 124.

### Minori
1. **stdin chiuso.** `stdin=subprocess.DEVNULL`. Test `test_stdin_is_devnull`: il comando `if read x ...` riceve una pipe aperta senza dati e deve uscire con 7, non andare in timeout. RED: `124 != 7`.
2. **Log del timeout.** Riga `[tollgate] timeout dopo <N> s` in fondo al log. Test `test_timeout_is_written_to_log`. RED: la riga manca.
3. **Variabili TOLLGATE_*.** `clean_env` le scarta sempre, anche se in `env_allow`. Test `test_clean_env_never_passes_tollgate_vars`. RED: passavano `TOLLGATE_STATE` e `TOLLGATE_TEST_CONFIG`.
4. **Percorsi del report.** `_report_path` rifiuta percorsi assoluti o con `..` con `ConfigError` in italiano. Il controllo avviene in `_verify`, prima di eseguire o cancellare alcunché. Test `test_report_outside_worktree_is_refused` (assoluto e `../fuori.xml`): il file esterno resta, nessuna ricevuta. RED: il file veniva cancellato e il messaggio non c'era.
5. **Uncounted senza report.** Con uscita 0 e nessun report, la riga dice che il comando non conta i test e che con `allow_no_tests = false` il verdetto è rosso. Test `test_uncounted_related_explains_the_red_verdict`. RED: messaggio assente.
6. **sqlite3.Error.** `run_verify` restituisce uscita 1 con «errore del database». `cli.main` ha un ramo `except sqlite3.Error` che stampa `tollgate: errore del database: ...` senza traceback. Test `test_sqlite_error_is_reported_not_raised` e `VerifyCliTest.test_sqlite_error_in_cli_is_exit_1_without_traceback`. RED: eccezione non gestita.
7. **Test di copertura mancanti.**
   - `test_failing_command_without_report_is_red`: uscita 3 senza report, ricevuta `red`, uscita 3.
   - `test_work_none_leaves_work_null`: esecuzione dal checkout principale, `work` NULL.
   - `test_config_error_is_exit_1`: `schema_version = 99` dà uscita 1 senza ricevute.
   Questi tre passavano già sul codice precedente, perché coprono comportamento esistente. Restano come rete di sicurezza.

### Nota sui test
- Le configurazioni di prova inline mancavano di `[gate] mode`, e il loader le rifiutava. Corretto nei test (`_cfg`, `report_outside`, `uncounted_related`). Non è un difetto del modulo.
- `test_stdin_is_devnull` usa una pipe aperta su fd 0. Senza quella pipe il test non dimostrava nulla, perché lo stdin del processo di test era già chiuso.

### Comandi ed esiti
- `python3 -B -m unittest tests.test_verify`: `Ran 23 tests in 6.120s` / `OK`.
- `tests/run`: Python 3.11.16 `Ran 345 tests in 8.276s` / `OK`; Python 3.13.5 `Ran 345 tests in 8.339s` / `OK`. Exit 0.
- Nessun processo `sleep` orfano dopo la suite.

### File cambiati
- `bin/tollgate_core/verify.py` (riscritto con le correzioni)
- `bin/tollgate_core/cli.py` (`import sqlite3`, ramo `except sqlite3.Error`)
- `tests/test_verify.py` (11 test nuovi, più la correzione delle configurazioni)

### Dubbi
- Un figlio in background che esce da solo prima della fine del comando non viene ucciso alla fine di un verify riuscito. Il timeout copre solo il caso di scadenza. Va deciso se pulire il gruppo anche a fine normale.
