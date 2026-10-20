# Prova reale del percorso L2 (P3c)

Versioni: Claude Code 2.1.304, tollgate 0.1.0 (`tollgate_core.VERSION`), modello `sonnet` per le sessioni e per gli agenti. Data: 20 ottobre 2026.

Piano: Task 14 di P3c. Script: `spikes/run-p3c-flow.sh` (`prepara`, `passo1`..`passo6`, `libero "<prompt>"`, `registra`, `tutto`). Uscite grezze in `/tmp/tollgate-p3c/prova-1/flow/logs (copia conservata; `/tmp/tollgate-p3c/flow` è stato rigenerato dopo la prova)` (fuori dal repo): `passo*.jsonl`, `events.jsonl`, `stats.json`, `status.txt`, `sessioni.txt`, `reviews-1/` (copia dei report), `fakegh.log`, `fakegh-data-finale.json`, `origin-refs.txt`, `hooks.log` (copia di `hook-errors.log`, vuoto), `git-log-worktree.txt`. I log del primo tentativo del passo 1 sono in `/tmp/tollgate-p3c-keep/tentativo1-logs`.

**Esito: riuscito** per il percorso completo, **composito** per il passo 1 (due tentativi, vedi D1) e con una variante del passo 2 rispetto al brief (spec scritta dal modello, non quella di prova). Il passo 1 è girato con una versione dello script precedente a quella committata (D5).

## Impianto

- Tutto sotto `/tmp/tollgate-p3c/flow`: checkout `repo`, repo nudo `origin.git`, stato `state` con la sentinella `.tollgate-test`, log. `remote.origin.url = https://github.com/prova/flow.git` con `url.<repo nudo>.insteadOf` (decisione 23). **Nessun push in rete**: prima di ogni passo lo script esegue `git remote get-url --push origin` e si ferma se non è `/tmp/tollgate-p3c/flow/origin.git` (mai scattato). Nessun push è stato fatto: `origin.git` ha solo `main` alla base.
- `gh` è `tests/fakegh.py` (`TOLLGATE_GH`), con l'issue 1 aperta (`author_association OWNER`), stato `success` per `tollgate/guard` e `tollgate/verdict` sul predefinito, nessuna PR. Il `gh` vero non è mai stato chiamato dalla CLI di tollgate; nel `fakegh.log` ci sono solo `auth status`, `api …/issues/1`, `api --paginate …/pulls`, `api …/commits/<sha>/status`. Il modello non ha usato `gh`, `git push` né `curl`.
- `claude -p` sempre con `--plugin-dir` sul percorso reale del worktree del ramo `p3c-percorso-l2` (con spazi), `--model sonnet`, `--permission-mode acceptEdits`, `--allowedTools Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob`, e `--add-dir /tmp/tollgate-p3c/flow` (per far leggere al modello i file di prova fuori dal worktree). Nessun `plugin install`, `marketplace add`, `--continue`. `~/.local/state/tollgate` non esiste (verificato a fine prova). Il processo `claude` tiene le proprie trascrizioni sotto `~/.claude`, come nelle prove precedenti; nessun comando dello script scrive là.
- Dal passo 2 ogni `claude -p` parte dal worktree del lavoro: lo script lo ricava da `git worktree list`, richiede il ramo `tg/1-*` e un percorso sotto `/tmp/tollgate-p3c/flow` e si ferma altrimenti. Il worktree è `/tmp/tollgate-p3c/flow/repo/.claude/worktrees/tg-1-aggiungi-sottrai-a-calc`.
- Repo di prova come in P3b (stdlib, `tools/unittest_junit.py`, gate installato). `prepara` crea anche `spec-L2.md` (una fetta, «Tane di coniglio» con le scelte, «Cosa non fare») e `piano-L2.md`, e verifica che passino `specdoc.pitch_problems` e `plan.check_plan` con `level="L2"`.

## Sessioni reali (id e cartella)

