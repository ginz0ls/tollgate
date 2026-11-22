# Scan pre-flight del piano C1 (tracciamento locale)

Analista: sonnet, sola lettura. Worktree `c1`, ramo `c1-tracciamento-locale`, HEAD `055dc80` (uguale a `main`, albero pulito). Sigle: `P:<riga>` piano C1 (`docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md`), `C:<riga>` progetto di C, `S:<riga>` spec del nucleo rev 35, `PP:<riga>` piano principale di C, altrimenti `file:riga` del codice di oggi.

**Esito in una riga:** 2 conflitti A, 5 M, 14 B (21 in tutto). Nessun fatto «verificato» del piano è smentito (3 righe hanno numeri di riga imprecisi, 1 non è verificabile da qui). Nessun conflitto tocca una scelta «utente» del progetto di C né un profilo approvato.

## 1. Metodo e limiti

**Letto per intero:** il brief, il piano (422 righe), le istruzioni d'esecuzione (205 righe), il progetto di C (209 righe), il piano principale di C (165 righe). Della spec rev 35: 3.1, 3.2, 5, 6.1, 7.1, 7.2 (tabella), 8.4 (parte), 11.4 (`[retention]`), 12.2 (righe di `events` e `lookups`), 18.4 (riga `**Tipi:**`); 20 e il resto di 12.2 non letti (li scrive il Task 10). Il modello di forma: `docs/sdd/2026-11-18-tollgate-b8-eval-chiusura/preflight-scan.md`.

**Codice letto:** `bin/tollgate_core/{db,events,config,paths,fsutil,scope,phases,subagents,effects,intents,acts,cli,sessions,reviews,stats}.py`, `bin/tollgate_flow/{start,housekeeping,l2acts,actapply,adopt,research_cmd,taskcmd}.py`, `bin/tollgate_checks/{post_edit,session,cli_calls,acts,subagent_stop,task_verdict,final_review,audit_round,bash_rules,_common}.py` (parti), `bin/tollgate_hooks/{model,adapter,runner,apply,registry}.py`, `hooks/run`, `hooks/hooks.json`, `bin/tollgate_analysis/{specdoc,profiles,report,brief,research,bash}.py` (parti), `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `evals/scrub.py`; i test citati e quelli che fissano i valori toccati (`test_db`, `test_events`, `test_config`, `test_start`, `test_adopt`, `test_check_post_edit`, `test_l2acts`, `test_wrapper`, `test_manifest`, `test_hook_engine`, `test_docs`, `test_skill_contract`, `test_layers`, `test_analysis_isolation`, `test_modelsfetch`, `test_b1_scripts`, `test_check_audit_round`, `test_reviews`, `test_report`, `test_brief`).

**Sonde** (tutte in `W/sonda-preflight/`, `python3 -B`, nessuna rete, nessun `claude`, nessun programma di servizio; il codice del repo non è stato modificato; le cartelle temporanee hanno prefisso `tollgate` e si cancellano da sole):
- `sonda_cli_calls.py`: `cli_calls.decide` con il comando heredoc della decisione 5 (apostrofo, `$HOME`, backtick, parole `task`, `review`, `start`), da subagente e da sessione principale.
- `sonda_areas.py`: forma di `ctx.config.profiles`, `profiles.vertical_for`, `specdoc.slices` sul testo di un piano (con e senza `## Fette previste`), `plan.check_plan`.
- `sonda_migrazione7.py`: le tre `ALTER TABLE` della decisione 1 su un DB alla versione 6 con un lavoro (`TempState`).
- `sonda_misura.py`: la misura del Task 8 su copie in `mkdtemp(prefix="tollgate-")` (cancellata alla fine, verificato; `git status` pulito, nessun `-wal`/`-shm` nel repo).
- `sonda_rompe.py`: applica **in-process** (nessun file cambia) `events_days = 0` con «0 = mai» e una migrazione 7 in coda a `MIGRATIONS`, poi lancia 12 test mirati: elenca quali cambiano esito.

