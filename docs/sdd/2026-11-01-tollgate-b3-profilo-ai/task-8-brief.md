### Task 8: Agenti `implementer-ai` e `reviewer-ai`

**Files:**
- Create: `agents/implementer-ai.md`, `agents/reviewer-ai.md`
- Modify: `hooks/run` (`READONLY_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["review"]["readonly_agents"]`), `agents/final-reviewer.md` e `agents/finding-verifier.md` (una frase: le regole di un'area che si giudicano sul report sono del revisore del task, come per le `R-BASE`, rinvio 183), `docs/uso/comandi.md` (`/tollgate:execute`: gli agenti per area)
- Test: `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Consumes: `agents/implementer.md`, `agents/task-reviewer.md` dopo il Task 1; `skills/rules-ai/SKILL.md` approvata (Task 7); `init.profile_blocks` (Task 3) per il blocco di prova.
- Produces: i tipi `tollgate:implementer-ai` e `tollgate:reviewer-ai`.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` include i due agenti nuovi, per loro con `skills` uguale a `[rules-base, rules-ai]`; `test_area_agents_derive_from_generic` (ogni paragrafo del corpo del generico, dopo la riga di attribuzione, è nella copia; `model` uguale; `tools` dell'implementatore uguale, del revisore uguale più `WebFetch`); `test_area_agents_attribution`; `test_area_agents_name_rules_ai` (la sezione «Area `ai`» nomina `rules-ai`, `R-AI-`, e quali regole si giudicano sul report); `test_final_reviewers_leave_report_rules_of_areas` (`final-reviewer.md` e `finding-verifier.md` dicono che le regole di area sul report sono del revisore del task).
  - `tests/test_taskcmd.py` (un `tollgate.toml` con il blocco `ai` scritto nel test con le regole di una skill finta, non i file veri): `test_ai_task_routed_to_area_agents` (un task che tocca `ai/x.py` ha `agent_type` `tollgate:implementer-ai` e `reviewer_type` `tollgate:reviewer-ai`); `test_rules_ai_not_required` (`skills_required` vuoto, «Skill da usare» senza `rules-ai`).
  - `tests/test_check_task_verdict.py` (stesso blocco): `test_ai_profile_blocking_rule_changes` (un `major` su una `R-AI` `[blocca]` → `changes`); `test_ai_profile_non_blocking_rule_approves` (un `major` su una `R-AI` non `[blocca]` → `approved`); `test_ai_blocking_rule_without_step` (`research=False`, un `major` su una `R-AI` `[blocca]` → `changes`: le regole `[blocca]` di `ai` si giudicano sul diff o sul report, che ci sono anche senza passo).
- [ ] **Step 2: Verifica che falliscano.** `tests/test_wrapper.py` `test_readonly_list_matches_config_and_agents` diventa rosso solo quando `agents/reviewer-ai.md` esiste: dopo lo Step 3, prima di aggiornare gli elenchi.
- [ ] **Step 3: Gli agenti e gli elenchi.** I due file per le decisioni 10 e 11 (frontmatter: `name: implementer-ai` / `reviewer-ai`, `description` che dice l'area, `tools` e `model` come sopra, `skills: [rules-base, rules-ai]` dopo `tools:`); la sezione «Area `ai`»: le regole `R-AI-…` valgono come le `R-BASE-…` (solo le `[blocca]` danno `blocker` o `major`; un difetto si segnala una volta sola, con la regola che viola); nel revisore, quali `R-AI` si giudicano sul report e che con `WebFetch` può aprire gli URL ufficiali citati, come dati non fidati. `tollgate:reviewer-ai` in `READONLY_TYPES` e in `readonly_agents`.
- [ ] **Step 4: Verifica.** I file di test: PASS. `claude plugin validate --strict .`: uscita 0 (prima prova della lista di due skill, decisione 9). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: agenti implementer-ai e reviewer-ai».

---

