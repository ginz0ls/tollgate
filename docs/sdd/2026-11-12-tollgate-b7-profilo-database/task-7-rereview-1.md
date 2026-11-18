### Verdetti sui rilievi
**In L2 `finish check` era rosso: il `verify` usciva 0 senza rapporto (`uncounted`) e i test dei must-have non risultavano contati.** INDIRIZZATO.
- `spikes/b7/flow/tools/unittest_junit.py` (nuovo) scrive `reports/junit.xml` con `classname`/`name` separati dall'ultimo punto di `test.id()`. Eseguito in una copia temporanea: 1 test, rc 0, XML scritto; `tollgate_analysis.junit.parse_junit` (`bin/tollgate_analysis/junit.py:52-54`) lo legge e produce `tests.test_migrations.MigrationsTest::test_every_table_has_row_level_security` in `ids_run`. Gli id sono quindi nella forma `classname::name`, la stessa dei must-have della spec (`spikes/b7/input/spec-L2.md:13-14`: `tests.test_migrations.MigrationsTest::test_tags_table`, `tests.test_function.FunctionTest::test_reads_tags`), che per un `FunctionTest` in `tests/test_function.py` darebbe esattamente quegli id.
- `spikes/b7/flow/tollgate.toml`: `verify = "python3 tools/unittest_junit.py"` e `report = "junit:reports/junit.xml"`; `report_path` (`bin/tollgate_core/runner.py:36-44`) accetta il prefisso `junit:` e un percorso relativo senza `..`; il rapporto viene letto a `runner.py:131-133`.
- `reports/` già in `spikes/b7/flow/.gitignore`.
- `spikes/run-b1-flow.sh:124`: file nuovo in `PROJ_FILES` del caso `database` (e il ciclo a riga 294 lo copia).
- `spikes/b7/input/spec-L2.md:27`: vieta di modificare `tools/unittest_junit.py`.
- Test: `test_real_flow_case_database_project_verifies` e `test_real_flow_case_database_project_declares_junit_report` (`tests/test_b1_scripts.py`), eseguiti io: 2 test OK. Il primo gira in una copia temporanea, quindi non sporca il worktree.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important.
- Minor, `spikes/b7/flow/tools/unittest_junit.py:37`: `res.cases` vuoto dà exit 1; coerente con `allow_no_tests = true`? Se il progetto non ha test il verify è rosso. Non succede, perché `tests/test_migrations.py` esiste; è solo una nota.
- Minor, stesso file: i `failure`/`error` hanno `message="x"` senza dettaglio; il dettaglio resta su stderr. Basta per i conteggi.
- Il test `..._verifies` non controlla gli id `tests.test_function...` (non esistono ancora nel progetto di prova, li crea l'implementatore in L2): corretto, non è un difetto.

### Osservazioni fuori ambito
Nessuna. (Il rosso `test_committed_evidence_has_no_long_web_results` è dichiarato fuori giudizio.)

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
