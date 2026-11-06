# Report Task 5

## Cosa
- `tests/run`: `RUN_TMP=$(mktemp -d "${TMPDIR:-/tmp}/tollgate-run-XXXXXX")`, `export TMPDIR`, trap D1 (`chmod -R u+rwX` + `rm -rf`, entrambi con `|| true`: l'uscita resta quella dei test).
- Perdite chiuse: `tests/test_gh.py` (addCleanup rmtree su `self.tmp`), `tests/test_statusline.py` (CtxTest, `self.home`), `tests/test_hook_engine.py` (RunnerTest.tearDownClass).
- `tests/test_run_script.py`: sonda + 3 test della corsa (compreso `test_run_removes_sealed_dirs_and_keeps_exit_code`, D1) + `test_known_leaks_closed` (D13: PrReadTest per FakeGhCase; setUpClass/tearDownClass a mano per RunnerTest).

## TDD
RED: `python3 -B -m unittest tests.test_run_script` prima del codice: 4 failure (cartella non `tollgate-run-*`, leak ancora presenti), 1 skipped (sonda).
GREEN: `python3.11 -B` e `python3 -B -m unittest tests.test_run_script tests.test_p4_ghguard tests.test_gh tests.test_statusline tests.test_hook_engine`: 149 test OK (skipped=1) per entrambi.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3.11.16 Ran 3545 OK (skipped=5); 3.13.5 Ran 3545 OK (skipped=3); EXIT=0. Uscita in `task-5-suite.out`.
`/tmp/tollgate*` prima e dopo la corsa: identici (`task-5-tmp-prima.txt`, `task-5-tmp-dopo.txt`, nessuna differenza). Instabile test_cli ctrl-c: verde.

## Scostamento dal piano (necessario)
`RunnerTest.tearDownClass` toglie anche da `sys.modules` `finti_checks*`: `fake_checks` importa il pacchetto dalla cartella temporanea; ripetere setUpClass nello stesso processo (come fa `test_known_leaks_closed`) lasciava i moduli in cache che puntavano alla cartella tolta e rompeva 14 test di RunnerTest (visto in un primo giro).

## Autorevisione
Valori del brief e di D1/D13 usati alla lettera. Nessun `__pycache__`, nessun file fuori dal worktree toccato. La CI (`PYTHONS=python tests/run`) funziona invariata; la guardia P4 accetta `$TMPDIR` sotto `/tmp`.

## Fix round 1
- Ambiente del figlio: `os.environ` senza `MODEL_KEY_VARS` e `PYTHONWARNINGS`, più `TMPDIR`, `PYTHONS`, `RUN_TMP_PROBE`.
- `RunnerTest.tearDownClass` registrato con `addCleanup` subito dopo `setUpClass`.
- `seen.parent.resolve()` contro `self.base.resolve()`.
- Test della cartella sigillata: `skipIf(os.geteuid() == 0)`.
- Comando: `python3.11 -B -m unittest tests.test_run_script` e con `python3`: Ran 5 tests OK (skipped=1) in entrambi.
