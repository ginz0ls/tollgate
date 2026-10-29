# Decisioni del controller portate nei task (carry)

Ogni voce nomina i task a cui si applica. Prima di lanciare un task il controller copia nel dispatch tutte le voci che lo nominano, in qualunque sezione, e quelle dei `task-N-carry-extract.md`.

## Task 1
- (Task 1) Hook della sonda: registrano in JSONL solo l'input JSON che l'hook riceve su stdin (con `hook_event_name`), mai l'ambiente; eventi `PreToolUse`, `PostToolUse` e `PostToolUseFailure` con matcher `.*`, più `SubagentStart` e `SubagentStop` (servono a legare `agent_id` al subagente `probe:lettore`). Il log sta sotto `/tmp/tollgate-b1/` (mai nella HOME); il modo `raccogli` lo copia nelle evidenze.
- (Task 1) URL con reindirizzamento: lo sceglie il controller prima della sonda; `sonda` lo riceve come argomento obbligatorio (`--redirect-url <url>`) e rifiuta senza; il prompt lo usa così com'è.
- (Task 1) `sonda`: oltre agli argomenti dello Step 1, `--disallowedTools` per `curl`, `wget`, `gh` e `git push` (forma `Bash(curl:*)` ecc., come `spikes/run-p4-flow.sh` se c'è un modello lì), `--output-format json` (token e costo nel rapporto) e un tetto di tempo (`timeout`). Ogni esecuzione numerata (`tentativo-N`): le uscite non si cancellano mai. Il repo di prova in `/tmp/tollgate-b1/probe/` si ricrea a ogni esecuzione.
- (Task 1) Heredoc di B1-V5: la sonda chiede di mandare a `bin/eco` (percorso dalla skill con `${CLAUDE_PLUGIN_ROOT}`) un testo con backtick, una riga `EOF` e una riga con `$HOME`, con il delimitatore `<<'NOTA_DI_RICERCA_FINE'`; `eco` scrive stdin in un file sotto `/tmp/tollgate-b1/`; `raccogli` confronta il file con il testo atteso e scrive l'esito (integro / diverso).
- (Task 1) B1-V3 a secco: dentro il modo `latenza` (stesso repo attivo di prova, stessa sentinella), un `hooks/run PreToolUse` con `tool_name` `mcp__plugin_context7_context7__query-docs` e `agent_id` dell'implementatore registrato; si salvano uscita e risposta (attesa oggi: `deny` per effetto esterno).
- (Task 1) `latenza`: stato con la sentinella `.tollgate-test` in `/tmp/tollgate-b1/state` (`TOLLGATE_STATE`), HOME temporanea sotto `/tmp/tollgate-b1/`, lavoro e implementatore costruiti col programma vero e gli hook (come fanno `tests/flowkit.py` e `tests/hookkit.py`), `python3 -B`; stampa mediana e 95° percentile delle due serie e li salva nelle evidenze.
- (Task 1) `raccogli`: produce `spikes/fixtures/hook-inputs/samples-b1.json` anonimizzato (percorsi della HOME sostituiti, nessuna variabile d'ambiente, `session_id`/`transcript_path` sostituiti con segnaposto) con le chiavi dello Step 3; una chiave senza campione resta assente. Test in più (miglioramento a basso costo): `test_checks_raccogli_anonymizes` su un log finto.

## Dagli esiti del Task 1 e dallo scan pre-flight (D1-D18; testo completo delle ruling nel ledger)

Esiti del Task 1 (rapporto `docs/verifiche/2026-10-27-b1-verifiche.md`, campioni `spikes/fixtures/hook-inputs/samples-b1.json` con le chiavi `read`, `grep_content` (path file), `grep_content_dir` (path cartella), `grep_default` (senza output_mode), `grep_files`, `glob`, `bash_cat`, `webfetch`, `webfetch_redirect`, `websearch`; **niente `mcp_docs`**): `agent_id` presente su tutte le letture del subagente; context7 chiede l'autenticazione (non usabile); `WebFetch` non riporta l'URL finale; heredoc integro; latenza sopra 300 ms; `approved` accettato da `validate --strict`.

### Task 2
- (Task 2, D10) `lookups.prune` cancella le righe dei lavori con `phase = 'closed'` e `updated` più vecchio di `days` giorni (non esiste un'ora di chiusura); `lookups.record` non inserisce un doppione della terna (work, task, kind, target) se esiste già; `for_task` resta senza doppioni.
- (Task 2, scan punto 5) Il test che controlla `latest_version()` è `tests/test_db.py:198-199` (`test_latest_version_is_5`): rinominarlo e portarlo a 6.

### Task 3
- (Task 3, D1) Al posto di `ATTRIBUTE_UNNAMED: bool` la costante è `ATTRIBUTE_UNNAMED_TOOLS: frozenset[str] = frozenset()` (nessun ripiego attivo: B1-V1 positivo).
- (Task 3, D2) Funzione pura `active(work_research: int, component_on: bool) -> bool` (vero solo con `work_research == 1` e componente acceso), con test `test_active`.
- (Task 3, B1-V2) `doc_library(tool_input)` legge `libraryId` o, in mancanza, `context7CompatibleLibraryID`; test su input sintetico (nessun campione `mcp_docs`). `DOC_MCP_TOOLS` con i pattern della decisione 6.
- (Task 3, B1-V7) Niente `APPROVAL_FILE`.
- (Task 3, D13) `read_targets` conosce le opzioni con argomento per comando (`head`/`tail` `-n` `-c`; `grep`/`rg` `-e` `-f` `-A` `-B` `-C` `-m`; `sed` `-e` `-f` e il programma di `sed -n`), tratta `-` come stdin, conta i bersagli di un reindirizzamento `<` se `Cmd.redirects` li porta; asserzioni in più in `test_read_targets`: `head -n 5 f` → `f`, `grep -A 3 foo f` → `f`, `cat a | head -n 5` → `a` per il primo comando e `[]` per il secondo. Best effort dichiarato.

### Task 4
- (Task 4, D4) `tests/hookkit.py` entra nei Files: `Lab(..., research: bool = False)` passato a `create_work` (predefinito invariato), e caricamento di `spikes/fixtures/hook-inputs/samples-b1.json` (`SAMPLES_B1`, `sample_b1(name, phase)`).
- (Task 4, D1) `lookup_owner`: ramo del ripiego solo per gli strumenti in `research.ATTRIBUTE_UNNAMED_TOOLS` (oggi vuoto); quando è attivo sceglie, tra i subagenti `running` non di sola lettura con `task` non nullo, quelli non fermi (`subagents.is_stale` o equivalente reale) e dà `None` se non ne resta esattamente uno. Test `test_unnamed_fetch_attributed_when_enabled` (costante sostituita nel test), `test_unnamed_ambiguous_writers_not_attributed`, `test_unnamed_readonly_agent_ignored`; `test_main_session_read_not_recorded` vale con l'insieme vuoto.
- (Task 4, B1-V1, D15) `Grep` si registra solo con `output_mode == "content"` esplicito e `path` che è un file; `Grep` `content` su cartella e `Grep` senza `output_mode` non contano (test `test_grep_on_dir_not_recorded`, `test_grep_default_mode_not_recorded` con i campioni `grep_content_dir` e `grep_default`).
- (Task 4, B1-V4) `WebFetch`: solo `tool_input.url` normalizzato (nessun URL finale nel `tool_response`); un `tool_response.code` presente e ≥ 400 non conta (`test_webfetch_error_code_not_recorded`). `test_webfetch_recorded_normalized` con una riga.
- (Task 4, B1-V2) `test_doc_mcp_recorded` su input sintetico.
- (Task 4, B1-V6 sopra soglia, D5) `Grep` fuori dal matcher di `PostToolUse` in `hooks.json` (il codice di `lookup_rec` per `Grep` resta, provato con eventi diretti). Via breve di `post_lookup` nel runner, senza `load_config` né `registry.load`: lavoro dalla cartella dell'evento, subagente per `agent_id` con `task` non nullo e tipo uguale a `tasks.agent_type` di un task `running`, lavoro con `research = 1`, poi `lookups.record` (stessa normalizzazione di `lookup_rec`: una sola funzione condivisa, niente duplicazione). La via breve non legge `[components]`: registra anche a componente spento (lo si scrive nel report). Test `test_post_lookup_short_path_skips_config`. `spikes/b1/latenza.py` entra nei Files: aggiungi la serie «PostToolUse Read da subagente» e rimisura (50, mediana e p95 nel report del task; la misura è del tuo Step 4, ma esegui `latenza.py` direttamente con una radice temporanea tua sotto `/tmp/tollgate-b1-t4/`, mai il modo `latenza` dello script).
- (Task 4, B1-V1, D6) Uscita anticipata di `hooks/run` per `PostToolUse` con `tool_name` `Read`, `Grep`, `WebFetch`, `WebSearch` o che comincia con `mcp__`, senza `agent_id`, prima del controllo del repo attivo (letti con `json_str` come il ramo di `UserPromptSubmit`); gli strumenti di `ATTRIBUTE_UNNAMED_TOOLS` (oggi nessuno) sarebbero esclusi: un test confronta l'elenco del wrapper con la costante. Test `test_main_session_read_exits_early`, `test_main_session_websearch_exits_early`, `test_subagent_read_reaches_python`.
- (Task 4, D13) `lookup_rec` normalizza i bersagli di Bash con la cartella effettiva del comando (dopo un `cd`; usa la funzione reale di `bash.py`, per esempio `effective_dir`), non con `event.cwd`.
- (Task 4, D14) `lookup_rec` risolve (`Path.resolve()`) worktree e percorso letto prima di `normalize_path`; test con un worktree dietro un collegamento simbolico.
- (Task 4, scan punto 5) `apply.OPS`: `tests/test_check_audit_round.py:576-577` (`test_ops_count_is_28` → rinominare, 29).

### Task 5
- (Task 5, B1-V2) Nessuna voce MCP in `agents/implementer.md`: `tools: Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch`; `test_implementer_tools` lo controlla alla lettera (il test esistente è `tests/test_manifest.py:78-81`). Il testo dice di usare `WebFetch` sulla documentazione ufficiale (context7 solo «se disponibile», senza promettere lo strumento).
- (Task 5, B1-V3) I test di `effects` usano il nome `mcp__plugin_context7_context7__query-docs`.
- (Task 5, D7) Se il paragrafo nuovo di `setup` lo richiede, aggiorna anche la `description` del frontmatter di `skills/setup/SKILL.md`.

### Task 6
- (Task 6, D2) `submit` dà `REFUSED` con «componente research_note spento» se `[components] research_note = false` (via `research.active`); test `test_component_off_submit_refused`.
- (Task 6, D9) `cli_calls` nega alla sessione principale in L1/L2 solo `research submit` (anche con programma incerto, e nel ripiego testuale con le parole `research` e `submit` accanto a `tollgate`); `research show` resta ammesso; test `test_research_show_allowed_to_main_session`.
- (Task 6, D17) `research_cmd.note_path(worktree: Path, issue: int, number: int) -> Path` è l'unico punto che compone `.tollgate-run/<N>/research-<k>.md`.
- (Task 6, B1-V5) Heredoc integro: nessun `--file`.

### Task 7
- (Task 7, D3) L'avviso: `inject` in `pre_edit`/`pre_bash` **senza** `record`; `research_reminder` registrato in `post_edit`/`post_bash` alla stessa condizione (modifica riuscita). Eventi del CHECK: `pre_edit`, `pre_bash`, `post_edit`, `post_bash`. Test `test_reminder_not_consumed_by_other_deny` (un `deny` di `writes` alla prima modifica: nessun `research_reminder`, l'avviso arriva alla modifica successiva ammessa).
- (Task 7, D11) Un helper unico in `bin/tollgate_checks/_common.py` per gli eventi del lavoro con `seq` dopo l'ultimo `plan_reset` (lettura in sola lettura dal DB del contesto, filtro in Python su `data`): lo usano il conteggio degli avvisi e i problemi della consegna precedente nel testo del rifiuto; test `test_refusal_ignores_problems_before_plan_reset`.
- (Task 7, D12) `_abs`, `_braces`, `_expand`, `_write_paths` passano da `bin/tollgate_checks/bash_rules.py` a `bin/tollgate_checks/_common.py` a comportamento invariato (i test di `bash_rules` restano verdi) e `research_gate` li usa per i bersagli di Bash; `bash.restores_from_index(c)` non conta come modifica; `bash_rules.py` e `_common.py` nei Files; test `test_bash_restore_not_denied`, `test_bash_relative_target_resolved`.
- (Task 7, B1-V7) L'interruttore è il campo `approved` del frontmatter di `skills/rules-base/SKILL.md` (niente `APPROVAL_FILE`).
- (Task 7, D4) `Lab(research=…)` esiste già dal Task 4; qui si aggiunge `plugin_root`.

### Task 8
- (Task 8, D2) Con `research.active(...)` falso (lavoro con `research = 0` oppure componente spento): nessuna sezione «Nota di ricerca» nei brief di implementatore e revisore, nessuna riga in `SubagentStart`; test `test_component_off_brief_without_research`, `test_component_off_review_brief_without_section`.
- (Task 8, D17) Il percorso della nota viene da `research_cmd.note_path` (Task 6).

### Task 9
- (Task 9, B1-V2) `--allowedTools` senza voci MCP di context7.
- (Task 9, B1-V7) La copia del plugin riceve `skills/rules-base/SKILL.md` con `approved: prova-b1` (niente `APPROVED`).
- (Task 9, B1-V6) `Grep` non è più nel matcher: l'atteso «almeno una lettura `read`» resta; il rapporto dice che i `Grep` dell'implementatore non sono registrati.
- (Task 9, dal Task 5) `spikes/run-b1-flow.sh` lancia `claude plugin validate --strict` sulla copia del plugin in `/tmp/tollgate-b1/plugin` prima del primo `claude -p` (senza modello) e si ferma se fallisce: è la verifica del frontmatter nuovo di `implementer.md` e di `setup`.

### Task 10
- (Task 10, D7) Rev 27 comprende anche: glossario (sezione 0: matcher delle letture, una lettura dell'implementatore rinfresca `touch`), 8.5 punto 3 (MCP ha ora un `PostToolUse`; l'atto si consuma ancora a `PreToolUse`), 3.2 (`record lookup` senza evento di 18.4), 11.3 (`setup`).
- (Task 10, D8) Rev 27 e piano principale: la deroga di `adopt` e il fatto che i lavori con `research = 1` in corso all'approvazione di `rules-base` ricevono il rifiuto dal task successivo.
- (Task 10, D18) In 3.3 della rev 27: «non tutte e due» (fonti e «Nessuna fonte esterna» insieme non valgono) e il tetto di 8.000 caratteri.
- (Task 10, scan punto 4) Nel piano principale, rinvio a B8: dopo B2 i casi di eval con implementatore L1/L2 (s1, s2, s3, s9) ricevono il rifiuto e vanno ridisegnati con la nota.
- (Task 10) Sezione 16 della rev 27: gli esiti B1-V1..V7 come nel rapporto delle verifiche (B1-V2 negativo per autenticazione; B1-V3 non determinato per MCP; B1-V4 senza URL finale; B1-V6 sopra soglia, con le conseguenze).
- (Task 4, dal Task 3) `bash.read_targets` può dare cartelle (`grep -r foo src`) e non conta `cat < f` (il parser scarta `<`): `lookup_rec` registra un bersaglio di Bash come `bash_read` solo se, risolto, è un file esistente nel worktree.
- (Task 4, dal Task 3) `Source.ref` di una fonte context7 è il solo libraryId (senza il prefisso `context7:`): la lettura `docs` si registra con lo stesso valore.
