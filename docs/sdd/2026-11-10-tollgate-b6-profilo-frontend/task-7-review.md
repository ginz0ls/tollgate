# Revisione Task 7 (caso frontend), commit 22dac03

Sola lettura sul pacchetto `review-21244ff..22dac03.diff`, più controlli mirati: `bash -n` (ok), elenco dei file di `spikes/b6/flow/`, `skills/rules-frontend/SKILL.md`, `templates/profiles/frontend.toml`, confronto con il caso `backend`. Nessuna suite lanciata.

### Aderenza
- ✅ Tutti i punti dello script di D8: commento (`run-b1-flow.sh:17-21`), valore predefinito (`CASE=` con l'elenco), `OUT` b6/flusso, `PROJ`/`PROJ_FILES`/`PLAN_REL`/`ISSUE_TITLE`/`PROFILE_AREA`/`PROFILE_FILE`, `DEPLOY_CLIS` e ciclo, `case` e messaggio di `die` (cita tutti e cinque i valori), testo di `controlla`, `api_status`, `scrivi_limiti`, regex di `registra`, commento di `proponi_profilo`. `HOME`, `trascrizioni` e `tipi` erano già generici (`!= b1`). `flowreg.py` ha il titolo frontend.
- ✅ D2: le quattro forme sono generate per `python3 -m http.server` e `python -m http.server` (ciclo a parte, perché due parole). `test_flow_disallows_ui_tools_frontend` copre i programmi di backend, UI e i due `http.server`, e verifica che il caso `backend` non ne abbia.
- ✅ `registra` segnala `http.server`; `test_real_registra_flags_ui_tools_frontend` ha `python3 -m http.server 8000` e `python -m http.server`, più `npx vite`, `chromium --headless x`, `tsc`, `google-chrome`, `env firefox`, `node`; i falsi positivi (`cat web/index.html`, `ls web/vite.config.txt`, `git add web/styles.css`) sono esclusi.
- ✅ `issue-1.md` e `piano-L1.md`: pulsante «Salva» con la sola icona, «Salvato», `src/components/SaveButton.tsx`, test con `html.parser`, «Non si avviano server né browser». Riletti: nessuna delle parole vietate (aria, etichetta, nome accessibile, role, componenti simili, indirizzo, documentazione). Il test con regex a parola intera le cerca davvero, sul testo normalizzato.
- ✅ `home.tsx` ha `from "@tanstack/react-router"` (marcatore del frammento, `templates/profiles/frontend.toml:50-54`); il test lo verifica sul frammento vero e controlla l'assenza di `backend` nel `tollgate.toml` proposto (P9 dal vivo). `frontend.toml` ha `exclude` di `server/`, `api/`, ecc., non di `routes/`: coerente.
- ✅ Nessun `package.json`, `.env*`, `node_modules/`, file Vercel/Wrangler; `.gitignore` con le cinque voci; test dedicato con `rglob`.
- ✅ Comando di verifica `python3 -m unittest discover -s tests -t .`: solo libreria standard; `test_page.py` usa `html.parser`. Eseguito con `-B` dal test e senza `__pycache__` residui.
- ✅ `--disallowedTools` del caso: DEPLOY_CLIS contiene tutti i programmi del test (vite next tsc eslint vitest playwright chromium chromium-browser google-chrome firefox) + i due `http.server`. La precedenza `a || b && c` di `[ backend ] || [ frontend ] && ...` è (a||b)&&c: corretta.
- ✅ Nessun token, nome utente o host nei file nuovi (grep mentale sul diff: solo `prova`, `example.com`).
- ⚠️ Non verificabile dal diff: il comportamento di Claude Code con prefissi di due parole in `Bash(python3 -m http.server:*)` (stesso meccanismo di `Bash(command gh:*)`, ma non provato qui); la reale tenuta della prova sarà vista nel Task 8.

### Punti di forza
- Il caso ricalca `backend` senza duplicare: un ciclo a parte per i comandi a due parole, `registra` con regex distinta e `-m http.server` in qualunque posizione.
- Il test sul testo del compito è a parola intera, insensibile alle maiuscole e senza falsi positivi su «ruolo»/«variabile».
- Il progetto è piccolo, `StatusBadge.tsx` con `role="status"` offre il «componente simile» da trovare senza che il compito lo nomini.
- RED documentato (`task-7-red.txt`), suite verde su 3.11 e 3.13.

### Rilievi

**Critical:** nessuno.

**Important**
1. `tests/test_b1_scripts.py:1816` `test_scrivi_limiti_heading_is_generic_frontend` passa da `frontend_prepara()` → `src_repo(case="frontend")` con i file veri e `spikes/b6/flow/`, ma non ha il prefisso `test_real_` che il brief impone a ogni test nuovo di questo tipo. Il caso `backend` (`:1952`) ha lo stesso difetto, ma è precedente, non una deroga. Correggere: rinominare in `test_real_scrivi_limiti_heading_is_generic_frontend`.

**Minor**
1. `spikes/run-b1-flow.sh`, bullet `(backend, frontend) in più nega supabase, deno e node…`: la seconda frase («I file .ts del progetto… il test della rotta chiama la funzione, senza aprire una porta») per `frontend` è inesatta (i file sono `.tsx`, non c'è una rotta testata; il bullet frontend successivo dice già il vero). Separare la frase, o dirla solo per `backend`.
2. `registra` cerca `-m[[:space:]]+http\.server`, più stretta del `http.server` chiesto da D2 (dichiarato nel report). Lascia fuori `-mhttp.server`, `python3 -c "import http.server…"` e `python3.11 -m http.server` (quest'ultimo preso). Accettabile, ma D2 prevale sul piano: valutare `http\.server` in posizione di comando, o aggiungere la nota ai limiti. Anche `DISALLOWED` non copre `python3 -B -m http.server` né `python3.11`: va detto in `limiti.txt` (ora cita solo `env VAR`, `sudo`, `xargs`, `bash -c`).
3. `test_real_flow_case_frontend_project_verifies` asserisce che il `tollgate.toml` del progetto sia identico a quello di `spikes/b1/flow`: accoppia B6 a B1 senza ragione di prova. Basta controllare `verify` e `allow_no_tests`.
4. `tests/test_b1_scripts.py:~1819` due righe vuote dentro la classe prima di `bash_saved_stream`.

### Valutazione
**Qualità del task:** Da correggere (una correzione di una riga, il prefisso `test_real_`).
**Motivo:** il caso è completo e coerente con D2/D8 e con le lezioni di B4/B5; resta solo la violazione esplicita del prefisso `test_real_` su un test che legge i file veri, più rifiniture dei testi dei limiti e della regex.
