# Ri-revisione giro 1 del Task 2 (6cb106d..6352aa9)

### Verdetti sui rilievi
**I-1 — la copia pre-migrazione poteva essere potata/duplicata dai processi concorrenti; test indebolito:** INDIRIZZATO.
- `bin/tollgate_core/db.py:225-238`: sotto `_migration_lock` si rilegge la versione (`continue` se già migrata) e solo poi si copia (`backup`) e si applica il passo: una sola copia per passo, fatta da chi lo applica, dal DB ancora allo schema precedente.
- `db.py:307-309`: la potatura esclude i nomi con `-migrazione-`, quindi non può più cancellare il punto di ritorno.
- `tests/test_db.py:~380-410`: il test originale è ripristinato e rafforzato (`assert_pre_migration_copy`: copia `migrazione-2` integra, riga presente, `schema_version` 1; una copia per passo). `test_retention_never_prunes_the_pre_migration_copy` copre la potatura con 10 copie recenti. Tolti il test che dava `[]` come atteso e l'`assertLessEqual` tautologico. Il report mostra RED (2 FAIL) e GREEN; il diff conferma ciò che afferma.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Verifiche sul lucchetto (`db.py:204-214`):
- Blocco per sempre: no per eccezioni o morte del processo. L'fd si chiude nel `finally` (anche su `continue` e su eccezione dentro `with`), e il kernel rilascia comunque `flock` alla morte del processo; l'fd non è ereditato (non inheritable di default in Python 3). L'attesa è senza timeout, ma il possessore tiene il lucchetto solo per versione+copia+passo, limitati dal busy_timeout di SQLite; un hook ucciso dal suo tempo massimo libera il lucchetto. Nessun ordine invertito possibile: chi aspetta il flock non tiene lock di scrittura sul DB (la `tx` si apre solo dopo averlo preso).
- macOS: `fcntl.flock` è disponibile e funziona su file locali. Nota: su NFS può non essere affidabile, irrilevante per `~/.local/state`.
- File creato dove non serve: `migrate.lock` si crea solo se un passo è da fare (DB nuovo o aggiornamento). A schema aggiornato il ciclo salta (`target <= current`, `db.py:222`) prima del lucchetto, quindi nessun file né apertura a ogni hook. La cartella `state.root` esiste già (`ensure_dirs` in `open_db`). In una cartella di test (TempState) o di produzione si crea un file da 0 byte, 0600, innocuo; nessun codice elenca `state.root` in modo che lo disturbi (`offlog.py:52` filtra per regex).
- Crescita delle copie `migrazione-*`: Minor. Non potate, ma al massimo una per passo di schema per ogni migrazione reale di un DB non nuovo. Cresce solo con eventi rari (un `db restore` di una copia vecchia seguito da nuova migrazione, o un crash tra copia e passo), non con l'uso. Ogni copia è un intero DB, ma lo schema ha pochi passi e il limite è ragionevole. Non c'è un tetto esplicito: accettabile, da citare se si vuole in «Dopo la v1».

### Osservazioni fuori ambito
- `fresh` (`db.py:220`) è calcolato una volta sola: se un DB nuovo viene creato da un altro processo durante l'attesa e riceve righe prima di un passo successivo, quel passo non avrebbe copia. Finestra stretta e preesistente alla correzione; da tenere per P6.
- Il rilievo CI M-1/M-2/M-3 e la verifica del `main` remoto per `test_task1_script_still_passes...` restano al controller come da revisione.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
