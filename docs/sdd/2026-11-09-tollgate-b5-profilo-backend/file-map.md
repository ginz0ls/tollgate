## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py`, `docs/uso/comandi.md` (sezione di `/tollgate:init`); `tests/test_fragments.py`, `tests/test_init.py` | 1 | `[detect] exclude` nel frammento e nella proposta |
| `bin/tollgate_analysis/bash.py`; `tests/test_bash.py` | 2 | scritture di Wrangler su KV, D1 e R2; script nei monorepo |
| `skills/rules-backend/SKILL.md`, `templates/profiles/backend.toml`, `docs/uso/comandi.md` (`/tollgate:rules-backend`); `tests/test_rules_backend.py`, `tests/test_fragments.py`, `tests/test_init.py` | 3, 4, 5 | regole e frammento di `backend` |
| `docs/profili/verifiche/backend-fonti.md`, `docs/profili/backend.md` | 4, 5 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-backend.md`, `agents/reviewer-backend.md`, `agents/implementer-infra.md` (frase sui comandi non coperti), `hooks/run`, `bin/tollgate_core/config.py`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `docs/uso/comandi.md` (`/tollgate:execute`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_profiles.py`, `tests/test_check_task_verdict.py` | 6 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `spikes/b5/flow/`; `tests/test_b1_scripts.py` (test nuovi e nomi `test_real_`) | 7 | prova reale: script e progetto; `togli-pagine` per `Bash`; prefisso `test_real_` |
| `docs/verifiche/2026-11-09-b5-prova-flusso.md`, `docs/verifiche/evidenze/b5/flusso/` | 8 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 9 | revisione 32 e stato |

