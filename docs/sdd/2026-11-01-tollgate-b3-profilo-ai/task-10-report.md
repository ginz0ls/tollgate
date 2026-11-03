# Report Task 10 (rapporto della prova reale)

Status: DONE. Commit: vedi `git log` del ramo b3-profilo-ai ("tollgate B3: prova reale corta con il profilo ai").

- Scritto `docs/verifiche/2026-11-01-b3-prova-flusso.md` sulla base di `task-10-fatti.md` e delle evidenze.
- Anonimizzazione di `docs/verifiche/evidenze/b3/flusso/`: id di sessione -> SESSIONE-1/SESSIONE-2; /home/<utente> -> /home/USER; nome utente -> USER; host -> HOST; tolte 13 righe (passo 1) e 11 (passo 2) di init e SessionStart di altri plugin (resta la coppia di tollgate nel passo 2); intestazione di comandi-modello.txt resa relativa; tre segnaposto di esempio di pagine pubbliche (prefisso di chiave, Bearer) neutralizzati; JSON ancora valido.
- Controlli con grep -rI su evidenze/b3 e rapporto: nome utente 0, host 0, /home/ non-USER 0, prefissi di token (sk- fuori da parole, ghp_, github_pat_, Bearer ) 0.
- Test: python3 -B -m unittest tests.test_b1_scripts tests.test_docs, con python3.11 e python3: 62 test, OK.
- Nessuna rete, nessun claude/gh vero, nessun accesso a ~/.claude.
- Dubbio: nessuno. Nota: nel nome del rapporto la data è quella del piano (2026-11-01), la prova è del 2026-11-02.

## Fix round 1
Solo documentazione nel rapporto: (a) riga di limiti sul rischio `ai/summary.py:14` (`content[0].text` con thinking adattivo), progetto non toccato; (b) nell'anonimizzazione, `/tmp/claude-1000` e gli id di hook e messaggi restano perché non identificano l'utente; (c) ID del modello `claude-sonnet-5-5` da `modelUsage` dell'evento `result` di entrambi i passi (l'`init` era stato tolto). Test: `python3.11 -B -m unittest tests.test_docs` e `python3 -B -m unittest tests.test_docs` OK. Controllo nome utente/host nel rapporto: 0.
