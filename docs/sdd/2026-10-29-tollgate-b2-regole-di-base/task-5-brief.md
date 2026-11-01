### Task 5: Approvazione dell'utente e accensione del blocco

**Files:**
- Modify: `skills/rules-base/SKILL.md`, `docs/profili/base.md`, `docs/profili/verifiche/base-fonti.md` (solo con correzioni), `tests/test_rules_base.py`, `tests/test_check_research_gate.py`

**Interfaces:**
- Consumes: la pagina del Task 4; `lookups.rules_enforced`; `tests/hookkit.Lab`.
- Produces: `approved: <AAAA-MM-GG>` nella skill vera; da qui il blocco è acceso per ogni lavoro con `research = 1`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Il controller mostra all'utente la pagina `docs/profili/base.md` (il testo, nel terminale) e chiede di approvare, correggere o togliere. Ogni correzione torna all'implementatore come giro di questo task: la skill, la pagina e il rapporto delle fonti cambiano insieme; una regola nuova, o con una fonte nuova, ripassa dal verificatore dello Step 1 del Task 4, solo per quella regola. Si ripete finché l'utente non approva. Se l'utente rinvia l'approvazione, vedi la decisione 13 e le istruzioni d'esecuzione («Quando fermarsi»).
- [ ] **Step 2: I test che falliscono** (implementatore, con la data dell'OK nel brief). `tests/test_rules_base.py`: `test_frontmatter` si inverte (ora `approved` c'è, nella forma `^\d{4}-\d{2}-\d{2}$`, ammessa anche tra apici per la `Ruling:` dello Step 3, e `research.enforced(text)` è vero); `test_real_rules_base_is_approved` (`lookups.rules_enforced(ROOT)` è vero). `tests/test_check_research_gate.py`: `test_real_rules_base_blocks_l1` e `test_real_rules_base_blocks_l2` (`Lab(level=…, research=True, plugin_root=ROOT)`: la prima modifica dell'implementatore senza nota è negata con `rule` `research_gate`).
- [ ] **Step 3: L'accensione.** `approved: <data>` nel frontmatter, dopo `version`; nella pagina la riga «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0 (una data YAML non tra apici è un tipo diverso dalla stringa provata in B1-V7; se la rifiuta, la data va tra apici, con una `Ruling:`). `python3 -B -m unittest tests.test_rules_base tests.test_check_research_gate`: PASS. Poi `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde (Review Focus 2).
- [ ] **Step 4: Commit** «tollgate B2: rules-base approvata dall'utente, blocco acceso».

---

