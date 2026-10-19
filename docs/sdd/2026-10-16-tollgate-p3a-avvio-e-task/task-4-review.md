# Revisione Task 4: `start` in ripresa (12.4), commit 4dd1782

### Aderenza
- ✅ Worktree assente: ramo esistente -> `worktree_add(new_branch=False)`; senza ramo -> `new_branch=True` da `work_base_sha`; `set_worktree` se il percorso cambia (start.py `_restore_worktree`, `_resume`; phases.py `set_worktree` + test C15).
- ✅ Rebase in corso e worktree sporco: solo avviso con la proposta, mai eseguiti (il test asserisce che il rebase resta in corso).
- ✅ Subagenti `running` di sessioni non vive -> `interrupt`; quelli di sessioni vive no; la sessione corrente è esclusa.
- ✅ Intenti `requested` e altra sessione viva -> codice 3 senza effetti collaterali, `--confirm` per procedere. Conferme valutate prima di toccare il worktree.
- ✅ Legame: `bind_session`, `mark_bound`, `active.register(force=True)`, `add_excludes`.
- ✅ Fase `review`/`pr_open`: riga con `--reopen-execution`; col flag `set_phase(execution, "start")` fuori da transazione (decisione 19; `subagents.interrupt` chiude la sua tx con `db.tx`, quindi nessun `in_transaction`).
- ✅ C4: rete assente, prerequisiti, stati non verdi, checkout sporco sono avvisi.
- ❌ Pulizia (spec 12.4 «`start` cancella log e file di contesto vecchi»; vincolo globale 3 «`start` pulisce `bound/`»): `_resume` non chiama `housekeeping.run` (lo fa solo `_create`). Vedi Important 2.
- ⚠️ Rifiuto con codice 1 se la ricreazione fallisce (`_restore_worktree` -> `_refuse`): non è fra i rifiuti ammessi da brief/C4. Dichiarato nel report e ragionevole (senza worktree non c'è dove entrare); da far confermare al controller.
- ⚠️ `issue.md` e gli altri file non tracciati di `.tollgate-run/<N>/` si perdono con un worktree ricreato e la ripresa non li riscrive (dichiarato; serve la rete). Nessun avviso all'utente: Minor 1.

### Punti di forza
- Ordine corretto: avvisi -> conferme (uscita 3 pulita) -> effetti.
- `_Steps` unifica le registrazioni indipendenti senza duplicare `step`.
- Refactoring di `_checks` verificato sul diff: stesso ordine di avvisi e conferme (checkout pulito, issue chiusa, stati con `strict=True`); `_Steps` allarga solo le eccezioni catturate (`TransitionError`, `GitError`); `issue_file` FAILED -> None come prima. Nessun cambio di comportamento per il Task 3.
- I test di ResumeTest asseriscono comportamenti reali (stato di subagente e task, fase, causa dell'evento, riga di `sessions`).

### Rilievi

**Important**

1. `bin/tollgate_flow/gitw.py:63` e `start.py` `_restore_worktree` (`gitw.worktree_prune(main)`): `git worktree prune` è globale. Verificato con un esperimento in scratchpad (git 2.47.3): con due worktree spariti, il prune toglie la registrazione di tutti, non solo di quello da ricreare. Un worktree altrui temporaneamente assente (disco smontato, cartella rinominata) perde la registrazione in silenzio. Senza prune (o `-f`) l'`add` fallisce («mancante ma già registrato»), quindi un rimedio serve, ma mirato. Correzione: togliere il prune e usare `worktree add --force` solo per il percorso registrato mancante (provato: `add -f ../w1 b1` riesce e lascia `w2` registrato), oppure tentare l'add e ricorrere a `-f` solo se fallisce con quel messaggio. Aggiungere un test con un secondo worktree spento che resta registrato.
2. `start.py` `_resume`: manca `housekeeping.run(conn, state, cfg, now=now)` con i suoi avvisi (come in `_create`). La ripresa è il caso comune di `start` ripetuto: senza la chiamata la pulizia di `bound/`, eventi, log, `ctx`, copie temporanee non avviene su una ripresa (spec 12.4 «Pulizia»; vincolo 3). Aggiungere la chiamata e un test (segnalino vecchio in `bound/` rimosso dopo la ripresa).
3. `tests/test_start.py` `test_resume_recreates_missing_worktree`: usa `git worktree remove --force`, che toglie anche la registrazione. Il caso per cui esiste il prune (cartella cancellata a mano o crash, registrazione stale; review-focus punto 3) non è mai esercitato. Cambiarlo con `shutil.rmtree(fl.wt)` (o coprire entrambi). Il report ammette anche l'assenza di RED: questo test è il minimo per provare il caso reale.

**Minor**

1. Dopo una ricreazione nessun avviso dice che `.tollgate-run/<N>/issue.md` (e brief/checkpoint non tracciati) sono andati persi: aggiungere una riga all'avviso di ricreazione.
2. `_restore_worktree` fallita: `_refuse(why)` scarta gli avvisi già raccolti (rete, prerequisiti). Includerli.
3. `test_pending_intent_needs_confirmation` non verifica che l'intento resti `requested` dopo `--confirm`; nessun test per la ricreazione fallita (codice 1).

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** requisiti funzionali e refactoring corretti, ma `worktree prune` globale tocca le registrazioni di altri worktree dell'utente, la pulizia di 12.4 / vincolo 3 manca nella ripresa e il caso di crash (registrazione stale) non è coperto da test.
