# Ri-revisione giro 1, Task 1 (8db63e2..88ee27c)

### Verdetti sui rilievi
- **I1. `--local` come valore di un'opzione globale (`db push --network-id --local`)**: INDIRIZZATO. `_strip_value_options` (bash.py:1285-1298) e' una sola funzione, usata da `_supabase_reason` (riga ~1318, prima di `_flag_data_reason`) e da `_supabase_asks_help`. Sonde: `--network-id --local`, `-o --local`, via `npx` chiedono; `--network-id=x --local`, `--network-id n --local`, `-ojson --local`, `--local -o json` passano. Fermata al primo `--` corretta. Test `test_supabase_local_flag_hidden_as_option_value_asks` (6 sottocomandi x 8 opzioni).
- **I2. `--remote false` / `--linked false` per Supabase**: INDIRIZZATO. `_supabase_flag_present` (bash.py:1230-1241) conta l'opzione se compare in qualsiasi forma; scelta per `argv[0] == "supabase"` (riga ~1252). Sonde: `db reset --linked false`, `--remote=false`, `db diff --linked false`, `migration list --linked false`, anche dietro `npx`/`pnpm exec`, chiedono. Wrangler: `--remote false --file x` e `--remote false --local` passano come prima. Il test di `test_supabase_remote_flag_asks` ora fissa il contrario.
- **M1. `--local=<v>`**: INDIRIZZATO. Locale solo con `true,1,t,T,TRUE,True`; sonde: `=TRUE` passa, `=tRUE`, `=0`, `=false` chiedono. Wrangler invariato (`--local=0` passa). Test `test_supabase_local_value_only_when_true`.
- **M6. Test deboli**: INDIRIZZATO. Tolta l'asserzione vuota in `test_wrangler_new_entries_in_config`; `test_supabase_tables` non ripete piu' `REMOTE_FLAGS["supabase"]`, `SUPABASE_VALUE_OPTIONS`, `SUPABASE_GLOBAL_OPTIONS`. Resta `assertEqual(REMOTE_FLAGS["wrangler"], ...)` (costante, innocuo).

### Danni nuovi nel diff della correzione
Nessuno. Controllati: scorrimento delle opzioni (`--network-id --` consuma `--` come valore, come pflag; opzione a valore a fine riga passa, il comando fallirebbe da solo), comandi locali (`status`, `start`, `db diff --network-id x`, `gen types --network-id x --local`, `--workdir x` con `db lint`) non chiedono, aiuto (`--network-id x --help` passa, `--network-id --help` chiede perche' `--help` e' il valore), Wrangler invariato (test `test_wrangler_flag_semantics_unchanged`). `python3 -B -m unittest tests.test_bash`: 110 OK.

### Osservazioni fuori ambito
- `db dump --local=0` passa: `db dump` e' locale di default, quindi coerente; non e' un difetto.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
