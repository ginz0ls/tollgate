# Task 17 report: git commit e PostToolUse Bash

## Implementato
- `bin/tollgate_checks/_common.py`: `commit_violations` (test-guard + scope, esclusi `output_dirs` e `.tollgate-run/` (C9), deroghe anche pending via `unresolved`).
- `bin/tollgate_checks/commit.py` (pre_bash, ordine 25): working tree + indice + non tracciati vs HEAD; `_inside` (C13); deny se L0 cresce o ci sono violazioni senza deroga.
- `bin/tollgate_checks/post_bash.py` (post_bash, ordine 20): eventi `commit` + `task_commit`, controllo di ogni commit nuovo vs primo genitore, blocco `needs_you` (non riaperto se il lavoro e' gia' `blocked`), ramo cambiato, livello ricalcolato. C8: senza commit nuovi, se un `finish` pending ha `head_sha <> HEAD` registra `invalidate_finish`.
- `bin/tollgate_hooks/apply.py`: nuova operazione `invalidate_finish` (necessaria a C8: `commit` scrive anche un evento, qui non c'e' commit).
- Il consumo degli effetti resta solo in `effects.py` (Task 16): nessuna duplicazione.

## Scostamenti dal piano
1. `test_pending_test_waiver_lets_commit_pass`: `write_waiver` crea deroghe senza `tests`, ma la violazione di test cancellato ha `ids` e `covers` richiede sottoinsieme. Il test ora scrive una deroga con gli id; aggiunto `test_waiver_missing_a_test_id_does_not_cover`.
2. `commit_violations` filtra le esclusioni; `commit.py` passa anche `exclude` a `git.changes`.
3. `post_bash._block`: niente nuovo blocco se la fase e' gia' `blocked` (open_block fallirebbe); il deny resta.
4. `rev_list` in try/except GitError.
Test aggiunti: C9 (coverage/ e .tollgate-run/), C8 (finish su A, `reset --soft HEAD~1` -> expired; un comando senza movimento di HEAD lo lascia pending).

## TDD
RED: `python3 -B -m unittest tests.test_check_commit tests.test_check_post_bash` -> FAILED (failures=11), moduli assenti.
GREEN: stesso comando con `-W error::ResourceWarning` -> 16 test OK. `PYTHONWARNINGS=error::ResourceWarning tests/run`: 562 test OK su python3.11 e python3 (3.13.5).

## Dubbi
Nessuno bloccante. Con `git commit <pathspec>` si controlla comunque tutto l'albero (conservativo, decisione 17).
