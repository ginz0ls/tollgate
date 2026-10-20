# Revisione Task 4 (5fd29f7..0e7558c)

### Aderenza
- ✅ Fonte unica: `_common.py` non ha più la logica di `scope_exempt`/`locked_docs`/`is_docs_md`/`_is_registered_plan`/`commit_violations` (restano alias e deleghe, `_common.py` diff); `Ctx.guard_config` e `Ctx.waiver_file` delegano (`context.py`). Nessuna duplicazione letterale (`_ORDER`/`_rank` spostati, non copiati).
- ✅ Strati: `violations.py` importa solo `tollgate_analysis` e moduli di `tollgate_core`; nessun import di checks/hooks/flow.
- ✅ Test degli hook invariati: il diff dei test tocca solo `tests/test_verify.py` e `tests/test_violations.py` (nuovo).
- ✅ Equivalenza di comportamento (controllata riga per riga): `ctx.component(n)` = `bool(config.data["components"].get(n, True))` e `diff_violations` usa `components.get(n, True)` con lo stesso dizionario passato da `commit_violations` (C15); `output_excludes(ctx)` = `config.output_excludes(ctx.config)`; `ctx.scope(work)` = `scope.paths(conn, work["id"])` per work non nullo; `ctx.cfg(x)` = `config.get(x)`; deroghe (`waivers.unresolved(.., waiver_file(work))`), piano registrato e `locked_docs` identici.
- ✅ `run_gate`: `produced_by` passato alle ricevute (`verify.py` execute), `states`/`junits` per comando, `sha None` per non eseguito con motivo in `lines` (C17), `extra` accodato al gate. `run_verify` passa dagli stessi passi (`_guarded`/`_gate`), `strict=False` conserva il caso «nessun comando» = ok; prefisso `tollgate verify:` invariato.
- ✅ `dod_commands`: dod dei profili attivi non già nel gate, nome `profile:<p>:<c>`.
- ✅ Test richiesti presenti; `test_same_result_as_hook` asserisce attesi espliciti e uguaglianza con `commit_violations` (C23). Il test del piano registrato è significativo: la fase `execution` blocca il piano, quindi l'esenzione viene da `is_registered_plan` e non dalla regola dei docs.
- ⚠️ Non rilanciati: suite completa (1088 OK riportati), nessun dubbio preciso che lo richiedesse.

### Punti di forza
Spostamento fedele e minimo; alias che mantengono i nomi per i chiamanti esistenti; test in più (`components` assenti = acceso, dod già nel gate, nessun comando, worktree sporco).

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `bin/tollgate_core/verify.py` (riga con `nessun riferimento remoto da cui leggere tollgate.toml` dentro `GateRun(False, [...])`): riga oltre 100 caratteri dopo la riscrittura; andare a capo.
2. `tests/test_violations.py:5`: importa `with_scope`, `write_waiver` da `tests.test_check_writes`, accoppiando due moduli di test; e `lab._base` (privato) alla riga ~46. Meglio spostare gli helper in `tests/hookkit.py` quando conveniente (non ora: vincolo di non toccare i test degli hook).
3. ⚠️ `verify.py` `execute`: un comando `dod` non configurato produce ricevuta `unverified` e `good=False`, quindi `run_gate.ok` è False. È coerente con il gate, ma il Task 6 deve sapere che un `dod` di profilo senza comando rende rosso `finish check` (se non voluto, va distinto lì).
4. `states`/`junits` sono indicizzati per nome: due comandi con lo stesso nome (es. gate e dod con nome uguale) si sovrascrivono; `dod_commands` già li esclude, quindi caso teorico.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** spostamento fedele con deleghe, strati rispettati, hook e test invariati, `run_gate` conforme a C17 e al brief; solo rifiniture minori.
