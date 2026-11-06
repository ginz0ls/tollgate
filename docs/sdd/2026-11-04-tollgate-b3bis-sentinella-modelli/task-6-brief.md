### Task 6: Evidenze su `main` senza testo di terzi

**Files:**
- Modify: `spikes/b1/flowreg.py` (`external_skill`, `togli_pagine`), i `.jsonl` di `docs/verifiche/evidenze/` che `togli-pagine` cambia, la sezione «Anonimizzazione» (o, se manca, una riga in fondo) dei rapporti `docs/verifiche/2026-10-27-b1-prova-flusso.md`, `docs/verifiche/2026-10-29-b2-prova-flusso.md` e `docs/verifiche/2026-10-21-p4-prova-flusso.md` (evidenze di gh-p4)
- Test: `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: `flowreg.togli_pagine(paths) -> int`, `flowreg.MAX_WEB_RESULT` (5000), `flowreg.external_skill(text)`, `flowreg.web_results`.
- Produces: `flowreg.tollgate_skill(path: str) -> bool`; l'iteratore interno della decisione 11 (nome a scelta dell'implementatore, per riga: oggetto, blocco, tipo), usato da `togli_pagine` per sostituire; `flowreg.third_party_blocks(path) -> list[str]` (in sola lettura, una voce `<riga>: <tipo> (<caratteri>)` per blocco, avvolge l'iteratore; la usa il test).

- [ ] **Step 1: I test che falliscono** (`tests/test_b1_scripts.py`):
  - `test_tollgate_skill_by_folder_not_word` (`…/Plugin IT workflow/skills/execute` → di tollgate; `…/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/writing-plans` → esterna; `…/plugins/cache/x/tollgate/0.2.0/skills/start` → di tollgate; `/tmp/tollgate-b1/plugin/skills/start` → di tollgate; `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p4/skills/execute` → di tollgate; `/home/x/altro/skills/init` → esterna; il risultato non dipende da `ROOT.name`);
  - `test_external_skill_keeps_tollgate_execute` (un blocco lungo della skill `execute` di questo repo non si tocca);
  - `test_session_start_output_of_other_plugins_replaced` (uno stream finto con un'uscita di hook `SessionStart` lunga di un altro plugin e una di `hooks/run` di tollgate, nella forma di `gh-p4/flusso/passo3.jsonl:10`: `togli_pagine` sostituisce solo la prima, in tutti i campi che la contengono; un'uscita corta di terzi, di 1129 caratteri, si sostituisce anch'essa; quella il cui `additionalContext` comincia con `tollgate:` resta; una seconda chiamata di `togli_pagine` sullo stesso file restituisce 0 e `third_party_blocks` sul file ripulito è `[]`);
  - `test_committed_evidence_has_no_long_web_results` **si estende**: su ogni `.jsonl` tracciato in `docs/verifiche/evidenze/`, `third_party_blocks(path) == []` (le skill di terzi ovunque, non più solo in `evidenze/b3/`; gli hook di terzi; i risultati web lunghi).
- [ ] **Step 2: Verifica che falliscano.** Il test esteso fallisce sui file di B1, B2 e gh-p4 trovati nella preparazione del piano.
- [ ] **Step 3: Correzione e pulizia.** `external_skill` usa `tollgate_skill`; `togli_pagine` sostituisce anche le uscite di hook della decisione 11. Poi `python3 -B spikes/b1/flowreg.py togli-pagine` sui file che il test segnala, e controllo del risultato (ogni file resta JSONL valido, `tool_use` e prompt restano). Nei tre rapporti una riga: «Il <data> il testo di skill, pagine e hook di terzi è stato sostituito da un segnaposto (`flowreg.py togli-pagine`); i commit precedenti lo contengono ancora.» Se un test esistente legge un file ripulito (`grep -rn evidenze tests/`), si controlla che resti verde.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_b1_scripts tests.test_p4_flowstate tests.test_p5_scripts tests.test_eval_run`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: evidenze delle prove senza testo di skill, pagine e hook di terzi».

---

