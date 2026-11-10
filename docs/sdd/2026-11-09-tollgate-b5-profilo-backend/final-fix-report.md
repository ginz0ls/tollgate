# Report del giro di correzione della revisione finale B5

Base 80e9f47. Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> 3760 test OK su Python 3.11 (skipped=10) e 3.13 (skipped=8), exit 0 (`final-fix-suite.txt`). Nota: la suite è stata lanciata con una subshell in background (`&` dentro il comando) invece del solo `run_in_background`; nessun test ne ha risentito (incluso il Ctrl-C su pty).

## I-1 (profile_blocks)
- RED: `python3 -B -m unittest tests.test_init.ProfileBlocksTest` -> 3 failures (`test_path_only_light_skipped_when_content_goes_to_another_profile`, `test_path_only_light_skipped_in_drift_too`, `test_real_content_match_of_ai_keeps_nested_routes_out_of_backend`: `'profiles.x]' unexpectedly found`, `'backend' unexpectedly found`).
- GREEN: dopo il codice, 60 test OK. In `lighting` entra un file solo se è in `detected[area]` oppure non è in `detected` di nessun altro frammento.
- Test nuovi (`tests/test_init.py`): quattro con frammenti finti `x`/`y` (anche senza marcatore, trovato da tutti e due, e la deriva) e `test_real_content_match_of_ai_keeps_nested_routes_out_of_backend` con i frammenti veri.
- File: `bin/tollgate_flow/init.py`.

## M-1 (_flag_present)
- RED: `tests.test_bash` -> FAIL `'wrangler kv key put K -- --local': None`.
- GREEN: 89 test OK. La scansione si ferma al primo `--`. Aggiunti anche `wrangler d1 execute DB --remote -- --local` (fermato) e `wrangler kv key put K V --local -- x` (libero).
- File: `bin/tollgate_analysis/bash.py`, `tests/test_bash.py`.

## M-2, 22, 23
`agents/implementer-backend.md`: `psql` tolto dai non coperti (esempio `mysql`/`mongosh`, che bash.py non conosce); `kv namespace` e `r2 bucket` «salvo le letture `list`, `get` e `info`»; aggiunto `d1 time-travel restore`. `tests.test_manifest` OK.

## 7
`tests/test_bash.py`: `test_script_name` e `test_monorepo_deploy_scripts` hanno `pnpm -w release`, `npm run-script deploy`, i valori di `-C`/`--dir`/`--prefix` e `yarn workspace deploy build`. Le sonde davano già il risultato giusto: i test passano subito (copertura aggiunta, nessun rosso atteso).

## 13, 14, 16
`tests/test_rules_backend.py`: `USER_CHOICES` con R-BACKEND-02 (sezione 3.4) e R-BACKEND-12 (sezione 12), le loro `Fonte:` le nominano; tolte le due righe dell'`if any`; tolto `sources_main`.

## 28, 29
`docs/verifiche/2026-11-09-b5-prova-flusso.md`: verificato sullo stream (riga 208 = percorso di review-1.md, riga 225 = `Read` con solo R-BASE-05); frase corretta.

## 33 e documenti
Spec del nucleo: 8.5 (parentesi unite, `_flag_present` si ferma a `--`), 11.2 (regola di I-1 e limite), 11.4 (limite), riga 32 della sezione 20. Piano principale, sezione 9: voce del limite di I-1.
