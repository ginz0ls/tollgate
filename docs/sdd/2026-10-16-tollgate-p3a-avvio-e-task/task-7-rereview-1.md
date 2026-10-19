# Ri-revisione giro 1, Task 7 (17f77db..59c925c)

### Verdetti sui rilievi
1. **task_done / review_prepare non legati a git.head e al worktree pulito**: INDIRIZZATO.
   `taskcmd.py` `_range` ora va dal genitore del primo commit del task alla punta (`git.head`), non più a `commits[-1]`; `review_prepare` chiama `_ensure_clean` prima del range e registra la punta come SHA; `task_done` chiama `_ensure_clean` e poi confronta `review_sha` con `git.head(wt)`. Un commit fuori da `tasks.commits`, un `reset --soft` + nuovo commit, file modificati o nuovi non committati non chiudono più il task. Restano esclusi solo `review.output_dirs` e `.tollgate-run/`; gli ignorati non compaiono in `status --porcelain`. Test: `test_done_refuses_commit_outside_task_commits`, `test_done_refuses_soft_reset`, `test_done_refuses_uncommitted_changes` (modificato e nuovo), `test_review_prepare_refuses_dirty_worktree`, `test_review_prepare_uses_head_as_sha`.
2. **`changes` con soli rilievi bloccanti scartati diventava approved**: INDIRIZZATO.
   `verdicts.py`: con `standard`, `declared == "changes"`, nessun blocker/major valido, `spec_compliance` vuoto e almeno un rilievo scartato con `_may_block` -> `TaskVerdict(False, ..., None, declared)`, quindi veto e dopo 2 veti `needs_you` (`task_verdict.py` invariato in quel ramo). Soli minor (validi o scartati) restano `approved` (criterio 40); `dropped` passa da `verdicts` a `record task_verdict`, `apply._OPS`, `tasks.set_verdict` e `_log` (evento `task_change`). La scelta fail-closed per gravità illeggibile (`_may_block` vero se non è `moderate`/`minor`, incluso un rilievo non-dict) è coerente con la decisione del controller: un `changes` che non riesce a dimostrare di essere solo minor non passa. Senza `standard` il verdetto resta `changes` (testato). Test: `test_changes_with_only_dropped_blocking_findings_is_invalid` (4 forme di scarto + misto minor/regola vuota), `test_dropped_minor_finding_does_not_invalidate`, `test_dropped_blocker_with_a_valid_blocker_stays_changes`, `test_changes_with_dropped_blocker_kept_without_standard`, `test_dropped_blocker_vetoes_and_dropped_count_in_event`.

### Modifiche ai test esistenti
`ReviewDoneTest.to_review` committa il piano: necessario perché il worktree sia pulito, il contenuto del piano non cambia (il controllo su `plan_sha` resta valido). In `test_verdicts` l'asserzione rimossa (`changes` con solo scartato -> approved) è l'esatto comportamento invertito dalla decisione del controller, ora coperto dal test nuovo. Nessuna regressione nascosta.

### Danni nuovi nel diff della correzione
Nessuno. Minor non bloccante: `_review_prepare` carica la config due volte (una già presente, una dentro `_ensure_clean`); una riga di `test_check_task_verdict.py` supera la lunghezza usuale.

### Osservazioni fuori ambito
Un verdetto dichiarato `approved` con un rilievo blocker scartato resta `approved` (la regola nuova riguarda solo `changes`): coerente con la decisione, il revisore ha dichiarato di approvare.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
