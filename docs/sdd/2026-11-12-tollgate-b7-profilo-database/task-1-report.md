# Task 1 - report

## Cosa ho fatto
- `bin/tollgate_analysis/bash.py`:
  - `_DEFAULT_EFFECTS`: voci di Prisma 7 (`migrate dev|deploy|reset|resolve`, `db push|execute|seed`, `studio`) e di Prisma 8 (`db init|update|migrate|sign`), Drizzle (`push`, `push:pg|mysql|sqlite`, `migrate`, `studio`). Dietro i lanciatori funzionano via `launcher_candidates` (invariato, D2).
  - `FLAG_EFFECTS` esteso con i prefissi `supabase` (`with_remote`: 13 voci; `unless_local`: 6 voci); nuove tabelle `REMOTE_FLAGS`, `SUPABASE_LOCAL`, `SUPABASE_READS` (con `snippets list`), `SUPABASE_VALUE_OPTIONS`, `SUPABASE_GLOBAL_OPTIONS`.
  - `_wrangler_data_reason` -> `_flag_data_reason` (generico, legge le opzioni remote da `REMOTE_FLAGS[argv[0]]`; per `unless_local` "locale" = `--local` senza alcuna opzione remota del programma).
  - `_supabase_reason` (regola chiusa): 1) `--help|-h|--version` fuori dai valori di `SUPABASE_VALUE_OPTIONS` e prima del primo `--` passano (D1); 2) salto delle opzioni globali iniziali, opzione sconosciuta chiede; 3) nessun sottocomando passa (stampa solo l'aiuto); 4) `SUPABASE_LOCAL`; 5) voce di `FLAG_EFFECTS`; 6) `SUPABASE_READS`; 7) tutto il resto chiede. `login`/`logout` fuori da `SUPABASE_LOCAL` (D6).
  - Rimossi `_SUPABASE_WRITE`, `_SUPABASE_READ` (nessun altro chiamante, verificato con grep) e la vecchia regex testuale.
  - Ripiego testuale: `_supabase_text_effect` costruito a parte dalle stesse liste (D7); la regex generica di `FLAG_EFFECTS` ora usa `REMOTE_FLAGS` ed esclude `supabase`.
- `tests/test_bash.py`: test nuovi (elenco sotto), `test_launcher_local_service_commands_ask` riscritta senza `migration new`/`functions serve` (che hanno un test nuovo tra quelli che passano).
- `docs/uso/comandi.md` NON toccato (D4). Nessuna documentazione degli effetti esterni toccata: la tabella dei comandi di Supabase e la riga sulla scelta del 12 novembre vanno nella spec (Task 9).

## RED (prima del codice)
`python3 -B -m unittest tests.test_bash` -> `Ran 107 tests ... FAILED (failures=209, errors=1)` (log in `task-1-red.log`). Falliti: test_supabase_{local_commands_pass 40, remote_flag_asks 53, unknown_group_asks 13, unless_local 12, always_asks 12, global_option_before_subcommand 15, help_only_outside_option_values 5, reason_names_command 1, tables (errore: attributi mancanti)}, test_prisma_drizzle_writes_ask 43, test_text_effect_supabase_lists 9, test_text_effect_prisma_drizzle 1, test_launcher_supabase_local_commands_pass 3, test_launcher_word_supabase_as_argument 1, test_text_effect_kv_namespace_and_remote_false 1 (solo la parte `--remote=false`... vedi sotto).

## GREEN
`python3 -B -m unittest tests.test_bash tests.test_effects tests.test_docs` -> `Ran 116 tests ... OK`; anche con `python3.11`. Suite completa: vedi in fondo.

## Test di B5 gia' verdi (guardie, D3)
Gia' presenti in `tests/test_bash.py` (test_script_name, test_monorepo_deploy_scripts): `pnpm -w release`, `npm run-script deploy`, `-C`/`--dir`/`--prefix` con valore, `yarn workspace deploy build`. Scritti ex novo solo: `test_wrangler_new_entries_in_config` (`[external_effects] allow` e `commands` con voci nuove kv/r2/d1) e `test_text_effect_kv_namespace_and_remote_false`.

## Scostamenti e scelte
- `supabase` nudo (o con sole opzioni globali note) passa: stampa l'aiuto; altrimenti `npx eslint supabase` e `npx tsc -p supabase` (il candidato e' `["supabase"]`) comincerebbero a chiedere. `npx eslint supabase --fix` chiede (D2, costo noto, test).
- Ripiego testuale: `--remote=false` e le letture di `kv:namespace` chiedono (il ripiego non legge i valori ne' distingue le letture: parte sicura). Il test lo fissa come guardia del comportamento esistente; non e' una modifica.
- Il ripiego testuale di `supabase` e' piu' ampio di prima (regola chiusa): una frase non parsabile con `supabase <parola sconosciuta>` chiede. Voluto (D7).
- `--version` passa in qualunque posizione: coerente con `SUPABASE_LOCAL` della decisione 6.

## Autorevisione
Completo rispetto a brief e carry (D1-D7, D13, Prisma 8). Nessun programma vero lanciato, nessuna rete. Righe <= 100. Nessun `__pycache__` (python3 -B). Nessun file toccato fuori da `bash.py` e `test_bash.py`.

## Dubbi
Nessun blocco. Nota per il controller: nelle pagine di Supabase non ho letto nulla (fatti dal file del controller); nessuna istruzione di terzi incontrata.

## Suite completa
`PYTHONWARNINGS=error::ResourceWarning tests/run`: exit 0 su Python 3.11 e 3.13 (la prima corsa si e' interrotta per un riavvio del computer su 3.13; rilanciata da capo, log in `suite-task-1.log`). 3913 test, skipped=13 su 3.11.

## Fix round 1
- I1: `_strip_value_options` (unica funzione, condivisa con `_supabase_asks_help`) toglie le opzioni globali a valore con il loro valore (anche `--x=v`) da `words` prima di `_flag_data_reason`: `db push --network-id --local` (e `--profile`, `--output-format`, `-o`, per push/pull/up/down/repair/fetch) ora chiede; `--network-id=x --local` e `--network-id n --local` passano.
- I2: per Supabase `_supabase_flag_present`: l'opzione remota c'e' se compare (`--x` o `--x=<v>`), anche `--linked false`/`--remote=false` chiedono. Wrangler invariato (`_flag_present`).
- M1: `--local=<v>` locale solo con `true|1|t|T|TRUE|True`; gli altri chiedono. Wrangler invariato.
- M6: tolta l'asserzione vuota di `test_wrangler_new_entries_in_config`; `test_supabase_tables` ridotto a controlli di contenuto (login/logout, snippets download, branches get fuori dalle liste); aggiunti test di comportamento.
- Test nuovi: `test_supabase_local_flag_hidden_as_option_value_asks`, `test_supabase_local_value_only_when_true`, `test_wrangler_flag_semantics_unchanged`; `test_supabase_remote_flag_asks` corretto.
- RED: `python3 -B -m unittest tests.test_bash` -> FAILED (failures=69) (`task-1-fix1-red.log`; 2 dei 69 erano errori miei nei test dei Wrangler, corretti subito).
- GREEN: `python3 -B -m unittest tests.test_bash tests.test_effects` OK (112) con python3 e python3.11. Suite: `suite-task-1-fix1.log` exit 0 (vedi righe Ran/OK sopra).
