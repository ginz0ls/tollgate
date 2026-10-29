# tollgate B1: informati prima

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il meccanismo del passo «informati prima» del sotto-progetto B: gli implementatori ricevono gli strumenti per leggere la documentazione, gli hook registrano le letture, l'implementatore consegna una nota di ricerca che tollgate confronta con le letture registrate, e la prima modifica di un task senza nota valida riceve un avviso (L0, e ogni livello finché `rules-base` non è approvata) o un rifiuto (L1 e L2 dopo l'approvazione). Il revisore del task controlla che la nota sia pertinente. Nessuna regola di profilo: quelle sono di B2-B7.

**Architecture:** Le letture (`Read`, `Grep`, `WebFetch`, `WebSearch`, gli strumenti di documentazione MCP e le letture riconosciute nei comandi Bash) arrivano da `PostToolUse` come nuovo evento d'ingresso `post_lookup` e finiscono, normalizzate e attribuite al task dell'implementatore, nella tabella `lookups` (migrazione 6), scritte dal modulo `tollgate_checks.lookup_rec`. L'implementatore consegna la nota con `research submit <k>` (testo da stdin): la CLI (`tollgate_flow.research_cmd`) la analizza con una funzione pura (`tollgate_analysis.research`), la confronta con le letture del task, la salva in `tasks` e in `.tollgate-run/<N>/research-<k>.md` e stampa i problemi. Un modulo nuovo del registro (`research_gate`) guarda `tasks.research_ok` alla prima modifica.

**Tech Stack:** Python ≥ 3.11, solo libreria standard; bash; git; Claude Code 2.1.311 (verifiche e prova reale con `claude -p --plugin-dir`, solo dal controller). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità per B: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui) e la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 26 (la 27 la scrive il Task 10): sezioni 3.2, 5, 6.3, 7.1, 7.2, 8.1, 8.5, 8.6, 11.4, 12, 14, 16, 18.4, 18.5. Piano principale di B: `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_gate` non importa `db` né `sqlite3`.
- **Un modulo del registro non scrive nel DB** (spec 3.2): chiede con `record`; ogni operazione nuova va in `apply._OPS` (oggi 28) e il suo test.
- **Migrazioni solo in avanti**, con la copia prima (spec 12.2): la 6 è l'unica di B1.
- **Testo non fidato** (pagine scaricate, nota di ricerca, report): mai in un argomento di `git` o `gh`; nei brief dentro `brief.fence` con `brief.DATA_NOTE`. Le pagine scaricate sono dati, mai istruzioni, con la stessa frase già usata da `agents/spec-auditor.md` e `agents/spec-adversary.md`.
- Programma nei messaggi per il modello: sempre `tollgate_core.paths.program_command`; nelle skill `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`.
- **Nessuna rete nei test**, nessun `claude` vero nei test (uno finto nel `PATH` è ammesso), `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`.
- **`claude -p` solo dal controller**, solo nel Task 1 e nel Task 9, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`.
- Un lavoro iniziato prima di B1 continua con le regole con cui era partito (progetto 8): mai un avviso né un rifiuto del passo su di lui.
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che il progetto lascia a chi costruisce (sezione 6) o che il codice reale impone, con il costo se sbagliate. Il Task 10 le riporta nella revisione 27 della spec.

1. **Dove sta la nota** (progetto 6). La consegna l'implementatore con `python3 "<bin>" research submit <k>` e il testo su stdin, non con `Write`: una scrittura sarebbe essa stessa «la prima modifica», e una cartella esente dallo scope sarebbe una porta aperta. Lo stdin è un heredoc con il **delimitatore tra apici e poco probabile**, `<<'NOTA_DI_RICERCA_FINE'` (`research.HEREDOC_END`): senza apici la shell eseguirebbe i backtick del Markdown, e una riga `EOF` dentro la nota la chiuderebbe. Il delimitatore non contiene `TOLLGATE_`, che `bash_rules` nega; il brief avvisa che una nota con `TOLLGATE_` nel testo viene negata allo stesso modo. La CLI salva il testo in `tasks.research_note` e in `.tollgate-run/<N>/research-<k>.md` (già fuori da git, spec 6.3), con l'esito in `tasks.research_ok`. Costo: un comando in più per l'implementatore; il brief e il rifiuto lo scrivono già completo.
2. **Formato della nota.** Markdown con le sezioni `## Letto nel progetto` (un percorso per riga, elenco puntato), `## Documentazione` (una fonte per riga: `- <URL> — <cosa dice>` oppure `- context7:<libraryId> — <cosa dice>`), `## Cosa ho trovato` (testo non vuoto), oppure, al posto di `## Documentazione`, `## Nessuna fonte esterna` con il motivo sulla riga seguente. Separatore tra fonte e descrizione: ` — ` (trattino lungo) oppure ` - `. Al più 8.000 caratteri. Costo: una nota scritta in un'altra forma è non valida e il messaggio dice quale sezione manca.
3. **Una nota è valida** (progetto 3.3) se: (a) ha almeno un file in «Letto nel progetto»; (b) ogni file dichiarato è stato letto nel task; (c) ha almeno una fonte in «Documentazione» oppure «Nessuna fonte esterna» con un motivo non vuoto, e non tutte e due; (d) ogni fonte dichiarata è stata consultata nel task; (e) «Cosa ho trovato» non è vuota. Il messaggio elenca ogni problema, con il nome della fonte o del file che manca.
4. **Cosa conta come lettura** (progetto 6).
   - **File** (`kind` `read`, `grep`, `bash_read`): `Read` del file; `Grep` in modo `content` (o senza `output_mode`, se il predefinito mostra il contenuto: B1-V1) con `path` uguale al file; in un comando Bash i file nominati da `cat`, `head`, `tail`, `less`, `sed -n`, `grep`, `rg` (best effort, `bash.read_targets`). Non contano, perché non mostrano il contenuto: `Glob`, `Grep` in modo `files_with_matches` o `count`, `wc`. Se il Task 1 (B1-V1) trova nel `tool_response` di `Grep` in modo `content` i file mostrati, contano anche quelli. Una lettura fallita non conta: né `PostToolUseFailure` di `Read` né un `post_bash` nato da `PostToolUseFailure`.
   - **Documentazione** (`kind` `fetch`, `docs`): `WebFetch` dell'URL; una chiamata di uno strumento MCP di documentazione (decisione 6) con quel `libraryId`. `WebSearch` si registra (`kind` `search`) ma non soddisfa una fonte da sola: la fonte è la pagina aperta dopo (progetto 3.3).
   - **Percorsi** normalizzati relativi al worktree del lavoro (`research.normalize_path`): un percorso fuori dal worktree, o nel checkout principale, non conta. **URL** normalizzati con `research.normalize_url`: schema e host in minuscolo, porta predefinita tolta, frammento tolto, barra finale tolta (tranne la radice), query mantenuta. Se il Task 1 (B1-V4) trova l'URL finale di un reindirizzamento nel `tool_response` di `WebFetch`, si registrano entrambi.
   Costo: una lettura fatta in una forma non riconosciuta (per esempio `python -c "open(…)"`) non conta; la nota dice quale file manca e l'implementatore lo rilegge con `Read`.
