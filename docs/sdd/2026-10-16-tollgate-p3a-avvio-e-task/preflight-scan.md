# Pre-flight scan del piano P3a (avvio, ripresa e task)

Piano: `docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md` (879 righe, 14 task, decisioni 1-22). Autorità: spec rev 21 (sezioni 3, 3.1, 3.2, 5, 6.1, 6.3, 7.3, 8.1, 8.4, 8.6, 11.1, 11.3, 12.3, 12.4, 18.5) e piano principale sezione 3. Codice letto: `bin/tollgate_core`, `tollgate_hooks`, `tollgate_checks`, `tollgate_analysis`, `hooks/run`, `tests/hookkit.py`, `tests/helpers.py` e i test esistenti toccati dal piano.

## 1. Metodo e limiti

- Lettura integrale del piano, delle sezioni di spec indicate e del codice reale che il piano consuma o modifica. Ogni nome «Consumes» è stato cercato nel codice con la firma indicata. Tutti esistono con la firma attesa, salvo le eccezioni nei conflitti (`subagents.report` è una colonna, non una funzione; `events.prune_events` ha firma `(conn, now, events_days)`; `bash.uses_tollgate_bin` guarda solo `argv[0]` e, per `python*`, `argv[1]`).
- Eseguite due sonde in `/tmp/tollgate-p3a-scan/` (`probe1.py`, solo cartelle temporanee e `python3 -B`, mai la cartella di stato vera): (a) `active.register` chiamato come fa il runner e poi come fa `start` (conflitto C6); (b) `git remote get-url` contro `git config --get remote.origin.url` con `insteadOf` (conferma la scelta del piano: `get-url` espande, la chiave del repo resta coerente tra hook e CLI).
- Non ho eseguito la suite né applicato il codice del piano (il piano dà firme e test, non il codice). Gli esiti dei test sono quindi «per lettura»: ho verificato che helper, campi e fixture esistano e che le asserzioni siano compatibili con il comportamento reale.
- Task 1: nel working tree c'è già il lavoro di `impl-t1` (non committato quando l'ho letto: `docs/verifiche/2026-10-16-p3a-verifiche.md`, `spikes/run-p3a-experiments.sh`). Esiti letti: V1 sì, V2 informativo, **V3 sì**, V4 sì (con `description` radice e `author`), V5 sì. Il caso V3 «no» non si verifica; la sezione 5 elenca comunque cosa ne dipende.
- Non verificabile da qui (cautele): il formato di `~/.claude/plugins/installed_plugins.json`, l'esistenza e i nomi dei file di Superpowers 7.0.0 (`implementer-prompt.md`, `task-reviewer-prompt.md`, `LICENSE`), l'effettiva concorrenza dei `PreToolUse` per chiamate parallele, `claude -p` e `EnterWorktree`.

## 2. Tabella per coppie di task

«P1/P2» è il codice esistente. Il tabellone copre ogni coppia che condivide un file o un'interfaccia.

