### Task 9: `gate evaluate` su GitHub

**Files:**
- Create: `bin/tollgate_gate/verdict.py`, `tests/test_gate_github.py`
- Modify: `bin/tollgate_gate/github.py`, `bin/tollgate_gate/cli.py`

**Interfaces:**
- Consumes: `evaluate.evaluate` (puro, Task 4-5), `artifacts`, `baseids.load` (Task 7), `comment` (Task 6), `github` (Task 8).
- Produces in `verdict.py` (l'I/O sta qui, `evaluate.py` resta puro, rilievo M-12): `prechecks(event: dict, pr: dict | None, *, default_branch: str, open_prs_for_sha: list[dict]) -> tuple[str, str]` (`"ok"`, `"error"` o `"not_applicable"`, con il motivo; decisione 5); `inputs_from_github(repo: Path, event: dict, pr: dict, *, artifacts: Path, base_ids_cache: Path | None, base_ids_artifact: Path | None, state, environ) -> tuple[GateInputs | None, list[str]]`; `main(event_path, *, artifacts, base_ids_cache, base_ids_artifact, publish, head_ids_out, environ) -> int`. Il payload di `workflow_run` non porta corpo né repo della testa (rilievo M-3): `verdict` legge la PR con `GET pulls/<n>` (numero da `workflow_run.pull_requests`, o da `GET commits/<sha>/pulls` se vuoto), il corpo da lì, e fa `git fetch origin refs/pull/<n>/head`. `github.pr_from_event` serve solo a `guard` (`pull_request_target`).
- CLI: `tollgate gate evaluate --event <file> --artifacts <dir> [--base-ids-cache <file>] [--base-ids-artifact <dir>] [--publish] [--head-ids-out <file>]`.

- [ ] **Step 1: Test** `test_gate_github.py` (banco `GateLab` più il `gh` finto con PR, issue, stati e commenti; evento `workflow_run` scritto dal test nella forma di V3):
  - `test_clean_pr_green` (criterio 10 «PR pulita»: `verdict` e `attention` `success`, commento con il marcatore);
  - `test_prechecks` (`workflow_run.path` diverso, `event` diverso da `pull_request` → `error`);
  - `test_not_applicable_writes_no_status` (PR verso `other`: nessuno stato `tollgate/*` scritto, solo il commento «non applicabile»; Review Focus 5);
  - `test_sha_shared_by_two_prs_is_error` (due PR aperte verso il predefinito con la stessa testa → `error`);
  - `test_superseded_sha_is_error` (la PR ha una testa nuova: `error` sullo SHA vecchio, nessun commento scritto);
  - `test_missing_or_invalid_artifact_is_error` (artefatto assente, `report` con `../` e XML con entità, criterio 10);
  - `test_config_changed_after_run_is_error` (`config_sha` diverso dalla punta, rilievo M-6);
  - `test_invalid_default_config_is_error` (motivo nella descrizione, uscita 0, niente traceback);
  - `test_fork_pr_treated_as_manual` (decisione 4);
  - `test_base_ids_source_order` (Review Focus 7; cache e artefatto nel formato per comando);
  - `test_comment_updated_not_duplicated` (due esecuzioni sullo stesso SHA → un commento; un commento con lo stesso marcatore di un altro autore resta intatto; più di 100 commenti → paginati);
  - `test_head_ids_cached_only_on_success` (e non da fork, non con `guard` assente o di un altro autore, non con un insieme di comandi diverso da `ids_commands`);
  - `test_sentinel_issue_open_in_attention` (`sentinel_open` «da leggere»).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: gate evaluate su GitHub (controlli preliminari, stati, commento, cache della testa)».

---

