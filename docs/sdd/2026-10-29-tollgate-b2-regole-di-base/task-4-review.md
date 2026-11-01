# Revisione Task 4 (b17cbf0..8c8e6fd)

### Aderenza
- ✅ Skill, pagina e rapporto coincidono: 10 regole R-BASE-01..10 senza buchi; testo e `[blocca]` della skill (`skills/rules-base/SKILL.md`) corrispondono alla colonna «Blocca?» di `docs/profili/base.md:27-36` (sì per 01-06 e 09, no per 07, 08, 10). Verificato a mano riga per riga.
- ✅ Rapporto (`docs/profili/verifiche/base-fonti.md:11-23`): le 11 righe `ok` sono identiche a quelle del verificatore (`task-4-fonti.md`), con R-BASE-12 diventata R-BASE-10; la sezione «Regole tolte» (:30-43) ha «Bozza n. 10» e «Bozza n. 11» con testo (uguale alle righe tolte dal diff), riga del verificatore, motivo e correzione, senza id `R-BASE-`.
- ✅ Nessun `approved` né riga di approvazione (grep); la frase «bozza finché...» resta nella skill, come chiede il carry del Task 5.
- ✅ Decisione 10 resa nella pagina (:15-20): L1/L2 rifiuto, L0 solo avviso, lavori in corso e task già avvisati, lavori veri dalla versione unita. Risposte «approvo / correggi la N con … / togli la N» presenti (:49-53). Sezione delle regole tolte con le due correzioni suggerite e «rimetti la bozza n. 10 corretta» (:46).
- ✅ I test non dipendevano dal 12 (report); nessun altro file toccato.

### Punti di forza
Rinumerazione pulita e coerente nei tre file; test su tabella con parsing separato per sezione (la sezione delle tolte è esclusa dagli id); il test «Blocca?» ha già colto un errore reale dell'implementatore.

### Rilievi
**Important**
- `docs/profili/base.md:15-20, 22`: la pagina non è del tutto «senza gergo non spiegato», requisito esplicito del brief e della memoria `feedback-spiegazioni-semplici`. Restano senza spiegazione «task» (:18), «la versione unita su main arriva al plugin installato» (:19, parole di decisione 10 copiate così), «report», «plugin»; «progetto di B» compare come fonte (:30, :35) senza dire cos'è. Anche «L1 e L2 sono i lavori medi e grandi, L0 quelli piccoli» (:13) è una parafrasi non verificata sulla spec (la spec li definisce con soglie e con chi scrive). Correzione: una riga di spiegazione per ciascun termine (es. «task: un singolo pezzo di lavoro del piano»; «quando la correzione passa nel programma che usi davvero»; «progetto di B: il documento in cui sono scritte le tue correzioni») e frasi più corte; per L0/L1/L2 meglio «lavoro piccolo / più grande» con rimando alla definizione, oppure chiedere conferma al controller.

**Minor**
- `docs/profili/base.md:17`: in L0 a ricevere l'avviso è la sessione principale, non «l'agente» che lavora al task (spec 6.3/riga PreToolUse); dire «tu e Claude, nella sessione principale, ricevete un promemoria» o simile.
- `tests/test_rules_base.py` `test_page_lists_every_rule`/`test_page_blocca_matches_skill`: controllano solo l'id tra parentesi, non che il numero «N.» davanti (`1 (R-BASE-01)`) coincida con l'id; una pagina con «3 (R-BASE-02)» passerebbe. Aggiungere il confronto del numero con le cifre dell'id.
- `test_sources_report_covers_every_rule`: non controlla che nella tabella principale non ci siano righe `no` (una riga `no` ad una regola con altra riga `ok` è ammessa dal brief, quindi va bene) né che la sezione tolte nomini «bozza n.»; copertura più debole di quanto il rapporto prometta ma conforme al brief.
- `test_page_explains_what_changes`: le frasi attese sono confrontate quasi alla lettera in minuscolo; fragile a riformulazioni, ma non aggirabile in modo utile (i quattro contenuti devono esserci).
- `docs/profili/verifiche/base-fonti.md:3`: scrive che per ogni fonte si è controllato che la licenza sia MIT/Apache-2.0, ma il verificatore dichiara di non aver controllato i file `LICENSES/*` (`task-4-fonti.md`, Metodo). Riportare il limite (esistono entrambi i file, `ls LICENSES`; l'intestazione di agent-skills è già provata da `test_licenses_listed`).

### Valutazione
**Qualità del task:** Da correggere (lievemente). **Motivo:** contenuto, numeri, fedeltà della tabella e test sono a posto e senza `approved`; resta un rilievo Important sul linguaggio della pagina (gergo non spiegato, frasi lunghe), requisito esplicito per l'utente che approva.
