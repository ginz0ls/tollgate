### Task 13: Prova reale del flusso con `claude -p`

Una sola esecuzione reale del percorso skill → CLI → hook → agenti, su un repo locale. Non si usano repo GitHub. Chiude i rischi che i test unitari non vedono: frontmatter, nomi degli agenti, `EnterWorktree`, iniezioni, segnale della CLI.

**Files:**
- Create: `spikes/run-p3a-flow.sh`, `docs/verifiche/2026-10-16-p3a-prova-flusso.md`

**Regole di cautela (vanno nel brief):**
- tutto in `/tmp/tollgate-p3a/flow`;
- `TOLLGATE_STATE=/tmp/tollgate-p3a/flow/state` con la sentinella;
- `TOLLGATE_GH=<repo>/tests/fakegh.py` con dati che dichiarano l'issue 1 aperta e lo stato del predefinito `success`;
- `HOME` resta quella vera (serve l'autenticazione di `claude`), ma nessun comando scrive sotto `~/.claude`;
- `claude -p --plugin-dir <worktree del ramo> --model sonnet`;
- mai `claude plugin install`;
- il repo di prova ha `remote.origin.url = https://github.com/prova/flow.git` e `url.<repo nudo locale>.insteadOf` su quell'URL, come `FlowLab`: il fetch va al repo nudo e `prereq.is_github` legge l'URL grezzo. Nessun push.

- [ ] **Step 1: Script** `spikes/run-p3a-flow.sh`. Prepara:
  - il repo con `tollgate.toml` (L1, `verify = "python3 -m unittest"` con un report JUnit finto, oppure `allow_no_tests` come serve);
  - i 5 workflow vuoti e `.github/tollgate/VERSION`;
  - un piano L1 di un task già scritto in un file fuori dal repo.

  Poi lancia in sequenza, con `--continue`:
  1. `/tollgate:start #1 L1`;
  2. «scrivi il piano copiando <file> in docs/superpowers/plans/2026-10-16-prova.md»;
  3. `/tollgate:execute`.

  Registra stdout e log degli hook (`hooks.log`, eventi del DB con `bin/tollgate events`).
- [ ] **Step 2: Eseguire.** Esito atteso: task 1 `done` e un verdetto `approved` nei `task_change`. Ogni passo che si ferma si annota con l'evento o il messaggio che l'ha fermato. Si ripete una volta dopo una correzione **solo** se la causa è un difetto di questo piano, con un commit di correzione e un test che lo copre. Un esito non ottenuto si scrive «non riuscito», con la causa, e diventa un rilievo per il controller. Non si dichiara riuscito ciò che non lo è.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-16-p3a-prova-flusso.md`: versione, passi, esito per passo, numero di veti e di token (`bin/tollgate stats`), difetti trovati e correzioni.
- [ ] **Step 4: Commit** «tollgate P3a: prova reale del flusso con claude -p».

---

