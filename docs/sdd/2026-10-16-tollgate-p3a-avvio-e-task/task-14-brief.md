### Task 14: Criteri, revisione 22 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p3a.py`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 22), `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «criteri di P3a → test» nel piano principale; i contratti reali P3a → P3b/P3c/P4.

- [ ] **Step 1: Test dal programma vero** (`test_criteria_p3a.py`, `FlowLab` più `hooks/run` reale come in `test_criteria_p2.py`):
  - `test_start_from_wrapper_flow` (criterio 1): `PreToolUse Bash` di `start 7` attraverso `hooks/run` registra il segnale, poi `bin/tollgate start 7` → 0;
  - `test_task_cycle_end_to_end` (criteri 4 e 38): `task start 1`, `PreToolUse Agent` con il nome del brief → 0, `SubagentStart`, commit, `verify`, `SubagentStop` con il report → task in `review`, `review-prepare`, `SubagentStop` del revisore con il verdetto → `approved`, `task done` → `done`.
- [ ] **Step 2: Matrice.** Per i criteri di P3a scrivere nel piano principale la tabella «Prove dei criteri di P3a» (formato `file::Classe.metodo`), con «Resta a» per le parti di P3b, P3c e P4:
  - 1: senza la proposta d'adozione eseguita (P3b `adopt`);
  - 4: parte `task`;
  - 18: `reviewer_standard`;
  - 22: tetto;
  - 28: senza «interruzione dopo `finish check`» (P3b);
  - 38: `task start` e unione; `final_specialist` a P3b;
  - 39: `status`;
  - 40: revisore del task; verificatore a P3b.

  Un criterio senza test è un buco: si aggiunge il test nel modulo che possiede il codice.
- [ ] **Step 3: Revisione 22 della spec**:
  - le decisioni 2-22 di questo piano nelle sezioni pertinenti: 3.1 (segnale della CLI, `act apply` senza id, `start` con `--confirm` e `--reopen-execution`), 6.1 (passi e codici d'uscita, percorso del worktree, `exclude`), 6.3 (instradamento, skill assenti, prenotazione, verdetto effettivo), 8.4 (`act apply`, riga «programma»), 5 (tetto e fase), 11.1 (intervallo di Superpowers), 11.3 (involucro della statusline), 12.2 (migrazione 3), 0 (checkpoint non committato);
  - nota M3 in 0 («sessione viva»): `Read`, `Grep` e `Glob` non aggiornano la vita, per non lanciare Python a ogni lettura; un implementatore che legge per più di `stale_minutes` senza altri strumenti risulta fermo;
  - sezione 16: esiti V1-V5;
  - riga 22 nella sezione 20.
- [ ] **Step 4: Piano principale**:
  - «Stato»: P3a chiuso sul ramo, merge in attesa dell'OK dell'utente, con il numero di test;
  - sezione 3: pacchetto `tollgate_flow` con i moduli reali, e i contratti P3a → P3b/P3c/P4 con i nomi reali, tra cui `APPLIERS`, `checkpoint.CAPS`, `prereq.GATE_FILES` e `.github/tollgate/VERSION` per P4;
  - i vincoli per P3b e P3c emersi qui.
- [ ] **Step 5: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi.

```bash
git add tests/test_criteria_p3a.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "tollgate P3a: prove dei criteri, spec rev 22, piano principale"
```
wrote /home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p3a/.superpowers/sdd/2026-10-16-tollgate-p3a-avvio-e-task/task-14-brief.md: 39 lines
