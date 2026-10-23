# Task 8: gate guard

## Implementato
- `bin/tollgate_gate/github.py`: read_event, pr_from_event, repo_slug, set_status (JSON via --input), statuses, issue (404 e PR -> None), pr_comments, upsert_comment (prefisso + autore in BOT_LOGINS, corpo con -F body=@file), comment_issue, create_issue, prs_for_commit, shared_sha_prs, open_sentinel_issues (--paginate, niente --limit).
- `bin/tollgate_gate/guard.py`: check() e run(event_path, *, publish, environ, repo=None). Il parametro `repo` (predefinito cwd) e' aggiunto per i test.
- `cli.py`: sottocomando `guard` (--event, --publish), allow_abbrev=False, guardrail D4 estratto in `_require_actions` e condiviso con base-ids.
- `ghcli.api`: nuovo `file_fields` (-F chiave=@file).
- `tests/fakegh.py`: stati, commenti (POST/PATCH), issue, commit_pulls, open_issues, `--include` sulle issue REST.
- Carry rev-t7: test `test_setup_uncounted_is_neither_red_nor_missing` in test_gate_evaluate.py; passa senza modifiche a evaluate.

## Scelte
- Stato rosso = `failure`. Con --publish run risponde 0 (il segnale e' lo stato); senza --publish stampa i problemi come stringhe JSON (una per riga) e risponde 1 se rosso, senza toccare GitHub.
- Ordine rosso: prima commento, poi stato (se il commento fallisce lo stato manca e la protezione blocca).
- PR non verso il predefinito: nessuno stato, solo commento «non applicabile» (stesso prefisso GUARD_PREFIX, quindi sovrascrive un guard precedente).
- SHA condiviso: `error` «SHA condiviso da più PR: chiudine una», nessun commento.
- Testa non piu' quella dell'evento (oggetto assente dopo il fetch): GitError, nessuna scrittura.
- Il confronto dei workflow e' con la punta del predefinito (come la decisione 15 per i file di tollgate): se il predefinito e' avanzato su un workflow, la versione vecchia della PR viene controllata.

## TDD
RED: `python3 -B -m unittest tests.test_gate_guard` -> `ImportError: cannot import name 'github' from 'tollgate_gate'` (Ran 1 test, FAILED errors=1).
GREEN: stesso comando dopo l'implementazione -> `Ran 46 tests ... OK`.
Suite: `tests/run` python3.11: Ran 2064 tests OK (545 s); python3 (3.13.5): Ran 2064 tests OK (505 s).

## Dubbi
Nessuno bloccante. `gh.sentinel_issues` in tollgate_flow/gh.py usa ancora `--limit 100`: non toccato (il brief non lo assegna a questo task); va collegato a `github.open_sentinel_issues`.

## Fix round 1
- I-1: `shared_sha_prs` filtra anche `head.sha == sha`. RED `test_stacked_pr_does_not_make_sha_shared` (dava `error`), ora `success`.
- I-2: titolo e docstring di `render_guard` dicono «tollgate/guard: rosso», senza «in attesa». RED `test_red_comment_says_red_not_waiting` e `test_guard_comment_says_red_not_waiting`.
- M-1: dopo il fetch, `FETCH_HEAD` deve essere la testa dell'evento; altrimenti nessuna scrittura, uscita 0 con un messaggio. RED `test_pr_advanced_since_the_event_writes_nothing`. Il ricontrollo e' subito dopo il fetch, non subito prima del commento (nessuna chiamata GitHub in piu').
- M-3: `protected.WAIVER_FILES`, usato da `REPO_PROTECTED` e da guard.
- M-6: test aggiunti `test_tollgate_file_moved_is_red`, `test_hostile_file_names_stay_inert`, `test_edit_to_other_base_after_green_guard_keeps_green_status` (passavano gia').
- M-7: docstring di ghcli entro 100 colonne.
- Il test del token ora chiama il vero `fetch_ref` (serve a FETCH_HEAD).
- Comando: `tests/run` -> python3.11 Ran 2074 OK; python3 3.13.5 Ran 2074 OK.
