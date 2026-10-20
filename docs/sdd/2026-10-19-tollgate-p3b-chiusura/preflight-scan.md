# Pre-flight scan del piano P3b (chiusura)

Piano: `docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md` (745 righe, 18 task, decisioni 1-26). Autorità: spec rev 22 (sezioni 3, 3.1, 3.2, 6.3, 6.4, 6.5, 8.4, 8.6, 8.7, 10, 11.4, 12.2-12.4, 15, 18.1, 18.3-18.5) e piano principale sezione 3. Modello di forma: `docs/sdd/2026-10-16-tollgate-p3a-avvio-e-task/preflight-scan.md`.

## 1. Metodo e limiti

- Lettura integrale del piano, delle sezioni di spec indicate, del piano principale (sezione 3, «Vincoli per P3b e P3c» e «Rinviati»), di `bin/tollgate_core`, `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_analysis` (tutti i moduli che il piano consuma o modifica), `hooks/run` (solo l'uso), `tests/flowkit.py`, `hookkit.py`, `helpers.py`, `fakegh.py` e dei test esistenti toccati (`test_sessions`, `test_check_cli_calls`, `test_check_acts`, `test_check_common`, `test_db`, `test_verdicts`, `test_taskcmd`, `test_checkpoint`, `test_dod`, `test_start`, `test_actapply`, `test_criteria_p3a`, `test_flowkit`, `test_manifest`, `test_layers`).
- Ogni nome «Consumes» è stato cercato nel codice. Quelli che esistono hanno la firma attesa; quelli che il piano dice di creare (`run_gate`, `dod_commands`, `diff_violations`, `reviews.*`, `intents.*`, `gh.pr_*`, `gitw.push_sha/merge_base/rebase/...`, `git.patch_id`, `phases.set_base/set_pr/...`) non esistono e sono prodotti da un task precedente: ho controllato l'ordine di produzione e consumo, non il codice che non c'è.
- Sonde: una sola, di lettura (`python3 -B`, nessuna scrittura): conteggio di `apply.OPS` = **25** voci (coincide con il piano principale; con `review_report` e `finding_verify` diventano 27, come dice il Task 8). Nessun altro esperimento: non ho eseguito la suite né applicato il piano. Gli esiti dei test sono «per lettura».
- Stato del repo durante la scansione: il piano dice «ramo identico a `main`», ma `HEAD` è già `b5a3630 tollgate P3b: verifiche dell'interfaccia di gh` (Task 1 eseguito, con `spikes/run-p3b-experiments.sh` e `docs/verifiche/2026-10-19-p3b-verifiche.md`) e `.superpowers/sdd/2026-10-19-tollgate-p3b-chiusura/` contiene brief e rapporto del Task 1. Lo scan vale per i Task 2-18; del Task 1 ho letto solo l'esito (G1-G5: nessuna conseguenza nuova sul piano, salvo che i nomi dei campi JSON di `gh pr list/view` restano non verificati su 2.46.0).
- Non verificabile da qui: `gh` vero, `claude -p`, il comportamento di `EnterWorktree`, la concorrenza reale di due `PreToolUse` paralleli.

## 2. Tabella per coppie (produttore → consumatore)

«P3a» è il codice esistente su `main`.

| A (produce) | B (consuma) | Cosa produce A / cosa consuma B; nomi e firme che devono coincidere | Esito |
|---|---|---|---|
| P3a | T2 | `sessions.cli_session(state, cwd, sub, *, now)` (oggi senza `argv`), `note_cli_call` (chiave `argv[0]`, una voce per sottocomando), `cli_calls._SIGNALLED/_COORDINATOR_ONLY`, `cli.main(argv)`, `FlowLab.cli` (scrive `list(argv)` e lancia `bin/tollgate argv`) | `FlowLab.cli` e il hook producono gli stessi token che `main` riceve: compatibile. Conflitto C2 (consumo senza `argv`), C21 (corsa) |
| P3a | T3 | `db.MIGRATIONS` fino a 3; `review_cycles`, `findings`, `intents` già nello schema v1 (colonne elencate sotto); `phases.create_work`, `events.EVENT_TYPES` (ha già `review_cycle`, `finding`, `pr_opened`, `pr_updated`, `merge_detected`; mancano `finish_check`, `base_realigned`); `dod.compute_dod/receipt_verdict`; `Ctx.approved_waivers` | Migrazione 4 coerente con lo schema reale (vedi punto d sotto). C3 (`MigrationV3Test`), C12 (`FlowLab.register_plan`), C16 (`counted`) |
| P3a | T4 | `_common.commit_violations/scope_exempt/locked_docs/is_docs_md/_is_registered_plan`, `Ctx.guard_config/waiver_file`, `verify._verify` (produced_by fisso `"verify"`) | Test degli hook indipendenti dai nomi privati (punto c sotto). C15 |
| P3a | T5 | `config.PROFILE_DEFAULTS` (non ha `rules`, `blocking_rules`), `_merge_profile`, `verdicts.parse_task_verdict(... standard)`, `task_verdict.decide` | C4 (fixture `probe:web-dev`), C8 (riga 108 vs test esistente) |
| T3 | T5 | `verdicts.is_blocking(finding, blocking_rules, known_rules)` | Firma coincide con l'uso in `reviews.add_report` e `parse_task_verdict` |
| P3a, T3, T4 | T6 | `compute_dod` (esteso in T3), `run_gate`/`dod_commands` (T4), `violations.diff_violations` (T4), `acts.has_approval`, `phases.set_finish`, `set_phase(.., "review", "finish_check_green")`, `gitw.fetch`, `sessions.work_for_path` | Ordine corretto. C5 (ricevuta `related`), C13 (rerun in `review` su altro SHA), C14 (`external` come set), C17 (`GateRun` su worktree sporco), C9 (uscite) |
| T6 | T9 | `finishcheck.check` (Task 9 vi aggancia `prstate.detect`) | Il Task 6 sta in piedi senza `prstate`: `detect` è chiamato solo con `pr_number` valorizzato, e nei test del Task 6 non lo è. Punto (a) sotto |
| T3, T5 | T7 | `reviews.*`, `git.patch_id`, `profiles.final_specialists`, `brief.fence`, `[review] models` | Ok |
| T7 | T8 | Stadi del ciclo (`review`, `verify`, `closed`), `reported`, codice per ciclo; `awaiting_final` | Ok; C16 |
| T3, T5, T7 | T8 | `reviews.add_report(... blocking_rules, known_rules ...)`, `parse_final_verdict`, `parse_verifier_results`, `apply.OPS` 25 → 27 | Ok. C18 (normalizzazione dei rilievi scartati) |
| P3a, T3, T6, T8 | T9 | `gh.py` (`prs_for_branch_prefix` con `pr list --limit 200`), `fakegh.py` (nessun `pr create/edit/view`, nessun `api --paginate`), `gitw` (nessun `push_sha/remote_sha`), `receipts.latest(conn, work, sha)`, `waivers.status/path_for`, `acts.find_usable/consume`, `stats.off_periods` (T3), `approvals.parse_approval` (T6), `phases.set_pr` (T3) | Firme reali coincidono. C6 (voci esterne della DoD in `open-pr`), C19 (`is_ancestor` prima della definizione) |
| T9 | T11 | `openpr.open_pr(..., via_sync)`, `prstate.detect` | `via_sync` non deve chiamare `cli_session("finish")` (il segnale `sync` è già consumato): da dire nel Task 9 |
| T9 | T12, T14 | `prblock.parse`, `gh.pr_for_branch`, `gh.pr_comments` | Ok |
| T3, T10 | T11, T12 | `gitw.merge_base` nasce nel Task 10, usato dai Task 11 e 12 | Ordine ok; `gitw.is_ancestor` e `rebase` nascono nel Task 11 (vedi C19) |
| T3 | T10 | `intents.SYNC_CONFLICT_REASON`, `authorize_force`, `phases.set_base/add_extra_cycles`, `tasks.add_extra_rounds` (T10) | Ok. C7 (`approve unverified-review`) |
| P3a | T10 | `actapply.APPLIERS`, `_pick`, `_resolve`; `taskcmd.MAX_FIX_ROUNDS` (5, costante) | Ok; il blocco «giri di correzione esauriti sul task k» è prodotto da `taskcmd` (riga 106) con il testo che il Task 10 deve riconoscere |
| P3a, T6, T9, T10 | T11 | `start._resume`, `gitw.rebase_in_progress`, `post_bash` (evento `commit` per sha già noti) | Compatibile: `post_bash` considera nuovi solo gli sha di `rev_list(base..head)` non negli eventi `commit`. C20 (ordine in `_resume`) |
| P3a, T9 | T12 | `phases.create_work` (il piano aggiunge `phase`, `cause`), `scope.register_plan(conn, state, work, *, ..., advance, now)`, `plan.check_plan`, `gitw.create_branch/worktree_add`, `git.worktrees`, `active.register`, `sessions.mark_bound`, `phases.set_level_cap` | Firme coincidono. Dettaglio: `set_level_cap` vuole `cap_paths` (adopt non li ha: da calcolare come `_approve_level`) |
| P3a, T9 | T13 | `start._resume`, `_common.orphan_tg(ctx, repo) -> int|None` (4 chiamanti: `writes`, `bash_rules` x2, `session`), `gitw` | C11 (`orphan_tg` non può dire «cleanup») |
| T3, T5 | T14 | `reviews.blocking_open`, `tasks.add_task(kind="fix")` (c'è già), `tasks.task_text`/`add_task(task_text=)` (nuovo), `taskcmd._task_start` legge il piano e rifiuta se il task non c'è | Ok se il Task 14 aggira davvero `_plan_text`/`task_text` per `kind = "fix"` anche in `review_prepare` e `task_done` |
| P3a, T8 | T15 | `checkpoint.next_step/CAPS` | C10 (`approve finding` lascia fase `execution` con ciclo `ok`) |
| T6-T15 | T16 | Righe `agente:`, `prossimo passo:`, codici d'uscita | C9: uscita 2 di `finish check` non gestita dalla skill |
| T1-T16 | T17 | Prova reale | C1 (bloccante) |
| T1-T17 | T18 | Criteri e rev 23 | Vedi C22 (elenco delle deviazioni dichiarate da riportare) |

### Punti guardati apposta

**(a) Task 6 senza Task 9.** `finishcheck.check` nel Task 6 chiama solo `gitw.fetch`, `run_gate`, `diff_violations`, `compute_dod`, `set_finish`, `set_phase`. Il Task 9 vi aggiunge `prstate.detect`, che nasce dopo ma è inerte finché `work_items.pr_number` è nullo (i test del Task 6 non aprono PR). Il Task 6 ha le sue dipendenze (`run_gate`, `violations`, `reviews.latest`) tutte nei Task 3-4. Esito: ok, con la riserva C13 (il piano non dice come si fa il «verde» quando la fase è già `review`).

**(b) `cli_session` con `argv`.** Come si confronta: il hook salva `argv = args[args.index(sub):]` (token già privi di virgolette, dal sottocomando in poi); `cli.main(argv)` riceve `sys.argv[1:]` e `build_parser` non ha opzioni globali oltre `--version`: i due elenchi coincidono token per token, quindi `entry["argv"] == argv` funziona passando `argv` intero a `start`, `finish`, `sync`, `adopt`, `cleanup`, `abandon`, `act`. Un comando con variabili (`start $N`) registra `$N` letterale e non coincide: fail-closed, accettabile. `FlowLab.cli` scrive `list(argv)` e lancia gli stessi `argv`: compatibile. Le chiamate dirette dei test (`start.start(...)`, `apply_act(...)` senza `argv`, `note_cli_call(.., ["act"])` in `test_actapply.py:28,231`, `["start","7"]` in `test_start.py:343,376,442`) restano valide solo se `argv=None` significa «nessun confronto». Resta aperto il consumo (C2). I Task 9, 11, 12, 13 lo usano come il Task 2 prevede; `openpr.open_pr` deve chiamare `cli_session("finish", argv=...)` e ignorare `CliSessionError` se c'è un atto `finish` valido, ma non quando è `via_sync`.

**(c) `_common` → `violations` e test degli hook.** I test esistenti importano da `tollgate_checks._common` solo `locked_docs`, `orphan_tg` (`test_check_common.py:6`, `test_flowkit.py:12`); `test_check_post_edit.py:180` fa `mock.patch("tollgate_checks.post_edit.level_records")` (resta in `_common`, non si sposta); `test_check_writes.py:172` e `test_check_bash.py:409` patchano `core_git.worktrees`. Nessun test importa o patcha `commit_violations`, `scope_exempt`, `is_docs_md`, `_is_registered_plan`, `Ctx.guard_config`. I moduli `commit`, `post_bash`, `writes`, `bash_rules` importano `commit_violations`, `scope_exempt`, `locked_docs`, `is_docs_md` da `_common`: i nomi devono restare lì come delega (il piano lo dice). Esito: i test degli hook restano verdi senza modifiche, purché `_common` conservi gli stessi nomi e la stessa firma a base di `ctx`.

**(d) Migrazione 4.** `MIGRATIONS` arriva a 3: il numero 4 è giusto. `review_cycles` ha già `work, number, sha, patch_id, outcome, findings_confirmed, counted` (le colonne nuove `code, stage, reviewers, reported, opened` non esistono: ok). `findings` ha già `id, work, cycle, source, severity, confidence, file, line, text, verification, verification_reason, user_decision`; mancano `rule`, `blocking`: ok. `intents` esiste (`work, action, idempotency_key UNIQUE, data, state, outcome, at`), quindi `intents.py` non crea tabelle: ok; `start._pending_intents` elencherà anche gli intenti `pr` e `sync` `requested` (comportamento voluto). `work_items` non ha nessuna delle sei colonne nuove; `tasks` non ha `extra_fix_rounds`, `task_text`. `tasks.kind` ha già il CHECK `('plan','fix')`, `tasks.source` è NOT NULL (ok per `cycle:<n>`, `gate:<sha>`). Attenzione: `review_cycles.counted` ha `DEFAULT 1` (C16) e `findings.severity` ha un CHECK a quattro valori (C18). `tests/test_db.py:174` asserisce `schema_version == "3"` (C3).

**(e) `apply.OPS`.** Oggi 25 (verificato). Il piano dice «passa a 27 voci» dopo il Task 8: coincide. Nessun test conta le voci.

**(f) `fakegh.py` e `FlowLab`.** `fakegh` ha oggi: `auth status`, `issue view/list`, `pr list` (richiede la chiave `prs`, filtra `--head`, ignora `--state`), `api .../commits/<sha>/status`, `api .../issues/<n>`. Mancano `pr create`, `pr edit`, `pr view`, `api --paginate .../pulls`, `data["fail"]`: tutto previsto dal Task 9. Il cambio di `prs_for_branch_prefix` da `pr list --limit 200` ad `api --paginate` richiede che il finto serva la stessa lista `prs` anche per `api`: i test di `test_start` esistenti ne dipendono (PR con `headRefName`, forse senza `state`/`url`: il finto deve usare `.get`). `FlowLab` ha `cli`, `hook`, `git`, `set_gh`, `gh_calls`, `env`, `close`; non ha `register_plan`, `commit`, `close_tasks`, `JUNIT_TOML`, `tools/junit_fake.py`: tutto nuovo (Task 3). Il piano dice «piano L1 di `tests/test_taskcmd.PLAN`»: `PLAN` è solo il percorso; il testo è `plan_text()`, che dipende da `SECTIONS` di `test_check_post_edit` (C12).

**(g) Funzioni usate, firma reale.** Esistono e coincidono: `gitw.fetch/create_branch/delete_branch/worktree_add/rebase_in_progress/add_excludes/remote_branches/worktree_dir/set_config/is_dirty`; `gh.issue/auth_ok/commit_state/sentinel_issues/prs_for_branch_prefix/run_json`; `acts.find_usable/consume/record_act/invalidate_finish`; `phases.set_phase/open_block/close_block/get_work/find_active/set_level_cap/bind_session/set_worktree`; `dod.compute_dod/dod_passes/receipt_verdict`; `verify.gate_commands/counts_green/receipt_state/CommandSpec`; `receipts.latest/add/any_since`; `waivers.status/path_for/parse/unresolved/covers`; `scope.paths/register_plan/set_plan_path`; `profiles.active_profiles/min_level/task_routing/vertical_for`; `report.json_candidates/parse_report`; `git.changes/diff_size/commit_changes/worktrees/default_ref/default_branch/exists_at/blob_sha/blob_text/rev_list/fingerprint/is_clean/main_worktree/origin_url`; `junit.Junit(ids_run, ids_failed, ids_skipped)`; `plan.MustHave(id, text, tests)`; `brief.fence/ImplBrief`; `sessions.work_for_path/mark_bound/alive`; `active.register`. Non esistono (previste dal piano): vedi la tabella sopra.

## 3. Tabella per task

| Task | Test previsti contro codice previsto | File toccati anche da altri task | Firme del piano contro codice reale | Esito |
|---|---|---|---|---|
| 1 | Nessun test; già eseguito (b5a3630) | — | — | ok |
| 2 | `test_signal_consumed_once` non dice con quale `argv`: se `argv=None` consuma, rompe `test_sessions::test_cli_session_found` (due `find` di fila), `test_two_subcommands_of_same_session_both_valid` (rilegge `data["start"]` dopo `find("start")`), `test_criteria_p3a:41` (`cli_session` e poi il CLI vero). `test_parse_failure_message_explains` non confligge con `test_uncertain_program_denial_says_what_to_do` (rami diversi). Il test del tetto di `json_candidates` ok. `test_cache_dirs_ignored` ok | `cli.py` (T2, 6, 7, 9, 11, 12, 13, 14), `start.py` (T2, 11, 13), `actapply.py` (T2, 10), `git.py` (T2, T3), `flowkit.py` (T2, T3) | `cli_session` aggiunge `argv`; `note_cli_call` invariata; `acts.py` check: `abandon` come `adopt/cleanup` | C2, C21 |
| 3 | `MigrationV3Test` asserisce `"3"` e fallisce con la 4; `test_phases`, `test_intents`, `test_reviews` ok; `test_findings_only_latest_cycle`, `test_downgraded_to_major_still_blocks` ok rispetto a `test_dod.py:86-90` (resta verde: `downgraded:minor` passa). Mancano test diretti per `set_pr`, `set_finish`, `add_extra_cycles`, `set_review_unverified`, `has_approval`, `intents.complete` (coperti solo dai task successivi) | `verdicts.py` (T3, T5), `context.py` (T3, T4), `git.py` | `create_work(phase, cause)` (oggi `from_approved_spec` già decide la fase: non specificato se coesistono); `compute_dod` oggi senza `skip/findings_cycle/specialists/allow_unverified`; `Ctx.approved_waivers` delega ok | C3, C12, C14, C16 |
| 4 | `test_same_result_as_hook` confronta `diff_violations` con `commit_violations`, che dopo il task delega alla prima: test tautologico (C23). `RunGateTest` ok. Test degli hook invariati (punto c) | `_common.py` (T4, T8, T13), `verify.py` | `diff_violations(cfg, conn, work, wt, base_ref, head_ref, changes, *, components)` coerente con `commit_violations`; `run_gate(.., produced_by, extra, ..)` vs `_verify` che ha `produced_by="verify"` cablato | C15, C17, C23 |
| 5 | `test_verdicts` esistente `test_finding_with_bad_severity_or_line_dropped` (approved con rilievi scartati valido) contraddice `test_approved_with_dropped_blocker_invalid`. `test_taskcmd.py:21-22,138-140` usa `probe:web-dev` e `probe:web-reviewer`: con la decisione 9 diventano `""` | `verdicts.py`, `config.py`, `task_verdict.py` | `parse_task_verdict(..., blocking_rules, known_rules)` si aggiunge a `standard`; `PROFILE_DEFAULTS` senza `rules` | C4, C8 |
| 6 | Test coerenti. `test_rerun_in_review_same_sha` copre solo lo stesso SHA; sull'altro SHA `set_phase(review→review)` solleverebbe `TransitionError` (nessuna transizione `review→review`). `test_must_have_test_missing_is_red` ok con `JUNIT_TOML`. Il test del `finish_check` evento non asserisce l'evento | `finishcheck.py` (T6, T9), `cli.py` | `compute_dod(..., external={...})` è dato come set, ma la firma vuole un Mapping | C5, C9, C13, C14, C17 |
| 7 | Coerenti; `test_same_patch_id_after_rebase_no_new_cycle` richiede `git.patch_id` (T3) e un rebase: ok. Il ciclo aperto su altro SHA resta aperto per sempre | `taskcmd.py` (T7, 10, 14), `brief.py` (T7, 14) | `reviews.latest/open_cycle/to_verify/close_cycle`; `profiles.final_specialists` | C16 |
| 8 | `test_stale_interrupted_reviewer_verdict_counts`: `subagent_stop` e `task_verdict` escono su `state != 'running'`, quindi il modulo nuovo deve gestire `interrupted` per conto suo: il piano lo dice. `subagents.finish` accetta righe `interrupted` | `_common.py`, `checkpoint.py` (T8, T15), `apply.py` | `awaiting_final`, `OPS` 25 → 27 | C18 |
| 9 | Test fitti e coerenti con la decisione 10. Non testati: `--update` senza PR aperta (decisione 10), `open-pr` e `sync` con PR `CLOSED` (decisione 12: solo `finish check` ha il test), push con lease in `open-pr` (solo in `sync`), evento `pr_opened/pr_updated`. `test_block_in_body_parses` duplica `test_prblock` | `gitw.py` (T9, 10, 11, 13), `finishcheck.py`, `fakegh.py` | `gh.pr_*` e `fakegh` nuovi; `prs_for_branch_prefix` cambia comando | C6, C19, C24 |
| 10 | Coerenti. `test_approve_rounds_on_fix_rounds_cap` richiede di leggere il numero del task dal testo del motivo (`taskcmd` riga 105): fragile ma ok | `actapply.py`, `taskcmd.py`, `gitw.py` | `APPLIERS` ok; `act["target"]` per `finding`/`rounds` è `args[1]` (confermato da `test_check_acts`) | C7 |
| 11 | Coerenti. `complete_interrupted` va chiamata prima di `_pending_intents` (riga 134 di `start.py`), ma `wt` si ricava più sotto (riga 145) | `start.py`, `gitw.py` | `gitw.rebase_in_progress` esiste; `merge_ff_only/rebase/rebase_abort/is_ancestor` nuove | C19, C20 |
| 12 | Coerenti. `test_refused_with_active_work_or_merged_pr_or_two_branches` raggruppa tre casi senza `subTest` | — | firme reali ok | C25 |
| 13 | `test_orphan_hint_on_closed_work_points_to_cleanup`: `orphan_tg` torna `int|None`, non può distinguere | `start.py`, `_common.py`, `gitw.py` | `worktree_remove` nuova | C11 |
| 14 | Coerenti | `taskcmd.py`, `tasks.py` (T10, T14), `brief.py` | `add_task(task_text=)` nuova | ok |
| 15 | Esistente `test_next_step_sequence` e `..._without_tasks` restano compatibili (righe 56-99 di `test_checkpoint.py`) | `checkpoint.py` | — | C10 |
| 16 | `test_skills_use_program_command_form` e il regex di `test_agents_and_skills_never_write_a_bare_program_name` (vieta `tollgate finish`, `task`, `act`, ... nudi nelle skill/agenti) vanno rispettati nei testi nuovi | skill esistenti (approve, execute, start, resolve) | — | ok |
| 17 | Vedi C1 | — | — | C1 |
| 18 | `test_finish_to_pr_end_to_end` e gli altri sono duplicati voluti dei test dei task (E2E), ma dipendono da C1/C6 | piano principale, spec | — | C22 |

## 4. Conflitti

### Bloccante

**C1. Task 17 non può arrivare a `open-pr` con il repo di prova di P3a** (bloccante, Task 17 con Task 6)
- Dove: piano Task 17 Step 1 («Prepara il repo L1 di P3a e ripete i tre passi di `run-p3a-flow.sh`»); `spikes/run-p3a-flow.sh:44-52,122-124`; piano Task 6 (must-have dal JUnit).
- Cosa: il `tollgate.toml` del repo di prova ha `allow_no_tests = true` e `verify = python3 -m unittest …`, nessun `report`. Il piano ha `M1 … — test: tests.test_calc.CalcTest::test_sottrai`. `run_gate` non produce nessun JUnit (`junits["verify"]` è `None`), `mustcheck.check` vede `ids_run` vuoto, `M1` risulta assente, `must_have` falso, `finish check` rosso: la fase resta `execution` e `open-pr` non è raggiungibile. Il criterio atteso del Task 17 («PR nel finto `gh`, fase `pr_open`») non si ottiene. `unittest` non scrive JUnit con la sola libreria standard.
- Proposta: nello script del Task 17 il piano della prova usa `— test: manuale` per `M1` (finisce tra le voci «da leggere», non rende falsa la voce) oppure il repo di prova porta un piccolo `tools/unittest_junit.py` (circa 30 righe, stdlib) e `report = "junit:reports/junit.xml"`. Costo: la prima perde la prova del criterio 42 nella prova reale (resta coperto dai test del Task 6); la seconda aggiunge uno script al banco di prova. Da scrivere nel brief del Task 17.

### Da decidere

**C2. Il consumo del segnale senza `argv` rompe test esistenti** (da decidere, Task 2)
- Dove: piano Task 2 («la voce trovata si toglie dal file»; `test_signal_consumed_once`); `bin/tollgate_core/sessions.py:113`; `tests/test_sessions.py:68-74` (due `find` consecutivi sulla stessa voce), `:97-103` (rilegge `data["start"]` dopo `find("start")`); `tests/test_criteria_p3a.py:41` (`cli_session` e poi `bin/tollgate start` vero senza nuovo segnale); `tests/test_flowkit.py:57`.
- Cosa: se «si toglie» vale anche con `argv=None`, quei test falliscono e il Task 2 non lo elenca tra le modifiche ai test.
- Proposta: consumare solo se `argv is not None` (chi passa `argv` — `start`, `act`, `finish`, `sync`, `adopt`, `cleanup`, `abandon` — consuma; le chiamate di lettura dei test no) e scrivere `test_signal_consumed_once` con `argv`. Costo: nessuno (dopo il Task 2 tutti i chiamanti reali passano `argv`).

**C3. `MigrationV3Test` asserisce la versione «3»** (minore, già visto in P3a come C2, Task 3)
- Dove: `tests/test_db.py:173-174` (`schema_version == "3"` dopo aver riaperto con tutte le `MIGRATIONS`); piano Task 3 Step 1 aggiunge solo `MigrationV4Test`.
- Proposta: portare l'asserzione a `str(db.latest_version())` e nominarla nei Files del Task 3. Costo: nessuno.

**C4. La decisione 9 (nomi dei profili) invalida le fixture di `test_taskcmd`** (minore, Task 5)
- Dove: `tests/test_taskcmd.py:21-22` (`agent = "probe:web-dev"`, `reviewer = "probe:web-reviewer"`), asserzioni `:138-140`; piano Task 5 (Files e test non citano `test_taskcmd.py`); piano principale riga 219 (la prova del criterio 38 è `test_profile_agent_chosen`).
- Cosa: i due nomi non hanno la forma `<plugin>:implementer-<area>` / `<plugin>:reviewer-<area>`, quindi diventano `""` con avviso e il test `task start sceglie l'agente del profilo` fallisce. Il Task 5 chiude rosso.
- Proposta: rinominare le fixture in `probe:implementer-web` e `probe:reviewer-web` (sono già la forma del criterio 38) e aggiungere `tests/test_taskcmd.py` ai Files del Task 5. Costo: nessuno.

**C5. `dod._receipt` conta anche le righe `related`** (da decidere, Task 6)
- Dove: `bin/tollgate_core/dod.py:179-182` passa tutte le ricevute dello SHA a `receipt_verdict`; `bin/tollgate_checks/subagent_stop.py:51` le esclude esplicitamente (`command != "related"`); `bin/tollgate_core/verify.py:211-216` registra una riga `related` (anche `empty`) prima di ripiegare sul gate completo.
- Cosa: se l'ultimo `verify --related` su HEAD ha dato `empty` o `uncounted` e `allow_no_tests` è falso, resta una riga `related` non verde per quello SHA: `finish check` e `open-pr` sono rossi anche con il gate verde. Il Task 6 non lo prova (i suoi test non creano ricevute `related`).
- Proposta: in `dod._receipt` escludere `command == "related"`, con un test (`test_dod.py`) e una riga nel Task 3 o 6. Costo: una condizione e un test.

**C6. `open-pr` ricalcola «sempre l'intera DoD», ma le voci esterne non si possono ricalcolare** (da decidere, Task 9)
- Dove: piano decisione 15 e Task 9 (`facts.dod` «dalla DoD ricalcolata da `open-pr`»); `dod.EXTERNAL_KEYS = guard_scope, must_have, approvals, specialists`.
- Cosa: `guard_scope`, `must_have` (serve il JUnit della stessa esecuzione) e `approvals` li calcola `finish check`; `open-pr` non ha il JUnit. Il piano non dice da dove le prende.
- Proposta: `open-pr` legge le voci esterne da `work_items.finish_report` (valido perché si esige `HEAD == finish_sha`) e ricalcola solo `receipt`, `tasks_approved`, `findings`, `skills`, `specialists` e le voci dei profili. Scriverlo nel Task 9. Costo: `finish_report` diventa contratto (già nella migrazione 4).

**C7. `approve unverified-review`: effetto sul blocco e sulla fase non definito** (da decidere, Task 10)
- Dove: piano decisione 14 («`review_unverified = 1`»), Task 10; spec 8.4 («chiude la revisione come non verificata»), spec 10.
- Cosa: l'ottavo ciclo `needs_fix` lascia fase `execution` con il blocco dei cicli aperto (e `approve rounds` è rifiutato oltre 8). Il piano non dice se `unverified-review` chiude quel blocco né come si torna a `review`. Resta in piedi solo `resolve` (che concede un ciclo oltre l'ottavo?).
- Proposta: `unverified-review` chiude il blocco dei cicli (come `approve rounds`), imposta il flag e lascia la fase `execution`; il percorso è poi `finish` → `finish check` → «revisione non verificata» → `open-pr`. Test da aggiungere in Task 10. Costo: una funzione e un test.

**C8. Il piano cambia `approved` con rilievo scartato e rompe un test che è anche prova del criterio 40** (da decidere, Task 5)
- Dove: piano decisione 8 e Task 5 («un `approved` dichiarato con un rilievo bloccante scartato per forma è non valido», riga 108); `bin/tollgate_analysis/verdicts.py:76-81` (oggi solo `changes`); `tests/test_verdicts.py:81-85` (`test_finding_with_bad_severity_or_line_dropped`: `verdict()` ha `outcome="approved"` e si aspetta `valid=True, dropped=1` per `severity="critical"`, `line="2"`, `file=""`, `"testo"`); piano principale riga 221 elenca quel test come prova del 40.
- Cosa: la modifica voluta rende non validi quei quattro casi; il test e la riga della matrice vanno aggiornati.
- Proposta: riscrivere il test con `outcome="changes"` e un `moderate`/`minor` illeggibile (che resta valido) e aggiungere i casi `approved` + bloccante scartato come non validi; aggiornare la riga 221 nel Task 18. Costo: un test riscritto.

**C9. Codici d'uscita di `finish check` incoerenti con la skill e con gli altri sottocomandi** (minore, Task 6 e 16)
- Dove: piano Task 6 (`OK = 0`, `RED = 1`, `REFUSED = 2`); Task 16 skill `finish` («uscita 1 → mostra le voci `[no]` e fermati»); `start` ha `REFUSED = 1`, `open-pr` rifiuta con 1, `sync` `REFUSED = 1`; l'uscita 2 è anche quella di argparse e dei veti.
- Proposta: `finish check`: rifiuto = 1 come gli altri e rosso = 3, oppure la skill gestisce anche il 2. Costo: una costante e una riga di skill.

**C10. Dopo `approve finding … dismiss` il ciclo è `ok` ma la fase è `execution` e `next_step` dice `--from-findings`** (minore, Task 10 e 15)
- Dove: piano decisione 14 (esito ricalcolato, nessun cambio di fase), Task 15 («ciclo `needs_fix`: `task start --from-findings`»).
- Proposta: `next_step` guarda l'esito attuale del ciclo (`ok` → `/tollgate:finish`); con `ok` su HEAD `review prepare` risponde «revisione già superata» e si arriva a `open-pr` senza ciclo nuovo. Aggiungere il caso a `test_checkpoint`. Costo: un ramo e un test.

**C11. `orphan_tg` non può dire «cleanup»; quattro chiamanti non sono nei Files del Task 13** (minore, Task 13)
- Dove: `bin/tollgate_checks/_common.py:111` (`-> int | None`), chiamanti `writes.py:36`, `bash_rules.py:253,257`, `session.py:25`; piano Task 13 (solo `_common.py`); test `test_check_common.py:76`, `test_flowkit.py:90` (`assertIsNone`), `test_check_session.py:83`.
- Proposta: lasciare `orphan_tg` com'è (solo senza lavoro attivo) e aggiungere `closed_tg(ctx, repo) -> int | None` per il ramo di un lavoro `closed`; i tre chiamanti scelgono il messaggio. Elencare `writes.py`, `bash_rules.py`, `session.py` nei Files. Costo: tre chiamanti.

**C12. `FlowLab.register_plan` importerebbe `tests/test_taskcmd` da `tests/flowkit`** (minore, Task 3)
- Dove: piano Task 3 («piano L1 di `tests/test_taskcmd.PLAN`»); `tests/test_taskcmd.py` importa `FlowLab` da `flowkit` (import circolare); `PLAN` è solo un percorso, il testo è `plan_text()` e dipende da `SECTIONS` di `tests/test_check_post_edit.py`.
- Proposta: spostare `plan_text`/`PLAN`/`SECTIONS` in `tests/flowkit.py` (o in un modulo di fixture) e far importare i due test da lì; oppure importazione tardiva dentro il metodo. Costo: spostamento di fixture, test invariati.

**C13. `finish check` in fase `review` su un altro SHA: la transizione non esiste** (minore, Task 6)
- Dove: piano Task 6 («in `review` … su un altro SHA ricalcola»; «verde: … fase `review`»); `bin/tollgate_core/phases.py:41-61` (`review → review` non ammesso: `TransitionError`).
- Cosa: dopo un commit del coordinatore in `review`, il secondo `/tollgate:finish` riesegue `finish check`; se l'implementazione chiama `set_phase(.., "review", "finish_check_green")` anche da `review` solleva. Nessun test lo copre (c'è solo lo stesso SHA).
- Proposta: se la fase è già `review`, solo `set_finish` ed evento, senza `set_phase`; test `test_rerun_in_review_other_sha`. Costo: un `if` e un test.