| Task A | Task B | Cosa produce A / cosa consuma B | Esito |
|---|---|---|---|
| P1/P2 | T2 | `bash.uses_tollgate_bin/effective_dir`, `Ctx.plugin_bin`, `hookkit.Lab.bash`, `sessions._SAFE`, `apply.OPS` (22 voci, verificate: event, bind, act, expire_acts, block, level, phase, plan, plan_path, subagent_start/name/report/veto/finish/interrupt, task, task_commit, skill_used, commit, invalidate_finish, effect_request, effect_execute) | conflitto C1 (strati), C8 (segnale), C16, C19 |
| P1/P2 | T3 | `create_work`, `find_active`, `db.backup`, `active.register`, `mark_bound`, `prune_events`, `load_config`, `git.default_branch/resolve_ref/local_branches/exists_at/main_worktree/toplevel/origin_url`, `labels_level/max_level` | conflitto C6 (registro attivi), C4 (ordine passi), C7, C18; resto ok |
| P1/P2 | T4 | `set_phase(..., "execution", "start")` (ammesso da `review` e `pr_open`), `bind_session`, `subagents.running/interrupt`, `sessions.alive`, tabella `intents` | ok (`phases.set_worktree` non è in `Files:`, vedi C15) |
| P2 | T5 | `plan._parse/_FILE/_file_value`, `check_plan`, `subagent_stop._GENERATED/_task_lines`, `PlanCheckTest` (esiste) | ok; nota: i casi esistenti usano `` `tests/test_a.py:10-20` `` e `Must-have: M1`, il parser multi-file deve mantenerli |
| P2 | T6 | `tasks.assign` (oggi azzera `reviewer_type`), `take_pending`, `db.MIGRATIONS`, `apply._subagent_start` | conflitto C2 (test esistente), C10 |
| P2 | T7 | `subagent_stop.decide`, `report._candidates` (privata, chiave `status`), `agents.decide`, `apply`, `_common` | conflitto C3, C10, C11, C14, C17 |
| P2 | T8 | `acts.consume`, `phases.close_block`, `level_records/next_level`, `acts.py` (target di `approve level` = `args[1]`, di `resolve` = `args[0]`) | conflitto C9; ok per le firme |
| P2 | T9 | `session.compose` (budget SessionStart), `stats.compute_stats`, `cli.status` | conflitto C12 |
| P2 | T10 | `tests/test_manifest.py` (`plugin.json.version == VERSION`), `skills/off`, `report.REQUIRED` | conflitto C13 (minore) |
| P2 | T11 | `agents.context_pct` legge `ctx/<session>.json` con `used_pct` | ok; C21 |
| P2 | T12 | `phases.bind_session/set_level`, `verify._run_one`, `_common.waiver_hint/explain`, `bash_rules._rm_rf` | conflitto C15 (minore) |
| T1 | T2 | V3 → decisione 2 (segnale della CLI) | ok (V3 sì) |
| T1 | T10 | V1 (`${CLAUDE_PLUGIN_ROOT}` espanso nelle skill: sì), V4 (forma di `marketplace.json`) | ok; il piano a Task 10 Step «Manifest» va allineato a V4 (root `description`, `author` in `plugins[0]` e in `plugin.json`) |
| T1 | T14 | V5 (campione `PreToolUse-NotebookEdit`), voce di sezione 16 | ok |
| T2 | T3 | `sessions.cli_session`, `FlowLab`, `fakegh` | conflitto C16, C8 |
| T2 | T6, T7 | decisione 22 (subagenti negati), `apply.OPS` 22 → 23 → 25 | ok (23 dopo T2, 25 dopo T7; nessun test conta le voci) |
| T2 | T8 | `cli_session(state, cwd, "act")` | conflitto C8 |
| T3 | T4 | `start.py`, `gitw.py`, `housekeeping` | conflitto C4 |
| T3 | T6 | `naming.implementer_name`, `prereq.skill_installed`, `info/exclude` | ok |
| T3 | T9 | `gitw.add_excludes` (3 righe) ↔ `checkpoint.md` ignorato | ok |
| T5 | T6 | `plan.task_text`, `profiles.task_routing`, `brief.implementer_brief` | ok |
| T5 | T7 | `size.task_lines`, `brief.review_brief`, modifica a `subagent_stop` | ok |
| T6 | T7 | `tasks.set_review_prep/set_verdict/reserve/clear_reservation`, `take_pending(number=)`, `taskcmd.py`, `cli.py` (`task`), `apply.py` | conflitto C10, C11 |
| T6 | T9 | motivo del blocco «giri di correzione esauriti sul task k» ↔ `checkpoint.CAPS` | ok (il prefisso deve coincidere alla lettera; vedi C12) |
| T7 | T9 | `awaiting_review`, stato `review` ↔ `next_step` | conflitto C12 |
| T4, T7, T8, T12 | (stessi file) | `phases.py` (`set_worktree`, `set_level_cap`, chiuso), `_common.py` (T7, T12), `cli.py` (T3, T6, T7, T8, T9) | ok: task in sequenza, nessuna modifica concorrente |
| T10 | T11 | skill `setup` nomina `statusline/ctx`, creato dal T11 | ok (nessun test del T10 dipende dal file) |
| T1-T12 | T13, T14 | prova reale e criteri | vedi sezione 3 |

## 3. Tabella per task

