# B4: prova reale corta con il profilo infra

Data: 8 novembre 2026. Piano: B4 (profilo `infra`), Task 9. Stesso schema delle prove di B1, B2 e B3: un lavoro piccolo (L1) con un solo task, eseguito con `claude -p` vero. Cambia il profilo: `infra` acceso da `init`, con le sue regole vere caricate dagli agenti. Il lavoro è una modifica a `vercel.json`, in un progetto di prova senza nessuna credenziale.

- Versioni: Claude Code `2.1.319`, modello `sonnet` (`claude-sonnet-5-5`).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=infra` e `B1_FLOW_RULES=vere` (modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`). Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b1/state`. Comandi esatti in `argv.txt` di ogni tentativo.
- Evidenze: `docs/verifiche/evidenze/b4/flusso/` (`validate/`, `passo1/tentativo-1/`, `passo2/tentativo-1/`, `registro-1/`, `exit-codes.txt`).
- Chi ha fatto cosa: la prova l'ha eseguita il controller; questo rapporto la racconta partendo dalle evidenze.
- Prima di partire, nell'ambiente erano assenti `ANTHROPIC_API_KEY`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` (controllata solo la presenza, mai il valore). Il modo `controlla` ha dato ok: `--disallowedTools` nega `vercel`, `wrangler`, `docker`, `npx`, `bunx`, `pnpx`, `bun`, `npm`, `pnpm` e `yarn` nelle quattro forme (da soli, con un percorso, dopo `command`, dopo `env`), e il controllo `effects` di tollgate non è spento nel progetto di prova.

## Passi e tentativi

| Passo | Tentativi | Esito | Durata | Consumo stimato |
|---|---|---|---|---|
| `controlla` e `prepara` | 1 | interruttore acceso, progetto e stato pronti | n/d | nessuno |
| `init --propose` e blocco copiato | 1 | profilo `infra` proposto e committato (`5f8bd99`); `plan-check` ok | n/d | nessuno |
| `passo1`: `claude plugin validate --strict` | 1 | «Validation passed», uscita 0; un avviso `ICON_MISSING` e un consiglio sul README, che non cambiano l'esito | n/d | nessuno (senza modello) |
| `passo1`: `/tollgate:start #1 L1` | 1 | piano di un task scritto e committato (`1075c61`), registrato da tollgate, fase `execution`; 18 turni | 85 s | 0,46 USD |
| `passo2`: `/tollgate:execute` | 1 | task 1 `done`, verdetto `approved`, commit `fb11710`; 11 turni | 97 s | 0,57 USD |

