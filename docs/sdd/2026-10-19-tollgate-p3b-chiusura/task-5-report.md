# Task 5 - Report

## Implementato
- `config.py`: `PROFILE_DEFAULTS["rules"|"blocking_rules"] = []`; `AGENT_FORMS`; in `_merge_profile` un `blocking_rules` fuori da `rules` e' `ConfigError`, un nome agente fuori forma diventa `""` con l'avviso della decisione 9.
- `profiles.py`: `blocking_rules`, `known_rules`, `final_specialists`.
- `verdicts.py`: `parse_task_verdict` con `blocking_rules`/`known_rules` (usa `is_blocking`); con lo standard un rilievo scartato che poteva bloccare invalida anche un `approved` dichiarato (C8); `FinalVerdict`/`parse_final_verdict` (rilievi senza prova o con gravita' fuori elenco in `rejected`, C18; `"v"` non richiesto, C22); `VerifierResults`/`parse_verifier_results`.
- `task_verdict.py`: profili attivi sul diff del task (dal genitore del primo commit a `review_sha`); se il diff non e' leggibile la lista file e' vuota e ogni `R-...` blocca (fail-closed).
- Test: `test_config.ProfileNamesTest`, `test_verdicts` (riscritto `test_finding_with_bad_severity_or_line_dropped`, nuovi test regole, finale, verificatore), `test_profiles.RulesTest`, `test_check_task_verdict.BlockingRulesTest`; fixture C4 in `test_taskcmd.py`.

## Verifica
- `tests/run`: python3.11 1111 test OK, python3 (3.13) 1111 test OK.
- TDD: scritto codice e test nello stesso passo, senza una esecuzione RED separata registrata (scostamento di processo; i test mirati passano e coprono i casi del brief).

## Scostamenti / note
- Un rilievo non-dict in `rejected` e' avvolto come `{"text": str(f)}`.
- Un `approved` dichiarato con un solo rilievo scartato `moderate`/`minor` resta valido (C8).
- Verificatore: `results` vuoto o senza id validi e' non valido.
