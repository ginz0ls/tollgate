### Task 9: `status --checkpoint`, tetto che ha fermato il lavoro, sola lettura di `status`

**Files:**
- Create: `bin/tollgate_flow/checkpoint.py`
- Modify: `bin/tollgate_core/cli.py` (`status --checkpoint [--note TESTO]`; `status` senza DB non lo crea), `bin/tollgate_core/stats.py` (eventi senza lavoro nei conteggi globali)
- Test: `tests/test_checkpoint.py`, `tests/test_cli.py`, `tests/test_stats.py`

**Interfaces:**
- Produces in `checkpoint.py`:
  - `CAPS`: prefissi dei motivi dei blocchi, `"budget superato"` → `"budget del task"` e `"giri di correzione esauriti"` → `"giri di correzione"`; P3b aggiunge i cicli di revisione;
  - `stopped_by(conn, work) -> list[str]`: per i blocchi aperti che corrispondono a un prefisso, «tetto: <nome> (blocco <id>)»;
  - `next_step(conn, work) -> str`: il primo task non `done` con il suo stato e il comando successivo (`task start k`, `task review-prepare k`, `task done k`); con tutti i task `done`, «`/tollgate:finish`»;
  - `write_checkpoint(state, cwd, *, note: str | None, now=None) -> Path`. Scrive `docs/superpowers/reviews/<N>/checkpoint.md` nel worktree con fase, livello, piano e `plan_sha`, task per stato, `stopped_by`, prossimo passo e note. Le note precedenti si conservano, le ultime 5. Scrittura con tmp più `os.replace`.
- Produces in `cli.py`: `status` stampa anche `stopped_by`, nel JSON (chiave `stopped_by`) e nel testo. Se `state.db_path` non esiste stampa «nessun lavoro attivo» senza creare nulla.
- Produces in `stats.py`: i conteggi globali (`work=None`) comprendono anche gli eventi con `work` nullo (veti, blocchi); `phase_hours` resta per lavoro.

- [ ] **Step 1: Test**:
  - `test_checkpoint.py`:
    - `test_checkpoint_written_and_ignored_by_git` (`git status --porcelain` nel worktree vuoto dopo la scrittura, grazie all'exclude);
    - `test_next_step_sequence`;
    - `test_notes_kept_last_five`;
    - `test_stopped_by_budget_and_rounds` (criterio 39: «`status` dice quale tetto»);
    - `test_session_start_injects_checkpoint` (con `hookkit`: dopo `write_checkpoint`, `SessionStart` contiene «prossimo passo»).
  - `test_cli.py::StatusReadOnlyTest::test_status_without_db_creates_nothing`.
  - `test_stats.py::GlobalTest::test_vetoes_without_work_counted`.
- [ ] **Steps 2-4**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: checkpoint, tetto che ha fermato il lavoro, status in sola lettura».

---

