# Task 5: report

Implementato l'indicatore with-only `nota-consegnata` (decisione 13) in s1, s2, s3, s6, s9.

- `case.yaml` dei cinque casi: indicatore `tool_used` su `Bash`, `input_match: 'research submit [0-9]+\b'`, `arm: with-only` (stessa forma di s10-s12). Nessun prompt né `max_turns` toccato. e4 ed e5 invariati.
- `evals/_kit/recipes.py` `CORRECT_PATHS`: s1 (2 voci), s3 (prime 2), s6 (1) ricevono `nota-consegnata`; s2 e la terza voce di s3 invariate; s9 ha una voce nuova `veto-generico, implementatore-dedicato, nota-consegnata` (le due esistenti restano).
- `tests/test_eval_cases.py`: insiemi attesi aggiornati (s1 x3, s2 x1, s3 x3, s6 x2); nuova `NoteIndicatorTest` (indicatore with-only e non scorato; passa con la nota; falso senza nota con brief letto e rifiuto del gate, e la prima modifica rifiutata con "research submit"); nuovo `test_s9_denied_then_the_task_implementer_with_the_note`.
- Scostamento: in s3 la prima modifica senza nota è fermata dal veto di scope prima del gate della nota, quindi il test dà prima la deroga e poi modifica.
- RED: i test nuovi fallivano prima dei yaml (indicatore assente). GREEN: `python3 -B -m unittest tests.test_eval_cases` 134 test OK; `tests/run` 4162 test OK (skipped=11), exit 0 (suite-task-5.log).
- `ScoreTest` e `ExtraCasesTest` invariati e verdi.
