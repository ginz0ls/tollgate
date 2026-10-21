# Revisione Task 8: `reopen spec|plan` (dfe3938..543d29a)

### Aderenza
- ✅ D5: `subagents.in_use` (`bin/tollgate_core/subagents.py:118-134`) è la regola unica; `sync._in_use` (`sync.py:132-146`) la usa e i due messaggi sono identici carattere per carattere a quelli prima (diff letto; `tests.test_sync` verde, rilanciato: 36 test OK con `ReopenTest`). Config caricata solo con un subagente in corso, come prima.
- ✅ `reopen` indica `/tollgate:resolve writer` (`l2acts.py:289-291`); test del task `pending` con commit presente (`tests/test_l2acts.py` test_reopen_refused_with_running_task_or_writer).
- ✅ Decisione 12: motivo obbligatorio, fasi ammesse, solo L2 per spec, giro aperto `superseded`, `reset_plan`, causa `reopen_*`, file di approvazione lasciati come storico. Sospensioni non toccate (nessun codice le tocca).
- ✅ Decisione 27: in `blocked` rifiuta con rimando a `/tollgate:resolve <id>`; `set_phase` fuori transazione.
- ✅ D20: atti dall'hook del banco e `actapply` con `now=fl.now`.
- ✅ Review Focus 1 e 2 attraversano davvero hook (`pre_edit`, `post_edit`, `SubagentStop` via `report_round`), `audit prepare`, `finish check` e `task start` dalla CLI; asserzioni su `sha` nuovo, spec di nuovo bloccata (exit 2), `approvals` senza `[no]`, nessun `out_of_scope`, scope col file nuovo, task `pending`, brief del task 2 con `docs/uso.md`.
- ✅ Rischio 1: ordine `reset_plan` poi `set_phase` giusto. `reset_plan` ritorna `[]` se `plan_sha` è già `None`, quindi un secondo `reopen` dopo un'interruzione a metà riparte senza errori (`scope.py:26`); `supersede` è idempotente. Non c'è un test dell'interruzione (Minor 2).
- ✅ Rischio 3: `reopen plan` in L1 da `execution` e nuova registrazione con `post_edit` coperti (test_reopen_plan_l1_from_execution).
- ⚠️ Rischio 2 (sospensioni): non c'è alcun test che dopo `reopen` `audits.suspended` resti invariato (Minor 1).

### Punti di forza
Regola estratta nel modulo che possiede le query, senza cambiare i testi di `sync`; rifiuti prima di qualsiasi scrittura; test end-to-end veri; report onesto.

### Rilievi
**Critical:** nessuno.

**Important**
1. `bin/tollgate_flow/l2acts.py:302-305`: il messaggio di `reopen plan` in L1 dice «poi `audit prepare`», ma `audit prepare` rifiuta in L1 (`audit.py:399`: «l'audit di spec e piano è di L2»). In L1 l'istruzione è sbagliata; la parentesi «in L1 il piano corretto si registra da solo» compare anche in L2 dove è fuori luogo. Correggere: il messaggio dipende da `work["level"]`: L1 «correggi il piano: si registra da solo alla modifica»; L2 «correggi il piano, poi audit prepare». Aggiungere l'asserzione nel test L1.

**Minor**
1. Nessun test che `reopen` lasci intatte le sospensioni (decisione 7, rischio 2): in `ReopenTest` scrivere `audits.suspend` prima e confrontare `audits.suspended` dopo.
2. `l2acts.py:279`: `_cfg(state, work)` carica la config sempre, vanificando il `load_config` pigro di `in_use`; una config non valida blocca `reopen` anche senza subagenti in corso (e il rifiuto non dipende dalla regola condivisa). Passare un lambda che chiama `_cfg`.
3. I due testi di rifiuto (task / implementatore) sono duplicati tra `sync.py` e `l2acts.py` salvo il suffisso `/tollgate:sync` o `/tollgate:reopen`: una sola funzione di formattazione con il suffisso come parametro eviterebbe la deriva.
4. Nessun test dell'interruzione fra `reset_plan` e `set_phase` (secondo `reopen` che riparte).

### Valutazione
**Qualità del task:** Da correggere (leggermente). **Motivo:** logica, ordine delle scritture e test end-to-end solidi e la regola con `sync` è davvero condivisa; resta il messaggio errato di `reopen plan` in L1 (Important 1).
