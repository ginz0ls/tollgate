### Task 6: Comando `research`

**Files:**
- Create: `bin/tollgate_flow/research_cmd.py`, `tests/test_research_cmd.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando), `bin/tollgate_checks/cli_calls.py` (decisione 12)
- Test: `tests/test_check_cli_calls.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `lookups.for_task`, `lookups.set_note` (Task 2); `research.parse_note`, `check_note`, costanti (Task 3).
- Produces:
  - `tollgate_flow.research_cmd.submit(state, cwd: Path, number: int, text: str, *, now=None) -> SubmitResult` con `SubmitResult(code: int, lines: list[str], path: Path | None)`, codici `OK` 0 (nota valida), `INVALID` 1 (nota salvata ma non valida, `lines` elenca i problemi), `REFUSED` 2 (nessun lavoro per la cartella, fase diversa da `execution`, L0, lavoro con `research = 0`, task inesistente o non `running`);
  - `tollgate_flow.research_cmd.show(state, cwd: Path, number: int) -> SubmitResult` (stampa la nota salvata e l'esito; `REFUSED` se non c'è);
  - CLI `research submit <k>` (testo da stdin) e `research show <k>`;
  - file `.tollgate-run/<N>/research-<k>.md` con la nota così com'è e una riga finale `esito: valida|non valida`;
  - evento `research_note` {task, ok, problems} a ogni consegna.

- [ ] **Step 1: Test** `test_research_cmd.py` (repo e lavoro da `tests/flowkit.py`, letture scritte con `lookups.record`):
  - `test_submit_valid_note` (uscita 0, `tasks.research_ok = 1`, file scritto, evento con `ok: true`);
  - `test_submit_invalid_lists_problems` (fonte non consultata → uscita 1, la riga del problema nomina l'URL, `research_ok = 0`, nota salvata lo stesso);
  - `test_resubmit_replaces` (valida poi non valida → `research_ok = 0`);
  - `test_refused_in_l0`, `test_refused_outside_execution`, `test_refused_legacy_work` (testo «lavoro iniziato prima del passo informati prima»), `test_refused_task_not_running`;
  - `test_lookups_of_previous_round_count` (letture con `agent_id` diverso dello stesso task contano, progetto 3.6);
  - `test_show_prints_note_and_outcome`.
  `test_cli.py::test_research_submit_reads_stdin`. `test_check_cli_calls.py::test_research_denied_to_main_session_in_l1` (input senza `agent_id`, lavoro L1 → `deny` con «la nota la scrive l'implementatore del task») e `test_research_allowed_to_implementer`; `test_research_uncertain_program_denied_to_main_session` (programma come espansione `$p research submit 1`) e `test_unparseable_research_denied_to_main_session` (decisione 12); `test_heredoc_research_passes_bash_rules` (il comando di `research.submit_command` dell'implementatore, con una nota che contiene backtick e una riga `EOF`, non riceve `deny` da nessun modulo, con `hooks/run` vero, e la nota arriva intera alla CLI).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** `research_cmd.py` (lavoro dalla cartella con `sessions.work_for_path`, come `taskcmd`), il sottocomando e la regola di `cli_calls`. Il file della nota si scrive con lo stesso schema atomico di `apply._write_atomic`.
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: comando research per la nota di ricerca».

---

