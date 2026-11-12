# Brief per l'agente che esegue B7 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-12-tollgate-b7-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-12-tollgate-b7-profilo-database.md` (profilo `database`: schema, migrazioni, RLS, edge function di Supabase, con lo specialista finale `final-database`; 9 task) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-12-tollgate-b7-esecuzione.md`:
- ramo `b7-profilo-database`, worktree `.claude/worktrees/b7`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio, con le tre righe sulla suite (uscita su file, ciclo `until` in primo piano, commit dopo `exit 0`).

Scrivi nel ledger le righe esatte che le condizioni qui sotto cercano, con queste parole. **Dove stanno i file:** il ledger è `progress.md` del workspace, nel worktree: `.claude/worktrees/b7/.superpowers/sdd/<cartella>/progress.md` (dopo il merge la sua copia è in `docs/sdd/2026-11-12-tollgate-b7-profilo-database/progress.md` su `main`); `final-review.md` sta nella stessa cartella; `skills/rules-database/SKILL.md`, `docs/profili/database.md` e `docs/verifiche/2026-11-12-b7-prova-flusso.md` stanno nel worktree `.claude/worktrees/b7` prima del merge e su `main` dopo.

## Fermate previste (non sono la fine del lavoro)

A ogni fermata la sessione fa una **domanda diretta** all'utente (`AskUserQuestion`), oltre al messaggio.
- **Task 5, Step 1:** mostri all'utente la pagina delle regole `docs/profili/database.md`, in parole semplici, e chiedi se le approva, le corregge, le toglie o rinvia.
- **Una scelta della revisione finale** che tocca una scelta dell'utente o un profilo approvato: messaggio con la riga `Fermata: revisione finale` e la domanda.
- **Prima del merge su `main`:** mandi il rapporto della condizione 6 e chiedi l'OK. Senza OK non si unisce niente.
- **Dopo il merge:** il rapporto «Chiusura di B7» e, per ultima, la domanda sul worktree.
- Le altre fermate sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione; il messaggio di ognuna comincia con la riga `Fermata: <caso>`.

## Finito quando

Ogni condizione si controlla leggendo un file o il transcript, senza interpretazioni. Le condizioni dipendono da **una sola** delle quattro situazioni, scelta da ciò che è scritto. **Si controllano prima C e D: se una delle due vale, prevale su A e B** (le righe che riconoscono A e B restano scritte anche quando la sessione è ferma ad aspettare l'utente). Tra A e B: se `skills/rules-database/SKILL.md` ha la riga `approved: `, vale A anche se il ledger ha la riga del rinvio (l'utente può approvare dopo aver rinviato). **Domande dell'utente a una fermata:** se l'utente risponde a una fermata (C, D, la domanda finale della condizione 6 o quella sul worktree della condizione 7) con una domanda o una richiesta di chiarimento, la sessione risponde e chiude lo stesso messaggio ripetendo la richiesta della fermata: per C la richiesta di approvare, correggere, togliere o rinviare le regole; per D la riga `Fermata: <caso>` in testa al messaggio; per la condizione 6 la riga «Posso unire su `main`?» in fondo; per il worktree la domanda sul worktree. Quel messaggio vale come il messaggio della fermata, e le condizioni guardano l'ultima risposta dell'utente che dice sì o no.

