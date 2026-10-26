### Task 8: Casi s1-s5

**Files:**
- Create: `evals/s1-done-senza-ricevuta/`, `evals/s2-conflitto-test-spec/`, `evals/s3-fuori-scope/`, `evals/s4-deploy/`, `evals/s5-l0-cresce/` (ognuno `case.yaml` e `scaffold.sh`), ricette nuove in `evals/_kit/recipes.py`, `tests/test_eval_cases.py`

**Interfaces:**
- Consumes: `Recipe`, `scaffold.build` (Task 7); decisioni 1, 2, 5.
- Produces: `tests/test_eval_cases.py` con `load_case(path) -> dict` (lettore YAML ristretto alle forme dei nostri `case.yaml`, senza librerie: mappe, elenchi, stringhe tra virgolette, numeri) e `dry_run(case, events) -> list[dict]` (gli esiti di `hooks/run` per gli eventi dati).

- [ ] **Step 1: Test** `test_eval_cases.py`: `test_case_shape` (per ogni cartella di `evals/` tranne `_kit`: chiavi della decisione 1, `runs: 3`, `env` solo `EVAL_[A-Z0-9_]*`, grader dei soli tipi della decisione 2, `scaffold.sh` presente e che chiama `scaffold.py` con una ricetta di `RECIPES`); `test_correct_paths_score_above_threshold` (decisione 7: vale per tutti i casi di `evals/`, compresi quelli dei Task 9 e 10, e ogni caso ha la sua voce in `CORRECT_PATHS`); `test_s1_dry_run` … `test_s5_dry_run` (Review Focus 2: per ogni caso l'evento dell'azione vietata dà `deny` o veto e ogni `regex` dei grader trova il testo prodotto; l'azione corretta passa).
- [ ] **Step 2: Fallimento, casi e ricette, `tests/run`, commit** «tollgate P5: casi di eval s1-s5 con le prove a secco».

---

