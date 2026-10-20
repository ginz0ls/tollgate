### Task 11: `sync`

**Files:**
- Create: `bin/tollgate_flow/sync.py`
- Modify: `bin/tollgate_flow/gitw.py` (`merge_ff_only`, `rebase`, `rebase_abort`, `is_ancestor`; `merge_base` è del Task 10), `bin/tollgate_flow/start.py` (ripresa: `sync.complete_interrupted`), `bin/tollgate_core/cli.py` (`sync`)
- Test: `tests/test_sync.py`, `tests/test_start.py`

**Interfaces:**
- Consumes: `acts.find_usable`/`consume` (`type_="sync"`), `intents.request/complete/authorize_force`, `phases.set_base`, `phases.set_phase(..., "execution", "sync")`, `finishcheck.check`, `openpr.open_pr(..., via_sync=<atto>)`, `prstate.detect`.
- Produces in `gitw.py`: `merge_ff_only(wt, ref) -> bool`; `rebase(wt, onto) -> bool` (falso con conflitto, rebase lasciato in corso); `rebase_abort(wt) -> None`; `is_ancestor(repo, a, b) -> bool`. Il blocco del conflitto ha il motivo che comincia con `intents.SYNC_CONFLICT_REASON`.
- Produces in `sync.py`:
  - `SyncResult(code: int, lines: list[str])`, codici `OK = 0`, `REFUSED = 1`, `BLOCKED = 2`, `REVIEW_NEEDED = 3`;
  - `sync(state, cwd, *, now=None, argv=None, environ=None) -> SyncResult` (decisione 17);
  - `complete_interrupted(conn, state, work, wt: Path, *, now, session=None) -> str | None`: con un intento `sync` `requested`, nessun rebase in corso e la punta di arrivo antenata di HEAD, completa base, commit ed eventi e restituisce la riga d'avviso; altrimenti `None`. `start` la chiama **prima** di raccogliere gli intenti da confermare: un `sync` completato così non chiede conferma.
- CLI: `tollgate sync`, sessione con `cli_session(state, cwd, "sync", argv=…)`.

- [ ] **Step 1: Test** `test_sync.py` (`FlowLab` con lavoro in `pr_open`, PR nel finto `gh`, il predefinito avanzato con un commit che non tocca i file del lavoro):
  - `test_refused_without_sync_act` (criterio 16);
  - `test_rebase_realigns_base_and_updates_pr` (ramo rifatto sulla punta, `work_base_sha` = punta, eventi `commit` per gli SHA nuovi, `pr_updated`, push con lease; criterio 16);
  - `test_same_patch_id_no_cycle_consumed` (numero di cicli invariato; criterio 16);
  - `test_remote_merge_then_rebase` (un commit «Update branch» su `origin/<ramo>` → integrato con `--ff-only`, poi rebase; Review Focus 4; criterio 16);
  - `test_conflict_aborts_and_blocks` (conflitto → nessun rebase in corso, base e fase invariate, `needs_you` con le due strade; criterio 16);
  - `test_post_bash_ignores_rewritten_commits` (dopo `sync`, `PostToolUse Bash` sul worktree non apre blocchi);
  - `test_different_patch_id_asks_new_review` (codice 3, nessun push).
- [ ] **Step 2: Test** `test_start.py::ResumeTest::test_interrupted_sync_completed_by_start` (intento `sync` `requested` e rebase finito → `start` completa base ed eventi; Review Focus 4) e `test_interrupted_sync_with_rebase_in_progress_proposes_abort`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: sync (integrazione, rebase, base riallineata, PR aggiornata)».

---

