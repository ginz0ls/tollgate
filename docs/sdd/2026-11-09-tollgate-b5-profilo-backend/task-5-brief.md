### Task 5: Approvazione dell'utente

**Files:**
- Modify: `skills/rules-backend/SKILL.md`, `docs/profili/backend.md`, `docs/profili/verifiche/backend-fonti.md` (solo con correzioni), `docs/uso/comandi.md` (sezione `/tollgate:rules-backend` con la data), `tests/test_rules_backend.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: la pagina del Task 4; `fragments.approved`.
- Produces: `approved: <AAAA-MM-GG>` in `skills/rules-backend/SKILL.md`; da qui `init` propone `backend`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Come in B4, Task 6: la pagina nel terminale, in breve; approva, correggi o togli; ogni correzione è un giro di questo task, e una regola nuova o con una fonte nuova ripassa dal verificatore. **Fermata prevista** (decisione 15).
- [ ] **Step 2: I test che falliscono.** `test_frontmatter` si inverte; `test_page_approval_date_matches_skill`; `test_approved_skill_leaves_no_pending_decisions`; `test_page_records_the_choices` (la pagina riporta, in una sezione «Cosa hai deciso», come l'utente ha risposto a ogni punto di «Da decidere tu»); `test_page_choices_count_matches_list` passa da «Da decidere tu» a «Cosa hai deciso» (il motivo nel report); in `tests/test_fragments.py` `test_real_backend_fragment_approved`.
- [ ] **Step 3: L'approvazione.** `approved: <data>` dopo `version`; nella pagina «Approvata dall'utente il <data>.»; in `docs/uso/comandi.md` la data. `claude plugin validate --strict .`: uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde.
- [ ] **Step 4: Commit** «tollgate B5: rules-backend approvata dall'utente».

---

