### Task 3: Analisi pura: approvazioni L2, workflow del progetto, issue della PR

**Files:**
- Create: `bin/tollgate_analysis/workflows.py`, `bin/tollgate_analysis/prref.py`, `tests/test_workflows.py`, `tests/test_prref.py`
- Modify: `bin/tollgate_analysis/approvals.py`, `tests/test_approvals.py`, `tests/test_l2tree.py`

**Interfaces:**
- Produces in `approvals.py`: `L2Problem(kind: str, text: str)` (`MISSING = "missing"`, `STALE = "stale"`); `check_l2_detail(files, *, issue, spec_path, spec_blob, plan_path, plan_blob, components: Mapping[str, bool] | None = None) -> list[L2Problem]` (decisione 10); `check_l2` invariata nella firma, sopra `check_l2_detail`; `locate_spec_approval` con l'ordine del caso (a) (decisione 22).
- Produces in `workflows.py`: `problems(text: str) -> list[str]` (decisione 15); `FORBIDDEN_EVENTS = ("pull_request_target", "workflow_run")`, `GUARDED_SCOPES = ("statuses", "checks")`, `SAFE_VALUES = ("read", "none")`; `is_workflow_path(rel: str) -> bool` (`.github/workflows/*.yml` e `*.yaml`).
- Produces in `prref.py`: `issue_from_branch(ref: str) -> int | None`, `closes_issue(body: str) -> int | None`, `is_tg_branch(ref) -> bool`, `is_config_branch(ref) -> bool` (`tollgate-config/`).

- [ ] **Step 1: Test** `test_approvals.py`:
  - `test_current_beats_own_stale` (propria con `sha` X, issue 3 con `sha` Y, `spec_blob` Y → la 3; `spec_blob` X → la propria; `spec_blob` None → la propria);
  - `test_check_l2_detail_kinds` (approvazione assente → `missing`; `sha` diverso → `stale`; `slices: "tre"` → `missing`; `plan-approval.md` con `path` diverso da `plan_path` → `missing`; `plan-approval.md` superato e nessun report del piano → un solo problema `stale`, nessun «report del piano mancante»);
  - `test_reports_bound_to_approved_sha` (caso (d): un solo `spec-adversarial-1.md` con `spec_sha` vecchio → `missing` «nessun report della spec sullo sha approvato»; con `adversarial: off` e `lens: off` → nessuno; `plan-adversarial` con `plan_sha` vecchio → `missing`);
  - `test_check_l2_messages` (riga 7 di P3c: asserzioni sul testo di ogni problema, compreso il caso dell'approvazione propria con `path` diverso);
  - `test_plan_approval_on_other_spec_is_missing` (`plan-approval.md` corrente sul piano ma con `spec_sha` diverso dall'approvazione della spec → `missing`, rilievo I-4);
  - `test_header_off_with_component_on_is_missing` (`adversarial: off` con `components={"spec_adversary": True}` → `missing`; con `False` nessun problema; `components=None` → comportamento di oggi).
- [ ] **Step 2: Test** `test_l2tree.py::test_spec_approval_current_when_other_issue_approved_same_blob` (`CURRENT` con la propria superata e la 9 corrente).
- [ ] **Step 3: Test** `test_workflows.py`: `test_clean_workflow` (`permissions: {contents: read}` e `on: push` → `[]`); `test_forbidden_events` (anche in forma di elenco e di mappa); `test_forbidden_permissions_any_level` (`statuses: write` dentro un job, `permissions: write-all`); `test_quoted_and_flow_forms` (`statuses: "write"`, `statuses: 'write'`, `permissions: {statuses: write}`, `on: [push, pull_request_target]` → rossi; `statuses: read` e `checks: none` → nessun problema); `test_anchors_and_aliases_fail_closed` (`&perm`, `*perm`, `<<:`); `test_yaml_extension` (`is_workflow_path`); `test_missing_top_level_permissions`; `test_comments_and_strings_ignored` (`# pull_request_target` in un commento non conta; in una stringa di `run:` conta: fail-closed); `test_unreadable_is_a_problem` (testo con tabulazioni di rientro o byte non UTF-8). `test_prref.py`: `test_issue_from_branch` (`tg/7-x` → 7; `tg/x` → None); `test_closes_issue_variants` (`Closes #3`, `fixes #3`, `Resolves #3`; la prima riga vince; `#3` senza parola chiave → None).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`.** I test esistenti di `finish check` e di `audit prepare` che dipendono dall'ordine di `locate_spec_approval` si aggiornano con una riga nel report.
- [ ] **Step 5: Commit** «tollgate P4: approvazioni L2 dettagliate (corrente vince, report sullo sha approvato), regole dei workflow, issue della PR».

---

