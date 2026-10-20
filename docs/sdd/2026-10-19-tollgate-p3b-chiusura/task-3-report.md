# Report Task 3: migrazione 4 e dati della chiusura

## Implementato
- `db.py`: `SCHEMA_V4` (decisione 1), `MIGRATIONS` fino a 4. `events.py`: `finish_check`, `base_realigned`.
- `phases.py`: `create_work(phase, cause)` (ValueError per `closed`, fase fuori sequenza, `phase` con `from_approved_spec`), `set_base`, `set_pr`, `set_finish`, `add_extra_cycles`, `set_review_unverified`.
- `acts.py`: `approved_waivers`, `has_approval`; `Ctx.approved_waivers` delega.
- `intents.py` (nuovo): `request`, `complete`, `authorize_force`, `take_force`, `pending`, `SYNC_CONFLICT_REASON`.
- `reviews.py` (nuovo): come da brief, più `supersede` (C16) e normalizzazione dei `rejected` (C18).
- `dod.py`: `receipt_verdict(allow_unverified)`, `compute_dod(allow_unverified, findings_cycle, specialists, skip)`, ricevute `related` escluse (C5), `findings` via `reviews.blocking_open`.
- `verdicts.is_blocking`, `git.patch_id`, `stats.off_periods` (con `_off_intervals` condiviso con `_off_seconds`).
- `tests/flowkit.py`: `PLAN`/`plan_text(task2, tasks)` spostati qui (C12), `register_plan`, `commit`, `close_tasks`, `JUNIT_TOML`, `JUNIT_FAKE`/`JUNIT_FILES` (il file `tools/junit_fake.py` entra nel repo del banco solo se il toml nomina `junit_fake`).

## Scelte e scostamenti
- `close_cycle` è ripetibile: su un ciclo già chiuso riprende fase e blocco rimasti a metà. Motivo del blocco `needs_you` del revisore: «il revisore finale chiede una decisione (ciclo n)».
- Al tetto la fase passa a `execution` (causa `needs_fix`) e poi si apre il blocco: dopo lo sblocco si torna in `execution`, dove `task start --from-findings` funziona.
- `add_report` rifiuta (ValueError) una fonte non attesa, una ripetuta e un ciclo non in stadio `review`. `supersede` rifiuta un ciclo già chiuso. I Task 5 e 7 devono tenerne conto.
- Eventi: `review_cycle` solo alla chiusura (anche `superseded`), `finding` a ogni cambio di esito o decisione. `set_finish` non scrive `finish_check`: lo registra il chiamante (Task 7).
- `patch_id` usa `git diff --binary --no-ext-diff --no-textconv` (il brief dice solo `git diff`), per non farsi ingannare da diff binari e non eseguire driver del repo.
- `blocking_open` e DoD: `downgraded:<g>` accetta qualunque gravità valida, anche verso l'alto.

## Evidenza TDD
- RED: `python3 -B -m unittest tests.test_db tests.test_phases tests.test_intents tests.test_reviews tests.test_dod tests.test_acts tests.test_stats tests.test_git tests.test_flowkit` -> 159 test, `FAILED (failures=3, errors=30)` (moduli e funzioni mancanti, versione 3 invece di 4).
- GREEN: stesso comando -> OK. `tests/run`: python3.11 e python3.13 `Ran 1078 tests ... OK`.
- Un bug trovato dai test: in `compute_dod` la voce `skip` veniva aggiunta due volte (corretto con `continue`).

## Test aggiunti
Quelli del brief più: `test_related_receipt_ignored`, `test_superseded_not_counted`, rejected normalizzati (`severity="critical"`, `line="2"`), `set_pr`/`set_finish`/`add_extra_cycles`/`set_review_unverified`, `has_approval`, `intents.complete`, `Ctx.approved_waivers` che delega, creazione di `phase`+`from_approved_spec`, `test_junit_fake_writes_report_from_ids`. `test_is_blocking` è in `test_reviews.py` come da brief (nessun test aggiunto in `test_verdicts.py`). In `test_dod.py` e `test_phases.py` ho aggiunto classi base senza test (`DodBase`, `WorkCase`) per non rieseguire i test ereditati.

## Dubbi
Nessuno bloccante. `bin/tollgate_flow/checkpoint.py` `CAPS` non include ancora «cicli di revisione esauriti»: non era nel brief, lo toccherà il task che usa il checkpoint.
