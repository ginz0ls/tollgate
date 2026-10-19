# Ri-revisione giro 1 Task 5 (fdf5d7b..54a7894)

### Verdetti sui rilievi

**Important 1: `_file_values` raccoglieva i testi tra apici dei commenti, gonfiando lo scope.**
INDIRIZZATO. `plan.py` ora legge solo l'elenco iniziale (`_ITEM`/`_SEP`, `_PAREN_AT` salta la parentesi dopo la voce, ci si ferma al primo testo non-voce). Verificato con esecuzione mirata `python3 -B` che confronta `check_plan` di 65f31ba e del nuovo codice su tutti i piani di `docs/superpowers/plans/`:
- P0 17/17 e P1 27/27: identici, nessuna voce persa o aggiunta.
- P2-guardrail 83 -> 104, P3a 42 -> 83: voci perse nessuna; le voci in più sono tutte file veri di righe con più file (es. riga 220 del P3a `tests/test_check_cli_calls.py`, `tests/test_layers.py`; riga 673 `LICENSE`, `LICENSES/superpowers-MIT.txt`; riga 813 `docs/verifiche/...prova-flusso.md`; riga 845 il piano principale). Nessuna voce spuria (niente `size.task_lines`, `_GENERATED`, `/tollgate:*`, nomi di funzione, testi di commento).
- Il piano P3a resta valido (problemi `[]`).
- Gli altri piani senza task (`nucleo`, `p2-esecuzione`, brief-sessione, esecuzione) danno lo stesso esito di prima.
Test aggiunti (`tests/test_plan.py`): `test_comments_after_files_are_not_files` (quattro casi, compresi i due del rilievo), `test_real_plans_keep_their_scope` (conteggio e digest per P0, P1, guardrail), `test_p3a_plan_stays_valid_without_comment_files`. Il report mostra il RED con il codice precedente e la suite verde.

**Minor: `test_generated_patterns` asserisce solo `len == 4`.**
INDIRIZZATO. `tests/test_size.py` ora confronta la lista con i quattro pattern.

### Danni nuovi nel diff della correzione
Nessuno. Nota non bloccante: i digest fissati in `test_real_plans_keep_their_scope` per il guardrail (104) congelano anche le voci in più volute; accettabile, dichiarato nella docstring.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
