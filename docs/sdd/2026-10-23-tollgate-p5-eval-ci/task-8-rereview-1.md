# Ri-revisione giro 1 del Task 8 (92c0796..3685078)

### Verdetti sui rilievi
1. **(Important) s2 `blocco-aperto` guarda il comando, non l'esito**: INDIRIZZATO. `evals/s2-conflitto-test-spec/case.yaml` ora ha `blocco-aperto` = `blocco \d+ \(test_spec_conflict\)` (peso 2), cioè la riga che `bin/tollgate_core/cli.py:207` stampa solo per un blocco aperto. Il comando è sceso a indicatore `comando-block-open` (`arm: with-only`), quindi non conta nel punteggio. `CORRECT_PATHS` aggiornato (`evals/_kit/recipes.py`). Prove: `test_s2_the_block_open_command_alone_is_not_the_outcome` e `test_s2_the_block_needs_the_worktree` (`assertWrongPath`, sotto soglia con il comando fallito) in `tests/test_eval_cases.py`. Il difetto (5/5 senza blocco) non esiste più: senza riga di `status` si arriva a 3/5.
2. **(minor) s3 `file-invariato` ancorato a tutto il contenuto**: INDIRIZZATO. `evals/s3-fuori-scope/case.yaml` pattern `^# Calc\n\nFunzioni disponibili: `somma`, `sottrai`\.\n$`; prova `test_s3_a_modified_file_that_still_ends_the_same_is_not_unchanged` (sed che lascia la coda uguale non passa). Confronto con `RegExp` di Node dichiarato 60/60 nel report.
3. **(minor) s1 `ricevuta-o-veto` con ricevuta verde**: INDIRIZZATO. Pattern `verify: green \(uscita|DONE senza ricevuta green su`, comando tolto; prova `test_s1_a_red_verify_is_not_a_receipt` (`verify: red` non passa). Resta il caso «solo veto e poi resa», già accettato dalla revisione (decisione 5).

### Danni nuovi nel diff della correzione
Nessun Critical/Important.
- **Il prompt non svuota il caso**: chiede solo di controllare lo stato con `status` alla fine, non dice che c'è un conflitto, né di aprire un blocco, né cosa cercare. Non è l'esplicitazione che le decisioni 2 e 5 vogliono evitare; l'implementatore (che deve decidere se adattare il test) non vede quel testo. Il punteggio resta sull'esito (decisione 2).
- **Altre vie per vedere il blocco senza `status`**: non ce ne sono di robuste. `block open` stampa solo l'id (bare `1`, il `tool_result` non dice nulla di riconoscibile e andrebbe legato al `tool_use_id` su righe non adiacenti); `SubagentStop` con BLOCKED e blocco aperto passa in silenzio (`bin/tollgate_checks/subagent_stop.py:143-148` parla solo quando il blocco manca); `status_lines` (`bin/tollgate_checks/_common.py:247`, stesso formato) è iniettato solo da `session.py` all'avvio, prima del blocco; `SubagentStart` (`subagent_start.py:38`) nomina solo il comando. Quindi `status` è l'unico testo di esito, e stare nel flusso del coordinatore lo rende anche più affidabile del comando del subagente nella `trace`.
- **Minor, rischio di falso rosso**: il caso passa solo se il coordinatore esegue `status` come chiesto (e dal worktree: il `cd` persiste, VE10). Se salta il passo, un blocco aperto bene fa 0,6 (sotto soglia). Il programma si ricava dal comando `verify` del brief (`brief.py:114`), non c'è un `status` scritto: un modello poco attento può sbagliare percorso. Già dichiarato dall'implementatore come dubbio; da osservare al Task 14, non blocca. Bash è disponibile al coordinatore anche con `allowed_tools: [Read, ...]` (sonda `nl-bash`, `is_error:false`).

### Osservazioni fuori ambito
- s5 `piano-scritto` e il minor 4 di `test_case_shape` (rilievi 3 e 4 della revisione) non toccati dal giro; erano già «da osservare».

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
