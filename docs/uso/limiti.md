# Limiti della garanzia

tollgate ferma gli errori onesti di un agente e ricalcola da zero i fatti di una PR. Non è una barriera contro chi lavora apposta per aggirarlo. Qui sotto c'è l'elenco di quello che resta fuori dalla garanzia, voce per voce. `/tollgate:status` stampa il percorso di questo file.

Le voci seguono la specifica (sezione 1.2). Alcune sono limiti nati con il gate su GitHub e ridotti dagli interventi successivi: dove è successo, la voce lo dice.

## Credenziali, comandi digitati dall'utente ed effetti

### L'agente che usa le credenziali GitHub dell'utente

Lo limitano i guardrail e il token separato consigliato ([installazione](installazione.md)). In modalità `protected` l'agente non può soddisfare la protezione pubblicando lui `tollgate/verdict`: la sorgente è fissata su GitHub Actions e uno stato pubblicato con un altro token non conta.

### I comandi `!` digitati dall'utente

I comandi `!` scritti nel prompt di Claude Code non passano da nessun hook. Possono cambiare file e ramo senza i guardrail locali. Il gate su GitHub ricalcola comunque i fatti della PR.

### Gli effetti esterni

Hanno un solo livello di controllo: quando arriva la PR sono già avvenuti. L'atto `approve effect` serve proprio a decidere prima.

### Il codice scritto nel lavoro ed eseguito in locale

I test e `verify` eseguono il codice del lavoro sulla tua macchina, con l'ambiente ripulito. Se quel codice è ostile, gira.

## Qualità del giudizio e dichiarazioni dell'agente

### Asserzioni rese più deboli o compensate con asserzioni banali

Le cerca il revisore finale, ma nessuna regola meccanica le vede tutte.

### La qualità del giudizio dei revisori

I revisori sono modelli: possono sbagliare, in entrambi i versi.

### Il codice della PR che falsifica l'esito dei propri test

Resta visibile nel diff.

### Scope e deroghe sono dichiarati dall'agente

Il gate verifica che scope e deroghe siano coerenti con il piano e con il diff, non che siano legittimi. Gli atti locali non sono verificabili da GitHub.

### Le PR da rami che non sono `tg/*`

Ricevono dal gate solo i controlli sui test, con `attenzione` rosso. Lo stesso vale per una PR da fork, anche con un ramo `tg/*` o `tollgate-config/*`.

### Una serie di PR L0

Ogni PR piccola è valutata da sola come L0: tollgate non guarda la somma di una serie.

## Il gate su GitHub

### Il sabotaggio deliberato della CI

Per esempio workflow aggiunti per pubblicare stati falsi. Una modalità rinforzata con una GitHub App è prevista dopo la v1.

### In modalità `detect` il merge non è impedito, solo rilevato

Su un repo privato con GitHub Free non c'è protezione del ramo. L'agente con le tue credenziali potrebbe anche coprire la segnalazione; la cronologia degli stati del commit resta visibile. Vedi [modalità](modalita.md).

### Gli identificativi della base presi da un run della PR

Se manca la cache `tollgate-ids-<albero>` della base, `verdict` usa l'artefatto del job `base` di `tollgate-run`. Quel job esegue il codice della base ma nel workflow della PR, che la PR può cambiare, e la cache di quel job può essere avvelenata dal job `head`. Il commento del gate lo dice con la voce `base_ids_from_run` ("da leggere"). I job `workflow_run` hanno la cache in sola lettura, anche sui repo privati con GitHub Free, quindi `verdict` non scrive mai in cache.

### Il codice unito sul predefinito, eseguito da `tollgate-base`

Il job `ids` esegue la suite senza token di scrittura, ma il codice unito può falsificare `ids.json` e con esso lo stato `tollgate/base` in `detect`, e può scrivere voci di cache per alberi diversi dal proprio. Non ottiene mai un token che pubblica stati, e la sentinella non esegue codice del progetto.

### Gli artefatti di `tollgate-run` sono dati non fidati

`upload-artifact` segue i collegamenti simbolici: il codice della PR può farci finire il contenuto di file leggibili dal job. `tollgate-run` non ha segreti né token di scrittura e `verdict` legge gli artefatti come dati. Se `download-artifact` trova un artefatto con un digest diverso lo estrae lo stesso e lo step fallisce; il fallimento è assorbito (`continue-on-error`) e `verdict` legge il contenuto come dato non fidato, come prima.

### Le azioni dei workflow sono fissate per SHA, e uno SHA vecchio non riceve correzioni

Nella revisione 25 della specifica le azioni erano fissate a `@v4`. Dalla versione 0.2.0 sono fissate per SHA, con i valori in `gate/workflows/PINS` ([aggiornarle](emergenze-e-aggiornamenti.md)). Uno SHA non cambia da solo: le correzioni di un'azione arrivano quando aggiorni `PINS` e il tuo progetto con `init --update`.

### I workflow del progetto già presenti

