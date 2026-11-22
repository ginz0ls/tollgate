# Revisione Task 1 (055dc80..f528076)

### Aderenza
- ✅ `SCHEMA_V7` con le tre istruzioni esatte della decisione 1 (`bin/tollgate_core/db.py`, blocco SCHEMA_V7): CHECK `size IS NULL OR size IN ('small','medium','large')`, `size_by IS NULL OR size_by IN ('rules','user')`, `slices INTEGER` nullabile; `(7, SCHEMA_V7)` in `MIGRATIONS`; `latest_version() == 7`.
- ✅ Cinque tipi esatti in `events.EVENT_TYPES`; `ENVELOPE_VERSION` resta 1 (nessuna modifica).
- ✅ Spec 18.4: cambia solo la riga `**Tipi:**` (1 riga nel diff), con soli nomi tra backtick (D17); `tests.test_docs` verde.
- ✅ D2: `"6"` -> `str(db.latest_version())` in `MigrationV6Test`; le asserzioni su `migrazione-6` restano; `test_latest_version_is_6` rinominato `_is_7`.
- ✅ Test richiesti presenti: colonne, migrazione da 6 con righe e copia `migrazione-7`, CHECK (valore non valido su `size` e `size_by`, più caso valido), tipi nuovi con `v == 1`.
- ✅ Solo libreria standard, nessun `__pycache__` (git status pulito, nessun pycache nel commit), nessun nome utente/host.
- Verifica mia: `python3 -B -m unittest tests.test_db tests.test_events tests.test_docs` -> 55 test OK. La suite completa (4184 test su 3.11 e 3.13) è affermazione del report, non rieseguita.
- Controllo dei chiamanti: nessun altro codice o test in `bin/` o fuori da `tests/test_db.py` dipende da versione 6 o `migrazione-6`.

### Punti di forza
Diff minimo e chirurgico; test della migrazione da 6 che usa il pattern esistente (`MIGRATIONS[:]` troncato) e verifica sia le righe sia la copia di sicurezza; il caso valido dopo i CHECK evita che il test passi per un vincolo troppo stretto.

### Rilievi
- Critical: nessuno.
- Important: nessuno.
- Minor: `tests/test_events.py` (nuovo test) verifica `v == 1` e il tipo, ma non il round-trip di `data` (`{"x": 1}`); copertura sufficiente per il task.
- Minor: il CHECK su `slices` non c'è, ma la decisione 1 non lo prevede (corretto).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** schema, tipi, riga 18.4 e decisioni D2/D17 corrispondono esattamente al brief; i test mirati passano e non ci sono effetti sui chiamanti.
