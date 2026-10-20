### Task 12: `adopt`

**Files:**
- Create: `bin/tollgate_flow/adopt.py`
- Modify: `bin/tollgate_core/cli.py` (`adopt N`)
- Test: `tests/test_adopt.py`

**Interfaces:**
- Consumes: `acts.find_usable`/`consume` (`type_="adopt"`, `target=str(N)`, `work=None`), `phases.create_work(..., phase=, cause="adopt")`, `scope.register_plan(..., advance=False)`, `plan.check_plan`, `approvals.parse_approval`, `prblock.parse`, `gh.pr_for_branch`, `gh.issue`, `level.diff_level`, `labels_level`, `gitw.create_branch`, `gitw.worktree_add`, `git.worktrees`, `active.register`, `sessions.mark_bound`, `phases.set_level_cap`.
- Produces in `adopt.py`: `AdoptResult(code: int, lines: list[str], worktree: Path | None, work: int | None)` e `adopt(state, cwd, issue: int, *, now=None, argv=None) -> AdoptResult` (decisione 18). Ultima riga `prossimo passo: EnterWorktree <percorso>`.
- CLI: `tollgate adopt N`.

- [ ] **Step 1: Test** `test_adopt.py`:
  - `test_hooks_deny_on_orphan_branch_then_adopt` (DB cancellato, Edit su un file di codice nel worktree `tg/7-*` → `deny` con `/tollgate:adopt #7`; poi `adopt 7` → riga, fase, sessione legata; criteri 17 e 1);
  - `test_start_refusal_then_adopt` (ramo remoto `tg/7-x` → `start 7` rifiuta con l'adozione; `adopt 7` riesce; criterio 1);
  - `test_l2_with_plan_approval_stays_execution` (criterio 17);
  - `test_l2_without_plan_approval_goes_approval` (criterio 17);
  - `test_approved_waivers_back_pending` (deroga `test` nel file del ramo → `waivers.status` la dà `pending`; criterio 17);
  - `test_l1_without_plan_goes_plan`; `test_l1_with_plan_registers_scope_and_pending_tasks`;
  - `test_open_pr_gives_pr_open_and_cap_from_block` (corpo della PR con `level_cap: "L1"` → tetto L1);
  - `test_branch_in_existing_worktree_reused` (riga 74, Review Focus 5);
  - `test_remote_only_branch` (Review Focus 5);
  - `test_refused_with_active_work_or_merged_pr_or_two_branches`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: adopt (ricostruzione dal ramo, fase dalle prove, worktree riusato)».

---

