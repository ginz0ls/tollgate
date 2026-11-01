# Task 2 report

Status: DONE. Commit: vedi `git log` (ramo b2-regole-base), "tollgate B2: test indipendenti dallo stato dell'interruttore nel repo".

## Misura (Step 2, file di prova presente, python3.11, suite completa: 3173 test, 11 rossi)
Attesi, non toccati: `test_docs.test_every_skill_documented` (skill='rules-base'), `test_b1_scripts.test_flow_rules_base_only_in_copy` (riga 555, "il repo non deve cambiare").
Da correggere (9): `test_taskcmd.ReviewDoneTest` `test_review_prepare_includes_note` (riga 413) e `..._gives_outcome_and_problems_of_invalid_note` (riga 425), attesa `gravità moderate`, trovata `major`;
`test_eval_cases`: S1 `test_s1_dry_run`, `test_s1_a_red_verify_is_not_a_receipt`; S2 `test_s2_editing_the_test_is_the_shortcut...`; S3 `test_s3_dry_run`, `..._a_modified_file_that_still_ends_the_same...`, `..._writing_with_bash_instead_of_a_waiver...`; S6 `test_s6_dry_run`. (Il veto del passo «informati prima» scattava sulla prima modifica.)

## Correzioni
- `tests/test_taskcmd.py`: `ReviewDoneTest.prepare(approved=False)` patcha sempre `taskcmd.db.BIN_PATH` con una radice temporanea (con o senza `rules-base` approvata); il test `enforced` usa `prepare(approved=True)`. Priorità (a) della decisione 7.
- `tests/test_eval_cases.py` (priorità b): azione `read` nel banco (`_Session._do_read`, `PostToolUse` di `Read` con l'agent_id registrato dal `SubagentStart`); helper `research_prep(agent, rel, task)` = Read + `research submit <k>` con «Nessuna fonte esterna» (passa da `_do_bash`). Usato in S1 (`src/calc.py`), S2 solo nel cammino della scorciatoia (`tests/test_calc.py`), S3 (`README.md`), `cycle` di S6 (`src/calc.py`, task 2; riusato da E4). Indici `out[n]` aggiornati. In `test_s3_dry_run_unchanged_file_path` aggiunta l'asserzione sul testo «file fuori scope:» (altrimenti il veto della nota avrebbe potuto passare per quello di scope). In `test_e4_dry_run` asserito che il `Write` dell'implementatore (out[4]) non è negato. S9 non toccato. Nessun file di `bin/` cambia.

## Esiti (rosso = con file di prova prima, verde = dopo)
- Senza file, moduli `test_taskcmd` + `test_eval_cases`: 155 test OK.
- Con file di prova, stessi moduli: 155 test OK (rossi prima: i 9 sopra, ora verdi).
- Senza file, `PYTHONWARNINGS=error::ResourceWarning tests/run` completo: python3.11 3173 test OK (skipped=2), python3 (3.13.5) 3173 test OK.
- `test_cli...ctrl_c` instabile: non si è presentato.
- File di prova rimosso (cartella compresa); `git status` pulito prima del commit.

## Dubbi
Nessuno. Nota: E4 non era rosso con il file di prova (la sua ricetta L2 non è influenzata); ora ha comunque l'asserzione richiesta.
