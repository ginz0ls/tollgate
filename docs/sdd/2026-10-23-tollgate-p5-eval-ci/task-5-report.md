# Task 5: report dell'implementatore

## Cosa è stato fatto

- **M-3, `pending` di `guard`** (`bin/tollgate_gate/guard.py`): `PENDING_ACTIONS = ("opened", "edited", "reopened")`,
  `PENDING_DESCRIPTION = "rivalutazione in corso"`, `VERDICT_CONTEXT`. Il `pending` su `tollgate/verdict` si scrive
  solo con `publish`, **dopo** il ritorno per PR non applicabile (scan 5.3: una PR verso un altro ramo non riceve
  mai stati) e prima dei controlli (`origin/<default>`, fetch, SHA condiviso). `verdict.VERDICT` ora è
  `guard.VERDICT_CONTEXT` (un solo punto).
- **Guard verde aggiorna il commento rosso**: `comment.is_guard_red` (riconosce il titolo «rosso» alla terza riga,
  quindi non il «non applicabile» né un testo d'utente), `comment.render_guard_resolved`, e in `github.py`
  `bot_comment` / `edit_comment` (`upsert_comment` le riusa). Un guard verde riscrive in «risolto» il commento
  rosso del bot, senza mai crearne uno.
- **M-4, sentinella** (`bin/tollgate_gate/sentinel.py`): `CHECKED_DESCRIPTION = "controllato fino a qui"`,
  `WALK_LIMIT = 200`, `last_checked(repo, after, statuses, *, limit=200)`: risale il primo genitore da `after`
  escluso, al più 200 GET, e si ferma al primo commit con uno stato `tollgate/sentinel` di qualunque valore scritto da
  `github-actions[bot]` (`ghcli.STATUS_BOT`). `_commits` usa `last_checked(...) or before` solo per il push non
  forzato con `before` non zero; push forzato e `before` tutto zeri come prima; `_first_install` invariato.
  `run` con `publish` scrive, dopo i `failure`, il `success` «controllato fino a qui» su `after` se `after` non è
  tra i non verificati (anche con altri commit rossi), prima dell'issue.
- `gate/workflows/tollgate-sentinel.yml`: `concurrency: {group: tollgate-sentinel, cancel-in-progress: false}`
  (nessuna `${{ }}` in `run:`, azioni ancora fissate per SHA).
- **Minori**:
  - `verdict._judge`: un `GhError` nel commento «non applicabile» di una PR verso un altro ramo non scrive `error`:
    messaggio su stderr (`json.dumps`, una riga), uscita 0.
  - `baseids.publish_from`: `ConfigError`/`GitError` dopo il caricamento della configurazione della punta → in
    `detect` stato `error` (descrizione fissa) e uscita 1, in `protected` nessuno stato e uscita 1 (D11).
  - `baseids._publish`: con `components.base_test_ids` spento, in `detect`, `tollgate/base` `success` con
    «componente base_test_ids spento» (senza issue).
  - `ghcli._retry_delays`: `TOLLGATE_GH_RETRY_DELAYS` malformato, negativo, `nan` o `inf` → `GhError` con il nome
    della variabile, `gh` non parte.
  - `tests/fakegh.py`: righe 46, 230, 231 spezzate; il finto pagina davvero (senza `--paginate` solo la prima pagina,
    `per_page` della query, 30 se manca; con `--paginate` tutto), anche per `statuses`, `commits/<sha>/pulls`,
    `issues?state=open`.

## Test nuovi e cambiati, RED/GREEN

Comandi: `python3.11 -B -m unittest <modulo>` dalla radice del worktree.

RED (prima del codice), esiti reali:
- `tests.test_gate_sentinel` (dopo aver scritto `SkipCiTest` e aggiornato gli attesi): `Ran 67 tests ... FAILED
  (failures=7, errors=5)`: ERROR `test_clean_push_writes_success_marker`, `test_last_checked_follows_first_parent_only`,
  `test_last_checked_returns_the_first_marker_going_up`, `test_no_marker_walk_bounded`,
  `test_other_context_marker_does_not_stop_the_walk` (manca `sentinel.last_checked`/`CHECKED_DESCRIPTION`/`WALK_LIMIT`);
  FAIL `test_evaluate_then_sentinel_cross_command`, `test_fast_forward_is_not_forced`, `test_first_install_ignored`,
  `test_rebase_merge_commits`, `test_first_install_still_ignored`, `test_skipped_push_checked_next_time`,
  `test_success_marker_on_after_even_if_an_earlier_commit_is_red`.
- `tests.test_gate_guard`: `Ran 69 tests ... FAILED (failures=5, errors=1)`: `PendingTest.test_edited_publishes_pending_then_verdict_replaces`,
  `test_opened_publishes_pending`, `test_reopened_publishes_pending`, `test_pending_is_written_before_the_checks`,
  `test_pending_actions` (ERROR, manca `PENDING_ACTIONS`), `RunTest.test_green_guard_updates_previous_red_comment`.
- `tests.test_gate_workflows`: `FAIL: test_sentinel_concurrency ... AssertionError: {} != {'group': 'tollgate-sentinel', 'cancel-in-progress': 'false'}` (file riportato allo stato precedente per vedere il rosso).
- `tests.test_ghcli`: `test_bad_retry_delays_is_config_error` falliva per `-1`, `nan`, `inf` (nessun errore) e con `ValueError` nudo per `abc`, `1,,2`, `0,x`, `1;2`.
- `tests.test_gate_github`: FAIL `test_other_base_ghError_writes_no_status` e `test_other_base_comment_write_failure_writes_no_status` (scriveva `error`).
- `tests.test_gate_run`: ERROR per le tre `PublishFromErrors*` (la `ConfigError`/`GitError` usciva dal comando) e FAIL
  `test_component_off_description`.

GREEN (dopo il codice), un modulo per volta:
- `test_gate_sentinel` 67 OK; `test_gate_guard` + `test_gate_comment` 87 OK; `test_gate_github` 68 OK;
  `test_gate_run` + `test_gate_sentinel` 101 OK; `test_gate_workflows` 32 OK; `test_ghcli` 29 OK; `test_gh` 16 OK.
- Suite completa: vedi in fondo.

### Test nuovi (per file)
- `test_gate_guard.py`: `PendingTest` (`test_edited_publishes_pending_then_verdict_replaces`, `test_reopened_publishes_pending`,
  `test_opened_publishes_pending`, `test_synchronize_no_pending`, `test_no_pending_for_other_base`,
  `test_other_base_keeps_the_previous_verdict`, `test_dry_run_publishes_no_pending`, `test_pending_is_written_before_the_checks`,
  `test_pending_actions`); `RunTest.test_green_guard_updates_previous_red_comment`, `test_green_guard_without_comment_creates_none`,
  `test_green_guard_leaves_not_applicable_comment_alone`. `GuardBase.event` ha il nuovo parametro `action`.
- `test_gate_sentinel.py::SkipCiTest`: `test_clean_push_writes_success_marker`, `test_dry_run_writes_no_marker`,
  `test_red_after_gets_failure_not_success`, `test_success_marker_on_after_even_if_an_earlier_commit_is_red`,
  `test_skipped_push_checked_next_time` (P0 controllato dal codice, A senza run, B: si vedono A e B e ci si ferma al
  segnale di P0), `test_walk_stops_at_a_failure_marker_too`, `test_user_written_sentinel_status_ignored`,
  `test_user_marker_on_after_parent_does_not_skip_commits` (login `github-actions` senza `[bot]`),
  `test_other_context_marker_does_not_stop_the_walk`, `test_last_checked_returns_the_first_marker_going_up`,
  `test_last_checked_follows_first_parent_only`, `test_no_marker_walk_bounded` (catena vera di 210 commit con
  `commit-tree`: esattamente 200 GET poi `before`), `test_forced_push_still_uses_before`,
  `test_before_all_zeros_checks_only_after`, `test_first_install_still_ignored`, `test_single_issue`.
- `test_gate_workflows.py::test_sentinel_concurrency`: fissa `concurrency` e le chiavi di primo livello
  (`name`, `on`, `permissions`, `concurrency`, `jobs`).
- `test_gate_github.py` (`MinorsTest`): `test_other_base_ghError_writes_no_status`, `test_other_base_comment_write_failure_writes_no_status`,
  `test_edited_changing_base_reevaluated`.
- `test_gate_run.py`: `PublishFromErrorsDetectTest` (`test_publish_from_config_error_is_error_and_red_job` come da D11,
  `test_publish_from_git_error_is_error_and_red_job`, `test_unreadable_config_at_the_tip_is_still_a_message`),
  `PublishFromErrorsProtectedTest.test_publish_from_config_error_is_red_job_without_status`,
  `ComponentOffDescriptionTest.test_component_off_description`.
- `test_ghcli.py`: `test_bad_retry_delays_is_config_error`, `test_paginate_non_object_values`.
- `test_gh.py`: `SentinelIssuesTest.test_fake_pages_like_github` (il finto pagina davvero; `test_sentinel_issues_paginated`
  resta con la sentinella alla riga 105 e il finto che adesso pagina).
- `test_gate_comment.py`: `test_guard_red_is_told_from_resolved_and_not_applicable`.

### Test esistenti cambiati (e perché, D13)
- `test_gate_sentinel.py::RunTest.test_rebase_merge_commits`: dopo il primo push solo `commits[-1]` ha il `success`;
  al secondo push la risalita si ferma lì e l'atteso è `[commits[-1], direct]` con `direct` `failure`. Il secondo push
  non usa più `set_gh` (che azzerava il segnale scritto dal codice) ma aggiorna i dati.
- `test_first_install_ignored`: ultimo atteso `[install, later]` (`install` `success`, `later` `failure`).
- `test_fast_forward_is_not_forced`: gli stati sentinella di `after` sono `["success"]`.
- `CrossCommandTest.test_evaluate_then_sentinel_cross_command`: il commit di merge ha il `success` «controllato fino a qui»
  (nessuna issue, nessun `failure`).
- `RunTest.test_dry_run_does_not_need_github_repository`: la prima chiamata ora è la GET degli stati della risalita;
  si cerca la GET di `commits/<sha>/pulls` tra le chiamate.
- `tests/test_gh.py`: import di `ghcli` per il nuovo test.
- `tests/test_criteria_p4.py::assert_sentinel_red` non cambia e passa.

## File toccati
`bin/tollgate_core/ghcli.py`, `bin/tollgate_gate/{baseids,comment,github,guard,sentinel,verdict}.py`,
`gate/workflows/tollgate-sentinel.yml`, `tests/fakegh.py`, `tests/test_{gate_comment,gate_github,gate_guard,gate_run,gate_sentinel,gate_workflows,gh,ghcli}.py`.

## Scostamenti dal piano e perché
- D11 (uscita 1 in `publish_from`, nome del test): applicato. La configurazione della **punta** deve comunque
  leggersi: se `load_config_at` fallisce non si conosce la modalità, l'errore arriva al confine di `cli` (messaggio,
  uscita 1, nessuno stato). Coperto da `test_unreadable_config_at_the_tip_is_still_a_message`.
