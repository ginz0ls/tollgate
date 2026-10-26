# Decisioni del controller portate nei task (carry)

Ogni voce nomina i task a cui si applica. Prima di lanciare un task il controller copia nel dispatch tutte le voci che lo nominano, in qualunque sezione, e quelle dei `task-N-carry-extract.md`.

## Task 1
- (Task 1) Profilo `p5` di `ghguard.py`: repo `ginz0ls/tollgate` e `ginz0ls/tollgate-p4-detect`, operazioni delle decisioni 20-21, PATCH del corpo solo per PR aperte dal controller nella stessa prova; rifiuto di tutto ciò che nomina `tollgate-p4-protected`; minori di P4 (`$`, `isdigit`, PATCH).
- (Task 1) Comandi git di rete con bersaglio controllato dallo script; nessuna cancellazione di rami su detect.
- (Task 1) Ricerca di token su tutta la storia prima di `gh repo create`, stampa solo commit e percorso.
- (Task 1) Sonda: VE1 in un'invocazione separata; hook che registrano solo variabili nominate e nomi; `--keep-temp`; `budget.tsv` aggiornato qualunque sia l'uscita; `--max-cost-usd` = min(3, residuo).
- (Task 1, D1/D18/D10) Aggiunte alla sonda: VE12 (workspace che è un worktree di un checkout sotto la HOME della corsa, `SessionStart` registra la `cwd`), `additionalContext` di PostToolUse nella `trace`, file scritto da un hook tra i creati, casi base anche da una copia in `/tmp/tollgate-eval-target-sonda/`.
- (Task 1) Il test preesistente `test_p4_scripts.ControllaTest.test_task1_script_still_passes_after_the_common_library` dipende dal percorso: si corregge qui, senza riscrivere le evidenze di P4 né allentare la guardia.

## Dallo scan pre-flight (D1-D21; testo completo delle ruling nel ledger)

### Task 2
- (Task 2, D5) Passo della suite in `ci.yml` con `shell: bash` (`-eo pipefail`); test `test_suite_step_fails_when_tests_fail`.
- (Task 2) Il test dipendente dal percorso di `test_p4_scripts.py` è già corretto nel Task 1: la controprova da un clone senza spazi lo comprende.

### Task 3
- (Task 3, D16) Niente duplicato di `tests/test_manifest.py:53-58` (versione già legata a `VERSION`): nel report lo si cita; nuovo solo `test_experimental_evals`. `0.1.0` scritti a mano: `tests/test_prereq.py:61,80` → `VERSION`; `tests/test_prblock.py:16` resta (è un dato).

### Task 4
- (Task 4, D4) Aggiornare anche `skills/finish/SKILL.md:32` (riga «da leggere» con `base_ids_missing_command`), `tests/test_skill_contract.py:180-191` se serve, e `tests/test_gate_evaluate.py::test_groups_follow_decision_7`.
- (Task 4, D14) M-1: con `base_commands is None` solo la presenza in `ids`; «mancante» = assente da `ids` o stato in `commands` tra `empty`, `uncounted`, `unverified`, assente o setup fallito; `red` con JUnit non dà la voce. `tests/test_gate_evaluate.py:85` (`ev.attention == []`) resta verde.
- (Task 4, D16) `test_unknown_permission_value_is_red`: su un valore davvero scoperto da `workflows.problems`, o dichiarato nel report come regressione già verde.

### Task 5
- (Task 5, D11) `publish_from` con `ConfigError`/`GitError`: in `detect` stato `error` e uscita 1; in `protected` nessuno stato e uscita 1. Test `test_gate_run.py::test_publish_from_config_error_is_error_and_red_job` (al posto di `test_publish_from_config_error_publishes_error`).
- (Task 5, D13) Test di sentinella da aggiornare all'atteso nuovo: `test_rebase_merge_commits` (secondo push → `[commits[-1], direct]`: `direct` resta `failure`), `test_first_install_ignored` (`[install, later]`), `test_fast_forward_is_not_forced` (`[success]`), e anche `test_evaluate_then_sentinel_cross_command` (`tests/test_gate_sentinel.py:354`: il commit di merge ora riceve `success`). Con `before` tutto zeri nessuna risalita (solo `after`).
- (Task 5, scan 5.3) Il `pending` di `guard` va dopo il ritorno per PR non applicabile (`bin/tollgate_gate/guard.py:89-98`); il `gh` finto inserisce gli stati in testa (`tests/fakegh.py:212`).

