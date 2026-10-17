# Prova reale del flusso P3a

Versioni: Claude Code 2.1.302, tollgate 0.1.0 (`tollgate_core.VERSION`), modello `sonnet` per la sessione e per gli agenti. Data: 17 ottobre 2026 (il piano è del 16).

Piano: `docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md` (Task 13). Script: `spikes/run-p3a-flow.sh` (`bash spikes/run-p3a-flow.sh tutto`, oppure `prepara`, `passo1`, `passo2`, `passo3`). Uscite grezze in `/tmp/tollgate-p3a/flow/logs` (fuori dal repo): `passo*.jsonl` (stream di `claude -p`), `events.jsonl`, `stats.json`, `status.txt`, `fakegh.log`, `hooks.log` (copia di `hook-errors.log`, vuoto).

## Impianto

- Tutto sotto `/tmp/tollgate-p3a/flow`: checkout `repo`, repo nudo `origin.git`, stato `state` con la sentinella `.tollgate-test`, log. Il repo di prova ha `remote.origin.url = https://github.com/prova/flow.git` e `url.<repo nudo>.insteadOf` su quell'URL, come `FlowLab`. Nessun push, nessuna rete verso GitHub.
- `gh` è `tests/fakegh.py` (`TOLLGATE_GH`), con l'issue 1 aperta e lo stato `success` per `tollgate/guard` e `tollgate/verdict` sul predefinito. Il log del finto mostra le sole chiamate previste: `auth status`, `api repos/{owner}/{repo}/issues/1`, `pr list`, `api .../commits/<sha>/status`.
- `claude -p` solo da `/tmp/tollgate-p3a/flow/repo`, con `--plugin-dir /tmp/tollgate-p3a/flow/plugin` (link senza spazi al worktree del ramo: vedi D2), `--model sonnet`, `--permission-mode acceptEdits`, `--allowedTools Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob`. Nessun `plugin install`, `marketplace add`, enable o disable. `HOME` vera, solo per l'autenticazione e per la lettura di Superpowers fatta dalla CLI (`start` ha riconosciuto la versione installata).
- `~/.local/state/tollgate` non esiste e non è stato creato (verificato a fine prova con `stat`).
- Il repo di prova: `tollgate.toml` con `allow_no_tests = true` e `verify = "python3 -m unittest discover -s tests -t ."` (senza report JUnit, quindi la ricevuta è `uncounted`), cinque workflow vuoti e `.github/tollgate/VERSION`. Il piano di controllo `piano-L1.md` passa `plan_check.check_plan` (verificato dallo script prima di lanciare `claude`).

## Passi e esiti

Esito della prima prova riuscita (commit `cfc07ae`, codice di D1 ma ancora con il programma tra virgolette e il link senza spazi): **riuscito**, task 1 `done`, verdetto `approved`. Vale per quel codice. La ripetizione con il percorso con spazi sul codice finale del giro 2 è nella sezione «Giro di correzione 2».

