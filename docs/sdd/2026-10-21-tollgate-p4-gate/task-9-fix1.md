# Task 9 — giro di correzione 1

Leggi W/task-9-review.md. Correggi, ogni volta prima il test RED:

- **I-1** Decisione 5: con `--publish`, una volta noto lo SHA, ogni esito pubblica `tollgate/verdict` e `tollgate/attention` espliciti.
  - Dopo aver letto `sha`, `verdict.main` avvolge il resto in un confine che cattura ogni `Exception`, non `BaseException`. Con `publish` scrive `error` con `DESC_ERROR` e il motivo, entro 140 caratteri.
  - Esce 0 se gli stati sono scritti, 1 solo se non si riesce a scriverli. Senza `publish` stampa il motivo ed esce con un codice diverso da zero.
  - Restano senza stati i casi «non applicabile» e «SHA superato», cioè quelli in cui la decisione 5 vieta di scrivere.
  - Test: `GhError` da `shared_sha_prs`, da `pull` e dal ricontrollo; `ValueError` da `pr_from_rest`; un'eccezione qualsiasi in `evaluate.evaluate`. Riscrivi `test_gh_failure_is_a_clean_refusal`.
- **I-2** La regola «issue della PR» vive in una sola funzione, in `evaluate.py` o `model.py`, ed è usata sia da `Context.issue_no` sia da `verdict`. Togli la copia in `verdict.py`.
- **Minori**
  - Il commento «non applicabile» ricontrolla la testa prima di scrivere.
  - Le PR del payload `workflow_run.pull_requests` si filtrano per `state == "open"` quando il campo c'è.
  - Niente `KeyError` possibile in `finish`.
  - `tests/fakegh.py:26` sta entro 100 caratteri.
  - Un test per il caso fork con issue chiusa.

Non toccare i file del Task 10 (`sentinel.py`, `baseids.py`, `tollgate_flow/gh.py`, `test_gate_sentinel.py`, `test_gh.py`, `test_start.py`). Se devi toccare `cli.py` o `github.py`, limita la modifica a ciò che serve qui. Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 9, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-9-report.md la sezione «Fix round 1».
