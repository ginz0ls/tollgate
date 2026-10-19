### Task 6: `task start` e i giri di correzione

**Files:**
- Modify: `bin/tollgate_core/db.py` (migrazione 3, decisione 9), `bin/tollgate_core/tasks.py`, `bin/tollgate_core/git.py` (`blob_text`)
- Modify: `bin/tollgate_hooks/apply.py` (`_subagent_start` passa il numero alla ripresa)
- Create: `bin/tollgate_flow/taskcmd.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `task`)
- Test: `tests/test_db.py`, `tests/test_tasks.py`, `tests/test_taskcmd.py`, `tests/test_check_agents.py`

**Interfaces:**
- Produces in `tasks.py`:
  - `assign(..., reviewer_type=None, ...)`: un `reviewer_type` `None` non sovrascrive il valore esistente (`coalesce`);
  - `take_pending(conn, work, *, agent_type, resume, number=None) -> int | None`: con `number` cerca solo quel task;
  - `reserve(conn, work, number, *, now) -> None` e `clear_reservation(conn, work, number)`;
  - `set_skills_required(conn, work, number, skills: list[str]) -> None`;
  - `set_review_prep(conn, work, number, *, sha, code) -> None`;
  - `set_verdict(conn, work, number, *, outcome: str, findings: list[dict], now, session=None) -> None`: `outcome` ∈ (`approved`, `changes`), stato invariato, evento `task_change`.
- Produces in `git.py`: `blob_text(repo, sha) -> str | None` (decisione 20).
- Produces in `taskcmd.py`:
  - `TaskError(Exception)`;
  - `task_start(state, cwd, number: int, *, fix: bool, claude_dir: Path, now=None) -> tuple[Path, str]`: restituisce il percorso del brief e un riepilogo di una riga, con il tipo di agente, il `name`, l'eventuale `model: inherit` e se si lancia o si riprende.
- Comportamento di `task_start`:
  - Lavoro: `sessions.work_for_path(cwd)`. Fase `execution`, livello L1 o L2: in L0 rifiuto «in L0 lavora la sessione principale».
  - Senza `--fix` il task deve essere `pending`. Con `--fix`, `review` con verdetto `changes`; al quinto giro rifiuto e `needs_you` (decisione 18).
  - Piano a `plan_sha` (decisione 20), poi `plan.task_text`, i file del task da `check_plan` e il `Routing`.
  - Skill assenti tolte con `set_skills_required` (decisione 16).
  - Brief scritto in `.tollgate-run/<N>/task-<k>.md`, oppure `task-<k>-fix-<giro>.md` per `--fix`.
  - `tasks.task_event(start)` per `pending`, oppure `fix` per `--fix`.
  - `tasks.assign(implementer=<nome>, agent_type=<routing>, pending=launch|resume, reviewer_type=<routing>)`.
  - Test correlati: le voci `Test:` del task e i test dei must-have collegati (riga `Must-have:`, altrimenti tutti).
- CLI: `tollgate task start <k> [--fix]`. Stampa il percorso del brief e il riepilogo, esce con 0. `TaskError` esce con 1.

- [ ] **Step 1: Test** (`test_db.py::MigrationV3Test`):
  - DB v2 con righe in `tasks` → dopo `open_db` le colonne nuove esistono, i dati restano, la copia `*migrazione-3*` c'è;
  - DB nuovo → nessuna copia.
- [ ] **Step 2: Test** (`test_tasks.py`):
  - `test_assign_keeps_reviewer_type`;
  - `test_take_pending_by_number` (due task `resume` dello stesso tipo → `number=2` prende il 2);
  - `test_set_verdict_keeps_state`;
  - `test_reserve_and_clear`.
- [ ] **Step 3: Test** (`test_taskcmd.py`, con `FlowLab` dopo `start` e un piano L1 registrato tramite il hook `post_edit`, come in `test_check_post_edit`):
  - `test_task_start_writes_brief_and_assigns`: brief con `tg-7-t1`; `tasks` con `state running`, `pending launch`, `implementer tg-7-t1`, `agent_type tollgate:implementer`;
  - `test_task_start_only_from_pending`;
  - `test_profile_agent_chosen` (profilo `web`; criterio 38);
  - `test_fix_rounds_counted` (tre volte verdetto `changes` e `--fix` → `fix_rounds == 3` e `pending resume` con lo stesso nome; criterio 4);
  - `test_rounds_four_five_new_implementer` (giro 4 → `tg-7-t1-r4`, `pending launch`, riepilogo con `model: inherit`);
  - `test_sixth_fix_opens_needs_you`;
  - `test_absent_skill_removed_from_required`;
  - `test_plan_changed_after_registration_refuses`;
  - `test_l0_refuses`.
- [ ] **Step 4: Test** (`test_check_agents.py::ResumeTaskTest`):
  - `test_resume_takes_its_own_task`: due task in `resume` dello stesso tipo; `SubagentStart` di ripresa per l'agente del task 2 → resta associato al 2;
  - `test_resumed_implementer_keeps_fingerprint`: il rinviato del Task 19 di P2.
- [ ] **Steps 5-7**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: task start e giri di correzione; migrazione 3».

---

