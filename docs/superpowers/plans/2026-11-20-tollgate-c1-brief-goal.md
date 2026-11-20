# Brief per l'agente che esegue C1 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-20-tollgate-c1-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md` con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-20-tollgate-c1-esecuzione.md`. Il piano ha 10 task: stato ed eventi nuovi, storia che non si cancella, taglia, ruling, fermate, costo, fotografia, prova reale, revisione della spec.
- ramo `c1-tracciamento-locale`, worktree `.claude/worktrees/c1`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio, con le tre righe sulla suite (uscita su file, ciclo `until` in primo piano, commit dopo `exit 0`).

Scrivi nel ledger le righe esatte che le condizioni qui sotto cercano, con queste parole.

**Dove stanno i file.**
- **Ledger e revisione.** Il ledger è `progress.md` del workspace, nel worktree: `.claude/worktrees/c1/.superpowers/sdd/<cartella>/progress.md`. Dopo il merge la sua copia è in `docs/sdd/2026-11-20-tollgate-c1-tracciamento-locale/progress.md` su `main`. `final-review.md` sta nella stessa cartella.
- **Rapporto della prova.** `docs/verifiche/2026-11-20-c1-prova-flusso.md` sta nel worktree prima del merge e su `main` dopo.

## Fermate previste (non sono la fine del lavoro)

A ogni fermata la sessione fa una **domanda diretta** all'utente (`AskUserQuestion`), oltre al messaggio.
- **Una scelta della revisione finale** che tocca una scelta dell'utente: messaggio con la riga `Fermata: revisione finale` e la domanda.
- **Prima del merge su `main`:** mandi il rapporto della condizione 5 e chiedi l'OK. Senza OK non si unisce niente.
- **Dopo il merge:** il rapporto «Chiusura di C1» e, per ultima, la domanda sul worktree.
- **Le altre fermate** sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione (`Fermata: prova` e le altre). Il messaggio di ognuna comincia con la riga `Fermata: <caso>`.

## Finito quando

Ogni condizione si controlla leggendo un file o il transcript, senza interpretazioni. Le situazioni sono due. **Si controlla prima D: se vale, prevale su A.**

**Domande dell'utente a una fermata.** Se l'utente risponde a una fermata (D, la domanda finale della condizione 5 o quella sul worktree della condizione 6) con una domanda o una richiesta di chiarimento, la sessione risponde e chiude lo stesso messaggio ripetendo la richiesta della fermata:
- per D, la riga `Fermata: <caso>` in testa al messaggio;
- per la condizione 5, la riga «Posso unire su `main`?» in fondo;
- per il worktree, la domanda sul worktree.

Quel messaggio vale come il messaggio della fermata, e le condizioni guardano l'ultima risposta dell'utente che dice sì o no.

- **D** (fermata): l'ultimo messaggio della sessione all'utente comincia con la riga `Fermata: ` e l'utente non ha ancora risposto. Il lavoro è finito per ora; quando l'utente risponde si riprende, e alla fine vale A.
- **A** (lavoro completo). Valgono tutte:
  1. `progress.md` ha, per ciascuno dei Task 1-10, una riga che comincia con `Task N: complete`, e almeno una riga che comincia con `Prova:`.
  2. `docs/verifiche/2026-11-20-c1-prova-flusso.md` esiste e ha una riga che comincia con `Esito:` seguita da `riuscita`, `riuscita (composita)` oppure `non riuscita:` con il motivo.
  3. `progress.md` ha una riga che comincia con `Revisione finale (opus):` e, dopo, una riga che comincia con `Revisione finale chiusa: 0 critical, 0 important aperti`.
  4. `progress.md` ha tre righe che cominciano con `Suite finale corsa 1: verde su python3.11 e python3`, `Suite finale corsa 2: verde su python3.11 e python3`, `Suite finale corsa 3: verde su python3.11 e python3`.
  5. Nel transcript c'è un messaggio all'utente, prima del merge, con le sezioni intitolate «Commit e test», «Decisioni prese durante il lavoro», «Rilievi minori rinviati», «Prova reale», «Cosa cambia nei progetti».
     - «Decisioni prese durante il lavoro» ha **una riga per ogni** riga di `progress.md` che comincia con `Ruling:`, ciascuna con il suo costo.
     - «Rilievi minori rinviati» ha **una riga per ogni** voce della tabella di triage di `final-review.md` del workspace con l'esito `rinviato`, ciascuna con il motivo.
     - Il messaggio finisce con la riga «Posso unire su `main`?».
  6. Dopo il messaggio della condizione 5, una di queste due:
     - l'utente non ha ancora risposto, oppure ha detto di no: il lavoro è finito qui;
     - l'utente ha detto di sì: valgono tutte le condizioni qui sotto.
       - `git log main` ha un commit con l'oggetto che comincia con `tollgate C1: tracciamento locale`.
       - `docs/sdd/2026-11-20-tollgate-c1-tracciamento-locale/README.md` esiste su `main`.
       - Il piano principale di C su `main` ha, nella riga C1 della sezione 2, la parola «unita».
       - `plugin-workflow-decisioni.md` della memoria ha una riga che comincia con `- C1 eseguito`.
       - Nel transcript, dopo il merge, c'è un messaggio all'utente che comincia con la riga «Chiusura di C1», e dopo di esso una domanda diretta all'utente sulla rimozione del worktree `.claude/worktrees/c1` e del ramo `c1-tracciamento-locale`.

       Il lavoro è finito quando l'utente non ha ancora risposto a quella domanda, oppure quando ha risposto e, se ha scelto di rimuovere il worktree, `git worktree list` non mostra più `.claude/worktrees/c1`.