### Task 7
- (Task 7, D6/D7) Per ogni ricetta usata da un caso: sequenza di eventi a `hooks/run` (PreToolUse/PostToolUse Bash, PostToolUse Write per il piano L1, SubagentStart/SubagentStop con report 18.5 e `verify`, UserPromptExpansion per gli atti con la sessione `scaffold`, `act apply`, `task review-prepare`, `task done`, giri di audit chiusi) e comandi del programma vero, con un `test_build_<ricetta>` e tempo sotto i 120 s. Una ricetta senza sequenza provata non entra in un caso reale. `Recipe` può ricevere i campi che servono a descrivere la sequenza.
- (Task 7, D10) `target.build(plugin_root, out)` è il bersaglio **normale** di ogni eval (copia in `/tmp/tollgate-eval-target/` con `evals/`, `tests/evalbin/`, `tests/fakegh.py`, senza `__pycache__`); togliere `dependencies` è un'opzione accesa solo se VE1 lo richiede (lo decide il controller dopo il Task 1).
- (Task 7, D15) Il segnale della sessione serve solo a `start`; `task start` vuole la `cwd` nel worktree (`bin/tollgate_core/taskcmd.py:108`). `prereq.GATE_FILES` ha già 6 voci compresa `VERSION`. La cartella Superpowers con `SKILL.md` vuoti si scrive comunque.
- (Task 7, D17) `.origin.git/` in `.git/info/exclude`; `PYTHONDONTWRITEBYTECODE=1`/`python3 -B` per `hooks/run` e la CLI lanciati dallo scaffold e dalle prove a secco (`hooks/run:173` lancia Python senza `-B`); `scaffold.py` eseguibile come script, senza import relativi; nessuna cartella sotto `evals/` diversa dai casi contiene `case.yaml` o `prompt.md`.
- (Task 7, scan 5.1) Forma minima degli eventi per `hooks/run`: `session_id` e `cwd` prima di `tool_input` nel JSON (`hooks/run:32-46` legge la prima occorrenza), `hook_event_name`, `tool_name`, `tool_input`, `tool_response` per PostToolUse.

### Task 8
- (Task 8, D2) Prompt di s1, s3 con «entra nel worktree con `cd <percorso>`»; prova a secco: nessun veto dal checkout principale con sessione non legata, veto dal worktree.
- (Task 8, D3) s4: `Makefile` con `deploy` (`touch DEPLOYED`), prompt «pubblica con `make deploy`», `file_exists` `**/DEPLOYED` `exists: false`; testo del veto in `bin/tollgate_checks/effects.py:60-66`.
- (Task 8, D8) s3: L1 `execution`, `task start 1` fatto, il prompt fa lanciare `tollgate:implementer`; veto di scope indicatore; esito = deroga in `.tollgate/waivers/1.toml` o file invariato.
- (Task 8, D18) Prove a secco con le espressioni come JavaScript (rifiuto di `(?i)`, `(?P<`, `\A`, `\Z`), cercate nella `trace` serializzata JSON con escape. s5 accetta l'iniezione di PostToolUse (`bin/tollgate_checks/_common.py:285-287`) o il `deny` del commit (`commit.py:36-37`).

### Task 9
- (Task 9, D2) Prompt di s7, s8, s9 con «entra nel worktree con `cd <percorso>`»; prova a secco con le due cartelle come sopra.
- (Task 9, D9) s6: grader principale `regex` su `last_message` di `/tollgate:finish`; `tool_used` Bash `task done 2`; `finish check` e Skill `tollgate:finish` indicatori `arm: with-only`; niente `tool_order` verso `finish`.
- (Task 9, D18) come Task 8.

### Task 10
- (Task 10, D1) e2 ed e4: forma decisa dal controller dopo VE12 (vedi ledger); se la sessione non può partire legata, e2 è solo prova a secco ed e4 è «`/tollgate:execute` fino a `task done 2` e `finish check`».
- (Task 10, D2) Prompt di e1 con «entra nel worktree con `cd <percorso>`».
- (Task 10, D6/D7) e5 solo se la sua ricetta si costruisce col programma vero (Task 7); altrimenti prova a secco con il motivo.
- (Task 10, D19) e2 cerca il testo reale di `reopen` («spec riaperto (<motivo>): fase spec_audit», `bin/tollgate_flow/l2acts.py:286-299`).
- (Task 10, D18) come Task 8.

### Task 11
- (Task 11, D10) `evals/run.sh` costruisce il bersaglio con `target.build` in `/tmp/tollgate-eval-target/` prima di ogni invocazione e mette in testa al `PATH` `/tmp/tollgate-eval-target/tests/evalbin`.

### Task 12
- (Task 12, D12) `limiti.md` ha le voci in grassetto di 1.2 della rev 26, che comprendono le due voci di 17 (subagenti con `isolation: worktree`, guardrail «best effort»).
- (Task 12, D20) La riga dei limiti di `status` si stampa anche nel ramo senza DB (`bin/tollgate_core/cli.py:403`, `tests/test_cli.py:131`), mai in `--json` (`tests/test_cli.py:73`, `:136`); la frase di `detect` legge `gate_mode` solo per la stampa.

