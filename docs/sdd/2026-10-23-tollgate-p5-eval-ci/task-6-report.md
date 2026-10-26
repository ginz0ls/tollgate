# Task 6: rinviati del nucleo e del flusso. Report

Commit: `e1a9e97` «tollgate P5: rinviati del nucleo e del flusso (git assente, db restore, eventi, cicli, intenti, JSON, checkpoint)». Suite: `tests/run` con python3.11 (2659 test, OK, skipped=2 preesistenti) e python3 3.13.5 (2659 test, OK). Output pulito (resta solo la riga `guard: la PR è avanzata…` di un test preesistente).

## Cosa

| Rinviato | Test | Codice |
|---|---|---|
| P1: traceback senza `git` | `test_cli.py::test_status_without_git_is_message_not_traceback` (status, status --json, stats --work, con `PATH` vuoto) | `cli.current_repo_key`: `FileNotFoundError` -> `UsageError("git non disponibile…")`, uscita 1 |
| P1: `input()` senza EOF/Ctrl-C | `test_db_restore_interactive_eof_and_ctrl_c` (pty reale: Ctrl-D e SIGINT al processo figlio) | `cli._restore`: `EOFError`/`KeyboardInterrupt` nel `confirm` -> «annullato» su stderr, uscita 1, DB e `broken/` invariati (la risposta «n» resta «annullato», uscita 0) |
| P1: ramo interattivo da CLI | `test_db_restore_interactive_confirm_from_cli` (pty, risposta `s`) | nessuna modifica: il test fissa il comportamento (già verde) |
| P3a 163 | `test_tasks.py::test_assign_event_carries_implementer_and_pending` | `tasks.assign`: `implementer` e `pending` nell'evento `task_change` (solo di `assign`) |
| P3b 10 | `test_reviews.py::test_close_cycle_requires_verify_stage` | `reviews.ReviewError(ValueError)`; `close_cycle` si chiude solo da `verify`; anche con rilievi senza esito (`verification` nullo) rifiuta (riga 10 li nomina) |
| P3b 11 | `test_close_cycle_twice_is_idempotent` (tetto a 4 cicli, blocco chiuso, fase riportata a review) | su ciclo già chiuso `close_cycle` dà l'esito senza toccare fase, blocchi ed eventi |
| P3b 13 | `test_intents.py::test_request_existing_key_other_work_or_action_refused` | `intents.request`: stessa chiave con altro `work` o altra `action` -> `ValueError`, riga intatta |
| P3b 27 | `test_finishcheck.py::CorruptReportTest::test_corrupt_finish_report_is_message` (5 forme) | `finishcheck._saved` legge con `db.load_json`; report illeggibile: avviso `esito salvato illeggibile, si ricalcola` e il gate si rilancia |
| P3b 44 | `test_openpr.py::OpenCorruptTest::test_corrupt_json_fields_are_messages` (8 casi: finish_report x3, reviewers, commits, intents.data, events.data x2) | `openpr` usa `db.load_json` (e `finishcheck.report_items`) su tutti i `json.loads`; `events._as_dict` idem; `rifiuto:` che nomina `tabella.campo`, nessuna PR/push, fase invariata |
| P3b 54 | `test_reviews.py::test_approve_finding_reason_in_event` + asserzione in `test_actapply.py::test_approve_finding_dismiss_turns_cycle_ok` | `reviews.set_decision(..., reason=)` mette `reason` nell'evento `finding` (solo se c'è); `actapply._approve_finding` lo passa |
| P3b 74 | `test_checkpoint.py::test_review_brief_by_task_number` (+ aggiornato `test_prepared_review_not_reprepared`) | `checkpoint._review_brief(worktree, issue, code)`: il brief del task è quello che contiene il suo `review_code`, non il `review-<k>.md` con k più alto |
| P3b 76 | `test_all_cap_blocks_listed` | `checkpoint._cap_step`: elenca il passo di ogni blocco di tetto aperto, separati da ` \| `; con un solo blocco il testo è quello di prima |
| P3c 12 | `test_audits.py::test_close_round_rejects_bad_outcome_and_counts` (7 casi) | `audits.close_round`: `outcome` in `OUTCOMES = ("empty","findings")`, `counts` con le 4 gravità intere non negative (non bool), `ValueError` prima della transazione |

