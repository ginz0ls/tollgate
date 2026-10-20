# Task 14 — report

Implementato `task start --from-findings C` e `--from-gate` (decisione 16).

- `bin/tollgate_flow/fixtask.py` (nuovo): `GATE_MARKER`, `from_findings`, `from_gate`. Un'unica transazione: `add_task(kind="fix", source, task_text)` poi `taskcmd._task_start`; se il brief o l'assegnazione falliscono il task non resta. Rifiuta: nessun lavoro, L0, fase diversa da execution, ciclo inesistente o non `needs_fix`, nessun rilievo bloccante aperto, `source` già presente, PR ignota, nessun commento col marcatore. `source` del gate = `gate:<HEAD del worktree>`; commento troncato a 20000 caratteri; mai in un argomento di gh.
- `brief.py`: `findings_task_text`, `gate_task_text` (testo recintato; i file fuori scope marcati «serve una deroga» dentro il recinto).
- `tasks.add_task(..., task_text=None)`.
- `taskcmd.py`: per `kind = "fix"` testo da `tasks.task_text`, scope = scope del lavoro, nessun must-have, instradamento dai file dei rilievi (`_fix_files`; vuoto per `gate:`); stesso trattamento in `review_prepare`. `task_done` non usava il piano: invariato.
- `cli.py`: `K` opzionale, `--from-findings`, `--from-gate`; combinazioni errate o nessun argomento: codice 2.

## TDD
RED: `python3 -B -m unittest tests.test_fixtask` -> `ImportError: cannot import name 'fixtask' from 'tollgate_flow'` (Ran 1 test, FAILED errors=1).
GREEN: stesso comando -> `Ran 11 tests ... OK`. `tests/run`: python3.11 e python3 (3.13) `Ran 1374 tests ... OK`.

## Scostamenti
Nessuno rilevante. Un file di brief resta in `.tollgate-run` se `_task_start` fallisce dopo la scrittura (il DB torna indietro).
