# Task 20: report

Stato: DONE_WITH_CONCERNS (vedi «Dubbi»).
Commit: `f543fe3` su `p2-guardrail`, «tollgate P2: prove dei criteri dal wrapper, spec rev 21, piano principale».
Test: `tests/run` verde su Python 3.11.16 e 3.13.5, 642 test (628 prima del Task 20). `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 642 OK, nessun avviso (con un'eccezione, vedi Fix round 1).

## Cosa è stato fatto

### Step 1: `tests/test_criteria_p2.py`
- Il codice del piano è passato così com'è: le 4 asserzioni reggono sul comportamento reale. Nessuna modifica al test.
  - `test_push_denied_in_bound_session`: exit 2, `open-pr` nel motivo.
  - `test_session_start_injects_state`: exit 0, contesto ≤ 1500 caratteri.
  - `test_general_purpose_denied`: exit 2, hint `/tollgate:execute`.
  - `test_read_tool_not_routed`: exit 0 con stdout vuoto (`PreToolUse-Read` esiste in `samples.json`).
- Nessun prodotto modificato per far passare test.

### Step 2: matrice dei criteri e buchi chiusi
Test aggiunti nel modulo che possiede il codice:
- **Chiavi di `[components]` (criterio 18)**: nei test esistenti mancavano 5 delle 11 chiavi usate da P2. Aggiunto `tests/test_components_p2.py` con un test per chiave: `ContextGuardOffTest` (`context_guard`), `SingleWriterOffTest` (`single_writer`), `TaskSizeOffTest` (`task_size`), `ReportFieldsOffTest` (`report_fields`), `MustHaveTestsOffTest` (`must_have_tests`). Per `context_guard`, `single_writer` e `must_have_tests` il test confronta anche col componente acceso. Per `task_size` e `report_fields` il lato «acceso» è in `BudgetAndSizeTest.test_size_reason_required_over_max` e `ExtraTest.test_invalid_report`.
- **Criterio 38**: `tests/test_check_subagent_stop.py::WebProfileSkillTest.test_done_without_profile_skill_vetoes`. Scostamento dal brief: invece di `tasks.add_task(..., skills_required=...)` passa dal percorso di produzione, cioè `prof.task_skills` su un profilo `web` dichiarato nel TOML, poi `scope.register_plan`. Aggiunto anche `tests/test_check_agents.py::PreAgentTest.test_profile_agent_replaces_generic_implementer`: su un task con agente di profilo, `tollgate:implementer` è negato e l'agente di profilo passa. Questo caso non era coperto da nessun test.
- **Criterio 34**: `tests/test_check_bash.py::DetectModePushTest`. Il push sul predefinito era testato solo in `protected`. Le regole degli hook non leggono `gate.mode`, ma il criterio chiede `detect` esplicitamente.
- **Criterio 15**: `tests/test_verify.py::VerifyRunTest.test_old_report_is_removed_before_run`. Il test esistente `test_green_receipt_and_clean_env` non dimostrava la cancellazione: il comando riscrive `reports/junit.xml`. Il nuovo test usa un comando che non scrive il report. Verifica di discriminazione: con `report.unlink` disattivato in `bin/tollgate_core/verify.py:92` il test fallisce (`AssertionError: True is not false`); il codice è stato ripristinato e `git diff -- bin/` è vuoto.
- **Criterio 5, `xdescribe`**: nessun test a livello di hook. Il commit chiama `testguard.check` (`bin/tollgate_checks/_common.py:218`), coperta da `test_testguard.py::TestGuardTest.test_xdescribe_added`. Non ho aggiunto un fixture JS al commit.

Controllo dei riferimenti: nel piano principale ci sono 93 riferimenti `file::Classe.metodo`. Uno script li ha verificati uno per uno (file, classe, metodo presenti): nessun mancante.

### Step 3: spec, revisione 21
File: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`. Revisione completata, non aperta una 22.
- Intestazione: elenco delle decisioni del piano P2 e dei ruling del controller.
- 3.2: `Ctx.approved_waivers(work)` documentato come API per P3; pattern di percorsi con dialetto `.gitignore` (`tollgate_analysis/globs.py`), pattern di comandi con fnmatch (`*` attraversa `/`).
- 6.2: il blocco di spec e piano vale solo nelle fasi successive all'approvazione; dopo `reopen` torna modificabile il documento riaperto.
- 6.3: il taglio via `UserPromptSubmit` è riconosciuto solo se il prompt comincia con `<task-notification>`, blocco per blocco; `<summary>` con «stopped at its N-turn limit»; riga sempre `cut`; `budget_exceeded` e `needs_you` solo con `task_budget` acceso.
- 6.6: sessione legata negata nel worktree di un altro lavoro attivo; file protetti per ogni radice.
- 7.1: messaggi di `/tollgate:off` e `/tollgate:on` su stdout (`systemMessage` e `additionalContext`); ore 1-9999; classificazione degli hook di controllo (`PreToolUse`) e informativi; Python mancante; scadenza con `signal.alarm`, cane da guardia a `timeout_s + 2`, tetto 85 s, `hooks.json` a 90 s; `OFF` con `skipped.log`; segnalino `bound/`.
- 7.4: `rm`, `rmdir`, `mv`, `git rm`, `unlink`, `find -delete` su cartelle con file protetti negati; `core.hooksPath` negato a ogni livello.
- 8.1: report configurato e assente → `red`; `uncounted` solo senza report; gate completo come la DoD o ricevuta `related` green; veti azzerati alla ripresa; impronta alla ripresa per la sola lettura.
- 8.2: salti e asserzioni su testo pulito e grezzo, caso peggiore; soglie abbassate o commentate; file di copertura noti in ogni cartella.
- 8.3: deroghe dichiarate sciolgono la violazione in locale anche se in attesa; `open-pr` le rifiuta (decisione 9).
- 8.4: oggetto e target per ogni comando; `approve waiver` vale in ogni stato dell'atto (decisione 10).
- 8.5: atto consumato a `PostToolUse Bash`; MCP a `PreToolUse` (verificato in `bin/tollgate_checks/effects.py`, `pre_mcp` con `consume=True`).
- 11.1: già in Task 1.
- 11.3: forma `{"used_pct": <numero o null>}` in `<cartella di stato>/ctx/<session_id>.json` (decisione 13).
- 12.2: migrazione 2 con le colonne e la tabella reali (`session_seen`, `subagents.last_seen|vetoes|report`, `tasks.pending`, `work_items.level_cap_paths`) (decisione 7).
- 16: già in Task 1.
- 18.2: `file` relativo alla radice del worktree; `--test` obbligatorio per `type = "test"`; deroga con identificativi copre solo se li elenca tutti.
- 18.5: status fuori dai quattro valori → report non valido (fail-closed).
- Riga 21 della sezione 20: elenca tutto quanto sopra, decisioni incluse.
- Allineamento delle decisioni: i tre elenchi (titolo Files, Step 3, intestazione «Decisioni») ora coincidono: **1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15, 22**. È l'unione dei tre elenchi originali (vedi «Dubbi»). Aggiornate anche le due righe corrispondenti nel piano P2 (`docs/superpowers/plans/2026-10-09-tollgate-p2-guardrail.md`).

