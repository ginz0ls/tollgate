### Task 7: `review prepare`

**Files:**
- Create: `bin/tollgate_flow/finalreview.py`
- Modify: `bin/tollgate_analysis/brief.py`, `bin/tollgate_core/cli.py` (sottocomando `review prepare`), `bin/tollgate_flow/taskcmd.py` (modello da `[review] models` nel riepilogo, decisione 21)
- Test: `tests/test_brief.py`, `tests/test_finalreview.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Consumes: `reviews.*`, `git.patch_id` (Task 3), `profiles.final_specialists`, `profiles.active_profiles`, `git.changes`, `brief.fence`.
- Produces in `brief.py`:
  - `FinalBrief(issue, cycle, sha, code, base, head, diff_path, plan_path, plan_sha, must_haves, scope, checklists: list[str], severity: dict, issue_file, role: str)` e `final_review_brief(b) -> str`: contiene `sha` e `code` alla lettera, standard del revisore e disaccordo istruito (8.6: cercare difetti; ogni rilievo con `file`, `line` e `rule` `R-…` o passo del piano), asserzioni indebolite e casi speciali (R3), la definizione delle gravità di `[severity]`, il JSON di 18.5 del revisore finale e il divieto di modificare file e di eseguire test che scrivono file;
  - `VerifierBrief(issue, cycle, sha, code, diff_path, findings: list[dict])` e `verifier_brief(b) -> str`: i rilievi in un recinto, il JSON di 18.5 del verificatore, «conferma o scarta ogni rilievo, senza discutere con il revisore; un rilievo senza prova si scarta».
- Produces in `finalreview.py`:
  - `Launch(agent_type: str, brief: Path, model: str | None)`;
  - `PrepareResult(lines: list[str], launches: list[Launch], stage: str)`;
  - `ReviewError(Exception)`;
  - `prepare(state, cwd, *, now=None) -> PrepareResult` (decisione 5).
- Comportamento di `prepare`:
  - fase `review`, `HEAD == finish_sha` (altrimenti «rilancia /tollgate:finish»); L0 → «in L0 non c'è revisione finale»; componente `final_review` spento → «revisione finale spenta», nessun lancio;
  - `review_unverified` → nessun lancio («revisione non verificata»);
  - ultimo ciclo aperto su HEAD: stadio `review` → i lanci dei revisori non ancora riportati, stesso codice; stadio `verify` → `to_verify` e il lancio del verificatore, oppure `close_cycle` se non resta nulla;
  - ultimo ciclo chiuso `ok` su HEAD o con lo stesso `patch-id` (`git.patch_id`) → «revisione già superata (ciclo n): prossimo passo: finish open-pr»;
  - cicli già fatti `>= MAX_CYCLES` → rifiuto con «/tollgate:approve unverified-review»;
  - altrimenti `open_cycle` e i brief in `.tollgate-run/<N>/final-<ciclo>.md`, `final-<ciclo>-<area>.md` per ogni specialista (solo L2), diff in `final-<ciclo>.diff`, verificatore in `verify-<ciclo>.md`;
  - una riga `agente: <tipo> brief: "<percorso>"` per lancio (percorso tra virgolette: può contenere spazi), con ` model: <m>` da `[review] models`; ultima riga `prossimo passo: …`.
- CLI: `tollgate review prepare` stampa `lines`; `ReviewError` → uscita 1.

- [ ] **Step 1: Test** `test_brief.py`: `test_final_brief_has_sha_code_rules_and_format`; `test_verifier_brief_fences_findings` (testo del rilievo con ```` ``` ```` → recinto più lungo).
- [ ] **Step 2: Test** `test_finalreview.py`:
  - `test_new_cycle_l1_one_reviewer` (un lancio `tollgate:final-reviewer`, ciclo 1 `review`);
  - `test_l2_adds_final_specialists` (profilo `security` con `final_specialist = "probe:final-security"` attivo sul diff → due lanci; criterio 38);
  - `test_resume_open_cycle_keeps_code` (criterio 28);
  - `test_verify_stage_launches_verifier`;
  - `test_same_patch_id_after_rebase_no_new_cycle` (criterio 16);
  - `test_ninth_cycle_refused`;
  - `test_head_differs_from_finish_sha_refused`;
  - `test_models_override_in_launch_line`.
- [ ] **Step 3: Test** `test_taskcmd.py::test_models_override_in_summary` (`models = {"tollgate:implementer" = "sonnet"}` → `model: sonnet` nel riepilogo; giro 4 resta `inherit`).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: review prepare (cicli, specialisti in L2, verificatore), modelli per agente».

---