`guard` guarda solo i workflow aggiunti o modificati dalla PR. Quelli già nel repo che violano le sue regole (per esempio `statuses: write` su `pull_request`) non li ferma: `init` li elenca nel `README.md` della proposta e `verdict` li riporta come voce informativa `existing_workflow_rules`.

### File di approvazione e documenti bloccati nei guardrail locali

I file di approvazione si possono falsificare con comandi git e le regole su Bash non conoscono i documenti bloccati. Il gate li ricontrolla dall'albero della testa.

### Un comando della base senza report non ha identificativi da confrontare

Nella revisione 25 un comando richiesto che mancava da `ids.json` non dava nessuna voce. Dalla 0.2.0 la voce "da leggere" `base_ids_missing_command` lo segnala quando il comando ha un report e manca dagli identificativi della base o vi ha uno stato che non è `green`, anche con una cache scritta con una configurazione precedente. Senza report non ci sono identificativi da confrontare e il confronto resta vuoto.

### Il verdetto precedente vale ancora fino al `pending` di `guard`

Nella revisione 25 dopo `edited` o `reopened` il vecchio `tollgate/verdict` valeva fino al nuovo. Dalla 0.2.0 `guard` pubblica `tollgate/verdict` in attesa ("rivalutazione in corso") su `opened`, `edited` e `reopened` verso il ramo predefinito, e `verdict` lo sostituisce. Restano i pochi secondi tra la modifica e quel `pending`, in cui vale ancora il verdetto precedente. Se `verdict` arriva prima di `guard`, la PR resta in attesa e basta rilanciare i controlli.

### `[skip ci]` nel commit di testa dell'ultimo push sul predefinito

Salta `tollgate-sentinel` per quel push. Dalla 0.2.0 ogni push controllato lascia uno stato `tollgate/sentinel` sul commit, e la sentinella risale dai commit non ancora controllati fino all'ultimo con quello stato, scritto da `github-actions[bot]`: un push saltato si controlla al successivo. Resta che l'ultimo push, se salta la sentinella, non è controllato finché non ne arriva un altro. Il segnale è uno stato del commit, che un workflow del progetto con `statuses: write` potrebbe falsificare: rientra nel sabotaggio della CI.

### `tollgate gate … --publish` vale solo dentro GitHub Actions

`--publish` si rifiuta fuori da Actions e il guardrail locale lo nega in un repo attivo. È difesa in profondità: in `protected` uno stato pubblicato con il token dell'utente non conta comunque.

### Un aggiornamento del CLI sul predefinito durante un run non dà errore

`verdict` confronta il contenuto di `tollgate.toml` che il run ha usato con quello della punta del predefinito, non il commit: un merge che non tocca `tollgate.toml` non dà più `error` alle PR in volo. Un aggiornamento di `.github/tollgate/bin/` nello stesso intervallo passa: il run ha eseguito il CLI della sua base, `verdict` usa quello della punta.

## I guardrail locali

### I subagenti con `isolation: worktree` non vengono bloccati

Il subagente parte dal ramo predefinito e le sue modifiche non entrano nel ramo del lavoro.

### I guardrail locali sono «best effort»

Sono hook e regole sui comandi Bash: fermano gli errori onesti, non un agente che sa cosa sta aggirando. Il gate su GitHub è il controllo che non dipende dalla macchina dell'agente. Per esempio, i file creati e committati nello stesso comando Bash non li vede il controllo del commit, che guarda il working tree prima che il comando giri: l'avviso arriva dopo il commit. Dopo il passaggio a L1 redirect e heredoc sono negati, ma la scrittura di un file da un interprete (per esempio `python3 -c "open(...)"`) non è vista dai guardrail locali: la vede solo il gate su GitHub.

## Gli eval

### Gli eval girano in una sandbox senza rete, su casi costruiti

Gli eval di comportamento ([eval e CI](eval-e-ci.md)) usano una sandbox di `claude plugin eval`: senza rete, con `gh` finto, su casi offline. Misurano se l'agente rispetta gli obblighi nei casi scelti. Non provano il gate su GitHub vero, che si prova su repo di prova. La sandbox protegge anche `.git/config` del workspace: tollgate non lo riscrive se il valore c'è già, ma un caso che lo cambiasse davvero non potrebbe girare lì.

### Gli eval misurano un modello, in tre corse per caso

Un solo modello e tre corse per caso, con grader deterministici. Un caso può restare sotto soglia per la varianza del modello: allora lo si dichiara, senza ritoccare il prompt per farlo passare. Il confronto con e senza plugin si calcola solo per i casi della specifica.

### Due casi extra misurano meno del previsto

Il caso `e2` (`/tollgate:reopen`) resta una prova a secco e `e4-chiusura-l2` si ferma a `task done 2` e `finish check`, senza PR né atto `finish`. Gli atti digitati nel prompt valgono solo in una sessione legata a un lavoro, e una corsa di `claude plugin eval` parte con la sessione non legata.
