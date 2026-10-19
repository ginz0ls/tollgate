# Report Task 14

Commit `1d8906f`: «tollgate P3a: prove dei criteri, spec rev 22, piano principale».

## Cosa è stato fatto
- `tests/test_criteria_p3a.py` (nuovo, 2 test dal programma vero):
  - `StartFromWrapperTest.test_start_from_wrapper_flow` (criterio 1): `PreToolUse Bash` di `python3 <bin> start 7 --level L1` attraverso `hooks/run`, verifica del segnale con `sessions.cli_session`, poi `bin/tollgate start` → 0, riga con fase `plan` e sessione legata, worktree esistente, ultima riga `prossimo passo: EnterWorktree`.
  - `TaskCycleEndToEndTest.test_task_cycle_end_to_end` (criteri 4 e 38): piano registrato da `PostToolUse Write` → `execution`; `task start 1`; `PreToolUse Agent` col nome del brief; `SubagentStart`; commit visto da `PostToolUse Bash`; `verify`; `SubagentStop` col report → `review`; `review-prepare`; `SubagentStop` del revisore col verdetto → `approved`; `task done` → `done`.
- Spec rev 22: intestazione, 0 (sessione viva, checkpoint non committato), 3 (strati con eccezione di `cli.py`, manifest V4), 3.1 (segnale per sottocomando, `start` con `--confirm` e `--reopen-execution` e codici 0/1/3/4, `act apply [<id>]`, comandi negati ai subagenti, `python3 "<bin>"`, riga «programma»), 5 (tetto), 6.1 (passi, codici, percorso del worktree, `exclude`, `--no-track`, stati obbligatori), 6.2 (piano registrato committabile), 6.3 (precondizioni, task senza commit, instradamento, skill assenti, giri, prenotazione non atomica, `task_verdict`, checkpoint), 8.4 (`act apply`, riga «programma»), 8.6 (verdetto effettivo, validità, veto per soli rilievi bloccanti scartati, `dropped`, [blocca] rinviato a P3b), 11.1 (intervallo, formato del registro), 11.3 (involucro con `sh -c`), 12.2 (migrazione 3), 12.3 (`--reopen-execution`), 16 (V1-V5, prova reale, nessuna voce aperta), riga 22 nella 20.
- Piano principale: Stato (P3a chiuso sul ramo, merge in attesa dell'OK dell'utente, 984 test), sezione 3 (moduli reali di `tollgate_flow`, regola degli strati, contratti P3a verso P3b/P3c/P4: `start`, `taskcmd`, `APPLIERS`, `checkpoint.CAPS`, `prereq.GATE_FILES`, `.github/tollgate/VERSION`, `apply.OPS` a 25, `program_command`, vincoli per P3b e P3c), sezione 4 con la tabella «Prove dei criteri di P3a» (criteri 1, 4, 18, 22, 28, 38, 39, 40).
- Verificato con uno script che tutti i 44 riferimenti `file::Classe.metodo` della tabella esistono (classe e metodo).

## TDD
I due test nuovi non hanno avuto un RED di prodotto: provano codice già esistente. Gli unici fallimenti iniziali erano errori del test (firma di `cli_session` con `now=` keyword; `start` senza `--level L1` va in `execution`, non `plan`), corretti prima del commit.

## Test
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 984 test, OK (la prima corsa aveva dato 1 fallimento, vedi sotto).
- `tests/run`: Python 3.11.16 984 OK; Python 3.13.5 984 OK.

## Anomalia da riportare
`tests.test_wrapper.WrapperTest.test_watchdog_is_capped_at_85` è fragile sotto carico: attende 0,5 s fissi e poi cerca con `pgrep` il processo `sleep 87`. Con il load average a ~20 (altri agenti in parallelo) ha fallito in modo ripetuto, anche da solo, con 3.11 e una volta con python3. Passa con la macchina scarica. Non è toccato da questo task (codice di P2); consiglio un'attesa a polling al posto di `time.sleep(0.5)` (come `wait_gone`) in un giro successivo.

## Scostamenti
Nessuno rispetto al brief. Nella rev 22 la distinzione [blocca] resta rinviata a P3b, come da C14.

## Dubbi
Nessuno di sostanza. La riga «Resta a» per il criterio 18 dice «le chiavi con il modulo in P3b e P3c»: è una lettura mia delle chiavi di P3b/P3c, da confermare.

## Giro di correzione 1

Commit: «tollgate P3a: fix round 1 del Task 14 (watchdog a polling, riga 18, programma nel footer del runner, GATE_FILES)».

- **Important 1.** `tests/test_wrapper.py`: nuovo helper `wait_alive` (polling 50 ms, scadenza 10 s) al posto di `time.sleep(0.5)` in `test_watchdog_is_capped_at_85`; il test verifica ancora `sleep 87` vivo e `sleep 902` assente. Wrapper intatto. Il test da solo, 5 volte di fila con python3.11: 5 OK (anche con carico alto sulla macchina).
- **Minor 1.** Riga 18 della matrice: elencate le chiavi rimaste (`final_review`, `definition_of_done` P3b/P4; `spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch` P3c; `base_test_ids`, `sentinel` P4), nomi verificati in `config.py` (`DEFAULTS["components"]`).
- **Minor 2.** Commento di `test_task_cycle_end_to_end`: «criterio 4 (ramo generico, senza profili verticali)».
- **Minor 3 (TDD).** RED: `test_hook_engine.FooterTest.test_footer_names_the_program_as_the_model_runs_it` fallisce (footer con il percorso nudo). GREEN: `runner._footer` usa `paths.program_command(db.BIN_PATH)`. Resta `db.restore_command` (`db.py:35`) con il percorso nudo: è il comando da terminale dell'utente, non del modello.
- **Minor 4.** Sezione 3 del piano: `prereq.GATE_FILES` (sei voci: cinque workflow più `.github/tollgate/VERSION`). Stato: 985 test.
- **Suite.** `bash tests/run`: 3.11.16 985 OK, 3.13.5 985 OK; `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 985 OK. Nota: a fine corsa compare «Exception ignored … unclosed database» (già presente prima del Task 14, all'uscita dell'interprete, non fa fallire nulla; non indagato).