Le situazioni:
- **A** (regole approvate): `skills/rules-database/SKILL.md` ha una riga `approved: `.
- **B** (rinvio, anche quando l'utente toglie tutte le regole o rifiuta il profilo): `progress.md` ha una riga che comincia con `Task 5: rinviato dall'utente`.
- **C** (in attesa dell'utente sulle regole): l'ultimo messaggio della sessione all'utente mostra la pagina delle regole e chiede di approvarle, correggerle, toglierle o rinviarle, e l'utente non ha ancora risposto.
- **D** (fermata per un altro caso): l'ultimo messaggio della sessione all'utente comincia con la riga `Fermata: ` e l'utente non ha ancora risposto.

In C e in D il lavoro è finito per ora; quando l'utente risponde si riprende, e alla fine vale A o B.

**Situazione A.** Valgono tutte:
1. `progress.md` ha, per ciascuno dei Task 1-9, una riga che comincia con `Task N: complete`.
2. `skills/rules-database/SKILL.md` ha la riga `approved: <AAAA-MM-GG>`, e `docs/profili/database.md` ha la riga «Approvata dall'utente il <AAAA-MM-GG>.» con la stessa data.
3. `docs/verifiche/2026-11-12-b7-prova-flusso.md` esiste e ha una riga che comincia con `Esito:` seguita da `riuscita`, `riuscita (composita)` oppure `non riuscita:` con il motivo.
4. `progress.md` ha una riga che comincia con `Revisione finale (opus):` e, dopo, una riga che comincia con `Revisione finale chiusa: 0 critical, 0 important aperti`.
5. `progress.md` ha tre righe che cominciano con `Suite finale corsa 1: verde su python3.11 e python3`, `Suite finale corsa 2: verde su python3.11 e python3`, `Suite finale corsa 3: verde su python3.11 e python3`.
6. Nel transcript c'è un messaggio all'utente, prima del merge, con le sezioni intitolate «Commit e test», «Regole approvate», «Decisioni prese durante il lavoro», «Rilievi minori rinviati», «Prova reale», «Cosa cambia nei progetti». «Decisioni prese durante il lavoro» ha **una riga per ogni** riga di `progress.md` che comincia con `Ruling:`, ciascuna con il suo costo. «Rilievi minori rinviati» ha **una riga per ogni** voce della tabella di triage di `final-review.md` del workspace con l'esito `rinviato`, ciascuna con il motivo. Il messaggio finisce con la riga «Posso unire su `main`?».
7. Dopo il messaggio della condizione 6, una di queste due:
   - l'utente non ha ancora risposto, oppure ha detto di no: il lavoro è finito qui;
   - l'utente ha detto di sì: `git log main` ha un commit con l'oggetto che comincia con `tollgate B7: profilo database`; `docs/sdd/2026-11-12-tollgate-b7-profilo-database/README.md` esiste su `main`; `plugin-workflow-decisioni.md` della memoria ha una riga che comincia con `- B7 eseguito`; nel transcript, dopo il merge, c'è un messaggio all'utente che comincia con la riga «Chiusura di B7», e dopo di esso una domanda diretta all'utente sulla rimozione del worktree `.claude/worktrees/b7` e del ramo `b7-profilo-database`. Il lavoro è finito quando l'utente non ha ancora risposto a quella domanda, oppure quando ha risposto e, se ha scelto di rimuovere il worktree, `git worktree list` non mostra più `.claude/worktrees/b7`.

**Situazione B** (rinvio delle regole, decisione 15 del piano). Valgono tutte:
1. `progress.md` ha una riga che comincia con `Task N: complete` per i Task 1, 2, 3 e 4, la riga `Task 5: rinviato dall'utente` e una riga che comincia con `Task 9 ridotto: complete`; i Task 6, 7 e 8 non si fanno e la prova reale non c'è.
2. `progress.md` ha una riga che comincia con `b7-parziale: ` (uno sha e un oggetto) per ogni commit del ramo, scritte prima del merge; tra gli oggetti ci sono quelli degli Step 5 dei Task 1 e 2 del piano («tollgate B7: comandi locali di Supabase senza permesso, scritture remote salvo --local; Prisma e Drizzle», «tollgate B7: togli-pagine per la sola cartella tool-results; init senza percorsi esatti coperti da un'estensione») e il commit «tollgate B7 (parziale): spec rev 33 ridotta».
3. `progress.md` ha una riga che comincia con `Revisione finale b7-parziale (opus):` e, dopo, una che comincia con `Revisione finale b7-parziale chiusa: 0 critical, 0 important aperti`, e tre righe che cominciano con `Suite finale b7-parziale corsa 1: verde su python3.11 e python3`, `… corsa 2: …`, `… corsa 3: …` (righe distinte da quelle della situazione A, che restano per il ramo completo se l'utente approva più tardi).
4. La condizione 6 della situazione A, con «Rilievi minori rinviati» presi da `final-review-b7-parziale.md`, «Regole approvate» che dice «rinviate dall'utente» (o «rifiutate dall'utente») e «Prova reale» che dice «non fatta: regole rinviate», e la proposta di unire solo `b7-parziale`.
5. La condizione 7 della situazione A, con il commit su `main` che comincia con `tollgate B7 (parziale):`, la riga della memoria che comincia con `- B7 parziale` al posto di `- B7 eseguito`, e la domanda sul worktree che riguarda solo `.claude/worktrees/b7-parziale` e il ramo `b7-parziale` (con il sì, `git worktree list` non mostra più `.claude/worktrees/b7-parziale`).
