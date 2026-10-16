# SDD ledger — plan: docs/superpowers/plans/2026-10-09-tollgate-p2-guardrail.md

Spec: docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md (rev 20). Worktree: .claude/worktrees/p2-guardrail, ramo p2-guardrail, base d87383a. Baseline tests/run: 124 test OK.

Ruling: Task 1 Step 5 (documentazione D1-D3) lo esegue un subagente claude-code-guide (sonnet) lanciato dal controller, non l implementatore — gli implementatori non lanciano subagenti; risposta in task-1-docs.md — costo se sbagliato: nessuno, stessa fonte.
Ruling: pre-flight scan delegato a un analista sonnet in sola lettura (preflight-scan.md), giudicato dal controller prima del Task 2 — il Task 1 non scrive codice, quindi corre in parallelo — costo se sbagliato: un conflitto sfuggito emerge nelle revisioni dei task.
Task 1: dispatched (sonnet), base d87383a
Ruling: INJECT_MODE (Task 12) = additionalContext per session_start, prompt_expansion, pre_edit, pre_bash, pre_agent, pre_send_message, pre_mcp, post_edit, post_bash, post_agent, post_skill, subagent_start (arriva al subagente); subagent_stop: uscita 2 + stderr; subagent_handback: nessuna iniezione — fonte documentazione ufficiale (task-1-docs.md), non esperimento — costo se sbagliato: un contesto iniettato ignorato; il deny non ne dipende.
Ruling: dependencies (Task 13) senza version: i tag di superpowers sono v6.4.1, la doc chiede superpowers--v6.4.1, un intervallo farebbe fallire l installazione; controllo di versione in start (11.1, P3) — costo se sbagliato: nessun vincolo di versione in installazione fino a P3.
Ruling: taglio maxTurns in background/alla ripresa si riconosce da UserPromptSubmit con prompt che inizia con <task-notification> e contiene «stopped at its N-turn limit» (task-id = agent_id). Si aggiunge in P2: evento d ingresso prompt_submit (adattatore Task 12, hooks.json Task 13 con il wrapper che esce 0 subito se il prompt non contiene task-notification, cosi Python non parte a ogni prompt), controllo nel Task 18 (task -> blocked/needs_you, chiusura riga subagente come il taglio in primo piano K2); spec 3.2 aggiornata nel Task 20 — il piano (Task 1 step 6) prevede la riga se l evento esiste; stale_minutes resta rete — costo se sbagliato: un evento e un modulo in piu da togliere.
Ruling: campioni samples.json con permission_mode acceptEdits (E9 rifatto: in -p con manual le Write sono negate) — costo se sbagliato: nessuno, i controlli non leggono permission_mode.
Task 1: implementer DONE_WITH_CONCERNS, commit 3da986d; review dispatched (sonnet)
Task 1: minor (deferred): spikes/run-p2-experiments.sh lancia E9 con manual, ma i campioni vengono dalla riesecuzione acceptEdits (e9b) — lo script non lo riflette.
Ruling: l evento prompt_submit entra nella spec 3.2 gia nel fix del Task 1 (rev 21 in corso), non nel Task 20 — evita una spec che si contraddice tra 3.2 e 6.3 — costo se sbagliato: nessuno.
Task 1: fix round 1/5 (3 addressed, 0 open — 6.3 taglio, 11.1 version, D1 condizionale; commits 3da986d..fb338d9)
Task 1: complete (commits d87383a..fb338d9, review clean)
Nota per Task 12/13/18/20: il testo del piano non cita prompt_submit — va portato nei dispatch (ruling sopra).
## 1. Tabella per coppie di task

Colonne: Task A | Task B | cosa produce A / cosa consuma B | esito. Le righe sono raggruppate; dove una riga copre più simboli, tutti sono stati incrociati col codice effettivamente eseguito.