**C14. `external` è dato come insieme, ma `compute_dod` vuole un dizionario** (minore, Task 6)
- Dove: piano Task 6 (`external={"guard_scope", "must_have", "approvals"}`); `dod.py:213-216,231` (`external.get(key)`).
- Proposta: `external={"guard_scope": bool, "must_have": bool, "approvals": bool}`. Costo: nessuno.

**C15. `components` in `diff_violations` e `Ctx.component`** (minore, Task 4)
- Dove: piano Task 4 (`components: Mapping[str,bool]`); `Ctx.component` usa `data["components"].get(name, True)`.
- Cosa: `finish check` deve passare `cfg.data["components"]` con lo stesso default `True` per le chiavi mancanti, altrimenti un `tollgate.toml` senza `[components]` spegne i controlli. Un mapping nudo non ha il default.
- Proposta: dire nel Task 4 che il default è `True` (`components.get(name, True)`). Costo: una riga.

**C16. `review_cycles.counted` ha `DEFAULT 1`: un ciclo aperto o abbandonato conta** (minore, Task 3 e 7)
- Dove: `bin/tollgate_core/db.py:78`; piano Task 3 (`counted`, `open_cycle`), decisione 5 (un ciclo aperto su altro SHA resta aperto, si apre `n+1`).
- Cosa: `reviews.counted()`/`count()` sommerebbero cicli non chiusi; il tetto di 4/8 scatta troppo presto.
- Proposta: `open_cycle` scrive `counted = 0`; `close_cycle` lo imposta; il ciclo lasciato aperto da un nuovo `review prepare` si chiude con esito `superseded`; `counted()` filtra `outcome IS NOT NULL`. Test in `test_reviews`. Costo: tre righe e un test.

