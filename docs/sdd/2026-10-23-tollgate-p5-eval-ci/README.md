# Registro dell'esecuzione del piano P5

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-10-23-tollgate-p5-eval-ci.md` (ramo `p5-eval-ci`, unito su `main` in fast-forward fino a `3b5d365` il 26 ottobre 2026; 2897 test).

- `progress.md`: il ledger. Contiene:
  - i 15 task completati, con i giri di correzione;
  - le 81 righe `Ruling:`, cioè le decisioni prese durante l'esecuzione, ognuna con il suo costo se sbagliata;
  - le 45 righe dei minori rinviati;
  - la revisione finale, le tre corse della suite, la CI e il merge.
- `carry.md` e `task-N-carry-extract.md`: le decisioni del controller portate nei singoli task.
- `preflight-scan.md`: l'analisi dei conflitti del piano (D1-D21) fatta prima del Task 1.
- File dati ai subagenti:
  - le parti del piano e del brief: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `cautele.md`;
  - le regole del loro ruolo: `implementer-rules.md`, `reviewer-rules.md` e `rereview-rules.md`.
- Testo, report e revisioni dei task:
  - `task-N-brief.md` e `task-N-report.md`: il testo di ogni task e il report dell'implementatore;
  - `task-N-review.md` e `task-N-rereview-*.md`: le revisioni;
  - `task-14-fix-*`: i giri di correzione degli eval;
  - `task-14-e3-analisi.md` e `task-14-s5-analisi.md`: l'analisi dei due casi sotto soglia al primo giro;
  - `task-15-contesto.md`: il contesto dato al Task 15.
- Revisione finale dell'intero ramo:
  - `final-review-brief.md` e `final-review.md`: la revisione (opus: 0 critical, 0 important, 5 minor);
  - `final-fix-brief.md` e `final-fix-report.md`: l'unico giro di correzione;
  - `final-fix-rereview.md`: la ri-revisione.
- File delle sonde:
  - `*.log`: le sonde del controller (eval, CI, cache e fissaggio su detect);
  - `plugin-eval-help.txt` e `plugin-evals-doc.md`: le fonti su `claude plugin eval`;
  - `ve-analisi.md`: l'analisi delle verifiche VE.
- Dove sono gli esiti:
  - verifiche: `docs/verifiche/2026-10-23-p5-verifiche.md`;
  - prova del gate: `docs/verifiche/2026-10-23-p5-prova-gate.md`;
  - eval: `docs/verifiche/2026-10-23-p5-eval.md`;
  - CI: `docs/verifiche/2026-10-23-p5-ci.md`;
  - evidenze: `docs/verifiche/evidenze/p5/` e `docs/verifiche/evidenze/eval-p5/`.

I pacchetti di revisione (`.diff`) non sono stati copiati: si rigenerano con `git diff`.