5. **A chi appartengono le letture** (progetto 3.6). Al **task**, non al singolo implementatore: `lookups` ha `work`, `task`, `agent_id` e il confronto usa tutte le letture del task, quindi un implementatore nuovo dal quarto giro eredita quelle dei giri precedenti. Una lettura con `agent_id` vale per il task del subagente (`subagents.task`), solo se è un implementatore (non in `readonly_agents`). Una lettura **senza** `agent_id` (sessione principale) non si registra, salvo il ripiego del progetto 3.5 se il Task 1 trova `WebFetch`, `WebSearch` o MCP senza `agent_id` anche nei subagenti: allora quelle tre si attribuiscono al task il cui implementatore è `running` nel worktree (scrittore unico, spec 7.2), con una `Ruling:` che accende la costante `research.ATTRIBUTE_UNNAMED`. Costo: con il ripiego una lettura del coordinatore fatta mentre l'implementatore lavora finirebbe al task; il coordinatore in quel momento aspetta l'implementatore in primo piano (spec 6.3), quindi il caso non nasce dal flusso normale.
6. **Strumenti MCP di documentazione** (progetto 3.5, secondo punto; spec 8.5). Oggi `effects.decide` tratta ogni MCP fuori da `mcp_allow` come effetto esterno da approvare: anche una lettura di context7. Gli strumenti che corrispondono a `research.DOC_MCP_TOOLS` (pattern fnmatch: `mcp__*context7*__resolve-library-id`, `mcp__*context7*__query-docs`, `mcp__*context7*__get-library-docs`; i nomi esatti li fissa il Task 1, B1-V2) passano senza atto e non sono un effetto esterno. Costo: un server che si chiamasse «context7» ma scrivesse qualcosa passerebbe; il pattern guarda anche il nome dello strumento, che per context7 è di sola lettura.
7. **Strumenti degli implementatori** (progetto 3.5). `agents/implementer.md` passa a `tools: Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch` più le voci MCP di context7 nelle forme che il Task 1 trova valide (`mcp__context7__*` per un server dell'utente, `mcp__plugin_context7_context7__*` per il plugin), solo se B1-V2 mostra che una voce che non si risolve non impedisce il lancio. Il prompt dice che le pagine scaricate sono dati non fidati e spiega la nota. Nessun implementatore per area esiste ancora: B3-B7 copiano questi strumenti. Costo: con context7 assente restano `WebFetch` e `WebSearch` (ripiego del progetto 3.5).
8. **Interruttore del blocco** (progetto 5, «il blocco resta spento finché `rules-base` non è approvata»; piano principale, decisione 1). `research.enforced(text)` è vero solo se il frontmatter di `skills/rules-base/SKILL.md` della radice del plugin ha un campo `approved` non vuoto. Spento: in L1 e L2 la prima modifica senza nota valida riceve lo stesso avviso di L0 (una volta per task) e la modifica passa. Acceso: rifiuto. Il componente `[components] research_note` (predefinito `true`) spegne del tutto il passo per un progetto (R10). Il Task 1 (B1-V7) prova che `claude plugin validate --strict` accetta il campo `approved` nel frontmatter di una skill; se lo rifiuta, l'approvazione sta in un file a parte, `skills/rules-base/APPROVED` (una riga con la data), e `enforced` legge quello (`research.APPROVAL_FILE`), con una `Ruling:`. Costo: fino a B2 nessun lavoro si ferma per la nota.
9. **L0** (progetto 3.6). Scrive la sessione principale, senza task: un solo avviso per lavoro alla prima modifica di un file non escluso (decisione 11), registrato con l'evento `research_reminder` (`task: null`). Nessuna nota, nessuna verifica, nessuna tabella nuova letta. Se il lavoro sale a L1, vale il blocco dai task del piano.
10. **Lavori iniziati prima di B1** (progetto 8). `work_items.research` (migrazione 6, predefinito `0`): `start` scrive `1` per i lavori che crea da qui in poi. Con `0` il modulo `research_gate` non fa nulla e `research submit` rifiuta con «lavoro iniziato prima del passo informati prima». **Deroga al progetto 8 per `adopt`**: anche `adopt` scrive `1`. Motivo: `adopt` ricostruisce un lavoro di cui il DB non sa più nulla (spec 12.4), quindi non c'è modo di sapere con quali regole era partito, e il ramo adottato prosegue con il codice attuale; tenerlo fuori aprirebbe una via per saltare il passo (adottare invece di avviare). Costo: un lavoro nato prima di B1 e adottato dopo riceve il passo.
11. **Quali modifiche contano** (progetto 3.1, «la prima modifica di un file in un task»). `pre_edit` su un file del worktree che non sia escluso; `pre_bash` di un implementatore con bersagli di scrittura (`bash.write_targets`) nel worktree non esclusi. **Esclusi**, per L0 come per L1 e L2: i `.md` sotto `docs/superpowers/` (`violations.is_docs_md`), `.superpowers/`, `.tollgate-run/` e le cartelle di output (`config.output_excludes`, per esempio `reports/`). Solo in fase `execution`. Costo: una scrittura che sfugge al riconoscimento di Bash passa senza nota; resta il controllo del revisore.
12. **Chi può consegnare la nota.** `research` è un sottocomando degli implementatori: `cli_calls` lo nega alla sessione principale (input senza `agent_id`) in un lavoro L1 o L2, con «la nota la scrive l'implementatore del task». Vale anche quando il programma non è certo (`_program_args` con `certain=False`) e gli argomenti cominciano con `research`, e per un comando che non si analizza e contiene la parola `research` accanto a `tollgate` (ripiego testuale, come gli altri di `cli_calls`). In L0 non serve. Costo: nessuno nel flusso normale.
13. **Revisore del task** (progetto 3.3, ultimo paragrafo). Il brief di revisione contiene il percorso della nota e il suo testo in un recinto, e dice se l'interruttore è acceso. `agents/task-reviewer.md` chiede di controllare che le fonti riguardino le librerie e i servizi toccati dal diff e che il motivo di «Nessuna fonte esterna» sia vero. **Con l'interruttore acceso**: nota mancante o non pertinente → rilievo `major` con `rule` `nota di ricerca` (un passo, non una regola `R-…`: bloccante per 8.6), `file` il percorso della nota (o il primo file del diff se manca) e `line` 1; una nota mancante è anche un `missing` di aderenza. **Con l'interruttore spento** (fino a B2): lo stesso rilievo con gravità `moderate`, che non ferma il task (piano principale, decisione 1: nessun lavoro si ferma per la nota prima di B2), e nessun `missing`. Costo: un rilievo di pertinenza in più per i task con una nota debole.
14. **Giri di correzione** (progetto 3.6). Il brief di `--fix` dice dove sta la nota già consegnata e chiede di integrarla e risottometterla solo se il giro tocca librerie o servizi nuovi. Una nota valida resta valida finché una nuova consegna non la sostituisce; una nuova consegna non valida riporta `research_ok` a `0` e la modifica successiva riceve di nuovo avviso o rifiuto. **Dopo `reopen plan`** (spec 12.3) i task si rinumerano: `scope.reset_plan` mette `lookups.task` a `NULL` per il lavoro, così le letture del vecchio task 2 non valgono per il nuovo task 2, e l'avviso «una volta per task» conta solo gli eventi `research_reminder` successivi all'ultimo `plan_reset`.
15. **Registrazione e costo degli hook.** `hooks.json` aggiunge `Read|Grep|WebFetch|WebSearch|mcp__.*` al matcher di `PostToolUse` (`Glob` no: non si registra mai). Se il Task 1 (B1-V1) conferma che gli strumenti chiamati da un subagente portano `agent_id`, `hooks/run` esce subito con 0, prima di ogni comando git, per un `PostToolUse` di `Read` o `Grep` senza `agent_id` (la sessione principale non registra letture, decisione 5): il costo per la sessione principale resta quello di una shell. Per l'implementatore ogni lettura costa un processo Python che apre il DB, carica la configurazione e il registro: il Task 1 (B1-V6) lo stima con un `PostToolUse` di Bash da subagente su un repo attivo (lo stesso percorso), il Task 4 lo rimisura con `post_lookup` vero. **Soglia: mediana oltre 300 ms** → il Task 4 toglie `Grep` dal matcher e dà a `post_lookup` una via breve nel runner (nessun `load_config` né `registry.load`: solo lavoro, task e `lookups.record`), con una `Ruling:`. Un errore nella registrazione è informativo (spec 7.1): la lettura non conta e la nota lo dirà. Costo: nessuno sulla correttezza.
16. **Eventi nuovi** (spec 18.4): `research_note` {task, ok, problems} a ogni consegna e `research_reminder` {task} a ogni avviso. Le letture non producono eventi (sarebbero troppi): la loro traccia è `lookups`, potata con la stessa soglia degli eventi (`[retention] events_days`) per i lavori chiusi, da `housekeeping.run`.
17. **Revisione 27 della spec del nucleo.** Le sezioni che il brief di scrittura nomina (7.2, 8.1, 11.4, 16) più quelle che il disegno tocca davvero: 3.2 (evento d'ingresso `post_lookup`), 7.1 (uscita anticipata di `hooks/run`), 8.5 (MCP di documentazione), 8.6 (pertinenza della nota), 12.2 (migrazione 6), 18.4 (eventi), 20. Motivo: senza, la spec direbbe che un `PostToolUse` di `Read` non esiste e che context7 è un effetto esterno.
18. **Permessi di `WebFetch` e `WebSearch` nelle sessioni vere** (corretta dalla revisione finale). In una sessione interattiva Claude Code chiede un permesso la prima volta che l'implementatore apre un dominio nuovo: il lavoro si ferma su una domanda all'utente, e questo tocca l'anti-obiettivo «passo troppo pesante». La skill `setup` aggiunge un paragrafo in parole semplici che propone **per prime le regole per dominio** (`WebFetch(domain:…)`, una per sito di documentazione) in `permissions.allow` del `.claude/settings.json` del **progetto** (gratis, valgono solo lì), e scrive in una frase il rischio di un `WebFetch` libero: può portare dati fuori nell'URL, una pagina scaricata può contenere istruzioni ostili, e tollgate non controlla `WebFetch`. Le voci globali `"WebFetch"` e `"WebSearch"` in `~/.claude/settings.json` restano una scelta dell'utente, con il rischio scritto. `setup` non scrive nessun file (come per le altre impostazioni). Le prove con `claude -p` concedono gli strumenti con `--allowedTools` e non rappresentano la domanda: il rapporto della prova reale lo dice. Costo: una domanda di permesso in più per ogni dominio nuovo non elencato.

## Review Focus

1. **Attribuzione delle letture.** Una lettura fatta da un altro task, da un altro lavoro, da un revisore di sola lettura o dalla sessione principale non deve rendere valida la nota del task. Test: Task 4 `test_read_by_other_task_not_counted`, `test_readonly_agent_reads_not_recorded`, `test_main_session_read_not_recorded`.
2. **Percorsi in forme diverse.** Lo stesso file dichiarato come assoluto nel worktree, con `./`, o letto con un percorso assoluto, deve combaciare; un percorso con `..` che esce dal worktree o che sta nel checkout principale non deve combaciare con un file del worktree. Test: Task 3 `test_normalize_path_forms`.
3. **URL in forme diverse.** Host in maiuscolo, frammento, barra finale e porta predefinita non devono rompere la corrispondenza; un percorso diverso sullo stesso host sì. Test: Task 3 `test_url_forms`.
4. **Lavori nati prima di B1 e lavori che crescono.** Un DB migrato con un lavoro in corso non riceve mai avvisi né rifiuti; un lavoro L0 avvisato che sale a L1 riceve il rifiuto (con l'interruttore acceso) al primo task. Test: Task 2 `test_migration_keeps_existing_works_outside`; Task 7 `test_legacy_work_never_reminded`, `test_l0_grown_to_l1_blocks`.
5. **Nota e giri di correzione.** Un implementatore nuovo del quarto giro con la nota valida del task non viene fermato; una nuova consegna non valida torna a fermare. Test: Task 7 `test_round4_new_implementer_keeps_valid_note`, `test_resubmitted_invalid_note_blocks_again`.

## Mappa dei file

| File | Responsabilità |
|---|---|
| `spikes/b1/run-b1-checks.sh`, `spikes/b1/probe-plugin/`, `docs/verifiche/2026-10-27-b1-verifiche.md`, `docs/verifiche/evidenze/b1/`, `spikes/fixtures/hook-inputs/samples-b1.json` | Task 1: fatti sugli strumenti per informarsi |
| `bin/tollgate_core/db.py` (migrazione 6), `bin/tollgate_core/lookups.py` (nuovo), `bin/tollgate_core/phases.py`, `bin/tollgate_core/scope.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/config.py`, `bin/tollgate_flow/start.py`, `bin/tollgate_flow/adopt.py`, `bin/tollgate_flow/housekeeping.py` | Stato |
| `bin/tollgate_analysis/research.py` (nuovo), `bin/tollgate_analysis/bash.py` | Analisi pure |
| `bin/tollgate_hooks/adapter.py`, `bin/tollgate_hooks/model.py`, `bin/tollgate_hooks/apply.py`, `bin/tollgate_checks/lookup_rec.py` (nuovo), `bin/tollgate_checks/_common.py`, `hooks/hooks.json`, `hooks/run` | Registrazione delle letture |
| `bin/tollgate_checks/effects.py`, `agents/implementer.md`, `skills/setup/SKILL.md` | Strumenti per informarsi |
| `bin/tollgate_flow/research_cmd.py` (nuovo), `bin/tollgate_core/cli.py`, `bin/tollgate_checks/cli_calls.py` | Comando `research` |
| `bin/tollgate_checks/research_gate.py` (nuovo), `tests/hookkit.py` (`plugin_root` di `Lab`) | Avviso e rifiuto alla prima modifica |
| `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py`, `bin/tollgate_checks/subagent_start.py`, `agents/task-reviewer.md` | Brief e revisore |
| `spikes/run-b1-flow.sh`, `spikes/b1/flow/`, `tests/test_b1_scripts.py`, `docs/verifiche/2026-10-27-b1-prova-flusso.md` | Prova reale |
| Spec del nucleo, piano principale di B | Task 10 |

---

### Task 1: Verifiche degli strumenti per informarsi (controller)

Il progetto 3.5 chiede di provare tre fatti prima di ogni altro codice, con i ripieghi già decisi lì. Qui servono anche le forme reali degli input degli hook, perché le funzioni dei Task 3 e 4 le leggono. Già provati e **non** da riprovare: `agent_id` presente solo nei subagenti per `Write`, `Edit`, `Skill`, `Bash` (P0, P2), `additionalContext` di `PreToolUse` e `PostToolUse` (P2, D2), `skills:` e campi ignorati dei subagenti di plugin (P0).

**Files:**
- Create: `spikes/b1/run-b1-checks.sh` (modi `controlla`, `sonda`, `latenza`, `valida`, `raccogli`), `spikes/b1/probe-plugin/` (plugin minimo: un hook che registra in JSONL l'input di `PreToolUse` e `PostToolUse` con matcher `.*`, un agente `probe:lettore` con `tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__context7__*, mcp__plugin_context7_context7__*`, una skill che lo lancia), `tests/test_b1_scripts.py` (parte del Task 1), `docs/verifiche/2026-10-27-b1-verifiche.md`, `docs/verifiche/evidenze/b1/`, `spikes/fixtures/hook-inputs/samples-b1.json`

**Chi:** un implementatore sonnet scrive script, plugin e test **senza rete e senza `claude`** (`bash -n`, `controlla` con un `claude` finto nel `PATH`); il controller esegue.

- [ ] **Step 1 (implementatore): script, sonda e test.** `sonda` lancia `claude -p --plugin-dir spikes/b1/probe-plugin --model sonnet --permission-mode acceptEdits --allowedTools "Read,Grep,Glob,Bash,Agent,Skill,Write,Edit,WebFetch,WebSearch,mcp__context7__*,mcp__plugin_context7_context7__*"` da `/tmp/tollgate-b1/probe/` (in `-p` uno strumento non concesso viene negato e non arriva a `PostToolUse`: senza la concessione la sonda misurerebbe i flag, non Claude Code; stessa forma di `spikes/run-p4-flow.sh`) (un repo git di prova con `src/app.py` e un `pyproject.toml`), con un prompt che chiede all'agente `probe:lettore` di: leggere `src/app.py` con `Read`, cercare con `Grep` in modo `content` e `files_with_matches`, elencare con `Glob`, `cat` di un file con Bash, `WebFetch` di `https://docs.python.org/3/library/tomllib.html` e di un URL che reindirizza davvero su un altro percorso (scelto dal controller con una prova a mano prima della sonda, per esempio un vecchio indirizzo della documentazione, e scritto nel rapporto; il passaggio da http a https non basta, `WebFetch` lo fa da sé), `WebSearch` di «python tomllib», una chiamata a context7 per `tomllib` se lo strumento c'è, e un comando Bash con heredoc verso `spikes/b1/probe-plugin/bin/eco` (legge stdin e lo scrive in un file). Lo script rifiuta se la cartella di lavoro non è sotto `/tmp/tollgate-b1/` o se manca `--plugin-dir`. `latenza` misura 50 invocazioni di `hooks/run PostToolUse` con un input di **Bash** da subagente (un `cat`) su un repo attivo di prova con un lavoro e un implementatore registrati (stato con la sentinella in `/tmp/tollgate-b1/state`), senza `claude`: oggi un `PostToolUse` di `Read` esce dal runner prima del DB (`adapter._kind` dà `None`), mentre quello di Bash fa tutto il percorso che `post_lookup` farà (apertura del DB, `touch`, `load_config`, registro); in più 50 invocazioni di un `Read` senza `agent_id` per il costo della sola shell. `valida` copia la sonda in `/tmp/tollgate-b1/valida/`, aggiunge `skills/rules-base/SKILL.md` con `approved: prova` nel frontmatter e lancia `claude plugin validate --strict` (non lancia il modello). Test in `tests/test_b1_scripts.py`: `test_checks_controlla_lists_steps`, `test_checks_refuses_outside_tmp`, `test_checks_requires_plugin_dir`, `test_checks_valida_uses_tmp_copy` (con un `claude` finto: la copia sta sotto `/tmp/tollgate-b1/valida/`, il comando è solo `plugin validate --strict`, nessun `-p`), `test_checks_allowed_tools` (gli argomenti registrati dal `claude` finto contengono `--permission-mode acceptEdits` e un `--allowedTools` con `WebFetch` e `WebSearch`).
- [ ] **Step 2 (controller): verifiche.**

| Id | Fatto da provare | Dove incide |
|---|---|---|
| B1-V1 | `tool_input` e `tool_response` reali di `PreToolUse` e `PostToolUse` per `Read`, `Grep` (`content` e `files_with_matches`), `Glob`, `WebFetch`, `WebSearch`, Bash con `cat`, chiamati dal subagente del plugin: presenza di `agent_id` e `agent_type` su ognuno; file mostrati da `Grep` nel `tool_response`; `Read` di un file assente (arriva come `PostToolUseFailure`?) | Decisioni 4, 5, 15; Task 4 |
| B1-V2 | context7 da un subagente di plugin: le voci MCP in `tools` sono accettate, con quale nome dello strumento; una voce che non si risolve non impedisce il lancio; i parametri reali (`libraryId` o altro) di `query-docs`/`get-library-docs`; se il server chiede l'autenticazione (nella sessione dell'utente del 27/10 il plugin context7 espone solo `authenticate` e `complete_authentication`) | Decisioni 6, 7; ripiego del progetto 3.5 |
| B1-V3 | `PreToolUse` di uno strumento MCP chiamato dal subagente: porta `agent_id`; con tollgate attivo oggi verrebbe negato come effetto esterno (dalla lettura di `bin/tollgate_checks/effects.py`, confermata con una prova a secco di `hooks/run`, senza `claude`) | Decisione 6 |
| B1-V4 | `WebFetch` con reindirizzamento su un altro percorso: il `tool_response` (letto da `event.raw`, perché l'adattatore scarta un `tool_response` che non è un oggetto) porta l'URL finale? `WebSearch`: il `tool_response` porta gli URL dei risultati? | Decisione 4 |
| B1-V5 | Un comando Bash con heredoc verso un programma che legge stdin, dal subagente: passa intatto (nessuna richiesta di permesso in `-p`, testo integro) | Decisione 1 |
| B1-V6 | Latenza di `hooks/run` per un `PostToolUse` di Bash da subagente su un repo attivo, stima del costo di `post_lookup` (mediana e 95° percentile su 50), e per un `Read` senza `agent_id` | Decisione 15 (soglia 300 ms) |
| B1-V7 | `claude plugin validate --strict` accetta il campo `approved` nel frontmatter di una skill | Decisione 8 |

- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-27-b1-verifiche.md`: tabella `Id | Fatto | Esito | Evidenza | Conseguenza per il piano`, con `claude --version`. I campioni anonimizzati (senza percorsi della `HOME`, senza ambiente) vanno in `spikes/fixtures/hook-inputs/samples-b1.json`, con chiavi `read`, `grep_content`, `grep_files`, `glob`, `bash_cat`, `webfetch`, `webfetch_redirect`, `websearch`, `mcp_docs` (assente se B1-V2 non lo ottiene), ognuna con `pre` e `post`. Un fatto non ottenuto si scrive «non determinato» con la causa.
- [ ] **Step 4: Ruling.** Gli esiti scelgono i ripieghi del progetto 3.5, e il disegno dei task successivi dipende da loro così:
  - B1-V1 senza `agent_id` su `WebFetch`, `WebSearch` o MCP → `research.ATTRIBUTE_UNNAMED = True` (Task 3) e il ramo del ripiego nel Task 4; senza `agent_id` anche su `Read` → niente uscita anticipata in `hooks/run` (decisione 15) e la stessa attribuzione per tutte le letture;
  - B1-V2 negativo (context7 non usabile o con autenticazione) → nel Task 5 nessuna voce MCP in `tools`; `DOC_MCP_TOOLS` resta (non nuoce) e la forma `context7:` della nota resta accettata;
  - nessuna lettura registrabile in nessun modo → il Task 6 confronta la sola forma della nota (decisione 3 senza (b) e (d)), il Task 4 si riduce all'evento d'ingresso, e il rapporto lo dice in chiaro (progetto 3.5, terzo ripiego);
  - B1-V5 negativo → il Task 6 accetta anche `--file <percorso>` con un file sotto `/tmp`, e il Task 7 esenta dal conteggio delle modifiche il solo file nominato.
  - B1-V6 con mediana oltre 300 ms → la via breve di `post_lookup` e `Grep` fuori dal matcher (decisione 15) entrano nel Task 4;
  - B1-V7 negativo → `research.APPROVAL_FILE` (decisione 8) nel Task 3 e nel Task 9;
  - **un esito ottenuto con lo strumento negato** (un permesso mancante nella sonda, non un comportamento di Claude Code) è «non determinato», non negativo: si corregge la sonda e si ripete, nel tetto di 3 esecuzioni.
  Ogni scelta è una riga `Ruling:` nel registro, prima del Task 2.
- [ ] **Step 5: Commit** «tollgate B1: verifiche degli strumenti per informarsi».

---

### Task 2: Stato: migrazione 6, letture, lavori nati prima di B1

**Files:**
- Modify: `bin/tollgate_core/db.py` (`SCHEMA_V6`, `MIGRATIONS`), `bin/tollgate_core/phases.py` (`create_work`), `bin/tollgate_core/scope.py` (`reset_plan`), `bin/tollgate_core/events.py` (`EVENT_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["components"]`), `bin/tollgate_flow/start.py`, `bin/tollgate_flow/adopt.py`, `bin/tollgate_flow/housekeeping.py`
- Create: `bin/tollgate_core/lookups.py`, `tests/test_lookups.py`
- Test: `tests/test_db.py`, `tests/test_phases.py`, `tests/test_scope.py`, `tests/test_start.py` (anche `housekeeping`), `tests/test_adopt.py`

**Interfaces:**
- Produces:
  - `SCHEMA_V6`: tabella `lookups (id INTEGER PRIMARY KEY AUTOINCREMENT, work INTEGER NOT NULL, task INTEGER, agent_id TEXT, session TEXT, kind TEXT NOT NULL CHECK (kind IN ('read','grep','bash_read','fetch','search','docs')), target TEXT NOT NULL, at TEXT NOT NULL)` con indice `lookups_task(work, task)`; `tasks.research_note TEXT`; `tasks.research_ok INTEGER NOT NULL DEFAULT 0`; `work_items.research INTEGER NOT NULL DEFAULT 0`.
  - `lookups.KINDS`; `lookups.record(conn, *, work: int, task: int | None, agent_id: str | None, session: str | None, kind: str, target: str, now) -> None` (`ValueError` per un `kind` fuori elenco o un `target` vuoto); `lookups.for_task(conn, work: int, task: int) -> list[Lookup]` con `Lookup(kind: str, target: str)` (`NamedTuple`), in ordine di registrazione, senza doppioni; `lookups.set_note(conn, work: int, task: int, *, text: str, ok: bool) -> None`; `lookups.note(conn, work: int, task: int) -> tuple[str | None, bool]`; `lookups.prune(conn, *, now, days: int) -> int` (cancella le righe dei lavori chiusi da più di `days` giorni; la chiama `housekeeping.run` con `[retention] events_days`).
  - `scope.reset_plan` mette `lookups.task = NULL` per il lavoro (decisione 14).
  - `phases.create_work(..., research: bool = False)` scrive `work_items.research`; `start` e `adopt` passano `research=True`.
  - `EVENT_TYPES` con `research_note` e `research_reminder`; `DEFAULTS["components"]["research_note"] = True`.

- [ ] **Step 1: Test** `test_lookups.py`: `test_record_and_for_task` (due letture dello stesso task in ordine, una di un altro task esclusa); `test_for_task_without_duplicates` (stessa coppia `kind`, `target` due volte → una); `test_unknown_kind_rejected`; `test_empty_target_rejected`; `test_set_note_roundtrip` (`note` restituisce testo ed esito; una seconda `set_note` con `ok=False` sostituisce). `test_db.py`: `test_migration_6_columns` (colonne e indice dopo `open_db`); `test_migration_keeps_existing_works_outside` (Review Focus 4: un DB alla versione 5 con un lavoro in `execution` e un task `running`, aperto con il codice nuovo, ha `research = 0` per quel lavoro e `research_ok = 0`, e la copia `migrazione-6` esiste); il test esistente `test_db.py` che controlla `latest_version() == 5` passa a 6. `test_scope.py::test_reset_plan_drops_task_lookups` (dopo `reset_plan` `for_task` del vecchio numero è vuota). `test_start.py::test_prune_lookups_of_closed_works` (righe di un lavoro chiuso oltre la soglia cancellate, quelle di un lavoro attivo no). `test_phases.py`: `test_create_work_research_flag` (predefinito `0`, `research=True` → `1`). `test_start.py::test_new_work_has_research_on` e `test_adopt.py::test_adopted_work_has_research_on` (dal programma vero, come i test esistenti dei due file). `test_config.py::test_research_note_component_default_true`.
- [ ] **Step 2: Esegui i test nuovi** e controlla che falliscano per l'assenza di `lookups`, della migrazione e del parametro.
- [ ] **Step 3: Implementa** migrazione, modulo `lookups`, parametro di `create_work`, chiamate di `start` e `adopt`, eventi e componente. `lookups.record` scrive con la sua transazione (vincolo (1) di P1).
- [ ] **Step 4: `tests/run`** verde su python3.11 e python3.
- [ ] **Step 5: Commit** «tollgate B1: migrazione 6, letture registrate, lavori nati prima del passo».

---

### Task 3: Analisi pure: nota di ricerca, percorsi, URL, letture da Bash

**Files:**
- Create: `bin/tollgate_analysis/research.py`, `tests/test_research.py`
- Modify: `bin/tollgate_analysis/bash.py` (`read_targets`), `tests/test_bash.py`

**Interfaces:**
- Consumes: i campioni `spikes/fixtures/hook-inputs/samples-b1.json` e le `Ruling:` del Task 1.
- Produces (tutto puro, nessun import di tollgate fuori da `tollgate_analysis`):
  - `RULES_BASE = "skills/rules-base/SKILL.md"`; `enforced(skill_text: str | None) -> bool` (decisione 8: frontmatter tra `---` iniziali con `approved:` non vuoto; `None`, testo senza frontmatter o campo vuoto → `False`); `APPROVAL_FILE = "skills/rules-base/APPROVED"` solo se B1-V7 lo impone (allora `enforced` riceve il testo di quel file: vero se non vuoto).
  - `HEREDOC_END = "NOTA_DI_RICERCA_FINE"` e `submit_command(program: str, task: int) -> str` (il comando completo con `<<'NOTA_DI_RICERCA_FINE'`, le quattro intestazioni di sezione e il delimitatore finale: lo usano brief e rifiuto).
  - `ATTRIBUTE_UNNAMED: bool` (valore dalla `Ruling:` del Task 1; predefinito `False`).
  - `DOC_MCP_TOOLS: tuple[str, ...]` (decisione 6) e `is_doc_tool(name: str) -> bool`; `doc_library(tool_input: dict) -> str | None` (il `libraryId` della chiamata, con il nome del parametro fissato dal Task 1).
  - `normalize_url(url: str) -> str | None` (decisione 4; `None` per uno schema diverso da `http`/`https` o un URL senza host).
  - `normalize_path(path: str, *, cwd: str, worktree: str) -> str | None` (percorso relativo POSIX al worktree, `None` se fuori; `~` non espanso: un percorso con `~` è `None`).
  - `Note(files: list[str], sources: list[Source], no_external: str | None, findings: str, problems: list[str])` con `Source(ref: str, kind: str, text: str)`, `kind` in `url`, `context7`; `parse_note(text: str) -> Note` (decisione 2; i problemi di forma stanno in `problems`, mai un'eccezione).
  - `check_note(note: Note, lookups: list[tuple[str, str]], *, worktree: str) -> list[str]` (decisione 3; `lookups` sono coppie `(kind, target)` già normalizzate; lista vuota = valida; i file dichiarati si normalizzano con `cwd = worktree`).
  - In `bash.py`: `read_targets(c: Cmd) -> list[str]` (decisione 4: argomenti non opzione di `cat`, `head`, `tail`, `less`, `sed -n`, e dopo il pattern per `grep` e `rg`; nient'altro, `wc` compreso).

- [ ] **Step 1: Test** `test_research.py`:
  - `test_enforced` (`approved: 2026-11-02` vero; `approved:` vuoto, frontmatter assente, `None` falsi; `approved` nel corpo e non nel frontmatter falso);
  - `test_url_forms` (Review Focus 3: `HTTPS://Docs.Python.org:443/3/library/tomllib.html#module-tomllib` e `https://docs.python.org/3/library/tomllib.html/` danno `https://docs.python.org/3/library/tomllib.html`; `https://docs.python.org/3/library/json.html` diverso; `?v=2` mantenuto; `ftp://x` e `file:///etc/passwd` → `None`);
  - `test_normalize_path_forms` (Review Focus 2: con `worktree = "/w"` e `cwd = "/w/src"`, `app.py`, `./app.py`, `/w/src/app.py` → `src/app.py`; `../../etc/passwd` → `None`; `/main/src/app.py` (checkout principale) → `None`; `~/x` → `None`);
  - `test_parse_note_complete` (nota con le tre sezioni, due file, una fonte URL e una `context7:/python/cpython`, findings di due righe: campi giusti, `problems == []`);
  - `test_parse_note_separators` (` — ` e ` - ` entrambi accettati come separatore della descrizione);
  - `test_parse_note_missing_sections` (senza «Letto nel progetto» o senza «Cosa ho trovato» → un problema che nomina la sezione);
  - `test_parse_note_both_sources_and_none` (fonti e «Nessuna fonte esterna» insieme → problema);
  - `test_parse_note_too_long` (oltre 8.000 caratteri → problema «nota oltre 8000 caratteri»);
  - `test_check_note_valid` (letture `read src/app.py` e `fetch <url>` → `[]`);
  - `test_check_note_source_not_read` (fonte dichiarata senza `fetch` → un problema che contiene l'URL normalizzato);
  - `test_check_note_file_not_read` (file dichiarato senza `read`, `grep` né `bash_read` → problema con il percorso);
  - `test_check_note_glob_does_not_count` (una lettura di tipo diverso dai tre di file, per esempio `search`, non basta);
  - `test_check_note_no_external_without_reason` (sezione presente e motivo vuoto → problema; con motivo e un file letto → `[]`);
  - `test_check_note_context7` (`context7:/python/cpython` con `docs /python/cpython` → `[]`; senza → problema);
  - `test_search_alone_not_a_source` (`search tomllib` senza `fetch` dell'URL dichiarato → problema);
  - `test_doc_tools` (i nomi di context7 trovati dal Task 1 → `True`; `mcp__github__create_issue` → `False`);
  - `test_doc_library` (dai campioni `mcp_docs` del Task 1, se presenti); `test_submit_command_quotes_delimiter` (il comando contiene `<<'NOTA_DI_RICERCA_FINE'` tra apici, termina con la riga del delimitatore e non contiene `TOLLGATE_`).
  `test_bash.py::test_read_targets` (`cat a b` → `a`, `b`; `sed -n 1,20p f` → `f`; `sed -i s/x/y/ f` → `[]`; `grep -n foo src/a.py` → `src/a.py`; `rg foo` → `[]`; `head -n 5 f` → `f`; `wc -l f` → `[]`; `echo f` → `[]`).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** `research.py` e `read_targets`. Le espressioni e i nomi delle sezioni sono costanti del modulo (`SECTION_FILES = "Letto nel progetto"`, `SECTION_DOCS = "Documentazione"`, `SECTION_FOUND = "Cosa ho trovato"`, `SECTION_NONE = "Nessuna fonte esterna"`, `MAX_NOTE_CHARS = 8000`): i testi dei brief e dei rifiuti dei Task 6-8 le importano.
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: analisi della nota di ricerca».

---

### Task 4: Registrazione delle letture dagli hook

**Files:**
- Modify: `bin/tollgate_hooks/model.py` (`INPUT_EVENTS`), `bin/tollgate_hooks/adapter.py` (`_kind`), `bin/tollgate_hooks/apply.py` (operazione `lookup`), `bin/tollgate_checks/_common.py` (`lookup_owner`), `hooks/hooks.json`, `hooks/run`
- Create: `bin/tollgate_checks/lookup_rec.py`, `tests/test_check_lookups.py`
- Test: `tests/test_hook_engine.py` (adattatore e operazioni), `tests/test_check_audit_round.py` (il conteggio di `apply.OPS`, oggi 28), `tests/test_wrapper.py` (`hooks/run`), `tests/test_manifest.py` (`hooks.json`)

**Interfaces:**
- Consumes: `lookups.record` (Task 2); `research.normalize_path`, `normalize_url`, `is_doc_tool`, `doc_library`, `ATTRIBUTE_UNNAMED`, `bash.read_targets` (Task 3).
- Produces:
  - evento d'ingresso `post_lookup`: `adapter._kind("PostToolUse", t)` lo restituisce per `Read`, `Grep`, `WebFetch`, `WebSearch` e per ogni `mcp__…` (non per `Glob`) (il modulo decide se è di documentazione); `PostToolUseFailure` non lo produce (una lettura fallita non conta);
  - operazione `record("lookup", work=, task=, agent_id=, kind=, target=)` (`apply.OPS` passa a 29);
  - `_common.lookup_owner(ctx, event) -> tuple[int, int] | None` (decisione 5: `(work, task)` dal subagente implementatore con un task; con `ATTRIBUTE_UNNAMED` e senza `agent_id`, solo per `WebFetch`, `WebSearch` e MCP, il task dell'implementatore `running` del lavoro che governa il `cwd`; altrimenti `None`);
  - modulo `tollgate_checks.lookup_rec`, `CHECK = {"api": 1, "events": ["post_lookup", "post_bash"], "component": "research_note", "order": 40}`: per `post_lookup` registra secondo la decisione 4 (`Grep` solo in modo `content` con `path` che è un file, più i file mostrati se il Task 1 li ha trovati; `WebFetch` con l'URL e l'eventuale URL finale letto da `event.raw`; `WebSearch` con la query come `target` e `kind` `search`; MCP di documentazione con `docs` e il `libraryId`); per `post_bash` registra i `read_targets` di ogni comando come `bash_read`, ma non se `event.hook_event == "PostToolUseFailure"`; solo per i lavori con `research = 1`.
  - `hooks.json`: matcher di `PostToolUse` `Edit|Write|MultiEdit|NotebookEdit|Bash|Agent|Skill|SubagentHandback|Read|Grep|WebFetch|WebSearch|mcp__.*` (senza `Grep` se scatta la soglia della decisione 15).
  - `hooks/run`: per `PostToolUse` con `tool_name` in `Read`, `Grep` e senza `agent_id` esce con 0 prima del controllo del repo attivo (decisione 15; solo se il Task 1 lo permette).
  - con la soglia della decisione 15 superata: la via breve di `post_lookup` nel runner (nessun `load_config` né `registry.load`), con il test `test_post_lookup_short_path_skips_config`.

- [ ] **Step 1: Test** `test_check_lookups.py` (con `tests/hookkit.py` e i campioni del Task 1, forma degli input uguale a quella reale):
  - `test_read_recorded_for_task` (implementatore del task 1 legge `src/app.py` → `lookups` ha `read src/app.py` per il task 1);
  - `test_read_by_other_task_not_counted` (Review Focus 1: implementatore del task 2 legge lo stesso file → il task 1 non lo ha);
  - `test_readonly_agent_reads_not_recorded` (un `tollgate:task-reviewer` legge → nessuna riga);
  - `test_main_session_read_not_recorded` (nessun `agent_id` → nessuna riga; con `ATTRIBUTE_UNNAMED` vero resta nessuna riga per `Read`);
  - `test_webfetch_recorded_normalized` (URL con frammento → riga `fetch` normalizzata; con l'URL finale nel `tool_response`, se B1-V4 l'ha trovato, due righe);
  - `test_websearch_is_search_only`;
  - `test_grep_on_file_recorded` (modo `content`); `test_grep_files_with_matches_not_recorded`;
  - `test_doc_mcp_recorded` (se B1-V2 ha dato un campione);
  - `test_bash_cat_recorded` (`post_bash` con `cat src/app.py` dall'implementatore → `bash_read src/app.py`); `test_failed_bash_cat_not_recorded` (lo stesso da `PostToolUseFailure` → nessuna riga);
  - `test_read_outside_worktree_not_recorded` (percorso nel checkout principale → nessuna riga);
  - `test_legacy_work_not_recorded` (`research = 0` → nessuna riga);
  - `test_unnamed_fetch_attributed_when_enabled` (solo con `ATTRIBUTE_UNNAMED`: `WebFetch` senza `agent_id` mentre l'implementatore del task 1 è `running` → riga del task 1; senza implementatore `running` → nessuna);
  - `test_failed_read_not_recorded` (`PostToolUseFailure` di `Read` → nessun evento d'ingresso).
  `test_hook_engine.py::test_post_lookup_kinds` (con `Glob` → nessun evento), `test_hook_engine.py::test_lookup_op`; il conteggio in `test_check_audit_round.py` passa a 29; `test_manifest.py::test_post_tool_use_matcher_has_lookups`; `test_wrapper.py::test_main_session_read_exits_early` (con uno stato che fallirebbe se Python partisse: nessuna riga in `hooks.log`, uscita 0) e `test_subagent_read_reaches_python`.
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** evento, adattatore, modulo, operazione, matcher e uscita anticipata. Nel wrapper l'uscita anticipata legge `tool_name` e `agent_id` con `json_str`, come il ramo di `UserPromptSubmit`.
- [ ] **Step 4: `tests/run`** verde, e la misura della decisione 15 ripetuta con un `PostToolUse` di `Read` vero da subagente (50 invocazioni, mediana e 95° percentile nel report del task); con una mediana oltre 300 ms si applica la stessa conseguenza della decisione 15 (via breve, `Grep` fuori dal matcher), con una `Ruling:` e un giro di questo task.
- [ ] **Step 5: Commit** «tollgate B1: letture registrate dagli hook».

---

### Task 5: Strumenti per informarsi: MCP di documentazione e implementatore

**Files:**
- Modify: `bin/tollgate_checks/effects.py`, `agents/implementer.md`, `skills/setup/SKILL.md`
- Test: `tests/test_check_effects.py`, `tests/test_manifest.py` (frontmatter degli agenti; il test esistente con l'elenco esatto degli strumenti di `implementer.md` si aggiorna), `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `research.is_doc_tool` (Task 3); esiti B1-V2 e B1-V3.
- Produces: `effects.decide` per `pre_mcp` restituisce `[]` per uno strumento di documentazione, prima di `mcp_allow`; frontmatter di `implementer.md` con gli strumenti della decisione 7; paragrafo della skill `setup` sui permessi di `WebFetch` e `WebSearch` (decisione 18).

- [ ] **Step 1: Test** `test_check_effects.py`: `test_doc_mcp_not_an_effect` (il nome di context7 del Task 1 → nessun `deny`, nessun `effect_request`); `test_other_mcp_still_effect` (`mcp__github__create_issue` → `deny` con «strumento MCP non in mcp_allow», come oggi). `test_manifest.py`: `test_implementer_tools` (contiene `WebFetch` e `WebSearch`; le voci MCP solo se la `Ruling:` del Task 1 le ammette; nessun `Agent`); `test_implementer_mentions_untrusted_pages` (il corpo contiene la frase sulle pagine scaricate come dati non fidati, la stessa di `agents/spec-auditor.md`); `test_implementer_mentions_research_submit` (il corpo nomina `research submit` e le quattro sezioni della nota, prese dalle costanti di `research.py`). `test_skill_contract.py::test_setup_proposes_web_permissions` (il testo di `setup` nomina `permissions.allow`, `WebFetch` e `WebSearch` e dice che l'utente le aggiunge da sé).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa.** In `implementer.md` una sezione «Informati prima di scrivere», dopo «Prima di cominciare»: leggi i file che tocchi e quelli che li chiamano; prendi le versioni dal file delle dipendenze; per ogni libreria o servizio esterno apri la documentazione ufficiale con `WebFetch` (o context7, se c'è); poi consegna la nota con il comando del brief, con il formato della decisione 2; in L0 non c'è nota. `claude plugin validate --strict` deve restare verde.
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: strumenti per informarsi agli implementatori».

---

### Task 6: Comando `research`

**Files:**
- Create: `bin/tollgate_flow/research_cmd.py`, `tests/test_research_cmd.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando), `bin/tollgate_checks/cli_calls.py` (decisione 12)
- Test: `tests/test_check_cli_calls.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `lookups.for_task`, `lookups.set_note` (Task 2); `research.parse_note`, `check_note`, costanti (Task 3).
- Produces:
  - `tollgate_flow.research_cmd.submit(state, cwd: Path, number: int, text: str, *, now=None) -> SubmitResult` con `SubmitResult(code: int, lines: list[str], path: Path | None)`, codici `OK` 0 (nota valida), `INVALID` 1 (nota salvata ma non valida, `lines` elenca i problemi), `REFUSED` 2 (nessun lavoro per la cartella, fase diversa da `execution`, L0, lavoro con `research = 0`, task inesistente o non `running`);
  - `tollgate_flow.research_cmd.show(state, cwd: Path, number: int) -> SubmitResult` (stampa la nota salvata e l'esito; `REFUSED` se non c'è);
  - CLI `research submit <k>` (testo da stdin) e `research show <k>`;
  - file `.tollgate-run/<N>/research-<k>.md` con la nota così com'è e una riga finale `esito: valida|non valida`;
  - evento `research_note` {task, ok, problems} a ogni consegna.

- [ ] **Step 1: Test** `test_research_cmd.py` (repo e lavoro da `tests/flowkit.py`, letture scritte con `lookups.record`):
  - `test_submit_valid_note` (uscita 0, `tasks.research_ok = 1`, file scritto, evento con `ok: true`);
  - `test_submit_invalid_lists_problems` (fonte non consultata → uscita 1, la riga del problema nomina l'URL, `research_ok = 0`, nota salvata lo stesso);
  - `test_resubmit_replaces` (valida poi non valida → `research_ok = 0`);
  - `test_refused_in_l0`, `test_refused_outside_execution`, `test_refused_legacy_work` (testo «lavoro iniziato prima del passo informati prima»), `test_refused_task_not_running`;
  - `test_lookups_of_previous_round_count` (letture con `agent_id` diverso dello stesso task contano, progetto 3.6);
  - `test_show_prints_note_and_outcome`.
  `test_cli.py::test_research_submit_reads_stdin`. `test_check_cli_calls.py::test_research_denied_to_main_session_in_l1` (input senza `agent_id`, lavoro L1 → `deny` con «la nota la scrive l'implementatore del task») e `test_research_allowed_to_implementer`; `test_research_uncertain_program_denied_to_main_session` (programma come espansione `$p research submit 1`) e `test_unparseable_research_denied_to_main_session` (decisione 12); `test_heredoc_research_passes_bash_rules` (il comando di `research.submit_command` dell'implementatore, con una nota che contiene backtick e una riga `EOF`, non riceve `deny` da nessun modulo, con `hooks/run` vero, e la nota arriva intera alla CLI).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** `research_cmd.py` (lavoro dalla cartella con `sessions.work_for_path`, come `taskcmd`), il sottocomando e la regola di `cli_calls`. Il file della nota si scrive con lo stesso schema atomico di `apply._write_atomic`.
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: comando research per la nota di ricerca».

---

### Task 7: Avviso e rifiuto alla prima modifica

**Files:**
- Create: `bin/tollgate_checks/research_gate.py`, `tests/test_check_research_gate.py`
- Modify: `tests/hookkit.py` (`Lab(..., plugin_root=ROOT)`: parametro nuovo, predefinito invariato)

**Interfaces:**
- Consumes: `research.enforced`, `RULES_BASE`, costanti di sezione (Task 3); `tasks.research_ok`, `work_items.research` (Task 2); `ctx.plugin_root`.
- Produces: modulo con `CHECK = {"api": 1, "events": ["pre_edit", "pre_bash"], "component": "research_note", "order": 25}` e `decide(event, ctx)`:
  - nessuna decisione se il lavoro che governa il bersaglio non c'è, ha `research = 0`, non è in `execution`, o il bersaglio è escluso (decisione 11, le stesse esclusioni per L0, L1 e L2);
  - L0, sessione principale: alla prima modifica del lavoro `inject` dell'avviso più `record("event", type="research_reminder", data={"task": None}, work=…)`; nessuna decisione se un `research_reminder` del lavoro esiste già;
  - L1 e L2, implementatore del task (`subagents.task`): nessuna decisione con `research_ok = 1`; altrimenti, con `enforced(<radice del plugin>/RULES_BASE)` vero, `deny` con il testo del rifiuto; con l'interruttore spento `inject` dell'avviso e `research_reminder` {task}, una volta per task (contando solo gli eventi successivi all'ultimo `plan_reset` del lavoro, decisione 14);
  - `pre_bash`: solo per un implementatore e solo se `bash.write_targets` ha un bersaglio nel worktree non escluso.
  - Testo del rifiuto: comincia con «nota di ricerca mancante o non valida per il task <k>», contiene il comando di `research.submit_command(<program_command>, k)` e il rimando ai problemi della consegna precedente (letti da `research_note` più recente, se c'è). Testo dell'avviso: comincia con «tollgate: informati prima di modificare».

- [ ] **Step 1: Test** `test_check_research_gate.py` (con `tests/hookkit.py`; l'interruttore si prova con il parametro nuovo `Lab(plugin_root=…)` puntato a una copia temporanea della radice del plugin (`bin/` compreso, perché `ctx.plugin_bin` e il riconoscimento del programma in `cli_calls` ed `effects` dipendono da lì) che contiene una `skills/rules-base/SKILL.md` con o senza `approved`):
  - `test_l1_without_note_denied_when_enforced` (progetto 7: «nota mancante: L1 nega»);
  - `test_l1_without_note_warned_when_not_enforced` (avviso, nessun `deny`, una volta per task: la seconda modifica non riceve l'avviso);
  - `test_l0_warns_once` (progetto 7: «nota mancante: L0 avvisa»; la seconda modifica nessuna decisione);
  - `test_valid_note_passes` (progetto 7: «nota valida: la modifica passa»);
  - `test_invalid_note_denied_with_problems` (progetto 7: «fonte dichiarata ma non letta» e «nessuna fonte esterna senza motivo» → il rifiuto riporta i problemi della consegna);
  - `test_docs_and_run_files_exempt` (`docs/superpowers/plans/x.md`, `.tollgate-run/1/x`, `.superpowers/x`, `reports/junit.xml` → nessuna decisione, in L0 e in L1);
  - `test_reminder_again_after_plan_reset` (avviso al task 1, `reopen plan` e nuovo task 1 → nuovo avviso);
  - `test_legacy_work_never_reminded` (Review Focus 4);
  - `test_l0_grown_to_l1_blocks` (Review Focus 4: lavoro L0 avvisato, `set_level` a L1 e piano registrato con un task `running`, interruttore acceso → `deny`);
  - `test_round4_new_implementer_keeps_valid_note` (Review Focus 5);
  - `test_resubmitted_invalid_note_blocks_again` (Review Focus 5);
  - `test_bash_write_by_implementer_denied` (`sed -i` su `src/app.py` senza nota, interruttore acceso → `deny`); `test_bash_read_not_denied` (`cat src/app.py` → nessuna decisione);
  - `test_component_off` (`[components] research_note = false` → nessuna decisione);
  - `test_scope_denial_wins` (file fuori scope: il primo `deny` resta quello di `writes`, ordine 20 prima di 25).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** il modulo. Il testo di `enforced` si legge da `ctx.plugin_root / research.RULES_BASE` (assente → spento).
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: avviso e rifiuto alla prima modifica senza nota».

---

### Task 8: Brief dell'implementatore e del revisore

**Files:**
- Modify: `bin/tollgate_analysis/brief.py` (`ImplBrief`, `ReviewBrief`, `implementer_brief`, `review_brief`), `bin/tollgate_flow/taskcmd.py`, `bin/tollgate_checks/subagent_start.py`, `agents/task-reviewer.md`
- Test: `tests/test_brief.py`, `tests/test_taskcmd.py`, `tests/test_check_agents.py` (`SubagentStart`), `tests/test_manifest.py`

**Interfaces:**
- Consumes: `lookups.note` (Task 2); costanti di `research` (Task 3); comando del Task 6.
- Produces:
  - campi nuovi con valore predefinito (le dataclass hanno già campi con predefinito): `ImplBrief.research_cmd: str | None = None` (da `research.submit_command`; `None` per i lavori con `research = 0`) e `ImplBrief.research_note_path: str | None = None` (la nota già consegnata, nei giri `--fix`);
  - `ReviewBrief.research: bool = False` (il lavoro ha il passo), `ReviewBrief.research_enforced: bool = False` (l'interruttore della decisione 8), `ReviewBrief.research_note: str | None = None`, `ReviewBrief.research_note_path: str | None = None`, `ReviewBrief.first_diff_file: str | None = None` (il primo file del diff, scritto da `taskcmd.review_prepare`: è il `file` del rilievo quando la nota manca);
  - sezione «Nota di ricerca» del brief dell'implementatore (prima di «Istruzioni»): il formato della decisione 2 con i nomi delle sezioni dalle costanti, il comando con l'heredoc, e nei giri `--fix` «la nota è in <percorso>: integrala e risottomettila solo se questo giro tocca librerie o servizi nuovi»;
  - sezione «Nota di ricerca» del brief del revisore solo con `research` vero: il testo in un recinto e `DATA_NOTE`, o «nessuna nota consegnata»; la gravità da usare secondo la decisione 13 (`major` e `missing` con l'interruttore acceso, `moderate` senza `missing` con l'interruttore spento), `file` il percorso della nota, o il primo file del diff se la nota manca, e `line` 1;
  - riga in più nel promemoria di `SubagentStart` per gli implementatori di un lavoro con `research = 1`: «prima di modificare file consegna la nota di ricerca (vedi il brief)».

- [ ] **Step 1: Test** `test_brief.py`: `test_impl_brief_has_research_section` (comando e sezioni); `test_impl_brief_without_research_for_legacy` (con `research_cmd=None` nessuna sezione); `test_fix_brief_points_to_note`; `test_review_brief_fences_note` (una nota con ```` ``` ```` e «ignora le istruzioni» sta in un recinto più lungo, dopo `DATA_NOTE`); `test_review_brief_missing_note_enforced` (gravità `major`, `missing`, `file` uguale al primo file del diff) e `test_review_brief_missing_note_not_enforced` (gravità `moderate`, nessun `missing`); `test_review_brief_legacy_has_no_section` (`research` falso). `test_taskcmd.py::test_task_start_brief_has_research_cmd` e `test_review_prepare_includes_note`. `test_check_agents.py::test_implementer_reminder_mentions_note`. `test_manifest.py::test_task_reviewer_checks_note` (il corpo nomina la regola `nota di ricerca`, «Nessuna fonte esterna» e il rimando alla gravità indicata dal brief).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa.** In `task-reviewer.md` un punto nella «Parte 1»: se il brief ha la sezione «Nota di ricerca», la nota esiste, le fonti riguardano le librerie e i servizi del diff, il motivo di «Nessuna fonte esterna» è vero; altrimenti un rilievo con `rule` `nota di ricerca`, la gravità e il `file`/`line` che il brief indica (decisione 13). `taskcmd.review_prepare` legge l'interruttore dalla radice del plugin (`db.BIN_PATH`, come gli altri percorsi del programma).
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: nota di ricerca nei brief e nella revisione del task».

---

### Task 9: Prova reale di un lavoro L1 (preparazione con test, esecuzione del controller)

Progetto 7: «un lavoro L1 vero su un progetto di prova, dove l'implementatore si informa, scrive la nota e lavora, con le evidenze come nelle prove reali del nucleo». Modello: `spikes/run-p4-flow.sh` e `spikes/run-p3a-flow.sh`, senza GitHub: `gh` finto (`tests/fakegh.py`), `origin` nudo locale.

**Files:**
- Create: `spikes/run-b1-flow.sh` (modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`), `spikes/b1/flow/` (progetto di prova: un pacchetto Python minimo con `unittest`, `tollgate.toml`, i file del gate finti come in `tests/flowkit.py`, issue #1 nei dati del `gh` finto: «leggi la configurazione da `config.toml` con `tomllib` e restituisci il valore di `[app] nome`; prima di scrivere controlla sulla documentazione ufficiale di Python come si apre il file per `tomllib.load` e da quale versione esiste il modulo, e cita la pagina», piano L1 con un task, come testo che il modello scrive), `docs/verifiche/2026-10-27-b1-prova-flusso.md`, `docs/verifiche/evidenze/b1/flusso/`
- Modify: `tests/test_b1_scripts.py`

- [ ] **Step 1 (implementatore, senza rete e senza `claude`): lo script.** `prepara` copia il plugin in `/tmp/tollgate-b1/plugin/` e aggiunge **solo nella copia** `skills/rules-base/SKILL.md` di prova (frontmatter `name: rules-base`, `approved: prova-b1`, corpo «Regole di prova della prova reale di B1: non sono le regole di B2»), così l'interruttore è acceso (decisione 8); crea il progetto in `/tmp/tollgate-b1/flow/`, lo stato con la sentinella in `/tmp/tollgate-b1/state`, il `gh` finto nel `PATH`. `passo1`: `claude -p "/tollgate:start #1 L1"` dal checkout. `passo2`: dal worktree, con il prompt di `passo2` di `spikes/run-p4-flow.sh` adattato: il modello scrive il piano con `Write` (il testo del piano di prova sta nel prompt; un piano già committato non passerebbe da `plan-check` e non verrebbe registrato), lo committa, poi `/tollgate:execute`. Ogni passo con `--plugin-dir /tmp/tollgate-b1/plugin`, `--model sonnet`, `--permission-mode acceptEdits`, `--allowedTools "Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob,WebFetch,WebSearch"` (più le voci MCP di context7 se B1-V2 le ammette), un tetto di tempo, `--disallowedTools` per `gh` per percorso, `git push` verso remoti non locali, `curl` e `wget`; lo script rifiuta fuori da `/tmp/tollgate-b1/` e senza `--plugin-dir`. `registra`: versione di `claude`, righe di `lookups` del task, nota salvata e `.tollgate-run/1/research-1.md`, eventi `research_note`, `research_reminder`, `veto` del passo, stato dei task (`tollgate status --json`), comandi Bash del modello. Uscite in `docs/verifiche/evidenze/b1/flusso/`, mai cancellate, con l'esito di ogni tentativo. Test in `tests/test_b1_scripts.py`: `test_flow_controlla_lists_steps`, `test_flow_refuses_outside_tmp`, `test_flow_rules_base_only_in_copy` (dopo `prepara` con radici finte il `SKILL.md` di prova, o `APPROVED` se B1-V7 lo impone, esiste nella copia e non nel repo), `test_flow_requires_plugin_dir`, `test_flow_allowed_tools` (`--permission-mode acceptEdits` e `--allowedTools` con `WebFetch` e `WebSearch` in ogni passo), `test_flow_passo2_writes_plan` (il prompt di `passo2` chiede `Write` del piano, il commit e poi `/tollgate:execute`).
- [ ] **Step 2 (controller): esecuzione.** `prepara`, `passo1`, `passo2`, `registra`. Atteso: task 1 `done` con verdetto `approved`; almeno una lettura `read` di un file del progetto e una `fetch` di una pagina di `docs.python.org` nel task 1 (l'issue lo chiede in modo esplicito; una nota con «Nessuna fonte esterna» è un esito da riportare, non un difetto del prodotto, e il verdetto del revisore dice se il motivo regge); nota valida consegnata con `research submit`; nessuna modifica di codice prima della nota valida (eventi `veto` del passo prima della consegna ammessi, modifiche riuscite no). Un esito ottenuto in più tentativi è «composito». Un difetto del prodotto scoperto qui è un giro di questo task (implementatore, test che fallisce, `tests/run`), poi si ripete **solo** il passo interessato.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-27-b1-prova-flusso.md`: passi, tentativi, letture registrate, nota, avvisi e rifiuti, verdetto del revisore (con l'eventuale rilievo `nota di ricerca`), token (`tollgate stats`), consumo stimato, difetti trovati e corretti; e il limite dichiarato della decisione 18 (i permessi di `WebFetch` concessi con `--allowedTools` non rappresentano la domanda per dominio di una sessione interattiva).
- [ ] **Step 4: Commit** «tollgate B1: prova reale di un lavoro L1 con la nota di ricerca».

---

### Task 10: Prove, revisione 27 della spec, piano principale di B

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 27), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (solo una riga di stato in testa: «B1 eseguita, vedi piano principale di B»)

- [ ] **Step 1: Prove.** Nel piano principale di B una tabella «Prove di B1»: ogni riga della tabella «Copertura» qui sotto con il test o l'evidenza che la prova; un punto senza prova si scrive così, con il motivo.
- [ ] **Step 2: Revisione 27 della spec del nucleo** (decisione 17): 3.2 (evento `post_lookup`); 7.1 (uscita anticipata di `hooks/run`); 7.2 (righe `PostToolUse` delle letture e `PreToolUse` della nota); 8.1 (la nota come ricevuta delle letture: «non si crede a quello che l'agente dice»); 8.5 (strumenti MCP di documentazione); 8.6 (pertinenza della nota dal revisore del task); 11.4 (`[components] research_note`); 12.2 (migrazione 6); 16 (esiti del Task 1 e della prova del Task 9); 18.4 (eventi `research_note` e `research_reminder`); riga 27 della sezione 20.
- [ ] **Step 3: Piano principale di B:** stato in testa (B1 chiusa sul ramo, merge in attesa dell'OK dell'utente, numero di test), riga B1 della sezione 2, sezione 3 con i nomi reali di B1, rinvii a B2 e oltre (righe «minor (deferred)» che riguardano le fette successive).
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md
git commit -m "tollgate B1: prove, spec rev 27, piano principale di B"
```

---

## Copertura: punti del progetto destinati a B1 → task

| Punto del progetto | Task |
|---|---|
| 1, causa tecnica: implementatore senza `WebFetch`, `WebSearch`, context7 | 5 |
| 2, obiettivo 1: passo comune prima di modificare file | 4, 6, 7, 8 |
| 2, obiettivo 2: controllo delle fonti sulle letture registrate | 2, 3, 4, 6 |
| 2, anti-obiettivo «frase vuota senza lettura registrata» | 3 (`check_note`), 6, 7 |
| 2, obiettivi 3 e 5 (primo gruppo di profili, agenti per area) | **B2-B7** (piano principale di B, sezione 4) |
| 2, anti-obiettivo «passo troppo pesante»: L0 solo avviso, una volta per lavoro; permessi di `WebFetch` | 7 (`test_l0_warns_once`); 5 (decisione 18) |
| 2, anti-obiettivo «regole mai lette da una persona» | **B2-B7** (pagine approvate) |
| 2, anti-obiettivo «fonti inventate» nella nota | 3 (`test_check_note_source_not_read`), 6 |
| 3.1 L0 avvisa, L1 e L2 bloccano; L0 che cresce | 7; interruttore: decisione 8 (accensione in B2) |
| 3.2 contenuto della nota, «nessuna fonte esterna» con motivo | 3, 6, 8 (revisore) |
| 3.3 punti 1-4 | 3 (`check_note`), 4 (letture), 6 |
| 3.3 pertinenza dal revisore del task | 8 |
| 3.4 «Dove informarsi» | **B2-B7**: sono le regole dei profili; B1 consegna il formato delle fonti (decisione 2) |
| 3.5 strumenti, pagine come dati non fidati | 5 |
| 3.5 le tre verifiche e i ripieghi | 1 (Step 2 e 4); conseguenze nei Task 3-7 |
| 3.5 context7 assente → solo `WebFetch` | 1 (Step 4), 5 |
| 3.6 giri di correzione, nota del task; `reopen plan` | 2 (`for_task`, `reset_plan`), 6, 7, 8 |
| 3.6 L0 senza task: un avviso per lavoro | 7 |
| 3.6 nomi dei modelli in `rules-base` | **B2** (è una regola) |
| 4 i profili; `base` caricata da ogni agente | **B2-B7** |
| 5 regole approvate; il blocco acceso dopo `rules-base` | interruttore nel Task 3 e 7 (decisione 8); approvazione in **B2** |
| 6 dove sta la nota e in che formato | decisioni 1, 2; Task 3, 6 |
| 6 come gli hook registrano le letture | decisioni 4, 5, 15; Task 2, 4 |
| 6 normalizzazione degli URL, libreria e context7 | decisione 4; Task 3 |
| 6 come `rules-base` arriva agli agenti | **B2** |
| 6 testo dell'avviso e del rifiuto | Task 7 |
| 6 ordine e dimensione delle fette | piano principale di B |
| 6 revisione della spec del nucleo | 10 |
| 7 test della suite (quattro casi) | 7 (`test_l1_without_note_denied_when_enforced`, `test_l0_warns_once`, `test_invalid_note_denied_with_problems`, `test_valid_note_passes`) e 3 |
| 7 prova reale L1 | 9 |
| 7 eval minimi | **B8** |
| 8 vincoli del nucleo | Global Constraints |
| 8 lavori iniziati prima di B; deroga per `adopt` | 2, 6, 7 (decisione 10) |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il brief di scrittura, il progetto di B, la spec rev 26, il codice di `main` e il modello di P5.

| Giro | Rilievi | Esito |
|---|---|---|
| 1 | 1 critical (C-1: in `claude -p` `WebFetch`, `WebSearch` e MCP non concessi falserebbero sonda e prova reale), 7 important (I-1 revisore che blocca con l'interruttore spento; I-2 letture del vecchio task dopo `reopen plan`; I-3 latenza misurata su un percorso che oggi non esiste e senza soglia; I-4 piano della prova non registrato; I-5 atteso della prova che dipende da una scelta del modello; I-6 campo `approved` non provato contro `validate --strict`; I-7 permessi di `WebFetch` nelle sessioni vere), 17 minor | «Non pronto». Corretti: decisioni 1, 4, 8, 10-16, 18 nuova; Task 1-9 |
| 2 | Tutti i 25 rilievi del giro 1 chiusi; 4 minor nuovi (M-n1 `file` del rilievo con la nota mancante; M-n2 seconda misura senza conseguenza; M-n3 B1-V7 nello scan pre-flight; M-n4 test del modo `valida`) | **«Pronto». Critical aperti: 0. Important aperti: 0.** M-n1..M-n4 corretti prima del commit |
| 3 | M-n1..M-n4 chiusi; 1 minor nuovo (M-n5: manca nel brief del revisore il campo con il primo file del diff) | **«Pronto». Critical aperti: 0. Important aperti: 0.** M-n5 corretto (`ReviewBrief.first_diff_file`) |
