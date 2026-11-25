# Brief per la sessione che esegue C4a

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano di C4a senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-25-tollgate-c4-ponte-github.md` (C4a, fondamenta del ponte con GitHub) con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-25-tollgate-c4-esecuzione.md`: ramo `c4-ponte-github`, worktree `.claude/worktrees/c4`, sessione avviata dalla radice del repo. Il piano ha 11 task:
1. `ghcli` per le bacheche: segreto, redazione, classi d'errore, GraphQL;
2. il token delle bacheche, `[board]`, la protezione del file, `/tollgate:setup`;
3. profilo `c4` della guardia, script della sonda, `fakegh` di base;
4. la sonda su GitHub vero (solo il controller);
5. `fakegh` allineato alla sonda, e i guasti;
6. le operazioni verso GitHub;
7. migrazione 8, la coda, il tipo `sync`;
8. il filtro di ciò che esce, `submit`, `repo_key`;
9. lo svuotamento, l'avvio staccato, i comandi `board`;
10. la fotografia, l'avvio di sessione, le pagine d'uso;
11. revisione 38 della spec, progetto di C, piano principale.

C4a costruisce il **trasporto** verso GitHub. Le bacheche vere (bacheca principale, bacheca di progetto, macchina che possiede un lavoro, avvisi, allineamento) sono di **C4b**, con un piano scritto dopo la sonda.

## Il lavoro è finito quando

- tutti gli 11 task sono `complete` nel ledger, ognuno con la revisione pulita (il Task 4 per il rapporto della sonda);
- la sonda è fatta e il rapporto `docs/verifiche/2026-11-25-c4-sonda.md` ha la riga `Esito: riuscita` o `Esito: riuscita con differenze`, oppure l'utente ha scelto «Non ora» alla fermata `sonda` e il rapporto ha `Esito: rinviata a C4b` (variante «sonda rinviata», decisione 25 del piano);
- la revisione finale (Fable) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto prima del merge è salvato in `W/rapporto-merge.md` e consegnato all'utente nella forma del punto 4 di «Chiusura» delle istruzioni;
- **dopo il merge** (solo con l'OK dell'utente) tutti i passi del punto 5 di «Chiusura» sono fatti, uno per uno: push, CI verde, stato nel piano principale, memoria, trascrizioni, rapporto «Chiusura di C4a», copia del registro, un solo push dei documenti, di nuovo la CI verde sull'ultimo commit, subagenti fermati, domanda diretta sul worktree e copia finale del ledger;
- nell'ultimo messaggio hai lanciato `python3 -B docs/superpowers/plans/2026-11-25-tollgate-c4-verifica-fine.py` e ne hai incollato l'uscita.

**Il merge su `main` non si fa senza l'OK dell'utente.**

