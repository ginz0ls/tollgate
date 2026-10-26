### Task 12: Documentazione d'uso

**Files:**
- Create: `README.md`, `docs/uso/{installazione,comandi,modalita,limiti,emergenze-e-aggiornamenti,eval-e-ci}.md`, `tests/test_docs.py`
- Modify: `bin/tollgate_core/cli.py` (stampa di `status`, accanto a `_status`) e `tests/test_cli.py`

L'implementatore usa la skill `humanizer` sui testi (decisione 19) e scrive dal codice reale (skill, `argument-hint`, sottocomandi, messaggi), non dalla memoria.

- [ ] **Step 1: Test** `test_docs.py`: `test_every_skill_documented` (Review Focus 7: ogni `skills/<nome>/SKILL.md` compare in `comandi.md` come `/tollgate:<nome>` con il suo `argument-hint`, e con «solo l'utente» se ha `disable-model-invocation: true`); `test_limits_match_spec_1_2` (le voci in grassetto di tutti gli elenchi di 1.2 e i titoli delle voci di `limiti.md` sono lo stesso insieme); `test_no_local_paths` (nessun `/home/` né `MEGA` in `README.md` e `docs/uso/`); `test_relative_links_exist`; `test_update_pins_documented` (`emergenze-e-aggiornamenti.md` nomina `gate/workflows/PINS` e `init --update`). `test_cli.py::test_status_points_to_limits` (percorso assoluto sotto la radice del plugin, che esiste) e `test_status_detect_sentence`.
- [ ] **Step 2: Fallimento, scrittura, `tests/run`, commit** «tollgate P5: documentazione d'uso (installazione, comandi, modalità, limiti, aggiornamenti, eval e CI)».

---

