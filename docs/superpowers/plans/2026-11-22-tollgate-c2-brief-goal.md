# Brief per l'agente che esegue C2 (obiettivo)

## Prompt per /goal

```text
Leggi per intero docs/superpowers/plans/2026-11-22-tollgate-c2-brief-goal.md e seguilo: esegui il piano di C2 (profilo security) con superpowers:subagent-driven-development, alla lettera secondo docs/superpowers/plans/2026-11-22-tollgate-c2-esecuzione.md, sul ramo c2-profilo-security nel worktree .claude/worktrees/c2, con la sessione avviata dalla radice del repo. Revisori su Fable, implementatori e correzioni su opus, mai sonnet. A ogni fermata scrivi la riga del ledger e fai una domanda diretta con AskUserQuestion; niente merge su main senza il mio OK. Hai finito quando valgono i punti della sezione «Finito quando» del brief, controllati sui file: nell'ultimo messaggio lancia python3 -B docs/superpowers/plans/2026-11-22-tollgate-c2-verifica-fine.py dalla radice del repo e mostrane l'uscita.
```

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-22-tollgate-c2-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-22-tollgate-c2-profilo-security.md` (profilo `security`: autenticazione, autorizzazione, middleware e proxy, con lo specialista finale `final-security`; in più i modelli di tutti gli agenti di tollgate; 8 task) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-22-tollgate-c2-esecuzione.md`:
- ramo `c2-profilo-security`, worktree `.claude/worktrees/c2`;
- sessione avviata dalla radice del repo;
- revisori, scan e verificatori su **Fable**, implementatori e giri di correzione su **opus**, i Task 2 e 3 su **Fable**; **mai sonnet né haiku**;
- regole di cautela nel brief di ogni subagente, al lancio, con le tre righe sulla suite (uscita su file, ciclo `until` in primo piano, commit dopo `exit 0`).

Scrivi nel ledger le righe esatte che le condizioni qui sotto cercano, con queste parole (elenco completo nella sezione «Righe del ledger che il brief corto cerca» delle istruzioni).

**Dove stanno i file.**
- **Ledger, revisione e rapporto del merge.** Il ledger è `progress.md` del workspace, nel worktree: `.claude/worktrees/c2/.superpowers/sdd/<cartella>/progress.md` (una sola cartella sotto `.superpowers/sdd/`). Nella stessa cartella stanno `final-review.md` e `rapporto-merge.md` (nella variante del rinvio `final-review-c2-parziale.md` e `rapporto-merge-c2-parziale.md`). Dopo il merge la copia del registro è in `docs/sdd/2026-11-22-tollgate-c2-profilo-security/` su `main`, e se il worktree non c'è più lo script legge quella.
- **Regole, pagina, prova.** `skills/rules-security/SKILL.md`, `docs/profili/security.md` e `docs/verifiche/2026-11-22-c2-prova-flusso.md` stanno nel worktree prima del merge e su `main` dopo.
- **Memoria.** `plugin-workflow-decisioni.md` nella cartella `memory/` del progetto sotto `~/.claude/projects/`.

## Fermate previste (non sono la fine del lavoro)

A ogni fermata la sessione scrive nel ledger `Fermata aperta: <caso>`, manda il messaggio e fa una **domanda diretta** all'utente (`AskUserQuestion`); quando l'utente risponde con un sì, un no o una scelta, scrive `Fermata chiusa: <caso> — <risposta>`. Se l'utente risponde con una domanda, la sessione risponde, ripete la richiesta e la fermata resta aperta.
- **Task 4, Step 1** (`regole`): la pagina `docs/profili/security.md` in parole semplici, con la domanda se approvare, correggere, togliere o rinviare le regole.
- **Una scelta della revisione finale** (`revisione finale`) che tocca una scelta dell'utente o un profilo approvato: il messaggio comincia con `Fermata: revisione finale`.
- **Prima del merge** (`merge`): il rapporto salvato in `rapporto-merge.md` e mandato all'utente, la riga `Rapporto del merge: consegnato`, poi la domanda. Senza OK non si unisce niente.
- **Dopo il merge** (`worktree`): il rapporto «Chiusura di C2», la riga `Chiusura di C2: consegnata`, la copia del registro su `main` e, per ultima, la domanda sul worktree.
- **Le altre fermate** sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni; il messaggio di ognuna comincia con la riga `Fermata: <caso>`.

## Finito quando

**Ogni condizione si controlla leggendo un file su `main` o nel worktree, mai solo il transcript.** Lo script `docs/superpowers/plans/2026-11-22-tollgate-c2-verifica-fine.py` (provato a secco su 14 situazioni) le controlla tutte e stampa la situazione e l'esito di ognuna: **nell'ultimo messaggio della sessione lancialo dalla radice del repo e incollane l'uscita**. Esce con 0 quando il lavoro è finito, anche «finito per ora» in attesa dell'utente.

Le condizioni dipendono da **una sola** delle quattro situazioni, scelta da ciò che è scritto. **Si controllano prima C e D** (una fermata aperta nel ledger, diversa da `merge` e `worktree`): se una delle due vale, prevale su A e B. Tra A e B: se `skills/rules-security/SKILL.md` ha la riga `approved: `, vale A anche se il ledger ha la riga del rinvio.

