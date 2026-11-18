# Task 5 - report

Status: DONE.

Fatto
- `skills/rules-database/SKILL.md`: `approved: 2026-11-17` dopo `version`; regole invariate.
- `docs/profili/database.md`: riga «Approvata dall'utente il 2026-11-17.»; «Da decidere tu» e' diventata «Cosa hai deciso» (17 punti, testo di Costo e Proposta invariato, ogni punto chiude con «Hai approvato la proposta.»); nel punto 17 l'introduzione della skill (`create table` in un `.sql`) come scelta nostra; tolta «Come rispondere» con il Rinvio; rimandi interni aggiornati.
- `docs/profili/verifiche/database-fonti.md`: i due rimandi a «Da decidere tu» ora puntano a «Cosa hai deciso».
- `docs/uso/comandi.md`: data di approvazione al posto di «bozza».
- Test: `test_frontmatter` con `approved`; `test_approved_skill_is_enforced` al posto di quello sulla bozza; nuovi `test_page_approval_date_matches_skill`, `test_approved_skill_leaves_no_pending_decisions`, `test_approved_page_has_no_pending_sections`, `test_page_records_the_choices` (costante PROPOSALS, 17 testi), `test_page_records_the_introduction_as_our_choice`; `test_page_choices_count_matches_list` e gli altri sulla nuova sezione; tolti `test_page_is_a_proposal`, `test_page_brings_the_open_choices_to_the_user`, `test_page_rinvio_says_what_stays_on_the_branch`; `test_real_database_fragment_approved` in `tests/test_fragments.py`.
- `claude plugin validate --strict .`: uscita 0 (un avviso sull'icona e un consiglio sul README, non bloccanti).
- Suite: 4023 test, Python 3.11 OK (13 skipped), Python 3.13 OK (11 skipped), `exit 0`. Nessun test dipendeva dall'assenza di `final_specialist`.

Dubbi: nessuno. Il punto 17 dice «sei regole» e poi aggiunge l'introduzione come settimo elemento, per tenere il testo approvato identico.