Nuovo in `db.py`: `load_json(raw, what, kind=None)` (JSON guasto o di forma diversa -> `DbError` con il nome del campo). `finishcheck.check` ora cattura anche `db.DbError`.

## Step 5 (verifica, nessun codice)

```
$ grep -n "git.changes" bin/tollgate_flow/finishcheck.py
117:    files = [c.path for c in git.changes(wt, base, head=sha) if c.status != "D"]
$ grep -c "git.changes" bin/tollgate_flow/finishcheck.py
1
$ grep -n "_TG" bin/tollgate_flow/closing.py bin/tollgate_checks/_common.py
(nessuna riga, rc=1)
```
Riga 28: `git.changes` una sola volta in `finishcheck.py`. Riga 66: nessuna regex `_TG` in `closing.py` né in `_common.py` (le sole `_TG_SUBST_` sono costanti di stringa in `bash.py`, `bash_rules.py`, `runner.py`, non la regex di quella riga). Entrambe chiuse.

## RED / GREEN

RED (prima del codice; `python3.11 -B -W error::ResourceWarning -m unittest <test>`):
- git assente: 3 subtest FAIL, stderr con `FileNotFoundError: [Errno 2] No such file or directory: 'git'` e traceback da `cli.py:22`.
- eof/ctrl-c: FAIL `'annullato' not found` (EOF: traceback `EOFError` da `cli.py:213`), Ctrl-C: `-2 != 1` (KeyboardInterrupt). Il test di conferma da CLI è verde subito (caratterizzazione).
- assign: `KeyError: 'implementer'`. reviews: `AttributeError: ... no attribute 'ReviewError'` e `set_decision() got an unexpected keyword argument 'reason'`; idempotenza: `'blocked' != 'review'`. intents: `ValueError not raised` (x2) e dati sovrascritti (`{'n': 3} != {'n': 1}`). audits: `ValueError not raised` (outcome sconosciuto). finishcheck: `JSONDecodeError`, `TypeError`, `KeyError: 'items'`, `AttributeError`. openpr: `JSONDecodeError` / `TypeError` / `AttributeError` negli 8 casi. checkpoint: `all_cap_blocks` `'cicli di revisione esauriti' not found`; actapply `KeyError: 'reason'`.

GREEN: `python3.11 -B -W error::ResourceWarning -m unittest tests.test_tasks tests.test_reviews tests.test_intents tests.test_audits tests.test_checkpoint tests.test_finishcheck tests.test_openpr tests.test_actapply tests.test_cli tests.test_db tests.test_finalreview` -> `Ran 318 tests ... OK` dopo l'ultimo fix di `events._as_dict` (prima: 2 errori su `events.data`, causa `stats.off_periods` -> `events.export_events`); poi `tests/run` completo: OK/OK.

## File

Codice: `bin/tollgate_core/{audits,cli,db,events,intents,reviews,tasks}.py`, `bin/tollgate_flow/{actapply,checkpoint,finishcheck,openpr}.py`.
Test: `tests/test_{actapply,audits,checkpoint,cli,finishcheck,intents,openpr,reviews,tasks}.py`.

## Scostamenti dal piano e perché

