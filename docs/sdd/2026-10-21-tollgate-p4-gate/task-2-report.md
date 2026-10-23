# Report Task 2: moduli senza stato, `tollgate_gate`, strati

Commit `7102192` (ramo `p4-gate`, base `bae003e`).

## Implementato
- `tollgate_core/runner.py`: `CommandSpec`, `gate_commands`, `dod_commands`, `receipt_state`, `clean_env`, `counts_green`, `report_path`, `run_one` (firma di oggi, annotata), `executed_ids`, `ids_commands`, `TIMEOUT_EXIT`. `verify.py` li importa da lì e tiene gli alias privati `_run_one`, `_report_path`, `_report_for`.
- `tollgate_core/ghcli.py`: `GhError`, `GH_ENV`, `GH_TIMEOUT_S`, `REQUIRED_CONTEXTS`, `SENTINEL_TITLE`, `BOT_LOGINS` (V1), `gh_cmd`, `run`, `run_json`, `run_json_lines`, `decode_json_values`, `ApiResult`, `api(...)`. `tollgate_flow/gh.py` li re-esporta (stessa classe `GhError`; `gh._run` è `ghcli.run`). `api`: `paginate` senza `jq` → `ValueError` (D15), `data` = lista dei valori; `include=True` legge la riga di stato (forma V2, accetta `\r\n\r\n` e `\n\n`), l'uscita non zero con riga di stato non è un errore; senza `--include` l'uscita non zero è `GhError`.
- `tollgate_core/diffcheck.py`: `DiffCheck`, `diff_check`, `diff_findings` (firma del piano), `scope_exempt_rel`, `guard_config` e `is_docs_md` (spostati, importabili ancora da `violations`). `violations.diff_violations(..., *, components, approved_spec=None)` prepara i dati dal DB e chiama `diff_findings`; il controllo del collegamento simbolico di `is_registered_plan` resta in `violations`.
- `finishcheck`: `_own_document` rimosso; calcola `approved_spec = (spec_path, sha)` con `l2tree` come prima e lo passa a `diff_violations`.
- `tollgate_gate/__init__.py` e `tollgate_gate/l2tree.py` (spostato con `git mv`); `tollgate_flow/l2tree.py` re-esporta i nomi.
- `git.py`: `_check_ref` usata da `resolve_ref`, `changes`, `diff_size`, `show` (quindi `text_at`), `ls_files_at`, `blob_at`, `exists_at`, `rev_list`, `patch_id` e `fetch_ref`; `fetch_ref(repo, ref, *, token=None)` con l'intestazione solo nelle variabili `GIT_CONFIG_*` del figlio.
- `tests/fakegh.py`: `api_status` (forma V2 di `--include`) e route REST dei commenti (`user.login = github-actions[bot]`, `type = Bot`) accanto a `pr view` (`author.login = github-actions`); risposte esistenti invariate.

## Test
- Nuovi: `test_runner.py` (executed_ids, ids_commands, nomi di verify, run_one), `test_ghcli.py` (include 403/404/200/corpo vuoto/LF, errore senza include, paginate, argomenti, BOT_LOGINS, re-export), `test_diffcheck.py` (uguale a `diff_violations`, `watched`, scope None, L0 e componente spento, spec approvata solo sullo stesso blob, `plan_change_is_attention`, working tree, `scope_exempt_rel`, nomi spostati), `test_git.py` (`test_refs_starting_with_dash_refused` su 15 chiamate senza processi lanciati; `fetch_ref` con token solo nell'ambiente e senza token su un repo nudo locale), `test_layers.py` (`imported_modules`, allowlist del gate, nucleo senza gate, runtime senza DB su moduli scoperti dinamicamente, flusso può importare il gate), `test_analysis_isolation.py` (`tollgate_gate` vietato all'analisi).
- RED: i nuovi test eseguiti su un `git archive` di `bae003e` con i soli file di test nuovi: `Ran 46 tests ... FAILED`; `ImportError: cannot import name 'runner'/'ghcli'/'diffcheck' from 'tollgate_core'` (3 moduli di test), 14 sotto-test di `test_refs_starting_with_dash_refused`, 2 `fetch_ref`, `test_flow_may_import_gate`, `test_gate_runtime_has_no_db`.
- GREEN: `tests/run` (python3.11 e python3 = 3.13.5): `Ran 1788 tests ... OK` per entrambi, exit 0. Dopo la corsa ho tolto un import inutilizzato da `tollgate_flow/gh.py` (nessun effetto) e rilanciato `test_gh` e `test_ghcli` (24 test, OK).

## Scostamenti dal piano
- `diff_check`/`DiffCheck` (D14) e `approved_spec` facoltativo (D1) come da carry.
- `test_same_result_as_diff_violations` usa `FlowLab(issue=7, phase="plan")` con `register_plan` e commit del piano (L1), come da brief.
- `resolve_ref` e `patch_id` ricevono anch'esse `_check_ref` (il brief dice «ogni funzione che riceve un riferimento»): un riferimento con `-` iniziale ora è `GitError` invece di `None`.
- `fetch_ref` non restituisce nulla (il chiamante legge `FETCH_HEAD`); timeout 120 s (`FETCH_TIMEOUT_S`), non i 10 s di `GIT_TIMEOUT_S`.
- `api(include=True, paginate=True)` → `ValueError` (non specificato: due modalità di uscita incompatibili).

## Dubbi
Nessuno bloccante. Il docstring di `git.py` ora dice «sola lettura, tranne `fetch_ref`».

## Fix round 1
- `git.blob_text` ora chiama `_check_ref(sha)`; riga `blob_text` aggiunta a `test_refs_starting_with_dash_refused`. Ricontrollate tutte le funzioni di `git.py` con un riferimento o SHA: `range_base` e `commit_changes` passano da `resolve_ref` e `changes` (già coperte); `blob_sha` e `worktree_text` ricevono percorsi, non riferimenti.
- `fetch_ref` imposta `GIT_TERMINAL_PROMPT=0` nell'ambiente del figlio (con o senza token); asserzione in `test_fetch_ref_passes_token_only_in_environment` e `test_fetch_ref_without_token_...`.
- Test mirati: `python3 -B -m unittest tests.test_git` → 34 test OK. `tests/run`: python3.11 `Ran 1788 tests ... OK`, python3 (3.13.5) `Ran 1788 tests ... OK`, exit 0.
