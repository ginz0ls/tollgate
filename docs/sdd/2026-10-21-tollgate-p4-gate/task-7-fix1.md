# Task 7 — giro di correzione 1

Leggi W/task-7-review.md. Correggi, ogni volta prima il test RED:

- **I-1** `allow_abbrev=False` sul parser principale e su ogni sottoparser di `bin/tollgate_gate/cli.py`. Test: `gate base-ids … --publ` è un errore di argomenti. In `bin/tollgate_checks/cli_calls.py` il guardrail nega anche ogni prefisso di `--publish` lungo almeno quanto `--pu` (con o senza `=valore`), sempre senza sollevare mai. Test con `--pub`.
- **I-2** `_report_problem` rifiuta un `report` che contiene NUL o caratteri di controllo. `read_results` resta fail-closed: ogni `ValueError` o `OSError` sulla lettura diventa `(None, False, problemi)` e non viene sollevato. Test con `"report": "junit/a\u0000.xml"`.
- **Minori** Aggiungi il test «nessuno stato» per `gate base-ids`: processo vero, `HOME` e `TOLLGATE_STATE` temporanei, nessuna cartella creata, `sqlite3` e `tollgate_core.db` non caricati. `read_results` controlla la dimensione di `results.json` prima di leggerlo.

Non toccare `evaluate.py`, `comment.py` e `prbody.py`, che sono del Task 6. Il workspace W è ignorato di proposito: non usare mai `git add -f` sui suoi file e non committare report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Deve essere verde su python3.11 e python3, poi committa con «(Task 7, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-7-report.md la sezione «Fix round 1» (test RED/GREEN con l'output).
