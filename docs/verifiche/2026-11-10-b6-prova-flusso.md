# B6: prova reale corta con il profilo frontend

Esito: riuscita

Data: 11 novembre 2026. Piano: B6 (profilo `frontend`), Task 8. Stesso schema delle prove di B1, B2, B3, B4 e B5: un lavoro piccolo (L1), eseguito con `claude -p` vero. Cambia il profilo: `frontend` acceso da `init`, con le sue regole vere caricate dagli agenti. Il lavoro è un pulsante «Salva» a sola icona in una pagina statica (`web/index.html`), con un messaggio «Salvato» e un componente `SaveButton.tsx` accanto a `StatusBadge.tsx`. Due task, nessuna credenziale, nessun servizio collegato, nessun browser.

- Versioni: Claude Code `2.1.322`, modello `sonnet` (`claude-sonnet-5-5`).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=frontend` e `B1_FLOW_RULES=vere` (modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`). Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova in `/tmp/tollgate-b1/state`. Comandi esatti in `argv.txt` di ogni tentativo.
- Evidenze: `docs/verifiche/evidenze/b6/flusso/` (`prepara/`, `validate/`, `passo1/tentativo-1/`, `passo2/tentativo-1/`, `registro-1/`, `exit-codes.txt`).
- Chi ha fatto cosa: la prova l'ha eseguita il controller; questo rapporto la racconta partendo dalle evidenze.
- Prima di partire, nell'ambiente erano assenti `ANTHROPIC_API_KEY`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN`, `SUPABASE_ACCESS_TOKEN`, `DATABASE_URL` e `NPM_TOKEN` (controllata solo la presenza, mai il valore). Il modo `controlla` ha dato ok: `--disallowedTools` nega `vercel`, `wrangler`, `docker`, `npx`, `bunx`, `pnpx`, `bun`, `npm`, `pnpm`, `yarn`, `supabase`, `deno`, `node`, `vite`, `next`, `tsc`, `eslint`, `vitest`, `playwright`, `chromium`, `chromium-browser`, `google-chrome`, `firefox`, `python3 -m http.server` e `python -m http.server` nelle quattro forme (da soli, con un percorso, dopo `command`, dopo `env`); `gh`, `curl` e `wget` sono negati come su `main`. Il controllo `effects` di tollgate non è spento nel progetto di prova.

## Passi e tentativi

| Passo | Tentativi | Esito | Durata | Consumo stimato |
|---|---|---|---|---|
| `controlla` e `prepara` | 1 | interruttore acceso, progetto e stato pronti | n/d | nessuno |
| `init --propose` e blocco copiato | 1 | profilo `frontend` proposto e committato (`e5c5df6`); `plan-check` ok (uscita di `prepara` in `evidenze/b6/flusso/prepara/uscita.txt`) | n/d | nessuno |
| `passo1`: `claude plugin validate --strict` | 1 | «Validation passed», uscita 0; un avviso `ICON_MISSING` e un consiglio sul README, che non cambiano l'esito | n/d | nessuno (senza modello) |
| `passo1`: `/tollgate:start #1 L1` | 1 | piano di due task scritto e committato (`8ad7a20`), registrato da tollgate, fase `execution`; 23 turni | 109 s | 0,51 USD |
| `passo2`: `/tollgate:execute` | 1 | task 1 `done` (`4b991ab`) e task 2 `done` (`d360da3`), entrambi `approved`; 16 turni | 176 s | 0,94 USD |

