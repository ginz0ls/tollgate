# Task 4 — report

## Implementato
- `db.py`: `SCHEMA_V5` (spec_audit: `code`, `sha`, `spec_sha`, `stage` NOT NULL DEFAULT 'closed' con CHECK, `opened`; work_items: `audit_suspended` DEFAULT '{}'), `MIGRATIONS` fino a 5.
- `events.py`: tipo `plan_reset`.
- `audits.py` (nuovo): `KINDS`, `AGENTS`, `COMPONENTS`, `CAP_REASONS`, `DECLINE_REASON`, `SUSPENDED_LABELS`, `open_round`, `open_round_row`, `supersede`, `close_round`, `rounds`, `any_rows`, `last_closed(conn, work, kinds)` (D16, mai `superseded`), `suspend`, `suspended` (D17, docstring con `in`), `cap_reason` (D19), `cap_kind`.
- `phases.py`: tre cause in `_FORWARD_CONDITION`; `set_spec_path` (solo se nullo); `create_work(from_approved_spec=True)` senza `spec_path` -> `ValueError("from_approved_spec richiede spec_path")` (il controllo di esclusività con `phase` resta prioritario).
- `scope.reset_plan(conn, work, *, now, session=None) -> list[int]`, una transazione, evento `plan_reset {plan_sha, tasks}`.
- `git.ls_files_at` (D11, `ls-tree -r -z --name-only`, split su NUL, `[]` se il riferimento manca) e `git.blob_at` (D15, `rev-parse --verify -q ref:path`).
- `violations.scope_exempt(cfg, work, rel, scope, *, locked=None)`: esenta `docs/superpowers/reviews/<issue>/` (decisione 26); `diff_violations` calcola `locked_docs` una volta per chiamata (D7). La delega di `tollgate_checks/_common.scope_exempt(ctx, ...)` non cambia (il parametro è opzionale), nessun test degli hook toccato.

## Decisione su reset_plan e tabelle collegate (coerente con decisione 12)
- Senza `plan_sha` registrato: no-op, `[]`, nessun evento.
- `subagents.task` (unica tabella che porta il numero del task, senza FK): le righe restano come storico ma con `task = NULL`. Perché: il piano nuovo rinumera i task da 1 e `taskcmd._concerns` cerca per `(work, task, type)`, quindi un report vecchio sarebbe attribuito al task nuovo. `receipts` non ha numero di task; `findings`/`review_cycles` non esistono prima di `review` e `reopen` parte da approval/execution senza task `running`/`review`. Nessuna FK blocca la cancellazione dei task.
- Le righe di `scope` con origine diversa da `plan` (es. deroghe) restano.

## Test
- Nuovi: `test_db.MigrationV5Test` (+ `test_latest_version_is_5`, il test v3->v4 ora asserisce `str(db.latest_version())`), `test_phases` (`EXPECTED["L2"]`/`CAUSES` aggiornate, `test_l2_forward_needs_its_cause`, `test_from_approved_spec_requires_spec_path`, `test_set_spec_path_only_once`; l'esclusività esistente ora passa `spec_path` per testare davvero quel ramo), `test_scope.ResetPlanTest`, `test_git.LsFilesAtTest`/`BlobAtTest`, `test_violations.ReviewsExemptTest`, `test_audits` (tutti i casi del brief più D16, D17, D19, numeri per lavoro).
- RED: `python3 -B -m unittest tests.test_db tests.test_phases tests.test_scope tests.test_audits tests.test_git tests.test_violations` -> `Ran 122 tests ... FAILED (failures=6, errors=16)`.
- GREEN stesso comando -> `Ran 122 tests ... OK`.
- Suite: `tests/run` -> python3.11 `Ran 1481 tests ... OK`, python3 (3.13.5) `Ran 1481 tests ... OK`, output pulito.

## Scostamenti dal piano
- `last_closed` prende `kinds: tuple` (carry D16) invece di `kind=None`.
- `reset_plan` azzera anche `subagents.task` (vedi sopra); `reset_plan` senza piano è no-op.
- `supersede` agisce solo su un giro aperto (un giro chiuso non diventa `superseded`).
- `db` ha un CHECK su `stage` (`open`,`closed`).
- `open_round` numera con `max(number)+1` su tutte le righe del tipo (anche superate) per non riusare mai il numero di un report.

## Dubbi
- Nessun chiamante di produzione di `from_approved_spec` senza `spec_path` trovato nei test (suite verde).
- `blob_at` su un percorso che è una cartella darebbe lo SHA dell'albero: non gestito, non richiesto.

## Fix round 1
- `finishcheck._own_document`: tolto il ramo morto di `reviews/<issue>/` (ora solo in `violations.scope_exempt`, decisione 26); docstring aggiornato. Resta il ramo della spec approvata.
- `violations.py`: i letterali `docs/superpowers/reviews/` sostituiti da `approvals.REVIEWS_DIR` (import da `tollgate_analysis`, ammesso dagli strati).
- `git.blob_at`: ora solo blob. Ho provato `<ref>:<path>^{blob}`, ma git lo legge come parte del nome del file e dava sempre `None`; uso `git ls-tree -z <ref> -- <path>` e accetto solo la voce `blob` con nome uguale a `path`. Una cartella dà `None`. Aggiunto `test_blob_at_directory_is_none`.
- Test mirati: `python3 -B -m unittest tests.test_git tests.test_violations tests.test_finishcheck tests.test_layers` -> `Ran 64 tests ... OK` (i test di finishcheck sull'esenzione passano ora da `scope_exempt`).
- Suite: `tests/run` -> python3.11 `Ran 1482 tests OK`, python3 (3.13.5) `Ran 1482 tests OK`.