### Step 4: piano principale
File: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
- Intestazione: revisione 21; P2 chiuso sul ramo `p2-guardrail`, merge su `main` in attesa dell'OK dell'utente, 641 test verdi.
- Sezione 3: pacchetto `tollgate_hooks`; contratti P2 → P3/P4 con i nomi reali (verificati con grep in `bin/`): `plan.check_plan`, `level.*`, `testguard.check` e `GuardConfig`, `junit.parse_junit`, `waivers.*`, `bash.*`, `report.*`, `verify.run_verify`, `verify.gate_commands`, `dod.receipt_verdict`, `receipts.*`, `scope.register_plan`, `subagents.start(..., refresh_fingerprint=)`, `tasks.assign` con `pending`, `sessions.*`, `effects.*`, `apply.OPS`, `_common.budget_cut_records`, `git.changes(..., exclude=)`, `globs.escape`. Vincoli per P3 (sette punti).
- Sezione 4: riga 16 con l'esito delle due voci del Task 1 (nessun `version` per Superpowers, tag `<plugin>--v<versione>`; taglio di `maxTurns` riconosciuto da `UserPromptSubmit`). Nuova sottosezione «Prove dei criteri di P2 (Task 20)» con la matrice.

## Matrice dei criteri di P2 → test

Formato `file::Classe.metodo`, con `tests/` come radice. «Resta a» indica la parte che P2 non copre. «(nuovo)» indica i test aggiunti nel Task 20.

