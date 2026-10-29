### Task 8: Brief dell'implementatore e del revisore

**Files:**
- Modify: `bin/tollgate_analysis/brief.py` (`ImplBrief`, `ReviewBrief`, `implementer_brief`, `review_brief`), `bin/tollgate_flow/taskcmd.py`, `bin/tollgate_checks/subagent_start.py`, `agents/task-reviewer.md`
- Test: `tests/test_brief.py`, `tests/test_taskcmd.py`, `tests/test_check_agents.py` (`SubagentStart`), `tests/test_manifest.py`

**Interfaces:**
- Consumes: `lookups.note` (Task 2); costanti di `research` (Task 3); comando del Task 6.
- Produces:
  - campi nuovi con valore predefinito (le dataclass hanno già campi con predefinito): `ImplBrief.research_cmd: str | None = None` (da `research.submit_command`; `None` per i lavori con `research = 0`) e `ImplBrief.research_note_path: str | None = None` (la nota già consegnata, nei giri `--fix`);
  - `ReviewBrief.research: bool = False` (il lavoro ha il passo), `ReviewBrief.research_enforced: bool = False` (l'interruttore della decisione 8), `ReviewBrief.research_note: str | None = None`, `ReviewBrief.research_note_path: str | None = None`, `ReviewBrief.first_diff_file: str | None = None` (il primo file del diff, scritto da `taskcmd.review_prepare`: è il `file` del rilievo quando la nota manca);
  - sezione «Nota di ricerca» del brief dell'implementatore (prima di «Istruzioni»): il formato della decisione 2 con i nomi delle sezioni dalle costanti, il comando con l'heredoc, e nei giri `--fix` «la nota è in <percorso>: integrala e risottomettila solo se questo giro tocca librerie o servizi nuovi»;
  - sezione «Nota di ricerca» del brief del revisore solo con `research` vero: il testo in un recinto e `DATA_NOTE`, o «nessuna nota consegnata»; la gravità da usare secondo la decisione 13 (`major` e `missing` con l'interruttore acceso, `moderate` senza `missing` con l'interruttore spento), `file` il percorso della nota, o il primo file del diff se la nota manca, e `line` 1;
  - riga in più nel promemoria di `SubagentStart` per gli implementatori di un lavoro con `research = 1`: «prima di modificare file consegna la nota di ricerca (vedi il brief)».

- [ ] **Step 1: Test** `test_brief.py`: `test_impl_brief_has_research_section` (comando e sezioni); `test_impl_brief_without_research_for_legacy` (con `research_cmd=None` nessuna sezione); `test_fix_brief_points_to_note`; `test_review_brief_fences_note` (una nota con ```` ``` ```` e «ignora le istruzioni» sta in un recinto più lungo, dopo `DATA_NOTE`); `test_review_brief_missing_note_enforced` (gravità `major`, `missing`, `file` uguale al primo file del diff) e `test_review_brief_missing_note_not_enforced` (gravità `moderate`, nessun `missing`); `test_review_brief_legacy_has_no_section` (`research` falso). `test_taskcmd.py::test_task_start_brief_has_research_cmd` e `test_review_prepare_includes_note`. `test_check_agents.py::test_implementer_reminder_mentions_note`. `test_manifest.py::test_task_reviewer_checks_note` (il corpo nomina la regola `nota di ricerca`, «Nessuna fonte esterna» e il rimando alla gravità indicata dal brief).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa.** In `task-reviewer.md` un punto nella «Parte 1»: se il brief ha la sezione «Nota di ricerca», la nota esiste, le fonti riguardano le librerie e i servizi del diff, il motivo di «Nessuna fonte esterna» è vero; altrimenti un rilievo con `rule` `nota di ricerca`, la gravità e il `file`/`line` che il brief indica (decisione 13). `taskcmd.review_prepare` legge l'interruttore dalla radice del plugin (`db.BIN_PATH`, come gli altri percorsi del programma).
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: nota di ricerca nei brief e nella revisione del task».

---

