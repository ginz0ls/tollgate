## Review Focus

1. **Testo dell'issue ostile** (titolo con `$(rm -rf ~)`, backtick, `"; touch /tmp/x`, emoji, recinti ```` ``` ````): lo slug resta `[a-z0-9-]`, nessun comando riceve il testo, `issue.md` lo racchiude in un recinto più lungo. Test: Task 3 `test_hostile_issue_title_and_body`.
2. **Due sessioni e il segnale della CLI** (due sessioni nella stessa cartella entro 120 s; segnale vecchio; sottocomando diverso): mai la sessione sbagliata. Si rifiuta con un messaggio. Test: Task 2 `test_cli_session_ambiguous_or_stale_refuses`.
3. **Avvio interrotto** (crash dopo `worktree add` e prima della riga; crash dopo la riga e prima del worktree): il secondo `start` propone l'adozione invece di creare `-2`, oppure ricrea il worktree in ripresa. Test: Task 3 `test_branch_without_row_proposes_adopt`, Task 4 `test_resume_recreates_missing_worktree`.
4. **Verdetto falsificato o vecchio** (SHA superato, codice sbagliato, verdetto scritto da un implementatore, revisore che ha cambiato file, JSON in mezzo al testo): mai `approved`. Test: Task 7 `test_verdict_validity_matrix`.
5. **Percorsi con spazi e titoli non ASCII** (il repo stesso è in `.../Plugin IT workflow/`): worktree, brief ed `exclude` funzionano. `FlowLab` crea repo con spazi nel percorso. Test: Task 3 `test_start_creates_work_in_path_with_spaces`.