**C17. `GateRun` non distingue «non eseguito» da «rosso»** (minore, Task 4 e 6)
- Dove: piano Task 4 (`GateRun(ok, lines, sha, ...)`); `verify._verify` torna `(1, [msg])` per worktree sporco o config non valida.
- Proposta: `GateRun.sha is None` = non eseguito → `finish check` `REFUSED`, mai «rosso con elenco di voci». Dirlo nel Task 4 e provarlo (`test_finishcheck`: worktree sporco → rifiuto, fase invariata). Costo: un test.

**C18. Rilievi scartati con campi illeggibili violano i vincoli di `findings`** (minore, Task 3 e 8)
- Dove: `db.py:79-86` (`severity` CHECK a quattro valori; `file`, `line` ammettono NULL); piano Task 3 (`rejected` registrati con `verification = 'rejected'`) e Task 5 (`parse_final_verdict`: «rilievi senza prova in `rejected`»).
- Cosa: un rilievo con `severity: "critical"` o non stringa farebbe `sqlite3.IntegrityError` nell'`apply` di `review_report`: il riporto intero salta (il runner lo registra come errore del DB) e il revisore resta `running`.
- Proposta: `add_report` normalizza i `rejected` (gravità fuori elenco → NULL, `line` non intera → NULL, testo troncato). Test con `severity="critical"`. Costo: una funzione e un test.

