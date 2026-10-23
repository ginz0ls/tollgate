# Revisione Task 7 (6279719..3fb65e9)

### Aderenza
- ✅ `bin/tollgate gate …` smistato prima di `tollgate_core.cli` (`bin/tollgate:12-15`); `test_no_state_created` (`tests/test_gate_run.py`) lancia il processo vero con `PYTHONVERBOSE`, verifica che `tollgate_core.db`, `tollgate_core.cli`, `sqlite3` non siano caricati e che né lo stato né la HOME cambino. L'asserzione `tollgate_gate.cli in loaded` prova che la regex legge davvero gli import.
- ✅ Configurazione dalla punta del predefinito: `cli.py:cmd_run` usa `origin/<default>`, `run.py` `load_config_at(repo, config_sha)`; test `test_config_from_default_tip_not_head` e `test_cli_root_is_the_tree_config_is_the_default_tip` (D8, `cfg_repo`).
- ✅ D5: `setup` globale e dei profili attivi prima del gate, `setup` fallito → `red` + comandi del gate `red` con `reason`, non eseguiti (test sui tre casi). Ruling del controller: `setup` anche in `base-ids`, `cfg_repo` presente.
- ✅ D21c: cinque eccezioni → messaggio e uscita 1, un test ciascuna (`MainErrorsTest`); in più evento malformato.
- ✅ V4/V4b: nessuna cache, nessun `--head-ids-out`.
- ✅ D4, difesa in-process: `cli.py:cmd_base_ids` rifiuta senza `GITHUB_ACTIONS=true` prima di ogni lavoro (test con tre valori). Difesa locale: `cli_calls.py` copre il ramo analizzabile, il ramo non analizzabile (fail-closed), `--publish=x`, agente e coordinatore; non solleva.
- ❌ D4, difesa locale incompleta: vedi I-1.
- ✅ `artifacts.validate`: `..`, assoluto, symlink (file e cartelle, non seguiti), file non regolari, limiti per file e totale, DOCTYPE/entità (via `parse_junit`), `report` fuori da `junit/` o non stringa. `read_results` fail-closed su JSON malformato, versione o forma errata, stati non validi.
- ✅ Testo non fidato: `results.json` contiene solo nomi di comandi dalla configurazione del predefinito e numeri; i log restano file; nessun testo del progetto finisce in argomenti di git/gh (`resolve_ref` controlla il ref). `base.ref` dell'evento è solo confrontato.
- ⚠️ Non verificabile qui: come `evaluate` (Task 8) tratterà le voci `setup`/`profile:*:setup` in `results.json`. Un `setup` riuscito senza report ha stato `uncounted` (`receipt_state`), non `green`: Task 8 non deve leggerlo come rosso né come comando del gate mancante.

### Punti di forza
- Strati rispettati e provati a runtime. `run_commands` condivisa tra `run` e `base-ids` (niente duplicazione). `report_path` validato prima di eseguire o cancellare. Log troncati tenendo la coda. Test dei casi limite (`setup` di profilo, JUnit con skipped, ids illeggibili, cartella `--out` non scrivibile). Messaggi senza `tollgate gate` nudo.
- Sul RED ricostruito: i moduli sono nuovi, quindi i test non importavano prima; i test di comportamento (`results_shape`, D5, D8, `load` per albero, `validate`) asseriscono esiti reali e fallirebbero con un'implementazione sbagliata. Accettabile; `test_gate_publish_denied_to_everyone` e `test_gate_is_dispatched_before_the_core_cli` hanno un RED dimostrato.

### Rilievi

**Important**
- **I-1** `bin/tollgate_gate/cli.py:378,384` e `bin/tollgate_checks/cli_calls.py:79`. argparse accetta le abbreviazioni univoche (`allow_abbrev` è vero): `gate base-ids … --pub` o `--publ` imposta `publish=True` (verificato con `build_parser().parse_args`). `_publishes` confronta solo `--publish` e `--publish=`, quindi il guardrail locale lascia passare l'abbreviazione; resta solo la difesa in-process, aggirabile con `GITHUB_ACTIONS=true tollgate gate base-ids … --pub`. D4 vuole due difese indipendenti. Correzione: `allow_abbrev=False` sul parser principale e su ogni sottoparser (`add_parser(..., allow_abbrev=False)`), con un test che `--pub` esce con errore di uso; in alternativa, nel guardrail, negare ogni argomento `--pu…` che sia prefisso di `--publish`. La prima è più semplice e protegge anche i Task 8-10. Test del guardrail: aggiungere `--publ` alla lista di `test_gate_publish_denied_to_everyone`.
- **I-2** `bin/tollgate_gate/artifacts.py:275`. `read_results` con `"report": "junit/a\u0000.xml"` supera `validate` e poi alza `ValueError: embedded null byte` (`read_bytes` fuori da `except (OSError, JunitError)`), invece di restituire un problema. Il contratto è `(None, False, problemi)` e il chiamante (Task 9) ne trae `error` con il motivo; con un `ValueError` esce solo la riga generica di D21c, senza lo stato. Correzione: rifiutare in `_report_problem` i percorsi con `\x00` (o altri caratteri di controllo) e/o aggiungere `ValueError` all'`except`; test con NUL in `test_report_path_in_results_json_rejected`.

**Minor**
- `artifacts.py:197`: `results.json` si legge intero prima che i limiti di dimensione si applichino a quel file (l'eventuale problema di taglia è già in `problems`, ma `_load_results` legge comunque tutto). Saltare la lettura se `size > max_file`.
- `artifacts.py:241`: nessun tetto al numero di file in `junit/` (si fa `parse_junit` su ciascuno): rientra nel limite totale di 200 MB, quindi solo costo.
- `tests/test_gate_run.py`: `test_no_state_created` copre solo `gate run`; `gate base-ids` (stesso smistamento) non ha un test «nessuno stato».
- `read_results` non ritorna `sha` né `config_sha` di `results.json`: il Task 9 deve rileggerli a parte per la verifica del rilievo M-6; coerente con l'interfaccia del piano, ma da ricordare.
- `run.py`: `tests_skipped` non è validato in `read_results` (non usato); `reason` ignorato. Nessun effetto.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** Il task è solido e ben testato, ma la difesa locale di D4 si aggira con un'abbreviazione di `--publish` (I-1) e `read_results` solleva invece di restituire problemi su un `report` con NUL (I-2). Entrambe sono correzioni di poche righe.