1. **Riga 74, «per numero del task»**: il `k` di `review-<k>.md` è un contatore del lavoro (`taskcmd.py:322`), quindi il numero del task non è nel nome. Il brief giusto si riconosce dal `review_code` del task (che `review-prepare` scrive nel brief, nel blocco JSON del verdetto). Il test conserva il nome del brief. Ho aggiornato `test_prepared_review_not_reprepared`, che fissava l'euristica «k più alto» scrivendo contenuti `b`.
2. **Riga 27, «è messaggio»**: con un report corrotto non rifiuto per sempre (il lavoro resterebbe bloccato in `review` sullo stesso SHA): il report è una cache, quindi `finish check` stampa un `avviso:` e ricalcola (poi riscrive il report se verde). Se si preferisce un `rifiuto:` è una riga da cambiare.
3. **Riga 10**: oltre allo stadio, `close_cycle` rifiuta i rilievi con `verification` nullo (il testo del registro li nomina; tutti i chiamanti già lo garantiscono, nessun test esistente si è rotto).
4. **Riga 11**: il docstring diceva «ripetibile: riprende i passi rimasti a metà». Ora la ripetizione non fa più nulla: se il processo muore tra la transazione di chiusura e `set_phase`/`open_block`, la ripetizione non completa più i passi. Il brief lo chiede alla lettera (M2 di P3b, fase riportata a `execution` e blocco del tetto riaperto dopo `approve finding`/`rounds`).
5. **Riga 54**: la `reason` è nell'evento solo quando c'è, per non cambiare gli altri eventi `finding`.
6. **Riga 13**: controllo di `work` e `action`; non lo stato di partenza (rimettere a `requested` un intento `executed` è il ritorno voluto dell'idempotenza di `open-pr`).
7. **P3c 12**: coerenza `outcome`/`counts` (es. `findings` con tutti zeri) non imposta: un test esistente (`test_close_emits_event_and_needs_open_round`) chiude `findings` con conteggi nulli. Non toccato il parametro `now` inutilizzato di `audits.supersede` (non nel brief).
8. `events._as_dict` (non nell'elenco del brief) è stato toccato perché `openpr.facts` -> `stats.off_periods` -> `export_events` dava il traceback con `events.data` guasto; ora `DbError` e `tollgate events` stampa un messaggio.

## Autorevisione

Completezza rispetto al brief: tutti i test elencati esistono con i nomi indicati; Step 5 riportato. Nessun extra fuori scope oltre ai punti sopra. Layer: `audits` (core) importa `tollgate_analysis.auditrules` come già fanno altri moduli del core. `tollgate status` non cambia stampa (solo l'errore senza `git`), nessun conflitto con il Task 12. Pseudo-terminale chiuso in `finally` (master/slave) e `Popen` in `with`; test verdi con `-W error::ResourceWarning`. Rimossi gli `import json` diventati inutili in `finishcheck.py` e `openpr.py`.

## Dubbi

- Scostamenti 2 e 4 (riga 27: ricalcolo invece di rifiuto; riga 11: niente ripresa dei passi a metà).
- Il prompt di `input()` va su stderr (readline), per questo il test mette stdout e stderr sullo stesso pty.

## Fix round 1

- **Important 1 (P3b riga 11)**: `reviews.close_cycle` ora fa chiusura, evento, cambio di fase e blocchi nella stessa transazione (`phases.set_phase_in_tx`, `phases.open_block_in_tx`; `set_phase` e `open_block` pubblici li usano e restano identici). Le copie del DB (`fase-execution`, `fase-blocked`) si fanno dopo il commit. Docstring aggiornato; la ripetizione su ciclo chiuso resta idempotente e non serve più alcun recupero.
  Test: `test_close_is_resumable` sostituito da `test_close_is_atomic_with_phase_and_blocks` (errore iniettato in `phases._change_phase`: ciclo ancora in `verify`, nessun evento, fase `review`; la ripetizione chiude) e `test_close_leaves_a_db_copy_per_phase_change`. RED sul codice di e1a9e97 (archivio in scratchpad): `('closed','needs_fix',1) != ('verify',None,0)`.
- **openpr**: `skills_absent` con forma sbagliata (`{}`, task non intero, skills non elenco) -> `DbError` che nomina `events.data` (prima `KeyError: 'skills'`, o PR aperta); `_size_reasons` ignora un `size_reason` non stringa. Test: 3 casi nuovi in `OpenCorruptTest` (RED: KeyError e `0 != 1`).
- **events.known_commits**: `load_json(..., "events.data", dict)`; test `test_known_commits_corrupt_data_is_dberror` (RED: `JSONDecodeError`).
- Verifica: test mirati OK (293), `tests/run` python3.11 e python3: 2661 test OK.
