# Task 8, Step 2-3: report

Status: DONE. Commit 09396ba (ramo b5-profilo-backend).

## Sostituzioni nelle evidenze (docs/verifiche/evidenze/b5/flusso/)
- Righe `init` degli stream tolte: 1 per passo (2 in tutto). Righe `SessionStart` di altri plugin tolte: 12 nel passo 1, 10 nel passo 2 (resta la coppia di tollgate nel passo 2, hook_id f58dbbe7). JSON valido riga per riga.
- Id di sessione: 217 occorrenze -> SESSIONE-1, 281 -> SESSIONE-2.
- Percorso del checkout assoluto nelle intestazioni (comandi-modello.txt, togli-pagine.txt): 4 occorrenze -> percorso relativo.
- `/home/<utente>` -> `/home/USER`: 0 residue dopo la tolta di init e del percorso checkout; nome utente: 0 residue; host -> HOST: 18 occorrenze (events.jsonl, eventi-ricerca.jsonl).
- Non toccato: togli-pagine (nessuno stream riscritto nel contenuto); evidenze B1-B4.

## Grep di controllo (tutti 0)
nome utente, host, `/home/` diverso da `/home/USER`, `sk-ant`, `ghp_`, `github_pat_`, `vercel_`, id di sessione reali, MEGA/sainapse/ginz0ls, `.claude/plugins`, `.claude/projects`. Le sequenze lunghe residue sono slug di percorsi, SHA di git e trattini.
Nomi di plugin di terzi: restano solo `superpowers:writing-plans` (nome usato dal modello) e `docs/superpowers/...` (cartelle del progetto) e un `context7:` nel testo della skill di tollgate.

## Test
`python3.11 -B -m unittest tests.test_b1_scripts tests.test_docs` e lo stesso con `python3`: 98 test OK entrambi (compreso test_committed_evidence_has_no_long_web_results).

## Fatti nuovi dal lavoro sugli stream
- Gli id `R-BACKEND-01..12` compaiono nel passo 1 solo nella lettura del `tollgate.toml` (elenco `rules` senza testo); non nel piano, né nel testo del task, né nel brief del revisore. Il revisore ha citato da sé R-BACKEND-01, 02, 03, 04, 05, 09, 10, 11, 12.
- Il report dell'implementatore ha dichiarato senza che il task lo chiedesse: contratti (assenti), indirizzo ufficiale, nessun campo tolto, nessun input, prova locale non necessaria.
- Il riepilogo finale del passo 2 dice che M2 non è nel piano, ma task-1.md la elenca: imprecisione del modello, riportata come scostamento minore.
- Durate: passo 1 80 s, passo 2 126 s.

## Dubbi
Nessuno. Il commit contiene solo il rapporto e `evidenze/b5/flusso/`; nessun `__pycache__`. La suite completa non è stata lanciata (nessun codice cambia).
