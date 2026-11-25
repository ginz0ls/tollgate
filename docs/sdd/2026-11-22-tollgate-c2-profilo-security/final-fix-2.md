# Giro di correzione 2 dopo la revisione finale (due rilievi della ri-revisione)

La ri-revisione del giro (`final-rereview.md`) ha chiuso tutti i rilievi della revisione finale e ha trovato due danni nuovi nel giro stesso. Leggili per intero in `final-rereview.md` (sezione «Danni nuovi nel diff della correzione»).

## Mano Fable: solo `docs/profili/database.md` (nessun commit, nessuna suite)
- **D1 (Important)**, riga 109 circa: l'esempio `gate = ["db_test"]` fa girare il test delle policy prima del reset del database. Diventa: «se vuoi un comando anche durante il task, aggiungi anche a `gate` i comandi, nello stesso ordine (per esempio `gate = ["db_reset", "db_test"]`)». Il resto della frase resta. Nient'altro della pagina approvata cambia (la nota di storia del 2026-11-24 c'è già). Verifica: `python3 -B -m unittest tests.test_rules_database tests.test_docs tests.test_manifest`. Report: «## Giro 2, mano Fable» in fondo a `final-fix-report.md` (frase vecchia e nuova, esito dei test).

## Mano opus: dopo la mano Fable (suite e commit)
- **D2 (Minor)**, spec del nucleo (`:507`, `:1147`, `:2348` circa): i comandi di `dod` girano solo con `finish check`; `open-pr` non li esegue, ne ricontrolla le ricevute sul commit. Controlla sul codice (`bin/tollgate_flow/finishcheck.py`, `openpr.py`) e scrivi ciò che vedi, nei tre punti e ovunque la spec, il catalogo o il piano principale dicano che `open-pr` li esegue (cerca). Agenti, pagine e `comandi.md` dicono già solo `finish check`: non toccarli.
- `git add docs/profili/database.md` (la frase della mano Fable, senza cambiarla).
- Verifica: `python3 -B -m unittest tests.test_docs tests.test_manifest tests.test_rules_database tests.test_rules_security`; `claude plugin validate --strict .`. Suite completa con le tre righe (uscita su `suite-final-fix-2.log`), commit nuovo (mai amend) «tollgate C2: correzioni dopo la ri-revisione finale» con le due righe Co-Authored-By (Opus 5.5 e Fable 5.2). Nessun «unita su `main`» per C2. Report: «## Giro 2, mano opus» in fondo a `final-fix-report.md`.
