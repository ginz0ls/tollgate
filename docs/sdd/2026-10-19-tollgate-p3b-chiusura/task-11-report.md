# Task 11 - report

## Implementato
- `bin/tollgate_flow/sync.py` (nuovo): `SyncResult`, codici OK=0/REFUSED=1/BLOCKED=2/REVIEW_NEEDED=3, `sync()`, `complete_interrupted()`.
  Flusso: sessione `cli_session("sync", argv)` e atto `sync` usabile; `prstate.detect` (MERGED chiude, CLOSED rifiuta con `CLOSED_HINT`); fase execution/pr_open (review solo se la PR esiste: ripetizione); `fetch`; intento `sync:<lavoro>:<atto>` con from/to/base; commit remoti del ramo integrati con `merge --ff-only` (divergenza = `needs_you`; un push nostro poi riscritto, noto dagli eventi `commit`, non e' divergenza); `rebase` sulla punta del predefinito; conflitto = `rebase --abort`, `needs_you` con `SYNC_CONFLICT_REASON` e le due strade, base e fase invariate; riuscito = `_realign` (base alla punta con `base_realigned`, eventi `commit` per i SHA non noti, `pr_open -> execution` causa `sync`, `authorize_force` solo se il remoto non e' antenato di HEAD, intento eseguito; tutti i passi ripetibili); atto consumato; `finish check`; senza PR "PR non ancora aperta: /tollgate:finish"; `openpr.review_state` non ok (patch-id diverso) = codice 3 "serve una nuova revisione: /tollgate:finish" senza push; altrimenti `open_pr(update=True, via_sync=<atto>)`.
- `gitw.py`: `merge_ff_only`, `rebase` (falso con conflitto e rebase in corso; guasto senza rebase in corso = `GitWriteError`), `rebase_abort`. `is_ancestor`/`merge_base` esistevano.
- `start.py` (C20): `wt` calcolato prima della raccolta degli intenti, poi `sync.complete_interrupted` (errori = avviso), riga riletta; un sync completato non chiede conferma. Con rebase in corso resta l'avviso esistente con la proposta `rebase --abort`.
- `cli.py`: sottocomando `sync` (`argv` per il segnale).
- `openpr.py`: rinominati `_review`/`_Review` in `review_state`/`Review` (usati da sync; nessun cambio di comportamento).
- `tests/test_openpr.py`: `OpenCase.lab` accetta `files` e `app` (retrocompatibile).

## Test
`tests/test_sync.py` (16): refused_without_sync_act, closed PR con hint, merged, fase errata, rebase_realigns_base_and_updates_pr, same_patch_id_no_cycle_consumed, nothing_to_rebase, stale_pending_intent, remote_merge_then_rebase (ff-only verificato con mock wraps), diverged_remote_needs_you, conflict_aborts_and_blocks, different_patch_id_asks_new_review, repeat_after_review_needed_is_not_divergent, execution_without_open_pr, post_bash_ignores_rewritten_commits (con controllo positivo), CLI end-to-end.
`tests/test_start.py::ResumeTest`: test_interrupted_sync_completed_by_start, test_interrupted_sync_with_rebase_in_progress_proposes_abort.

## TDD
RED test_sync: `ImportError: cannot import name 'sync' from 'tollgate_flow'`.
RED test_start (complete_interrupted neutralizzato): `AssertionError: 3 != 0 : conferma: intento 1 (sync) richiesto ...`.
Mutazioni verificate: senza eventi `commit` il test post_bash fallisce; senza la regola "push nostro riscritto" fallisce test_repeat_after_review_needed.
GREEN: `python3.11 -B -m unittest discover -s tests -t .` = Ran 1314 tests OK; `python3` (3.13.5) = Ran 1314 tests OK.

## Scostamenti / note
- Il piano non chiede la fase `review` in `sync`: l'ho ammessa solo con PR esistente, per ripetere dopo un `open-pr` fallito o codice 3.
- `finish check` rosso dopo il rebase = codice 1 (REFUSED); il rebase resta fatto.
- Nessuna skill/comando `/tollgate:sync` (non in questo task).

## Fix round 1
Cambiato:
1. (Important) `sync.py`: nuova `_record_commits(conn, wid, wt, base, ...)` (estratta da `_realign`, che la riusa). In `_sync`, subito dopo `_remote_conflict`, se HEAD si e' mosso (ff-only) registra gli eventi `commit` di `base..HEAD` non noti, prima di rebase/blocco/divergenza. Chiude anche Minor 1 (il merge «Update branch» e' ora noto: il secondo sync non e' divergente). Minor 3: l'intento si chiude `non riuscito` con qualunque eccezione di `ERRORS`, non solo `GitWriteError`.
2. (Lease) `intents.authorize_force(..., lease=None)` salva `lease` nei dati; nuova `intents.force_lease(conn, work)` (sola lettura, stessa autorizzazione che `take_force` consumerebbe). `sync` autorizza con lease = punta di `origin/<ramo>` dopo l'integrazione; `approve rebase` (`actapply`) con `gitw.remote_sha` letto all'applicazione (errore = nessun lease). `openpr._publish` usa `force_lease(...) or remote`.
Test nuovi: `test_sync`: test_integrated_commits_recorded_when_rebase_conflicts, test_repeat_after_integrated_merge_is_not_divergent, test_force_lease_is_remote_tip_at_sync_and_rejects_newer_remote; `test_intents`: test_force_lease_is_the_latest_authorized_one; `test_actapply`: test_approve_rebase_force_carries_remote_tip_as_lease.
RED (prima del codice): `python3.11 -B -m unittest tests.test_sync tests.test_intents tests.test_actapply.ApproveRebaseTest` -> `Ran 33 tests ... FAILED (failures=2, errors=3)` (AttributeError `force_lease` x3; sha ignoti in base..HEAD; `2 != 3` divergente a torto).
GREEN: stessi moduli + test_openpr + test_start: `Ran 177 tests OK`. Suite completa `python3.11 -B -m unittest discover -s tests -t .` e `python3 ...`: `Ran 1319 tests OK` entrambe.
Non fatto (Minor): test su ordine dell'intento, rebase in corso all'avvio, fallimento ff-only, finish check rosso.
