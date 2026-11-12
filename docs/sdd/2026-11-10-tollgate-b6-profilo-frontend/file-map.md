## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py`, `docs/uso/comandi.md` (sezione di `/tollgate:init`); `tests/test_fragments.py`, `tests/test_init.py`, `tests/test_profiles.py` | 1 | forma `ext` nel frammento e nella proposta; guardie di runtime |
| `spikes/b1/flowreg.py`, `spikes/run-b1-flow.sh` (intestazione di `limiti.txt`); `tests/test_b1_scripts.py` | 2 | `togli-pagine` per ogni `Bash` su `tool-results/`, `stderr`; intestazione generica |
| `skills/rules-frontend/SKILL.md`, `templates/profiles/frontend.toml`, `docs/uso/comandi.md` (`/tollgate:rules-frontend`, frase di `/tollgate:init`); `tests/test_rules_frontend.py`, `tests/test_fragments.py`, `tests/test_init.py` (`FrontendPrecedenceTest`) | 3, 4, 5 | regole e frammento di `frontend`; tabella delle precedenze |
| `docs/profili/verifiche/frontend-fonti.md`, `docs/profili/frontend.md` | 4, 5 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-frontend.md`, `agents/reviewer-frontend.md`, `hooks/run`, `bin/tollgate_core/config.py`, `agents/final-reviewer.md` e `agents/finding-verifier.md` (l'esempio nomina anche le `R-FRONTEND-…`), `docs/uso/comandi.md` (`/tollgate:execute`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_profiles.py`, `tests/test_check_task_verdict.py` | 6 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py` (titolo della skill), `spikes/b6/flow/`; `tests/test_b1_scripts.py` | 7 | prova reale: script e progetto |
| `docs/verifiche/2026-11-10-b6-prova-flusso.md`, `docs/verifiche/evidenze/b6/flusso/` | 8 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 9 | revisione 33 e stato |
