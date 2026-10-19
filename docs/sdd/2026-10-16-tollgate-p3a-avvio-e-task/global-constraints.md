## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11 (spec 2). Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- Strati: `tollgate_analysis` non importa nulla di tollgate. `tollgate_flow` importa solo `tollgate_core` e `tollgate_analysis`. `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`. I moduli di `tollgate_checks` non scrivono nel DB: usano `record` (spec 3.2). Un test lo controlla (Task 2).
- Scritture nel DB solo con le funzioni di `tollgate_core`. `set_phase`, `open_block` e `close_block` si chiamano fuori da una transazione. Gli errori da gestire sono `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni (vincoli 1-5 del piano principale).
- Vincoli per P3 del piano principale, tutti in questo piano:
  - (1) `name` del brief = `tasks.implementer` (Task 6);
  - (2) la statusline scrive `ctx/<session_id>.json` (Task 11);
  - (3) `start` pulisce `bound/` (Task 3);
  - (5) `approve level` scrive `level_cap_paths` (Task 8);
  - (6) i verdetti sono moduli nuovi di `subagent_stop` che controllano `tampered` (Task 7);
  - (7) `task start` chiama `tasks.assign` con `pending` (Task 6);
  - `start` registra le radici attive con `active.register` (Task 3).
  - Il vincolo (4), `open-pr`, è di P3b.
- La configurazione si legge dalla base del lavoro o dalla punta del ramo predefinito di `origin`, mai dal working tree (spec 3.2). `start` fa `git fetch origin` prima di leggerla.
- Il testo dell'issue non è fidato: non entra mai in un comando shell né negli argomenti di `git`. Va su file, in un recinto più lungo di ogni sequenza di backtick che contiene, marcato come dato (spec 6.1).
- Nessuna rete nei test. `gh` nei test è il finto `tests/fakegh.py`, attivato da `TOLLGATE_GH` con la sentinella (spec 3.1). **Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json` o `~/.claude/plugins/`**: si passano cartelle temporanee (`TempState`, `HOME` temporanea).
- I test non lanciano `claude`. Solo i Task 1 e 13 lanciano `claude -p`, sempre in `/tmp/tollgate-p3a`, con `--plugin-dir`, mai nel repo e mai con il plugin installato nella configurazione dell'utente.
- Identificatori in inglese, testi per l'utente in italiano (spec 0). Nessun `__pycache__` nel repo (`-B`).
- Commit dopo ogni task.
