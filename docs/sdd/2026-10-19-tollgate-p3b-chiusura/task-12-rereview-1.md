### Verdetti sui rilievi
1. **(Important) Le approvazioni contavano come prova senza verifica** — INDIRIZZATO.
   `adopt.py` `_approval` (diff, righe ~150-160): `kind` coincidente, `path` relativo sicuro (`_safe_rel`), con `doc` il target deve essere proprio quel documento, e `approvals.is_current(header, _blob(main, sha, target))`; documento assente => `_blob` None => non valida. `_gather` (righe ~218-225): `plan-approval` valutata solo con piano scelto e spec valida, `doc=plan[0]`; `spec_sha` presente e diverso dal blob della spec verificata => `plan_header=None`. `_phase` (194-206) scende quindi a `spec_audit`/`approval`/`plan`. Logica condivisa: `approvals.is_current` (approvals.py) usata anche da `finishcheck._approvals`, nessuna duplicazione. Test: `test_l2_superseded_or_mismatched_approvals_go_back` copre piano modificato, `path` diverso, `spec_sha` diverso, spec modificata, spec assente (fasi e assenza di scope attese corrette); `test_l2_with_plan_approval_stays_execution` usa sha veri e `spec_sha`. RED/GREEN riportati nel report e coerenti col diff.
2. **(Minor) Righe «PR aperta» e «tetto ripristinato» solo a passo riuscito** — INDIRIZZATO.
   `step` ritorna il sentinella `FAILED` nel ramo di errore; le due righe sono emesse solo se `is not FAILED` (adopt.py 335-341). `test_pr_and_cap_lines_only_when_step_succeeded` simula i due fallimenti e verifica codice 4, assenza delle righe e presenza di «registrazione incompleta: PR».

Controllo `finishcheck`: `header["sha"] != blob` diventa `not is_current(header, blob)`; `blob` lì è sempre una stringa (il GitError è già gestito prima), quindi `is_current` equivale a `==`: comportamento invariato.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
