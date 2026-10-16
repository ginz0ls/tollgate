---
name: status
description: Mostra lo stato dei lavori tollgate attivi (fase, livello, task, blocchi) in sola lettura, e le statistiche di un lavoro su richiesta.
---

**Programma:** `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`, sempre tra virgolette (il percorso può contenere spazi). Se la variabile non risulta espansa nel testo, usa il percorso della riga `tollgate: programma` del contesto. Nel seguito `<programma>` indica questo percorso.

Lancia `"<programma>" status` e riferisci l'output all'utente: per ogni lavoro attivo la fase, il livello, i task per stato, i blocchi aperti e l'eventuale tetto che ha fermato il lavoro. È di sola lettura: non crea nulla e non cambia fase. Con `--json` l'uscita è strutturata.

Se l'utente chiede le statistiche di un lavoro, lancia `"<programma>" stats --work N` dal repo (N è il numero dell'issue) e riassumi il JSON.

Dopo lo stato, indica il passo successivo in base alla fase: task `pending` o in corso, `/tollgate:execute`; blocco aperto, `/tollgate:resolve`; tutti i task `done`, `/tollgate:finish` (arriva con P3b).
