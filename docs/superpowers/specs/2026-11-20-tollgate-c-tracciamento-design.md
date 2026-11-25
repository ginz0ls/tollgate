# tollgate C: tracciamento, piano a fette e bacheche su GitHub

Avanzamento: **C1 eseguita** il 21/11/2026 e unita su `main` il 22/11/2026 (`e0929a8`). Prova reale corta riuscita (`docs/verifiche/2026-11-20-c1-prova-flusso.md`, un tentativo per passo, circa 0,93 USD equivalenti, nessun addebito); spec del nucleo alla revisione 36. **C2 eseguita** e unita su `main` il 25/11/2026 (`401cb7e`): profilo `security` con le 17 regole approvate dall'utente il 23/11/2026, agenti di area e `final-security`, modelli degli agenti scelti dall'utente il 22/11/2026, sicurezza fin dal progetto in ogni lavoro; prova reale L2 riuscita (`docs/verifiche/2026-11-22-c2-prova-flusso.md`, 19,55 USD equivalenti, nessun addebito); spec del nucleo alla revisione 37. C3-C6 non ancora cominciate. Piano di C4a scritto il 25/11/2026 (`docs/superpowers/plans/2026-11-25-tollgate-c4-ponte-github.md`); C4 divisa in C4a e C4b per scelta dell'utente.

Progetto del sotto-progetto C (20 novembre 2026). È scritto dopo una conversazione con l'utente. Le scelte marcate **utente** non si discutono; quelle marcate **mia scelta** sono del progettista e chi costruisce le può correggere con un motivo scritto.

