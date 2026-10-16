## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Nessuna dipendenza esterna.
- Python ≥ 3.11 (spec 2). Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- `tollgate_analysis` non importa `tollgate_core`, `tollgate_hooks` né `tollgate_checks` (piano principale, sezione 3). Un test lo controlla (Task 4).
- Un modulo di `tollgate_checks` non scrive mai nel DB: restituisce decisioni `record` (spec 3.2). Il contesto che riceve espone il DB solo in lettura.
- Chi scrive nel DB lo fa con le funzioni di `tollgate_core`; `set_phase`, `open_block` e `close_block` si chiamano fuori da una transazione; ogni commit visto dagli hook diventa un evento `commit` e fa scattare `acts.invalidate_finish`; gli hook gestiscono `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni (vincoli 1-5 del piano principale).
- Gli hook non usano mai la rete (spec 3.2). La configurazione si legge dalla base del lavoro, o dalla punta del ramo predefinito di `origin`, mai dal working tree.
- I pattern usano ovunque il dialetto di `.gitignore` (spec 3.2), implementato una volta in `tollgate_analysis/globs.py`.
- Solo l'uscita 2 blocca (spec 7.1). Il veto si dà con uscita 2 e il motivo su stderr; ogni messaggio d'errore riporta il percorso assoluto di `bin/tollgate` e il comando `touch <cartella di stato>/OFF`.
- Variabili di test (`TOLLGATE_STATE`, `TOLLGATE_GH`, `TOLLGATE_TEST_CONFIG`) valide solo con la sentinella `.tollgate-test` (spec 3.1). **Nessun test tocca `~/.local/state/tollgate`**: ogni test usa `tests.helpers.TempState`.
- I test non lanciano `claude` e non usano la rete. Solo il Task 1 lancia `claude -p`, in `/tmp/tollgate-p2`, mai nel repo.
- Identificatori in inglese, messaggi all'utente in italiano (spec 0).
- Nessun `__pycache__` nel repo (`sys.dont_write_bytecode`, `-B`).
- Commit dopo ogni task (e dopo ogni passo di commit indicato).
