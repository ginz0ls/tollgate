# Task 7 report: approve spec, approve plan, sospensioni dei tetti

## Implementato
- `bin/tollgate_flow/l2acts.py` (nuovo): `Refused`, `approve_spec` (decisione 9, D2, D16), `approve_plan` (decisione 10, D3), `suspend_on_resolve(conn, work, block_reason, *, now, cfg=None)` (D6).
- `actapply.py`: voci `("approve","spec")` e `("approve","plan")`; `_resolve` chiama `suspend_on_resolve` prima di `close_block` (solo se `audits.cap_kind(reason)` non è `None`, con la config del lavoro) e aggiunge l'etichetta al messaggio; `Refused` convertito in `ActApplyError`; testo di `_pick` con spec, plan e reopen.
- `violations.locked_docs`: spec bloccata se `approvals.locate_spec_approval(..., spec_blob=None)` trova un'approvazione sui `spec-approval.md` del disco del worktree (anche di altre issue); letto da `_approval_files`, una volta per chiamata di `diff_violations` (già calcolava `locked` una volta).
- `audit.py`: resi pubblici `passed`, `clean`, `last_round` (erano `_passed`, `_clean`, `_last`), perché `l2acts` non duplichi la regola «giro passato».
- `tests/flowkit.py`: `FlowLab` aggiunge `start.EXCLUDES` all'`info/exclude` alla creazione; `RoundCase.lab` rimosso da `tests/test_check_audit_round.py`.

## Test
- `tests/test_l2acts.py` (36): `ApproveSpecTest`, `ApprovePlanTest`, `SuspendOnResolveTest`, `PickMessageTest`; tutti i test del brief più: spec in recinto con titoli ostili, fase sbagliata, tre fette con lenti sospese, piano rovinato dopo l'approvazione, giro aperto/sporco in approval, soglia del piano da config, sospensione idempotente, blocchi a mano senza giri e sotto il tetto.
- Review Focus 3, 4 e 6 attraversano i comandi: atto digitato con l'hook `UserPromptExpansion`, applicato con `actapply` e `now=fl.now`, `audit prepare` e `audit decline` dalla CLI (`fl.cli`), commit del coordinatore da `PreToolUse Bash`, report degli agenti da `SubagentStop`.
- `tests/test_check_common.py`: fixture riscritta con `render_approval` (D10); nuovi `test_spec_locked_by_real_approve_spec`, `..._by_approval_of_another_issue`, `..._not_locked_by_invalid_or_foreign_approval`.
- `tests/run`: python3.11 1624 test OK in 469 s, python3 (3.13.5) 1624 test OK in 614 s, output pulito.

## TDD
Scritto prima il modulo e poi i test (scostamento dal TDD stretto): il RED non è stato registrato. I test sono stati poi guidati dai fallimenti reali (messaggi, `NEEDS_CONFIRM` con adversary spento a tre fette, config senza `gate.mode`, `isclean` rotto da un rename).

## Scostamenti e note
- `suspend_on_resolve` ha un parametro opzionale `cfg` oltre la firma del brief: i tetti (`spec_rounds`, `plan_rounds`, `spec_audit_cycles`) stanno nella config; senza `cfg` valgono i predefiniti (`config.DEFAULTS`).
- Per il tetto dell'audit a lenti il numero scritto è quello dell'ultimo ciclo chiuso (0 solo per il rifiuto del costo).
- Messaggio di `approve spec` con fette > 1: righe `fetta k/n di <file>: <titolo>` e comando `/tollgate:start #<numero> --spec "<percorso>"` in un solo recinto sotto `DATA_NOTE`; nessuna chiamata a `gh`.
- `approve spec`/`approve plan` senza target numerico non si registrano come atti dall'hook (l'hook di P2 li scarta): il rifiuto con «N fette» scatta solo con un numero sbagliato.

## Dubbi
Nessuno bloccante. `l2acts` dipende da `audit` (stesso strato), non da `actapply`.

## Fix round 1
Modifiche:
1. Duplicazioni tolte: in `audit.py` pubblici `comp`, `on`, `work_base`, `work_config` (unico punto di caricamento della config per `audit`, `l2acts`, `actapply`; `ConfigError` se manca worktree o base), `Uncommitted` e `committed_blob(wt, path)` (i chiamanti scelgono il messaggio), `plan_check(cfg, text)` (usato da `audit prepare` e da `approve plan`). `l2acts._on`, `_cfg` copiata, `_committed` copiata e la chiamata a `check_plan` sono sparite; `actapply._config` e `l2acts._cfg` convertono solo l'errore.
2. `_spec_approved` passa il blob attuale a `locate_spec_approval`; se non trova nulla con quello sha ma esiste un'approvazione per quel percorso rifiuta «spec cambiata dopo approve spec».
3. `_resolve` senza worktree usa i tetti predefiniti invece di `TypeError`.
4-5. Test: messaggio completo in `test_wrong_slice_count_refused`; `approve spec` e `approve plan` in `blocked` (indicano `/tollgate:resolve <id>`); spec non committata; due approvazioni di altre issue con la più bassa stantia; resolve senza worktree.
RED (`python3.11 -B -m unittest tests.test_l2acts`, prima del codice): 2 errori, `test_later_slice_approval_with_current_sha_wins_over_stale_lower_issue` (Refused «spec cambiata dopo approve spec») e `test_resolve_without_worktree_falls_back_to_default_caps` (TypeError); gli altri nuovi test erano già verdi (comportamento già giusto, ora coperto).
GREEN: stesso comando, 41 test OK; mirati con test_actapply, test_audit_prepare, test_check_audit_round: 179 OK.
Suite: `tests/run`, 1629 test OK su python3.11 (617 s) e python3 3.13 (616 s).
