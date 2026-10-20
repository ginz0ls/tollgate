# Task 13 - report

## Implementato
- `gitw.worktree_remove(repo, path)`: `git worktree remove <percorso>` senza `--force`; `GitWriteError` se sporco.
- `bin/tollgate_flow/closing.py`: `abandon`, `CleanupItem`, `cleanup`, `collect`.
  - `abandon`: atto `abandon` con target N, lavoro attivo per (repo, N), `set_phase(closed, abandoned)`, atto consumato dopo la chiusura; ramo, worktree e PR restano.
  - `cleanup`: senza `--confirm` elenca ed esce con 3 senza consumare l'atto; con `--confirm` consuma l'atto e poi toglie worktree (mai `--force`, mai se sporco) e ramo (`delete_branch` sullo SHA letto in quel momento, che il messaggio riporta per il recupero). Mai toccati: ramo del checkout principale, rami di lavori attivi, worktree in cui si trova `cwd`. Gli orfani (`tg/<N>-*` locali che non sono il `branch` di nessuna riga del repo) sono indicati con «adottalo con /tollgate:adopt #N, se non c'è già un lavoro attivo»; con `--orphans` entrano nell'elenco. Niente da togliere: codice 0 e atto non consumato.
- `cli.py`: sottocomandi `abandon N` e `cleanup [--confirm] [--orphans]` con `argv` per `cli_session`.
- `start._resume`: dopo il fetch `prstate.detect`; `merged` -> «lavoro #N chiuso: la PR è stata unita (PR #n)», codice 0, nessun `EnterWorktree`; `closed` -> voce di conferma con `closed_line` (CLOSED_HINT), codice 3; con `--confirm` `set_pr(None, None)` e ripresa normale; errore di `gh` -> avviso e ripresa.
- C11: `_common.closed_tg(ctx, repo)` nuova; `orphan_tg` invariata; `_common.orphan_next` sceglie il comando (`/tollgate:cleanup` o `/tollgate:adopt #N`), usata da `writes.py`, `bash_rules.py`, `session.py`.

## TDD
RED (`python3 -B -m unittest tests.test_closing`): 11 failure e 2 error, per esempio
`tollgate: error: argument cmd: invalid choice: 'cleanup'` e `'/tollgate:cleanup' not found in "tollgate: ramo tg/7-* senza lavoro nel DB ..."`.
RED (`tests.test_start.ResumeTest`): `AssertionError: 0 != 3 : lavoro #7 ripreso ...`, `'lavoro #7 chiuso: la PR è stata unita' not found`, `'avviso: PR #1: stato non letto' not found` (3 failure).
GREEN: `python3 -B -m unittest tests.test_closing tests.test_start` ok; `tests/run`: python3.11 1363 test OK, python3 (3.13.5) 1363 test OK.

## File
bin/tollgate_flow/closing.py (nuovo), gitw.py, start.py, bin/tollgate_core/cli.py, bin/tollgate_checks/_common.py, writes.py, bash_rules.py, session.py, tests/test_closing.py (nuovo), tests/test_start.py.

## Scostamenti dal piano
- Test in più: `GitwWorktreeRemoveTest`, `test_abandon_without_active_work_refuses`, `test_cleanup_needs_act`, `test_cleanup_keeps_active_work`, `test_cleanup_never_touches_branch_of_main_checkout`, `test_cleanup_does_not_list_branch_of_other_repo_work`, `test_open_pr_resumes_normally`, `test_unreadable_pr_state_warns_and_resumes`, hint su SessionStart e Bash.
- Gli orfani sono i soli rami `tg/<N>-*` (come `orphan_tg` e `naming.branch_name`), non qualunque `tg/*`: serve N per l'indicazione di `adopt`.
- `update-ref -d` non rifiuta un ramo estratto: per questo `cleanup` salta il ramo del checkout principale e rimuove prima il worktree.

## Dubbi
- `cleanup --confirm` con avvisi (worktree sporco) esce 0, con le righe `avviso:`.
- Un lavoro `pr_open` con PR scollegata resta in `pr_open` (si esce con `--reopen-execution`, avviso già esistente).
- Il comando da ripetere stampato dal codice 3 usa `program_command(db.BIN_PATH)`.
