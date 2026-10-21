### Task 14: Prova reale del percorso L2 con `claude -p`

Una sola esecuzione reale del percorso skill → CLI → hook → agenti in L2, fino all'esecuzione del primo task. Chiude i rischi che i test non vedono: frontmatter degli agenti nuovi, righe di lancio lette dal modello, riga JSON dei giri, atti `approve spec` e `approve plan` digitati in una sessione legata.

**Files:**
- Create: `spikes/run-p3c-flow.sh`, `docs/verifiche/2026-10-20-p3c-prova-flusso.md`

**Regole di cautela (vanno nel brief):**
- tutto in `/tmp/tollgate-p3c/flow`, sul modello di `spikes/run-p3b-flow.sh` (lo script rifiuta un `FLOW` diverso prima di ogni `rm -rf`);
- `TOLLGATE_STATE=/tmp/tollgate-p3c/flow/state` con la sentinella; `TOLLGATE_GH=<worktree>/tests/fakegh.py` con l'issue 1 aperta (`author_association OWNER`), stati del predefinito `success`, nessuna PR;
- `claude -p --plugin-dir <worktree del ramo> --model sonnet`; mai `claude plugin install`; nessun comando scrive sotto `~/.claude`;
- **nessun push in rete** (decisione 23): `remote.origin.url = https://github.com/prova/flow.git` con `url.<repo nudo locale>.insteadOf`; prima di ogni passo lo script controlla `git remote get-url --push origin`;
- **dal passo 2 ogni `claude -p` parte dalla cartella del worktree del lavoro** (sessione nuova, legata da `SessionStart`); lo script verifica che la cartella sia il worktree `tg/1-*` sotto `/tmp/tollgate-p3c/flow` e si ferma altrimenti; mai `--continue` dalla radice;
- mai `pkill`, `killall` o `kill` per pattern.

- [ ] **Step 1: Script** `spikes/run-p3c-flow.sh` (`prepara|passo1|…|libero "<prompt>"|registra|tutto`). `prepara`: repo come P3b (stdlib, `tools/unittest_junit.py`, gate installato) più una spec di prova `spec-L2.md` con una fetta, «Tane di coniglio» con le scelte e «Cosa non fare», e un piano di prova `piano-L2.md` che passa `plan-check` (verificato dallo script). Passi:
  1. dal checkout: `/tollgate:start #1 L2`; dopo il passo lo script controlla che nel ramo non ci sia ancora nessun file sotto `docs/superpowers/specs/` (il modello potrebbe aver avviato il brainstorming e scritto una spec sua: in quel caso si ferma con la nota «rifare il passo 1», perché il «primo file nuovo» sarebbe quella spec);
  2. dal worktree: «la spec è in <file>: copiala in `docs/superpowers/specs/2026-10-20-prova.md` senza cambiarla, committala, poi segui `/tollgate:spec-audit` finché audit prepare non chiede `/tollgate:approve spec 1`»;
  3. dal worktree: `/tollgate:approve spec 1`;
  4. dal worktree: «il piano è in <file>: scrivilo con lo strumento Write in `docs/superpowers/plans/2026-10-20-prova.md` (così passa da plan-check), committalo, poi segui `/tollgate:spec-audit` per l'avversario del piano finché non chiede `/tollgate:approve plan`»;
  5. dal worktree: `/tollgate:approve plan`;
  6. dal worktree: `/tollgate:execute`, fino a «task 1 `done`»;
  7. `registra`: `status`, `events`, `stats`, report in `reviews/1/`, `hooks.log`, dati del finto `gh`.

  `libero "<prompt>"` lancia un prompt dal worktree (per esempio `/tollgate:resolve <id> <nota>` a un tetto, o «continua con /tollgate:spec-audit»).
- [ ] **Step 2: Eseguire.** Esito atteso: almeno un giro `spec-adversarial` chiuso con report in `reviews/1/`, `spec-approval.md` con lo `sha` della spec, fase `plan`, almeno un giro `plan-adversarial`, fase `approval` poi `execution` con `plan_sha` = blob del piano approvato, `plan-approval.md` con `spec_sha`, task 1 `done`. Un passo che si ferma si annota con l'evento o il messaggio. Si ripete una volta dopo una correzione **solo** se la causa è un difetto di questo piano, con un commit e un test che la copre. Un esito non ottenuto si scrive «non riuscito», con la causa; un esito ottenuto in più tentativi si dichiara composito. Non si dichiara riuscito ciò che non lo è.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-20-p3c-prova-flusso.md`: versione di `claude`, sessioni reali (id e cartella di ogni passo), passi ed esiti, veti, giri e loro esiti, token (`bin/tollgate stats`), difetti e correzioni, ciò che resta non esercitato (audit a lenti, `reopen`, `--spec`, tetti, uso interattivo).
- [ ] **Step 4: Commit** «tollgate P3c: prova reale del percorso L2 con claude -p».

---