| Task | Test previsti contro codice previsto | File creati contro file toccati dopo | Esito |
|---|---|---|---|
| 2 | `CliSessionTest`, `test_check_cli_calls`, `ProgramLineTest`, `test_layers`: gli helper (`hookkit.Lab.bash`, `sample`) esistono. **`test_layers.test_imports` non può passare:** `tollgate_core/cli.py:138` importa già `tollgate_hooks.runner` e T3/T6/T7/T8/T9 aggiungono import di `tollgate_flow` allo stesso file. Il test sul segnale è compatibile con `Lab` (sessione `sess-lab`) | `cli_calls.py`, `flow/__init__.py`, `fakegh.py`, `flowkit.py` nuovi; `sessions.py`, `apply.py`, `acts.py` modificati. `tests/test_analysis_isolation.FORBIDDEN` non include `tollgate_flow` | C1 (blocca), C8, C16, C19 |
| 3 | `naming`, `prereq`, `start`: i nomi consumati esistono. Il test «`active/` contiene il worktree» passa solo perché `.cli()` non passa dagli hook. `gh auth status` non ha una funzione nell'interfaccia | `gitw/gh/prereq/housekeeping/start/naming` nuovi; `sessions.py`, `cli.py` | C4, C5, C6, C7, C18 |
| 4 | `ResumeTest`: tutti gli helper esistono; `phases.set_phase(..., "start")` è ammesso da `review` e `pr_open` | `start.py`, `gitw.py`; `phases.set_worktree` non è nei `Files:` | C4, C15 |
| 5 | `TaskTextTest`, `RoutingTest`, `test_brief`, `test_size`: `PlanCheckTest` esiste. Le colonne `agent/reviewer/reviewer_skills/cross` esistono in `PROFILE_DEFAULTS` | `brief.py`, `size.py` nuovi; `plan.py`, `profiles.py`, `subagent_stop.py` modificati | ok |
| 6 | `MigrationV3Test`, `test_tasks`, `test_taskcmd`, `ResumeTaskTest`. **`tests/test_db.py:140` (`MigrationV2Test`) asserisce `schema_version == "2"`** e fallirà con la migrazione 3 | `taskcmd.py` nuovo; `db.py`, `tasks.py`, `git.py`, `apply.py`, `cli.py` | C2, C9, C10 |
| 7 | `test_verdicts`, `test_check_task_verdict`, `ReviewDoneTest`, `ReservationTest`. `report._candidates` è privata e vincolata a `status` | `verdicts.py`, `task_verdict.py` nuovi; `_common.py`, `subagent_stop.py`, `agents.py`, `apply.py`, `cli.py` | C3, C10, C11, C14, C17 |
| 8 | `LevelCapTest`, `test_actapply`: il test del tetto richiede un lavoro L2 in `execution`, che `FlowLab` non sa creare (`Lab.goto` sì) | `actapply.py` nuovo; `phases.py`, `cli.py` | C9, C16 |
| 9 | `test_checkpoint`, `StatusReadOnlyTest`, `GlobalTest`. La cartella `docs/superpowers/reviews/**` è protetta ma la scrive la CLI: ok | `checkpoint.py` nuovo; `cli.py`, `stats.py` | C12 |
| 10 | `test_manifest` aggiunte: `plugin.json.version == VERSION` resta vero. Stringa attesa in minuscolo, testo del piano con maiuscola | file di skill, agenti, licenze | C13 |
| 11 | `test_statusline`: `agents.context_pct` legge il formato scritto | `statusline/ctx` nuovo | C21 |
| 12 | `ClosedWorkTest`, `test_background_child_killed_after_success` (con `start_new_session=True` il gruppo esiste), messaggio `rm -rf` | `phases.py`, `verify.py`, `_common.py`, `bash_rules.py`; i chiamanti `post_bash.py:62`, `writes.py:84`, `commit.py:42` non sono elencati | C15 |
| 13 | prova reale (nessun test unitario); `HOME` vera: `prereq` legge il registro vero dei plugin | `spikes/run-p3a-flow.sh`, rapporto | C5; aggiungere `TOLLGATE_FAKEGH_DATA` e `TOLLGATE_FAKEGH_LOG` alle cautele |
| 14 | `test_criteria_p3a`: richiede `hooks/run` reale: il wrapper lancia Python solo se `origin/<predefinito>:tollgate.toml` esiste, ok con `FlowLab(gate=True)` | `test_criteria_p3a.py`; spec rev 22 e piano principale | ok; la rev 22 deve registrare gli esiti di C1, C5, C14 |

## 4. Conflitti