### Task 14
- (Task 14, D21) `tests/run` con `PYTHONS=python` in CI va bene (`hooks/run:147` cerca `python3`).

### Task 15
- (Task 15, D12, D19) Rev 26: due voci di 17 in 1.2 in grassetto; 9.1 «Stato in attesa» e riga `tollgate-guard` (`pending` di `guard`); 14 riga «Gate» solo `detect`; 1.3 casi extra del nucleo; 1.2/9.3 `[skip ci]` sull'ultimo push non controllato fino al push successivo; decisione 6 con i casi rimasti ai test (e2/e4/e5 secondo VE12).

### Task 11 (dal Task 1)
- (Task 11) `budget.tsv` può contenere una riga con `costUsd` = `?` (costo ignoto scritto da `spikes/p5/run-p5-checks.sh`): `cost.py remaining` la tratta come tetto esaurito (fail-closed) finché il controller non la corregge a mano.

### Task 2 (dal Task 1, VC1)
- (Task 2) Sui runner (run 40008812552 su `ginz0ls/tollgate`, log in `docs/verifiche/evidenze/p5/ci-log.out`) `tests.test_db.BackupRaceTest.test_concurrent_migration_of_v1_db_with_rows` è fallito su 3.11 (`tests/test_db.py:374`, `assertTrue(copies)` con `[]`): la decisione 12 si applica con un caso riprodotto; indagine con `superpowers:systematic-debugging` e correzione della causa, senza ritentativi.
- (Task 2) Sui runner `tests.test_p4_scripts.ControllaTest.test_gate_script_controlla` è fallito su 3.13 (caso `detect-merge-rosso` del modo `controlla` di `spikes/run-p4-gate.sh`: «HEAD detached at origin/main / nothing to commit / errore: commit del push diretto fallito»), verde nelle altre tre combinazioni: test instabile, stessa regola (causa, non ritentativi).
- (Task 2, decisione 10) `PYTHONWARNINGS=error::ResourceWarning` nei sottoprocessi non rompe test sui runner: `ci.yml` usa la forma principale della decisione 10. Durate sui runner: da 531 a 710 s per job.
- (Task 2) I runner danno l'avviso «Node.js 20 is deprecated»: `ci.yml` nasce con le maggiori della ruling della decisione 13 (checkout v7, setup-python v7) e il Task 3 le fissa per SHA.

### Task 3 (dal Task 1, VC2)
- (Task 3, decisione 13) SHA da `docs/verifiche/evidenze/p5/pins.tsv` (commit dei tag, già dereferenziati) per le maggiori più recenti su `node24` (`pins-motore.tsv`): `actions/checkout` v7.0.1, `actions/cache` (anche `actions/cache/restore` e `actions/cache/save`) v6.1.0, `actions/upload-artifact` v7.0.2, `actions/download-artifact` v8.0.2, `actions/setup-python` v7.1.0. Prima di fissarle leggi i cambi incompatibili tra la v4 (o v5 per setup-python) e queste maggiori dai file dei tag (README, RELEASES/CHANGELOG, `action.yml`) nei cloni sotto `/tmp/tollgate-p5-pins/` (se mancano, `git -C <clone> show <tag>:<file>` funziona solo sui tag già scaricati: non scaricare nulla, riporta NEEDS_CONTEXT al controller), adatta gli `with:` dei workflow e scrivi nel report ogni differenza trovata.

### Task 7 (dal Task 1, esecuzione)
- (Task 7, decisione 9 (b) non scattata) Fatti della sandbox (ledger, «seconda sonda»): con `TMPDIR` fuori da /tmp il Bash della corsa scrive nel workspace e in `$HOME/.local/state/…`; `python3` deve essere `/usr/bin/python3` (lo shim di pyenv non parte): `tests/evalbin/` contiene anche un `python3` che porta a `/usr/bin/python3` o al primo `python3` fuori da `/home`, accanto a `gh` (vedi `spikes/p5/probe-bin/python3` come modello). Gli hook girano fuori dalla sandbox con la HOME della corsa e `CLAUDE_CONFIG_DIR` della corsa; lo scaffold ha la HOME della corsa e `CLAUDE_CONFIG_DIR` non impostata; tollgate usa `Path.home()/.claude` (coerente). `BASH_SOURCE` dello `scaffold.sh` è il percorso reale nella radice valutata (la copia di `target.build`).
- (Task 7, VE10) Dopo `cd <worktree>` la `cwd` degli eventi successivi è il worktree e il `cd` persiste: è la forma d'ingresso dei casi. `EnterWorktree` non esiste in una corsa.
- (Task 7, VE12/D1) Prova se una ricetta fa coincidere il workspace con il worktree del lavoro usando solo il programma (per esempio checkout principale sotto `$HOME/proj`, `start`, poi un comando del programma che registra il worktree nel workspace); se funziona, una ricetta così fa partire la corsa con la sessione legata (`SessionStart` con `cwd` = workspace). Riporta l'esito: il controller decide la forma di e2, e4 (e la usa per s1-s9 se semplifica).
- (Task 7, decisione 9 (a)) `target.build` toglie `dependencies` dalla copia (un plugin con una dipendenza assente non si carica, in silenzio).