| Task A | Task B | Cosa produce A / cosa consuma B | Esito |
|---|---|---|---|
| 1 | 8 | `samples.json`: `PostToolUse-Agent-maxturns-cut`, `PostToolUse-Agent-foreground-manual` (già da P0) / `test_report.test_turn_cut_from_real_sample` (righe 3441-3448) | ok |
| 1 | 12 | Chiavi nuove `PreToolUse-Write`, `PostToolUse-Write`, `PreToolUse-Edit`, `PostToolUse-Edit`, `PostToolUse-Skill`, `PreToolUse-Write-subagent` (presenti, verificate) / `hookkit.sample` (4830-4847), che ora non usa più il ripiego | ok |
| 1 | 12 | Esito D2 / `adapter.INJECT_MODE` (5267-5269) | conflitto minore: `SubagentStop: "stderr"` non è visibile al modello con uscita 0 (conflitto 6) |
| 1 | 13 | Esito D1 («no», nessun `version`) / `plugin.json` (6245-6256) | conflitto minore: il blocco di codice contiene ancora `version` (conflitto 5) |
| 1 | 12, 13, 18 | Esito E7/E8 e spec rev 21 (3.2 riga 232, 6.3 riga 411): evento d'ingresso `prompt_submit` / niente nel piano | conflitto che blocca (conflitto 2) |
| 2 | P1 | `db.MIGRATIONS` con migrazione 2 / `db._migrate` (`bin/tollgate_core/db.py:147-166`) e test P1 sui backup | conflitto che blocca (conflitto 1) |
| 2 | 3 | `db.latest_version()`, `tasks.add_task`, colonne `tasks.skills_required` / `scope.register_plan`, test | ok |
| 2 | 12 | `sessions.touch/alive/bound_work/work_for_path/mark_bound`, `subagents.start/touch/get/set_name/set_report/add_veto/finish/interrupt/by_name/running`, `tasks.take_pending` / `context.py`, `apply.py`, `runner.py` | ok, firme identiche |
| 2 | 18, 19 | `subagents.is_stale` (riga 699) / `agents.live_writers` (8158) | ok per il codice; `is_stale` manca dall'elenco **Produces** del Task 2 (riga 284): solo documentale |
| 2 | 18 | `tasks.assign(..., pending=)` , `tasks.PENDING` / test (8003, 8051, 8083) | ok |
| 3 | 10 | `receipts.add(..., exit_code=...)` / `verify.run_verify` (4473-4489) | ok |
| 3 | 12 | `scope.paths/register_plan/set_plan_path`, `effects.*`, `offlog.import_log` / `context.scope`, `apply._OPS`, `runner` (5744) | ok |
| 3 | 16 | `effects.effect_key/effect_id/get/request/mark_executed/executed_at` / `tollgate_checks/effects.py` (7497-7578) | ok |
| 3 | 19 | `receipts.latest(conn, work, sha)`, `any_since` / `subagent_stop` (8694-8705) | ok |
| 3 | 10 | Regola «`uncounted` verde con `allow_no_tests` e uscita 0»: scritta due volte, `dod._receipt.ok` (1237-1242) e `verify.counts_green` (4399-4401) | ok, ma duplicazione di una regola di business (nessuna Single Source of Truth) |
| 3 | 13 | `offlog._LINE` (1197) / righe scritte dal wrapper (6130-6136, 6146) | ok: `…T..:..:..000000Z off [epoch]` e `… on` combaciano |
| 4 | 5, 6, 8 | `globs.match/match_any` / `level.sensitive_in`, `testguard.check`, `waivers.covers` | ok; `test_analysis_isolation` (1500-1528) conferma che `tollgate_analysis` non importa il resto |
| 4 | 10, 12, 15 | `profiles.active_profiles/task_skills/min_level`, `plan.check_plan(kwargs)` / `verify.gate_commands`, `context.guard_config`, `post_edit._plan`, `_common.level_records` | ok |
| 4 | P1 | `config.load_config_text` + avviso `profili attivi` / `tests/test_config.py` | conflitto minore (conflitto 4: il test usa un nome non importato) |
| 5 | 9, 15 | `level.FileChange` e attributi / `git.Change` (3862-3869), `level_records` | ok (duck typing: `path, added, removed, binary, old_path`) |
| 5 | 10, 19 | `junit.parse_junit`, `Junit` / `verify._run_one`, `report` | ok |
| 6 | 8 | `testguard.Violation` / `waivers.covers` (usa `waiver_type`, `kind`, `ids`) | ok |
| 6 | 12, 17 | `GuardConfig(...)`, `Change`, `check` / `context.guard_config` (5423-5436), `_common.commit_violations` (7789-7813) | ok |
| 6 | 15 | `Violation("out_of_scope", ...)` aggiunto dal Task 15 (riga 2129) / `writes.py` 7064 | ok |
| 7 | 16 | `bash.parse/…/effect_reason/script_path/text_danger` / `bash_rules.py`, `effects.py` | ok per i nomi; lacune di riconoscimento (conflitto 7) |
| 8 | 11, 12, 15 | `waivers.parse/dumps/next_id/path_for/unresolved/Waiver/WaiverFile` / `waiver_cli`, `context.waiver_file`, `writes` | ok |
| 8 | 18, 19 | `report.is_turn_cut/parse_report/transcript_tokens` / `post_agent`, `subagent_stop` | ok |
| 9 | 10-19 | `git.toplevel/head/branch/changes/commit_changes/diff_size/rev_list/fingerprint/is_clean/…` | ok per firme; `git.toplevel` ritorna `None` per percorsi sotto `.git/` (conflitto 3) |
| 10 | 11, 12 | Modifiche successive a `cli.py` (verify, waiver/block, hook): le ancore indicate (`dopo events`, `prima di conn = db.open_db`, `dopo if args.cmd is None:`) esistono e combaciano | ok |
| 10 | 12 | `tests/helpers.make_origin_repo` / `hookkit.Lab` (4855), `test_wrapper` (5927) | ok |
| 10 | 19 | `verify.counts_green` / `subagent_stop` (8695) | ok |
| 12 | 13 | `bin/tollgate hook <evento>` / wrapper | ok |
| 12 | 14-19 | `Event`, `Decision`, `record(op, **data)`, `Ctx`, `hookkit.Lab/sample/DROP`; operazioni `record` usate dai moduli: `subagent_name, subagent_report, subagent_finish, task, block, subagent_veto, skill_used, commit, task_commit, effect_request, effect_execute, subagent_interrupt, subagent_start, phase, level, expire_acts, bind, act, plan, plan_path` | ok: tutte presenti in `apply.OPS`, campi dei dati combaciano |
| 12 | 13 | `runner._off_active` (formato `until=<epoch>`) / wrapper (6126) | ok |
| 13 | 12 | `bound/<sessione>` scritto da `sessions.mark_bound` / letto dal wrapper (6167) e dal runner (5740) | ok, con il caso di sessione vuota (conflitto 10) |
| 14 | 15 | `_common.locked_docs/is_docs_md/orphan_tg/governing_work/explain` / `writes.py` | ok |
| 15 | 17 | `_common.scope_exempt/level_records` / `commit.py`, `post_bash.py`, `_common.commit_violations` | ok; il Task 17 aggiunge import a metà file di `_common.py` (stile) |
| 16 | 17 | `bash_rules` (ordine 20), `commit` (25), `effects` (30): tutti su `pre_bash` | ok: il primo `deny` vince, i `record` si scrivono comunque |
| 18 | 19 | `agents.live_writers`, `subagents.finish(state="cut"/"budget"/"tampered")` / `subagent_stop` | ok, `STATES` lo permette |
| 18 | 14 | `SubagentStart`: `take_pending` / `tasks.assign` nei test | ok |
| 20 | 13 | `hooks/run` e `bin/tollgate` veri / `tests/test_criteria_p2.py` | ok |
| 20 | spec/piano principale | Elenco decisioni da riportare in rev 21: titolo Files (riga 8746) dice 1, 6, 7, 13, 15, 22; Step 3 (8826-8831) cita anche 4, 5, 9, 10, 11; l'intestazione «Decisioni» (riga 31) dice 1, 2, 6, 7 | ok funzionalmente, tre elenchi incoerenti (conflitto 12) |
| Tutti | P1 (funzioni usate) | Verificate nel codice reale con la firma usata: `phases.create_work/bind_session/set_phase/set_level/open_block/get_work/SEQUENCES/_FORWARD_CONDITION/BLOCK_TYPES/TransitionError`, `acts.record_act/find_usable/consume/expire_stale/invalidate_finish/ACT_TYPES/APPROVE_OBJECTS/ActError`, `tasks.add_task/task_event/add_skill_used/get_task/TaskTransitionError`, `events.record_event`, `db.open_db/tx/backup/DbError/DbCorrupt/BIN_PATH/restore_hint/latest_version`, `config.load_config/load_config_text/ConfigError/ConfigNotFound/Config.get/.profiles`, `paths.resolve_state/State/repo_key/ensure_dirs`, `clock.fmt/parse/now`, `dod.compute_dod` | ok |
| Colonne migrazione 2 | usi | `session_seen`, `subagents.last_seen/vetoes/report`, `tasks.pending`, `work_items.level_cap_paths`, indice `subagents_work` | ok: tutte usate come definite (`level_cap_paths` solo letta da `_common.level_records`, 6968; la scrive P3) |

---

## 2. Tabella per task

