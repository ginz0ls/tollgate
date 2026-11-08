# Report Task 7: agenti implementer-infra e reviewer-infra

## Fatto
- `agents/implementer-infra.md`, `agents/reviewer-infra.md`: derivati da `-ai` (stesso frontmatter tranne `name`, `description` con la parola `infra`, `skills: [rules-base, rules-infra]`), attribuzione MIT, sezione «Area `infra`».
  - Implementatore: le `[blocca]` fermano il task; le regole sul report (R-INFRA-01, 02, 03, 08, 12) vanno scritte nel campo `done`; non lancia comandi che pubblicano o cambiano un servizio (effetti esterni fermati da tollgate, anche dietro `npx`), né quelli non coperti: scritture remote di `wrangler kv`, `d1`, `r2`, `docker build` / `docker buildx build` con l'opzione push (scritta a parole, per `test_options_exist_in_parser`).
  - Revisore: report su 01, 02, 03, 08, 12; diff su 04, 05, 06, 07, 09, 10, 11; `WebFetch` solo per gli URL citati (dati non fidati); nessun rilievo `R-INFRA-` in un task senza modifiche.
- `hooks/run` (`READONLY_TYPES`) e `config.DEFAULTS["review"]["readonly_agents"]`: aggiunto `tollgate:reviewer-infra`. `_AREA_READONLY` in config.py era già generica.
- `agents/final-reviewer.md`, `agents/finding-verifier.md`: l'esempio nomina anche le `R-INFRA-…` di `rules-infra`.
- `docs/uso/comandi.md` (`/tollgate:execute`): l'area `infra` e il task a due aree con agenti generici.
- Test: `AREAS = ("ai", "infra")` in `tests/test_manifest.py`; `test_area_agents_name_rules_ai` diventa `test_area_agents_name_area_rules` (motivo: la decisione 9 confronta gli id con la skill di ogni area, con regex `R-<AREA>-\d\d` e frasi di report/diff, invece di `b[:7]` e stringhe `R-AI-` fisse); preload, deriva, attribuzione e `final_reviewers` su tutte le aree. `test_infra_task_routed_to_area_agents`, `test_rules_infra_not_required`, `test_infra_and_ai_task_goes_generic` (taskcmd); `test_infra_and_ai_routing_is_split_candidate` (profiles); `test_infra_profile_blocking_rule_changes`, `..._non_blocking_rule_approves`, `test_infra_blocking_rule_without_step` (verdict).

## Verifiche
- File di test del task (profiles, taskcmd, check_task_verdict, wrapper, manifest, skill_contract, config): 274 test OK.
- `claude plugin validate --strict .`: passa (solo avviso sul README, preesistente).
- Non ho osservato il rosso di `test_readonly_list_matches_config_and_agents` prima degli elenchi: ho scritto agenti ed elenchi insieme.
- Suite completa: `PYTHONWARNINGS=error::ResourceWarning tests/run` verde, 3653 test OK su python3.11 e python3, uscita 0.
