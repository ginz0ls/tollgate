# Registro dell'esecuzione del piano B8 (eval e chiusura di B)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-18-tollgate-b8-eval-chiusura.md` (ramo `b8-eval-chiusura`, 35 commit `8cbf5b5..7dfee80`, unito su `main` il 20 novembre 2026 con l'OK dell'utente in un solo commit, `3733953`, come per B3-B7; 4180 test). Nome utente e host non compaiono (i percorsi sono scritti con `USER`, ripuliti con `evals/scrub.py anonymize`).

- `progress.md`: il ledger. Contiene:
  - la baseline (4062 test) e lo Step 0 del Task 1 (fatti degli involucri dell'ambiente e della CLI di Supabase);
  - lo scan dei conflitti prima del Task 1 (D1-D17);
  - gli 8 task con i giri di correzione;
  - le due sonde dal vivo (righe `Sonda:`) e i difetti che hanno trovato: il redirect contato come lettura, la pulizia che si rompeva, la pagina dei modelli di Gemini spostata, l'anonimizzazione incompleta;
  - il limite della sandbox di Claude Code 2.1.328 sui commit negli eval;
  - i 16 eval (righe `Eval `) e la fermata su s12 con la scelta dell'utente («Lascia così», 19 novembre 2026);
  - le 47 righe `Ruling:` con il costo se sbagliate, i minori rinviati;
  - la revisione finale e il suo giro di correzione, le tre corse finali della suite, il merge.
- `carry.md`: le decisioni del controller portate nei singoli task, comprese quelle nate dalla sonda e dagli eval per il Task 8.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti. Le sonde dello scan stanno in `sonda-preflight/`.
- `task-1-fatti.md`: i fatti delle pagine ufficiali (dotenv-cli, dotenvx, cross-env, env-cmd, Doppler, Infisical, 1Password CLI, CLI di Supabase), con parole nostre.
- File dati ai subagenti: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `fatti-verificati.md`, `cautele.md`, `plan-path`. Regole di ruolo: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`.
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-N.md`. Le prove a secco sono in `task-3-asecco.txt` e `task-4-asecco-s10.txt`.
- Correzioni dopo la sonda (Task 6): `task-6-fix-brief.md`, `task-6-fix-report.md`, `task-6-fix-review.md`, `task-6-fix-rereview-1.md`, `task-6-fix-rereview-2.md`.
- Rapporto degli eval (Task 7): `task-7-rapporto-brief.md`, `task-7-rapporto-report.md`. Il rapporto è `docs/verifiche/2026-11-18-b8-eval.md`, le evidenze sono in `docs/verifiche/evidenze/eval-b8/`.
- Strumenti del controller per controllare le evidenze dopo ogni caso: `check-eval.py`, `check-priv.sh` (`/usr/bin/grep -ra` di nome utente, host e forme di token, senza stamparli), `notes.py`, `probe_r1.py`.
- Revisione finale dell'intero ramo:
  - `final-review-brief.md` e `final-review.md`, la revisione opus: da correggere, con 0 critical, 1 important e 4 minor, e il triage dei 29 minori rinviati (12 da correggere, 14 nessuna azione, 3 rinviati);
  - le sonde in `sonda-finale/`;
  - `final-fix-brief.md` e `final-fix-report.md`, il giro unico di correzione;
  - `final-rereview.md`, la ri-revisione sonnet: 16 punti su 16 indirizzati, con le sonde in `sonda-rerev/`;
  - `final-commits.txt`.
- `rapporto-merge.md`: il rapporto all'utente prima del merge.
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` (python3.11 e python3).

Non sono stati copiati:
- i pacchetti di revisione (`.diff`, si rigenerano con `git diff`);
- i log delle corse della suite e degli eval (i loro esiti sono nel ledger);
- la copia del database della prima sonda (`sonda-db/`, mai ripulita);
- la cartella vuota delle evidenze grezze;
- gli elenchi di `/tmp` prima e dopo le corse (nomi di cartelle di altre sessioni).
