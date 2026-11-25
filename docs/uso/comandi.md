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

La sicurezza fin dal progetto vale in ogni lavoro con agenti (L1 e L2), anche quando nessun profilo di sicurezza è attivo: in L2 gli avversari di spec e piano chiedono chi può usare ciò che si costruisce, quali dati e segreti tocca e cosa succede con un input ostile, e ogni implementatore chiude il report con la riga `Sicurezza:` (cosa ha considerato, oppure che il task non tocca input esterni, accessi, dati o segreti). In L0 implementa la sessione, senza agenti, e la riga non c'è.

In modalità `detect` mostra a ogni avvio "modalità rilevazione: il merge non è impedito" e le issue aperte "tollgate: merge non verificato".

Se `tollgate.toml` dichiara `[models] files`, all'avvio di un lavoro nuovo `start` controlla anche i modelli AI scritti in quei file, e mostra righe `avviso: modelli: …` quando ne trova uno più nuovo o in ritiro. Sono solo avvisi: non cambiano l'esito di `start`. Dettagli in [il controllo dei modelli](#il-controllo-dei-modelli).

### `/tollgate:spec-audit`

Audit di spec e piano nei lavori L2: giri avversariali, audit a lenti sulla spec e avversario del piano, finché tollgate chiede la tua approvazione. Nessun argomento. Il coordinatore non scrive codice: lancia gli agenti, legge i report, corregge spec e piano. L'audit a lenti ha un costo: `audit prepare` chiede conferma prima di partire.

Se un giro supera un tetto, o rifiuti il costo, il lavoro si ferma con un blocco e la strada è `/tollgate:resolve`.

### `/tollgate:execute`

Esegue il piano task per task con gli agenti `tollgate:implementer` e `tollgate:task-reviewer`, fino a quando tutti i task sono chiusi. Nessun argomento. È rientrante: dopo un `/clear` riparte dalla riga "prossimo passo" del checkpoint. Un solo implementatore scrive per volta, il coordinatore non scrive codice e ogni task passa da una revisione prima di chiudersi. Se il task tocca i percorsi di un profilo con agenti propri, i tipi sono quelli del profilo: per l'area `ai` (codice che usa modelli AI) sono `tollgate:implementer-ai` e `tollgate:reviewer-ai`, copie dei generici che precaricano anche le regole `rules-ai`; per l'area `infra` (configurazione e deploy su Vercel, Cloudflare e Docker) sono `tollgate:implementer-infra` e `tollgate:reviewer-infra`, con le regole `rules-infra`; per l'area `backend` (server, API e Worker di Cloudflare) sono `tollgate:implementer-backend` e `tollgate:reviewer-backend`, con le regole `rules-backend`; per l'area `frontend` (componenti, pagine, stili e accessibilità) sono `tollgate:implementer-frontend` e `tollgate:reviewer-frontend`, con le regole `rules-frontend`; per l'area `database` (migrazioni, schema, policy RLS, funzioni ed edge function di Supabase) sono `tollgate:implementer-database` e `tollgate:reviewer-database`, con le regole `rules-database`, e l'implementatore non lancia `supabase`, `psql`, `docker`, `prisma`, `drizzle-kit` né un lanciatore di pacchetti: le prove del database passano da `verify`, che esegue il gate del progetto e i comandi che metti nel `gate` del profilo (quelli di `dod` girano solo a fine lavoro, con `finish check`: un comando che serve anche durante il task va messo anche nel `gate`); per l'area `security` (login, controlli d'accesso, token, password, cookie di sessione, middleware e proxy, segreti) sono `tollgate:implementer-security` e `tollgate:reviewer-security`, con le regole `rules-security`, e l'implementatore non usa credenziali vere, non agisce su un servizio in linea e non lancia `node`, `npm`, `npx`, `pnpm`, `yarn`, `bun`, `bunx`, `deno`, `supabase`, `psql`, `docker`, `wrangler`, `vercel` né `openssl`: le prove passano da `verify`, che esegue il gate del progetto e i comandi che metti nel `gate` del profilo (quelli di `dod` girano solo a fine lavoro, con `finish check`: un comando che serve anche durante il task va messo anche nel `gate`); il revisore di un'area può anche aprire gli indirizzi ufficiali citati nel report, ed è di sola lettura come il generico. Un task che tocca due aree usa gli agenti generici. Ogni implementatore, generico o di area, segue la sezione «Sicurezza fin dal progetto» (input validato al confine, nessun segreto nel codice né nei log, accesso chiuso per difetto con il test del caso negato, valori predefiniti che rifiutano, permessi minimi) e chiude il campo `done` del report con la riga `Sicurezza: <cosa ha considerato>` oppure `Sicurezza: il task non tocca input esterni, accessi, dati o segreti`; il revisore del task controlla quella riga e il diff contro di essa. A fine lavoro ti dice di scrivere `/tollgate:finish`.

