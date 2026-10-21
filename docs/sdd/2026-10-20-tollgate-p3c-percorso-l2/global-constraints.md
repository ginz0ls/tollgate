## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- Strati (spec 3, `tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_flow` importa solo `tollgate_core` e `tollgate_analysis`; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`, tranne `tollgate_core/cli.py`; i moduli di `tollgate_checks` non scrivono nel DB né su file: usano `record`.
- Scritture nel DB solo con le funzioni di `tollgate_core`. `set_phase`, `open_block` e `close_block` fuori da una transazione. `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni diventano rifiuti, mai traceback (vincoli 1-5 del piano principale).
- **Programma nei comandi per il modello:** ogni comando scritto in un messaggio della CLI, di un hook, di un brief, di una skill o di un agente usa `tollgate_core.paths.program_command` (`python3 "<bin>"`); le skill scrivono `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`. Mai il percorso nudo.
- **Sottocomandi del coordinatore:** ogni sottocomando nuovo va in `cli_calls._COORDINATOR_ONLY`; se legge la sessione anche in `_SIGNALLED`, e passa `argv` a `sessions.cli_session` (vincolo (5) di P3b). In P3c nessun sottocomando nuovo legge la sessione: `audit` va solo in `_COORDINATOR_ONLY`; `approve spec`, `approve plan` e `reopen` passano da `act apply`, già segnalato.
- La configurazione si legge dalla base del lavoro o dalla punta del ramo predefinito di `origin`, mai dal working tree (spec 3.2). Gli hook non usano la rete.
- **Testo non fidato** (issue, spec e piano scritti dal modello, messaggi degli avversari e degli auditor): mai in un comando shell né in un argomento di `git` o `gh`. Va su file, in un recinto più lungo di ogni sequenza di backtick (`tollgate_analysis.brief.fence`), marcato come dato (`brief.DATA_NOTE`).
- `docs/superpowers/reviews/**` lo scrivono solo la CLI e gli hook (spec 0, file protetti): report e file di approvazione non si scrivono mai con Edit o Write, e il coordinatore li committa con `git add`/`git commit`.
- Nessuna rete nei test. `gh` nei test è `tests/fakegh.py` con `TOLLGATE_GH` e la sentinella. **Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json` o `~/.claude/plugins/`.** I test non lanciano `claude`; solo il Task 14 lancia `claude -p`, in `/tmp/tollgate-p3c`, con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