| Criterio | Test | Resta a |
|---|---|---|
| 2 Piano | `test_plan.py::PlanCheckTest.test_missing_section`; `test_plan.py::PlanCheckTest.test_pattern_or_dir_rejected`; `test_check_post_edit.py::PlanCheckHookTest.test_complete_plan_registers_scope`; `test_check_post_edit.py::PlanCheckHookTest.test_incomplete_plan_vetoed_and_not_registered`; `test_scope.py::ScopeTest.test_register_twice_rejected_and_scope_unchanged`; `test_check_writes.py::ExecutionL1Test.test_locked_plan` | |
| 3 Scope | `test_check_writes.py::ExecutionL1Test.test_scope`; `test_check_commit.py::CommitTest.test_out_of_scope_then_waiver`; `test_check_writes.py::PhasesTest.test_plan_phase`; `test_check_writes.py::ExecutionL1Test.test_coordinator_cannot_write_code` | |
| 4 Implementatore | `test_check_agents.py::PreAgentTest.test_general_purpose_denied_with_execute_hint`; `test_check_agents.py::PreAgentTest.test_implementer_rules`; `test_check_agents.py::PreAgentTest.test_profile_agent_replaces_generic_implementer` (nuovo); `test_check_agents.py::StartAndResumeTest.test_name_registry_and_send_message`; `test_check_agents.py::StartAndResumeTest.test_start_associates_task_and_keeps_base_on_resume`; `test_check_agents.py::StartAndResumeTest.test_needs_context_resume_allowed` | `task done` senza `approved` e terzo `task start --fix` (P3) |
| 5 Commit | `test_check_commit.py::CommitTest.test_deleted_test`; `test_check_commit.py::CommitTest.test_deleted_js_test_in_dunder_tests`; `test_check_commit.py::CommitTest.test_pytest_skip_added`; `test_check_commit.py::CommitTest.test_mark_skip_added`; `test_check_commit.py::CommitTest.test_assertion_replaced_by_comment`; `test_check_commit.py::CommitTest.test_process_exit_is_fine`; `test_testguard.py::TestGuardTest.test_xdescribe_added` | `xdescribe` solo a livello di modulo (vedi sopra) |
| 6 Comandi | `test_check_effects.py::EffectsTest.test_other_effects`; `test_check_effects.py::EffectsTest.test_veto_act_once_then_warning`; `test_check_effects.py::EffectsTest.test_allowed`; `test_check_effects.py::EffectsTest.test_untracked_ignored_script_is_still_an_effect`; `test_check_bash.py::BoundSessionTest.test_destructive_and_forbidden`; `test_bash.py::ClassifyTest.test_claude_and_tollgate`; `test_check_bash.py::RepoLevelTest.test_inactive_repo_push_passes` | |
| 7 Ambito | `test_check_bash.py::BoundSessionTest.test_branch_changes_in_worktree`; `test_check_bash.py::BoundSessionTest.test_push_other_branch_denied_from_bound_session` (nuovo: ramo non `tg/*` da sessione legata); `test_check_bash.py::BoundSessionTest.test_push_and_pr_denied`; `test_check_writes.py::ExecutionL1Test.test_main_checkout_is_denied`; `test_check_post_bash.py::PostBashTest.test_merge_bringing_deleted_test_opens_needs_you` | |
| 8 Subagenti | `test_check_agents.py::PreAgentTest.test_context_guard`; `test_check_agents.py::PreAgentTest.test_single_writer_and_stale`; `test_subagents.py::SubagentsTest.test_is_stale_uses_last_seen_then_started` | |
| 13 Atti | `test_check_acts.py::ActsTest.test_skill_tool_does_not_create_acts`; `test_check_acts.py::ActsTest.test_non_tollgate_and_status_are_not_acts`; `test_check_acts.py::ActsTest.test_approve_waiver` (positivo); `test_check_acts.py::ActsTest.test_finish_bound_to_head` (positivo); `test_check_acts.py::ActsTest.test_decision15_object_and_target` (positivo) | |
| 14 Wrapper | `test_wrapper.py::WrapperTest.test_control_errors_become_2`; `test_wrapper.py::WrapperTest.test_timeout_becomes_2`; `test_wrapper.py::WrapperTest.test_informative_errors_become_0`; `test_wrapper.py::WrapperTest.test_inactive_repo_exits_0_without_running`; `test_wrapper.py::WrapperTest.test_without_python`; `test_wrapper.py::WrapperTest.test_off_on_and_expiry` | |
| 15 Ricevute | `test_verify.py::VerifyUnitTest.test_receipt_state` (zero test → `empty`); `test_verify.py::VerifyRunTest.test_old_report_is_removed_before_run` (nuovo); `test_verify.py::VerifyRunTest.test_green_receipt_and_clean_env` (`SEGRETO` non visibile); `test_verify.py::VerifyUnitTest.test_clean_env` | |
| 18 Componenti | `test_check_writes.py::ExecutionL1Test.test_scope_component_off` (`scope_check`); `test_check_post_edit.py::PlanCheckHookTest.test_plan_component_off` (`plan_check`); `test_check_commit.py::CommitTest.test_test_guard_component_off` (`test_guard`); `test_check_subagent_stop.py::ReceiptGateOffTest.test_done_without_receipt_passes` (`subagent_receipt_gate`); `test_check_subagent_stop.py::ReadonlyOffTest.test_tampering_ignored_when_component_off` (`readonly_check`); `test_check_agents.py::PromptSubmitCutTest.test_budget_component_off_still_closes_row_without_block` (`task_budget`); `test_components_p2.py::ContextGuardOffTest.test_context_over_stop_passes_when_off` (`context_guard`, nuovo); `test_components_p2.py::SingleWriterOffTest.test_second_writer_passes_when_off` (`single_writer`, nuovo); `test_components_p2.py::TaskSizeOffTest.test_big_task_without_size_reason_passes_when_off` (`task_size`, nuovo); `test_components_p2.py::ReportFieldsOffTest.test_invalid_report_passes_when_off` (`report_fields`, nuovo); `test_components_p2.py::MustHaveTestsOffTest.test_must_have_without_test_registers_when_off` (`must_have_tests`, nuovo) | |
| 19 Budget | `test_criteria_p2.py::EndToEndTest.test_session_start_injects_state`; `test_hook_engine.py::RunnerTest.test_inject_budget_session_start` | |
| 20 Rinomine | `test_testguard.py::TestGuardTest.test_rename_with_same_tests` | |
| 21 Deroghe | `test_check_commit.py::CommitTest.test_pending_test_waiver_lets_commit_pass`; `test_check_commit.py::CommitTest.test_out_of_scope_then_waiver`; `test_waivers.py::WaiversTest.test_pending_waiver_still_covers_locally` | Deroga per pattern in `attenzione` (P4) |
| 22 Livelli | `test_check_post_edit.py::LevelTest.test_l0_grows_to_l1_and_plan`; `test_check_post_edit.py::LevelTest.test_sensitive_path_goes_l2`; `test_level.py::LevelTest.test_cap_holds_until_new_sensitive_path` | Livello dichiarato sotto il minimo → `verdict` rosso (P4) |
| 23 Effetti ripetuti | `test_check_effects.py::EffectsTest.test_veto_act_once_then_warning`; `test_check_effects.py::EffectsTest.test_new_sha_is_a_new_effect_without_warning` | |
| 29 Profili | `test_profiles.py::ProfilesTest.test_active_and_skills`; `test_verify.py::VerifyUnitTest.test_gate_commands_with_profiles` | `gate` del profilo nel gate (P4) |
| 30 Senza test | `test_check_subagent_stop.py::AllowNoTestsTest.test_empty_receipt_counts`; `test_dod.py::DodTest.test_empty_needs_allow_no_tests` | `attenzione` rosso nel gate (P4) |
| 31 Fasi dopo `finish` | `test_check_writes.py::PhasesTest.test_review_and_pr_open` | `finish check` rosso riporta a `execution` (P3) |
| 32 Marcatori e `skipped` | `test_check_commit.py::CommitTest.test_mark_skip_added`; `test_check_commit.py::CommitTest.test_pytest_skip_added`; `test_testguard.py::TestGuardTest.test_pytest_mark_skip_added` | `skipped` nel JUnit della testa → `verdict` rosso (P4) |
| 34 Modalità | `test_check_bash.py::DetectModePushTest.test_push_default_branch_denied_in_detect` (nuovo); `test_check_bash.py::RepoLevelTest.test_push_to_default_branch` | `init` con token senza amministrazione; primo push con `tollgate-sentinel` (P4) |
| 37 Flusso dopo l'approvazione | `test_check_writes.py::PhasesTest.test_spec_audit_no_plans`; `test_check_common.py::LockedDocsTest.test_spec_locked_after_approval_in_later_phase`; `test_check_common.py::LockedDocsTest.test_spec_unlocked_after_reopen_spec_keeps_history_file`; `test_check_common.py::LockedDocsTest.test_plan_locked_after_registration_in_execution`; `test_check_common.py::LockedDocsTest.test_plan_unlocked_after_reopen_plan` | `needs_fix` → `task start --from-findings`; `plan_sha` di `approve plan` in L2 (P3) |
| 38 Profili verticali | `test_check_subagent_stop.py::WebProfileSkillTest.test_done_without_profile_skill_vetoes` (nuovo); `test_check_subagent_stop.py::ExtraTest.test_required_skill_missing_vetoes`; `test_check_agents.py::PreAgentTest.test_profile_agent_replaces_generic_implementer` (nuovo) | `task start` che sceglie gli agenti dal profilo; unione delle skill di due profili; `final_specialist` (P3) |
| 39 Task piccoli e budget | `test_check_subagent_stop.py::BudgetAndSizeTest.test_size_reason_required_over_max`; `test_check_subagent_stop.py::BudgetAndSizeTest.test_tokens_over_cap_block_even_with_green` (con `needs_you` aperto); `test_check_subagent_stop.py::ReceiptGateTest.test_invalid_report` (report senza campi, hook); `test_check_agents.py::PromptSubmitCutTest.test_background_cut_closes_row_budgets_task_and_blocks`; `test_check_agents.py::PostAgentExtraTest.test_foreground_cut_records_tokens`; `test_report.py::ReportTest.test_turn_cut_requires_int_count_and_prefix`; `test_report.py::ReportTest.test_missing_fields` | `status` che dice quale tetto ha fermato il lavoro (P3); `attenzione` per `size_reason` mancante (P4) |
| 42 Must-have e `plan-check` | `test_plan.py::PlanCheckTest.test_must_have_without_test`; `test_plan.py::PlanCheckTest.test_manual_test_allowed`; `test_check_post_edit.py::PlanCheckHookTest.test_pattern_and_must_have_without_test`; `test_components_p2.py::MustHaveTestsOffTest.test_must_have_without_test_registers_when_off` (nuovo) | Ricalcolo della voce dal JUnit in DoD e nel gate (P3, P4) |

