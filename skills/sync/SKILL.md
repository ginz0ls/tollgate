---
name: sync
description: Rimette il ramo del lavoro sul ramo predefinito e aggiorna la PR. Solo l'utente.
disable-model-invocation: true
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando. Lancia dal worktree del lavoro, che deve essere in fase `execution` o `pr_open` (anche `review`, se la PR è già aperta):

```
<programma> sync
```

Il comando fa `fetch`, integra i commit remoti del ramo, fa il rebase sul predefinito di `origin`, rilancia `finish check` e, se il contenuto non è cambiato, aggiorna la PR. Riferisci l'esito riga per riga, senza riassumere. Il codice d'uscita dice cosa fare:

- **0, riallineato**: le righe dicono cosa è stato fatto; se la PR non è ancora aperta, indica `/tollgate:finish`.
- **1, rifiuto**: riporta le righe `rifiuto:` così come sono. Se dicono che un task è in corso («chiudi o riporta in attesa il task k, poi /tollgate:sync») o che un implementatore sta scrivendo, il rebase non è partito: chiudi il task (o riportalo in attesa) oppure aspetta l'implementatore, poi l'utente rilancia `/tollgate:sync`. Se dicono che il rebase è stato fatto, un nuovo `/tollgate:sync` completa il riallineamento senza ripeterlo.
- **2, blocco `needs_you`** (base e fase restano): leggi la riga `needs_you:` e distingui i due casi, mostrando all'utente le strade che la riga stessa indica. Non risolvere nulla al posto suo.
  - **«sync: conflitto nel rebase …»**: il rebase è annullato. Strade: (a) risolvere fuori da tollgate (rebase a mano nel worktree, finito), poi `/tollgate:approve rebase`, che riallinea la base e autorizza il push forzato del prossimo `finish open-pr`; oppure (b) `/tollgate:abandon #N`.
  - **«sync: il ramo remoto … e HEAD … sono divergenti …»**: i commit remoti del ramo non sono integrabili in avanti. `approve rebase` qui rifiuta. Strade: (a) integrare a mano i commit remoti nel worktree e chiudere il blocco con `/tollgate:resolve <id>`; oppure (b) `/tollgate:abandon #N`.
- **3, serve una nuova revisione**: il rebase ha cambiato il contenuto rispetto all'ultima revisione finale. Indica all'utente di digitare `/tollgate:finish`.

Non lanciare `git push`, `git rebase` o `gh` da solo.
