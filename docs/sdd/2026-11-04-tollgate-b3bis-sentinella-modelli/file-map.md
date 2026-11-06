## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_analysis/models.py`; `tests/test_models.py` | 1 | letterali, elenchi, confronto, forma delle righe (puro) |
| `templates/models.toml`, `bin/tollgate_flow/modelsfetch.py`, `tests/helpers.py`; `tests/test_modelsfetch.py` | 2 | dati dei fornitori, client HTTP, cache, helper dei test senza rete |
| `bin/tollgate_core/config.py`, `bin/tollgate_core/git.py`, `bin/tollgate_flow/models_check.py`; `tests/test_config.py`, `tests/test_git.py`, `tests/test_models_check.py` | 3 | sezione `[models]`, componente, orchestrazione |
| `bin/tollgate_flow/start.py`, `bin/tollgate_core/cli.py`, `skills/start/SKILL.md`, `docs/uso/comandi.md`, `docs/uso/installazione.md`; `tests/test_start.py`, `tests/test_cli.py` | 4 | `start`, `models check`, documentazione d'uso |
| `tests/run`, `tests/test_gh.py`, `tests/test_statusline.py`, `tests/test_hook_engine.py`; `tests/test_run_script.py` | 5 | temporanei dei test |
| `spikes/b1/flowreg.py`, `docs/verifiche/evidenze/**`, rapporti delle prove di B1, B2, gh-p4; `tests/test_b1_scripts.py` | 6 | evidenze ripulite |
| `spikes/b3bis/models-prova.sh`, `spikes/b3bis/progetto/`; `tests/test_b3bis_script.py`; `docs/verifiche/2026-11-04-b3bis-prova-modelli.md`, `docs/verifiche/evidenze/b3bis/` | 7 | pulizia di `/tmp` (controller), prova vera |
| spec del nucleo, progetto di B, piano principale di B | 8 | revisione 30 e stato |
