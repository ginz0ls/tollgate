# B2: prova reale corta con la rules-base vera

Data: 1 novembre 2026. Piano: B2 (regole di base), Task 7. Progetto 5 e piano principale (riga B2): «il blocco scatta in L1 e L2 (test e una prova reale corta)». Stesso progetto di prova e stesso lavoro L1 di B1 (decisione 12): la differenza da provare è la regola vera, caricata dagli agenti.

- Versioni: Claude Code `2.1.314`, modello `sonnet` (`claude-sonnet-5-5`; `modelUsage` riporta anche `claude-haiku-5-5`).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_RULES=vere` (modi `prepara`, `passo1`, `passo2`, `registra`), progetto di prova `spikes/b1/flow/`, raccolta `spikes/b1/flowreg.py`. Nessun GitHub: `gh` finto (`tests/fakegh.py`) in testa al `PATH`, `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b1/state`.
- Interruttore: con `vere` la copia del plugin (`/tmp/tollgate-b1/plugin`) tiene la `skills/rules-base/SKILL.md` del repo, approvata (`approved: 2026-11-01`), senza sostituirla. `prepara` controlla con `lookups.rules_enforced` che l'interruttore sia acceso e altrimenti si ferma. I quattro agenti di codice hanno `skills: [rules-base]`.
- Comando di ogni passo: `claude -p --plugin-dir /tmp/tollgate-b1/plugin --model sonnet --permission-mode acceptEdits --allowedTools "Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob,WebFetch,WebSearch"` con `--disallowedTools` per `gh` per percorso, `git push` verso remoti non locali o forzato, `curl` e `wget`, tetto di 2400 s. Argomenti esatti in `argv.txt` di ogni tentativo.
- Evidenze della prima corsa: `docs/verifiche/evidenze/b2/flusso/` (`validate/validate-1.txt`, `passo1.prev-20261101-082818-633829/tentativo-1/` e `passo2.prev-20261101-082818-633829/tentativo-1/`, spostate da `prepara` alla seconda corsa e mai cancellate, `registro-1/`, `exit-codes.txt`). Evidenze della seconda: `validate/validate-2.txt`, `passo1/tentativo-2/`, `passo2/tentativo-2/`, `registro-2/`. Anonimizzazione: vedi in fondo.

La prova è stata eseguita due volte: la prima prima della revisione finale, la seconda dopo il suo giro di correzione (sezione «Seconda corsa»). Le sezioni da «Passi e tentativi» a «Limiti» descrivono la prima corsa.

## Passi e tentativi

| Passo | Tentativi | Esito | Durata | Consumo stimato |
|---|---|---|---|---|
| `prepara` | 1 | copia del plugin con la skill vera, progetto, `plan-check` del piano di prova ok | — | nessuno |
| `passo1`: `claude plugin validate --strict` sulla copia | 1 | «Validation passed», uscita 0; un avviso `ICON_MISSING` e un consiglio sul README, che non cambiano l'esito | — | nessuno (senza modello) |
| `passo1`: `/tollgate:start #1 L1` | 1 | lavoro L1, piano di un task scritto e committato dal modello e registrato da tollgate, fase `execution` | 85 s | 0,40 USD |
| `passo2`: `/tollgate:execute` | 1 | task 1 `done`, verdetto `approved`, commit `0b11351` | 72 s | 0,52 USD |

