# Report Task 6: `finish check`

## Implementato
- `bin/tollgate_analysis/mustcheck.py`: `MustHaveResult(ok, missing, failed, manual)` e `check(must_haves, ids_run, ids_failed)`. `missing`/`failed` hanno voci `Mn: <id>`; `manual` ha gli id dei must-have con `— test: manuale` (non rendono falso il risultato).
- `bin/tollgate_analysis/approvals.py`: `parse_approval` (intestazione `---`, `chiave: valore`, virgolette o nudi, `null`, interi nudi; `None` se manca/non chiude/riga malformata/`kind` non di approvazione/manca `path` o `sha`) e `approval_paths(issue)`.
- `bin/tollgate_flow/finishcheck.py`: `CheckResult`, `OK/RED/REFUSED`, `check(state, cwd, *, now, environ)`. Ordine: lavoro -> fase (execution/review) -> idempotenza (review sullo stesso SHA con report: esito salvato, nessun gate, nessun evento) -> `gitw.fetch` (avviso) -> task non `done`/`approved` (rifiuto con i numeri, solo L1/L2) -> `run_gate(produced_by="finish", extra=dod_commands)` (`sha is None` = rifiuto, C17) -> `diff_violations` -> must-have dal JUnit del gate -> approvals (L2) -> `compute_dod(skip=("findings","specialists"), external, profile_items, allow_unverified)`. Verde: `set_finish` + `set_phase(review, finish_check_green)` solo se la fase è `execution` (C13) + evento; rosso: solo evento `ok: false`.
- `finish_report` = `{"items": {chiave: bool|null}, "manual": [...]}` con tutte le voci del livello (comprese guard_scope, must_have, approvals) e le voci di profilo (C6). `external` è un dizionario con le sole chiavi applicabili al livello (C14).
- Voce di profilo per un `dod` senza comando in `[commands]`: riga `[no] Voce del profilo p:lint: il comando «lint» non è in [commands]: ...`.
- `cli.py`: sottocomando `finish check`; `except` finale in `main` per `gh.GhError`, `git.GitError`, `gitw.GitWriteError` (import in `_external_errors()`, a richiesta): messaggio e uscita 1; qualsiasi altra eccezione si propaga (C24).
- Ultima riga: `prossimo passo: <program_command> review prepare` (L1/L2), `... finish open-pr` (L0), o `correggi le voci [no] e rilancia ...` se rosso. Comandi via `program_command(db.BIN_PATH)`.

## TDD
RED (moduli rimossi di nascosto): `python3 -B -m unittest tests.test_mustcheck tests.test_approvals` -> `ImportError: cannot import name 'approvals' from 'tollgate_analysis'`; `tests.test_finishcheck` -> `ImportError: cannot import name 'finishcheck' from 'tollgate_flow'`.
GREEN: `python3 -B -m unittest tests.test_mustcheck tests.test_approvals tests.test_finishcheck` -> 7 + 6 + 22 test OK.
Suite: `tests/run` -> python3.11 e python3 (3.13.5): `Ran 1146 tests ... OK` entrambi. Nessun `__pycache__`.

Test (tests/test_finishcheck.py, 22): i otto del brief, più rerun in review su altro SHA (C13: nessun nuovo `phase_change`, due eventi `finish_check`), rosso in review su altro SHA (fase invariata), worktree sporco (C17), fase sbagliata, nessun lavoro, avviso di fetch, L2 con approvals (assenti, sha piano sbagliato, corretti), must-have manuale nel report, `dod` di profilo senza comando (rosso, nome e `[commands]` nella riga) e con `approve unverified-tests` (verde), sottocomando CLI (uscita 0/1), errori esterni -> uscita 1 con messaggio (subTest per tre eccezioni), errore sconosciuto che si propaga.

## Scostamenti e decisioni mie (da rivedere)
1. **Scope in L2**: `diff_violations` (Task 4) segnala `out_of_scope` per spec, piano e file sotto `docs/superpowers/reviews/<N>/` (approvazioni), perché `scope_exempt` non li esenta e nel diff dalla base ci sono sempre. Senza correzione ogni `finish check` L2 sarebbe rosso. Ho filtrato in `finishcheck._own_document` solo quei percorsi e solo per `out_of_scope`, senza toccare `violations.py` (condiviso con gli hook). Se si preferisce, la regola va in `scope_exempt`.
2. `must_have_tests` spento in `[components]` -> voce `must_have` vera con dettaglio «componente spento». `definition_of_done` spento NON è gestito in `finish check` (verde = `dod_passes`); la regola «stampa e non ferma» di decisione 10 è di `open-pr` (Task 9).
3. `approvals` L2 controlla solo kind e `sha` = blob in HEAD (come da brief); non confronta `spec_sha` del piano.
4. `reviews.latest` non serve (findings/specialists saltati). `taskcmd._plan_text` riusato (nome privato) per leggere il piano a `plan_sha`.
5. Nel banco il JUnit finto legge `tests/ids.txt`: i test usano `[scope] always = ["tests/ids.txt"]` per non farlo contare fuori scope.
6. `prstate.detect` non agganciato (Task 9).

## File
bin/tollgate_analysis/mustcheck.py, bin/tollgate_analysis/approvals.py, bin/tollgate_flow/finishcheck.py, bin/tollgate_core/cli.py, tests/test_mustcheck.py, tests/test_approvals.py, tests/test_finishcheck.py.

## Fix round 1 (ruling «Scope in L2»)
Cambiato `finishcheck._own_document(wt, work, v)`: il piano non è più esente (lo resta solo come blob registrato, dentro `diff_violations`); la spec è esente solo se il suo blob in HEAD è uguale allo `sha` di `spec-approval.md` in HEAD (`parse_approval`, kind `spec-approval`); i file sotto `docs/superpowers/reviews/<N>/` restano esenti. `violations.py` non toccato.

Test aggiunti in `LevelsTest` (con helper `l2_lab`/`approve`): `test_l2_approved_spec_and_reviews_files_exempt`, `test_l2_modified_plan_after_registration_is_out_of_scope`, `test_l2_spec_changed_after_approval_is_out_of_scope`.
RED (prima della correzione): `python3 -B -m unittest tests.test_finishcheck` -> `Ran 26 tests ... FAILED (failures=3)`; fallivano i due test di piano modificato e spec cambiata (più un quarto test mio, vedi sotto); l'esente passava già.
GREEN: `tests/run` -> python3.11 e python3 (3.13.5): `Ran 1149 tests ... OK` entrambi.

Nota: senza `spec-approval.md` in worktree la spec NON è «bloccata» per `locked_docs`, quindi `scope_exempt` (Task 4) la esenta già come `.md` di docs: non resta `out_of_scope` e non posso cambiarlo senza toccare `violations.py`. In quel caso la voce `approvals` è comunque falsa (file mancante), quindi il finish resta rosso. Il test che avevo provato per questo caso l'ho tolto perché asseriva il contrario del comportamento di `violations.py`.
