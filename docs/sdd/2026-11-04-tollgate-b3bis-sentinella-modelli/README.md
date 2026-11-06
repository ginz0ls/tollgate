# Registro dell'esecuzione del piano B3-bis (sentinella dei modelli)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-04-tollgate-b3bis-sentinella-modelli.md` (ramo `b3bis-sentinella-modelli`, 21 commit `b3d1549..ad98f61`, unito su `main` in fast-forward il 6 novembre 2026 con l'OK dell'utente; 3572 test). Nome utente e host sono anonimizzati (`USER`, `HOST`).

- `progress.md`: il ledger. Contiene la baseline, lo scan dei conflitti prima del Task 1 (decisioni D1-D30), lo Step 0 del Task 1 (pagine ufficiali), la pulizia di `/tmp`, gli 8 task con i giri di correzione, l'incidente del Task 4 (un test fallito ha stampato l'ambiente nel terminale di un subagente: nessun file né commit lo contiene), le 37 righe `Ruling:` con il costo se sbagliate, i minori rinviati, la revisione finale, il giro di correzione finale, le tre corse finali della suite.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti del piano.
- File dati ai subagenti: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `fatti-verificati.md`, `cautele.md`, `plan-path`; regole di ruolo `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`.
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-1.md`; `task-6-files.txt` e `task-6-red.txt` (file ripuliti e test rosso della pulizia delle evidenze, solo nomi e lunghezze).
- Pulizia di `/tmp` (Task 7, Step 1): `tmp-prefixes.txt` (prefissi dei temporanei dei test, da `grep`), `tmp-counts.txt` (conteggi per prefisso mostrati all'utente), `tmp-others.txt` (le cartelle `tollgate*` non toccate). In tutto 22.487 cartelle cancellate (21.437 il 4 novembre, 2 sigillate e 1.048 il 5 novembre).
- Revisione finale dell'intero ramo: `final-review-brief.md` e `final-review.md` (opus: non pronto, 0 critical, 1 important, 7 minor, con il triage dei 24 minori rinviati); `final-deferred.md` e `final-rulings.md`; `final-fix-brief.md`, `final-fix-report.md` e `red1.txt` (il giro di correzione); `final-rereview-1.md` (sonnet: 12 punti indirizzati).
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` su `ad98f61` (python3.11 e python3), nessuna cartella nuova in `/tmp`.
- Prova vera: `docs/verifiche/2026-11-04-b3bis-prova-modelli.md`, evidenze in `docs/verifiche/evidenze/b3bis/` (nessuna chiave nell'ambiente: la parte di rete non è provata dal vivo).

Non sono stati copiati: i pacchetti di revisione (`.diff`, si rigenerano con `git diff`), i log delle corse della suite, l'elenco completo delle cartelle cancellate da `/tmp` e gli elenchi di `/tmp` prima e dopo le corse.
