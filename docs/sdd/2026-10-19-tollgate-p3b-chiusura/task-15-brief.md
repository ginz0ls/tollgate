### Task 15: Prossimo passo nelle fasi di chiusura

**Files:**
- Modify: `bin/tollgate_flow/checkpoint.py`
- Test: `tests/test_checkpoint.py`

**Interfaces:**
- Produces: `next_step(conn, work) -> str` copre anche:
  - `review` con un task revisionato: «revisione preparata, lancia il revisore <tipo> con <brief>» se `review_sha` e `review_code` ci sono e il verdetto manca; «task review-prepare k» solo se la revisione non è preparata (riga 133);
  - blocco «giri di correzione esauriti sul task k»: «serve una decisione dell'utente: /tollgate:approve rounds <n>, /tollgate:resolve <id> o /tollgate:abandon #N» (m12);
  - tutti i task `done` in `execution`: `/tollgate:finish`; fase `review`: secondo lo stadio dell'ultimo ciclo (`review prepare`, lancio del verificatore, `finish open-pr`); fase `pr_open`: «PR #n aperta: attendi il gate; per correggere /tollgate:start #N --reopen-execution; se il predefinito è avanzato /tollgate:sync»;
  - ciclo `needs_fix`: `task start --from-findings <ciclo>`.

- [ ] **Step 1: Test** `test_checkpoint.py`: `test_steps_use_program_command` (ogni comando nelle righe di `next_step` ha la forma di `program_command`; vincolo (2)); `test_prepared_review_not_reprepared` (riga 133); `test_fix_rounds_cap_asks_user` (m12); `test_review_phase_steps` (tre stadi); `test_pr_open_step`; `test_needs_fix_points_to_from_findings`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: prossimo passo per revisione finale, PR e tetti».

---

