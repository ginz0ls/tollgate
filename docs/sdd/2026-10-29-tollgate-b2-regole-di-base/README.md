# Registro dell'esecuzione del piano B2 (regole di base)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-10-29-tollgate-b2-regole-di-base.md` (ramo `b2-regole-base`, unito su `main` in fast-forward fino a `a4742a4` il 1° novembre 2026; 3238 test). Nome utente e host sono anonimizzati (`USER`, `HOST`).

- `progress.md`: il ledger. Contiene:
  - lo scan dei conflitti prima del Task 1, con le decisioni D1-D16;
  - gli 8 task completati, con i giri di correzione e l'approvazione delle regole da parte dell'utente (2026-11-01, con la bozza n. 10 rimessa in forma corretta);
  - le righe `Ruling:`, cioè le decisioni prese durante l'esecuzione, ognuna con il suo costo se sbagliata;
  - i minori rinviati, la revisione finale, la prova reale ripetuta, le tre corse finali della suite.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti del piano.
- File dati ai subagenti:
  - le parti del piano e del brief: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `cautele.md`, `plan-path`;
  - le regole del loro ruolo: `implementer-rules.md`, `reviewer-rules.md` e `rereview-rules.md`.
- Testo, report e revisioni dei task:
  - `task-N-brief.md` e `task-N-report.md`: il testo di ogni task e il report dell'implementatore;
  - `task-N-review.md` e `task-N-rereview-*.md`: le revisioni;
  - `task-4-fonti-brief.md`, `task-4-fonti.md`, `task-5-fonti-brief.md` e `task-5-fonti.md`: la verifica delle fonti delle regole (Task 4) e della regola 10 rimessa (Task 5);
  - `task-7-review-rapporto.md`: la revisione del rapporto della prova reale.
- Revisione finale dell'intero ramo:
  - `final-review-brief.md` e `final-review.md`: la prima revisione (opus: non pronto, 0 critical, 2 important), con il triage dei minori rinviati;
  - `final-deferred.md` e `final-rulings.md`: i minori e le ruling passati al revisore;
  - `final-fix-brief.md` e `final-fix-report.md`: il giro di correzione;
  - `final-rereview-1.md`: la ri-revisione (sonnet);
  - `final-review-2.md`: il secondo verdetto (opus, dopo le correzioni e la prova ripetuta: pronto per il merge, 0 critical, 0 important, 3 minor, rinviati a B3 nel piano principale).
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` su `a4742a4` (python3.11 e python3).
- Dove sono gli esiti:
  - regole: `skills/rules-base/SKILL.md`, pagina per l'utente `docs/profili/base.md`, verifica delle fonti `docs/profili/verifiche/base-fonti.md`;
  - prova reale (due corse): `docs/verifiche/2026-10-29-b2-prova-flusso.md`;
  - evidenze: `docs/verifiche/evidenze/b2/`.

Non sono stati copiati: i pacchetti di revisione (`.diff`, si rigenerano con `git diff`), i log delle corse della suite e `fonti/` (copie dei file sorgente di terzi, citati con versione e sezione nella verifica delle fonti).