Criteri non assegnati a P2 dalla matrice di piano: 1, 9-12, 16, 17, 24-28, 33, 35, 36, 40, 41, 43, 44.

## Test ed esiti
- `tests/run`: `Ran 642 tests ... OK` su Python 3.11.16 e 3.13.5 (nel run del fix round 1 il solo 3.13 ha avuto un fallimento intermittente, vedi sotto).
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: `Ran 641 tests ... OK`, nessun avviso.
- Test nuovi: `test_criteria_p2` (4), `test_components_p2` (5), `WebProfileSkillTest` (1), `DetectModePushTest` (1), `test_old_report_is_removed_before_run` (1), `test_profile_agent_replaces_generic_implementer` (1), `test_push_other_branch_denied_from_bound_session` (1, nel fix round 1). Totale nuovi: 14. Totale: 628 + 14 = 642.
- Mutazione temporanea (`bin/tollgate_core/verify.py:92` disattivato): il test di criterio 15 fallisce; ripristinato, `git diff -- bin/` vuoto.

## File cambiati
- Creati: `tests/test_criteria_p2.py`, `tests/test_components_p2.py`.
- Modificati: `tests/test_check_agents.py`, `tests/test_check_bash.py`, `tests/test_check_subagent_stop.py`, `tests/test_verify.py`, `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`, `docs/superpowers/plans/2026-10-09-tollgate-p2-guardrail.md` (solo le due righe delle decisioni, vedi sotto).
- Codice di prodotto: nessuno modificato.

