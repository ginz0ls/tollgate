### Task 10: Casi extra e1-e5

**Files:**
- Create: `evals/e1-audit-a-lenti/`, `evals/e2-reopen-spec/`, `evals/e3-start-spec/`, `evals/e4-chiusura-l2/`, `evals/e5-rientro-gate/`, ricette e fixture nuove, test in `tests/test_eval_cases.py`

- [ ] **Step 1: Test** `test_e1_dry_run` (con la ricetta, `audit prepare` esce con 3 e chiede la conferma del costo; con `--confirm` stampa i lanci di `tollgate:spec-auditor`); `test_e2_dry_run` (`act apply` di un atto `reopen spec` registrato con `UserPromptExpansion` → fase `spec_audit`); `test_e3_dry_run` (`start 2 --spec <percorso>` → fase `plan`); `test_e4_dry_run` (con il `gh` finto, dopo i due `task done` e un ciclo di revisione `ok` scritto dagli eventi come in `test_criteria_p3b.py`, `finish open-pr` stampa l'URL della PR finta e spinge sull'`origin` nudo); `test_e5_dry_run` (`task start --from-gate` legge il commento del bot dai dati del `gh` finto e crea il task `fix`).
- [ ] **Step 2: Fallimento, casi e ricette, `tests/run`, commit** «tollgate P5: casi di eval extra e1-e5 con le prove a secco».

---

