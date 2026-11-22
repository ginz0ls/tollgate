# Task 9 (Step 1-2): report dell'implementatore

## Implementato
- `spikes/b1/flowreg.py`: comando `eventi-c1 <events.jsonl>` (stampa i soli `size_decided` con `data` intero, `cost` con `data` ridotto a `tokens` e chiavi ordinate di `by_model`, `ruling` con `data` intero). `WANTED` ed `eventi` invariati.
- `spikes/run-b1-flow.sh`: `B1_FLOW_EVIDENCE` (validata `^[a-z0-9-]+$`, errore con il nome della variabile) applicata dopo le righe `OUT=` e prima della riga del banco di prova, quindi vince su RULES/CASE e `B1_FLOW_OUT` dei test vince ancora; `registra` scrive `eventi-c1.jsonl` (dopo `eventi`) e `snapshot.json` (`tollgate snapshot` con lo stesso `TOLLGATE_STATE` di `status --json`, nel repo di prova); fallimenti registrati in `fallimenti.txt` come gli altri.
- Test in `tests/test_b1_scripts.py`: `test_registra_lists_c1_events`, `test_flow_registra_writes_c1_files` (fallimenti.txt vuoto, snapshot.json JSON), `test_flow_evidence_out_dir`, `test_flow_evidence_rejects_bad_values` (`../x`, `A`, `a/b`, `x y`), `test_flow_evidence_test_out_still_wins`.

## TDD
- RED: `python3 -B -m unittest tests.test_b1_scripts -k c1_events -k c1_files -k flow_evidence` -> `FAILED (failures=6, errors=1)` (eventi-c1 sconosciuto, `eventi-c1.jsonl` assente, variabile ignorata).
- GREEN: stesso comando -> `Ran 5 tests ... OK`; `python3 -B -m unittest tests.test_b1_scripts` -> `Ran 139 tests ... OK`; `bash -n spikes/run-b1-flow.sh` ok.
- Suite completa: vedi esito in fondo.

## Scostamenti dal piano
Nessuno. Nessun file nuovo (nessun `git add` necessario). Mai lanciati `claude`, `prepara`, `passo1/2` veri (i test usano il claude finto del banco), rete, `gh` vero, stato della macchina.

## Dubbi
Il riepilogo `controlla` e l'intestazione dello script non elencano i nuovi file di `registra`; solo la riga d'uso dell'uscita è aggiornata. Nessun altro.

## Suite
`PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 4334 test OK (skipped=13), python3 4334 test OK (skipped=11), exit 0. Commit: vedi git log.

## Step 5
Scritto `docs/verifiche/2026-11-20-c1-prova-flusso.md` (Esito: riuscita; versioni, script e variabili, tabella dei passi con durata, turni e costo da `esito.txt` e riga `result`, taglia, costo, fotografia, `session_start`, 0,93 USD senza addebito, punti non provati: fermate e crescita del `cost` di un subagente ripreso, pulizia delle evidenze solo per ciò che il controller ha controllato). Numeri verificati sulle evidenze (passo1 78 s, 14 turni, 0,39; passo2 75 s, 10 turni, 0,54; token 49528 e 32293, somma 81821). Evidenze non toccate.
Test: `python3 -B -m unittest tests.test_docs` 7 OK. Suite completa (`suite-task-9-rapporto.log`): python3.11 4334 OK (skipped=13), python3 4334 OK (skipped=11), exit 0. Commit: `tollgate C1: prova reale corta`.