### `/tollgate:finish`

Chiude il lavoro. Nessun argomento. Tre passi:

1. `finish check`: la copia locale del gate. Stampa la Definition of Done voce per voce, più le voci di `attenzione` ("da leggere" e informative). Il worktree deve essere pulito.
2. La revisione finale (L1 e L2), a cicli, con revisori e verificatori dei rilievi. In L2, se il lavoro tocca un profilo con uno specialista (oggi `database`, con `tollgate:final-database`, e `security`, con `tollgate:final-security`), si aggiunge un revisore di sola lettura che guarda il diff con le regole dell'area e la lista di controllo; costa un agente in più per ciclo. `tollgate:final-security` guarda prima l'intero diff per rischio e raggio d'azione: quali confini di fiducia attraversa il cambio, chi può raggiungere il codice cambiato, quali dati e permessi tocca. Se il lavoro tocca tutti e due i profili partono tutti e due gli specialisti, ognuno con la sua lista. Il tetto è di 4 cicli contati, 8 in assoluto con la tua approvazione.
3. `finish open-pr`: spinge lo SHA e apre o aggiorna la PR. Il modello non lancia mai `git push` né `gh pr create` da Bash.

Il merge lo fai tu su GitHub.

### `/tollgate:sync`

Rimette il ramo del lavoro sul ramo predefinito e aggiorna la PR. Solo l'utente. Lo lanci dal worktree, in fase `execution` o `pr_open`. Fa `fetch`, integra i commit remoti, rebase, rilancia `finish check` e aggiorna la PR se il contenuto non è cambiato. Se il rebase va in conflitto il lavoro si ferma: risolvi a mano e scrivi `/tollgate:approve rebase`, oppure `/tollgate:abandon`.

## Approvazioni e blocchi

### `/tollgate:approve`

Approvazioni dell'utente.

- Argomenti: `level <L> <motivo> | size <piccolo|medio|grande> <motivo> | spec <fette> | plan | finding <id> <gravità|dismiss> <motivo> | rounds <n> | unverified-review | rebase | waiver <id> | effect <id>`
- Solo l'utente.

Cosa fa ciascuno:

- `level`: fissa un tetto al livello, con motivo. Il gate lo riporta tra le voci da leggere.
- `size <piccolo|medio|grande> <motivo>`: fissa la taglia del lavoro, anche verso il basso, con motivo. Non autorizza le fette.
- `spec` (L2, fase `spec_audit`): approva la spec, scrive il file di approvazione da committare e passa a `plan`. `<fette>` è il numero di fette della spec; con più fette il lavoro diventa grande; per le fette dalla seconda in poi propone un'issue ciascuna.
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

Prima installazione con `--propose`, aggiornamento con `--update` (propone solo i file che differiscono dal ramo predefinito). Propone anche i profili verticali approvati che hanno file nel repo: aggiunge blocchi `[profiles.<area>]` in coda al `tollgate.toml` proposto, senza riscrivere il tuo testo, e li descrive nella sezione «Profili proposti» del `README.md`. Un profilo che hai già dichiarato non lo tocca: ti scrive a terminale le righe da cambiare a mano (regole nuove, percorsi non coperti, agenti ora presenti). I percorsi di un profilo possono avere quattro forme: una cartella a qualunque profondità, una cartella alla radice del repo, il nome di un file, un'estensione; per le prime due `init` scrive la cartella trovata nel repo, per la terza il percorso esatto di ogni file (un `Dockerfile` o un `vercel.json` nuovo, anche nella stessa cartella, si aggiunge poi con le righe di `init --update`), per l'ultima il pattern stesso (`**/*.tsx`), una volta per estensione. I pattern per estensione li dichiarano i profili `frontend` e `database`: a runtime perdono contro ogni cartella e ogni file di un altro profilo. I documenti (`.md`, `.mdx`, `.markdown`, `.rst`, `.txt`, `.adoc`) non accendono un profilo per la sola cartella in cui stanno. I file in `.github/workflows/` e `.github/actions/` non accendono nessun profilo. Un profilo può anche escludere dei prefissi dalla proposta (`exclude` in `[detect]` del suo frammento): i file sotto quelle cartelle non lo accendono, né per percorso né per contenuto. Lo fa il profilo `backend` con `supabase/`: le edge function di Supabase non lo accendono. Lo fa anche `frontend`, con le cartelle alla radice dei server e di `infra` e con `supabase/`. Lo fa anche `security`, con `supabase/`: le edge function e le policy sotto `supabase/` alla radice restano a `database`. Un profilo può poi chiedere di accendere i suoi percorsi anche per i file che il rilevamento per contenuto assegna a un altro profilo (`keep_paths = true` in `[detect]`): lo fa solo `security`, così una rotta di login dentro una cartella `auth/` riconosciuta da `backend` accende anche `security`; a runtime il file va comunque al profilo con il percorso più specifico. I passi sono in [installazione](installazione.md) e [emergenze e aggiornamenti](emergenze-e-aggiornamenti.md); come sceglie la modalità è in [modalità](modalita.md).

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

