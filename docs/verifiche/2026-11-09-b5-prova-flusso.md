# B5: prova reale corta con il profilo backend

Esito: riuscita

Data: 10 novembre 2026. Piano: B5 (profilo `backend`), Task 8. Stesso schema delle prove di B1, B2, B3 e B4: un lavoro piccolo (L1) con un solo task, eseguito con `claude -p` vero. Cambia il profilo: `backend` acceso da `init`, con le sue regole vere caricate dagli agenti. Il lavoro è una rotta nuova (`GET /health`) in un piccolo server Python di prova, senza nessuna credenziale e senza nessun servizio collegato.

- Versioni: Claude Code `2.1.321`, modello `sonnet` (`claude-sonnet-5-5`).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=backend` e `B1_FLOW_RULES=vere` (modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`). Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b1/state`. Comandi esatti in `argv.txt` di ogni tentativo.
- Evidenze: `docs/verifiche/evidenze/b5/flusso/` (`validate/`, `passo1/tentativo-1/`, `passo2/tentativo-1/`, `registro-1/`, `exit-codes.txt`).
- Chi ha fatto cosa: la prova l'ha eseguita il controller; questo rapporto la racconta partendo dalle evidenze.
- Prima di partire, nell'ambiente erano assenti `ANTHROPIC_API_KEY`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN`, `SUPABASE_ACCESS_TOKEN` e `DATABASE_URL` (controllata solo la presenza, mai il valore). Il modo `controlla` ha dato ok: `--disallowedTools` nega `gh`, `curl`, `wget`, `vercel`, `wrangler`, `docker`, `npx`, `bunx`, `pnpx`, `bun`, `npm`, `pnpm`, `yarn`, `supabase`, `deno` e `node` nelle quattro forme (da soli, con un percorso, dopo `command`, dopo `env`), e il controllo `effects` di tollgate non è spento nel progetto di prova.

## Passi e tentativi

| Passo | Tentativi | Esito | Durata | Consumo stimato |
|---|---|---|---|---|
| `controlla` e `prepara` | 1 | interruttore acceso, progetto e stato pronti | n/d | nessuno |
| `init --propose` e blocco copiato | 1 | profilo `backend` proposto e committato (`185409b`); `plan-check` ok | n/d | nessuno |
| `passo1`: `claude plugin validate --strict` | 1 | «Validation passed», uscita 0; un avviso `ICON_MISSING` e un consiglio sul README, che non cambiano l'esito | n/d | nessuno (senza modello) |
| `passo1`: `/tollgate:start #1 L1` | 1 | piano di un task scritto e committato (`fe49212`), registrato da tollgate, fase `execution`; 20 turni | 80 s | 0,38 USD |
| `passo2`: `/tollgate:execute` | 1 | task 1 `done`, verdetto `approved`, commit `5ea7b17`; 11 turni | 126 s | 0,54 USD |

