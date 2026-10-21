# Report Task 12: rinviati di P3b nel flusso e nei test

Commit: 6cc4f31 «tollgate P3c: rinviati di P3b nel flusso e nei test (righe 34-82)».
`tests/run` (python3.11 e python3 3.13.5): 1715 test ciascuno, OK, output pulito.

## Righe e carry

| Riga | Esito | Codice | Test |
|---|---|---|---|
| 34 | corretta | `brief.final_review_brief`: se `sha != head` la riga «Il ciclo è stato aperto su `<sha>`; HEAD è `<head>` dopo un rebase senza modifiche di contenuto: rivedi il diff di HEAD.» | `test_brief.FinalBriefTest` (2), `test_finalreview.PrepareBriefTest.test_rebase_explained_in_brief` (rebase vero con stesso patch-id, ciclo ripreso) |
| 36 | corretta | `FinalBrief.issue_file: str | None`; `finalreview._issue_file` dà `None` se `issue.md` non c'è e il brief non lo nomina | `test_brief...test_issue_file_named_only_when_present`, `test_finalreview...test_issue_file_named_only_if_start_wrote_it` |
| 49 | corretta | `actapply._approve_finding`: non più limitato all'ultimo ciclo; ricalcola il ciclo del rilievo se chiuso e chiude il blocco dei cicli (decisione 25) | `ApproveFindingTest.test_old_cycle_finding_closes_cycles_block` |
| 50 | corretta | `ValueError` di `recompute_outcome` diventa `ActApplyError` con il messaggio, a decisione già scritta | `test_superseded_last_cycle_is_a_refusal` |
| 51 | solo test | codice già giusto | `FixRoundsTest.test_sixth_round_name_launch_inherit` (`tg-7-t1-r6`, `launch`, `model: inherit`) |
| 55 | solo test | codice già giusto | `SyncEdgeTest`: 4 test richiesti |
| 60 | corretta | `adopt._adopt`: avviso «ramo locale e remoto diversi: uso la punta locale <sha12>» | `AdoptEdgeTest` (avviso con punte diverse, nessun avviso con punte uguali) |
| 62 | corretta | `sqlite3.Error` in `acts.consume` dopo `create_work`: codice 4, riga «avviso: lavoro creato, atto non consumato: …», niente «rifiuto:» | `AdoptEdgeTest.test_consume_sqlite_error_after_create_work_is_incomplete` |
| 67 | solo test | codice già giusto | `test_closing`: i 3 test richiesti (`StartConfirmTest` per il terzo) |
| 71 | corretta | `taskcmd._fix_files`: tutti i rilievi confermati e `blocking = 1` del ciclo, senza filtrare per `user_decision` | `test_routing_stable_after_dismiss` |
| 72 | corretta | `brief._finding`: gravità effettiva (`downgraded:<g>`) con «(originale X)» se diversa; non importa il core (strato), regola duplicata con commento | `test_brief_shows_effective_severity` (fixtask), `FindingSeverityTest` (brief) |
| 73 | solo test | codice già giusto | `test_from_findings_rollback_on_error`, `test_l0_refused`, `test_cli_from_gate`, `test_gate_fence_longer_than_any_backtick_run` (recinto esatto di 6 backtick sul testo del task; il brief lo ricopia in uno di 7) |
| 82 | solo test | helper `prepare_needs_fix_cycle`; criterio 26 asserisce codice 1 e che ogni riga sia «rifiuto:» (prima «la fase è execution»); nuovo `test_second_finish_is_new_cycle` dal programma vero (ciclo 2 `ok`, `open-pr` 0, PR aperta) | `test_criteria_p3b.NeedsFixTest` |
| carry T10 | verificato, già risolto in parte | `git.text_at` non solleva più (ripiego Latin-1, Task 11 riga 5): spec e piano non UTF-8 committati non danno traceback; aggiunto `UnicodeDecodeError` a `audit.ERRORS` per le altre letture | `NonUtf8Test` (3): reali + `text_at` che solleva (peek = ripiego, prepare = `AuditError`) |
| carry T11 | corretta | `violations.active_profile_names`: `head` nullo (nessun commit) dà `[]` senza chiamare `changes` | `ActiveProfileNamesTest` (2) |

