### Task 7: Avviso e rifiuto alla prima modifica

**Files:**
- Create: `bin/tollgate_checks/research_gate.py`, `tests/test_check_research_gate.py`
- Modify: `tests/hookkit.py` (`Lab(..., plugin_root=ROOT)`: parametro nuovo, predefinito invariato)

**Interfaces:**
- Consumes: `research.enforced`, `RULES_BASE`, costanti di sezione (Task 3); `tasks.research_ok`, `work_items.research` (Task 2); `ctx.plugin_root`.
- Produces: modulo con `CHECK = {"api": 1, "events": ["pre_edit", "pre_bash"], "component": "research_note", "order": 25}` e `decide(event, ctx)`:
  - nessuna decisione se il lavoro che governa il bersaglio non c'è, ha `research = 0`, non è in `execution`, o il bersaglio è escluso (decisione 11, le stesse esclusioni per L0, L1 e L2);
  - L0, sessione principale: alla prima modifica del lavoro `inject` dell'avviso più `record("event", type="research_reminder", data={"task": None}, work=…)`; nessuna decisione se un `research_reminder` del lavoro esiste già;
  - L1 e L2, implementatore del task (`subagents.task`): nessuna decisione con `research_ok = 1`; altrimenti, con `enforced(<radice del plugin>/RULES_BASE)` vero, `deny` con il testo del rifiuto; con l'interruttore spento `inject` dell'avviso e `research_reminder` {task}, una volta per task (contando solo gli eventi successivi all'ultimo `plan_reset` del lavoro, decisione 14);
  - `pre_bash`: solo per un implementatore e solo se `bash.write_targets` ha un bersaglio nel worktree non escluso.
  - Testo del rifiuto: comincia con «nota di ricerca mancante o non valida per il task <k>», contiene il comando di `research.submit_command(<program_command>, k)` e il rimando ai problemi della consegna precedente (letti da `research_note` più recente, se c'è). Testo dell'avviso: comincia con «tollgate: informati prima di modificare».

- [ ] **Step 1: Test** `test_check_research_gate.py` (con `tests/hookkit.py`; l'interruttore si prova con il parametro nuovo `Lab(plugin_root=…)` puntato a una copia temporanea della radice del plugin (`bin/` compreso, perché `ctx.plugin_bin` e il riconoscimento del programma in `cli_calls` ed `effects` dipendono da lì) che contiene una `skills/rules-base/SKILL.md` con o senza `approved`):
  - `test_l1_without_note_denied_when_enforced` (progetto 7: «nota mancante: L1 nega»);
  - `test_l1_without_note_warned_when_not_enforced` (avviso, nessun `deny`, una volta per task: la seconda modifica non riceve l'avviso);
  - `test_l0_warns_once` (progetto 7: «nota mancante: L0 avvisa»; la seconda modifica nessuna decisione);
  - `test_valid_note_passes` (progetto 7: «nota valida: la modifica passa»);
  - `test_invalid_note_denied_with_problems` (progetto 7: «fonte dichiarata ma non letta» e «nessuna fonte esterna senza motivo» → il rifiuto riporta i problemi della consegna);
  - `test_docs_and_run_files_exempt` (`docs/superpowers/plans/x.md`, `.tollgate-run/1/x`, `.superpowers/x`, `reports/junit.xml` → nessuna decisione, in L0 e in L1);
  - `test_reminder_again_after_plan_reset` (avviso al task 1, `reopen plan` e nuovo task 1 → nuovo avviso);
  - `test_legacy_work_never_reminded` (Review Focus 4);
  - `test_l0_grown_to_l1_blocks` (Review Focus 4: lavoro L0 avvisato, `set_level` a L1 e piano registrato con un task `running`, interruttore acceso → `deny`);
  - `test_round4_new_implementer_keeps_valid_note` (Review Focus 5);
  - `test_resubmitted_invalid_note_blocks_again` (Review Focus 5);
  - `test_bash_write_by_implementer_denied` (`sed -i` su `src/app.py` senza nota, interruttore acceso → `deny`); `test_bash_read_not_denied` (`cat src/app.py` → nessuna decisione);
  - `test_component_off` (`[components] research_note = false` → nessuna decisione);
  - `test_scope_denial_wins` (file fuori scope: il primo `deny` resta quello di `writes`, ordine 20 prima di 25).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** il modulo. Il testo di `enforced` si legge da `ctx.plugin_root / research.RULES_BASE` (assente → spento).
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: avviso e rifiuto alla prima modifica senza nota».

---

