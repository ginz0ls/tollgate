# Revisione Task 3 (6d7f81e)

Controlli propri: `python3 -B -m unittest tests.test_bash` (79 test OK) e una scansione di circa 40 comandi dati solo a `bash.parse` / `effect_reason` (nessun programma vero). Un primo giro con annidamento a 40 livelli è stato ucciso per colpa del mio `shlex.quote` (cresce in modo esponenziale), non del codice; rifatto a 5 livelli, risultato corretto.

### Aderenza
- ✅ `launcher_candidates` (bash.py:1026-1042) segue la decisione 17: solo `basename(argv[0])` in `LAUNCHERS`; normalizzazione (`--x=v`, suffisso `@versione` non sulla `@` iniziale, ultimo pezzo solo per `.bin/`, `PACKAGE_PROGRAMS`); candidato `[programma]+resto` per ogni `i>=1`; veto dopo un token grezzo di `PACKAGE_COMMANDS` che segue un gestore normalizzato, anche annidato (`npx pnpm add vercel` → None, verificato).
- ✅ `PACKAGE_COMMANDS` contiene le 24 voci della decisione 17 più le 13 di D13 (bash.py:1001-1005); guardie `npm search vercel` / `npm explain vercel` nel test (test_bash.py, `test_launcher_without_effect_passes`).
- ✅ Quattordici voci Wrangler + `pages publish` (D13) + `docker image push` / `docker compose push` (D3) in `_DEFAULT_EFFECTS` (bash.py:984-1000); `_TEXT_EFFECTS` le eredita; `versions upload`, `versions secret put`, `pages dev`, `deployment list` restano None (testato e riverificato).
- ✅ `[external_effects] allow`/`commands` restano sul testo dell'intero comando (bash.py:1142-1146, invariati e prima dei candidati). `project_scripts`, `curl`, `wget`, `gh` restano sull'`a` originale.
- ✅ `-c`, `--call`, `--call=`: solo il testo di quel token (bash.py:1068-1075, 1155-1167). Ricorsione su `parse` + `effect_reason`; `BashParseError` → `text_effect`, che non solleva. Verificati: `npx -c`, `--call` senza valore, `npx -c ''`, `-c "("`, `$(…)`, `-c` ripetuto, annidamento a 5 livelli: nessuna eccezione, nessun ciclo (ogni livello lavora su un testo più corto, quindi termina).
- ✅ Strati: nessun import nuovo in `tollgate_analysis` (usa solo `os`, già presente). Nessun messaggio nuovo in `bin/` (D15). Nessuna operazione in `_OPS`, nessun evento nuovo. `bash.is_claude` intatto. Unico chiamante esterno: `bin/tollgate_checks/effects.py:127`, firma invariata.
- ✅ Comandi che non erano effetti e lo diventano: solo quelli voluti dalla decisione 17 (programma di servizio dietro un lanciatore, comandi locali di Supabase/vercel, valori uguali a un servizio come `npx vitest run vercel`, `npm run build -- --env=vercel`, `npm cache clean vercel`) e le voci Wrangler/Docker nuove. Per un comando senza lanciatore `launcher_candidates` dà `[]`, quindi nessuna regressione.
- ⚠️ La suite completa (3589 test, due interpreti) è nel report, non rilanciata.

### Punti di forza
- Il ciclo `for argv in [[base]+a[1:]] + launcher_candidates(a)` unifica argv e candidati senza duplicare la logica Supabase.
- Test ampi e fedeli al brief, con helper `check_effects` che stampa comando e motivo in caso di fallimento.
- Nessun `os.environ` nelle asserzioni; solo testo dato a `parse`.

### Rilievi
Critical: nessuno.
Important: nessuno.

Minor / note (nessuna da correggere nel task):
1. bash.py:1001-1005 + 1038-1040 — le voci D13 `docs`, `config`, `help`, `repo`, `home`, `patch` allargano il buco già dichiarato «valore d'opzione uguale a un comando dei pacchetti»: `pnpm --filter docs exec wrangler deploy`, `yarn workspace docs wrangler deploy`, `pnpm -C docs wrangler deploy` danno None (verificato). `docs` e `config` sono nomi di workspace molto comuni. È coperto dalla riga di D13 («restano aperti … cartelle o pacchetti con quel nome»); da dire con questa esemplificazione nella pagina del Task 5 e nel piano principale (Task 10).
2. `docker compose -f a.yml push` e `npx wrangler --env prod deploy` danno None; il secondo è dichiarato, il primo non è nell'elenco dei buchi di D3 (nomina `buildx build --push`, `build --push`, `--context`). Aggiungerlo all'elenco dei buchi nel Task 10.
3. Mancano test di sola regressione per `[external_effects] commands` con un lanciatore e per `curl`/`gh` sull'argv originale; il comportamento è corretto per lettura del codice (bash.py:1144-1146, 1171+), ma non è bloccato da un test.
4. Falsi positivi minori rimasti, in linea con il costo dichiarato: `npm cache clean vercel`, `npm run docker push`, `npm test -- -c vercel`.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** implementazione fedele alla decisione 17 e alle voci D3/D13, gestione di `-c` sicura (nessuna eccezione né ciclo), nessuna regressione fuori dai lanciatori; restano solo note sui buchi già dichiarati da documentare meglio.