L'esito **non è composito**: ogni passo è riuscito al primo tentativo (`exit-codes.txt`: uscita 0 per entrambi). Consumo stimato: 0,51 + 0,94, circa 1,45 USD, dentro l'abbonamento: nessuna spesa in denaro (`total_cost_usd` è la stima dell'evento `result`).

## Proposta di `init`

Il progetto di prova è una pagina statica (`web/index.html`, `web/styles.css`), un componente (`src/components/StatusBadge.tsx`), una rotta (`src/routes/home.tsx` che importa `@tanstack/react-router`), un test Python che legge la pagina come testo (`tests/test_page.py`) e i workflow di tollgate. I file `.tsx`, `.css`, `.html` e `.js` sono solo testo: nessun programma li esegue né li serve.

- `init` propone `frontend` con `paths = ["**/*.tsx", "/web/**", "src/components/**"]` e dice che lo accendono 4 file: `src/components/StatusBadge.tsx`, `src/routes/home.tsx`, `web/index.html`, `web/styles.css`.
- **`backend` non è proposto**: l'uscita di `prepara` (`evidenze/b6/flusso/prepara/uscita.txt`) dice che nessun file del repo corrisponde ai suoi percorsi. `src/routes/home.tsx` ha l'import da `@tanstack/react-router` ed è trovato per contenuto da `frontend`; la sola cartella `routes/` non basta ad accendere `backend` (P9 visto dal vivo).
- I profili `ai` e `infra` non sono proposti (stessa uscita: nessun file corrisponde).
- Il blocco è stato copiato nel `tollgate.toml` del progetto e committato (`e5c5df6 profilo frontend proposto da init`); `plan-check` risponde ok (`plan-check: ok []` nella stessa uscita).

## Agenti lanciati e instradamento

Due task, quindi quattro agenti, tutti di tipo `frontend` (`registro-1/tipi-task.txt`, `events.jsonl`):

| Agente | Task | Tipo | Token |
|---|---|---|---|
| implementatore (`a738e6ee…`) | 1 | `tollgate:implementer-frontend` | 67.609 |
| revisore (`ac4946d5…`) | 1 | `tollgate:reviewer-frontend` | 39.959 |
| implementatore (`ada78619…`) | 2 | `tollgate:implementer-frontend` | 43.293 |
| revisore (`a3ad75d2…`) | 2 | `tollgate:reviewer-frontend` | 28.739 |

Totale 179.600 token (`registro-1/stats.json`): 110.902 gli implementatori, 68.698 i revisori. Veti: 0. Giri di correzione: 0. Blocchi: 0. Il passo 1 non lancia subagenti.

## Precaricamento delle due skill

Le regole arrivano agli agenti con il campo `skills: [rules-base, rules-frontend]`. `registro-1/trascrizioni.txt` elenca i titoli trovati nelle trascrizioni dei quattro subagenti del passo 2 (lette dal controller, solo nelle cartelle della prova):

- Per ciascuno dei quattro agenti (due implementatori, due revisori), `# Regole di base (versione 1)` e `# Regole frontend (versione 1)` compaiono come messaggi `isMeta: sì`. Sono le skill iniettate dal sistema per il campo `skills:`, non una lettura del file fatta dal modello.
- Compare anche una riga `isMeta: no` per ciascun titolo. `trascrizioni.txt` dà solo i titoli: la lettura che sia la richiesta già composta, come nelle prove precedenti, è un'ipotesi non provata da queste evidenze, e la prova resta quella delle righe `isMeta: sì`.
- Il passo 1 (sessione dal checkout) non ha trascrizioni di subagenti.

Perché `registro-1/precarico.txt` dice «solo indizio» e non «prova»: lo script cerca nelle uscite del passo, e lì le trascrizioni dei subagenti non ci sono (lo stream-json non porta il loro percorso). Può solo contare le righe `R-BASE-` nell'uscita (4). La prova del precaricamento è quella di `trascrizioni.txt`, letta dal controller.

**Come si distingue dal piano scritto dal modello (decisione 15).** Questa volta il piano **non** è un testimone pulito, a differenza di B5. Nel passo 1 (`passo1/tentativo-1/claude.jsonl`) la sequenza è questa:

- Il modello legge il `tollgate.toml` del progetto (uso a riga 128, risultato a riga 135 dello stream): lì ci sono gli id `R-FRONTEND-01 … 12` dell'elenco `rules`, solo gli id.
- Poi dice di voler leggere le regole prima del piano (un pulsante a sola icona ha vincoli di accessibilità) e **carica da sé** la skill `tollgate:rules-frontend` con lo strumento `Skill` (righe 156-164). Ne ha quindi il testo intero prima di scrivere.
- Il piano (`Write` a riga 182) cita per nome `R-FRONTEND-06` (nome accessibile con `aria-label`), `R-FRONTEND-09` (regione di stato che annuncia il testo inserito), `R-FRONTEND-04`/`08`/`12` (nessuno stile nuovo), `R-FRONTEND-01`/`02`/`11` (decisione D8: versione di React non dichiarata, componenti simili, nessun test dei componenti). Il piano nomina quindi le regole, a differenza di quello di B5, perché il modello le aveva già lette.

Il piano non dice dunque nulla sul precaricamento. Il segnale buono sta altrove:

- **I titoli `isMeta: sì` nelle trascrizioni dei quattro subagenti**: è la prova diretta.
- **Il task 2.** `task-2.md` (riga 351 dello stream) non contiene nessuna `R-FRONTEND-…`, né `package.json`, né l'indirizzo di React; nomina `StatusBadge.tsx` come modello di stile. L'implementatore del task 2 non ha letto il piano (`lookups.txt`: ha letto `task-2.md`, `StatusBadge.tsx`, `tests/test_save_button.py` e, con `cat`, i file della pagina). Eppure il suo report dice, con le parole delle regole, che non c'è `package.json` e quindi la versione di React non è dichiarata, dà l'indirizzo della documentazione corrente, e spiega perché `StatusBadge.tsx` non è riusabile. Per fare questo non bastano gli id: gli viene dalla skill precaricata.
- **Il revisore cita da sé regole che nessun file gli passa.** Il file di revisione del task 1 (`review-1.md`, riga 294 dello stream) porta solo `R-FRONTEND-01`, `02` e `11` (dal report dell'implementatore) e il revisore cita in più `R-FRONTEND-04`, `05`, `06`, `08`, `09` e `12`. Quello del task 2 (`review-2.md`, riga 469) porta solo `01` e `02` e il revisore cita in più `03`, `04`, `05`, `06`, `08`, `09`, `11` e `12`. `R-FRONTEND-03` e `05` non compaiono nemmeno nel piano. Le letture dei revisori si vedono nello stream e nessuna è il piano: quello del task 1 legge `review-1.md` (riga 288), `task-1.md` (297) e `review-1.diff` (300), quello del task 2 `review-2.md` (463), `task-2.md` (472) e `review-2.diff` (475), e i resoconti dicono `tool_uses: 3` (righe 316 e 491). Le regole citate dai revisori e assenti da quei file possono quindi venire solo dalla skill precaricata.
- **Il task 1 non è un testimone pulito.** L'implementatore del task 1 ha letto il piano (`lookups.txt`, n. 5; stream del passo 2, `passo2/tentativo-1/claude.jsonl`, riga 147), che descrive già `R-FRONTEND-01`, `02` e `11`: il suo report su queste tre non prova il precaricamento. Vale il task 2.

## Letture registrate

Tutte degli implementatori (`registro-1/lookups.txt`): 9 `read`, 5 `bash_read`, 1 `fetch`.

| Task | Tipo | Bersaglio |
|---|---|---|
| 1 | `read` | `.tollgate-run/1/task-1.md`, `web/index.html`, `tests/test_page.py`, `web/styles.css`, il piano, `src/components/StatusBadge.tsx` |
| 2 | `read` | `.tollgate-run/1/task-2.md`, `src/components/StatusBadge.tsx`, `tests/test_save_button.py` |
| 2 | `bash_read` | `web/index.html`, `web/app.js`, `web/styles.css`, `tollgate.toml`, `config.toml` |
| 2 | `fetch` | la pagina di React sugli attributi comuni dei componenti del DOM (`react.dev`) |

Il modello non ha fatto `Grep` nella sessione principale (`grep-non-registrati.txt`: 0). Un `Glob` e le letture dei subagenti non entrano in `lookups` oltre a quanto sopra.

## Note di ricerca

Due note, ciascuna valida al primo invio (eventi `research_note` in `eventi-ricerca.jsonl`: `ok: true`, nessun problema), prima di ogni modifica del task (`registro-1/research-1.md` e `research-2.md`, riga finale `esito: valida`).

- **Task 1** (`research-1.md`): cinque file letti nel progetto (pagina, stili, test esistente, `StatusBadge.tsx`, piano). «Nessuna fonte esterna»: il diff usa solo HTML, JavaScript del browser senza librerie e `unittest`. Cosa ha trovato: un solo submit «Invia» e nessuno script; gli stili di `button` e del focus esistono già; il test esistente della pagina non va toccato.
- **Task 2** (`research-2.md`): cinque file letti, più la pagina di React. **Ramo di R-FRONTEND-01 visto: versione non dichiarata.** La nota dice «Non c'è package.json: la versione di React non è dichiarata (documentazione corrente react.dev)», con l'indirizzo della pagina e due fatti presi da lì (`onClick` riceve una funzione, gli attributi `aria-*` si scrivono come in HTML). Per **R-FRONTEND-02** (componenti simili) la nota e il report cercano in `src/components/` e trovano solo `StatusBadge.tsx`, che non è un pulsante: ne seguono lo stile (props tipizzate, `export function`) e non lo riusano.

Nessun veto di `research_gate`: le note sono arrivate prima delle modifiche, quindi il rifiuto dal vivo non si è visto (lo provano i test dei Task precedenti).

## Cosa è stato scritto (il diff)

Due commit sul ramo del lavoro, dopo il piano (`8ad7a20`):

- `4b991ab feat: pulsante Salva a sola icona con messaggio Salvato`: in `web/index.html`, lo `<script src="app.js" defer>`, un `<button type="button" id="salva" aria-label="Salva">` con dentro `<span aria-hidden="true">` e il dischetto 💾, e un `<p id="salvato" role="status">` vuoto dopo il modulo; il nuovo `web/app.js`, senza librerie, che al clic di `#salva` scrive «Salvato» in `#salvato` con `textContent`; il nuovo `tests/test_save_button.py`, con un parser `html.parser` e tre test. Il test falliva prima (3 errori), poi passano tutti e 4 i test del progetto, compreso quello esistente di `test_page`.
- `d360da3 feat: componente SaveButton accanto a StatusBadge`: il nuovo `src/components/SaveButton.tsx` (`type SaveButtonProps`, `export function SaveButton`, pulsante `type="button"`, `aria-label="Salva"`, icona in uno `span aria-hidden`, `onClick={onSave}`, nessuno stile in linea né colore scritto a mano) e un quarto test in `tests/test_save_button.py`. Rosso (file inesistente), poi 5 test verdi.

Il pulsante con la sola icona ha quindi un nome accessibile (`aria-label="Salva"`, icona nascosta ai lettori di schermo) sia nella pagina sia nel componente, e il messaggio è una regione di stato (`role="status"`) vuota nel markup, a cui lo script aggiunge il testo. `web/styles.css` non è toccato.

## Verdetto e rilievi R-FRONTEND

Task 1 `done`, verdetto `approved`, nessun rilievo. Task 2 `done`, verdetto `approved`, con **un rilievo `minor`** (`R-FRONTEND-12`, riga 22 del diff `review-2.diff`, relativa a `src/components/SaveButton.tsx`): `id="salva"` è fisso nel componente, quindi due istanze nella stessa pagina darebbero id duplicati. Il brief lo richiedeva e il revisore lo segnala come nota. Un secondo appunto del revisore (il test del componente guarda solo il testo del file con espressioni regolari) è scritto nel testo e non è nel blocco dei rilievi: è ciò che chiede il piano, e il repo non ha un test runner per i componenti.

Cosa ha detto il revisore (testo dei suoi `task_notification` in `passo2/tentativo-1/claude.jsonl`):

- **Task 1:** `R-FRONTEND-05` e `06` rispettate (`button` nativo di tipo `button`, `aria-label="Salva"`, un solo `span aria-hidden`); `R-FRONTEND-09` rispettata (messaggio in `p#salvato` con `role="status"`, vuoto all'inizio); `R-FRONTEND-08` (il diff non tocca il focus), `04` e `12` (nessun colore né stile nuovo), `11` (nessun test dei componenti nel repo) non applicabili o rispettate; `R-FRONTEND-02` rispettata nel report. Regole di base viste: `R-BASE-01`, `02`, `03`, `09`.
- **Task 2:** `R-FRONTEND-01` (report con la versione non dichiarata e l'indirizzo), `02` (`StatusBadge.tsx` nominato e motivato), `05` e `06` (pulsante nativo con `aria-label`, icona nascosta), `03`, `04`, `08` (il componente non carica dati, non ha colori né tocca il focus), `11` (nessun test dei componenti), `09` (il componente non mostra messaggi, non si applica).

Le regole che bloccano non hanno avuto occasione di scattare: la parte «rilievi R-FRONTEND noti al verdetto» resta provata dai test, non da questa prova. Nessun rilievo, nemmeno minore, ha toccato il nome accessibile o la regione di stato: erano già giusti perché il modello aveva letto le regole prima di scrivere (vedi sopra).

## I report degli implementatori

Entrambi `DONE`. Task 1: must-have M1, M2, M3, M5 (M4 è del task 2); dichiara che il clic non è provato in un browser e che la ricevuta di `verify` è `uncounted` con uscita 0, «non un esito green». Task 2: M1-M5, senza dubbi. Con parole proprie, e senza che il testo dei task lo chiedesse:

- `R-FRONTEND-01`: nessuna libreria toccata (task 1) oppure versione di React non dichiarata, con l'indirizzo della documentazione corrente (task 2).
- `R-FRONTEND-02`: `src/components/StatusBadge.tsx` cercato, non riusabile perché non reagisce a un clic.
- `R-FRONTEND-11`: nel repo non ci sono test dei componenti, quindi non si applica.
- Comandi con il loro esito: RED e GREEN con `python3 -m unittest …` e `tollgate verify` con ricevuta `uncounted`.

## Comandi del modello

`registro-1/comandi-modello.txt` elenca i comandi del modello (sessione principale e subagenti) e il totale degli strumenti. Letti a mano: comandi `tollgate` (`start`, `status`, `status --checkpoint`, `research submit`, `verify`, `task review-prepare`, `task done`, `task start`), `git` (elenco dei file, log, stato, `add`, `commit`), `cat`, `ls` e `grep` dei file del progetto, `python3 -m unittest` e uno script `python3` di modifica del test. Il modello ha lanciato anche `tollgate plan-check` nel passo 1 (stream, riga 193): il comando **non esiste** (`invalid choice: 'plan-check'`, `exit=2`, riga 204). Non ha avuto effetto: il piano era già registrato dall'hook alla scrittura. Nessun `node`, `npm`, `npx`, `vite`, `tsc`, `playwright`, browser, `http.server`, `wrangler`, `supabase`, `deno`, `docker`, `gh`, `curl` o `git push`. `registro-1/comandi-rischiosi.txt` è vuoto.

Strumenti: 4 `Agent`, 23 `Bash` (8 dei subagenti), 2 `Edit` (2), 1 `EnterWorktree`, 1 `Glob` (1), 24 `Read` (15), 4 `Skill` (1), 1 `ToolSearch`, 1 `WebFetch` (1), 3 `Write` (2).

## Scostamenti dall'atteso

- **Il piano è stato scritto già nel passo 1**, come in B4 e B5. Il passo 1 doveva fermarsi prima, ma il modello ha scritto e committato il piano subito (`docs/superpowers/plans/2026-11-11-pulsante-salva.md`, `8ad7a20`), con un nome diverso dal `PLAN_REL` dello script. Nel passo 2 non ne ha scritto un altro. Questa volta il piano nomina le regole e ciò che chiedono (vedi «Precaricamento»), perché il modello aveva caricato `tollgate:rules-frontend` da sé; per questo la distinzione si fa sul task 2 e sui titoli `isMeta`.
- **`verify` dà `uncounted`** (uscita 0) in entrambi i task: il progetto di prova non produce un report di test che tollgate sappia contare. Gli implementatori lo dicono nel report.
- **Nota del revisore sul task 2**: l'`id="salva"` fisso nel componente (rilievo `minor`, sopra). Nessun effetto sul verdetto.
- **Un comando inesistente nel passo 1**: il modello ha lanciato `tollgate plan-check` (non è un sottocomando; `exit=2`). Nessun effetto sul flusso: il piano è stato registrato lo stesso dall'hook alla scrittura (evento `scope_registered` in `events.jsonl`).
- Avvisi dell'avvio del passo 1, non legati al profilo: le impostazioni di GitHub Actions non erano leggibili col `gh` finto e la modalità è `detect` (il merge non è impedito).

## Esito rispetto all'atteso del Task 8

| Atteso | Esito |
|---|---|
| `init` propone `frontend` con `**/*.tsx`, `/web/**`, `src/components/**` e non propone `backend` | sì |
| task 1 `done` con verdetto `approved` | sì (e anche il task 2) |
| `agent_type` `tollgate:implementer-frontend`, `reviewer_type` `tollgate:reviewer-frontend` | sì, per entrambi i task |
| titolo di `rules-frontend` nelle trascrizioni di entrambi gli agenti | sì (`isMeta: sì`, quattro agenti) |
| nota valida prima della prima modifica | sì, per entrambi i task |
| nessun comando rischioso del modello | sì (`comandi-rischiosi.txt` vuoto) |
| il piano scritto nel passo 1 nomina ciò che le regole chiedono | sì: `aria-label`, `role="status"` e le `R-FRONTEND-…` |

## Difetti trovati

Nessuno nel prodotto; nessun giro di correzione del Task 8 necessario.

## Limiti

- Un solo lavoro piccolo (L1) con due task: nessun veto dal vivo, nessun giro `--fix`, nessun lavoro grande. Il revisore ha approvato due volte con un solo rilievo minore.
- **Il modello ha scritto bene perché aveva letto le regole.** Le `R-FRONTEND` che contano (nome accessibile, regione di stato) erano già nel piano, quindi la prova non mostra un rilievo del revisore che corregga un errore del modello: mostra che le regole arrivano e che il modello le segue.
- **Una pagina statica, nessun browser.** Il clic non è provato in nessun browser: il test legge la pagina con `html.parser` e `web/app.js` come testo. Nessun server avviato, nessun programma di `--disallowedTools` lanciato, nessun file `.tsx` compilato o eseguito. Un test di una pagina statica non prova il comportamento in un browser.
- **Le difese che `--disallowedTools` non chiude** (`registro-1/limiti.txt`): i divieti sono a prefisso e non chiudono `env VAR=… <programma>`, `sudo`, `xargs`, `bash -c '…'`; per `git`/`gh` restano aperti `git -C x push …`, `git push --force-with-lease`, `git remote set-url` seguito da un push, `env gh`. Non coprono le forme con opzioni prima di `-m` né altri interpreti (`python3 -B -m http.server`, `python3.11 -m http.server`, `python3 -c "import http.server…"`): per quelle `registra` cerca `http.server` in qualunque punto dei comandi Bash dello stream, e non ha trovato nulla. `Write` ed `Edit` nudi valgono per qualsiasi percorso. La difesa vera è l'hook `effects` di tollgate più un progetto di prova senza credenziali.
- `--allowedTools` concede gli strumenti senza domande: in una sessione interattiva `WebFetch` chiede un permesso per dominio, che qui non è rappresentato.
- La prova gira con gli altri plugin dell'utente attivi nella sessione.
- La prova del precaricamento viene da trascrizioni lette a mano dal controller, non dallo script.
- **Un risultato di `WebFetch` è rimasto nelle evidenze.** È la pagina di React letta nel task 2 (`react.dev`), 1.238 caratteri, sotto il tetto `MAX_WEB_RESULT` che `togli-pagine` usa per toglierli. Il controller l'ha letto: un riassunto in italiano del modello di `WebFetch`, con un esempio JSX di poche righe e due frasi brevi della pagina tra virgolette (una riga ciascuna). Lo lascio, e il test `test_committed_evidence_has_no_long_web_results` è verde.
- Gli orari degli eventi sono UTC; quelli di `esito.txt` sono locali.

## Anonimizzazione delle evidenze

Prima del commit, su tutti i file di `evidenze/b6/flusso/`:

- I due id di sessione sono diventati `SESSIONE-1` (passo 1) e `SESSIONE-2` (passo 2), anche in `events.jsonl`, in `eventi-ricerca.jsonl` e nei percorsi delle cartelle di lavoro. Gli `agent_id` restano: non sono segreti.
- Il nome della macchina è diventato `HOST` (campo `host` degli eventi e ogni altra occorrenza). Il nome utente e `/home/<utente>` comparivano solo nel percorso assoluto del checkout (in `comandi-modello.txt` e `togli-pagine.txt`) e nelle righe `init` poi tolte: il percorso è diventato relativo al repo.
- Dagli stream-json sono state tolte le righe del messaggio `init` (elenco dei plugin, dei server MCP e delle skill della macchina, percorso del socket) e quelle degli hook di `SessionStart` degli altri plugin: 13 righe nel passo 1 (1 `init` e 12 di `SessionStart`, cioè 6 hook) e 11 nel passo 2 (1 `init` e 10 di `SessionStart`, cioè 5 hook; resta la coppia dell'hook di tollgate, «lavoro #1, fase execution»). Nel passo 1 non resta nessuna riga `SessionStart`: tollgate non aveva ancora un lavoro attivo. Il JSON resta valido riga per riga.
- Il testo delle pagine dei fornitori e delle uscite degli hook di terzi era già stato tolto da `registra` (`flowreg.py togli-pagine`): 4 risultati nel passo 1 e 3 nel passo 2, ognuno sostituito da un segnaposto con indirizzo e lunghezza. Per `Read`, `Grep` o `Bash` su `tool-results/` il controller ha verificato a mano che non ce ne fossero.
- Restano, perché non identificano l'utente: gli id degli hook e dei messaggi, gli id degli agenti, i nomi `superpowers:…` usati dal modello, le firme dei blocchi di ragionamento e i commit SHA della prova. Restano anche le righe vuote o `{}` degli hook `PreToolUse` e `PostToolUse` degli altri plugin, che non portano testo.

Controllo (comandi con `grep -rIE` sulla cartella `evidenze/b6/`, valori cercati non riportati; esito zero in tutti i casi):

| Cercato | Dove | Occorrenze |
|---|---|---|
| nome utente | `docs/verifiche/evidenze/b6/` e questo rapporto | 0 |
| nome dell'host | `docs/verifiche/evidenze/b6/` e questo rapporto | 0 |
| `/home/` seguito da qualcosa di diverso da `USER` | `docs/verifiche/evidenze/b6/` | 0 |
| i prefissi di token di API, di GitHub e di Vercel | `docs/verifiche/evidenze/b6/` e questo rapporto | 0 |
| gli id di sessione reali | `docs/verifiche/evidenze/b6/` e questo rapporto | 0 |
| cartelle dei plugin dell'utente (`.claude/plugins`, `.claude/projects`), percorso del socket (`/run/user`) e nomi di cartelle private | `docs/verifiche/evidenze/b6/` | 0 |
| stringhe lunghe da 40 caratteri in su | `docs/verifiche/evidenze/b6/` | solo firme dei blocchi di ragionamento, SHA di commit, id di test, nomi di rami e di cartelle di lavoro della prova |