| Passo | Sessione | Cartella |
|---|---|---|
| 1 | `57b1b76d-6a3e-4042-b715-7195863b695d` (il tentativo scartato: `fceacf93-18f7-470f-a406-940a271b5642`) | `/tmp/tollgate-p3c/flow/repo` (checkout) |
| 2 | `86047cb1-c581-4b67-8143-2102439ab394` | worktree del lavoro |
| 3 | `ade345b6-6419-4834-98b7-3a9778344181` | worktree del lavoro |
| 4 | `bad45a2e-0bdc-4095-8d1d-4737876021fa` | worktree del lavoro |
| 5 | `801c2af8-9510-4720-a619-d72ce374d77f` | worktree del lavoro |
| 6 | `63fbcaad-8245-4e60-aa97-c162ca45a541` | worktree del lavoro |

Sessioni nuove e distinte, tutte legate (gli eventi del DB portano il `session` di ciascun passo). Gli atti `approve spec 1` (`a-1`, passo 3) e `approve plan` (`a-2`, passo 5), `source: claude-code`, sono stati registrati e applicati nella sessione nuova del passo, senza rifiuti.

## Passi ed esiti

| Passo | Prompt | Esito | Evidenza |
|---|---|---|---|
| 1 | `/tollgate:start #1 L2` (checkout) | riuscito (giudizio) al secondo tentativo, con lo script in forma precedente (D1, D5) | `start 1 --level L2`, `EnterWorktree`, `superpowers:brainstorming`, spec scritta con Write e committata dal modello (`9e3f5a8`), fase `spec_audit` |
| 2 | spec già scritta: segui `/tollgate:spec-audit` | riuscito | giro 1 `tollgate:spec-adversary` con `findings` (0 blocker, 0 major, 1 moderate, 2 minor), spec corretta e committata (`62676b0`); giro 2 `empty` (`52d8ddc`); `audit prepare` chiede `/tollgate:approve spec 1` |
| 3 | `/tollgate:approve spec 1` | riuscito | `act apply`, `spec-approval.md` con `sha` = blob della spec a HEAD (`a4816f6b…`), `slices: 1`, `adversarial: closed`, fase `plan` |
| 4 | piano con Write in `docs/superpowers/plans/2026-10-20-prova.md`, poi `/tollgate:spec-audit` | riuscito | il modello ha letto `piano-L2.md` e lo ha scritto con Write byte per byte, committato in `486c3ab` (blob `6ad777ba…`), `spec-approval.md` committato (`audit prepare` rifiutava finché non lo era); giro 1 `tollgate:plan-adversary` con un `minor` (import e comando di verifica nel Task 1), il modello ha corretto il piano (`4aca8f5`, blob `f7340037…`, quello approvato); giro 2 `empty`; fase `approval` (`audit_clean`) |
| 5 | `/tollgate:approve plan` | riuscito | `plan-approval.md` con `sha` = `plan_sha` = `f7340037…` (blob del piano approvato, quello corretto) e `spec_sha` = `a4816f6b…`; scope di 2 file e 1 task; fase `execution` |
| 6 | `/tollgate:execute` | riuscito | `plan-approval.md` committato, `task start 1`, implementatore (`DONE`), ricevuta `verify` green con 2 test, revisore `approved`, `task done 1`; `status`: `task: 1 done` |

Il piano di prova `piano-L2.md` è stato usato: copiato dal modello senza modifiche nel primo commit del piano e poi corretto dal giro 1 dell'avversario (un `minor`); il piano approvato è quindi il piano di prova più quella correzione. La spec di prova `spec-L2.md` non è stata usata: vedi D1.

Esiti attesi dal brief, verificati sui dati finali: giro `spec-adversarial` chiuso con report in `reviews/1/` (`spec-adversarial-1.md`, `-2.md`, con la riga JSON `v: 1` letta dal hook); `spec-approval.md` con lo `sha` della spec; fase `plan`; due giri `plan-adversarial` (`plan-adversarial-1.md`, `-2.md`); `approval` poi `execution` con `plan_sha` = blob del piano approvato; `plan-approval.md` con `spec_sha`; task 1 `done`.

