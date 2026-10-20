### Task 6: `finish check`

**Files:**
- Create: `bin/tollgate_flow/finishcheck.py`, `bin/tollgate_analysis/mustcheck.py`, `bin/tollgate_analysis/approvals.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `finish` con `check`; `open-pr` arriva nel Task 9)
- Test: `tests/test_mustcheck.py`, `tests/test_approvals.py`, `tests/test_finishcheck.py`

**Interfaces:**
- Consumes: `verify.run_gate`, `verify.dod_commands`, `violations.diff_violations`, `dod.compute_dod`, `acts.has_approval`, `phases.set_finish`, `phases.set_phase(..., "review", "finish_check_green")`, `reviews.latest`; `prstate.detect` arriva nel Task 9 e si aggancia lì.
- Produces in `mustcheck.py`: `MustHaveResult(ok: bool, missing: list[str], failed: list[str], manual: list[str])` e `check(must_haves: list[MustHave], ids_run: set[str], ids_failed: set[str]) -> MustHaveResult` (un id assente o fallito rende falsa la voce; `manuale` va in `manual` e non la rende falsa).
- Produces in `approvals.py`: `parse_approval(text: str) -> dict | None` (intestazione YAML di 18.3 per `spec-approval` e `plan-approval`: `kind`, `path`, `sha`, `spec_sha`, `slices`, `adversarial`, `lens`, `act_id`, `approved_at`; righe `chiave: valore`, valori tra virgolette o nudi, `null`); `approval_paths(issue: int) -> tuple[str, str]`.
- Produces in `finishcheck.py`:
  - `CheckResult(code: int, lines: list[str], items: list[DodItem])`, codici `OK = 0`, `RED = 1`, `REFUSED = 2`;
  - `check(state, cwd, *, now=None, environ=None) -> CheckResult`.
- Comportamento di `check` (decisione 4):
  - lavoro da `sessions.work_for_path(conn, cwd)`; fase `execution`, oppure `review` (sullo stesso `finish_sha` restituisce l'esito salvato, su un altro SHA ricalcola); altrimenti rifiuto con la fase;
  - `gitw.fetch` (senza rete: avviso, si prosegue);
  - L1 e L2: ogni task `done` con `verdict == "approved"`, altrimenti rifiuto con i numeri (criterio 41);
  - `run_gate(produced_by="finish", extra=dod_commands(...))`; poi `diff_violations` da `work_base_sha` a HEAD; poi i must-have del piano a `plan_sha` contro l'unione di `ids_run` e `ids_failed` dei JUnit;
  - L2: `approvals` vera se `spec-approval.md` e `plan-approval.md` esistono in HEAD con `sha` uguale al blob di spec e piano in HEAD;
  - `compute_dod(..., required_commands=<gate + dod>, external={"guard_scope", "must_have", "approvals"}, profile_items={"profile:<p>:<c>": <ricevuta green>}, allow_unverified=has_approval(..., "unverified-tests"), skip=("findings", "specialists"))`; il verde di `finish check` è `dod_passes` sulle voci non saltate; in L2 `approvals` controlla solo i file di approvazione, i report avversariali sono di P3c;
  - verde: `set_finish(sha, {"items": {...}, "manual": [...]})`, evento `finish_check` {sha, ok: true}, fase `review`; rosso: evento con `ok: false`, fase invariata (criterio 31);
  - righe: una per voce, `[sì]`, `[no]` o `[dopo la revisione]` con l'etichetta e il dettaglio; ultima riga `prossimo passo: …` (`review prepare` in L1/L2, `finish open-pr` in L0).
- CLI: `tollgate finish check`, uscita con `code`.

- [ ] **Step 1: Test** `test_mustcheck.py` (presente e verde; assente; fallito; `manuale`) e `test_approvals.py` (intestazione valida; senza `---` → `None`; `sha` tra virgolette).
- [ ] **Step 2: Test** `test_finishcheck.py` (con `FlowLab`, `register_plan`, `commit`, `close_tasks`, `JUNIT_TOML`):
  - `test_green_moves_to_review_and_prints_dod` (uscita 0, fase `review`, `finish_sha == HEAD`, una riga per voce di L1; criterio 41);
  - `test_red_stays_in_execution` (un test fallito nel JUnit → uscita 1, fase `execution`; criterio 31);
  - `test_task_not_done_refused` (criterio 41);
  - `test_must_have_test_missing_is_red` (`M1 — test: tests.test_x::test_a` e quel test assente dal JUnit → voce `must_have` falsa; criterio 42);
  - `test_out_of_scope_commit_is_red` (commit fuori scope senza deroga → `guard_scope` falsa);
  - `test_checkpoint_present_is_ignored` (checkpoint scritto con `status --checkpoint` → verde; vincolo (7));
  - `test_rerun_in_review_same_sha_is_idempotent` (criterio 28: interruzione dopo `finish check`);
  - `test_l0_without_tasks`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: finish check, must-have dal JUnit, file di approvazione».

---

