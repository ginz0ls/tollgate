# Task 3, ri-revisione del giro di correzione 1

### Verdetti sui rilievi
1. **Errori di git/filesystem in `start` (rifiuto prima di `create_work`, registrazioni indipendenti dopo)**: INDIRIZZATO. `start.py` (`start`): `set_config` in try con `GitWriteError` e rifiuto in italiano; `_create`: mkdir e `worktree_add` in try con `(GitWriteError, OSError)`, codice 1. Dopo `create_work` ogni passo passa da `step()` (backup, radici attive, segnalino, `info/exclude`, `issue.md`), avviso «registrazione incompleta: ...», codice `INCOMPLETE=4`, ultima riga sempre «prossimo passo: EnterWorktree». Test: `test_worktree_add_failure_refuses`, `test_git_config_failure_refuses`, `test_issue_file_failure_is_incomplete_registration`, `test_exclude_failure_does_not_skip_issue_file`.
2. **housekeeping con pulizie indipendenti**: INDIRIZZATO. `housekeeping.py` `run`: `step()` per eventi, segnalini, copie temporanee, logs, ctx, segnali CLI; cattura anche `ValueError`/`TypeError`. Test: `test_malformed_sessions_do_not_skip_other_cleanups`, `test_prune_events_error_does_not_skip_prune_bound`.
3. **timeout in `prereq.is_github`**: INDIRIZZATO. `prereq.py`: `timeout=git.GIT_TIMEOUT_S`, `stdin=DEVNULL`, `OSError`/`TimeoutExpired` -> `False`. Test: `test_is_github_has_timeout_and_survives_git_errors`.
4. **test `no_auth` con il messaggio completo**: INDIRIZZATO. `tests/test_start.py`, caso «gh non è autenticato (gh auth status fallisce)».

### Danni nuovi nel diff della correzione
- **Important** `bin/tollgate_flow/gitw.py` (`delete_branch`) e `bin/tollgate_flow/start.py` (`_create`, blocco `except (GitWriteError, OSError)`): `delete_branch` esegue `git branch -D <branch>` incondizionato (forma forzata) in QUALUNQUE fallimento del blocco, senza verificare che il ramo sia stato creato da questa chiamata né a che commit punti. Casi in cui cancella un ramo che non è suo:
  - l'`OSError` viene da `mkdir`: `worktree add` non è mai partito, il ramo non è stato creato da noi; se nel frattempo un altro processo ha creato un ramo con quel nome, viene eliminato;
  - `worktree add -b` fallisce proprio perché il ramo esiste già (corsa tra la lettura di `git.local_branches` e l'`add`, per esempio due `start` simultanei): `-D` distrugge il ramo preesistente, anche con commit propri non integrati.
  La finestra è stretta, ma l'operazione è distruttiva e irreversibile (i commit restano solo nel reflog), e `-D` non ha motivo di essere incondizionato. Correzione richiesta: cancellare solo se il ramo esiste ora e punta ESATTAMENTE a `base_sha` (es. `git update-ref -d refs/heads/<branch> <base_sha>`, che fallisce se il valore atteso non coincide), e solo se `worktree_add` è partito (non per l'errore di `mkdir`); più un test: ramo preesistente con commit proprio che non viene toccato quando `worktree add` fallisce. Il test attuale verifica solo il caso felice (nessun ramo residuo).
- Minor `start.py` (`_create`, messaggio di `WorkExists`): dice «creati nel frattempo il ramo e il worktree: rimuovili a mano», corretto, ma dopo `WorkExists` la riga di un altro lavoro esiste già; nessun danno, solo testo.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti, nel senso che i quattro rilievi sono tutti indirizzati ma il diff introduce un danno nuovo Important: `gitw.delete_branch` con `branch -D` incondizionato (vedi sopra). Basta restringerlo a «ramo esistente che punta a `base_sha`, creato dopo il lancio di `worktree add`» e aggiungere il test del ramo preesistente.