**C19. Il Task 9 ha bisogno di `is_ancestor`/`merge_base` che nascono nei Task 10-11** (minore, Task 9)
- Dove: piano Task 9 `test_non_fast_forward_without_intent_refused` («rifiuto senza push»); `gitw.is_ancestor` è prodotto dal Task 11, `merge_base` dal Task 10.
- Cosa: per rifiutare *prima* del push serve sapere se il ramo remoto è antenato di HEAD; altrimenti il rifiuto è quello di git (push tentato e respinto).
- Proposta: spostare `is_ancestor` (e se serve `merge_base`) nel Task 9, oppure dire che il rifiuto è quello di `git push` (senza `--force`). Costo: una funzione spostata.

**C20. `complete_interrupted` va chiamata prima di `_pending_intents`, ma `wt` è calcolato dopo** (minore, Task 11)
- Dove: `bin/tollgate_flow/start.py:134` (intenti raccolti) contro `:145-146` (`wt`); piano Task 11.
- Proposta: nel Task 11 spostare il calcolo di `wt` (e l'eventuale ricreazione) prima della raccolta degli intenti, oppure chiamare `complete_interrupted` subito dopo il calcolo di `wt` e filtrare dagli intenti da confermare quello completato. Costo: riordino di poche righe e un test (già previsto).

**C21. Il consumo del segnale è lettura-modifica-scrittura senza lucchetto** (minore, Task 2)
- Dove: `sessions.note_cli_call` (già così) e la nuova rimozione; due Bash paralleli della stessa sessione.
- Cosa: l'hook del secondo comando può scrivere il suo segnale mentre il primo CLI sta riscrivendo il file senza quella voce: il secondo perde il segnale e rifiuta («sessione non riconosciuta»).
- Proposta: nessuna nel Task 2 (fail-closed, si ripete il comando); annotarlo nella rev 23 accanto al costo già scritto. Costo: una riga di spec.

**C22. Deviazioni dalla spec rev 22 dichiarate dal piano: la rev 23 deve riportarle tutte** (minore, Task 18)
- Elenco: (1) 3.1 e 8.4: segnale anche per `finish/sync/adopt/cleanup/abandon`, `argv` confrontato e consumato (decisione 2); (2) 8.4: `abandon` con lavoro nullo (3); (3) 8.4: `approve rounds` vale anche per i giri di correzione, tetto 8 giri (13); (4) 8.4: `approve finding` ricalcola l'esito, `unverified-review`, `rebase` (14); (5) 8.6: scarto dei rilievi senza prova prima del verificatore (5); (6) 8.6 e 11.4: chiavi `rules`/`blocking_rules`, nomi dei profili convalidati (8, 9); (7) 8.7: la voce `findings` guarda solo l'ultimo ciclo su HEAD (15); (8) 10: il `needs_you` del tetto si apre solo se il ciclo contato è anche `needs_fix` (6); (9) 12.2: migrazione 4; (10) 18.1: campo `state` negli `acts`, `GATE_MARKER` per P4; (11) 18.4: eventi `finish_check`, `base_realigned`; (12) 15: criterio 41 diviso; (13) 3.1: `[review] models` applicato. Inoltre 18.5 non mette `"v": 1` nei JSON del revisore finale e del verificatore mentre l'intestazione di 18 dice che ogni verdetto lo porta: decidere se `parse_final_verdict`/`parse_verifier_results` lo richiedono (proposta: lo ignorano, e la rev 23 corregge l'intestazione). Il Task 18 Step 3 elenca già quasi tutto: aggiungere (2), (3) e `v`.

