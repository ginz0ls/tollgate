# Task 7 - report

Commit: vedi `git log -1` (tollgate B1: avviso e rifiuto alla prima modifica senza nota).

## Fatto
- `bin/tollgate_checks/research_gate.py` (nuovo): CHECK eventi pre_edit, pre_bash, post_edit, post_bash, componente `research_note`, order 25. L0 (sessione principale, solo Edit/Write): un avviso per lavoro. L1/L2 (implementatore del task via `lookups.owner`): nessuna decisione con `research_ok`; altrimenti `deny` con interruttore acceso (`research.enforced` sul testo di `ctx.plugin_root / RULES_BASE`, assente = spento), `inject` una volta per task con interruttore spento.
- D3: l'avviso e' un `inject` in pre_*; il `research_reminder` (op `event`) si registra in post_* solo se l'hook non e' `PostToolUseFailure`.
- D11: helper `work_events(ctx, work, type_)` in `_common.py` (eventi dopo l'ultimo `plan_reset`, sola lettura, filtro Python su `data`); usato dal conteggio degli avvisi e dai problemi della consegna precedente.
- D12: `_abs`, `_braces`, `_expand`, `_write_paths` (e `_SUBST`, `_GLOB_*`) spostati da `bash_rules.py` a `_common.py` senza cambiare il corpo. `bash_rules` importa `_braces` (usato da `test_check_bash`), `_expand`, `_write_paths`. `bash.restores_from_index` non conta come modifica.
- `tests/hookkit.py`: `Lab(plugin_root=ROOT)`.
- Esclusioni (uguali per L0/L1/L2): `is_docs_md`, `.superpowers/`, `output_excludes` (comprende `.tollgate-run/` e `reports/`).
- Testi: rifiuto comincia con «nota di ricerca mancante o non valida per il task k», contiene `research.submit_command(program_command(...), k)` e i problemi dell'ultima `research_note` non ok del task; avviso comincia con «tollgate: informati prima di modificare».

## Test
`tests/test_check_research_gate.py`: 26 test (tutti quelli del brief e dei ruling: reminder_not_consumed_by_other_deny, refusal_ignores_problems_before_plan_reset, bash_restore_not_denied, bash_relative_target_resolved, piu' failed_edit_does_not_consume_reminder, reminder_per_task, reviewer_not_gated, bash_main_session_not_gated, docs esenti in L0, l0_bash_not_gated).
- RED: modulo spostato via, `python3 -B -m unittest tests.test_check_research_gate` -> FAILED (failures=13) (i test positivi; i negativi passano comunque). Mutazione: tolto il controllo `PostToolUseFailure` -> `test_failed_edit_does_not_consume_reminder` fallisce.
- GREEN: 26 test OK. `tests/run` (python3.11: 3083 test OK, skipped=2; python3 3.13.5: 3083 test OK), exit 0. Nessuna modifica a test esistenti.

## Scostamenti / note
- Nel test dell'interruttore il plugin root e' una copia temporanea di `bin/` con `skills/rules-base/SKILL.md` (con o senza `approved`), come da brief. `skills/rules-base` non esiste ancora nel repo (B2): con la radice vera l'interruttore e' spento.
- Un lavoro L0 fa avviso solo da Edit/Write della sessione principale (il brief: `pre_bash` solo per implementatori).
- Per errore ho lanciato `git checkout -p --` senza risposte (stdin chiuso): non ha scartato nulla, il diff e' integro.
