### Task 9: Casi s6-s9

**Files:**
- Create: `evals/s6-fine-execute/`, `evals/s7-spec-contraddittoria/`, `evals/s8-cambio-ramo/`, `evals/s9-implementatore-generico/`, ricette e fixture nuove, test in `tests/test_eval_cases.py`

- [ ] **Step 1: Test** `test_s6_dry_run` (dopo `task done 2` dal programma vero, `status` e la tabella della skill `execute` indicano `/tollgate:finish`); `test_s7_dry_run` (`audit prepare` sulla ricetta stampa il lancio di `tollgate:spec-adversary` con il brief; la fixture della spec contiene le due frasi incompatibili che il grader cerca); `test_s8_dry_run` (`git switch -c altro` e `git checkout -b altro` nel worktree → `deny`); `test_s9_dry_run` (`Agent` `general-purpose` in `execution` → `deny` con il testo che nomina `tollgate:execute`).
- [ ] **Step 2: Fallimento, casi e ricette, `tests/run`, commit** «tollgate P5: casi di eval s6-s9 con le prove a secco».

---

