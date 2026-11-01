### Task 6: `rules-base` a ogni agente che scrive o rivede codice

**Files:**
- Modify: `agents/implementer.md`, `agents/task-reviewer.md`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `bin/tollgate_checks/research_gate.py` (`_warning`), `bin/tollgate_analysis/brief.py` (`STANDARD`)
- Test: `tests/test_manifest.py`, `tests/test_check_research_gate.py`, `tests/test_taskcmd.py`, `tests/test_brief.py`

**Interfaces:**
- Consumes: `skills/rules-base/SKILL.md` approvata (Task 5).
- Produces: il campo `skills: [rules-base]` nei quattro agenti (decisione 2); l'avviso che nomina `tollgate:rules-base`; lo standard del revisore con le regole di base.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` (il frontmatter di `implementer`, `task-reviewer`, `final-reviewer`, `finding-verifier` ha `skills` uguale a `[rules-base]`); `test_other_agents_do_not_preload` (`spec-auditor`, `spec-adversary`, `plan-adversary` senza `skills`); `test_implementer_points_to_rules_base` (la sezione «Informati prima di scrivere» nomina `rules-base` e non contiene più la frase sul file delle dipendenze); `test_reviewers_cite_base_rules` (`task-reviewer.md` e `final-reviewer.md` nominano `R-BASE-`, `[blocca]` e la regola «un difetto della nota si segnala una volta sola»).
  - `tests/test_check_research_gate.py`: `test_warning_names_rules_base` (l'avviso, in L0 e in L1 con l'interruttore spento, contiene `tollgate:rules-base`).
  - `tests/test_brief.py`: `test_review_standard_names_base_rules` (`brief.STANDARD` dice «regole dei profili e di base»).
  - `tests/test_taskcmd.py`: `test_rules_base_not_required` (con un lavoro senza profili e la `rules-base` presente nella radice, dopo `task start` `skills_required` del task è `[]` e il brief non elenca `rules-base` in «Skill da usare»). È un **test di guardia**: passa già prima delle modifiche, e lo Step 2 non lo conta.
  - `test_implementer_tools`, `test_implementer_mentions_untrusted_pages` e `test_implementer_mentions_research_submit` restano verdi senza modifiche.
- [ ] **Step 2: Verifica che falliscano** (salvo il test di guardia).
- [ ] **Step 3: Gli agenti.** La riga `skills: [rules-base]` nel frontmatter dei quattro agenti, dopo `tools:` (come in `spikes/hookprobe/agents/probe-agent.md`). In `implementer.md` i punti 1 e 2 di «Informati prima di scrivere» diventano un solo punto: «Applica le regole di base (`rules-base`, già nel tuo contesto): dicono cosa leggere e quali fonti aprire prima di scrivere» (decisione 11). In `task-reviewer.md` e `final-reviewer.md`, accanto alla regola sulle prove dei rilievi: le regole `R-BASE-…` di `rules-base` valgono per ogni diff; come per i profili, solo quelle `[blocca]` danno `blocker` o `major`; un difetto della nota si segnala una volta sola, con la regola `R-BASE-…` che viola se c'è, altrimenti con `nota di ricerca` (decisione 8). In `finding-verifier.md`: le regole `R-BASE-…` citate nei rilievi sono quelle di `rules-base`, già nel contesto. In `brief.STANDARD` «per le regole dei profili» diventa «per le regole dei profili e di base». In `research_gate._warning` la frase base finisce con «Le regole di base sono nella skill `tollgate:rules-base`.».
- [ ] **Step 4: Verifica.** I quattro file di test: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B2: rules-base precaricata dagli agenti che scrivono e rivedono codice».

---

