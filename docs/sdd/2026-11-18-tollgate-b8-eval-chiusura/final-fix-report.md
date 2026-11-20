# Report delle correzioni della revisione finale di B8

Commit: `0705d6a` (codice e test) e `7dfee80` (documenti). Scostamento dal brief: due commit invece di uno, con oggetti «tollgate B8: correzioni di codice/documentali della revisione finale»; l'oggetto unico richiesto non c'è.

## Codice (TDD)
1. **F1** `bin/tollgate_analysis/bash.py` `_loader_word_lists`: una parola con spazi bianchi salta `_ASSIGN` e `_command_path_ok`. Test: `tests/test_bash.py` `EffectsTest.test_env_loader_shell_text_with_paths_and_assignments` (8 forme che chiedono, 2 che passano), `test_true_inner_commands_of_shell_text`; `tests/test_check_effects.py` `test_untracked_script_behind_shell_text_asks`.
   RED: `python3 -B -m unittest tests.test_bash.EffectsTest.test_env_loader_shell_text_with_paths_and_assignments tests.test_bash.EffectsTest.test_true_inner_commands_of_shell_text` -> `FAILED (failures=9)` (8 subTest + 1); `tests.test_check_effects` -> `FAILED (failures=1)`.
   GREEN: `python3 -B -m unittest tests.test_bash tests.test_check_effects` -> `Ran 162 tests ... OK`.
2. **#1 e #2** `_SUPABASE_HELP` morta tolta, `_SUPABASE_HELP_FLAGS = ("--help", "-h")` usata in `_supabase_asks_help`. Coperti dai test di Supabase esistenti (verdi).
3. **#4** `tests/test_tasks.py` `test_take_pending_by_number_beats_a_newer_reservation_elsewhere` (verde subito: fissa il comportamento di oggi).
4. **#10** `evals/scrub.py`: `_is_note_delivery` (parole contigue `research submit` dopo `tollgate`, da solo o dietro `python3`/`python`); `_is_exempt` la usa. Test: `tests/test_eval_run.py` `StripBashWebTest.test_note_delivery_is_exempt_only_after_the_tollgate_program`. RED: `FAILED (failures=1)`; GREEN: `tests.test_eval_run` OK.
5. **#15** `tests/test_eval_cases.py` `test_s12_doing_nothing_scores_two_fifths`: aggiunto `assertAlmostEqual(score_of(...), 2 / 5)`.
6. **#20** `tests/test_lookups.py`: `ObservedWebFetchTest` sopra `if __name__ == "__main__"`.

Mirati: `tests.test_bash tests.test_check_effects tests.test_lookups tests.test_tasks tests.test_eval_run tests.test_eval_cases.S12DryRun tests.test_docs` verdi.

## Documenti
7. F3: spec 14 (grader di s10) e rapporto (apertura della sezione s10).
8. F4: spec 14 (conteggi), rapporto («I conteggi della nota»), docstring di `evals/research_counts.py`; colonna «braccio» nel blocco «Dopo B».
9. F5 e #22: `docs/uso/eval-e-ci.md` (riga 24 con s10, s11, s12; riga 89 con le quattro sostituzioni, senza il percorso letterale perché `test_no_local_paths` lo vieta) e docstring di `evals/scrub.py`.
10. F2: `docs/uso/limiti.md` sotto «### Gli effetti esterni»; voce nel blocco «Dopo B» (punto 5).
11. #24: 8.1 aggiunta all'intestazione della rev 35, alla riga 35 della sezione 20, e al piano principale (sezioni 5 e 17).
12. #25: spec 1.2 («sonda (g) ed `e3`»), spec 16 riga (g).
13. #26: «23 corse con un implementatore che modifica (8 casi su 16)» in spec 16, progetto di B (sez. 15), rapporto e piano principale (sezioni 5, 6, 17). Verifica: il rapporto stesso ricalcola 23 note valide (s10 3, s11 3, s12 3, s1 3, s3 3, s6 3, e4 3, e5 2), uguale alla revisione.
14. #27: voce `docs/profili/verifiche/ai-fonti.md` riga 20 nell'elenco delle pagine che invecchiano (file non toccato).
15. #28: spec 8.5 nomina `infisical sm run` e `infisical secrets-manager run`; la stessa sezione dice ora che una parola con spazi non passa dai filtri (F1).
16. Blocco «Dopo B», voce 5: #3, #7, #11, F2 e la colonna «braccio» di F4, ognuno con il motivo.

## Suite
`suite-final-fix.log` di questa cartella (esito in fondo).

## Dubbi
- Due commit anziché uno (il codice era già committato prima della suite, per la regola di commit dopo ogni modifica).
- La riga 7 del brief cita `docs/verifiche/2026-11-18-b8-eval.md` «sezione s10»: la frase sta nella sezione «s10, s11, s12: cosa hanno fatto i due bracci».
