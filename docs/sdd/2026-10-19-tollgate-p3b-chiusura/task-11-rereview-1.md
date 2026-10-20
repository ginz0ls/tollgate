# Task 11 - ri-revisione del giro di correzione 1

### Verdetti sui rilievi
1. **Commit integrati con `--ff-only` non registrati se il rebase va in conflitto (Important, Review Focus 4)**: INDIRIZZATO. `sync.py:_sync` (blocco `try`, dopo `_remote_conflict`) registra con `_record_commits(base..HEAD)` gli eventi `commit` appena HEAD si è mosso, prima di rebase/blocco/divergenza. Test `test_integrated_commits_recorded_when_rebase_conflicts` (test_sync.py): «Update branch» remoto + predefinito in conflitto, codice BLOCKED, nessuno SHA ignoto in `base..HEAD`, `PostToolUse Bash` exit 0 senza nuovi eventi né blocchi. Ho rilanciato `tests.test_sync tests.test_intents tests.test_actapply.ApproveRebaseTest`: 33 OK. Effetto collaterale utile: `test_repeat_after_integrated_merge_is_not_divergent`. Residuo Minor: nel caso «processo morto tra integrazione e registrazione» la ripetizione trova `head == head0` e non registra; il recupero avviene solo se il rebase riesce (`_realign`), non se va in conflitto. Finestra di pochi statement, non bloccante.
2. **Lease del push forzato nell'autorizzazione**: INDIRIZZATO. `intents.authorize_force(..., lease)` salva il lease; `force_lease` è di sola lettura e punta alla stessa riga di `take_force` (`ORDER BY id DESC`, `authorized`). `sync._realign` autorizza con `lease=remote` (punta di origin dopo l'integrazione); `actapply._approve_rebase` con `gitw.remote_sha` all'applicazione (errore = nessun lease); `openpr._publish` usa `force_lease(...) or remote`. Test: `test_force_lease_is_remote_tip_at_sync_and_rejects_newer_remote` (push rifiutato, remoto intatto, autorizzazione `authorized`, nessun `pr edit`), `test_force_lease_is_the_latest_authorized_one`, `test_approve_rebase_force_carries_remote_tip_as_lease`.
3. **Extra: intento chiuso «non riuscito» con qualunque `ERRORS`**: nessun danno. `sync()` ripropone comunque lo stesso insieme come rifiuto e il `raise` resta; il solo cambiamento è che l'intento non resta `requested` per errori diversi da `GitWriteError`.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- `_realign` non rinnova l'autorizzazione se ne esiste già una (`not force_authorized`): il lease di una vecchia autorizzazione non si aggiorna. Un remoto cambiato nel frattempo e non noto viene intercettato come divergenza prima, quindi il caso è raro; Minor.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
