# Brief per l'agente che esegue B8 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-18-tollgate-b8-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-18-tollgate-b8-eval-chiusura.md` con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-18-tollgate-b8-esecuzione.md`. Il piano ha 8 task: buchi dei comandi, eval con e senza plugin nel tetto di 20 USD stimati, chiusura di B.
- ramo `b8-eval-chiusura`, worktree `.claude/worktrees/b8`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio, con le tre righe sulla suite (uscita su file, ciclo `until` in primo piano, commit dopo `exit 0`).

Scrivi nel ledger le righe esatte che le condizioni qui sotto cercano, con queste parole.

**Dove stanno i file.**
- **Ledger e revisione.** Il ledger è `progress.md` del workspace, nel worktree: `.claude/worktrees/b8/.superpowers/sdd/<cartella>/progress.md`. Dopo il merge la sua copia è in `docs/sdd/2026-11-18-tollgate-b8-eval-chiusura/progress.md` su `main`. `final-review.md` sta nella stessa cartella.
- **Rapporto degli eval.** `docs/verifiche/2026-11-18-b8-eval.md` sta nel worktree prima del merge e su `main` dopo.

## Fermate previste (non sono la fine del lavoro)

A ogni fermata la sessione fa una **domanda diretta** all'utente (`AskUserQuestion`), oltre al messaggio.
- **Una scelta della revisione finale** che tocca una scelta dell'utente o un profilo approvato: messaggio con la riga `Fermata: revisione finale` e la domanda.
- **Prima del merge su `main`:** mandi il rapporto della condizione 5 e chiedi l'OK. Senza OK non si unisce niente.
- **Dopo il merge:** il rapporto «Chiusura di B8» e, per ultima, la domanda sul worktree.
- **Le altre fermate** sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione (`Fermata: sonda`, `Fermata: tetto`, `Fermata: eval` e le altre). Il messaggio di ognuna comincia con la riga `Fermata: <caso>`.

## Finito quando

Ogni condizione si controlla leggendo un file o il transcript, senza interpretazioni. Le situazioni sono due. **Si controlla prima D: se vale, prevale su A.**

**Domande dell'utente a una fermata.** Se l'utente risponde a una fermata (D, la domanda finale della condizione 5 o quella sul worktree della condizione 6) con una domanda o una richiesta di chiarimento, la sessione risponde e chiude lo stesso messaggio ripetendo la richiesta della fermata:
- per D, la riga `Fermata: <caso>` in testa al messaggio;
- per la condizione 5, la riga «Posso unire su `main`?» in fondo;
- per il worktree, la domanda sul worktree.

Quel messaggio vale come il messaggio della fermata, e le condizioni guardano l'ultima risposta dell'utente che dice sì o no.

- **D** (fermata): l'ultimo messaggio della sessione all'utente comincia con la riga `Fermata: ` e l'utente non ha ancora risposto. Il lavoro è finito per ora; quando l'utente risponde si riprende, e alla fine vale A.
- **A** (lavoro completo). Valgono tutte:
  1. `progress.md` ha, per ciascuno dei Task 1-8, una riga che comincia con `Task N: complete`, e almeno una riga che comincia con `Sonda:`.
  2. `docs/verifiche/2026-11-18-b8-eval.md` esiste e ha una riga che comincia con `Esito:` seguita da `tutti sopra soglia`, `sopra soglia con` oppure `non riuscito:` con il motivo. `progress.md` ha una riga che comincia con `Eval ` per ciascuno dei casi `s1-done-senza-ricevuta`, `s2-conflitto-test-spec`, `s3-fuori-scope`, `s4-deploy`, `s5-l0-cresce`, `s6-fine-execute`, `s7-spec-contraddittoria`, `s8-cambio-ramo`, `s9-implementatore-generico`, `s10-modello-a-memoria`, `s11-deploy-dedotto`, `s12-non-esiste`, `e1-audit-a-lenti`, `e3-start-spec`, `e4-chiusura-l2`, `e5-rientro-gate`, salvo i casi che l'utente ha scelto di saltare a una `Fermata: tetto`, scritti in una riga che comincia con `Eval saltati dall'utente:`.
  3. `progress.md` ha una riga che comincia con `Revisione finale (opus):` e, dopo, una riga che comincia con `Revisione finale chiusa: 0 critical, 0 important aperti`.
  4. `progress.md` ha tre righe che cominciano con `Suite finale corsa 1: verde su python3.11 e python3`, `Suite finale corsa 2: verde su python3.11 e python3`, `Suite finale corsa 3: verde su python3.11 e python3`.
  5. Nel transcript c'è un messaggio all'utente, prima del merge, con le sezioni intitolate «Commit e test», «Decisioni prese durante il lavoro», «Rilievi minori rinviati», «Eval», «Cosa cambia nei progetti», «Pagine approvate che invecchiano».
     - «Decisioni prese durante il lavoro» ha **una riga per ogni** riga di `progress.md` che comincia con `Ruling:`, ciascuna con il suo costo.
     - «Rilievi minori rinviati» ha **una riga per ogni** voce della tabella di triage di `final-review.md` del workspace con l'esito `rinviato`, ciascuna con il motivo.
     - Il messaggio finisce con la riga «Posso unire su `main`?».
  6. Dopo il messaggio della condizione 5, una di queste due:
     - l'utente non ha ancora risposto, oppure ha detto di no: il lavoro è finito qui;
     - l'utente ha detto di sì: valgono tutte le condizioni qui sotto.
       - `git log main` ha un commit con l'oggetto che comincia con `tollgate B8: eval e chiusura di B`.
       - `docs/sdd/2026-11-18-tollgate-b8-eval-chiusura/README.md` esiste su `main`.
       - Il progetto di B su `main` ha una riga che contiene «B chiusa».
       - `plugin-workflow-decisioni.md` della memoria ha una riga che comincia con `- B8 eseguito`.
       - Nel transcript, dopo il merge, c'è un messaggio all'utente che comincia con la riga «Chiusura di B8», e dopo di esso una domanda diretta all'utente sulla rimozione del worktree `.claude/worktrees/b8` e del ramo `b8-eval-chiusura`.

       Il lavoro è finito quando l'utente non ha ancora risposto a quella domanda, oppure quando ha risposto e, se ha scelto di rimuovere il worktree, `git worktree list` non mostra più `.claude/worktrees/b8`.
