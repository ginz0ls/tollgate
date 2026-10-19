# Task 2 — Report

## Implementato
- `sessions.py`: `CLI_DIR`, `CLI_WINDOW_S`, `CliSessionError`, `note_cli_call`, `cli_session`. File `cli/<sessione>.json` = dizionario per sottocomando (C8b), merge + tmp + `os.replace`, `OSError` catturato (C8d), sessioni non `_SAFE` ignorate. `cli_session` confronta `Path.resolve()`, finestra stretta (`at > now-120s`), errori «sessione non riconosciuta…» / «più sessioni…».
- `tollgate_checks/cli_calls.py` (pre_bash, ordine 5): trova l'indice del programma (`tollgate x` oppure `python3 <bin> x`, C8c); con `agent_id` nega `start`, `task`, `act`, `status --checkpoint` (`rule="coordinator_only"`); senza `agent_id` registra `cli_call` solo per `start` e `act` (C8a), con `cwd=effective_dir` e `argv` dal sottocomando in poi.
- `apply.py`: operazione `cli_call` (OPS = 23 voci).
- `acts.py`: `decide` aggiunge `tollgate: programma <ctx.plugin_bin>` a ogni `tollgate:*` tranne `off`/`on`; per gli atti (anche rifiutati, C16) la riga è accodata allo stesso inject di «atto ricevuto» / «non registrato». Il corpo vecchio è ora `_act`.
- `bin/tollgate_flow/__init__.py` (solo docstring).
- `tests/fakegh.py` (eseguibile): `auth status`, `issue view N --json`, `issue list`, `pr list [--head]`, `api repos/*/*/commits/<sha>/status`; log in `$TOLLGATE_FAKEGH_LOG`; esce 1 se la risposta manca dai dati o la chiamata non è prevista.
- `tests/flowkit.py`: `FlowLab` compone `hookkit.Lab` (sessione `sess-flow`), `set_gh`, `gh_calls`, `env`, `cli`, `hook`, `git`, `close`; gli altri metodi di Lab (`bash`, `pre_edit`, `goto`, `events`…) via `__getattr__`.
- `tests/hookkit.py`: `Lab` accetta `session`, `issue`, `origin_url` (default invariati; i test esistenti non cambiano).
- `tests/test_analysis_isolation.py`: `tollgate_flow` in `FORBIDDEN` (C19).

## Test
- `test_sessions.CliSessionTest` (found, ambiguous/stale/sub/cartella, 121 s, unsafe, due sottocomandi, stato non scrivibile).
- `test_check_cli_calls` (segnale, act+start, forma python, sottocomandi senza segnale, subagente, cd, stato non scrivibile → 0).
- `test_check_acts.ProgramLineTest`, `test_layers.LayersTest` (esenta solo `tollgate_core/cli.py`, import cercati con `ast` anche nelle funzioni), `test_flowkit` (banco di prova e finto gh).

## Evidenza TDD
- RED: `python3 -B -m unittest tests.test_check_cli_calls tests.test_check_acts tests.test_layers` prima di `cli_calls.py`, dell'operazione, della riga e di `tollgate_flow` → `Ran 28 tests ... FAILED (failures=11, errors=9)` (diniego subagente mancante, `programma` assente, `test_imports`, errori sul segnale).
- I test di `sessions` sono stati scritti dopo il codice (le funzioni erano già presenti): nessun RED registrato per quelli.
- GREEN: stessi test → `Ran 28 tests ... OK`; `tests/test_flowkit` 8 OK.
- `PYTHONS=python3.11 tests/run` → `Ran 719 tests ... OK` (160 s). `PYTHONS=python3 tests/run` (3.13.5) → `Ran 719 tests ... OK` (162 s). Output pulito.

## Scostamenti dal piano
- C8 applicato come da carry (segnale solo per `start`/`act`; dizionario per sottocomando).
- `Lab` parametrizzato (`session`, `issue`, `origin_url`) come previsto da C16.
- `test_flowkit.py` in più (verifica FlowLab e fakegh, non nel brief).

## Dubbi / note per i task successivi
- `git remote get-url origin` ESPANDE `insteadOf`: nel FlowLab restituisce il percorso locale del repo nudo, mentre `git config --get remote.origin.url` restituisce `https://github.com/prova/flow.git`. `prereq.is_github` (Task 3) deve leggere la config, non `get-url`. `cli.current_repo_key` usa `get-url`: nel FlowLab darebbe la chiave del percorso locale, mentre `Lab(origin_url=...)` crea il lavoro con `repo_key(ORIGIN_URL)`. Da risolvere in Task 3 (far leggere la config a `current_repo_key`, o adattare il banco).
- La suite impiega ~160 s per interprete; in background con pipe a `grep` l'output compare solo alla fine.

## Fix round 1
- `tests/hookkit.py`: `Lab` crea il lavoro con `repo_key(git.origin_url(self.main))` (nel ramo `origin_url` e nel default, dove coincide con il percorso dell'origin); tolto il `key_source = origin_url`.
- Nuovo `test_flowkit.test_work_repo_key_matches_origin_url_and_hook_finds_it`: `work_items.repo_key == repo_key(git.origin_url(fl.main))` e `orphan_tg` sul worktree restituisce `None` (lavoro trovato, non orfano); `bash` dal worktree esce 0.
- Nuovo `test_check_acts.ProgramLineTest.test_off_and_on_get_no_program_line`.
- Non toccati `is_github`, `current_repo_key`, `git.origin_url`.
- Test: `PYTHONS=python3.11 tests/run` e `PYTHONS=python3 tests/run` → `Ran 721 tests ... OK` (entrambi).
