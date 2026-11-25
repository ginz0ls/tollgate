# Brief per la sessione che scrive il piano di C4 (ponte con GitHub)

## Prompt per /goal

```text
Leggi per intero docs/superpowers/plans/2026-11-25-tollgate-c4-brief-scrittura.md e seguilo: scrivi il piano di C4 (ponte con GitHub) e i documenti per eseguirlo, senza eseguirlo. Solo documenti su main, un commit per passo, push dalla guardia. Revisione del piano su Fable a giri finché un giro dice «pronto» con 0 critical e 0 important; chi scrive o corregge su opus, mai sonnet né haiku. Le scelte vere chiedile a me con AskUserQuestion, in parole semplici, con il costo e un consiglio. Hai finito quando valgono i punti della sezione «Finito quando» del brief, controllati sui file: nell'ultimo messaggio lancia i controlli di quella sezione dalla radice del repo e mostrane l'uscita.
```

Leggi questo file per intero prima di fare qualsiasi altra cosa. Questa sessione **scrive** il piano di C4 e i documenti per eseguirlo, e **non lo esegue**.

## Cosa scrivere

Quattro file e uno script, con la data del giorno in cui li scrivi nel nome (qui sotto `<data>`), sul modello di quelli di C2 (`docs/superpowers/plans/2026-11-22-tollgate-c2-profilo-security.md`, `-esecuzione.md`, `-brief-sessione.md`, `-brief-goal.md`, `-verifica-fine.py`) e, per la parte che non è un profilo, di quelli di C1 (`docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md` e gli altri tre):

1. **Il piano di C4**, `docs/superpowers/plans/<data>-tollgate-c4-ponte-github.md`, con `superpowers:writing-plans`. Contiene:
   - «Fatti verificati», con la fonte di ogni fatto (codice di `main` con file e riga, oppure pagina ufficiale di GitHub letta con `WebFetch`);
   - «Global Constraints»;
   - «Decisioni di questo piano», ognuna con il costo se sbagliata;
   - le interfacce che C4 consegna a C5 e a C6 (piano principale, sezione 3, righe «C4 → C5», «C4 → C5, C6», «C4, C5 → C6»), con i nomi veri;
   - «Review Focus», «Mappa dei file», «Copertura» (ogni punto del progetto 4, 7 e 8 e ogni voce della riga C4 del piano principale ha un task, oppure un rinvio con il motivo);
   - i task, con firme e test, non con il codice;
   - la tabella «Revisione del piano» in fondo.
2. **Le istruzioni d'esecuzione**, `<data>-tollgate-c4-esecuzione.md`: ramo `c4-ponte-github`, worktree `.claude/worktrees/c4`, sessione avviata dalla radice del repo; scan pre-flight; ordine e modelli; regole di cautela con le sole eccezioni del controller, una per una (in C4 c'è GitHub vero nella sonda: va scritto chi, dove, con quale token, e cosa non si fa mai); quando fermarsi e chiedere; chiusura.
3. **Il brief della sessione d'esecuzione**, `<data>-tollgate-c4-brief-sessione.md`, con «Il lavoro è finito quando».
4. **Il brief corto per l'obiettivo**, `<data>-tollgate-c4-brief-goal.md`. In testa ha la sezione `## Prompt per /goal`, con il testo esatto da incollare dopo `/goal`. Poi ha «Finito quando» scritto a situazioni, con le righe esatte del ledger, come quello di C2.
5. **Lo script di verifica**, `<data>-tollgate-c4-verifica-fine.py`, che controlla ogni condizione di «Finito quando» sui file, stampa la situazione e l'esito di ognuna, ed esce con 0 quando il lavoro è finito o «finito per ora». Va provato a secco su tutte le situazioni previste (in C2 erano 25), e il brief-goal dice quante.

Solo documenti: nessun codice del plugin, nessun `claude -p`, nessun eval, **nessuna chiamata a GitHub vero** salvo il push di `main` dalla guardia. Rete solo per leggere con `WebFetch` le pagine ufficiali che servono ai fatti del piano. Lavora su `main`, con un commit per ogni passo e per ogni giro di revisione.

## Da leggere, in quest'ordine

