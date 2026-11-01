# Report Task 6

## Implementato
- `skills: [rules-base]` dopo `tools:` in implementer, task-reviewer, final-reviewer, finding-verifier.
- implementer.md: punti 1 e 2 di «Informati prima di scrivere» fusi in un rimando a `rules-base`; rinumerati (3 punti).
- task-reviewer.md / final-reviewer.md: regole `R-BASE-…` valide per ogni diff, solo `[blocca]` danno blocker/major; difetto della nota segnalato una volta sola (decisione 8, carry D3/D6; nel final-reviewer condizionato al brief che mostra la nota). Tolto l'inciso «non una regola R-…».
- finding-verifier.md: R-BASE-… sono quelle di `rules-base`.
- brief.STANDARD: «regole dei profili e di base». `_review_research`: nota non utilizzabile = un solo rilievo `nota di ricerca` senza R-BASE in più; nota utilizzabile con difetto = R-BASE (blocker/major solo se `[blocca]` e interruttore acceso, altrimenti moderate) o `nota di ricerca`, mai due.
- research_gate._warning: finisce con «Le regole di base sono nella skill `tollgate:rules-base`.».

## Test
- Nuovi: test_manifest (4), test_check_research_gate (`test_warning_names_rules_base`, L0 e L1 con radice temporanea senza approvazione), test_brief (2), test_taskcmd (`test_rules_base_not_required`, guardia, già verde).
- RED: i nuovi (tranne la guardia) fallivano prima del codice (7 + 2 + 4 fallimenti). GREEN: 4 file verdi.
- `claude plugin validate --strict .`: uscita 0, `skills: [rules-base]` accettato.
- `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3197 test OK (skipped=2); python3 (3.13.5) 3197 OK. Il test instabile D16 non è fallito.

## Dubbi
Nessuno.

## Fix round 1
Gap: `verdicts.is_blocking` tratta come bloccante ogni `R-…` ignota; le `R-BASE-…` non `[blocca]` (07, 08, 11) fermavano il task.

Modifiche:
- `bin/tollgate_analysis/research.py`: `base_rules(skill_text) -> (note, [blocca])`, funzione pura (nessun import di tollgate).
- `bin/tollgate_core/lookups.py`: `base_rules(root) -> (note, bloccanti)`; le `[blocca]` bloccano solo con l'interruttore acceso; pagina illeggibile: `(vuoto, vuoto)`, quindi comportamento di prima (ignota = blocca).
- `bin/tollgate_checks/task_verdict.py` e `bin/tollgate_hooks/apply.py::_final_rules`: R-BASE unite a regole note e bloccanti (`ctx.plugin_root`).
- Test: `tests/test_check_task_verdict.py` (`make_base_root`, `BaseRulesTest`, `BaseRulesSwitchOffTest`, `BaseRulesUnreadableTest`), `tests/test_check_final_review.py` (stesse prove sul verdetto finale; il ctx finto ha `plugin_root`), `tests/test_brief.py` (il test della sezione distingue nota non utilizzabile, anche consegnata ma non valida, da nota utilizzabile). Radici sempre temporanee.

RED (bin ripristinato a HEAD, test nuovi): `python3.11 -B -m unittest tests.test_check_task_verdict tests.test_check_final_review` -> 3 FAIL per file (non-blocca che bloccava; blocca con interruttore spento che bloccava). GREEN con le modifiche: 104 test mirati OK (task_verdict, layers, final_review, brief); `claude plugin validate --strict .` uscita 0.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3211 OK (skipped=2); python3 (3.13.5) 3211 OK.
