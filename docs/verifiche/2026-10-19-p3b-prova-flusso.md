# Prova reale del flusso di chiusura P3b

Versioni: Claude Code 2.1.304, tollgate 0.1.0 (`tollgate_core.VERSION`), modello `sonnet` per la sessione e per gli agenti. Data: 20 ottobre 2026 (il piano è del 19).

Piano: Task 17 di P3b. Script: `spikes/run-p3b-flow.sh` (`PLUGIN_REAL_PATH=1 bash spikes/run-p3b-flow.sh tutto`, oppure `prepara`, `passo1`..`passo6`; `passo5 [prompt [n]]` è ripetibile). Uscite grezze in `/tmp/tollgate-p3b/flow/logs` (fuori dal repo): `passo*.jsonl`, `events.jsonl`, `stats.json`, `status.txt`, `fakegh.log`, `fakegh-data-finale.json`, `origin-refs.txt`, `hooks.log` (copia di `hook-errors.log`, vuoto).

## Impianto

- Tutto sotto `/tmp/tollgate-p3b/flow`: checkout `repo`, repo nudo `origin.git`, stato `state` con la sentinella `.tollgate-test`, log. `remote.origin.url = https://github.com/prova/flow.git` con `url.<repo nudo>.insteadOf` (decisione 24). **Nessun push in rete**: prima di ogni passo lo script esegue `git remote get-url --push origin` e si ferma se non è `/tmp/tollgate-p3b/flow/origin.git` (mai scattato). L'unico push è quello di `finish open-pr` verso il repo nudo locale.
- `gh` è `tests/fakegh.py` (`TOLLGATE_GH`), con l'issue 1 aperta, stato `success` per `tollgate/guard` e `tollgate/verdict` sul predefinito e nessuna PR. Mai il `gh` vero, nessun repo su GitHub.
- `claude -p` solo da cartelle sotto `/tmp/tollgate-p3b/flow` (checkout principale per i passi 1-3, worktree del lavoro dal passo 4), `--plugin-dir` sul percorso reale del worktree del ramo (`PLUGIN_REAL_PATH=1`, con spazi), `--model sonnet`, `--permission-mode acceptEdits`, `--allowedTools Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob`. Nessun `plugin install`, `marketplace add`, enable o disable. Nessun comando della prova scrive sotto `~/.claude` (il processo `claude` tiene le proprie trascrizioni di sessione, come in P3a). `~/.local/state/tollgate` non esiste (verificato a fine prova).
- Repo di prova (C1): `tollgate.toml` con `verify = "python3 tools/unittest_junit.py"`, `gate = ["verify"]`, `report = "junit:reports/junit.xml"` (come `JUNIT_TOML` di `tests/flowkit.py`). `tools/unittest_junit.py` (stdlib) esegue `unittest`, scrive `reports/junit.xml` con `classname::name` nella forma `tests.test_calc.CalcTest::test_sottrai` ed esce 1 se un test fallisce o la suite è vuota. Il must-have M1 del piano di controllo è legato a quel test vero; `piano-L1.md` passa `plan-check` (verificato dallo script).

## Passi ed esiti

