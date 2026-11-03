### Task 1: Rinvii di B2 negli agenti generici e nel brief

**Files:**
- Modify: `agents/implementer.md`, `agents/task-reviewer.md` (riga ~53), `bin/tollgate_analysis/brief.py` (sezione del report in `review_brief`), `bin/tollgate_flow/taskcmd.py:278-281`
- Test: `tests/test_manifest.py`, `tests/test_brief.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Consumes: `brief.ReviewBrief` (campo `research`), la resa del report in `taskcmd` (B2).
- Produces: i testi dei generici che il Task 8 copia.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_implementer_reads_listed_files` (la sezione «Informati prima di scrivere» contiene «i file che elenchi nella nota aprili con `Read`»; rinvio 184); `test_implementer_fix_round_repeats_red_green` (il paragrafo del report dice che il report di un giro di correzione ripete il riscontro RED/GREEN del difetto corretto; rinvio 186).
  - `tests/test_brief.py`: `test_review_brief_no_research_says_base_rules_do_not_block` (`research=False`: la sezione del report contiene «in questo lavoro le regole `R-BASE-…` non bloccano»; con `research=True` la frase non c'è; rinvio 185).
  - `tests/test_taskcmd.py` (`ReviewDoneTest`, come gli altri test della classe): **`test_done_report_without_concerns_adds_none` (riga 653) si sostituisce** con `test_report_concerns_shown_with_done` (stato `DONE` con `concerns` non vuoto: il testo di `concerns` compare nella sezione del report), perché il rinvio 187 chiede il contrario di quel test; più `test_report_null_not_python_none` (un campo `null` del report non compare come `None`). Il test vecchio va tolto con questo motivo scritto nel report.
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_manifest tests.test_brief tests.test_taskcmd`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice e i testi.** In `implementer.md` la riga del rinvio 184 e quella del 186 (nel paragrafo del report). In `brief.py`, con `research` falso, la frase del rinvio 185 nella sezione del report; in `task-reviewer.md`, accanto alla riga 53, la stessa indicazione per il revisore. In `taskcmd.py` `concerns` si esclude dalla resa del report solo quando la sezione dei dubbi c'è (`DONE_WITH_CONCERNS`), e un valore `None` si rende `null`.
- [ ] **Step 4: Verifica.** Gli stessi file di test: PASS (anche `test_implementer_tools`, `test_implementer_mentions_*`, `test_code_agents_preload_rules_base`). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: rinvii di B2 negli agenti generici e nel brief».

---

