### Aderenza

- ✅ Step 6, gate (`docs/verifiche/2026-10-21-p4-prova-gate.md`): per ogni caso PR, SHA, stati con autore, atteso, esito, minuti; compositi dichiarati (righe 26-30 della tabella e intestazione); tentativi non riusciti elencati con causa (tabella «Tentativi non riusciti»); nessun «riuscito» per un esito non ottenuto (il ripristino della protezione del criterio 11 è scritto «parziale», non gonfiato).
- ✅ Conteggi: 37 casi distinti; 7 compositi con tentativi 4/3/3/3/3/2/2 coerenti con `casi-righe.md`; 30 al primo giro.
- ✅ Campione (6 casi, esiti e minuti ricalcolati dai `*-timing.out`): rosso-skip 46 s = 0,8; guard-toml 40 s = 0,7; token-personale 58 s = 1,0; error-due-pr 47 s = 0,8; verde-pulita 43 s = 0,7; detect-pulita 38 s = 0,6. Tutti uguali al rapporto. Totali di `raccogli-*-minuti.txt` (190 run, 3 693 s; 23 run, 352 s; fatturati 0) uguali. Esiti dei 6 casi uguali alle righe di `casi-righe.md`.
- ✅ Step 6, flusso (`2026-10-21-p4-prova-flusso.md`): versione di claude, sessioni (id e cartella), passi, veti, PR #105, stati con autore, token (`stats`), PATH, non esercitato. `attendi-esito.txt`, `pr.env`, `exit-codes.txt` concordano (SHA 19369c2, 4 uscite 0, una sola esecuzione per passo).
- ✅ Correzione di `spikes/gh-p4/ghguard.py` (commit 8fa32ba): `spikes/gh-p4/ghguard.py:335` ammette solo `args[2] == PROT` e `rest[0] == FLOW_CLONE` (uguaglianza esatta, non prefisso). `tests/test_p4_ghguard.py` (`FlowCloneTest`) copre: accettato con e senza `-- -q`; rifiutati detect, cartella sorella, `..`, sottocartella, cartella padre; il profilo `flow` continua a rifiutare `repo clone`. Il codice è coerente con la decisione del controller.
- ⚠️ Non verificato: il Task 16 dice che i test sono verdi su 3.11 e 3.13 (2453); non rilanciati, per le regole.

### Punti di forza
Onestà sui casi non ottenuti (parziale per il secondo `start`, «non riportato»); causa per ogni tentativo, anche dove il log del run manca («il log del run non è tra le evidenze»); nota sulla base degradata di detect; sezione «non esercitato» concreta; la garanzia del flusso è distinta dall'audit.

### Rilievi

**Critical:** nessuno.

**Important**
- I1 — `docs/verifiche/2026-10-21-p4-prova-gate.md:137` e `2026-10-21-p4-prova-flusso.md:80`: la violazione di `raccogli-comandi-controllo.txt` è descritta come «falso positivo del verificatore», ma i rapporti non dicono che è stata corretta nel commit 8fa32ba (ghguard ammette `/tmp/tollgate-p4/flow/protected`, con test). Chi legge pensa che il controllo continui a segnalarla e che la suite resti rossa. Inoltre l'evidenza `raccogli-comandi-controllo.txt` è stata prodotta prima della correzione: rieseguirla oggi darebbe 0 violazioni. Correggere: aggiungere in entrambi i rapporti «corretto in 8fa32ba (`FlowCloneTest`); l'evidenza è antecedente alla correzione», e nel rapporto del gate scrivere che la violazione è un difetto del verificatore, non del modello (il flusso del rapporto flusso resta valido).

**Minor**
- M1 — `2026-10-21-p4-prova-gate.md:81-82`: la colonna PR contiene `#p3` e `#p1`, che non sono PR (sono identificativi interni dei passi `p1`/`p3` del caso detect). Scrivere «n.d. (push diretto)» o il numero reale.
- M2 — `2026-10-21-p4-prova-gate.md:137`: si dichiara un solo `gh --version` superfluo, ma `comandi.log` ne registra 6 righe (2, 104, 127, 1108/1109, 1329) e il controllo ne conta 5. Specificare quali sono legittimi (probe iniziali) e che solo l'etichetta `aggiorna-push` è fuori elenco.
- M3 — `2026-10-21-p4-prova-gate.md` (riga del criterio 11): lo `start` senza avvisi dopo il ripristino non è stato registrato; è dichiarato, ma la riga «Atteso/Ottenuto» è `parziale`. Va bene; solo ricordarlo come lacuna aperta al Task 17 (già in «non esercitato»).
- M4 — rapporto flusso: i commenti sul tasso «0 differenze» sono corretti ma il campo costo USD riportato da `claude -p` non è verificabile dal diff (evidenze escluse); solo segnalazione.

### Valutazione
**Qualità del task:** Da correggere (lieve).
**Motivo:** i rapporti sono completi, onesti e le cifre campionate coincidono con le evidenze; la correzione di ghguard è stretta e coperta dai test. Manca solo il riferimento al commit 8fa32ba accanto alla violazione (I1): un ritocco di una riga per rapporto, nessun rilancio di prove.

### Ri-revisione (e101992, e658b49)
Pulito. I1: entrambi i rapporti citano 8fa32ba (`FlowCloneTest`), dicono che il difetto è del verificatore e che l'evidenza è antecedente alla correzione. M1: `#p1`/`#p3` sostituiti da «n.d. (push diretto)». M2: il `gh --version` fuori elenco è localizzato (`comandi.log` righe 1108-1109, 18:24:40Z, riga annotata «(controller...)»); i 5 contati tornano (6 righe meno l'annotazione). M3: `crit11-protected-start-completa.out` contiene solo l'avviso atteso «stati di tollgate assenti sul predefinito», rc 0, stderr vuoto; issue #106 chiusa (`...-issue-completa-close.out`; l'`.err` di 105 byte è l'avviso di gh sulla chiusura, non un errore, rc 0). Riga del criterio 11 e sezione «non esercitato» aggiornate.
