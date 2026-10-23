# Task 6 — giro di correzione 1

Leggi W/task-6-review.md. Correggi, ogni volta prima il test RED:

- **I-1** Il testo non fidato non deve stare in `Item.text` (Global Constraints: solo in `Item.data`). In `bin/tollgate_gate/evaluate.py` (Task 5, circa la riga 433) gli identificativi e i titoli dei test letti dalla PR (`v.detail`, per esempio `test_id_missing`) vanno in `data`, come già fa `evaluate.py:318-320`; `text` resta una frase fissa di tollgate. Controlla con grep ogni altro `Item(` di `evaluate.py` e `attention.py` dove `text` interpola valori letti dalla PR, dal piano o dall'agente, e spostali in `data`. Difesa in profondità: `comment` rende `Item.text` su una sola riga (gli a capo diventano spazi), da `defuse` e con un tetto di lunghezza. Test: un titolo di test con `</details>`, un recinto e `@utente` non esce attivo dal commento.
- **I-2** Il corpo resta entro `MAX_BODY` per ogni ingresso, anche con una voce sola da 100.000 caratteri in `text` o in `data`: c'è un ultimo taglio duro dopo la scala. Vale lo stesso per `prbody.render`, dove il blocco JSON resta intero e ultimo e `prblock.parse` lo trova.
- **I-3** Anche `render_guard` ha il tetto totale, con la nota «troncato». Test: 50 problemi da 2.000 caratteri.
- **I-4** La decisione 14 vince sul brief: i marcatori sono `<!-- tollgate-verdict sha=<40 esadecimali> -->` e `<!-- tollgate-guard sha=<sha> -->`. `marker_sha` legge quella forma; `MARKER_PREFIX` resta uguale a `fixtask.GATE_MARKER`. Aggiorna i test.
- **Minori** `defuse` spegne anche `--!>`. `prbody._cap` diventa pubblica (`prbody.cap`; aggiorna chi la usa). Una sola scala dei tetti, `prbody.CAPS`, che `comment` importa. Test dei casi limite: una voce enorme, molti gruppi, una guardia con molti problemi.

Non toccare i file del Task 7 (`bin/tollgate_gate/{run,baseids,artifacts,cli}.py`, `bin/tollgate`). Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Deve essere verde su python3.11 e python3, poi committa con «(Task 6, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-6-report.md la sezione «Fix round 1» (test RED/GREEN con l'output).