**C23. `test_same_result_as_hook` (Task 4) è una tautologia** (vedi §5; qui come conflitto interno)
- Dove: piano Task 4 Step 1. Dopo il task `_common.commit_violations` chiama `violations.diff_violations`: il confronto non prova niente.
- Proposta: asserire le violazioni attese (percorso, tipo, `waiver_type`) su un commit costruito a mano, e lasciare che `test_check_commit.py`/`test_check_post_bash.py` (invariati) provino l'equivalenza dell'hook. Costo: un test riscritto.

**C24. Sottocomandi e `cli.main` non gestiscono `GhError`/`GitError`/`GitWriteError`** (minore, Task 6-13)
- Dove: `bin/tollgate_core/cli.py:274-279` cattura solo `DbError`, `UsageError`, `TransitionError`, `sqlite3.Error`; piano Global Constraints (solo `db.DbError` e `sqlite3.Error`).
- Cosa: un'eccezione di `gh`/`git` non gestita dal modulo produce un traceback invece di un rifiuto.
- Proposta: ogni modulo di flusso la converte nel proprio `Result`/errore (come `start`); in `cli.main` un `except (gh.GhError, git.GitError, gitw.GitWriteError)` finale con uscita 1. Costo: tre righe.

**C25. Adopt: casi non specificati** (minore, Task 12)
- Dove: piano decisione 18. (1) PR `CLOSED` non unita: il piano dice «PR aperta → `pr_open`; PR unita → rifiuto», il caso chiusa-senza-merge non c'è (proposta: trattarla come assente e avvisare, o rifiutare con le due strade di `CLOSED_HINT`); (2) tetto di livello dal blocco JSON: `phases.set_level_cap` vuole `cap_paths`, che `adopt` deve ricalcolare come `actapply._approve_level` (righe 72-75); (3) `create_work(phase=…)` e il parametro già esistente `from_approved_spec`: dire che `phase` ha la precedenza o che sono esclusivi. Costo: tre righe nel Task 12.