1. **La memoria del progetto**: `plugin-workflow-decisioni.md` (voci di C, le righe «- C1 eseguito» e «- C2 eseguito»), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `feedback-modelli-fable-opus.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.
2. **Il progetto di C** `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`.
   - Sezioni 4, 7 e 8 per intero: sono l'autorità per C4.
   - Sezioni 2 (obiettivi e anti-obiettivi), 3 (le taglie decidono quali lavori vanno sulla bacheca di progetto), 6, 10, 12, 13 e 14.
   - Sezioni 5 e 9 per sapere cosa useranno C5 e C6 di ciò che C4 costruisce.
   - Le scelte marcate «utente» non si discutono. Quelle marcate «mia scelta» si correggono solo con un motivo scritto nel piano.
3. **Il piano principale di C** `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`: sezione 1 (regole 1-6, soprattutto la 3 e la 5), riga C4 della sezione 2, sezione 3 (ciò che C1 dà a C4 e ciò che C4 dà a C5 e C6), sezione 4, sezione 6 (i rischi sul token, sulle sotto-issue e sui 500), sezione 7 (decisioni 2, 3 e 5), sezione 8 (rinvii: «Da C1 (rilievo F6), per C4» è da chiudere qui), sezione 9.
4. **La spec del nucleo** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 37 (C2): le parti su GitHub (11.2 e il token dell'agente), sullo stato locale e le migrazioni, sugli eventi e la busta, su `tollgate.toml`, su `/tollgate:setup`, e la 16.
5. **I documenti di C1 e il suo registro**: il piano `2026-11-20-tollgate-c1-tracciamento-locale.md` e `docs/sdd/2026-11-20-tollgate-c1-tracciamento-locale/` (`README.md`, `progress.md`, `final-review.md`, `rapporto-merge.md`). C4 legge ciò che C1 ha prodotto.
6. **Il registro di C2** `docs/sdd/2026-11-22-tollgate-c2-profilo-security/` (`README.md`, `progress.md`, `cautele.md` se c'è, `final-review.md`, `rapporto-merge.md`): il metodo più recente e le sue lezioni.
7. **Il codice reale di `main`**, da cui partono i nomi (piano principale, regola 1: valgono quelli del codice):
   - gli eventi e la busta: `events.EVENT_TYPES`, con `size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost`;
   - la taglia: `work_items.size`, `size_by`, `slices`; `tollgate_analysis.worksize`, `tollgate_core.sizes`;
   - la fotografia: `tollgate snapshot`, `tollgate_core.snapshot.build`, e `tollgate_analysis.turn.waiting_on`;
   - lo stato locale e le migrazioni (l'ultima è la 7, di C1): dove nasce una migrazione nuova per la coda;
   - tutto ciò che oggi parla con GitHub: come si chiama `gh`, come si trattano gli errori e i 500, dove sta il token dell'agente, `spikes/gh-p4/ghguard.py`;
   - `tests/fakegh.py`: cosa sa fare oggi e cosa manca per i Projects, le sotto-issue e le assegnazioni;
   - `/tollgate:setup` e la configurazione (`bin/tollgate_core/config.py`, `tollgate.toml`): dove entrano il token delle bacheche e la tabella `[board]`;
   - i test degli strati (`tests/test_layers.py`): in quale strato può stare il codice che chiama GitHub.
8. **Le pagine ufficiali di GitHub**, con `WebFetch`, per ogni fatto che il piano usa: i Projects di un account personale con l'API GraphQL (creare il Project, i campi personalizzati, aggiungere un'issue, aggiornare un campo); gli scope dei token classici e i permessi dei token a grana fine; le sotto-issue e le dipendenze tra issue; le assegnazioni; i limiti di frequenza. Dalle pagine si prendono fatti con parole nostre, mai testo intero.

## Scelte dell'utente, da non riaprire

- **Due bacheche.** La principale è un GitHub Project dell'account dell'utente con una scheda per repo e le due percentuali (fette unite su fette totali; issue chiuse su issue totali). Quella di progetto è un Project per repo, con i lavori medi e grandi (progetto 4.1 e 4.2).
- **Solo il codice di tollgate aggiorna GitHub, mai il modello**: aggiornare la bacheca non consuma token (progetto 4.4, anti-obiettivo).
- **«Va bene indietro».** La bacheca si aggiorna quando tollgate gira sulla macchina dell'utente. **Nessun workflow di GitHub Actions** per le bacheche: il token resta solo sulla macchina.
- **Solo l'account personale.** I repo delle organizzazioni restano fuori da C.
- **Niente di delicato su GitHub**, con la stessa regola per repo privati e pubblici: la lista «non va mai» del progetto 7 è vincolante, e c'è un test che fallisce se una scrittura la viola.
- **Gli avvisi** sono l'assegnazione della scheda o dell'issue all'utente; la notifica la manda GitHub. Nessun sistema di notifiche nuovo.
- **Più computer, anche insieme**, sullo stesso repo.
- **Ruoli**: tollgate non gestisce permessi.
- **Modelli (22/11/2026)**: chi cerca i difetti usa Fable, chi scrive o corregge usa opus, mai sonnet né haiku. Vale per questa sessione, per la sessione d'esecuzione e per ciò che il piano scrive sui subagenti.
- **Le prove dal vivo** l'utente le fa tutte alla fine, con C6. C4 fa solo una **sonda** sul repo di prova per i fatti che solo GitHub vero mostra (piano principale, decisione 5).
- **Il valore di un token non si legge, non si stampa e non si scrive mai** in un file del repo. Si può sapere solo se una variabile è impostata.
- Il repo `ginz0ls/tollgate` è pubblico: niente nomi di progetti privati, nome utente, host o token nei file.
- I profili e le regole approvati non si toccano.

## Punti aperti da decidere nel piano

- **Il token delle bacheche** (piano principale, decisione 3 e primo rischio della sezione 6). Fatto di partenza: per i Projects di un account personale serve un token classico con lo scope `project`. Da decidere: nome della variabile, dove si conserva, come `/tollgate:setup` lo configura senza mai mostrarne il valore, come tollgate capisce che manca. **Se la sonda dice che serve lo scope `repo`, la sessione d'esecuzione si ferma e lo chiede all'utente**: nel piano va scritta la fermata, con la domanda già pronta in parole semplici.
- **La sonda su GitHub vero.**
  - Cosa deve creare l'utente e come (il repo di prova privato, il token), con i passi scritti per chi non è del mestiere.
  - Quali fatti verifica: se il solo `project` basta ad aggiungere a una bacheca un'issue di un repo privato; i campi personalizzati; le sotto-issue e le dipendenze sull'account; le assegnazioni.
  - Quando gira: prima dei task che dipendono dal suo esito, con una fermata se un fatto è diverso dall'atteso.
  - Chi la fa: solo il controller, mai un subagente; cosa lascia sul repo di prova e come si ripulisce.
  - Il rapporto in `docs/verifiche/`, senza nomi né identificativi dell'account.
- **La coda.** La migrazione dello stato (la 8), la forma di una voce (tipo, chiave d'idempotenza stabile da `repo_key`, `issue` e tipo, payload, tentativi, prossima ora), l'attesa crescente con i suoi valori, quando una voce si abbandona e come lo vede l'utente, l'evento `sync` e i suoi dati. L'API che C5 userà per creare issue e sotto-issue, con i titoli passati come dato in un file o in JSON, mai in una riga di comando.
- **Le scritture non idempotenti.** GitHub può rispondere 500 a corpo vuoto anche su un POST andato a buon fine: per ogni tipo di scrittura va detto se si ripete senza rischio o se prima si ricontrolla, e come (per esempio cercando la scheda con l'identificativo stabile).
- **Quando parte lo svuotamento della coda**, senza mai far aspettare il lavoro: a ogni comando o hook che registra un evento, all'avvio di una sessione, con il comando esplicito. Quanto può durare al massimo in un hook, e cosa succede se due processi la svuotano insieme.
- **La macchina che possiede un lavoro.** Come si riconosce una macchina senza mandare `host` su GitHub, dove si scrive chi possiede il lavoro, come un'altra macchina lo adotta.
- **La scheda del repo calcolata da GitHub**, non dallo stato di una sola macchina: la forma esatta dei due conteggi, quante chiamate costa, e come restare sotto i limiti di frequenza.
- **I nomi**: le colonne della bacheca di progetto, i campi personalizzati, i comandi (allineamento, sincronizzazione), le chiavi di `[board]` in `tollgate.toml` e i loro valori predefiniti, il campo `queue` della fotografia (un campo nuovo non cambia `v`).
- **Gli eventi mostrabili**: quali diventano campi e quali commenti brevi, con il controllo della lista «non va mai» su ognuno.
- **L'allineamento.** Quali differenze tollgate sistema da sé e registra, quali segnala e non tocca, e come riconosce un lavoro di un'altra macchina. Il controllo all'avvio di un lavoro non deve bloccare se GitHub non risponde.
- **Gli avvisi.** Come si assegna e come «l'assegnazione torna com'era» quando l'attesa finisce (dove si ricorda chi era assegnato prima).
- **`fakegh` esteso**: Projects, campi, sotto-issue, assegnazioni, errori 500 a corpo vuoto, limiti di frequenza. Nessun test parla con GitHub vero.
- **Il rinvio di C1 da chiudere**: `repo_key` nella fotografia può essere un percorso della macchina (remoto locale); prima di mandare qualcosa su GitHub, C4 lo filtra con la lista «non va mai».
- **Sicurezza fin dal progetto.** C4 tocca un token e scrive verso un servizio esterno: il piano dice per ogni task cosa può andare storto (valore del token in un log o in un messaggio d'errore, titoli non fidati in una riga di comando, dati delicati in un campo) e quale test lo impedisce.
- **Se C4 è troppo grande e va divisa.** È la fetta più grossa di C. Una divisione possibile: prima la coda, il token e la sonda; poi le bacheche; poi l'allineamento e gli avvisi. Decidi se un solo piano o più piani in sequenza, con il costo di ciascuna strada; se la scelta cambia il numero di sessioni o di merge, è una domanda per l'utente.
- **Quale revisione della spec del nucleo** scrive l'ultimo task (oggi 37; se C3 si unisce prima, vale la regola 3 del piano principale).
- **Quali rinvii chiude C4** tra quelli della sezione 8 del piano principale. Gli altri restano aperti, con il motivo.

## Lezioni di C1 e C2 da mettere nel piano e nelle istruzioni

- **Condizioni di fine verificabili sui file, mostrate alla fine (vincolante).** L'hook di Stop giudica «Finito quando» su un transcript che può essere compattato. Quindi, nel brief-goal di C4:
  - ogni condizione si controlla **leggendo un file su `main` o nel worktree**, mai solo il transcript;
  - il rapporto prima del merge si salva **anche** in un file del workspace (`rapporto-merge.md`);
  - le decisioni prese dopo il rapporto del merge sono righe `Nota:`, non `Ruling:`;
  - alla fine la sessione lancia lo script di verifica e ne mostra l'uscita nell'ultimo messaggio.
- **Ciò che viene dopo il merge va detto per esteso.** In C2 l'hook ha rifiutato più volte la chiusura sui passi dopo il merge (CI in corso sull'ultimo commit, subagenti ancora in elenco, commit di documenti). Il brief-goal di C4 elenca quei passi uno per uno, dice quali sono fermate e quali no, e lo script li controlla: CI verde sull'ultimo commit di `main`, nessun subagente della sessione in corso, registro copiato, memoria aggiornata, risposta sul worktree.
- **La suite sotto carico** dura da 1,5 a 2,5 ore per corsa (due interpreti; oggi 4520 test). Ogni giro di correzione costa caro: conviene raccogliere le correzioni e fare una corsa sola. Il brief di ogni implementatore ha le tre righe della suite: uscita su file, attesa `until grep -q '^exit '` in primo piano, commit dopo `exit 0`.
- **Un messaggio a un subagente in esecuzione arriva solo quando si ferma.** Una correzione non si manda a un implementatore che sta girando: si aspetta, oppure si fa in un commit a parte con la sua corsa.
- **I file nuovi vanno aggiunti a git prima della suite.** `tests/test_b1_scripts.py` copia il plugin dai soli file tracciati.
- **La CI di GitHub annulla la corsa precedente** quando arriva un push nuovo sullo stesso ramo. Dopo il merge, i commit di documenti si inviano tutti insieme o a CI finita.
- **Revisioni in parallelo** solo su file diversi e con una `Ruling:`. Il revisore legge con `git show` e lancia i test su una copia `git archive`, mai nel worktree vivo. Due implementatori insieme mai.
- **I subagenti rimasti** compaiono in `ListAgents` e l'hook li conta come lavori in corso. A fine sessione si fermano con `TaskStop` solo quelli della sessione, e si scrive quali nel ledger.
- **La tabella di triage** della revisione finale ha l'esito nell'ultima cella: lo script di verifica lo legge da lì.
- **Le stime dei costi vanno larghe.** La prova reale di C2 è costata 19,55 USD equivalenti di quota contro una stima di 10-18, per i giri degli avversari su Fable.

## Come lavorare

- **Domande all'utente.** Si chiedono le scelte vere (compromessi, costi), con `AskUserQuestion`, in parole semplici, con il costo esplicito (gratis, consumo dell'abbonamento o spesa vera) e un consiglio. Le risposte si scrivono nel progetto di C, nella sezione che toccano, con la data. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere. Il resto si decide con una `Ruling:` scritta nel piano.
- **Revisione del piano.** La fa **Fable** a contesto pulito, in sola lettura, a giri, finché un giro dice «pronto» con 0 critical e 0 important. I minor si correggono. La tabella dei giri va in fondo al piano. Le regole di cautela vanno nel brief di ogni subagente, al lancio.
- **Commit e push.**
  - Bastano `python3 -B -m unittest tests.test_docs` verde e `git status` pulito (salvo il file non tracciato dell'utente `docs/trascrizione edo aws workflow.md`, che non si tocca), perché si toccano solo documenti.
  - Il push si fa solo verso `https://github.com/ginz0ls/tollgate.git`, dopo `P4_PROFILE=p5 python3 -B spikes/gh-p4/ghguard.py gitcheck -- push https://github.com/ginz0ls/tollgate.git main` uscito con 0. Il repo locale non ha un remoto.
  - Se un commit trova `.git/index.lock`, ritenta dopo qualche secondo; non cancellarlo mai (la cartella è sincronizzata da MEGA).
