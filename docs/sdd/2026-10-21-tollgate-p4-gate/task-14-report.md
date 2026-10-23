# Task 14: report

## Implementato
- `audits.open_round(min_number=1)`: numero = max(numero dal DB, min_number). `open_round_row` invariata.
- `audit.prepare` passa `min_number` = (numero più alto dei report del tipo in `reviews/<N>/` a HEAD) + 1 (m-2, `_next_report_number`).
- Caso (b): `_decide_approval` con `plan_adversary` spento controlla l'approvazione della spec come `approve plan` (rifiuto «spec cambiata dopo approve spec: /tollgate:reopen spec»); `peek` coincide.
- m-4: `REGISTERED_NOTE` aggiunta al rifiuto «non è nel ramo» quando il percorso è quello registrato (audit.py e l2acts.py).
- Riga 16: il backtick è rifiutato da `_check_path`.
- Riga 29: `peek` con `confirm` dà il passo `CONFIRM_STEP`.
- Riga 19: `audit_round._mechanical` con blob illeggibile dà un rilievo (`UNREADABLE_SPEC`) che conta come major.
- Righe 22 e 34 e Review Focus 6: solo test (il codice già si comportava così; test_later_slice_with_other_current_approval_end_to_end passa subito, copre la regressione).

## TDD
RED (7 test falliti prima del codice): test_peek_needs_confirm_says_confirm, test_min_number_raises_the_number (TypeError min_number), test_approval_with_plan_adversary_off_and_spec_changed (0 != 1), test_backtick_path_refused, test_numbering_after_lost_db ((plan-adversarial, 1) != (…, 3)), test_registered_path_missing_named, test_registered_plan_missing_names_the_path, test_unreadable_spec_adds_major ((0,'empty') != (1,'findings')).
GREEN: gli stessi test mirati OK (129 test), poi `tests/run`: python3.11 2319 test OK, python3 (3.13.5) 2319 test OK, output pulito.

## Scostamenti
- Nel test di Review Focus 6 i report della spec stanno in `reviews/9/` (la cartella dell'approvazione corrente): `finish check` li cerca lì.
- `test_superseded_refusal_leaves_block_and_act` apre il blocco dei cicli con `open_block(CAP_REASON)` (un ciclo superato non può avere un blocco dei cicli per altra via).