## Dubbi e concerns
1. **Unione delle decisioni per la rev 21.** I tre elenchi erano diversi: Files 1, 6, 7, 13, 15, 22; Step 3 1, 4, 5, 22, 7, 13, 15, 10, 9, 11; intestazione del piano P2 1, 2, 6, 7. Ho scelto l'unione 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15, 22, applicata a spec, piano principale e righe del piano P2. Se il controller voleva un sottoinsieme, basta cambiare le tre righe.
2. **Correzione di sostanza in 8.1.** La spec diceva «uno stato non riconosciuto vale come DONE». Il codice (`subagent_stop.py`, `report_fields`) e la 18.5 dicono il contrario: report non valido e veto. Ho riscritto la frase. Va confermata, perché cambia un'affermazione della spec.
3. **OFF e lettura dell'input.** Il ruling dice «OFF si controlla prima di leggere l'input». Il wrapper fa `INPUT="$(cat)"` prima del controllo di `OFF`, poi non interpreta nulla finché `OFF` non è escluso (tranne `/tollgate:on|off`). Nella spec ho scritto «prima di ogni interpretazione dell'input», che descrive il codice. Il ruling letterale non coincide con l'ordine delle righe del wrapper: se va riformulato in modo più stretto, va cambiato il wrapper, non solo la spec.
4. **`xdescribe` non ha un test di hook.** Il commit usa `testguard.check`, già testato a livello di modulo. Non ho aggiunto un fixture JS.
5. **Parti non coperte da P2.** Sono indicate nella matrice: `task done` senza `approved`, terzo `task start --fix`, `finish check` rosso, `task start` che sceglie gli agenti di profilo, `status` con il tetto che ha fermato il lavoro, ricalcolo DoD dal JUnit, e tutto ciò che è gate (P4).
6. **Il Task 1 aveva dichiarato di aver scritto in 6.3 il riconoscimento via `UserPromptSubmit`.** Era presente, ma in forma più vaga di quanto fa il codice. Ho precisato il testo (prefisso, blocco per blocco, `task_budget`).

