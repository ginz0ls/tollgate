# Task 10 — giro di correzione 1

Leggi W/task-10-review.md. Correggi, ogni volta prima il test RED:

- **I-1** Push forzato. In `sentinel._commits`, se `before` non è tutto zeri e non si risolve, oppure non è antenato di `after` (storia riscritta o ramo tornato indietro), `after` è non verificato con il motivo «push forzato: intervallo non calcolabile». Questo dà stato rosso e issue di sentinella, e si aggiunge ai commit di `before..after` quando sono calcolabili. Restano com'erano la prima installazione e `before` tutto zeri. Riscrivi `test_unknown_before_checks_only_after`. Test nuovi: storia riscritta, ramo tornato indietro, `before` assente.
- **I-2** Gli stati sono fidati solo se scritti da `github-actions[bot]` (V6). Usa una costante dedicata, per esempio `ghcli.STATUS_BOT = "github-actions[bot]"`, separata da `BOT_LOGINS`, che resta per i commenti (V1). Usala in `sentinel` e in ogni altro posto che giudica `creator.login` degli stati: cercali con grep, anche in `verdict.py`, `guard.py` e `github.py`. Se tocchi `verdict.py`, limita la modifica a quella costante. Test: `creator.login = "github-actions"` con `success` non verifica un commit.
- **Minori**
  - Gli stati si scrivono prima dell'issue.
  - I comandi `unverified` compaiono nella descrizione di `tollgate/base`, entro 140 caratteri.
  - `GITHUB_REPOSITORY` è richiesto solo con `--publish`.

Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 10, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-10-report.md la sezione «Fix round 1».