- **Controlli su nome utente, host e token.** In questa shell `grep` è una funzione che salta i binari e i file ignorati: usa `/usr/bin/grep -ra`.
- **Lingua.** Testi in italiano con gli accenti giusti, identificatori in inglese. Risposte all'utente brevi e semplici.

## Stato al momento di questo brief (25/11/2026)

- **`main`** contiene il nucleo, B, C1 e C2 completi. Il merge di C2 è `401cb7e`, il registro è in `docs/sdd/2026-11-22-tollgate-c2-profilo-security/`, la spec del nucleo è alla revisione 37. Tutto è inviato a GitHub, e la CI di `main` è verde.
- **Suite:** 4520 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`, rilanciata su `main` il 25/11/2026.
- **C3** (profilo `ci`) non è iniziata e non ha un piano: è indipendente da C4 e può girare prima, dopo o insieme, in un'altra sessione.
- **Sulla macchina:** `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0. Nessun worktree aperto.

## Finito quando

Ogni punto si controlla leggendo un file. Alla fine lancia i controlli dalla radice del repo e mostrane l'uscita nell'ultimo messaggio.

- I quattro file del piano di C4 e lo script di verifica sono su `main`, committati e inviati a GitHub: `git ls-tree -r --name-only main docs/superpowers/plans/` li mostra, `git status --short` mostra solo il file non tracciato dell'utente, e `git ls-remote https://github.com/ginz0ls/tollgate.git main` dà lo stesso SHA di `git rev-parse main`.
- L'ultima riga della tabella «Revisione del piano» del piano di C4 dice «Pronto», 0 critical, 0 important.
- Il brief-goal di C4 ha la sezione `## Prompt per /goal`, e lo script di verifica, lanciato a secco, dà l'esito atteso su ogni situazione prevista.
- `python3 -B -m unittest tests.test_docs` è verde.
- Il piano principale di C ha, nella riga C4 della sezione 2 o nello stato in testa, il nome del file del piano di C4.
- `plugin-workflow-decisioni.md` nella memoria ha una riga che comincia con «- Piano C4 scritto».
- L'utente ha ricevuto, in italiano semplice:
  - cosa fa C4;
  - le scelte chieste e le risposte;
  - cosa dovrà preparare lui prima dell'esecuzione (il repo di prova privato e il token delle bacheche), passo per passo;
  - quanto costerà eseguirla e quante sessioni servono;
  - dove la sessione d'esecuzione si fermerà a chiedere;
  - il testo per `/goal`, copiato dalla sezione `## Prompt per /goal` del brief-goal di C4.
