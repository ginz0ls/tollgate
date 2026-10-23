### Task 10: `gate sentinel`, base in `detect` e issue di sentinel

**Files:**
- Create: `bin/tollgate_gate/sentinel.py`, `tests/test_gate_sentinel.py`
- Modify: `bin/tollgate_gate/baseids.py` (`--publish`), `bin/tollgate_gate/cli.py`, `bin/tollgate_flow/gh.py` (`sentinel_issues` → `github.open_sentinel_issues`, rinviato di P3a riga 56), `tests/test_gh.py`

**Interfaces:**
- Produces: `sentinel.unverified(repo, *, before: str, after: str, prs_for_commit, statuses) -> list[tuple[str, str]]` (commit e motivo; funzioni di lettura passate come parametri per i test); `sentinel.run(event_path, *, publish, environ) -> int`; `baseids.publish(...)` (in `detect`: `tollgate/base`, commento sull'issue se la suite fallisce).
- CLI: `tollgate gate sentinel --event <file> [--publish]`.

- [ ] **Step 1: Test** `test_gate_sentinel.py` (criteri 10 e 34, decisione 16): `test_direct_push_red_and_issue` (commit senza PR → stato `failure` e issue creata); `test_merge_of_red_verdict` (PR unita con `verdict` `failure` → rosso); `test_status_from_user_token_not_trusted` (Review Focus 4); `test_latest_status_wins` (`success` vecchio seguito da `failure` → non verificato); `test_rebase_merge_commits` (forma di V5); `test_evaluate_then_sentinel_cross_command` (Review Focus 4: `gate evaluate --publish` scrive gli stati nel `gh` finto, poi `gate sentinel` sul commit di merge li legge e non apre l'issue); `test_first_install_ignored` (il commit che aggiunge `tollgate-sentinel.yml` e i precedenti non aprono l'issue); `test_single_issue_reused` (secondo allarme → commento sulla stessa issue); `test_before_all_zeros`; `test_component_off_exits`; `test_base_failure_comments_issue_in_detect`.
- [ ] **Step 2: Test** `test_gh.py::test_sentinel_issues_paginated` (110 issue aperte, quella di sentinel alla 105 → trovata; le PR scartate).
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: sentinel, tollgate/base in detect, issue di sentinel paginate».

---

