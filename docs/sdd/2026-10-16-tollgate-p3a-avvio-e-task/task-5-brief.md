### Task 5: Analisi pura: testo del task, brief, instradamento, dimensione

**Files:**
- Modify: `bin/tollgate_analysis/plan.py`, `bin/tollgate_analysis/profiles.py`
- Create: `bin/tollgate_analysis/brief.py`, `bin/tollgate_analysis/size.py`
- Modify: `bin/tollgate_checks/subagent_stop.py` (usa `size.task_lines`; `_GENERATED` si sposta in `size.GENERATED`)
- Test: `tests/test_plan.py`, `tests/test_profiles.py`, `tests/test_brief.py`, `tests/test_size.py`

**Interfaces:**
- Produces in `plan.py`:
  - `task_text(text: str, number: int) -> str | None`: il testo da `### Task <number>` all'intestazione `###` o `##` successiva, esclusa. I recinti si rispettano: un `###` dentro un blocco di codice non chiude il task.
  - Correzioni del parser:
    - una riga `- Create: a.py, b.py` o `` - Modify: `a.py`, `b.py` `` porta tutti i file;
    - recinti `~~~` e di 4 o più backtick, chiusi solo dallo stesso marcatore di lunghezza ≥;
    - `**M1.** testo — test: id` riconosciuto;
    - ID di must-have duplicati → problema «M1 duplicato»;
    - numeri di task duplicati → problema.
- Produces in `profiles.py`: `Routing(implementer: str, reviewer: str, skills: list[str], reviewer_skills: list[str], split_candidate: bool)` e `task_routing(files, profiles: dict[str, dict]) -> Routing` (decisione 15). Costanti `DEFAULT_IMPLEMENTER = "tollgate:implementer"` e `DEFAULT_REVIEWER = "tollgate:task-reviewer"`.
- Produces in `size.py`: `GENERATED` (i quattro pattern oggi in `subagent_stop`) e `task_lines(changes, lockfiles) -> int`.
- Produces in `brief.py`:
  - `fence(text) -> str`: un recinto più lungo di ogni sequenza di backtick del testo;
  - `ImplBrief(issue, task, name, agent_type, model_hint, task_text, scope, related_tests, must_haves, skills, absent_skills, verify_cmd, fix_findings, fix_round)`;
  - `implementer_brief(b: ImplBrief) -> str`. Il testo contiene nell'ordine: intestazione con lavoro, task e `name`; il testo del task in un recinto; scope; test correlati (R2); must-have collegati; skill da usare con `(assente)`; per un giro di correzione, i rilievi da correggere in un recinto; istruzioni fisse (TDD, commit, `<verify_cmd>` prima di DONE, `block open test_spec_conflict`, report JSON di 18.5).
  - `ReviewBrief(issue, task, sha, code, base, head, brief_path, diff_path, lines, lines_warn, lines_max, concerns, reviewer_skills, standard: bool)`;
  - `review_brief(b: ReviewBrief) -> str`. Contiene la riga del verdetto con `sha` e `code` alla lettera, l'avviso di dimensione oltre `lines_warn`, i dubbi di DONE_WITH_CONCERNS in un recinto e, con `standard`, lo standard di 8.6.

- [ ] **Step 1: Test** (`test_plan.py::TaskTextTest`):
  - `test_task_text_stops_at_next_task`;
  - `test_task_text_ignores_headings_in_fences`;
  - `test_multiple_files_on_one_line`;
  - `test_tilde_and_long_fences`;
  - `test_bold_must_have`;
  - `test_duplicate_must_have_and_task_ids`;
  - `test_existing_cases_unchanged` (rilanciare la suite `PlanCheckTest` esistente: deve restare verde).
- [ ] **Step 2: Test** (`test_profiles.py::RoutingTest`):
  - profilo `web` (`paths=["web/**"]`, `agent="probe:implementer-frontend"`, `reviewer="probe:reviewer-frontend"`, `skills=["ui-ux-pro-max"]`): task su `web/a.tsx` → quei due agenti e `skills == ["ui-ux-pro-max"]` (criterio 38);
  - task su `web/a.tsx` e `api/b.py`, con `api` che ha `agent="probe:implementer-backend"` → `tollgate:implementer`, `tollgate:task-reviewer`, unione delle skill e `split_candidate`;
  - profilo `cross` `a11y` (`reviewer_skills=["axe"]`) elencato in `web.cross` → `"axe" in reviewer_skills`;
  - quattro skill → tre e `split_candidate`;
  - nessun profilo → generici.
- [ ] **Step 3: Test** (`test_brief.py`):
  - `test_fence_longer_than_content`;
  - `test_implementer_brief_has_name_verify_and_report_fields` (contiene `tg-7-t2`, il comando di verifica, «18.5» e ognuno dei campi `REQUIRED` di `report.py`);
  - `test_absent_skill_marked`;
  - `test_fix_brief_includes_findings_in_fence`;
  - `test_review_brief_has_sha_code_and_size_warning` (righe 250 con warn 200 → l'avviso c'è; righe 50 → non c'è).
- [ ] **Step 4: Test** (`test_size.py`): lockfile e `dist/` esclusi; somma `added + removed`. `tests.test_check_subagent_stop` resta verde.
- [ ] **Steps 5-7**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: analisi del task (testo, brief, instradamento, dimensione), plan.py corretto».

---

