# Brief per l'agente che esegue C4a (obiettivo)

## Prompt per /goal

```text
Leggi per intero docs/superpowers/plans/2026-11-25-tollgate-c4-brief-goal.md e seguilo: esegui il piano di C4a (fondamenta del ponte con GitHub) con superpowers:subagent-driven-development, alla lettera secondo docs/superpowers/plans/2026-11-25-tollgate-c4-esecuzione.md, sul ramo c4-ponte-github nel worktree .claude/worktrees/c4, con la sessione avviata dalla radice del repo. Revisori su Fable, implementatori e correzioni su opus, mai sonnet né haiku. La sonda su GitHub vero la fa solo il controller, dalla guardia, e il valore del token non si legge né si stampa mai. A ogni fermata scrivi la riga del ledger e fai una domanda diretta con AskUserQuestion; niente merge su main senza il mio OK. Hai finito quando valgono i punti della sezione «Finito quando» del brief, controllati sui file: nell'ultimo messaggio lancia python3 -B docs/superpowers/plans/2026-11-25-tollgate-c4-verifica-fine.py dalla radice del repo e mostrane l'uscita.
```

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-25-tollgate-c4-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati, cosa prepara l'utente e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-25-tollgate-c4-ponte-github.md` (11 task: `ghcli` per le bacheche, token delle bacheche con la protezione del file e il passo di setup, profilo `c4` della guardia con lo script della sonda, la sonda su GitHub vero, `fakegh` allineato, le operazioni verso GitHub, migrazione 8 e coda, filtro di ciò che esce, svuotamento staccato e comandi `board`, fotografia e pagine d'uso, spec rev 38) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-25-tollgate-c4-esecuzione.md`:
- ramo `c4-ponte-github`, worktree `.claude/worktrees/c4`;
- sessione avviata dalla radice del repo;
- scan pre-flight, revisori, ri-revisioni e revisione finale su **Fable**; implementatori e ogni correzione su **opus**; **mai sonnet né haiku**;
- regole di cautela nel brief di ogni subagente, al lancio, con le tre righe sulla suite (uscita su file, ciclo `until` in primo piano, commit dopo `exit 0`);
- la sonda (Task 4) **solo dal controller**, da sola, con `spikes/c4/probe.py` e il profilo `c4` della guardia; il valore del token non si legge, non si stampa e non si scrive mai.

Scrivi nel ledger le righe esatte che le condizioni qui sotto cercano, con queste parole (elenco completo nella sezione «Righe del ledger che il brief corto cerca» delle istruzioni).

**Dove stanno i file.**
- **Ledger, revisione e rapporto del merge.** Il ledger è `progress.md` del workspace, nel worktree: `.claude/worktrees/c4/.superpowers/sdd/<cartella>/progress.md` (una sola cartella sotto `.superpowers/sdd/`, anche nella variante «sonda rinviata»). Nella stessa cartella stanno `final-review.md` e `rapporto-merge.md`. Dopo il merge la copia del registro è in `docs/sdd/2026-11-25-tollgate-c4-ponte-github/` su `main`, e se il worktree non c'è più lo script legge quella.
- **Rapporto della sonda.** `docs/verifiche/2026-11-25-c4-sonda.md`, nel worktree prima del merge e su `main` dopo. Gli esiti grezzi (`W/sonda-c4/`) restano nel workspace e non vanno mai in git.
- **Piano principale.** `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md` su `main`, riga che comincia con `| **C4a`.
- **Memoria.** `plugin-workflow-decisioni.md` nella cartella `memory/` del progetto sotto `~/.claude/projects/`.

## Fermate previste (non sono la fine del lavoro)

A ogni fermata la sessione scrive nel ledger `Fermata aperta: <caso>`, manda il messaggio e fa una **domanda diretta** all'utente (`AskUserQuestion`); quando l'utente risponde con un sì, un no o una scelta, scrive `Fermata chiusa: <caso> — <risposta>`. Se l'utente risponde con una domanda, la sessione risponde, ripete la richiesta e la fermata resta aperta.
- **Prima della sonda** (`sonda`, Task 4 Step 1, dopo i Task 1-3): il repo privato `tollgate-c4-probe` e il token delle bacheche messo nel file con `board token set`, con i passi del piano. Risposte: «Sì, pronte»; «Non ora: rinvia la sonda a C4b»; «Ho un dubbio».
- **Durante la sonda**, solo se serve: `scope repo` (il solo `project` non basta: domanda già scritta nelle istruzioni), `sotto-issue` (GitHub rifiuta sotto-issue o dipendenze sull'account), `fatto diverso` (un fatto cambia un task e tocca una scelta dell'utente o aggiunge una sessione o un merge). La domanda sulla notifica dopo S13 non è una fermata: la risposta va nella riga `Sonda: S13 notifica — <risposta>`.
- **Una scelta della revisione finale** (`revisione finale`) che tocca una scelta dell'utente: il messaggio comincia con `Fermata: revisione finale`.
- **Prima del merge** (`merge`): il rapporto salvato in `rapporto-merge.md` e mandato all'utente, la riga `Rapporto del merge: consegnato`, poi la domanda. Senza OK non si unisce niente.
- **Dopo il merge** (`worktree`): nel ledger, in quest'ordine e **prima** della copia del registro, `Chiusura di C4a: consegnata` e `Fermata aperta: worktree`; poi la copia del registro, il push, la CI, i subagenti; per ultima, la domanda sul worktree, e dopo la risposta la copia finale del ledger su `main`.
- **Le altre fermate** sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni (`ambiente`, `perimetro`, `piano rotto`); il messaggio di ognuna comincia con la riga `Fermata: <caso>`.

## Finito quando

**Ogni condizione si controlla leggendo un file su `main` o nel worktree, mai solo il transcript.** Lo script `docs/superpowers/plans/2026-11-25-tollgate-c4-verifica-fine.py` (**provato a secco su <N> situazioni**) le controlla tutte e stampa la situazione e l'esito di ognuna: **nell'ultimo messaggio della sessione lancialo dalla radice del repo e incollane l'uscita**. Esce con 0 quando il lavoro è finito, anche «finito per ora» in attesa dell'utente, con 1 altrimenti.

Le condizioni dipendono da **una sola** delle tre situazioni, scelta da ciò che è scritto. **Si controlla prima C** (una fermata aperta nel ledger, diversa da `merge` e `worktree`): se vale, prevale su A e B. Tra A e B decide la riga `Esito:` del rapporto della sonda (nel worktree, o su `main` se il worktree non c'è più): `Esito: riuscita` o `Esito: riuscita con differenze` dà A; `Esito: rinviata a C4b` dà B. Se l'utente prepara la sonda dopo averla rinviata e la sonda si fa, l'`Esito:` cambia e vale A. Senza ledger, con più di un workspace, o senza rapporto della sonda e senza fermate aperte, il lavoro non è finito.

- **C** (fermata aperta): il ledger ha `Fermata aperta: <caso>` senza una `Fermata chiusa: <caso>` dopo, con un caso diverso da `merge` e `worktree` (per esempio `sonda`, `scope repo`, `sotto-issue`, `fatto diverso`, `revisione finale`, `ambiente`, `perimetro`, `piano rotto`). Il lavoro è finito per ora; quando l'utente risponde si riprende, e alla fine vale A o B.
- **A** (lavoro completo con la sonda fatta): il rapporto della sonda ha `Esito: riuscita` o `Esito: riuscita con differenze`.
- **B** (lavoro completo con la sonda rinviata, decisione 25 del piano): il rapporto della sonda ha `Esito: rinviata a C4b`.

**Situazione A.** Valgono tutte:
1. Il ledger ha, per ciascuno dei Task 1-11, una riga che comincia con `Task N: complete`.
2. La sonda:
   - il ledger ha una riga che comincia con `Fermata chiusa: sonda — ` e righe che cominciano con `Sonda: controlla`, `Sonda: esegui`, `Sonda: pulisci` e `Sonda: S13 notifica — `;
   - `docs/verifiche/2026-11-25-c4-sonda.md` ha una riga `Esito: riuscita` o `Esito: riuscita con differenze`, e una riga di tabella che comincia con `| S<n> |` per ognuno dei fatti S1-S22;
   - il rapporto della sonda non contiene il login `ginz0ls`, il nome del repo di prova `tollgate-c4-probe`, `/home/`, né una forma di token (`gh` seguito da una lettera tra `p`, `o`, `u`, `s`, `r`, un trattino basso e almeno 20 caratteri; oppure `github_pat_`).
3. Il ledger ha una riga che comincia con `Revisione finale (Fable):` e, dopo, una che comincia con `Revisione finale chiusa: 0 critical, 0 important aperti`.
4. Il ledger ha le tre righe che cominciano con `Suite finale corsa 1: verde su python3.11 e python3`, `Suite finale corsa 2: verde su python3.11 e python3`, `Suite finale corsa 3: verde su python3.11 e python3`.
5. Il rapporto del merge `rapporto-merge.md` del workspace (o, se il worktree non c'è più, la sua copia su `main`):
   - ha le sezioni `## Commit e test`, `## La sonda`, `## Il token delle bacheche`, `## Decisioni prese durante il lavoro`, `## Rilievi minori rinviati`, `## Cosa cambia nei progetti`;
   - nella sezione «La sonda» ha le parole `riuscita` (che coprono anche «riuscita con differenze»);
   - in «Decisioni prese durante il lavoro» ha **un elemento di elenco (`- `) per ogni** riga `Ruling:` del ledger scritta **prima** della riga `Rapporto del merge: consegnato` (le decisioni dopo il rapporto sono righe `Nota:` e non contano);
   - in «Rilievi minori rinviati» ha **un elemento di elenco per ogni** riga della tabella di triage di `final-review.md` la cui **ultima cella** comincia con `rinviato`, maiuscole o no (e «Nessuno.» se non ce ne sono);
   - finisce con la riga «Posso unire su `main`?»;
   - e il ledger ha la riga `Rapporto del merge: consegnato`.
