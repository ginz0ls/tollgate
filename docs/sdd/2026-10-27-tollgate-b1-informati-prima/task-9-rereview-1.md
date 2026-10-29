# Ri-revisione giro 1, Task 9 Step 1 (db7cd80..b39deaa)

Letti: regole, cautele, revisione, report (Giro 1), diff, `flowreg.py` e `rot`. Eseguiti solo `bash -n spikes/run-b1-flow.sh` (ok) e `python3 -B -m unittest tests.test_b1_scripts` (36 test OK). Simulata la `tar` della copia in lettura (scratchpad): contiene agents bin .claude-plugin evals gate .gitignore hooks LICENSE LICENSES README.md skills statusline templates.

### Verdetti sui rilievi
- **I1 tetto di 3 tentativi su tutta la prova**: INDIRIZZATO. `tentativi_fatti` (run-b1-flow.sh:81-85) conta `tentativo-*` di `<passo>/` e `<passo>.prev-*/`; `claude_step` rifiuta se >= 3 prima di `valida_copia` e di `claude`, e numera fatti+1 (nessun nome ripetuto). Test: tetto dopo `prepara` (test_b1_scripts.py ~:700) e `test_flow_attempt_cap_counts_moved_attempts_in_two_folders` (2+1 tra due cartelle, passo2 con tetto proprio).
- **I2 Grep sommati**: INDIRIZZATO. Una sola chiamata `flowreg.py comandi "${files[@]}"` (registra), un solo blocco "# strumenti del modello"; `_count` somma (flowreg.py:78-83). Test `test_flow_registra_sums_greps_over_attempts_and_steps`: 2+0+7 = 9, un solo blocco, letture registrate sommate. Prefissi `Grep: ` e `read: ` non collidono con altre righe (i comandi sono `bash:`/`grep:`, le righe dei lookups cominciano per id).
- **I3 copia per esclusione**: INDIRIZZATO. `tar --anchored --exclude=./.git ./.github ./.claude ./.superpowers ./docs ./spikes ./tests --no-anchored --exclude=__pycache__ -cf - .` dentro `$PLUGIN`, che `verifica_radice` ha già confinato sotto `/tmp/tollgate-b1/`. Esclusi .git (anche come file del worktree), .claude, .superpowers; presenti evals e LICENSES. Test: percorso `experimental.evals` esiste, presenze e assenze elencate.
- **Minor, test PATH e variabili del gh finto**: INDIRIZZATO (`test_flow_claude_gets_the_fake_gh_first_in_path`: PATH con ghbin per primo, `TOLLGATE_GH`, `TOLLGATE_FAKEGH_DATA`).
- **Minor, `timeout -k`**: INDIRIZZATO (`KILL_AFTER`, default 60; regex nel test statico).
- **Minor, `registra` scrive i fallimenti ed esce != 0 dopo aver raccolto il resto**: INDIRIZZATO (`fallimenti.txt`, `fallisce`, `return $rc`; test con DB corrotto verifica uscita != 0 e file raccolti).
- **Minor, `limiti.txt` con le scappatoie dei prefissi**: INDIRIZZATO (`scrivi_limiti`, test su due frasi).

### Danni nuovi nel diff della correzione
- Minor, run-b1-flow.sh:152: con l'elenco nero la copia include anche file non versionati o ignorati nella radice del repo (oggi non ce ne sono: `git status --ignored` mostra solo `.superpowers/`, già escluso; un futuro `.env` o `.tollgate-test-home-*` in radice finirebbe nella copia, sempre sotto `/tmp/tollgate-b1/`). Rischio basso; si può aggiungere `--exclude=./.env*` o dichiararlo in `limiti.txt`. Non blocca.
- Minor, `fallisce` non copre `claude --version`, `grep` e `comandi-rischiosi`: accettabile (la `grep` senza match esce 1 per natura).

### Osservazioni fuori ambito
Nessuna.

### Dubbio dell'implementatore (`registra` legge solo la preparazione corrente)
Va bene così e non contraddice I2. Dopo `prepara` cambiano stato, DB e repo: sommare i Grep delle `passo*.prev-*` con i `lookups` del DB nuovo confronterebbe dati di prove diverse. I2 chiede la somma su tentativi e passi della stessa preparazione, ed è soddisfatta. I `registro-N` precedenti non si ruotano né si cancellano, quindi il conto della prova vecchia resta nelle sue evidenze; il tetto (I1) invece vale su tutta la prova. È dichiarato in `limiti.txt`.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
