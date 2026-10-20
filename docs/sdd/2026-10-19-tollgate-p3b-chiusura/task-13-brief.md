### Task 13: `abandon`, `cleanup`, merge e chiusura in `start`

**Files:**
- Create: `bin/tollgate_flow/closing.py`
- Modify: `bin/tollgate_flow/start.py` (ripresa: `prstate.detect`, PR chiusa senza merge → conferma), `bin/tollgate_flow/gitw.py` (`worktree_remove`), `bin/tollgate_checks/_common.py` (`orphan_tg`: per un ramo di un lavoro chiuso indica `/tollgate:cleanup`, non `adopt`), `bin/tollgate_core/cli.py` (`abandon N`, `cleanup [--confirm] [--orphans]`)
- Test: `tests/test_closing.py`, `tests/test_start.py`

**Interfaces:**
- Produces in `gitw.py`: `worktree_remove(repo, path) -> None` (`git worktree remove <percorso>`, senza `--force`; `GitWriteError` se sporco).
- Produces in `closing.py`:
  - `abandon(state, cwd, issue: int, *, now=None, argv=None) -> tuple[int, list[str]]` (decisione 20);
  - `CleanupItem(kind: str, issue: int | None, branch: str, sha: str | None, worktree: Path | None, dirty: bool)` con `kind` in `closed`, `orphan`;
  - `cleanup(state, cwd, *, confirm: bool, orphans: bool, now=None, argv=None) -> tuple[int, list[str]]` (decisione 19: senza `confirm` codice 3 e l'elenco, atto non consumato).
- Produces in `start.py`: in ripresa, dopo il fetch, `prstate.detect`; `merged` → riga «lavoro #N chiuso: la PR è stata unita» e codice 0 senza `EnterWorktree`; `closed` → conferma (codice 3) con `CLOSED_HINT`; con `--confirm` `set_pr(None, None)`.

- [ ] **Step 1: Test** `test_closing.py`: `test_abandon_closes_and_keeps_branch`; `test_abandon_needs_act_and_matching_issue`; `test_cleanup_lists_then_deletes_with_confirm` (primo giro codice 3 e atto ancora `pending`; secondo giro ramo e worktree tolti); `test_cleanup_skips_dirty_worktree`; `test_cleanup_orphans_only_with_flag` (riga 55: `WorkExists` simulato dopo `worktree_add`, con una riga attiva per lo stesso N su un altro ramo → il ramo orfano è elencato e, con `--orphans --confirm`, tolto); `test_orphan_hint_on_closed_work_points_to_cleanup`.
- [ ] **Step 2: Test** `test_start.py::ResumeTest`: `test_merged_pr_closes_work` (criterio 1, 6.5); `test_closed_pr_asks_and_confirm_clears_pr`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: abandon, cleanup, merge e chiusura rilevati alla ripresa».

---