Eventi chiave del DB: `phase_change` start->spec_audit, `commit`, `subagent_start/stop` + `spec_audit_round` (`spec-adversarial` 1 `findings`, 2 `empty`), `act` approve spec, `phase_change` approve_spec spec_audit->plan, `spec_audit_round` `plan-adversarial` 1 e 2 (`empty`, con `outcome` calcolato sui soli blocker/major: il `minor` del giro 1 non conta), `phase_change` audit_clean plan->approval, `act` approve plan, `scope_registered` (2 file), `phase_change` approve_plan approval->execution, ciclo del task 1 fino a `done`.

## Veti, token, costi

`bin/tollgate stats`: veti 0, blocchi 0, `needs_you` 0, giri di correzione 0, deroghe 0, cicli di revisione finale 0 (non esercitata). Token 155743: spec-adversary 45142 (2 giri), plan-adversary 47842 (2 giri), implementer 38150, task-reviewer 24609. Ore di fase: `spec_audit` 0,04, `plan` 0,03, `approval` 0,01, `execution` 0,02. `hooks.log` vuoto, `*.err` vuoti. Costo riportato da `claude -p`: passo 1 0,25 USD, passo 2 0,38, passo 3 0,16, passo 4 0,44, passo 5 0,16, passo 6 0,42 (più il tentativo scartato del passo 1).

## Difetti e osservazioni

- **D1, ipotesi del brief smentita (non difetto del codice).** Il brief prevedeva che il passo 1 non lasciasse spec e fermava lo script con «rifare il passo 1» se ne trovava una. In due esecuzioni su due `/tollgate:start #1 L2` ha portato il modello, come la skill `start` prescrive in `spec_audit` senza spec, a `superpowers:brainstorming` e a una spec propria scritta con Write e committata (nel primo tentativo il modello ha provato prima a scriverla via shell: un veto `pre_bash` «in L2 il codice lo scrivono gli implementatori…», poi ha usato Write; veto presente solo nel tentativo scartato, `events.jsonl` di `tentativo1-logs`). Rifare il passo non cambia nulla, quindi la correzione è dello script, non di P3c: il passo 1 ammette una sola spec scritta dal modello (si ferma se sono più di una, perché il «primo file nuovo» sarebbe ambiguo) e il passo 2 usa quella al posto di `spec-L2.md`; se non c'è spec, copia `spec-L2.md` come nel brief (ramo non esercitato). Conseguenza: il passo 1 è composito (due esecuzioni, la prima scartata e rifatta da `prepara`), e la spec provata è quella del modello, non quella controllata. Vantaggio: si è esercitato il percorso reale della skill.
- **O1.** Il passo 3 e il passo 5 non committano i file di approvazione (la riga dell'atto lo propone all'utente). Il passo 4 e il passo 6 li hanno committati su richiesta del rifiuto di `audit prepare` e del worktree sporco di `execute`: il meccanismo regge, ma dipende dal modello. Nessun difetto di codice.
- **O2.** Il giro 1 dell'avversario della spec ha trovato rilievi `moderate`/`minor` sul testo del modello e il coordinatore li ha corretti (skill `spec-audit`, punto 3); l'avversario del piano ha trovato un solo `minor`. I giri hanno chiuso `empty` al secondo, come atteso con una spec e un piano piccoli.
- **O3.** Frontmatter degli agenti nuovi (`spec-adversary`, `plan-adversary`) letto da Claude Code (tipi risolti e registrati in `subagents.type`), lanciati in primo piano da righe `agente:` di `audit prepare`, brief letto dal percorso, riga JSON dei giri riconosciuta (`code`, `spec_sha`, `plan_sha`). I rischi che i test non vedevano (frontmatter, righe di lancio, riga JSON, atti in sessione legata) sono tutti chiusi in questa prova.
- **D5, versione dello script del passo 1.** Il passo 1 (entrambe le esecuzioni) è girato con la forma precedente dello script, in cui `passo1` si fermava se trovava una spec: `exit-codes.txt` chiude il passo con «rifare il passo 1». Il passo 1 è stato accettato per giudizio, dopo aver cambiato lo script. Il ramo committato del controllo del passo 1 (una sola spec ammessa, nota «ha scritto la spec del modello») e `tutto` end to end non sono stati eseguiti nella prova di riferimento; il solo ramo nuovo girato è quello `spec_nel_ramo` del passo 2.
- Nessun difetto di P3c emerso: nessuna correzione al codice, nessun passo ripetuto per un difetto.

