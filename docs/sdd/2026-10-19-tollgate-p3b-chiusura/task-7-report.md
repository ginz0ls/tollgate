# Task 7: `review prepare`: report

## Implementato
- `bin/tollgate_analysis/brief.py`: `FinalBrief`/`final_review_brief` e `VerifierBrief`/`verifier_brief` (sha e code alla lettera, standard con disaccordo istruito, R3, gravità da `[severity]`, JSON di 18.5, divieto di scrivere file; testo non fidato in recinto).
- `bin/tollgate_flow/finalreview.py` (nuovo): `Launch`, `PrepareResult`, `ReviewError`, `prepare` (decisione 5, C16 `supersede`, C7 `review_unverified`, M1 `close_cycle` solo dopo `to_verify` vuoto). Brief in `.tollgate-run/<N>/final-<c>.md`, `final-<c>-<area>.md`, `final-<c>.diff`, `verify-<c>.md`. Lo stesso `patch-id` riprende un ciclo aperto con lo stesso codice (anche dopo rebase).
- `bin/tollgate_core/cli.py`: `tollgate review prepare`; `ReviewError` -> uscita 1.
- `bin/tollgate_flow/taskcmd.py`: modello di `[review] models` nel riepilogo e nel brief; il giro 4 resta `inherit` (decisione 21).

## TDD
RED (prima del codice): `python3 -B -m unittest tests.test_finalreview tests.test_brief tests.test_taskcmd` -> `FAILED (failures=1, errors=4)`: `AttributeError: module 'tollgate_analysis.brief' has no attribute 'verifier_brief'`, `ModuleNotFoundError` per `finalreview`, `test_models_override_in_summary`: `'model: sonnet' not found in 'task 1: tollgate:implementer name=tg-7-t1 launch ...'`.
GREEN: `python3 -B -m unittest tests.test_finalreview tests.test_brief tests.test_taskcmd` -> OK (17 test in test_finalreview).

## Scostamenti e scelte
- L0, componente spento e `review_unverified` non sono errori: stampano la riga e `prossimo passo: ... finish open-pr` senza lanci. Fase sbagliata, HEAD diverso da `finish_sha`, nono ciclo sono `ReviewError`.
- Un ciclo aperto con lo stesso `patch-id` ma SHA diverso si riprende (sha del ciclo nei brief); con `patch-id` diverso si chiude `superseded` (C16).
- Area dello specialista = nome dell'agente senza prefisso `final-` (`probe:final-security` -> `security`). Lista di controllo = `checklist` dei profili attivi (per lo specialista, solo il suo).
- `issue_file` nel brief punta a `.tollgate-run/<N>/issue.md`: il file non è scritto da questo task (non specificato).
- Test aggiunti oltre il brief: L0/componente spento, `review_unverified`, fase sbagliata, verify senza rilievi chiude il ciclo, supersede, needs_fix poi nuovo ciclo, CLI.

GREEN suite: `bash tests/run` -> python3.11 e python3: Ran 1170 tests, OK.

## Fix round 1
- `finalreview.py`: `_must_haves` legge il piano registrato prima di `open_cycle` (e prima di riprendere un ciclo in stadio review); un piano non leggibile dà `ReviewError` e nessun ciclo aperto. Tolto l'import `phases` inutilizzato.
- `brief.py`: `"v": 1` nei JSON di 18.5 del revisore finale e del verificatore.
- Test: `test_unreadable_plan_refused_before_opening_cycle` (`plan_sha` alterato: `ReviewError`, `reviews.count == 0`), asserzioni `{"v": 1, "sha"` in `test_brief.py`.
- Comando: `bash tests/run` -> python3.11 e python3 verdi (vedi sotto).
Output: python3.11 e python3: Ran 1171 tests, OK.
