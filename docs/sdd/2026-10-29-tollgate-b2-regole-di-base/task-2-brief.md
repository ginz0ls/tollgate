### Task 2: La suite non dipende dall'interruttore vero

**Files:**
- Modify: i file di `tests/` che lo Step 2 trova, compreso `tests/test_eval_cases.py` se una prova a secco cambia esito (nessun file di `bin/`)
- Test: gli stessi

**Interfaces:**
- Consumes: `tests/hookkit.Lab(plugin_root=…)`; `mock.patch.object(taskcmd.db, "BIN_PATH", …)`; `make_root` di `tests/test_check_research_gate.py`; il comando `research submit` (B1).
- Produces: nessuna interfaccia; la garanzia che il Task 5 può accendere l'interruttore nel repo senza rompere la suite.

- [ ] **Step 1: Interruttore acceso per prova, mai committato.** Scrivi `skills/rules-base/SKILL.md` con `---\nname: rules-base\napproved: 2026-01-01\n---\n` nel worktree, **senza** `git add`.
- [ ] **Step 2: Misura.** `tests/run` completo (in background, aspetta l'esito sul file d'uscita). Elenca nel report ogni test che fallisce, con la riga dell'errore. Tre fallimenti sono **attesi** e non vanno toccati qui: `tests/test_docs.py` `test_every_skill_documented` (la skill di prova non è documentata) e le due asserzioni di `tests/test_b1_scripts.py` alle righe 169 e 555 («il repo non deve cambiare»); li sistema il Task 3.
- [ ] **Step 3: Togli il file di prova** (`rm skills/rules-base/SKILL.md` e la cartella vuota) e controlla con `git status` che non resti niente.
- [ ] **Step 4: Rendi esplicita la radice** in ogni altro test dello Step 2 che presume l'interruttore spento, con la priorità della decisione 7 (a, b, c). Un test che con l'interruttore acceso fallisce per un altro motivo è un difetto da riportare con DONE_WITH_CONCERNS, non da correggere qui.
- [ ] **Step 5: Ripeti la misura.** Di nuovo il file di prova, di nuovo `tests/run` (verde salvo i tre attesi), di nuovo via il file. Poi `tests/run` senza il file: verde.
- [ ] **Step 6: Commit** «tollgate B2: test indipendenti dallo stato dell'interruttore nel repo».

---

