# Report Task 7 — review-prepare, verdetto del revisore, task done, prenotazione

## Implementato
- `bin/tollgate_analysis/report.py`: `json_candidates(text, key)` pubblica (C3); `_last_json` la usa con `"status"`.
- `bin/tollgate_analysis/verdicts.py` (nuovo): `TaskVerdict`, `parse_task_verdict`. Decisione 10 + C14: ultimo oggetto con `outcome`; valido solo se `outcome` in `approved|changes`, `task` intero uguale, `sha` e `code` uguali, `spec_compliance` lista di `missing|extra`, `findings` lista. Rilievi senza `rule`/`file`, con `line` non intera (bool escluso) o `severity` fuori da `blocker|major|moderate|minor` scartati e contati in `dropped`. Con `standard`: esito effettivo `changes` solo se `spec_compliance` non vuoto o un rilievo valido `blocker|major`. Un verdetto non valido ha `outcome=None`, mai `approved`.
- `bin/tollgate_analysis/brief.py`: `ReviewBrief.no_changes` (default False) con la riga «Nessuna modifica: verifica che il task sia già soddisfatto dal codice esistente.» (C11).
- `bin/tollgate_checks/_common.py`: `awaiting_review`, `fingerprint_changed` (spostata da `subagent_stop`), `tampered_records` (le due `record` della manomissione, condivise da `subagent_stop` e `task_verdict`).
- `bin/tollgate_checks/task_verdict.py` (nuovo, ordine 15): tamper con `readonly_check`; verdetto valido -> `task_verdict` + `subagent_finish(done)`; non valido -> `subagent_veto` + deny; al terzo stop (dopo 2 veti) `subagent_finish(done)` + `needs_you`. Messaggio da `last_assistant_message` o `subagents.report`.
- `bin/tollgate_checks/subagent_stop.py`: i revisori in attesa sono saltati prima del ramo di sola lettura; per gli implementatori `record("subagent_report")` in testa. Il corpo implementatore è la funzione `_implementer` (stesso codice, indentazione invariata).
- `bin/tollgate_checks/agents.py`: dopo i controlli di nome e primo piano, `reserved_at` < 120 s -> deny «lancio già in corso per il task k», altrimenti `record("task_reserve")`.
- `bin/tollgate_hooks/apply.py`: operazioni `task_reserve` e `task_verdict`.
- `bin/tollgate_flow/taskcmd.py`: `review_prepare` (diff `log --oneline` + `--stat` + `-U10`, brief con codice `secrets.token_hex(4)`, `set_review_prep`; numerazione `review-<k>`; dubbi dall'ultimo implementatore del task solo se `DONE_WITH_CONCERNS`; brief dell'implementatore `task-k.md` o `task-k-fix-<fix_rounds>.md`; C11 senza commit), `task_done`.
- `bin/tollgate_core/cli.py`: `task review-prepare K`, `task done K`.

## Scostamenti dal piano
1. `apply._subagent_start` NON chiama `tasks.clear_reservation`: `tasks.take_pending` (Task 6) azzera già `reserved_at` nella stessa UPDATE che azzera `pending`. Una seconda chiamata sarebbe ridondante; la proprietà è coperta da `ReservationTest.test_subagent_start_clears_reservation`.
2. `spec_compliance` assente è un verdetto non valido (fail-closed: senza, il controllo di conformità alla spec non è dichiarato). `findings` assente vale lista vuota.
3. `review_prepare` e `task_done` richiedono la fase `execution` del lavoro (come `task start`).
4. `awaiting_review` filtra anche per `row["task"]` quando il subagente ha già un task.
5. Il token della transcript del revisore finisce in `subagent_finish` (come per gli implementatori).

## TDD
- RED: i quattro file di test nuovi/modificati lanciati sul codice di HEAD (esportato in cartella a parte, `git archive`):
  `python3 -B -m unittest tests.test_verdicts tests.test_check_task_verdict tests.test_taskcmd tests.test_check_agents` -> `Ran 70 tests ... FAILED (failures=3, errors=13)` (modulo `verdicts` e `review_prepare` assenti, nessuna prenotazione).
- GREEN: `tests/run` -> python3.11: `Ran 889 tests ... OK`; python3 (3.13.5): `Ran 889 tests ... OK`.

## Test aggiunti
`test_verdicts.py` (11, tra cui `test_verdict_validity_matrix` con 12 sottocasi, prosa attorno al JSON, ultimo oggetto vince), `test_check_task_verdict.py` (12: approved, changes con rilievi, due veti poi needs_you, tampering, implementatore, handback in auto mode, C10 dopo `--fix`, altro tipo di revisore, standard on/off, `readonly_check` spento), `test_taskcmd.py::ReviewDoneTest` (11, compresi C11, CLI, dubbi, avviso dimensione, dopo `--fix`), `test_check_agents.py::ReservationTest` (4).

## Autorevisione
Tutti i punti del brief e di carry (C3, C10, C11, C14, C17, variante di C10 del Task 6) coperti. `set_review_prep` azzerava già `verdict` e `review_findings`: verificato con `test_review_prepare_clears_previous_verdict`. Output dei test pulito, nessun `__pycache__`.

## Dubbi
- Se due task sono insieme in `review` con revisione preparata e il revisore non ha `task` valorizzato, `awaiting_review` sceglie il più basso (il flusso è sequenziale, quindi di norma ce n'è uno).
- `review_prepare` rilegge il piano a `plan_sha` per l'instradamento delle skill del revisore: se il piano è stato toccato dopo la registrazione, rifiuta come `task start`.

## Fix round 1
- Rilievo 1: `task_done` richiede `review_sha == git.head(wt)` e il worktree pulito (`git.is_clean` con `review.output_dirs` e `.tollgate-run/` esclusi); `review_prepare` usa `git.head(wt)` come SHA (range dal genitore del primo commit del task alla punta) e rifiuta con «committa o scarta le modifiche prima della revisione». Test: commit fuori da `tasks.commits`, `reset --soft` + nuovo commit, file modificato e file nuovo non committati, SHA = HEAD.
- Rilievo 2 (decisione del controller): con `reviewer_standard`, `changes` senza blocker/major validi, senza `spec_compliance`, e con un rilievo scartato che poteva essere bloccante (gravità non `moderate`/`minor`, anche illeggibile) -> `valid=False`, problema «rilievo bloccante senza file, riga o regola: riscrivilo» (veto, dopo 2 veti `needs_you`). `changes` con soli minor validi (o minor scartati) resta `approved`. `dropped` va nell'evento `task_change` del verdetto (`tasks.set_verdict(..., dropped=)`, `record task_verdict`).
- Test: 4 in `test_verdicts.py`, 1 in `test_check_task_verdict.py`, 5 in `ReviewDoneTest`. I test di `ReviewDoneTest` committano il piano in `to_review` (il worktree deve essere pulito).
- RED osservato prima del codice: `python3 -B -m unittest tests.test_verdicts tests.test_check_task_verdict tests.test_taskcmd` -> `FAILED (failures=7)`.
- GREEN: `tests/run` -> python3.11 `Ran 899 tests OK`; python3 (3.13.5) `Ran 899 tests OK`.
