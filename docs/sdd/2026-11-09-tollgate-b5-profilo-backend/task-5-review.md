# Revisione Task 5 (aeb48b4): approvazione di rules-backend

### Aderenza
- ✅ `approved: 2026-11-10` dopo `version` (`skills/rules-backend/SKILL.md`, riga 4).
- ✅ Pagina: «Approvata dall'utente il 2026-11-10.» (riga propria, la intercetta il test di corrispondenza con la skill); introduzione riscritta al presente.
- ✅ «Cosa hai deciso»: 9 punti, ciascuno con «Hai approvato: resta la proposta, cioè ...» e la proposta in breve; testo, numeri, blocca, si giudica su, fonti delle regole invariati (il diff non tocca la tabella né la skill oltre `approved`).
- ✅ `docs/uso/comandi.md`: sezione `/tollgate:rules-backend` con 2026-11-10 e «init propone il profilo backend», stesso schema di rules-ai e rules-infra.
- ✅ `backend-fonti.md`: solo «Da decidere tu» -> «Cosa hai deciso» (storia della verifica lasciata com'era, corretto).
- ✅ Nessun file di rules-base, rules-ai, rules-infra o delle loro pagine toccato (stat: 6 file, tutti backend/comandi/test_fragments).
- ✅ `test_real_backend_fragment_approved` presente (`tests/test_fragments.py`), gemello di ai e infra.
- ✅ La pagina resta vera: «il profilo si può accendere» è corretto; «Il profilo non si accende da solo» (riga 35) descrive `init`, resta vero; nessun «finché non le approvi». «bozza che è stata verificata» (riga 117) è storia della verifica, accettabile.

### Rischio dei 3 test saltati in più
Lanciato `python3 -B -m unittest -v tests.test_rules_backend`: OK, 3 saltati; per infra 2 saltati. I tre di backend:
1. `test_page_is_a_proposal` (gemello attivo: `test_page_approval_date_matches_skill`, che pretende la riga di approvazione e la data uguale a quella della skill).
2. `test_page_brings_the_open_choices_to_the_user` (gemello: `test_page_records_the_choices`, stessi 13 needle sulla sezione «Cosa hai deciso» più 9 occorrenze di «Hai approvato: resta la proposta»).
3. `test_page_rinvio_says_what_stays_on_the_branch`: è il terzo in più rispetto a infra. Infra non ha un test del rinvio, quindi la differenza è un controllo che infra non aveva; qui si salta perché la sezione «Come rispondere» e il punto «Rinvio» non esistono più. Lo schema è lo stesso di infra (i test "da proposta" si saltano con `skip_if_approved`), e nessun controllo utile resta spento: il rinvio non è più offerto. Gemello implicito: `test_approved_skill_leaves_no_pending_decisions` (nessun «Da decidere tu», nessun «va confermata dall'utente» in pagina e rapporto).
Nessun controllo sulle regole, sul frammento o sul parsing è saltato: i salti sono solo test sul testo della pagina come proposta.

### Punti di forza
- Inversione di `test_frontmatter` completa (`approved` presente e `research.enforced` vero).
- `test_page_choices_count_matches_list` semplificato correttamente (la sezione vecchia non esiste più, nessun ramo morto).
- Differenze rispetto a infra minime e motivate.

### Rilievi
- Critical: nessuno.
- Important: nessuno.
- Minor (`tests/test_rules_backend.py:~440-450` e dintorni): nessun test asserisce che la sezione «Come rispondere» o il punto «Rinvio» siano spariti dalla pagina approvata; infra non lo fa neanche. Facoltativo.
- Minor (`tests/test_rules_backend.py:462`): le docstring dei test saltati dicono ancora «col Task 5» (riferimento di processo nel codice); stesso stile di infra («col Task 6»), accettabile.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** i requisiti di `carry.md` sono rispettati alla lettera, le regole non cambiano, i tre salti in più sono test della pagina come proposta, tutti con un gemello attivo o resi inutili dalla rimozione della sezione offerta.
