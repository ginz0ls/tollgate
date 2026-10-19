### Verdetti sui rilievi
1. **set_skills_required, task_event e assign in un'unica transazione**: INDIRIZZATO. `taskcmd.py` (diff, ~riga 156) li racchiude in un solo `with db.tx(conn)`. `db.tx` (`bin/tollgate_core/db.py:144-157`) se `conn.in_transaction` rende la stessa connessione senza BEGIN/COMMIT, quindi le tre `with db.tx(conn)` interne (`tasks.py:69, 102, 143`) si uniscono: nessuna transazione annidata, nessun commit proprio, nessun backup/copia del DB nelle tre funzioni (nessun `commit`/`backup`/`copy` in quei corpi). Un'eccezione fa ROLLBACK dell'esterna. `sqlite3.Error` è mappato a `TaskError` (`taskcmd.py:78`). Test `AtomicityTest` (`tests/test_taskcmd.py`): assign mockato che fallisce, stato invariato (pending / review con --fix) e ritentabile; il report mostra RED con `nullcontext` e GREEN 850 test.
2. **Riga `test_files` duplicata in plan.py**: INDIRIZZATO. Resta una sola definizione (`plan.py:28`).

### Danni nuovi nel diff della correzione
Nessuno. La scrittura del brief resta prima della transazione, quindi un fallimento del DB lascia al più un file di brief, che viene riscritto al tentativo successivo.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
