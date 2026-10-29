## Regole di cautela (obbligatorie, vincolanti per l'utente)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test.
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api`, `gh pr create` né alcun altro comando col `gh` vero.
- Negli script dei Task 1 e 9 (`spikes/b1/run-b1-checks.sh`, `spikes/run-b1-flow.sh`) usi solo `bash -n` e il modo `controlla` (o una corsa con un `claude` finto nel `PATH`). Non li esegui mai in nessun altro modo, nemmeno per prova, nemmeno durante un giro di correzione: l'esecuzione è del controller.
- `evals/run.sh` di P5: solo `bash -n` e il modo `controlla`, mai un'altra forma (gli eval sono di B8).

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push verso remoti veri, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b1` (ramo `b1-informati-prima`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Con circa 2900 test una corsa di `tests/run` dura da 20 a 35 minuti quando la macchina è carica. Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.
