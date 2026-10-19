### Task 2: Segnale della sessione, strati, banco di prova del flusso

**Files:**
- Modify: `bin/tollgate_core/sessions.py`
- Create: `bin/tollgate_checks/cli_calls.py`
- Modify: `bin/tollgate_hooks/apply.py` (operazione `cli_call`)
- Modify: `bin/tollgate_checks/acts.py` (riga «programma» per ogni `/tollgate:*`)
- Create: `bin/tollgate_flow/__init__.py`
- Create: `tests/fakegh.py`, `tests/flowkit.py`
- Test: `tests/test_sessions.py`, `tests/test_check_cli_calls.py`, `tests/test_check_acts.py`, `tests/test_layers.py`

**Interfaces:**
- Consumes: `bash.parse`, `bash.uses_tollgate_bin(cmd, plugin_bin)`, `bash.effective_dir`, `Ctx.plugin_bin`.
- Produces:
  - `sessions.CLI_DIR = "cli"`;
  - `sessions.CLI_WINDOW_S = 120`;
  - `sessions.note_cli_call(state, session: str, cwd: str, argv: list[str], *, now) -> None`: scrittura atomica (tmp più `os.replace`) di `<stato>/cli/<session>.json`. Ignora le sessioni che non passano `_SAFE`;
  - `sessions.cli_session(state, cwd, subcommand: str, *, now) -> str`, che solleva `sessions.CliSessionError` con il messaggio di decisione 2;
  - `sessions.CliSessionError(Exception)`.
- Produces: modulo `cli_calls` (evento `pre_bash`, ordine 5). Per ogni `Cmd` che usa il programma (`uses_tollgate_bin` o `argv[0]` con basename `tollgate`):
  - con `agent_id` e sottocomando `start`, `task`, `act`, o `status` con `--checkpoint`: `deny(..., rule="coordinator_only")` (decisione 22);
  - altrimenti, senza `agent_id`: `record("cli_call", cwd=<effective_dir>, argv=<argv[1:]>)`.
- Produces: `apply` registra `cli_call`, che chiama `sessions.note_cli_call` con `ctx.event.session`. `apply.OPS` passa a 23 voci.
- Produces: in `acts.py`, per ogni `command_name` che comincia con `tollgate:`, compresi quelli che non sono atti (`start`, `execute`, `status`, `setup`, `finish`, `init`), un `inject` con la riga `tollgate: programma <ctx.plugin_bin>`. Per gli atti la riga si aggiunge a «atto ricevuto».
- Produces: `tests/fakegh.py`, un eseguibile Python che legge `$TOLLGATE_FAKEGH_DATA` (JSON). Risponde a `issue view N --json …`, `pr list …`, `api repos/{o}/{r}/commits/{sha}/status`, `issue list …` e `auth status`, registra ogni chiamata in `$TOLLGATE_FAKEGH_LOG` ed esce con 1 se la risposta manca dai dati.
- Produces: `tests/flowkit.FlowLab(*, toml=DEFAULT_TOML, files=None, gate=True, issue=None)`, con:
  - `.ts` (TempState), `.main`, `.origin`, `.home` (HOME temporanea con `.claude/plugins/installed_plugins.json` che dichiara Superpowers 7.0.0);
  - `.env()`, con `TOLLGATE_STATE`, `TOLLGATE_GH=tests/fakegh.py`, i dati del finto e `HOME`;
  - `.cli(*argv, cwd=None, session="sess-flow") -> CompletedProcess`: scrive prima il segnale con `sessions.note_cli_call`, poi esegue `bin/tollgate`;
  - `.hook(payload)`, come `hookkit.Lab.hook`;
  - `.conn`, `.close()`.

  Con `gate=True` l'origin contiene i file della decisione 8. Le cartelle temporanee hanno uno spazio nel nome. `remote.origin.url` vale `https://github.com/prova/flow.git`, con `url.<origin nudo>.insteadOf` impostato su quell'URL: il fetch va al repo nudo locale e il controllo GitHub di `prereq.is_github` passa.

- [ ] **Step 1: Test che falliscono**
  - `test_sessions.py::CliSessionTest`:
    - `test_cli_session_found` (segnale di 5 s prima, stessa cartella e sottocomando → restituisce la sessione);
    - `test_cli_session_ambiguous_or_stale_refuses`: (a) due sessioni con segnali validi → `CliSessionError` con «più sessioni»; (b) segnale di 121 s prima → errore «sessione non riconosciuta»; (c) sottocomando diverso → errore; (d) cartella diversa → errore;
    - `test_note_cli_call_rejects_unsafe_session` (`"../x"` non crea file).
  - `test_check_cli_calls.py`:
    - `test_coordinator_call_records_signal`: `hookkit.Lab`, `bash(f"'{BIN}' start 7")` dalla sessione principale → uscita 0 e file `cli/sess-lab.json` con `argv[0] == "start"`;
    - `test_subagent_cannot_run_coordinator_commands`: con `agent_id`, `task start 1`, `act apply` e `status --checkpoint` → 2; `verify` e `block open needs_you --reason x` → 0;
    - `test_cd_then_call_records_effective_dir`.
  - `test_check_acts.py::ProgramLineTest::test_every_tollgate_command_gets_program_line` (`tollgate:start` e `tollgate:resolve` → l'iniezione contiene `programma` e il percorso di `bin/tollgate`).
  - `test_layers.py::LayersTest::test_imports`: con `ast`, `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`, e `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`.
- [ ] **Step 2: Verificare il fallimento**: `python3 -B -m unittest tests.test_sessions tests.test_check_cli_calls tests.test_check_acts tests.test_layers` → errori di import e asserzioni.
- [ ] **Step 3: Implementare** le firme sopra, più `fakegh.py` e `flowkit.py`. `cli_session` legge i file di `cli/` e confronta le cartelle con `Path.resolve()`.
- [ ] **Step 4: Verificare**: stesso comando verde, poi `tests/run`.
- [ ] **Step 5: Commit** «tollgate P3a: segnale della sessione per la CLI, riga del programma, strati, banco di prova del flusso».

---

