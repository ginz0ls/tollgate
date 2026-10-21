# Ri-revisione giro 1, Task 12

### Verdetti sui rilievi
1. **I-1: `_fix_files` filtra su gravità dichiarata blocker/major.** INDIRIZZATO. `bin/tollgate_flow/taskcmd.py:75-79` aggiunge `severity IN (reviews.BLOCKING_SEVERITIES)` (= blocker, major, `bin/tollgate_core/reviews.py:21`) alla colonna `severity` originale, non alla decisione: un declassato resta. `reviews` è già importato (riga 14). Test `tests/test_fixtask.py` `test_routing_files_only_declared_blocker_or_major`: moderate con `blocking=1` escluso (asserito il flag a 1), major `lib/altro.py` declassato a minor resta; eseguito, OK.
2. **I-2: `test_ff_only_failure_blocks` rinominato, nessun blocco aperto.** INDIRIZZATO. `tests/test_sync.py` ora `test_ff_only_failure_refuses`, docstring corretta, asserisce `count(*) FROM blocks WHERE closed IS NULL == 0`.
3. **Minore: `NonUtf8Test` con esiti precisi.** INDIRIZZATO. `tests/test_audit_prepare.py`: spec -> `OK`, lancio di `ADV`, `spec_path`; piano -> `REFUSED`, messaggio «nessun piano valido nel ramo», nessun lancio. Rinominati di conseguenza.

### Danni nuovi nel diff della correzione
Nessuno. Il solo codice di produzione toccato è `_fix_files`; il placeholder SQL è costruito da una costante, nessuna iniezione.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
