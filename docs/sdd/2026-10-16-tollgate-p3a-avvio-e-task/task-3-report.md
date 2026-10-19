# Task 3 — report dell'implementatore

Status: DONE_WITH_CONCERNS (scostamenti dal piano elencati sotto; nessun blocco).

## Cosa è stato fatto
- Nuovo pacchetto `bin/tollgate_flow`: `gitw.py`, `gh.py`, `prereq.py`, `housekeeping.py`, `start.py`.
- Nuovo `bin/tollgate_analysis/naming.py` (puro).
- `bin/tollgate_core/sessions.py`: `prune_bound(conn, state, *, now, stale_minutes)`.
- `bin/tollgate_core/active.py`: `register(..., force=False)` (C6).
- `bin/tollgate_core/cli.py`: sottocomando `start N [--level L1|L2] [--confirm] [--reopen-execution]`; `N` accetta `7` e `#7`. Stampa `lines` su stdout ed esce con `code`.
- Test: `tests/test_naming.py`, `tests/test_prereq.py`, `tests/test_start.py` (`StartNewTest`, `HousekeepingTest`), un test in `tests/test_active_roots.py`.

## Ordine dei passi (C4)
toplevel e checkout principale, remote origin, `fetch` (esito annotato), ramo predefinito con commit, `tollgate.toml` su `origin/<predefinito>` («repo non attivo»), `load_config`, `tollgate.defaultBranch`, `cli_session`, `find_active`. Se c'è un lavoro attivo → `_resume` (rifiuta: «ripresa non ancora disponibile», lo riempie il Task 4). Poi fetch fallito → «senza rete non si avvia un lavoro nuovo»; prerequisiti (raccolti tutti in un solo rifiuto); issue e rami/PR esistenti; controlli; rifiuti `adopt` PRIMA della richiesta di conferma (così non si chiede una conferma per poi rifiutare); codice 3 se servono conferme; creazione.

## Scostamenti dal piano e perché
1. **`gh.issue` usa l'API REST** (`gh api repos/{owner}/{repo}/issues/N`), non `gh issue view --json`: verificato con `gh issue view --json xyz` (gh 2.46.0) che `authorAssociation` non è un campo dell'issue. L'API REST dà `author_association`, `state` (minuscolo, normalizzato in maiuscolo), `labels` come oggetti. Di conseguenza ho esteso `tests/fakegh.py` con la rotta `repos/*/*/issues/N` (dati da `issues`, stessa chiave di prima; la rotta `issue view` resta). Additivo, i test del Task 2 restano verdi.
2. **`gh.commit_state` (C7)** ritorna `dict[str, str]`: `{contesto: stato}` per i soli `tollgate/guard` e `tollgate/verdict` presenti (costante `REQUIRED_CONTEXTS`); `{}` = nessuno presente. `start`: uno non `success` → conferma (3); nessuno presente → avviso «stati di tollgate assenti sul predefinito»; `GhError` → avviso «non leggibili». Aggiunta `gh.auth_ok`.
3. **`tollgate.defaultBranch`** si scrive dopo il controllo «repo attivo», non al passo 3 del brief: non si tocca la config git di un repo non attivo.
4. **`hookkit.Lab` ha il parametro `worktree=True`**; `FlowLab` passa `worktree=issue is not None`. Prima `FlowLab()` creava comunque il ramo `tg/7-demo` e il worktree, quindi `start 7` avrebbe sempre trovato un ramo `tg/7-*` senza riga. Nessun test esistente cambia (default invariato).
5. Nel test `test_hostile...` il recinto atteso è più lungo di ogni sequenza di backtick di titolo, etichette e corpo (tutto sta dentro il recinto, non solo il corpo).
6. `start` non stampa il titolo dell'issue (solo `#N`, livello, ramo e percorso di `issue.md`): il titolo è testo non fidato e l'output arriva al modello.
7. `worktree_add` riceve lo SHA di `origin/<predefinito>` come `start_point` (lo stesso scritto in `work_base_sha`: nessuna corsa tra due letture).

## Comportamenti da sapere
- Autore non in `OWNER|MEMBER|COLLABORATOR` (anche vuoto/sconosciuto) → L2, con avviso.
- `housekeeping.run` non solleva: gli errori diventano righe di avviso. `prune_bound` tiene i segnalini di sessioni in un lavoro attivo o `alive` (stale_minutes = `review.stale_minutes`).
- `reopen_execution` e `claude_dir` sono accettati dalla firma ma `reopen_execution` non è ancora usato (Task 4). `claude_dir` dalla CLI è `Path.home()/".claude"`.
- `git.is_clean` esclude `.claude/worktrees`; `info/exclude` contiene le tre righe di decisione 4, una volta sola.
- Layering: `gitw` usa `tollgate_core.git` (solo `common_dir`); `tollgate_flow` non importa hook né check. `test_layers` verde.

## Evidenza TDD
- RED: con `naming.py` e `start.py` temporaneamente spostati, `python3 -B -m unittest tests.test_naming tests.test_start` → `FAILED (failures=30, errors=1)` (28 test eseguiti).
- GREEN: `python3 -B -m unittest tests.test_naming tests.test_prereq tests.test_start` → `Ran 40 tests ... OK` (41 con il test aggiunto dopo per stati illeggibili: incluso nella suite completa).
- Suite completa: `tests/run` → `Python 3.11`: `Ran 762 tests in 134.834s OK`; `Python 3.13.5`: `Ran 762 tests in 146.424s OK`.