6. Dopo il rapporto, una di queste tre (vale l'ultima riga che comincia con `Merge:`):
   - il ledger ha `Fermata aperta: merge` senza la sua chiusura e nessuna riga `Merge:`: l'utente non ha ancora risposto, il lavoro è finito per ora;
   - l'ultima riga `Merge:` è `Merge: no dell'utente`: il lavoro è finito qui;
   - l'ultima riga `Merge:` è `Merge: OK dell'utente`, e valgono **tutti** i passi dopo il merge, uno per uno:
     1. **Merge.** `git log --first-parent main` ha un commit con l'oggetto che comincia con `tollgate C4a:`; il più vecchio di questi è il commit del merge (da qui `M`).
     2. **Stato nel piano principale.** Il piano principale di C su `main` ha le parole «unita su» nella riga che comincia con `| **C4a`.
     3. **Memoria.** `plugin-workflow-decisioni.md` della memoria ha una riga che comincia con `- C4a eseguito`.
     4. **Chiusura.** Il ledger ha `Chiusura di C4a: consegnata` e, dopo di essa, `Fermata aperta: worktree`.
     5. **Registro.** `docs/sdd/2026-11-25-tollgate-c4-ponte-github/README.md` è su `main`, e la cartella su `main` non contiene file di `sonda-c4/`.
     6. **CI verde sull'ultimo commit di `main`.** L'ultima riga del ledger che comincia con `CI di main: verde su ` dà uno SHA che esiste; `M` è un suo antenato (o è lui); lui è un antenato di `main` (o è `main`); e i commit dopo di lui su `main` toccano **solo** file sotto `docs/sdd/2026-11-25-tollgate-c4-ponte-github/` (al più la copia finale del ledger). Una riga `CI di main: verde su <M>` da sola non basta, perché dopo `M` ci sono i commit del piano principale e del registro.
     7. **Subagenti.** Il ledger ha, dopo `Chiusura di C4a: consegnata`, una riga che comincia con `Subagenti: nessuno in corso`.
     8. **GitHub allineato.** `git ls-remote https://github.com/ginz0ls/tollgate.git main` dà lo stesso SHA di `git rev-parse main`.
     9. **Worktree**, una di queste:
        - il ledger del worktree ha `Fermata aperta: worktree` senza chiusura: la domanda è fatta e l'utente non ha ancora risposto (il worktree c'è ancora): finito per ora;
        - il ledger ha `Fermata chiusa: worktree — tieni tutto` e `git worktree list` mostra ancora `.claude/worktrees/c4`;
        - il ledger ha `Fermata chiusa: worktree — rimuovi solo il worktree`, `git worktree list` non mostra più `.claude/worktrees/c4` e il ramo `c4-ponte-github` esiste ancora;
        - il ledger ha `Fermata chiusa: worktree — rimuovi worktree e ramo`, `git worktree list` non mostra più `.claude/worktrees/c4` e il ramo `c4-ponte-github` non esiste più.
        Se il worktree non c'è più, lo script legge la copia del ledger su `main`, che deve avere la riga `Fermata chiusa: worktree — <risposta>` (la copia finale del ledger del punto 5.10 delle istruzioni); una copia su `main` con la sola `Fermata aperta: worktree` e il worktree assente non basta.

