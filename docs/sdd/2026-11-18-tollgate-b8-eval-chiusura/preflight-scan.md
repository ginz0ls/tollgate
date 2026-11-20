# Scan pre-flight del piano B8 (eval e chiusura di B)

Analista: sonnet, sola lettura. Worktree `b8`, ramo `b8-eval-chiusura`, HEAD `8cbf5b5` (uguale a `main`). Sigle: `P:<riga>` piano (`docs/superpowers/plans/2026-11-18-tollgate-b8-eval-chiusura.md`), `B:<riga>` progetto di B, `S:<riga>` spec del nucleo rev 34, `PP:<riga>` piano principale, altrimenti `file:riga` del codice di `main`.

**Esito in una riga:** 1 conflitto A, 4 M, 12 B (17 in tutto). Le **94 forme** della sonda (Review Focus 1, esempi delle decisioni 1-3, forme dei test del Task 1): 36 danno già oggi l'esito voluto, 58 no; con un prototipo scritto alla lettera dalle decisioni 1-3 **tutte e 94 danno l'esito voluto**, e l'intero `tests/test_bash.py` (111 test) resta verde. Nessuna forma ha un esito voluto irraggiungibile con il testo del piano. L'unico A (D1) è una fixture di test che il piano non nomina: con la decisione 4 undici test di `tests/test_init.py` diventano rossi.

## 1. Metodo e limiti

**Letto per intero:** il brief, il piano (607 righe), la sezione «Scan pre-flight» e il resto delle istruzioni d'esecuzione, il progetto di B (sezioni 7 e 15; la 1 e la 2 solo per i titoli e i punti citati dal piano), il modello `docs/sdd/2026-11-12-tollgate-b7-profilo-database/preflight-scan.md` (forma e prime 60 righe). Della spec rev 34: 1.2 (S:114), 8.5 (S:935-960), 6.3 (S:440-496), 11.2 (titoli), 14 (S:1610-1642), 16 (titolo), intestazione. Del catalogo: righe 3-4, 81, 171. Del piano principale: sezione 9, riga PP:288 e i titoli.

**Codice letto:** `bin/tollgate_analysis/bash.py` (20-60, 170-290, 975-1513), `bin/tollgate_checks/effects.py` (60-160), `bin/tollgate_core/tasks.py` (120-185), `bin/tollgate_hooks/apply.py` (25-60), `bin/tollgate_checks/{agents,subagent_start}.py`, `bin/tollgate_flow/init.py` (315-420), `bin/tollgate_core/{config,lookups}.py`, `bin/tollgate_analysis/{research,profiles}.py`, `hooks/hooks.json`, `bin/tollgate_hooks/adapter.py`, `evals/cost.py`, `evals/run.sh` (intero), `evals/_kit/{recipes,scaffold}.py`, `evals/s1-…/case.yaml`, `evals/s9-…/case.yaml`, `spikes/b1/flowreg.py` (251-460), `agents/implementer*.md` (intestazioni), `templates/profiles/{ai,infra}.toml`. **Test letti o cercati:** `test_bash.py` (141-230, 300-400, 585-600), `test_check_effects.py` (intero elenco), `test_init.py` (660-880, 1251-1500, 1949-2040), `test_tasks.py`, `test_check_agents.py` (94-250), `test_taskcmd.py:455-485`, `test_eval_run.py` (intero), `test_eval_cases.py` (30-60, 212-640, 640-1010, 1133-1224, 1441-1500, 1768-1803), `test_eval_kit.py` (intestazione e `grep`), `test_docs.py`, `test_b1_scripts.py:1105-1130`, `test_p5_scripts.py` (`grep`). Non letti né toccati: `suite-baseline.log`, `~/.local/state/tollgate`, `.env*`, chiavi.

**Sonde** (tutte in `W/sonda-preflight/`, `python3 -B`, nessuna rete, nessun programma di servizio, nessun `claude`; i file temporanei stanno in `/tmp` con prefisso `tollgate-sonda-` e si cancellano da soli):
- `sonda_d1.py`: le 94 forme contro `bash.parse` + `bash.effect_reason` di oggi (con il ripiego `text_effect` se `parse` solleva), come fa `effects._bash_intents`. `cfg`: `project_scripts = deploy, release`.
- `proto_b8.py`: un **prototipo** delle decisioni 1-3 innestato su `bash` in-process (`ENV_LOADERS`, `LOADER_PACKAGES`, `inner_commands` con i candidati costruiti da `bash.parse(shlex.join(…))`, il filtro dei token con `/`, `--command`/`--cmd`, la ricorsione dietro un lanciatore con `PACKAGE_COMMANDS`, profondità 3, ogni `--` di testa, `SUPABASE_COMMAND_VALUE_OPTIONS` e `_supabase_option_tokens`). Prova il **disegno**, non il codice del Task 1. Non scrive `true_inner_commands` né `_script_reason` (hanno bisogno di un repo vero: vedi i limiti sotto).
- `sonda_d1_proto.py`, `sonda_d1_extra.py` (37 forme in più dei test del Task 1), `sonda_tests_proto.py` (esegue `tests.test_bash` con il prototipo), `tabella_d1.py` (genera la tabella del §4).
- `sonda_drift.py`: applica **in-process** la decisione 4 a `init._drift` e fa girare `tests.test_init` (230 test): elenca i test che cambiano esito.
- `sonda_trace.py`, `sonda_trace2.py`: `flowreg.third_party_blocks` sulle 81 trace committate di `eval-p5` e su trace sintetiche (sola lettura; `togli-pagine` non lanciato su file miei).
- `sonda_scaffold.py`: `scaffold.build` con tre ricette provvisorie (extra_files con `tollgate.toml`, `ai/client.py`, `vercel.json`, `src/operazioni/divisione.py`), piani di prova scritti in una copia temporanea di `fixtures/`, blocchi di profilo generati da `init.profile_blocks` sul plugin vero; solo `bin/tollgate`, `hooks/run` e il `gh` finto, nella HOME temporanea (come i test di `test_eval_kit.py`).
- `sonda_fetch.py`: un passo `fetch` provvisorio (monkeypatch di `_Session`) contro `lookups`, con quattro forme di `tool_response`.
- `sonda_regex.py`: i grader del piano contro `js_regex` e contro un `vercel.json` giusto e uno senza `rewrites`.

**Non verificabile da qui:** le pagine ufficiali (Step 0 del Task 1); la forma vera di `tool_use_result` di `WebFetch` e **di `WebSearch`**, e se `tool_used` conta gli strumenti del subagente (Task 6); il comportamento del modello nei 16 casi; i costi; `true_inner_commands` e `_script_reason` con i file veri (il repo di `Lab` dei test: provato dal revisore del piano con `r5_fix.py`/`r8`, non rifatto qui); la suite intera e `claude plugin validate`; `claude plugin eval --help`.

## 2. Tabella per coppie di task

