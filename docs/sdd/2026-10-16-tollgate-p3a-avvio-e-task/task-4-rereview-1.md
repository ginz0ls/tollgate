### Verdetti sui rilievi
1. **`worktree prune` globale / `--force` mirato**: INDIRIZZATO. `worktree_prune` rimosso (gitw.py). `force` passato solo se `wt.resolve()` è tra i percorsi registrati (`start.py:_restore_worktree`, `git.worktrees` risolve i path, git.py:105-115) e solo nel ramo `recreated = not wt.exists()`: una cartella esistente con contenuto non arriva mai a `worktree add`. Il percorso è sempre quello del lavoro. Test `test_resume_keeps_other_missing_worktrees_registered` (secondo worktree spostato, resta registrato) e `..._registration_removed`.
2. **`housekeeping.run` in `_resume`**: INDIRIZZATO (start.py, `notes.warnings.extend(housekeeping.run(...))`); test `test_resume_runs_housekeeping` (segnalino morto rimosso, quello corrente resta).
3. **Test del crash con rmtree**: INDIRIZZATO. `test_resume_recreates_missing_worktree` usa `shutil.rmtree`; il caso a registrazione rimossa ha un test a parte.
4. **Rifiuto con avvisi**: INDIRIZZATO. Il rifiuto include gli `avviso:` raccolti; `test_resume_failed_recreation_refuses_with_warnings`.
5. **issue.md dopo la ricreazione**: INDIRIZZATO. `_write_issue` (stessa funzione dell'avvio, quindi stesso recinto "DATO NON FIDATO") solo se `recreated`; se gh fallisce c'è un avviso esplicito. Tre test (riscrittura, senza gh, worktree esistente intatto).

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: con `--force` git smette anche di rifiutare un ramo già in uso in un altro worktree; accade solo se il percorso del lavoro è registrato-mancante e lo stesso ramo è attivo altrove (caso quasi impossibile, nessun test).

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