## Fix round 1

Richiesta del coordinatore: sistemare la spec, la matrice e il piano, e aggiungere test. Nessun codice di prodotto modificato.

1. **Spec 7.1, punto 2 (OFF).** Riscritto come richiesto: «`OFF` si controlla prima della ricerca del repo attivo, di Python e di ogni logica di tollgate; dall'input il wrapper legge solo `command_name` e `command_args` per `/tollgate:on|off` e, per `UserPromptSubmit`, la presenza di `<task-notification>`». Il wrapper non è stato toccato.
2. **Matrice, criterio 13.** Aggiunti i positivi `test_check_acts.py::ActsTest.test_approve_waiver`, `ActsTest.test_finish_bound_to_head`, `ActsTest.test_decision15_object_and_target` (nomi verificati: classe `ActsTest`).
3. **Criterio 39.**
   - `test_check_subagent_stop.py::BudgetAndSizeTest.test_tokens_over_cap_block_even_with_green`: aggiunta l'asserzione che il blocco aperto sul lavoro sia uno solo, di tipo `needs_you`.
   - Matrice: citato il test d'hook per il report senza campi. Nota: il coordinatore indicava `ExtraTest.test_invalid_report`, ma il test sta in `ReceiptGateTest`; citato `ReceiptGateTest.test_invalid_report`.
   - «Resta a»: aggiunta la parte `attenzione` per `size_reason` mancante (P4).
