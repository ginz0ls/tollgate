## Regole di cautela (obbligatorie)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState`, cioè `TOLLGATE_STATE` con la sentinella `.tollgate-test`.
- Mai installare, abilitare o disinstallare plugin nella configurazione dell'utente: niente `claude plugin install`, niente `claude plugin marketplace add`.
- Mai modificare `~/.claude/settings.json`.

**Esperimenti e rete**
- `claude -p` si usa solo nel Task 1: solo con `--plugin-dir spikes/hookprobe` e solo da `/tmp/tollgate-p2`.
- Nessun repo su GitHub, nessun push, nessuna rete nei test.

**Git e segreti**
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati.
- Mai `npm run dev`.
- Non leggere né riportare `.env`, `auth.json` o segreti.

**Commit e lingua**
- Un commit dopo ogni task. Prima di ogni commit `tests/run` deve passare, con `python3.11` e con `python3`.
- Risposte e messaggi in italiano; identificatori in inglese.
