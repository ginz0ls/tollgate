# Report Task 2

Implementato (decisioni 4 e 5, D1, D14):
- `bin/tollgate_flow/init.py` `_drift`: righe `aggiungi min_level = ...` e `aggiungi checklist = ...` se il frammento li ha non vuoti e diversi da `config.PROFILE_DEFAULTS` e il blocco dichiarato non ha la chiave.
- `bin/tollgate_core/tasks.py` `take_pending`: `ORDER BY (reserved_at IS NULL), reserved_at DESC, number`.
- Test: `test_init.py` (due nuovi in `FrontendPrecedenceTest`, accanto a `test_real_precedence_p39`; D1: `DECLARED_X` con `min_level = "L1"`), `test_tasks.py` (launch, resume, senza prenotazione, D14 più recente vince), `test_check_agents.py` (`test_second_task_of_same_type_bound_by_name`, con `tasks.add_task` per il task 2).

RED (codice in `bin/` annullato): falliscono i 4 test nuovi che dipendono dal codice (init database, take_pending launch e resume, bound_by_name); gli altri passano già (per costruzione).
GREEN: `python3 -B -m unittest tests.test_init tests.test_tasks tests.test_check_agents`: 305 test OK.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 4094 test OK (skipped 13), python3.13 4094 OK (skipped 11), exit 0 (suite-task-2.log).

Scostamenti dal piano: nessuno. Dubbi: nessuno. Nota: solo `database` ha oggi `checklist` tra i frammenti reali.
