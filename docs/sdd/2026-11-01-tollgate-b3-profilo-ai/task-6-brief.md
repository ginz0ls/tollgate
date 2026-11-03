### Task 6: Verifica delle fonti e pagina per l'utente

**Files:**
- Create: `docs/profili/verifiche/ai-fonti.md`, `docs/profili/ai.md`
- Modify: `skills/rules-ai/SKILL.md` e `templates/profiles/ai.toml` (solo se una fonte non passa), `tests/test_rules_ai.py`

**Interfaces:**
- Consumes: `tests/test_rules_ai.rules(text)` (Task 5); `<workspace>/fonti/ai/`.
- Produces: la pagina che il Task 7 mostra all'utente; il rapporto delle fonti.

- [ ] **Step 1 (controller): la verifica delle fonti.** Un subagente `Explore` (sonnet, sola lettura) verifica **ogni fonte di ogni regola** e **ogni marcatore di `[detect] content`** sulle copie di `fonti/ai/` e sul progetto di B: il file esiste; la sezione esiste; dice ciò che la regola o il marcatore le attribuisce (citazione di al più una riga); è una pagina ufficiale del fornitore o del framework (con la licenza annotata da `FONTI.md`), oppure il progetto di B. Il criterio di B2 «licenza MIT o Apache-2.0» qui non vale: le pagine danno fatti, non testo da distillare (Global Constraints). Esito `ok` o `no` con il motivo. Il controller salva l'uscita in `<workspace>/task-6-fonti.md`.
- [ ] **Step 2: I test che falliscono** (da `RulesBasePageTest`, con i correttivi del rinvio 182): `test_sources_report_covers_every_rule`, `test_page_lists_every_rule` (anche «N.» uguale all'id tra parentesi), `test_page_blocca_matches_skill`, `test_page_explains_what_changes` (la pagina dice che il profilo si accende solo nei progetti dove `init` lo propone e l'utente lo copia, a partire da L1; quali cartelle e quali import lo accendono; che R-AI-01 guarda il solo diff; che «più recente» vuol dire ultimo modello stabile), `test_detect_markers_verified` (ogni marcatore del frammento ha una riga `ok` nel rapporto); `test_real_markers_not_in_tollgate_bin` (nessun marcatore del frammento vero compare nei file di `bin/`, che ogni progetto riceve in `.github/tollgate/`: difesa in più oltre all'esclusione della decisione 5).
- [ ] **Step 3: Le correzioni e i due file.** Escono le fonti `no` e le regole o i marcatori che restano senza fonte `ok`; le regole rimaste si rinumerano senza buchi. Rapporto e pagina come in B2 (tabella «N.», «In parole semplici», «Blocca?», «Da dove viene»; sezione «Regole tolte dalla verifica»; come rispondere), in parole semplici.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_rules_ai`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: fonti di rules-ai verificate e pagina per l'utente».

---

