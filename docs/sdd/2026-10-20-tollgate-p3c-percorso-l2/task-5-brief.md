### Task 5: `audit prepare` e `audit decline`

**Files:**
- Create: `bin/tollgate_flow/audit.py`
- Modify: `bin/tollgate_analysis/brief.py`, `bin/tollgate_core/cli.py` (gruppo `audit`), `bin/tollgate_checks/cli_calls.py` (`audit` in `_COORDINATOR_ONLY`), `tests/flowkit.py`
- Test: `tests/test_brief.py`, `tests/test_audit_prepare.py`, `tests/test_check_cli_calls.py`

**Interfaces:**
- Consumes: `audits.*`, `specdoc.slices`, `auditrules.lens_state`, `auditrules.next_viewpoint`, `plan.check_plan`, `profiles.task_routing`, `approvals.locate_spec_approval`, `git.ls_files_at`, `git.blob_sha`, `git.text_at`, `phases.set_spec_path`, `phases.set_phase(..., "approval", "audit_clean")`, `phases.open_block`.
- Produces in `brief.py`: `AuditBrief(issue: int, kind: str, number: int, code: str, doc_path: str, doc_sha: str, spec_path: str, spec_sha: str, reviews_dir: str, issue_file: str | None, severity: dict, viewpoint: str | None, method_path: str | None, tasks: list[dict])` e `audit_brief(b: AuditBrief) -> str`: contiene `code`, `spec_sha` (e per il piano `plan_sha`) alla lettera e la riga JSON della decisione 5 come esempio esatto; vieta di modificare file; chiede ogni rilievo con sezione e gravità; per `spec-adversarial` chiede di controllare «Fette previste», «Tane di coniglio» (una tana senza scelta è `major`) e «Cosa non fare»; per `spec-lens` il punto di vista e il file del metodo; per `plan-adversarial` la tabella dei task.
- Produces in `audit.py`:
  - `OK = 0`, `REFUSED = 1`, `NEEDS_CONFIRM = 3`;
  - `STEPS: dict[str, str]`, i testi fissi delle righe `prossimo passo:` (chiavi `launch`, `fix_spec`, `fix_plan`, `approve_spec`, `approve_plan`, `write_spec`, `write_plan`, `resolve`); la skill e il Task 13 li citano;
  - `PrepareResult(code: int, lines: list[str], launches: list[finalreview.Launch])` (riusa `Launch` di `finalreview`);
  - `AuditError(Exception)`;
  - `prepare(state, cwd, *, confirm: bool, now=None) -> PrepareResult` (decisioni 3, 4, 6, 21; i brief in `.tollgate-run/<N>/<tipo>-<n>.md`);
  - `decline(state, cwd, *, now=None) -> tuple[int, list[str]]` (solo in `spec_audit`, con fette > 1, `spec_audit` acceso e nessun ciclo a lenti; apre il blocco `DECLINE_REASON`);
  - `adversarial_ok(conn, work: sqlite3.Row, cfg, spec_blob: str) -> bool` (decisione 3, usata anche da `l2acts.approve_spec`);
  - `peek(conn, work) -> str` (lo stesso calcolo senza scritture, per `next_step`, decisione 20).
  - I testi di `STEPS` cominciano con una parte fissa senza segnaposto (`<…>`); i segnaposto, se ci sono, vengono dopo. Il Task 13 confronta la parte fissa.
- CLI: `tollgate audit prepare [--confirm]` e `tollgate audit decline`, uscita con il codice; `AuditError` → uscita 1 con il messaggio.
- Produces in `tests/flowkit.py`: `SPEC = "docs/superpowers/specs/2026-10-20-prova.md"`, `spec_text(slices: int = 1, pitch: bool = True) -> str`; `FlowLab.write_spec(slices=1, pitch=True) -> str` (scrive e committa la spec, restituisce il blob); `FlowLab.write_l2_plan(tasks=1) -> str` (scrive il piano, `post_edit`, commit); `FlowLab.report_round(kind: str | None = None, counts: dict | None = None, *, bad_json=False, cut=False) -> subprocess.CompletedProcess` (legge il giro aperto, porta l'orologio del banco a `opened` più un secondo (`lab.now`), poi scrive `SubagentStart` e `SubagentStop` dell'agente del giro con il JSON corretto, attraverso `hookkit.Lab.hook`). **Orologi:** `audit prepare` lanciato dalla CLI usa l'ora reale, mentre gli hook del banco usano l'ora di `hookkit` (dal 9 ottobre 2026): senza questo allineamento nessun agente simulato apparterrebbe al giro. I test non tolgono mai la condizione `started >= opened` per farli passare.

- [ ] **Step 1: Test** `test_brief.py::AuditBriefTest`: `test_brief_has_code_sha_and_json_line`; `test_issue_file_only_when_present`; `test_lens_brief_has_viewpoint_and_method`; `test_plan_brief_lists_split_candidates` (task a cavallo di due profili con agenti diversi → «candidato a essere diviso»).
- [ ] **Step 2: Test** `test_audit_prepare.py` (`FlowLab(issue=7, level="L2", phase="spec_audit")`: senza `issue=` il banco non crea il lavoro):
  - `test_no_spec_refused`;
  - `test_first_round_registers_spec_path_and_launches_adversary` (una riga `agente: tollgate:spec-adversary brief: "…"`, `spec_path` registrato, giro 1 aperto);
  - `test_uncommitted_spec_refused` (worktree diverso da HEAD → «committa»);
  - `test_open_round_same_sha_reprinted_same_code`;
  - `test_open_round_other_sha_superseded`;
  - `test_dirty_round_same_sha_asks_fix` (codice 1, `STEPS["fix_spec"]`);
  - `test_clean_round_one_slice_asks_approve_spec`;
  - `test_three_slices_lens_needs_confirm_then_executor` (codice 3 con il costo; con `--confirm` lancio di `tollgate:spec-auditor` con `executor`);
  - `test_lens_closed_then_confirmation_round_if_spec_changed`;
  - `test_suspended_adversarial_goes_to_lens_or_approve` (dopo «avversariale sospeso» sulla spec attuale: con una fetta «approve spec», con tre il ciclo a lenti; I-2 della revisione del piano);
  - `test_adversary_off_three_slices_reaches_lens`;
  - `test_superseded_first_lens_cycle_does_not_ask_confirm_again`;
  - `test_plan_written_by_bash_is_found` (piano committato senza `post_edit` → `plan_path` registrato e giro del piano);
  - `test_decline_opens_block` (`audit decline` → blocco `DECLINE_REASON`, fase `blocked`; poi `prepare` rifiuta con `STEPS["resolve"]`);
  - `test_components_off` (`spec_adversary = false` e una fetta → subito `approve_spec`; `plan_adversary = false` in `plan` → fase `approval` senza giri);
  - `test_plan_round_then_clean_moves_to_approval` (giro del piano pulito → `plan → approval`, causa `audit_clean`);
  - `test_l1_refused`; `test_models_override_in_launch_line`.
- [ ] **Step 3: Test** `test_check_cli_calls.py::test_audit_is_coordinator_only` (con `agent_id`: `audit prepare` → 2; dalla sessione principale ammesso, nessuna voce di segnale).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: audit prepare e audit decline (giri, lenti, passaggio plan → approval)».

---

