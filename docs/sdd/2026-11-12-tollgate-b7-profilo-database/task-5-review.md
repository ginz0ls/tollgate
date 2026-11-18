# Revisione Task 5 (b2e773c): approvazione di rules-database

Letto solo il pacchetto `review-eec75d2..b2e773c.diff`, il brief, le proposte e il report. Più due grep mirati in sola lettura (rischio: rimandi superstiti a «Da decidere tu»; riga di `docs/uso/comandi.md`). Suite non rilanciata.

### Aderenza
- ✅ Le 16 regole sono invariate: nel diff della skill c'è una sola riga aggiunta, `approved: 2026-11-17` dopo `version` (`skills/rules-database/SKILL.md`, riga 4). Nessun numero né testo di regola toccato.
- ✅ La data è la stessa in tre posti: skill, pagina (`docs/profili/database.md` riga 4 «Approvata dall'utente il 2026-11-17.») e `docs/uso/comandi.md:169-170`. `test_page_approval_date_matches_skill` la lega alla skill.
- ✅ «Cosa hai deciso» riporta i 17 punti. Nel diff le righe di Costo e Proposta dei punti 1-17 sono contesto invariato. Si aggiunge solo «Hai approvato la proposta.» a ogni punto. Cambia l'introduzione della sezione, scritta al passato.
- ✅ Carry (punto 17): c'è il paragrafo sull'introduzione della skill come «scelta nostra», con il `create table` in un `.sql`. È coerente con l'introduzione della skill, che dice «questo criterio è una scelta nostra». `test_page_records_the_introduction_as_our_choice` controlla pagina e skill.
- ✅ Nessuna sezione in sospeso: tolti «Come rispondere» e il Rinvio. `test_approved_page_has_no_pending_sections` lo difende. Il grep mirato non trova più «Da decidere tu» in `docs/profili`, `skills/rules-database`, `docs/uso`. I due rimandi nel rapporto delle fonti (`database-fonti.md`) e quello al punto 4 e al punto 11 nella pagina sono aggiornati.
- ✅ Nessun file approvato di altre aree toccato: lo stat elenca solo 6 file (pagina, rapporto database, comandi, skill database, due test).
- ✅ `test_real_database_fragment_approved` aggiunto in `tests/test_fragments.py`. I test di «bozza» sono invertiti o tolti.
- ⚠️ `claude plugin validate --strict` e la suite (4023 test, due interpreti) sono affermazioni del report, non verificabili dal pacchetto.

### Punti di forza
- Modifica minima e chirurgica sulla skill; la pagina cambia solo dove deve.
- I test di stato (approvata, data, nessuna sezione in sospeso, nessun rimando a «Da decidere tu» nella pagina e nel rapporto) sono mirati e hanno messaggi che non stampano dati.
- Il conteggio «Hai approvato la proposta.» pari al numero dei punti.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `tests/test_rules_database.py` (`PROPOSALS`, `test_page_records_the_choices`): il confronto con il testo di prima è debole su due lati. (a) Controlla solo la riga «Proposta:», non il «Costo:». Il report dice «testo di Costo e Proposta invariato», ma il test non lo prova per il Costo (lo prova il diff, non la suite). (b) Il controllo è `f"Proposta: {proposal}" in section` sull'intera sezione, non sul punto N. Cinque proposte sono identiche («lasciare così.», punti 2, 5, 7, 10, 11), quindi scambiare o cancellare una di quelle non fa fallire il test finché ne resta una. Correzione: dividere la sezione per punto (come fa `test_page_choices_count_matches_list`) e asserire la proposta nel punto con lo stesso numero. Per il Costo, aggiungere una seconda costante, oppure dichiarare nel commento che il Costo è difeso solo dalle parole chiave di `CHOICE_NEEDLES`.
2. `docs/profili/database.md:95`: «I tre agenti del profilo ... arrivano dopo la tua approvazione; fino ad allora la proposta di init non ha lo specialista». La pagina ora è approvata e gli agenti li fa il Task 6. La frase è ancora vera nei fatti, ma al lettore suona sfasata. Il Task 6 deve riscriverla (il punto è già nel suo perimetro, `final_specialist`). Nessuna azione qui.
3. Punto 17 della pagina: la «Proposta: tenerle tutte e sei.» è seguita dall'introduzione come settimo elemento. Il report lo dichiara. È coerente con il carry; resta solo una piccola asimmetria di lettura.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** Le regole, i testi delle proposte, la data e i file toccati corrispondono al brief e alla decisione dell'utente; nessuna sezione in sospeso. Restano solo rifiniture sul rigore del test delle proposte (rilievo 1) e sulla frase al punto 2 che il Task 6 riscriverà.
