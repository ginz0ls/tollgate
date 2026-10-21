# Task 11 - rinviati di P3b in core, analisi e hook

## Implementato
- Riga 5: `tests/test_cli.py::ArgvSignalTest` (classe nuova; segnale scritto da `hooks/run PreToolUse`, poi `bin/tollgate start`): `test_second_start_without_new_signal_refused`, `test_level_option_in_argv_matches`. Verdi subito: il codice di P3b era già corretto (solo test mancanti).
- Riga 21: `config.py:194` usa `re.fullmatch`; `ProfileNamesTest::test_trailing_newline_name_falls_back`.
- Righe 22, 23: `git.range_base(repo, first_commit)`, usata da `git.commit_changes`, `taskcmd._range`, `task_verdict._task_files`, `post_bash`; `import json` nel gruppo stdlib; `TaskFilesTest` (profilo attivato dai soli `paths`, regola `[blocca]`, nessun file corrispondente, diff illeggibile fail-closed); `test_git.py::test_range_base_is_parent_or_empty_tree`.
- Riga 24: classi spostate sopra il blocco `if __name__` in `test_verdicts.py`, `test_profiles.py`, `test_checkpoint.py` (carry) e anche `test_bash.py` (4 classi, trovato dal grep richiesto). `PYTHONPATH=bin:. python3 -B tests/<f>.py` esegue lo stesso numero di test della scoperta (63, 23, 11, 29). Il lancio diretto senza `PYTHONPATH=bin:.` fallisce per l'import dei moduli (già prima).
- Riga 25: `parse_verifier_results` riporta «ogni risultato ha un id» una volta; `test_missing_id_problem_once`.
- Riga 32 (D18a): frase sull'esenzione di `reviews/<N>/` a ogni livello nella docstring di `violations.scope_exempt`. `finishcheck._own_document` non la contiene (il suo docstring dice già «in un lavoro L2» solo per la spec approvata): non toccato.
- Righe 38-40: `violations.active_profile_names(cfg, wt, work, *, head=None)` in `tollgate_core`, usata da `finalreview` (tolta `_profiles`) e da `apply._final_rules`. Scostamento minimo dal brief: parametro opzionale `head` (apply passa lo SHA del ciclo, `finalreview` la punta come prima; default punta del worktree). Un diff illeggibile solleva `GitError` (apply lo cattura: fail-closed come prima). `apply._review_report` con `ValueError` registra `veto` {event: subagent_stop, rule: final_review, reason}. Test: `RulesTest` (3), `ReviewerTest::test_interrupted_reviewer_that_changed_files_tampered`, `ReviewerTest::test_rejected_report_leaves_trace` (chiama `apply._review_report` con un ctx minimo, perché il percorso via hook filtra prima i riporti non attesi).

## Righe già risolte da task precedenti
Nessuna: tutte ancora presenti nel codice prima del task (riga 32: l'esenzione sta già in `scope_exempt`, dove ho messo la frase).

## TDD
RED (prima del codice):
- `python3 -B -m unittest tests.test_config.ProfileNamesTest.test_trailing_newline_name_falls_back` -> `AssertionError: 'acme:reviewer-web\n' != ''`, FAILED (failures=1).
- `python3 -B -m unittest tests.test_git.GitTest.test_range_base_is_parent_or_empty_tree` -> errore (manca `range_base`), FAILED (errors=1).
- `...VerifierResultsTest.test_missing_id_problem_once` -> FAILED (problema ripetuto 3 volte).
- `tests.test_check_final_review`: `test_rules_with_default_ref_fallback` FAIL `1 != 0`; `test_rejected_report_leaves_trace` errore (nessun evento `veto`).
GREEN: gli stessi comandi, OK. I test di sola copertura (righe 5, 22, 40, ordine classi) passano subito per costruzione.

## Verifica
`tests/run`: python3.11 `Ran 1684 tests ... OK`; python3 (3.13.5) `Ran 1684 tests ... OK`; EXIT 0. `tests.test_layers` OK.

## File
bin: `tollgate_core/{config,git,violations}.py`, `tollgate_analysis/verdicts.py`, `tollgate_checks/{task_verdict,post_bash}.py`, `tollgate_flow/{taskcmd,finalreview}.py`, `tollgate_hooks/apply.py`.
tests: `test_cli`, `test_config`, `test_git`, `test_check_task_verdict`, `test_verdicts`, `test_profiles`, `test_checkpoint`, `test_bash`, `test_check_final_review`.

## Dubbi
Nessuno rilevante. `test_bash.py` è fuori dall'elenco del brief ma coperto dalla richiesta del grep.
