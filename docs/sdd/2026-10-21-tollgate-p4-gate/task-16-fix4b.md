# Task 16 — giro 4, minori della ri-revisione (cautele invariate: vedi task-16-fix4.md e cautele.md)

- M4-1 `bin/tollgate_core/ghcli.py` `_run_retrying`: gh passa a POST quando ci sono `-f`, `-F`, `--field`, `--raw-field` (anche nella forma `--field=`/`--raw-field=`) o `--input` senza `--method`. Questi argomenti rendono la chiamata una scrittura: nessun ritentativo. Test rossi prima: `api ... -f x=y` senza method con 500 → 1 chiamata; idem `-F`, `--input`, `--raw-field=`.
- M4-2 `RETRY_DELAYS_S` sostituibile nei test tramite una variabile d'ambiente di test letta con `paths.test_env` (stesso meccanismo di `TOLLGATE_GH`; solo nello stato di test, mai in produzione), così `tests/test_init.py::test_token_without_admin_undetermined` non dorme 6 s reali. Test che la variabile valga solo dove `paths.test_env` la ammette.

Suite verde con `tests/run` su python3.11 e python3. Commit nuovo «tollgate P4: ritentativi solo per le letture vere e attese brevi nei test (Task 16, giro 4, minori)» con la riga esatta «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>». Aggiorna la sezione «Giro 4» del report; rispondi solo con stato, commit, una riga sui test, dubbi.