4. **Criterio 7.** Nuovo test `tests/test_check_bash.py::BoundSessionTest.test_push_other_branch_denied_from_bound_session`: `git push origin feature-x` e `git push origin HEAD:feature-x` da una sessione legata nel worktree sono negati (exit 2). Citato in matrice.
5. **Spec 7.1, punto 5 (scadenza).** Il tetto di 85 s vale solo per il cane da guardia: `timeout_s` letto dal riferimento remoto è limitato a 85 s per il cane (`timeout_s + 2`, al più 87 s). Python usa `timeout_s` come configurato. Verificato in `hooks/run`: `[ "$TIMEOUT" -gt 85 ] && TIMEOUT=85` precede la scrittura del cane.
6. **Piano principale, `apply.OPS`.** Elencati i 22 nomi, letti da `bin/tollgate_hooks/apply.py` e confrontati con il runtime `apply.OPS` (stesso insieme).
7. **Spec 6.3 (token).** Aggiunto che il conteggio esclude `cache_read_input_tokens` (decisione 20).

Verifica dei riferimenti della matrice: 98 riferimenti `file::Classe.metodo` nel piano principale, tutti presenti.

Test:
- `tests/run`: 642 test. Python 3.11.16: OK. Python 3.13.5: un fallimento intermittente, vedi sotto.
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 642 OK, nessun avviso.

**Fallimento intermittente (non corretto, da decidere).** `tests/test_db.py::OpenTest.test_concurrent_first_open` fallisce in circa 1 esecuzione su 6 se lanciato da solo, e una volta nella suite completa su 3.13. Tre processi aprono per la prima volta lo stesso DB con `db.open_db`, e uno di loro esce con `sqlite3.OperationalError: disk I/O error` (poi `DbError`). È un difetto di concorrenza nell'apertura del DB (P1, con le modifiche di P2 in `db.py`), non un problema del test. Non l'ho corretto in questo task, come da regole: va deciso se aprirlo come fix di P1/P2 prima del merge.

## Dubbi aggiornati
- Il punto 6 dei dubbi del primo giro resta valido per la decisione 20: ora è scritta nella 6.3.
- Il fallimento intermittente di `test_concurrent_first_open` (sopra) è un difetto di prodotto: stato DONE_WITH_CONCERNS.
