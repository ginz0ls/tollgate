### Task 8: `act apply` per `resolve` e `approve level`

**Files:**
- Create: `bin/tollgate_flow/actapply.py`
- Modify: `bin/tollgate_core/phases.py` (`set_level_cap`), `bin/tollgate_core/cli.py` (sottocomando `act apply`)
- Test: `tests/test_phases.py`, `tests/test_actapply.py`

**Interfaces:**
- Produces in `phases.py`: `set_level_cap(conn, work, cap: str, reason: str, cap_paths: list[str], *, now, session=None) -> None` (decisione 14). Solleva `TransitionError` se la fase corrente, o `phase_before_block` per `blocked`, non è nella sequenza di `cap`. Abbassa `level` a `cap` se è più alto (evento `level_change` con `{"from", "to", "cause": "cap"}`) e scrive `level_cap`, `level_cap_reason` e `level_cap_paths` (JSON).
- Produces in `actapply.py`:
  - `APPLIERS: dict[tuple[str, str | None], Callable]`, con chiavi `("resolve", None)` e `("approve", "level")`;
  - `ActApplyError(Exception)`;
  - `apply_act(state, cwd, act_id: str | None, *, now=None) -> str`.
- Comportamento di `apply_act`:
  - Sessione con `cli_session(state, cwd, "act")`. Lavoro con `sessions.work_for_path(cwd)`.
  - Atto: quello indicato, oppure l'ultimo `pending` della sessione con chiave in `APPLIERS`. Deve essere della sessione, del lavoro, non scaduto e con chiave applicabile.
  - `acts.consume(...)` nella stessa sequenza, poi l'applicatore.
  - `resolve <id>`: `close_block` con la nota (`args[1:]` unite); se l'id non è un blocco aperto del lavoro, rifiuto. Quando la fase esce da `blocked`, ogni task `blocked` riceve `unblocked`.
  - `resolve writer`: `interrupt` sugli implementatori `running` del lavoro.
  - `approve level <L> <motivo>`: `cap_paths = level.sensitive_in(<percorsi del diff dalla base, compresi old_path>, sensitive_paths)`, poi `set_level_cap`.
- CLI: `tollgate act apply [<id>]`.

- [ ] **Step 1: Test** (`test_phases.py::LevelCapTest`):
  - `test_cap_lowers_level_and_records_paths`;
  - `test_cap_refused_when_phase_not_in_target_sequence` (L2 in `spec_audit` → L1 rifiutato);
  - `test_cap_in_blocked_uses_phase_before_block`.
- [ ] **Step 2: Test** (`test_actapply.py`, `FlowLab` più `hookkit` per registrare l'atto con `UserPromptExpansion`):
  - `test_resolve_closes_block_and_unblocks_tasks`;
  - `test_resolve_writer_interrupts`;
  - `test_approve_level_cap_holds_until_new_sensitive_path` (dopo il tetto il ricalcolo di `post_edit` non rialza per un file non sensibile, e rialza per `src/auth/x.py`; criterio 22);
  - `test_act_of_other_session_or_expired_refused`;
  - `test_act_consumed_once` (secondo `act apply` sullo stesso id → rifiuto);
  - `test_unknown_act_type_refused` (`approve waiver` → «non si applica con act apply»).
- [ ] **Steps 3-5**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: act apply (resolve, resolve writer, approve level)».

---

