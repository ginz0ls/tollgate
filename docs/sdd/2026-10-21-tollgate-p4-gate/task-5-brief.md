### Task 5: Calcolo: livello, L2, issue, DoD dichiarata, componenti, file di tollgate

**Files:**
- Modify: `bin/tollgate_gate/evaluate.py`
- Test: `tests/test_gate_evaluate.py`

**Interfaces:**
- Consumes: `model`, `attention` (Task 4); `approvals.check_l2_detail`, `prref` (Task 3); `level.diff_level`, `level.labels_level`, `profiles.min_level`, `profiles.active_profiles`; `workflows.problems`.
- Produces in `evaluate.py`: le famiglie `level`, `l2`, `issue`, `declared`, `guard_local`, le voci `components_off`, `audit_*`, `off_periods`, `sentinel_open`, `not_tg_branch`, `tollgate_config`, `lockfile_without_manifest`, `task_over_warn`, `skills_absent`; `TOLLGATE_FILE_GLOBS` e `tollgate_files_changed(repo, base_ref, head_ref) -> list[str]` (riusata da `gate guard` nel Task 8).

- [ ] **Step 1: Test** `LevelTest` (criterio 22): `test_declared_below_minimum_without_cap_is_red` (`level: "L1"`, percorso sensibile → rosso); `test_with_cap_is_attention` (`level_cap` dichiarato → `level_cap` «da leggere», nessun rosso); `test_labels_and_profile_min_level` (etichetta `security` → minimo L2; `min_level = "L2"` di un profilo attivo).
- [ ] **Step 2: Test** `L2Test`: `test_missing_report_is_red` (criterio 10: «report L2 mancante»); `test_stale_approval_is_attention_with_diff`; `test_spec_audit_off_three_slices_attention_not_red` (criterio 35: `spec_audit = false` sul predefinito, blocco con `lens: "off"`, nessun `spec-lens-*.md` → nessun rosso, `components_off` e `audit_off`); `test_suspended_is_attention` (`adversarial: "suspended"` → `audit_suspended`); `test_later_slice_reports_in_other_folder` (`spec_reviews_dir` dell'issue 3); `test_default_components_passed_to_check_l2` (rilievo I-9 dentro `evaluate`: `spec_adversary = true` sul predefinito e intestazione `adversarial: off` → rosso).
- [ ] **Step 3: Test** `IssueTest` (criterio 33, decisione 8): `test_tg_branch_with_other_closed_issue_is_red_and_no_waivers` (`tg/7-x` con «Closes #3», issue 3 chiusa, deroghe in `waivers/3.toml` e `waivers/7.toml` → rosso e nessuna deroga applicata); `test_block_issue_mismatch`; `test_manual_pr_without_closes` (`fix/x` senza `Closes` → `no_issue`, `not_tg_branch`, nessun rosso dall'issue); `test_config_branch` (`tollgate-config/0.2.0` → nessuno scope né test-guard, `tollgate_config` «da leggere», elenco delle chiavi di `tollgate.toml` cambiate e `FINGERPRINT` nella voce).
- [ ] **Step 4: Test** `DeclaredTest` (decisione 11, criterio 41): `test_blocking_finding_last_cycle_red_even_unverified`; `test_old_cycle_finding_ignored`; `test_blocking_missing_is_blocking`; `test_dismissed_is_attention`; `test_declared_dod_false_is_red_unless_component_off`; `test_recomputed_items_override_declared` (`dod.items.receipt = false` con i comandi verdi → nessun rosso); `test_block_missing_on_tg_is_red`; `test_tasks_over_and_skills_absent_info` (criterio 39); `test_existing_workflow_rules_info` (decisione 15: un workflow non cambiato con `statuses: write` sul predefinito → voce informativa).
- [ ] **Step 5: Test** `LocalTest`: `test_local_skips_issue_declared_base` (`where="local"`: nessuna voce delle tre famiglie); `test_guard_local_tollgate_file_changed` (`tollgate.toml` cambiato nel diff → rosso `guard_local` solo in locale; su GitHub nessuna voce, lo fa `guard`).
- [ ] **Step 6: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: calcolo del gate (livello, L2, issue, DoD dichiarata, componenti)».

---