L'esito **non è composito**: ogni passo è riuscito al primo tentativo. Totale stimato: 0,92 USD, dentro l'abbonamento (nessuna spesa in più; `total_cost_usd` è la stima dell'evento `result`). Token degli agenti di tollgate (`tollgate stats`): implementatore 49.015, revisore del task 30.531, totale 79.546. Gli orari di questo rapporto sono quelli degli eventi (UTC).

## Letture registrate (task 1)

Tutte con l'`agent_id` dell'implementatore (`registro-1/lookups.txt`):

| Tipo | Bersaglio |
|---|---|
| `read` | `.tollgate-run/1/task-1.md` |
| `bash_read` | `config.toml` |
| `fetch` | `https://docs.python.org/3/library/tomllib.html` |
| `read` | `src/__init__.py`, `tests/test_smoke.py`, `tests/__init__.py`, `config.toml` |

L'implementatore non ha usato `Grep` (`grep-non-registrati.txt`: 0).

## Nota, avvisi e rifiuti

- Prima consegna (evento `research_note`, `seq` 11): `ok: false`, tre file nella nota (`src/__init__.py`, `tests/test_smoke.py`, `tests/__init__.py`) non letti in questo task: erano stati visti solo con i glob di `cat` e `ls`. Seconda consegna (`seq` 12, otto secondi dopo): `ok: true`, `research_ok = 1`. Testo in `registro-1/research-1.md`, con la riga finale `esito: valida`: quattro file in «Letto nel progetto», una fonte in «Documentazione» (`tomllib`) e «Cosa ho trovato».
- Veti: `coordinator` 1 (nel passo 1 la sessione principale ha provato a scrivere il piano con un heredoc in Bash; ha poi usato `Write`) e `plan_check` 1 (primo piano scritto senza task, non registrato; poi corretto). **Nessun veto di `research_gate`**: l'implementatore ha consegnato la nota valida prima di ogni modifica, quindi il rifiuto dal vivo del blocco non si è visto. La prova del blocco resta quella deterministica: `test_real_rules_base_blocks_l1` e `test_real_rules_base_blocks_l2` (Task 5), sulla regola vera.
- Nessun `research_reminder`. Nessuna modifica di codice prima della nota valida: i `Write` dell'implementatore vengono dopo la seconda consegna.

## Verdetto

Task 1 `done`, verdetto `approved`, nessun rilievo (`spec_compliance` vuoto). Il revisore cita **`R-BASE-06`** nel testo: l'URL che compare nel commento del codice è presente in «Documentazione» della nota. È una conferma, non un rilievo: nessun rilievo `R-BASE-…` aperto e nessun rilievo `nota di ricerca`. Il revisore ha anche notato, senza effetto sul verdetto, un `os.chdir` ridondante in un test.

## Precaricamento della rules-base negli agenti

- `registro-1/precarico.txt`: `flowreg.py precarico` ha dato **«indizio»** (3 righe con `R-BASE-` nel flusso), perché lo stream-json di `claude -p` **non contiene `agent_transcript_path`**: nessuna trascrizione leggibile dai percorsi delle uscite.
- **Prova** raccolta dal controller a mano, in `registro-1/precarico-trascrizioni.txt`: le trascrizioni dei due subagenti del passo 2 (`~/.claude/projects/<cartella della prova>/<sessione>/subagents/`) contengono il titolo `# Regole di base (versione 1)`. In entrambe la skill entra come messaggio utente di tipo `isMeta`, in testa alla trascrizione (riga 2 del revisore, riga 4 dell'implementatore), con `<command-name>rules-base</command-name>`, e **nessuna riga nomina `rules-base/SKILL.md`**: nessun agente l'ha aperta con `Read`.
- L'argomento più forte: in entrambe le trascrizioni il messaggio `isMeta` con la skill precede ogni turno dell'assistente, quindi non può venire da una chiamata `Skill` o `Read` dell'agente.
- Cosa dice la prova e cosa no: il titolo da solo non distingue un precaricamento da una lettura con `Read`; lo distingue l'assenza di letture di `rules-base/SKILL.md` insieme al messaggio `isMeta` iniziale. Quindi la skill è caricata dal campo `skills:` degli agenti, non dalla loro iniziativa. Il revisore, che applica le regole, l'ha ricevuta come l'implementatore.

## Esito rispetto all'atteso del Task 7

| Atteso | Esito |
|---|---|
| task 1 `done` con verdetto `approved` | sì |
| nessuna modifica di codice riuscita prima della nota valida | sì |
| almeno una lettura `read` e una `fetch` del task 1 | sì (5 `read`, 1 `bash_read`, 1 `fetch`) |
| rifiuto di `research_gate` dal vivo | non visto (la nota è arrivata prima di ogni modifica); prova deterministica: Task 5 |

## Difetti trovati e corretti

- **Nel prodotto:** nessuno.
- **Nello script di raccolta:** `flowreg.py precarico` conta su `agent_transcript_path` nel flusso, che `claude -p --include-hook-events` non emette: il modo ripiega sull'indizio e lo dichiara, come previsto. La prova l'ha raccolta il controller dalle trascrizioni (`precarico-trascrizioni.txt`). Nessun tentativo consumato; da decidere se il modo debba cercare le trascrizioni per `session_id` e `agent_id` in `~/.claude/projects/`.

## Limiti

- I permessi di `WebFetch` e `WebSearch` sono concessi con `--allowedTools`: in una sessione interattiva `WebFetch` chiede un permesso per dominio e la prova non lo rappresenta.
- Un solo lavoro, piccolo, con un solo task e una sola libreria: la prova mostra il percorso completo con la regola vera, non la tenuta su un lavoro grande, né il rifiuto del blocco dal vivo.
- I divieti di `--disallowedTools` sono a prefisso e non chiudono ogni forma; `Write` ed `Edit` valgono per qualsiasi percorso. Il modello è stato cooperativo: `comandi-rischiosi.txt` è vuoto. Elenco completo in `registro-1/limiti.txt`.
- La prova gira con gli altri plugin dell'utente attivi: nel passo 1 la sessione principale ha invocato `superpowers:writing-plans`. Il testo di quella skill (plugin pubblico, licenza MIT, versione 7.0.0) è caricato in `passo1.prev-20261101-082818-633829/tentativo-1/claude.jsonl` (riga 68 circa) e resta nelle evidenze, perché è già pubblico.
- La prova di precaricamento sta in un file scritto a mano dal controller, non raccolto dallo script.
- L'uscita di `prepara` non è salvata dallo script.

## Seconda corsa, dopo la revisione finale

**Perché.** Il giro di correzione della revisione finale ha cambiato due cose che il passo 2 della prima corsa aveva provato: il brief del revisore (ora contiene anche il report dell'implementatore, in un recinto) e il verdetto sulle regole `R-BASE-…`. Il controller ha quindi rilanciato `prepara`, `passo1`, `passo2` e `registra` sul commit `7c8deb4` del plugin, il 1 novembre 2026. Il passo 2 da solo non si può ripetere: ha bisogno del lavoro in `execution` creato dal passo 1.

**Passi e tentativi.** Secondo tentativo di `passo1` e di `passo2` (tetto 3 su tutta la prova); `prepara` ha spostato la prima corsa in `passo1.prev-20261101-082818-633829/` e `passo2.prev-20261101-082818-633829/`. Ogni passo è riuscito al primo colpo: l'esito **non è composito**.

| Passo | Esito | Durata | Consumo stimato |
|---|---|---|---|
| `passo1`: `validate --strict` | «Validation passed» (`validate/validate-2.txt`) | — | nessuno |
| `passo1`: `/tollgate:start #1 L1` | piano di un task scritto e committato, fase `execution`; un solo `veto`, quello di `coordinator` sull'heredoc del piano | 64 s | 0,41 USD |
| `passo2`: `/tollgate:execute` | task 1 `done`, verdetto `approved`, commit `8ffda85` | 79 s | 0,54 USD |

Totale della seconda corsa 0,95 USD; delle due corse circa 1,87 USD stimati, dentro l'abbonamento. Token di tollgate: implementatore 53.213, revisore del task 31.425, totale 84.638. Claude Code `2.1.314`.

**Letture del task 1** (`registro-2/lookups.txt`), tutte con l'`agent_id` dell'implementatore: `read` del brief, `bash_read` di `config.toml`, `fetch` di `https://docs.python.org/3/library/tomllib.html`, `read` di `tests/test_smoke.py`, `src/__init__.py`, `tollgate.toml` e `config.toml`. Nessun `Grep`.

**Nota.** Come nella prima corsa: prima consegna (`seq` 10) non valida, con tre file nella nota (`tests/test_smoke.py`, `src/__init__.py`, `tollgate.toml`) non ancora aperti con `Read`; dopo la lettura, seconda consegna (`seq` 11, sette secondi dopo) valida, `research_ok = 1` (`registro-2/research-1.md`).

**Veti.** `coordinator` 1; nessun `plan_check` e **nessun veto di `research_gate`**: la nota valida è arrivata prima di ogni modifica, quindi anche qui il rifiuto dal vivo non si è visto (prova deterministica: Task 5).

**Verdetto.** `approved`, `spec_compliance` vuoto, un solo rilievo `minor` (`os.chdir` ridondante con `addCleanup` in `tests/test_config.py`, riga 88), segnalato con `R-BASE-07` nel testo e con la regola «Task 1, passo 1» nel JSON; non blocca. Il revisore ha anche accettato come completo il comando con l'esito di `unittest` nel report (`R-BASE-11`).

**Il report dell'implementatore nel brief del revisore.** Il brief (`review-1.md`, visibile nel flusso di `passo2/tentativo-2/claude.jsonl`) ha la sezione «Report dell'implementatore» con l'avvertenza che le regole sul report si giudicano su quel testo, poi il report (`status: DONE`, `tests`, `files`, `must_have`…) in un recinto, poi la «Nota di ricerca» in un altro recinto. Il revisore ha giudicato il report: il rilievo sopra cita proprio una sua omissione (la funzione da cui ci si è ispirati) e ne valuta il comando di test.

**Precaricamento** (`registro-2/precarico.txt` dice di nuovo «indizio», per la stessa ragione; la prova è in `registro-2/precarico-trascrizioni.txt`, del controller). Il messaggio `isMeta` con la skill è alla riga 2 nella trascrizione del revisore e alla riga 4 in quella dell'implementatore; il primo turno dell'assistente è alla riga 15 e alla riga 18. Nessuna riga nomina `rules-base/SKILL.md`. Il messaggio precede ogni turno dell'assistente: non viene da una chiamata `Skill` o `Read` dell'agente.

**Difetti trovati.** Nessuno nel prodotto e nessuno nello script.

**Anonimizzazione della seconda corsa.** Come per la prima, sui file nuovi: `/home/USER`, `USER`, `HOST`, due id di sessione `SESSION-ID`; dagli stream-json tolte altre 24 righe (2 `init` e 22 eventi di `SessionStart` degli altri plugin). Gli stessi grep (nome utente, host, prefissi di token) su `evidenze/b2` e sul rapporto sono vuoti.

## Anonimizzazione delle evidenze

Come in B1, prima del commit: la cartella home `/home/<utente>` è `/home/USER`, il nome utente `USER`, il nome dell'host (campo `host` di `events.jsonl` e `eventi-ricerca.jsonl`) `HOST`, i due id di sessione (quelli di `session_id` negli stream e di `session` negli eventi) `SESSION-ID`. Sostituzione di testo su tutti i file di `evidenze/b2/flusso/`, compresi `events.jsonl`, `comandi-modello.txt` e `precarico.err` (vuoto). Dagli stream-json sono state tolte **24 righe**: i 2 messaggi `init` (elenco dei plugin e dei server MCP della macchina) e 22 eventi degli hook di `SessionStart` degli altri plugin (restano i due eventi dell'hook di tollgate del passo 2). Controllo: nessuna occorrenza dei nomi della macchina o dell'utente né di prefissi di token di API o di GitHub.