## Evidenza TDD (RED prima del codice, ottenuto ripristinando il solo codice di produzione)
- Righe 34/36: `FAIL` x4 (`test_issue_file_named_only_when_present`, `test_rebase_note_when_sha_differs_from_head`, `test_issue_file_named_only_if_start_wrote_it`, `test_rebase_explained_in_brief`); Ran 39, FAILED (failures=4).
- Righe 49/50: `ERROR: test_superseded_last_cycle_is_a_refusal` (`ValueError: ciclo 1: esito superseded non ricalcolabile`); `FAIL: test_old_cycle_finding_closes_cycles_block` (`['cicli di revisione esauriti'] != []`).
- Righe 60/62: `AssertionError: 1 != 4 : rifiuto: disco pieno`; avviso di punte diverse assente.
- Righe 71/72: `'probe:implementer-src' not found in 'task 3: tollgate:implementer ...'`; `'- [major (originale blocker)] ...' not found`.
- Carry T10: `UnicodeDecodeError` non gestito da peek/prepare con `text_at` che solleva.
- Carry T11: `Expected 'changes' to not have been called. Called 2 times.`
- Righe 51, 55, 67, 73, 82: solo test, il codice era già corretto (verde al primo colpo; nessun RED possibile).

## Scostamenti e note
- Riga 71: il DB non registra quali rilievi servirono a creare il task; si usano quelli confermati e bloccanti del ciclo, senza filtro sulla decisione. Un rilievo archiviato prima della creazione entra nell'instradamento (effetto marginale, solo skill e agente).
- Riga 72: l'originale è scritto «(originale blocker)»; il brief non fissava il formato.
- Riga 55 `test_ff_only_failure_blocks`: l'esito reale è un rifiuto con intento chiuso e atto non consumato, non un blocco `needs_you`; il test asserisce questo.
- `test_sync.py`: `update_branch_remote` spostato da `SyncRebaseTest` a `SyncCase` per riusarlo.
- Riga 82: il criterio 26 prima dava per scontato un solo «rifiuto:»; le righe sono 3 (fase, ciclo `ok`, Definition of Done).

## Autorevisione
Brief e carry completi; nessun `__pycache__` nel commit; nessuno scritto fuori dal worktree; nessun processo ucciso, nessuna rete, solo `TempState` e `fakegh`.

## Fix round 1
1. I-1: `taskcmd._fix_files` filtra anche sulla gravità dichiarata `reviews.BLOCKING_SEVERITIES` (blocker, major), oltre a confermato e `blocking = 1`; un major declassato dopo resta. Test `FromFindingsTest.test_routing_files_only_declared_blocker_or_major`.
   RED (`python3.11 -B -m unittest tests.test_fixtask.FromFindingsTest.test_routing_files_only_declared_blocker_or_major`): `AssertionError: Lists differ: ['src/app.py', 'lib/altro.py', 'lib/nota.py'] != ['src/app.py', 'lib/altro.py']`; FAILED (failures=1). GREEN dopo il fix.
2. I-2: `test_ff_only_failure_blocks` rinominato `test_ff_only_failure_refuses`, docstring corretta, asserito che non ci sono blocchi aperti (solo test, il codice era giusto).
3. `NonUtf8Test`: esiti precisi con il ripiego Latin-1. Spec non UTF-8: `OK`, lancia `tollgate:spec-adversary`, `spec_path` registrato. Piano non UTF-8: `REFUSED`, «rifiuto: nessun piano valido nel ramo», nessun lancio (il controllo con piano UTF-8 valido dà il giro avversariale). Solo test, nessun RED possibile.
Suite: `tests/run` python3.11 e python3, 1716 test ciascuno, OK.
