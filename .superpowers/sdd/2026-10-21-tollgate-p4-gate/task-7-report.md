# Report Task 7: gate run, base-ids e artefatti

## Implementato
- `bin/tollgate_gate/run.py`: `run.run(...)` (D5: `setup` globale e dei profili attivi prima del gate; `setup` fallito = voce `red` `setup` / `profile:<p>:setup` e comandi del gate dopo = `red` con `reason`), `run_commands` condivisa con `base-ids`, log troncati a 1 MB (si tiene la coda), JUnit copiati in `junit/<i>.xml`. Comando non configurato = `unverified` (come `verify`). Ritorno 1 solo se non si può scrivere.
- `bin/tollgate_gate/baseids.py`: `compute` (formato decisione 12, un solo insieme `runner.ids_commands`) e `load(path, tree=)`.
- `bin/tollgate_gate/artifacts.py`: `validate` (symlink, file non regolari, limiti per file e totale, XML con DOCTYPE/entità, `results.json` assente o con `report` assoluto, con `..` o fuori da `junit/`) e `read_results`.
- `bin/tollgate_gate/cli.py`: `gate run` e `gate base-ids`, `main` con D21c (GhError, GitError, ConfigError, OSError, ValueError -> messaggio, uscita 1). `HANDLERS` è la tabella dei sottocomandi (i Task 8-10 ne aggiungono).
- `bin/tollgate`: smista `gate` prima di importare `tollgate_core.cli`. `tollgate_core/cli.py`: una riga di aiuto (epilog), nessun sottoparser.
- D4: `--publish` rifiutato senza `GITHUB_ACTIONS=true`; `bin/tollgate_checks/cli_calls.py` nega `gate … --publish` a chiunque (programma riconosciuto come per i comandi del coordinatore; ramo non analizzabile fail-closed; non solleva).

## Scostamenti e scelte
- `baseids.compute` ha un parametro in più, `cfg_repo` (di norma `repo`): D8 vuole la configurazione della punta del predefinito letta dal checkout della CLI mentre l'albero è quello di `--root`, e la punta può non esistere nel checkout di `--root`.
- `gate base-ids` esegue anche i `setup` (globale e di tutti i profili dichiarati, coerente con `ids_commands`): senza, la suite della base non girerebbe in CI. D5 nominava solo `gate run`. Un `setup` fallito lascia i comandi `red` senza identificativi.
- `--publish` in `base-ids` per ora fa solo il controllo D4: la pubblicazione vera la aggiunge il Task 10.
- `results.json`: voci con `reason` solo per i comandi non eseguiti per un `setup` fallito; `report` = `junit/<indice del comando>.xml`.
- Messaggi e `prog` di argparse non scrivono `tollgate gate …` nudo: `tests/test_manifest.py::BareProgramInMessagesTest` lo vieta (etichette `gate run: …`, `prog="gate"`).
- Nessuna cache: né `gate run` né `base-ids` salvano nulla in cache, nessun `--head-ids-out` (V4).

## TDD
RED: ho scritto il codice prima di rilanciare i test, quindi il RED l'ho ricostruito dopo su una copia di `HEAD` (`git archive`) con i soli test nuovi:
`python3 -B -m unittest tests.test_gate_run tests.test_gate_artifacts tests.test_check_cli_calls tests.test_cli` -> `Ran 36 tests ... FAILED (failures=14, errors=2)`: ImportError `cannot import name 'artifacts'` / `'baseids'` da `tollgate_gate`; FAIL `test_gate_publish_denied_to_everyone`, `test_gate_is_dispatched_before_the_core_cli`, `test_help_names_gate`. (`test_python_form_with_double_quoted_spaced_path` fallisce in quella copia solo perché il percorso del banco non ha spazi.)
GREEN: gli stessi comandi nel worktree: tutti verdi. Suite completa: `PYTHONS=python3.11 tests/run` -> `Ran 2002 tests ... OK` (426 s); `PYTHONS=python3 tests/run` -> `Ran 2002 tests ... OK` (436 s). Un primo giro aveva due fallimenti in `BareProgramInMessagesTest` (messaggi con `tollgate gate` nudo), corretti.

## Test
- `tests/test_gate_run.py` (22): `test_results_shape`, `test_not_applicable_runs_nothing`, `test_config_from_default_tip_not_head`, `test_no_state_created` (processo vero con `PYTHONVERBOSE`, `HOME` e `TOLLGATE_STATE` temporanei: né `tollgate_core.db`, né `tollgate_core.cli`, né `sqlite3`; nessuna cartella creata), `test_base_ids_format_and_tree`, `test_load_rejects_other_tree`, D5 (3), D8, D4 (rifiuto e accettazione), D21c (uno per eccezione).
- `tests/test_gate_artifacts.py` (8): `test_dotdot_absolute_symlink_rejected`, `test_report_path_in_results_json_rejected`, `test_size_limits`, `test_xml_entity_rejected`, `test_valid_dir` e altri.
- `tests/test_check_cli_calls.py` (+2), `tests/test_cli.py` (+2). `test_layers` (isolamento a runtime e AST) resta verde.

## File
bin/tollgate, bin/tollgate_core/cli.py, bin/tollgate_checks/cli_calls.py, bin/tollgate_gate/{run,baseids,artifacts,cli}.py, tests/test_gate_run.py, tests/test_gate_artifacts.py, tests/test_check_cli_calls.py, tests/test_cli.py.

## Dubbi
- `read_results` considera problema un `report` dichiarato ma assente; la spec non lo dice.
- `sha` di `results.json` è `HEAD` del checkout (non `pull_request.head.sha`): il workflow del Task 9 deve fare il checkout della testa.
