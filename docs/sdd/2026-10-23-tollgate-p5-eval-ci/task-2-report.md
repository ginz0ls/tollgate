# Task 2: report

Commit 6cb106d «tollgate P5: suite indipendente dal percorso, CI del plugin».

## Cosa
1. Decisione 11: `test_check_cli_calls` costruisce il percorso con spazi in `tempfile.mkdtemp(prefix="tollgate sp ")` (addCleanup); `test_prstate` confronta con `program_command(db.BIN_PATH)`; `test_taskcmd` con `program_command(BIN / 'tollgate')`. Tolti i controlli `assertIn(" ", ...)`.
2. Decisione 12, `BackupRaceTest.test_concurrent_migration_of_v1_db_with_rows`: causa trovata e test corretto (sotto).
3. Terzo instabile (3.13, `detect-merge-rosso`): correzione in `spikes/p4/make_case.py`.
4. `.github/workflows/ci.yml` e `tests/test_ci_workflow.py` (9 test: i 7 del brief + `test_suite_step_fails_when_tests_fail` (D5) + `test_actions_use_current_major_versions`).

## Indagine 1: BackupRaceTest (systematic-debugging)
- Fase 1: log runner (`ci-log.out:156-161`): `copies = glob("tollgate-*-migrazione-2.db")` vuoto su 3.11. In locale 50 corse con 8 processi di carico (script `race50.sh` nel scratchpad, carico fermato per PID): 0 falliti su 50. Non si riproduce.
- Strumentazione: 100 corse del flusso (4 processi, `taskset -c 0,1` più 2 processi di calcolo sugli stessi core) contando le copie nella cartella: distribuzione `{4:2, 5:2, 6:5, 7:57, 8:25, 9:7, 10:2}`. Ogni processo fa la copia prima di ogni passo che vede da fare (`db._migrate`), quindi con i processi in fila il totale può superare `KEEP_BACKUPS = 10` (`db.py:18`); `db.backup` pota le più vecchie per nome (`db.py:290`), e le più vecchie sono proprio quelle di `migrazione-2`. Sui runner (2 core) con 11 o più copie la pulizia le toglie tutte. Il massimo visto in locale è 10: sul limite.
- Prova deterministica: con `KEEP_BACKUPS` copie valide più recenti già presenti, la vecchia asserzione fallisce con lo stesso errore dei runner (`AssertionError: [] is not true`).
- Causa: il test presumeva che una copia `migrazione-2` sopravviva alla ritenzione; il codice è corretto (la potatura è voluta).
- Correzione (nel test, nessun ritentativo): helper `migrate_v1_db_with_rows_concurrently(newer_copies=0)`; il test ora controlla DB migrato, riga presente, copie non vuote, `<= KEEP_BACKUPS`, tutte integre; nuovo `test_migration_copies_older_than_the_retention_window_are_pruned` (deterministico) documenta la causa.
- Comando: `python3 -B -m unittest tests.test_db.BackupRaceTest` -> 4 test OK.

## Indagine 2: ControllaTest.test_gate_script_controlla (3.13)
- Log runner (`ci-log.out:788-876`): `caso-detect-merge-rosso: FALLITO`, «nothing to commit … commit del push diretto fallito» (`spikes/run-p4-gate.sh:273-274`).
- Causa: `make_case.py:789,803` scrivevano `notes/diretto-<ts>.md` con testo fisso, con `ts` al secondo (`run-p4-gate.sh:391`). In modo `controlla` (gh finto, veloce) `detect-push-diretto` e `detect-merge-rosso` girano in fila sulla stessa base, nello stesso secondo: stesso file e stesso testo, già su origin/main, quindi niente da committare. Dipende dalla velocità del runner, non dalla versione di Python.
- RED: `test_direct_push_files_differ_between_cases_built_in_the_same_second` (in `tests/test_p4_make_case.py`) fallisce prima: `['notes/diretto-20261022-000000.md'] == [...]`. GREEN dopo aver messo `{ctx.name}` nel nome del file: `tests.test_p4_make_case` 23 test OK.

## Nota: test_task1_script_still_passes... fallito su tutti e 4 i job
Non in elenco, ma nel log. Il ramo `p5-probe-ci` è stato clonato da `main` (`run-p5-checks.sh:434`), che non ha ancora la riscrittura `moved` di `ghguard.check_comandi` (Task 1): il fallimento riguarda il vecchio stato, non HEAD. Verificato: `python3 -B -I spikes/gh-p4/ghguard.py comandi …/comandi.log` in un clone con percorso `…/tollgate src` passa (1405 comandi), e `tests.test_p4_scripts` passa (14 test) in un clone senza spazi.