## 5. Test previsti che asseriscono poco o duplicano logica

- **Task 4 `test_same_result_as_hook`**: tautologico dopo la delega (C23).
- **Task 2 `test_p3b_subcommands_signalled`, parte «`finish check` lascia la voce `finish`, innocua»**: fissa un dettaglio d'implementazione (una voce che nessuno legge) invece di un comportamento; meglio asserire solo che `review prepare` non lascia voci e che `finish open-pr` sì.
- **Task 9 `test_block_in_body_parses`**: duplica `test_prblock::test_parse_last_block_and_garbage` e `test_hostile_finding_text_neutralized_and_block_roundtrips`; il valore è solo l'integrazione `open_pr` → corpo, e asserisce quattro campi presenti. Meglio confrontare il blocco con `facts` o con i dati noti del lavoro (`head_sha == HEAD`).
- **Task 9 `test_dod_component_off_does_not_block` e `test_final_review_off_skips_cycle`**: provano solo il ramo «spento passa»; non provano che *acceso* blocca (già coperto da altri test, ma l'asimmetria è il difetto classico).
- **Task 9 `test_finish_act_valid_without_session_signal`**: verifica l'assenza di un rifiuto; asserire anche che l'atto `finish` è `consumed` e che `approve pr` senza segnale è rifiutato.
- **Task 3 `test_request_is_idempotent`, `test_pending_lists_requested`, `test_force_taken_once`**: CRUD banale su una tabella; non provano l'interazione con `start._pending_intents` né la chiave `effect:` già in uso. Mancano test diretti per `phases.set_pr/set_finish/add_extra_cycles/set_review_unverified`, `acts.has_approval`, `intents.complete`, `reviews.count/counted/effective_severity/blocking_open` (coperti solo indirettamente).
- **Task 3 `test_downgrade_and_dismiss`**: tre asserzioni (rilievo `rejected` rifiutato, declassamento, archiviazione) in un metodo: se la prima fallisce le altre non girano.
- **Task 6 `test_l0_without_tasks`** e **`test_green_moves_to_review_and_prints_dod`**: il primo non dichiara cosa asserisce; il secondo non controlla l'evento `finish_check` {sha, ok} della decisione 25 (nessun test del piano lo fa).
- **Task 10 `test_unverified_review_only_after_eight`**: non asserisce l'effetto sul blocco e sulla fase (C7).
- **Task 12 `test_refused_with_active_work_or_merged_pr_or_two_branches`**: tre scenari senza `subTest`.
- **Task 15 `test_steps_use_program_command`, `test_pr_open_step`**: confronti su stringhe di prosa (`in`); fragili ai cambi di testo, non provano il comportamento.
- **Task 16 `test_finish_skill_never_pushes`, `test_finish_skill_keeps_worktree_clean`**: asseriscono che il testo contiene una frase («mai `git push`», «committa»). Servono come guardia, ma non dimostrano che la skill si comporti così: la prova è nel Task 17.
- **Task 18 `test_sync_after_default_advanced`, `test_adopt_after_db_lost`**: ripetono i test dei Task 11 e 12 attraverso `hooks/run`; il valore sta solo nel passaggio dal hook vero (segnale), da dichiarare nel test.
- **Mancano** (decisioni senza test): `finish open-pr --update` senza PR aperta (decisione 10); `open-pr` e `sync` con PR `CLOSED` (decisione 12; c'è solo `finish check` e `start`); `finish_check` e `pr_opened/pr_updated` come eventi (decisioni 10 e 25); `tasks.source = "gate:<sha>"` oltre il caso base; `approve rounds` quando sono aperti entrambi i blocchi (decisione 13, «rifiuta»); `approve rebase` quando la fase tornata è `execution` (il piano la lascia, ma nessun test lo prova).