### `/tollgate:rules-frontend`

Le regole per il codice d'interfaccia (componenti, pagine, stili) e la sua accessibilità: la documentazione della versione di ogni libreria, cercare un componente simile prima di crearne uno, gli stati di caricamento, errore e vuoto, i token di design al posto dei colori scritti a mano, controlli nativi, nomi accessibili, etichette dei campi, focus visibile, messaggi di stato annunciati e un test dei componenti dove il repo li ha già. Le caricano gli agenti dell'area `frontend`, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-11): `init` propone il profilo `frontend` dove trova codice d'interfaccia.

### `/tollgate:rules-database`

Le regole per il database: leggere lo schema e le migrazioni già presenti prima di scriverne una, la documentazione della versione di PostgreSQL o di Supabase, una migrazione nuova invece di modificare le vecchie, come si annulla, le colonne rinominate o tolte in due tempi, i blocchi che un cambio causa su una tabella con dati. Per PostgreSQL e Supabase anche la RLS sulle tabelle nuove, le policy per ruolo e per operazione, `auth.uid()` dentro `(select …)`, gli indici delle policy e delle chiavi esterne, le funzioni `security definer` con il `search_path` fissato, le viste con `security_invoker`, i segreti delle edge function, `verify_jwt = false` motivato, e nessuna scrittura sul progetto collegato. Le regole sul database valgono per ogni base dati; quelle su RLS, policy e funzioni valgono solo per PostgreSQL e Supabase. Le caricano gli agenti dell'area `database`, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-17): `init` propone il profilo `database` dove trova codice del database.

### `/tollgate:rules-security`

Le regole per la sicurezza: dire nel report chi può arrivare al codice cambiato, cosa può fare e quale controllo lo ferma; la documentazione della versione di una libreria di sicurezza usata per la prima volta; il test del caso di accesso negato per ogni controllo d'accesso nuovo o cambiato; l'autorizzazione controllata sul server per ogni funzione che tocca dati di un utente, dentro di essa o in una guardia della sua rotta, mai solo nel browser, con il proprietario confrontato (una Server Function di Next.js la controlla al suo interno: `proxy.ts` o `middleware.ts` da soli non bastano), tranne che nel login, nella registrazione, nella richiesta di reset, nella callback di un login e nelle funzioni che leggono solo dati pubblici e lo dichiarano nel diff; valori predefiniti che rifiutano quando manca un segreto o un'impostazione di sicurezza: nessun ripiego per un segreto, per un'impostazione solo il valore che nega, e nei test un valore finto evidente ammesso; password solo con un hash lento con un sale per ciascuna, quando il codice le salva o le controlla; token verificati senza spegnere firma e scadenza, con l'elenco degli algoritmi ammessi dove la libreria lo chiede, e una scadenza per i token creati; il confronto dei segreti, dei token, delle firme e degli hash dei segreti a tempo costante, fuori dai test; cookie di sessione con `HttpOnly`, `Secure` e `SameSite` scritti nel codice quando il codice li costruisce da sé, opzioni non indebolite quando li scrive una libreria, `SameSite=None` solo con `Secure` e un motivo scritto che dice quale altro sito manda il cookie, e nessun token dove il JavaScript della pagina può leggerlo; nessun segreto nel diff o nei test, nessun segreto, token o hash di password nei log o nei messaggi d'errore, e nelle risposte nessuna password, nessun hash di password e nessun segreto del server, e mai un token di reset (il token consegnato al suo titolare, come la risposta di un login, è ammesso); risposte di login, reset e recupero della password che non dicono quali account esistono; input validato al confine, query e comandi con parametri; reindirizzamenti e richieste del server verso un indirizzo del chiamante solo dopo un controllo (un percorso interno, non `//host`, o un host di un elenco); CORS con le credenziali solo per origini di un elenco, mai `*`; il limite dei tentativi falliti su login, reset e recupero detto nel report; il raggio d'azione del cambio nel report; nessuna azione su credenziali vere o servizi in linea. Le regole su segreti e input ripetono quelle di `backend`, `infra` e `database`, perché un file che va a `security` non riceve le loro. Una edge function o una policy sotto `supabase/` alla radice ha le regole di `database`, non queste. Le caricano gli agenti dell'area `security`, quindi non serve lanciarla a mano. Le regole sono approvate dall'utente (2026-11-23): `init` propone il profilo `security` dove trova una cartella `auth/`, `security/` o `rls/`, un middleware o un proxy, o una libreria di password o di token.

