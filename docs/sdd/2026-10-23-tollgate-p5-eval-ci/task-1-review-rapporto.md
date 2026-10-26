# Revisione del rapporto del Task 1 (Step 3), commit 9aaed85

Rapporto: `docs/verifiche/2026-10-23-p5-verifiche.md`. Metodo: lettura del brief (Step 3), del ledger (dalla riga «Task 1: esecuzione del controller»), di `ve-analisi.md`; controllo a campione sulle evidenze in `docs/verifiche/evidenze/p5/` e `eval-p5/` (trace, `result.json`, `esiti.txt`, `sonda-hooks.jsonl`, `settings.json`, log CI). Nessun `claude`, rete, `gh` o suite lanciati.

### Aderenza (✅ / ❌; ⚠️ non verificabile)

- ✅ Tabella completa: VE1-VE12, VC1, VC2, VG1, VG2 presenti, più D10 e D18 (a)/(b). VE11 «non eseguita» con motivo (la decisione 9 (b) non scatta). Nessun fatto «non determinato» rimasto senza causa: la prima sonda lo dichiara per VE3 e spiega perché.
- ✅ Versioni: `raccogli-versioni.txt` coincide con la tabella (claude 2.1.309, gh 2.46.0, bwrap 0.12.0, socat 1.8.0.3). Tutti i `result.json` riportano `claudeVersion` 2.1.309.
- ✅ Costo: `eval-p5/budget.tsv` somma 0,3930 (prima sonda) + 0,3557 (seconda) = 0,7486 USD, come nel rapporto; 10 righe = 10 invocazioni = 10 righe di `eval-p5/comandi.log`, tutte con `--no-publish`.
- ✅ VE1 (`…190504Z-sonda-ve1-dependencies/corse/*/trace.jsonl`): il messaggio `init` ha `plugins` = solo i due integrati, `skills`/`agents` vuoti; nelle corse `skill` (190421Z e 201313Z) `init` contiene `sonda` e `sonda:prova`. Controllo valido e, in più, `home/.claude/plugins/installed_plugins.json` con superpowers era presente (scaffold) nella corsa VE1: l'esito regge anche con il registro scritto dallo scaffold. Uscita 0 (`claude.rc`), nessun avviso in `stderr.txt`. Ruling 9 (a) coerente.
- ✅ VE5 (`…201225Z-sonda-nl-bash/result.json`): `motivo-del-veto-nella-trace` true, `negato-non-creato` true, `ammesso-creato` true; braccio senza plugin: motivo assente, `NEGATO` presente (cartella `corse/claude-eval-3vswfF/cwd`), `AMMESSO` presente. Controprova corretta.
- ✅ VE7: aggregati 0,9167 vs 0,4167, delta 0,50 come dichiarato.
- ✅ VE10: in `corse/claude-eval-JGdbCR/cwd/.claude/worktrees/sonda-wt/sonda-hooks.jsonl` gli eventi dopo `cd … && touch WT-OK` hanno `event_cwd` e `process_cwd` = il worktree; i precedenti = workspace. Il comando era `cd .claude/worktrees/sonda-wt && touch WT-OK && pwd` seguito da un secondo Bash: il `cd` persiste. `EnterWorktree` assente da `tools` dell'`init` e `ToolSearch select:EnterWorktree` risponde «No matching deferred tools found» (`…190354Z-sonda-nl-worktree`). Nota: questo esito viene dalla sola prima sonda (non rifatto con TMPDIR fuori da /tmp), ma la lista degli strumenti non dipende dalla scrittura: identica nella seconda sonda (nessun `EnterWorktree` in nessuna trace tranne la prima).
- ✅ VE12 (`…201258Z-sonda-ws-worktree`): `git status`, `git log`, commit riusciti (`5a09fbc sonda: commit dal workspace`), `SessionStart` con `event_cwd` = workspace.
- ✅ VE2/VE3/VE4: gli eventi contati (PostToolUse 3, PreToolUse 3, SessionStart 1, SubagentStop 1, UserPromptExpansion 1) coincidono con `…201313Z-sonda-skill/…/sonda-hooks.jsonl`; `env` degli hook = `CLAUDE_CONFIG_DIR, CLAUDE_PLUGIN_ROOT, HOME, PATH, PWD, TMPDIR` (9 righe su 9); `esiti.txt` conferma STATE_*=ok, INSTALLED_PLUGINS_UNCHANGED=yes, WORKTREES_WRITE_*=ok, SHIM_RUN=ok, PATH_ENTRIES=17, `ENV_CLAUDE_PLUGIN_ROOT=UNSET`; `sonda-scaffold.txt` conferma `CLAUDE_CONFIG_DIR=UNSET` nello scaffold e `BASH_SOURCE_0`/`ROOT_GUESS_IS_PLUGIN=yes`. D10: `…201325Z-sonda-radice-tmp` ha `PLUGIN_ROOT_FROM_FILE=/tmp/tollgate-eval-target-sonda` e `PLUGIN_ROOT_READABLE=yes`.
- ✅ D18: `contesto-del-hook-posttooluse-nella-trace` false (0 occorrenze di `SONDA-CONTESTO` nella trace), `file-scritto-da-un-hook-esiste` true; la sonda `hooks/post.py` stampa il JSON `hookSpecificOutput.additionalContext` nella forma giusta, quindi il «no» non è un difetto della sonda (vedi però il rilievo M3).
- ✅ VC1 (`p5/ci-log.out`, `ci-view.out`, `ci-riepilogo.txt`): durate 655/710/531/699 s; `Ran 2465 tests` in tutti e 4; FAIL per job: 3.11 off = Task1 + `BackupRaceTest`; 3.13 off = Task1 + `test_gate_script_controlla`; entrambi i job `error` = solo Task1; `FAILED (failures=…)` coerente; 0 righe «unclosed database»; annotazioni Node 20/Ubuntu 26 presenti. Il rapporto dice quanto le evidenze dicono.
- ✅ VC2 (`p5/pins.tsv`, `pins-motore.tsv`): gli SHA e i motori citati (checkout v7.0.1 `3d3c42e5…`, cache v6.1.0 `55cc8345…`, upload v7.0.2 `cf430e03…`, download v8.0.2 `9000827c…`, setup-python v7.1.0 `6d4fd22b…`; v4 su node20, setup-python v4.9.1 su node16, ultime su node24) corrispondono.
- ✅ VG1: `p5/cache-mode.txt` = `Cache mode: read` nel job `tollgate-verdict` (`cache-verdict-log.out:31`, run 40008475385 `workflow_run`, creato 19:04:18Z, 16 secondi dopo la PR 16 del ramo `p5-probe-cache`); PR creata e chiusa (`cache-pr-create.rc` 0, `cache-pr-close.rc` 0), `prs-aperte.txt` lista la sola PR 16 della sonda come creata.
- ✅ VG2: `pin-iniziale.out` `sha_pinning_required:false`; `pin-on.rc`, `pin-ripristino.rc`, `pin-dopo.rc` tutti 0; `pin-v4-log-failed.out` contiene il messaggio esatto citato; `pin-v4-view.out` failure, `pin-sha-view.out` success con `Download action repository 'actions/checkout@11d5960a…'`; `pin-dopo.out` `false`.
- ✅ Segreti: `git grep -I -l` con il pattern richiesto su `9aaed85 -- docs/verifiche/evidenze/` non trova file. Con un pattern più largo (`gho_`, `x-access-token:`) restano solo `ci-auth.out:5` e `gh-p4/prepara-auth.out:5` (`gho_****…` mascherato dall'output di `gh auth status`) e `cache-verdict-log.out:172` (comando del workflow, `x-access-token:%s` con `$GH_TOKEN` non espanso): nessun valore reale. Le chiavi d'ambiente degli hook sono 6 nomi noti; `env_names` contiene solo nomi (compresi `CLAUDE_CODE_MESSAGING_TOKEN`, `AWS_*`: i soli nomi).
- ✅ Contraddizioni con le ruling: nessuna. Le ruling del ledger (9 (a) sì, 9 (b) no, 9 (c) non serve, D10 copia in /tmp, D18 (a), D1/VE12, decisioni 10, 12, 13) discendono dalle evidenze lette. Il numero dei comandi (73 nel rapporto contro 71 nel ledger) è spiegato nel rapporto; `p5/comandi.log` ha 73 righe.
- ⚠️ Non verificabile senza rete: gli SHA e i tag (provenienza `git ls-remote`), l'esistenza reale dei run e dei ripristini su GitHub. Le evidenze sono coerenti tra loro.

### Punti di forza

- Il rapporto smentisce da solo la propria prima sonda (EROFS attribuito a /tmp, non alla sandbox) e riscrive VE3/VE5/VE10 con la causa; ogni esito della seconda sonda ha un file puntuale.
- Controprove tenute (braccio senza plugin, `AMMESSO`, controllo dell'`init` per VE1, ripristino del fissaggio verificato dopo l'`PUT`).
- Costi e conteggi tornano con `budget.tsv`, `comandi.log`, `raccogli-versioni.txt`.
- Le ruling indicano il costo se sbagliate e restano confinate (nessun `local.py`, nessun `claude -p`).

### Rilievi

**Critical** — nessuno.

**Important**

I1. Fatto osservato e omesso dal rapporto (e dal ledger): nella sandbox il workspace mostra file fantasma non tracciati. In `eval-p5/20261023T201258Z-sonda-ws-worktree/corse/claude-eval-kBNkCv/trace.jsonl` il primo risultato di `git status --short --branch` elenca `?? .bash_profile .bashrc .claude/ .eval-artifacts .gitconfig .gitmodules .idea .mcp.json .profile .ripgreprc .vscode .zprofile .zshrc` (oltre a `sonda-hooks.jsonl`, `sonda-scaffold.txt`), che non esistono nella cartella `cwd/` raccolta (è la sandbox che li monta; sono nella `denyWrite` di `settings.json`). Inoltre ogni comando Bash stampa due righe `…/home/.bashrc: Permesso negato` all'inizio dell'output. Conseguenze per il piano: un albero «pulito» non esiste mai in una corsa; i controlli di tollgate su `git status --porcelain` pulito, o un `git add -A`/`git commit -a` del flusso, vedranno o proveranno ad aggiungere questi file; i grader `regex` sull'output dei comandi incontrano rumore. Il Task 7/8 deve saperlo prima di scrivere ricette e grader. Correzione: aggiungere una riga al rapporto (per esempio «VE12b / rumore della sandbox») con l'evidenza e la conseguenza, e una `Ruling:` o un carry per i Task 7/8 (ricette con `git add <file>` espliciti; controlli di albero pulito da escludere o da fare su un elenco fisso; il rumore su stderr non va nei grader).

**Minor**

M1. `docs/verifiche/2026-10-23-p5-verifiche.md` (sezione «Minuti di Actions»): «tutto da sottrarre ai 2000 minuti mensili» è un'inferenza non provata e contraddice la frase precedente (`billable` 0 ms nell'API, `raccogli-minuti.txt`). Dire «non determinato: la API `timing` dà 0 ms; la durata dei job è un limite superiore» e non asserire la sottrazione.

