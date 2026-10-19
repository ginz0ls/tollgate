# Revisione Task 6 (P3a): `task start` e giri di correzione

### Aderenza
- ✅ Migrazione 3 (`db.py` SCHEMA_V3: review_sha, review_findings default '[]', reserved_at), solo in avanti, test v2→v3 con copia e DB nuovo senza copia.
- ✅ `tasks.py`: `assign` con coalesce su `reviewer_type`; `take_pending(number=)` che azzera `reserved_at`; `reserve`, `clear_reservation`, `set_skills_required`, `set_review_prep` (azzera verdict e findings), `set_verdict` (stato invariato, evento `task_change`, outcome validato).
- ✅ `git.blob_text` (cat-file, None se manca/binario); decisione 20 nel complesso rispettata con ripiego su file del worktree solo se `blob_sha` coincide (`taskcmd.py` `_plan_text`).
- ✅ `apply._subagent_start`: la ripresa passa il numero; fallback `or task` se il task non è più pending.
- ✅ `taskcmd`: L0 rifiutato, fase execution, `pending` solo senza `--fix`, giro >=5 -> `needs_you` (dopo l'apertura la fase è `blocked`, quindi nessun blocco duplicato alla riga successiva), giri 1-3 `resume` con stesso nome, 4-5 `launch` `-rN` con `model: inherit`, skill assenti tolte con la stessa lista del brief (una sola fonte), `assign(pending=...)` (vincolo 7), name del brief = `tasks.implementer` (vincolo 1), strati rispettati (solo core + analysis).
- ✅ CLI: exit 0 / 1, messaggio in italiano.
- Test: copertura ampia dei casi richiesti dal brief più extra utili; evidenza RED/GREEN credibile (848 test su due interpreti).

### Valutazione dei dubbi del report
- (a) C10: scostamento accettabile e sicuro. Dopo `fix` -> `report_done` il task è in `review` con `review_code` e `review_sha` NULL: non è riconoscibile come «in attesa» con il codice del giro precedente, e un secondo `--fix` è rifiutato (`taskcmd.py:_check_state`, ultimo controllo) finché `review-prepare` non imposta `review_sha`. Nessun giro consumabile senza nuova revisione. Residuo: `verdict` resta `changes` (stale) mentre il carry diceva di azzerare solo con `set_review_prep`: vedi Minor 1.
- (b) `PlanTask.test_files`: additivo, giustificato dal brief («voci `Test:`»); ok (vedi Minor 2 per il duplicato).
- (c) `blob_text` solo `cat-file` con ripiego in `taskcmd`: coerente con la decisione 20 e con la firma `(repo, sha)` del brief; ok. La logica di ripiego è in un solo punto.
- (d) Brief scritto prima delle transizioni: l'orfano è innocuo (`.tollgate-run/` ignorato, sovrascritto al tentativo successivo); ma il vero problema è l'ordine/atomicità delle scritture DB, vedi Important 1.
- (e) Giri 4-5 con più task `launch` dello stesso tipo: il rischio è chiuso a monte da `bin/tollgate_checks/agents.py:67-73`: `pre_agent` ammette il lancio solo col `name` del task a numero più basso tra i `launch` del tipo (`cand[0]`), quindi `take_pending` (ORDER BY number) associa lo stesso task. Non è un difetto di questo task; vale la stessa garanzia per i giri 0.

### Punti di forza
- Brief, `skills_required` e riepilogo derivano dalla stessa `Routing`; validazione dello stato prima di toccare il filesystem o il DB; errori `sqlite3`/`GitError`/`TransitionError` convertiti in `TaskError`.
- Test del giro con verdetto fresco a ogni round (`test_fix_needs_changes_verdict_and_a_fresh_one_each_round`) e della presenza del blob negli oggetti.

### Rilievi
**Critical:** nessuno.

**Important**
1. `bin/tollgate_flow/taskcmd.py:150-154` (fine di `_task_start`): `set_skills_required`, `task_event` e `assign` sono tre transazioni separate. Se `assign` (o `task_event`) fallisce dopo la precedente (`sqlite3.OperationalError` per lock con un hook concorrente, plausibile: gli hook scrivono sullo stesso DB), il task resta `running` senza `pending` e senza `implementer`: `task start` non è ripetibile (richiede `pending`) e `pre_agent` nega ogni lancio. Correggere avvolgendo le tre chiamate in un solo `with db.tx(conn):` (le funzioni si uniscono a una transazione aperta, `db.tx` in `db.py`), così l'assegnazione è tutto-o-niente; aggiungere un test che forza il fallimento di `assign` e verifica stato `pending` invariato.

**Minor**
1. `bin/tollgate_core/tasks.py:~83` (evento `fix`): il verdetto `changes` resta dopo il giro, con `review_sha` NULL. Il consumatore corretto è `review_sha`, non `verdict`: il Task 9 (`next_step`: «review con changes -> task start --fix») e il Task 7 (`awaiting_review`) devono controllare anche `review_sha IS NOT NULL`, altrimenti suggeriranno un comando che poi viene rifiutato. ⚠️ non verificabile in questo task: ricordarlo nel carry dei Task 7 e 9 (o azzerare `verdict` nell'evento `fix` adattando il test esistente).
2. `bin/tollgate_analysis/plan.py:28-29`: la riga `test_files: list[str] = field(default_factory=list)` è duplicata (innocua per il dataclass, ma duplicazione letterale): toglierne una.
3. `taskcmd.py` `_task_start`: il brief è scritto prima di `set_skills_required` e delle transizioni; ordine più pulito sarebbe validare tutto, scrivere il brief e poi fare l'unica transazione (Important 1 la rende comunque coerente).

### Valutazione
**Qualità del task:** Da correggere (un solo Important, correzione piccola e localizzata).
**Motivo:** requisiti e carry rispettati e i dubbi (a)-(e) del report non nascondono difetti, ma la scrittura dello stato del task non è atomica e un fallimento a metà lascia il task bloccato in `running` senza assegnazione.