## Modelli degli agenti

Ogni agente di tollgate fissa il suo modello nella riga `model:` della definizione. La scelta è dell'utente (22/11/2026): chi cerca i difetti usa Fable, chi scrive o corregge usa opus, mai sonnet né haiku.

- `fable`: il revisore del task (`tollgate:task-reviewer` e i revisori di area `tollgate:reviewer-<area>`), la revisione finale (`tollgate:final-reviewer` e gli specialisti `tollgate:final-<area>`), `tollgate:finding-verifier` e gli agenti dell'audit (`tollgate:spec-auditor`, `tollgate:spec-adversary`, `tollgate:plan-adversary`).
- `opus`: l'implementatore (`tollgate:implementer` e gli implementatori di area `tollgate:implementer-<area>`), anche il nuovo implementatore che parte dal giro 4 di correzione.

Sono alias, non ID completi: seguono la versione più recente della famiglia senza un cambio del plugin.

Per un progetto puoi dare a un tipo di agente un altro modello con `[review] models` in `tollgate.toml`:

```toml
[review]
models = {"tollgate:implementer" = "fable"}
```

Il valore va scritto come alias (per esempio `fable` o `opus`): il coordinatore lo passa al parametro `model` dello strumento `Agent`, che non accetta un ID completo né `inherit`, e tollgate non lo controlla. Vale per l'implementatore (il riepilogo di `task start` dice `model: <valore>`), per la revisione finale e per l'audit (le righe di lancio dicono `model: <valore>`). Dal giro 4 il riepilogo di `task start --fix` dice sempre un modello: il valore di `[review] models` per quell'implementatore, o `opus` se il progetto non lo fissa. Il revisore del task usa il modello della sua definizione.

Se `availableModels` esclude il modello chiesto, Claude Code fa girare l'agente sulla versione più recente permessa della stessa famiglia, dove il fornitore lo consente, poi sul modello di `CLAUDE_CODE_SUBAGENT_MODEL`, poi su quello della sessione, con un avviso nelle sessioni interattive; con una catena di modelli di riserva configurata passa al primo della catena. Con `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` Claude Code ignora sia la riga `model:` degli agenti sia il `model` della chiamata, e la scelta qui sopra non vale.

## La CLI

La CLI è `bin/tollgate` e si lancia con `python3` davanti al percorso, tra virgolette se contiene spazi. Quasi tutti i sottocomandi li chiamano le skill. Quelli che puoi usare direttamente:

- `status [--json]`: lo stesso di `/tollgate:status`. `--checkpoint [--note TESTO]` scrive il checkpoint nel worktree del lavoro.
- `stats [--since AAAA-MM-GG] [--work N]`: statistiche dagli eventi, in JSON (tempo per fase, veti per regola, blocchi, deroghe, token). Serve a vedere se tollgate rallenta più di quanto protegge.
- `events --after-seq N`: esporta gli eventi in JSONL.
- `snapshot`: una fotografia JSON dei lavori aperti (taglia, fase, task, a chi tocca, cosa aspetta l'utente, costo), in sola lettura, senza testo libero. Come usarla: [leggere lo stato da un gestionale](gestionale.md).
- `init --propose` e `init --update`: come sopra.
- `models check [--refresh]`: il controllo dei modelli sul repo corrente, senza aprire un lavoro. Vedi [il controllo dei modelli](#il-controllo-dei-modelli).
- `ruling add [--task K] [--by agent|user]`: registra nello stato locale una decisione presa al posto dell'utente. Il testo va da stdin, in un heredoc, con tre righe: `cosa:`, `perché:`, `costo:` (al più 1000 caratteri per campo; le etichette valgono anche in maiuscolo). Lo usano gli agenti, e il coordinatore con `--by user` per una scelta data dall'utente in chat: un subagente non può usare `--by user`. Niente va su GitHub.
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
