---
name: resolve
description: Chiude un blocco aperto del lavoro (needs_you, conflitto tra test e specifica, budget) oppure interrompe l'implementatore in corso. Solo l'utente.
disable-model-invocation: true
argument-hint: "<id del blocco> <nota> | writer"
---

**Programma:** `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`, sempre tra virgolette (il percorso può contenere spazi). Se la variabile non risulta espansa nel testo, usa il percorso della riga `tollgate: programma` del contesto. Nel seguito `<programma>` indica questo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando. Lancia dal worktree del lavoro:

```
"<programma>" act apply
```

Riferisci l'esito: il blocco chiuso, la **fase** a cui il lavoro torna e i task tornati `pending` (con `writer`: gli implementatori interrotti). Se rifiuta, riporta il motivo (per esempio un id che non è un blocco aperto di questo lavoro, o «sessione non riconosciuta»: in quel caso il comando va lanciato da Claude Code con tollgate acceso).

Poi indica il passo successivo: con task pendenti, `/tollgate:execute`. Non aggiungere note o decisioni al posto dell'utente.
