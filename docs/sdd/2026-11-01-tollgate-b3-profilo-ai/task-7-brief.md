### Task 7: Approvazione dell'utente

**Files:**
- Modify: `skills/rules-ai/SKILL.md`, `docs/profili/ai.md`, `docs/profili/verifiche/ai-fonti.md` (solo con correzioni), `tests/test_rules_ai.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: la pagina del Task 6; `fragments.approved` (Task 2).
- Produces: `approved: <AAAA-MM-GG>` in `skills/rules-ai/SKILL.md`; da qui `init` propone il profilo `ai`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Come in B2, Task 5, Step 1: la pagina nel terminale; approva, correggi o togli; ogni correzione è un giro di questo task, una regola nuova o con una fonte nuova ripassa dal verificatore. Fermata prevista.
- [ ] **Step 2: I test che falliscono.** `test_frontmatter` si inverte; `test_page_approval_date_matches_skill`; in `tests/test_fragments.py` `test_real_ai_fragment_approved`.
- [ ] **Step 3: L'approvazione.** `approved: <data>` dopo `version`; nella pagina «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde (`test_real_trees_light_no_profile` garantisce che i test di `init` dalla CLI non cambino esito).
- [ ] **Step 4: Commit** «tollgate B3: rules-ai approvata dall'utente».

---

