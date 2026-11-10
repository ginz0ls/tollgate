# Report Task 6 (implementer-backend, reviewer-backend)

Implementato: agents/implementer-backend.md, agents/reviewer-backend.md (copie degli -infra con sezione «Area `backend`»); implementer-infra.md: solo la frase sui comandi non coperti (build Docker con push, altri gruppi di Wrangler); READONLY_TYPES in hooks/run e readonly_agents in config.py; final-reviewer e finding-verifier nominano le R-BACKEND-; docs/uso/comandi.md (area backend).
Test: AREAS con backend; nuovo test_real_infra_agent_names_uncovered_commands (non esisteva); guardie in test_taskcmd, test_profiles, test_check_task_verdict (verdi già prima, 137 test OK).

RED: `python3 -B -m unittest tests.test_manifest` -> FAILED (failures=3, errors=8): agenti backend mancanti, final reviewer senza r-backend-, test infra.
RED elenchi: dopo la creazione di reviewer-backend.md, con hooks/run e config.py ripristinati a main:
`python3 -B -m unittest tests.test_wrapper.WrapperTest.test_readonly_list_matches_config_and_agents` -> FAILED (failures=1), diff: `+ 'tollgate:reviewer-backend'` mancante negli elenchi. (Gli elenchi li avevo scritti nello stesso passo; ripristinati per vedere il rosso, poi riapplicati.)
GREEN: manifest, wrapper, profiles, check_task_verdict, taskcmd, skill_contract: 245 test OK. `claude plugin validate --strict .`: Validation passed, uscita 0.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3742 test OK (skipped=10); python3.13 3742 test OK (skipped=8); exit 0.

Scostamenti: il test del piano `test_real_infra_agent_names_uncovered_commands` non esisteva, scritto da me. Nel test taskcmd del task generico backend+infra ho messo `edge/**` tra i path di backend e `wrangler.jsonc` per infra. Nessun cambiamento a reviewer-infra.md. Il test di deriva non ha richiesto altro.
Dubbi: nessuno.
