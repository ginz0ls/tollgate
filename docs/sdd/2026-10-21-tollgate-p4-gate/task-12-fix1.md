# Task 12 — giro di correzione 1

Leggi W/task-12-review.md. Il giro 1 del Task 11, appena committato, ha portato `fullmatch` e le virgolette singole in `install.py`. Correggi, ogni volta prima il test RED:

- **I-1** Una sola regola di convalida dei servizi (nome `^[a-z0-9-]+$`, immagine, porta) vive in `bin/tollgate_gate/install.py`, con `fullmatch`. `init.py` la importa e non ha una copia sua. Test: un a capo finale nel nome e nell'immagine viene rifiutato, sia da `init` sia da `install.files`.
- **I-2** `_gate_seconds` usa solo le ricevute del repo corrente: JOIN con `work_items` sul `repo_key` del repo, che ricavi come fa già il resto di `tollgate_flow`. Usa solo le ricevute verdi. Test: le ricevute di un altro repo con lo stesso nome di comando e le ricevute rosse non contano.
- **Minori**
  - I nomi dei workflow già presenti entrano nel README neutralizzati (`prbody.neutralize` o l'helper che usa già il resto).
  - Il README dice di compilare `[commands]` in `tollgate.toml`.
  - `--update` segnala la protezione mancante anche quando nessun file è cambiato.
  - La riga lunga nella docstring di `tests/fakegh.py` sta entro 100 caratteri.

Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 12, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-12-report.md la sezione «Fix round 1».
