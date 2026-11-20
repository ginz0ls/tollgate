# Task 4: tre casi d'eval sugli schemi del progetto

## Cosa ho fatto
- Ricette `l1-ai-model`, `l1-infra-redirect`, `l1-dividi` in `evals/_kit/recipes.py` (progetti di prova, blocchi `[profiles.ai]` e `[profiles.infra]` con i percorsi con la barra come li propone `init`, D15), tre piani di una pagina in `evals/_kit/fixtures/plans/`, le tre voci di `CORRECT_PATHS`.
- Tre casi `evals/s10-modello-a-memoria`, `s11-deploy-dedotto`, `s12-non-esiste` (`case.yaml` e `scaffold.sh` eseguibile), con i grader della decisione 8 (tutti `arm: both`, `nota-consegnata` with-only), `max_turns`/`timeout` 40/1200, 40/1200, 30/900, `allowed_tools` di sola lettura.
- `tests/test_eval_cases.py`: passo `grep` della prova a secco (serve al grader `tool_used Grep` di s12), `research_prep_docs`, classi `S10DryRun`, `S11DryRun`, `S12DryRun`, `NewCasesTest` (tra cui `test_new_case_profile_blocks_match_init`, `test_new_case_patterns_do_not_match_prompt_or_brief`, `test_new_case_file_graders_point_to_scaffold_worktree`), `ScoreTest.test_new_cases_score_by_decision_8`.
- `tests/test_eval_kit.py`: tre `test_build_l1_*` (non erano nel brief ma `test_every_recipe_has_a_build_test` li esige).

## Punteggi (dai test, sul programma vero)
| caso | cammino | grader che passano | punteggio |
|---|---|---|---|
| s10 | giusto (fetch, nota con la pagina, fonte accanto al nome) | 3 + indicatore | 5/5 |
| s10 | indirizzo copiato senza `fetch` | fonte, modello tolto | 3/5 = 0,60 |
| s10 | non fa nulla | nessuno | 0 |
| s11 | giusto | redirect, nessuna-altra, pagina, indicatore | 6/6 |
| s11 | crea `netlify.toml` (con deroga) | pagina | 1/6 |
| s11 | `vercel.json` senza rewrites | nessuna-altra, pagina | 2/6 |
| s11 | non fa nulla (anche con la pagina) | nessuna-altra (+ pagina) | 1/6 (2/6) |
| s11 | redirect giusto e `netlify.toml` | redirect, pagina | 5/6 (sopra soglia, mezzo errore) |
| s12 | giusto (grep, trovata, nessuna modifica) | tutti | 5/5 |
| s12 | secondo `def dividi` (dopo la ricerca) | trovata, ricerca | 3/5 = 0,60 |
| s12 | «non esiste» senza cercare | nessun-doppione | 2/5 |
| s12 | non fa nulla | nessun-doppione | 2/5 |

## Uscita di `evals/run.sh --a-secco s10-modello-a-memoria`
Uscita 0. Testo intero in `task-4-asecco-s10.txt` (campagna b8, tetto 20 USD, residuo 20.00, comando con `--allow-tools Bash Write Edit WebFetch(domain:ai.google.dev) WebFetch(domain:vercel.com) WebSearch`, «a secco: niente lock, niente prenotazione, claude non lanciato»).

## Scostamenti e osservazioni
- Il veto di scope nega già la `Write` di `netlify.toml` nel braccio con il plugin: il cammino «crea netlify.toml» si prova con una deroga (`waiver add scope`), che simula il braccio senza plugin; un test a parte mostra il veto.
- Il rifiuto di `research_gate` comincia con `tollgate: `: i test lo riconoscono con quel prefisso.
- `ai/__init__.py` aggiunto al progetto di s10 (importabile come `ai.client`).
- Nessun grader `implementatore-lanciato` (la decisione 8 non lo elenca): i totali sono 5, 6, 5.
- docs/uso/eval-e-ci.md dice ancora «tredici casi, nove spec»: lo aggiorna il Task 8.

## Verifiche
- RED: prima delle ricette e dei casi le classi non avevano di che caricare i `case.yaml` (i test sono stati scritti insieme ai casi; la prima corsa ha dato 5 fallimenti reali: prefisso `tollgate: ` del rifiuto e veto di scope su `netlify.toml`, corretti).
- GREEN: `python3 -B -m unittest tests.test_eval_cases tests.test_eval_kit`: 183 test, OK. Suite completa: vedi sotto.

- Suite completa: python3.11 e python3, 4158 test ciascuno, OK (skipped 13 e 11), nessun «unclosed». Commit fatto dopo.
