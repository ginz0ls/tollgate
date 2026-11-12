# Report Task 7 (caso frontend della prova reale)

Commit: 22dac03

## Implementato
- `spikes/run-b1-flow.sh`: valore `frontend` di B1_FLOW_CASE (commento, OUT b6/flusso, PROJ/PROJ_FILES/PLAN_REL/ISSUE_TITLE, PROFILE_AREA=frontend con web/index.html, DISALLOWED con i programmi di backend più vite, next, tsc, eslint, vitest, playwright, chromium, chromium-browser, google-chrome, firefox e, in un ciclo a parte, python3/python -m http.server, tutti nelle quattro forme; messaggio di die; testo di controlla; api_status; limiti; regex dei comandi rischiosi con `-m http.server`).
- `spikes/b1/flowreg.py`: titolo `# Regole frontend (versione 1)` in AREA_TITLES.
- `spikes/b6/flow/`: progetto di prova (solo testo, nessun package.json), issue-1.md e piano-L1.md senza i termini vietati.
- `tests/test_b1_scripts.py`: src_repo con `frontend` e `frontend_approved`, 12 test nuovi (con sotto-casi), tra cui il caso http.server.

## RED
Comando: `python3 -B -m unittest -k frontend tests.test_b1_scripts`
Esito: Ran 12 tests, FAILED (failures=19, errors=3); elenco in `task-7-red.txt` (die: "i valori ammessi sono b1, ai, infra e backend", progetto assente).

## GREEN
- Stesso comando dopo la modifica: Ran 12 tests, OK. P9 dal vivo confermato: `[profiles.frontend]` con `**/*.tsx`, `/web/**`, `src/components/**`, nessun `[profiles.backend]`.
- `python3 -B -m unittest tests.test_b1_scripts`: Ran 110 tests, OK. `bash -n spikes/run-b1-flow.sh`: ok.
- Suite: `suite-task-7.log`: Python 3.11.16 e 3.13.5, 3894 test ciascuno, OK, `exit 0`.

## Scostamenti dal piano
- `registra` cerca `-m http.server` (regex più precisa di `http.server`, per non segnalare file con quel nome).
- Nessun `web/app.js` nel progetto di base: lo crea il lavoro L1.

## Dubbi
Nessuno. Lo script non è stato eseguito oltre `bash -n`, `controlla` e i test.

## Fix round 1
- Rinominati `test_real_scrivi_limiti_heading_is_generic_frontend` e `..._backend` (leggono i file veri).
- Limiti: la frase sui file .ts e sul test della rotta è solo del caso backend.
- `registra`: regex `^bash( \(subagente\))?: .*http\.server`; test con `-mhttp.server`, `python3 -B -m http.server`, `python3.11 -m http.server 8000`, `python3 -c "import http.server..."`; riga nuova in `scrivi_limiti` per il caso frontend.
- Test: `python3 -B -m unittest tests.test_b1_scripts` 110 OK; `bash -n` ok; suite (`suite-task-7-fix1.log`) 3.11 e 3.13 OK, exit 0. Commit d61f7e6.
