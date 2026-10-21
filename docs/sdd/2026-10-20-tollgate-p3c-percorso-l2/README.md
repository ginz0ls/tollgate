# Registro dell'esecuzione del piano P3c

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md` (ramo `p3c-percorso-l2`, unito su `main` in fast-forward fino a `3aa47c2`; 1753 test).

- `progress.md`: il ledger. Contiene i 15 task completati con i giri di correzione, le 44 righe `Ruling:` (decisioni prese durante l'esecuzione, con il costo se sbagliate), i rilievi minori rinviati e la chiusura. `rulings-so-far.md` raccoglie le stesse decisioni per la revisione finale.
- `carry.md`, `task-4-carry.md`, `task-5-carry.md`: le decisioni del controller portate nei singoli task (dallo scan pre-flight e dalle revisioni).
- `preflight-scan.md`: l'analisi dei conflitti del piano (D1-D20) prima del Task 1.
- `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `cautele.md`: le parti del piano e del brief date ai subagenti.
- `final-review.md`: la revisione finale dell'intero ramo (opus), con il triage dei 41 minori rinviati (`deferred-minors.md`); `final-fix-report.md` le correzioni (giro unico: I-1, righe 18, 38, 40, m-1, m-5, m-6); `final-rereview.md` la ri-revisione.
- `task-N-brief.md` / `task-N-report.md`: il testo di ogni task e il report dell'implementatore, con i giri di correzione; `task-N-review.md` / `task-N-rereview-1.md` le revisioni.
- Gli esiti del Task 1 e del Task 14 sono in `docs/verifiche/2026-10-20-p3c-verifiche.md` e `docs/verifiche/2026-10-20-p3c-prova-flusso.md`.
- Gli altri file sono le regole date ai subagenti.

I pacchetti di revisione (`.diff`) non sono stati copiati: si rigenerano con `git diff`.