| Passo | Prompt | Esito (ultima esecuzione) | Evidenza |
|---|---|---|---|
| 1 | `/tollgate:start #1 L1` | riuscito, e più in là di quanto il brief prevedesse | `start 1 --level L1` esce con 0 e stampa `prossimo passo: EnterWorktree <wt>`; `EnterWorktree` entra nel worktree; la skill passa da sola a `superpowers:writing-plans`, il modello scrive il piano in `docs/superpowers/plans/`, `plan-check` lo registra (`scope_registered`, 2 file, fase `execution`) e il piano viene committato dal coordinatore (`commit f8e54e0`). Nessun veto |
| 2 | «scrivi il piano copiando `piano-L1.md` in `docs/superpowers/plans/2026-10-16-prova.md`» | **non eseguito come scritto**: già superato dal passo 1 | Il piano esisteva già, registrato e committato. Il prompt è stato adattato («se non c'è ancora un piano, copialo; poi controlla che sia committato»): il modello ha verificato e non ha fatto nulla. Il piano copiato da `piano-L1.md` non è quindi stato usato in nessuna esecuzione; il piano provato è quello scritto dal modello (e passa `plan-check`, per `scope_registered`) |
| 3 | `/tollgate:execute` | riuscito | `status --checkpoint` dal worktree, `task start 1`, `Agent` `tollgate:implementer` con `name=tg-1-t1` in primo piano, `task review-prepare 1`, `Agent` `tollgate:task-reviewer` (tipo preso dall'output di `review-prepare`), `task done 1` → `task 1: done` |

Eventi del DB (`bin/tollgate events`), ultima esecuzione: `phase_change` (start → plan), `task_change` (pending), `scope_registered`, `phase_change` (plan → execution), `commit` (piano), due `task_change` `running`, `subagent_start` (implementer), `receipt` (`verify`, `uncounted`), `commit`, `subagent_stop` (`DONE_WITH_CONCERNS`, 43349 token), `task_change` `review`, `subagent_start` (task-reviewer), `task_change` con `verdict: approved` e `dropped: 0`, `subagent_stop` (`approved`, 25240 token), `task_change` `done`.

`bin/tollgate stats` (ultima esecuzione): veti 0, blocchi 0, `needs_you` 0, giri di correzione 0, deroghe 0, token 68589 (implementer 43349, task-reviewer 25240), ore di fase: `plan` 0,01 e `execution` 0,02. Costo riportato da `claude -p` per i tre passi: circa 0,27 + 0,21 + 0,52 USD.

Cosa il percorso ha esercitato davvero, e che i test unitari non vedevano: frontmatter di skill e agenti letti da Claude Code; `${CLAUDE_PLUGIN_ROOT}` espanso nel testo delle skill; segnale di sessione (`PreToolUse Bash` → `cli/<session_id>.json`) letto da `start`; `EnterWorktree` sul percorso stampato da `start`; `SubagentStart`/`SubagentStop` con `take_pending`; tipo del revisore dal comando `review-prepare`; verdetto legato a SHA e codice.

## Esecuzioni precedenti: non riuscite (difetto D1)

Prima della correzione ci sono state tre esecuzioni parziali, tutte ripetute da zero con `prepara`: (a) con il percorso del plugin con spazi, ferma al commit del piano e con `tollgate` rifiutato dal guardiano del worktree (D2); (b) con il link senza spazi, ferma allo stesso commit; (c) dopo (b), per vedere cosa c'era più avanti, ho committato il piano da fuori Claude (senza hook) e lanciato il passo 3: il `PostToolUse` ha visto il commit con la stessa violazione, aperto un `needs_you` e il modello si è fermato prima di `task start`. (c) non conta come prova del passo 3. Nessuna delle tre ha scritto fuori da `/tmp/tollgate-p3a/flow`. Cosa è successo in (b):

Il piano veniva registrato e la fase passava a `execution`, ma il commit del piano, che la skill `start` affida al coordinatore, era negato dal hook: `piano: file fuori dallo scope del piano` (evento `veto`, regola `commit`, stesso messaggio nel `PreToolUse` e, per un commit fatto fuori banda, nel `PostToolUse` con apertura di un `needs_you`). Il passo 3 non poteva partire.

## Difetti trovati e correzioni

- **D1, corretto (commit `cfc07ae`).** `locked_docs` blocca il piano appena registrato, e `scope_exempt` non esenta i documenti bloccati: committare il piano stesso era una violazione di scope. Il piano non è nel proprio scope, quindi la skill `start` e il hook si contraddicevano. Correzione minima in `_common.commit_violations`: un cambio sul `plan_path` con lo stesso blob di `plan_sha` non è una violazione (`_is_registered_plan`). Se il piano cambia dopo la registrazione resta fuori scope. Test: `RegisteredPlanCommitTest` in `tests/test_check_commit.py` (piano uguale ammesso, piano modificato negato, commit già fatto non apre il blocco). Dopo la correzione l'ultima esecuzione è passata senza altri interventi.
- **D2, limite dell'ambiente (SUPERATO dai giri 1 e 2: chiuso, vedi sotto).** In una sessione isolata in un worktree Claude Code 2.1.302 rifiuta un comando il cui nome è un percorso tra virgolette con spazi: «this command runs a command whose name is computed at runtime… Refusing to run it». Le skill dicono `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`, che con `--plugin-dir` su un percorso con spazi (come questo checkout) non gira dentro il worktree: nella prima esecuzione (a), e a ogni comando dopo `EnterWorktree`, `tollgate status` fu rifiutato (lo stesso rifiuto vale per il mio shell). Provati con lo stesso guardiano: percorso con spazi tra virgolette (rifiutato), con `\ ` (rifiutato), senza spazi tra virgolette (ammesso), senza virgolette (ammesso), `python3 "<percorso con spazi>"` (ammesso). Per la prova ho usato il link `/tmp/tollgate-p3a/flow/plugin` senza spazi. Una installazione normale (`~/.claude/plugins/cache/...`) non ha spazi, a meno che la home li contenga. Se si vuole coprire anche quel caso, le skill potrebbero scrivere `python3 "<programma>"`; ma `python3` potrebbe essere < 3.11 (il wrapper degli hook sceglie l'interprete): scelta di design, non fatta.
- **D3, osservazione.** `--continue` riprende la conversazione ma non rimette la sessione nel worktree: il passo 3 è ripartito dal checkout principale, `status --checkpoint` ha risposto «nessun lavoro attivo per questa cartella» e il modello ha fatto `cd` nel worktree da solo. Nell'uso interattivo la sessione resta nel worktree; con `claude -p` per passi separati no. La riga della skill «lancia i comandi dal worktree» ha retto.
- **D4, osservazione (SUPERATA dal giro 1: chiusa).** Senza report JUnit, `tollgate verify` dà `uncounted` e l'implementatore ha chiuso con `DONE_WITH_CONCERNS`, perché non sapeva se `uncounted` valesse `green` (concern nel report: «non posso confermare che la ricevuta sia green»). Il revisore l'ha spiegato come questione della ricevuta e ha approvato. Un cenno in `agents/implementer.md` («`uncounted` con uscita 0 è normale se il progetto non ha un report e `allow_no_tests` è acceso») eviterebbe il giro di dubbio. Non fatto: testo dell'agente, decide il controller.
- **D5, osservazione.** Nell'hook di `UserPromptExpansion` la riga `tollgate: programma` riporta il percorso reale del plugin (con spazi), mentre `${CLAUDE_PLUGIN_ROOT}` nel testo della skill è il percorso passato a `--plugin-dir` (il link). Il modello se n'è accorto e ha usato quello della skill; coerente col ripiego previsto (la riga è solo il ripiego).
- **D6, osservazione (SUPERATA dal giro 1: chiusa, nessun difetto).** Due `task_change` `running` consecutivi (seq 6 e 7) per `task start 1`; non indagato, innocuo.

## Limiti della prova

- `gh.issue` e `gh.commit_state` (`gh api repos/{owner}/{repo}/...`, rilievo del Task 3) sono provati solo su `tests/fakegh.py`: `gh` era il finto, senza rete. Il log del finto mostra che la CLI chiama `repos/{owner}/{repo}/issues/1` e `.../commits/<sha>/status` con i segnaposto letterali, come li risolve il vero `gh` dal repo corrente, ma questo punto resta non verificato su un `gh` vero.
- Un solo task, livello L1, nessun giro di correzione, nessun veto del revisore, nessun `needs_you`: i percorsi `--fix`, `/clear` con ripresa dal checkpoint, `SendMessage` e il blocco da budget non sono stati esercitati.
- Il piano provato è quello scritto da `superpowers:writing-plans`, non il file di controllo (passo 2, vedi sopra).
- Una sola esecuzione riuscita (più una non riuscita prima della correzione di D1): il comportamento del modello varia da una esecuzione all'altra.

## Giro di correzione 1 (decisioni del controller)

Commit: `tollgate P3a: fix round 1 del Task 13 (programma via python3, uncounted nell'implementer, D6 senza difetto)`.

- **D2, deciso e applicato.** Il programma nelle skill è `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` (interprete + percorso tra virgolette; `<programma>` indica la coppia), con il ripiego «riprova con `python3.11`» se la CLI risponde «tollgate richiede Python >= 3.11». La riga `tollgate: programma` di `UserPromptExpansion` (`bin/tollgate_checks/acts.py`) ora è `python3 "<bin>"`. `cli_calls` già riconosceva la forma `python3 <bin/tollgate>`; un nuovo test la fissa con un percorso con spazi (segnale per `start` e `act`, divieto ai subagenti). La forma con `python3` davanti è quella provata ammessa in D2. Non riprovata con `claude -p`, come da decisione.
- **D4, deciso e applicato.** `agents/implementer.md`: una ricevuta `uncounted` con uscita 0 è normale quando non c'è un report e `allow_no_tests` è acceso; non è un motivo per `DONE_WITH_CONCERNS`.
- **D6, nessun difetto.** I due `task_change` `running` vengono da due scritture volute, nella stessa transazione di `task start`: `tasks.task_event(... "start")` (pending a running) e `tasks.assign(...)` (decisione 7: scrive implementatore, tipo di agente e `pending`; `_log` emette un `task_change` con gli stessi campi visibili, che non mostrano né `implementer` né `pending`). Non è una doppia scrittura dello stato. Nessuna modifica.

## Giro di correzione 2

Commit: «tollgate P3a: fix round 2 del Task 13 (programma via python3 nei brief e nei messaggi, piano registrato rinominato o symlink, prova con spazi)».

- **D2 esteso, applicato.** Un unico helper `tollgate_core.paths.program_command` (`python3` + percorso quotato con `shlex.quote`) è usato ovunque nasca un comando destinato al modello: il brief dell'implementatore (`tollgate_flow/taskcmd.py`, `verify`), i messaggi di `subagent_start.py` (verify e `block open`), i veti di `subagent_stop.py` e la riga `tollgate: programma` di `acts.py`. Test con percorso con spazi sulla forma del brief e dei messaggi. Nelle skill `<programma>` è ora detto «il comando intero, interprete più percorso».
- **D1, casi limite.** Test per cancellazione e rinomina del piano registrato (negate) e per un symlink al posto del piano (negato; `_is_registered_plan` rifiuta i symlink).
- **Script.** `PLUGIN_REAL_PATH=1 bash spikes/run-p3a-flow.sh` usa il percorso reale del worktree, con gli spazi, al posto del link.
- **Dichiarazioni.** Il `git push -q -u origin main` dello script va al repo nudo locale `/tmp/tollgate-p3a/flow/origin.git` (necessario per avere `origin/main`), lo fa lo script e non tollgate; nessun push verso GitHub. Il processo `claude` scrive le proprie trascrizioni di sessione sotto `~/.claude` (comportamento di Claude Code con la `HOME` vera, non della prova): nessun comando della prova scrive lì.

### Prova reale ripetuta, con il plugin sul percorso con spazi

Comando: `PLUGIN_REAL_PATH=1 bash spikes/run-p3a-flow.sh tutto` sul codice del commit di questo giro; `--plugin-dir` e `CLAUDE_PLUGIN_ROOT` sono `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p3a` (spazi). Stessa impostazione di prima (tutto in `/tmp/tollgate-p3a/flow`, stato con sentinella, finto `gh`, `--model sonnet`).

| Passo | Esito | Evidenza |
|---|---|---|
| 1 `/tollgate:start #1 L1` | **riuscito** | `python3 "<percorso con spazi>/bin/tollgate" start 1 --level L1` accettato, `EnterWorktree`, `writing-plans`, piano registrato (`scope_registered`, 2 file) e committato (`72a102a`) senza veti |
| 2 piano | **non eseguito come scritto** (come prima) | il piano esisteva già, il modello ha solo verificato che fosse committato |
| 3 `/tollgate:execute` | **riuscito** | dopo `EnterWorktree`/`cd` nel worktree: `status --checkpoint`, `task start 1`, `Agent` implementer (`DONE`, non più `DONE_WITH_CONCERNS`: D4 efficace), ricevuta `verify` registrata (`uncounted`), `task review-prepare 1`, `Agent` task-reviewer (`approved`), `task done 1` -> `done` |

Tutti i comandi `python3 "<percorso con spazi>/bin/tollgate" ...` girano nel worktree senza il rifiuto di D2, e `verify` dell'implementatore produce la ricevuta: la catena skill -> brief -> agente -> `verify` funziona con gli spazi. Eventi 1-16 come nella prova precedente; `stats`: veti 0, blocchi 0, token 63762 (implementer 38833, task-reviewer 24929). `hooks.log` vuoto.
