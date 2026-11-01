## Regole di cautela (obbligatorie, vincolanti per l'utente)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/`, né nei test né nel lavoro: le fonti delle regole sono le copie nel workspace.
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api`, `gh pr create` né alcun altro comando col `gh` vero.
- `spikes/run-b1-flow.sh`: solo `bash -n`, il modo `controlla` e i test di `tests/test_b1_scripts.py`. Mai un altro modo, nemmeno per prova, nemmeno in un giro di correzione: l'esecuzione è del controller.
- `evals/run.sh`: solo `bash -n` e il modo `controlla` (gli eval sono di B8).

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push verso remoti veri, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`. Il file di prova del Task 2 (`skills/rules-base/SKILL.md` con `approved: 2026-01-01`) **non si committa mai**.
- **Mai scrivere `approved` in `skills/rules-base/SKILL.md` fuori dal Task 5**: accenderebbe il blocco senza l'utente.
- Lavora solo nel worktree `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2` (ramo `b2-regole-base`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Con circa 3200 test una corsa di `tests/run` dura da 25 a 55 minuti quando la macchina è carica. Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.

