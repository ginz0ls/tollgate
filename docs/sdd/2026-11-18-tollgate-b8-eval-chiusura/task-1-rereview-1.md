# Ri-revisione Task 1, giro di correzione 1

### Verdetti sui rilievi
**`dotenv -- "supabase db push"` (comando interno in una sola parola con spazi) passava senza permesso:** INDIRIZZATO.
`bin/tollgate_analysis/bash.py` (`_loader_candidates`, righe ~1240-1255 del file dopo il diff): se una parola contiene spazi si aggiunge il candidato `" ".join(words)` e, in scansione larga, le posizioni delle parole ri-spezzate. Provato con `bash.parse` + `effect_reason` (script temporaneo, poi rimosso):
- chiedono: `dotenv -- "supabase db push"`, `op run -- "prisma migrate deploy"`, `npx dotenv -- "npm run deploy"`, `dotenv -- jest -t "vercel deploy"` (costo scritto), più varianti: `dotenv -e .env -- ...`, `doppler run -- "..."`, `infisical run -- "..."`, `FOO=1`/`sudo`/`bash -c '...'`/`npx` dentro la parola, `&&` e `;` dentro la parola, `env X=1 "..."`, `cross-env A=1 "..."`, `dotenv -- dotenv -- "..."`, `curl -X POST`, `gh pr create`.
- passano: `dotenv -- "python3 -m unittest"`, `"echo ok"`, `"npm test"`, `pytest -k "a b"`, `python3 -c "print(1)"`, `node "scripts/x y.js"`.
Test `tests/test_bash.py` `test_env_loader_inner_command_in_one_word` copre i casi del rilievo; il report ne nomina il comando (166 test OK, suite `exit 0`).

### Danni nuovi nel diff della correzione
Nessuno. Falso positivo noto e dichiarato: `dotenv -- "python3 -m unittest" -k "supabase db push"` chiede (lato sicuro, stessa famiglia del costo di `jest -t "vercel deploy"`). Il ramo `true=True` aggiunge solo il candidato `" ".join`, senza ri-spezzatura: coerente con il suo scopo.

### Osservazioni fuori ambito
`dotenv -- "./deploy.sh"` passa (nessuno script risolto nel mio sandbox, dipende dal filesystem): non toccato dal diff.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
