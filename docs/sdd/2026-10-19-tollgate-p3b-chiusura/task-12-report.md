# Task 12: `adopt` — report

## Implementato
- `bin/tollgate_flow/adopt.py`: `AdoptResult(code, lines, worktree, work)` e `adopt(state, cwd, issue, *, now=None, argv=None)`. Codici: 0 fatto, 1 rifiuto, 4 lavoro creato ma registrazione incompleta (come `start`). Ultima riga `prossimo passo: EnterWorktree <percorso>`.
- Flusso: fetch (non obbligatorio), predefinito e `tollgate.toml`, sessione dal segnale (`cli_session(..., "adopt", argv=)`), atto `adopt` con `target=str(N)` e `work=None` (rifiuto senza atto), nessun lavoro attivo per (repo, N), candidato unico tra `tg/<N>-*` locali e su origin (più rami: rifiuto con l'elenco), PR del ramo (`gh.pr_for_branch`): unita -> rifiuto; chiusa senza merge -> avviso C25 «PR #n chiusa senza merge: ignorata, finish open-pr ne aprirà una nuova», nessun `pr_number` e nessun tetto; aperta -> `pr_open`, `set_pr`, tetto da `prblock.parse` del corpo.
- Worktree: se il ramo è già in un worktree si riusa (rifiuto se è il checkout principale o se il percorso registrato manca: «git worktree prune»); altrimenti ramo locale da origin con `gitw.create_branch` (atomico, nessun upstream) e `gitw.worktree_add` senza `force`; se l'add fallisce il ramo creato si toglie con `delete_branch`.
- Base = `merge-base(origin/<predefinito>, ramo)`. Livello = `diff_level` sul diff base..ramo (senza `output_dirs`) + `min_level` dei profili + `labels_level` dell'issue (etichette non lette: avviso, solo diff).
- Fase: PR aperta `pr_open`; L0 `execution`; L1 senza piano `plan`, con piano `execution`; L2 senza `spec-approval.md` `spec_audit`, senza piano valido `plan`, senza `plan-approval.md` `approval`, con entrambi `execution`. Il piano è il primo file nuovo (`A`) sotto `docs/superpowers/plans/` che passa `check_plan`. `create_work(..., phase=, cause="adopt")` senza `from_approved_spec`; `spec_path` dal `path` di `spec-approval.md` (solo se relativo e senza `..`).
- Piano: L1 (o L2 con `plan-approval.md`, livello letto dopo l'eventuale tetto) -> `scope.register_plan(advance=False)` con scope e task `pending`; L2 senza approvazione -> solo `set_plan_path` (come l'hook).
- Tetto: `phases.set_level_cap` con `cap_paths` ricalcolati come `actapply._approve_level` (`sensitive_in` sul diff base..worktree); valori del blocco validati (livello noto, `issue` uguale), altrimenti avviso e nessun tetto.
- Deroghe: nessuna approvata (restano `pending` da `waivers.status`); una riga riporta il numero di deroghe nel file del ramo.
- Poi: atto consumato, copia di sicurezza, radici attive, segnalino, `info/exclude`, `.tollgate-run/<N>/issue.md` (riuso di `start._write_issue`, testo dell'issue mai in un argomento).
- `bin/tollgate_core/cli.py`: sottocomando `adopt N` (`_hook_argv`).
- `bin/tollgate_flow/gh.py`: nuova `pr_body` (`pr view --json body`), perché `pr_for_branch` non porta il corpo. Test in `tests/test_gh.py::test_pr_body`.

## Scostamenti dal piano
- `gh.pr_body` e il test in `test_gh.py` non erano nel brief: servono per leggere il blocco JSON (il campo `body` non è in `pr list`).
- Lettura della PR con `gh` in errore: rifiuto (fail-closed), perché senza saperlo una PR già unita verrebbe adottata. Il piano non lo diceva.
- L2 senza piano valido -> fase `plan` (il brief dice solo «senza plan-approval -> approval»): senza piano non c'è nulla da approvare.
- La PR chiusa senza merge è ignorata del tutto, anche il suo blocco JSON (lettura di C25).

## Test (tests/test_adopt.py, 22 test; più 1 in test_gh.py)
Brief: `test_hooks_deny_on_orphan_branch_then_adopt`, `test_start_refusal_then_adopt`, `test_l2_with_plan_approval_stays_execution`, `test_l2_without_plan_approval_goes_approval`, `test_approved_waivers_back_pending`, `test_l1_without_plan_goes_plan`, `test_l1_with_plan_registers_scope_and_pending_tasks`, `test_open_pr_gives_pr_open_and_cap_from_block` (cap_paths e scope dopo il tetto), `test_branch_in_existing_worktree_reused`, `test_remote_only_branch`, `test_refused_with_active_work_or_merged_pr_or_two_branches` (subTest per i tre casi, atto ancora `pending`).
In più: senza atto, atto di un'altra issue, nessun ramo, senza segnale della sessione, PR non leggibile, PR chiusa ignorata (C25), blocco con tetto non valido/altra issue, PR senza blocco, ramo locale senza worktree, ramo nel checkout principale, worktree registrato ma mancante (nessun `--force`), L2 senza `spec-approval`.

## TDD
RED: `python3 -B -m unittest tests.test_adopt` -> `Ran 22 tests ... FAILED (failures=24)` (24 con i subTest), tutti con `tollgate: error: argument cmd: invalid choice: 'adopt'`.
GREEN: `python3 -B -m unittest tests.test_gh tests.test_adopt` -> `Ran 34 tests ... OK`.
Suite: `tests/run` -> python3.11.16 `Ran 1343 tests ... OK`; python3.13.5 `Ran 1343 tests ... OK`. `git status`: nessun `__pycache__`.

## Dubbi
- `adopt.py` usa `start._write_issue` e `start.EXCLUDES` (nome con underscore): evita una copia, ma è un accoppiamento tra moduli del flusso.
- Il livello viene ricalcolato: un lavoro avviato con `--level L2` e diff piccolo torna L0/L1 (decisione 18 non usa il campo `level` del blocco).
- Un ramo di un lavoro `closed` (non unito) si adotta come nuovo lavoro: non c'è un controllo sul passato, coerente con la decisione 18.

## Fix round 1
- Important 1: `approvals.is_current(header, blob_sha)` (pura, in `tollgate_analysis/approvals.py`) è ora il confronto usato sia da `finishcheck._approvals` sia da `adopt`. In `adopt._approval` un file di approvazione è prova solo se `kind` coincide, `path` è relativo, il documento esiste nel ramo e il suo blob è `sha`; `plan-approval` vale solo se `path` è il piano scelto da `_find_plan`, e se ha `spec_sha` questo è il blob della spec. Senza spec valida anche il piano non è approvato (fase `spec_audit`, nessuno scope). Altrimenti si scende: spec non valida `spec_audit`, piano non approvato o approvazione superata `approval`, senza piano `plan`.
- Minor 2: le righe «PR aperta» e «tetto ripristinato» escono solo se il passo è riuscito (`step` ritorna `FAILED`).
- Test: `test_l2_with_plan_approval_stays_execution` usa gli sha veri (e `spec_sha`); nuovo `test_l2_superseded_or_mismatched_approvals_go_back` (subTest: piano modificato, `path` diverso, `spec_sha` diverso, spec modificata, spec assente); nuovo `test_pr_and_cap_lines_only_when_step_succeeded`.
- RED (adopt.py di d04bf07 rimesso temporaneamente): `python3 -B -m unittest tests.test_adopt` -> `Ran 25 tests ... FAILED (failures=6)` (i 5 subTest e il test delle righe).
- GREEN: `tests.test_adopt tests.test_finishcheck tests.test_approvals` -> `Ran 56 tests ... OK`; `tests/run`: python3.11.16 `Ran 1345 tests ... OK`, python3.13.5 `Ran 1345 tests ... OK`.
