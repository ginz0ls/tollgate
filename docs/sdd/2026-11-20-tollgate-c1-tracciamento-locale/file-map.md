## Mappa dei file

| File | Task |
|---|---|
| `bin/tollgate_core/db.py`, `bin/tollgate_core/events.py`, spec 18.4 (riga `**Tipi:**`) | 1 |
| `bin/tollgate_core/config.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/lookups.py` (solo il chiamante), `bin/tollgate_flow/housekeeping.py`, `bin/tollgate_core/paths.py` (se serve la cartella `archive`) | 2 |
| `bin/tollgate_analysis/worksize.py` (nuovo), `bin/tollgate_core/sizes.py` (nuovo), `bin/tollgate_flow/start.py`, `bin/tollgate_checks/post_edit.py`, `bin/tollgate_hooks/apply.py` (operazioni `plan` e `level`), `bin/tollgate_flow/l2acts.py` (`approve_plan`), `bin/tollgate_flow/adopt.py` | 3 |
| `bin/tollgate_flow/l2acts.py` (`approve_spec`), `bin/tollgate_core/acts.py`, `bin/tollgate_checks/acts.py`, `bin/tollgate_flow/actapply.py`, `skills/approve/SKILL.md`, `docs/uso/comandi.md` | 4 |
| `bin/tollgate_flow/ruling_cmd.py` (nuovo), `bin/tollgate_core/cli.py`, `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py`, `skills/execute/SKILL.md` | 5 |
| `bin/tollgate_hooks/model.py`, `bin/tollgate_hooks/adapter.py`, `bin/tollgate_hooks/runner.py`, `hooks/hooks.json`, `hooks/run`, `bin/tollgate_checks/stops.py` (nuovo), `bin/tollgate_checks/session.py` | 6 |
| `bin/tollgate_analysis/report.py`, `bin/tollgate_checks/subagent_stop.py`, `task_verdict.py`, `final_review.py`, `audit_round.py`, `bin/tollgate_hooks/apply.py`, `bin/tollgate_core/subagents.py` | 7 |
| `bin/tollgate_analysis/turn.py` (nuovo), `bin/tollgate_core/snapshot.py` (nuovo), `bin/tollgate_core/cli.py`, `docs/uso/gestionale.md` (nuovo), `docs/uso/comandi.md` | 8 |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `tests/test_b1_scripts.py`, `docs/verifiche/2026-11-20-c1-prova-flusso.md`, `docs/verifiche/evidenze/c1/` | 9 |
| spec del nucleo, progetto di C, piano principale di C | 10 |
