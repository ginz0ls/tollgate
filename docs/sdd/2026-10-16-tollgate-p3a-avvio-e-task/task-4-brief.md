### Task 4: `start` in ripresa

**Files:**
- Modify: `bin/tollgate_flow/start.py`, `bin/tollgate_flow/gitw.py` (`rebase_in_progress(wt) -> bool`, `is_dirty(wt) -> bool`)
- Test: `tests/test_start.py::ResumeTest`

**Interfaces:**
- Consumes: `phases.find_active`, `phases.bind_session`, `phases.set_phase(..., "execution", "start")`, `subagents.running`, `subagents.interrupt`, `sessions.alive`, `sessions.mark_bound`, `effects.get` / tabella `intents` (`state = 'requested'`).
- Produces: un ramo di `start.start` per il lavoro attivo (12.4). Rifiuti ammessi solo per «repo attivo» e «Python». Rete assente, `gh` non raggiungibile, stati non verdi e checkout principale sporco diventano avvisi.

Comportamento:
- **Worktree assente:**
  - con il ramo locale presente, `worktree_add(new_branch=False)`;
  - senza ramo, `worktree_add(new_branch=True, start_point=work_base_sha)`;
  - aggiorna `work_items.worktree` se il percorso è cambiato, con una funzione nuova `phases.set_worktree(conn, work, path, *, now)`.
- **Rebase in corso:** avviso con «`git -C <wt> rebase --abort`» proposto, senza eseguirlo.
- **Worktree sporco:** avviso e proposta di un commit di lavoro in corso.
- **Subagenti `running` di sessioni non vive:** `interrupt`.
- **Intenti `requested`:** codice 3 con l'elenco; si procede solo con `--confirm`.
- **Un'altra sessione viva tra le `sessions`:** codice 3, si procede con `--confirm` (12.4).
- **Legame:** `bind_session`, `mark_bound`, `active.register`.
- **Fase `review` o `pr_open`:** riga «fase X: per correggere rilancia con `--reopen-execution`» (decisione 19). Con il flag, `set_phase(execution, start)`.

- [ ] **Step 1: Test** (`ResumeTest`):
  - `test_resume_recreates_missing_worktree`: rimosso con `git worktree remove --force` → ricreato sullo stesso ramo, uscita 0;
  - `test_resume_without_branch_starts_from_base`: ramo e worktree assenti → ramo ricreato su `work_base_sha`;
  - `test_resume_dirty_worktree_proposes_commit` (criterio 28);
  - `test_resume_offline_and_dirty_main_are_warnings` (origin rinominato: `fetch` falso → uscita 0 con due avvisi; criterio 28);
  - `test_two_live_sessions_need_confirmation` (sessione B toccata 1 minuto fa, `start` da A → 3; con `--confirm` → 0, ed entrambe in `sessions`);
  - `test_second_session_does_not_interrupt_live_implementer` (implementatore `running` di B viva → resta `running`; criterio 28);
  - `test_dead_session_implementer_interrupted_task_pending`;
  - `test_pending_intent_needs_confirmation`;
  - `test_reopen_execution_from_review`;
  - `test_rebase_in_progress_warns`, con un rebase in conflitto preparato a mano nel worktree.
- [ ] **Steps 2-5**: fallimento, implementazione, verifica (`python3 -B -m unittest tests.test_start`), `tests/run`, commit «tollgate P3a: start in ripresa (12.4)».

---

