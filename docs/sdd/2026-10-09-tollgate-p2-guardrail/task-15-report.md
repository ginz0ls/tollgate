# Task 15 - Report

## Implementato
- `bin/tollgate_checks/writes.py` (pre_edit, ordine 20): file protetti (anche `.git/hooks`, `.git/config`, sessione legata e non legata), orfano `tg/*` (decisione 16), checkout principale, spec/piano bloccati, fasi solo-docs (in `blocked` vale `phase_before_block` per la regola dei piani), L0 libero, coordinatore negato in L1/L2, scope con deroghe (componente `scope_check`).
- `bin/tollgate_checks/post_edit.py` (post_edit, ordine 20): `level_records` + `plan-check` (componente `plan_check`).
- `_common.py`: `_inside` (una sola copia, C13), `edit_target` (percorso risolto, collegamenti compresi), `output_excludes`, `scope_exempt`, `level_records`.
- `tollgate_core/git.py`: parametro `exclude=()` su `changes` e `diff_size` (pathspec `:(top,literal,exclude)` per il tracciato, filtro per i non tracciati); `_excluded` reso pubblico come `excluded` (stesso uso interno).

## Decisioni del controller
- C3: test per `main/.git/hooks/x`, `main/.git/config`, `wt/.git/...` in sessione legata; `main/.git/...` in sessione non legata e senza alcun lavoro.
- C9: `review.output_dirs` + `.tollgate-run/` esclusi da livello (changes e byte) e dallo scope (`scope_exempt`). Test con `reports/junit.xml` non ignorato (Lab senza `.gitignore`), con controllo che lo stesso volume fuori da output_dirs alzi il livello.
- C13: `_inside` solo in `_common.py`.
- Scope letterale: lo scope registrato si confronta per uguaglianza di stringa (nessun glob applicato), quindi `[ ]` e `*` nei nomi non sono mai pattern; `globs.escape` non serve. Solo `[scope] always` usa i pattern. Test: `app/[id]/page.tsx` ammesso, `app/i/page.tsx` negato; `src/a*.py` ammesso, `src/ab.py` negato.
- Decisione 18: changes con i non tracciati e `diff_bytes` = diff + dimensione dei non tracciati (già in `git.changes`/`diff_size`). Test: un solo file non tracciato da 5000 byte porta L0 a L1; file tracciato da 5000 byte idem.

## Scostamenti dal piano
- Il percorso si risolve con `.resolve()` (`edit_target`) prima di ogni decisione, anche in post_edit.
- Checkout principale: non basta essere dentro la radice del principale; si esclude un altro worktree annidato nel principale (caso reale: `.claude/worktrees/` sta dentro il principale). Test dedicato.
- In `blocked` la regola «niente piani» in `spec_audit`/`approval` usa `phase_before_block`.
- `git.worktrees` che fallisce con GitError: nessun deny (fail-open sul solo ramo checkout principale).
- `level_records` non cattura GitError: lo gestisce il runner (modulo informativo in post_edit).

## Test e TDD
- RED: `python3 -B -m unittest tests.test_check_writes tests.test_check_post_edit tests.test_git` -> `FAILED (failures=43, errors=2)` (Ran 56).
- GREEN mirati: `tests.test_check_writes tests.test_check_post_edit` -> 38 test OK; `tests.test_git` -> 18 OK.
- Suite: `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` -> Ran 472, OK. `tests/run` -> 472 OK con 3.11.16 e 3.13.5.
- Nuovi test: 38 (writes + post_edit) e 2 in test_git (432 -> 472).
- Casi: nuove cartelle, spazi nei percorsi, collegamenti simbolici (verso cartella fuori scope, verso file protetto, verso il principale, worktree raggiunto da un link).

## File
- `bin/tollgate_checks/_common.py`, `writes.py`, `post_edit.py`
- `bin/tollgate_core/git.py`
- `tests/test_check_writes.py`, `tests/test_check_post_edit.py`, `tests/test_git.py`

## Dubbi
- Nessun controllo di sola lettura per gli agenti `readonly` su Edit/Write: la tabella 7.2 non lo prevede per questa riga (copre 7.3 a SubagentStop).
- Un collegamento simbolico in scope che punta a un altro file viene giudicato sul bersaglio, non sul nome del collegamento (scelta prudente).

## Fix round 1
- Protezione con repo annidato (writes.py): `_protected` valuta `is_protected` su ogni radice pertinente (repo più vicino, worktree del lavoro, repo del contesto); basta una che dica protetto. Test `NestedRepoTest` (`git init` su `docs/superpowers/reviews/7` e su `.tollgate`), sessione legata e non legata.
- `git.worktrees` che fallisce: ora nega con messaggio «non è stato possibile verificare i worktree». Test `test_worktrees_failure_denies`.
- Sessione legata che scrive nel worktree di un altro lavoro attivo: negato, il messaggio nomina `#N`; `/tmp` resta permesso. Test `test_other_active_work_is_denied_but_tmp_is_allowed`.
- post_edit: `_plan` calcolato prima; `level_records` in try/except che diventa un avviso. Test `test_level_failure_does_not_block_plan_registration`.
- RED: 7 fallimenti sui 4 test nuovi. GREEN: `python3 -B -m unittest tests.test_check_writes tests.test_check_post_edit` -> 43 OK.
- Suite: `-W error::ResourceWarning` e `tests/run` (3.11 e 3.13) verdi, 477 test.
