## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `agents/*.md` (riga `model:`), `bin/tollgate_flow/taskcmd.py` (`MODEL_HINT`, giro 4), `skills/execute/SKILL.md`, `spikes/run-b1-flow.sh`, `spikes/b1/run-b1-checks.sh` ed `evals/run.sh` (modello), `docs/uso/comandi.md`, `docs/uso/eval-e-ci.md`; `tests/test_manifest.py`, `tests/test_taskcmd.py`, `tests/test_brief.py`, `tests/test_b1_scripts.py`, `tests/test_eval_run.py` | 1 | modelli |
| `agents/{implementer,task-reviewer,final-reviewer,spec-adversary,plan-adversary}.md` e le copie di area (`*-{ai,infra,backend,frontend,database}.md`, `final-database.md`), `docs/uso/comandi.md`; `tests/test_manifest.py` | 2 | sicurezza fin dal progetto |
| `bin/tollgate_core/fragments.py` (`Fragment.keep_paths`), `bin/tollgate_flow/init.py` (`profile_blocks`); `tests/test_fragments.py`, `tests/test_init.py` | 3 | `keep_paths` |
| `skills/rules-security/SKILL.md`, `templates/profiles/security.toml`, `docs/uso/comandi.md` (`/tollgate:rules-security`); `tests/test_rules_security.py`, `tests/test_fragments.py`, `tests/test_init.py` (`SecurityPrecedenceTest`) | 4 | bozza delle regole, frammento, precedenze |
| `docs/profili/verifiche/security-fonti.md`, `docs/profili/security.md`; `tests/test_rules_security.py` | 5, 6 | verifica delle fonti, pagina, approvazione |
| `agents/implementer-security.md`, `agents/reviewer-security.md`, `agents/final-security.md`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `hooks/run`, `bin/tollgate_core/config.py`, `docs/uso/comandi.md`; `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_finalreview.py`, `tests/test_init.py`, `tests/test_check_task_verdict.py` | 7 | agenti e specialista |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py` (titolo della skill), `spikes/c2/flow/`, `spikes/c2/input/`; `tests/test_b1_scripts.py` | 8 | prova reale: script e progetto |
| `docs/verifiche/2026-11-22-c2-prova-flusso.md`, `docs/verifiche/evidenze/c2/flusso/` | 9 | esecuzione e rapporto |
| spec del nucleo, catalogo, progetto di C, piano principale di C | 10 | revisione 37 e stato |
