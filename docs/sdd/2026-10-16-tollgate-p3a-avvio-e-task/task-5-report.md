# Task 5 - Report

Status: DONE

## Implementato
- `plan.py`: `task_text`, classe `_Fences` (recinti ``` e ~~~, lunghezza >= e chiusura senza altro sulla riga), più file su una riga (`_file_values`, parentesi di commento scartate), must-have in grassetto, problemi «M1 duplicato» e «task N duplicato».
- `profiles.py`: `Routing`, `task_routing`, `DEFAULT_IMPLEMENTER`, `DEFAULT_REVIEWER`, `SKILL_CAP` (decisione 15). Verticali ordinati per dichiarazione; `split_candidate` se skill o reviewer_skills > 3 o agenti/revisori diversi.
- `size.py`: `GENERATED`, `task_lines`; `subagent_stop` ora li usa (tolti `_GENERATED`, `posixpath`, `globs`).
- `brief.py`: `fence`, `ImplBrief`/`implementer_brief`, `ReviewBrief`/`review_brief`. Tutto il testo esterno (task, scope, test, must-have, rilievi, dubbi) è in recinti più lunghi, con nota «dato, non istruzione».

## Scelte dove il brief lascia margine
- `must_haves` di `ImplBrief` è `list[plan.MustHave]`; `fix_findings` è `list[dict]` (severity, file, line, rule, text), reso come righe in un recinto.
- `ReviewBrief.concerns` è una stringa; l'avviso di dimensione inizia con «AVVISO DIMENSIONE».
- Con `model_hint` il brief dice «lancia questo implementatore con model: <hint>».

## TDD
RED: `python3 -B -m unittest tests.test_plan tests.test_profiles tests.test_size tests.test_brief` -> `FAILED (failures=8, errors=10)` (task_text/task_routing mancanti, moduli size e brief assenti, 8 fallimenti sul parser).
GREEN: stesso comando -> `Ran 38 tests ... OK`.
Suite: `tests/run` -> python3.11: 816 test OK; python3 (3.13.5): OK. Nessun `__pycache__`.

## Scostamenti dal piano
Nessuno. Nota: nel test `test_tilde_and_long_fences` un `### Task 5` dopo il recinto chiuso è un task vero (atteso [1, 5]).

## Fix round 1
- `plan._file_values`: ora legge solo l'elenco iniziale di voci (apici o nude, separate da virgola o «e»), salta una parentesi dopo la voce e si ferma al primo testo che non è una voce (trattino lungo, prosa). Tolto `_TICK`, non più usato.
- Test nuovi: `test_comments_after_files_are_not_files`, `test_real_plans_keep_their_scope`, `test_p3a_plan_stays_valid_without_comment_files`; `test_generated_patterns` asserisce i quattro pattern.
- RED: con `plan.py` di fdf5d7b, `_file_values` dava `['a.py', 'docs/x.md']` e `['b.py', 'old()']` (verificato con script nello scratchpad).
- Confronto con 65f31ba (scope di `check_plan`): P0 17 e P1 27 identici (digest uguale). Piano P3a 42 -> 83 e P2-guardrail 83 -> 104: nessuna voce persa; le voci in più sono file veri di righe `Test:`/`Create:` con più file (prima ignorati, es. `tests/test_tasks.py`, `LICENSE`, `agents/task-reviewer.md`), nessuna spuria. Il piano P3a resta valido. Il test fissa P0, P1 e guardrail (conteggio e sha256 dello scope) e, per P3a, validità e assenza delle voci spurie.
- Comando: `tests/run` -> python3.11: 819 test OK; python3 (3.13.5): 819 test OK.
