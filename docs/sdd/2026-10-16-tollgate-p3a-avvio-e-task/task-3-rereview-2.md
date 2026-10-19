# Task 3, ri-revisione del giro di correzione 2

### Verdetti sui rilievi
1. **`gitw.delete_branch` con `branch -D` incondizionato (poteva cancellare un ramo preesistente)**: INDIRIZZATO.
   - `bin/tollgate_flow/gitw.py` (`delete_branch`): ora `git update-ref -d refs/heads/<ramo> <expected_sha>`; con il vecchio valore atteso git rifiuta se il ramo punta altrove (atomico). Mai `branch -D`. `_run` non solleva sul returncode, quindi `returncode == 0` è il segnale corretto; `GitWriteError` (timeout/git assente) -> `False`.
   - `bin/tollgate_flow/start.py` (`_create`): `mkdir` separato in un proprio `try/except OSError` che rifiuta senza cancellare nulla; `delete_branch(main, branch, base_sha)` chiamato solo nel ramo `except GitWriteError` di `worktree_add`, cioè solo se l'add è partito. Se non si toglie, il rifiuto lo dice («il ramo ... è stato lasciato»).
   - Test: `test_failed_add_never_deletes_a_preexisting_branch` (ramo con commit proprio, add fallito, `delete_branch` -> False, SHA invariato), `test_delete_branch_removes_branch_still_at_start_point`, `test_mkdir_failure_never_deletes_branches` (`delete_branch` mockato, mai chiamato; esito 1). Il report mostra RED/GREEN e le suite complete su 3.11 e 3.13.

### Danni nuovi nel diff della correzione
- Minor `tests/test_start.py` (`test_failed_add_never_deletes_a_preexisting_branch`): esercita `worktree_add` e `delete_branch` direttamente, non il percorso `start()` con il ramo che compare dopo `local_branches`; la garanzia sta comunque tutta in `delete_branch` (valore atteso), quindi la copertura è sufficiente. Non blocca.
- Il limite dichiarato nel report (ramo preesistente esattamente a `base_sha`, senza lavoro proprio, verrebbe tolto) è accettabile: nessun commit si perde.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
