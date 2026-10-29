# Revisione Task 2 (e1d286e..468b7d7)

### Aderenza
- ✅ Migrazione 6 (`db.py` SCHEMA_V6, MIGRATIONS): tabella, CHECK su `kind`, indice `lookups_task(work, task)`, `tasks.research_note/research_ok`, `work_items.research DEFAULT 0`. La copia `migrazione-6` la fa `_migrate` (db.py:259-260) come per 2-5, solo se il DB non è nuovo; i lavori esistenti restano a `research = 0` (test `test_migration_keeps_existing_works_outside`, con DB a versione 5, lavoro `execution`, task `running`).
- ✅ `lookups.py`: `KINDS`, `Lookup`, `record` (ValueError per kind ignoto e target vuoto; scrive con `db.tx`, che si unisce a una transazione già aperta, come gli altri moduli; nessuna scrittura fuori dal modulo), `for_task` senza doppioni, `set_note`/`note`, `prune`.
- ✅ D10 del controller: `record` salta la terna già presente con `task IS ?` (corretto anche con task NULL); `prune` cancella solo i lavori `phase = 'closed'` con `updated < now - days` (lookups.py:193-201). Il test copre: chiuso vecchio cancellato, attivo e chiuso recente no, seconda corsa 0.
- ✅ `create_work(research=False)` scrive `int(research)`; `start.py:495` e `adopt.py:325` passano `True` (deroga della decisione 10) con test dal programma vero.
- ✅ `reset_plan` (scope.py:298): `detach_tasks` dopo la cancellazione dei task, dentro la stessa transazione, prima dell'evento. Il numero riusato dal piano nuovo non eredita le letture; non c'è collisione con il dedup di `record` perché le righe vecchie hanno task NULL. L'uscita anticipata con `plan_sha` NULL non lascia letture agganciate a task inesistenti.
- ✅ Eventi `research_note`, `research_reminder`; componente `research_note` True; passo «letture» in `housekeeping.run` con `events_days`, dentro `step` (un errore diventa avviso).
- ✅ Test di versione portato a 6; `MigrationV5Test` ora usa `str(db.latest_version())`: modifica corretta e necessaria (altrimenti fallirebbe con la 6).
- ✅ Aggiunta `detach_tasks`: giustificata (le scritture su `lookups` restano nel modulo), strati rispettati (`scope` core importa `lookups` core).
- ⚠️ Fallimento `test_db_restore_interactive_eof_and_ctrl_c`: nel diff nessun legame con `db restore`/pty; lo rilancia il controller.

### Punti di forza
Migrazione minimale e idempotente nel meccanismo esistente; `IS` per il task NULL; potatura limitata ai lavori chiusi; test della migrazione dal DB v5 vero con controllo della copia; nessuna dipendenza nuova.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.
**Minor**
- tests/test_lookups.py:659: manca un test che il dedup valga anche con `task=None` (la ragione di `IS`, lookups.py:155); oggi una regressione a `=` passerebbe.
- tests/test_scope.py:760: il test non verifica che le righe staccate restino nel DB con task NULL né che una nuova lettura del "nuovo task 2" non venga scartata come doppione; è garantito dal codice ma non asserito.
- lookups.py:197: `prune` usa `updated` come proxy dell'ora di chiusura (dichiarato): un lavoro chiuso e poi toccato (es. evento tardivo) ritarda la potatura. Accettabile per D10.
- lookups.py:179: `set_note` su un task inesistente non fa nulla in silenzio (rowcount 0); i chiamanti futuri (Task 3+) dovrebbero verificare l'esistenza del task.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e decisioni D10/14/16 rispettati, migrazione con copia prima e lavori esistenti a `research = 0`, `reset_plan` corretto nell'ordine, nessun rilievo bloccante; solo rifiniture di test.
