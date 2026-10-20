### Task 4: Violazioni dell'intero diff in core, `verify.run_gate`

`finish check` vive in `tollgate_flow` e non può importare `tollgate_checks`. Le regole di scope e test-guard si spostano in `tollgate_core`, e gli hook le chiamano da lì: una sola fonte.

**Files:**
- Create: `bin/tollgate_core/violations.py`
- Modify: `bin/tollgate_checks/_common.py` (`commit_violations`, `scope_exempt`, `locked_docs`, `is_docs_md`, `_is_registered_plan` delegano), `bin/tollgate_hooks/context.py` (`guard_config` delega), `bin/tollgate_core/verify.py`
- Test: `tests/test_violations.py`, `tests/test_verify.py`; restano verdi senza modifiche `tests/test_check_commit.py`, `tests/test_check_post_bash.py`, `tests/test_check_writes.py`, `tests/test_check_common.py`

**Interfaces:**
- Produces in `violations.py` (nessuna dipendenza da `Ctx`):
  - `guard_config(cfg: Config, files) -> GuardConfig`;
  - `locked_docs(work) -> set[str]`; `is_docs_md(rel) -> bool`;
  - `scope_exempt(cfg, work, rel: str, scope: set[str]) -> bool`;
  - `is_registered_plan(work, wt: Path, path: str, head_ref: str | None) -> bool`;
  - `waiver_file(work) -> WaiverFile | None`;
  - `diff_violations(cfg, conn, work, wt: Path, base_ref: str, head_ref: str | None, changes, *, components: Mapping[str, bool]) -> list[Violation]` (stessa logica di `_common.commit_violations`, violazioni non coperte da una deroga).
- Produces in `verify.py`:
  - `dod_commands(cfg, files) -> list[CommandSpec]`: i `dod` dei profili attivi che non sono già nel gate, con nome `profile:<p>:<c>`;
  - `GateRun(ok: bool, lines: list[str], sha: str | None, states: dict[str, str], junits: dict[str, Junit | None])`;
  - `run_gate(state, cwd, *, produced_by: str, extra: list[CommandSpec] = (), now=None, environ=None) -> GateRun`: come `run_verify` senza `--related`, con le ricevute `produced_by` dato e i JUnit restituiti; `run_verify` usa gli stessi passi interni.

- [ ] **Step 1: Test** `test_violations.py`:
  - `test_same_result_as_hook` (un commit che cancella un test e uno fuori scope: `diff_violations` dà le due violazioni, come `commit_violations` del hook sullo stesso commit);
  - `test_waiver_resolves` (deroga `scope` nel file del lavoro → la violazione sparisce);
  - `test_registered_plan_committed_is_exempt`;
  - `test_components_off` (`scope_check` e `test_guard` a `false` → nessuna violazione).
- [ ] **Step 2: Test** `test_verify.py::RunGateTest`: `test_run_gate_returns_junit_and_produced_by` (comando che scrive un JUnit con due test → `junits["verify"].ids_run` ha i due id, ricevuta con `produced_by == "finish"`); `test_dod_command_of_profile_runs` (profilo con `dod = ["lint"]` e `commands.lint = "true"` → ricevuta `profile:web:lint`).
- [ ] **Step 3: Fallimento, implementazione** (sposta il codice, poi le funzioni di `_common` e `Ctx` chiamano `violations`), **verifica** con la suite degli hook invariata e `tests/run`.
- [ ] **Step 4: Commit** «tollgate P3b: violazioni del diff in tollgate_core, run_gate per finish check».

---