**Situazione B** (sonda rinviata a C4b). Valgono tutte le condizioni della situazione A, con queste differenze:
1. Il ledger ha, per ciascuno dei Task 1-11, una riga che comincia con `Task N: complete` (anche il Task 4, chiuso con il rapporto del rinvio).
2. La sonda:
   - il ledger ha una riga che comincia con `Fermata chiusa: sonda — Non ora` e una riga che comincia con `Sonda: rinviata a C4b`; le righe `Sonda: esegui`, `Sonda: pulisci` e `Sonda: S13 notifica` non servono;
   - `docs/verifiche/2026-11-25-c4-sonda.md` ha la riga `Esito: rinviata a C4b`; la tabella S1-S22 non serve;
   - il rapporto della sonda non contiene il login, il nome del repo di prova, `/home/` né forme di token, come in A.
3. Il rapporto del merge, nella sezione «La sonda», ha le parole `rinviata a C4b`.
4. Le condizioni 3, 4, 5 (salvo la sezione «La sonda») e 6 di A valgono uguali, compresi tutti i passi dopo il merge.

## Situazioni della prova a secco

Specifica per chi scrive lo script `docs/superpowers/plans/2026-11-25-tollgate-c4-verifica-fine.py` (sul modello di `2026-11-22-tollgate-c2-verifica-fine.py`, con le opzioni `--repo`, `--home` e `--senza-rete` per le prove, e una per sostituire il remoto con un repo nudo locale). Ogni situazione si prepara in un repo git temporaneo con un ramo `main`, un worktree finto o vero, un ledger, i file e una `HOME` temporanea con la memoria; per ognuna è scritto l'esito atteso dello script (uscita 0 = finito o finito per ora; 1 = non finito). Il numero di situazioni provate va scritto nel segnaposto della prima frase di «Finito quando».

