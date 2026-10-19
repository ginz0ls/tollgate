### Task 7: `task review-prepare`, verdetto del revisore, `task done`, prenotazione

**Files:**
- Create: `bin/tollgate_analysis/verdicts.py`, `bin/tollgate_checks/task_verdict.py`
- Modify:
  - `bin/tollgate_flow/taskcmd.py`;
  - `bin/tollgate_checks/_common.py` (`awaiting_review`, `fingerprint_changed` spostata da `subagent_stop`);
  - `bin/tollgate_checks/subagent_stop.py` (salta i revisori in attesa; registra il report del messaggio finale);
  - `bin/tollgate_checks/agents.py` (prenotazione);
  - `bin/tollgate_hooks/apply.py` (`task_reserve`, `task_verdict`);
  - `bin/tollgate_core/cli.py`.
- Test: `tests/test_verdicts.py`, `tests/test_check_task_verdict.py`, `tests/test_taskcmd.py`, `tests/test_check_agents.py`

**Interfaces:**
- Produces in `verdicts.py`:
  - `TaskVerdict(valid: bool, problems: list[str], outcome: str | None, declared: str | None, findings: list[dict], dropped: int)`;
  - `parse_task_verdict(text: str | None, *, task: int, sha: str, code: str, standard: bool) -> TaskVerdict`: cerca l'ultimo oggetto JSON con `outcome`, come `report._candidates`, e applica la decisione 10.
- Produces in `taskcmd.py`:
  - `review_prepare(state, cwd, number, *, now=None) -> Path`. Il task deve essere in `review`. Range: dal genitore del primo SHA di `tasks.commits` all'ultimo. Senza commit, rifiuto. Scrive:
    - `.tollgate-run/<N>/review-<k>.diff`, con `git log --oneline`, `--stat` e `diff -U10` del range;
    - `.tollgate-run/<N>/review-<k>.md`, con `brief.review_brief`, il codice da `secrets.token_hex(4)` e lo SHA uguale all'ultimo commit;
    - `set_review_prep`.

    Il report dell'implementatore viene da `subagents.report` dell'ultimo implementatore del task e passa come dubbi se dice `DONE_WITH_CONCERNS`.
  - `task_done(state, cwd, number, *, now=None) -> str`: rifiuta senza `verdict == approved` e senza `review_sha == tasks.commits[-1]`. Con un commit dopo la revisione rifiuta con «serve una nuova revisione». Altrimenti `task_event(approved)`.
- Produces in `_common.py`:
  - `awaiting_review(ctx, row) -> tuple | None` restituisce `(work, task)` se `row["type"]` è il `reviewer_type` di un task del lavoro in `review` con `review_code` non nullo; il lavoro si trova da `row["work"]`, oppure da `governing_work(ctx, ctx.event.cwd)`;
  - `fingerprint_changed(ctx, row, wt) -> bool`.
- Produces: modulo `task_verdict` (evento `subagent_stop`, ordine 15, componente `None`). Per un revisore in attesa:
  - con `readonly_check` acceso e l'impronta cambiata: `subagent_finish(tampered)` più `needs_you`;
  - con il verdetto valido: `task_verdict(work, number, outcome, findings)` più `subagent_finish(done)`;
  - con il verdetto non valido: veto con i problemi (uscita 2), e dopo 2 veti `subagent_finish(done)` più `needs_you` «verdetto del revisore non valido».

  Il messaggio viene da `last_assistant_message`, o da `subagents.report` (auto mode).
- Produces: in `subagent_stop.decide`:
  - prima del ramo di sola lettura, `if _common.awaiting_review(ctx, row): return []`;
  - per gli implementatori, quando c'è `last_assistant_message`, un `record("subagent_report", ...)` in testa alle decisioni, così `review-prepare` ha i dubbi anche in modalità manuale.
- Produces: in `agents.decide`, quando ammette l'implementatore: con `reserved_at` del task più recente di 120 s → `deny("lancio già in corso per il task k", rule="writer")`; altrimenti `record("task_reserve", work=..., number=...)`. `apply._subagent_start` chiama `tasks.clear_reservation` sul task preso.
- CLI: `tollgate task review-prepare <k>` stampa il percorso del brief del revisore. `tollgate task done <k>`.

- [ ] **Step 1: Test** (`test_verdicts.py`):
  - `test_valid_approved`;
  - `test_minor_only_changes_becomes_approved_with_standard` (criterio 40);
  - `test_minor_only_changes_kept_without_standard`;
  - `test_finding_without_rule_dropped` (criterio 40);
  - `test_spec_compliance_forces_changes`;
  - `test_verdict_validity_matrix`, un sottocaso per: SHA diverso, codice diverso, task diverso, JSON assente, JSON malformato, `outcome` sconosciuto. Tutti danno `valid` falso.
- [ ] **Step 2: Test** (`test_check_task_verdict.py`, `hookkit.Lab` con il task in `review` e la preparazione fatta):
  - `test_approved_recorded_and_row_closed`;
  - `test_invalid_verdict_vetoes_twice_then_needs_you`;
  - `test_tampering_reviewer_verdict_ignored` (file cambiato durante la revisione → `tampered`, `needs_you`, verdetto non registrato);
  - `test_implementer_cannot_deliver_verdict` (stesso JSON da `tollgate:implementer` → nessun `task_verdict`);
  - `test_handback_report_used_in_auto_mode`;
  - `test_reviewer_standard_component_off` (criterio 18).
- [ ] **Step 3: Test** (`test_taskcmd.py::ReviewDoneTest`):
  - `test_review_prepare_writes_diff_and_code`;
  - `test_done_requires_approved_on_last_sha` (senza verdetto → rifiuto, criterio 4; con verdetto `approved` → `done`; commit dopo il verdetto → rifiuto);
  - `test_concerns_reach_review_brief`.
- [ ] **Step 4: Test** (`test_check_agents.py::ReservationTest`): `test_second_launch_in_same_message_denied` (due `PreToolUse Agent` di fila → il secondo 2); `test_reservation_expires_after_120s`.
- [ ] **Steps 5-7**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: review-prepare, verdetto del revisore del task, task done, prenotazione del lancio».

---

