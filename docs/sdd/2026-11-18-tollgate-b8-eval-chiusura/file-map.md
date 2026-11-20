## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_analysis/bash.py`, `bin/tollgate_checks/effects.py`, `docs/uso/comandi.md` (effetti esterni), `tests/test_bash.py`, `tests/test_check_effects.py` | 1 | involucri dell'ambiente, opzioni con valore di Supabase, doppio `--` |
| `bin/tollgate_flow/init.py` (`_drift`), `bin/tollgate_core/tasks.py` (`take_pending`), `tests/test_init.py`, `tests/test_tasks.py`, `tests/test_check_agents.py` | 2 | correzioni piccole di B7 |
| `evals/cost.py`, `evals/run.sh`, `evals/research_counts.py`, `evals/scrub.py`, `.gitignore`, `tests/test_eval_run.py`, `tests/test_eval_cases.py` (passo `fetch`), `docs/uso/eval-e-ci.md` | 3 | campagne, permessi web, pulizia e anonimizzazione delle trace, conteggi |
| `evals/s10-modello-a-memoria/`, `evals/s11-deploy-dedotto/`, `evals/s12-non-esiste/`, `evals/_kit/recipes.py`, `evals/_kit/fixtures/` (piani e file dei progetti), `tests/test_eval_cases.py` | 4 | tre casi nuovi |
| `evals/s1-…`, `s2-…`, `s3-…`, `s6-…`, `s9-…` (`case.yaml`), `tests/test_eval_cases.py` | 5 | casi di P5 con la nota |
| `docs/verifiche/evidenze/eval-b8/` | 6, 7 | sonda ed eval |
| `docs/verifiche/2026-11-18-b8-eval.md` | 7 | rapporto degli eval |
| spec del nucleo, catalogo, progetto di B, piano principale, `docs/uso/limiti.md`, `docs/uso/eval-e-ci.md` | 8 | revisione 35 e chiusura di B |

