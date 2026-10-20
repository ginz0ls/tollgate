### Task 17: Prova reale del flusso finish → open-pr con `claude -p`

Una sola esecuzione reale del percorso skill → CLI → hook → agenti per la chiusura, su un repo locale. Chiude i rischi che i test non vedono: frontmatter degli agenti nuovi, righe di lancio lette dal modello, atto `finish`, verdetti finali e del verificatore, PR nel finto `gh`.

**Files:**
- Create: `spikes/run-p3b-flow.sh`, `docs/verifiche/2026-10-19-p3b-prova-flusso.md`

**Regole di cautela (vanno nel brief):**
- tutto in `/tmp/tollgate-p3b/flow`, sul modello di `spikes/run-p3a-flow.sh`;
- `TOLLGATE_STATE=/tmp/tollgate-p3b/flow/state` con la sentinella; `TOLLGATE_GH=<worktree>/tests/fakegh.py` con dati che dichiarano l'issue 1 aperta, stato del predefinito `success` e nessuna PR;
- `claude -p --plugin-dir <worktree del ramo> --model sonnet`; mai `claude plugin install`; nessun comando scrive sotto `~/.claude`;
- **nessun push in rete** (decisione 24): `remote.origin.url = https://github.com/prova/flow.git` con `url.<repo nudo locale>.insteadOf`; prima di ogni passo lo script controlla che `git remote get-url --push origin` sia il repo nudo in `/tmp/tollgate-p3b/flow/origin.git`, altrimenti si ferma;
- mai `pkill`, `killall` o `kill` per pattern.

- [ ] **Step 1: Script** `spikes/run-p3b-flow.sh` (`prepara|passo1|passo2|passo3|tutto`). Prepara il repo L1 di P3a e ripete i tre passi di `run-p3a-flow.sh` con `claude -p` (`/tollgate:start #1 L1`, piano copiato e committato, `/tollgate:execute`) fino a «task 1 `done`». Poi, con `--continue`:
  1. `/tollgate:finish` (atto, `finish check`, `review prepare`, revisore finale, verificatore);
  2. se serve, «continua con /tollgate:finish» fino a `finish open-pr`;
  3. `bin/tollgate status` e `bin/tollgate events`.

  Registra stdout, `hooks.log`, eventi e il file dei dati del finto `gh`.
- [ ] **Step 2: Eseguire.** Esito atteso: un ciclo di revisione chiuso `ok` (o `needs_fix` seguito da un task di correzione e da un secondo ciclo), una PR nel finto `gh` con `Closes #1` e il blocco JSON leggibile con `prblock.parse`, fase `pr_open`, ramo spinto sul repo nudo allo SHA di HEAD. Un passo che si ferma si annota con l'evento o il messaggio. Si ripete una volta dopo una correzione **solo** se la causa è un difetto di questo piano, con un commit e un test che lo copre. Un esito non ottenuto si scrive «non riuscito», con la causa. Non si dichiara riuscito ciò che non lo è.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-19-p3b-prova-flusso.md`: versione di `claude`, passi, esito per passo, veti, token (`bin/tollgate stats`), difetti e correzioni, ciò che resta non esercitato (`sync`, `adopt`, L2).
- [ ] **Step 4: Commit** «tollgate P3b: prova reale del flusso di chiusura con claude -p».

---