- `test_paginate_non_object_values` e `test_edited_changing_base_reevaluated` passavano già prima del codice
  (`decode_json_values` rifiuta già i valori non oggetto, e verdetto/guard già non scrivono per altro ramo): sono test di
  caratterizzazione che chiudono la lacuna di test dei minori di P4, senza codice nuovo.
- Il guard verde riscrive il commento rosso **di qualunque SHA** (non solo dello stesso): un «rosso» rimasto su una PR
  ormai verde sarebbe peggio. Il commento è uno solo per PR per costruzione.
- Descrizione di `tollgate/base` per `ConfigError`/`GitError`: fissa («errore nella lettura della configurazione o
  dell'albero della base»); il messaggio dell'eccezione va solo su stderr, con `json.dumps`.
- `fakegh`: le liste (statuses, commit pulls, issue aperte) ora rispondono anche senza `--paginate` (prima pagina).

## Autorevisione
- Completezza: M-3, M-4, concurrency, tutti i minori del brief e le voci di `carry.md` (D11, D13, scan 5.3, righe lunghe).
- Nessuna `${{ }}` nelle righe `run:`; `PinTest` verde. `git status` pulito da `__pycache__` (`-B`).
- Costo dichiarato in decisione 16: una GET di stati per commit risalito (in un push normale: 1).
- Nessun file fuori dal task; il testo non fidato non entra negli argomenti di `gh` (commenti e stati passano da file).

## Dubbi
- Un push forzato su un ramo con `before` non antenato non risale (decisione 16): `after` resta `failure` «push forzato» e
  non riceve il `success`.
- Se la risalita passa oltre `before` (push saltato) e c'è un merge commit nella storia di primo genitore, `rev_list`
  può includere commit già controllati dall'altro lato del merge: ricontrollati (più GET), mai saltati.

## Suite completa
`tests/run` (in background, una volta): `== Python 3.11.16  Ran 2644 tests in 730.366s  OK (skipped=2)` e
`== Python 3.13.5  Ran 2644 tests in 717.511s  OK`, uscita 0. Dopo la suite ho solo avvolto in `redirect_stdout` il
test `test_dry_run_publishes_no_pending` (stampava `guard: verde`) e rilanciato `tests.test_gate_guard` (69 OK, 3.11 e
3.13); il resto dell'output «guard: la PR è avanzata…» è del test preesistente `test_pr_advanced_since_the_event_writes_nothing`.

## Fix round 1
- `guard` verde riscrive in «risolto» solo il commento rosso con marcatore `sha == head` (`comment.guard_marker_sha`); il commento di un altro SHA resta com'è. Corregge anche il dubbio del primo report.
- Test `RunTest.test_green_guard_keeps_red_comment_of_another_sha`: RED prima (`FAIL`, condizione tolta temporaneamente), poi OK.
- Test `test_edit_comment_failure_after_green_status_is_a_message`: `GhError` in `edit_comment` dopo il `success` esce da `cli.main` con messaggio e uscita 1, senza traceback (il confine di `cli` già lo gestiva; nessun codice nuovo).
- `tests/fakegh.py`: riga corta a metà frase ricomposta.
- `tests.test_gate_guard` + `test_gate_comment` OK; `tests/run`: 3.11 `Ran 2646 OK (skipped=2)`, 3.13 `Ran 2646 OK`, uscita 0.
