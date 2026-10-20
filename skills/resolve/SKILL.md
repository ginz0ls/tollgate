---
name: resolve
description: Chiude un blocco aperto del lavoro (needs_you, conflitto tra test e specifica, budget) oppure interrompe l'implementatore in corso. Solo l'utente.
disable-model-invocation: true
argument-hint: "<id del blocco> <nota> | writer"
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando. Lancia dal worktree del lavoro:

```
<programma> act apply
```

Riferisci l'esito: il blocco chiuso, la **fase** a cui il lavoro torna e i task tornati `pending` (con `writer`: gli implementatori interrotti). Se rifiuta, riporta il motivo (per esempio un id che non è un blocco aperto di questo lavoro, o «sessione non riconosciuta»: in quel caso il comando va lanciato da Claude Code con tollgate acceso).

Se il blocco era il tetto dei cicli di revisione finale («cicli di revisione esauriti»), `resolve` concede **un** ciclo in più (entro il tetto assoluto di 8); per concederne altri, o per le altre decisioni sui cicli, serve `/tollgate:approve rounds <n>` o `/tollgate:approve unverified-review`.

Se il blocco era un tetto dell'audit di spec o piano («giri avversariali della spec esauriti», «giri avversariali del piano esauriti», «audit a lenti: tetto di cicli raggiunto», oppure «audit a lenti rifiutato dall'utente»), `resolve` oltre a chiuderlo **sospende** quell'audit («avversariale sospeso», «avversario del piano sospeso», «audit a lenti sospeso»): riferiscilo, e il lavoro prosegue con `/tollgate:spec-audit`, che passa alla fase seguente senza ripetere l'audit sospeso. L'altra strada è correggere la spec o il piano e rilanciare `audit prepare` dopo il `resolve`.

Poi indica il passo successivo: con task pendenti, `/tollgate:execute`; con la fase `review`, `/tollgate:finish`; in `spec_audit` o `plan` di L2, `/tollgate:spec-audit`. Non aggiungere note o decisioni al posto dell'utente.
