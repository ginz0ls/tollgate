# Report Task 3

## Implementato
- `bin/tollgate_analysis/bash.py`: `LAUNCHERS`, `PACKAGE_COMMANDS` (con le voci D13), `PACKAGE_PROGRAMS`, `launcher_candidates(argv)` (scansione della decisione 17, con il veto dei comandi dei pacchetti dopo un gestore, anche annidato), `_launcher_call_texts` per `-c`, `--call`, `--call=`; `effect_reason` prova `_DEFAULT_EFFECTS` e il ramo `supabase` su argv e su ogni candidato; il testo di `-c/--call` passa da `bash.parse` (ricorsione su `effect_reason`) o, su `BashParseError`, da `text_effect`.
- `_DEFAULT_EFFECTS`: le quattordici voci Wrangler, `wrangler pages publish` (D13), `docker image push` e `docker compose push` (D3).
- `tests/test_bash.py` (`EffectsTest`): tutti i test del brief, più `test_docker_push_forms`, `test_launcher_candidates`, e `x; wrangler pages deploy dist` in `test_text_effect_fallback`.

## TDD
- RED: `python3 -B -m unittest tests.test_bash` prima del codice: FAILED (failures=61, errors=1) (AttributeError su `launcher_candidates`).
- GREEN: stesso comando dopo: Ran 79 tests, OK. `tests.test_bash tests.test_effects tests.test_check_effects tests.test_layers tests.test_manifest`: 164 test OK.
- Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python 3.11.16 e 3.13.5, 3589 test, OK (skipped 5 e 3), nessun «unclosed».

## Scostamenti dal piano
Nessuno. Nessun messaggio nuovo in `bin/` (D15 non toccata).

## Dubbi
Restano aperti, come scritto: `docker buildx build --push`, `docker build --push`, `docker --context <remoto>`, `pnpm -c exec '…'`, valori d'opzione uguali a un servizio, `npm --loglevel info exec vercel --prod`.

## Fix round 1
- `PACKAGE_COMMANDS`: tolte `docs`, `config`, `help`, `repo`, `home`, `patch`; restano `search`, `explain`, `bugs`, `rebuild`, `dedupe`, `prune`, `fund`.
- `test_launcher_wrapped_effects`: aggiunti `pnpm --filter docs exec wrangler deploy`, `pnpm -C docs wrangler deploy`, `yarn workspace docs wrangler deploy`.
- Guardie nuove: `test_commands_config_matches_launcher_text` (`commands=["npx mytool"]` su `npx mytool run`), `test_curl_and_gh_stay_on_original_argv` (`npx curl https://x.invalid`, `npx gh pr list` -> None; il comportamento attuale era già questo, codice invariato).
- `python3 -B -m unittest tests.test_bash tests.test_effects tests.test_check_effects`: 105 test OK.
- `PYTHONWARNINGS=error::ResourceWarning tests/run`: python 3.11.16 e 3.13.5, 3606 test, OK (skipped 5 e 3), exit=0, nessun «unclosed».
