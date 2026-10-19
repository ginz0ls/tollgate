# Task 6 — report

## Implementato
- `bin/tollgate_core/db.py`: migrazione 3 (`tasks.review_sha`, `review_findings` default `'[]'`, `reserved_at`).
- `bin/tollgate_core/tasks.py`: `assign` con `coalesce` su `reviewer_type`; `take_pending(..., number=None)` (azzera anche `reserved_at`); `reserve`, `clear_reservation`, `set_skills_required`, `set_review_prep` (azzera `verdict` e `review_findings`), `set_verdict` (stato invariato, evento `task_change`, `outcome` ∈ `VERDICTS`); l'evento `fix` azzera `review_code` e `review_sha` (C10).
- `bin/tollgate_core/git.py`: `blob_text(repo, sha)`.
- `bin/tollgate_hooks/apply.py`: `_subagent_start` passa il numero del task alla ripresa.
- `bin/tollgate_flow/taskcmd.py` (nuovo): `TaskError`, `task_start`.
- `bin/tollgate_core/cli.py`: `tollgate task start <k> [--fix]` (stampa percorso del brief e riepilogo; `TaskError` → exit 1).

## Scostamenti dal piano
- `bin/tollgate_analysis/plan.py`: `PlanTask.test_files` (campo nuovo, additivo) con i file delle righe `Test:`. Il brief chiede come test correlati «le voci `Test:` del task», e `PlanTask.files` fonde Create/Modify/Test. Test in `test_plan.py`.
- `tests/flowkit.py`: `FlowLab` accetta `level` e `phase` (default invariati) per registrare un piano L1 dalla fase `plan` e per il test L0.
- C10: il verdetto `changes` resta dopo l'evento `fix` (lo storico; `test_fix_rounds_counted_by_cli` esistente lo pretende), quindi il secondo `--fix` si rifiuta perché `review_sha` è vuoto: `--fix` richiede stato `review`, `verdict == changes` e `review_sha` non nullo.
- C2: `tests/test_db.py` usa `str(db.latest_version())`.
- Decisione 20: `git.blob_text` ha solo `(repo, sha)`; la ripresa dal file del worktree (se `hash-object` coincide) è in `taskcmd._plan_text`.
- Il riepilogo è `task K: <agente> name=<nome> [model: inherit] launch|resume`.
- Il comando di verifica nel brief è `'<BIN_PATH>' verify` (percorso citato con `shlex.quote`).

## Test aggiunti
- `test_db.py::MigrationV3Test` (v2 → v3 con dati e copia `*migrazione-3*`; DB nuovo senza copia).
- `test_tasks.py::TaskCmdSupportTest`: `test_assign_keeps_reviewer_type`, `test_take_pending_by_number`, `test_set_verdict_keeps_state`, `test_reserve_and_clear`, più `set_skills_required` e `set_review_prep`/evento `fix`.
- `test_git.py`: `blob_text` (presente, assente, binario).
- `test_check_agents.py::ResumeTaskTest`: `test_resume_takes_its_own_task`, `test_resumed_implementer_keeps_fingerprint` (quest'ultimo è un test di non regressione: già verde sul codice di prima, come atteso dal rinviato di P2).
- `test_taskcmd.py` (17 test): `test_task_start_writes_brief_and_assigns`, `test_task_start_only_from_pending`, `test_profile_agent_chosen`, `test_fix_rounds_counted`, `test_rounds_four_five_new_implementer`, `test_sixth_fix_opens_needs_you`, `test_absent_skill_removed_from_required` (con tetto di 3: brief e `skills_required` coincidono), `test_plan_changed_after_registration_refuses`, `test_l0_refuses`, più: ricorrenza del blob negli oggetti, task senza riga `Must-have:`, fase diversa da execution, task inesistente, cartella fuori dal lavoro, secondo `--fix` senza nuovo verdetto (C10), CLI exit 0 e 1.

## TDD
RED (core, eseguito su un `git archive HEAD` in una cartella di scratch con i soli test nuovi sovrapposti):

    python3.11 -B -m unittest tests.test_db tests.test_tasks tests.test_git tests.test_check_agents
    ERROR: test_reserve_and_clear / test_review_prep_clears_verdict_and_fix_clears_review_ids /
           test_set_skills_required / test_set_verdict_keeps_state / test_take_pending_by_number
           (TaskCmdSupportTest), test_blob_text_binary_is_none, test_blob_text_reads_stored_blob_and_none_for_missing
    FAIL: MigrationV3Test.test_from_v2_adds_task_columns_keeps_rows_and_backup,
          test_assign_keeps_reviewer_type, ResumeTaskTest.test_resume_takes_its_own_task
    Ran 95 tests ... FAILED (failures=3, errors=7)

RED di `test_taskcmd.py`: il modulo `tollgate_flow.taskcmd` non esisteva (ImportError alla collezione).

GREEN:

    python3.11 -B -m unittest tests.test_db tests.test_tasks tests.test_git tests.test_check_agents  -> Ran 95 tests OK
    python3.11 -B -m unittest tests.test_taskcmd  -> Ran 17 tests OK
    tests/run  -> python3.11: Ran 848 tests OK; python3 (3.13.5): Ran 848 tests OK

## Autorevisione
- Brief e carry (C2, C10, tipi del Task 5, una sola fonte per le skill) coperti.
- `taskcmd` importa solo `tollgate_core` e `tollgate_analysis` (strati rispettati).
- Dubbio minore: `task start` scrive il brief prima delle transizioni di stato; se una transizione fallisce resta un brief orfano in `.tollgate-run/` (ignorato da git).
- Limite noto: con più task `launch` dello stesso tipo, i giri 4-5 (nuovo implementatore, nessuna riga `subagents` precedente) associano ancora il task col numero più basso: manca un'informazione per distinguerli prima dell'inizio (la risolvono la prenotazione e il nome, Task 7).

## Fix round 1
- `taskcmd.py`: `set_skills_required`, `task_event` e `assign` in un unico `with db.tx(conn)` (le funzioni si uniscono alla transazione esterna, nessuna annidata). Se `assign` fallisce il task resta `pending` (o `review` con `--fix`) e il comando è ritentabile.
- `plan.py`: tolta la riga `test_files` duplicata.
- Test: `AtomicityTest` (2 test: assign che fallisce da pending e da review con `--fix`, poi ritento riuscito).
- RED: con `db.tx` sostituito da `nullcontext`, `AtomicityTest` -> `FAILED (failures=2)` (es. `('running', 1, 'changes', None)` invece di `('review', 0, 'changes', 'abc')`).
- GREEN: `tests/run` -> python3.11 Ran 850 OK; python3 (3.13.5) Ran 850 OK.
