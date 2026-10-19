# Ri-revisione del giro 3 (1636d48..ab64a9a)

### Verdetti sui rilievi

1. **Test dopo `unittest.main()` in `tests/test_manifest.py`.** INDIRIZZATO. `BareProgramInMessagesTest` è ora prima del blocco `__main__`, che chiude il file (diff, fine di `tests/test_manifest.py`). Rieseguita con `python3 -B -m unittest tests.test_manifest.BareProgramInMessagesTest tests.test_check_cli_calls`: 13 test OK.
2. **Helper `flow_start_naming` inutilizzato.** INDIRIZZATO. Rimosso da `tests/test_start.py` (5 righe tolte); il report dichiara che non c'erano altri usi.
3. **Elenco dei sottocomandi incompleto.** INDIRIZZATO. Il test legge le scelte di `cmd` da `cli.build_parser()` (verificato: act, block, db, events, hook, start, stats, status, task, verify, waiver), toglie `hook` e aggiunge i sottocomandi futuri (`open-pr`, `gate`, …). `stats`, `events`, `db`, `open-pr`, `gate` ora sono coperti. Il limite sulle composizioni (`"tollgate " + sub`) resta, ma era già accettato.
4. **Messaggio di diniego poco chiaro.** INDIRIZZATO. `cli_calls.py:53-60`: `_deny_subagent(sub, certain)` aggiunge, per programma incerto, di scrivere il percorso in modo letterale senza variabile né `$(…)`; il chiamante passa `certain` (riga 85). Resta fail-closed. Test `test_uncertain_program_denial_says_what_to_do` copre il caso incerto e il caso certo (senza l'aggiunta).

### Danni nuovi nel diff della correzione

Nessuno Critical o Important. Un Minor:
- **Minor, `cli_calls.py:72-74`.** Il ramo del parsing fallito ha ancora il messaggio senza l'indicazione. Non è un danno della correzione: lì il programma non si può riconoscere e un cenno non sarebbe preciso. Il testo dice già cosa fare (riportare al coordinatore). Non blocca.

### Osservazioni fuori ambito

I file di test non si lanciano direttamente con `python3 tests/test_x.py` (`from tests.helpers import …` fallisce senza la radice nel path): vale per tutti i test, quindi lo spostamento del punto 1 è corretto ma il caso «eseguito da solo» non si presenta comunque.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
