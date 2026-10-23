# Task 7 — giro di correzione 2

Leggi W/task-7-rereview-1.md. Correggi, ogni volta prima il test RED:

- **N-1** `_load_results` in `bin/tollgate_gate/artifacts.py` cattura anche `RecursionError`, insieme a `ValueError` e `OSError`. Fai lo stesso in ogni altro punto di `artifacts.py` e `baseids.py` in cui un file degli artefatti passa da `json.loads`. Test: un `results.json` con `"[" * 100000`, entro il tetto di dimensione. `read_results` e `validate` restituiscono problemi e non sollevano. Fai lo stesso test per `baseids.load`.
- **N-2** `read_results` legge `results.json` una volta sola e usa quel risultato: niente seconda lettura dopo `_load_results`.

Non toccare i file del Task 8 (`guard.py`, `github.py`, `tests/fakegh.py`, `tests/test_gate_guard.py`). Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Deve essere verde su python3.11 e python3, poi committa con «(Task 7, fix round 2)» e Co-Authored-By. Aggiungi in fondo a W/task-7-report.md la sezione «Fix round 2».