M2. VE6 non risponde a metà della domanda del brief: se `execution.allowed_tools` con `Agent`, `Skill`, `EnterWorktree` è accettato (lo è: nessun errore in `…190354Z-sonda-nl-worktree/claude.rc`/`stderr.txt`, `…201313Z-sonda-skill/claude.rc` 0) e quale effetto ha. Le evidenze mostrano anche che `allowed_tools: [Read]` non impedisce `Bash` (`ws-worktree`, `nl-bash`): il Bash è concesso dal flag CLI `--allow-tools Bash Write Edit` (`eval-p5/comandi.log`), non dal caso. `evals/run.sh` deve quindi passare quel flag. Aggiungere la riga.

M3. D18 (a): la trace non contiene gli eventi degli hook `PreToolUse`/`PostToolUse` (solo `hook_started`/`hook_response` di `SessionStart`, verificato con `jq` su `…201225Z…/trace.jsonl`). L'assenza di `SONDA-CONTESTO-POST` dice che il testo non è visibile ai grader, non che il modello non lo riceva. La ruling già lo limita («non arriva nella trace») e rimanda alla prova a secco del Task 8: nel rapporto dire esplicitamente «il modello potrebbe averlo ricevuto; non determinato».

M4. VE3: «`PATH` del chiamante arrivato intatto (17 voci)» non è confrontato con il `PATH` di partenza (solo conteggio, `esiti.txt` `PATH_ENTRIES=17`, shim primo, `/usr/bin` presente). Scrivere «17 voci, shim in testa, `/usr/bin` presente».

