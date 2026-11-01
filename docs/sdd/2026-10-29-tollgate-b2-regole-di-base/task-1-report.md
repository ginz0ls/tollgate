# Report Task 1: interruttore pronto per l'accensione

## Implementato
- `research.enforced`: apici tolti prima del confronto con `_YAML_EMPTY`, che ora contiene anche `no`, `off`, `n` (confronto senza maiuscole).
- `lookups.rules_switch(root) -> (bool, str | None)`: file assente `(False, None)`, altro `OSError` `(False, "<classe>: <messaggio>")`. `rules_enforced` = `rules_switch(root)[0]`.
- `events.EVENT_TYPES`: `research_switch_unreadable`.
- `research_gate`: `_UNREADABLE` (testo della decisione 5). `_verdict` ritorna `(esito, lavoro, task, errore)`; l'interruttore si legge una volta prima del controllo della nota, e con nota valida ritorna `(None, work, task, errore)` se c'è un errore. `decide`: a `pre_*` antepone `_UNREADABLE` all'avviso; a `post_*` registra l'evento una volta per lavoro (`work_events` dopo l'ultimo `plan_reset`) più il `research_reminder` se dovuto. Vale per implementatori L1/L2 (anche via Bash), mai su `PostToolUseFailure`; L0 invariato.
- `brief._review_research`: ritorno anticipato con `b.no_changes and not usable`.

## Test e TDD
- RED (sorgenti di `bin/` riportati al commit precedente, test nuovi): `Ran 125 tests ... FAILED (failures=11, errors=3)`: i test nuovi di test_research, test_lookups, test_check_research_gate, test_brief.
- GREEN: `python3 -B -m unittest tests.test_research tests.test_lookups tests.test_check_research_gate tests.test_brief`: `Ran 125 tests ... OK`.
- Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: Python 3.11.16 `Ran 3173 tests, OK (skipped=2)`; Python 3.13.5 `Ran 3173 tests, OK`; EXIT 0.
- Test aggiunti: `test_enforced_refuses_no_off_n`; `test_switch_missing_is_silent_off`, `test_switch_unreadable_reports_error`, `test_switch_approved` (al posto di `test_unreadable_is_off_for_now`); `UnreadableSwitchTest` con i tre test del brief (radice con cartella al posto di `SKILL.md`, costruita nel `setUp` della sottoclasse di `Base`); `test_review_brief_no_changes_invalid_note_asks_nothing`.

## Scostamenti
Nessuno. Nota: l'output della suite contiene una riga `guard: la PR è avanzata...` stampata da un test preesistente.

## Dubbi
Nessuno.