## File cambiati
Creati: `bin/tollgate_analysis/naming.py`, `bin/tollgate_flow/{gitw,gh,prereq,housekeeping,start}.py`, `tests/test_{naming,prereq,start}.py`.
Modificati: `bin/tollgate_core/{active,cli,sessions}.py`, `tests/{fakegh,flowkit,hookkit,test_active_roots}.py`.

## Dubbi
- La skill `start` (Task 10) dovrà passare `--confirm` solo dopo che l'utente ha letto le righe «conferma:»; il modello può passarlo da solo (decisione 6, costo dichiarato).
- Il Task 4 sostituisce `_resume` e il test `test_resume_is_not_available_yet`.
- Un worktree creato e un `create_work` fallito (raro) lascia ramo e cartella: la spec lo copre con «ramo locale `tg/<N>-*` senza riga → adopt».

## Fix round 1

Cambiato:
1. `start.py`: `set_config`, `mkdir` e `worktree_add` sono in `try` (`GitWriteError`, `OSError`) -> rifiuto in italiano, codice 1. Dopo un `worktree_add` fallito il ramo nuovo viene tolto (`gitw.delete_branch`, nuovo): git lo lascia creato e un nuovo `start` avrebbe trovato «ramo locale senza riga» e proposto `adopt`. `WorkExists` ora cita ramo e percorso rimasti (minor 2).
2. Dopo `create_work` ogni registrazione (backup, radici attive, segnalino, `info/exclude`, `issue.md`) è un passo indipendente: se fallisce, le altre proseguono; avviso «registrazione incompleta: <cosa>: <errore>»; **codice d'uscita 4** (`INCOMPLETE`, distinto da 0/1/3), ultima riga sempre `prossimo passo: EnterWorktree <wt>`; la riga con il percorso di `issue.md` manca se non scritto. Scelta del 4: il lavoro esiste e si può entrare, ma il chiamante (skill) deve leggere gli avvisi; la ripresa del Task 4 completa le registrazioni.
3. `housekeeping.run`: ogni pulizia è un passo indipendente (eventi, segnalini, copie temporanee, logs, ctx, segnali CLI); `ValueError`/`TypeError` (sessions malformato) catturati; avviso «pulizia non riuscita (<cosa>)».
4. `prereq.is_github`: timeout (`git.GIT_TIMEOUT_S`), `stdin` nullo, `OSError`/`TimeoutExpired` -> `False`.
5. Test `no_auth`: asserisce «gh non è autenticato (gh auth status fallisce)».

Test nuovi (`tests/test_start.py`, `tests/test_prereq.py`): `test_worktree_add_failure_refuses` (cartella dei worktree in sola lettura; salta se utente privilegiato; asserisce anche nessun ramo residuo), `test_git_config_failure_refuses` (`config.lock`), `test_issue_file_failure_is_incomplete_registration` (`.tollgate-run` è un file nel repo -> `issue.md` non scrivibile; codice 4), `test_exclude_failure_does_not_skip_issue_file` (`info/` in sola lettura), `test_malformed_sessions_do_not_skip_other_cleanups`, `test_prune_events_error_does_not_skip_prune_bound`, `test_is_github_has_timeout_and_survives_git_errors`.

RED: con `bin/` ripristinato al commit precedente, `python3 -B -m unittest tests.test_start tests.test_prereq` -> `FAILED (failures=5, errors=2)` (i 7 test nuovi; il test `no_auth` passava già: è un rinforzo dell'asserzione).
GREEN: stesso comando -> `Ran 43 tests ... OK`. Suite: `tests/run` -> `Python 3.11.16: Ran 769 tests OK`; `Python 3.13.5: Ran 769 tests OK`.

Non fatti (minor): 4 (paginazione `gh`), 5 (`base_sha` in `_checks`), 6, 9. `cli.main` non cambia: gli errori sono gestiti dentro `start`.

## Fix round 2

Cambiato: `gitw.delete_branch(repo, branch, expected_sha) -> bool` usa `git update-ref -d refs/heads/<ramo> <sha>` (atomico: fallisce se il ramo punta altrove), mai `branch -D`. In `start._create` il `mkdir` è separato dal `worktree_add`: se fallisce `mkdir` non si cancella nulla; se fallisce `worktree_add` si prova a togliere il ramo solo se punta ancora a `base_sha`; se non si toglie, il rifiuto dice «il ramo <ramo> è stato lasciato: toglilo a mano se è residuo».
Test nuovi (`StartNewTest`): `test_failed_add_never_deletes_a_preexisting_branch` (ramo con commit proprio, `worktree_add` fallisce, `delete_branch` con lo SHA di partenza -> False, ramo intatto), `test_delete_branch_removes_branch_still_at_start_point`, `test_mkdir_failure_never_deletes_branches` (in-process, `delete_branch` mockato: mai chiamato). Resta `test_worktree_add_failure_refuses` (ramo residuo tolto).
RED: `python3 -B -m unittest tests.test_start.StartNewTest` -> `FAILED (failures=1, errors=2)`. GREEN: `tests.test_start tests.test_prereq` -> `Ran 46 tests OK`; `tests/run` -> 3.11.16: `Ran 772 tests OK`; 3.13.5: `Ran 772 tests OK`.
Limite: un ramo preesistente che punta esattamente a `base_sha` (corsa) verrebbe tolto; è indistinguibile da quello creato dall'add fallito e non porta lavoro.
