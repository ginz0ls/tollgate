# Registro dell'esecuzione del piano C1 (tracciamento locale)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md` (ramo `c1-tracciamento-locale`, 16 commit `055dc80..4cf5824`, unito su `main` il 22 novembre 2026 con l'OK dell'utente in un solo commit, `e0929a8`, come per B3-B8; 4349 test). Nome utente e host non compaiono (i percorsi sono scritti con `USER`, ripuliti con `evals/scrub.py anonymize`).

- `progress.md`: il ledger. Contiene:
  - la baseline (4180 test su Python 3.11; la corsa su 3.13 fermata, con la ruling);
  - lo scan dei conflitti prima del Task 1 (D1-D21) e le ruling che ne nascono;
  - i 10 task con le revisioni, i giri di correzione (Task 5 e Task 7, uno ciascuno) e i minori rinviati;
  - le righe `Prova:` della prova reale del Task 9 (passi, taglia, costo, fotografia, pulizia delle evidenze);
  - le 44 righe `Ruling:` con il costo se sbagliate;
  - la revisione finale e il suo giro di correzione, le tre corse finali della suite, il merge.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti. Le sonde dello scan stanno in `sonda-preflight/`.
- File dati ai subagenti: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `fatti-verificati.md`, `cautele.md`, `plan-path`. Regole di ruolo: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`. `mkbrief.sh` compone il brief di ogni task (testo del task, voci di `carry.md`, cautele).
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-1.md`; per il Task 9 anche `task-9-rapporto-review.md` (la revisione del rapporto della prova).
- Prova reale: il rapporto è `docs/verifiche/2026-11-20-c1-prova-flusso.md`, le evidenze sono in `docs/verifiche/evidenze/c1/flusso/`.
- Revisione finale dell'intero ramo:
  - `final-review-brief.md` e `final-review.md`, la revisione opus: 0 critical, 0 important, 6 minor (F1-F6), un punto da verificare dal vivo (V1), e il triage dei 39 minori rinviati (26 da correggere, 2 rinviati, 11 nessuna azione); la sonda in `sonda-finale/`;
  - `final-fix-brief.md` e `final-fix-report.md`, il giro unico di correzione;
  - `final-rereview.md`, la ri-revisione sonnet: tutti i rilievi indirizzati.
- `rapporto-merge.md`: il rapporto all'utente prima del merge.
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` (python3.11 e python3).

Non sono stati copiati:
- i pacchetti di revisione (`.diff`, si rigenerano con `git diff`);
- i log delle corse della suite e dei passi della prova (i loro esiti sono nel ledger);
- gli elenchi di `/tmp` prima e dopo le corse finali (nomi di cartelle di altre sessioni).
