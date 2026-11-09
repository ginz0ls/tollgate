# Brief per l'agente che esegue B5 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-09-tollgate-b5-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md` (profilo `backend`: server, API, Worker di Cloudflare; 9 task) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-09-tollgate-b5-esecuzione.md`:
- ramo `b5-profilo-backend`, worktree `.claude/worktrees/b5`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio.

Scrivi nel ledger (`progress.md` del workspace) le righe esatte che le condizioni qui sotto cercano, con queste parole.

## Fermate previste (non sono la fine del lavoro)

- **Task 5, Step 1:** mostri all'utente la pagina delle regole `docs/profili/backend.md`, in parole semplici, e aspetti che le approvi, le corregga, le tolga o rinvii.
- **Prima del merge su `main`:** mandi il rapporto della condizione 6 e chiedi l'OK. Senza OK non si unisce niente.
- Le altre fermate sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione.

## Finito quando

Ogni condizione si controlla leggendo un file o il transcript, senza interpretazioni. Le condizioni dipendono da **una sola** delle tre situazioni, scelta da ciò che è scritto: **A** (regole approvate: `skills/rules-backend/SKILL.md` ha una riga `approved: `), **B** (rinvio: `progress.md` ha una riga che comincia con `Task 5: rinviato dall'utente`), **C** (in attesa: l'ultimo messaggio della sessione all'utente mostra la pagina delle regole e chiede di approvarle, e l'utente non ha ancora risposto). In C il lavoro è finito per ora; quando l'utente risponde si passa ad A o a B.

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
2. Il ramo `b5-parziale` esiste e contiene i commit dei Task 1 e 2 e quello del Task 9 ridotto (decisione 15).
3. Le condizioni 4 e 5 della situazione A, per la revisione finale e le tre corse della suite fatte su `b5-parziale`.
4. La condizione 6 della situazione A, con «Regole approvate» che dice «rinviate dall'utente» e «Prova reale» che dice «non fatta: regole rinviate», e la proposta di unire solo `b5-parziale`.
5. La condizione 7 della situazione A, con il commit su `main` che comincia con `tollgate B5 (parziale):`.