**C1. Strati: `tollgate_core` importa già `tollgate_hooks`, e il piano aggiunge import di `tollgate_flow` a `core/cli.py`** (blocca, Task 2)
- Piano: Global Constraints righe 15-16 («`tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`»); Task 2, test `test_layers::test_imports` (riga 255); T3/T6/T7/T8/T9 aggiungono sottocomandi a `tollgate_core/cli.py` che devono chiamare `tollgate_flow.*`.
- Codice: `bin/tollgate_core/cli.py:138` (`from tollgate_hooks.runner import run_hook`, già lì da P2). Un test AST su `tollgate_core` (come `tests/test_analysis_isolation.py`) lo trova, anche se l'import è dentro `main`.
- Correzione minima: `cli.py` è la radice di composizione (entrata di `bin/tollgate`). Il test e la frase dei vincoli dicono «`tollgate_core`, escluso `cli.py`». Il resto di `tollgate_core` resta senza import verso gli strati alti. Alternativa più pulita ma più larga: spostare il dispatch in `tollgate_flow/main.py`; sconsigliata (tocca P1/P2). Da registrare nella rev 22 (sezione 3, tabella pacchetti).
- Task: 2.

**C2. `MigrationV2Test` asserisce la versione «2»** (minore, Task 6)
- Piano: Task 6, decisione 9 e `MigrationV3Test` (righe 514-516).
- Codice: `tests/test_db.py:139-140` apre il DB con tutte le `MIGRATIONS` e asserisce `schema_version == "2"`; con la migrazione 3 diventa «3». Gli altri test (`test_db.py:42,60,230`) usano `latest_version()` e restano verdi; `migrazione-2` alle righe 149 e 233 resta vero.
- Correzione: nel Task 6 cambiare l'asserzione in `str(db.latest_version())` (o `"3"` con un commento) e dirlo nei `Files:`.
- Task: 6.

**C3. Il verdetto riusa `report._candidates` che non è riusabile** (minore, Task 7)
- Piano: Task 7, `parse_task_verdict`: «cerca l'ultimo oggetto JSON con `outcome`, come `report._candidates`».
- Codice: `tollgate_analysis/report.py:26-37`, funzione privata che filtra su `"status" in obj`. Copiarla sarebbe duplicazione; importare un nome privato è fragile.
- Correzione: generalizzare in `report.py` una funzione pubblica `json_candidates(text, key)` (con `_candidates` che la chiama con `"status"`) e farla usare a `verdicts.py`. Test esistenti di `test_report.py` invariati.
- Task: 7.

**C4. Ordine dei passi di `start`: la ripresa va decisa prima dei rifiuti** (minore, Task 3 e 4)
- Piano: Task 3, elenco dei passi 5, 6, 7 (righe 323-333): prerequisiti e controlli con rifiuto al passo 5-6, «lavoro attivo → ripresa» solo al passo 7. Task 4 dice che in ripresa i rifiuti sono solo «repo attivo» e «Python»; spec 6.1 («In ripresa i passi 0 e 1 cambiano»).
- Seguendo l'ordine del Task 3, `test_resume_offline_and_dirty_main_are_warnings` e i rifiuti per Superpowers/gate/`gh` in ripresa non passerebbero. Inoltre, per un repo non attivo, l'hook non scrive il segnale (il runner esce prima): `start` dice «sessione non riconosciuta» invece di «non attivo».
- Correzione: nel Task 3 mettere `find_active(repo_key, N)` subito dopo il passo 4 (config letta) e prima dei prerequisiti; il passo «sessione» (`cli_session`) va dopo il controllo «repo attivo».
- Task: 3, 4.

