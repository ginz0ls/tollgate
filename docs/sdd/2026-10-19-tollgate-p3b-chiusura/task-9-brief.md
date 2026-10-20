### Task 9: `finish open-pr`, blocco JSON 18.1, merge e chiusura

**Files:**
- Create: `bin/tollgate_analysis/prblock.py`, `bin/tollgate_analysis/prbody.py`, `bin/tollgate_flow/openpr.py`, `bin/tollgate_flow/prstate.py`
- Modify: `bin/tollgate_flow/gh.py`, `bin/tollgate_flow/gitw.py`, `bin/tollgate_flow/finishcheck.py` (chiama `prstate.detect`), `bin/tollgate_core/cli.py` (`finish open-pr [--update]`), `tests/fakegh.py`
- Test: `tests/test_prblock.py`, `tests/test_prbody.py`, `tests/test_gh.py`, `tests/test_openpr.py`, `tests/test_prstate.py`

**Interfaces:**
- Produces in `prblock.py` (decisione 11): `FIELDS` (le chiavi di 18.1 nell'ordine della spec), `SCHEMA_VERSION = 1`, `build(facts: dict) -> dict` (`KeyError` se manca un campo di `FIELDS`), `render(block: dict) -> str`, `parse(text: str) -> dict | None`.
- Produces in `prbody.py`: `MAX_TEXT = 2000`; `neutralize(text: str, max_len: int = MAX_TEXT) -> str` (recinto più lungo di ogni sequenza di backtick, `@` seguito da `​`, troncato con «… (troncato)»); `render(*, issue: int, level: str, dod_lines: list[str], notes: list[dict], waivers: list[str], warnings: list[str], block: dict) -> str` (prima riga `Closes #<issue>`, poi le sezioni; le note sono i rilievi confermati non bloccanti, 10; il blocco per ultimo).
- Produces in `gitw.py`: `push_sha(repo, sha, branch, *, lease: str | None) -> None` (`git push origin <sha>:refs/heads/<ramo>`, con `--force-with-lease=refs/heads/<ramo>:<lease>` se `lease`; `GitWriteError` se fallisce); `remote_sha(repo, branch) -> str | None` (`ls-remote --heads origin`).
- Produces in `gh.py`: `run_json_lines(state, repo, args) -> list[dict]` (una riga JSON per oggetto, per `--paginate --jq`); `pr_for_branch(state, repo, branch) -> dict | None` (`pr list --head <ramo> --state all --json number,state,url,headRefOid,mergedAt`, la PR con il numero più alto); `pr_view(state, repo, number) -> dict` (`pr view <n> --json number,state,url,mergedAt`); `pr_create(state, repo, *, branch, base, title, body_file) -> None`; `pr_edit(state, repo, number, *, body_file) -> None`; `pr_comments(state, repo, number) -> list[dict]`; `prs_for_branch_prefix` passa a `api --paginate repos/{owner}/{repo}/pulls?state=all&per_page=100 --jq '.[] | {number, headRefName: .head.ref, state, url: .html_url}'` (una riga JSON per PR, riga 56; G5 del Task 1).
- Produces in `fakegh.py`: le PR stanno in `data["prs"]` con `number`, `headRefName`, `state`, `url`, `headRefOid`, `mergedAt`, `body`, `comments`; `pr create` aggiunge una PR e riscrive il file dei dati; `pr edit` riscrive `body`; `pr view`; `api --paginate …/pulls` stampa una riga per PR; `data["fail"]` (`["pr create"]`…) fa uscire con 1 quel comando, per simulare i guasti.
- Produces in `prstate.py` (decisione 12): `Detection(kind: str | None, pr: dict | None)` con `kind` in `merged`, `closed`, `open`, `None`; `detect(state, conn, work, repo, *, now, session=None) -> Detection` (con `merged` chiude il lavoro ed emette `merge_detected`; senza rete o con `GhError` restituisce `None` e la CLI avvisa); `CLOSED_HINT` (le due strade).
- Produces in `openpr.py`:
  - `OpenResult(code: int, lines: list[str], url: str | None)`;
  - `open_pr(state, cwd, *, update: bool, now=None, argv=None, via_sync: str | None = None) -> OpenResult`. `via_sync` è l'id dell'atto `sync` già consumato da `sync`: sostituisce l'atto `finish` (decisione 17).
  - `facts(conn, state, work, cfg, wt, head) -> dict`: i campi di 18.1 (decisione 11), usati da `open_pr` (`adopt` legge il blocco con `prblock.parse`). `open_pr` ricalcola la DoD con `findings_cycle` = numero dell'ultimo ciclo chiuso su HEAD (o con lo stesso `patch-id`) e `specialists` = specialisti attesi in L2 (decisione 15).
- Comportamento: decisione 10, nell'ordine scritto lì; i rifiuti escono tutti insieme con le righe `rifiuto: …` e codice 1; con PR chiusa senza merge, `CLOSED_HINT`. Le note e il testo dei rilievi passano da `prbody.neutralize`.
- CLI: `tollgate finish open-pr [--update]`, sessione con `cli_session(state, cwd, "finish", argv=…)` (serve per `approve pr`).

- [ ] **Step 1: Test** `test_prblock.py`: `test_build_has_all_fields_in_order`; `test_render_never_contains_comment_close` (stringa con `-->` in `plan` → nessun `-->` dentro il commento); `test_parse_last_block_and_garbage` (due blocchi → l'ultimo; JSON rotto → `None`).
- [ ] **Step 2: Test** `test_prbody.py`: `test_hostile_finding_text_neutralized_and_block_roundtrips` (Review Focus 2); `test_closes_line_first`.
- [ ] **Step 3: Test** `test_gh.py` (con `fakegh`): `test_pr_for_branch_latest`; `test_prs_for_branch_prefix_paginated` (250 PR nei dati → trova la più vecchia); `test_pr_create_and_edit_roundtrip`.
- [ ] **Step 4: Test** `test_openpr.py` (`FlowLab` con lavoro L1 in `review`, ciclo `ok` su HEAD):
  - `test_refused_without_finish_or_approve_pr` (criterio 12);
  - `test_finish_act_after_long_review_opens_pr` (atto `finish` registrato 30 minuti prima → PR creata, fase `pr_open`, `pr_number`; criterio 12);
  - `test_commit_after_finish_invalidates` (criterio 12);
  - `test_finish_of_other_work_refused` (criterio 12);
  - `test_finish_survives_clear` (atto `finish` di una sessione, `open-pr` da un'altra sessione dello stesso lavoro → PR; criterio 12);
  - `test_interrupted_after_push_no_duplicate_pr` (`fail: ["pr create"]`, poi senza guasto → una sola PR; poi PR già creata e intento ancora `requested` → `pr edit`, non una seconda; criterio 12, Review Focus 1);
  - `test_refusals_collected` (deroga `test` in attesa, effetto `requested`, rilievo senza esito → tre righe `rifiuto:`; criterio 9);
  - `test_task_not_done_refused` (task rimesso `review` nel DB → rifiuto dalla DoD ricalcolata; criterio 41);
  - `test_open_pr_after_needs_fix_then_ok_cycle` (ciclo 1 `needs_fix`, task di correzione, ciclo 2 `ok` → PR aperta; decisione 15);
  - `test_closed_pr_then_confirm_creates_new_pr` (PR `CLOSED` con `pr_number` azzerato → `pr create`, non `pr edit`);
  - `test_finish_act_valid_without_session_signal` (atto `finish` valido e nessun segnale → PR aperta: la sessione serve solo per `approve pr`);
  - `test_dod_component_off_does_not_block` (criterio 18, `definition_of_done`);
  - `test_final_review_off_skips_cycle` (criterio 18, `final_review`);
  - `test_non_fast_forward_without_intent_refused` (ramo remoto avanzato a mano → rifiuto senza push; criterio 16);
  - `test_block_in_body_parses` (`prblock.parse(body)` ha `issue`, `head_sha`, `plan_sha`, `verdict.cycles`).
- [ ] **Step 5: Test** `test_prstate.py`: `test_merged_closes_work`; `test_closed_unmerged_returns_closed`; `test_offline_is_none`; `test_finish_check_refuses_on_closed_pr`.
- [ ] **Step 6: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: finish open-pr con il blocco JSON 18.1, rilevamento di merge e chiusura».

---