**Le condizioni esatte stanno nel brief corto** `docs/superpowers/plans/2026-11-25-tollgate-c4-brief-goal.md`, sezione «Finito quando», e lo script di verifica le controlla tutte **sui file**. Ogni fermata si scrive nel ledger (`Fermata aperta: <caso>`, poi `Fermata chiusa: <caso> — <risposta>`) e si accompagna a una **domanda diretta** con `AskUserQuestion`.

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-25-tollgate-c4-esecuzione.md`: le istruzioni.
2. Il piano di C4a, per intero: «Fatti verificati», «Global Constraints», «Decisioni di questo piano» (32 decisioni), «Le scritture verso GitHub», «Interfacce che C4a consegna», «Cosa C4a lascia pronto per C4b», «La sonda su GitHub vero» (con la tabella S1-S22 e le fermate), «Review Focus», «Mappa dei file», i task, «Copertura», «Costo e tempi dell'esecuzione».
3. Il progetto di C, `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`: sezioni 4, 7 e 8 per intero; poi 2, 3, 5, 6, 9, 10, 12, 13 e 14.
4. Il piano principale di C, `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`: sezioni 1, 2 (righe C4a e C4b), 3, 6, 7 (decisioni 2, 3, 5, 7, 8) e 8.
5. La spec del nucleo rev 37 `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`: 3.1, 7.2, 7.4, 11.2, 11.3, 11.4, 12.2, 16, 18.4, 20.
6. Il registro di C2 `docs/sdd/2026-11-22-tollgate-c2-profilo-security/`: `README.md`, `progress.md`, `cautele.md`, `carry.md`, `preflight-brief.md`, `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `mkbrief.sh`, `task-9-rapporto-brief.md`, `final-review-brief.md`, `final-review.md`, `rapporto-merge.md`.
7. Il codice che il piano cita nei «Fatti verificati»: `bin/tollgate_core/ghcli.py`, `paths.py`, `db.py`, `events.py`, `intents.py`, `config.py`, `snapshot.py`, `cli.py`, `runner.py`; `bin/tollgate_gate/github.py`, `guard.py`, `install.py`; `bin/tollgate_hooks/runner.py`, `context.py`; `bin/tollgate_checks/writes.py`, `bash_rules.py`, `cli_calls.py`, `session.py`; `bin/tollgate_analysis/bash.py`, `prbody.py`; `hooks/run`, `hooks/hooks.json`; `skills/setup/SKILL.md`; `spikes/gh-p4/ghguard.py`; `tests/fakegh.py`, `tests/test_layers.py`, `tests/test_wrapper.py`, `tests/test_db.py`, `tests/test_docs.py`.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di C, le righe «- C1 eseguito», «- C2 eseguito» e «- Piano C4 scritto»), `feedback-modelli-fable-opus.md`, `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di C è l'autorità, poi la spec, poi il piano; per i nomi vale il codice reale.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono. Lo scan fa anche la prova a secco del figlio staccato.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task, le regole di cautela e le tre righe sulla suite. Mai la storia della sessione. Ogni subagente di sola lettura scrive la sua uscita su un file del workspace.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Modelli:** chi cerca i difetti su Fable, chi scrive o corregge su opus, **mai sonnet né haiku** (scelta dell'utente del 22/11/2026, detta con forza: non riproporla e non chiederla di nuovo).
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`. I file nuovi in git prima della suite.
- **Correzioni raccolte, una corsa sola**: una corsa della suite costa 1,5-2,5 ore.
- **Lingua e tono.** Testi in italiano, identificatori in inglese. Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli. Niente gergo nelle domande.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **Due bacheche.** La principale è un GitHub Project dell'account dell'utente con una scheda per repo e le due percentuali (fette unite su fette totali; issue chiuse su issue totali). Quella di progetto è un Project per repo, con i lavori medi e grandi (progetto 4.1 e 4.2). In C4a si costruiscono solo le fondamenta.
- **Solo il codice di tollgate aggiorna GitHub, mai il modello**: aggiornare la bacheca non consuma token (progetto 4.4, anti-obiettivo).
- **«Va bene indietro».** La bacheca si aggiorna quando tollgate gira sulla macchina dell'utente. **Nessun workflow di GitHub Actions** per le bacheche: il token resta solo sulla macchina.
- **Solo l'account personale.** I repo delle organizzazioni restano fuori da C.
- **Niente di delicato su GitHub**, con la stessa regola per repo privati e pubblici: la lista «non va mai» del progetto 7 è vincolante, e c'è un test che fallisce se una scrittura la viola (i canarini).
- **Gli avvisi** sono l'assegnazione della scheda o dell'issue all'utente; la notifica la manda GitHub. Nessun sistema di notifiche nuovo.
- **Più computer, anche insieme**, sullo stesso repo.
- **Ruoli**: tollgate non gestisce permessi.
- **Modelli (22/11/2026)**: chi cerca i difetti usa Fable, chi scrive o corregge usa opus, mai sonnet né haiku.
- **Le prove dal vivo** l'utente le fa tutte alla fine, con C6. C4a fa solo la **sonda** sul repo di prova per i fatti che solo GitHub vero mostra.
- **Il valore di un token non si legge, non si stampa e non si scrive mai** in un file del repo. Si può sapere solo se una variabile è impostata.
- Il repo `ginz0ls/tollgate` è pubblico: niente nomi di progetti privati, nome utente, host o token nei file.
- I profili e le regole approvati non si toccano.
- **C4 in due parti (25/11/2026).** Prima le fondamenta (C4a, questo piano), poi le bacheche (C4b), con il piano di C4b scritto dopo la sonda. Costo accettato: una sessione di scrittura, una d'esecuzione e un merge in più.
- **Il token delle bacheche in un file protetto (25/11/2026).** Token classico, in un file nella cartella personale dell'utente, fuori dai progetti, leggibile solo dal suo utente; lo scrive un comando che l'utente lancia nel suo terminale e che chiede il valore senza mostrarlo; solo il codice di tollgate lo legge e tollgate impedisce al modello di aprirlo. Scartata la variabile d'ambiente.

## Punti delicati di C4a

