# Revisione Task 13 (base f3829e0, testa f7240d1)

### Aderenza
- ✅ D1: `_is_registered_plan` (`bin/tollgate_checks/_common.py:69-79`, uso a `:104-105`). Esenta solo `c.path == plan_path` con blob identico a `plan_sha`. Provato con una sonda temporanea (scratchpad, non nel repo): cancellazione del piano -> negata (exit 2); rinomina del piano altrove -> negata; un file nuovo con lo stesso contenuto sotto un altro nome -> passa, ma per l'esenzione docs preesistente (`scope_exempt`, `_common.py:225`), non per D1. Percorso relativo/assoluto: se `plan_path` fosse assoluto non combacerebbe mai con `c.path` (direzione sicura). `plan_sha` vuoto -> False. Con `head_ref` (PostToolUse) usa `rev-parse sha:path`: un piano cancellato o diverso fallisce o non combacia.
- ✅ D1, test: `RegisteredPlanCommitTest` (`tests/test_check_commit.py:716-748`) copre piano uguale ammesso, piano cambiato negato, commit già fatto senza blocco `needs_you`.
- ✅ D2 sulle skill: tutte e sei le skill con programma (`approve`, `execute`, `resolve`, `setup`, `start`, `status`) hanno `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` e il ripiego `python3.11`; nessun `"<programma>"` rimasto; `off`/`on` non eseguono comandi. `acts.py:131` quota bene (`python3 "{ctx.plugin_bin}"`); `test_manifest.py:765-772` e `ProgramLineTest` aggiornati; `setup` ricava ancora `<radice>`. Il test `test_python_form_with_double_quoted_spaced_path` (`test_check_cli_calls.py:660-671`) è di aggancio e passa con percorso con spazi (i test sono nel checkout con spazi, `assertIn(" ", ...)`).
- ❌ D2 incompleto: vedi Important 1.
- ✅ D4: riga in `agents/implementer.md:65`, coerente col ruling.
- ✅ D6: la spiegazione regge sul codice. `taskcmd.py:158-162` fa `task_event("fix"/"start")` e `assign` nella stessa `db.tx`; `tasks.py:120` e il `_log` di `task_event` emettono entrambi un `task_change` con payload `number/kind/state/fix_rounds/verdict`, che non include `implementer`/`pending`. Due righe uguali nel log, nessuna doppia scrittura di stato.
- ✅ Script `spikes/run-p3a-flow.sh`: tutto sotto `/tmp/tollgate-p3a/flow` (con guardia `case` prima del `rm -rf`), `TOLLGATE_STATE` con sentinella `.tollgate-test`, `TOLLGATE_GH` su `fakegh.py`, `--plugin-dir`, `--model sonnet`, `--permission-mode acceptEdits` con `--allowedTools` esplicito, nessun `plugin install`/`marketplace`, nessun `kill`/`pkill`, nessun accesso a `.env`/`auth.json`. L'URL di origine è finto con `insteadOf` come `FlowLab`. Il piano di controllo passa `check_plan` prima di `claude` (`:570-584`).
- ⚠️ `git push -q -u origin main` (`:510`) va al repo nudo locale (URL reale ancora quello del nudo): è locale e necessario, ma il brief dice «nessun push»; vale la pena una frase nel rapporto. Il processo `claude` scrive comunque trascrizioni di sessione sotto `~/.claude/projects` (inevitabile con `HOME` vera): il report dice «nessuna scrittura sotto ~/.claude», vero per i comandi, impreciso per la CLI.
- ✅ Il rapporto non dichiara riuscito ciò che non lo è: il passo 2 è dichiarato «non eseguito come scritto», le tre esecuzioni parziali sono elencate come non riuscite, il limite `gh api` è scritto, e il giro 1 dice «non riprovata con claude -p».
- ⚠️ La forma D2 (`python3 "<percorso con spazi>"`) non è stata esercitata da nessuna esecuzione reale dopo il giro 1, e lo script passa ancora dal link senza spazi: non verificabile dal diff, già dichiarato.

### Punti di forza
- D1 minimo, nella direzione sicura (ogni errore git degrada a «violazione»), con test RED/GREEN documentati.
- Il rapporto è onesto su ciò che la prova non copre (un solo task, nessun `--fix`, `gh` finto).
- Messaggi di commit e separazione dei commit (D1, prova, giro 1) puliti.

### Rilievi

**Important**

1. D2 corretto solo nelle skill, non dove nasce lo stesso comando. `bin/tollgate_flow/taskcmd.py:147` mette nel brief dell'implementatore `verify_cmd=f"{shlex.quote(str(db.BIN_PATH))} verify"`; `bin/tollgate_checks/subagent_start.py:33,36` e `subagent_stop.py:126,134,135` iniettano/pretendono `'{plugin_bin}' verify` e `'{plugin_bin}' block open ...`. Sono tutti «percorso tra virgolette come nome del comando», esattamente la forma che il rapporto (D2) dice rifiutata da Claude Code in un worktree quando il percorso ha spazi. Con un plugin in un percorso con spazi (questo checkout) l'implementatore riceve da brief un comando che il guardiano rifiuta, quindi non produce la ricevuta `green` e il task si pianta (stesso sintomo della prova (a)). Il test `shlex.quote` del brief e i messaggi dei veti andrebbero allineati a `python3 <quoted> verify`. Ho verificato il codice, non ho riprodotto il rifiuto (vietato lanciare `claude`). La correzione D2 va estesa a questi cinque punti, con test sulla forma del brief; altrimenti la decisione «tutte le skill coerenti» lascia il percorso reale (skill -> agente -> verify) rotto con spazi.

**Minor**

2. `tests/test_check_commit.py:716-748`: mancano i casi limite che il punto di attenzione D1 chiede (cancellazione e rinomina del piano). Il comportamento regge (provato con sonda), ma non è fissato da un test.
3. `_is_registered_plan` con `head_ref is None` usa `git hash-object` sul working tree, che segue i symlink: sostituire il piano con un symlink a un file di contenuto identico passa il PreToolUse (il PostToolUse sul commit, dove il blob è il testo del link, lo nega). Esotico e già coperto dopo il fatto; se si vuole chiuderlo, rifiutare `os.path.islink`.
4. Le skill dicono «`<programma>` indica questo percorso» ma ora `<programma>` è la coppia interprete + percorso (`skills/*/SKILL.md`, riga **Programma:**). Meglio «questa forma».
5. `docs/verifiche/2026-10-16-p3a-prova-flusso.md:188,190,192` descrivono D2, D4 e D6 come «non corretto / non fatto / non indagato», smentiti dalla sezione «Giro di correzione 1» (`:201-207`). Marcare le righe come superate. L'intestazione «riuscito» (`:165`) vale per il codice di prima del giro 1: dirlo nella stessa riga.
6. `spikes/run-p3a-flow.sh:436-439,159`: il commento e l'uso del link senza spazi aggirano proprio il caso che il giro 1 ha corretto; per riprovare D2 serve poterlo disattivare (es. variabile d'ambiente che usa il percorso reale).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** D1, D4, D6 e la parte skill/`acts.py` di D2 sono corretti e testati, rapporto e script rispettano le cautele. Ma D2 lascia il brief dell'implementatore e i messaggi dei veti con il nome-del-comando tra virgolette (Important 1), cioè la stessa forma rifiutata, quindi la prova con percorso con spazi non scorre fino a `verify`.
