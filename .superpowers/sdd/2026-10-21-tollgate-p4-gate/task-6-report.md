# Task 6: report

Stato: DONE.

## Implementato
- `bin/tollgate_analysis/prbody.py`: `MAX_BODY = 60000` (unica); `defuse()` estratta da `neutralize` (riusata da comment); `render` con tetto totale: tetto per voce decrescente (2000..30), poi voci tolte dalla coda con nota «troncato: altre N voci omesse». Blocco JSON intero e ultimo.
- `bin/tollgate_gate/comment.py`: `MARKER_PREFIX`, `GUARD_PREFIX`, `marker`, `marker_sha`, `render(sha, ev)` (senza `plan_diff`/`approval_diff`, D19), `render_guard`; `MAX_BODY` importata da prbody (D17c, test `assertIs`). Il marcatore è letterale (tollgate_gate non può importare fixtask), uguaglianza controllata lato test. Ordine: errori, rosso, «da leggere», `<details>` informative, watch. `Item.data`, watch, errors, problemi della guardia passano da `prbody.neutralize`; `Item.text` solo da `defuse`.
- `render`/`marker` rifiutano con ValueError uno SHA non di 40 esadecimali minuscoli.

## TDD
RED: `tests.test_prbody` -> AttributeError: module 'tollgate_analysis.prbody' has no attribute 'MAX_BODY' (2 errori); `tests.test_gate_comment` senza comment.py -> ImportError (FAILED errors=1).
GREEN: `python3 -B -m unittest tests.test_gate_comment tests.test_prbody tests.test_layers` -> 30 test OK. `tests/run`: 1968 test OK su Python 3.11.16 e 3.13.5.

## Scostamenti
- Un secondo test di tetto in prbody e in comment (caso «voci omesse»), oltre a quelli del brief.
- Nella fase di taglio delle voci il tetto per voce è 60 (non 30) perché la nota di omissione, passando dallo stesso tetto, veniva troncata.
