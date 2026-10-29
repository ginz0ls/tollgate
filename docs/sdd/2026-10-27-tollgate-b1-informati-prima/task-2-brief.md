### Task 2: Stato: migrazione 6, letture, lavori nati prima di B1

**Files:**
- Modify: `bin/tollgate_core/db.py` (`SCHEMA_V6`, `MIGRATIONS`), `bin/tollgate_core/phases.py` (`create_work`), `bin/tollgate_core/scope.py` (`reset_plan`), `bin/tollgate_core/events.py` (`EVENT_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["components"]`), `bin/tollgate_flow/start.py`, `bin/tollgate_flow/adopt.py`, `bin/tollgate_flow/housekeeping.py`
- Create: `bin/tollgate_core/lookups.py`, `tests/test_lookups.py`
- Test: `tests/test_db.py`, `tests/test_phases.py`, `tests/test_scope.py`, `tests/test_start.py` (anche `housekeeping`), `tests/test_adopt.py`

**Interfaces:**
- Produces:
  - `SCHEMA_V6`: tabella `lookups (id INTEGER PRIMARY KEY AUTOINCREMENT, work INTEGER NOT NULL, task INTEGER, agent_id TEXT, session TEXT, kind TEXT NOT NULL CHECK (kind IN ('read','grep','bash_read','fetch','search','docs')), target TEXT NOT NULL, at TEXT NOT NULL)` con indice `lookups_task(work, task)`; `tasks.research_note TEXT`; `tasks.research_ok INTEGER NOT NULL DEFAULT 0`; `work_items.research INTEGER NOT NULL DEFAULT 0`.
  - `lookups.KINDS`; `lookups.record(conn, *, work: int, task: int | None, agent_id: str | None, session: str | None, kind: str, target: str, now) -> None` (`ValueError` per un `kind` fuori elenco o un `target` vuoto); `lookups.for_task(conn, work: int, task: int) -> list[Lookup]` con `Lookup(kind: str, target: str)` (`NamedTuple`), in ordine di registrazione, senza doppioni; `lookups.set_note(conn, work: int, task: int, *, text: str, ok: bool) -> None`; `lookups.note(conn, work: int, task: int) -> tuple[str | None, bool]`; `lookups.prune(conn, *, now, days: int) -> int` (cancella le righe dei lavori chiusi da più di `days` giorni; la chiama `housekeeping.run` con `[retention] events_days`).
  - `scope.reset_plan` mette `lookups.task = NULL` per il lavoro (decisione 14).
  - `phases.create_work(..., research: bool = False)` scrive `work_items.research`; `start` e `adopt` passano `research=True`.
  - `EVENT_TYPES` con `research_note` e `research_reminder`; `DEFAULTS["components"]["research_note"] = True`.

- [ ] **Step 1: Test** `test_lookups.py`: `test_record_and_for_task` (due letture dello stesso task in ordine, una di un altro task esclusa); `test_for_task_without_duplicates` (stessa coppia `kind`, `target` due volte → una); `test_unknown_kind_rejected`; `test_empty_target_rejected`; `test_set_note_roundtrip` (`note` restituisce testo ed esito; una seconda `set_note` con `ok=False` sostituisce). `test_db.py`: `test_migration_6_columns` (colonne e indice dopo `open_db`); `test_migration_keeps_existing_works_outside` (Review Focus 4: un DB alla versione 5 con un lavoro in `execution` e un task `running`, aperto con il codice nuovo, ha `research = 0` per quel lavoro e `research_ok = 0`, e la copia `migrazione-6` esiste); il test esistente `test_db.py` che controlla `latest_version() == 5` passa a 6. `test_scope.py::test_reset_plan_drops_task_lookups` (dopo `reset_plan` `for_task` del vecchio numero è vuota). `test_start.py::test_prune_lookups_of_closed_works` (righe di un lavoro chiuso oltre la soglia cancellate, quelle di un lavoro attivo no). `test_phases.py`: `test_create_work_research_flag` (predefinito `0`, `research=True` → `1`). `test_start.py::test_new_work_has_research_on` e `test_adopt.py::test_adopted_work_has_research_on` (dal programma vero, come i test esistenti dei due file). `test_config.py::test_research_note_component_default_true`.
- [ ] **Step 2: Esegui i test nuovi** e controlla che falliscano per l'assenza di `lookups`, della migrazione e del parametro.
- [ ] **Step 3: Implementa** migrazione, modulo `lookups`, parametro di `create_work`, chiamate di `start` e `adopt`, eventi e componente. `lookups.record` scrive con la sua transazione (vincolo (1) di P1).
- [ ] **Step 4: `tests/run`** verde su python3.11 e python3.
- [ ] **Step 5: Commit** «tollgate B1: migrazione 6, letture registrate, lavori nati prima del passo».

---

