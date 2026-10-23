### Task 13: `finish check` sul gate, campi del blocco, commento letto da `--from-gate`

**Files:**
- Modify: `bin/tollgate_flow/finishcheck.py`, `bin/tollgate_flow/openpr.py`, `bin/tollgate_analysis/prblock.py`, `bin/tollgate_flow/taskcmd.py` (evento `skills_absent`), `bin/tollgate_flow/fixtask.py`, `bin/tollgate_core/events.py` (tipo nuovo), `bin/tollgate_core/subagents.py`, `bin/tollgate_checks/subagent_stop.py` e `bin/tollgate_hooks/apply.py` (`size_reason` nell'evento `subagent_stop`, decisione 21)
- Test: `tests/test_finishcheck.py`, `tests/test_openpr.py`, `tests/test_prblock.py`, `tests/test_fixtask.py`, `tests/test_criteria_p4.py` (nuovo, la classe `AgreementTest`)

**Interfaces:**
- Consumes: `evaluate.evaluate`, `model.GateInputs` (Tasks 4-5), `comment.marker_sha` (Task 6).
- Produces: `finishcheck.check` invariata (firma, codici, `CheckResult`); `finishcheck._gate_inputs(state, conn, work, cfg, wt, sha, run, *, now, environ) -> GateInputs`; `finish_report["gate"]` (decisione 20); `prblock.FIELDS` con `tasks_over` e `skills_absent` in coda; `openpr.facts` con `findings[].blocking`, `tasks_over`, `skills_absent`; evento `skills_absent` {task, skills}; `fixtask.from_gate` con `source = "gate:<sha del marcatore>"` e solo commenti con `author.login` in `ghcli.BOT_LOGINS`.

- [ ] **Step 1: Test** `test_finishcheck.py`: `test_contract_unchanged` (codici e chiavi di `items` come prima su un lavoro L1 verde; `gate` presente); `test_level_below_minimum_is_red` (decisione 20); `test_tollgate_file_changed_is_red`; `test_attention_printed_in_groups`; `test_issue_unreadable_warns_and_continues`.
- [ ] **Step 2: Test** `test_check_subagent_stop.py::test_size_reason_in_event` (report con `size_reason` → l'evento `subagent_stop` lo porta); `test_finishcheck.py::test_stale_approval_still_fails_dod_locally` (rilievo I-4); `test_openpr.py::test_block_new_fields` e `test_prblock.py::test_fields_order_with_new_fields` (le due voci in coda; un blocco vecchio senza le due voci si legge ancora).
- [ ] **Step 3: Test** `test_fixtask.py`: `test_from_gate_uses_marker_sha_and_bot_author` (Review Focus 3); `test_marker_without_sha_refused` (commento con il solo prefisso → rifiuto «commento del gate senza SHA»).
- [ ] **Step 4: Test** `test_criteria_p4.py::AgreementTest`: `test_finish_check_and_gate_agree` (Review Focus 1: `FlowLab` L2 con un file fuori scope, un test cancellato e la spec approvata; `finish check` dal programma vero e `evaluate` con `where="github"` sugli stessi commit danno lo stesso insieme di chiavi rosse nelle famiglie `diff`, `l2`, `must_have`, `level`); `test_plan_change_is_the_only_difference` (stesso banco più il piano registrato cambiato senza file nuovi: `finish check` ha la violazione del piano, il gate solo `plan_changed`, decisione 9); `test_open_pr_block_feeds_gate` (Review Focus 2: corpo scritto da `open-pr` nel `gh` finto, letto da `gate evaluate` → `findings[].blocking`, `tasks_over`, `skills_absent` arrivati).
- [ ] **Step 5: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: finish check usa il calcolo del gate; campi nuovi del blocco; marcatore letto da --from-gate».

---

