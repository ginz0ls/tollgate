# Task 7 (Step 2-4): approvazione di rules-ai

Implementato: `approved: 2026-11-02` dopo `version` in `skills/rules-ai/SKILL.md`; pagina `docs/profili/ai.md` con la riga «Approvata dall'utente il 2026-11-02.», testo al presente, «Da decidere tu» diventata «Cosa hai deciso» (4 punti al passato), «Come rispondere» rinominata «Se vuoi cambiare qualcosa»; nessuna regola cambiata. `docs/uso/comandi.md` (sezione rules-ai) non dice più «bozza». `skills/rules-ai/SKILL.md` sezione «Fonti» non parlava di bozza: invariata. `ai-fonti.md` invariato.

Test: `test_frontmatter` invertito (approved == 2026-11-02, research.enforced vero); nuovo `test_page_approval_date_matches_skill`; nuovo `tests/test_fragments.py::test_real_ai_fragment_approved`.

RED: `python3 -B -m unittest tests.test_rules_ai tests.test_fragments` -> FAILED (failures=1, errors=2) (KeyError 'approved' x2, approved(fragment) False).
GREEN: stesso comando + tests.test_init -> Ran 158, OK (skipped=2).
Skip dichiarati: `test_page_is_a_proposal` e `test_page_brings_the_open_choices_to_the_user` saltano con il motivo «la skill è approvata».
`test_real_trees_light_no_profile` verde e attivo (non tra gli skip); i test di init dalla CLI non cambiano esito.
`claude plugin validate --strict .`: uscita 0 (Validation passed).
Suite `PYTHONWARNINGS=error::ResourceWarning tests/run` (uscita in task-7-suite.out): Python 3.11.16 Ran 3363 OK (skipped=4); Python 3.13.5 Ran 3363 OK (skipped=2). Nessun «unclosed». Gli skip in più su 3.11 (4 contro 2) non sono legati al task (i 2 della pagina sono presenti in entrambi); non indagati.
Nessun __pycache__ nel commit.

## Fix round 1
`ai-fonti.md` righe 62-64 (R-AI-11, R-AI-06, R-AI-03): «Va confermato/a dall'utente» -> «Confermato/a dall'utente il 2026-11-02», rimando a «Cosa hai deciso». Nella pagina nessun altro rimando. Nuovo test `test_approved_skill_leaves_no_pending_decisions` (cerca «Da decidere tu» e «va confermato dall'utente» in pagina e rapporto).
Test: `python3.11 -B -m unittest tests.test_rules_ai` e `python3 -B -m unittest tests.test_rules_ai`: vedi esito nella risposta (OK).
