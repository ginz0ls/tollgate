# Registro dell'esecuzione del piano B5 (profilo `backend`)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md` (ramo `b5-profilo-backend`, 13 commit `0854ad6..8cae7d2`, unito su `main` il 10 novembre 2026 con l'OK dell'utente in un solo commit, `525d8d8`, come per B3 e B4; 3760 test). Nome utente e host sono anonimizzati (`USER`, `HOST`).

- `progress.md`: il ledger. Contiene la baseline (3668 test), lo Step 0 del Task 3 (pagine ufficiali e copie locali delle fonti, fatto in anticipo), lo scan dei conflitti prima del Task 1 (decisioni D1-D14), i 9 task con i giri di correzione, la verifica delle fonti e la loro applicazione, l'approvazione di `rules-backend` da parte dell'utente («Approvo tutto», 10 novembre 2026), la prova reale, le 35 righe `Ruling:` con il costo se sbagliate, i minori rinviati, la revisione finale con la scelta dell'utente su I-1 («Correggi»), il giro di correzione finale, le tre corse finali della suite, il merge.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti del piano.
- File dati ai subagenti: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `fatti-verificati.md`, `cautele.md`, `plan-path`; regole di ruolo `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`.
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-1.md`.
- Verifica delle fonti di `rules-backend` (Task 4, Step 1): `task-4-fonti-brief.md` e `task-4-fonti.md` (verificatore Explore sonnet: regole 29 righe, 27 ok e 2 no; pattern 6 righe, 4 ok e 2 no per larghezza, tenuti come scelta dell'utente; marcatori 17 righe, 16 ok e 1 no; esclusione ok). Le copie delle fonti (`fonti/backend/`) non sono nel repo.
- Prova reale (Task 8): `task-8-rapporto-brief.md`, `task-8-report.md`, `task-8-review.md`; rapporto in `docs/verifiche/2026-11-09-b5-prova-flusso.md`, evidenze in `docs/verifiche/evidenze/b5/flusso/`.
- Revisione finale dell'intero ramo: `final-review-brief.md` e `final-review.md` (opus: non pronto, 0 critical, 1 important, 2 minor, con il triage dei 33 minori rinviati: 9 da correggere, 18 nessuna azione, 6 rinviati); `final-deferred.md` e `final-rulings.md`; `final-fix-report.md` (il giro di correzione); `final-rereview-1.md` (sonnet: tutti i rilievi indirizzati).
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` su `8cae7d2` (python3.11 e python3), nessuna cartella nuova in `/tmp`.

Non sono stati copiati: i pacchetti di revisione (`.diff`, si rigenerano con `git diff`), i log delle corse della suite e dei passi della prova, le copie delle fonti (`fonti/backend/`, testo di terzi) e l'elenco di `/tmp` prima delle corse.
