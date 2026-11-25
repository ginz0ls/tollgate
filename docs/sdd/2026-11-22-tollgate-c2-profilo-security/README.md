# Registro dell'esecuzione del piano C2 (profilo `security`)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-22-tollgate-c2-profilo-security.md` (ramo `c2-profilo-security`, 18 commit `7822aed..1517fd3`, unito su `main` il 25 novembre 2026 con l'OK dell'utente in un solo commit, `401cb7e`, come per B3-B8 e C1; 4520 test). Nome utente e host non compaiono (i percorsi sono scritti con `USER`, ripuliti con `evals/scrub.py anonymize`).

- `progress.md`: il ledger. Contiene:
  - la baseline (4349 test su Python 3.11; la corsa su 3.13 fermata, con la ruling);
  - lo scan dei conflitti prima del Task 1 (D1-D14) e le ruling che ne nascono;
  - i 10 task con le revisioni, i giri di correzione (Task 2, 4, 5, 7, 9 e 10, uno ciascuno) e i minori rinviati;
  - le fermate con le risposte dell'utente (`regole`, `revisione finale`, `merge`, `worktree`);
  - le righe `Prova:` della prova reale del Task 9 (passi, costo, segnali, pulizia delle evidenze);
  - le 49 righe `Ruling:` con il costo se sbagliate (dopo il rapporto del merge le decisioni sono righe `Nota:`);
  - la revisione finale con i suoi due giri di correzione, le tre corse finali della suite, il merge.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti. La sonda della tabella delle precedenze sta in `sonda-preflight/` (`rilancia.sh`).
- File dati ai subagenti: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `fatti-verificati.md`, `modelli.md`, `cautele.md`, `plan-path`. Regole di ruolo: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`. `mkbrief.sh` compone il brief di ogni task (testo del task, voci di `carry.md`, cautele).
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-1.md`, `task-N-fix-1.md`; per il Task 5 anche `task-5-fonti-brief.md`, `task-5-fonti.md` (la verifica delle fonti) e `task-5-proposte.md` (i punti di «Da decidere tu» com'erano quando l'utente ha approvato); per il Task 9 `task-9-rapporto-brief.md`, `task-9-rapporto-review.md`, `task-9-rapporto-rereview-1.md` e le uscite dei modi dello script (`task-9-*.txt`).
- Prova reale: il rapporto è `docs/verifiche/2026-11-22-c2-prova-flusso.md`, le evidenze sono in `docs/verifiche/evidenze/c2/flusso/`.
- Revisione finale dell'intero ramo:
  - `final-review-brief.md` e `final-review.md`, la revisione Fable: 0 critical, 1 important (F1), 4 minor, due rilievi portati all'utente (U1, U2), e il triage dei 36 minori rinviati (3 da correggere, 24 nessuna azione, 9 rinviati); le sonde in `sonda-finale/`;
  - `final-fix-brief.md`, `final-fix-2.md` e `final-fix-report.md`, i due giri di correzione;
  - `final-rereview.md` e `final-rereview-2.md`, le ri-revisioni Fable: alla fine 0 critical e 0 important aperti.
- `rapporto-merge.md`: il rapporto all'utente prima del merge.
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` (python3.11 e python3).

Non sono stati copiati:
- i pacchetti di revisione (`.diff`, si rigenerano con `git diff`);
- i log delle corse della suite (i loro esiti sono nel ledger);
- `fonti/` (le copie e le schede delle fonti di `rules-security`: non entrano mai in git; l'elenco delle fonti è in `docs/profili/verifiche/security-fonti.md`);
- gli elenchi di `/tmp` prima e dopo le corse finali (nomi di cartelle di altre sessioni).
