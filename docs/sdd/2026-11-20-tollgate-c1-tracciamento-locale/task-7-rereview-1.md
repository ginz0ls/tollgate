### Verdetti sui rilievi
**I1: helper della trascrizione finta copiato in quattro moduli (JSON 12/5/700/3, MODEL e dizionario atteso ripetuti).** INDIRIZZATO.
- Una sola `fake_transcript(case)` in `tests/hookkit.py` (da riga ~160), con `MODEL` e `USAGE` condivisi (righe 18-20). Il JSON 12/5/700/3 compare solo lì.
- I quattro moduli importano da `tests.hookkit`; `transcript_file` e `write_transcript` non esistono più in `tests` (grep vuoto).
- Asserzioni non indebolite: il dizionario inline è sostituito da `USAGE`, che è identico. I controlli di `test_check_subagent_stop.CostTest` su 500021 e `MODEL` restano.
- Import inutili: controllo AST sui quattro file a b87b77f, nessun import inutilizzato. `tests/hookkit.py` aveva già `tempfile`, `json` e `Path`.
- Verifica mirata su copia `git archive b87b77f` in cartella temporanea, poi cancellata: `tests.test_check_audit_round`, `test_check_final_review`, `test_check_task_verdict` e `test_check_subagent_stop` danno Ran 185, OK. Il report dichiara lo stesso numero.

### Danni nuovi nel diff della correzione
Nessuno. Il giro tocca solo i test. Una riga vuota in più resta in `test_check_audit_round.py` e `test_check_task_verdict.py` dopo la rimozione, ed è cosmetica.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
