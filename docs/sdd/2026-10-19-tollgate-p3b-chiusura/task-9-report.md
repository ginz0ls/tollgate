# Task 9 - report

Status: DONE_WITH_CONCERNS (vedi Scostamenti).

## Implementato
- `tollgate_analysis/prblock.py` (FIELDS, SCHEMA_VERSION, build/render/parse; `<`, `>`, `&` escapati), `prbody.py` (neutralize con recinto, `@` + ZWSP, `<!--`/`-->` disinnescati, troncamento; render con `Closes #N` in testa e blocco in coda).
- `gh.py`: `decode_json_values`, `run_json_lines` (raw_decode), `pr_for_branch`, `pr_view`, `pr_create`, `pr_edit`, `pr_comments`; `prs_for_branch_prefix` ora con `api --paginate --jq`.
- `gitw.py`: `push_sha` (lease opzionale), `remote_sha`, `is_ancestor`. `intents.force_authorized` (sola lettura).
- `prstate.py`: `Detection(kind, pr, error)`, `detect`, `CLOSED_HINT`, `closed_line`; agganciato a `finish check` (merged chiude, closed rifiuta, errore di rete = avviso).
- `openpr.py`: `open_pr` (decisione 10, rifiuti raccolti, ripresa da `pr_open` con intento `requested`), `facts` (decisione 11). CLI `finish open-pr [--update]`.
- `fakegh.py`: PR in `data["prs"]`, `pr create/edit/view/list`, `api --paginate .../pulls`, `fail`, campi `--json` sconosciuti rifiutati (anche senza PR).
- `finishcheck.profile_receipts` estratto e riusato da `open-pr`.

## TDD
RED: `tests.test_prblock/test_prbody` ImportError (`cannot import name 'prblock'`); `test_gh` 2 failures + 8 errors prima di gh.py/fakegh; `test_openpr` ImportError su `openpr` e poi 3 failures (CLI senza `open-pr`, atto non consumato per test sbagliato). `test_prstate`: 3 failures sui test di `finish check` prima dell'aggancio. GREEN: `tests/run` -> python3.11: 1266 test OK; python3 (3.13.5): 1266 test OK.

## Scostamenti / note
- `tests/test_flowkit.py`: le chiamate `pr list` ora passano `--json number` (il finto gh richiede `--json`, come il vero per avere JSON).
- `open_pr` ha il kwarg extra `environ`; `facts` ha i kwarg `now`, `dod`, `labels`, `cycle`; `Detection` ha il campo extra `error`.
- `spec_audit` e' sempre un oggetto `{adversarial, lens}` (null per campo), come nell'esempio 18.1.
- Con `review_unverified` i rilievi dei cicli non entrano nella DoD (findings_cycle = 0) e il corpo avvisa "revisione non verificata".
- `level_minimum` legge le etichette con `gh.issue`; se fallisce: avviso e solo diff.
- L'atto consumato e' quello `finish` e, se presente, anche `approve pr`; atti `finish` piu' vecchi sullo stesso SHA restano `pending`.
- Evento `pr_opened` se `pr_number` era nullo, altrimenti `pr_updated`.
- `start` non e' agganciato a `prstate.detect` (e' del Task 13).
- Il test del RED di `intents.force_authorized` e' stato scritto insieme al codice (funzione di 3 righe).

## Fix round 1
Modifiche:
1. `openpr._review`: con `review_unverified` la DoD guarda comunque l'ultimo ciclo chiuso su HEAD (o stesso patch-id); `_notes` e specialisti come per un ciclo normale; senza cicli chiusi voce vera e `verdict.outcome` null; il corpo dice ancora «non verificata».
2. `openpr._publish`: verifica con `intents.force_authorized`, `take_force` solo dopo `push_sha` riuscito.
3. `prbody._section`: tetto per voce (`_cap`) prima dell'unione, nessun tetto sulla sezione; anche `_note` senza «None» e `ZWSP` come escape `​` (M-5, M-3).
4. `gh.PR_JQ` normalizzato (`MERGED` da `merged_at`, `state | ascii_upcase`); `fakegh` stampa la forma normalizzata.
Test nuovi: `test_gh::test_prs_for_branch_prefix_paginated` (stringa jq), `test_prbody::test_long_entries_do_not_hide_later_ones_or_sections`, `::test_missing_file_or_line_in_note`, `test_openpr::OpenUnverifiedTest` (2), `OpenForceTest::test_failed_push_keeps_force_authorization`.
RED: `python3 -B -m unittest tests.test_gh tests.test_prbody tests.test_openpr.OpenUnverifiedTest tests.test_openpr.OpenForceTest` -> `Ran 21 tests ... FAILED (failures=5)` (jq, due prbody, unverified con bloccante, push fallito).
GREEN: stesso comando sui moduli completi -> `Ran 64 tests OK`; `tests/run` -> python3.11 `Ran 1271 tests OK`, python3 (3.13.5) `Ran 1271 tests OK`.
