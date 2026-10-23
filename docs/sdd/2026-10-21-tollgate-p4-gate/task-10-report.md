# Task 10 — report

Commit: aad7df7 «tollgate P4: sentinel, tollgate/base in detect, issue di sentinel paginate».

## Implementato
- `bin/tollgate_gate/sentinel.py` (nuovo): `unverified(repo, *, before, after, prs_for_commit, statuses, default_branch=None, attempts=3, wait=5.0, sleep=time.sleep)` e `run(event_path, *, publish, environ, repo=None, sleep, attempts, wait)`.
  - Commit nuovi: `git rev-list before..after`; `before` tutto zeri → solo `after`; `before` non più presente (push forzato) → solo `after`, con nota su stderr.
  - Prima installazione: si ignorano i commit che introducono `tollgate-sentinel.yml` (presente nel commit, assente nel primo genitore) e i loro antenati nel push (`merge-base --is-ancestor`).
  - Per commit: `commits/<sha>/pulls`, tenendo le PR con `merged_at` e `base.ref == predefinito`; elenco vuoto riletto fino a 3 volte con attesa iniettabile (V5). Verificato se almeno una PR unita ha, sulla testa, `tollgate/guard` e `tollgate/verdict` con **l'ultimo** stato `success` e `creator.login` in `BOT_LOGINS`.
  - `publish`: un solo commento/issue con SHA e motivi (nessun titolo o corpo di PR), poi `tollgate/sentinel` `failure` su ogni commit rosso; ritorna 0. Senza `publish` stampa una stringa JSON per riga e ritorna 1. `components.sentinel = false` esce subito; push su altro ramo o cancellazione del ramo: niente da fare. Configurazione letta da `after` (punta del predefinito).
- `github.py`: `push_from_event`, `report_sentinel` (unica issue: commenta la più vecchia, se no la crea).
- `baseids.publish(repo, *, config_sha, sha, result, environ)`: in `detect` pubblica `tollgate/base` (`success`, o `failure` se un comando è `red`, e in quel caso commenta/crea l'issue di sentinel); in `protected` non scrive nulla. `gate base-ids --publish` lo chiama.
- `cli.py`: sottocomando `sentinel --event --publish` (eredita `allow_abbrev=False`, rifiuto fuori da Actions, D21c).
- `tollgate_flow/gh.py`: `sentinel_issues` ora chiama `github.open_sentinel_issues(state, repo, "{owner}/{repo}")` (`gh` risolve i segnaposto), paginato. Gli strati permettono a `tollgate_flow` di importare `tollgate_gate`: nessuna regola condivisa in `ghcli` necessaria.
- Test: `tests/test_gate_sentinel.py` (29 test, inclusi i dieci del brief; il cross-command usa `VerdictBase` di `test_gate_github`, quindi `gate evaluate` vero più `github.set_status` per il guard), `tests/test_gh.py::SentinelIssuesTest::test_sentinel_issues_paginated`, `tests/test_start.py::test_detect_mode_warning` riscritto per `open_issues` (D12).
- `tests/fakegh.py`: i commenti arrivano anche alle `open_issues`; `POST issues` salva `body`; la lista `issues?state=open` scarta le righe con `pull_request` (come il jq reale).

## TDD
RED (prima del codice): `python3 -B -m unittest tests.test_gate_sentinel` → `ImportError: cannot import name 'sentinel'` (1 errore di caricamento); `tests.test_gh.SentinelIssuesTest` e `tests.test_start.test_detect_mode_warning` → FAIL/ERROR (`issue_list assente dai dati`, titolo di sentinel non trovato).
GREEN: `tests.test_gate_sentinel` 29 test OK; `tests/run`: python3.11 2154 test OK, python3 (3.13.5) 2154 test OK, exit 0.

## Scelte e scostamenti
- `unverified` ha un parametro in più, `default_branch` (opzionale, di norma da `git.default_branch`), perché serve a filtrare `base.ref` e la firma del brief non lo porta.
- «Basta una PR unita e verificata»: se un commit è in più PR unite, una sola verde lo rende verificato.
- `tollgate/base` in `detect`: rosso solo con comandi `red` (gli `unverified`, comandi vuoti, non lo rendono rosso).
- Push forzato con `before` assente: si controlla solo `after` (l'intervallo non è calcolabile). Da valutare in revisione se serve un altro comportamento.
- Nessuno stato `success` per `tollgate/sentinel` sui commit verificati (il brief parla solo del rosso).
- `gate sentinel` richiede `GITHUB_REPOSITORY` anche senza `--publish` (legge da GitHub).

## Dubbi
Nessuno bloccante. L'output di `tests/run` contiene una riga `guard: la PR è avanzata…` stampata da un test preesistente, non da questo task.

## Fix round 1
- I-1: `_commits` ritorna `(commit, forzato)`. `before` non zeri e non risolvibile, o non antenato di `after`: `after` è non verificato con «push forzato: intervallo non calcolabile» (unito al motivo per PR se c'è), in aggiunta ai controlli di `before..after` quando calcolabile. Test: `test_unknown_before_is_forced_push` (riscritto), `test_rewritten_history_is_forced_push`, `test_rewind_is_forced_push`, `test_forced_push_adds_to_the_range_checks`, `test_fast_forward_is_not_forced`.
- I-2: `ghcli.STATUS_BOT = "github-actions[bot]"`, usata in `sentinel._pr_problem`; `BOT_LOGINS` resta per i commenti. Nessun altro punto giudica `creator.login` di stati (grep). Test: `test_bot_login_without_suffix_not_trusted_for_statuses`.
- Minori: stati prima dell'issue (sentinel e `baseids.publish`, test d'ordine sul log); i comandi `unverified` nella descrizione di `tollgate/base` (≤140); `GITHUB_REPOSITORY` solo con `--publish` (senza, repository dall'evento; test).
- Non fatti, non richiesti: attese per commit (rilievo 4), nome del test paginato (5).
- RED: 9 test falliti/in errore prima del codice. GREEN: `tests/run` python3.11 e python3 (3.13.5), 2176 test OK, exit 0.
