# Task 8 — giro di correzione 1

Leggi W/task-8-review.md. Correggi, ogni volta prima il test RED:

- **I-1** `github.shared_sha_prs` tiene solo le PR aperte verso il predefinito con `head.sha == sha` (ruling D7, fatto V5b del Task 1: `commits/<sha>/pulls` elenca anche le PR impilate). Test: PR B impilata su A, entrambe verso il predefinito. La testa di A non è condivisa, quindi `guard` pubblica il suo stato normale e non `error`.
- **I-2** `guard` rosso resta `failure`. Titolo, docstring e testo di `comment.render_guard` e `_guard_build` dicono che `tollgate/guard` è rosso e perché, senza «in attesa». Aggiorna i test che leggono quel testo.
- **Minori**
  - Prima di scrivere il commento, `guard` ricontrolla che lo SHA sia ancora la testa della PR (decisione 14); se non lo è, non scrive nulla. Un test.
  - `WAIVERS` si importa da `tollgate_analysis.protected`, senza un secondo letterale.
  - Due test: un file di tollgate spostato (rinomina) è rosso; nomi di file ostili (con backtick, `-->`, `@`) nell'uscita e nel commento restano neutralizzati.
  - La docstring di `ghcli.py` sta entro 100 caratteri per riga.

Non toccare i file del Task 7 (`artifacts.py`, `baseids.py`). Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 8, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-8-report.md la sezione «Fix round 1».
