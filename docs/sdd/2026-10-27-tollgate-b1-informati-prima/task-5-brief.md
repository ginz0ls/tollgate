### Task 5: Strumenti per informarsi: MCP di documentazione e implementatore

**Files:**
- Modify: `bin/tollgate_checks/effects.py`, `agents/implementer.md`, `skills/setup/SKILL.md`
- Test: `tests/test_check_effects.py`, `tests/test_manifest.py` (frontmatter degli agenti; il test esistente con l'elenco esatto degli strumenti di `implementer.md` si aggiorna), `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `research.is_doc_tool` (Task 3); esiti B1-V2 e B1-V3.
- Produces: `effects.decide` per `pre_mcp` restituisce `[]` per uno strumento di documentazione, prima di `mcp_allow`; frontmatter di `implementer.md` con gli strumenti della decisione 7; paragrafo della skill `setup` sui permessi di `WebFetch` e `WebSearch` (decisione 18).

- [ ] **Step 1: Test** `test_check_effects.py`: `test_doc_mcp_not_an_effect` (il nome di context7 del Task 1 → nessun `deny`, nessun `effect_request`); `test_other_mcp_still_effect` (`mcp__github__create_issue` → `deny` con «strumento MCP non in mcp_allow», come oggi). `test_manifest.py`: `test_implementer_tools` (contiene `WebFetch` e `WebSearch`; le voci MCP solo se la `Ruling:` del Task 1 le ammette; nessun `Agent`); `test_implementer_mentions_untrusted_pages` (il corpo contiene la frase sulle pagine scaricate come dati non fidati, la stessa di `agents/spec-auditor.md`); `test_implementer_mentions_research_submit` (il corpo nomina `research submit` e le quattro sezioni della nota, prese dalle costanti di `research.py`). `test_skill_contract.py::test_setup_proposes_web_permissions` (il testo di `setup` nomina `permissions.allow`, `WebFetch` e `WebSearch` e dice che l'utente le aggiunge da sé).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa.** In `implementer.md` una sezione «Informati prima di scrivere», dopo «Prima di cominciare»: leggi i file che tocchi e quelli che li chiamano; prendi le versioni dal file delle dipendenze; per ogni libreria o servizio esterno apri la documentazione ufficiale con `WebFetch` (o context7, se c'è); poi consegna la nota con il comando del brief, con il formato della decisione 2; in L0 non c'è nota. `claude plugin validate --strict` deve restare verde.
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: strumenti per informarsi agli implementatori».

---

