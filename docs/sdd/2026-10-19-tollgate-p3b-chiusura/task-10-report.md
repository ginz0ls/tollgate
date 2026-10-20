# Task 10 - act apply per finding, rounds, unverified-review, rebase

## Implementato
- `actapply.APPLIERS`: `approve finding|rounds|unverified-review|rebase`; `_resolve` sul blocco `reviews.CAP_REASON` concede un ciclo (`phases.add_extra_cycles(…, 1)`), rifiutato con rinvio a `approve unverified-review` se i cicli fatti sono già 8.
- `approve rounds <n>`: un solo tetto aperto per volta (cicli o «giri di correzione esauriti sul task k»); con entrambi aperti rifiuta e chiede `resolve`; cicli fatti + n <= 8; giri: `tasks.add_extra_rounds` (5 + extra <= 8). Chiude il blocco.
- `approve finding <id> <gravità|dismiss> <motivo>`: `reviews.set_decision`, poi `reviews.recompute_outcome` (nuova, M2: nessun `close_cycle`, nessun cambio di fase) sul ciclo del rilievo se è l'ultimo e chiuso; chiude il blocco dei cicli se l'esito diventa `ok`.
- `approve unverified-review` (C7): >= 8 cicli, flag, chiude il blocco dei cicli se aperto, fase invariata.
- `approve rebase`: richiede blocco con prefisso `SYNC_CONFLICT_REASON`, rebase non in corso, `set_base(merge-base)`, `close_block`, `set_phase(execution, "sync")` solo se tornata `pr_open`, `authorize_force`.
- `tasks.add_extra_rounds`, `tasks.BASE_FIX_ROUNDS/MAX_FIX_ROUNDS`; `taskcmd.MAX_FIX_ROUNDS` = `tasks.BASE_FIX_ROUNDS`, tetto `MAX_FIX_ROUNDS + extra_fix_rounds`; `gitw.merge_base`.

## Scostamenti / dubbi
- `approve finding`: il brief dice «chiude il blocco dei cicli se aperto»; l'ho condizionato a esito `ok` dopo il ricalcolo (altrimenti declassare un solo rilievo di due aggirerebbe il tetto). Da confermare.
- `recompute_outcome` ricalcola `findings_confirmed` escludendo gli archiviati (`dismissed`); `counted` non cambia (il ciclo pesa ancora sul tetto).
- `resolve` al tetto con 8 cicli già fatti rifiuta (non nel brief).
- `approve rebase` rifiuta anche se il rebase è ancora in corso (non nel brief).

## RED
`python3 -B -m unittest tests.test_actapply tests.test_tasks tests.test_openpr tests.test_reviews`: FAILED (failures=7, errors=16): AttributeError su `tasks.add_extra_rounds`, `gitw.merge_base`, `reviews.recompute_outcome`; "nessun atto da applicare" per le voci nuove di APPLIERS; `extra_review_cycles` 0 invece di 1 su resolve.
## GREEN
Stessi moduli + test_taskcmd: Ran 171 tests OK. `tests/run`: 1295 test OK con Python 3.11.16 e 3.13.5.

## Test
test_actapply (8 del brief + both-blocks, rounds su task oltre 8, numero non valido, resolve oltre 8 cicli, downgrade, blocker residuo, chiusura blocco, rebase in execution/senza blocco); test_tasks (add_extra_rounds); test_reviews (recompute_outcome); test_openpr (merge_base).

## Fix round 1
Ruling del controller: `approve finding` chiude il blocco dei cicli se aperto, qualunque sia l'esito ricalcolato (punti 2 e 3 accettati).
- Codice: `actapply._approve_finding` non condiziona più la chiusura del blocco a `outcome == "ok"`.
- Test nuovo: `test_approve_finding_closes_cap_block_even_if_still_needs_fix` (due `major` confermati nell'ultimo ciclo, blocco aperto, `dismiss` sul primo: blocco chiuso, esito `needs_fix`, fase `execution`). L'helper `cycle` accetta `findings_n`, `cap_reached` accetta `last_findings`.
- RED: `python3 -B -m unittest tests.test_actapply.ApproveFindingTest` -> FAILED (failures=1): `['cicli di revisione esauriti'] != []`.
- GREEN: `python3 -B -m unittest tests.test_actapply` -> Ran 39 tests OK; `tests/run` -> 1296 test OK con Python 3.11.16 e 3.13.5.