L'esito **non è composito**: ogni passo è riuscito al primo tentativo (`exit-codes.txt`: uscita 0 per entrambi). Consumo stimato: 0,38 + 0,54, circa 0,92 USD, dentro l'abbonamento: nessuna spesa in denaro (`total_cost_usd` è la stima dell'evento `result`).

## Proposta di `init`

`init --propose` ha lavorato in modalità `detect`: la risposta del `gh` finto non portava la protezione dei rami. Il progetto di prova ha un server Python (`server/`), un file `edge/index.ts` con un import da `cloudflare:workers`, un file `supabase/functions/hello/index.ts` con una chiamata a `Deno.serve(`, un test di fumo in `tests/` e i workflow di tollgate. I file `.ts` sono solo testo: nessun programma li esegue.

- Il profilo `backend` è proposto con `paths = ["/server/**", "edge/index.ts"]`, e `init` dice che lo accendono 3 file: `edge/index.ts`, `server/__init__.py`, `server/app.py`. `edge/index.ts` è stato riconosciuto dal contenuto (l'import da `cloudflare:workers`), non dal nome.
- Niente sotto `supabase/` entra nel profilo: `supabase/functions/hello/index.ts` ha `Deno.serve(`, ma l'esclusione per frammento di percorso lo tiene fuori.
- I profili `ai` e `infra` non sono proposti.
- Il blocco è stato copiato nel `tollgate.toml` del progetto e committato (`185409b profilo backend proposto da init`); `plan-check` risponde ok.

## Agenti lanciati e instradamento

Un solo task, quindi due agenti, entrambi di tipo `backend` (`registro-1/tipi-task.txt`, `events.jsonl`):

| Agente | Tipo | Token |
|---|---|---|
| implementatore (`a02c045a…`) | `tollgate:implementer-backend` | 53.212 |
| revisore (`a29c344f…`) | `tollgate:reviewer-backend` | 36.703 |

Totale 89.915 token (`registro-1/stats.json`). Veti: 0. Giri di correzione: 0. Blocchi: 0. Il passo 1 non lancia subagenti.

## Precaricamento delle due skill

Le regole arrivano agli agenti con il campo `skills: [rules-base, rules-backend]`. `registro-1/trascrizioni.txt` elenca i titoli trovati nelle trascrizioni dei due subagenti del passo 2 (lette dal controller, solo nelle cartelle della prova):

- Per ciascun agente, `# Regole di base (versione 1)` e `# Regole backend (versione 1)` compaiono come messaggi `isMeta: sì`. Sono le skill iniettate dal sistema per il campo `skills:`, non una lettura del file fatta dal modello.
- Compare anche una riga `isMeta: no` per ciascun titolo: come in B3 e B4, è la richiesta all'API già composta, che contiene le skill precaricate.
- Il passo 1 (sessione dal checkout) non ha trascrizioni di subagenti.

Perché `registro-1/precarico.txt` dice «solo indizio» e non «prova»: lo script cerca nelle uscite del passo, e lì le trascrizioni dei subagenti non ci sono (lo stream-json non porta il loro percorso). Può solo contare le righe `R-BASE-` nell'uscita (3). La prova del precaricamento è quella di `trascrizioni.txt`, letta dal controller.

**Come si distingue dal piano scritto dal modello (decisione 14).** Il modello ha scritto il piano da sé già nel passo 1 (vedi gli scostamenti), quindi il testo del task è suo. Questa volta il piano non guida le risposte sul report: il testo del task che l'implementatore ha letto (`.tollgate-run/1/task-1.md`, riga per riga nello stream del passo 2) ha i passi TDD, i file e le due must-have, ma non nomina contratti, indirizzi ufficiali, prova locale né nessuna `R-BACKEND-…`. Il controller ha controllato con `grep` anche il piano. L'unico punto del passo 1 in cui compaiono gli identificatori `R-BACKEND-01 … 12` è la lettura del `tollgate.toml` del progetto (l'elenco `rules` del blocco proposto da `init`): sono solo gli id, senza il testo delle regole, e il piano che ne segue non li usa. Il segnale è quindi più netto che in B4:

- L'implementatore ha messo nel report, senza che il task lo chiedesse, i contratti letti (o la loro assenza), l'indirizzo ufficiale della documentazione, il fatto che nessun campo esistente cambia, che non c'è un input da validare e che non c'è stata una prova locale sui dati (vedi sotto).
- Il revisore ha citato da sé `R-BACKEND-01`, `02`, `03`, `04`, `05`, `09`, `10`, `11` e `12`. Nello stream (`passo2/tentativo-1/claude.jsonl`) il prompt dell'Agent del revisore (riga 208) è solo il percorso di `review-1.md`, e il testo da rivedere sta nella riga del suo `Read` (riga 225): lì compare solo `R-BASE-05`, mai una `R-BACKEND-…`. Le altre `R-BASE-…` le cita il revisore nella sua uscita, e i riferimenti a `R-BACKEND-…` vengono dalla skill precaricata. Nello stream gli `R-BACKEND-…` compaiono solo nelle due uscite del revisore.

## Letture registrate (task 1)

Tutte dell'implementatore (`registro-1/lookups.txt`):

| Tipo | Bersaglio |
|---|---|
| `read` | `.tollgate-run/1/task-1.md` |
| `read` | `server/app.py` |
| `read` | `tests/test_smoke.py` |
| `fetch` | `https://docs.python.org/3/library/http.server.html` |

Il modello ha fatto anche 3 `Grep` nella sessione principale (del passo 1), che non si registrano (B1-V6, `grep-non-registrati.txt`). I `Grep` e un `Glob` dei subagenti non entrano in `lookups`.

## Nota di ricerca

Consegnata una volta, valida al primo invio (evento `research_note` in `eventi-ricerca.jsonl`: `ok: true`, nessun problema), prima di ogni modifica (`registro-1/research-1.md`, riga finale `esito: valida`). Elenca due file letti nel progetto (`server/app.py`, `tests/test_smoke.py`), la pagina ufficiale di `http.server` e «Cosa ho trovato»: il progetto non ha contratti formali (tipi o schemi), c'è solo la tabella `ROUTES` con funzioni pure e un `dispatch` che dà 404 per rotte o metodi sconosciuti; `health()` segue lo schema di `hello()`; nessun campo o rotta esistente cambia, nessun input da validare, nessun dato toccato. Nessun veto di `research_gate`: la nota è arrivata prima della modifica, quindi il rifiuto dal vivo non si è visto (lo provano i test dei Task precedenti).

## Cosa è stato scritto (il diff)

Un commit, `5ea7b17 feat: aggiungi la rotta GET /health`:

- `server/app.py`: la funzione `health()`, che restituisce stato 200, tipo `application/json` e corpo `{"status": "ok"}`, la voce `("GET", "/health")` in `ROUTES` e `import json` in testa al file.
- `tests/test_health.py`, nuovo: due test (`health()` restituisce il JSON atteso; `GET /health` è instradata e `POST /health` dà 404). Il test falliva prima della modifica (2 errori `AttributeError`); con la modifica passano tutti e 4 i test del progetto, smoke compresi. Nessun server è stato avviato.
- Nessun comando `wrangler`, `supabase`, `deno`, `node` o simili scritto o lanciato.

## Verdetto e rilievi R-BACKEND

Task 1 `done`, verdetto `approved`, nessun rilievo. **Nessun rilievo `R-BACKEND-…` dal vivo.** Il revisore ha giudicato il report e il diff contro le regole del profilo (testo della sua uscita in `passo2/tentativo-1/claude.jsonl`, evento `task_notification` di `a29c344f…`):

- **R-BACKEND-01** (contratti letti): rispettata; il report nomina la tabella `ROUTES`, `dispatch` e il test di fumo come unici contratti e dice che non ci sono tipi o schemi formali.
- **R-BACKEND-02** (indirizzo ufficiale delle API del runtime): non applicabile, `Handler` non è modificato e il file importava già `http.server`; il report cita comunque la pagina ufficiale.
- **R-BACKEND-03** (input validati): non ce ne sono, rispettata.
- **R-BACKEND-04** (errori): nessun errore nuovo, il 404 di `POST /health` viene da `dispatch`.
- **R-BACKEND-05** (niente di pubblico tolto o cambiato): rispettata; nessun campo, rotta o parametro esistente cambia.
- **R-BACKEND-09** (casi del test): basta il caso riuscito, non ci sono input né risorse che possano mancare.
- **R-BACKEND-10** (liste): non ne restituisce.
- **R-BACKEND-11** (nomi): `/health` segue la convenzione di `/hello`.
- **R-BACKEND-12** (dati): rispettata; il report dice che nessun dato viene toccato.
- Regole di base viste dal revisore: R-BASE-07, 10 e 11.

Le regole che bloccano non hanno avuto occasione di scattare: la parte «rilievi R-BACKEND noti al verdetto» resta provata dai test, non da questa prova.

## Il report dell'implementatore

Stato `DONE`, con `must_have` M1 e M2, senza dubbi, senza lasciare nulla indietro. Dice, con parole sue (e senza che il testo del task lo chiedesse):

- Contratti letti: il progetto non ha tipi o schemi formali; ha letto la tabella `ROUTES`, `dispatch` e `tests/test_smoke.py`. Nessun campo, rotta o parametro esistente viene tolto o rinominato, quindi nessun chiamante da cercare.
- Indirizzo ufficiale: https://docs.python.org/3/library/http.server.html, con la precisazione che `Handler` non è modificato e `http.server` non è usato per la prima volta.
- Prova locale sui dati: **non fatta, e dice perché**: nessun input da validare e nessun dato toccato, quindi nessuna prova locale sui dati necessaria. Non ha avviato nessun server.
- Errori: nessun errore nuovo; i 404 restano quelli di `dispatch`.
- Comandi con il loro esito: RED (`python3 -m unittest tests.test_health -v`, 2 errori `AttributeError`), GREEN (`python3 -m unittest discover -s tests -t .`, 4 test OK) e `tollgate verify` con ricevuta `uncounted` e uscita 0 (il progetto non produce un report di test).

Il ramo in cui la prova locale si fa davvero (per esempio un endpoint che legge o scrive dati) non c'è stato: vedi i limiti.

## Comandi del modello

`registro-1/comandi-modello.txt` elenca i comandi del modello (sessione principale e subagenti) e il totale degli strumenti. Letti a mano: comandi `tollgate` (`start`, `status`, `task start`, `research submit`, `verify`, `task review-prepare`, `task done`), `git` (elenco dei file, log, stato, `add`, `commit`), `cat` e `ls` dei file del progetto, `python3 -m unittest`. Nessun `wrangler`, `supabase`, `deno`, `node`, `docker`, `npx`, `npm`, `gh`, `curl` o `git push`. `registro-1/comandi-rischiosi.txt` è vuoto.

Strumenti: 2 `Agent`, 13 `Bash` (3 dei subagenti), 1 `Edit` (1), 1 `Glob` (1), 3 `Grep`, 13 `Read` (6), 2 `Skill`, 1 `ToolSearch`, 1 `WebFetch` (1), 2 `Write` (1), 1 `EnterWorktree`.

## Scostamenti dall'atteso

- **Il piano è stato scritto già nel passo 1**, come in B4. Il passo 1 doveva fermarsi prima, ma il modello ha scritto e committato il piano subito (`docs/superpowers/plans/2026-11-10-rotta-get-health.md`, `fe49212`), con un nome diverso dal `PLAN_REL` dello script. Nel passo 2 non ne ha scritto un altro e il flusso è andato avanti con quello. Il piano fisso dello script (che detta testo e test) non è stato usato, e il testo del task l'ha scritto il modello. Per la prova del precaricamento non è un problema: il piano non nomina nessuna regola `R-BACKEND` né le righe del report (vedi sopra).
- **Il nome del revisore nel piano è sbagliato.** Il piano (e il riepilogo finale del passo 1) dice che l'esecuzione userà `tollgate:task-reviewer`. Il revisore vero lo sceglie tollgate in base al profilo, ed è stato `tollgate:reviewer-backend` (`tipi-task.txt`, `events.jsonl`). Nessun effetto sul flusso.
- Il riepilogo finale del passo 2 dice che la must-have M2 non è nel piano; invece `task-1.md` la elenca. È un'imprecisione del modello nel riassunto, senza effetti.
- Avvisi dell'avvio del passo 1, non legati al profilo: le impostazioni di GitHub Actions non erano leggibili col `gh` finto, la modalità è `detect` (il merge non è impedito), e i dati del `gh` finto non avevano le issue di sentinella.

## Esito rispetto all'atteso del Task 8

| Atteso | Esito |
|---|---|
| `init` propone `backend` con `/server/**` e `edge/index.ts`, non propone `ai` né `infra`, e non guarda sotto `supabase/` | sì |
| task 1 `done` con verdetto `approved` | sì |
| `agent_type` `tollgate:implementer-backend`, `reviewer_type` `tollgate:reviewer-backend` | sì |
| titolo di `rules-backend` nelle trascrizioni di entrambi gli agenti | sì (`isMeta: sì`) |
| nota valida prima della prima modifica | sì |
| report con contratti letti, indirizzo ufficiale e prova locale dichiarata non fatta | sì, e questa volta il task non lo chiedeva |
| nessun comando rischioso del modello | sì (`comandi-rischiosi.txt` vuoto) |

## Difetti trovati

Nessuno nel prodotto; nessun giro di correzione del Task 8 necessario.

## Limiti

- Un solo lavoro piccolo (L1) con un task: nessun rilievo `R-BACKEND` dal vivo, nessun giro `--fix`, nessun lavoro grande.
- **Le regole sul report sono state viste nel ramo «niente da dichiarare».** La rotta non ha input, non cambia nessun contratto e non tocca dati: il report dice che non c'è nulla da validare e che la prova locale non serve. I rami in cui il modello deve davvero cercare i chiamanti di un campo tolto, validare un input o fare una prova locale su dati veri non sono stati provati dal vivo.
- Modalità `detect` (conto Free finto), non `protected`.
- **Le difese che `--disallowedTools` non chiude** (`registro-1/limiti.txt`): i divieti sono a prefisso e non chiudono `env VAR=… <programma>`, `sudo`, `xargs`, `bash -c '…'`. Per `git`/`gh` restano aperti `git -C x push …`, `git push --force-with-lease`, `git remote set-url` seguito da un push, `env gh`. `Write` ed `Edit` nudi valgono per qualsiasi percorso. La difesa vera è l'hook `effects` di tollgate più un progetto di prova senza credenziali; il modello è cooperativo e lo script rileva a posteriori, in `comandi-rischiosi.txt`. Qui non ha trovato nulla.
- I file `.ts` del progetto di prova sono solo testo: nessun programma li esegue, e il test della rotta chiama la funzione senza aprire una porta.
- `--allowedTools` concede gli strumenti senza domande: in una sessione interattiva `WebFetch` chiede un permesso per dominio, che qui non è rappresentato.
- La prova gira con gli altri plugin dell'utente attivi nella sessione.
- La prova del precaricamento viene da trascrizioni lette a mano dal controller, non dallo script (vedi sopra).
- **Un risultato di `WebFetch` è rimasto nelle evidenze.** È la pagina ufficiale di `http.server` (`docs.python.org`), 3.201 caratteri, sotto il tetto `MAX_WEB_RESULT` che `togli-pagine` usa per toglierli. Il controller l'ha letto: è un riassunto in italiano scritto dal modello di `WebFetch`, con nomi di API e una data, senza frasi copiate dalla pagina. Lo lascio, e il test `test_committed_evidence_has_no_long_web_results` è verde.
- Gli orari degli eventi sono UTC; quelli di `esito.txt` sono locali.

## Anonimizzazione delle evidenze

Prima del commit, su tutti i file di `evidenze/b5/flusso/`:

- I due id di sessione sono diventati `SESSIONE-1` (passo 1) e `SESSIONE-2` (passo 2), anche in `events.jsonl` e nei percorsi delle cartelle di lavoro. Gli `agent_id` restano: non sono segreti.
- `/home/<utente>` è diventato `/home/USER`; il nome utente `USER`; il nome dell'host `HOST` (campo `host` degli eventi e ogni altra occorrenza).
- Nelle intestazioni di `comandi-modello.txt` e in `togli-pagine.txt` il percorso assoluto del checkout è stato sostituito da uno relativo al repo.
- Dagli stream-json sono state tolte le righe del messaggio `init` (elenco dei plugin e dei server MCP della macchina) e quelle degli hook di `SessionStart` degli altri plugin: 13 righe nel passo 1 (1 `init` e 12 di `SessionStart`) e 11 nel passo 2 (1 `init` e 10 di `SessionStart`; resta la coppia dell'hook di tollgate, «lavoro #1, fase execution»). Nel passo 1 non resta nessuna riga `SessionStart`: erano tutte di altri plugin, e tollgate non ne aveva ancora perché a quel punto non c'è un lavoro attivo. Il JSON resta valido riga per riga.
- Il testo delle pagine dei fornitori e delle uscite degli hook di terzi era già stato tolto da `registra` (`flowreg.py togli-pagine`): 4 risultati nel passo 1 e 3 nel passo 2, ognuno sostituito da un segnaposto con indirizzo e lunghezza. Per `Read`, `Grep` o `Bash` su `tool-results/` il controller ha verificato a mano che non ce ne fossero.
- Restano, perché non identificano l'utente: il percorso `/tmp/claude-1000` (la cartella temporanea del programma), gli id degli hook e dei messaggi, gli id degli agenti, i nomi `superpowers:…` usati dal modello e i commit SHA della prova.

Controllo (comandi con `grep -rI` sulla cartella `evidenze/b5/`, e su questo rapporto per i primi due; valori cercati non riportati; esito zero in tutti i casi):

| Cercato | Dove | Occorrenze |
|---|---|---|
| nome utente | `docs/verifiche/evidenze/b5/` e questo rapporto | 0 |
| nome dell'host | `docs/verifiche/evidenze/b5/` e questo rapporto | 0 |
| `/home/` seguito da qualcosa di diverso da `USER` | `docs/verifiche/evidenze/b5/` | 0 |
| i prefissi di token di API, di GitHub e di Vercel | `docs/verifiche/evidenze/b5/` e questo rapporto | 0 |
| gli id di sessione reali | `docs/verifiche/evidenze/b5/` e questo rapporto | 0 |
| cartelle dei plugin dell'utente (`.claude/plugins`, `.claude/projects`) e nomi di cartelle private | `docs/verifiche/evidenze/b5/` | 0 |
