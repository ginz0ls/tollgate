### Task 1: Interruttore pronto per l'accensione

**Files:**
- Modify: `bin/tollgate_analysis/research.py:37-61`, `bin/tollgate_core/lookups.py:170-177`, `bin/tollgate_core/events.py:13-20`, `bin/tollgate_checks/research_gate.py:76-122`, `bin/tollgate_analysis/brief.py:211-214`
- Test: `tests/test_research.py`, `tests/test_lookups.py`, `tests/test_check_research_gate.py`, `tests/test_brief.py`

**Interfaces:**
- Consumes: `research.enforced(text)`, `research.RULES_BASE`, `_common.work_events(ctx, work_id, *types)` (filtra dopo l'ultimo `plan_reset`), `hooks.model.inject`/`record` (B1).
- Produces: `lookups.rules_switch(root) -> tuple[bool, str | None]`; `lookups.rules_enforced(root) -> bool` invariata nella firma; evento `research_switch_unreadable` {`error`: str} in `events.EVENT_TYPES`; costante `research_gate._UNREADABLE` (testo della decisione 5, con `{error}`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_research.py`: `test_enforced_refuses_no_off_n`: `approved: no`, `approved: NO`, `approved: off`, `approved: Off`, `approved: n`, `approved: "no"`, `approved: 'off'`, `approved: "false"` → `False`; `approved: 2026-10-29` e `approved: prova-b1` → `True`.
  - `tests/test_lookups.py`: sostituisci `test_unreadable_is_off_for_now` con `test_switch_missing_is_silent_off` (`rules_switch(root senza file) == (False, None)`), `test_switch_unreadable_reports_error` (una cartella al posto di `SKILL.md`: primo elemento `False`, secondo una stringa che comincia con `IsADirectoryError`; `rules_enforced` `False`), `test_switch_approved` (`(True, None)`).
  - `tests/test_check_research_gate.py`: `test_unreadable_switch_warns_and_logs_once` (lavoro L1 con `research=True`, radice con `skills/rules-base/SKILL.md` come cartella: la prima modifica dell'implementatore senza nota non è negata, l'`inject` contiene «non si legge» e il comando `research submit`; dopo il `post_edit` c'è un evento `research_switch_unreadable` con `error`; una seconda modifica non aggiunge un secondo evento); `test_unreadable_switch_logged_with_valid_note` (stessa radice, nota valida: nessun `inject`, ma dopo la prima modifica c'è l'evento); `test_missing_switch_no_unreadable_event` (radice senza il file: nessun evento `research_switch_unreadable`, avviso normale).
  - `tests/test_brief.py`: `test_review_brief_no_changes_invalid_note_asks_nothing` (`no_changes=True`, nota consegnata non valida, `research_enforced=True`: nella sezione niente `` `major` ``, niente `missing`, c'è «non era richiesta»).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_research tests.test_lookups tests.test_check_research_gate tests.test_brief`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice.** In `research.enforced` gli apici si tolgono prima del confronto con `_YAML_EMPTY`, che riceve `"no", "off", "n"`. `rules_switch` in `lookups.py` con la docstring della decisione 5; `rules_enforced` diventa `return rules_switch(root)[0]` e perde la frase «la distinzione … è di B2». `"research_switch_unreadable"` in `events.EVENT_TYPES`. In `research_gate._verdict` l'interruttore si legge una volta con `rules_switch(ctx.plugin_root)`, **prima** del controllo della nota, e l'errore viaggia fino a `decide` anche quando la nota è valida: a `post_*`, se c'è un errore e `work_events(ctx, work_id, "research_switch_unreadable")` è vuoto, `record("event", type="research_switch_unreadable", data={"error": …}, work=…)`; a `pre_*`, quando l'esito è l'avviso, l'`inject` è `_UNREADABLE.format(error=…)` seguito dall'avviso normale. In `brief._review_research` la condizione del ritorno anticipato diventa `b.no_changes and not usable`.
- [ ] **Step 4: Verifica.** Gli stessi quattro file di test: PASS. Poi `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B2: interruttore con i valori negativi, il file illeggibile e il task senza modifiche».

---

