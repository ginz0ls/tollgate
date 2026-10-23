# Task 16 — correzioni dopo la prima esecuzione reale (difetti del piano: commit + test, poi si ripetono solo i casi interessati)

Cautele invariate: solo `bash -n`, `controlla`, test offline con gh finto; mai rete, mai gh vero, mai `claude`, mai ~/.claude/settings.json o ~/.claude/plugins/. Le evidenze in docs/verifiche/evidenze/gh-p4/ NON si toccano (il controller le ha prodotte).

## D-1 — attesa del merge con `attenzione` rossa
Esito reale su GitHub (6 casi: verde-config, verde-ramo-libero, verde-workflow-ci, attenzione-deroga-test, attenzione-piano-testo, attenzione-tetto-livello): con `guard` e `verdict` `success` e `tollgate/attention` `failure` GitHub dà `mergeStateStatus = UNSTABLE` (un controllo non obbligatorio rosso; la PR resta unibile), non `CLEAN`. In `spikes/p4/make_case.py` l'attesa del merge in quei casi diventa `UNSTABLE`, ricavata dalla regola (attention rossa e obbligatori verdi → UNSTABLE), non scritta caso per caso. Test che la regola valga per tutti i casi di `protected` dell'elenco.

## D-2 — `gh pr edit` non funziona con gh 2.46 (Debian)
Esito reale: `gh pr edit 18 --body-file …` → `GraphQL: Projects (classic) is being deprecated … (repository.pullRequest.projectCards)`, uscita 1. È un difetto del prodotto: `bin/tollgate_flow/gh.py:108` usa `gh pr edit` per aggiornare il corpo di una PR esistente (`open-pr` su PR già aperta).
- `bin/tollgate_flow/gh.py`: il corpo si aggiorna con la REST: `gh api --method PATCH repos/{owner}/{repo}/pulls/<n> -F body=@<file>` (`{owner}/{repo}` lo risolve gh, come in `sentinel_issues`; il numero è un intero). Test in tests/ con gh finto che verifichino gli argomenti esatti e che un errore resti un `GhError`. Controlla che `bin/tollgate_analysis/bash.py` e i guardrail non trattino diversamente questa chiamata quando è la CLI a farla (la CLI non passa dagli hook; non cambiare i guardrail del modello).
- `spikes/run-p4-gate.sh`, op `edit` del caso `verde-edit`: stessa chiamata REST.
- `spikes/gh-p4/ghguard.py`: ammessa (scelta dell'utente del 22/10/2026) SOLO questa forma: `api --method PATCH repos/ginz0ls/tollgate-p4-protected/pulls/<intero> -F body=@<file>` con il file nelle cartelle temporanee già ammesse (profilo script) o sotto `$FLOW` (profilo flow); nessun altro campo, nessun altro endpoint, nessun altro repo (detect no). Tutto il resto delle scritture `api` resta rifiutato. Test in test_p4_ghguard (forma ammessa; `-f title=`, secondo campo, `pulls/1/merge`, `issues/1`, detect, `-X PATCH` su altro owner → rifiutati).
- `spikes/gh-p4/flowcheck.py`: SHAPES con la forma REST al posto di `pr edit` (il percorso del corpo come in `openpr.py`).

Commit nuovo «tollgate P4: corpo della PR aggiornato con la REST (gh pr edit rotto con gh 2.46) e attesa UNSTABLE con attenzione rossa (Task 16)» con la riga esatta «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>». Sezione «Correzioni dopo l'esecuzione» nel report.
