## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_core/fragments.py`; `tests/test_fragments.py` | 1 | forme dei pattern, `load_approved`, `rules` che non tace |
| `bin/tollgate_flow/init.py`, `docs/uso/comandi.md` (sezione di `/tollgate:init`); `tests/test_init.py` | 2 | percorsi concreti per le tre forme, documenti e cartelle di GitHub esclusi, test sulla radice vera |
| `bin/tollgate_analysis/bash.py`; `tests/test_bash.py` | 3 | effetti esterni dietro i lanciatori dei pacchetti |
| `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml`, `docs/uso/comandi.md` (`/tollgate:rules-infra`); `tests/test_rules_infra.py`, `tests/test_rules_ai.py` (helper con l'area), `tests/test_fragments.py` | 4, 5, 6 | regole e frammento di `infra` |
| `docs/profili/verifiche/infra-fonti.md`, `docs/profili/infra.md` | 5, 6 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-infra.md`, `agents/reviewer-infra.md`, `hooks/run`, `bin/tollgate_core/config.py`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `docs/uso/comandi.md` (`/tollgate:execute`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_profiles.py`, `tests/test_check_task_verdict.py` | 7 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `spikes/b4/flow/`; `tests/test_b1_scripts.py` | 8 | prova reale: script e progetto |
| `docs/verifiche/2026-11-06-b4-prova-flusso.md`, `docs/verifiche/evidenze/b4/flusso/` | 9 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 10 | revisione 31 e stato |
