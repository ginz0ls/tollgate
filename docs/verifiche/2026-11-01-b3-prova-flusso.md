# B3: prova reale corta con il profilo ai

Data: 2 novembre 2026. Piano: B3 (profilo `ai`), Task 10. Stesso schema delle prove di B1 e B2: un lavoro piccolo (L1) con un solo task, eseguito con `claude -p` vero; la differenza da provare è il profilo `ai` acceso da `init` e le sue regole vere, caricate dagli agenti.

- Versioni: Claude Code `2.1.316`, modello `sonnet` per entrambi i passi (`claude-sonnet-5-5`, come riporta `modelUsage` dell'evento `result` di ciascun passo).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=ai` e `B1_FLOW_RULES=vere` (modi `prepara`, `passo1`, `passo2`, `registra`). Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b1/state`. Comandi esatti in `argv.txt` di ogni tentativo.
- Evidenze: `docs/verifiche/evidenze/b3/flusso/` (`validate/`, `passo1/tentativo-1/`, `passo2/tentativo-1/`, `registro-1/`, `exit-codes.txt`).
- Chi ha fatto cosa: la prova l'ha eseguita il controller; questo rapporto la racconta partendo dalle evidenze.

## Passi e tentativi

| Passo | Tentativi | Esito | Durata | Consumo stimato |
|---|---|---|---|---|
| `controlla` e `prepara` | 1 | interruttore acceso, progetto e stato pronti | n/d | nessuno |
| `init --propose` e blocco copiato | 1 | profilo `ai` proposto e committato (`31ad748`); `plan-check` ok | n/d | nessuno |
| `passo1`: `claude plugin validate --strict` | 1 | «Validation passed», uscita 0; un avviso `ICON_MISSING` e un consiglio sul README, che non cambiano l'esito | n/d | nessuno (senza modello) |
| `passo1`: `/tollgate:start #1 L1` | 1 | piano di un task scritto e committato (`742bf47`), registrato da tollgate, fase `execution` | 124 s | 0,72 USD |
| `passo2`: `/tollgate:execute` | 1 | task 1 `done`, verdetto `approved`, commit `bc86d6b` | 115 s | 0,60 USD |

L'esito **non è composito**: ogni passo è riuscito al primo tentativo (`exit-codes.txt`: uscita 0 per entrambi). Totale stimato: 1,32 USD, dentro l'abbonamento: nessuna spesa in più (`total_cost_usd` è la stima dell'evento `result`).

## Proposta di `init`

`init --propose` ha lavorato in modalità `detect`: la risposta del `gh` finto era quella di un conto Free, quindi nessuna protezione dei rami da leggere. Il progetto di prova ha una cartella `ai/` (con `ai/__init__.py` e `ai/summary.py`) e un file `services/notify.py`.

- Riga di `init`: «profilo ai: proposto con paths = ["/ai/**", "services/notify.py"]; lo accendono 3 file: ai/__init__.py, ai/summary.py, services/notify.py».
- Il percorso `/ai/**` viene dalla cartella; `services/notify.py` sta in una cartella qualunque e ci entra **per il suo contenuto** (importa l'SDK di Anthropic): è il rilevamento per contenuto.
- La proposta copre 137 file. Il blocco è stato copiato nel `tollgate.toml` del progetto e committato (`31ad748 profilo ai proposto da init`); `plan-check` risponde `ok []`.

## Agenti lanciati e instradamento

Un solo task, quindi due agenti, entrambi di tipo `ai` (`registro-1/tipi-task.txt`, `events.jsonl`):

| Agente | Tipo | Token |
|---|---|---|
| implementatore (`aea19f16…`) | `tollgate:implementer-ai` | 65.367 |
| revisore (`a09e1aec…`) | `tollgate:reviewer-ai` | 45.621 |

Totale 110.988 token (`registro-1/stats.json`). Veti: 0. Giri di correzione: 0. Blocchi: 0. Il passo 1 non lancia subagenti.

## Precaricamento delle due skill

Prima prova dal vivo della lista di due skill (`skills: [rules-base, rules-ai]`). `registro-1/trascrizioni.txt` elenca i titoli trovati nelle trascrizioni dei due subagenti del passo 2 (lette dal controller, solo nelle due cartelle della prova):

- Per ciascun agente, `# Regole di base (versione 1)` e `# Regole ai (versione 1)` compaiono come messaggi `isMeta: sì`, prima del primo turno dell'assistente. Sono le skill iniettate dal campo `skills:`.
- Compare anche una riga `isMeta: no` per ciascun titolo. Il controller ha verificato che quella riga è il messaggio `api-request-blob`, cioè la richiesta all'API già composta (che contiene le skill precaricate), non una lettura del file della skill fatta dall'agente.
- Nelle letture registrate non c'è nessun `Read` di un `SKILL.md`.
- Il passo 1 (sessione dal checkout) non ha trascrizioni di subagenti. `registro-1/precarico.txt` dice «indizio», perché lo stream-json non porta il percorso delle trascrizioni (come in B1 e B2); la prova è quella del controller.

Il revisore `reviewer-ai` ha usato `WebFetch` dal vivo: nello stream-json del passo 2 il suo `WebFetch` sulla pagina dei modelli (per controllare `claude-haiku-5-5`) ha come `parent_tool_use_id` quello del lancio `Revisione task 1`, quindi è del revisore e non dell'implementatore. È la prima prova reale della decisione 11 (strumenti di ricerca ai revisori). Le letture dei tipi di sola lettura non si registrano in `lookups` (7.1), per questo la tabella qui sotto è solo dell'implementatore.

## Letture registrate (task 1)

Tutte dell'implementatore (`registro-1/lookups.txt`):

| Tipo | Bersaglio |
|---|---|
| `read` | `.tollgate-run/1/task-1.md` |
| `read` | `ai/summary.py` |
| `fetch` | `https://platform.claude.com/docs/en/models/overview` |
| `fetch` | `https://platform.claude.com/docs/en/about-claude/model-deprecations` |

Il modello ha fatto anche 3 `Grep`, che non si registrano (B1-V6, `grep-non-registrati.txt`).

## Nota di ricerca

Consegnata una volta, valida al primo invio (evento `research_note`: `ok: true`, nessun problema), prima di ogni modifica (`registro-1/research-1.md`, riga finale `esito: valida`). Contiene due file letti nel progetto, due pagine ufficiali di Anthropic e «Cosa ho trovato»: l'ultimo Haiku stabile è `claude-haiku-5-5`, stato Active, senza deprecazioni; l'URL e la data vanno accanto alla costante. Nessun veto di `research_gate`: la nota è arrivata prima della modifica, quindi il rifiuto dal vivo non si è visto (lo provano i test del Task 5).

## Cosa è stato scritto (il diff)

Un commit, `bc86d6b feat(ai): aggiungi la costante SUMMARY_MODEL`:

- `ai/models.py`, nuovo: un commento con l'indirizzo della pagina ufficiale dei modelli e «verificato il 2026-11-02», e la costante `SUMMARY_MODEL: str = "claude-haiku-5-5"`. Regole viste: **R-AI-02** (fonte e data accanto all'ID) e **R-AI-01** (il nome del modello in un solo punto).
- `tests/test_models.py`, nuovo: controlla le proprietà dell'ID (stringa, prefisso `claude-`, nessuno spazio, nessuna data a 8 cifre) senza ripetere il nome del modello. Il test falliva per import prima della costante e passa dopo (RED e GREEN nella risposta finale del passo 2).
- `ai/summary.py` non cambia: riceve già il modello come parametro.
- **R-AI-03** (ultimo modello stabile della famiglia): la sessione principale e l'implementatore hanno scelto `claude-haiku-5-5` leggendo la pagina dei modelli e quella delle deprecazioni, non dalla memoria. Il piano cita R-AI-01 e R-AI-02.

## Verdetto e rilievi R-AI

Task 1 `done`, verdetto `approved`, nessun rilievo. **Nessun rilievo `R-AI-…` dal vivo.** La parte «rilievi R-AI noti al verdetto» è quindi provata dai test e non da questa prova: `test_ai_profile_blocking_rule_changes`, `test_ai_profile_non_blocking_rule_approves`, `test_ai_blocking_rule_without_step` in `tests/test_check_task_verdict.py`.

## Esito rispetto all'atteso del Task 10

| Atteso | Esito |
|---|---|
| task 1 `done` con verdetto `approved` | sì |
| `agent_type` `tollgate:implementer-ai`, `reviewer_type` `tollgate:reviewer-ai` | sì |
| titolo di `rules-ai` nelle trascrizioni di entrambi gli agenti | sì (`isMeta: sì`, prima del primo turno) |
| nota valida prima della prima modifica | sì |
| diff con il nome del modello in un punto, URL e data | sì |
| ultimo modello stabile della famiglia | sì (`claude-haiku-5-5`, Active) |

## Difetti trovati

Nessuno nel prodotto; nessun giro del Task 9 necessario.

## Limiti

- Un solo lavoro piccolo (L1) con un task: nessun rilievo `R-AI` dal vivo, nessun giro `--fix`, nessun lavoro grande.
- Modalità `detect` (conto Free finto), non `protected`.
- `--allowedTools` concede gli strumenti senza domande: in una sessione interattiva `WebFetch` chiede un permesso per dominio, che qui non è rappresentato. I divieti di `--disallowedTools` sono a prefisso e non chiudono ogni forma (elenco in `registro-1/limiti.txt`); `comandi-rischiosi.txt` è vuoto.
- La prova gira con gli altri plugin dell'utente attivi nella sessione.
- La prova del precaricamento viene da trascrizioni lette a mano dal controller, non dallo script.
- Gli orari degli eventi sono UTC; quelli di `esito.txt` sono locali.
- Rischio segnalato dal passo 1, fuori dallo scopo della prova e non corretto: `ai/summary.py:14` legge `content[0].text`, ma i modelli 5.x hanno il thinking adattivo attivo di default, quindi il primo blocco potrebbe essere di thinking (testo vuoto o `AttributeError`) e il thinking potrebbe consumare i 200 token di `max_tokens`. Non verificato con una chiamata reale; il progetto di prova non è stato toccato.

## Anonimizzazione delle evidenze

Come in B2, prima del commit, su tutti i file di `evidenze/b3/flusso/`:

- I due id di sessione sono diventati `SESSIONE-1` (passo 1) e `SESSIONE-2` (passo 2). Gli `agent_id` restano: non sono segreti.
- `/home/<utente>` è diventato `/home/USER`; il nome utente `USER`; il nome dell'host `HOST` (campo `host` di `events.jsonl` e `eventi-ricerca.jsonl`).
- Dagli stream-json sono state tolte le righe del messaggio `init` (elenco dei plugin e dei server MCP della macchina) e quelle degli hook di `SessionStart` degli altri plugin: 13 righe nel passo 1 (1 `init` e 12 di `SessionStart`, senza nessuna di tollgate perché ancora senza lavoro) e 11 nel passo 2 (1 `init` e 10 di `SessionStart`; resta la coppia dell'hook di tollgate).
- Nell'intestazione di `comandi-modello.txt` il percorso assoluto è stato sostituito da uno relativo al repo.
- Dagli stream-json è stato tolto il testo delle pagine dei fornitori: i risultati di `WebFetch` (quattro, due pagine della documentazione di Anthropic, da 14.616 a 22.794 caratteri) sono sostituiti da un segnaposto con URL e lunghezza (`[pagina di terzi tolta dalle evidenze: <URL>, <N> caratteri]`), sia nel messaggio sia nel campo `tool_use_result`. Le pagine non hanno una licenza aperta e il repo è pubblico. Per le prove future lo fa `registra` (comando `flowreg.py togli-pagine`, tetto di 5.000 caratteri per risultato di `WebFetch` o `WebSearch`) e un test fallisce se una evidenza pubblica ne contiene uno più lungo. I segnaposto di esempio che stavano in quelle pagine (due prefissi di chiave e una dicitura di intestazione) sono usciti con loro; ne resta uno solo, in un messaggio di testo del passo 1, già reso inoffensivo (`CHIAVE-ANT`).
- Restano, perché non identificano l'utente: il percorso `/tmp/claude-1000` (la cartella temporanea delle skill incorporate) e gli id degli hook e dei messaggi.
- Nel passo 1 è stato tolto anche il testo delle skill che non sono di tollgate, caricate nella sessione (la skill `claude-api` inclusa in Claude Code, circa 110 mila caratteri, e la skill `writing-plans` di `superpowers`, circa 10 mila): ognuna è sostituita da `[skill di terzi tolta dalle evidenze: <nome>, <N> caratteri]`. Restano le skill di tollgate e i titoli `# Regole … (versione 1)`, che provano il precaricamento. Le prove future lo fanno in automatico con `registra` (`flowreg.py togli-pagine`) e un test controlla le evidenze di `b3/`. Le evidenze di B1 e B2 non sono state toccate.

Controllo (comandi con `grep -rI`, valori cercati non riportati; esito zero in tutti i casi):

| Cercato | Dove | Occorrenze |
|---|---|---|
| nome utente | `docs/verifiche/evidenze/b3/` e questo rapporto | 0 |
| nome dell'host | `docs/verifiche/evidenze/b3/` e questo rapporto | 0 |
| `/home/` seguito da qualcosa di diverso da `USER` | `docs/verifiche/evidenze/b3/` | 0 |
| i quattro prefissi di token di API, di GitHub e di intestazione di autorizzazione | `docs/verifiche/evidenze/b3/` e questo rapporto | 0 |
