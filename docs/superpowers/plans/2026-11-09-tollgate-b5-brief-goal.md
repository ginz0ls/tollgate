# Brief per l'agente che esegue B5 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-09-tollgate-b5-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md` (profilo `backend`: server, API, Worker di Cloudflare; 9 task) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-09-tollgate-b5-esecuzione.md`:
- ramo `b5-profilo-backend`, worktree `.claude/worktrees/b5`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio.

## Fermate previste (non sono la fine del lavoro)

- **Task 5, Step 1:** mostri all'utente la pagina delle regole `docs/profili/backend.md`, in parole semplici, e aspetti che le approvi, le corregga o le tolga.
- **Prima del merge su `main`:** mandi il rapporto e chiedi l'OK. Senza OK non si unisce niente.
- Le altre fermate sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione.

## Finito quando

Ogni condizione si controlla leggendo un file o il transcript, senza interpretazioni. Valgono tutte:
1. `progress.md` del workspace ha, per ciascuno dei Task 1-9, una riga che comincia con `Task N: complete`.
2. `skills/rules-backend/SKILL.md` ha una riga `approved: <AAAA-MM-GG>`, e `docs/profili/backend.md` ha la riga «Approvata dall'utente il <AAAA-MM-GG>.» con la stessa data.
3. `docs/verifiche/2026-11-09-b5-prova-flusso.md` esiste e ha una riga «Esito:» che dice «riuscita» oppure «non riuscita» con il motivo.
4. `progress.md` ha una riga della revisione finale opus e, dopo, una riga di ri-revisione che dice che i rilievi `critical` e `important` sono tutti indirizzati (o una revisione finale con 0 `critical` e 0 `important`).
5. `progress.md` ha tre righe «Suite finale corsa 1», «corsa 2», «corsa 3», ognuna con l'esito verde su python3.11 e python3.
6. Nel transcript c'è un messaggio all'utente, prima del merge, con le sezioni intitolate «Commit e test», «Regole approvate», «Decisioni prese durante il lavoro», «Rilievi minori rinviati», «Prova reale», «Cosa cambia nei progetti»; la sezione «Decisioni prese durante il lavoro» ha **una riga per ogni** `Ruling:` di `progress.md`, ciascuna con il costo; la sezione «Rilievi minori rinviati» ha **una riga per ogni** voce `minor (deferred)` rimasta dopo il triage; il messaggio finisce con la domanda «Posso unire su `main`?».
7. Se l'utente ha detto di sì: `git log main` contiene il merge di B5; `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/README.md` esiste su `main`; `plugin-workflow-decisioni.md` della memoria ha una voce su B5 eseguita; e nel transcript, dopo il merge, c'è un messaggio all'utente che comincia con la riga «Chiusura di B5». Se l'utente ha detto di no o non ha ancora risposto, la condizione 6 basta e il lavoro si ferma lì.

**Se l'utente rinvia l'approvazione delle regole**, vale la variante del brief della sessione: Task 1-4 fatti, Task 9 ridotto, revisione finale, suite verde tre volte, e la condizione 6 con la proposta di unire solo i commit dei Task 1-2 e del Task 9 ridotto; la condizione 2 non vale.
