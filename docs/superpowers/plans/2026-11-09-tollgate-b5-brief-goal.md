# Brief per l'agente che esegue B5 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-09-tollgate-b5-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md` (profilo `backend`: server, API, Worker di Cloudflare; 9 task) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-09-tollgate-b5-esecuzione.md`:
- ramo `b5-profilo-backend`, worktree `.claude/worktrees/b5`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio.

Scrivi nel ledger le righe esatte che le condizioni qui sotto cercano, con queste parole. **Dove stanno i file:** il ledger è `progress.md` del workspace, nel worktree: `.claude/worktrees/b5/.superpowers/sdd/<cartella>/progress.md` (dopo il merge la sua copia è in `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/progress.md` su `main`); `final-review.md` sta nella stessa cartella; `skills/rules-backend/SKILL.md`, `docs/profili/backend.md` e `docs/verifiche/2026-11-09-b5-prova-flusso.md` stanno nel worktree `.claude/worktrees/b5` prima del merge e su `main` dopo.

## Fermate previste (non sono la fine del lavoro)

- **Task 5, Step 1:** mostri all'utente la pagina delle regole `docs/profili/backend.md`, in parole semplici, e aspetti che le approvi, le corregga, le tolga o rinvii.
- **Prima del merge su `main`:** mandi il rapporto della condizione 6 e chiedi l'OK. Senza OK non si unisce niente.
- Le altre fermate sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione; il messaggio all'utente di ognuna comincia con la riga `Fermata: <caso>`.

## Finito quando

Ogni condizione si controlla leggendo un file o il transcript, senza interpretazioni. Le condizioni dipendono da **una sola** delle quattro situazioni, scelta da ciò che è scritto. **Si controllano prima C e D: se una delle due vale, prevale su A e B** (le righe che riconoscono A e B restano scritte anche quando la sessione è ferma ad aspettare l'utente). Tra A e B: se `skills/rules-backend/SKILL.md` ha la riga `approved: `, vale A anche se il ledger ha la riga del rinvio (l'utente può approvare dopo aver rinviato). **Domande dell'utente a una fermata:** se l'utente risponde a una fermata (C, D o la domanda finale della condizione 6) con una domanda o una richiesta di chiarimento, la sessione risponde e chiude lo stesso messaggio ripetendo la richiesta della fermata: per C la richiesta di approvare, correggere, togliere o rinviare le regole; per D la riga `Fermata: <caso>` in testa al messaggio; per la condizione 6 la riga «Posso unire su `main`?» in fondo. Quel messaggio vale come il messaggio della fermata, e la condizione 7 guarda l'ultima risposta dell'utente che dice sì o no. Le situazioni: **A** (regole approvate: `skills/rules-backend/SKILL.md` ha una riga `approved: `), **B** (rinvio: `progress.md` ha una riga che comincia con `Task 5: rinviato dall'utente`), **C** (in attesa: l'ultimo messaggio della sessione all'utente mostra la pagina delle regole e chiede di approvarle, e l'utente non ha ancora risposto). **D** (fermata per un altro caso: l'ultimo messaggio della sessione all'utente comincia con la riga `Fermata: ` e l'utente non ha ancora risposto). In C e in D il lavoro è finito per ora; quando l'utente risponde si riprende, e alla fine vale A o B.

**Situazione A.** Valgono tutte:
1. `progress.md` ha, per ciascuno dei Task 1-9, una riga che comincia con `Task N: complete`.
2. `skills/rules-backend/SKILL.md` ha la riga `approved: <AAAA-MM-GG>`, e `docs/profili/backend.md` ha la riga «Approvata dall'utente il <AAAA-MM-GG>.» con la stessa data.
3. `docs/verifiche/2026-11-09-b5-prova-flusso.md` esiste e ha una riga che comincia con `Esito:` seguita da `riuscita`, `riuscita (composita)` oppure `non riuscita:` con il motivo.
4. `progress.md` ha una riga che comincia con `Revisione finale (opus):` e, dopo, una riga che comincia con `Revisione finale chiusa: 0 critical, 0 important aperti`.
5. `progress.md` ha tre righe che cominciano con `Suite finale corsa 1: verde su python3.11 e python3`, `Suite finale corsa 2: verde su python3.11 e python3`, `Suite finale corsa 3: verde su python3.11 e python3`.
6. Nel transcript c'è un messaggio all'utente, prima del merge, con le sezioni intitolate «Commit e test», «Regole approvate», «Decisioni prese durante il lavoro», «Rilievi minori rinviati», «Prova reale», «Cosa cambia nei progetti». «Decisioni prese durante il lavoro» ha **una riga per ogni** riga di `progress.md` che comincia con `Ruling:`, ciascuna con il suo costo. «Rilievi minori rinviati» ha **una riga per ogni** voce della tabella di triage di `final-review.md` del workspace con l'esito `rinviato`, ciascuna con il motivo. Il messaggio finisce con la riga «Posso unire su `main`?».
7. Dopo il messaggio della condizione 6, una di queste due:
   - l'utente non ha ancora risposto, oppure ha detto di no: il lavoro è finito qui;
   - l'utente ha detto di sì: `git log main` ha un commit con l'oggetto che comincia con `tollgate B5: profilo backend`; `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/README.md` esiste su `main`; `plugin-workflow-decisioni.md` della memoria ha una riga che comincia con `- B5 eseguito`; e nel transcript, dopo il merge, c'è un messaggio all'utente che comincia con la riga «Chiusura di B5».

**Situazione B** (rinvio delle regole, decisione 15 del piano). Valgono tutte:
1. `progress.md` ha una riga che comincia con `Task N: complete` per i Task 1, 2, 3 e 4, la riga `Task 5: rinviato dall'utente` e una riga che comincia con `Task 9 ridotto: complete`; i Task 6, 7 e 8 non si fanno e la prova reale non c'è.
2. `progress.md` ha una riga che comincia con `b5-parziale: ` (uno sha e un oggetto) per ogni commit del ramo, scritte prima del merge; tra gli oggetti ci sono quelli degli Step 5 dei Task 1 e 2 del piano («tollgate B5: un frammento può escludere cartelle dalla proposta», «tollgate B5: le scritture di Wrangler su KV, D1 e R2 e gli script dei monorepo sono effetti esterni») e il commit «tollgate B5 (parziale): spec rev 32 ridotta» (decisione 15).
3. Le condizioni 4 e 5 della situazione A, per la revisione finale e le tre corse della suite fatte su `b5-parziale`.
4. La condizione 6 della situazione A, con «Regole approvate» che dice «rinviate dall'utente» e «Prova reale» che dice «non fatta: regole rinviate», e la proposta di unire solo `b5-parziale`.
5. La condizione 7 della situazione A, con il commit su `main` che comincia con `tollgate B5 (parziale):` e la riga della memoria che comincia con `- B5 parziale` al posto di `- B5 eseguito`.