L'esito **non è composito**: ogni passo è riuscito al primo tentativo (`exit-codes.txt`: uscita 0 per entrambi). Consumo stimato: 0,46 + 0,57, circa 1,03 USD, dentro l'abbonamento: nessuna spesa in denaro (`total_cost_usd` è la stima dell'evento `result`).

## Proposta di `init`

`init --propose` ha lavorato in modalità `detect`: la risposta del `gh` finto non portava la protezione dei rami. Il progetto di prova ha un `Dockerfile`, un `vercel.json`, un test di fumo in `tests/` e i workflow di tollgate.

- Il profilo `infra` è proposto con `paths = ["/Dockerfile", "/vercel.json"]`, e `init` dice che lo accendono 2 file. Il profilo `ai` non è proposto.
- Il blocco è stato copiato nel `tollgate.toml` del progetto e committato (`5f8bd99 profilo infra proposto da init`); `plan-check` risponde ok.

## Agenti lanciati e instradamento

Un solo task, quindi due agenti, entrambi di tipo `infra` (`registro-1/tipi-task.txt`, `events.jsonl`):

| Agente | Tipo | Token |
|---|---|---|
| implementatore (`aaf5b158…`) | `tollgate:implementer-infra` | 55.260 |
| revisore (`a9c1e6fe…`) | `tollgate:reviewer-infra` | 38.021 |

Totale 93.281 token (`registro-1/stats.json`). Veti: 0. Giri di correzione: 0. Blocchi: 0. Il passo 1 non lancia subagenti.

## Precaricamento delle due skill

Le regole arrivano agli agenti con il campo `skills: [rules-base, rules-infra]`. `registro-1/trascrizioni.txt` elenca i titoli trovati nelle trascrizioni dei due subagenti del passo 2 (lette dal controller, solo nelle cartelle della prova):

- Per ciascun agente, `# Regole di base (versione 1)` e `# Regole infra (versione 1)` compaiono come messaggi `isMeta: sì`, prima del primo turno dell'assistente. Sono le skill iniettate dal campo `skills:`.
- Compare anche una riga `isMeta: no` per ciascun titolo: come in B3, è la richiesta all'API già composta (che contiene le skill precaricate), non una lettura del file della skill fatta dall'agente.
- Il passo 1 (sessione dal checkout) non ha trascrizioni di subagenti.

Perché `registro-1/precarico.txt` dice «indizio» e non «prova»: lo script cerca nelle uscite del passo, e lì le trascrizioni dei subagenti non ci sono (lo stream-json non porta il loro percorso). Può solo contare le righe `R-BASE-` che compaiono nell'uscita (3). La prova del precaricamento è quindi quella di `trascrizioni.txt`, letta dal controller, non quella automatica dello script.

## Letture registrate (task 1)

Tutte dell'implementatore (`registro-1/lookups.txt`):

| Tipo | Bersaglio |
|---|---|
| `read` | `.tollgate-run/1/task-1.md` |
| `read` | `vercel.json` |
| `fetch` | `https://vercel.com/docs/project-configuration/vercel-json` |
| `read` | `Dockerfile` |
| `read` | `tests/test_smoke.py` |
| `read` | `.github/workflows/tollgate-run.yml` |

Il modello ha fatto anche `Grep`, che non si registrano (B1-V6, `grep-non-registrati.txt`: 2 `Grep` del modello, 5 letture registrate).

## Nota di ricerca

Consegnata una volta, valida al primo invio (evento `research_note` in `eventi-ricerca.jsonl`: `ok: true`, nessun problema), prima di ogni modifica (`registro-1/research-1.md`, riga finale `esito: valida`). Elenca quattro file letti nel progetto (`vercel.json`, `Dockerfile`, `tests/test_smoke.py`, il workflow), la pagina ufficiale di Vercel e «Cosa ho trovato»: `vercel.json` ha solo `cleanUrls`, i workflow non fanno deploy, la chiave `headers` va aggiunta con una voce `/(.*)`. Nessun veto di `research_gate`: la nota è arrivata prima della modifica, quindi il rifiuto dal vivo non si è visto (lo provano i test dei Task precedenti).

## Cosa è stato scritto (il diff)

Un commit, `fb11710 feat: aggiungi X-Content-Type-Options nosniff in vercel.json`:

- `vercel.json`: la chiave `headers` con una sola voce, `source` `/(.*)` e la coppia `X-Content-Type-Options: nosniff`. `cleanUrls` resta `true`.
- `tests/test_vercel_headers.py`, nuovo: due test (la voce `nosniff` su tutte le risposte; `cleanUrls` invariato). Il primo falliva prima della modifica; con la modifica passano tutti e 4 i test del progetto (smoke compresi). RED e GREEN sono nel report dell'implementatore.
- Nessun comando `vercel`, `wrangler` o `docker` scritto o lanciato.

## Verdetto e rilievi R-INFRA

Task 1 `done`, verdetto `approved`, nessun rilievo. **Nessun rilievo `R-INFRA-…` dal vivo.** Il revisore ha giudicato il report e il diff contro le regole del profilo:

- **R-INFRA-01** (file di deploy letti e dove gira il progetto): rispettata; il report nomina `vercel.json`, `Dockerfile` e il workflow, e dice che dove gira oggi il progetto non è dimostrato dai file.
- **R-INFRA-03** (indirizzo ufficiale): rispettata; il report cita https://vercel.com/docs/project-configuration/vercel-json per la proprietà `headers`.
- **R-INFRA-12** (prova senza pubblicazione): rispettata; il report dichiara che non è stata fatta perché il progetto non è collegato a Vercel (nessun progetto, account o credenziale) e che non si è pubblicato né collegato nulla.
- **R-INFRA-02** (comandi dei servizi): non si applica, il diff non ne scrive.
- **R-INFRA-04** (un solo file di configurazione Vercel) e **R-INFRA-05** (nessun segreto nel diff): rispettate.
- Regole di base viste dal revisore: R-BASE-01, 03, 10 e 11.

Il revisore dice quindi di aver applicato le regole `infra` e quelle di base, segno che le ha davanti. Le regole che bloccano non hanno avuto occasione di scattare: la parte «rilievi R-INFRA noti al verdetto» resta provata dai test, non da questa prova.

## Il report dell'implementatore

Stato `DONE`, con `must_have` M1 e M2, senza dubbi. Attenzione a come leggerlo: il testo del task che l'implementatore ha ricevuto (`.tollgate-run/1/task-1.md`, riga «Per il report (R-INFRA-01, 02, 03, 12)») chiedeva già, quasi parola per parola, le tre righe sotto (file di deploy letti, indirizzo di `headers`, «prova non fatta perché il progetto non è collegato»). Quindi i «sì» su questo report provano che ha eseguito il task, non da soli che sia il precaricamento a guidarlo. Dice, con parole sue:

- File letti: `vercel.json` (solo `cleanUrls`), `Dockerfile` (`python:3.12-slim`, cartella `app/`) e il workflow `tollgate-run.yml`; gli altri workflow li ha visti solo nell'elenco e sono tutti di tollgate, quindi non c'è un workflow di deploy. Dove gira oggi il progetto: non è dimostrato dai file (`vercel.json` fa pensare a Vercel, il `Dockerfile` a un container, nessun collegamento a un servizio).
- Indirizzo ufficiale della proprietà `headers`: https://vercel.com/docs/project-configuration/vercel-json.
- Prova senza pubblicazione **non fatta**: il progetto non è collegato a Vercel, quindi un `vercel build` in un progetto collegato non era eseguibile; non ha pubblicato, collegato né cambiato nessun servizio.

## Comandi del modello

`registro-1/comandi-modello.txt` elenca i comandi del modello (sessione principale e subagenti) e il totale degli strumenti. Letti a mano: comandi `tollgate` (`start`, `status`, `task start`, `research submit`, `verify`, `task review-prepare`, `task done`), `git` (elenco dei file, log, stato, `add`, `commit`), `cat` e `ls` dei file del progetto, `python3 -m unittest`. `cat vercel.json` e `git add vercel.json` compaiono, ma sono file, non il programma `vercel`. Nessun `vercel`, `wrangler`, `docker`, `npx`, `npm`, `gh`, `curl` o `git push`. `registro-1/comandi-rischiosi.txt` è vuoto.

Strumenti: 2 `Agent`, 14 `Bash` (4 dei subagenti), 12 `Read` (8), 2 `Grep` (1), 2 `WebFetch` (1), 1 `WebSearch`, 3 `Write` (2), `Skill`, `ToolSearch`, `EnterWorktree`.

## Scostamenti dall'atteso

- **Il piano è stato scritto già nel passo 1.** Il passo 1 doveva fermarsi prima, ma il modello ha scritto e committato il piano subito (`docs/superpowers/plans/2026-11-08-x-content-type-options.md`, `1075c61`), con un nome diverso dal `PLAN_REL` dello script. Nel passo 2 non ne ha scritto un altro e il flusso è andato avanti con quello. L'effetto non è solo di tempi: il piano fisso dello script (che detta testo e test) non è stato usato, e il testo del task dato all'implementatore l'ha scritto il modello, dopo aver letto `rules-infra`. Per questo il task nominava già R-INFRA-01, 02, 03 e 12 e chiedeva le righe del report. Il segnale più forte che le regole arrivano agli agenti è un altro: il revisore cita da sé R-INFRA-04 e R-INFRA-05, che nel testo del task non compaiono (risposta del revisore in `passo2/tentativo-1/claude.jsonl`, evento `task_notification` di `a9c1e6fe…`), insieme a R-BASE-01, 03, 10 e 11.
- Avvisi dell'avvio del passo 1, non legati al profilo: le impostazioni di GitHub Actions non erano leggibili col `gh` finto, la modalità è `detect` (il merge non è impedito), e i dati del `gh` finto non avevano le issue di sentinella.

## Esito rispetto all'atteso del Task 9

| Atteso | Esito |
|---|---|
| `init` propone `infra` con `/Dockerfile` e `/vercel.json`, e non propone `ai` | sì |
| task 1 `done` con verdetto `approved` | sì |
| `agent_type` `tollgate:implementer-infra`, `reviewer_type` `tollgate:reviewer-infra` | sì |
| titolo di `rules-infra` nelle trascrizioni di entrambi gli agenti | sì (`isMeta: sì`, prima del primo turno) |
| nota valida prima della prima modifica | sì |
| report con file di deploy letti, indirizzo ufficiale di `headers` e prova senza pubblicazione dichiarata non fatta | sì (ma il task lo chiedeva già: vedi «Il report dell'implementatore») |
| nessun comando rischioso del modello | sì (`comandi-rischiosi.txt` vuoto) |

## Difetti trovati

Nessuno nel prodotto; nessun giro di correzione del Task 9 necessario.

## Limiti

- Un solo lavoro piccolo (L1) con un task: nessun rilievo `R-INFRA` dal vivo, nessun giro `--fix`, nessun lavoro grande.
- **R-INFRA-12 vista solo nel ramo «perché no».** Il progetto di prova non ha credenziali né un progetto collegato, quindi la regola sulla prova senza pubblicazione è stata rispettata dichiarando che non si poteva fare. Il ramo in cui la prova si fa davvero (per esempio una costruzione locale senza pubblicare) non è stato provato dal vivo.
- Modalità `detect` (conto Free finto), non `protected`.
- **Le difese che `--disallowedTools` non chiude** (`registro-1/limiti.txt`): i divieti sono a prefisso e non chiudono `env VAR=… <programma>`, `sudo`, `xargs`, `bash -c '…'`. Per `git`/`gh` restano aperti `git -C x push …`, `git push --force-with-lease`, `git remote set-url` seguito da un push, `env gh`. `Write` ed `Edit` nudi valgono per qualsiasi percorso. La difesa vera è l'hook `effects` di tollgate più un progetto di prova senza credenziali (nessun `.vercel`, `.env`, `.dev.vars` né file di Wrangler); il modello è cooperativo e lo script rileva a posteriori, in `comandi-rischiosi.txt`. Qui non ha trovato nulla.
- `--allowedTools` concede gli strumenti senza domande: in una sessione interattiva `WebFetch` chiede un permesso per dominio, che qui non è rappresentato.
- La prova gira con gli altri plugin dell'utente attivi nella sessione.
- La prova del precaricamento viene da trascrizioni lette a mano dal controller, non dallo script (vedi sopra). Il report dell'implementatore da solo non la prova (il task chiedeva già quelle righe, e il piano era del modello, non quello fisso dello script): contano le trascrizioni e le regole che il revisore cita senza che il task le nominasse.
- Una pagina di Vercel letta dal modello conteneva un invito rivolto agli agenti a installare un plugin con `npx`. Il modello non l'ha seguito: nei comandi non c'è nessun `npx`.
- Gli orari degli eventi sono UTC; quelli di `esito.txt` sono locali.

## Anonimizzazione delle evidenze

Prima del commit, su tutti i file di `evidenze/b4/flusso/`:

- I due id di sessione sono diventati `SESSIONE-1` (passo 1) e `SESSIONE-2` (passo 2). Gli `agent_id` restano: non sono segreti.
- `/home/<utente>` è diventato `/home/USER`; il nome utente `USER`; il nome dell'host `HOST` (campo `host` degli eventi e ogni altra occorrenza).
- Nelle intestazioni di `comandi-modello.txt` e in `togli-pagine.txt` il percorso assoluto del checkout è stato sostituito da uno relativo al repo.
- Dagli stream-json sono state tolte le righe del messaggio `init` (elenco dei plugin e dei server MCP della macchina) e quelle degli hook di `SessionStart` degli altri plugin: 13 righe nel passo 1 (1 `init` e 12 di `SessionStart`) e 11 nel passo 2 (1 `init` e 10 di `SessionStart`; resta la coppia dell'hook di tollgate).
- Dopo il controllo del rapporto sono stati tolti a mano anche i testi di terzi sotto il tetto di 5.000 caratteri, con lo stesso segnaposto di `togli-pagine` (`[pagina di terzi tolta dalle evidenze: <origine>, <N> caratteri]`): il risultato di `WebSearch` (titoli e indirizzi di siti terzi) e la lettura di una pagina di Vercel salvata, nel passo 1; l'anteprima `persisted-output` di quella pagina, in entrambi i passi. Nella revisione finale ne sono usciti altri due: i `Grep` dell'implementatore sulla copia salvata della stessa pagina (nel passo 1 e nel passo 2), che `togli-pagine` non riconosceva perché guardava solo `WebFetch` e `WebSearch`. Ora tratta come testo di terzi anche ogni risultato di `Read` e `Grep` su un file sotto `tool-results/`, a qualunque lunghezza, e li ha sostituiti con lo stesso segnaposto. Il JSON resta valido riga per riga.
- Nel passo 1 non c'è nessuna riga `SessionStart`: le 12 che c'erano (6 coppie) erano tutte di altri plugin e le ho tolte io; tollgate non ne aveva ancora, perché a quel punto non c'è un lavoro attivo. Nel passo 2 resta la coppia di tollgate («lavoro #1, fase execution»).
- Il testo delle pagine dei fornitori e delle skill e degli hook di terzi era già stato tolto da `registra` (`flowreg.py togli-pagine`, poi un test controlla le evidenze): 5 risultati nel passo 1 e 3 nel passo 2, ognuno sostituito da un segnaposto con indirizzo e lunghezza.
- Restano, perché non identificano l'utente: il percorso `/tmp/claude-1000` (la cartella temporanea delle skill incorporate) e gli id degli hook e dei messaggi.

Controllo (comandi con `grep -rI`, valori cercati non riportati; esito zero in tutti i casi):

| Cercato | Dove | Occorrenze |
|---|---|---|
| nome utente | `docs/verifiche/evidenze/b4/` e questo rapporto | 0 |
| nome dell'host | `docs/verifiche/evidenze/b4/` e questo rapporto | 0 |
| `/home/` seguito da qualcosa di diverso da `USER` | `docs/verifiche/evidenze/b4/` | 0 |
| i prefissi di token di API, di GitHub e di Vercel | `docs/verifiche/evidenze/b4/` e questo rapporto | 0 |
| gli id di sessione reali | `docs/verifiche/evidenze/b4/` e questo rapporto | 0 |
