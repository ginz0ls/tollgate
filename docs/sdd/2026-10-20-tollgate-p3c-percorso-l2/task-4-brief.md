### Task 4: Migrazione 5, giri nel DB, cause L2, reset del piano

**Files:**
- Create: `bin/tollgate_core/audits.py`
- Modify: `bin/tollgate_core/db.py`, `bin/tollgate_core/phases.py`, `bin/tollgate_core/scope.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/git.py`, `bin/tollgate_core/violations.py` (`scope_exempt`, decisione 26)
- Test: `tests/test_db.py`, `tests/test_audits.py`, `tests/test_phases.py`, `tests/test_scope.py`, `tests/test_git.py`, `tests/test_violations.py`

**Interfaces:**
- Produces in `db.py`: `SCHEMA_V5` (decisione 1), `MIGRATIONS` fino a 5.
- Produces in `events.py`: tipo `plan_reset` (decisione 24).
- Produces in `phases.py`: le tre cause della decisione 11 in `_FORWARD_CONDITION`; `set_spec_path(conn, work: int, path: str, *, now) -> None` (solo se nullo); `create_work(..., from_approved_spec=True)` senza `spec_path` → `ValueError("from_approved_spec richiede spec_path")`.
- Produces in `scope.py`: `reset_plan(conn, work: int, *, now, session=None) -> list[int]` (toglie le righe di `scope` con `origin = 'plan'`, azzera `plan_sha`, cancella i task del lavoro e restituisce i loro numeri; evento `plan_reset`; una transazione).
- Produces in `git.py`: `ls_files_at(repo, ref: str, prefix: str) -> list[str]` (`git ls-tree -r --name-only <ref> -- <prefix>`, `[]` se il riferimento non c'è).
- Produces in `audits.py` (ogni funzione apre la sua transazione):
  - `KINDS`, `AGENTS`, `COMPONENTS = {"spec-adversarial": "spec_adversary", "spec-lens": "spec_audit", "plan-adversarial": "plan_adversary"}`, `CAP_REASONS` (tipo → prefisso, decisione 7), `DECLINE_REASON = "audit a lenti rifiutato dall'utente"`, `SUSPENDED_LABELS` (tipo → «avversariale sospeso», «audit a lenti sospeso», «avversario del piano sospeso»);
  - `open_round(conn, work, *, kind, sha, spec_sha, viewpoint, code, now) -> int` (numero; `ValueError` se c'è già un giro aperto);
  - `open_round_row(conn, work) -> sqlite3.Row | None`;
  - `supersede(conn, work, number_kind: tuple[str, int], *, now) -> None`;
  - `close_round(conn, work, *, kind, number, counts: dict, outcome: str, report_path: str, now) -> None` (evento `spec_audit_round`);
  - `rounds(conn, work, kind) -> list[sqlite3.Row]` (chiusi, non `superseded`, in ordine);
  - `any_rows(conn, work, kind) -> bool` (anche superate e aperte: serve alla conferma del costo, decisione 6);
  - `last_closed(conn, work, kind=None) -> sqlite3.Row | None` (con `kind=None` di qualunque tipo);
  - `suspend(conn, work, kind, number: int, *, now) -> None`; `suspended(conn, work) -> dict[str, int]`;
  - `cap_kind(reason: str) -> str | None` (tipo dal motivo di un blocco, anche `DECLINE_REASON` → `spec-lens`).

- [ ] **Step 1: Test** `test_db.py::MigrationV5Test` (DB v4 con righe → colonne nuove, dati intatti, copia `*migrazione-5*`; `test_latest_version_is_5`; il test v4 asserisce `str(db.latest_version())` se ancora asserisce `"4"`).
- [ ] **Step 2: Test** `test_phases.py`: la tabella `ALLOWED` di L2 usa `approve_spec`, `audit_clean`, `approve_plan`; `test_l2_forward_needs_its_cause` (`spec_audit → plan` con `advance` → `TransitionError`); `test_from_approved_spec_requires_spec_path`; `test_create_work_phase_and_from_approved_spec_exclusive` (già coperto: verificare che esista); `test_set_spec_path_only_once`.
- [ ] **Step 3: Test** `test_scope.py::ResetPlanTest`: `test_reset_then_register_again` (registrato, `reset_plan`, nuova `register_plan` con un altro `plan_sha` → riuscita; task vecchi spariti; evento `plan_reset` con i numeri). `test_git.py::LsFilesAtTest`.
- [ ] **Step 3b: Test** `test_violations.py::ReviewsExemptTest::test_own_reviews_dir_exempt_other_issue_not` (decisione 26: con lo scope registrato un file nuovo sotto `docs/superpowers/reviews/7/` non dà violazioni; sotto `reviews/8/` sì).
- [ ] **Step 4: Test** `test_audits.py`: `test_open_one_at_a_time`; `test_close_and_last_closed_any_kind`; `test_superseded_not_in_rounds`; `test_suspend_roundtrip`; `test_cap_kind_from_reasons`; `test_numbers_per_kind` (giro avversariale 1, ciclo a lenti 1, avversariale 2).
- [ ] **Step 5: Fallimento, implementazione, verifica** (`python3 -B -m unittest tests.test_db tests.test_phases tests.test_scope tests.test_audits tests.test_git`), `tests/run`.
- [ ] **Step 6: Commit** «tollgate P3c: migrazione 5, giri di audit nel DB, cause dei passaggi L2, reset del piano».

---