**C5. Formato del registro dei plugin non verificato** (blocca per l'uso reale, non per i test unitari; Task 3, 6, 13)
- Piano: decisione 7 (riga 49: `plugins["superpowers@claude-plugins-official"][*].version`, «versione 2») e decisione 16 (`installPath`); `FlowLab.home` (riga 237). La spec 11.1 dice invece di leggere il `plugin.json` di Superpowers. Nessun esperimento di Task 1 verifica il formato (V1-V5 non lo toccano); nei documenti del repo `installed_plugins.json` compare solo nel piano.
- I test unitari passano (il file lo scrive `FlowLab`), ma un formato sbagliato fa rifiutare `start` per sempre in produzione, e Task 13 userebbe il registro vero. Inoltre la chiave `superpowers@claude-plugins-official` è cablata: il marketplace reale potrebbe avere un altro nome.
- Correzione: prima del Task 3, una verifica one-shot a cura del controller (che può leggere il file: io non posso): solo la struttura (chiavi, un `version`, `installPath`) in `docs/verifiche/`, oppure `claude plugin list --json` se esiste. Nel codice cercare la prima chiave che comincia per `superpowers@` e prendere la versione più alta; nessuna chiave → rifiuto con messaggio chiaro; JSON diverso da quello atteso → avviso e ripiego su `plugin.json` dentro `installPath`.
- Task: 3 (e 6 per le skill, 13).

**C6. `active.register(..., extra=[wt])` non scrive nulla nel flusso reale** (minore, Task 3)
- Piano: Task 3 passo 10; vincolo P2 (3); test «`active/` contiene il worktree».
- Codice: `tollgate_core/active.py:44` esce senza riscrivere se il file ha meno di 300 s e contiene già la radice. Il runner registra il checkout principale a ogni hook (`runner.py:242`), quindi, quando `start` gira dopo il `PreToolUse` del proprio comando, il file c'è, è recente e `extra` viene ignorato. Sonda: dopo `register(main)` e `register(main, extra=[wt])` il registro resta `[main]`. Il test del piano passa perché `FlowLab.cli()` non passa dagli hook.
- Effetto: il worktree resta fuori dal registro fino al primo hook con `cwd` dentro il worktree (si auto-ripara) o 300 s. Il worktree annidato è comunque coperto dal prefisso del checkout principale: danno basso.
- Correzione: parametro `force: bool = False` in `register`, usato da `start`; test in `test_active_roots.py` che registra prima il principale e poi chiama con `extra`.
- Task: 3.

**C7. Interfacce di `gh` incomplete** (minore, Task 3)
- Piano: Task 3, Produces di `gh.py` e `prereq.py` (righe 287-304) e passo 5 («`gh auth status` con uscita 0»).
- Mancano: una funzione per `auth status` (non è JSON, `run_json` non va bene); come ricavare `{owner}/{repo}` per `commit_state` (la chiave del repo è il percorso locale con `insteadOf`, vedi sonda; va usato l'URL grezzo o i segnaposto di `gh api`); come `FlowLab` inietta i dati di `fakegh` per test (issue 7 aperta, issue 8, chiusa, etichetta `security`, `author_association: NONE`, stato `failure`). Inoltre `commit_state` come «stato combinato» contraddice la spec 6.1 («stati obbligatori del ramo predefinito verdi»): il combinato diventa `failure` anche per `tollgate/attention`, che non è obbligatorio, e dà `pending` se non ci sono stati.
- Correzione: aggiungere `gh.auth_ok(state, repo) -> bool`; `commit_state` legge `statuses[]` e valuta solo `tollgate/guard` e `tollgate/verdict` (o i contesti elencati in una costante); `FlowLab.set_gh(**dati)` che riscrive il JSON letto da `$TOLLGATE_FAKEGH_DATA`.
- Task: 3.

**C8. Segnale della CLI: tre fragilità** (minore, Task 2)
- Piano: decisione 2; Task 2, `cli_calls` e `note_cli_call`.
- (a) Un solo file per sessione (`cli/<session>.json`): due chiamate a `tollgate` nella stessa riga (`verify && act apply`) o in chiamate Bash parallele si sovrascrivono; `cli_calls` registra anche `verify`/`status`, che non servono, e possono cancellare il segnale di `start`/`act` appena scritto (sottocomando diverso → rifiuto).
- (b) `record("cli_call", argv=argv[1:])`: con `python3 .../tollgate start 7` `argv[1:]` comincia dal percorso del programma, non da `start`; `uses_tollgate_bin` accetta quella forma, quindi segnale e confronto sul sottocomando falliscono.
- (c) `apply._OPS["cli_call"]` non gestisce `OSError`; qualunque errore non previsto in un'operazione `record` del `pre_bash` esce da `runner.py` come «errore interno» e diventa `exit 2`, cioè nega ogni comando Bash se la cartella di stato non è scrivibile. `mark_bound` e `active.register` seguono invece «mai un errore».
- Correzione: registrare il segnale solo per `start` e `act`; file `cli/<session>.json` con un dizionario per sottocomando; individuare l'indice del programma (0 o 1) prima di prendere il sottocomando; `note_cli_call` cattura `OSError`. Aggiungere i test: due chiamate diverse nello stesso minuto, forma `python3 <bin> start 7`, cartella di stato in sola lettura.
- Task: 2.

**C9. Il predicato «sola lettura» e le esclusioni del diff stanno negli strati vietati a `tollgate_flow`** (minore, Task 8; tocca 2 e 6)
- Piano: Task 8 (`resolve writer` → «implementatori `running`»; `approve level` calcola `cap_paths` sul diff senza `output_dirs` e `.tollgate-run/`); Global Constraints (`tollgate_flow` non importa hooks né checks).
- Codice: `Ctx.readonly` e `_AREA_READONLY` sono in `tollgate_hooks/context.py:18,52-56`; `output_excludes` in `tollgate_checks/_common.py:69`. `flow` deve duplicare entrambe, o `resolve writer` interrompe anche i revisori in corso (contro la spec 8.4: «gli implementatori»).
- Correzione: portare in `tollgate_core.config` un `Config.is_readonly(agent_type)` (con la regex) e `Config.output_excludes()` (con `.tollgate-run/`), e far delegare `Ctx.readonly` e `_common.output_excludes`. Test con `probe:reviewer-frontend`, `Explore`, `tollgate:implementer`. Stesso punto utile per validare, in `task start`, che l'agente di un profilo `reviewer` sia davvero di sola lettura (spec 6.3: `<plugin>:reviewer-<area>`) e che l'implementatore non lo sia.
- Task: 8 (con una piccola modifica a `config.py` e `context.py`).

**C10. Verdetto e codice di revisione restano «vecchi» dopo un giro di correzione** (minore, Task 6 e 7)
- Piano: Task 6 (`set_verdict`, `task start --fix` «da `review` con verdetto `changes`»), Task 7 (`awaiting_review`: «`review_code` non nullo»).
- Codice: `tasks.py:24,74`: l'evento `fix` imposta `verdict = 'changes'` e nulla azzera `review_code`/`review_sha`. Dopo `fix` → `running` → `report_done` → `review`, il task è di nuovo in `review` con il verdetto `changes` e il codice del giro precedente. Conseguenze: `task start k --fix` è ammesso subito, senza una nuova revisione (e consuma un giro); `awaiting_review` riconosce come «in attesa» un revisore lanciato prima del nuovo `review-prepare` (finirà in due veti e `needs_you`).
- Correzione: `tasks.set_review_prep` azzera `verdict` e `review_findings`; l'evento `fix` azzera `review_code` e `review_sha`; `task start --fix` richiede `verdict == 'changes'` e `review_code` non nullo. Test: dopo `--fix` e `report_done`, `--fix` di nuovo è rifiutato finché non c'è un nuovo verdetto.
- Task: 6 (azzeramenti), 7 (test su `awaiting_review`).

**C11. Un task senza commit non può uscire da `review`** (minore, Task 7)
- Piano: Task 7, `review_prepare`: «Senza commit, rifiuto»; `task_done`: «`review_sha == tasks.commits[-1]`».
- Spec 8.1: «Senza commit e senza modifiche: passa» e `SubagentStop` porta il task in `review` con `report_done`. Un task già soddisfatto dai precedenti resta in `review` senza via d'uscita (né `review-prepare` né `task done`).
- Correzione: con `tasks.commits` vuoto, `review_prepare` usa `git.head(wt)` come SHA e un diff vuoto (il brief lo dice) oppure apre `needs_you` «task senza modifiche»; `task_done` confronta con lo stesso SHA. Scegliere una delle due e testarla.
- Task: 7.

**C12. Checkpoint: l'ordine delle righe e il «prossimo passo»** (minore, Task 9)
- Piano: Task 9, ordine di `write_checkpoint` (fase, livello, piano, task, `stopped_by`, prossimo passo, note) e `test_session_start_injects_checkpoint` («contiene prossimo passo»).
- Codice: `tollgate_checks/session.py:42-52` tiene solo le ultime `MAX_LINES - len(status) - 1` righe del checkpoint (da 4 a 7) e scarta le prime. Con 5 note dopo il «prossimo passo» la riga può uscire dal budget. Inoltre `next_step` elenca solo `task start k`, `task review-prepare k`, `task done k`: mancano `running` (attendere/riprendere), `blocked` (`/tollgate:resolve`) e `review` con verdetto `changes` (→ `task start k --fix`).
- Correzione: scrivere le note prima e il «prossimo passo» per ultimo; completare la mappa di `next_step`; il test con 5 note da 2 righe.
- Task: 9.

**C13. Task 10: stringa di test, nome del test e fonti non verificabili** (minore, Task 10)
- `test_skills_never_mention_sdd_as_executor` richiede «mai subagent-driven-development» in minuscolo e il corpo del piano dice «Mai subagent-driven-development, mai implementatori…» (riga 732, maiuscola): `assertIn` sensibile alle maiuscole fallisce. Il nome del test dice «never mention» mentre asserisce che la frase c'è.
- Il piano deriva agenti e `LICENSES/superpowers-MIT.txt` da Superpowers **7.0.0** (`implementer-prompt.md`, `task-reviewer-prompt.md`, `LICENSE`) senza dire dove leggerli: stanno sotto `~/.claude/plugins/` (vietato nelle cautele di altri task) e il P0 (`docs/verifiche/2026-10-08-p0-esiti.md`) documenta 6.4.1 installata. Non ho potuto verificare che questi tre file esistano con questi nomi nella versione installata.
- `marketplace.json`: usare la forma di V4 (con `description` radice e `author` in `plugins[0]` e in `plugin.json`); il piano dice «oppure i campi che V4 ha indicato», ok, ma `test_plugin_and_marketplace_json` va scritto sulla forma di V4.
- Correzione: confrontare il test con il testo (stessa maiuscola, nome del test corretto); il controller fornisce al Task 10 i percorsi dei tre file Superpowers (o autorizza la lettura di quelle sole cartelle).
- Task: 10.

**C14. Verdetto del revisore del task: scarti rispetto alla spec 8.6/18.5 e un caso senza test** (minore, Task 7; spec rev 22)
- Spec 8.6: «Un JSON assente o malformato vale `needs_you`»; decisione 10: veto (uscita 2) per due volte e solo dopo `needs_you` («come 8.1»). Le due frasi vanno armonizzate nella rev 22 (la decisione 10 è migliore; va scritto che per il revisore del task vale 8.1).
- Spec 8.6: per i rilievi che citano una regola dei profili contano solo le regole `[blocca]`; il piano ignora la distinzione (non esiste ancora uno schema per `[blocca]` in `PROFILE_DEFAULTS`). Va dichiarato come rinvio (B/P3b).
- `parse_task_verdict` scarta i rilievi senza `rule`/`file`/`line` ma non dice nulla di `severity` fuori dall'elenco (`blocker|major|moderate|minor`) né di `line` non intero: un `severity` sconosciuto dovrebbe scartare il rilievo (fail-closed).
- Review Focus 4 elenca «JSON in mezzo al testo» ma `test_verdict_validity_matrix` non ha il sottocaso; aggiungere due: JSON valido preceduto e seguito da prosa (valido) e un oggetto d'esempio citato in prosa prima del vero verdetto (vale l'ultimo).
- Task: 7 (e rev 22 nel 14).

**C15. `Files:` incompleti nei Task 4 e 12** (minore, Task 4, 12)
- Task 4 usa `phases.set_worktree` (nuova funzione) ma non elenca `bin/tollgate_core/phases.py` né il test; la Mappa dei file non la riporta.
- Task 12 cambia le firme di `waiver_hint` e `explain` ma non elenca i chiamanti `tollgate_checks/post_bash.py:62`, `writes.py:84`, `commit.py:42`.
- Task 12, messaggio di `rm -rf`: suggerire «usa `rm -r` senza `-f`» insegna ad aggirare la regola; meglio «usa un percorso dentro il worktree, oppure chiedi all'utente di eseguirlo». Il test esistente (`test_check_bash.py:60`) controlla solo l'uscita 2.
- Task: 4, 12.

**C16. `FlowLab` duplica `hookkit.Lab` e non copre i bisogni dei test** (minore, Task 2)
- Piano: Task 2 Produces (`FlowLab` con `.hook`, `.cli`, `.env`, `.conn`).
- `hookkit.Lab` ha già `pre_edit`, `post_edit`, `bash`, `events`, `_base`, `goto`, `sample`; i test di T6-T8 li useranno (piano registrato tramite `post_edit`, atto con `UserPromptExpansion`, lavoro L2 in `execution`). Riscriverli in `FlowLab` è duplicazione; senza `goto` il test del tetto (T8) non ha un lavoro L2 in `execution` (`start --level L2` parte da `spec_audit`, e `approve spec/plan` sono di P3c).
- Correzione: far estendere a `FlowLab` i metodi di `Lab` per composizione (stessi `ts`, `tmp`, `conn`; sessione `sess-flow` parametrica) e aggiungere `goto(phase)` e `set_gh(**dati)`; chiarire che per un lavoro L2 in `execution` il test usa `phases.set_phase` come `Lab.goto`. Nei test di `ProgramLineTest` chiarire se anche un atto rifiutato (`resolve` senza id) riceve la riga «programma».
- Task: 2.

**C17. Prenotazione del lancio: non atomica** (minore, Task 7)
- Piano: decisione 12; Task 7, `agents.decide` + `record("task_reserve")`; test `test_second_launch_in_same_message_denied` (due `PreToolUse` di fila).
- Il controllo (in `decide`, sola lettura) e la scrittura (in `apply`, dopo) sono due passi in processi diversi. Se Claude Code lancia in parallelo gli hook di due `Agent` nello stesso messaggio, entrambi leggono prima che uno scriva. La stessa lacuna c'è già in `live_writers`. Il test sequenziale non la dimostra.
- Correzione: dichiarare il limite nella decisione 12 e nella rev 22, oppure rendere `task_reserve` un confronto-e-scrittura in `apply` che, se perde, apra un blocco/avviso (un `deny` tardivo non è possibile). Non blocca P3a.
- Task: 7.

**C18. `git worktree add -b ... origin/main` crea un tracking verso il predefinito** (minore, Task 3)
- Piano: Task 3 passo 9 (`worktree_add(new_branch=True)` da `origin/<predefinito>`).
- `git worktree add -b tg/N-x path origin/main` imposta `branch.tg/N-x.merge` su `origin/main`: `git status` dà ahead/behind rispetto al predefinito e un `git push` senza refspec (P3b) fallirebbe con `push.default=simple`.
- Correzione: `--no-track` in `gitw.worktree_add`, con un test sul `branch.<nome>.merge` assente.
- Task: 3.

**C19. Vincoli dichiarati senza test** (minore, Task 2)
- Global Constraints riga 16: «I moduli di `tollgate_checks` non scrivono nel DB… Un test lo controlla (Task 2)»: nessun test di Task 2 lo fa (`ReadDb` blocca le scritture SQL a runtime, `tests/test_hook_engine.py:413` lo prova già). `tests/test_analysis_isolation.py` ha `FORBIDDEN = ("tollgate_core", "tollgate_hooks", "tollgate_checks")` e non include `tollgate_flow`, mentre il piano dice che `tollgate_analysis` non importa nulla di tollgate.
- Correzione: togliere la frase o riferirla a `test_hook_engine`; aggiungere `tollgate_flow` a `FORBIDDEN`.
- Task: 2.

**C20. Decisione 3 (riga «programma») ridondante dopo V1=sì** (minore, opzionale, Task 2)
- V1: `${CLAUDE_PLUGIN_ROOT}` è espanso nelle skill. La riga iniettata a ogni `/tollgate:*` resta come ripiego (Task 1 lo dice). Costo: una riga di contesto per comando e un ramo in `acts.py`. Per la regola «miglioramenti utili e a basso costo si aggiungono» si può tenere; se si toglie, cade anche `ProgramLineTest`. Non è un blocco.
- Task: 2.

**C21. Involucro della statusline con un comando come argomenti** (minore, Task 11)
- Piano: decisione 21 e Task 11: «esegue il comando passato come argomenti». Il `statusLine.command` dell'utente è una stringa di shell (può avere pipe o virgolette); proposto come `ctx <comando attuale>` le pipe si applicano all'uscita di `ctx`, non al comando.
- Correzione: `ctx` esegue `sh -c "$*"` (un solo argomento stringa) oppure la skill `setup` quota il comando; test con un comando contenente una pipe.
- Task: 11.

## 5. Cosa dipende da V3

V3 è «sì» (rapporto di `impl-t1`). Se fosse stato «no», sarebbero cadute: decisione 2; Task 2 (`sessions.note_cli_call/cli_session`, `cli_calls`, operazione `cli_call`, `FlowLab.cli()`); il comando `start` (Task 3, sessione) e `act apply` (Task 8); i test `test_cli_session_*`, `test_no_session_signal_refuses`, `test_start_from_wrapper_flow`; il testo delle skill `start`, `approve`, `resolve`. L'unica alternativa documentata è V2: `CLAUDE_CODE_SESSION_ID` nell'ambiente di Bash (uguaglianza con il `session_id` degli hook non provata, nei subagenti sconosciuta), oppure il ripiego spec 6.1 («cd … && claude» con legame al `SessionStart`).

## 6. Riepilogo

- Conflitti: 21 (2 che bloccano: C1, C5; 19 minori).
- C1: il test degli strati contraddice `tollgate_core/cli.py:138` e i prossimi import verso `tollgate_flow`; serve l'esenzione della radice di composizione (Task 2).
- C5: il formato di `installed_plugins.json` e la chiave `superpowers@claude-plugins-official` non sono verificati da nessun esperimento; richiede una verifica one-shot del controller prima del Task 3.
- Da portare ai task prima dell'esecuzione: C2 e C10 (Task 6), C3 e C14 (Task 7), C4 (Task 3/4), C8 e C16 (Task 2).
