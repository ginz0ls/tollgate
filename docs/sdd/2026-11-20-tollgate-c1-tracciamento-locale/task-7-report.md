# Report Task 7: costo dei subagenti e guardia sulle decisioni dei rilievi

## Implementato
- `report.transcript_usage(path)`: uso per modello (`input`, `cache_creation`, `cache_read`, `output`), un messaggio una volta (ultima riga per id), modello assente -> `sconosciuto`, `{}` senza file o senza righe `usage`. `transcript_tokens` ora usa lo stesso lettore tollerante (`_messages`): comportamento invariato (test esistenti verdi).
- `_common.transcript_cost(event) -> (tokens, usage|None)`: una sola lettura; `tokens` = somma di input + cache_creation + output di tutti i modelli (0 senza uso); `usage` `None` per file mancante, illeggibile o senza righe `usage`. `tampered_records(row, work, *, tokens=None, usage=None)`.
- `subagents.finish(..., usage=None)`: dopo `subagent_stop` registra `cost` (`agent`, `type`, `task`, `tokens`, `by_model`, `usd` null, `source` "transcript") solo con un dizionario non vuoto. Operazione `subagent_finish` in `apply.py` passa `usage=d.get("usage")`.
- I 14 `subagent_finish` con trascrizione portano `tokens` e `usage`: `subagent_stop.py` (`_readonly` riceve l'evento, implementatore senza lavoro, budget, veti esauriti, fatto), `task_verdict.py` (valido, veti esauriti, tampered), `final_review.py` (`_invalid` riceve `usage`, revisore, verificatore, tampered), `audit_round.py` (componente spento, veti esauriti, report valido, tampered). `budget_cut_records` resta senza. Il calcolo e' spostato prima di `tampered_records`. Tolti gli import `report` non piu' usati in `task_verdict`, `final_review`, `audit_round`.

## Test
Nuovi: `test_report` (usage_by_model, missing_file), `test_check_common` (`TranscriptCostTest`: i tre casi di D3 piu' lettura unica; `BudgetCutCostTest`), `test_subagents` (cost_event_on_finish, no_cost_without_usage con `None`, `{}` e interruzione), `test_check_subagent_stop.CostTest` (6 rami piu' assenza di trascrizione), `UsageTest` in `test_check_task_verdict`, `test_check_final_review`, `test_check_audit_round` con trascrizione finta in cartella temporanea, `test_reviews.test_user_decision_written_only_by_set_decision`, `test_actapply.ApproveFindingTest.test_approve_finding_emits_finding_event` (messo in `test_actapply.py`, dove vive il flusso `approve finding`, invece di `test_reviews.py`).

RED (codice di HEAD con i test nuovi, copia in cartella temporanea fuori dal repo):
`python3 -B -m unittest tests.test_report tests.test_check_common tests.test_subagents tests.test_reviews tests.test_check_subagent_stop.CostTest tests.test_check_task_verdict.UsageTest tests.test_check_final_review.UsageTest tests.test_check_audit_round.UsageTest tests.test_actapply.ApproveFindingTest` -> `Ran 81 tests ... FAILED (failures=4, errors=17)` (ImportError di `transcript_cost`, AttributeError `transcript_usage`, `cost` assente). Passano gia' come previsto i due test della decisione 6 e i test "senza costo" (guardie).
GREEN mirato: gli stessi file con il codice nuovo, tutti OK. Suite completa: vedi esito sotto.

## Scostamenti
- `test_approve_finding_emits_finding_event` in `tests/test_actapply.py` (non elencato nel brief).
- Nei test "senza trascrizione" il controllo e' sugli eventi `cost` (assenti) e `tokens` falsy in `subagent_stop`, non sull'uguaglianza dei record.

## Dubbi
Nessuno.

## Esito suite completa
`PYTHONWARNINGS=error::ResourceWarning tests/run` -> python3.11: Ran 4311, OK (skipped=13); python3 (3.13.5): Ran 4311, OK (skipped=11); `exit 0`. Output pulito, nessun "unclosed".

## Fix round 1
Rilievo I1: l'helper della trascrizione finta era copiato in quattro moduli di test.
Cambiato (solo test): `fake_transcript(case)`, `MODEL` e `USAGE` ora stanno in `tests/hookkit.py`; `test_check_audit_round.py`, `test_check_final_review.py`, `test_check_task_verdict.py`, `test_check_subagent_stop.py` li importano e le copie locali (`transcript_file`, `write_transcript`, `MODEL`, il dizionario atteso) sono tolte, con gli import diventati inutili. Asserzioni invariate (il dizionario atteso e' `USAGE`).
Test mirati: `python3 -B -m unittest tests.test_check_audit_round tests.test_check_final_review tests.test_check_task_verdict tests.test_check_subagent_stop` -> Ran 185, OK.
Suite completa: `PYTHONWARNINGS=error::ResourceWarning tests/run` (log `suite-task-7-fix1.log`): python3.11 Ran 4329 OK (skipped=13); python3 (3.13.5) Ran 4329 OK (skipped=11); `exit 0`.
Commit: `b87b77f`.
