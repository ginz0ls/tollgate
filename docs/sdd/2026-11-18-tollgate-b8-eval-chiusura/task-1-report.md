# Report Task 1 (B8): involucri dell'ambiente, opzioni con valore di Supabase, doppio `--`

## Implementato
- `bash.py`: `ENV_LOADERS` (con `cross-env-shell`), `LOADER_PACKAGES`, `inner_commands`, `true_inner_commands`, `_launcher_hits` (base comune di `launcher_candidates` e della ricerca degli involucri dietro un lanciatore), `effect_reason(cmd, cfg, _depth=0)` con profondità 2 (il terzo involucro chiede), `launcher_candidates` toglie ogni `--` di testa, `SUPABASE_COMMAND_VALUE_OPTIONS` (tutti i sottocomandi di `FLAG_EFFECTS`), `_supabase_option_tokens` usata da `_supabase_flag_present` (nuovo parametro `prefix`), `_strip_value_options` e `_supabase_asks_help` (`--version` è aiuto solo prima di ogni sottocomando; il valore di un'opzione del sottocomando non è un aiuto), `script_path(cmd, inner=False)`.
- `effects.py`: `_script_reason(ctx, c, inner=False)` applicato anche a `true_inner_commands(c)`.
- `docs/uso/limiti.md`: due paragrafi sotto «### Gli effetti esterni».
- Opzioni «comando»: doppler `--command`; infisical `--command` e `-c`. `cross-env-shell` e `env-cmd --use-shell`: candidati anche con `" ".join`.

## Test
Nuovi in `tests/test_bash.py` (EffectsTest, ParseTest) e `tests/test_check_effects.py`, come da brief. RED: 80 fallimenti e 3 errori in test_bash, 11 + 1 in test_check_effects. GREEN: `python3 -B -m unittest tests.test_bash tests.test_check_effects tests.test_effects tests.test_docs tests.test_layers` OK. Suite completa: vedi esito sotto.

## Scostamenti e dubbi
- Candidato illegibile senza motivo da `text_effect`: chiede (lettura letterale di decisione 1, giro 3 m2), con motivo «comando di <involucro> non leggibile». Prototipo del preflight passava: segnalo la differenza.
- Profondità: involucro a profondità 2 (il terzo) chiede; il prototipo faceva chiedere il quarto.
- `_supabase_flag_present` ha un terzo parametro opzionale `prefix` (compatibile).
- `test_text_effect_supabase_value_options_still_ask`: il ripiego testuale non è cambiato.
- `npx @infisical/cli run -- prisma migrate deploy` chiede già oggi (per il `prisma` dopo il `--`): fissato da un test.
- Nelle pagine ufficiali nessuna istruzione di terzi incontrata in questo task.

## Fix round 1
- Cambiato: in `bash._loader_candidates`, se una parola del comando interno contiene spazi si costruisce anche il candidato `" ".join(parole)` (illeggibile: passa da `text_effect`/chiede); in scansione larga si provano anche le posizioni delle parole ri-spezzate (`dotenv -- jest -t "vercel deploy"` chiede: costo, dalla parte sicura).
- Test: `test_env_loader_inner_command_in_one_word` (chiedono `dotenv -- "supabase db push"`, `op run -- "prisma migrate deploy"`, `npx dotenv -- "npm run deploy"`, `dotenv -- jest -t "vercel deploy"`; passa `dotenv -- "python3 -m unittest"`).
- Comando: `python3 -B -m unittest tests.test_bash tests.test_check_effects tests.test_docs` OK (166 test); suite completa `exit 0` (W/suite-task-1-fix1.log). `limiti.md` invariato: resta vero.
