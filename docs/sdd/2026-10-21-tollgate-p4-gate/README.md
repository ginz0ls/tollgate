# Registro dell'esecuzione del piano P4

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-10-21-tollgate-p4-gate.md` (ramo `p4-gate`, unito su `main` in fast-forward; 2465 test).

- `progress.md`: il ledger. Contiene i 17 task completati con i giri di correzione (il Task 16 fino al giro 5, più una correzione mirata oltre il breaker), le 75 righe `Ruling:` (decisioni prese durante l'esecuzione, con il costo se sbagliate), le 58 righe dei minori rinviati, la revisione finale e le tre corse della suite.
- `carry.md`, `task-N-carry-extract.md`: le decisioni del controller portate nei singoli task (dallo scan pre-flight, dalle verifiche V1-V9 e dalle revisioni).
- `preflight-scan.md`: l'analisi dei conflitti del piano (D1-D21) prima del Task 1.
- `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `cautele.md`: le parti del piano e del brief date ai subagenti.
- `task-N-fixR.md`: le richieste dei giri di correzione; `task-16-rapporti.md` quella dei rapporti della prova reale.
- `final-review.md`: la revisione finale dell'intero ramo (opus: 0 critical, 1 important, 9 minor; `final-review-commits.txt` l'elenco dei commit); `final-fix.md` e `final-fix-report.md` il giro unico di correzione (I-1, M-2, M-6, M-7, M-8, limiti M-1, M-3, M-4 in spec 1.2); `final-rereview.md` la ri-revisione.
- `task-N-brief.md` / `task-N-report.md`: il testo di ogni task e il report dell'implementatore, con i giri di correzione; `task-N-review.md` / `task-N-rereview-*.md` le revisioni.
- Gli esiti del Task 1 sono in `docs/verifiche/2026-10-21-p4-verifiche.md`; quelli del Task 16 in `docs/verifiche/2026-10-21-p4-prova-gate.md` e `docs/verifiche/2026-10-21-p4-prova-flusso.md`, con le evidenze in `docs/verifiche/evidenze/gh-p4/`.
- Gli altri file sono le regole date ai subagenti.

I pacchetti di revisione (`.diff`) e i log della suite non sono stati copiati: si rigenerano con `git diff` e `tests/run`.