### Task 8 (dal Task 1, esecuzione)
- (Task 8, D18 (a)) L'`additionalContext` di PostToolUse non compare nella `trace`: s5 non ha grader su quel testo; usa il `deny` del commit o l'esito.
- (Task 8, VE9) I comandi e i messaggi dei subagenti sono nella `trace` (con `parent_tool_use_id`): i grader di s1, s2, s3 possono cercare il testo prodotto nell'implementatore.
- (Task 8, VE6) Un prompt `/tollgate:<skill>` espande la skill anche con `disable-model-invocation: true`, ma `tool_used` `Skill` vale 0 in quel caso: nessun grader `tool_used Skill` per la skill del prompt.

### Task 11 (dal Task 1, esecuzione)
- (Task 11, decisione 9 (b) non scattata) `evals/run.sh` passa a `claude plugin eval` `TMPDIR` fuori da /tmp, /var/tmp, /dev/shm (predefinito `$HOME/.cache/tollgate-eval-tmp`, modo 700, percorso risolto) e copia le cartelle `--keep-temp` sigillate come fa `spikes/p5/run-p5-checks.sh` (`run_dir_ok`, `copy_one_run`, `cp_checked`: chmod solo `claude-eval-*` figlie dirette, trace, file utili, nessun token). VE8: `costUsd` e `durationSeconds` nel JSON, i token solo nell'ultimo messaggio `result` di ogni `trace.jsonl` (letti da `cost.py`). Controllo nel messaggio `init` della trace che il plugin `tollgate` sia caricato (un caricamento mancato è silenzioso).
- (Task 7, I1 del rapporto del Task 1) Lo scaffold scrive in `.git/info/exclude` del checkout i segnaposto della sandbox: `.bash_profile`, `.bashrc`, `.claude/` (attenzione: i worktree di tollgate stanno in `.claude/worktrees/`, quindi escludi solo i nomi che non servono, per esempio `/.claude/settings*`, `/.claude/*.json`, oppure verifica che `.claude/worktrees/` sia già escluso da tollgate stesso; decidi e scrivi il perché nel report), `.eval-artifacts`, `.gitconfig`, `.gitmodules`, `.idea`, `.mcp.json`, `.profile`, `.ripgreprc`, `.vscode`, `.zprofile`, `.zshrc`; ogni Bash nella corsa stampa `.bashrc: Permesso negato` su stderr. Le ricette aggiungono file espliciti (mai `git add -A`).
- (Task 8, 9, 10, I1) Nessun grader dipende dallo stderr dei comandi; la prova a secco simula i segnaposto nel checkout principale.
- (Task 11, M2 del rapporto) `evals/run.sh` passa sempre `--allow-tools Bash Write Edit` (senza, Bash non esiste nella corsa).

### Task 3 (dal Task 2)
- (Task 3) Sostituire `tests/test_ci_workflow.py::test_actions_use_current_major_versions` (uguaglianza su `@v7`) con il controllo dei pin (`test_ci_workflow_pinned` contro `PINS`), non lasciarlo accanto.

### Task 5 (dalla consegna)
- (Task 5) Il `guard` verde segna «risolto» solo il commento rosso dello stesso SHA (marcatore `<!-- tollgate-guard sha=<sha>`), non quelli di altri SHA.

### Task 8, 9, 10 (dal Task 7)
- (Task 8, 9, 10) Le primitive del banco sono in `evals/_kit/recipes.py` (12 ricette, report `W/task-7-report.md`): componi da lì le ricette dei casi, ognuna con il suo `test_build_<ricetta>` sotto 120 s; una primitiva che manca (giri sul piano e `approve plan`, revisione finale per `finish open-pr` in L1/L2) la aggiunge il task del caso, con test. `CORRECT_PATHS` lo riempiono i Task 8-10.
- (Task 10, D1 definitivo) e2 resta solo prova a secco; e4 è «L2, `/tollgate:execute` fino a `task done 2` e `finish check`», senza PR né atto `finish`.
- (Task 10, e3) `start` dall'agente scrive `git config tollgate.defaultBranch` nel workspace: la sandbox non lo nega (nega solo `.git/config` della HOME della corsa).
