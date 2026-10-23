# Task 9 — gate evaluate su GitHub: report

Commit 6afc140 «tollgate P4: gate evaluate su GitHub (controlli preliminari, stati, commento)» (senza «cache della testa», V4).

## Implementato
- `bin/tollgate_gate/verdict.py` (nuovo): `prechecks`, `inputs_from_github`, `main` (con `repo` opzionale come in `guard.run`). Nessuna scrittura in cache, nessun `head_ids_out`.
- `cli.py`: sottocomando `evaluate` (`--event --artifacts [--base-ids-cache FILE] [--base-ids-artifact DIR] [--publish]`); eredita `allow_abbrev=False`, rifiuto di `--publish` fuori da Actions, gestione delle eccezioni.
- `github.py`: `pull` (GET pulls/<n>), `pr_from_rest`, `run_sha`, `event_repo`; D16: `issue` con chiave `pull_request` restituisce `IssueFacts(..., is_pr=True)`.
- `model.py`: `IssueFacts.is_pr` (default False). `evaluate.py`: `_issue_state` dà rosso «#M è una PR, non un'issue»; `waiver_issue` non vale per una PR.
- `artifacts.read_results(root, *, meta=None)`: compatibile, riempie `meta` con `sha` e `config_sha` dalla stessa lettura (rev-t7).
- `tests/fakegh.py`: `GET pulls/<n>` da `pulls[<n>]`. `tests/test_gate_guard.py`: `test_issue_that_is_a_pr_is_none` diventa `..._is_flagged` (D16).
- `tests/test_gate_github.py`: 44 test.

## Decisioni e scostamenti dal piano
- V4: `test_head_ids_cached_only_on_success` è `test_verdict_never_writes_cache` (verde, rosso ed errore: nessun file nuovo, cache invariata) più `test_no_head_ids_option`.
- D7: `prechecks` riceve `github.shared_sha_prs`; `SharedShaPrsTest` la copre direttamente (due PR stessa testa, impilata, chiusa, altra base, numero ripetuto).
- Fork (decisione 4): `evaluate.Context.is_work`, `issue_no` e `waiver_issue` ora trattano `pr.cross_repo` come ramo non `tg/*` (prima solo `tollgate-config/*`): senza questo un `tg/*` da fork veniva giudicato come lavoro. Modifica minima in `evaluate.py` (non nell'elenco file del brief); i test esistenti di evaluate passano.
- Il commento «non applicabile» usa il prefisso `<!-- tollgate-na sha=... -->`, non il marcatore del verdetto: `task start --from-gate` (`fixtask.GATE_MARKER`) lo leggerebbe come verdetto. Uno solo per PR, aggiornato.
- Errori di calcolo (artefatti, configurazione, SHA diverso da `results.json`, `config_sha` ≠ punta, lettura git/GitHub, base ids assenti): `verdict` e `attention` in `error`, e commento con i motivi (render con `ev.errors`). Errori da controlli preliminari (path, event, SHA condiviso, SHA superato, nessuna PR): solo stati `error` sullo SHA, nessun commento. Descrizione generica per i problemi degli artefatti (portano nomi non fidati).
- Ricontrollo della testa (decisione 14): `GET pulls/<n>` subito prima di commento e stati; se cambiata non si scrive nulla.
- La PR si trova da `workflow_run.pull_requests` o da `commits/<sha>/pulls` (aperte, `head.sha == sha`); ogni candidata è riletta con `GET pulls/<n>`. Le PR verso altri rami ricevono solo il commento.
- Senza `--publish`: stampa le voci (JSON per riga) e `verdict: ...`, esce 1 se non verde, non scrive su GitHub (legge comunque via `gh`).

## TDD
RED (verdict.py spostato fuori dal repo, `python3.11 -B -m unittest tests.test_gate_github`):
```
    from . import baseids, guard, verdict
ImportError: cannot import name 'verdict' from 'tollgate_gate' (/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p4/bin/tollgate_gate/__init__.py)


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```
GREEN: `python3.11 -B -m unittest tests.test_gate_github` → `Ran 44 tests ... OK` (un test sulla sentinella e uno sul ricontrollo sono stati sistemati dopo il primo giro: asserzione sul testo del commento e stdout catturato).
Suite completa: `tests/run` → python3.11 `Ran 2124 tests ... OK`; python3 (3.13.5) `Ran 2124 tests ... OK`, exit 0.

## Autorevisione
Completa rispetto a brief e carry (V4, D7, rev-t7, D14, D16). Nota: l'output di `tests/run` ha una riga di stampa «guard: la PR è avanzata...» che viene da un test esistente di guard (`test_gate_guard`), non da questo task.
## Dubbi
- Per le PR da `commits/<sha>/pulls` e per i job `workflow_run` reali, i campi di `GET pulls/<n>` (`head.repo` nullo per fork cancellato) seguono la REST documentata ma non sono verificati su GitHub qui (V3 vale per l'evento, non per questa risposta).
- Più PR verso rami non predefiniti sulla stessa testa: ognuna riceve il commento «non applicabile».

## Fix round 1
- I-1: `verdict.main` legge lo SHA e avvolge il resto (`_judge`) in un confine su `Exception`. Con `--publish` scrive `error` su `verdict` e `attention` (`DESC_ERROR` + motivo, 140 caratteri), esce 0; 1 solo se lo stato non si scrive; senza `--publish` stampa il motivo su stderr ed esce 1. «Non applicabile» e «SHA superato» restano senza stati. Test: `BoundaryTest` (GhError da `shared_sha_prs`, `pull`, ricontrollo; ValueError da `pr_from_rest`; RuntimeError da `evaluate.evaluate`; stato non scrivibile; senza publish) e, in `CliTest`, `test_read_failure_writes_explicit_error_through_cli` e `test_status_write_failure_is_a_clean_refusal` al posto di `test_gh_failure_is_a_clean_refusal`.
- I-2: `evaluate.pr_issue_number(pr)` è l'unica regola; la usano `Context.issue_no` e `verdict.inputs_from_github`; copia tolta. Test: `IssueRuleTest`.
- Minori: commento «non applicabile» saltato per PR con altra testa e ricontrollato prima di scrivere; `pulls` filtrate per `state == "open"` (se il campo c'è); `_head_is` usa `.get` (niente KeyError, risposta malformata = testa non coincidente); `_base_ids` protegge `stat()` da `OSError` (nessun test: gara non riproducibile in modo stabile); docstring di `tests/fakegh.py` rientrata entro 100 colonne; `test_fork_pr_with_closed_issue_is_red` (passava già: copre il caso). `DESC_ERROR` ora è «errore nel calcolo del gate» e la descrizione degli errori generici è `DESC_ERROR: motivo`.
- RED: prima del codice `python3.11 -B -m unittest tests.test_gate_github` → Ran 57 tests, FAILED (failures=6, errors=14).
- GREEN: stesso comando → Ran 57 tests OK. `tests/run`: python3.11 Ran 2167 OK; python3 (3.13.5) Ran 2167 OK.
