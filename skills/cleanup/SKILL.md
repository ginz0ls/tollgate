---
name: cleanup
description: Toglie rami e worktree dei lavori chiusi (e, a richiesta, dei rami tg/<N>-* orfani). Solo l'utente.
disable-model-invocation: true
argument-hint: "[--orphans]"
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando; vale 10 minuti. Argomento facoltativo: `--orphans`, che include anche i rami `tg/<N>-*` senza lavoro nel DB.

1. Lancia **prima senza `--confirm`**, dal checkout principale (o da una sessione non legata a un lavoro):

   ```
   <programma> cleanup [--orphans]
   ```

   - **3**: elenca soltanto (righe `da togliere: …` e, se ci sono, `orfano: …`) e non consuma l'atto. Mostra l'elenco **intero** all'utente e chiedigli se procedere.
   - **0** con «niente da ripulire»: riportalo e fermati.
   - **1, rifiuto**: riporta le righe `rifiuto:` così come sono e fermati.
2. Solo con il **sì esplicito** dell'utente, e entro i 10 minuti dell'atto, rilancia lo stesso comando aggiungendo `--confirm` (la riga `per procedere:` dell'elenco lo riporta). Mai `--confirm` di tua iniziativa. Se l'atto è scaduto, di' all'utente di digitare di nuovo `/tollgate:cleanup`.
3. Riferisci l'esito riga per riga. Il worktree si toglie sempre senza forzature e mai se ha modifiche non committate; il ramo solo se punta ancora allo SHA elencato (la riga indica lo SHA, per recuperarlo). Le righe `avviso:` spiegano ciò che è stato lasciato.

Non usare `git branch -D` né `git worktree remove --force` da solo.