Riferimenti: la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (rev 35), in particolare 1.3 (cosa è di C), 5 («Spec con più fette»), 11.2 (token dell'agente), 12 (stato locale), 18.4 (eventi); il progetto di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` come modello di forma; il piano principale di B (`docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`) come esempio reale di piano a fette fatto a mano.

## 1. Perché

**tollgate è il primo modulo di un gestionale agentico** che l'utente costruirà più avanti, usando il plugin stesso (utente). All'inizio tollgate si userà da solo, come oggi. Il gestionale, quando arriverà, deve trovare la storia completa dei lavori fatti nel frattempo: per questo C **traccia fin da subito** tutto ciò che il gestionale vorrà mostrare, senza costruire il gestionale (utente).

Oggi lo stato dei lavori sta solo nello stato locale di tollgate (`~/.local/state/tollgate/tollgate.db`, uno per macchina) e nei registri scritti a mano (`docs/sdd/…`, il piano principale di B). Un lavoro grande come B è stato spezzato in fette a mano: progetto, piano principale, una issue e un piano per ogni fetta. Nessuna bacheca mostra a che punto sono i progetti, cosa aspetta l'utente, quanto è costato un lavoro, quali decisioni sono state prese al posto suo.

La spec del nucleo assegna a C (1.3): il piano principale e le fette, le sotto-issue, il kanban con GitHub Projects, la riconciliazione, le decisioni dell'utente sui rilievi (R13). Questo progetto le prende tutte e ci aggiunge il tracciamento per il gestionale.

## 2. Obiettivi, non obiettivi, anti-obiettivi

**Obiettivi**
1. **Tracciare tutto fin da subito**, per il futuro gestionale (utente). Gli eventi nuovi della sezione 6 si registrano nello stato locale ed escono da `tollgate events`.
2. **Lo stato dei lavori su GitHub, su due livelli** (utente; sezione 4):
   - una **bacheca principale** nell'account dell'utente, con **una scheda per repo**;
   - una **bacheca per ogni progetto**, più dettagliata, con i lavori, le fette e gli eventi che si possono mostrare.
3. **Il piano a fette lo crea tollgate** (utente): dal piano approvato crea l'issue madre e una sotto-issue per ogni fetta, con le dipendenze, e le chiude quando le PR sono unite (sezione 5).
4. **Proporzionalità**: tollgate capisce dal lavoro se serve il percorso completo o se basta quello semplice, per non sprecare abbonamento su una cosa piccola (utente; sezione 3).
5. **Niente di delicato su GitHub**: ci va solo ciò che si può mostrare anche in un repo pubblico (utente: i repo sono per lo più privati, qualcuno pubblico; sezione 7).
6. **Pronto per la condivisione con ruoli**: oggi l'utente lavora da solo, ma ogni scheda dice a chi tocca, e i permessi restano a GitHub (utente; sezione 4.3).
7. **Le decisioni dell'utente sui rilievi** registrate per tarare in futuro le revisioni (R13 del nucleo; sezione 6).
8. **GitHub e stato locale allineati** (riconciliazione; sezione 8).
9. **Gli altri sette punti accettati dall'utente il 20 novembre** (utente; dettagli nelle sezioni indicate):
   1. non bloccare mai il lavoro se GitHub non risponde (8);
   2. tracciare le decisioni prese al posto dell'utente, le «ruling» (6);
   3. tracciare i costi (6);
   4. più computer (8);
   5. recuperare la storia dei lavori già fatti (9);
   6. un contratto stabile per il gestionale (10);
   7. avvisare l'utente quando qualcosa aspetta lui (4.3).

**Non obiettivi**
- Il **tabellone visivo del gestionale**: lo costruirà il gestionale (utente). In C l'unica cosa visiva è la bacheca di GitHub Projects.
- **Comandi dal gestionale verso tollgate** (avviare, approvare, sbloccare): il gestionale per ora legge soltanto (mia scelta, dalla conversazione).
- Un **modello di decisione** (per esempio CLM, `github.com/Contrastive-LM/CLM`) dentro C: C lascia solo la «presa» per collegarlo (utente; sezione 3.3).
- Gli eval estesi (sono di D).

**Anti-obiettivi** (C fallisce anche se tecnicamente funziona, se):
- un lavoro si ferma, o un comando dell'utente aspetta, perché GitHub è lento o giù;
- una cosa piccola si porta dietro la cerimonia di una grande (progetto, piano principale, fette, bacheca) e consuma abbonamento per niente;
- su GitHub finisce testo interno: note di ricerca, comandi negati, percorsi della macchina, nome utente, host, token, testo di pagine di terzi;
- l'aggiornamento della bacheca lo fa il modello invece del codice, e quindi consuma token;
- la bacheca dice una cosa e lo stato locale un'altra, senza che nessuno se ne accorga.

## 3. Le taglie: quanto processo serve

### 3.1 Tre taglie (mia scelta, approvata dall'utente come strada)

| Taglia | Cosa è | Cosa fa C |
|---|---|---|
| **Piccolo** | Un'issue, un lavoro, una PR (oggi L0 o L1 con pochi task) | Aggiorna solo la scheda del repo nella bacheca principale e il lavoro nella bacheca di progetto, se esiste. Niente issue madre, niente fette. Il tracciamento locale c'è comunque (gratis) |
| **Medio** | Un lavoro con il suo piano a più task (L1 o L2 di oggi) | Come piccolo, più i task del piano come voci della scheda del lavoro nella bacheca di progetto |
| **Grande** | Un lavoro che si spezza in fette, ognuna con la sua PR | Il percorso completo: issue madre, sotto-issue per le fette con le dipendenze, bacheca di progetto (sezione 5) |

La taglia non sostituisce il livello L0/L1/L2 del nucleo: il livello dice quanto controllare un lavoro, la taglia quanta struttura di gestione costruirgli intorno.

### 3.2 Come si sceglie

- **Chi decide.** tollgate **propone** la taglia all'avvio del lavoro e la scrive in una riga, con il motivo («taglia: medio — piano con 6 task su 2 aree»). Piccolo e medio partono senza aspettare; **grande aspetta un sì dell'utente**, perché è la taglia che consuma più abbonamento (mia scelta).
- **Quando diventa grande, e qual è il sì** (mia scelta, dalla revisione del progetto). All'avvio la taglia può essere solo piccolo o medio, perché le fette esistono solo dopo la spec. Il lavoro diventa grande quando la spec approvata ha più di una fetta: il **sì è l'atto `approve spec <n>` con n > 1**, che il nucleo ha già e che conferma il numero di fette. Non serve un atto nuovo e il lavoro non si ferma: la fetta 1 continua come nel nucleo, e il sì autorizza tollgate a creare issue e bacheca. `size_decided` si registra all'avvio e di nuovo a `approve spec`.
- **Segnali** (mia scelta: regole semplici e deterministiche): la spec o il piano hanno una sezione `## Fette previste` con più di una voce → grande; un piano con più task, o più aree di profilo, o livello L2 → medio; altrimenti piccolo. Le soglie esatte le fissa chi costruisce, con test.
- **Crescita.** Se un lavoro cresce (il livello sale, il piano aggiunge fette), tollgate propone la taglia sopra e aspetta un sì per passare a grande. **Non scende mai da solo** (mia scelta, come il livello del nucleo).
- **Scelta dell'utente.** L'utente può sempre fissare la taglia con un atto, come fa già per il livello (forma dell'atto a chi costruisce).

### 3.3 La presa per un modello di decisione (utente)

La scelta della taglia passa da **un punto unico**, con un'interfaccia chiara: in ingresso i segnali del lavoro, in uscita la taglia proposta e il motivo. In C dentro ci sono le regole di 3.2. In futuro il gestionale ci può collegare un modello di decisione (per esempio CLM, che però richiede una GPU e un modello da 8 miliardi di parametri: per questo non entra in C), senza cambiare il resto di tollgate. Ogni proposta e ogni correzione dell'utente si registrano (evento `size_decided`, sezione 6): sono i dati per confrontare in futuro un modello con le regole.

## 4. Le bacheche su GitHub

### 4.1 Bacheca principale (utente)

- Un **GitHub Project dell'account dell'utente**, con **una scheda per repo** in cui tollgate è attivo.
- Su ogni scheda (utente: le due percentuali; mia scelta: il resto):
  - **avanzamento del piano grande in corso**: fette unite su fette totali;
  - **lavoro aperto in generale**: issue chiuse su issue totali del repo (forma esatta del conteggio a chi costruisce);
  - la fase del lavoro attivo;
  - quante cose **aspettano l'utente** (decisioni, approvazioni, blocchi `needs_you`);
  - l'ultima attività;
  - l'esito dell'ultima CI sul ramo predefinito.

### 4.2 Bacheca di progetto (utente)

- Un **GitHub Project per repo**, con i lavori (taglia medio e grande) e, per i grandi, l'issue madre e le sotto-issue delle fette.
- Colonne per stato: da fare, in corso, in revisione, aspetta te, fatto (nomi esatti a chi costruisce).
- Gli **eventi che si possono mostrare** (mia scelta), come campi o come commenti brevi: cambi di fase, task iniziati e chiusi, cicli di revisione con l'esito, blocchi aperti e chiusi, attese di una decisione dell'utente, PR aperta e unita, costo stimato del lavoro. Mai il testo interno (sezione 7).
- Un repo con solo lavori piccoli può non avere la bacheca di progetto: l'utente la accende o la spegne in `tollgate.toml` (mia scelta).

### 4.3 A chi tocca, ruoli e avvisi

- **A chi tocca** (mia scelta): ogni scheda ha un campo con uno di tre valori: l'utente, un agente, «aspetta una decisione».
- **Ruoli** (utente: per ora da solo, aperto alla condivisione con ruoli): tollgate non gestisce permessi. Chi vede e chi modifica si decide nelle impostazioni del repo, del Project o dell'organizzazione su GitHub. Il giorno che l'utente condivide, tollgate non cambia.
- **Avvisi** (utente: punto 7): quando qualcosa aspetta l'utente, tollgate gli **assegna** la scheda o l'issue; la notifica la manda GitHub. Nessun sistema di notifiche nuovo. Quando l'attesa finisce, l'assegnazione torna com'era.

### 4.4 Chi aggiorna e come

- **Solo il codice di tollgate** aggiorna GitHub, con `gh` (anche `gh api graphql` per i Projects), **mai il modello**: aggiornare la bacheca non consuma token (mia scelta; anti-obiettivo).
- Gli aggiornamenti nascono dagli eventi che tollgate registra già o dai nuovi della sezione 6.
- **Quando** (utente, 20/11: «va bene indietro»). La bacheca si aggiorna **quando tollgate gira sulla macchina dell'utente**: a ogni comando o hook che registra un evento, all'avvio di una sessione e con un comando di sincronizzazione esplicito. Le cose che succedono su GitHub a computer spento (merge di una PR, CI sul ramo predefinito, un'issue chiusa a mano) la bacheca le mostra al primo uso successivo. **Nessun workflow di GitHub Actions** per le bacheche: il token resta solo sulla macchina.
- **Solo l'account personale** (utente, 20/11). Tutti i repo su cui l'utente usa tollgate sono del suo account personale; le bacheche stanno nel suo account. I repo di organizzazioni restano fuori da C (un'aggiunta futura: un token e una bacheca per organizzazione).
- **Token** (la spec 11.2 lo lascia a C): GitHub Projects richiede il permesso `project`, che il token dell'agente del nucleo non ha. C usa un **token separato** solo per le bacheche, con i permessi minimi (Projects; issue e sotto-issue sui repo dell'utente), configurato una volta da `/tollgate:setup`. Il token dell'agente resta com'è. Forma esatta (token classico o a grana fine, nome della variabile, dove si conserva) a chi costruisce, verificata sulle pagine ufficiali di GitHub. Il valore non si legge, non si stampa e non si scrive mai in un file del repo.
  - **Scelta dell'utente del 25/11/2026:** il token delle bacheche è un token classico e sta in un **file protetto** nella cartella personale dell'utente, fuori dai progetti, leggibile solo dal suo utente. Lo scrive un comando che l'utente lancia nel suo terminale e che chiede il valore senza mostrarlo. Solo il codice di tollgate lo legge, e tollgate impedisce al modello di aprirlo. La variabile d'ambiente è stata scartata perché è visibile a ogni programma lanciato dal terminale. Il resto della forma (percorso, nomi dei comandi) è nel piano `docs/superpowers/plans/2026-11-25-tollgate-c4-ponte-github.md`.

## 5. Il piano a fette (utente: lo crea tollgate)

- **Da dove legge** (mia scelta). La fonte delle fette è la sezione `## Fette previste` della spec approvata, che il nucleo ha già (5, «Spec con più fette»). C la estende con le **dipendenze**: ogni fetta può dire da quali altre dipende (forma esatta a chi costruisce, per esempio `3. Titolo (dopo 1, 2)`). Un «piano principale» separato, come quello di B, resta possibile come documento, ma tollgate legge l'elenco solo dalla spec approvata: è l'unico testo che l'utente ha approvato con un atto.
- **Cosa crea.** Dopo `approve spec` di un lavoro grande:
  - l'**issue madre** del lavoro è l'issue da cui è partito, e **resta aperta fino al merge dell'ultima fetta** (mia scelta, dalla revisione del progetto);
  - una **sotto-issue per ogni fetta, dalla 1 alla n**, collegata all'issue madre con le sotto-issue di GitHub e con le dipendenze tra fette. La fetta 1 è il lavoro corrente, come nel nucleo, ma con la sua sotto-issue: la sua PR chiude la sotto-issue della fetta 1 (`Closes`), non l'issue madre. Oggi il corpo della PR scrive sempre `Closes #<issue>` (`bin/tollgate_analysis/prbody.py`): per un lavoro grande C lo cambia, e chi costruisce controlla cosa legge il gate dal blocco JSON. L'avanzamento conta le fette da 1 a n; l'issue madre la chiude tollgate quando tutte le sotto-issue sono chiuse.
  - Oggi il nucleo **propone** le issue come testo e le crea l'utente o l'agente dopo `approve effect`. Con C le crea tollgate, **con il sì della taglia grande** come autorizzazione (mia scelta: un'autorizzazione per tutte le fette, non una per issue).
- **Titoli non fidati.** I titoli scritti nella spec restano testo non fidato (nucleo 5): non vanno mai in un argomento di `gh` come testo da eseguire; si passano come dato (file o input JSON), mai interpolati in una riga di comando.
- **Avanzamento.** Una fetta parte con `/tollgate:start #M --spec <percorso>` come nel nucleo. Quando la sua PR è unita, la sotto-issue si chiude e le percentuali si aggiornano.
- **Dipendenze e parallelo** (mia scelta, dalla revisione del progetto). Resta la regola del nucleo: le fette dalla 2 in poi partono solo dopo il merge della fetta 1, perché la spec approvata deve stare sul ramo predefinito. Dopo, le dipendenze sono un **vincolo**: `start --spec` rifiuta una fetta che ha una dipendenza non ancora unita, e dice quale. Due fette senza dipendenze aperte possono andare in parallelo. Una spec già approvata senza dipendenze vale come «ogni fetta dopo la precedente», cioè l'ordine dell'elenco.

## 6. Cosa si traccia in più

Gli eventi del nucleo (18.4) restano come sono. C aggiunge tipi nuovi alla busta versione 1 (un tipo nuovo non cambia `v`). Nomi e campi esatti a chi costruisce; i contenuti sono questi:

| Cosa | Perché (dalla conversazione) | Contenuto minimo |
|---|---|---|
| **Taglia** (`size_decided`) | Proporzionalità, dati per la presa di 3.3 | taglia proposta, segnali, motivo, se l'utente l'ha confermata o corretta |
| **Decisioni prese al posto dell'utente** (`ruling`) | Punto 2: oggi stanno solo nei registri scritti a mano (47 solo in B8) | cosa si è deciso, perché, costo se sbagliata, chi ha deciso (agente o utente), a quale lavoro e task si riferisce |
| **Fermate** (`stop_asked`, `stop_answered`) | Le domande dirette all'utente, con la risposta | caso della fermata, domanda in breve, risposta |
| **Costo** (`cost`) | Punto 3 | stima per subagente, per task e per lavoro (token e, dove c'è, dollari equivalenti); da dove viene la stima |
| **Decisioni sui rilievi** | R13: tarare le revisioni | il nucleo ha già `findings.user_decision` e l'evento `finding`; C si assicura che ogni decisione dell'utente su un rilievo (accettato, declassato, archiviato) esca come evento, con la confidenza e la verifica del revisore |
| **Sincronizzazione con GitHub** (`sync`) | Allineamento e coda (sezione 8) | cosa si è scritto su GitHub, esito, tentativi, differenze trovate |

- **Come si registrano le ruling.** Il nucleo non ha oggi un modo per un agente di dichiarare una decisione. C aggiunge un comando (forma a chi costruisce, sul modello di `research submit`) che il controller o un agente usa per registrare una decisione con i quattro campi. La skill o il metodo che usano i subagenti lo citano.
- **Dove sta il costo.** I subagenti hanno già i token (`subagents`, evento `subagent_stop`). Il costo in dollari degli eval viene da `evals/cost.py`. Per il resto è una stima: chi costruisce dice da dove la prende e lo scrive, senza inventare prezzi.
- **Tutto locale.** Questi eventi restano nello stato locale. Su GitHub va solo il riassunto della sezione 7.
- **La storia non si cancella** (mia scelta, dalla revisione del progetto: il gestionale deve trovare la storia completa). Oggi il nucleo cancella gli eventi più vecchi di `[retention] events_days`, 180 giorni per difetto (`bin/tollgate_core/config.py`). Con C il valore predefinito diventa «mai» per tutti gli eventi; l'utente può ancora fissare un numero di giorni in `tollgate.toml`, e allora prima di cancellare tollgate esporta gli eventi in un archivio JSONL nello stato locale (forma a chi costruisce). Gli eventi occupano poco: si scrive nella pagina d'uso quanto, misurato sullo stato reale di B.

## 7. Cosa va su GitHub e cosa no (utente: niente di delicato)

- **Va su GitHub:** titolo del lavoro e delle fette (come dato), stato, fase, livello, taglia, a chi tocca, numeri di avanzamento, link a issue e PR, esito della CI, costo stimato in cifre, numero di cose che aspettano l'utente, esito dei cicli di revisione (ok, da correggere, numero di rilievi).
- **Non va mai su GitHub:** il testo delle note di ricerca, i comandi negati e i motivi dei veti, il testo dei rilievi, il testo delle ruling, percorsi della macchina, nome utente, host, token, testo di pagine di terzi.
- La regola è **la stessa per repo privati e pubblici** (mia scelta): così un repo pubblico non mostra niente di delicato e non serve un interruttore per repo.
- Il campo `host` della busta degli eventi non va su GitHub (è il nome della macchina).

## 8. Robustezza: non bloccare mai, più computer, allineamento

- **Coda.** Ogni scrittura su GitHub passa da una coda nello stato locale. Il lavoro non aspetta mai GitHub: se GitHub non risponde, dà un errore 500 o la rete manca, la voce resta in coda e riparte dopo, con un numero di tentativi e un'attesa crescente (valori a chi costruisce). Lezione già nota: GitHub può rispondere 500 a corpo vuoto anche sui POST, quindi si ripetono senza rischio solo le scritture idempotenti; le altre si ricontrollano prima di riprovare.
- **Idempotenza.** Ogni scrittura su GitHub è fatta in modo che ripeterla non crei doppioni (per esempio, si cerca la scheda prima di crearla, con un identificativo stabile del lavoro).
- **Più computer, anche insieme** (utente, 20/11: sullo stesso repo possono esserci lavori aperti su due macchine nello stesso momento). Lo stato locale è uno per macchina. Su GitHub i lavori si riconoscono dalla coppia (`repo_key`, `issue`), che la busta degli eventi ha già, così due macchine aggiornano la stessa scheda senza doppioni. Ne seguono tre regole (mia scelta):
  - **ogni lavoro ha una macchina che lo possiede**, quella che l'ha avviato o adottato: solo lei scrive i campi della scheda di quel lavoro;
  - **i campi della scheda del repo** (le due percentuali, cosa aspetta l'utente, l'ultima attività, la CI) **si calcolano da GitHub** (issue, sotto-issue, campi delle schede dei lavori), non dallo stato di una sola macchina, così due macchine non si sovrascrivono a vicenda; ricalcolarli più volte dà lo stesso risultato;
  - un lavoro sulla bacheca che la macchina non conosce è **di un'altra macchina**: l'allineamento non lo tocca e non lo segnala come differenza.
  Il dettaglio locale resta su ciascuna macchina; il gestionale lo unirà leggendo gli eventi di ognuna.
- **Allineamento** (riconciliazione). Un comando (e un controllo all'avvio di un lavoro) confronta lo stato locale con GitHub: issue chiuse a mano, schede spostate a mano, fette create a mano. **Lo stato locale comanda** (mia scelta): una differenza che tollgate sa sistemare la sistema e la registra; una che non sa interpretare (per esempio un'issue chiusa a mano mentre il lavoro è aperto) la segnala all'utente e non la tocca.
- **Spento.** Se il token delle bacheche manca o l'utente spegne C in `tollgate.toml`, tollgate funziona come oggi e traccia comunque in locale.

## 9. Recuperare la storia (utente: punto 5)

Un comando porta sulle bacheche i lavori già fatti, a partire da ciò che il repo contiene: commit di unione, registri in `docs/sdd/`, piani principali, rapporti in `docs/verifiche/`, issue e PR chiuse. Per tollgate stesso vuol dire P1-P5 e B1-B8. Il comando:
- è da lanciare a mano, una volta per repo, e si può ripetere senza doppioni;
- **non inventa** dati che non trova: un costo o una data che manca resta vuoto;
- non riscrive lo stato locale dei lavori passati: crea le schede e, se serve, eventi marcati come «recuperati» (forma a chi costruisce).

## 10. Il contratto per il gestionale (utente: punto 6)

- `tollgate events --after-seq <n>` resta l'unico contratto per la **storia** (nucleo 18.4).
- C aggiunge un comando che dà la **fotografia di oggi** in JSON: lavori, taglie, fette con dipendenze, fase, a chi tocca, cosa aspetta l'utente, avanzamento, costo, stato della coda verso GitHub. Ha un numero di versione, come la busta: un campo nuovo non cambia la versione, un campo tolto o cambiato sì.
- I due comandi sono **in sola lettura** e sono documentati in `docs/uso/`: sono ciò su cui il gestionale si appoggerà.

## 11. I profili `security` e `ci` (utente, 20/11/2026)

**Scelta dell'utente:** il profilo `security`, rimasto fuori da B (che aveva scelto di aggiungere gli altri profili «quando un progetto reale ne ha bisogno»), entra nel piano di C come **una fetta a sé**, costruita con il modello **Fable** (`claude-fable-5-2`), il più capace. Con lo stesso «va bene come dici tu» entra anche il profilo **`ci`**, nella stessa fetta o in quella subito dopo (lo decide il piano principale): condivide con `security` lo specialista finale `final-security`, e i workflow sono un punto delicato per la sicurezza (permessi dei token, azioni fissate per SHA, segreti).

- **Cos'è.** Il profilo già progettato nel catalogo (`docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, righe `security` e `rules-security`): si accende su `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**`, porta il lavoro a L2, ha un implementatore e un revisore di area e lo specialista finale `final-security`, che il catalogo usa anche per `ci`. Le regole (`rules-security`) vengono dalle fonti elencate nel catalogo (`security-and-hardening` e `security-auditor` di agent-skills, MIT; le altre da leggere prima, licenza compresa).
- **Come si fa.** Come i profili di B (B3-B7):
  - fonti verificate e copiate con la licenza;
  - regole scritte con parole nostre, ognuna con la sua fonte;
  - pagina del profilo;
  - approvazione dell'utente prima di accendere il blocco;
  - agenti di area;
  - tabella delle precedenze con gli altri profili, con un test ciascuna;
  - prova reale.
- **Fable dove serve giudizio** (utente: «usando Fable»; mia scelta su dove): la verifica delle fonti, la scrittura delle regole, la revisione del piano, la revisione finale e, se il catalogo lo conferma, il modello di `final-security` e del revisore `security`. Gli implementatori meccanici possono restare sonnet. Il modello di ogni agente si scrive nel suo frontmatter, come per gli altri profili. **Aggiornato il 23/11/2026, a C2 costruita:** la frase sugli implementatori sonnet non vale più. L'ha superata la scelta dell'utente del 22/11/2026 sui modelli (sotto): chi scrive o corregge usa opus, chi cerca i difetti Fable, mai sonnet, sia per chi costruisce le fette sia per gli agenti di tollgate. `reviewer-security` e `final-security` sono su Fable, `implementer-security` su opus.
- **Cosa non cambia.** I profili approvati di B (`base`, `ai`, `infra`, `backend`, `frontend`, `database`) non si toccano. Dove una regola di `security` si sovrappone a una già approvata (i segreti di `backend` e `database`, RLS di `database`), la pagina del profilo lo dice e l'utente decide all'approvazione.
- **`ci`.** Percorsi del catalogo: `.github/workflows/**` (esclusi i `tollgate-*`, che sono del gate), `.gitlab-ci.yml`, `scripts/ci/**`; livello minimo L2; regole `rules-ci` dalle fonti del catalogo (`ci-cd-and-automation` di agent-skills, MIT; `gha-security-review` di getsentry, Apache-2.0, da leggere prima). Si costruisce come `security`, con Fable negli stessi punti, e con la stessa approvazione dell'utente.
- **Ordine.** È una fetta indipendente dal tracciamento: il piano principale di C decide dove metterla, e la può far girare anche prima delle bacheche.
- **Scelte dell'utente del 22/11/2026, scrivendo il piano di C2** (`docs/superpowers/plans/2026-11-22-tollgate-c2-profilo-security.md`):
  - **Modelli (utente).** Chi trova i bug usa **Fable**, chi scrive o corregge il codice usa **opus**, **mai sonnet**. Vale in tre posti, tutti scelti dall'utente: i subagenti che costruiscono C2 (revisori di task, ri-revisioni, scan, verifica delle fonti, revisione del piano e revisione finale su Fable; implementatori e giri di correzione su opus); gli agenti di `security` (`reviewer-security` e `final-security` su Fable, `implementer-security` su opus); e gli agenti già esistenti di tollgate, comprese le aree approvate (ogni revisore, specialista finale, verificatore, auditor e avversario su Fable; ogni implementatore su opus). Anche gli eval di `evals/` passano da sonnet a opus, subito (l'utente lo ha scelto dopo che gli è stato detto che i punteggi nuovi non si confrontano con quelli vecchi). Le regole e le pagine approvate non cambiano: cambia solo il campo `model` degli agenti e il modello delle prove e degli eval. Costo accettato: più quota dell'abbonamento a ogni lavoro, nessuna spesa in denaro.
  - **`**/*session*` esce (utente).** La forma non è tra le quattro dei frammenti e, sui progetti dell'utente, i nomi con «session» sono per lo più sessioni di chat degli agenti e documenti «…-sessione.md», non login: accenderli porterebbe in L2 lavori che con la sicurezza non c'entrano. I file di login restano coperti dalle cartelle, dai file `middleware`/`proxy` e dal rilevamento per contenuto.
  - **Rilevamento per contenuto delle sole librerie di password e di token (utente):** hashing delle password e firma o verifica dei token; non le librerie di login complete né i client dei servizi.
  - **Prova reale fino alla revisione finale con `final-security` (utente)**, come la prova di B7.
  - **I file di login riconosciuti per contenuto da un altro profilo accendono anche `security` (utente).** Un file dentro una cartella `auth/` che `backend` o `frontend` trovano dalle loro librerie (una rotta di Next.js, un file Express) resta a quel profilo per l'implementatore, ma `security` si accende lo stesso per la cartella: regole di sicurezza note al revisore e `final-security` alla revisione finale. È una deroga, per il solo `security`, alla regola di I-1 scelta dall'utente in B5.
  - **Sicurezza fin dal progetto in ogni lavoro (utente).** Anche fuori dal profilo `security`, chi pianifica e chi implementa pensa alla sicurezza: gli avversari della spec e del piano cercano ciò che il documento non dice su chi accede, dati, segreti e input ostili; ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi, e lo scrive nel report; i revisori lo controllano.
- **Gli altri profili del catalogo restano dopo C** (mia scelta, accettata dall'utente), uno alla volta quando un progetto reale ne ha bisogno: prima `3d` (l'utente lavora con Three.js), `a11y` e `performance` (rinforzano `frontend`) e `analytics`; poi `e2e`, `copy`, `docs`, `mobile`. Sono scritti nella lista delle cose da fare dopo: il blocco «Dopo B» della sezione 9 del piano principale di B (voce 6), che il piano principale di C riprenderà.

## 12. Lasciato a chi costruisce

- Nomi dei comandi, degli atti, dei campi e dei tipi di evento nuovi, e le loro firme.
- Le soglie esatte delle taglie, con un test per ognuna.
- La forma delle dipendenze in `## Fette previste`, e come si comporta con le spec già approvate senza dipendenze.
- Come si creano e si aggiornano i Projects (API GraphQL di GitHub con `gh api graphql`, campi personalizzati), verificato sulla documentazione ufficiale di GitHub prima del codice; la forma del token; cosa fare se l'API delle sotto-issue non è disponibile per un account.
- La forma della coda, dei tentativi e dell'allineamento.
- Da dove viene la stima dei costi fuori dagli eval.
- La divisione in fette di C stesso (come B1-B8 per B), con il piano principale di C.
  - **Scelta dell'utente del 25/11/2026:** la fetta del ponte con GitHub (C4) si costruisce in **due parti**: prima le fondamenta (C4a: token, coda che non blocca, sonda su GitHub vero, `fakegh` esteso, filtro di ciò che esce), poi le bacheche, gli avvisi e l'allineamento (C4b), con il piano di C4b scritto dopo la sonda. Costo accettato: una sessione di scrittura e una d'esecuzione in più, un merge in più, più quota dell'abbonamento; nessuna spesa in denaro.

## 13. Come si prova che funziona

- **Test senza rete**, come nel resto del progetto: il `gh` dei test è `tests/fakegh.py`, da estendere con i Projects e le sotto-issue. Nessun test parla con GitHub vero.
- **Una prova vera su un repo di prova** dell'utente (privato, creato apposta), sul modello delle prove di P4: un lavoro piccolo, uno medio, uno grande con tre fette, una caduta simulata di GitHub (coda), un'issue chiusa a mano (allineamento), il recupero della storia. Rapporto in `docs/verifiche/`.
- **Controllo di ciò che va su GitHub**: un test che scorre ogni scrittura verso GitHub e fallisce se contiene un campo della lista «non va mai» della sezione 7.

## 14. Vincoli

- Come il resto di tollgate: Python ≥ 3.11 e solo libreria standard in `bin/` e nei test; strati del nucleo rispettati (`tests/test_layers.py`); suite verde su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- Nessun modello di linguaggio nel codice di C (la presa di 3.3 resta vuota di modelli). Fable si usa per costruire la fetta `security` (sezione 11), non dentro tollgate. Dal 22/11/2026 gli agenti di tollgate dichiarano `fable` o `opus` nella riga `model:` (scelta dell'utente, sezione 11): è il modello con cui Claude Code fa girare i subagenti, non un modello chiamato dal codice di C.
- Profili e regole approvati di B non si toccano.
- Il repo `ginz0ls/tollgate` è pubblico: nei test e nei documenti niente nomi di progetti privati, nome utente, host o token.
