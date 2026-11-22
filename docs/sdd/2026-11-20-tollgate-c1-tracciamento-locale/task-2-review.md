# Revisione Task 2: la storia che non si cancella (f528076..69cf755)

### Aderenza
- ✅ `events_days` predefinito 0 = mai; `housekeeping.py:39-41` chiama `archive_and_prune` solo con `days > 0`; `test_housekeeping_never_prunes_with_zero` verifica nessuna cancellazione e nessun `archive/`.
- ✅ `lookups_days = 180` (`config.py:92`); `housekeeping.py:42` lo passa a `lookups.prune`; `test_lookups_use_lookups_days`.
- ✅ Archivio prima della potatura (`events.py` `archive_and_prune`): lettura, `write_atomic` (via modulo `fsutil`, D8) e `DELETE seq <= last AND at < limit` stanno in un solo `tx` (`BEGIN IMMEDIATE`, `db.py:217-230`). Se `write_atomic` solleva, `tx` fa ROLLBACK e l'errore risale; `housekeeping.step` lo cattura (`OSError`/`sqlite3.Error`) e lo trasforma in avviso. La connessione è in autocommit (`isolation_level=None`, `db.py:297`), quindi `tx` apre davvero una transazione propria (nei chiamanti `start.py:241,511` non c'è una transazione già aperta).
- ✅ D5: 0..36500 per le tre chiavi (`config.py:128,185-187`), test per -1, 36501 e gli estremi. D8: `mkdir(mode=0o700, parents=True, exist_ok=True)` e `fsutil.write_atomic` via modulo. D21: `prune_events` rimossa, nessun chiamante residuo in `bin/` (grep). D1: `test_housekeeping` e `test_malformed_sessions...` con `[retention] events_days = 180` e asserzione sull'archivio. `templates/tollgate.toml` invariato. Solo libreria standard.
- Strade per cui un evento sparisce senza essere nell'archivio:
  - due `start` insieme: il secondo aspetta il lucchetto (busy_timeout), poi rilegge e non trova righe (`(0, None)`); se il timeout scade è un `sqlite3.OperationalError`, che diventa avviso senza cancellare. OK. ⚠️ non c'è un test con due processi veri (solo `in_transaction` durante la scrittura).
  - archivio con lo stesso nome già presente: il nome dipende da primo e ultimo `seq`, e `seq` non si riusa (AUTOINCREMENT, `test_archive_seq_never_reused`); un file orfano di una transazione non confermata viene riscritto con contenuto uguale o più ampio, mai perso. OK, ma non testato.
  - stessa chiamata ripetuta: `(0, None)`, nessun file in più (`test_archive_twice_is_noop`).
  - cancellazione e lettura hanno lo stesso predicato nella stessa transazione con lucchetto: nessuna riga può entrare tra le due.
- ⚠️ Evidenza della suite: dichiarata nel report (`suite-task-2.log`, 4193 test ×2 interpreti OK); non rilanciata.

### Punti di forza
- Il lucchetto di scrittura è preso prima della lettura, quindi la vecchia corsa lettura/cancellazione non esiste. La condizione `seq <= last AND at < limit` coincide esattamente con le righe archiviate.
- Test mirati: fallimento della scrittura (e `in_transaction` falso dopo), assenza di tocco al disco, permessi 0700, lucchetto durante la scrittura con spia sul vero `write_atomic`.
- Modifiche piccole e coerenti con i pattern esistenti.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `bin/tollgate_core/fsutil.py:8-21` (`write_atomic`) non fa `fsync` né sul file né sulla cartella: dopo un'interruzione di corrente tra il COMMIT del DELETE (durevole in SQLite) e la scrittura su disco del file, l'archivio potrebbe mancare. Il difetto sta nel helper condiviso, non nel diff; il piano prescrive `write_atomic`. Da verificare/valutare in un task a parte o nella revisione finale.
2. `tests/test_events.py` (diff, `ConcurrencyTest.test_three_writers`): l'import `fsutil` aggiunto nel codice del sottoprocesso non serve. Rimuoverlo.
3. `events.py` `archive_and_prune`: carica in memoria tutte le righe da archiviare in una sola passata; con anni di eventi e `events_days` impostato la prima volta il file può essere grande. Accettabile (eventi piccoli), da ricordare nella pagina d'uso del Task 8.
4. `archive/` già esistente con permessi più larghi non viene corretta (`mkdir` con `exist_ok` non cambia il modo). Trascurabile: la crea sempre tollgate.
5. Test mancanti, non bloccanti: collisione di nome con un file già presente (riscrittura senza perdita) e due processi reali che archiviano insieme.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni D1, D5, D8, D21 rispettati; nessuna strada trovata per cui un evento si cancella senza essere nell'archivio (lettura, scrittura e DELETE sotto lo stesso lucchetto, errore di scrittura = ROLLBACK). Restano solo rilievi Minor, il più rilevante riguarda la durabilità di `write_atomic` (fuori dal diff).
