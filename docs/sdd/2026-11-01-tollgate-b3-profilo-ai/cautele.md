## Regole di cautela (obbligatorie, vincolanti per l'utente)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai leggere o scrivere i veri `~/.claude/settings.json`, `~/.claude/plugins/` e `~/.claude/projects/`, né nei test né nel lavoro: le fonti delle regole sono le copie nel workspace (`fonti/ai/`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete (niente `curl`, `wget`, `WebFetch`, `WebSearch`), nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai il `gh` vero (`gh auth`, `gh api`, `gh pr create` o altro).
- `spikes/run-b1-flow.sh`: solo `bash -n`, il modo `controlla` e i test di `tests/test_b1_scripts.py`. Mai un altro modo (`prepara`, `passo1`, `passo2`, `registra` fuori da un test), nemmeno per prova, nemmeno in un giro di correzione: l'esecuzione è del controller.
- `evals/run.sh`: solo `bash -n` e il modo `controlla` (gli eval sono di B8).

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Mai cancellare `.git/index.lock` a mano: la cartella è sincronizzata da MEGA e il lucchetto a volte resta per qualche secondo. Se un commit lo trova, aspetta qualche secondo e ritenta.
- Non leggere né riportare `.env`, `auth.json`, token o segreti. Nessuna chiave API nei test, negli script o nelle evidenze.
- La suite in background solo con lo strumento Bash e `run_in_background`, **mai con `&`, `nohup` o `setsid`** dentro il comando.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`, con `PYTHONWARNINGS=error::ResourceWarning` (come la CI).
- Nessun `__pycache__` nel commit (usa `python3 -B`): controlla `git status` prima di `git add`.
- **Mai scrivere `approved` in `skills/rules-ai/SKILL.md` fuori dal Task 7**: accenderebbe il profilo senza l'utente.
- Il repo `ginz0ls/tollgate` è **pubblico**: nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né nome dell'host, niente percorsi `/home/<utente>`. Le copie delle fonti (`fonti/ai/` nel workspace) non entrano mai in git: dalle pagine dei fornitori si prendono fatti, con parole nostre, e una citazione sta al più in una riga, solo nel rapporto delle fonti.
- Lavora solo nel worktree `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b3` (ramo `b3-profilo-ai`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Una corsa di `tests/run` (due interpreti, circa 3240 test) dura da 25 a 90 minuti. Lanciala in background con l'uscita su un file e **controlla tu stesso** quel file (notifica, o un ciclo `until` limitato sull'esito): non restare fermo ad aspettare un messaggio. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.
- `tests.test_cli.CliTest.test_db_restore_interactive_eof_and_ctrl_c` (Ctrl-C su un pty) è instabile sotto carico: se è rosso, ripetilo da solo e riporta entrambi gli esiti.
