### Task 3: Migrazione 4 e dati della chiusura

**Files:**
- Modify: `bin/tollgate_core/db.py`, `bin/tollgate_core/phases.py`, `bin/tollgate_core/acts.py`, `bin/tollgate_core/dod.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/stats.py`, `bin/tollgate_hooks/context.py` (`approved_waivers` delega a `acts`)
- Create: `bin/tollgate_core/reviews.py`, `bin/tollgate_core/intents.py`
- Modify: `bin/tollgate_analysis/verdicts.py` (`is_blocking`), `bin/tollgate_core/git.py` (`patch_id`)
- Modify: `tests/flowkit.py`
- Test: `tests/test_db.py`, `tests/test_reviews.py`, `tests/test_intents.py`, `tests/test_phases.py`, `tests/test_dod.py`, `tests/test_acts.py`, `tests/test_stats.py`, `tests/test_verdicts.py`, `tests/test_git.py`

**Interfaces:**
- Produces in `db.py`: `SCHEMA_V4` (decisione 1), `MIGRATIONS` fino a 4.
- Produces in `events.py`: tipi `finish_check`, `base_realigned` (decisione 25).
- Produces in `phases.py`:
  - `create_work(..., phase: str | None = None, cause: str = "start")`: `phase` deve stare in `SEQUENCES[level]` ed essere diversa da `closed`, altrimenti `ValueError`;
  - `set_base(conn, work, sha, *, cause: str, now, session=None) -> None` (evento `base_realigned` {from, to, cause});
  - `set_pr(conn, work, number: int | None, url: str | None, *, now) -> None`;
  - `set_finish(conn, work, sha: str | None, report: dict | None, *, now) -> None`;
  - `add_extra_cycles(conn, work, n: int, *, now) -> int` (restituisce il nuovo totale);
  - `set_review_unverified(conn, work, *, now) -> None`.