## RED/GREEN di ci.yml
- RED (ci.yml spostato): `python3 -B -m unittest tests.test_ci_workflow` -> `FAILED (errors=9)`.
- GREEN: `Ran 9 tests ... OK`.
- Mutazione: senza `shell: bash` nel passo suite, `test_suite_step_fails_when_tests_fail` fallisce (provato, poi ripristinato).
- Forma: `actions/checkout@v7` (`path: "tollgate src"`, `persist-credentials: false`), `actions/setup-python@v7` (`python-version: ${{ matrix.python }}`; input letti dai tag v7.0.1 e v7.1.0, node24), `defaults.run.working-directory: "tollgate src"`, `permissions: contents: read`, concorrenza per ramo, matrice 3.11 e 3.13, `fail-fast: false`, `timeout-minutes: 60`, passo suite (`shell: bash`) esattamente `PYTHONS=python PYTHONWARNINGS=error::ResourceWarning tests/run 2>&1 | tee suite.log`, passo che fallisce se `suite.log` contiene «unclosed database». Nessuna `${{ }}` nelle righe `run:`.

## Suite
- `tests/run` nel worktree: 3.11.16 `Ran 2570 tests in 853s OK (skipped=2)`; 3.13.5 `Ran 2570 tests in 906s OK`; rc=0.
- Controprova: copia senza spazi del worktree (rsync in `/tmp/tollgate-nospace-<pid>`, poi rimossa) con `PYTHONS=python3 tests/run`: `Ran 2570 tests in 838s OK`.

## Scostamenti dal piano
- `fail-fast: false` (non richiesto): una combinazione rossa non deve annullare le altre. Il test `test_actions_use_current_major_versions` è in più: va aggiornato dal Task 3 quando fissa gli SHA.
- La controprova senza spazi è stata fatta su una copia dei file del worktree (non `git clone` puro) per includere le modifiche non ancora committate.
- Un file extra modificato rispetto all'elenco del brief: `spikes/p4/make_case.py` e `tests/test_p4_make_case.py` (indagine 2, prevista dal carry).

## Autorevisione / dubbi
- Completezza rispetto al brief e a carry: ok. Nessun `__pycache__` nel commit; nessun `claude`/`gh`/rete usati.
- Dubbio: l'indagine 1 non riproduce il fallimento in locale; la causa è provata in modo deterministico (stesso errore) ma non osservata dal vivo. La potatura può scattare anche in P4 reale solo con >10 copie, comunque innocua.
- Il passo `suite.log` si scrive nella cartella del checkout (`tollgate src/`): non versionato, ma sporca l'albero del runner (innocuo).

## Fix round 1 (I-1: BackupRaceTest, correzione nel codice)
- Causa (confermata): `_migrate` copiava prima di rileggere la versione, quindi ogni processo concorrente faceva una copia per passo (4-10 copie per corsa), e `backup` potava per nome le più vecchie, cioè la sola copia pre-migrazione. Il mio primo fix indeboliva il test: ritirato.
- RED: test ripristinato e rafforzato (`test_concurrent_migration_of_v1_db_with_rows`: copia `migrazione-2` integra, con la riga e `schema_version` 1; esattamente una copia per passo) e `test_retention_never_prunes_the_pre_migration_copy` (10 copie recenti già presenti). Prima del codice: 2 FAIL (`['2.db','2.db','2.db','3.db','3.db','4.db','5.db']` e `[] is not true`). Tolti il test che dava `[]` come atteso e il `assertLessEqual` tautologico.
- Codice (`bin/tollgate_core/db.py`): `_migration_lock` (flock su `migrate.lock` nella cartella di stato) tiene insieme rilettura della versione, copia e passo; la copia la fa solo chi applica il passo. Tentativo scartato: copiare dentro `tx` (BEGIN IMMEDIATE) si blocca, perché l'API di backup di SQLite risponde BUSY alla connessione che sta scrivendo: da qui il lucchetto di file (già usato `fcntl.flock` in `waiver_cli.py`). La potatura non conta le copie `migrazione-*`: sono al più una per passo di schema (regola più semplice, e quelle copie sono i punti di ritorno).
- GREEN: `tests.test_db` 33 test OK; 12 corse di `tests.test_db` con 8 processi di calcolo (fermati per PID): 0 falliti; 60 corse del flusso sotto carico con `taskset` su 2 core: sempre 4 copie (prima 4-10), nessuna senza `migrazione-2`.
- `tests/run`: 3.11.16 2570 test OK (2 saltati, 871 s); 3.13.5 2570 test OK (1228 s); rc=0.