| Passo | Prompt | Esito | Evidenza |
|---|---|---|---|
| 1 | `/tollgate:start #1 L1` | riuscito | `start 1 --level L1`, `EnterWorktree`, `superpowers:writing-plans`, piano scritto dal modello (2 task di test in `CalcTest`, M1 e M2 con test unittest veri), `scope_registered` (2 file), fase `execution`, piano committato (`70135d7`) senza veti |
| 2 | copia del piano | **non eseguito come scritto** (come in P3a) | il piano esisteva già; il modello non ha fatto nulla. Il piano provato è quello scritto dal modello, non `piano-L1.md` |
| 3 | `/tollgate:execute` | riuscito | `task start 1`, implementer (`DONE`, 38498 token), ricevuta `verify` **`green`, 3 test eseguiti** (il report JUnit c'è, a differenza di P3a), `review-prepare`, task-reviewer (`approved`), `task done 1` |
| 4, tentativo a (cwd = checkout principale, `--continue`) | `/tollgate:finish` | **non riuscito**, causa nell'impianto di `claude -p` (D1 sotto) | hook: «atto non registrato: /tollgate:finish vale solo in una sessione legata a un lavoro». `finish check` verde, revisore finale lanciato (`ok`, 0 rilievi) ma `finish open-pr` ha rifiutato per mancanza dell'atto sullo SHA. Il modello si è fermato e non ha aggirato il rifiuto con `git push` o `gh` |
| 4, tentativo b (cwd = worktree del lavoro, sessione nuova) | `/tollgate:finish` | **riuscito** | atto `finish` registrato (`a-1`, `source: claude-code`), `finish check` verde (fase `review`), `review prepare` ha trovato il ciclo 1 già `ok` su HEAD, `finish open-pr` -> `PR #1 https://github.com/prova/flow/pull/1`, fase `pr_open` |
| 5 | «continua con /tollgate:finish» | non servito | `finish open-pr` è arrivato al passo 4b |
| 6 | `status`, `events`, `stats` | riuscito | vedi sotto |

Esiti attesi dal brief, verificati sui dati finali:
- Ciclo di revisione chiuso `ok`: evento `review_cycle` (ciclo 1, `outcome: ok`, `findings_confirmed: 0`), revisore finale `tollgate:final-reviewer` con `declared_status: ok`, 23587 token. Il frontmatter dell'agente nuovo è stato letto da Claude Code (tipo risolto, lanciato in primo piano da una riga `agente:` di `review prepare`, brief letto dal percorso).
- PR nel finto `gh`: `pr create` con `--head tg/1-aggiungi-sottrai-a-calc --base main`, corpo `Closes #1` più il blocco `<!-- tollgate {...} -->` che `tollgate_analysis.prblock.parse` legge (L1, `verdict.outcome ok`, DoD tutta vera, `head_sha` = `1fb3fe83…`, ricevuta `verify` green con 3 test).
- Fase `pr_open`; eventi `pr_opened` (`pr: 1`) e `phase_change` review -> pr_open.
- Ramo spinto sul repo nudo: `git for-each-ref` su `origin.git` mostra `refs/heads/tg/1-aggiungi-sottrai-a-calc` a `1fb3fe83…`, uguale a HEAD del ramo nel checkout; `main` resta a `94bf72e`.
- Chiamate al finto `gh` (`fakegh.log`): `auth status`, `api …/issues/1`, `api --paginate …/pulls`, `api …/commits/<sha di main>/status`, `pr list --head …`, `pr create`. Nessuna chiamata inattesa.

Eventi del DB: `phase_change` start->plan, `task_change` pending, `scope_registered`, `phase_change` plan->execution, `commit` (piano), due `task_change` `running`, `subagent_start`/`stop` (implementer), `receipt` green, `commit`, `task_change` review/approved/done, `subagent_start`/`stop` (task-reviewer), `receipt` green + `phase_change` execution->review + `finish_check` (ok) da `finish check`, `subagent_start` final-reviewer, `review_cycle` (ok), `subagent_stop`, `act` finish, `pr_opened`, `phase_change` review->pr_open.

## Veti, token, costi

`bin/tollgate stats`: veti 0, blocchi 0, `needs_you` 0, giri di correzione 0, deroghe 0, sostituzioni di rilievi 0, cicli di revisione 1, token 87076 (implementer 38498, task-reviewer 24991, final-reviewer 23587), ore di fase `plan` 0,01, `execution` 0,02, `review` 0,02. `hooks.log` vuoto. Costo riportato da `claude -p` per i passi: 0,37 + 0,17 + 0,45 USD (1-3), 0,59 USD (4a, non riuscito) e 0,18 USD (4b).

## Difetti e osservazioni

- **D1, limite dell'impianto di `claude -p` (non difetto di P3b, nessuna correzione al codice).** Una sessione di `claude -p` parte sempre dalla radice del checkout (cwd) con un `session_id` nuovo, e `--continue` non la rimette nel worktree: lo stesso fatto di D3 di P3a. L'atto `/tollgate:finish` richiede una sessione legata al lavoro (`acts.py`: `ctx.bound`), e il legame lo fa `SessionStart` quando il cwd cade nel worktree del lavoro, oppure `start`. Nell'uso interattivo la sessione è già nel worktree dopo `EnterWorktree`, quindi il caso non si pone. Correzione solo dello script: dal passo 4 in poi `claude -p` parte dal worktree del lavoro, con sessione nuova (la chiusura non ha bisogno della conversazione precedente). Il messaggio del hook («vale solo in una sessione legata a un lavoro») è chiaro, ma la skill `finish` non ha un passo che ne parli: il modello l'ha riportato bene da solo e ha indicato `/tollgate:finish` da una sessione nel worktree. Il rapporto non propone modifiche.
- **O1, osservazione.** Nel tentativo 4b il modello non ha rilanciato il revisore: `review prepare` ha risposto che la revisione era già superata (ciclo 1 `ok` sullo stesso HEAD, avviato in 4a) e `finish open-pr` è partito. Questo conferma che il ciclo `ok` resta valido tra due atti sullo stesso SHA.
- **O2, osservazione.** Nel tentativo 4a il modello ha chiamato la CLI come `python3 '<percorso>' …` (apici singoli, dalla riga `tollgate: programma`) invece del percorso con virgolette doppie della skill: entrambe le forme sono state ammesse da Claude Code nel worktree.
- **O3, osservazione.** Il piano scritto dal modello ha due test (`test_sottrai` e un secondo caso con risultato negativo): M1 e M2 erano legati a test unittest veri e `finish check` ha dato `[sì] Ogni must-have ha i suoi test eseguiti e verdi`. Il percorso `[no]` del must-have non è stato esercitato.

## Ciò che resta non esercitato

- Il verificatore dei rilievi (`tollgate:finding-verifier`): il revisore finale non ha riportato rilievi, quindi nessun verificatore è stato lanciato. Il frontmatter e il brief di quell'agente restano coperti solo dai test.
- Il percorso `needs_fix`: nessun task di correzione (`task start --from-findings`), nessun secondo ciclo, nessun tetto dei cicli, nessun `approve finding`/`approve rounds`.
- `finish open-pr --update`, `/tollgate:sync`, `/tollgate:adopt`, `/tollgate:cleanup`, `/tollgate:abandon`, il livello L2.
- Un'unica esecuzione riuscita per il passo 4, più la non riuscita 4a: il comportamento del modello varia da una esecuzione all'altra. Il `gh` vero non è mai stato chiamato: `pr create` con il blocco di commenti HTML e `--body-file` è provato solo sul finto.