**Non verificabile da qui:** le pagine di `code.claude.com` sugli hook (riga 33 dei fatti: rete vietata); la forma vera di `tool_response` e di `PostToolUseFailure` di `AskUserQuestion` (nessun campione in `spikes/fixtures/hook-inputs/`); se una trascrizione di subagente ripreso con `SendMessage` è cumulativa (riga 43); il comportamento delle trascrizioni vere (nel repo c'è solo lo stream di `claude -p`, che ha `message.model` e `message.usage`); la prova reale (Task 9, del controller). La suite completa non si lancia (gira già la baseline).

## 2. Tabella per coppie di task

| Coppia | File o interfaccia condivisi | Cosa produce / consuma | Nomi e firme che devono coincidere | Esito |
|---|---|---|---|---|
| T1 - T2 | `bin/tollgate_core/events.py` (T1: `EVENT_TYPES`; T2: `archive_and_prune`), `tests/test_events.py` | T1 aggiunge i 5 tipi; T2 non li usa | nessuna | Coincide. Sequenziali, nessun conflitto |
| T1 - T3 | colonne `work_items.size`, `size_by`, `slices`; tipo `size_decided` | T1 produce, T3 scrive con `UPDATE` e `record_event` | `size`, `size_by` (`rules`/`user`), `slices`; nome del tipo | Coincide. La sonda sulla migrazione conferma `CHECK` e `IntegrityError` (§4.3). **D2** per il test che fissa la versione |
| T1 - T5, T6, T7 | tipi `ruling`, `stop_asked`, `stop_answered`, `cost` | T1 produce; T5, T6, T7 registrano | nomi dei tipi | Coincide |
| T1 - T10 | riga `**Tipi:**` di 18.4 (S:2140) | T1 la cambia; T10 scrive il resto di 18.4 | `test_spec_event_types_match_registry` (`tests/test_docs.py:138-142`) confronta l'insieme dei nomi tra backtick con `EVENT_TYPES` | Coincide. Attenzione (D17): la riga deve avere solo i nomi dei tipi tra backtick |
| T2 - T8 | `retention.events_days`, cartella `archive/` | T2 la crea; T8 la descrive in `gestionale.md` | `ARCHIVE_DIR = "archive"`, nome `events-<s1>-<s2>.jsonl` | Coincide |
| T3 - T4 | `sizes.decide`, `sizes.set_by_user`, `worksize.LABELS`, `worksize.Signals` | T3 produce; T4 consuma in `approve_spec` e `_approve_size` | `decide(conn, work, signals, *, cause, confirmed=False, now, session=None) -> str`; `set_by_user(conn, work, size, reason, *, now, session=None) -> str`; `Signals(level, tasks, areas, slices)` | Coincide. Un dettaglio in D12 (`size_by` che torna `rules`) |
| T3 - T6 | nessun file; T6 usa l'op `event` esistente | — | `apply._OPS` resta a 29 (`tests/test_check_audit_round.py:576`) | Coincide: nessuna operazione nuova in T3, T6 e T7 |
| T3 - T7 | `bin/tollgate_hooks/apply.py` (T3: op `plan` e `level`; T7: op `subagent_finish`) | voci diverse dello stesso dizionario | — | Nessun conflitto, ma è lo stesso file: i due task non vanno mai in parallelo (già così: scrittore unico) |
| T3 - T8 | `size`, `size_by`, `slices`, `size_decided` | T8 legge le colonne | `size` può essere `None` (lavoro nato prima di C1) | Coincide (test `test_snapshot_pre_c1_work`) |
| T4 - T8 | `work_items.slices` scritto da `approve_spec` | T8 lo legge | la colonna è `None` per L1, per le fette dalla 2 in poi e per i lavori vecchi | Coincide; la pagina d'uso lo deve dire (D14) |
| T5 - T8 | `docs/uso/comandi.md`, `bin/tollgate_core/cli.py`, `tests/test_cli.py` | T5 aggiunge `ruling`; T8 aggiunge `snapshot` | due sottocomandi diversi nello stesso `build_parser` e nello stesso `if args.cmd` | Coincide. T8 deve mettere `snapshot` **prima** di `db.open_db` (come `status`, `cli.py:495`; `open_db` è a `:515`): oggi `events` e `stats` creano il DB (D15) |
| T4 - T5 | `docs/uso/comandi.md` | T4 la sezione di `approve`; T5 la riga della CLI | — | Come dice l'istruzione: il revisore di T4 legge con `git show`. Altri file in comune: nessuno (vedi §3) |
| T6 - T8 | eventi `stop_asked`, `stop_answered` (`data.tool_use_id`, `session` della busta), `session_start`, `act` | T6 produce; T8 `waiting_items` consuma | `data.tool_use_id`; la colonna `session`; `act` e `session_start` con `work` valorizzato | Coincide con riserva: il `tool_use_id` di `PostToolUseFailure` non è documentato (D16); `session_start` ha `work` nullo fuori dai worktree (progetto: limite dichiarato) |
| T7 - T8 | evento `cost` (`agent`, `type`, `task`, `tokens`, `by_model`, `usd`, `source`) | T7 produce; T8 prende l'ultimo per agente (`seq` più alto) | `data.agent`, `data.task`, `data.tokens` | Coincide. Dopo un `reopen plan` i numeri dei task cambiano ma gli eventi `cost` tengono il vecchio (D13) |
| T3, T5, T7 - T9 | eventi `size_decided`, `ruling`, `cost`; `tollgate snapshot` | T9 li stampa con `flowreg eventi-c1` e `registra` | `data.cause` e `data.applied`; `by_model`; `tokens` uguale a quello di `subagent_stop` | Coincide. `WANTED` e `eventi` non cambiano (`tests/test_b1_scripts.py:1186-1189` resta com'è) |
| T6 - T7 | nessun file in comune (T6 non tocca `_common.py`) | — | — | **Parallelo possibile** (revisione T6 con T7) ma con la cautela di D18 |
| T4 - T6, T5 - T6 | nessun file in comune | — | — | Paralleli ammessi, stessa cautela |
| T10 - tutti | spec rev 36, progetto di C, piano principale | T10 copia i nomi veri | `test_spec_event_types_match_registry` | Coincide |

## 3. Tabella per task

Test «esiste» = il file e, dove il piano lo cita, il nome. «nuovo» = lo crea il task.

| Task | Test previsti contro il codice previsto | File toccati (da P:139-150) | Coerenza interna |
|---|---|---|---|
| **1** | `tests/test_db.py`: `test_latest_version_is_6` esiste (`:198`, classe `MigrationV4Test`); i quattro test nuovi sono ben posti. **`MigrationV6Test.test_migration_keeps_existing_works_outside` (`:307-345`) ha `"6"` fisso (`:333`) e diventa rosso** (D2). `tests/test_events.py` esiste. Le `ALTER TABLE ... ADD COLUMN ... CHECK` funzionano su sqlite 3.46.1 (sonda): riga esistente con `size`, `size_by`, `slices` nulli; `IntegrityError` su `size='enorme'` e `size_by='modello'` | `db.py`, `events.py`, spec 18.4 (riga `**Tipi:**`) | Coerente tranne D2 |
| **2** | `test_config.py:23` esiste e cambia (rosso con 0). `test_events.py:73` esiste e resta verde se `prune_events` resta. `test_start.py`: `test_malformed_sessions_do_not_skip_other_cleanups` esiste a `:1190-1207` (il piano dice `:1188-1207`), `test_prune_events_error_does_not_skip_prune_bound` a `:1209-1219`. **`HousekeepingTest.test_housekeeping` (`:1127-1163`, `assertNotIn(old_event, seqs)` a `:1162`) diventa rosso e il piano non lo nomina** (D1). `test_prune_lookups_of_closed_works` (`:1165`) resta verde (200 giorni, `lookups_days` 180) | `config.py`, `events.py`, `housekeeping.py`, `lookups.py` (il chiamante), `paths.py` (non serve: `state.root / "archive"`) | Coerente tranne D1; D5 (OverflowError) e D8 (permessi della cartella) |
| **3** | Tutti i test nuovi sono ben formati (le firme coincidono, §2). `tests/test_adopt.py:106` esiste: l'ultima riga di stdout resta `prossimo passo: EnterWorktree`. `test_check_post_edit.py:180` esiste e resta verde se `level_records` resta importato e nel `try` (la patch è su `tollgate_checks.post_edit.level_records`). I test di `start` che confrontano le righe guardano solo l'ultima (`test_start.py:123-128`, `:544`, `:819`, `:906`) o la riga dopo `avviso: modelli` (`:1270-1271`): la riga della taglia dopo `lavoro #N avviato` non li rompe. `apply._OPS` resta 29 | `worksize.py` (nuovo), `sizes.py` (nuovo), `start.py`, `post_edit.py`, `apply.py` (op `plan` e `level`), `l2acts.py` (`approve_plan`), `adopt.py` | Coerente. Dettagli: D9 (adopt L1: il testo del piano non è in `_Evidence`), D12 (`size_by`), D19 (idempotenza di `approve_plan`) |
| **4** | `test_l2acts.py` esiste; `test_untrusted_slice_titles_stay_in_a_longer_fence` (`:297-309`, `lines[i+3] == fence`) resta verde se la riga della taglia non sta dentro il recinto. `test_check_acts.py:68-75` ha la forma giusta per `test_size_is_target_arg`. `test_skill_contract.py` e `test_docs.py:79-98` (`argument-hint` tra backtick in `comandi.md`) esistono e legano skill e pagina: si cambiano insieme | `l2acts.py`, `core/acts.py`, `checks/acts.py`, `actapply.py`, `skills/approve/SKILL.md`, `docs/uso/comandi.md` | Coerente. Il messaggio di `_pick` è a `actapply.py:267` (il piano dice `:268-269`); nessun test lo fissa (solo `tests/test_eval_cases.py:2087` cerca «nessun atto da applicare per questa sessione»). D10 (ordine rispetto a `set_phase`) |
| **5** | `test_cli.py:364` ha l'helper `research`, modello per `ruling`. `test_check_cli_calls.py` esiste. `test_brief.py:16` (`ImplBrief(**base)`) regge un campo con default. `test_taskcmd.py` esiste. Sonda: il comando heredoc non è negato (§4.1) | `ruling_cmd.py` (nuovo), `cli.py`, `brief.py`, `taskcmd.py` (`:180`, l'unico costruttore di `ImplBrief`), `skills/execute/SKILL.md`, `docs/uso/comandi.md` | Coerente. D4 (`--by user` dichiarabile da un subagente), D11 (il test del piano è vacuo senza controllo negativo), D20 (maiuscole e `TOLLGATE_X=`) |
| **6** | `test_wrapper.py` esiste (helper `run_wrapper(event, payload)`, `FAKE_MODE`); `test_hook_engine.py:132-170` ha le mappe dell'adattatore; `test_manifest.py:33-55` non fissa la stringa dei matcher ma `assertRegex(tool, ^(?:matcher)$)` e `assertNotRegex("Read", …)`: l'aggiunta di `AskUserQuestion` non lo rompe; `test_check_session.py` esiste. Nessun test del registro fissa «un evento senza controlli» (§5) | `stops.py` (nuovo), `model.py`, `adapter.py`, `runner.py`, `hooks.json`, `hooks/run`, `session.py` | Coerente. D16 (forma di `tool_response` e di `PostToolUseFailure`) |
| **7** | `test_report.py:63` (`transcript_tokens`) esiste; `test_check_common.py`, `test_check_subagent_stop.py`, `test_check_task_verdict.py`, `test_check_final_review.py`, `test_check_audit_round.py`, `test_subagents.py`, `test_reviews.py` esistono. Nessun test confronta i `record("subagent_finish")` per uguaglianza (grep: nessun hit in `tests/`), quindi una chiave `usage` in più non rompe niente. I test dei revisori usano `agent_transcript_path="/non/esiste.jsonl"`: non producono `cost`. `test_approve_finding...`: i due test sulla decisione 6 passano già oggi (`reviews.py:283` è l'unico `SET user_decision`; `test_reviews.py:401-433` ne copre già l'evento) | `report.py`, `checks/_common.py`, `subagent_stop.py`, `task_verdict.py`, `final_review.py`, `audit_round.py`, `apply.py` (op `subagent_finish`), `core/subagents.py` | D3 (None contro `{}`), D21 (due letture della trascrizione). Elenco dei 15 punti in §5.2 |
| **8** | `test_docs_exist` a `tests/test_docs.py:74-76` fissa le pagine di `docs/uso/` (senza `gestionale`): va cambiato. `test_no_local_paths` (`:108`) vieta `/home/` e `MEGA` nella pagina nuova. Misura: §4.4 | `turn.py` (nuovo), `snapshot.py` (nuovo), `cli.py`, `gestionale.md` (nuovo), `comandi.md` | D14 (campi e chiavi), D15 (`snapshot` prima di `open_db`; la migrazione scrive) |
| **9** | `tests/test_b1_scripts.py:1186-1189` esiste ed è il test di `eventi`. `test_flow_registra_collects_the_evidence` (`:854`) pretende `fallimenti.txt` vuoto: `snapshot` deve uscire con 0 nel banco di prova (lo fa, anche senza DB). `test_flow_registra_reports_collection_failures…` (`:1152`) resta verde | `run-b1-flow.sh`, `flowreg.py`, `test_b1_scripts.py`, rapporto, evidenze | D6 (posizione e controllo di `B1_FLOW_EVIDENCE`) |
| **10** | `test_docs` (`test_spec_event_types_match_registry`, `test_limits_match_spec_1_2`) | spec, progetto di C, piano principale | Coerente |

**File di T4, T5, T6, T7** (per decidere i paralleli):

| Task | Sorgenti | Test | Doc e skill |
|---|---|---|---|
| T4 | `bin/tollgate_flow/l2acts.py`, `bin/tollgate_core/acts.py`, `bin/tollgate_checks/acts.py`, `bin/tollgate_flow/actapply.py` | `test_l2acts`, `test_acts`, `test_check_acts`, `test_actapply`, `test_docs`, `test_skill_contract` | `skills/approve/SKILL.md`, `docs/uso/comandi.md` |
| T5 | `bin/tollgate_flow/ruling_cmd.py` (nuovo), `bin/tollgate_core/cli.py`, `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py` | `test_ruling_cmd`, `test_cli`, `test_check_cli_calls`, `test_brief`, `test_taskcmd` | `skills/execute/SKILL.md`, `docs/uso/comandi.md` |
| T6 | `bin/tollgate_checks/stops.py` (nuovo), `bin/tollgate_hooks/{model,adapter,runner}.py`, `hooks/hooks.json`, `hooks/run`, `bin/tollgate_checks/session.py` | `test_check_stops`, `test_wrapper`, `test_check_session`, `test_hook_engine`, `test_manifest` | — |
| T7 | `bin/tollgate_analysis/report.py`, `bin/tollgate_checks/{_common,subagent_stop,task_verdict,final_review,audit_round}.py`, `bin/tollgate_hooks/apply.py`, `bin/tollgate_core/subagents.py` | `test_report`, `test_check_common`, `test_check_subagent_stop`, `test_check_task_verdict`, `test_check_final_review`, `test_check_audit_round`, `test_subagents`, `test_reviews` | — |

- **T6 e T7 non toccano entrambi `_common.py`**: lo tocca solo T7 (T6 lo importa, `stops.py` usa `governing_work`). Nessun file in comune tra T4, T5, T6, T7 salvo `docs/uso/comandi.md` (T4 e T5).
- I test di T6 e di T5 importano, però, file che il task successivo modifica: i test di T6 passano da `tollgate_checks/_common.py` (T7) e da `tollgate_hooks/apply.py` (T7, via `runner`); i test di T4 e T5 lanciano `bin/tollgate` (`cli.py`, T5; `runner`, T6). Vedi D18.

## 4. Sonde

### 4.1 `cli_calls.decide` con il comando di `ruling add` (`sonda_cli_calls.py`)

Comando: `python3 '<bin/tollgate>' ruling add --task 2 --by agent <<'RULING_FINE'` con corpo di tre righe (`cosa: usa la copia dell'utente, perché $HOME \`date\` non c'è`, `perché: il task review start non dice niente`, `costo: nessuno`) e `RULING_FINE`.

| Caso | subagente (`agent_id`) | sessione principale |
|---|---|---|
| `ruling add` (oggi: sottocomando che il parser non ha) | **nessuna decisione** (`[]`) | **`[]`** |
| sottocomando sconosciuto `xyz add`, stesso corpo | `[]` | `[]` |
| controllo positivo: `task start 1`, stesso corpo | `deny coordinator_only` | `[]` |
| programma = `$P` (variabile), `ruling add --task 2` | `[]` | `[]` |

`bash.parse` regge il heredoc con apostrofo, `$` e backtick e dà `['python3', '<bin/tollgate>', 'ruling', 'add']`; il corpo non entra negli argomenti. **`cli_calls` non fa niente con un sottocomando sconosciuto**: lo lascia passare; a negarlo è argparse della CLI (uscita 2). La decisione 5 (`cli_calls` non cambia) regge. Il rischio è nel ramo `BashParseError` (`cli_calls.py:104-115`): lì un subagente è negato se il comando contiene `tollgate` e una delle parole `start`, `task`, `review`… (anche `--task` dà la parola `task`); non succede finché `parse` regge (D11).

### 4.2 `post_edit._plan`: aree e fette (`sonda_areas.py`)

- `ctx.config.profiles` è un `dict[str, dict]` senza la chiave `active` (`Config.profiles`, `config.py:139-141`): è la forma che vuole `worksize.areas`.
- `profiles.vertical_for(path, profiles)` con `ai` su `ai/**`, `infra` su `/vercel.json`, `base` di tipo `cross`: `ai/a.py` e `ai/b.py` → `ai`; `vercel.json` → `infra`; `README.md`, `src/x.py` → `None` (il `cross` non conta). Quindi `areas(["ai/a.py","ai/b.py","vercel.json","README.md"]) == 2`, come vuole `test_areas_counts_verticals_only`.
- Un profilo `vertical` dichiarato **senza `paths`** prende il predefinito `["**"]` e conta come area per ogni file non coperto da altri (provato: `vertical_for("src/x.py")` → `web`). I profili veri hanno sempre `paths`; vale solo per un `tollgate.toml` scritto a mano (D14, nota).
- `specdoc.slices(plan_text())` dà **1** senza la sezione; con `## Fette previste` a tre voci dà **3**. `check_plan` sul piano di prova: `ok`, scope `['src/app.py', 'tests/test_app.py', 'docs/uso.md']`, 2 task.

### 4.3 Migrazione 7 (`sonda_migrazione7.py`)

Su un DB reale alla versione 6 con un lavoro, le tre istruzioni di P:75-77 in `db.tx`: riuscite; riga esistente `(None, None, None)`; `UPDATE size='enorme'` e `UPDATE size_by='modello'` → `IntegrityError`; `size='large', size_by='user', slices=3` accettati. sqlite 3.46.1.

### 4.4 Misura del Task 8 (`sonda_misura.py`)

Copie in `mkdtemp(prefix="tollgate-")`, aperte solo le copie, cartella rimossa (verificato). **169 copie** (88 in `eval-b8`, 81 in `eval-p5`; nessun file `-wal`/`-shm` nel repo), tutte con la tabella `events`. **Schema 6 per le 88 di B8, schema 5 per le 81 di P5**: la misura va fatta sulle copie di B8 (le altre non hanno `lookups`). Su tutte: 1854 eventi, mediana 8 eventi per stato (min 1, max 46), tipi più frequenti `task_change` 542, `phase_change` 348, `commit` 225, `subagent_start` e `subagent_stop` 161. **Sulle 88 di B8: 1002 eventi, 334672 byte di JSONL (busta e `data`, una riga per evento), 334 byte per evento.** Una busta d'esempio, JSON con chiavi ordinate: 284 byte. Sono lavori di eval, corti: il limite della decisione 9 resta.

### 4.5 Quali test di oggi cambiano esito (`sonda_rompe.py`)

Con `events_days = 0` e «0 = mai» e `MIGRATIONS` con una settima voce, su 12 test mirati sono rossi:

| Test | Perché | Nel piano? |
|---|---|---|
| `tests/test_config.py:23` (`LoadTextTest.test_minimal_gets_defaults`) | `0 != 180` | sì (P:181) |
| `tests/test_start.py:1127` `HousekeepingTest.test_housekeeping` (`:1162`) | l'evento di 200 giorni non viene cancellato | **no** (D1) |
| `tests/test_start.py:1190` `test_malformed_sessions_do_not_skip_other_cleanups` (`:1207`) | idem | sì (P:175) |
| `tests/test_db.py:198` `test_latest_version_is_6` | `7 != 6` | sì (P:156) |
| `tests/test_db.py:307-345` `MigrationV6Test.test_migration_keeps_existing_works_outside` (`:333`) | `"6"` fisso | **no** (D2) |

Verdi: `test_events.py:73`, `test_start.py:1165` (`test_prune_lookups_of_closed_works`), `:1181`, `test_db.py` `OpenTest.test_pragmas_and_tables`, `MigrationV2Test.test_from_v1_adds_columns_and_backup`, `MigrationV6Test.test_fresh_db_makes_no_copy`. `test_prune_events_error_does_not_skip_prune_bound` (`:1209`) passa in questa sonda solo perché `prune_events` resta; con il codice del piano la patch su `events.prune_events` non ha più effetto e va spostata (P:175).

## 5. Verifica dei «Fatti verificati» del piano (P:21-48)

| # | Fatto | Esito |
|---|---|---|
| 1 | `EVENT_TYPES` frozenset chiuso, `record_event` rifiuta tipi sconosciuti, busta v1 | **Confermato** (`events.py:13-20` e `:24-41`; il piano dice `:12-41`) |
| 2 | `test_spec_event_types_match_registry` confronta la riga `**Tipi:**` | **Confermato** (`tests/test_docs.py:138-142`; la riga è `S:2140`) |
| 3 | schema alla migrazione 6, copia prima di ogni passo | **Confermato**; il riferimento `db.py:180-236` è largo (`SCHEMA_V6` `:185`, `MIGRATIONS` `:197`, `_migrate` `:243-267`, copia a `:260`). B |
| 4 | `[retention]` 30/180; `housekeeping.run` a ogni `start` (`:241`), prune di tutti gli eventi; `templates/tollgate.toml` senza `[retention]` | **Confermato** (`config.py:92`, `housekeeping.py:39-40`, `events.py:78-81`, spec 1345-1347, `start.py:241` e `:511`; il modello ha 16 righe e nessun `[retention]`) |
| 5 | `start._create` e le righe finali | **Confermato** (`start.py:457-527`; `prossimo passo` a `:526`, `incomplete = steps.failed` a `:509`) |
| 6 | piano registrato in `scope.register_plan`, tre chiamanti | **Confermato** (`scope.py:43-63`, `post_edit.py:15-48`, `apply.py:231-234`, `l2acts.py:236`, `adopt.py:412-425`; grep: nessun altro chiamante in `bin/`; `audit.py:506` usa `set_plan_path`) |
| 7 | `specdoc.slices`, `approve spec <n>` | **Confermato** (`specdoc.py:30-41`, `l2acts.py:152-179`) |
| 8 | `APPROVE_OBJECTS`, `_TARGET_ARG`, `APPLIERS` | **Confermato**; `APPLIERS` è a `actapply.py:238-249` (non `:240-251`), il messaggio di `_pick` a `:267`. B |
| 9 | `research submit` modello; `cli_calls` nega solo i comandi elencati | **Confermato** (`research_cmd.py`, `cli.py:429-440`, `cli_calls.py:19-20` e `:104-115`); sonda §4.1 |
| 10 | hook leggono gli strumenti da `adapter._PRE`/`_POST`; `INPUT_EVENTS`, `CONTROL_EVENTS`; matcher senza `AskUserQuestion`; `record("event", …)` | **Confermato** (`adapter.py:11-15`, `model.py:7-11`, `hooks.json:6-8`, `apply.py:218`; precedente in `research_gate.py:151-154`) |
| 11 | documentazione degli hook su `AskUserQuestion` | **Non verificabile da qui** (rete vietata). In repo: i campioni hanno `tool_use_id` in `PreToolUse` e `PostToolUse` (`spikes/fixtures/hook-inputs/*.json`); nessun campione di `AskUserQuestion` né di `PostToolUseFailure` |
| 12 | `subagent_finish` emesso nei punti elencati | **Confermato** con tre numeri di riga spostati di uno (`subagent_stop.py:107` e `:153`, non `:108` e `:154`); i 15 punti sono in §5.2. B |
| 13 | `transcript_tokens`, `subagents.finish`, `message.usage` e `message.model` | **Confermato** (`report.py:87-108`, `subagent_stop.py:95`, `subagents.py:77-96`, `apply.py:242-245`); `message.model` e `usage` visti nello stream di `claude -p` (`docs/verifiche/evidenze/b3/flusso/passo2/…/claude.jsonl`, 28 righe, modello `claude-sonnet-5-5`); `docs/verifiche/2026-10-08-p0-esiti.md` (E5) conferma `usage` nella trascrizione dei subagenti (il modello lì non è citato) |
| 14 | `PostToolUseFailure`: matcher solo per modifiche e `Bash` | **Confermato** (`hooks.json:8`, `adapter.py:44-49`) |
| 15 | `adopt` crea sempre un lavoro nuovo, legge `spec-approval.md` e `_approved_elsewhere` | **Confermato** (`adopt.py:215-244`, `:346`, `:412-427`) |
| 16 | un lavoro L1 non arriva ad `approve spec`; `reopen spec` solo L2; un livello che sale non riporta a `spec_audit` | **Confermato** (`l2acts.py:153` e `:268`; `phases.py:233-247`) |
| 17 | effetti in attesa: `intents` con `action='effect'`, `state='requested'`; `data.id` | **Confermato** (`effects.py:17-18`, `:31-41`; `intents.py:13`, `:35-37`). Nota: `effects.request` rimette `requested` una riga già eseguita se il comando si ripete |
| 18 | wrapper e `runner` trattano ogni `PreToolUse` come controllo | **Confermato** (`hooks/run:15`, `:176-177`, `:212-215`; `runner.py:30`, `:55-59`, `:203-218`) |
| 19 | `session_start` in `EVENT_TYPES` ma mai registrato | **Confermato** (`grep session_start bin/`: solo definizioni e mappe) |
| 20 | `post_edit.decide` chiama `_plan` prima di `level_records` | **Confermato** (`post_edit.py:60` e `:66`; `test_check_post_edit.py:180-189`) |
| 21 | ripresa con `SendMessage`: stessa riga, `resumes + 1`; `tokens` sovrascritto | **Confermato** (`subagents.py:36-40`, `:77-96`, `coalesce`); che la trascrizione sia cumulativa **non verificabile da qui** (lo guarda la prova) |
| 22 | `registra` esporta `TOLLGATE_STATE`, `flowreg.WANTED` | **Confermato** (`run-b1-flow.sh:603-606`, `flowreg.py:26`) |
| 23 | `reviews.set_decision` è l'unico punto che scrive `user_decision` ed emette `finding` | **Confermato** (`reviews.py:69-76`, `:269-286`; grep `bin/`: letture in `brief.py`, `evaluate.py`, `openpr.py`, un solo `SET user_decision` a `reviews.py:283`) |
| 24 | `status --json` è la sola fotografia di oggi, per repo, senza versione | **Confermato** (`cli.py:186-206`; `current_repo_key` filtra per repo) |
| 25 | 169 copie dello stato negli eval: 88 in `eval-b8/`, 81 in `eval-p5/` | **Confermato**; in più: schema 6 (B8) e 5 (P5), tutte con `events` (§4.4) |
| 26 | `run-b1-flow.sh` fa una prova L1 con `claude -p`, `gh` finto, `origin` nudo | **Confermato** (`run-b1-flow.sh:1-48`; il modello `docs/verifiche/2026-11-12-b7-prova-flusso.md` esiste) |

**Smentiti: nessuno.** Imprecisi nei numeri di riga: righe 3, 8 e 12 (B). Non verificabile: riga 11 (e, per la forma vera, 21).

### 5.1 Chiamanti di `scope.register_plan` (brief, punto 2)

| Chiamante | Riceve `areas`, `slices`, `level`? | Note |
|---|---|---|
| op `plan` di `apply` (`apply.py:231-234`), prodotta solo da `post_edit.py:38` | Sì, se `_plan` li mette nel record (`areas` con `ctx.config.profiles`, `slices` da `specdoc.slices(text)`, `level` nuovo). Nessun test costruisce `record("plan")` a mano (grep), quindi non c'è un record vecchio da reggere; `d.get(...)` con un predefinito è comunque più prudente (B) | `text` è già in `_plan` |
| `l2acts.approve_plan` (`l2acts.py:236`) | `check.scope`, `check.tasks`, `cfg.profiles`, `work["slices"]` sono tutti disponibili | `decide` va dentro l'`if work["plan_sha"] != plan_blob`, **prima** di `phases.set_phase` (D10/D19) |
| `adopt._register_plan` (`adopt.py:425`) | `check.scope`, `check.tasks`, `cfg.profiles`, `level`; in L2 `work["slices"]` | **In L1 il testo del piano non c'è** (`ev.plan = (path, check)`): serve `git.text_at(main, sha, path)` (D9) |
| `audit.py:506` | non è `register_plan` (`set_plan_path`) | nessuna taglia: lo scope arriva con `approve plan` |
| test: `flowkit.register_plan`, `test_scope`, `test_check_*` (≈20 file) | chiamano `scope.register_plan` con la firma di oggi | **Non si rompono**: il piano non cambia la firma, `decide` sta nei chiamanti |

### 5.2 Ogni `record("subagent_finish"` (brief, punto 2)

Trascrizione = `event.raw["agent_transcript_path"]` (presente in ogni `SubagentStop`).

| # | File:riga | Ramo | Trascrizione | Token oggi |
|---|---|---|---|---|
| 1 | `subagent_stop.py:27` | `_readonly`, chiusura generica | sì, ma `_readonly(ctx, row, work)` non riceve `event` | no |
| 2 | `subagent_stop.py:88` | implementatore senza lavoro o worktree | sì | no (calcolati a `:95`, dopo) |
| 3 | `subagent_stop.py:98` | tetto di token | sì | sì |
| 4 | `subagent_stop.py:107` | veti esauriti | sì | sì |
| 5 | `subagent_stop.py:153` | DONE/report valido | sì | sì |
| 6 | `_common.py:78` (`tampered_records`, chiamata da `subagent_stop.py:26`, `task_verdict.py:48`, `final_review.py:40`, `audit_round.py:52`) | sola lettura che ha cambiato file | sì | in `task_verdict` (calcolo a `:50`) e `final_review` (`:42`) il calcolo viene **dopo** la chiamata; in `audit_round` (`:46`) prima |
| 7 | `task_verdict.py:65` | verdetto valido | sì | sì (`:50`) |
| 8 | `task_verdict.py:69` | veti esauriti | sì | sì |
| 9 | `final_review.py:23` (`_invalid(row, work, tokens, what, problems)`, chiamata a `:47` e `:55`) | verdetto non valido | sì | sì, passato come parametro: la firma va estesa |
| 10 | `final_review.py:50` | revisore finale valido | sì | sì (`:42`) |
| 11 | `final_review.py:57` | verificatore valido | sì | sì |
| 12 | `audit_round.py:48` | componente spento | sì | sì (`:46`) |
| 13 | `audit_round.py:61` | veti esauriti | sì | sì |
| 14 | `audit_round.py:71` | report valido | sì | sì |
| 15 | `_common.py:343` (`budget_cut_records`; da `post_agent.py:29` e `prompt_submit.py:30`) | taglio di `maxTurns` | **no**: solo `totalTokens` da `PostToolUse Agent` | `totalTokens` |

`subagents.finish` ha un solo chiamante, l'op `subagent_finish` (`apply.py:242-245`). `subagents.interrupt` (da `session.py`) è un'altra funzione. Dei 15 punti, 14 hanno una trascrizione; l'ultimo resta senza `cost` come dice la decisione 3.

### 5.3 Gli eventi d'ingresso nuovi contro il registro (brief, punto 4)

- `registry._validate` (`registry.py:30-36`) accetta solo eventi in `INPUT_EVENTS`: `stops.py` con `pre_question` e `post_question` è un modulo «rotto» finché `model.INPUT_EVENTS` non li ha. Si cambiano insieme in T6: aggiungere i due nomi a `INPUT_EVENTS`, **non** a `CONTROL_EVENTS`; `adapter._PRE["AskUserQuestion"] = "pre_question"`, `_POST[…] = "post_question"` e, nel ramo `PostToolUseFailure` di `_kind` (`adapter.py:44-49`), un `return "post_question"` per `AskUserQuestion`.
- **Nessun test del registro fissa «un evento senza controlli» né «un controllo con un evento sconosciuto» su `INPUT_EVENTS` reali**: l'unico uso di `INPUT_EVENTS` nei test è `assertIn("post_lookup", INPUT_EVENTS)` (`test_hook_engine.py:140`); i controlli con eventi sconosciuti si provano con moduli finti (`finti_checks`, `test_hook_engine.py:20-83`). Quindi nessun test del registro va cambiato. `tests/test_modelsfetch.py:775-815` carica ogni modulo di `tollgate_checks` e vieta «modelsfetch»/«models_check» nei testi: `stops.py` non deve nominarli.
- Nessun test fissa la stringa dei matcher (`test_manifest.py:33-55` usa regex sugli strumenti). Nessun altro consumatore di `hooks.json` in `evals/`, `spikes/*.sh`, `gate/`.

## 6. Conflitti

**Legenda:** A = blocca o falsa un test/esito; M = difetto reale ma aggirabile; B = precisazione. Per ognuno: dove, cosa, **ruling proposta** e costo se sbagliata. Nessun conflitto tocca una scelta «utente» del progetto di C né un profilo approvato (le scelte «mia scelta» toccate sono segnalate).

### A

**D1 (A). Un secondo test di `start` cambia esito con «mai» e il piano non lo nomina.**
Dove: `P:175` (elenco dei test del Task 2), `tests/test_start.py:1127-1163`.
Cosa: `HousekeepingTest.test_housekeeping` crea un evento di 200 giorni (`:1135`) e asserisce che sia sparito (`:1162`) con la configurazione predefinita. Con `events_days = 0` (decisione 7) resta e il test è rosso (sonda §4.5). Il piano nomina solo `test_malformed_sessions…` (`:1188-1207`) e `test_prune_events_error…` (`:1209`).
Ruling proposta: aggiungere `test_housekeeping` al Task 2, con lo stesso trattamento di `test_malformed…` (`tollgate.toml` del repo di prova con `[retention] events_days = 180`, e l'evento nell'archivio al posto che sparito) e una riga nel ledger. `StartCase.make(toml=…)` lo permette (`test_start.py:350`).
Costo se sbagliata: il Task 2 non chiude `tests/run` verde e l'implementatore deve indovinare una correzione dei test non detta.

**D2 (A). Un test sulla migrazione 6 ha `"6"` fisso e cambia esito con la migrazione 7.**
Dove: `P:156` (Task 1: «anche `test_latest_version_is_6`»), `tests/test_db.py:307-345` (`MigrationV6Test.test_migration_keeps_existing_works_outside`, asserzione a `:333`).
Cosa: il test porta il DB a versione 5, riapre e si aspetta `schema_version == "6"`; con la settima voce il valore è `"7"` (sonda §4.5). Gli altri test di migrazione usano `str(db.latest_version())` e restano verdi; `:341` e `:345` (copie `migrazione-6`) restano giusti.
Ruling proposta: il Task 1 cambia `"6"` in `str(db.latest_version())` (come gli altri), tiene le due asserzioni sulle copie, e lo scrive nel ledger. Il test del piano `test_migration_7_from_6_keeps_rows_and_backs_up` lo completa per la 7.
Costo se sbagliata: Task 1 rosso al primo giro.

### M

**D3 (M). `transcript_cost`: «None» o `{}` per una trascrizione senza righe `usage`; il piano dice due cose.**
Dove: `P:91` (decisione 3), `P:319` e `P:324-325` (Task 7).
Cosa: «l'uso è `None` senza file o con una trascrizione senza righe `usage` (`{}`)» contraddice sé stessa; `transcript_usage` dà `{}` sia per un file mancante sia per uno senza righe `usage` (`test_transcript_usage_missing_file`), quindi `transcript_cost` deve distinguere i due casi con un controllo del file. E `subagents.finish` registra `cost` «quando `usage` non è `None`»: con `{}` registrerebbe un `cost` con `by_model` vuoto, contro la prova del Task 9 («`by_model` non vuoto») e contro «una trascrizione assente o illeggibile resta senza cost».
Ruling proposta: `usage` è `None` per file mancante, illeggibile o senza nessuna riga `usage`; è un dizionario non vuoto altrimenti. `finish` registra `cost` solo con un dizionario non vuoto. Un test per ciascuno dei tre casi.
Costo se sbagliata: eventi `cost` vuoti (rumore per il gestionale) o, al contrario, subagenti con trascrizione valida senza `cost`.

**D4 (M). `ruling add --by user` lo può dichiarare chiunque, anche un subagente.**
Dove: `P:101` e `P:104` (decisione 5), `C:126` («chi ha deciso (agente o utente)»).
Cosa: `cli_calls` non cambia (sonda §4.1: il comando passa per tutti), quindi il campo `by` è dichiarato e non provato. Serve ai dati di taratura (progetto 6, `R13`).
Ruling proposta: `cli_calls` nega a un input con `agent_id` un comando con `ruling add … --by user` (una riga e un test, nello stesso Task 5), oppure la pagina d'uso scrive che `by` è dichiarato. Consiglio la prima: costa poco e fa contare il campo.
Costo se sbagliata: i dati sulle decisioni «prese dall'utente» possono includerne di prese da un agente; si scopre solo a taratura fatta.

**D5 (M). Un `events_days` grande manda in errore `start` con un traceback.**
Dove: `P:108-109` (decisione 7), `housekeeping.py:39` (`step` prende `sqlite3.Error, OSError, ValueError, TypeError`).
Cosa: `now - timedelta(days=800000)` solleva `OverflowError`, che non è tra quelli presi (sonda: 180 va, 800000 e 10^9 sollevano). Oggi vale uguale per `retention_days`/`events_days`; con C1 l'utente è invitato a scrivere un numero.
Ruling proposta: la validazione di `config` rifiuta `events_days`, `lookups_days` e `retention_days` oltre un tetto (per esempio 36500 giorni, con il test accanto a quello del valore negativo), oppure `step` prende anche `OverflowError`. Consiglio il tetto.
Costo se sbagliata: un `tollgate.toml` con un numero esagerato ferma ogni `start` fino alla correzione.

**D6 (M). Posizione e controllo di `B1_FLOW_EVIDENCE`.**
Dove: `P:377` (Task 9, Step 2), `run-b1-flow.sh:60-68`.
Cosa: l'override «vince su `B1_FLOW_RULES` e `B1_FLOW_CASE`» va messo dopo le righe `OUT=` (`:60-66`) ma **prima** della riga del banco di prova (`:68`, `[ "$CHECK" = 1 ] && { OUT="${B1_FLOW_OUT:-$OUT}"; … }`), altrimenti `B1_FLOW_OUT` non sovrascrive più e i test del banco scrivono nelle evidenze vere (`no_repo_evidence`, `test_b1_scripts.py:543`). Il valore entra in un percorso del repo: va validato (`^[a-z0-9-]+$`), come `B1_FLOW_RULES` e `B1_FLOW_CASE` (`:162-163`).
Ruling proposta: come detto, più un test sul modo `controlla` con un valore non ammesso (`../x`) e con `c1`.
Costo se sbagliata: evidenze scritte nel posto sbagliato o un percorso fuori da `docs/verifiche/evidenze/`.

**D7 (M). `snapshot` non è «sola lettura» sul DB di una versione precedente.**
Dove: `P:112` (decisione 8), `cli.py:515` (`db.open_db`).
Cosa: `open_db` esegue `_migrate`: il primo `snapshot` dopo l'aggiornamento migra lo schema da 6 a 7 e scrive una copia in `backup/` (stessa cosa per `events` e `stats` oggi). La pagina d'uso e la spec 3.1 dicono «sola lettura». Con un plugin vecchio su un DB già migrato: `DbTooNew` (uscita 1).
Ruling proposta: nessun codice; la pagina `gestionale.md` e la riga di 3.1 dicono «sola lettura dei dati: il primo avvio dopo un aggiornamento può migrare lo schema, con una copia in `backup/`». Il caso «senza DB non crea niente» resta vero solo se `snapshot` sta nel ramo che controlla `state.db_path.exists()` (D15).
Costo se sbagliata: un gestionale che si aspetta uno stato intatto trova una copia in più.

### B

**D8 (B). Permessi e punto di patch dell'archivio.** `P:109-190`: `write_atomic` (`fsutil.py:8-21`) crea il padre con `mkdir(parents=True)` e i permessi predefiniti, non `0o700` come `paths.ensure_dirs`/`sessions.mark_bound`: la riga «creata con i permessi della cartella di stato» chiede un `mkdir(mode=0o700)` esplicito. I test che patchano `fsutil.write_atomic` (P:185, P:187) funzionano solo se `events.py` lo chiama come `fsutil.write_atomic(...)`, non con `from .fsutil import write_atomic`. Ruling: dirlo al Task 2. Costo: test che non intercettano.

**D9 (B). `adopt` L1: manca il testo del piano.** `P:84` (slices «da `specdoc.slices(<testo del piano>)` in L1») contro `adopt.py:412-427` (`ev.plan = (path, check)`, nessun testo). Ruling: leggere il testo con `git.text_at(main, sha, path)` in `_register_plan`. Costo: un `slices` sbagliato (sempre 1) per un piano L1 adottato con `## Fette previste`.

**D10 (B). Ordine in `approve_spec` e `approve_plan`.** `P:257`, `P:236`: `phases.set_phase` fa la copia del DB dopo il commit (`phases.py:203-211`); una `UPDATE slices` e un `decide` **dopo** `set_phase` restano fuori da quella copia e, se falliscono, l'atto è già consumato e la fase già cambiata. Ruling: in `approve_spec`, `UPDATE`+`decide` in un solo `db.tx` **prima** di `set_phase` (che vuole di essere fuori da una transazione); in `approve_plan`, `decide` subito dopo `register_plan` e prima di `set_phase`. Costo: una taglia mancante dopo un'interruzione, recuperabile solo con `approve size`.

**D11 (B). `test_subagent_may_add_ruling` è vacuo da solo.** `P:278`: se il programma non è riconosciuto, `decide` ritorna `[]` per qualunque comando. Ruling: nello stesso test, un controllo negativo con lo stesso corpo e `task start 1` che dà `deny coordinator_only` (la sonda lo fa); e un caso con il programma da `program_command(ctx.plugin_bin)`. Costo: un test che non protegge.

**D12 (B). `size_by` non torna `rules` quando la taglia non cambia.** `P:207` («scrive `size` e `size_by` se `applied` è cambiata») contro `P:88` («dopo `approve spec <n>` con `n > 1` su una taglia dell'utente `size_by` torna `rules`»): con la taglia dell'utente già `large` non cambia `applied` e `size_by` resterebbe `user`. Ruling: scrivere le due colonne se `applied` o `by` cambiano. Costo: `size_by` sbagliato, e la riga ripete «scelta dall'utente».

**D13 (B). Costo per task dopo `reopen plan`.** `P:113`, `P:91`: `subagents.task` viene azzerato da `scope.reset_plan` (`scope.py:32`) ma gli eventi `cost` tengono il numero vecchio; `cost.by_task` della fotografia può unire task del piano vecchio e del nuovo. Ruling: la pagina d'uso lo scrive come limite (un `reopen plan` rinumera i task). Costo: un conto per task sbagliato nei lavori riaperti.

**D14 (B). Pagina d'uso e fotografia, precisazioni.** (a) `work_items.slices` è nullo per L1, per le fette dalla 2 in poi e per i lavori vecchi; (b) le chiavi di `cost.by_task` sono stringhe dopo `json.dumps`; (c) il progetto 10 elenca anche «avanzamento, dipendenze, coda»: C1 non li ha (PP:47 li rinvia a C4 e C5); (d) un profilo `vertical` senza `paths` conta come area per ogni file (sonda §4.2). Ruling: righe in `gestionale.md`. Costo: ambiguità per il gestionale.

**D15 (B). `snapshot` prima di `open_db`.** `P:363`: `events` e `stats` oggi passano da `db.open_db` (`cli.py:515`) e **creano il DB** se manca; solo `status` controlla `state.db_path.exists()` (`:495`). Il test `test_cli_snapshot_without_db` lo richiede: il ramo di `snapshot` va nel blocco di `status`. Ruling: dirlo al Task 8. Costo: il test fallisce, non si perde dato.

**D16 (B). `stop_answered` senza `tool_use_id`.** `P:94`, `P:96`: non c'è nessun campione di `PostToolUseFailure` in `spikes/fixtures/hook-inputs/`, quindi non si sa se porta `tool_use_id`; senza, una domanda rifiutata non si lega alla sua `stop_asked` e resta «in attesa» fino al primo atto o `session_start`. E `adapter.to_event` mette `tool_response = None` se non è un dizionario (`adapter.py:66`): `stops` deve leggere `event.raw` per non perdere una risposta in forma di stringa o lista. Ruling: `stops` legge da `event.raw`; la prova vera di C6 chiude il dubbio (già PP:116). Costo: le risposte restano nulle, la domanda resta registrata.

**D17 (B). Riga `**Tipi:**` e test dei nomi.** `test_spec_event_types_match_registry` prende **ogni** parola minuscola con underscore tra backtick della riga (`tests/test_docs.py:142`): la riga nuova non deve avere altri backtick (nemmeno «`data`»). `BareProgramInMessagesTest` (`tests/test_manifest.py:655-690`) vieta nelle stringhe di `bin/` il testo `tollgate ruling` e `tollgate snapshot` (i nuovi sottocomandi entrano nell'elenco dal parser): i messaggi di `ruling_cmd`, `sizes`, `worksize` devono usare `<programma>`/`program_command` e `/tollgate:…` (con i due punti passa); `test_agents_and_skills_never_write_a_bare_program_name` (`:440-447`) vale per `skills/*/SKILL.md`. Ruling: dirlo ai brief dei Task 1, 4, 5, 8. Costo: un giro di correzione.

**D18 (B). Revisioni in parallelo: file disgiunti, import no.** `istruzioni di esecuzione, «Lavori in parallelo»`. I test di T6 importano `_common.py` e `apply.py` (modificati da T7, tramite `stops`/`runner`); quelli di T4 e T5 lanciano `bin/tollgate` (T5 modifica `cli.py`, T6 `runner.py`/`adapter.py`/`model.py`). Un revisore che lancia i test mentre l'implementatore dopo scrive può vedere rossi transitori. Ruling: nella `Ruling:` che ammette il parallelo, il revisore legge con `git show <commit>` e, se deve lanciare dei test, lo fa su una copia esportata (`git archive`) in una cartella `tollgate-…` temporanea, mai nel worktree vivo. Costo: falsi rossi nelle revisioni.

**D19 (B). Idempotenza di `approve_plan`.** `l2acts.py:230-239`: la registrazione avviene solo se `work["plan_sha"] != plan_blob`; con `decide` dentro lo stesso `if`, una ripetizione dopo interruzione (`test_repeat_after_interruption_does_not_register_twice`, `test_l2acts.py:476`) non registra un secondo `size_decided`; con `decide` fuori, ne registra due. Ruling: dentro l'`if`, e il test lo fissa (`fl.events("size_decided")` ha un solo `plan`). Costo: un evento doppio, innocuo.

**D20 (B). Parsing del testo delle ruling e `bash_rules`.** `P:100`: `startswith("cosa:")` distingue le maiuscole? Un implementatore scrive «Cosa:» e la riga diventa continuazione («campo mancante»). E `bash_rules.py:22` nega il comando intero se un `TOLLGATE_X=` compare nel testo (`_TOLLGATE_ASSIGN` su `raw`, corpo del heredoc compreso). Ruling: le etichette senza distinzione di maiuscole; la riga di brief/skill avvisa che un `TOLLGATE_X=` non si può scrivere. Costo: ruling rifiutate per motivi poco chiari.

**D21 (B). Due letture della trascrizione e dettagli di forma.** `transcript_cost` chiamato così com'è legge il file due volte (`transcript_tokens` e `transcript_usage`); `tokens` è la somma di `input + cache_creation + output` di `by_model` (lo dice il test), quindi basta una lettura. Inoltre: `subagents.finish(usage=…)` con `tokens=None`; `_readonly` senza `event`; `final_review._invalid`; `prune_events` che resta come codice morto non archiviante (meglio un involucro che chiama `archive_and_prune`, o toglierlo e spostare `test_events.py:73`); riferimenti di riga imprecisi del piano (`actapply.py:238-249` e `:267`, `subagent_stop.py:107` e `:153`, `db.py` 185-267). Nessun costo se non detto.

Tocca una scelta marcata «mia scelta» del progetto: D12 (taglia e `size_by`), D13; la precisazione che `approve size grande` non basta per C5 (P:88, PP:45) è già una scelta del piano e coerente con C:65 e C:113. Nessuna tocca una scelta «utente».

## 7. Esito dei punti da guardare apposta

1. **Test che fissano i valori di oggi, le righe di `start`, i matcher.** Rossi senza una ruling: `tests/test_config.py:23` (nel piano); `tests/test_start.py:1127-1163` `test_housekeeping` e `:1190-1207` `test_malformed_…` (il secondo nel piano, il primo **no**: D1); `tests/test_start.py:1209` (nel piano, da spostare); `tests/test_db.py:198` (nel piano) e `tests/test_db.py:333` (**no**: D2). Verdi: `tests/test_events.py:73` (se `prune_events` resta), `tests/test_db.py:459`. Righe di `start` e `adopt`: nessun confronto esatto di tutte le righe; i test guardano `splitlines()[-1]` (`test_start.py:123-128`, `:544`, `:819`, `:906`; `test_adopt.py:106`; `test_closing.py:263`; `test_criteria_p3a.py:49`, `test_criteria_p3b.py:311`) o `r.lines[at+1]` dopo `avviso: modelli` (`test_start.py:1270-1271`): una riga della taglia dopo `lavoro #N avviato` e prima di `prossimo passo` non li rompe. `test_l2acts.py:297-309` (recinto) resta verde se la riga non sta nel recinto. Matcher di `hooks.json`: `tests/test_manifest.py:33-55` usa regex sugli strumenti (`assertNotRegex("Read", …)`), nessun test fissa la stringa: nessuno rotto da `AskUserQuestion`. `test_check_audit_round.py:576` (`len(apply.OPS) == 29`) resta vero: nessuna operazione nuova.
2. **Chiamanti di `register_plan` e di `finish`.** §5.1 e §5.2: tre chiamanti di `register_plan` (uno solo costruisce `areas` e `slices` dal testo; `adopt` L1 non ha il testo: D9), quindici `record("subagent_finish")` (14 con trascrizione). Nessuna firma esistente si rompe con un parametro in più: nessun test confronta i record per uguaglianza.
3. **`post_edit._plan`.** `ctx.config.profiles` è `dict[str, dict]` come vuole `worksize.areas` (§4.2); `vertical_for` dà `None` per un file del generico e per un profilo `cross`; `specdoc.slices` dà 1 senza sezione e 3 con tre voci. La riorganizzazione (livello prima del piano) regge `test_level_failure_does_not_block_plan_registration` (`test_check_post_edit.py:180-189`) se `level_records` resta nel `try` e il nome importato resta `level_records`; l'ordine di applicazione `level + plan` non cambia; l'L0 che cresce (`phase` con causa `l0_grew`, che porta a L1 da solo, `phases.py:227-231`) non produce un record `level` ma non registra nemmeno un piano in quel passaggio (`_plan` vuole la fase `plan`).
4. **Eventi d'ingresso nuovi.** §5.3: nessun test del registro da cambiare; si cambiano insieme `INPUT_EVENTS`, `adapter` (`_PRE`, `_POST`, ramo `PostToolUseFailure`) e `stops.py`.
5. **`hooks/run` e `runner.run_hook`.** Oggi `CONTROL` è fissato a `hooks/run:15` (prima di leggere l'input a `:16`) e usato a `:177` e `:212`; `runner.py:203` (`control = hook_event in _CONTROL_HOOKS`), `:215` e `:218`. La regola della decisione 4 si inserisce senza cambiare gli altri strumenti: nel wrapper un `case`/`if` dopo `INPUT="$(cat)"` che mette `CONTROL=no` solo se `tool_name` è `AskUserQuestion` (un `awk` in più per ogni `PreToolUse`, B); nel runner `control = hook_event in _CONTROL_HOOKS and not _asks_user(stdin_text)` a `:203`. Nelle stdin reali `tool_name` precede `tool_input` (campioni non ordinati di `spikes/fixtures/hook-inputs/samples.json`: `session_id, transcript_path, cwd, …, tool_name, tool_input, tool_use_id`), quindi la «prima occorrenza» è quella di primo livello. Test che fissano il comportamento di oggi: `test_wrapper.py:104-126` (`test_control_errors_become_2`, `test_timeout_becomes_2`, `test_informative_errors_become_0`, `test_zero_and_two_pass_through`), `:300` (`test_without_python`); `test_hook_engine.py:295` e `:333` (`"{rotto"` su `PreToolUse` → 2), `:299` (`PostToolUse` → 0). Tutti usano `tool_name` `Bash` o nessuno: restano verdi.
6. **`cli_calls` e `ruling add`.** §4.1: un subagente non è negato, la sessione principale neppure; `task start` con lo stesso corpo è negato al subagente. Con un sottocomando sconosciuto `cli_calls` non fa niente (lo respinge argparse con 2). D4, D11.
7. **Riga `**Tipi:**` e `test_spec_event_types_match_registry`.** `S:2140`, `tests/test_docs.py:138-142`: l'insieme dei nomi tra backtick deve essere esattamente `EVENT_TYPES`; Task 1 aggiorna la riga nello stesso commit (D17).
8. **Misura del Task 8.** §4.4: 169 copie, schemi 6 (88) e 5 (81), tutte con `events`; B8: 1002 eventi in 88 stati, 334 byte per evento.
9. **`adopt`.** `_Evidence` (`adopt.py:39-49`) è costruita in un solo punto (`:263`): il campo `spec_own: bool = False` si aggiunge dopo `cap`, prima di `notes`, senza rompere niente; `_l2_proofs` (`:229-244`) ha un solo chiamante (`_gather`) e nessun test; `spec_header` viene da `approvals.approval_paths(issue)[0]` o, senza, da `_approved_elsewhere` (`:215-226`) tramite il `spec_sha` del piano: `spec_own` è vero solo nel primo caso. Gli `step(...)` attorno a `create_work` (`:346`) e `_register_plan` (`:381`) sono: PR, tetto, piano, deroghe, copia DB, radici, segnalino, exclude, issue; nessun test fissa l'ordine degli eventi (solo `fl.events("phase_change")[-1]`, `test_adopt.py:109`). `tests/test_adopt.py:106` resta verde.
10. **`approve spec`, `APPROVE_OBJECTS`, `_TARGET_ARG`, `APPLIERS`, `_pick`.** `acts.py:12-13`, `checks/acts.py:12`, `actapply.py:238-249` e `:252-270`. Nessun test fissa l'elenco degli oggetti (grep: nessun hit su `APPROVE_OBJECTS`/`_TARGET_ARG` in `tests/`); `test_check_acts.py:44` (`boh 3`) resta rifiutato; `test_docs.py:79-98` e `test_skill_contract.py` legano `argument-hint` e pagina: si cambiano insieme.
11. **`snapshot`.** Nessun sottocomando `snapshot` o `ruling` in `cli.py` (grep); `status --json` è per repo, senza versione (`cli.py:186-206`); `paths.program_command` come dice il piano (`paths.py:16-19`). `test_docs_exist` (`:74-76`) fissa le pagine di `docs/uso/` (senza `gestionale`). Nessun elenco dei sottocomandi nei test oltre a quello che il parser stesso fornisce a `BareProgramInMessagesTest` (D17) e a `test_skill_contract.call_problems`.
12. **Task 9.** `spikes/run-b1-flow.sh`: `OUT` a `:60-66`, riga del banco a `:68`, `registra` a `:588-659` (`export TOLLGATE_STATE` a `:603-606`); `controlla` stampa `cartella delle uscite: $OUT` (`:247`), quindi il test sul modo `controlla` del piano è fattibile; `flowreg.py` `WANTED` a `:26`; `evals/scrub.py anonymize <cartella> <utente> <host>` esiste. `tests/test_b1_scripts.py:1186-1189` è il test di `eventi`. D6.
13. **Nomi dichiarati esistenti.** `test_latest_version_is_6` → `tests/test_db.py:198`; `test_prune_events_error_does_not_skip_prune_bound` → `tests/test_start.py:1209`; `test_malformed_sessions_do_not_skip_other_cleanups` → `:1190`; `test_level_failure_does_not_block_plan_registration` → `tests/test_check_post_edit.py:180`; `test_spec_event_types_match_registry` → `tests/test_docs.py:138`; `test_every_skill_documented` → `:79`; `test_docs_exist` → `:74`; `test_committed_evidence_has_no_long_web_results` → `tests/test_b1_scripts.py:1142`; `transcript_tokens` → `bin/tollgate_analysis/report.py:87`; `research.submit_command` → `bin/tollgate_analysis/research.py:258`; `governing_work` → `bin/tollgate_checks/_common.py:223`; `tampered_records` → `:76`; `budget_cut_records` → `:335`; `reviews.set_decision` → `bin/tollgate_core/reviews.py:269`; `naming.branch_name` → `bin/tollgate_analysis/naming.py:18`; `fsutil.write_atomic` → `bin/tollgate_core/fsutil.py:8`; `db.tx` → `bin/tollgate_core/db.py:206`; `tests.hookkit.Lab` → `tests/hookkit.py:67`. Tutti esistono.

## 8. Risposta breve

- File: `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/c1/.superpowers/sdd/2026-11-20-tollgate-c1-tracciamento-locale/preflight-scan.md`
- Conflitti: **A 2**, **M 5**, **B 14** (21).
- A: D1 (`tests/test_start.py:1127` `test_housekeeping` rosso con `events_days = 0`, non nominato dal piano); D2 (`tests/test_db.py:333` ha `"6"` fisso e diventa rosso con la migrazione 7, non nominato dal piano).
- Fatti smentiti: nessuno.
