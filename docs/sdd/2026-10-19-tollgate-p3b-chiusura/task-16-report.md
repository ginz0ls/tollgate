# Task 16 - report

Implementati: `agents/final-reviewer.md` (inherit, attribuzione requesting-code-review), `agents/finding-verifier.md` (sonnet); skill nuove `finish`, `sync`, `adopt`, `abandon`, `cleanup`; aggiornate `approve`, `execute`, `start`, `resolve`; sei test nuovi più `test_updated_skills_describe_closing` in `tests/test_manifest.py`. Testi derivati dal codice reale (finishcheck, finalreview, sync, adopt, closing, actapply, openpr, prstate).

## TDD
RED: `python3 -B -m unittest tests.test_manifest` prima dei file: 5 errori `FileNotFoundError` (skills/finish/SKILL.md, agenti) e 1 FAIL `test_skills_use_program_command_form` (8 skill invece di >= 13). 
GREEN: `python3 -B -m unittest tests.test_manifest` -> Ran 24 tests OK.
Suite: `tests/run` -> python3.11 e python3 (3.13.5): Ran 1390 tests, OK entrambi.
`claude plugin validate --strict .` -> "Validation passed".

## Scostamenti / note
- `test_skills_use_program_command_form` controlla solo le skill (non gli agenti): `agents/implementer.md` (P3a) cita `python3 '<percorso>/bin/tollgate'` con apici singoli; non toccato.
- C9 e C22 applicati (finish: codici 1/2/altri; `"v": 1` nei JSON degli agenti).
- Il tetto cicli di `review prepare` esce con codice 1 e messaggio su stderr: la skill lo indica.
- Nessun `__pycache__`.

## Fix round 1
Cambiato (ogni frase verificata su sync.py, start.py, openpr.py, finishcheck.py, reviews.py, actapply.py):
- Important 1: `finish` passo 1 controlla `git status`; se sporco committa i file del coordinatore, dice di ridigitare `/tollgate:finish` e si ferma. `test_finish_skill_keeps_worktree_clean` asserisce la richiesta e che precede `finish check`.
- Important 2: tetto assoluto 8 cicli -> solo `approve unverified-review`; `approve rounds`/`resolve` per il blocco «cicli di revisione esauriti» (4 contati, totale 8).
- Important 3: `sync` codice 2 distingue conflitto nel rebase (`approve rebase` o abandon) da rami divergenti (integra a mano + `resolve <id>` o abandon).
- Minor 4: `needs_fix` con blocco cicli aperto (fase blocked) -> niente `task start`, vai a `resolve`/`approve rounds`. 5: `start` PR chiusa sotto il codice 3 con `--confirm` o `abandon`. 6: «il controllo». 7: `final-reviewer` usa `git show <sha>:<path>`/`git archive`, niente worktree add. 8: `adopt` in `pr_open` rimanda a `/tollgate:sync`. 9: `--update` facoltativo; `pr_open` richiede il ritorno in `execution` (sync / `start --reopen-execution`). Minor 10 invariato.
Test: `python3 -B -m unittest tests.test_manifest` OK (24); `tests/run`: 1390 OK su python3.11 e python3 3.13.5; `claude plugin validate --strict .`: Validation passed.
