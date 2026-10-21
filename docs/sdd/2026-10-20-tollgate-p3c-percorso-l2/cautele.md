## Regole di cautela (obbligatorie, vincolanti per l'utente)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete**
- `claude -p` solo nel Task 14: solo da `/tmp/tollgate-p3c` e solo con `--plugin-dir`.
- Nel Task 1 solo `claude --version` e `gh --version`: nessuna chiamata di rete.
- Nessun repo su GitHub, nessun push verso la rete, nessuna rete nei test. Il solo push ammesso è verso il repo nudo locale del banco (`FlowLab.origin`) o di `/tmp/tollgate-p3c/flow/origin.git`. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api` verso GitHub o `gh pr create` col `gh` vero.

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione (incidente del Task 8 di P3a).
- Mai force push (verso remoti veri), `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p3c` (ramo `p3c-percorso-l2`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

