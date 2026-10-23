### Task 4: Ingressi, gruppi di `attenzione` e calcolo: comandi, base, diff, piano

**Files:**
- Create: `bin/tollgate_gate/model.py`, `bin/tollgate_gate/attention.py`, `bin/tollgate_gate/evaluate.py`, `tests/gatekit.py`, `tests/test_gate_evaluate.py`

**Interfaces:**
- Produces in `model.py`:
  - `CommandResult(name: str, state: str, exit: int | None, tests_run: int | None, junit: Junit | None)`;
  - `PrFacts(number: int, head_sha: str, head_ref: str, base_ref: str, default_branch: str, body: str, cross_repo: bool)`;
  - `IssueFacts(number: int, state: str, labels: tuple[str, ...])`;
  - `GateInputs(where: str, repo: Path, cfg: Config, base_sha: str, head_sha: str, pr: PrFacts | None, block: dict | None, issue: IssueFacts | None, commands: list[CommandResult] | None, base_ids: dict[str, set[str]] | None, base_ids_source: str | None, waiver_text: str | None, sentinel_open: list[int])`;
  - `Item(key: str, family: str, text: str, data: str = "")` (`data` è testo non fidato, solo per il commento);
  - `Evaluation(red: list[Item], attention: list[Item], watch: list[str], errors: list[str])` con le proprietà `verdict_state` (`error` se `errors`, `failure` se `red`, altrimenti `success`) e `attention_state` (decisione 7).
- Produces in `attention.py`: `GROUPS` (decisione 7), `READ = "read"`, `INFO = "info"`, `group(key) -> str` (`KeyError` per una chiave sconosciuta: ogni voce ha un gruppo).
- Produces in `evaluate.py`: `evaluate(inputs: GateInputs) -> Evaluation`; in questo task le famiglie `commands`, `base_ids`, `diff` (con `plan_changed` e lo scope da `plan_sha`), `must_have` e le voci di deroga (`waiver_*`). Le famiglie `level`, `l2`, `issue`, `declared`, `guard_local` sono del Task 5.
- Produces in `tests/gatekit.py`: `GateLab` (repo git temporaneo con `origin` nudo locale, `tollgate.toml` sul predefinito, ramo `tg/7-x`), `GateLab.inputs(**override) -> GateInputs`, `GateLab.block(**override) -> dict` (da `prblock.build` con valori validi), `GateLab.junit(ids_run, ids_skipped=(), ids_failed=()) -> Junit`.

- [ ] **Step 1: Test** `test_gate_evaluate.py::CommandsTest`: `test_red_empty_uncounted_unverified` (ogni stato → voce rossa `commands`; `empty` con `allow_no_tests` → verde più `no_tests_counted`; `unverified` con un atto `approve unverified-tests` nel blocco → verde più `unverified_tests`); `test_or_true_with_failure_is_red` (criterio 10: uscita 0, JUnit con un fallito → `red`); `test_profile_gate_command_required` (criterio 29: profilo con `paths = ["web/**"]`; diff su `web/` senza il risultato `profile:web:lint` → rosso «manca»; diff fuori da `web/` → non richiesto).
- [ ] **Step 2: Test** `BaseIdsTest`: `test_missing_base_id_is_red`; `test_inactive_profile_ids_not_compared` (rilievo N-2: `ids.json` con i test di `profile:web:test`, PR che non tocca `web/` → nessuna voce rossa per quei test; PR che tocca `web/` e perde un test di `web` → rosso); `test_skipped_in_head_is_missing` (criterio 32); `test_test_waiver_covers_only_with_all_ids` (8.3, 18.2); `test_component_off_skips` (`base_test_ids = false` → nessuna voce `base_ids`, `components_off`); `test_local_has_no_base_ids` (`where="local"`).
- [ ] **Step 3: Test** `DiffTest`: `test_testguard_on_every_pr` (criterio 10: test cancellato e `.skip` aggiunto → rosso anche su un ramo non `tg/*`); `test_out_of_scope_tg_only` (file fuori scope → rosso su `tg/7-x`, nessuna voce su `fix/x`); `test_plan_changed_after_registration` (criterio 36: piano in testa con un file in più → quel file è fuori scope e `plan_changed` porta il diff); `test_waiver_of_other_issue_ignored` (criterio 10: deroga in `.tollgate/waivers/3.toml` su una PR dell'issue 7 → la violazione resta); `test_waiver_branch_must_match` (8.3); `test_waiver_groups` (criterio 44: una sola deroga `scope` → solo `waiver_scope` informativa, `attention_state == "success"`; una deroga `test` → `waiver_test` «da leggere», `failure`; tre deroghe `scope` → `waiver_scope_over_two`; deroga per pattern → `waiver_pattern`, criterio 21); `test_reviews_dir_exempt` (contratto P3c (6)).
- [ ] **Step 4: Test** `MustHaveTest`: `test_must_have_recomputed_from_head_junit` (criterio 42: `M1 — test: tests.test_x::test_a` assente → rosso, rosso nel JUnit → rosso, verde → nessuna voce; `— test: manuale` → `manual_must_have`); `test_component_off`.
- [ ] **Step 5: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: calcolo del gate (comandi, base, diff, piano, must-have) e gruppi di attenzione».

---

