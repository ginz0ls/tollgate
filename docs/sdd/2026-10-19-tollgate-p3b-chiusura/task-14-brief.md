### Task 14: `task start --from-findings` e `--from-gate`

**Files:**
- Create: `bin/tollgate_flow/fixtask.py`
- Modify: `bin/tollgate_analysis/brief.py` (`findings_task_text`, `gate_task_text`), `bin/tollgate_flow/taskcmd.py` (per i task `kind = "fix"` il testo viene da `tasks.task_text`, non dal piano: in `task_start --fix`, `review_prepare` e `task_done`), `bin/tollgate_core/tasks.py` (`add_task(..., task_text=None)`), `bin/tollgate_core/cli.py` (`task start --from-findings C`, `task start --from-gate`, esclusivi con `K`)
- Test: `tests/test_fixtask.py`

**Interfaces:**
- Consumes: `reviews.blocking_open(conn, work, cycle)`, `tasks.add_task(kind="fix", source=…)`, `tasks.assign`, `profiles.task_routing`, `brief.ImplBrief`, `gh.pr_comments`.
- Produces in `brief.py`: `findings_task_text(cycle: int, findings: list[dict], scope: list[str]) -> str` (i rilievi in un recinto; un file fuori scope è indicato come «serve una deroga»); `gate_task_text(sha: str, comment: str) -> str` (commento recintato, marcato come dato).
- Produces in `fixtask.py`: `GATE_MARKER = "<!-- tollgate-verdict"`; `from_findings(state, cwd, cycle: int, *, claude_dir, now=None) -> tuple[Path, str]`; `from_gate(state, cwd, *, claude_dir, now=None) -> tuple[Path, str]`. Stesso riepilogo di `task start` (tipo, `name`, `launch`, revisore). Errore `taskcmd.TaskError`. Decisione 16.

- [ ] **Step 1: Test** `test_fixtask.py`:
  - `test_from_findings_creates_fix_task_without_touching_plan` (ciclo `needs_fix` → task 2 `kind = "fix"`, `source = "cycle:1"`, brief con i rilievi, `plan_sha` e file del piano invariati; criteri 26 e 37);
  - `test_from_findings_twice_refused`;
  - `test_from_findings_ok_cycle_refused`;
  - `test_fix_task_review_and_done` (il task di correzione passa da `review-prepare` e `task done` come un task del piano);
  - `test_fix_task_fix_round` (verdetto `changes` sul task di correzione → `task start <k> --fix` scrive il brief dal testo salvato);
  - `test_from_gate_reads_marked_comment_as_data` (due commenti, l'ultimo con il marcatore e ```` ``` ```` → brief con il recinto più lungo; `source = "gate:<sha>"`);
  - `test_from_gate_without_pr_refused`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: task di correzione dai rilievi e dal gate».

---

