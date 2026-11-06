# Task 7 (Step 2-4) — report

## Cosa
- `spikes/b3bis/models-prova.sh` (modi `controlla`, `prepara`, `prova`), `spikes/b3bis/progetto/` (`tollgate.toml` con D3, `ai/models.py` con quattro segnaposto `"modello-da-scegliere"`, `README.md`), `tests/test_b3bis_script.py` (11 test).
- `controlla`: bash, git, interprete, tollgate, progetto, `bash -n`; per ogni variabile di `templates/models.toml` (nomi letti con grep dal file) stampa solo «impostata / non impostata» (vuota = non impostata). Nessuna scrittura.
- `prepara`: sposta in `<nome>.prev-<tempo>` repo, origin, state, out se esistono; copia il progetto, `git init -q -b main`, identità `prova` (D11) nel repo e nell'origin, commit, push, `remote set-head`, `tollgate.defaultBranch main`; stato con `.tollgate-test`.
- `prova`: dal repo lancia `"$B3BIS_PY" -B "$B3BIS_TOLLGATE" models check --refresh` e poi senza `--refresh` con `TOLLGATE_STATE=$B3BIS_DIR/state`; l'uscita sta in una variabile e si confronta con `[[ $out == *"${!n}"* ]]` (comando interno di bash) per ogni variabile non vuota; se c'è il valore, errore col solo nome della variabile e nulla salvato; altrimenti `out/refresh.txt` e `out/cache.txt` (un file per corsa). Rifiuta se `out/` esiste già (si rifà `prepara`, che lo sposta).
- Directory ammessa: `/tmp/tollgate-b3bis` o `/tmp/tollgate-b3bis-test-?*`; ogni `..` o `/` finale rifiutato per tutti e tre i modi, prima di scrivere. Sotto la cartella di test `B3BIS_TOLLGATE` è obbligatorio e deve esistere.
- Le richieste vere: ogni corsa è un file; le richieste per fornitore/pagina/tentativo non sono contate dallo script (l'uscita di `models check` non le dà).

## TDD
RED: prima dello script `python3 -B -m unittest tests.test_b3bis_script` -> `FAILED (failures=25, errors=2)` (script mancante, 127); `W/task-7-red.out`.
GREEN: dopo lo script `Ran 11 tests ... OK` con python3 (3.13) e python3.11.

## Verifica
- `bash -n spikes/b3bis/models-prova.sh`: ok.
- `PYTHONWARNINGS=error::ResourceWarning tests/run` (`W/task-7-suite.out`): 3.11.16 `Ran 3559 tests, OK (skipped=5)`; 3.13.5 `Ran 3559 tests, OK (skipped=3)`; RC=0. Il test instabile `test_db_restore_interactive_eof_and_ctrl_c` non è risultato rosso.
- Nessuna cartella `tollgate-b3bis*` rimasta in `/tmp`; nessun `__pycache__`.

## Scostamenti dal piano
- `controlla` stampa anche tutte le variabili «non impostata» (non solo le impostate): più utile al controller, nessun valore.
- Nessun file `.rc` per corsa (il codice d'uscita è solo stampato): le evidenze restano le sole uscite.
- `test_prepara_keeps_previous_work` e `test_prova_needs_prepara`, `test_controlla_fails_without_interpreter`, `test_prova_runs_twice_refresh_first`: test in più.

## Autorevisione / dubbi
- Una chiave molto corta (es. un solo carattere) farebbe rifiutare un'uscita innocua: errore sul lato sicuro.
- `prova` dà il comando reale con le chiavi dell'ambiente: l'ambiente del figlio è quello del controller.
- Nell'uscita il valore di una chiave non è mai in un argomento di processo; la variabile `CORSA_OUT` vive solo in bash.

## Come lancia il controller
```
bash spikes/b3bis/models-prova.sh controlla      # dopo aver scritto ai/models.py (Step 5) e committato
bash spikes/b3bis/models-prova.sh prepara
bash spikes/b3bis/models-prova.sh prova          # al più 3 tentativi: ogni nuovo tentativo si fa dopo `prepara`
```
Le uscite sono in `/tmp/tollgate-b3bis/out/{refresh,cache}.txt`.

## Fix round 1
- Importante 1: `verifica_dir` ammette solo `/tmp/tollgate-b3bis` o `/tmp/tollgate-b3bis-test-<nome>[/<una cartella>]`; rifiuta link simbolici su `<nome>` e su `B3BIS_DIR` e, se esistono, percorsi con `pwd -P` diverso. Test `test_dir_rejects_symlinks_and_deep_paths` (link dentro la cartella del test, link di primo livello in /tmp, alias, due livelli; nessun file nel bersaglio). RED: 17 failures; GREEN dopo la correzione.
- Minore 2: `umask 077` in cima allo script; test `test_out_and_state_are_private`.
- Minore 3: il test sulla chiave asserisce la frase esatta dello script e che il valore finto non sia in stdout, stderr né in alcun file sotto `B3BIS_DIR` (esclusa `.git` del repo).
- Comando: `bash -n spikes/b3bis/models-prova.sh`; `python3 -B -m unittest tests.test_b3bis_script` con python3 e python3.11: `Ran 13 tests ... OK` in entrambi. Suite completa non rilanciata.
- Contratto: invariato; `B3BIS_DIR` sotto `-test-*` ora ha un solo livello.