1. Nessun ledger, né nel worktree né su `main`: 1 («lavoro non cominciato»).
2. Due cartelle sotto `.claude/worktrees/c4/.superpowers/sdd/`: 1.
3. Ledger con qualche `Task N: complete`, nessuna fermata aperta, nessun rapporto della sonda: 1 («lavoro in corso»).
4. C: `Fermata aperta: sonda` senza chiusura: 0 (finito per ora).
5. C: `Fermata aperta: scope repo` dopo `Fermata chiusa: sonda — Sì, pronte`: 0.
6. Fermata `sotto-issue` aperta e poi chiusa (`Fermata chiusa: sotto-issue — la 1`), lavoro in corso: 1 (la fermata chiusa non è più C).
7. Fermata chiusa con il separatore ` - ` o ` – ` invece di ` — `: riconosciuta come chiusa (come la 6).
8. C prevale su A: tutte le condizioni di A vere, ma `Fermata aperta: revisione finale` senza chiusura: 0 con la situazione C.
9. `Fermata aperta: merge` senza chiusura non è C: con A completa fino al rapporto e nessuna riga `Merge:`, 0 («finito per ora» sul merge).
10. A completa fino al rapporto, ma manca `Task 7: complete`: 1.
11. A con il rapporto della sonda `Esito: riuscita con differenze` e la tabella S1-S22 intera: le condizioni della sonda verdi; variante senza la riga `| S17 |`: 1.
12. A con il rapporto della sonda che contiene `tollgate-c4-probe`: 1; variante con `ginz0ls`: 1.
13. A con il rapporto della sonda che contiene una forma di token (nel test costruita a pezzi, mai letterale): 1; variante con `/home/`: 1.
14. A senza la riga `Sonda: esegui` (o senza `Sonda: S13 notifica — `): 1.
15. A con il rapporto del merge senza la sezione `## Il token delle bacheche`: 1; variante senza `## La sonda`: 1.
16. Conteggio delle ruling: tre righe `Ruling:` prima di `Rapporto del merge: consegnato` e tre elementi in «Decisioni prese durante il lavoro»: verde; una `Ruling:` in più prima del rapporto: 1; una `Ruling:` o una `Nota:` dopo il rapporto: non conta, verde.
17. Rinviati: due righe di triage con l'ultima cella `Rinviato` (maiuscola) e due elementi: verde; zero righe e «Nessuno.»: verde; zero righe senza «Nessuno.»: 1; una riga con «rinviato» in una cella che non è l'ultima: non conta.
18. Rapporto del merge che non finisce con «Posso unire su `main`?»: 1.
19. `Merge: no dell'utente` come ultima riga `Merge:`: 0 (finito qui); `Merge: OK dell'utente` seguita da `Merge: no dell'utente`: 0; `Merge: no` seguita da `Merge: OK`: valgono i passi dopo il merge.
20. Dopo il merge, tutto fatto, risposta «tieni tutto» e worktree presente: 0.
21. Dopo il merge, l'ultima riga `CI di main: verde su <M>` con dopo `M` il commit del piano principale (che tocca `docs/superpowers/plans/`): 1.
22. Dopo il merge, `CI di main: verde su <R>` (commit del registro) con dopo solo la copia finale del ledger sotto `docs/sdd/2026-11-25-tollgate-c4-ponte-github/`: verde.
23. Dopo il merge, la riga `CI di main` con uno SHA più vecchio di `M` (antenato di `M`): 1; con uno SHA che non esiste: 1; nessuna riga `CI di main: verde su `: 1.
24. Dopo il merge, manca `Subagenti: nessuno in corso` (o c'è solo prima di `Chiusura di C4a: consegnata`): 1.
25. Dopo il merge, manca la riga `- C4a eseguito` della memoria: 1; manca «unita su» nella riga `| **C4a`: 1; manca il commit con l'oggetto `tollgate C4a:`: 1.
26. Dopo il merge, `Chiusura di C4a: consegnata` senza `Fermata aperta: worktree` dopo di essa (o con la fermata scritta prima della chiusura): 1.
27. Dopo il merge, manca `docs/sdd/2026-11-25-tollgate-c4-ponte-github/README.md` su `main`: 1; la cartella su `main` contiene `sonda-c4/creati.json`: 1.
28. «rimuovi worktree e ramo»: worktree rimosso, ramo cancellato, copia su `main` con `Fermata chiusa: worktree — rimuovi worktree e ramo`: 0; variante con il ramo ancora presente: 1.
29. «rimuovi solo il worktree»: worktree rimosso e ramo presente: 0; variante con il worktree ancora elencato da `git worktree list`: 1.
30. Worktree rimosso ma la copia su `main` ha solo `Fermata aperta: worktree` (manca la copia finale del ledger): 1.
31. Domanda sul worktree fatta e senza risposta, worktree presente, tutto il resto vero: 0 (finito per ora).
32. Remoto diverso: `git ls-remote` del repo nudo che fa da remoto dà uno SHA diverso da `git rev-parse main`: 1; uguale: verde; con `--senza-rete` il controllo si salta.
33. B: sonda rinviata, Task 1-11 `complete`, `Fermata chiusa: sonda — Non ora: rinvia la sonda a C4b`, `Sonda: rinviata a C4b — …`, rapporto con `Esito: rinviata a C4b`, tutto il resto di A, merge OK e passi dopo il merge fatti: 0.
34. B senza la riga `Sonda: rinviata a C4b`: 1; variante con il rapporto del merge che nella sezione «La sonda» non dice `rinviata a C4b`: 1.
35. B poi A: il rapporto della sonda passa a `Esito: riuscita` dopo un rinvio: valgono le condizioni di A (con le righe `Sonda: esegui`, `Sonda: pulisci`, `Sonda: S13 notifica — ` e la tabella S1-S22).
36. Rapporto della sonda con una riga `Esito:` diversa dai tre valori (per esempio `Esito: fallita`): 1.