| Coppia | File o interfaccia condivisi | Cosa produce / consuma | Nomi e firme che devono coincidere | Esito |
|---|---|---|---|---|
| T1 - T2 | nessuno (`bash.py`, `effects.py`, `test_bash.py`, `test_check_effects.py` contro `init.py`, `tasks.py`, `test_init.py`, `test_tasks.py`, `test_check_agents.py`) | indipendenti | — | Coincide con il parallelo ammesso dalle istruzioni (revisione T1 con T2). Nessun file in comune |
| T1 - T8 | `docs/uso/comandi.md` / `docs/uso/limiti.md`, spec 8.5 | T1 scrive «una riga sugli involucri» nella pagina degli effetti di `comandi.md` (P:382); T8 scrive 8.5 | — | **`comandi.md` non ha una pagina o sezione sugli effetti esterni** (solo `/tollgate:approve effect`, riga 66); la sezione esiste in `limiti.md:17` («### Gli effetti esterni», titolo legato a S:1.2). D8 |
| T2 - T8 | spec 6.3 e 11.2 | T2 cambia `take_pending` e `_drift`; T8 li descrive | nomi `take_pending`, `_drift` | Coincidono. T8 deve anche togliere i due minori chiusi dalla sezione 9 |
| T3 - T4 | `tests/test_eval_cases.py`, passo `fetch`, `research_prep`, `evals/_kit/recipes.py` | T3 aggiunge `_Session._do_fetch` e `test_fetch_step_records_lookup`; T4 lo consuma in `S10DryRun`, `S11DryRun` | `{"do": "fetch", "agent": <id>, "url": <url>}` | Coincide. Il piano non dice che `_do_fetch` deve passare da `self._use("WebFetch", …)`, come `_do_read` (:450): senza, `calls` non ha il `WebFetch` e il grader `pagina-modelli-aperta` (`tool_used`) non può passare nella prova a secco. D9 |
| T3 - T5 | `tests/test_eval_cases.py` | T3 aggiunge un metodo a `_Session` e un test; T5 modifica le classi `S1`-`S3`, `S6`, `S9` | — | Zone diverse. Nessun conflitto di merge |
| T3 - T6/T7 | `evals/run.sh`, `evals/cost.py`, `evals/scrub.py`, `eval-b8/budget.tsv`, `.gitignore` | T3 li crea; T6/T7 li usano dal vivo | uscite 3, 4, 5 di `run.sh`; `--campagna`; `scrub.WEB_DOMAINS` letto da `run.sh` | Coincide nel disegno. `run.sh` è uno script bash e `WEB_DOMAINS`/`CAMPAIGNS` sono in Python: il piano non dice come bash legge la cartella della campagna e i domini (D7). `cost.py` ha già `_trace_for` che usa `parts[-3]`: l'anonimizzazione di `/home/<utente>` non lo rompe |
| T3 - T7 | `test_committed_evidence_has_no_long_web_results`, `flowreg.togli_pagine` | T3 chiama `togli-pagine` e `strip_bash_web`; T7 committa le evidenze | soglia `MAX_WEB_RESULT = 5000` (`flowreg.py:35`) | **Non coincidono sui risultati corti**: `third_party_blocks` e `togli-pagine` toccano solo i risultati di `WebFetch`/`WebSearch` oltre 5000 caratteri (sonda: 1000 e 4999 non segnalati, 5001 sì). D4 |
| T4 - T5 | `evals/_kit/recipes.py` (`CORRECT_PATHS`), `tests/test_eval_cases.py` | T4 aggiunge tre voci di `CORRECT_PATHS` e tre classi; T5 modifica le voci dei cinque casi | `test_correct_paths_score_above_threshold` vuole una voce per ogni caso e `set(path) ⊆ grader` | Coincide. Righe diverse di `recipes.py` |
| T4 - T6 | grader `tool_used` su `WebFetch`, `{source: file, path: W<n>/…}` | T4 li scrive; T6 prova dal vivo (punto d) se `tool_used` conta gli strumenti del subagente | `W1`, `W2`, `W3` = `.claude/worktrees/tg-1-<slug>` | **Verificato**: gli slug di `naming.slug` sono `aggiorna-il-modello-gemini`, `reindirizza-la-pagina-vecchia`, `aggiungi-la-divisione`, e `scaffold.build` crea esattamente `.claude/worktrees/tg-1-<slug>` e il ramo `tg/1-<slug>` |
| T5 - T6 | `nota-consegnata` (`tool_used` su `Bash`, `research submit [0-9]+\b`) | T5 la scrive; T6 prova se il `Bash` del subagente conta | stesso rinvio al punto (d) | Coincide. Il piano ha il ripiego su regex (P:231) |
| T6 - T7 | `eval-b8/budget.tsv`, commit delle evidenze, ordine della decisione 11 | T6 spende circa 0,5 USD; T7 prosegue | residuo del tetto | Coincide. Il commit della sonda viene prima delle correzioni (P:505) |
| T7 - T8 | `docs/verifiche/2026-11-18-b8-eval.md`, `docs/uso/eval-e-ci.md` | T7 scrive il rapporto; T8 mette il rimando in `eval-e-ci.md` | `test_relative_links_exist` (test_docs.py:116) vuole che il file linkato esista | Coincide **solo se** il rimando lo scrive T8 e non T3 (il rapporto non esiste prima di T7). T3 tocca `eval-e-ci.md` (campagne): non deve linkare il rapporto di B8. D12 |

## 3. Tabella per task

### Task 1: effetti esterni (involucri dell'ambiente, opzioni con valore di Supabase, doppio `--`)

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| `test_launcher_double_dash_before_service_args` | esiste, `test_bash.py:209`; asserisce `check_effects` chiede per sei forme `npm exec prisma -- migrate deploy`… e `assertEqual(launcher_candidates([npm, exec, prisma, --, migrate]), [["prisma","migrate"]])` (:218) | il caso nuovo `npm exec prisma -- -- migrate deploy` oggi passa (sonda), con la decisione 3 chiede; l'asserzione :218 resta vera | Coerente |
| `test_launcher_candidates` | esiste, `test_bash.py:591`; `[]` per `ls wrangler deploy`, `[["wrangler","deploy"]]` per `npx -y wrangler@3 deploy` | non cambia (il piano lo dice: P:378) | Coerente |
| `test_reason_has_no_double_prefix` (modello per `Lab`) | esiste, `test_check_effects.py:112`; `Lab` si importa da `tests.hookkit` (:5, classe a `hookkit.py:67`; ce ne sono altre due locali in `test_gate_evaluate.py` e `test_p4_make_case.py`) | il piano non dice quale `Lab`: va usato `tests.hookkit.Lab` | Coerente (D13, B) |
| `test_supabase_help_only_outside_option_values` | esiste, `test_bash.py:312`: chiede `--workdir --help db push --db-url …`, `--profile -h db push --linked`, `db push -- --help`, `db push --linked -- --help`; passa `db push --help`, `-h`, `functions deploy -h`, `db push --linked --help` | con la decisione 2 tutte restano com'erano (provato con il prototipo: 111/111 verdi) | Non cambia |
| `test_supabase_local_flag_hidden_as_option_value_asks` | esiste, `test_bash.py:335`: sei sottocomandi × otto opzioni globali + `--local` chiedono; cinque forme con `--local` valido passano | il prototipo li lascia verdi (`migration repair --status applied 1 --network-id --local` chiede ancora: `--status` consuma `applied`, `--network-id` consuma `--local`) | Non cambia |
| `test_text_effect_supabase_lists` | esiste, `test_bash.py:386`; ripiego testuale | `_supabase_text_effect` non usa `_supabase_option_tokens` (P:151): verde | Non cambia |
| altri test di `test_bash.py` | 111 test | con il prototipo **0 rossi, 111 verdi** | Nessun test esistente cambia esito |
| `tests/test_effects.py` (citato dal brief, non dal piano) | esiste, ma prova `tollgate_core.effects` (chiave e stato di un effetto), non `bash`; nessuna chiamata a `effect_reason` | — | Irrilevante per B8 |
| test di `bash.effect_reason`/`text_effect` fuori da `test_bash.py` | `grep`: nessuno. `effects._bash_intents` (`effects.py:115`, `:127`) è l'unico chiamante di `text_effect` e `effect_reason` | — | Coerente |
| `launcher_candidates` | un solo chiamante, `effect_reason` (`bash.py:1377`), più i due test | la decisione 3 (togliere ogni `--` di testa) non cambia i due test | Coerente |
| `_unwrap` | un solo chiamante, `parse` (`bash.py:281`); `_WRAPPERS` non cambia (`ENV_LOADERS` non è nei wrapper trasparenti) | `env`, `sudo`, `timeout`, `time`, `FOO=1` dentro un candidato vengono tolti da `parse(shlex.join(…))` (provato: 9 forme del §4) | Coerente |
| controlli di `git` e `rm` (`push_is_force`, `branch_deletes`, `merge_args`, `worktree_op`, `git_config_write`, `rm_rf_targets`, `text_danger`) | guardano `argv[0]` | `dotenv -- git push --force origin x` → `push_is_force` falso, `argv[0]` = `dotenv` (sonda); lo stesso per `dotenv -- rm -rf /tmp/x` e `dotenv -- git reset --hard` | Il «limite» è più largo di `git push`: D3 |
| `script_name` | usato solo da `effect_reason` (`bash.py:1397`) | `dotenv -e .env.production -- npm run deploy` → candidato `npm run deploy` → `deploy` ∈ `project_scripts`: chiede (sonda) | Coerente |
| `_script_reason` (`effects.py:94`) | oggi su ogni `Cmd` del parse, con `bash.script_path`: ogni `argv[0]` con `/` che non è un interprete, **senza** controllare il bit `X_OK` | il piano lo applica a `true_inner_commands(c)` con una clausola in più, «file eseguibile (`isfile` e `X_OK`)» | La forma diretta `./deploy` non eseguibile **chiede** (nessun controllo di `X_OK` in `script_path`), mentre `cross-env A=1 ./deploy` non eseguibile passa (P:122, test a `0o755`). Il piano dice «come la forma diretta» ma la differenza non è scritta nella spec 8.5. D10 (B) |
| `_supabase_option_tokens`, `SUPABASE_COMMAND_VALUE_OPTIONS`, `ENV_LOADERS`, `LOADER_PACKAGES`, `inner_commands`, `true_inner_commands` | non esistono oggi | il prototipo prova la parte di `effect_reason` e di Supabase; non `true_inner_commands` | Raggiungibili |
| tabella `SUPABASE_COMMAND_VALUE_OPTIONS` | il piano dà 5 voci attese e dice «per ogni sottocomando di `FLAG_EFFECTS`» (P:142); le voci `with_remote` sono 13 (`db reset`, `lint`, `query`, `advisors`, `diff`, `dump`, `migration list`, `squash`, `gen types`, `test db`, `inspect db`, `inspect report`, `seed buckets`) | per i `with_remote` un'opzione a valore non in tabella lascia l'esito di oggi (la prudente: `db dump -f --linked` chiede); nessun falso permesso | Lo Step 0 decide; nessun rischio (D11, B) |
| `docs/uso/comandi.md` «la parte sugli effetti esterni» | non esiste | — | D8 |

### Task 2: `init --update` e `take_pending`

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| `test_real_precedence_p39` | esiste, `test_init.py:1465`; blocco `backend` dichiarato con i soli `paths`; asserisce `declared[...]["paths"]` e che nessuna riga abbia «togli» | `backend` ha `min_level = "L0"` e nessuna `checklist`: nessuna riga nuova | Verde (provato in-process) |
| le 44+3 righe della tabella delle precedenze (`FrontendPrecedenceTest` P1-P39, `DatabasePrecedenceTest` Q1-Q47) | `check()` parte da `DEFAULT_TOML` e legge solo `got.text` | nessun blocco dichiarato (tranne P39) | Nessun caso cambia |
| **blocchi dichiarati dei test di `init`** | `DECLARED_X` (`test_init.py:675`) non ha `min_level`, e `FRAGMENT_X` (:666) ha `min_level = "L1"` | con la decisione 4 ogni test che parte da `DECLARED_X` ha una riga in più | **11 test rossi** (sonda `sonda_drift.py`, 230 test eseguiti, 12 fallimenti con i subtest): `test_declared_profile_rules_drift_reported` (:779), `…blocking_rules_drift_reported` (:788), `…stale_rule_removal_reported` (:796), `…new_paths_reported` (:805), `test_declared_negation_respected_in_both_orders` (:816, due sottocasi), `…agent_now_available` (:822), `…empty_agent_is_a_choice` (:829), `…agent_missing_in_plugin_is_silent` (:833), `…same_rules_silent_ok` (:838), `test_declared_detected_files_reported_unless_covered` (:927), `DetectTest.test_declared_profile_new_detected_file_reported` (:2019). D1 (A) |
| `test_update_does_not_repeat_declared_min_level`, `test_real_update_proposes_min_level_and_checklist_for_database` | nuovi | `database.toml` ha `min_level = "L2"` e `checklist` non vuota (:48): le due righe si producono | Raggiungibili |
| test che confrontano l'uscita di `--update` in modo esatto | `test_init.py:483-533` (`run_init("--update")`) | passano (non rossi nella sonda) | Non cambiano |
| frammenti veri senza `min_level` o `checklist` non predefiniti | `frontend` e `backend`: L0 senza checklist; `ai` e `infra`: L1; `database`: L2 + checklist | un blocco `ai` o `infra` scritto a mano senza `min_level` riceve la riga | Voluto (P:161) |
| `take_pending` | chiamanti: `apply._subagent_start` (due chiamate, :40 e :44); `taskcmd.py:4` è solo un commento; nessun altro | — | Coerente |
| test di `take_pending` | `test_tasks.py:109-113` (un task), `:164` (`by_number`, due task senza prenotazione), `:216` (`reserve` poi `take_pending`, un task); `test_taskcmd.py:470` (`resume=True`, nessuna prenotazione) | l'ordine `(reserved_at IS NULL), reserved_at DESC, number` non cambia nessun caso con zero o un task prenotato | Nessuno dipende dall'ordine per numero con un task prenotato |
| `test_check_agents.py` | `ResumeTaskTest` (:133, due task, `start` senza `PreToolUse`: nessuna prenotazione), `ReservationTest` (:94, un task), `RelaunchInNewSessionTest` (:172, un task) | invariati | Coerente. Il test nuovo `test_second_task_of_same_type_bound_by_name` sta bene in `ResumeTaskTest` (due task `launch`); `agents.decide` (`agents.py:97`) sceglie il task per `name` e registra `task_reserve` su quello |
| prenotazione scaduta (> 120 s) su un altro task | `reserved_at` non si azzera da solo | un lancio prenota sempre prima il proprio task (`agents.py:102`), quindi alla `SubagentStart` il più recente è il suo; nessun caso raggiungibile trovato in cui vinca una prenotazione vecchia | Coerente (D14, B: nota) |

### Task 3: kit degli eval

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| `test_always_no_publish` | esiste, `test_eval_run.py:190`; l'asserzione è a :201-203 (`args[i+1:i+4] == ["Bash","Write","Edit"]`) | con la campagna `b8` dopo `Bash Write Edit` vengono altri tre elementi: lo slice `[i+1:i+4]` resta vero | Non cambia. Il test nuovo `test_b8_grants_web_tools` e il suo gemello per `p5` bastano |
| `DryRunRealRegistryTest` | esiste, `:491`; usa `self.real = …/eval-p5` (:506) e `budget.tsv`; controlla `--allow-tools Bash Write Edit` come sottostringa (:551) | il piano lo porta su `eval-b8`: la sottostringa è ancora vera | Coerente. `snapshot()` elenca i nomi nella cartella: con `eval-b8` ha solo `budget.tsv` finché non ci sono evidenze (e se un'invocazione vera tiene il lock il test si salta) |
| `CostTest` (:571) | `test_remaining` (:585: 80.0, 67.25), `test_remaining_cli_rounds_down_to_cents` (:600: «79.87»), `test_reserve_then_add_replaces_row_atomically` (:658: 77.5) usano il tetto 80 senza dirlo | con il predefinito `b8` danno 20.0, 7.25, 19.87, 17.5 | Vanno passati a `campaign="p5"` / `--campagna p5` (D5) |
| test di `RunShTest` che dipendono dal numero 80 **senza nominarlo** | `test_max_cost_is_remaining` (:217: `write_budget(30.25, 0.25)` → «49.50»), `test_preamble_prints_paths_and_test_mode` (:413: «75.00»), `test_dry_run_in_test_mode_touches_nothing` (:456: `write_budget(20)` → «60.00»), `test_dry_run_ignores_held_lock` (:476: `write_budget(20)`, uscita 0), `test_prints_command_and_residual` (:483: «60.00» e «58.75») | con `b8` i primi due cambiano il numero; gli ultimi tre **escono 1** (residuo 0: 20 − 20) | Vanno passati a `--campagna p5` o riscritti. Il piano dice «I test che usano 80»: ne elenca nessuno (D5) |
| test con `write_budget(80)` | `test_refuses_without_budget` (:204), la riga a :467 | esaurito in entrambe le campagne | Non cambiano. Il messaggio nuovo deve contenere ancora «esaurito» (:209) |
| `test_budget_env_ignored_outside_test_mode` | esiste, `:691`; chiama `cost.budget_path()` senza argomenti | il predefinito `campaign="b8"` lo tiene vero | Coerente |
| `test_env_paths_need_test_mode` | esiste a `:402` (il piano dice `:405`); scorre tre variabili | si aggiungono `TOLLGATE_EVAL_FAKE_USER`/`_HOST` (P:244) | Coerente |
| test di `run.sh` che fanno girare la corsa intera (con `FAKE_CLAUDE`) | `test_runs_copied_without_tokens` (:312), `test_symlinked_settings_not_followed`, `test_token_in_evidence_stops`, ecc. | con l'anonimizzazione ogni corsa vera chiama `id -un` e `hostname`; in TEST_MODE, se `TOLLGATE_EVAL_FAKE_USER`/`_HOST` non sono impostate, il piano non dice cosa succede | Con un host o un utente di meno di 4 caratteri (o `test`, `root`…) la corsa uscirebbe 2: D6 (M) |
| `tests/test_eval_kit.py` | nessun uso di `cost`, `run.sh`, `eval-p5` (`grep`) | — | Non cambia |
| `spikes/p5/run-p5-checks.sh` e `tests/test_p5_scripts.py` | il primo ha un proprio `BUDGET_TOTAL=80`, `budget_cap` e `budget.tsv` in bash (:31, :154-165); il secondo legge `eval-p5/budget.tsv` per l'intestazione (:20, :93) | nessuno importa `evals/cost.py` | Indipendenti: non cambiano |
| `flowreg.togli-pagine` sulle trace di P5 | 81 `trace.jsonl` in `eval-p5/*/runs/*/` | `third_party_blocks` dà **0 blocchi su tutte e 81** | `test_committed_evidence_has_no_long_web_results` resta verde sulle trace già committate |
| formato della trace di B8 | `togli_pagine` legge `assistant.tool_use` (`WebFetch`/`WebSearch`) e `user.tool_result` con lo stesso `tool_use_id`, anche con `parent_tool_use_id` di un subagente | trace sintetica (WebFetch con `tool_use_result.result`): 5001 e 20000 caratteri → 1 blocco; 1000 e 4999 → 0; un `Bash` con 20000 caratteri → 0 (serve `strip_bash_web`) | Il formato è quello giusto. Il limite dei 5000 caratteri: D4 |
| funzione di `flowreg` che riscrive le trace | `togli_pagine(paths)` (:419), CLI `togli-pagine <file>…` (:452); non c'è una funzione `strip` | — | Coerente |
| `docs/uso/eval-e-ci.md` | cita «i nove casi», «80 USD» e `eval-p5` (:3, :9, :31-40) | T3 le campagne, T8 il rimando al rapporto | Coerente; D12 sul link |

### Task 4: tre casi nuovi

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| `scaffold.build` con `extra_files` per `tollgate.toml`, `ai/client.py`, `tests/test_client.py`, `vercel.json`, `src/operazioni/divisione.py` | `_make_checkout` scrive `extra_files` dopo la copia di `fixtures/project/` e prima del commit `base` (`scaffold.py:226-265`) | sonda `sonda_scaffold.py`: le tre ricette (L1, `task_started=1`, `phase="execution"`) **si costruiscono**; il brief dice `tg-1-t1` (agente `tollgate:implementer-ai`), `tg-1-t1` (`tollgate:implementer-infra`), `tg-1-t1` (`tollgate:implementer`) | Coincide |
| blocco del profilo | `init.profile_blocks` sul plugin vero | per `ai`: `paths = ["/ai/**"]`, `min_level = "L1"`, `agent`/`reviewer` di `ai`, `rules` R-AI-01…11, `blocking_rules` R-AI-01…06. Per `infra`: `paths = ["/vercel.json"]`, `rules` R-INFRA-01…12, `blocking_rules` R-INFRA-01…06 e 12 | I percorsi sono nella forma con la barra iniziale (il piano scrive `ai/**`, P:188). Il piano non ha un test che confronti il blocco della ricetta con la proposta di `init`: D15 (B) |
| il piano di prova passa `plan-check` | `register_plan` scrive il piano con il PostToolUse della `Write` | provato con un piano di una pagina (sezioni, un must-have con un test esistente, un task `Modify` più `Test`; per `infra` solo `Modify: vercel.json`): `_hook` non nega | Coincide |
| slug e worktree | `naming.slug` | `aggiorna-il-modello-gemini`, `reindirizza-la-pagina-vecchia`, `aggiungi-la-divisione` | Coincidono con P:187, 202, 217 |
| livello | `ai` e `infra` hanno `min_level = "L1"`, la ricetta è L1 | `start --level L1` riesce | Coerente |
| `test_case_shape` e simili | `allowed_tools ⊆ CASE_TOOLS` (:57), `case.yaml` + `scaffold.sh` soli (:714), `scaffold.sh` con `BASH_SOURCE` | i tre casi nuovi con `allowed_tools: [Read, Glob, Grep, Agent]` e `tags: [spec]` rientrano; `test_correct_paths_score_above_threshold` (:745) vuole una voce per ogni cartella: il Task 4 la scrive | Coerente |
| grader `{source: file, path}` | ammesso da `check_graders` (:681-:700) e da `grade` (`end["texts"].get(path)`) | **se il file manca il grader dà `False` anche con `not_contains`** (`grade`, riga «if text is None») | I tre file esistono nei tre progetti: nessun problema |
| regex di s11 | `js_regex` | sonda: un `vercel.json` giusto → vero; senza `rewrites` → falso; `def dividi` assente da un `from … import dividi` → ammesso; il brief e `skills/rules-base/SKILL.md` non combaciano con `research submit [0-9]+\b` (la skill ha `research submit` ma non seguito da un numero) | Coerente (con `<n>` nel brief il pattern combacia, ed è il motivo per cui è un `tool_used`) |
| punteggi | pesi della decisione 8 | s10: 5, s11: 6, s12: 5; i cammini sbagliati danno 3/5=0,60, 0, ≤2/6, ≤1/6, 5/6, 2/5 come scritto | Coerente |
| nome dei test citati | `ExtraCasesTest` (:1768), `ScoreTest` (:728) | `ExtraCasesTest.EXTRA` è una lista fissa di quattro nomi (:1771): i casi nuovi non vi entrano | Coerente |

### Task 5: i casi di P5 con la nota

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| `CORRECT_PATHS` | `recipes.py:133`; voci di s1 (2), s2 (1), s3 (3), s6 (1), s9 (2) | gli insiemi attesi dei test con `PREP` cambiano come sotto | Vedi la lista |
| `research_prep` | `test_eval_cases.py:799`; usata a :826, :835, :843 (s1), :895 (s2, `test_s2_editing_the_test…`), :930, :941, :964, :972 (s3), :1161 (s6 `cycle`, `task=2`) | il comando è `research submit <n> <<…`: il pattern `research submit [0-9]+\b` combacia con `_compact(tool_input)` | Raggiungibile |
| insiemi attesi da aggiornare con `nota-consegnata` | s1: `test_s1_dry_run` (due `assertCorrectPath`, :825-838), `test_s1_a_red_verify_is_not_a_receipt` (:840, `assertWrongPath`); s2: `test_s2_editing_the_test_is_the_shortcut…` (:893); s3: `test_s3_dry_run` (:929), `…unchanged_file_path` (:940), `…writing_with_bash…` (:970); s6: `test_s6_dry_run` (:1172), `test_s6_task_closed_but_no_instruction_scores_below_threshold` (:1202), via `cycle()` | — | Sono 8-9 test, tutti elencabili. **Non** ricevono l'indicatore: s2 `test_s2_dry_run` (percorso senza `PREP`), s3 `…unchanged_file_without_trying` (:948), s9 le due voci esistenti. E4 usa lo stesso `cycle()` ma non ha il grader: invariato |
| `ScoreTest` | :728 | gli indicatori `with-only` non entrano in `scored_graders` | Invariato, come dice il piano |
| s9 | nessun `PREP`; `DEDICATED` lancia `tollgate:implementer` senza lavoro | serve una voce nuova con `research_prep` | Coerente. Nota: l'implementatore dedicato di s9 **scrive** in una corsa vera (`moltiplica`), quindi PP:288 («`s9` non modifica file e non è cambiato») va corretta da T8: D2 (B) |
| s2 e s3 reali | la nota vuole il `Read` dei file dichiarati | un implementatore che apre il blocco (s2) o segnala fuori scope senza modificare (s3) non consegna la nota: `nota-consegnata` falso, non scorato | Coerente (indicatore) |

### Task 6 e 7 (controller)

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| passo `fetch` e `lookups.observed` | `observed("WebFetch", …)` (`lookups.py:73-80`); `PostToolUse` ha `WebFetch\|WebSearch` nel matcher (`hooks.json:8`); `LOOKUP_TOOLS` include entrambi (`adapter.py:12`) | `sonda_fetch.py`: `tool_response` `{"code":200}` → riga `fetch` con l'URL normalizzato (senza barra finale); `{"code":404}` → nessuna riga; senza `code` → riga; `code` stringa `"200"` → riga | Un `PostToolUse` di `WebFetch` arriva a `observed` nella prova a secco, per l'agente (`agent_id`); la forma vera la prova il Task 6 |
| agenti con `WebFetch` | `agents/implementer*.md`: `tools: Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch` | l'implementatore può aprire la pagina | Coerente |
| `PostToolUseFailure` | matcher solo `Edit\|Write\|MultiEdit\|NotebookEdit\|Bash` | un `WebFetch` negato non lascia traccia in tollgate | Come dice il piano (P:43) |
| punto (b) della sonda | solo `WebFetch` | per `WebSearch` (concessa dalla decisione 6) non c'è un punto: la forma di `tool_use_result` è ignota, e `togli_pagine` ripulisce `tool_use_result` solo se ha una `result` stringa o è esso stesso una stringa | D4 |
| `.git/info/exclude` | `**/.claude/worktrees/` presente nell'exclude comune | `git check-ignore` conferma che `eval-b8/…/cwd/.claude/worktrees/…` è ignorato | Coerente (P:531) |
| P5 `state` copiati | 81 `tollgate.db` in `eval-p5` senza `-wal`/`-shm`; le trace di P5 non hanno la tabella `lookups` (stato di prima di B1) | `research_counts.count` su uno stato di P5 solleverebbe un errore SQL; su uno di B8 va | D16 (B) |

### Task 8

| Voce | Esistenza / stato oggi | Contro il codice previsto | Esito |
|---|---|---|---|
| `test_limits_match_spec_1_2` | `test_docs.py:100`; confronta **i titoli in grassetto** di S:1.2 con i `### ` di `limiti.md`, normalizzati | il piano tiene il titolo «Gli eval girano in una sandbox senza rete, su casi costruiti» (S:114, `limiti.md:123`) e cambia solo il testo sotto | Funziona. Il titolo diventa falso («senza rete» mentre `WebFetch` raggiunge due domini): il test è **simmetrico**, quindi si possono cambiare insieme i due titoli e il test passa (D17, B) |
| `test_no_local_paths` | vieta `/home/`, `/Users/`, `MEGA` in `docs/uso/*.md` | le frasi nuove di `eval-e-ci.md` (il `TMPDIR` è `$HOME/.cache/…`) non lo toccano | Coerente |
| `test_relative_links_exist` | `test_docs.py:116` | il rimando al rapporto di B8 vuole il file | D12 |
| `test_spec_event_types_match_registry` | `test_docs.py:138` legge la riga `**Tipi:**` di 18.4 | B8 non aggiunge tipi (P:67) | Coerente |
| catalogo | C:3-4, C:81 («circa 35 agenti (28 per area e 7 generici)»), C:171 | `ls agents` dà **18** file: 7 generici, 10 di area (5 implementatori + 5 revisori), 1 specialista | Coincide con P:557 |
| spec rev 34 → 35 | intestazione e riga 34 della sezione 20 | — | Da scrivere dal ramo (T8) |
| PP:288 | «`s9` non modifica file e non è cambiato» | contraddice B:228 e la decisione 13 | D2 |

## 4. Sonda della decisione 1 su `bash.effect_reason`

**Come leggerla.** «Oggi» = `bash.parse` + `bash.effect_reason` (con `bash.text_effect` se `parse` solleva), per ogni comando della riga, come `effects._bash_intents`. «Piano» = l'esito che il piano scrive. Le forme con `./script` o `scripts/x.sh` passano da `effect_reason` e chiedono (se chiedono) per un altro motivo, `_script_reason`: qui il voluto è «passa» da `effect_reason`. «Prototipo» = il prototipo `proto_b8.py` scritto alla lettera dalle decisioni 1-3. `cfg`: `project_scripts = [deploy, release]`.

| # | Gruppo | Forma | Oggi | Piano | Già come voluto | Prototipo del piano |
|---|---|---|---|---|---|---|
| 1 | RF1 | `dotenv -e .env.production -- prisma migrate deploy` | passa | chiede | no | chiede |
| 2 | RF1 | `dotenv -e .env.production -- npm run deploy` | passa | chiede | no | chiede |
| 3 | RF1 | `cross-env NODE_ENV=production drizzle-kit push` | passa | chiede | no | chiede |
| 4 | RF1 | `doppler run -- npx supabase db push` | passa | chiede | no | chiede |
| 5 | RF1 | `doppler run --command 'prisma migrate deploy'` | passa | chiede | no | chiede |
| 6 | RF1 | `op run -- supabase db push` | passa | chiede | no | chiede |
| 7 | RF1 | `infisical run --env=prod -- prisma db push` | passa | chiede | no | chiede |
| 8 | RF1 | `dotenv -- curl -X POST https://x` | passa | chiede | no | chiede |
| 9 | RF1 | `dotenv -- bash -c 'prisma migrate deploy'` | passa | chiede | no | chiede |
| 10 | RF1 | `npm exec prisma -- -- migrate deploy` | passa | chiede | no | chiede |
| 11 | RF1 | `supabase db push -p --local` | passa | chiede | no | chiede |
| 12 | RF1 | `supabase db pull --schema --local` | passa | chiede | no | chiede |
| 13 | RF1 | `supabase db push -p --help` | passa | chiede | no | chiede |
| 14 | RF1 | `dotenv -- python3 -m unittest` | passa | passa | sì | passa |
| 15 | RF1 | `dotenv -- npm i -g vercel` | passa | passa | sì | passa |
| 16 | RF1 | `supabase db push -p x --local` | passa | passa | sì | passa |
| 17 | RF1 | `cross-env CI=1 python3 tools/build.py` | passa | passa | sì | passa |
| 18 | D1 | `cross-env A=1 /usr/local/bin/vercel --prod` | passa | chiede | no | chiede |
| 19 | D1 | `env-cmd -f .env /usr/local/bin/vercel --prod` | passa | chiede | no | chiede |
| 20 | D1 | `cross-env A=1 /usr/bin/curl -X POST https://x` | passa | chiede | no | chiede |
| 21 | D1 | `cross-env A=1 /usr/bin/make deploy` | passa | chiede | no | chiede |
| 22 | D1 | `cross-env A=1 ./deploy.sh` | passa | passa | sì | passa |
| 23 | D1 | `cross-env A=1 ./deploy` | passa | passa | sì | passa |
| 24 | D1 | `dotenv -e .env ./scripts/deploy.sh` | passa | passa | sì | passa |
| 25 | D1 | `env-cmd -f ./test/.env mocha -R spec` | passa | passa | sì | passa |
| 26 | D1 | `dotenv -e ./.env.test -- jest` | passa | passa | sì | passa |
| 27 | D1 | `cross-env NODE_ENV=test jest src/aws` | passa | passa | sì | passa |
| 28 | D1 | `cross-env NODE_ENV=test mocha 'test/**/*.spec.js'` | passa | passa | sì | passa |
| 29 | D1 | `npx dotenv -e .env -- npm run deploy` | passa | chiede | no | chiede |
| 30 | D1 | `npx dotenv@16 -e .env -- npm run deploy` | passa | chiede | no | chiede |
| 31 | D1 | `npx dotenv-cli -e .env -- npm run deploy` | passa | chiede | no | chiede |
| 32 | D1 | `npx @dotenvx/dotenvx run -- npm run deploy` | passa | chiede | no | chiede |
| 33 | D1 | `npx cross-env NODE_ENV=production npm run release` | passa | chiede | no | chiede |
| 34 | D1 | `pnpm exec dotenv -- gh pr create` | passa | chiede | no | chiede |
| 35 | D1 | `npm i -D cross-env vercel` | passa | passa | sì | passa |
| 36 | D1 | `pnpm add -D dotenv vercel` | passa | passa | sì | passa |
| 37 | D1 | `cross-env NODE_ENV=production prisma migrate deploy` | passa | chiede | no | chiede |
| 38 | D1 | `dotenv -- env X=1 prisma migrate deploy` | passa | chiede | no | chiede |
| 39 | D1 | `dotenv -- sudo prisma migrate deploy` | passa | chiede | no | chiede |
| 40 | D1 | `dotenv -- timeout 60 supabase db push` | passa | chiede | no | chiede |
| 41 | D1 | `dotenv -- python3 manage.py check` | passa | passa | sì | passa |
| 42 | D1 | `cross-env CI=1 python3 -m pytest tests/vercel` | passa | passa | sì | passa |
| 43 | D1 | `dotenv -e vercel -- echo x` | passa | chiede | no | chiede |
| 44 | D1 | `dotenv -e vercel echo x` | passa | chiede | no | chiede |
| 45 | D1 | `cross-env vercel echo x` | passa | chiede | no | chiede |
| 46 | D1 | `cross-env NODE_ENV=test jest aws` | passa | chiede | no | chiede |
| 47 | D1 | `cross-env NODE_ENV=production npm run deploy -- --prod` | passa | chiede | no | chiede |
| 48 | D1 | `env-cmd -f .env npm run release -- --tag x` | passa | chiede | no | chiede |
| 49 | D1 | `dotenv -e .env.production npm run deploy -- --prod` | passa | chiede | no | chiede |
| 50 | D1 | `cross-env NODE_ENV=production prisma migrate deploy -- --x` | passa | chiede | no | chiede |
| 51 | D1 | `dotenv -- doppler run -- prisma migrate deploy` | passa | chiede | no | chiede |
| 52 | D1 | `dotenv -- doppler run -- infisical run -- prisma migrate deploy` | passa | chiede | no | chiede |
| 53 | D1 | `dotenv -- sh -c 'curl -X POST https://x'` | passa | chiede | no | chiede |
| 54 | D1 | `dotenv -- FOO=1 prisma migrate deploy` | passa | chiede | no | chiede |
| 55 | D1 | `dotenv -- time npm run deploy` | passa | chiede | no | chiede |
| 56 | D1 | `doppler run --command='prisma migrate deploy'` | passa | chiede | no | chiede |
| 57 | D1 | `doppler run --project supabase --config prd -- npm run dev` | passa | chiede | no | chiede |
| 58 | D1 | `dotenv -- git push` | passa | passa | sì | passa |
| 59 | D1 | `cross-env A=1 scripts/deploy` | passa | passa | sì | passa |
| 60 | D1 | `cross-env A=1 ./vercel --prod` | passa | passa | sì | passa |
| 61 | D1 | `dotenv -- bash -c "it's; curl -X POST https://x"` | passa | chiede | no | chiede |
| 62 | D1 | `dotenv --debug node x.js` | passa | passa | sì | passa |
| 63 | D1 | `dotenv -- node scripts/migrate.js` | passa | passa | sì | passa |
| 64 | D1 | `cross-env NODE_ENV=test c8 -r text node --test 'test/**/*.test.js'` | passa | passa | sì | passa |
| 65 | F | `env-cmd -f .env prisma migrate deploy` | passa | chiede | no | chiede |
| 66 | F | `infisical run -- prisma migrate deploy` | passa | chiede | no | chiede |
| 67 | F | `doppler run -- prisma migrate deploy` | passa | chiede | no | chiede |
| 68 | F | `op run -- supabase db push` | passa | chiede | no | chiede |
| 69 | F | `npx dotenv -e .env -- prisma migrate deploy` | chiede | chiede | sì | chiede |
| 70 | F | `npx -- prisma migrate deploy` | chiede | chiede | sì | chiede |
| 71 | F | `env FOO=1 prisma migrate deploy` | chiede | chiede | sì | chiede |
| 72 | D2 | `supabase db push --password --local` | passa | chiede | no | chiede |
| 73 | D2 | `supabase db push -p --local` | passa | chiede | no | chiede |
| 74 | D2 | `supabase db pull --schema --local` | passa | chiede | no | chiede |
| 75 | D2 | `supabase db pull -s --local` | passa | chiede | no | chiede |
| 76 | D2 | `supabase db pull --schema -h` | passa | chiede | no | chiede |
| 77 | D2 | `supabase db push --help` | passa | passa | sì | passa |
| 78 | D2 | `supabase db push -p x --local` | passa | passa | sì | passa |
| 79 | D2 | `supabase db push -p segreto --local` | passa | passa | sì | passa |
| 80 | D2 | `supabase --version` | passa | passa | sì | passa |
| 81 | D2 | `supabase db reset --linked --version 20240101` | passa | chiede | no | chiede |
| 82 | D2 | `supabase db reset --version 20240101 --local` | passa | passa | sì | passa |
| 83 | D2 | `supabase migration down --last --local` | passa | chiede | no | chiede |
| 84 | D2 | `supabase migration down --last 1 --local` | passa | passa | sì | passa |
| 85 | D2 | `supabase migration repair --status applied 1 --local` | passa | passa | sì | passa |
| 86 | D2 | `supabase db push --db-url postgres://prod --local` | chiede | chiede | sì | chiede |
| 87 | D2 | `npx supabase db push -p --local` | passa | chiede | no | chiede |
| 88 | D2 | `npx supabase db push -p x --local` | passa | passa | sì | passa |
| 89 | D2 | `npx supabase migration down --last --local` | passa | chiede | no | chiede |
| 90 | D2 | `npx supabase db pull --schema --local` | passa | chiede | no | chiede |
| 91 | D3 | `npm exec prisma -- -- migrate deploy` | passa | chiede | no | chiede |
| 92 | D3 | `npm exec prisma -- migrate deploy` | chiede | chiede | sì | chiede |
| 93 | D3 | `npx prisma -- migrate deploy` | chiede | chiede | sì | chiede |
| 94 | D3 | `supabase -- db push` | chiede | chiede | sì | chiede |

Totale forme: 94; già come voluto oggi: 36; diverse oggi: 58; diverse con il prototipo: 0.

**Lettura della tabella.**
- **36 forme su 94 danno già oggi l'esito voluto**: 29 «passa» (le guardie: `dotenv -- python3 -m unittest`, `dotenv -- npm i -g vercel`, `supabase db push -p x --local`, `cross-env CI=1 python3 tools/build.py`, i percorsi di dati, `dotenv -- git push`, `supabase db push --help`, `supabase --version`, …) e 7 «chiede»: `npx dotenv -e .env -- prisma migrate deploy`, `npx -- prisma migrate deploy`, `env FOO=1 prisma migrate deploy`, `supabase db push --db-url postgres://prod --local`, `npm exec prisma -- migrate deploy`, `npx prisma -- migrate deploy`, `supabase -- db push`. Le prime tre sono nel fatto verificato di P:34; le altre quattro sono guardie che la decisione 3 e la tabella dei valori non devono rompere.
- **58 forme oggi danno l'esito sbagliato** (sono i buchi): tutte le forme con un involucro (`dotenv`, `dotenvx`, `cross-env`, `env-cmd`, `doppler`, `infisical`, `op`) con un comando di servizio dentro, tutte le forme di Supabase con un'opzione a valore e `--local` o `--help`, `db reset --linked --version …`, `npm exec prisma -- -- migrate deploy`.
- **Con il prototipo tutte le 94 danno l'esito voluto** (colonna «Prototipo»), e `tests.test_bash` (111 test) resta verde: nessuna forma ha un esito voluto irraggiungibile con il testo del piano. Le 37 forme in più dei test del Task 1 (`sonda_d1_extra.py`: percorsi di dati, `dotenvx run`, `op run --env-file`, `infisical run --command=…`, `supabase db push -p x -p --local`, `db dump -f --linked`, `db reset --version`, `db query`, tre involucri annidati) danno anch'esse l'esito voluto.
- **Ciò che il prototipo non prova:** `true_inner_commands` e `_script_reason` con i file veri (restano i test del Task 1 con `Lab`); il termine della profondità («due livelli, al terzo chiede») è nel prototipo come tetto 3 e dà `dotenv -- dotenv -- dotenv -- vercel` → chiede, ma lo stesso esito arriverebbe dalla ricorsione illimitata: il test `test_env_loader_nesting_depth` (tre involucri chiedono) non distingue le due letture, ed è innocuo.

## 5. Conflitti

Gravità: A = blocca o falsa un test o un esito; M = difetto reale ma aggirabile; B = precisazione. Segnalo per ognuno se tocca una scelta dell'utente o un profilo approvato.

### A

**D1 (A): `DECLARED_X` senza `min_level`: la decisione 4 manda in rosso 11 test di `tests/test_init.py`.**
- **Dove:** P:159-162 (decisione 4), P:395-398 (Task 2, Step 1: elenca solo i due test nuovi); `tests/test_init.py:666-676` (`FRAGMENT_X` ha `min_level = "L1"`, `DECLARED_X` no); `bin/tollgate_flow/init.py:362-364` (il punto dove si aggiunge la riga).
- **Cosa:** con la riga nuova in `_drift`, ogni test che dichiara `[profiles.x]` senza `min_level` riceve una riga `aggiungi min_level = "L1"` in più. Sonda in-process (`sonda_drift.py`, `tests.test_init` interi, 230 test): 12 fallimenti, 11 test distinti: `test_declared_profile_rules_drift_reported` (:779), `…blocking_rules_drift_reported` (:788), `…stale_rule_removal_reported` (:796), `…new_paths_reported` (:805), `test_declared_negation_respected_in_both_orders` (:816, due sottocasi), `…agent_now_available` (:822), `…empty_agent_is_a_choice` (:829), `…agent_missing_in_plugin_is_silent` (:833), `…same_rules_silent_ok` (:838), `test_declared_detected_files_reported_unless_covered` (:927), `DetectTest.test_declared_profile_new_detected_file_reported` (:2019). Sono asserzioni su `len(got.lines) == 1` o su `lines == []`. Le tabelle P1-P39 e Q1-Q47 **non** cambiano (nessun blocco dichiarato, salvo P39 che è `backend`, L0 senza checklist).
- **Ruling proposto:** il Task 2 Step 1 scrive che `DECLARED_X` riceve `min_level = "L1"` (uguale a `FRAGMENT_X`) e che i due test nuovi partono da `DECLARED_X.replace('min_level = "L1"\n', '')` (e uno con `checklist`, per il frammento `database` vero). Nessuna asserzione esistente si tocca.
- **Costo se sbagliato:** l'implementatore trova 11 rossi e li «sistema» cambiando `== 1` in `== 2` o filtrando le righe: undici asserzioni che fissavano «una sola riga» si indeboliscono. Non tocca una scelta dell'utente né un profilo approvato.

### M

**D3 (M): il limite degli involucri è più largo di `git push`.**
- **Dove:** P:138 («`dotenv -- git push` resta un limite, scritto nella spec 8.5 e fissato da un test»), P:376 (`test_git_push_behind_env_loader_unchanged`); `bash.py:532` (`push_is_force`), `:591` (`rm_rf_targets`), `:945`, `:950`, `:968`, `:505`.
- **Cosa:** sonda: `dotenv -- git push --force origin x` → `push_is_force` falso (`argv[0]` = `dotenv`); `dotenv -- rm -rf /tmp/x` e `dotenv -- git reset --hard` non sono visti dai controlli sull'`argv`. Con `sudo` o `env` lo sono (`_unwrap`). Il piano fissa un solo caso, il `git push` del gate; la spec 8.5 scriverebbe un limite più stretto del vero.
- **Ruling proposto:** scrivere in 8.5, e fissare con due forme in più in quel test, il limite per intero: ogni controllo che guarda `argv[0]` (force push, `git push` del gate, `reset --hard`, `branch -D`, `merge`, `worktree`, scritture di `git config`, `rm -r` fuori dal worktree). Non far entrare i comandi interni in `parse`: tocca tutti i chiamanti e non è di B8.
- **Costo se sbagliato:** l'utente legge «limite: `git push`» e crede protetto `dotenv -- git push --force`. Oggi è già aperto: B8 non peggiora, ma lo descriverebbe male. Non tocca una scelta dell'utente.

**D4 (M): la pulizia delle trace lascia i risultati web sotto i 5000 caratteri, e non conosce la forma di `WebSearch`.**
- **Dove:** P:235-237 (decisione 9), P:84, P:236 (il test sintetico), P:499-504 (la sonda: il punto (b) è solo `WebFetch`); `spikes/b1/flowreg.py:35` (`MAX_WEB_RESULT = 5000`), `:341-396` (`_third_party`), `:369-376` (il `swap` dei risultati web); `tests/test_b1_scripts.py:1117`.
- **Cosa:** sonda su trace sintetiche: un risultato di `WebFetch` di 1000 o 4999 caratteri **non** è segnalato da `third_party_blocks` né riscritto da `togli-pagine`; 5001 e 20000 sì. Un `WebFetch` restituisce di norma una risposta già riassunta dal modello, spesso breve. Quindi il test `test_committed_evidence_has_no_long_web_results` resta verde con testo di una pagina di terzi nelle evidenze pubbliche, e il piano chiede «niente testo di pagine di terzi» (P:83). Per `WebSearch` (concessa dalla decisione 6) la forma di `tool_use_result` è sconosciuta: `togli_pagine` riscrive `tool_use_result` solo se ha una `result` stringa (o è esso stesso una stringa): un `results` strutturato con titoli e frammenti resta, e il blocco `tool_result` è già il segnaposto, quindi nessun controllo lo vede.
- **Ruling proposto:** `evals/scrub.py` ha una funzione (accanto a `strip_bash_web`) che sostituisce **ogni** risultato di `WebFetch`/`WebSearch` indipendentemente dalla lunghezza, compreso `tool_use_result`, con il segnaposto con indirizzo o interrogazione, e un test su un risultato di 1000 caratteri e su un `tool_use_result` strutturato; `flowreg` non si tocca. La sonda del Task 6 aggiunge un punto (b2): la forma di un risultato di `WebSearch` (solo le chiavi), se il modello l'ha usata. Lo Step 2 del Task 7 resta.
- **Costo se sbagliato:** fino a 5000 caratteri per pagina di testo di terzi nel repo pubblico; si scopre solo con la lettura a mano. Non tocca una scelta dell'utente.

**D5 (M): i test di P5 che dipendono dal tetto 80 senza nominarlo.**
- **Dove:** P:436 («I test che usano 80 passano a `--campagna p5`»); `tests/test_eval_run.py`.
- **Cosa:** con il predefinito `b8` (20) cambiano o escono 1 otto test, e solo due contengono la cifra 80: `RunShTest.test_max_cost_is_remaining` (:217, «49.50»), `test_preamble_prints_paths_and_test_mode` (:413, «75.00»), `test_dry_run_in_test_mode_touches_nothing` (:456, «60.00»; con `write_budget(20)` il residuo b8 è 0, uscita 1), `test_dry_run_ignores_held_lock` (:476, uscita 0 attesa), `test_prints_command_and_residual` (:483, «60.00», «58.75»); `CostTest.test_remaining` (:585), `test_remaining_cli_rounds_down_to_cents` (:600, «79.87»), `test_reserve_then_add_replaces_row_atomically` (:658, 77.5). `test_refuses_without_budget` (:204) e la riga :467 restano veri.
- **Ruling proposto:** il Task 3 Step 1 elenca questi otto con riga; passano a `--campagna p5` (per `run.sh`) e a `campaign="p5"` o `--campagna p5` (per `cost`). I numeri attesi non si toccano: sono la prova che `p5` resta com'era.
- **Costo se sbagliato:** otto rossi scoperti al primo giro; il rischio vero è che li si «aggiusti» cambiando i numeri attesi, e `p5` perde la sua prova. Non tocca una scelta dell'utente.

**D6 (M): l'anonimizzazione nei test dipende dall'utente e dall'host della macchina.**
- **Dove:** P:244 (`$(id -un)`, `$(hostname)`; «in TEST_MODE, valori finti da `TOLLGATE_EVAL_FAKE_USER` e `TOLLGATE_EVAL_FAKE_HOST`»), P:242 (uscita 2 sotto 4 caratteri o parola riservata); `tests/test_eval_run.py:130-170` (`EvalRunBase.env`).
- **Cosa:** il piano non dice cosa fa `run.sh` in TEST_MODE quando le due variabili non sono impostate, cioè in **tutti** i test di `RunShTest` esistenti (la corsa finta passa dalla copia, quindi dall'anonimizzazione). Se prende i valori veri, un utente o un host corto (`pc`, `ci`, `test`) fa uscire 2 e rende rossi i test su quella macchina; e i test leggerebbero dati veri della macchina.
- **Ruling proposto:** in TEST_MODE `run.sh` non chiama mai `id` né `hostname`: usa `${TOLLGATE_EVAL_FAKE_USER:-utente-prova}` e `${TOLLGATE_EVAL_FAKE_HOST:-macchina-prova}`; `test_run_anonymizes_copied_runs` imposta due valori suoi. Fuori da TEST_MODE restano `id -un` e `hostname`.
- **Costo se sbagliato:** una suite che passa in CI e fallisce sul portatile dell'utente (o al contrario). Non tocca una scelta dell'utente.

### B

**D2 (B): s9, PP:288 e il nome «i quattro ridisegnati».**
- **Dove:** B:228 (**utente**: «s1, s2, s3 e s9 ridisegnati con la nota»), PP:288 («`s9` non modifica file e non è cambiato»; «il `cycle` di `s6`»), P:263 (decisione 11: «i quattro ridisegnati (s1, s2, s3, s6)»), P:289-296 (decisione 13: i cinque).
- **Cosa:** il piano rispetta il progetto (cinque casi con l'indicatore: s1, s2, s3, s6, s9). Restano due testi da allineare: la decisione 11 mette s9 tra «gli altri casi spec» e PP:288 dice che s9 non cambia (nelle corse vere l'implementatore dedicato di s9 modifica `src/calc.py`).
- **Ruling proposto:** decisione 11 «s1, s2, s3, s6 e s9»; il Task 8 corregge PP:288 e la sezione 9. Costo: documenti incoerenti, nessun effetto sul codice. **Tocca una scelta dell'utente (B:228), che il piano rispetta.**

**D7 (B): `run.sh` (bash) non sa dove prende cartella e domini della campagna.**
- **Dove:** P:169-173, P:237 (`WEB_DOMAINS` «letto anche da `run.sh`»), P:171; `evals/run.sh:9-13`, `:78`, `:122`.
- **Cosa:** `CAMPAIGNS` e `WEB_DOMAINS` stanno in Python, `run.sh` costruisce già oggi registro, evidenze e messaggio in bash: il piano non dice come li legge (due copie dei nomi `eval-b8`/`eval-p5` e dei domini).
- **Ruling proposto:** un sottocomando `cost.py info --campagna X` (cartella e tetto) e `evals/scrub.py domains` (uno per riga) che `run.sh` legge; `test_grants_follow_web_domains` e un test gemello per la cartella. Costo: deriva silenziosa tra le due copie.

**D8 (B): «la pagina degli effetti esterni» di `docs/uso/comandi.md` non esiste.**
- **Dove:** P:328, P:382; `docs/uso/comandi.md` (nessuna sezione sugli effetti, solo la riga 66 su `approve effect`); `docs/uso/limiti.md:17` («### Gli effetti esterni», titolo legato a S:1.2).
- **Ruling proposto:** le due righe (involucri, opzioni con valore) vanno nel corpo di `limiti.md` sotto «Gli effetti esterni» (il titolo non cambia: `test_limits_match_spec_1_2`), e il Task 1 aggiunge `docs/uso/limiti.md` ai suoi file. Costo: l'implementatore inventa una sezione in `comandi.md`.

**D9 (B): `_do_fetch` deve anche registrare la `tool_use`.**
- **Dove:** P:418, P:176, P:436; `tests/test_eval_cases.py:450-460` (`_do_read` come modello), `:578-583` (`tool_used` conta `self.calls`).
- **Cosa:** il piano descrive solo il `PostToolUse`. I grader `tool_used` su `WebFetch` leggono `calls`, riempito da `_use`: senza, `pagina-modelli-aperta` non può passare nella prova a secco. La sonda del passo `fetch` (con `_use`) registra la riga `fetch` per `code` 200, nessuna riga per 404.
- **Ruling proposto:** scriverlo nel Task 3: `_do_fetch` fa `_use("WebFetch", {"url": …}, agent)`, il `PostToolUse` con `tool_response`, `_result` come `_do_read`. Costo: tre test del Task 4 rossi per un motivo non ovvio.

**D10 (B): `./deploy` non eseguibile: la forma diretta chiede, quella dietro un involucro passa.**
- **Dove:** P:116-122 (la clausola «`os.path.isfile` e `X_OK`»), P:138-140; `effects.py:94-107` + `bash.py` `script_path` (nessun controllo di `X_OK`).
- **Cosa:** `./deploy` diretto, non tracciato e non eseguibile, chiede oggi; `cross-env A=1 ./deploy` con lo stesso file passa (il test a `0o755` lo fissa dal lato «chiede», e lo stesso file senza il bit «passa»). Il piano dice «come la forma diretta» ma non scrive la differenza in 8.5.
- **Ruling proposto:** una riga in 8.5 tra i costi. Costo: una spec che dice «come la forma diretta» dove non lo è.

**D11 (B): la tabella dei valori per «ogni sottocomando di `FLAG_EFFECTS`».**
- **Dove:** P:142-147 (cinque voci attese), P:349-350 (Step 0).
- **Cosa:** i `with_remote` sono 13; un'opzione a valore non in tabella lascia l'esito di oggi, che è quello prudente (`db dump -f --linked` chiede). Nessun falso permesso, solo qualche permesso in più. Con il prototipo `db dump -f --linked` chiede, come oggi.
- **Ruling proposto:** lo Step 0 si limita ai `unless_local` e a `db reset`; per i `with_remote` il piano dichiara che resta com'è. Costo: nessuno.

**D12 (B): il rimando al rapporto di B8 in `eval-e-ci.md`.**
- **Dove:** P:330, P:545, P:440; `tests/test_docs.py:116` (`test_relative_links_exist`).
- **Cosa:** T3 modifica `docs/uso/eval-e-ci.md` prima che il rapporto esista: un link a `../verifiche/2026-11-18-b8-eval.md` farebbe rosso il test del Task 3.
- **Ruling proposto:** T3 non linka il rapporto e dice «i casi spec sono dodici» (la frase di oggi cita «i nove casi»); il link lo scrive T8. Costo: suite rossa al Task 3.

**D13 (B): quale `Lab` per `test_check_effects.py`.**
- **Dove:** P:377; `tests/hookkit.py:67` (usato da `test_check_effects.py:5`), `tests/test_gate_evaluate.py:65` (`LabCase`), `tests/test_p4_make_case.py:54` (altra `Lab`).
- **Ruling proposto:** scrivere «`tests.hookkit.Lab`». Costo: un import sbagliato.

**D14 (B): `take_pending` con una prenotazione scaduta.**
- **Dove:** P:163-167; `tasks.py:145-158`, `agents.py:97-102`.
- **Cosa:** controllato, nessun caso raggiungibile: ogni lancio prenota prima il proprio task, quindi alla `SubagentStart` la prenotazione più recente è la sua; una vecchia (> 120 s) su un altro task perde. Resta valido il limite `launch` + `resume` dello stesso tipo (P:166).
- **Ruling proposto:** nessuno; una riga di test («due task prenotati, vince il più recente») basta. Costo: nessuno.

**D15 (B): i blocchi di profilo delle ricette non sono confrontati con `init`.**
- **Dove:** P:188, P:203, P:463; `evals/_kit/recipes.py`; sonda `sonda_scaffold.py`.
- **Cosa:** `init.profile_blocks` propone `paths = ["/ai/**"]` (con la barra iniziale) e `["/vercel.json"]`, `rules` R-AI-01…11, `blocking_rules` R-AI-01…06; R-INFRA-01…12 e 01…06 più 12. Il piano scrive «paths `ai/**`». Un test che confronti il testo della ricetta con la proposta di `init` non c'è (`test_new_case_…` non lo copre).
- **Ruling proposto:** aggiungere `test_new_case_profile_blocks_match_init` (la `tollgate.toml` della ricetta contro `init.profile_blocks` sul plugin vero) e usare i percorsi con la barra. Costo: il blocco invecchia in silenzio se un frammento cambia (non in B8).

**D16 (B): `research_counts.count` su uno stato senza `lookups`.**
- **Dove:** P:252-261; `eval-p5/*/runs/*/home/.local/state/tollgate/tollgate.db` (nessuna tabella `lookups`, stato di prima di B1).
- **Ruling proposto:** una tabella mancante dà zero righe, non un errore. Costo: lo strumento non si può lanciare sulle evidenze di P5.

**D17 (B): il titolo «senza rete» resta falso.**
- **Dove:** P:549, P:545; S:114; `docs/uso/limiti.md:123`; `tests/test_docs.py:100`.
- **Cosa:** il test confronta i titoli di spec e `limiti.md` tra loro: si possono cambiare insieme (per esempio «Gli eval girano in una sandbox, su casi costruiti») e il test resta verde. Il piano vieta di cambiare il titolo e lascia un titolo che contraddice il testo.
- **Ruling proposto:** cambiare i due titoli insieme nel Task 8 (e nei rimandi), oppure lasciare il titolo e dirlo nel rapporto. Costo: un titolo che dice «senza rete» sopra un testo che dice «due domini concessi».

## 6. Esito dei punti da guardare apposta

1. **Decisione 1 contro `launcher_candidates`, `_unwrap`, `effect_reason`, `text_effect`, git e `rm`, `script_name`, i test.** Un solo chiamante di `launcher_candidates` (`effect_reason`) e di `_unwrap` (`parse`); `text_effect` è chiamato solo da `effects._bash_intents`; `script_name` solo da `effect_reason`; i test di `test_bash.py` (111) restano verdi con il prototipo, `test_effects.py` non riguarda `bash`, `test_check_effects.py` non fissa nessun comando dietro un involucro. I controlli su `argv[0]` (git, `rm`) non vedono dentro `dotenv`: D3. Sonda del §4: 94 forme, 36 già come volute, 58 no, 0 irraggiungibili.
2. **I tre scorrimenti di Supabase.** `_supabase_flag_present` (`bash.py:1235`) e `_supabase_asks_help` (`:1304`) condividono `_supabase_option_tokens`; `_supabase_text_effect` (`:1483`) resta com'è. `test_supabase_local_flag_hidden_as_option_value_asks` (:335), `test_supabase_help_only_outside_option_values` (:312) e `test_text_effect_supabase_lists` (:386): **nessuno cambia esito** (provato). Cambiano solo i casi nuovi (`db push -p --local`, `db pull --schema --local`, `db push -p --help`, `db pull --schema -h`, `db reset --linked --version …`).
3. **`take_pending`.** Chiamanti: `apply._subagent_start` (due volte) e i test; `taskcmd.py:4` è un commento. Nessun test dipende dall'ordine per numero con un task prenotato (`ResumeTaskTest` fa `start` senza `PreToolUse`: zero prenotazioni). D14 è una nota.
4. **`_drift`.** Cambiano esito 11 test di `test_init.py` (D1, A), tutti per `DECLARED_X` senza `min_level`. Le tabelle P1-P39 e Q1-Q47 non cambiano (P39: `backend` è L0 senza checklist). I frammenti veri con `min_level` o `checklist` non predefiniti sono `ai`, `infra` (L1) e `database` (L2, checklist); `frontend` e `backend` sono L0 senza checklist.
5. **Le campagne.** Otto test di `test_eval_run.py` da passare a `p5` (D5); `DryRunRealRegistryTest` passa a `eval-b8` e la sottostringa `--allow-tools Bash Write Edit` resta vera; `test_always_no_publish` non cambia (lo slice `[i+1:i+4]`); `test_eval_kit.py` non usa `cost` né `run.sh`; `spikes/p5/run-p5-checks.sh` e `tests/test_p5_scripts.py` non importano `evals/cost.py` (hanno un proprio `BUDGET_TOTAL=80`) e non cambiano.
6. **La pulizia delle trace.** 81 trace di P5 committate: **0 blocchi** ciascuna. La funzione che riscrive è `flowreg.togli_pagine` (CLI `togli-pagine`). Limiti: i risultati sotto 5000 caratteri e la forma di `WebSearch` (D4).
7. **I casi nuovi contro `scaffold.build`.** Le tre ricette (L1, task avviato) si costruiscono; brief con `tollgate:implementer-ai`, `-infra`, `tollgate:implementer`; il piano di una pagina passa `plan-check`; gli slug e i worktree sono quelli del piano; `rules` e `blocking_rules` sono quelle di `init` con le skill approvate (11/6 per `ai`, 12/7 per `infra`) ma i percorsi hanno la barra iniziale (D15).
8. **La decisione 13.** `CORRECT_PATHS` cambia per: s1 (2 voci), s3 (le prime 2 delle 3), s6 (1 voce); non per s2 (il percorso corretto non consegna una nota) né per s3 «file invariato senza tentare», né per s9 (voce nuova). Test con `PREP` da aggiornare: `test_s1_dry_run` (:825), `test_s1_a_red_verify_is_not_a_receipt` (:840), `test_s2_editing_the_test_is_the_shortcut…` (:893), `test_s3_dry_run` (:929), `…unchanged_file_path` (:940), `…writing_with_bash…` (:970), `test_s6_dry_run` (:1172), `test_s6_task_closed_but_no_instruction…` (:1202); `test_s3_a_modified_file…` (:963) asserisce solo un `assertNotIn`. `ScoreTest` e `ExtraCasesTest` non cambiano; E4 usa lo stesso `cycle()` ma non ha il grader.
9. **La prova a secco e il passo `fetch`.** Un `PostToolUse` di `WebFetch` con `agent_id` arriva a `lookups.observed` e scrive una riga `fetch` con l'URL normalizzato (`code` 200, senza `code`, `code` stringa); `code` 404 non scrive. `hooks.json` ha `WebFetch` e `WebSearch` nel matcher di `PostToolUse` e non in `PostToolUseFailure`. Serve anche la `tool_use` (D9).
10. **Il Task 8 contro `test_docs.py`.** Legati da un test: i titoli in grassetto di S:1.2 e i `### ` di `limiti.md` (si possono cambiare insieme: D17), i link relativi (D12), l'assenza di `/home/`, `/Users/`, `MEGA` nei sei file di `docs/uso/`, la riga `**Tipi:**` di 18.4 e `init --update` in `emergenze-e-aggiornamenti.md`. Nessun test lega le frasi del catalogo, il conto degli agenti o le righe della sezione 20.
11. **I nomi dichiarati già esistenti.** `test_launcher_double_dash_before_service_args` (`test_bash.py:209`), `test_launcher_candidates` (:591), `test_reason_has_no_double_prefix` (`test_check_effects.py:112`), `Lab` (`tests/hookkit.py:67`), `test_real_precedence_p39` (`test_init.py:1465`), `DryRunRealRegistryTest` (`test_eval_run.py:491`), `test_always_no_publish` (:190), `test_budget_env_ignored_outside_test_mode` (:691), `research_prep` (`test_eval_cases.py:799`), `ScoreTest` (:728), `ExtraCasesTest` (:1768), `test_the_extra_cases_exist_and_are_tagged` (:1776), `test_committed_evidence_has_no_long_web_results` (`test_b1_scripts.py:1117`), `flowreg.togli_pagine` (:419; non c'è una funzione `strip`). **Tutti esistono**; nessun nome del piano è sbagliato (alcune righe del piano sono spostate di 1-3: `test_env_paths_need_test_mode` è a :402 e non a :405; `:202` è :201-203).

## 7. Risposta breve

- File: `.superpowers/sdd/2026-11-18-tollgate-b8-eval-chiusura/preflight-scan.md` (nel worktree `b8`).
- Conflitti: **A 1, M 4, B 12.**
- D1 (A): la decisione 4 manda in rosso 11 test di `tests/test_init.py` perché `DECLARED_X` (:675) non ha `min_level` mentre `FRAGMENT_X` ha L1; il piano non nomina la fixture.
- Forme della sonda con esito voluto non raggiungibile con il testo del piano: **nessuna** (94 su 94 con il prototipo).
