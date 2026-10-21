# Task 4, ri-revisione del giro di correzione 1

### Verdetti sui rilievi
1. **`_own_document` ripeteva l'esenzione di `reviews/<issue>/`; in `violations.py` niente letterale del percorso**: INDIRIZZATO. Il ramo è tolto da `bin/tollgate_flow/finishcheck.py` (`_own_document`) e il docstring è riscritto (resta solo la spec approvata). `bin/tollgate_core/violations.py` usa `REVIEWS_DIR` (import da `tollgate_analysis.approvals`, strato ammesso; `approvals.py` importa solo stdlib): `grep "docs/superpowers/reviews"` su violations.py non dà più nulla. `approvals_mod` è ancora usato in finishcheck.py:191,243.
2. **`blob_at` solo blob, `None` per cartella o assente; test**: INDIRIZZATO. `bin/tollgate_core/git.py` usa `ls-tree -z ref -- path` e accetta solo la voce `blob` con nome uguale a `path`. Verificato a mano su un repo temporaneo: `d`, `d/`, `d/s`, `nope` danno `None`; `d/f.md` e `d/s/x.md` (sottocartella) danno lo SHA; `d/f` (prefisso comune a `d/f.md` e `d/f.mdx`) dà `None`. Test: `tests/test_git.py` `test_blob_at_directory_is_none` (copre anche il file in sottocartella). Manca un test esplicito per il prefisso comune: il comportamento però è corretto.

### Danni nuovi nel diff della correzione
Nessuno. Il report cita i test mirati e la suite (1482 test, due interpreti).

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
