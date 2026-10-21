# Report Task 3: regole pure dell'audit

## Implementato
`bin/tollgate_analysis/auditrules.py`: VIEWPOINTS, VIEWPOINT_LABELS, SEVERITIES, outcome, is_clean, RoundJson, parse_round_json, LensState, lens_state, next_viewpoint, render_lens_status. Importa solo `.report.json_candidates`.
Test: `tests/test_auditrules.py` (12 test, copre i 6 del brief più regole sui counts, superseded, problemi senza valori ricevuti).

## Scelte
- `parse_round_json`: problemi come nomi di campo («kind diverso da quello del giro», ecc.), mai valori ricevuti. `counts` è None se il giro non è valido. `viewpoint` atteso solo per `spec-lens` (altrimenti deve essere null); `plan_sha` solo per `plan-adversarial`. `v` non richiesto (brief non lo cita). Bool rifiutati come interi.
- `lens_state` ignora righe `superseded` e punti di vista sconosciuti.
- `next_viewpoint`: ordine circolare con `last` per ultimo; senza `last` parte da executor; a audit chiuso il successivo di `last`.
- `render_lens_status`: tabella con colonna «<id> (<etichetta>)», poi «stato: aperto|chiuso|sospeso» e «cicli fatti: N (tetto C)»; intestazione con #issue.

## TDD
RED: `python3 -B -m unittest tests.test_auditrules` -> errore di import (modulo assente). GREEN: 12 test OK (una asserzione sul testo di render corretta nel test per allinearla al formato).
`tests/run`: python3.11 1456 test OK; python3 (3.13.5) 1456 test OK.

## Scostamenti dal piano
Nessuno. Dubbi: nessuno.
