---
name: abandon
description: Chiude un lavoro tollgate senza unirlo; ramo, worktree e PR restano. Solo l'utente.
disable-model-invocation: true
argument-hint: "#N"
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

Argomento: `#N`, il numero dell'issue. L'atto è già registrato dal hook quando l'utente ha digitato il comando, e non è legato al lavoro: lancia da una sessione qualsiasi nel repo (di norma il checkout principale).

```
<programma> abandon <N>
```

Riferisci l'esito:

- **0**: il lavoro è in fase `closed` (le righe `avviso:` vanno mostrate). Ramo, worktree e PR **restano**: l'utente chiude la PR su GitHub se vuole, e `/tollgate:cleanup` toglie ramo e worktree.
- **1, rifiuto**: riporta le righe `rifiuto:` così come sono (per esempio «serve un atto dell'utente» o nessun lavoro attivo per quell'issue) e fermati.

Non chiudere PR, non cancellare rami e non rimuovere worktree da solo.
