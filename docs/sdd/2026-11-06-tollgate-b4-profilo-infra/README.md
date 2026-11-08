# Registro dell'esecuzione del piano B4 (profilo `infra`)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-06-tollgate-b4-profilo-infra.md` (ramo `b4-profilo-infra`, 16 commit `0c15d33..af0b1bb`, unito su `main` il 9 novembre 2026 con l'OK dell'utente in un solo commit, `a1098ea`, come per B3: due commit intermedi del ramo contenevano testo di pagine di terzi nelle evidenze, tolto dalla correzione finale; 3668 test). Nome utente e host sono anonimizzati (`USER`, `HOST`).

- `progress.md`: il ledger. Contiene la baseline (3572 test), lo Step 0 del Task 4 (pagine ufficiali, fatto in anticipo), lo scan dei conflitti prima del Task 1 (decisioni D1-D16), i 10 task con i giri di correzione, la verifica delle fonti e la loro applicazione, l'approvazione di `rules-infra` da parte dell'utente («approva tutto», 7 novembre 2026), la prova reale, le 29 righe `Ruling:` con il costo se sbagliate, i minori rinviati, la revisione finale, il giro di correzione finale, le tre corse finali della suite.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti del piano.
- File dati ai subagenti: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `fatti-verificati.md`, `cautele.md`, `plan-path`; regole di ruolo `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`.
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-1.md`.
- Verifica delle fonti di `rules-infra` (Task 5, Step 1): `task-5-fonti-brief.md` e `task-5-fonti.md` (verificatore Explore sonnet: regole 31 righe, 27 ok e 4 no; pattern 14 righe, 14 ok). Le copie delle pagine ufficiali (`fonti/infra/`) non sono nel repo.
- Prova reale (Task 9): `task-9-rapporto-brief.md`, `task-9-rapporto-report.md`, `task-9-review.md`; rapporto in `docs/verifiche/2026-11-06-b4-prova-flusso.md`, evidenze in `docs/verifiche/evidenze/b4/flusso/`.
- Revisione finale dell'intero ramo: `final-review-brief.md` e `final-review.md` (opus: non pronto, 0 critical, 1 important, 5 minor, con il triage dei minori rinviati); `final-deferred.md` e `final-rulings.md`; `final-fix-brief.md` e `final-fix-report.md` (il giro di correzione); `final-rereview-1.md` (sonnet: tutti i rilievi indirizzati).
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` su `af0b1bb` (python3.11 e python3), nessuna cartella nuova in `/tmp`.

Non sono stati copiati: i pacchetti di revisione (`.diff`, si rigenerano con `git diff`), i log delle corse della suite, le copie delle fonti (`fonti/infra/`, testo di terzi) e l'elenco di `/tmp` prima delle corse.
