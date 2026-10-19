# Report Task 13: prova reale del flusso con `claude -p`

Stato: DONE_WITH_CONCERNS (esito della prova riuscito dopo una correzione; D2 richiede una scelta di design).

## Commit
- `cfc07ae` tollgate P3a: il piano registrato si può committare tale e quale (correzione D1, con test)
- commit finale `tollgate P3a: prova reale del flusso con claude -p` (script + rapporto); SHA nel messaggio di risposta

## Cosa ho fatto
- `spikes/run-p3a-flow.sh`: prepara repo di prova, repo nudo, stato con sentinella, fakegh (issue 1 aperta, `success`), piano di controllo verificato con `check_plan`; lancia `claude -p` in tre passi con `--continue`; registra stream, `events`, `stats`, `status`, `fakegh.log`, `hooks.log`.
- Rapporto: `docs/verifiche/2026-10-16-p3a-prova-flusso.md` (passi, esiti, veti/token, difetti, limiti).

## Esito per passo (ultima esecuzione)
1. `/tollgate:start #1 L1`: riuscito. `start` esce 0, `EnterWorktree`, `writing-plans` da solo, piano registrato (`scope_registered`) e committato dal coordinatore.
2. Copia del piano di controllo: non eseguito come scritto, il piano esisteva già dal passo 1 (prompt adattato; il piano provato è quello scritto dal modello).
3. `/tollgate:execute`: riuscito. implementer `tg-1-t1`, `review-prepare`, task-reviewer, `task done 1` -> done, verdetto `approved`. Veti 0, token 68589.

## Evidenza TDD della correzione D1
- RED: `python3.11 -B -m unittest tests.test_check_commit.RegisteredPlanCommitTest` -> 2 failure (`test_unchanged_registered_plan_can_be_committed`: 2 != 0; `test_committed_registered_plan_does_not_open_a_block`: blocco `needs_ you` per il piano).
- GREEN: stesso comando dopo `_is_registered_plan` in `bin/tollgate_checks/_common.py` + `tests.test_check_commit tests.test_check_post_bash`: 20 test OK.
- `bash tests/run`: 977 test OK con python3.11 e con python3 (3.13.5), prima del commit di D1 e di nuovo prima del commit finale.

## Difetti e rilievi per il controller
- D1 corretto (sopra). Scoperto perché `locked_docs` blocca il piano dopo la registrazione ma la skill `start` lo fa committare dopo.
- D2 (scelta di design, non fatta): Claude Code 2.1.302 in una sessione isolata nel worktree rifiuta un comando il cui nome è un percorso con spazi tra virgolette; `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` non gira dopo `EnterWorktree` se il plugin ha spazi nel percorso. Ho aggirato nella prova con un link senza spazi. Provato: `python3 "<percorso con spazi>"` è ammesso.
- D4: `uncounted` fa chiudere l'implementatore con `DONE_WITH_CONCERNS`; un cenno in `agents/implementer.md` lo eviterebbe.
- D3, D5, D6: osservazioni minori nel rapporto.
- Limite: `gh api repos/{owner}/{repo}/...` provato solo sul finto.

## Cautele rispettate
Tutto in `/tmp/tollgate-p3a/flow` e nel worktree; `TOLLGATE_STATE` con sentinella; `~/.local/state/tollgate` non esiste (verificato con `stat`); nessun install/enable/disable; nessuna scrittura sotto `~/.claude`; nessun segreto letto; nessun processo fermato per nome. Link `/tmp/tollgate-p3a/tgl` creato nella fase di diagnosi D2 (fuori da `flow`, solo un link, in `/tmp/tollgate-p3a`) e `/tmp/tollgate-p3a/tools/show.py` (lettore dello stream), entrambi senza effetti.

## Dubbi
Un solo run riuscito; il comportamento del modello varia. Un solo task L1: `--fix`, `/clear` e budget non esercitati.

## Giro di correzione 1

- D2: `**Programma:**` in tutte le skill (approve, execute, resolve, setup, start, status) diventa `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con il ripiego `python3.11`; `"<programma>"` -> `<programma>` nei corpi; riga `tollgate: programma python3 "<bin>"` in `bin/tollgate_checks/acts.py`. Setup ricava `<radice>` dallo stesso percorso (testo invariato).
- Test: `tests.test_check_acts.ProgramLineTest` e `tests.test_manifest` aggiornati (rossi con il vecchio testo per costruzione); nuovo `tests.test_check_cli_calls.CliCallsTest.test_python_form_with_double_quoted_spaced_path` (segnale start/act e divieto ai subagenti con `python3 "<percorso con spazi>"`): e' un test di aggancio, passato subito perche' `cli_calls` gia' gestiva la forma python.
- D4: riga su `uncounted` in `agents/implementer.md`.
- D6: nessun difetto. `task start` fa `task_event("start")` e `assign(...)` nella stessa transazione; `_log` emette un `task_change` per ciascuno, e `assign` cambia solo implementer/agent_type/pending (non nel payload). Nessuna modifica.
- Comando: `python3.11 -B -m unittest tests.test_check_cli_calls tests.test_check_acts tests.test_manifest` -> 43 test OK. `bash tests/run`: python3.11 978 test OK, python3 (3.13.5) 978 test OK.

## Giro di correzione 2

- Important: helper `tollgate_core.paths.program_command` (python3 + `shlex.quote`), usato in `taskcmd.py` (brief), `subagent_start.py`, `subagent_stop.py`, `acts.py`. Altre occorrenze trovate con grep: `db.py:35` (`db restore`, testo per l'utente da terminale) e `runner.py:50` (messaggio per l'utente): lasciate. Test RED prima (3 fallimenti: brief, SubagentStart, veto di SubagentStop) e GREEN dopo, con percorso con spazi: `tests.test_taskcmd`, `tests.test_check_agents`, `tests.test_check_subagent_stop`, `tests.test_paths.ProgramCommandTest`, `tests.test_check_acts`.
- Minor 1-2: test di cancellazione e rinomina (passano senza modifiche al codice: aggancio) e del symlink (RED, poi `_is_registered_plan` rifiuta i symlink). Minor 3: `<programma>` = comando intero nelle skill (assert in `test_manifest`). Minor 4: rapporto coerente. Minor 5: `PLUGIN_REAL_PATH=1` nello script.
- Comando mirato: `python3.11 -B -m unittest tests.test_check_commit tests.test_check_acts tests.test_manifest tests.test_paths tests.test_taskcmd tests.test_check_agents tests.test_check_subagent_stop` -> 173 test OK. `bash tests/run` in foreground: python3.11 982 OK, python3 982 OK.
- Prova reale con il percorso con spazi (`PLUGIN_REAL_PATH=1`): passo 1 riuscito, passo 2 non eseguito come scritto (piano già presente), passo 3 riuscito (task 1 `done`, `approved`, implementer `DONE`, ricevuta `verify` registrata, veti 0, token 63762). Dettaglio nel rapporto.
