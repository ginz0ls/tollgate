# Task 9 Step 2-3: report

Commit: vedi `git log -1` (messaggio «tollgate B4: prova reale corta con il profilo infra»). File: `docs/verifiche/2026-11-06-b4-prova-flusso.md` e `docs/verifiche/evidenze/b4/flusso/`.

## Sostituzioni (conteggi, mai i valori)
- id di sessione: 227 (SESSIONE-1) + 316 (SESSIONE-2)
- `/home/<utente>` -> `/home/USER`: 14; nome utente -> `USER`: 14 (stesse righe dei percorsi)
- nome host -> `HOST`: 18
- percorso assoluto del worktree (intestazioni di `comandi-modello.txt` e `togli-pagine.txt`): tolto, resta relativo al repo (4 occorrenze)

## Righe tolte
- passo1: 1 `init` + 12 `SessionStart` di altri plugin = 13; passo2: 1 `init` + 10 `SessionStart` = 11 (resta la coppia di tollgate). Come in B3.
- `togli-pagine` non rieseguito: gli stream non erano cambiati nei contenuti da togliere (già 5+3 risultati sostituiti da `registra`).

## Controlli
- grep (nome utente, host, `/home/` diverso da USER, `sk-ant`, `ghp_`, `github_pat_`, token Vercel, Bearer, AKIA, id di sessione reali): 0 in evidenze e rapporto. Le 3 occorrenze di `/home/` nel rapporto sono testo esplicativo.
- `python3 -B -m unittest tests.test_b1_scripts` e con `python3.11`: 77 test OK. `tests.test_docs`: 7 OK su entrambi.

## Note
- Non ho letto variabili d'ambiente né file fuori dal worktree; i valori da sostituire li ho trovati nei file stessi.
- Nel rapporto ho scritto che i 3 avvisi del passo 1 (Actions non leggibili, detect, sentinella assente) vengono dal riassunto finale del modello.

## Fix round 1
- Rapporto: corretta la frase «effetto solo di tempi»; aggiunto ai limiti e allo scostamento che il task dato all'implementatore (piano del modello) chiedeva già le righe del report, e che il segnale forte è il revisore che cita R-INFRA-04/05 da sé. Aggiunte le righe sull'invito `npx` della pagina (non seguito) e sul passo 1 senza `SessionStart` (12 righe di altri plugin tolte da me, tollgate non ne aveva).
- Evidenze: 4 testi di terzi sostituiti col segnaposto di `flowreg` (`[pagina di terzi tolta dalle evidenze: <origine>, <N> caratteri]`): WebSearch (passo1 riga 115, anche `tool_use_result.results`), anteprima persisted-output (passo1 146, passo2 120), lettura pagina salvata (passo1 160, anche `tool_use_result.file`). JSON valido riga per riga (verificato con json.loads).
- Grep (utente, host, `/home/` non USER, sk-ant, ghp_, github_pat_, Bearer, id di sessione): 0.
- `python3 -B -m unittest tests.test_b1_scripts tests.test_docs` e con `python3.11`: 84 test OK ciascuno.
