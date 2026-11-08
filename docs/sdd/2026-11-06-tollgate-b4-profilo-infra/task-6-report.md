# Task 6 - report

Status: fatto.

Modifiche: `approved: 2026-11-07` in `skills/rules-infra/SKILL.md`; pagina `docs/profili/infra.md` approvata
("Cosa hai deciso" con i sette punti tenuti, riga di approvazione, introduzione e coda adeguate);
`infra-fonti.md` rimanda a "Cosa hai deciso"; sezione `/tollgate:rules-infra` di `docs/uso/comandi.md` riscritta
con la data (voce carry del Task 6). Test: `test_frontmatter` invertito, `test_page_choices_count_matches_list`
sulla nuova sezione, nuovo `test_page_records_the_choices`, `test_real_infra_fragment_approved`.
I test nuovi erano rossi prima dell'approvazione. Nessun test esistente ha cambiato esito.

Verifica: `claude plugin validate --strict .` uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`:
3644 test, python3.11 OK (skipped=7), python3 OK (skipped=5), EXIT=0.

Saltati: 4 comuni a entrambi sono i test "pagina come proposta" di ai e di infra (2+2), che si saltano a skill
approvata; 1 e' la sonda `test_tmpdir_probe` (serve RUN_TMP_PROBE). Su python3.11 i 2 in piu' sono i test
che richiedono PyYAML (assente su 3.11, presente su python3).

## Fix round 1

Modifica: aggiunto `test_approved_skill_leaves_no_pending_decisions` in `RulesInfraPageTest`
(`tests/test_rules_infra.py`), copiato dal modello di `tests/test_rules_ai.py`: pagina e rapporto delle fonti
senza «Da decidere tu» né «va confermato/a dall'utente»; salta se la skill non è approvata.
Prova di rosso: aggiunta temporanea di una riga `## Da decidere tu` alla pagina, test rosso (1 failure);
pagina ripristinata (nessuna differenza in `docs/`), test verde sul testo vero.
Comando: `python3.11 -B -m unittest tests.test_rules_infra` e `python3 -B -m unittest tests.test_rules_infra`:
38 test, OK (skipped=2) con entrambi.