## Ciò che resta non esercitato

- L'audit a lenti (`tollgate:spec-auditor`, conferma di costo `--confirm`/`audit decline`), `/tollgate:reopen spec|plan`, `start --spec` (fette successive), i tetti dei giri (`/tollgate:resolve`), le più fette e la proposta di issue per le fette successive (la spec ha una sola fetta).
- Il ramo «nessuna spec» del passo 2 (copia di `spec-L2.md`) (`spec-L2.md`, verificata da `pitch_problems` ma non usata).
- `/tollgate:finish` e la PR in L2, il verificatore dei rilievi, la revisione finale.
- L'uso interattivo (compreso `/clear` e la ripresa dal checkpoint): tutta la prova è `claude -p`, un passo per sessione.
- Il `gh` vero: solo il finto.
- Un'unica esecuzione dei passi 2-6: il comportamento del modello varia da una esecuzione all'altra.

## Correzioni dopo la prova

Rilievi della revisione, corretti solo nello script e in questo rapporto; **la prova di riferimento non è stata rifatta** e le correzioni dello script non sono state esercitate da una prova pianificata di `claude -p`. Verifiche senza modello: `bash -n`, `prepara` (che rigenera `/tmp/tollgate-p3c/flow`; la prova di riferimento è conservata in `/tmp/tollgate-p3c/prova-1/flow`, con `logs/`, `repo/`, `state/`, `origin.git/`), controllo di `verifica_gh` e di `verifica_push`, esecuzione dello shim `gh auth status`.

- `gh`: `prepara` crea `$FLOW/shim/gh`, che esegue `tests/fakegh.py`; ogni `claude -p` parte con `PATH="$FLOW/shim:$PATH"` e prima di ogni passo `verifica_gh` controlla che `command -v gh` sia lo shim. Prima di questa correzione il `gh` vero era raggiungibile dal modello (non usato nella prova: nessun `gh`, `curl` o `git push` nei `tool_use` dei passi).
- Esito dei passi: `claude_step` restituisce l'uscita di `claude` (o il fallimento dei controlli), il passo registra comunque i log e propaga l'esito, quindi `tutto` si ferma al primo passo fallito. Prima l'uscita di `registra` lo sostituiva.
- `--add-dir` ristretto a `$FLOW/input` (solo `spec-L2.md` e `piano-L2.md`), non più `$FLOW` con `state/`, `origin.git/` e `logs/`.
- `worktree_lavoro` legge il percorso intero (anche con spazi). `verifica_push` gira anche dopo ogni passo, oltre che prima.
- **Esecuzione accidentale.** Durante la verifica ho lanciato per errore `tutto` invece del solo controllo; il `claude -p` è partito (stesse cautele: solo in `/tmp/tollgate-p3c/flow`, shim, `--plugin-dir`, `--model sonnet`, nessun push, nessuna rete) e ha eseguito i passi 1-3 e parte del 4, poi l'ho fermato per PID. Non fa parte della prova: è un'esecuzione non pianificata, contraria all'indicazione di non lanciare `claude -p` in questo giro, con i log in `/tmp/tollgate-p3c/prova-accidentale/logs`. Di fatto ha girato con la nuova forma dello script (passo 1 con la nota «ha scritto la spec del modello (1 file)», shim `gh`, `--add-dir` su `input/`): il modello ha di nuovo scritto una propria spec al passo 1, il passo 2 l'ha usata, il passo 3 ha approvato la spec e il passo 4 ha letto e copiato il piano; nessuna chiamata `gh` oltre alle 4 della CLI. Non la uso come evidenza del rapporto.
