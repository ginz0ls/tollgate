# Task 6 fix: report

Commit 2bb649c.

RED (sorgenti ripristinati allo stato precedente, test nuovi presenti): `python3 -B -m unittest tests.test_lookups tests.test_b1_scripts tests.test_eval_cases tests.test_eval_run`: 372 test, 12 failures + 1 error: ObservedWebFetchTest (301/302/307/199, redirect con code 200), flowreg string message (ERROR), FetchStepTest redirect, S10 redirect e nuovo indirizzo, RunShTest string message e grants (`test_b8_grants_web_tools`), piu test_p5_registry_untouched_by_b8 (vedi sotto, difetto preesistente del test).

GREEN: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 4172 test OK (skipped=13), python3 (3.13.5) 4172 test OK (skipped=11), exit 0, nessun "unclosed". Log: W/suite-task-6-fix.log.

Scostamento dal piano: `test_p5_registry_untouched_by_b8` pretendeva che il registro di b8 fosse la sola intestazione; dopo la sonda (d2d2a7b) contiene la riga vera. Ora confronta i byte prima/dopo la corsa a secco.

Nota: `anonymize` lavora su byte (non legge la trace come JSON): nessuna modifica; il test `test_anonymize_leaves_the_row_alone` lo documenta. Rimossa nessuna altra riga di codice: in `evals/scrub.py` `_blocks` era gia protetto, il crash era solo in `flowreg.web_results` e `flowreg.tool_uses`.

La pagina approvata `skills/rules-ai/SKILL.md` (vecchio indirizzo) non e toccata: va nel rapporto finale.

## Fix round 1

Cambiato: `evals/scrub.py` `_patterns` (nuova regex `-home-<utente>-` -> `-home-USER-`, valida per file di testo e colonne dei `.db`), `evals/research_counts.py` `count` (`Path(run_dir).resolve()`). Test: `AnonymizeTest.test_anonymize_project_folder_names_with_dashes`, `ResearchCountsTest.test_research_counts_accepts_a_relative_folder` (RED: 0 != 2 e ValueError; GREEN dopo la correzione).
Comando: `PYTHONWARNINGS=error::ResourceWarning tests/run` su python3.11 e python3: 4174 test OK (skipped=11 sull'ultimo), exit 0 (W/suite-task-6-fix2.log).

## Fix round 2

Cambiato: `evals/scrub.py` `_patterns` (parola intera `<utente>` -> `USER`, dopo le forme `/home/` e `-home-`; controllo dei valori corti sempre per primo) e docstring di `anonymize`. Test: `AnonymizeTest.test_anonymize_user_name_as_a_whole_word` (riga di `ls -la` in file di testo e `.db`; `utente-provax` resta; valore corto rifiutato); in `test_anonymize_project_folder_names_with_dashes` il file `altro.txt` ora cambia (`-home-utente-prova` senza trattino finale diventa `-home-USER` come parola intera), atteso 3 file.
Comando: `PYTHONWARNINGS=error::ResourceWarning tests/run`: 4175 test OK su entrambi gli interpreti, exit 0 (W/suite-task-6-fix3.log).
