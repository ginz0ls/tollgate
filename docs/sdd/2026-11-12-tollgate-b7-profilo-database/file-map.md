## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_analysis/bash.py`, `docs/uso/comandi.md` (effetti esterni), `tests/test_bash.py` | 1 | effetti di Supabase, Prisma, Drizzle; test di B5 |
| `spikes/b1/flowreg.py`, `bin/tollgate_flow/init.py` (`_concrete_paths`), `bin/tollgate_core/fragments.py` (`_parse`); `tests/test_b1_scripts.py`, `tests/test_init.py`, `tests/test_fragments.py` | 2 | rinvii piccoli di B6 |
| `skills/rules-database/SKILL.md`, `templates/profiles/database.toml`, `docs/uso/comandi.md` (`/tollgate:rules-database`, frase di `/tollgate:init`); `tests/test_rules_database.py`, `tests/test_fragments.py`, `tests/test_init.py` (`DatabasePrecedenceTest`, `test_real_precedence_p14`) | 3, 4, 5 | regole e frammento; tabella delle precedenze |
| `docs/profili/verifiche/database-fonti.md`, `docs/profili/database.md` | 4, 5 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-database.md`, `agents/reviewer-database.md`, `agents/final-database.md`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `hooks/run`, `bin/tollgate_core/config.py`, `docs/uso/comandi.md` (`/tollgate:execute`, `/tollgate:finish`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_finalreview.py`, `tests/test_init.py`, `tests/test_check_task_verdict.py` | 6 | agenti per area e specialista; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py` (titolo della skill), `spikes/b7/flow/`, `spikes/b7/input/` (spec e piano del lavoro di prova); `tests/test_b1_scripts.py` | 7 | prova reale L2: script e progetto |
| `docs/verifiche/2026-11-12-b7-prova-flusso.md`, `docs/verifiche/evidenze/b7/flusso/` | 8 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 9 | revisione 34 e stato |
