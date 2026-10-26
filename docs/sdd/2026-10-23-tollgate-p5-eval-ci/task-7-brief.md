### Task 7: Banco degli eval

**Files:**
- Create: `evals/_kit/__init__.py`, `evals/_kit/scaffold.py`, `evals/_kit/recipes.py`, `evals/_kit/target.py` (decisione 9 (a) e (c)), `tests/evalbin/gh`, `evals/_kit/fixtures/` (progetto minimo con `unittest` e `tools/unittest_junit.py` come nella prova di P4, `tollgate.toml`, spec e piani delle ricette), `tests/test_eval_kit.py`

**Interfaces:**
- Consumes: `bin/tollgate` e `hooks/run` come processi; `tests/fakegh.py`; la forma degli eventi di `tests/hookkit.py` (il segnale e gli eventi `commit` li scrive `hooks/run`, decisione 3); `ORIGIN_URL` e `insteadOf` di `tests/hookkit.py`; i fatti VE1-VE11.
- Produces:
  - `Recipe` (`dataclass(frozen=True)`: `name`, `level` (`"L0"|"L1"|"L2"`), `issue: int`, `plan: str | None` (nome di un piano in `fixtures/`), `tasks_done: tuple[int, ...]`, `task_started: int | None`, `spec: str | None`, `phase: str | None`, `extra_files: dict[str, str]`, `gh_data: dict`, `issue_title: str` (fissa lo slug del ramo e quindi i percorsi nel worktree)), `RECIPES: dict[str, Recipe]` e `CORRECT_PATHS: dict[str, tuple[tuple[str, ...], ...]]` (per **caso**, non per ricetta: per ogni cammino corretto, i nomi dei grader che passano; li usa `test_correct_paths_score_above_threshold`) in `recipes.py`;
  - `scaffold.build(recipe: Recipe, *, workspace: Path, home: Path, state: Path | None = None) -> Built` (`Built(worktree: Path, work_branch: str, state_root: Path)`); `state=None` vuol dire la cartella predefinita di `home` (decisione 3);
  - `scaffold.main(argv) -> int` (entrata degli `scaffold.sh`: `scaffold.py <ricetta>`, workspace = cartella corrente, `home` = `$HOME`);
  - `target.build(plugin_root: Path, out: Path) -> Path` (copia senza `dependencies`, con `tests/evalbin/` e `tests/fakegh.py`).

- [ ] **Step 1: Test** `test_eval_kit.py`: `test_build_l1_execution` (ricetta `l1-execution`: worktree `tg/1-*`, fase `execution`, piano registrato, task 1 `running`, dal programma vero); `test_state_seen_without_tollgate_env` (Review Focus 1: dopo `build(..., state=None)` con `home` temporanea, `bin/tollgate status --json` lanciato con `HOME=home` e **senza** variabili `TOLLGATE_*` vede il lavoro); `test_scaffold_env_never_reaches_agent_env` (`scaffold.main` non lascia `TOLLGATE_*` nell'ambiente del processo padre né in file letti dall'agente); `test_superpowers_registry_written` (`prereq.superpowers_version(home/.claude) == (7, 0, 0)`); `test_shim_without_data_fails_closed` (Review Focus 6: `tests/evalbin/gh` con `HOME` senza dati → uscita 1, «gh finto dell'eval: dati assenti», nessun altro `gh` lanciato: un `gh` trappola più avanti nel `PATH` non viene chiamato); `test_shim_serves_issue` (con i dati, `gh api repos/<o>/<r>/issues/1` risponde l'issue); `test_build_under_120_seconds` (tempo di `build` sotto i 120 s dello scaffold, VE4); `test_scaffold_writes_no_db_directly` (nessun import di `tollgate_core` in `evals/_kit/`, analisi AST come `test_layers.py`); `test_origin_is_github_url` (`prereq.is_github` vero sul checkout costruito); `test_target_without_dependencies` (`target.build` toglie solo `dependencies`).
- [ ] **Step 2: Fallimento, implementazione, `tests/run`, commit** «tollgate P5: banco degli eval (scaffold dal programma vero, gh finto, ricette)».

---

