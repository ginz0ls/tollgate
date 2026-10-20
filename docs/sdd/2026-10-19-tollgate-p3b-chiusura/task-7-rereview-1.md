# Ri-revisione giro 1, Task 7 (a9879b7..a336123)

### Verdetti sui rilievi
1. **Important: `TaskError` inghiottito in `_final_brief`, ciclo aperto con must-have vuoti.** INDIRIZZATO. `_must_haves` (`finalreview.py:193-200`) non cattura nulla; è chiamato in `_open` prima di `reviews.open_cycle` (`:118`). `TaskError` diventa `ReviewError` al `:51`. Anche la ripresa in stadio review rilegge il piano (`_resume`, `must_haves is None`). Test `test_unreadable_plan_refused_before_opening_cycle` (`tests/test_finalreview.py:131`): `ReviewError` e `reviews.count == 0`; eseguito con `python3 -B`, OK.
2. **Minor: import `phases` inutilizzato.** INDIRIZZATO. Tolto da `finalreview.py:16`.
3. **Minor: `"v": 1` nei JSON dei brief.** INDIRIZZATO. `brief.py` nei blocchi del revisore finale e del verificatore; asserzioni `{"v": 1, "sha"` in `tests/test_brief.py`.

### Danni nuovi nel diff della correzione
Nessuno. Come effetto collaterale utile, `check_plan` è calcolato una volta per ciclo e non per agente (chiude anche il Minor 5 della revisione).

### Osservazioni fuori ambito
Restano aperti i Minor 3, 6, 7, 8 della revisione originale (verificatore che omette id, nota sul rebase, `default_ref` None, `issue.md` inesistente): non bloccano.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
