# Report Task 8

## Implementato
- Spec del nucleo, revisione 28: intestazione; 6.3 (`rules-base` skill comune, precaricata dai quattro agenti, fuori da tetto e `skills_required`, avviso); 8.1 (interruttore: data 2026-11-01, `no`/`off`/`n`/`false` anche tra apici, `0` e `none` accendono, file illeggibile con avviso ed evento una volta per piano, perché evento e non `hooks.log`, `tollgate events` non `stats`); 8.6 (difetto della nota una volta sola, D3; task senza modifiche con nota non utilizzabile; R-BASE note al verdetto, `[blocca]` solo con interruttore acceso); 12.2 (approvazione avvenuta); 16 (riga della prova reale; rifiuto dal vivo non visto; precaricamento visto nelle trascrizioni, non nello stream-json); 18.4 (`research_switch_unreadable`); riga 28 della sezione 20 con le decisioni 1-13 e i ruling.
- Catalogo: sezione 1 (skill comune `rules-base`), sezione 4 (riga `rules-base` con le fonti e nota sulla forma reale).
- Progetto di B: avanzamento «B1 e B2 eseguite».
- Piano principale: intestazione e stato (merge in attesa dell'OK, 3218 test), riga B2 sezione 2, sezione 3 (nomi reali), sezione 5 (`PYTHONWARNINGS`), sezione 9 (B2 chiusi; rinvii a B3-B7 e B8, D15, D16), nuova sezione 10 «Prove di B2» con tutte le 20 righe di Copertura e le prove oltre la tabella.
- La sezione «Prove di B2» è la 10 e non la 9 per non spostare i riferimenti esistenti alla «sezione 9».

## Test
`PYTHONWARNINGS=error::ResourceWarning tests/run`: Python 3.11.16 3218 OK (skipped=2, 1449 s); Python 3.13.5 3218 OK (1467 s); EXIT 0; nessun «unclosed database». Il test instabile D16 non è fallito.

## Scostamenti / dubbi
Nessun codice toccato. I nomi dei test citati nella sezione 10 sono stati verificati con grep. Il nome di `tollgate events` viene dal carry D10, non verificato nel codice.