M5. Non provato: `git worktree add`, `git branch` e `git config` dal Bash della sandbox (VE12 prova solo `status`, `log`, `add`, `commit`; VE3 scrive file con `touch`). `settings.json` ha in `denyWrite` `home/.git/config`, `home/.git/hooks`, `home/.git/commondir`. Il Task 7 dovrà provare i comandi di tollgate che creano il worktree prima di fidarsi della ricetta VE12. Segnalare come rischio aperto nella conseguenza di VE12.

M6. VC1: i rossi «già corretti in dcd0485/9d5c802» sono un'affermazione non provata dal run (eseguito su `main` a9b37e3, `Ran 2465 tests`, mentre oggi la suite ne conta 2559 secondo il rapporto): le durate sono quindi un po' sotto la suite attuale. Dirlo accanto al limite del timeout («sopra 12 minuti misurati, +4% di test»). VC2: il motore è registrato solo per v4 e per l'ultima maggiore; per `setup-python@v5` usato dalla sonda (e citato nell'annotazione) manca. Non cambia la decisione 13.

### Valutazione

**Qualità del task:** Da correggere (una correzione piccola al rapporto).

**Motivo:** gli esiti dichiarati corrispondono alle evidenze controllate (VE1, VE3, VE5, VE10, VE12, D18, VC1, VC2, VG1, VG2, costo) e le ruling non contraddicono i dati; nessun segreto. Resta da registrare il fatto omesso dei file fantasma e del rumore di `.bashrc` della sandbox (I1), che incide sulle ricette e sui grader dei Task 7-8, oltre a qualche precisazione minore (M1-M6).
