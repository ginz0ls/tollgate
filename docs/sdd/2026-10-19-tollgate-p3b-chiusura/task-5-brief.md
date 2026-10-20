### Task 5: Regole `[blocca]`, nomi dei profili, verdetti finali

**Files:**
- Modify: `bin/tollgate_core/config.py` (chiave `blocking_rules`, nomi convalidati), `bin/tollgate_analysis/profiles.py`, `bin/tollgate_analysis/verdicts.py`, `bin/tollgate_checks/task_verdict.py`
- Test: `tests/test_config.py`, `tests/test_profiles.py`, `tests/test_verdicts.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Produces in `config.py`: `PROFILE_DEFAULTS["rules"] = []`, `PROFILE_DEFAULTS["blocking_rules"] = []` (un elemento di `blocking_rules` fuori da `rules` → `ConfigError`); `AGENT_FORMS = {"agent": "implementer", "reviewer": "reviewer", "final_specialist": "final"}`; un nome che non combacia con `^[^:\s]+:<forma>-[a-z0-9-]+$` diventa `""` con l'avviso «profilo <p>: <chiave> «<valore>» non ha la forma <plugin>:<forma>-<area>: uso l'agente generico» (decisione 9).
- Produces in `profiles.py`: `blocking_rules(names, profiles) -> set[str]`; `known_rules(names, profiles) -> set[str]`; `final_specialists(names, profiles) -> list[str]` (valori non vuoti, in ordine di dichiarazione, senza doppioni).
- Consumes: `verdicts.is_blocking` (Task 3).
- Produces in `verdicts.py`:
  - `parse_task_verdict(..., blocking_rules: set[str] = frozenset(), known_rules: set[str] = frozenset())`: la gravità bloccante vale solo se `is_blocking`; con entrambi vuoti ogni `R-…` è bloccante, come in P3a. Con lo standard, un `approved` dichiarato con un rilievo scartato che poteva bloccare → non valido («rilievo bloccante senza file, riga o regola: riscrivilo», riga 108);
  - `FinalVerdict(valid: bool, problems: list[str], outcome: str | None, findings: list[dict], rejected: list[dict])` e `parse_final_verdict(text, *, sha: str, code: str) -> FinalVerdict` (18.5 revisore finale; `outcome` in `ok|needs_fix|needs_you`; ultimo JSON con `outcome`; rilievi senza prova in `rejected`, non scartati in silenzio);
  - `VerifierResults(valid, problems, results: list[dict])` e `parse_verifier_results(text, *, sha, code, ids: set[str]) -> VerifierResults` (`verification` in `confirmed|rejected|unverified`; id fuori da `ids` ignorati e contati nei problemi solo se nessuno è valido).
- Produces: `task_verdict` passa `blocking_rules` e `known_rules` dei profili attivi sul diff del task.

- [ ] **Step 1: Test** `test_config.py::ProfileNamesTest`: `test_bad_reviewer_name_falls_back_with_warning` (`reviewer = "acme:code-review"` → `""` e avviso; m9); `test_good_names_kept`; `test_blocking_rules_type` (stringa al posto di lista → `ConfigError`); `test_blocking_rule_must_be_known` (`blocking_rules = ["R-X-1"]` senza `rules` → `ConfigError`).
- [ ] **Step 2: Test** `test_verdicts.py`: `test_non_blocking_rule_major_is_approved` (standard acceso, `major` su `R-WEB-2` in `rules` ma non in `blocking_rules` → `approved`); `test_blocking_rule_major_is_changes`; `test_plan_step_rule_blocks`; `test_unknown_rule_blocks`; `test_approved_with_dropped_blocker_invalid` (riga 108); `test_final_verdict_matrix` (SHA diverso, codice diverso, `outcome` sconosciuto, JSON assente → non valido; un rilievo senza `line` → in `rejected`); `test_verifier_results` (id sconosciuto ignorato, `verification` sconosciuta → non valido).
- [ ] **Step 3: Test** `test_check_task_verdict.py::BlockingRulesTest::test_profile_rule_not_blocking` (profilo `web` con `rules = ["R-WEB-1", "R-WEB-2"]` e `blocking_rules = ["R-WEB-1"]`, verdetto `changes` con un solo `major` su `R-WEB-2` → registrato `approved`).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: regole [blocca], nomi degli agenti dei profili convalidati, verdetti della revisione finale».

---

