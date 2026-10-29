# Ri-revisione del giro 1 del Task 10 (commit 4faeb17, base 7e1aee2)

Solo documentazione. Letti il diff, il rapporto («Giro 1»), `bin/tollgate_checks/research_gate.py`, la ruling D8 (progress.md:150) e `docs/verifiche/2026-10-27-b1-prova-flusso.md`. Suite non rilanciata.

### Verdetti sui rilievi

- **I-1 (spec 12.2: il rifiuto per i lavori in corso non rispecchiava il codice e D8): INDIRIZZATO.** La voce ora dice che `research_gate` legge l'interruttore a ogni modifica e che dalla prima modifica successiva senza nota valida il rifiuto vale in qualunque task in corso, anche dove c'era già l'avviso, con il messaggio che dice come consegnare la nota. Coincide con `_verdict` (`research_gate.py:90-117`: `_rules_enforced` letto a ogni chiamata, `deny` per ogni task con proprietario e senza nota) e con D8. Anche la voce gemella nella sezione 9 del piano è riallineata: spec e piano non si contraddicono più.
- **I-2 (piano «scritto e registrato dal modello»): INDIRIZZATO.** Spec 16 ora dice «scritto e committato dal modello e registrato da tollgate (`scope_registered`)», come nel rapporto della prova (riga 24: `scope_registered`, `seq` 4).
- **M-1 (limiti omessi): INDIRIZZATO.** Spec 16 e piano sezione 8 (riga 7) riportano: ramo `Write` di `passo2` non esercitato (rapporto riga 71), `WebFetch` principale non in `lookups` (decisione 5), `prepara` ricopiato (rapporto riga 15), `README_MISSING`/`ICON_MISSING` senza cambio d'esito (riga 16), token 46.532 e 27.783 (riga 20), un solo lavoro con un solo task.
- **M-2 (250 ms limite inferiore): INDIRIZZATO.** Aggiunto «caso ripetuto ... è un limite inferiore» e «si deduce ... (non misurato)».
- **M-3 (stato «chiusa»): INDIRIZZATO.** Stato in testa e riga B1: «implementata sul ramo, merge in attesa dell'OK dell'utente».
- **M-4 (legame 3.3): INDIRIZZATO.** Aggiunta in 8.1 la frase «(a)-(e) sono i punti 1-4 del controllo 3.3 del progetto di B, con (c) che unisce il 3 e il 4».
- **M-5 («terna»): INDIRIZZATO.** Ora «la stessa combinazione di work, task, kind e target». Il docstring di `lookups.record` (`bin/tollgate_core/lookups.py:27`) resta com'era: fuori dal diff e dal tipo di task.
- **M-6 (order di `research_gate`): INDIRIZZATO.** La riga `PreToolUse` dice order 25, dopo `writes`, `bash_rules`, `agents` (20) e `cli_calls` (5), prima di `effects` (30). Verificato: `writes.py:15`, `bash_rules.py:20`, `agents.py:12` = 20; `cli_calls.py:17` = 5; `research_gate.py:20` = 25; `effects.py:22` = 30.
- **M-7 (rinvii per B3-B7): INDIRIZZATO.** Due voci aggiunte in sezione 9: avviso su `TOLLGATE_` solo in `agents/implementer.md`, e `research submit` che non sa chi lo chiama.

### Danni nuovi nel diff della correzione

Nessuno. Il diff tocca solo spec e piano; i fatti nuovi (order, limiti, token, comportamento di `_verdict`) sono stati controllati su codice e rapporto.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
