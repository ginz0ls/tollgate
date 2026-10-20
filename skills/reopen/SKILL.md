---
name: reopen
description: Riapre la spec o il piano di un lavoro dopo l'approvazione, per correggerli. Solo l'utente.
disable-model-invocation: true
argument-hint: "spec <motivo> | plan <motivo>"
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando. Lancia dal worktree del lavoro:

```
<programma> act apply
```

Riferisci l'esito riga per riga: la **fase** a cui il lavoro torna, il giro di audit eventualmente superato e lo **scope** tolto (con la registrazione del piano se c'era). I file di approvazione restano come storico e non valgono più. Se rifiuta, riporta il motivo così com'è (il motivo del comando è obbligatorio; il rifiuto indica anche un task o un implementatore ancora in corso, o un blocco aperto da chiudere prima con `/tollgate:resolve`).

Poi, in base all'oggetto:

- **`spec`** (solo L2): correggi la spec, committala e riparti da `/tollgate:spec-audit`: serve un nuovo giro avversariale e una nuova `/tollgate:approve spec`.
- **`plan`**: correggi il piano e committalo. In **L2** riparti da `/tollgate:spec-audit`, che lancia l'avversario del piano, poi serve una nuova `/tollgate:approve plan`. In **L1** il piano corretto si registra da solo con la modifica.

I task già fatti risulteranno «task già soddisfatto» dopo la nuova registrazione del piano. Non correggere spec o piano al posto dell'utente prima del suo comando, e non toccare le sospensioni dell'audit: `reopen` non le cambia.