- Produces in `acts.py`: `approved_waivers(conn, work: int) -> set[str]` (stessa query di `Ctx.approved_waivers`, che delega); `has_approval(conn, work: int, object_: str) -> bool` (un atto `approve` di quell'oggetto del lavoro in qualunque stato; serve a `unverified-tests`).
- Produces in `intents.py` (azioni `pr`, `sync`, `force_push`; stati `requested`, `executed`, `authorized`, `used`):
  - `request(conn, *, work, action, key, data: dict, now) -> int` (idempotente sulla chiave: una riga esistente torna `requested` e aggiorna `data`);
  - `complete(conn, key, *, outcome: str, now) -> None` (`executed`);
  - `authorize_force(conn, work, *, reason: str, now) -> str` (chiave `force:<work>:<n>`, stato `authorized`);
  - `take_force(conn, work, *, now) -> str | None` (consuma il più recente `authorized`: `used`; `None` se non ce n'è);
  - `pending(conn, work, action: str) -> list[sqlite3.Row]`.
- Produces in `reviews.py` (tabelle `review_cycles`, `findings`; ogni funzione apre la sua transazione, eventi `review_cycle` e `finding` di 18.4):
  - `SEVERITY_ORDER = ("blocker", "major", "moderate", "minor")`, `CAP_COUNTED = 4`, `MAX_CYCLES = 8`, `CAP_REASON = "cicli di revisione esauriti"`;
  - `latest(conn, work) -> sqlite3.Row | None`; `count(conn, work) -> int`; `counted(conn, work) -> int`;
  - `open_cycle(conn, work, *, sha, patch_id, code, reviewers: list[str], now) -> int` (numero del ciclo, stadio `review`);
  - `add_report(conn, work, cycle, *, source: str, outcome: str, findings: list[dict], rejected: list[dict], blocking_rules: set[str], known_rules: set[str], now) -> str`: identificativi `f-<ciclo>-<n>` in ordine di arrivo; `rejected` registrati con `verification = 'rejected'` e motivo «senza prova (8.6)»; `rule` e `blocking` (con `verdicts.is_blocking`) per la decisione 8; segna `reported[source]`; restituisce lo stadio dopo il riporto (`verify` quando tutti i `reviewers` hanno riportato);
  - `to_verify(conn, work, cycle, *, max_findings: int, now) -> list[sqlite3.Row]`: rilievi con `verification` nullo in ordine di gravità; oltre `max_findings` diventano `unverified` («oltre max_findings»);
  - `apply_verification(conn, work, cycle, results: list[dict], *, now) -> int` (rilievi ancora senza esito);
  - `effective_severity(row) -> str` (gravità dopo `downgraded:<g>`);
  - `blocking_open(conn, work, cycle=None) -> list[sqlite3.Row]` (confermati, `blocking = 1`, gravità effettiva `blocker`/`major`, non `dismissed`);
  - `close_cycle(conn, state, work, cycle, *, now, session=None) -> str`: esito e passaggi della decisione 6 (`set_phase`, `open_block` fuori transazione); restituisce `ok`, `needs_fix` o `needs_you`;
  - `set_decision(conn, work, finding_id, decision: str, *, now, session=None) -> None` (`downgraded:<g>` o `dismissed`, solo su un rilievo `confirmed`).
- Produces in `dod.py`: `receipt_verdict(..., allow_unverified: bool = False)`; `compute_dod(..., allow_unverified: bool = False, findings_cycle: int | None = None, specialists: list[str] | None = None, skip: tuple[str, ...] = ())`: con `findings_cycle` la voce `findings` guarda solo quel ciclo (decisione 15; con `None` tutti i cicli, come P1); `specialists` (L2) è l'elenco atteso e `_specialists` controlla i riporti di quel ciclo; le chiavi in `skip` valgono `None` con dettaglio «dopo la revisione» e `dod_passes` le ignora solo se il chiamante le filtra.
- Produces in `tollgate_analysis/verdicts.py`: `is_blocking(finding: dict, blocking_rules: set[str], known_rules: set[str]) -> bool` (decisione 8); la usano `reviews.add_report` (qui) e il Task 5.
- Produces in `git.py`: `patch_id(repo, base: str, head: str) -> str | None` (`git diff <base> <head> | git patch-id --stable`, `None` con diff vuoto); la usano i Task 7, 9 e 11.
- Produces in `intents.py`: `SYNC_CONFLICT_REASON = "sync: conflitto nel rebase"`, prefisso del motivo del blocco aperto da `sync` (Task 11) e riconosciuto da `approve rebase` (Task 10).
- Produces in `stats.py`: `off_periods(conn, start: datetime, end: datetime) -> list[dict]` (`{"from", "to"}`, `to` nullo se `OFF` è ancora attivo).
- Produces in `tests/flowkit.py`: `FlowLab.register_plan(tasks: int = 1) -> None` (piano L1 di `tests/test_taskcmd.PLAN` registrato come farebbe l'hook), `FlowLab.commit(path, text, msg) -> str` (commit nel worktree con l'evento `commit`), `FlowLab.close_tasks() -> None` (ogni task `done` con verdetto `approved`), `JUNIT_TOML` e il file `tools/junit_fake.py` (scrive `reports/junit.xml` con i test di `tests/ids.txt`: righe `id ok` o `id fail`) per i test dei must-have.

- [ ] **Step 1: Test** `test_db.py::MigrationV4Test` (DB v3 con righe → colonne nuove, dati intatti, copia `*migrazione-4*`; DB nuovo → nessuna copia; `test_latest_version_is_4`).
- [ ] **Step 2: Test** `test_phases.py::CreateWorkPhaseTest` (`phase="execution", cause="adopt"` in L2 → fase `execution`, evento `phase_change` con causa `adopt`; `phase="closed"` → `ValueError`; `phase="spec_audit"` in L1 → `ValueError`) e `SetBaseTest::test_set_base_records_event`.
- [ ] **Step 3: Test** `test_intents.py`: `test_request_is_idempotent`, `test_force_taken_once` (`authorize_force` poi due `take_force` → chiave, poi `None`), `test_pending_lists_requested`.
- [ ] **Step 4: Test** `test_reviews.py`:
  - `test_open_and_report_moves_to_verify` (due revisori attesi: dopo il primo stadio `review`, dopo il secondo `verify`; id `f-1-1`, `f-1-2`);
  - `test_rejected_without_proof` (rilievo senza `rule` → `rejected`, motivo con «senza prova»; criterio 40);
  - `test_beyond_max_findings_unverified` (17 rilievi, `max_findings=15` → 15 da verificare, 2 `unverified`, prima i `blocker`);
  - `test_close_needs_fix_goes_execution` (un `major` confermato → `needs_fix`, fase `execution`, `counted == 1`; criterio 26);
  - `test_cycle_without_confirmed_not_counted` (solo `rejected` → `ok`, `counted == 0`; criterio 9);
  - `test_fourth_counted_cycle_opens_needs_you` (quattro cicli con un `major` confermato → al quarto blocco `needs_you` con `CAP_REASON`; criterio 9);
  - `test_reviewer_needs_you_opens_block`;
  - `test_non_blocking_rule_is_note` (rilievo `major` con `rule` `R-WEB-2` in `known_rules` ma fuori da `blocking_rules` → confermato ma `ok`);
  - `test_is_blocking` (passo del piano → sì; `R-` in `blocking_rules` → sì; nota e non bloccante → no; sconosciuta → sì);
  - `test_downgrade_and_dismiss` (`set_decision` su un `rejected` → `ValueError`; `downgraded:minor` → `blocking_open` vuoto).
- [ ] **Step 5: Test** `test_dod.py`: `test_downgraded_to_major_still_blocks` (rinviato P1), `test_dismissed_passes`, `test_findings_only_latest_cycle` (ciclo 1 con un `major` confermato, ciclo 2 `ok` → con `findings_cycle=2` la voce è vera), `test_skip_items`, `test_unverified_receipt_counts_with_allow`, `test_specialists_item`. `test_acts.py::test_approved_waivers_any_state`. `test_git.py::PatchIdTest` (`None` con diff vuoto; stesso id dopo un rebase senza conflitti su una base avanzata; id diverso con un contenuto diverso). `test_stats.py::test_off_periods_overlap`.
- [ ] **Step 6: Fallimento, implementazione, verifica** (`python3 -B -m unittest tests.test_db tests.test_phases tests.test_intents tests.test_reviews tests.test_dod tests.test_acts tests.test_stats`), `tests/run`.
- [ ] **Step 7: Commit** «tollgate P3b: migrazione 4, cicli di revisione e rilievi, intenti, DoD dei rilievi».

---

