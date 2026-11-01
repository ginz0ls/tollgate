# Ri-revisione giro 1, Task 6

### Verdetti sui rilievi
1. **R-BASE non `[blocca]` fermavano task e revisione finale**: INDIRIZZATO. `research.base_rules` (bin/tollgate_analysis/research.py, regex `^(R-BASE-\d{2})( \[blocca\])? \S`) combacia con le righe reali della skill (R-BASE-01 `[blocca]`, R-BASE-07 senza). `lookups.base_rules` (bin/tollgate_core/lookups.py) restituisce note sempre e bloccanti solo se `research.enforced`; skill illeggibile: `(vuoto, vuoto)` quindi fail-closed. Usata in `task_verdict.py:57` e `apply.py:_final_rules`. Test con radice temporanea (`make_base_root`): non-blocca non blocca, blocca con interruttore acceso, spento nulla blocca, R-BASE-99 ignota blocca, skill mancante come prima; stesso per il finale. Rieseguiti i 104 test mirati (task_verdict, final_review, brief, layers): OK.
2. **Test «Nota di ricerca» deve distinguere i due rami**: INDIRIZZATO. `tests/test_brief.py` separa «unusable» (nessuna nota e nota consegnata ma non valida: `nota di ricerca` + «nessun rilievo `R-BASE-…` in più») da «usable» (`che viola` + `oppure con rule nota di ricerca`, niente «in più»); le stringhe esistono in `bin/tollgate_analysis/brief.py:230-234`.

### Danni nuovi nel diff della correzione
Nessuno. Strati rispettati (`research.py` senza import tollgate; `lookups` in core usa `research` di analysis; `task_verdict` importa `lookups` di core). Lettura del file con `read_text` (chiude il file, nessun ResourceWarning). Una lettura per verdetto. I test usano radici temporanee e `plugin_root` esplicito (anche il ctx finto).
Nota Minor non bloccante: `lookups.base_rules` rilegge il file anche in `rules_switch` (due letture indipendenti in punti diversi), accettato dal ruling.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
