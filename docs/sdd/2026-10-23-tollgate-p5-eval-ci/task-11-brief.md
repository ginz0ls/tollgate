### Task 11: Esecuzione degli eval con tetto e conto dei costi

**Files:**
- Create: `evals/run.sh`, `evals/cost.py`, `tests/test_eval_run.py`; solo se il Task 1 fa scattare la decisione 9 (b) **e l'utente dà l'OK**: `evals/_kit/local.py`

**Interfaces:**
- Produces:
  - `evals/run.sh <spec|extra|<caso>> [--runs N]`: controlla il residuo del tetto (`cost.py remaining`), mette `tests/evalbin` (o la sua copia in `/tmp/tollgate-eval-target/tests/evalbin` con la decisione 9 (c)) in testa al `PATH`, lancia `claude plugin eval <radice o target> --tag <tag>|--case <caso> --scaffold --trust-plugin --no-publish --model claude-sonnet-5-5 --allow-tools Bash Write Edit --threshold 0.66 --ablation <with-without per spec, none per extra> --max-cost-usd <residuo> --output-dir <cartella della decisione 23> --json <…>/result.json --report <…>/report.html`, poi `cost.py add` **qualunque sia l'uscita** (1 sotto soglia è il caso comune, 2 al tetto); senza `result.json` dopo una corsa avviata si ferma con «costo ignoto: controlla a mano prima di continuare» e non lancia altro; rifiuta senza residuo, con un `--publish-report` o con una cartella d'uscita diversa;
  - `cost.py add <result.json>` (aggiunge a `budget.tsv` una riga `ora | invocazione | costUsd | durationSeconds | casi`), `cost.py remaining -> float` (80 meno la somma), `cost.py table <result.json…> -> str` (tabella Markdown per caso: punteggio con e senza plugin, Δ, corse, costo, durata, token se presenti, VE8);
  - se serve, `local.py run <caso> --runs 3 --arm with|without --out <dir>` (decisione 9 (b)): residuo del tetto controllato prima di **ogni** corsa, stessi grader sul `stream-json`, controllo dei comandi della `trace` a fine corsa, risultato nella stessa forma usata da `cost.py`.

- [ ] **Step 1: Test** `test_eval_run.py` con un `claude` finto nel `PATH` che registra gli argomenti e scrive un `result.json` fittizio: `test_always_no_publish` (Review Focus 6); `test_refuses_without_budget` (`budget.tsv` a 80 → uscita 1, `claude` mai lanciato); `test_max_cost_is_remaining`; `test_cost_added_on_nonzero_exit` (uscita 1 e 2: la riga entra in `budget.tsv`); `test_missing_result_stops_and_asks`; `test_shim_first_in_path` (la cartella è `tests/evalbin` della radice, o della copia con la decisione 9 (c)); `test_output_dir_fixed`; `test_cost_table` (dal JSON di VE8). Se c'è `local.py`: `test_local_graders_on_stream_json` (regex, `tool_used`, `tool_order`, `file_exists` su un flusso registrato), `test_local_arm_without_plugin_has_no_plugin_dir`, `test_local_checks_budget_before_each_run`, `test_local_flags_exclude_user_config` e `test_local_audit_flags_unlisted_command`.
- [ ] **Step 2: Fallimento, implementazione, `tests/run`, commit** «tollgate P5: esecuzione degli eval con tetto, conto dei costi».

---

