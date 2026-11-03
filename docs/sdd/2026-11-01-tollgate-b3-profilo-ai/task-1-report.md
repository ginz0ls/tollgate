# Task 1 B3: report

Status: DONE. Commit: bcb031b "tollgate B3: rinvii di B2 negli agenti generici e nel brief".

## Implementato
- `agents/implementer.md`: rinvio 184 (sezione «Informati prima di scrivere»: «i file che elenchi nella nota aprili con `Read`», con il perché: i glob di cat/ls non registrano le letture); rinvio 186 (punto `tests` del report finale: il report di un giro di correzione ripete il riscontro RED/GREEN del difetto corretto).
- `agents/task-reviewer.md` (riga 53): se il brief dice che in questo lavoro le `R-BASE-…` non bloccano, un rilievo su di esse è una nota.
- `bin/tollgate_analysis/brief.py` (`review_brief`): rinvio 185, D13: la frase «in questo lavoro le regole `R-BASE-…` non bloccano» compare nella sezione del report quando `not (research and research_enforced)`.
- `bin/tollgate_flow/taskcmd.py` (`_implementer_report`, nuovo `_render`): D12: `None` si rende `null`; `concerns` escluso solo con `DONE_WITH_CONCERNS`, saltato se vuoto, mostrato con `DONE` se non vuoto; gli altri campi come prima.

## TDD
RED: `python3 -B -m unittest tests.test_manifest tests.test_brief tests.test_taskcmd` -> FAILED (failures=7): i 3 test manifest nuovi, i 2 test brief con frase attesa (research falso; interruttore spento), `test_report_concerns_shown_with_done`, `test_report_null_not_python_none` (output `size_reason: None`).
GREEN: stesso comando -> Ran 154 tests, OK.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: Python 3.11.16 OK (skipped=2), Python 3.13.5 OK, 3247 test, nessun «unclosed». Uscita in `task-1-suite.out`.

## Test
- test_manifest: `test_implementer_reads_listed_files`, `test_implementer_fix_round_repeats_red_green` (l'asserzione cerca «report di un giro di correzione ripete…» senza la maiuscola iniziale, perché la frase è a metà riga), `test_task_reviewer_says_base_rules_do_not_block_when_brief_says_so` (extra, copre la riga del revisore).
- test_brief: classe `ReviewBaseRulesTest`, tre combinazioni D13.
- test_taskcmd (`ReviewDoneTest`, D19): helper `_report_brief`; `test_report_concerns_shown_with_done`, `test_report_null_not_python_none`, più `test_report_empty_concerns_skipped` e `test_report_concerns_not_in_report_section_with_done_with_concerns`.

## Sostituzione di `test_done_report_without_concerns_adds_none`
Tolto: asseriva che `concerns` con stato `DONE` NON compaia nel brief, cioè il contrario del rinvio 187 (e di D12: con `DONE` e `concerns` non vuoto deve comparire nella sezione del report). Sostituito da `test_report_concerns_shown_with_done`.

## Scostamenti
- Nessuno rispetto al brief. Sopra il minimo: la frase del brief ha anche un inciso («il lavoro non ha il passo «informati prima» acceso»); l'aggiunta in task-reviewer è una riga. Docstring di `_implementer_report` aggiornata.

## Autorevisione
Completo rispetto a brief e carry (D12, D13, D19). Nessun `__pycache__` nel commit; solo i 7 file del task. Gli altri test citati (`test_implementer_tools`, `mentions_*`, `test_code_agents_preload_rules_base`) sono nella suite verde.

## Dubbi
Nessuno. Nota: `concerns` di sola spaziatura è trattato come vuoto (strip).
