# Ri-revisione giro 1 - Task 8

### Verdetti sui rilievi
1. **Messaggio di `reopen plan` in L1 con `audit prepare` e frase L1 anche in L2**: INDIRIZZATO. `l2acts.py` (diff, ramo `nxt`) distingue L1/plan, L2/plan e spec. Asserito in `test_reopen_plan_l1_from_execution` (contiene "si registra da solo", non "audit prepare"), `test_reopen_plan_then_reapprove_registers_new_scope` (L2: "audit prepare", "avversario del piano", non "si registra da solo") e nel test spec.
2. **Test che `reopen` lascia intatte le sospensioni**: INDIRIZZATO. `test_reopen_keeps_audit_suspensions` copre reopen plan e reopen spec con sospensioni ADV e LENS.
3. **Config caricata solo se serve**: INDIRIZZATO. `lambda: _cfg(state, work)` passato a `subagents.in_use`, che chiama `load_config` solo con subagenti in corso (`subagents.py:128`). `test_reopen_loads_config_only_for_a_running_subagent` copre entrambi i casi. Eseguito `tests.test_l2acts.ReopenTest`: 11 OK.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
