# Revisione Task 7, Step 1 (8df8f6e..7e46b47)

### Aderenza
- ✅ `B1_FLOW_RULES` prova|vere, altro valore = errore per ogni modo (`spikes/run-b1-flow.sh`, case dopo `die`; test `test_flow_rules_unknown_value` su tutti e 5 i modi, nessun claude, nessuna radice creata).
- ✅ `vere`: OUT = `docs/verifiche/evidenze/b2/flusso` (riga `[ "$RULES" = vere ] && OUT=...`), `prepara` non scrive la rules-base di prova, chiama `lookups.rules_enforced` sulla copia con `python3 -B -` e `pathlib`, `die` con "interruttore" se spento/assente (`rules_switch` gestisce file assente = False).
- ✅ `B1_FLOW_SRC` solo con `B1_FLOW_CHECK=1` (errore per ogni modo, prima del dispatch); cambia solo la sorgente di `git ls-files`/`tar`; `fakegh.py`, `here/b1/flow` e OUT restano dalla radice del repo (D12).
- ✅ `controlla` stampa RULES, radice sorgente, cartella uscite; test `out_dir` copre vere/prova/assente.
- ✅ `flowreg.py precarico`: cerca davvero `# Regole di base (versione 1)` nelle trascrizioni (percorsi `agent_transcript_path` ovunque nel JSON), stampa `metodo: trascrizioni` o `metodo: indizio` con la frase che dice che non è prova; stampa solo il nome del file (niente `/home/...`). `WANTED` invariato (D7). `registra` lo chiama solo con `vere` e scrive `precarico.txt`. `--include-hook-events` è nel comando (riga 104) e `agent_transcript_path` è un campo reale degli hook (bin/tollgate_checks/subagent_stop.py:95).
- ✅ Nessun `open(...)`; letture con `Path.read_text`. Test: nessun `claude` vero (finto in `Bench`), nessuna rete. `bash -n` ok.
- ✅ D13: `test_flow_copy_fails_on_missing_tracked_file` è di guardia, script invariato. I test di B1 con `prova` non sono toccati (solo aggiunte nel diff).
- ⚠️ Che il flusso reale contenga davvero `agent_transcript_path`: non verificabile qui (lo dichiara anche il report); il ripiego sull'indizio è dichiarato.
- ⚠️ La suite completa (3218 test, ResourceWarning=error) è un'affermazione del report, non rilanciata.

### Punti di forza
Modifiche minime e chirurgiche; il test `keeps_real_rules_base` verifica anche l'assenza di `__pycache__` nella copia (prova che `-B` funziona); test del precarico copre trascrizione mancante, assente, trovata e il ripiego; il report segnala lo scostamento (controllo `flow/.git`).

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `spikes/b1/flowreg.py` (`precarico`, `RULES_TITLE in text`): il titolo compare anche se l'agente lo ha solo letto con `Read` o se è incollato nel prompt; non distingue precaricamento da lettura, e conta anche subagenti non implementatori/revisori. Il rapporto del controller deve dirlo (o contare solo le trascrizioni dei subagenti tollgate-*).
2. `spikes/run-b1-flow.sh` `modo_prepara`: il controllo dell'interruttore avviene dopo `rot` di `$OUT/passo1|passo2`, `$PLUGIN`, `$REPO`, ecc. e dopo `mkdir "$OUT"`: un `prepara` rifiutato sposta comunque da parte le evidenze precedenti (rinominate, non perse). Meglio controllare l'interruttore sulla sorgente prima del `rot`; non bloccante.
3. Report, punto D11: dice che `registra` non raccoglie `research_switch_unreadable`; ma `registra` copia l'intero `events.jsonl` (riga 346), che lo conterrebbe con il percorso assoluto. Con la regola vera approvata l'evento non dovrebbe esistere, ma il controller deve anonimizzare comunque `events.jsonl`.
4. `precarico.err` (stderr, eventuale traceback con percorsi) non è anonimizzato dallo script: ricade nell'anonimizzazione del controller, da ricordare.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni D7, D12, D13 rispettati, nessuna regressione sui test di B1, errori e risorse gestiti; restano solo rifiniture minori e due promemoria per l'esecuzione del controller.
