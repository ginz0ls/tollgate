### Task 10: Voci nuove di `act apply`

**Files:**
- Modify: `bin/tollgate_flow/actapply.py`, `bin/tollgate_flow/taskcmd.py` (`MAX_FIX_ROUNDS + extra_fix_rounds`), `bin/tollgate_core/tasks.py` (`add_extra_rounds`), `bin/tollgate_flow/gitw.py` (`merge_base`)
- Test: `tests/test_actapply.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Produces in `tasks.py`: `add_extra_rounds(conn, work, number, n: int) -> int` (tetto 8 giri in tutto: `ValueError` oltre).
- Produces in `gitw.py`: `merge_base(repo, a, b) -> str | None` (la usa anche il Task 11).
- Consumes: `intents.SYNC_CONFLICT_REASON`, `intents.authorize_force`, `phases.set_base` (Task 3).
- Produces in `actapply.APPLIERS` (decisioni 13 e 14): `("approve", "finding")`, `("approve", "rounds")`, `("approve", "unverified-review")`, `("approve", "rebase")`. `_resolve` sul blocco con `reviews.CAP_REASON` aggiunge un ciclo (`phases.add_extra_cycles(…, 1)`).
- Produces: `approve finding` vuole `<id> <gravità|dismiss> <motivo>`; gravità in `blocker|major|moderate|minor`; motivo obbligatorio; id di un rilievo `confirmed` del lavoro.

- [ ] **Step 1: Test** `test_actapply.py`:
  - `test_approve_rounds_one_more_cycle` (quarto ciclo contato → blocco; `approve rounds 1` → blocco chiuso, `extra_review_cycles == 1`, il quinto ciclo si apre; criterio 9);
  - `test_approve_rounds_over_eight_refused`;
  - `test_approve_rounds_on_fix_rounds_cap` (blocco «giri di correzione esauriti sul task 1» → `approve rounds 2` → `task start 1 --fix` ammesso al sesto giro; m12);
  - `test_resolve_on_cycles_cap_grants_one`;
  - `test_approve_finding_dismiss_turns_cycle_ok` (ultimo ciclo `needs_fix` per un solo `major` → `dismiss` → esito `ok`);
  - `test_approve_finding_needs_reason_and_confirmed`;
  - `test_unverified_review_only_after_eight`;
  - `test_approve_rebase_realigns_base_and_authorizes_force` (blocco del `sync` → base = `merge-base`, fase `execution`, un intento `force_push`; criterio 16).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: act apply per finding, rounds, unverified-review e rebase».

---