| Task | Coerenza interna (test previsti vs codice previsto; file creati vs toccati dopo) | Esito |
|---|---|---|
| 1 | Già eseguito e committato (`3da986d`, `fb338d9`). Il rapporto `docs/verifiche/2026-10-09-p2-verifiche.md` contiene due «conseguenze per il piano» che il piano non ha assorbito: `prompt_submit` e dipendenza senza `version`. | ok per sé; origina i conflitti 2, 5, 6 |
| 2 | Test e codice coerenti (`MigrationV2Test`, sessioni, subagenti, `tasks.assign`). Ma la migrazione 2, aggiunta in fondo a `MIGRATIONS`, fa fare a `_migrate` un backup `migrazione-2` anche su un DB appena creato (il ciclo passa per la 1 e poi `current>0`): rompe `tests/test_db.py:59-62` (`test_fresh_db_makes_no_backup…`), `tests/test_db.py:71-85` (`test_migration_makes_backup_first` aggiunge una seconda migrazione numero 2, ora duplicata, quindi niente tabella `extra` né backup) e `tests/test_phases.py:96-100` (conta 2 backup invece di 1). Il piano ritocca solo le righe 39 e 56 di `test_db.py` (riga 289). Il passo 10 (`tests/run` verde, 768-771) non può riuscire. | conflitto 1 (blocca) |
| 3 | `scope`, `receipts`, `effects`, `offlog`, `dod._receipt`: test e codice coerenti, nessun test vuoto. Il Modify di `dod.py` combacia con la funzione esistente; l'import di `receipts` in `test_dod.py` va aggiunto (il piano lo dice). | ok |
| 4 | `globs/protected/profiles/plan`: tutti i test passano; i casi di `globs` sono corretti sul dialetto gitignore. Il test aggiunto a `tests/test_config.py` (1532-1538) usa `config.load_config_text`, ma il file importa solo `load_config_text` (righe 6-8): `NameError`. Il passo 8 (`tests/run`) non riesce finché non si corregge. | conflitto 4 (minore) |
| 5 | `level`, `junit`: coerenti, test significativi (soglie, binario, tetto, entità XML). | ok |
| 6 | `scan/testids/testguard`: coerenti. `test_binary_and_latin1_do_not_crash` (2289-2293) non prova il latin-1: passa stringhe già decodificate, mentre la decodifica con `replace` sta in `git._text` (4057-4060), mai coperta. Le aggiunte di fixture nuove sono trattate come «aggiornate» (`fixture_changed` anche per `status="A"`, 2643-2645): non è in contrasto con la spec («aggiornati»), ma costringe a una deroga per ogni fixture nuova. | ok con test debole (conflitto 11) |
| 7 | `bash.py`: coerente coi test; nessun crash su 90 comandi di prova (fuzz delle funzioni di classificazione). Lacune di riconoscimento sul comportamento reale (vedi conflitto 7). | ok con lacune (conflitto 7) |
| 8 | `waivers`, `report`: coerenti con 18.2 e 18.5 (campi obbligatori del report corrispondono a 6.3: `must_have` e `size_reason` non obbligatori, `size_reason` imposto oltre `task_lines_max` nel Task 19). | ok |
| 9 | `git.py`: test su repo con spazi, rinomine, non tracciati, worktree, impronta. `toplevel` ritorna `None` per percorsi dentro `.git/` (la cartella non è un work tree): è la causa del conflitto 3. `_parse_z` e `commit_changes` su commit radice funzionano. | ok per i test; origina il conflitto 3 |
| 10 | `verify`: test coerenti. Il passo 6 (4521) attribuisce la prova «config dalla base» a `test_missing_command_is_unverified`; la prova vera è `test_config_read_from_work_base` (4296-4303). Con un lavoro senza `work_base_sha` (permesso da `create_work`) `base` vale `None` e `git.changes(root, None, …)` solleva `TypeError` (riga 4454): caso limite, P3 imposta sempre la base. | ok (conflitto 11 per la nota, 13 per il limite) |
| 11 | `waiver_cli`: test coerenti; nessuna normalizzazione del percorso in `--file` né obbligo di `--test` per `type=test` (4655-4685): una deroga con percorso non relativo alla radice o senza identificativi non copre mai nulla, in silenzio. | ok con lacuna (conflitto 13) |
| 12 | Motore: 14 test passano. `test_malformed_input_missing_fields` (5081-5086) accetta `(0, 2)` per un caso deterministico (il primo dà sempre 2 per il modulo finto con `api` 2): asserisce quasi nulla. Il rilievo P1 «corruzione dopo l'apertura» (riga 71) è dichiarato coperto, ma `test_corrupt_db` (5112-5126) corrompe prima di aprire, quindi passa da `DbCorrupt` e non dal ramo `sqlite3.DatabaseError` (5821-5825), mai provato. `INJECT_MODE["SubagentStop"]="stderr"` (5269) è invisibile al modello. `INPUT_EVENTS` (5203-5205) e `_PLAIN` (5263) non hanno `prompt_submit`. Sessione vuota: `marker = bound/""` coincide con la cartella `bound` (5740). | conflitti 2, 6, 10, 11 |
| 13 | Wrapper e manifest: 13 test passano. `plugin.json` ha `version` nella dipendenza (6253) contro D1; `test_manifest` non lo controlla. `test_manifest.test_hooks_json` fissa per uguaglianza l'insieme degli eventi (6044-6045) senza `UserPromptSubmit`. `json_str` (6112-6115) prende l'ultima occorrenza e ignora l'annidamento. Ore di `/tollgate:off` ricavate da cifre (6122): `08` fa abortire lo script per aritmetica ottale, `0.5` diventa 5 ore. `license`/`author` (6249-6251) senza decisione né file `LICENSE` nel repo: non verificabile. | conflitti 2, 5, 10 |
| 14 | `session`, `acts`: 12 test passano; oggetto e target degli atti combaciano con la decisione 15 e con 8.4. Nessun test vuoto. | ok |
| 15 | `writes`, `post_edit`, `_common`: 18 test passano. Nessun test tocca `.git/hooks` o `.git/config` e il percorso sotto `.git` bypassa sia la protezione sia la regola del checkout principale (probe: Write su `<main>/.git/hooks/pre-commit` e `.git/config` → uscita 0 sia da sessione legata sia non legata). `level_records` conta i file non ignorati in `output_dirs`. | conflitti 3, 9 |
| 16 | `bash_rules`, `effects`: 15 test passano. Stesso buco `.git` nel ramo `is_protected(…, ctx.protected_roots(r))` con `r = git.toplevel(p)` (7398-7400): `echo x > .git/hooks/pre-commit` → 0. Lacune di riconoscimento (conflitto 7). `script_path` mette in veto anche `./node_modules/.bin/…` e qualunque binario non tracciato (7538-7552), coerente con 8.5 alla lettera ma di forte attrito. | conflitti 3, 7, 14 |
| 17 | `commit`, `post_bash`: 13 test passano. `post_bash` torna presto se non ci sono commit nuovi (7898-7899): un `git reset --soft` avanti e indietro tra due SHA, senza commit nuovi, lascia un `finish` di nuovo utilizzabile (probe: `pending` e `find_usable` vero dopo il ritorno a SHA A), contro il vincolo 3 del piano principale. Commit con file di `output_dirs` non ignorati: scope e livello li contano. | conflitti 8, 9 |
| 18 | `agents`, `send_message`, `subagent_start`, `post_agent`, `skills`, `handback`: 10 test passano. Il taglio di `maxTurns` è riconosciuto solo da `PostToolUse Agent` (primo piano): niente per il taglio dopo una ripresa con `SendMessage` (giri di correzione 1-3), che la spec rev 21 affida a `prompt_submit`; la riga dell'implementatore resta `running` e blocca lo scrittore unico per `stale_minutes`. `SubagentStart` inietta il promemoria dell'implementatore a ogni subagente non di sola lettura, in qualunque fase (8296-8303). | conflitti 2, 12 |
| 19 | `subagent_stop`: 9 test passano. Report, ricevuta e dimensione sono imposti a **ogni** subagente non di sola lettura, anche senza task (8663-8680): in fase `plan` o in L0 un `general-purpose` riceve fino a 2 veti e poi un `needs_you` (conforme al glossario «implementatore», ma con rischio di falsi blocchi). La ricevuta usa `all(counts_green)` su tutte le ricevute dello SHA (8695): un `verify` rosso e un `related` verde sullo stesso SHA danno veto, coerente con la decisione 24. | conflitto 12 |
| 20 | Test end-to-end dal wrapper vero: 4 test passano. Nessun test asserisce nulla di vuoto. Bookkeeping delle decisioni incoerente (vedi tabella coppie). Il passo 2 elenca la copertura per criterio ma non include `prompt_submit`. | ok (conflitti 2 e 12 per le omissioni) |

