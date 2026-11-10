# Comandi

Ogni comando è una skill del plugin e si scrive nel prompt di Claude Code come `/tollgate:<nome>`. Le skill marcate "solo l'utente" non le lancia mai il modello: un hook registra l'atto quando le digiti tu, e senza quell'atto il comando che la skill chiama rifiuta. Gli atti decadono se il lavoro cambia (un commit dopo `/tollgate:finish`, per esempio) o dopo qualche minuto.

Dopo ogni `/tollgate:*` (tranne `off` e `on`) compare la riga `tollgate: programma python3 "<percorso>/bin/tollgate"`: è il comando della CLI, che le skill usano e che puoi usare anche tu dal terminale (vedi [la CLI](#la-cli)).

## Il flusso di un lavoro

### `/tollgate:start`

Avvia o riprende il lavoro su un'issue. Lo lanci dal checkout principale.

- Argomenti: `#N [L1|L2] [--spec <percorso>]`
- Chi lo lancia: tu o il modello.

Crea il ramo `tg/<N>-<slug>` e il worktree in `.claude/worktrees/`, sceglie il livello e porta la sessione dentro il worktree. Il livello è il massimo tra quello calcolato dal diff, quello stimato da etichette e autore dell'issue e quello che chiedi tu. L0 è per le modifiche piccole (fino a 2 file e 50 righe), L1 è il caso normale, L2 è per percorsi sensibili, etichette sensibili, autori esterni al repo o una tua scelta, e aggiunge spec e audit prima del piano.

`--spec` vale solo per un lavoro nuovo: indica la spec già approvata di cui questa issue è una fetta successiva. Se la spec è cambiata dopo l'approvazione, `start` esce con un avviso da confermare. Se `start` elenca avvisi (issue chiusa, stati del ramo predefinito non verdi, altra sessione viva), si rilancia con `--confirm` solo dopo il tuo sì. Un ramo o una PR già esistenti per l'issue rifiutano e rimandano a `/tollgate:adopt`.

In modalità `detect` mostra a ogni avvio "modalità rilevazione: il merge non è impedito" e le issue aperte "tollgate: merge non verificato".

Se `tollgate.toml` dichiara `[models] files`, all'avvio di un lavoro nuovo `start` controlla anche i modelli AI scritti in quei file, e mostra righe `avviso: modelli: …` quando ne trova uno più nuovo o in ritiro. Sono solo avvisi: non cambiano l'esito di `start`. Dettagli in [il controllo dei modelli](#il-controllo-dei-modelli).

### `/tollgate:spec-audit`

Audit di spec e piano nei lavori L2: giri avversariali, audit a lenti sulla spec e avversario del piano, finché tollgate chiede la tua approvazione. Nessun argomento. Il coordinatore non scrive codice: lancia gli agenti, legge i report, corregge spec e piano. L'audit a lenti ha un costo: `audit prepare` chiede conferma prima di partire.

Se un giro supera un tetto, o rifiuti il costo, il lavoro si ferma con un blocco e la strada è `/tollgate:resolve`.

### `/tollgate:execute`

Esegue il piano task per task con gli agenti `tollgate:implementer` e `tollgate:task-reviewer`, fino a quando tutti i task sono chiusi. Nessun argomento. È rientrante: dopo un `/clear` riparte dalla riga "prossimo passo" del checkpoint. Un solo implementatore scrive per volta, il coordinatore non scrive codice e ogni task passa da una revisione prima di chiudersi. Se il task tocca i percorsi di un profilo con agenti propri, i tipi sono quelli del profilo: per l'area `ai` (codice che usa modelli AI) sono `tollgate:implementer-ai` e `tollgate:reviewer-ai`, copie dei generici che precaricano anche le regole `rules-ai`; per l'area `infra` (configurazione e deploy su Vercel, Cloudflare e Docker) sono `tollgate:implementer-infra` e `tollgate:reviewer-infra`, con le regole `rules-infra`; per l'area `backend` (server, API e Worker di Cloudflare) sono `tollgate:implementer-backend` e `tollgate:reviewer-backend`, con le regole `rules-backend`; il revisore di un'area può anche aprire gli indirizzi ufficiali citati nel report, ed è di sola lettura come il generico. Un task che tocca due aree usa gli agenti generici. A fine lavoro ti dice di scrivere `/tollgate:finish`.

### `/tollgate:finish`

Chiude il lavoro. Nessun argomento. Tre passi:

1. `finish check`: la copia locale del gate. Stampa la Definition of Done voce per voce, più le voci di `attenzione` ("da leggere" e informative). Il worktree deve essere pulito.
2. La revisione finale (L1 e L2), a cicli, con revisori e verificatori dei rilievi. Il tetto è di 4 cicli contati, 8 in assoluto con la tua approvazione.
3. `finish open-pr`: spinge lo SHA e apre o aggiorna la PR. Il modello non lancia mai `git push` né `gh pr create` da Bash.

Il merge lo fai tu su GitHub.

### `/tollgate:sync`

Rimette il ramo del lavoro sul ramo predefinito e aggiorna la PR. Solo l'utente. Lo lanci dal worktree, in fase `execution` o `pr_open`. Fa `fetch`, integra i commit remoti, rebase, rilancia `finish check` e aggiorna la PR se il contenuto non è cambiato. Se il rebase va in conflitto il lavoro si ferma: risolvi a mano e scrivi `/tollgate:approve rebase`, oppure `/tollgate:abandon`.

## Approvazioni e blocchi

### `/tollgate:approve`

Approvazioni dell'utente.

- Argomenti: `level <L> <motivo> | spec <fette> | plan | finding <id> <gravità|dismiss> <motivo> | rounds <n> | unverified-review | rebase | waiver <id> | effect <id>`
- Solo l'utente.

Cosa fa ciascuno:

- `level`: fissa un tetto al livello, con motivo. Il gate lo riporta tra le voci da leggere.
- `spec` (L2, fase `spec_audit`): approva la spec, scrive il file di approvazione da committare e passa a `plan`. `<fette>` è il numero di fette della spec; per le fette dalla seconda in poi propone un'issue ciascuna.
- `plan` (L2, fase `approval`): approva il piano, registra scope e task e passa a `execution`.
- `finding`: declassa un rilievo della revisione finale (`blocker|major|moderate|minor`) o lo scarta (`dismiss`). Il motivo è obbligatorio.
- `rounds <n>`: concede giri di correzione a un task fermo, o cicli di revisione finale oltre i quattro.
- `unverified-review`: dopo il tetto dei cicli, prosegue con la revisione dichiarata non verificata. La PR lo riporta.
- `rebase`: dopo un conflitto di `/tollgate:sync` risolto a mano, riallinea la base e autorizza il push forzato del prossimo `finish open-pr`.
- `waiver <id>` e `effect <id>`: l'approvazione di una deroga o di un effetto esterno (un deploy, per esempio). Vale già dal momento in cui la digiti; la skill non lancia altro.

### `/tollgate:resolve`

Chiude un blocco aperto del lavoro (`needs_you`, conflitto tra test e specifica, budget) oppure interrompe l'implementatore in corso.

- Argomenti: `<id del blocco> <nota> | writer`
- Solo l'utente.

Dice la fase a cui il lavoro torna e i task tornati in attesa. Sui blocchi dei tetti dell'audit sospende quell'audit, e il lavoro prosegue con `/tollgate:spec-audit`. Sul tetto dei cicli di revisione concede un ciclo; per altri serve `approve rounds` o `approve unverified-review`.

### `/tollgate:reopen`

Riapre la spec o il piano dopo l'approvazione, per correggerli.

- Argomenti: `spec <motivo> | plan <motivo>`
- Solo l'utente.

Il motivo è obbligatorio. I file di approvazione restano come storico e non valgono più: dopo la correzione serve una nuova approvazione (in L1 il piano corretto si registra da solo con la modifica).

## Ripresa e pulizia

### `/tollgate:adopt`

Ricostruisce un lavoro da un ramo `tg/<N>-*` esistente: livello, fase (dalle prove presenti nel ramo), base e tetto.

- Argomenti: `#N`
- Solo l'utente.

Si lancia dal checkout principale. Rifiuta se la PR è già unita, se il ramo è nel checkout principale o se il repo non è attivo.

### `/tollgate:abandon`

Chiude un lavoro senza unirlo; ramo, worktree e PR restano.

- Argomenti: `#N`
- Solo l'utente.

Il lavoro passa in fase `closed`. La PR la chiudi tu su GitHub se vuoi, e ramo e worktree li toglie `/tollgate:cleanup`.

### `/tollgate:cleanup`

Toglie rami e worktree dei lavori chiusi.

- Argomenti: `[--orphans]`
- Solo l'utente.

La prima chiamata elenca soltanto. Con il tuo sì la skill rilancia con `--confirm` entro 10 minuti dall'atto. Il worktree non si toglie mai se ha modifiche non committate, e il ramo solo se punta ancora allo SHA elencato. Con `--orphans` include i rami `tg/<N>-*` senza lavoro nel DB.

## Gate e installazione

### `/tollgate:init`

Prepara l'installazione del gate su GitHub: misura la modalità (`protected` o `detect`) e scrive una proposta con i file da copiare e i tuoi passi. Non scrive mai nel repo.

- Argomenti: `[--propose|--update] [--merges-per-month N] [--service NOME=IMMAGINE[,PORTA]]`
- Chi lo lancia: tu o il modello.

Prima installazione con `--propose`, aggiornamento con `--update` (propone solo i file che differiscono dal ramo predefinito). Propone anche i profili verticali approvati che hanno file nel repo: aggiunge blocchi `[profiles.<area>]` in coda al `tollgate.toml` proposto, senza riscrivere il tuo testo, e li descrive nella sezione «Profili proposti» del `README.md`. Un profilo che hai già dichiarato non lo tocca: ti scrive a terminale le righe da cambiare a mano (regole nuove, percorsi non coperti, agenti ora presenti). I percorsi di un profilo possono avere tre forme: una cartella a qualunque profondità, una cartella alla radice del repo, il nome di un file; per le prime due `init` scrive la cartella trovata nel repo, per la terza il percorso esatto di ogni file (un `Dockerfile` o un `vercel.json` nuovo, anche nella stessa cartella, si aggiunge poi con le righe di `init --update`). I documenti (`.md`, `.mdx`, `.markdown`, `.rst`, `.txt`, `.adoc`) non accendono un profilo per la sola cartella in cui stanno. I file in `.github/workflows/` e `.github/actions/` non accendono nessun profilo. Un profilo può anche escludere dei prefissi dalla proposta (`exclude` in `[detect]` del suo frammento): i file sotto quelle cartelle non lo accendono, né per percorso né per contenuto. Lo fa il profilo `backend` con `supabase/`: le edge function di Supabase non lo accendono. I passi sono in [installazione](installazione.md) e [emergenze e aggiornamenti](emergenze-e-aggiornamenti.md); come sceglie la modalità è in [modalità](modalita.md).

### `/tollgate:setup`

Propone la modifica di `statusLine.command` per avvolgere la statusline con `statusline/ctx`, che alimenta la guardia del contesto. Solo l'utente. Nessun argomento. Non scrive mai `settings.json`: la riga la incolli tu ([installazione](installazione.md)).

## Controllo

### `/tollgate:status`

Mostra lo stato dei lavori attivi (fase, livello, task, blocchi, tetti che hanno fermato il lavoro) in sola lettura, e le statistiche di un lavoro su richiesta. Nessun argomento. Non legge GitHub e non cambia niente. Stampa anche una riga col percorso di [limiti.md](limiti.md) e, se un lavoro attivo è in `detect`, la frase "in modalità detect il merge non è impedito, solo rilevato".

### `/tollgate:off`

Spegne tollgate su questa macchina, per sempre o per un numero di ore.

- Argomenti: `[ore]`
- Solo l'utente.

Con tollgate spento non gira nessun guardrail locale, e `start` e gli atti non funzionano. Il gate su GitHub resta attivo.

### `/tollgate:on`

Riaccende tollgate su questa macchina. Solo l'utente. Nessun argomento.

### `/tollgate:rules-base`

Le regole di base del passo «informati prima»: leggere i file e la documentazione ufficiale prima di scrivere, citare dove si è cercato, provare ciò che si dichiara. Le caricano gli agenti di tollgate che scrivono o rivedono codice, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-01): il blocco del passo è acceso.

### `/tollgate:rules-ai`

Le regole per il codice che usa modelli AI (Claude, Gemini, OpenAI, OpenRouter, Agno): il nome del modello in un solo punto, con l'indirizzo della pagina ufficiale e la data della verifica; l'ultimo modello stabile della famiglia; le note di migrazione lette prima di cambiare modello; un errore chiaro se un modello non è più disponibile. Le caricano gli agenti dell'area `ai`, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-02): `init` propone il profilo `ai` dove trova codice che usa modelli AI.

### `/tollgate:rules-infra`

Le regole per la configurazione e il deploy su Vercel, Cloudflare (Wrangler) e Docker: leggere i file di deploy già presenti prima di parlare di deploy, citare la pagina ufficiale di ogni comando e di ogni proprietà di configurazione, nessun segreto nei file versionati, un solo file di configurazione per progetto Vercel, e nessuna pubblicazione fatta dal task. Le caricano gli agenti dell'area `infra`, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-07): `init` propone il profilo `infra` dove trova file di configurazione o di deploy.

### `/tollgate:rules-backend`

Le regole per il codice dei server e delle API, anche i Worker di Cloudflare: leggere i contratti già presenti prima di scrivere un endpoint, validare corpo e parametri, errori con la stessa forma in tutto il progetto, nessun segreto nel codice né nei log, query con parametri, un test per ogni endpoint e prove locali sui dati dei servizi. Le caricano gli agenti dell'area `backend`, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-10): `init` propone il profilo `backend` dove trova codice di server o di API.

## La CLI

La CLI è `bin/tollgate` e si lancia con `python3` davanti al percorso, tra virgolette se contiene spazi. Quasi tutti i sottocomandi li chiamano le skill. Quelli che puoi usare direttamente:

- `status [--json]`: lo stesso di `/tollgate:status`. `--checkpoint [--note TESTO]` scrive il checkpoint nel worktree del lavoro.
- `stats [--since AAAA-MM-GG] [--work N]`: statistiche dagli eventi, in JSON (tempo per fase, veti per regola, blocchi, deroghe, token). Serve a vedere se tollgate rallenta più di quanto protegge.
- `events --after-seq N`: esporta gli eventi in JSONL.
- `init --propose` e `init --update`: come sopra.
- `models check [--refresh]`: il controllo dei modelli sul repo corrente, senza aprire un lavoro. Vedi [il controllo dei modelli](#il-controllo-dei-modelli).
- `db restore`: ripristina l'ultima copia integra del DB, solo da un terminale interattivo e solo se il DB è guasto. Nessuna skill lo chiama.
- `gate -h`: i comandi del gate che girano nei workflow di GitHub Actions (`run`, `evaluate`, `guard`, `base-ids`, `base-publish`, `sentinel`). Senza stato locale. Il flag `--publish` vale solo dentro GitHub Actions.
- `--version`.

Il resto (`start`, `task`, `act`, `finish`, `review`, `audit`, `sync`, `adopt`, `abandon`, `cleanup`, `verify`, `waiver`, `block`) è del coordinatore o dell'agente. Un subagente non lancia quelli del coordinatore: gli hook glielo negano.

### Il controllo dei modelli

Un progetto che usa modelli AI dichiara in `tollgate.toml` i file dove scrive i loro nomi:

```toml
[models]
files = ["src/ai/models.py"]
```

I percorsi sono quelli esatti dei file, relativi alla radice del repo, al più 20, senza `*` né `..`. Uno scritto male viene tolto con un avviso. Un tipo sbagliato in `[models]` (per esempio un testo al posto dell'elenco) è un errore di configurazione, come per ogni altra sezione di `tollgate.toml`. `[components] models_check = false` spegne il controllo.

Il controllo legge quei file dal ramo predefinito di `origin`, non dalla tua cartella di lavoro: una modifica non ancora spinta non conta. Prende i nomi scritti tra virgolette (`"..."`, `'...'` o con l'apice rovesciato) e li confronta con l'elenco ufficiale che ogni fornitore pubblica. I nomi senza virgolette, come in un file `.env` o in uno YAML non quotato, non si vedono. Per interrogare un fornitore serve la sua chiave nell'ambiente: [come darla](installazione.md#le-chiavi-per-il-controllo-dei-modelli). Senza chiave quel fornitore si salta, e la riga lo dice se nei file c'è un nome con la forma dei suoi modelli.

Cosa controlla, fornitore per fornitore:

- Anthropic: un modello più nuovo della stessa famiglia, un modello deprecato (con la data di ritiro, se c'è), un nome che non è nell'elenco.
- Gemini: un modello più nuovo della stessa famiglia. Il ritiro non lo controlla: l'elenco non lo dice.
- OpenAI: il ritiro. Il modello più nuovo non lo controlla.
- OpenRouter: il ritiro. Il modello più nuovo non lo controlla, e la riga rimanda alla pagina del fornitore originale.

Quello che non si può controllare compare come riga «non controllato», una volta per fornitore. Il controllo non usa modelli AI e non spende token: fa una richiesta di elenco per fornitore, con un tempo massimo di 20 secondi in tutto, più al più una risoluzione DNS e una lettura di 5 secondi. Se la rete non risponde, o la risposta non ha la forma attesa, usa la cache se ce n'è una (anche scaduta, e lo dice con la sua data); altrimenti avvisa e va avanti. Se nei file non c'è nessun nome riconosciuto, anche questo compare come riga. Dietro un proxy aziendale non funziona: i proxy dell'ambiente non si usano.

L'elenco di ogni fornitore resta in una cache di un giorno nella cartella di stato di tollgate: un modello uscito oggi può arrivare con un giorno di ritardo. `models check --refresh` la ignora e rilegge gli elenchi. All'avvio di un lavoro nuovo la riga «elenco dalla cache» non compare; con `models check` sì.

`models check` lo lanci da dentro il repo, con il programma del plugin e non con la copia del gate in `.github/tollgate/`: quella ha il codice (si copia tutto `bin/`) ma non `templates/models.toml`, e lanciato da lì il comando dà «controllo non riuscito (ProvidersError)». Un subagente può lanciarlo, anche con `--refresh`: una richiesta per fornitore e nessun token. Stampa le stesse righe di `start`, oppure «modelli: nessun avviso» (che non compare se ci sono solo avvisi di configurazione, cioè voci tolte da `[models] files`, e nessuna riga del controllo). Se il controllo è spento o `[models] files` è vuoto lo dice. Esce con 0; con 1 solo se la cartella non è in un repo, manca `origin` o `tollgate.toml` non è leggibile.

Le righe nascono da file del progetto e da elenchi esterni: per Claude sono dati, non istruzioni, e non cambia modello da solo.
