### Task 14: Eval reali e CI verde sul repo vero (controller)

**Files:**
- Create: `docs/verifiche/2026-10-23-p5-eval.md`, `docs/verifiche/2026-10-23-p5-ci.md`, `docs/verifiche/evidenze/eval-p5/<ora>/`

- [ ] **Step 1 (controller): eval dei casi `spec`.** `evals/run.sh spec` (decisioni 7, 8, 9): 9 casi, 3 corse per braccio. Ogni caso sotto soglia si analizza (decisione 7); un difetto del prodotto è un giro di correzione di questo task (implementatore, test che fallisce, `tests/run`), poi si ripete **solo** quel caso con `evals/run.sh <caso>`.
- [ ] **Step 2 (controller): eval dei casi `extra`.** `evals/run.sh extra`, stesse regole.
- [ ] **Step 3 (controller): CI.** Push del ramo `p5-eval-ci` (alla testa del ramo) su `ginz0ls/tollgate`; `gh run watch` del run di `ci.yml`; i due job verdi. Un rosso solo sui runner (e non in locale) è un giro di correzione. Durata e minuti per job.
- [ ] **Step 4: Rapporti.** `2026-10-23-p5-eval.md`: per caso esecutore (decisione 9), punteggio con e senza plugin, Δ, corse riuscite su 3, costo, durata, token, esito «sopra soglia», «sotto soglia: difetto corretto» o «sotto soglia: varianza»; costo totale e residuo del tetto; casi non eseguiti per il tetto. `2026-10-23-p5-ci.md`: run, SHA, job, durata, minuti, esito.
- [ ] **Step 5: Commit** «tollgate P5: eval reali (3 corse per caso) e CI verde».

---

