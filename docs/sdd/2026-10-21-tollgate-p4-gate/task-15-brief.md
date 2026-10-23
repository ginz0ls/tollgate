### Task 15: Skill `init`, skill aggiornate, contratto tra skill e codice

Le skill si scrivono dopo i sottocomandi (lezione di P3b): ogni codice e ogni passo citati vengono dalle costanti dei Task 7-13.

**Files:**
- Create: `skills/init/SKILL.md`
- Modify: `skills/finish/SKILL.md` (voci del gate in `finish check`, «da leggere» e «informative»), `skills/start/SKILL.md` (avvisi di protezione e di modalità), `skills/status/SKILL.md` (issue di sentinel), `skills/execute/SKILL.md` (`task start --from-gate` legge lo SHA del commento), `tests/test_skill_contract.py`, `tests/test_manifest.py`

Contenuto di `skills/init/SKILL.md` (anche il modello, «solo proposta»): lancia `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate" init --propose` (chiedendo prima all'utente i servizi dei test, 9.6, e il ritmo di merge per la stima); riferisce la modalità misurata; con «non determinata» chiede all'utente di rilanciare con le sue credenziali (`! …`); elenca i passi dell'utente dal `README.md` della proposta: copiare `files/` nel repo (i file di tollgate sono protetti: li copia l'utente), committare sul predefinito **prima** della protezione, poi lanciare `protect.sh` in `protected`; consiglia il token separato per l'agente; `--update` prepara un ramo `tollgate-config/<versione>` che l'utente apre come PR. Codici: `- **0, …**` proposta scritta; `- **1, …**` rifiuto con il motivo. Mai copiare i file al posto dell'utente, mai lanciare `protect.sh`.

- [ ] **Step 1: Test** `test_skill_contract.py`: la riga `init` nella tabella `(skill, sezione, modulo, costanti)` con `init.OK`, `init.REFUSED`; ogni sottocomando nominato nelle skill (`init`, `gate`) esiste nel parser; nessuna skill contiene «P4». `test_manifest.py::test_init_model_invocable`.
- [ ] **Step 2: Fallimento, scrittura, `tests/run`;** se `claude` è disponibile `claude plugin validate --strict .` (esito nel report).
- [ ] **Step 3: Commit** «tollgate P4: skill init e skill aggiornate, contratto tra skill e codice».

---

