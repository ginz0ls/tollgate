## Regole di cautela (obbligatorie, vincolanti per l'utente)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState`, cioè `TOLLGATE_STATE` con la sentinella `.tollgate-test`.
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` e niente `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete**
- `claude -p` si usa solo nei Task 1 e 13: solo da `/tmp/tollgate-p3a` e solo con `--plugin-dir`.
- Nessun repo su GitHub, nessun push, nessuna rete nei test. `gh` nei test è `tests/fakegh.py`.

**Git e segreti**
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati.
- Mai `npm run dev`.
- Mai `pkill`, `killall` o `kill` per nome o pattern: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Non leggere né riportare `.env`, `auth.json` o segreti. V2 del Task 1 riporta solo i **nomi** delle variabili, mai i valori.

**Commit e lingua**
- Un commit dopo ogni task. Prima di ogni commit `tests/run` deve passare, con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Risposte e messaggi in italiano; identificatori in inglese.
