# Ri-revisione giro di correzione 1, Task 5 (a11795c..ff9de1b)

### Verdetti sui rilievi
1. **I-1: con `plan_adversary` spento un giro del piano aperto resta aperto prima di `plan -> approval`.** INDIRIZZATO. `audit.py:_decide_plan` ora legge `row` prima del ramo spento e restituisce `_Act("advance", supersede=row, ...)`; `_execute` chiude con `audits.supersede` prima di `set_phase`. Test `test_plan_adversary_off_supersedes_open_plan_round`: fase `approval`, nessun giro aperto, riga `superseded`.
2. **I-2: titolo del task non fidato fuori dal recinto.** INDIRIZZATO. `brief.py` `audit_brief`: tabella in `_block(...)`, che usa `fence()` (più lungo di ogni sequenza di backtick, minimo 3); `DATA_NOTE` presente nel brief (asserito in `test_plan_brief_lists_split_candidates`). Test `test_plan_task_titles_stay_inside_a_fence` con titolo a backtick tripli: recinto da 4, righe prima e dopo.
3. **M-1: rifiuto `fix_spec`/`fix_plan` lascia aperto un giro su un altro SHA.** INDIRIZZATO. `_decide_spec` avvolge `_spec_branches` e imposta `r.supersede = stale` sul `_Refuse`; `_decide_plan` fa lo stesso nel ramo `fix_plan`; `prepare` chiude con `supersede` nel gestore di `_Refuse`. Il ramo 1 (stesso SHA, ristampa) resta prima del `try`, quindi non viene mai superato per errore; i rifiuti di `_spec_doc` avvengono prima e hanno `supersede=None`; il gestore non tocca `ctx` quando `supersede` è None (nessun UnboundLocalError per i rifiuti di `_context`). Test per spec e piano.
4. **M-3: `ValueError` di `open_round` come traceback.** INDIRIZZATO. `_execute` lo converte in `AuditError`; `cli.py:330` la gestisce (uscita 1 con messaggio). Test `test_open_round_value_error_is_an_audit_error`.

Test eseguito: `python3 -B -m unittest tests.test_audit_prepare tests.test_brief` -> 78 test OK (coincide col report). Il report nomina i test nuovi, mostra RED (5 falliti) e GREEN.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- M-2 (backtick nel percorso del documento in `audit_brief`) resta aperto: era un minore non incluso nel giro.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
