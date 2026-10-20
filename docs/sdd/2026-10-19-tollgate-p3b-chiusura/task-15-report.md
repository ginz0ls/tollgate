# Task 15 - Prossimo passo nelle fasi di chiusura

## Implementato (bin/tollgate_flow/checkpoint.py)
- `next_step` legge il lavoro (`work_items`) e prima di tutto controlla i blocchi aperti: "giri di correzione esauriti sul task k" e `reviews.CAP_REASON` danno «<motivo>: serve una decisione dell'utente: /tollgate:approve rounds <n>, /tollgate:resolve <id> o /tollgate:abandon #N» (m12, decisione 13).
- Revisione del task: con `review_sha` e `review_code` presenti e verdetto mancante dice «revisione preparata, lancia il revisore <tipo> con il brief "<percorso>"» (tipo = `reviewer_type` o `DEFAULT_REVIEWER`; brief = ultimo `.tollgate-run/<N>/review-<k>.md`); `task review-prepare k` solo se non preparata (o brief non trovato).
- Task tutti `done` (`_closing_step`): `pr_open` con PR -> attendi il gate / `--reopen-execution` / `sync`; `pr_open` senza PR (carry Task 15 dal Task 13) -> «PR chiusa senza merge...»; ciclo `needs_fix` con rilievi bloccanti aperti e nessun task `cycle:<n>` -> `task start --from-findings <n>` (C10: guarda l'esito attuale; `ok` in execution -> `/tollgate:finish`); fase `review` per stadio (nessun ciclo/superseded: `review prepare`; stadio review/verify: `review prepare`; chiuso ok: `finish open-pr`; needs_you: `/tollgate:resolve`); L0 in `review`: `finish open-pr`.
- Tutti i comandi del programma passano da `program_command`.

## Scostamenti dal piano
- Il «riga 133» di `skills/execute/SKILL.md` non esiste (il file ha 58 righe): ho usato la tabella alle righe 22-23.
- Dopo che esiste un task `cycle:<n>` (o i rilievi non sono più aperti) un ciclo `needs_fix` non rimanda di nuovo a `--from-findings` ma a `/tollgate:finish`: altrimenti loop.

## TDD
RED (`python3 -B -m unittest tests.test_checkpoint`): Ran 18, FAILED (failures=8): test_fix_rounds_cap_asks_user, test_needs_fix_points_to_from_findings, test_pr_open_step, test_pr_open_without_pr_step, test_prepared_review_not_reprepared, test_review_cycles_cap_asks_user, test_review_phase_steps, test_steps_use_program_command.
GREEN: stesso comando, 18 OK (9 test nuovi inclusi `test_ok_cycle_after_dismiss_points_to_finish`, che passava già per costruzione). `tests/run`: python3.11 1383 OK, python3 (3.13.5) 1383 OK.

## File
bin/tollgate_flow/checkpoint.py, tests/test_checkpoint.py

## Dubbi
Nessuno rilevante. Se il brief del revisore non è più su disco, il passo ricade su `task review-prepare k`.
