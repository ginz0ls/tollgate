# Task 7 — giro di correzione 3

Leggi W/task-7-rereview-2.md. Correggi, ogni volta prima il test RED:

- **N-3** Un JUnit con `<?xml version="1.0" encoding="bogus"?>` fa sollevare `LookupError`.
  - In `tollgate_analysis.junit.parse_junit` (o dove nasce) convertilo in `JunitError`, insieme a ogni altro errore di decodifica. Così ne beneficia anche `tollgate_core.runner`.
  - Ruling: `artifacts.validate`, `artifacts.read_results` e `baseids.load` sono confini fail-closed su dati non fidati. Al loro bordo esterno catturano **ogni** `Exception`, non `BaseException`, e la trasformano in un problema con il tipo e il messaggio (`baseids.load`: `None`). Un commento di una riga spiega perché.
  - Test: `encoding="bogus"`, sia per `validate`/`read_results` sia per `runner`, se `runner` legge i JUnit.
- **N-4** `p.stat()` dopo `is_file()` è protetto dalla stessa regola.

Non toccare i file del Task 8. Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 7, fix round 3)» e Co-Authored-By. Aggiungi in fondo a W/task-7-report.md la sezione «Fix round 3».
