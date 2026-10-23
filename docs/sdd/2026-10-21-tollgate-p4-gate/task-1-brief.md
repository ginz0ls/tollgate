### Task 1: Verifiche reali su GitHub (controller)

Solo i fatti non ancora provati e necessari al disegno. Già provati in P0 e **non** da riprovare: 403 «Upgrade to GitHub Pro…» su protezione e rulesets del privato, 404 «Branch not protected», `actions: read` per gli artefatti nei privati, `pull_request_target` con la definizione del predefinito, `app_id` 15368 e la sorgente fissata, `workflow_run` per Dependabot, `creator.login = github-actions[bot]` degli stati scritti con `GITHUB_TOKEN`.

**Files:**
- Create: `spikes/gh-p4/run-p4-checks.sh`, `spikes/gh-p4/workflows/probe-{target,run,verdict,base}.yml`, `docs/verifiche/2026-10-21-p4-verifiche.md`, `docs/verifiche/evidenze/gh-p4/` (uscite grezze)

**Chi:** un implementatore sonnet scrive script e workflow sonda **senza rete** (`bash -n`, prova con un `gh` finto); il controller li esegue (decisione 25).

**Regole dello script** (lezione dell'incidente di P0): le uscite si scrivono direttamente in `docs/verifiche/evidenze/gh-p4/` del worktree, mai in `/tmp`, e nessuna cartella di uscite si cancella; prima di ogni comando lo script controlla che il repo bersaglio sia uno dei due della decisione 25 e si ferma altrimenti; nessun `gh api user`.

| Id | Fatto da provare | Come | Dove incide |
|---|---|---|---|
| V1 | Campi JSON di `gh` 2.46: `pr list --json headRefOid,mergedAt,isCrossRepository,mergeStateStatus`, `pr view --json comments` con `author.login` e `body`; login esatto di un commento scritto **da un workflow** con `GITHUB_TOKEN`, sia in `pr view --json comments` sia in `GET issues/<n>/comments` (`user.login`) | Una PR sul repo `protected`, un commento dell'utente e uno scritto dalla sonda `probe-verdict` | `gh.pr_for_branch`, `ghcli.BOT_LOGINS`, `fixtask`, `fakegh` (decisione 14), Task 16 |
| V2 | Forma di `gh api --include` con risposta 403 e 404 (riga di stato, dove finisce il corpo, codice d'uscita) | GET di protezione su `detect` (403) e su `protected` non protetto (404) | `protection.classify` (decisione 18) |
| V3 | Campi dell'evento `workflow_run` (`path`, `event`, `head_sha`, `head_branch`, `pull_requests[].number`, `pull_requests[].base.ref`) e di `pull_request_target` (`pull_request.head.sha`, `head.ref`, `head.repo.full_name`, `base.ref`, `number`); `git fetch origin refs/pull/<n>/head` dentro `pull_request_target` | Sonde `probe-target`, `probe-run` → `probe-verdict` che salvano le chiavi (non i valori di testo) | `github.pr_from_event` (Task 9), `guard` |
| V4 | `actions/cache@v4`: una voce salvata da un job `workflow_run` (ambito del predefinito) si ripristina in un job `pull_request` e in un job `push` del predefinito | `probe-verdict` salva `probe-<tree>`, `probe-run` di una seconda PR e `probe-base` la ripristinano | Decisione 12 |
| V5 | `GET commits/<sha>/pulls` per un commit di merge, un merge squash, un merge con rebase e un push diretto (`merged_at`, `base.ref`) | Quattro commit sul repo `protected` | Decisione 16 |
| V6 | Uno stato scritto con `GITHUB_TOKEN` in un job `push` e in `pull_request_target` ha `creator.login = github-actions[bot]`; nome del check-run del job di `probe-base` e `.app.id` | `GET commits/<sha>/statuses`, `GET commits/<sha>/check-runs` | Decisioni 5, 16, 18 |
| V7 | Versione di `gh` sui runner `ubuntu-latest` e autenticazione con `env: GH_TOKEN: ${{ github.token }}` | `gh --version` e `gh api repos/<o>/<r>` in una sonda | Decisione 17 |
| V8 | `upload-artifact@v4` con un percorso `..` e con un collegamento simbolico; dove `download-artifact@v4` estrae con `path:` | Sonda `probe-run` con i due casi | Decisione 13, Task 16 |
| V9 | `GET repos/<o>/<r>/actions/permissions`: campo `enabled` | Sui due repo | Decisione 19 |

- [ ] **Step 1 (implementatore, senza rete):** script con i modi `prepara` (crea i due repo, se mancano, con `--add-readme`; spinge le sonde), `v1` … `v9`, `raccogli`, `pulisci-sonde` (un commit che toglie i workflow sonda da entrambi i repo, senza toccare la storia). `bash -n` e una corsa con `PATH` che punta a un `gh` finto che registra gli argomenti: nessun comando nomina un repo diverso dai due.
- [ ] **Step 2 (controller):** `gh auth status` (scope `repo` e `workflow`), poi `prepara`, `v1`-`v9`, `raccogli`, `pulisci-sonde`. Un fatto che non si ottiene si scrive «non determinato», con la causa.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-21-p4-verifiche.md`: tabella `Id | Fatto | Esito | Evidenza | Conseguenza per il piano`, versioni (`gh --version`, `claude --version`), minuti di Actions consumati. Se un esito smentisce una decisione, una riga «da correggere nel Task N» e una `Ruling:` nel ledger prima di lanciare quel task.
- [ ] **Step 4: Commit** «tollgate P4: verifiche reali su GitHub (campi di gh, eventi, cache, commit e PR)».

---

