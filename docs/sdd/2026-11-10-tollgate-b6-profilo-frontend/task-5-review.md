# Revisione Task 5 (approvazione di rules-frontend), pacchetto f2fe35b..3b2a258

### Aderenza
- ✅ `approved: 2026-11-11` subito dopo `version` (skills/rules-frontend/SKILL.md:5). Stessa data nella pagina («Approvata dall'utente il 2026-11-11.», docs/profili/frontend.md:5) e in docs/uso/comandi.md (sezione `/tollgate:rules-frontend`).
- ✅ «Cosa hai deciso» ha 22 punti; in ognuno la riga «Proposta: …» diventa «Hai approvato: resta la proposta, cioè …» con lo stesso contenuto (diff riga per riga: nessun testo di proposta cambiato; le altre righe dei punti sono contesto invariato). Nessun pattern, marcatore o prefisso toccato (nessun file di templates/ o di codice nel diff).
- ✅ Spariti «Come rispondere», «Rinvio» e «Da decidere tu»; i rimandi sono passati a «Cosa hai deciso» (frontend.md:55, 57, 43). «finché non le approvi» e «dopo che avrai approvato» non ci sono più. «bozza» resta solo nel rapporto delle fonti, riferito alla bozza verificata (corretto, storico).
- ✅ frontend-fonti.md: solo il rimando alla sezione e «costi accettati dall'utente» (era «accettati o da accettare»): è la modifica dovuta all'approvazione.
- ✅ I test pedinano il requisito: `test_frontmatter` invertito; `test_page_approval_date_matches_skill`; `test_approved_skill_leaves_no_pending_decisions`; `test_page_records_the_choices` (needles + 22); `test_page_choices_count_matches_list` e `test_our_choices_are_named_in_the_choices` su «Cosa hai deciso»; `test_approved_page_has_no_pending_sections` (decisione 16); `test_real_frontend_fragment_approved` (tests/test_fragments.py:278).
- ✅ Le asserzioni usano `assertTrue(needle in section, "manca un testo atteso")` o `assertFalse(... , messaggio)`: in caso di errore non stampano la pagina.
- ⚠️ Evidenze (RED/GREEN, suite 3872 OK, validate --strict) sono nel report, non rilanciate: coerenti con il diff.

### Punti di forza
- Cambio minimo e chirurgico; stessa forma della pagina di backend approvata in B5.
- `CHOICE_NEEDLES` condivisa tra il test «aperto» e quello «deciso»: niente duplicazione della lista.
- Il test sulla data usa `re.M` ancorato e confronta la lista intera (data unica).

### Rilievi
**Critical / Important:** nessuno.

**Minor**
- tests/test_rules_frontend.py (test «Vale solo finché `approved` non è nella skill», circa riga 578 e riga 574/663 con `skip_if_approved`): il test su «Da decidere tu» e il suo gemello restano ma ora sono sempre saltati (i 3 skipped). Codice morto, identico a quanto lasciato da B5 (test_rules_backend.py:459): si può togliere in un giro di pulizia finale, non blocca.
- `test_page_records_the_choices` conta «Hai approvato: resta la proposta» ma non verifica che il testo della proposta di ciascun punto non sia cambiato rispetto alla versione precedente; è coperto dal diff di questo commit, non dal test (accettabile).

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** l'approvazione è applicata senza cambiare regole né proposte, la pagina non ha più sezioni o frasi in sospeso, le date coincidono nei tre posti e i test nuovi asseriscono con messaggi fissi.
