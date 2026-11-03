# Report Task 4 (rilevamento per contenuto)

## Implementato
- `git.grep_files_at(repo, ref, markers, pathspecs)`: un `git grep -z -I -l -F -e ...`; rc 1 senza output = `[]`; altri errori e timeout = `GitError`; prefisso `<ref>:` tolto; `_check_ref`.
- `init.detect_files(repo, ref, frags, sizes, warnings=None)`: un grep per frammento con marcatori (D3), pathspec `:(glob)**/*.<ext>`, filtri dopo (prefissi esclusi, cartelle test, nomi test, tetto 256 KiB da `sizes`). `GitError`: area vuota e riga di avviso in `warnings`.
- `init.propose`: carica i frammenti approvati, chiama `detect_files`, passa `detected=` a `profile_blocks`; avvisi in `lines` e nel README (sezione "Avvisi sul rilevamento").
- D17 era già in `_drift` (negazioni); test sui due ordini aggiunto. D16 rispettata (nessun `tollgate <sottocomando>` nudo, niente "protezione").

## Scostamenti dal piano
- `detect_files` ha un parametro extra opzionale `warnings` (il ritorno resta il dict del piano): serve per la riga di avviso.
- `test_real_default_root_is_the_plugin`: `fragments.load` ora è chiamato due volte (propose e profile_blocks); il test confronta l'insieme delle radici invece della lista.
- I test di `grep_files_at` stanno in `LsFilesAtTest` (repo già con file).

## TDD
- RED git: `W/task-4-red-git.out` (AttributeError: no attribute 'grep_files_at', 2 errori). RED init: `W/task-4-red-init.out` (3 failures, 6 errors, DetectTest).
- GREEN: `python3 -B -m unittest tests.test_git tests.test_init tests.test_layers`: 153 test OK (skipped=1).
- Suite completa: `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3326 test OK su python3.11 (skipped=3) e python3.13 (skipped=1), nessun unclosed (`W/task-4-suite.out`).

## Autorevisione
Completa rispetto a brief e carry; nessun extra; nessun `__pycache__`; non toccato `approved`.
## Dubbi
Nessuno. `fragments.load` doppio è trascurabile.

## Fix round 1
- Aggiunto `DetectTest.test_failed_grep_of_one_fragment_does_not_stop_the_others` (due frammenti x e y, il grep di x solleva `GitError`: risultato `{"x": [], "y": ["src/ok.py"]}`, una sola riga di avviso che nomina x). Test di guardia: verde subito, il codice già si comportava così.
- I test di `grep_files_at` spostati da `LsFilesAtTest` in `GrepFilesAtTest` (tests/test_git.py).
- Comando: `python3.11 -B -m unittest tests.test_git tests.test_init` e lo stesso con `python3`: 147 test OK (skipped=1) in entrambi.