- **Il token e la sua protezione.** Il file è `~/.config/tollgate/board-token` (cartella 0700, file 0600, decisione 3). Lo legge solo `boardtoken.read`, che lo tiene in un `ghcli.Secret` e lo passa solo come `GH_TOKEN` nell'ambiente del figlio, togliendo `GH_HOST` e `GH_DEBUG`. Nessuno, controller compreso, apre quel file o `~/.config/gh/`. Dopo il Task 2 il guardrail nega anche al modello i comandi che nominano quel percorso: un messaggio di commit o un `grep` che lo nomina si riformula.
- **Il token vero sulla macchina.** Dopo la fermata `sonda` il file vero esiste. Ogni test deve usare `TOLLGATE_BOARD_TOKEN_FILE` con la sentinella o una `HOME` temporanea; un test che arriva alla `HOME` vera è un difetto `critical`. Nei test il token vale `PROVA-123`; una forma di token vero si costruisce a pezzi.
- **La sonda.** Solo il controller, solo con `spikes/c4/probe.py` e la guardia (profilo `c4`), solo sul repo `tollgate-c4-probe` e sui Projects che la sonda crea, prima a secco (`controlla`), poi `esegui`, `pulisci`, `rapporto`. Il rapporto non ha login, nome del repo, id o numeri dell'account: segnaposto. La domanda sulla notifica (S13) non è una fermata. I fatti diversi dall'atteso cambiano i task dopo con una `Ruling:`.
- **Il figlio staccato.** Hook e comandi mettono solo in coda; lo svuotamento parte con un doppio `fork` e non deve far aspettare nessun hook (un hook ha 20 s). Lo scan lo prova a secco prima del codice; i test del Task 9 non lasciano processi vivi né zombie.
- **I canarini.** Il test `tests/test_outbound_canaries.py` (Task 8 e 9) è la prova che niente della lista «non va mai» arriva alla coda o a `gh`. C4b e C5 lo estendono: va scritto in modo che un tipo nuovo senza filtro lo faccia fallire.
- **`fakegh` è l'unica verità dei test.** Nessun test parla con GitHub vero. Il Task 5 allinea `fakegh` a ciò che la sonda ha visto, con il numero del fatto accanto a ogni valore; un `fakegh` più gentile di GitHub (che non simula il 500 **dopo** la scrittura, per esempio) farebbe passare un doppione.
- **La migrazione 8.** Rompe i test che fissano la 7 (`test_latest_version_is_7`, `MigrationV7Test`): il Task 7 li sistema tutti; un DB a 7 si migra con la copia `-migrazione-8`.
- **I nomi già occupati.** Esistono già il comando `tollgate sync` e l'azione `sync` di `intents`: i comandi nuovi stanno tutti sotto `tollgate board …`, e l'evento nuovo `sync` è un'altra cosa (tipo in `EVENT_TYPES` e nella riga `**Tipi:**` della spec 18.4, nello stesso commit).

## Cosa deve preparare l'utente prima

Due cose, gratis (il repo privato e i Projects di un account personale non costano niente). I passi, per chi non è del mestiere, sono nella sezione «La sonda su GitHub vero» del piano, punti 1-4:
1. **Il repo di prova privato** `tollgate-c4-probe` nel suo account, con un README (punto 1). Lo può creare anche prima che la sessione cominci. Resta anche dopo C4a: serve a C4b e a C6.
2. **Il token delle bacheche**: un token classico con il solo scope `project`, scadenza 90 giorni (punto 2). Lo può creare anche prima.
3. **Il token nel file**, con `board token set` lanciato in un **suo** terminale dalla cartella del worktree (punto 3). Questo si può fare solo **dopo il Task 2**, perché il comando nasce lì; poi `board token status` deve dire `token delle bacheche: presente`.
4. **Mai incollare il token nella chat** (punto 4); se succede, si cancella e si rifà.

**Quando gli verrà chiesto:** alla fermata `sonda`, dopo i Task 1-3 (circa uno o due giorni di calendario dall'avvio). L'utente può rispondere «Sì, pronte», «Non ora: rinvia la sonda a C4b» (C4a va avanti e si unisce lo stesso; la sonda diventa il primo passo della sessione che scrive C4b) o «Ho un dubbio». Il suo tempo: circa 15 minuti.

## Stato al momento di questo brief (25/11/2026)

- **`main`** contiene il nucleo, B, C1 e C2 completi. Il merge di C2 è `401cb7e`, il registro è in `docs/sdd/2026-11-22-tollgate-c2-profilo-security/`, la spec del nucleo è alla revisione 37. Su `main` ci sono anche il progetto di C con le scelte del 25/11/2026, il piano principale con le righe C4a e C4b, e i file del piano di C4a (piano, istruzioni, questo brief, brief corto, script di verifica). Tutto è inviato a GitHub, e la CI di `main` è verde.
- **Suite:** 4520 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`, rilanciata su `main` il 25/11/2026.
- **C3** (profilo `ci`) non è iniziata e non ha un piano: è indipendente da C4a e può girare prima, dopo o insieme, in un'altra sessione e su un altro ramo (regola 3 del piano principale per il numero della revisione della spec).
- **Sulla macchina:** `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0. Nessun worktree aperto.
- **Il repo locale non ha un remoto configurato**: il push di `main` si fa verso `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.

## Costo e tempi

Stime larghe (lezione di C2: la prova reale di C2 è costata 19,55 USD equivalenti contro una stima di 10-18).
- **Nessuna spesa in denaro.** Niente `claude -p`, niente eval. GitHub è gratis per un repo privato e i Projects di un account personale.
- **Consumo dell'abbonamento:** circa 30-45 subagenti (implementatori e correzioni su opus; scan, revisori e revisione finale su Fable), simile a C2 senza la prova reale. Può essere di più se la revisione finale chiede due giri di correzione, come in C2.
- **Tempo:** una corsa della suite dura 1,5-2,5 ore; dieci task con codice, i giri di correzione e le tre corse finali fanno circa 15-22 corse, cioè **3-6 giorni di calendario** in una sessione d'esecuzione, più le fermate: `sonda` (circa 15 minuti dell'utente), eventuali `scope repo`, `sotto-issue`, `fatto diverso`, poi `merge` e `worktree`.
