## Mappa dei file

| File | Responsabilità |
|---|---|
| `spikes/b1/run-b1-checks.sh`, `spikes/b1/probe-plugin/`, `docs/verifiche/2026-10-27-b1-verifiche.md`, `docs/verifiche/evidenze/b1/`, `spikes/fixtures/hook-inputs/samples-b1.json` | Task 1: fatti sugli strumenti per informarsi |
| `bin/tollgate_core/db.py` (migrazione 6), `bin/tollgate_core/lookups.py` (nuovo), `bin/tollgate_core/phases.py`, `bin/tollgate_core/scope.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/config.py`, `bin/tollgate_flow/start.py`, `bin/tollgate_flow/adopt.py`, `bin/tollgate_flow/housekeeping.py` | Stato |
| `bin/tollgate_analysis/research.py` (nuovo), `bin/tollgate_analysis/bash.py` | Analisi pure |
| `bin/tollgate_hooks/adapter.py`, `bin/tollgate_hooks/model.py`, `bin/tollgate_hooks/apply.py`, `bin/tollgate_checks/lookup_rec.py` (nuovo), `bin/tollgate_checks/_common.py`, `hooks/hooks.json`, `hooks/run` | Registrazione delle letture |
| `bin/tollgate_checks/effects.py`, `agents/implementer.md`, `skills/setup/SKILL.md` | Strumenti per informarsi |
| `bin/tollgate_flow/research_cmd.py` (nuovo), `bin/tollgate_core/cli.py`, `bin/tollgate_checks/cli_calls.py` | Comando `research` |
| `bin/tollgate_checks/research_gate.py` (nuovo), `tests/hookkit.py` (`plugin_root` di `Lab`) | Avviso e rifiuto alla prima modifica |
| `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py`, `bin/tollgate_checks/subagent_start.py`, `agents/task-reviewer.md` | Brief e revisore |
| `spikes/run-b1-flow.sh`, `spikes/b1/flow/`, `tests/test_b1_scripts.py`, `docs/verifiche/2026-10-27-b1-prova-flusso.md` | Prova reale |
| Spec del nucleo, piano principale di B | Task 10 |
