# Task 7 - revisione (d2c6a23..98994fc)

### Aderenza
- ✅ CHECK: `research_gate.py:19-20` componente `research_note`, order 25 (dopo `writes`, 20); eventi pre_edit, pre_bash, post_edit, post_bash (D3: il brief ne elenca due, il carry ne vuole quattro).
- ✅ Nessuna decisione per lavoro assente, `research = 0`, fase diversa da `execution` o componente spento (`research_gate.py:90-93`, `runner` salta il componente spento).
- ✅ Esclusioni D11 identiche per L0/L1/L2: `_counts` (`:25-28`) è usato da `_edit_work` e `_bash_work` prima di distinguere il livello.
- ✅ L0: avviso `inject` in pre, `research_reminder` {task: None} in post, una volta per lavoro (`:95-98`, `:68-69`). Solo sessione principale e solo Edit/Write.
- ✅ L1/L2: nota valida -> niente; interruttore acceso -> `deny`; spento -> `inject` una volta per task, conteggio dopo l'ultimo `plan_reset` (`_common.py:193-208`, helper unico D11 usato da `_reminded` e `_problems`).
- ✅ D3: l'avviso non si registra in pre; il post non registra per `PostToolUseFailure` (`:87`).
- ✅ D12: `_abs/_braces/_expand/_write_paths` spostati in `_common.py` con corpo identico (verificato sul diff); `restores_from_index` salta il comando (`:42`).
- ✅ B1-V7: `research.enforced` sul testo di `plugin_root / RULES_BASE`, assente = spento. D4: solo `plugin_root` in `Lab`.
- ✅ Testi: rifiuto con prefisso esatto, comando di `submit_command`, problemi dell'ultima `research_note` non ok del task dopo l'ultimo `plan_reset`; avviso con prefisso esatto.
- ✅ `pre_bash` solo con `agent_id` (`:80`) e solo con bersaglio nel worktree non escluso. Verificato a mano che `research submit` (heredoc) del rifiuto non è fermato dal gate, mentre `echo > src/app.py` e `tee` sì.
- ✅ Test: ci sono tutti i nomi del brief (14 voci) e del carry (`test_reminder_not_consumed_by_other_deny`, `test_refusal_ignores_problems_before_plan_reset`, `test_bash_restore_not_denied`, `test_bash_relative_target_resolved`) più extra. Il «test di rimozione non eseguito» del report non corrisponde a un test richiesto: non manca nulla.
- ✅ Review Focus 4 e 5 coperti (`test_legacy_work_never_reminded`, `test_l0_grown_to_l1_blocks`, `test_round4_new_implementer_keeps_valid_note`, `test_resubmitted_invalid_note_blocks_again`).
- ✅ Strati: il modulo importa solo `tollgate_analysis`, `tollgate_core`, `tollgate_hooks.model`, `._common`. Nessun `__pycache__` tracciato né nel working tree.
- Errori: un'eccezione in `decide` in un pre diventa deny del runner (`runner.py:305-311`), un errore di DB fa `_fail`: coerente con spec 7.1. Letture di `SKILL.md` fallite -> interruttore spento (fail-open, previsto dal brief «assente -> spento»); `GitError` e `BashParseError` in `_bash_work` -> nessuna decisione, perché `bash_rules` (order 20) nega già questi casi.

### Punti di forza
- Verdetto calcolato in un'unica funzione `_verdict`, riusata in pre e post: pre e post non possono divergere.
- Helper `work_events` unico, con test sul reset del piano; early return prima delle query nel caso comune (nota valida).
- Spostamento di codice in `_common.py` a comportamento invariato; suite di `bash_rules` verde.
- Test con mutazione dichiarata sul ramo `PostToolUseFailure`; copia temporanea della radice per l'interruttore.

### Rilievi
**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. `tests/test_check_research_gate.py:~150` (`test_reminder_not_consumed_by_other_deny`): la riga `assertEqual(events("research_reminder"), [])` è ripetuta due volte di fila. Toglierne una.
2. Test mancanti, senza che il comportamento sia sbagliato: fase diversa da `execution` (nessuna decisione), L2 (solo L1 provato), `PostToolUseFailure` di Bash (provato solo per Write), esenzioni di `docs/` e `.tollgate-run/` via Bash. Il ramo `work["phase"] != "execution"` (`research_gate.py:91`) non ha nessun test che lo faccia fallire se tolto.
3. `bash_rules.py:16`: `_braces` è importato con `# noqa: F401` solo perché `test_check_bash` lo prende da lì. Meglio far importare il test da `_common` (la regola di non toccare test esistenti non vale per un import spostato) o lasciare il commento che lo dice.
4. `research_gate.py:62-64`: `_rules_enforced` inghiotte `OSError` (permessi, non solo file assente) come «spento». Se `rules-base` esiste ma è illeggibile, il blocco cade senza traccia. Distinguere `FileNotFoundError` (spento) da altri `OSError` (lasciar salire: il runner fa deny con messaggio).
5. Due modifiche in parallelo prima del primo post ricevono entrambe l'avviso (il record è a post): è la conseguenza voluta di D3, nessuna azione.

### Valutazione
**Conformità alla spec:** conforme (tutti i requisiti del brief e del carry presenti e provati).
**Qualità del task:** Approvato. **Motivo:** logica corretta, coerente con i controlli vicini e coperta dai test richiesti; restano solo rifiuti minori sulla copertura e sull'errore di lettura di `rules-base`.
