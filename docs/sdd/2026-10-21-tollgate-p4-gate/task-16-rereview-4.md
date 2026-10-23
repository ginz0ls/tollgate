# Ri-revisione giro 4 — Task 16 (e7dd195)

### Verdetti sui rilievi
**Letture di `gh api` ritentano sui 5xx transitori (ruling)** — INDIRIZZATO. `ghcli.py` `_run_retrying` (unico helper, usato da `api`, `run_json`, `run_json_lines`); lettura = `args[:1]==["api"]` senza `--method`/`-X`/`--method=`/`-X…`; transitorio = `_TRANSIENT` (`HTTP 5dd`, `unexpected end of JSON input`) o, con `--include`, riga di stato >= 500; 3 tentativi, `RETRY_DELAYS_S=(2,4)`, `_sleep` sostituibile; dopo l'ultimo l'errore passa dal codice di sempre (stesso `GhError`, stesso `ApiResult`); `pr …` e scritture mai ritentati; il timeout (`GhError` da `run`) esce subito. Docstring aggiornate.
**Gli 8 test richiesti** — INDIRIZZATI. `RetryTest` copre i punti 1-7 (anche timeout, `-X`, `--method=`, `pr list`, `pr create`); `test_gate_guard.py::test_transient_500_on_commit_pulls_is_retried` il punto 8. Il report dichiara 11 errori prima (`_sleep` assente): rosso sensato. Eseguito: `tests.test_ghcli tests.test_gate_guard` 76 test OK.
**gh finto `api_flaky`** — INDIRIZZATO. Minimo (8 righe), documentato, testato da `FakeGhFlakyTest` (consuma un messaggio, riscrive il file dati).

### Danni nuovi nel diff della correzione
- Minor, `bin/tollgate_core/ghcli.py:~87` (`_run_retrying`): la classificazione dagli argomenti non conosce l'inferenza di gh «`-f`/`-F`/`--input` senza `--method` = POST». Oggi nessun chiamante fa `api(method="GET", fields=…)` né passa `-f/-F/--input` a `run_json*` (verificato in `bin/`), quindi nessuna scrittura è ritentata. È però un invariante latente: conviene trattare anche `-f`, `-F`, `--field`, `--raw-field`, `--input` come scrittura (direzione sicura). Non blocca.
- Minor, `tests/test_init.py:142` `test_token_without_admin_undetermined`: ora dorme davvero 6 s per interprete (3 tentativi con 500 sul sottoprocesso `--include`). Accettabile funzionalmente; meglio renderlo istantaneo con una variabile di test (`paths.test_env`, attiva solo in test_mode) per `RETRY_DELAYS_S`, oppure accettare il costo. Non blocca.

Sul dubbio (1): classificare un `run_json` qualsiasi dagli argomenti è corretto e prudente (solo `api` senza flag di metodo; tutto il resto no), con la riserva del primo Minor.

### Osservazioni fuori ambito
Il working tree ha file non tracciati/modificati in `docs/verifiche/evidenze/gh-p4/` (prove P4): estranei al diff.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.

## Verifica dei minori (aa1a0b3)
- M4-1 INDIRIZZATO: `_WRITE_FLAGS` con `startswith` copre `-f/-F/--field/--raw-field/--input` (anche `-fx=y`, `--field=`, `--input=`); test `test_api_field_arguments_make_a_write` (nove forme + `fields`/`file_fields`/`input_file` di `api`). Verificato che nessun argomento di lettura usato in `bin/` (`--jq`, `--paginate`, `--include`, `--hostname`, `-H`, percorsi, filtri jq) combacia col prefisso: le letture restano ritentate.
- M4-2 INDIRIZZATO: `TOLLGATE_GH_RETRY_DELAYS` è letta solo in `_retry_delays` via `paths.test_env` ed è in `TEST_ENVS`; fuori da test_mode vale `(2, 4)` (test dedicato); il banco `flowkit.env()` la imposta a "0,0". Test `tests.test_ghcli` e `tests.test_flowkit`: 40 OK.
- Minor residuo (non blocca): in test_mode un valore malformato solleverebbe `ValueError`; irrilevante in produzione.
Verdetto: pulito.
