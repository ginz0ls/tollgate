# Task 8 - report

## Implementato
- `bin/tollgate_checks/final_review.py` (subagent_stop, ordine 15, componente final_review): tampered con readonly_check; revisore -> `review_report` + finish(done); verificatore -> `finding_verify` + finish(done); verdetto/risultati non validi o JSON assente -> finish(done) + blocco needs_you (nessun veto); messaggio da last_assistant_message o subagents.report.
- `_common.awaiting_final` (running e interrupted; ruoli reviewer/verifier); `subagent_stop` salta i revisori finali in attesa.
- `apply.py`: `review_report` (blocking/known rules dei profili attivi sul diff del ciclo; ValueError di add_report ignorato; close_cycle se verify senza rilievi da verificare), `finding_verify` (solo in stadio verify; close_cycle a zero senza esito, altrimenti conteggio). OPS = 27.
- `reviews`: `VERIFIER` (finalreview lo riusa), `unjudged_ids`, `verifier_incomplete` (contatore in review_cycles.reported[VERIFIER]; dal secondo riporto incompleto needs_you «verificatore senza esito su: <id>»).
- `checkpoint.CAPS`: `reviews.CAP_REASON` -> «cicli di revisione».
- Esito mai dall'outcome dichiarato (salvo needs_you): lo decide close_cycle.

## TDD
RED (test_check_final_review prima del codice): Ran 20, FAILED (failures=14, errors=2). RED di test_stopped_by_review_cycles con CAPS senza la voce: `- [] / + ['tetto: cicli di revisione (blocco 1)']`, FAILED.
GREEN: `bash tests/run`: python3.11 e python3 (3.13.5), Ran 1192, OK.

## Scostamenti / note
- Ignorare il riporto non valido di add_report e' silenzioso: EVENT_TYPES e' chiuso e apply non puo' iniettare avvisi.
- Test in piu' rispetto al brief: ok pulito, esito dichiarato ignorato, needs_you dichiarato, verificatore (tampered, non atteso in review, secondo giro), riporto doppio.
- Nessun __pycache__.