- **C** (in attesa dell'utente sulle regole): il ledger ha `Fermata aperta: regole` senza una `Fermata chiusa: regole` dopo.
- **D** (fermata per un altro caso): il ledger ha `Fermata aperta: <caso>` senza la sua `Fermata chiusa`, con un caso diverso da `regole`, `merge` e `worktree`.
- **A** (regole approvate): `skills/rules-security/SKILL.md` (nel worktree, o su `main` se il worktree non c'è più) ha la riga `approved: <AAAA-MM-GG>`.
- **B** (regole rinviate, anche quando l'utente toglie tutte le regole o rifiuta il profilo): il ledger ha la riga `Task 4: rinviato dall'utente`.

In C e in D il lavoro è finito per ora; quando l'utente risponde si riprende, e alla fine vale A o B.

**Situazione A.** Valgono tutte:
1. Il ledger ha, per ciascuno dei Task 1-8, una riga che comincia con `Task N: complete`, e almeno una riga che comincia con `Prova:`.
2. `skills/rules-security/SKILL.md` ha la riga `approved: <AAAA-MM-GG>`, e `docs/profili/security.md` ha la riga «Approvata dall'utente il <AAAA-MM-GG>.» con la stessa data.
3. `docs/verifiche/2026-11-22-c2-prova-flusso.md` ha una riga `Esito: riuscita`, `Esito: riuscita (composita)` oppure `Esito: non riuscita: <motivo>`.
4. Il ledger ha una riga che comincia con `Revisione finale (Fable):` e una che comincia con `Revisione finale chiusa: 0 critical, 0 important aperti`.
5. Il ledger ha le tre righe `Suite finale corsa 1: verde su python3.11 e python3`, `… corsa 2: …`, `… corsa 3: …`.
6. Il rapporto del merge `rapporto-merge.md` del workspace:
   - ha le sezioni `## Commit e test`, `## Regole approvate`, `## Modelli degli agenti`, `## Decisioni prese durante il lavoro`, `## Rilievi minori rinviati`, `## Prova reale`, `## Cosa cambia nei progetti`;
   - in «Decisioni prese durante il lavoro» ha **un elemento di elenco per ogni** riga `Ruling:` del ledger scritta **prima** della riga `Rapporto del merge: consegnato` (le decisioni dopo il rapporto sono righe `Nota:` e non contano);
   - in «Rilievi minori rinviati» ha **un elemento di elenco per ogni** riga della tabella di triage di `final-review.md` con l'esito `rinviato` (o «Nessuno.» se non ce ne sono);
   - finisce con la riga «Posso unire su `main`?»;
   - e il ledger ha la riga `Rapporto del merge: consegnato`.
7. Dopo il rapporto, una di queste tre:
   - il ledger ha `Fermata aperta: merge` senza la sua chiusura (l'utente non ha ancora risposto): il lavoro è finito per ora;
   - il ledger ha `Merge: no dell'utente`: il lavoro è finito qui;
   - il ledger ha `Merge: OK dell'utente`, e valgono tutte:
     - `git log main` ha un commit con l'oggetto che comincia con `tollgate C2: profilo security`;
     - `docs/sdd/2026-11-22-tollgate-c2-profilo-security/README.md` è su `main`;
     - il piano principale di C su `main` ha la parola «unita» nella riga C2 della sezione 2;
     - `plugin-workflow-decisioni.md` della memoria ha una riga che comincia con `- C2 eseguito`;
     - il ledger ha `Chiusura di C2: consegnata`;
     - `git ls-remote https://github.com/ginz0ls/tollgate.git main` dà lo stesso SHA di `git rev-parse main`;
     - sul worktree: il ledger ha `Fermata aperta: worktree` senza chiusura (domanda fatta, l'utente non ha risposto, oppure il worktree è già stato rimosso e lo script legge la copia su `main`), oppure `Fermata chiusa: worktree — <risposta>` e, se la risposta è di rimuoverlo, `git worktree list` non mostra più `.claude/worktrees/c2`.

**Situazione B** (rinvio delle regole, decisione 19 del piano). Valgono tutte:
1. Il ledger ha una riga che comincia con `Task N: complete` per i Task 1, 2 e 3, la riga `Task 4: rinviato dall'utente` e una riga che comincia con `Task 8 ridotto: complete`; i Task 5, 6 e 7 non si fanno e la prova reale non c'è.
2. Il ledger ha una riga che comincia con `c2-parziale: ` (uno sha e un oggetto) per ogni commit del ramo, tra cui quella con «tollgate C2: revisori su Fable, implementatori su opus, mai sonnet» e quella con «tollgate C2 (parziale): spec rev 37 ridotta».
3. Il ledger ha `Revisione finale c2-parziale (Fable): …`, `Revisione finale c2-parziale chiusa: 0 critical, 0 important aperti` e le tre righe `Suite finale c2-parziale corsa <N>: verde su python3.11 e python3`.
4. La condizione 6 della situazione A sul file `rapporto-merge-c2-parziale.md`, con i rinviati presi da `final-review-c2-parziale.md`, «Regole approvate» che dice «rinviate dall'utente» (o «rifiutate dall'utente») e «Prova reale» che dice «non fatta: regole rinviate».
5. La condizione 7 della situazione A, con il commit su `main` che comincia con `tollgate C2 (parziale):`, la riga della memoria che comincia con `- C2 parziale` e il worktree `.claude/worktrees/c2-parziale`.
