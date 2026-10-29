# Registro dell'esecuzione del piano B1 («informati prima»)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-10-27-tollgate-b1-informati-prima.md` (ramo `b1-informati-prima`, unito su `main` in fast-forward fino a `6b4fd3d` il 29 ottobre 2026; 3166 test).

- `progress.md`: il ledger. Contiene:
  - i 10 task completati, con i giri di correzione;
  - le 47 righe `Ruling:`, cioè le decisioni prese durante l'esecuzione, ognuna con il suo costo se sbagliata;
  - le 44 righe dei minori rinviati, con il loro triage;
  - la revisione finale, la prova reale ripetuta, le tre corse della suite (normale e con `-W error::ResourceWarning`, su python3.11 e python3), il merge, la CI rossa al primo push (file non chiusi in due script di prova, visibili solo con `PYTHONWARNINGS`) e la correzione, con la CI verde.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-scan.md`: l'analisi dei conflitti del piano fatta dopo il Task 1 e prima del Task 2.
- File dati ai subagenti:
  - le parti del piano e del brief: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `cautele.md`;
  - le regole del loro ruolo: `implementer-rules.md`, `reviewer-rules.md` e `rereview-rules.md`.
- Testo, report e revisioni dei task:
  - `task-N-brief.md` e `task-N-report.md`: il testo di ogni task e il report dell'implementatore;
  - `task-N-review.md` e `task-N-rereview-*.md`: le revisioni;
  - `task-1-review-rapporto.md`, `task-1-rereview-rapporto.md` e `task-9-review-rapporto.md`: le revisioni dei rapporti delle verifiche e della prova reale.
- Revisione finale dell'intero ramo:
  - `final-review.md`: la prima revisione (opus: 0 critical, 2 important, 8 minor nuove), con il triage dei minori rinviati;
  - `final-deferred.md`, `final-copertura.md` e `final-rulings.md`: i minori, la tabella di copertura e le ruling passati al revisore;
  - `final-fix-brief.md` e `final-fix-report.md`: il giro di correzione;
  - `final-rereview-1.md`: la ri-revisione (sonnet);
  - `final-review-2.md`: il secondo verdetto (opus, dopo le correzioni e la prova ripetuta: pronto per il merge, 0 critical, 0 important, 3 minor).
- Dove sono gli esiti:
  - verifiche del Task 1: `docs/verifiche/2026-10-27-b1-verifiche.md`;
  - prova reale (due corse): `docs/verifiche/2026-10-27-b1-prova-flusso.md`;
  - evidenze: `docs/verifiche/evidenze/b1/`.

I pacchetti di revisione (`.diff`) non sono stati copiati: si rigenerano con `git diff`.
