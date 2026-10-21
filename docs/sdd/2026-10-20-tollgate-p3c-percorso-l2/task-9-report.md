# Task 9, report

## Implementato
- `bin/tollgate_flow/l2tree.py` (nuovo): lettura dall'albero di un commit di approvazioni e report (`listing`, `spec_approvals`, `locate`, `collect`); legge il testo solo delle approvazioni delle spec, del `plan-approval.md` del lavoro e dei report delle due cartelle che servono. Mai il disco (D3).
- `tollgate_analysis/approvals.py`: `report_listing(paths, folders)`.
- `start.py` + `cli.py`: `start N --spec PERCORSO` (decisione 14). Convalida (relativo, normalizzato, sotto `docs/superpowers/specs/`, senza `..` né caratteri di controllo, presente sulla punta del predefinito = `base_sha`); approvazione con `sha` attuale: L2, `from_approved_spec`, fase `plan`, riga «spec approvata: <percorso> (approvazione in <cartella>)»; `sha` vecchio: uscita 3 (confirm) e con `--confirm` L2 con `spec_path` in `spec_audit`; senza approvazione: rifiuto. `--spec` in ripresa: avviso. Con `--spec` il livello è almeno L2.
- `finishcheck.py`: `_approvals` usa `approvals.check_l2` sui file di HEAD; `_own_document` ora usa l'approvazione trovata (anche di un'altra issue), calcolata una volta; la docstring non parla più dell'esenzione di `reviews/<N>/` (D18a).
- `openpr.py`: `_l2_dirs` (cartelle 18.1 e `spec_audit` dall'approvazione trovata a HEAD = SHA spinto; solo con `spec_path`).
- `adopt.py`: `_l2_proofs`/`_approved_elsewhere` (fetta successiva con `plan-approval.md` corrente) e fase `plan`/`approval` secondo `plan_adversary` (decisione 16).

## Test (RED poi GREEN)
RED registrati prima del codice: `tests.test_finishcheck.L2ApprovalsTest` (5 fallimenti: dettagli `approvals`, report richiesti, fetta successiva), `tests.test_openpr` (`L2FactsTest`: 2 fallimenti), `tests.test_adopt` (6 fallimenti: `approval` al posto di `plan`, fette successive), `tests.test_start.StartSpecTest` (`tollgate: error: unrecognized arguments: --spec ...`, 15 fallimenti + 1 errore).
`LaterSliceTest.test_later_slice_end_to_end` è stato scritto a codice già fatto; la prova che non è vacuo è una mutazione: con `_approved_elsewhere` che restituisce `None` fallisce con `(9,'L2','spec_audit',None) != (9,'L2','execution',SPEC)`.
GREEN: `tests/run` (python3.11 e python3 3.13.5): 1665 test, OK, entrambi.

Test nuovi: `test_start.StartSpecTest` (6 richiesti + `test_spec_forces_l2...` e `test_approval_only_on_the_local_disk...`), `test_finishcheck.L2ApprovalsTest` (`test_reports_required`, `test_complete_l2_is_green`, `test_kind_mismatch_is_false`, `test_must_have_tests_off` + fetta successiva, report con intestazione non valida, esenzioni), `test_openpr.L2FactsTest`, `test_adopt.AdoptL2Test`, `test_approvals.test_report_listing`, `test_criteria_p3c.LaterSliceTest`.
`test_later_slice_end_to_end` attraversa `hooks/run` e `bin/tollgate`: `start 9 --spec`, Edit della spec (deny, uscita 2), Write del piano, commit da Bash (PreToolUse/PostToolUse), `audit prepare` con giro `plan-adversarial` (SubagentStart/Stop), `approve plan` (atto + `act apply`), `task start`, `finish check` (voce `approvals` sì), revisione finale, `open-pr` (`spec_reviews_dir` = reviews/3/, `plan_reviews_dir` = reviews/9/, `spec_audit`), DB cancellato, PR segnata CLOSED, `adopt 9` → `execution`, spec di nuovo bloccata.

## Test esistenti riscritti (asserzioni sostituite, non tolte)
- `test_finishcheck`: `test_l2_approvals_follow_the_files` si divide in `test_missing_approvals_is_red_and_stays_in_execution` (assenza → voce falsa, fase `execution`), `test_plan_sha_different_from_blob_is_false` (sha del piano diverso dal blob), `test_complete_l2_is_green` (verde, chiavi di `ITEMS_BY_LEVEL["L2"]`, `specialists` `None`). `l2_lab`/`approve` ora usano gli helper di `FlowLab` (`approve_spec_file`, `approve_plan_file`, `write_report`) con `spec_sha` e report; `test_l2_approved_spec_and_reviews_files_exempt`, `..._modified_plan_...`, `..._spec_changed_...` stessi controlli su `guard_scope`, più `approvals` falsa nel terzo.
- `test_openpr.test_counters_and_reviews_dirs`: lavoro con `spec_path` e approvazione con `sha` reale; stesse asserzioni su cartelle, `spec_audit`, contatori. `facts` spostato da `FactsTest` a `OpenCase` per condividerlo con `L2FactsTest`. `test_openpr:243` (spec_audit con due `None` in L1) invariato.
- `test_adopt`: `test_l2_without_plan_approval_goes_approval` → `AdoptL2Test.test_plan_without_approval_goes_plan_with_adversary_on` (+ variante `off` → `approval`); i tre sottocasi «approval» di `test_l2_superseded_or_mismatched_approvals_go_back` attesi `plan`. `branch_lab` accetta `toml`.

## Scostamenti e scelte
- D4 «altrimenti null»: `spec_audit` senza `spec_path` resta `{"adversarial": None, "lens": None}` (forma della spec 18.1 e del test `test_openpr:243`, che D4 non riscrive); `spec_reviews_dir` è `None`.
- `adopt 9` nel test end-to-end dà `execution` solo con la PR segnata CLOSED (con PR aperta sarebbe `pr_open`), e il livello L2 si ricostruisce dal diff: il piano tocca `src/auth/login.py` (percorso sensibile).
- `FlowLab` (tests/flowkit.py): aggiunti `write_report` e `approve_plan_file`.
- La cartella `docs/superpowers/reviews/` e `locked_docs`/`audit`/`l2acts` hanno ancora loro letture duplicate dell'albero (Task 5/7): non toccate (minimo impatto).

## Autorevisione
Brief e carry D3, D4, D8/D10, D18a/b coperti; niente testo di spec/issue in comandi o argomenti di git/gh (solo percorsi convalidati, `git ls-tree`/`cat-file`); nessun `__pycache__` nel commit.

## Fix round 1
- `audit._spec_approval_current` e `l2acts._spec_approved` usano `l2tree.spec_approvals(wt, "HEAD")` al posto delle due righe duplicate (comportamento invariato).
- `finishcheck`: unificare le due letture dell'albero costava più del guadagno (stanno in fasi diverse, una per lo scope, una per `check_l2` che serve anche i report); ho corretto il commento di `_approved_spec_blob`, che non dice più «una sola lettura».
- `start.py`: docstring riavvolta; `tests/test_adopt.py`: una sola doppia riga vuota prima di `AdoptL2Test`.
- Test mirati: `python3.11 -B -m unittest tests.test_audit_prepare tests.test_l2acts tests.test_finishcheck tests.test_adopt` -> `Ran 179 tests ... OK`.
- Suite: `tests/run` -> python3.11 e python3 3.13.5, 1665 test ciascuno, OK.
