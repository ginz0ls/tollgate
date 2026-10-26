## Mappa dei file

| File | Responsabilità |
|---|---|
| `spikes/p5/`, `docs/verifiche/2026-10-23-p5-verifiche.md`, `docs/verifiche/evidenze/p5/`, `docs/verifiche/evidenze/eval-p5/` | Task 1: fatti nuovi su `claude plugin eval`, CI e GitHub |
| `.github/workflows/ci.yml` (nuovo), `tests/test_ci_workflow.py` (nuovo) | CI del plugin |
| `tests/test_check_cli_calls.py`, `tests/test_prstate.py`, `tests/test_taskcmd.py`, `tests/test_db.py` | Suite indipendente dal percorso; test instabile |
| `gate/workflows/tollgate-*.yml`, `gate/workflows/PINS` (nuovo), `bin/tollgate_core/__init__.py`, `.claude-plugin/plugin.json` | Azioni fissate, versione 0.2.0, `experimental.evals` |
| `bin/tollgate_gate/{model,evaluate,attention,verdict,guard,sentinel,baseids,comment,github}.py`, `bin/tollgate_analysis/{workflows,prref,waivers}.py`, `bin/tollgate_core/{runner,ghcli}.py`, `bin/tollgate_flow/init.py` | Rinviati del gate |
| `bin/tollgate_core/{cli,tasks,reviews,intents,audits}.py`, `bin/tollgate_flow/{finishcheck,openpr,actapply,checkpoint}.py` | Rinviati del nucleo e del flusso |
| `evals/_kit/{scaffold.py,recipes.py,target.py}` (e `local.py` solo con la decisione 9 (b) e l'OK dell'utente), `tests/evalbin/gh`, `evals/_kit/fixtures/` | Banco degli eval |
| `evals/<caso>/{case.yaml,scaffold.sh}` (14 casi) | Casi di eval |
| `evals/run.sh`, `evals/cost.py` | Esecuzione degli eval con tetto e conto dei costi |
| `tests/test_eval_kit.py`, `tests/test_eval_cases.py`, `tests/test_eval_run.py` (nuovi) | Prove a secco e test del banco |
| `README.md`, `docs/uso/*.md` (nuovi), `bin/tollgate_core/cli.py` (stampa di `status`), `tests/test_docs.py` (nuovo) | Documentazione d'uso |
| `spikes/run-p5-gate.sh`, `tests/test_p5_scripts.py` | Prova reale su detect |
| `spikes/gh-p4/ghguard.py` (profilo `p5`), `tests/test_p4_ghguard.py` | Guardia dei comandi `gh` del controller (Task 1) |
| `docs/verifiche/2026-10-23-p5-prova-gate.md`, `docs/verifiche/2026-10-23-p5-eval.md`, `docs/verifiche/2026-10-23-p5-ci.md` | Rapporti dei Task 13 e 14 |