---


## Ruling sullo scan pre-flight (dettaglio per task in carry.md)
Ruling: C1 — la migrazione 2 non fa backup su DB nuovo (_migrate con fresh), test_migration_makes_backup_first aggiornato (Task 2) — spec 12.1: la copia protegge dati esistenti e P1 lo ha fissato con un test — costo se sbagliato: un backup in meno su un DB vuoto.
Ruling: C2 — prompt_submit in Task 12/13/18 come da ruling del Task 1 — spec rev 21 3.2 e 6.3 — costo: un modulo da togliere.
Ruling: C3 — file protetti sotto .git: git.toplevel risale alla .git (Task 9), protected_roots dal repo del contesto (Task 12), test Write/Edit (15) e Bash (16); git config in forma di scrittura negato come scrittura di .git/config — spec riga 32 e 7.4 — costo se sbagliato: un git config legittimo dall agente richiede OFF.
Ruling: C4 — test di config con load_config_text (Task 4) — bug del piano — costo: nessuno.
Ruling: C5 — plugin.json senza version (D1) e senza license/author (nessun LICENSE nel repo; resta all utente in P3) — costo: campi da aggiungere in P3.
Ruling: C6 — inject su subagent_stop/subagent_handback va nel log degli hook, non su stderr con uscita 0 — D2: stderr con 0 non arriva al modello — costo: note non viste dal subagente in chiusura.
Ruling: C7 — Bash: HEAD risolto nel ramo corrente per push (16), -c combinato (-lc), commit -n, redirezioni numerate (7) — 7.4 best effort, correzioni economiche — costo: nessuno.
Ruling: C8 — post_bash invalida un finish in attesa a ogni HEAD diverso, anche senza commit nuovi (17) — vincolo 3 del piano principale — costo: nessuno.
Ruling: C9 — output_dirs e .tollgate-run/ esclusi da livello, scope e commit_violations (15, 17) — 8.1/7.3 li trattano come non rilevanti — costo: un file di output fuori dallo scope non segnalato.
Ruling: C10 — wrapper: prima occorrenza della chiave, ore validate ^[0-9]+$ con base 10, segnalino bound ignorato con session vuota (12, 13) — robustezza 7.1 — costo: nessuno.
Ruling: C11 — test rafforzati: uscita 2 esatta, ramo sqlite3.DatabaseError, byte Latin-1 veri (6, 9, 12) — costo: nessuno.
Ruling: C12 — controlli da implementatore su ogni subagente non in sola lettura, come il piano — glossario spec riga 22 — costo se sbagliato: veti a un general-purpose fuori dai task (attrito, da segnalare all utente).
Ruling: C13 — verify con base nulla usa il ref; waiver add normalizza il file e chiede --test per type=test; _inside una sola volta in _common.py (10, 11, 15-17) — DRY e robustezza — costo: nessuno.
Ruling: C14 — script non tracciati ma ignorati da git restano effetto esterno (lettera di 8.5), nessuna esenzione in P2 — la spec vince — costo: attrito su ./node_modules/.bin/*; da segnalare all utente.
Ruling: C15/C16 — documentali: Task 18 riceve prompt_submit, Task 20 cita 6.3 e allinea gli elenchi; is_stale e un Produces del Task 2 — costo: nessuno.
Task 2: dispatched (haiku), base fb338d9
Task 2: implementer DONE, commit 82e6e16 (138 test); review dispatched (sonnet)
Task 2: minor (deferred): tasks.assign senza reviewer_type azzera il valore gia scritto (firma del piano) — da considerare in P3.
Task 2: minor (deferred): subagents.is_stale senza test; interrupt solo caso felice — coprire al primo chiamante (Task 18).
Task 2: minor (deferred): MigrationV2Test non verifica la migrazione su DB con dati (verificata a mano dal revisore).
Task 2: complete (commits fb338d9..82e6e16, review clean)
Task 3: dispatched (haiku), base 82e6e16
Task 3: implementer DONE, commit 0093c24 (150 test); review dispatched (sonnet)
Task 3: minor (deferred): scope.register_plan — se set_phase fallisce dopo il commit, scope registrato e fase non avanzata; il chiamante deve gestirlo (imposto dal vincolo set_phase fuori transazione).
Task 3: fix round 1 dispatched (offlog: unlink solo dopo commit, orfani, date invalide)
Task 3: fix round 1/5 (1 addressed, 0 open — offlog unlink dopo commit, orfani, date invalide; commits 0093c24..4975975)
Task 3: minor (deferred): offlog — unlink fallito dopo il commit porta a doppio import (non documentato nel docstring); _pid_alive vede vivo uno zombie/pid riusato (recupero ritardato).
Task 3: complete (commits 82e6e16..4975975, review clean)
Task 4: dispatched (haiku), base 4975975
Task 4: implementer DONE, commit 50c3f62 (175 test); review dispatched (sonnet)
Ruling: Task 4 — globs.py implementa il dialetto .gitignore fedele: negazione ! con «l ultimo che corrisponde vince» in match_any, escape \, classi con ] iniziale ed escape dei caratteri speciali di re, pattern non valido = non corrisponde mai (come wildmatch di git) senza eccezioni, a**b come *, [/] non corrisponde a / — rilievi imposti dal piano, la spec 3.2 chiede il dialetto di .gitignore — costo se sbagliato: codice in piu in globs.py.
Ruling: Task 4 — nello scope del piano (plan.py) e pattern solo un percorso con * o ?; le parentesi quadre sono nomi letterali (rotte Next.js app/[id]/page.tsx); dove i percorsi dello scope diventano pattern vanno escapati (globs.escape) — 7.5 vuole file espliciti e [id] e un file esplicito — costo se sbagliato: una classe [] nel piano non e rifiutata.
Task 4: minor (deferred): plan.py — righe con piu file tengono solo il primo; blocchi ~~~ e fence da 4 backtick non gestiti; must-have in grassetto/multiriga ignorati, ID duplicati non segnalati; test: manuale come tests=["manuale"] senza costante; protected.abs_path non normalizzato (il chiamante passa percorsi risolti).
Task 4: fix round 1/5 (4 addressed, 0 open — classi, negazione/escape, isolamento, is_pattern; commits 50c3f62..6db3590)
Task 4: minor (deferred): globs [z-a] su z non corrisponde (git si); compile ritorna None per pattern non validi — i chiamanti usano match, non compile().fullmatch.
Task 4: complete (commits 4975975..6db3590, review clean)
Task 5: dispatched (haiku), base 6db3590
Task 5: implementer DONE, commit 7410a39 (202 test); review dispatched (sonnet)
Task 5: fix round 1 dispatched (junit: XXE con UTF-16, tetto di dimensione, radice non JUnit, test, docstring diff_bytes)
Ruling: Task 5 — parse_junit rifiuta DOCTYPE/ENTITY dal parser (indipendente dalla codifica), tetto 32 MiB, radice non JUnit = errore — sicurezza del gate che leggera JUnit di runner non fidati — costo se sbagliato: un report JUnit legittimo oltre 32 MiB rifiutato.
Task 5: fix round 1/5 (5 addressed, 0 open — XXE dal parser, tetto 32 MiB, radice, test, docstring; commits 7410a39..b9a778e)
Task 5: minor (deferred): junit.py:81 la regex _DANGER sui byte resta e rifiuta un report legittimo con <!DOCTYPE dentro un CDATA; il parser basta da solo — candidata alla rimozione.
Task 5: complete (commits 6db3590..b9a778e, review clean)
Task 6: dispatched (haiku), base b9a778e
Task 6: implementer DONE, commit bf5c315 (229 test); review dispatched (sonnet)
Ruling: Task 6 — scanner JS: regex letterali riconosciute dal token precedente, pila per i template ${}, apostrofo tra due lettere nei .jsx/.tsx non apre una stringa; in piu i marcatori di salto e le asserzioni si contano anche sul testo grezzo e vale il conteggio peggiore (fail-closed) — rilievo imposto dal piano, ma un guardrail che perde un it.skip contraddice 8.2 — costo se sbagliato: qualche falso positivo su marcatori dentro commenti, risolvibile con deroga.
Ruling: Task 6 — soglia rimossa o commentata = abbassata; il controllo soglie gira anche sui file di configurazione di copertura noti (.nycrc*, .coveragerc, jest/vitest.config.*, pyproject.toml, setup.cfg, package.json) ovunque nel repo — 8.2 «in tutto il repo» — costo: nessuno.
Task 6: minor (deferred): testids JS — describe con oggetto opzioni perde il prefisso, titoli duplicati collassano, it.each/test.each senza id, \n nei titoli diventa n; asserzioni contate per file, non per test; classi Test* annidate ignorate; test_deleted con ids=() per file non parsabili non documentato.
Task 6: fix round 1 dispatched
Task 6: fix round 1/5 (3 addressed, 1 open — nuovo: _strip_comments con /* cancella le soglie in .coveragerc/setup.cfg; commits bf5c315..c30d181)
Task 6: minor (deferred): JSX possessivo plurale users' e from'react' sfasano lo scanner (coperto dalla rete grezza); falsi positivi della rete grezza su commenti/titoli (direzione sicura, risolvibili con deroga); i++ / 2 letto come regex.
Task 6: fix round 2/5 (1 addressed, 0 open — commenti per formato, soglie fail-closed, stringhe a fine riga; commits c30d181..68c57bd)
Task 6: minor (deferred): scan.py/testguard.py — continuazione backslash seguita da CRLF non e piu continuazione (sfasamento di una riga; coperto dalla rete grezza).
Task 6: complete (commits b9a778e..68c57bd, review clean)
Task 7: dispatched (haiku), base 68c57bd
Task 7: implementer DONE_WITH_CONCERNS, commit 8ca1a65 (268 test); review dispatched (sonnet)
Ruling: Task 7 — i pattern di comandi ([external_effects] allow, commands) usano fnmatch come nel piano (* attraversa /), non il dialetto .gitignore, che vale per i pattern di percorsi; il Task 20 lo chiarisce nella spec 3.2 («pattern di percorsi») — con la semantica gitignore cat * non coprirebbe cat src/a.py e allow diventerebbe inutile — costo se sbagliato: un pattern di comando piu largo del previsto.
Ruling: Task 7 — i falsi negativi del parser Bash (punteggiatura fusa, parole chiave, wrapper con opzioni, -fu, gh -R, curl --request=) si correggono in P2 anche se 7.4 e best effort — sono economici e riguardano il push forzato, il rischio principale — costo: codice in piu in bash.py.
Task 7: fix round 1 dispatched (7 Important + 4 Minor)
Task 7: fix round 1/5 (8 addressed, 1 open — nuovo: placeholder SUBST rompe VAR=$(..) git push -f; commits 8ca1a65..237b1de)
Task 7: minor (deferred): token di punteggiatura quotati (git -C ";" push -f) spezzati come operatori; env -S non analizzato.
Task 7: fix round 2 dispatched
Task 7: fix round 2/5 (5 addressed, 0 open — placeholder, redirect nei token, time -p, heredoc non quotati, _scan unica; commits 237b1de..53c1585)
Task 7: minor (deferred): write_targets puo restituire il segnaposto _TG_SUBST_ per >$(x); bash.py ora ~740 righe (piano ~380); Cmd con argv vuoto per redirect senza comando (gestito).
Task 7: complete (commits 68c57bd..53c1585, review clean)
Task 8: dispatched (haiku), base 53c1585
Task 8: implementer DONE, commit 8871a33 (297 test); review dispatched (sonnet)
Ruling: Task 8 I1 — unresolved/covers accettano anche deroghe pending: e la decisione 9 del piano (la deroga dichiarata scioglie la violazione in locale; open-pr in P3 rifiuta finche qualcosa e in attesa); si documenta nel docstring con un test — criteri 3 e 21 valgono insieme — costo se sbagliato: un commit locale passa prima dell approvazione, fermato da open-pr.
Ruling: Task 8 I2 — covers: se la violazione porta ids, servono tutti in w.tests (anche test_deleted); se non ne porta, basta una deroga test sullo stesso file — chiude il buco di test_deleted — costo: nessuno.
Ruling: Task 8 I3 — status normalizzato (strip, maiuscolo); uno status fuori dai 4 di 18.5 rende il report non valido (fail-closed), contro il test del brief test_unknown_status_counts_as_done — la spec elenca 4 valori e un guardrail non deve far scegliere all implementatore — costo: un report con status creativo riceve un veto.
Task 8: fix round 1 dispatched
Task 8: fix round 1/5 (5 addressed + 3 minor, 0 open; commits 8871a33..975bb06)
Task 8: minor (deferred): parse_report preferisce un oggetto annidato completo a uno esterno incompleto; waivers.parse non verifica che l id abbia il numero di issue del file; declared_by non limitato; size_reason non verificato (task che usera task_lines_max).
Task 8: complete (commits 53c1585..975bb06, review clean)
Task 9: dispatched (haiku), base 975bb06
Task 9: implementer DONE, commit 6a036f3 (315 test); review dispatched (sonnet)
Ruling: Task 9 — git in sola lettura anche per l indice (GIT_OPTIONAL_LOCKS=0), timeout 10 s per chiamata, nessuna esecuzione dalla config del repo (--no-ext-diff --no-textconv, core.fsmonitor=false) — vincolo di sola lettura e scadenza degli hook (decisione 4) — costo: nessuno.
Task 9: minor (deferred): toplevel con repo dentro una cartella chiamata .git da None; run usa surrogateescape per nomi non UTF-8 (attenzione nei chiamanti).
Task 9: fix round 1 dispatched
Task 9: fix round 1/5 (5 addressed, 0 open — indice privato in /tmp, timeout 10 s, fingerprint OSError, lettura a blocchi, niente esecuzione da config; commits 6a036f3..9334bf3)
Task 9: minor (deferred): copia dell indice due volte per changes+diff_size (costo misurato 0,07-0,30 s su 20000 file).
Task 9: complete (commits 975bb06..9334bf3, review clean)
Task 10: dispatched (haiku), base 9334bf3
Task 10: implementer DONE, commit 2751b94 (334 test); review dispatched (sonnet)
Task 10: fix round 1 dispatched (timeout uccide il gruppo di processi, stdin devnull, env, report path, sqlite3.Error, test)
Task 10: fix round 1/5 (1 Important + 7 minor addressed, 0 open; commits 2751b94..cb09e05)
Task 10: minor (deferred): figli in background sopravvivono a un verify riuscito (killpg anche a fine normale costerebbe una riga); KeyboardInterrupt lascia il gruppo vivo; percorso del report validato solo lessicalmente (symlink).
Task 10: complete (commits 9334bf3..cb09e05, review clean)
Task 11: dispatched (haiku), base cb09e05
Ruling: Task 11 — waiver add --file: un percorso relativo e relativo alla radice del worktree (come nelle violazioni e nel test del brief test_add_two_waivers), un assoluto si converte in relativo alla radice, un percorso fuori dal worktree si rifiuta — costo se sbagliato: chi lancia da una sottocartella deve scrivere il percorso dalla radice.
Task 11: implementer DONE, commits e021f29, d77435d (352 test); review dispatched (sonnet)
Task 11: minor (deferred): waiver add senza lock (due add concorrenti perdono una deroga; .tmp a nome fisso); .tmp lasciato e OSError con traceback se la scrittura fallisce; evento registrato dopo il file; issue/branch del file esistente non verificati, dumps perde commenti; test di riletta identica e di file malformato/sqlite3.Error in main mancanti; help del parser senza «relativo alla radice»; --pattern non normalizzato; uscita senza messaggio leggibile.
Task 11: complete (commits cb09e05..d77435d, review clean)
Task 12: dispatched (sonnet), base d77435d
Task 12: implementer DONE_WITH_CONCERNS, commit 0db2c8d (373 test); review dispatched (sonnet)
Ruling: Task 12 I1/I3 (imposti dal piano) — un modulo rotto su un evento informativo diventa avviso con uscita 0 (decisione 1, spec 7.1 punto 7); OFF si controlla prima del parsing dell input — la spec vince — costo: nessuno.
Task 12: fix round 1 dispatched (I1 rotto informativo=0, I2 footer nei rifiuti del motore, I3 OFF prima del parsing + 3 minor)
Task 12: fix round 1/5 (3 Important + 3 minor addressed, 0 open; commits 0db2c8d..69dde89)
Task 12: minor (deferred): registry._validate events [["x"]] gestito; manca test OFF con TOLLGATE_STATE senza sentinella; avviso di modulo rotto ripetuto a ogni evento; ReadDb aggirabile via _conn (protezione da uso accidentale); test_concurrent_hooks senza record contesi; deny e inject di prompt_submit scartati non documentati; hooks.log e il nome del log degli hook (runner.HOOKS_LOG).
Task 12: complete (commits d77435d..69dde89, review clean)
Task 13: dispatched (haiku), base 69dde89
Task 13: implementer DONE_WITH_CONCERNS, commit f79ed8d (396 test); review dispatched (sonnet)
Ruling: Task 13 — i messaggi di off/on vanno su stdout come systemMessage + additionalContext di UserPromptExpansion (D2), non su stderr con uscita 0 che Claude Code scarta; ore valide 1-9999 — costo se sbagliato: nessuno.
Task 13: minor (deferred): UserPromptExpansion senza matcher (il wrapper gira a ogni slash command; matcher su command_name non verificato); due hook concorrenti su OFF scaduto scrivono due righe on; OFF scritto senza rename atomico.
Task 13: fix round 1 dispatched
Task 13: fix round 1/5 (1 Important + 4 minor addressed, 0 open; commits f79ed8d..1697e59)
Task 13: minor (deferred): hooks/run:65 — in locale UTF-8 la regex [0-9] accetta cifre non ASCII, poi 10# va in errore aritmetico e il ramo off salta senza messaggio (usare LC_ALL=C); trap del guardiano con una finestra teorica prima di SP.
Task 13: complete (commits 69dde89..1697e59, review clean)
Task 14: dispatched (haiku), base 1697e59
Task 13: nota — tests/test_wrapper.py produce ResourceWarning (Popen non chiuso); da correggere prima della chiusura (suite con -W error::ResourceWarning). Lo porto nel giro di correzione del Task 14.
Task 14: implementer DONE_WITH_CONCERNS, commit 3c8f44d (416 test); review dispatched (sonnet)
Ruling: Task 14 — locked_docs blocca la spec solo nelle fasi successive alla sua approvazione (non per la sola presenza di spec-approval.md), il piano allo stesso modo — spec 6.2: dopo reopen l approvazione resta come storico ma non vale — costo: nessuno.
Task 14: minor (deferred): governing_work con sessione legata restituisce sempre il lavoro legato; waiver_hint/explain con parametro issue inutilizzato; abandon #N eredita il lavoro della sessione (da verificare in P3).
Task 14: fix round 1 dispatched (+ ResourceWarning di test_wrapper)
Task 14: fix round 1/5 (2 Important + 4 minor + ResourceWarning del Task 13 addressed, 0 open; commits 3c8f44d..37dad52)
Task 14: minor (deferred): in L1 il piano resta modificabile finche la fase e plan anche con plan_sha registrato (spec 6.2: blocco dopo plan-check).
Task 14: complete (commits 1697e59..37dad52, review clean)
Task 15: dispatched (sonnet), base 37dad52
Task 15: implementer DONE, commit 4bda89a (472 test); review dispatched (sonnet)
Ruling: Task 15 — file protetti valutati rispetto a repo piu vicino, worktree del lavoro e checkout principale (basta uno); git.worktrees in errore = veto con messaggio (fail-closed); sessione legata che scrive nel worktree di un altro lavoro attivo = veto; fuori dai repo attivi passa — spec 6.6 e decisione 22 — costo se sbagliato: un veto in piu su una scrittura tra lavori.
Task 15: fix round 1 dispatched
Task 15: fix round 1/5 (1 Important + 3 decisioni addressed, 0 open; commits 4bda89a..44f60d3)
Task 15: minor (deferred): nessuno nuovo.
Task 15: complete (commits 37dad52..44f60d3, review clean)
Task 16: dispatched (sonnet), base 44f60d3
Task 16: implementer DONE_WITH_CONCERNS, commit 8a3e48c (517 test); review dispatched (sonnet)
Ruling: Task 16 — il consumo dell atto di un effetto si sposta a PostToolUse Bash (il comando e partito davvero); PreToolUse verifica soltanto — spec 3.2 vuole i record scritti anche dopo un deny, quindi non si scartano nel runner — costo se sbagliato: due comandi identici prima del PostToolUse usano lo stesso atto.
Ruling: Task 16 — rm/rmdir/mv su cartelle che contengono file protetti (.git, .tollgate, reviews, radice del repo) negati; mv conta la sorgente; core.hooksPath negato a ogni livello; comandi illeggibili con ripiego testuale sugli effetti noti — 7.4 «scrittura sui file protetti» e 8.5 — costo: nessuno.
Task 16: minor (deferred): regole distruttive (reset --hard, rm -rf) valgono anche in repo non attivo mentre push -f no (6.6 dice nessuna regola) — da chiarire in spec; allow non esenta uno script non tracciato (C14, da documentare); corpo di bash <<EOF non scansionato per gli effetti.
Task 16: fix round 1 dispatched
Task 16: fix round 1/5 (3 Important + 5 minor addressed, 1 open — glob non espansi aggirano la protezione; commits 8a3e48c..bd7f615)
Task 16: minor (deferred): MCP consuma l atto al Pre (nessun PostToolUse MCP nell adattatore); chiave dell effetto con SHA — git commit && ssh a non consuma l atto (nessuna esecuzione in piu); ripiego testuale senza allow (prudente); variabili come $PWD/.tollgate non espanse.
Task 16: fix round 2 dispatched (glob, guardia row None, -c compatto, git rm/unlink/find -delete)
Task 16: fix round 2/5 (1 Important + 3 minor addressed, 0 open; commits bd7f615..0703492)
Task 16: minor (deferred): find . -name *.pyc -delete negato (attrito; il messaggio non suggerisce di restringere la radice); variabili ($X/*), xargs rm e sh -c dentro find -exec non analizzati (limite statico).
Task 16: complete (commits 44f60d3..0703492, review clean)
Task 17: dispatched (sonnet), base 0703492
Task 17: implementer interrotto dal limite d uso, ripreso (lavoro non committato nel worktree)
Task 17: implementer DONE_WITH_CONCERNS, commit aa1fd5b (562 test, verificati dal controller anche con -W error::ResourceWarning); review dispatched (sonnet)
Task 17: minor (deferred): pre-check falso negativo con indice e working tree divergenti (coperto dal post); post_bash con fase vecchia puo aprire 2 blocchi; GitError in post_bash inghiottito senza avviso; test mancanti (gia blocked, piu commit, rebase); filtro exclude doppio. Da rivedere in P3: rebase/merge del ramo predefinito porta commit estranei in base..HEAD (sync); alias git ci non visti dal pre; attribuzione dei commit riscritti al task.
Task 17: complete (commits 0703492..aa1fd5b, review clean)
Task 18: dispatched (sonnet), base aa1fd5b
Task 18: implementer DONE, commit 0382c46 (587 test); review dispatched (sonnet)
Ruling: Task 18 — il taglio in background si riconosce solo da un prompt che inizia con <task-notification>, blocco per blocco, con la frase dentro <summary>; la chiusura cut della riga e sempre attiva, solo budget_exceeded e needs_you dipendono da task_budget — forma verificata in E7/E8; lo scrittore unico non deve vedere falsi vivi — costo: nessuno.
Task 18: fix round 1 dispatched
Task 18: fix round 1/5 (2 Important + 2 minor addressed, 0 open; commits 0382c46..f3c6d91)
Task 18: minor (deferred): race del lancio in parallelo (riga in subagents solo a SubagentStart, due Agent nello stesso messaggio passano PreToolUse); take_pending(resume=True) fragile con piu task dello stesso tipo; notifica non chiusa inghiotte i blocchi successivi (rete stale_minutes).
Task 18: complete (commits aa1fd5b..f3c6d91, review clean)
Task 19: dispatched (sonnet), base f3c6d91
Task 19: implementer DONE_WITH_CONCERNS, commit 5e7e10c (621 test; una esecuzione intermittente FAILED=1 non identificata, il controller ripete la suite 3 volte); review dispatched (sonnet)
Ruling: Task 19 — SubagentStop richiede tutti i comandi del gate green sull ultimo commit, con la stessa logica della DoD (fonte unica); related green resta sufficiente (decisione 24); alla ripresa l impronta di sola lettura si riprende e i veti si azzerano — 8.1, 7.3 — costo se sbagliato: un subagente ripreso riceve di nuovo 2 veti.
Task 19: minor (deferred): il motivo di tampered non elenca i file (impronta come hash unico); DONE con commit e working tree sporco non controlla l impronta (caso residuo della spec).
Task 19: fix round 1 dispatched
Controller: 5 esecuzioni complete a codice fermo (621 test) verdi; il FAILED intermittente del Task 19 non riprodotto; da riverificare nella chiusura con piu esecuzioni.
Task 19: fix round 1/5 (2 Important + 2 minor addressed, 0 open; commits 5e7e10c..c323997)
Task 19: minor (deferred): _receipt_ok con work_base_sha assente usa files=[] (solo gate base) senza test; manca un test diretto che l implementatore ripreso non rinnova l impronta.
Task 19: complete (commits f3c6d91..c323997, review clean)
Task 20: dispatched (haiku), base c323997
Ruling: Task 20 — elenco delle decisioni nella rev 21 = unione 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15, 22 (i tre elenchi del piano erano diversi); 8.1 corretta: status non riconosciuto = report non valido (coerente con 18.5 e il codice); OFF «prima di leggere l input» descritto come nel codice (il wrapper legge stdin, il runner controlla OFF prima del parsing) — costo: nessuno.
Task 20: implementer DONE_WITH_CONCERNS, commit f543fe3 (641 test); review dispatched (sonnet)
Task 20: minor (deferred): criterio 34 passa anche in protected (gli hook non leggono gate.mode); criterio 19 controlla solo la lunghezza ≤1500.
Task 20: fix round 1 dispatched (7.1 OFF, matrice 13/39/7, 7.1 punto 5, apply.OPS, decisione 20)
Trovato il test intermittente: tests/test_db.py::OpenTest.test_concurrent_first_open (circa 1 su 6 da solo): tre processi aprono per la prima volta lo stesso DB, uno esce con disk I/O error — difetto di concorrenza in db.open_db (P1 + _migrate di P2). Da correggere nella fase finale.
Task 20: fix round 1/5 (1 Important + 6 minor addressed, 0 open; commits f543fe3..4a91fea)
Task 20: complete (commits c323997..4a91fea, review clean)

## Revisione finale
Final review: dispatched (opus), range d87383a..4a91fea
Final review: 2 Critical, 3 Important, 7 Minor; verdetto «con correzioni» (final-review.md).
Ruling: revisione finale I2 — PostToolUseFailure si aggiunge in base alla documentazione ufficiale (task-1-docs.md), senza la sonda claude -p suggerita: le cautele permettono claude -p solo nel Task 1 — costo se sbagliato: un hook in piu che non scatta mai; il comportamento attuale resta.
Ruling: revisione finale I1/M1 — registro delle radici attive nella cartella di stato (active/), il wrapper lancia Python su PreToolUse se l input nomina una radice attiva anche con cwd non attivo; il runner prende la configurazione dal repo del bersaglio; cwd inesistente su un evento di controllo usa il repo del bersaglio o nega — spec 6.6 (la protezione segue il bersaglio) — costo: un grep -F per hook fuori dai repo attivi.
Final fix wave: dispatched (sonnet) — C1, C2, I1, I2, I3, M1, M2, M4, M5, M6, triage 2 e 13
Final fix wave: DONE_WITH_CONCERNS, commits 8125473..6e73c05 (680 test, 30/30 test_concurrent_first_open); __pycache__ entrati in 2757ec0 e tolti in cbc74ce (restano nella storia del ramo, nessun amend); scoped re-review dispatched (sonnet).
Final re-review: C1, C2, I2, M2, M4, M5, M6, triage 13 indirizzati; aperti I1 (relativi, ~, redirect/sed -i da cwd non attivo) e un danno nuovo Important (alias -c alias.push=status apre un bypass del push).
Ruling: secondo giro mirato sulle correzioni finali, contro la regola della skill «una sola ondata»: le istruzioni dell utente chiedono di correggere tutti i critical e important, e l alias e una regressione introdotta dalla correzione — costo: un giro in piu.
Ruling: I1 — con cwd non attivo e registro active/ non vuoto il wrapper lancia sempre Python su PreToolUse; il runner considera anche i bersagli di scrittura (write_targets), git -C relativo e ~ — la protezione segue il bersaglio (6.6) — costo: un avvio di Python per hook fuori dai repo attivi, solo per chi usa tollgate.
Final fix wave 2: dispatched (sonnet, stesso implementatore)
Final fix wave 2: DONE, commits 2ea840f..3f7430d (685 test); scoped re-review dispatched (sonnet)
Final re-review 2: alias, I1, Minor 3 indirizzati; danno nuovo Important (main+worktree contati come piu repo attivi); trovato buco preesistente (bersagli di git -C risolti rispetto al cwd: checkout/restore di tollgate.toml passano). Costo misurato: ~180 ms per PreToolUse fuori dai repo attivi con registro non vuoto (dichiarato in spec).
Final fix wave 3: dispatched (stesso implementatore) — common_dir per il raggruppamento, bersagli di git -C
Final fix wave 3: DONE, commit 94b8977 (690 test); scoped re-review dispatched (sonnet)
Final re-review 3: punti del giro 3 indirizzati; aperto Important (preesistente) — piu -C in fila non composti come fa git, bypass della protezione di tollgate.toml; Minor: GitError su common_dir scarta il candidato (fail-open).
Final fix wave 4: dispatched (stesso implementatore) — composizione dei -C, fail-closed su GitError
Final fix wave 4: DONE, commit 234df82 (692 test); scoped re-review dispatched (sonnet)
Final re-review 4: tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
Final review: COMPLETE — revisione finale (opus) registrata in final-review.md; correzioni in 4 giri (8125473..234df82), ognuno con ri-revisione mirata.
Chiusura: suite finale su 234df82 — tests/run 3 volte (692 test, 3.11 e 3.13) e -W error::ResourceWarning tutti OK; memoria del progetto aggiornata; workspace conservato fino al merge; merge su main NON eseguito, in attesa dell OK dell utente.
