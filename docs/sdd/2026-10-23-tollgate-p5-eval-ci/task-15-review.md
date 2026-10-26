# Revisione del Task 15 (d2610c0..bf02e5c, 2 commit)

Ambito: spec rev 26, piano principale (matrice «Prove dei criteri di P5», Stato, sezioni 2, 3, 5, 7), `limiti.md`, `eval-e-ci.md`, `test_docs.py`. Revisione limitata al task. Test eseguito: `python3 -B -m unittest tests.test_docs` (6 test, OK). Controlli mirati a mano su numeri e citazioni, descritti sotto.

### Aderenza

- ✅ **Step 1, matrice.** Nove casi `spec` con esecutore, punteggio con e senza plugin, Δ, prova a secco e rapporto; casi `extra` con `--ablation none` e «non misurato» dove il Δ non esiste; e2 senza esito con il motivo (VE12, ruling D1). La CI ha run e SHA.
- ✅ **Citazioni esistenti.** Ho estratto con uno script tutte le citazioni `file::Classe.metodo` della sezione «Prove dei criteri di P5» e ho verificato che file, classe e metodo esistano in `tests/`: nessuna mancante (incluso `test_ci_workflow.py::CiWorkflowTest.test_ci_workflow_pinned`, riga 80).
- ✅ **Numeri coerenti con le fonti.** Controllati contro `2026-10-23-p5-eval.md` e `evidenze/eval-p5/*/tabella.md`: tutti i punteggi e i Δ dei nove casi coincidono; il Δ medio è (0,67+0,40+0,40+1+0,75+1+1+0,60+0,75)/9 = 0,73. s5: le tre invocazioni valgono 0,00, 0,25 e 0,75, come scrive la matrice. e3: 0,00 poi 1,00. Costo: la somma di `budget.tsv` è 9,06315, cioè 9,0632; sonde 0,7486, ripetizioni 0,5806+0,5829+0,2254 = 1,3889, residuo 70,94 (nel rapporto, e nel piano il tetto di 80). CI: run 40252693867, SHA 87cc62f, 21 min 12 s e 23 min 29 s come in `p5-ci.md`. Il mancato riporto di 70,94 nella matrice non è un difetto (c'è nel rapporto).
- ✅ **Step 2, rev 26.** Intestazione, 1.2 (limiti rivisti e nuovi), 1.3, 3, 9.x, 14, 16, 17 e riga 26 della sezione 20 presenti. D12 (le due voci di 17 in grassetto in 1.2, 17 «le voci di 1.2») applicata; ruling `digest-mismatch` nell'item degli artefatti; D1 definitivo nella voce «Due casi extra».
- ✅ **limiti.md e 1.2 allineati.** `test_limits_match_spec_1_2` passa sulla testa bf02e5c (il commit bf02e5c ha cambiato i testi del limite «best effort» ma non i titoli). I corpi di `limiti.md` e di 1.2 per le voci toccate da bf02e5c (best effort, scrittura da interprete) dicono la stessa cosa.
- ✅ **Step 3, piano.** Stato (P5 chiuso sul ramo, merge in attesa dell'OK, 2897 test, nessun `.superpowers/` nel piano: il solo ritrovamento è nella spec riga 604, descrizione di un hook preesistente), riga P5 della sezione 2, sezione 3, sezione 5 (costo misurato), sezione 7 «Dopo la v1» con rinviati, limiti rimasti, sezione 17, B/C/D e ripulitura dei percorsi locali.
- ⚠️ **Step 4, suite completa.** Non rilanciata (non ammesso). Le evidenze del report (2897 test OK su 3.11 e 3.13, e con `-W error::ResourceWarning`) sono affermazioni; non ci sono incongruenze.
- ⚠️ **Ledger.** `progress.md` non è nel mio perimetro letto; ho usato le voci di `task-15-contesto.md`.

### Punti di forza

- La matrice dice dove il numero è sporco (s5 e e3 corretti con un test, primo giro a 0,00) invece di mostrare solo il valore finale.
- I nomi dei test citati sono tutti veri: l'implementatore non ha inventato prove.
- `spec_limit_titles` ridotto alla sola 1.2, come da ruling Task 12; il test resta severo in entrambe le direzioni.
- Il test delle ancore (`heading_slugs`) asserisce davvero (`assertIn(anchor, heading_slugs(linked))`, con `checked > 5` contro il passaggio vuoto).

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**

1. `tests/test_p5_scripts.py:951`: `open(reg).read()` lascia un file aperto e produce `ResourceWarning: unclosed file` nell'output. Non fa fallire né `tests/run` né la CI (`ci.yml:31` ha `PYTHONWARNINGS=error::ResourceWarning`, ma l'eccezione è in `__del__`, e il controllo di `ci.yml:35` cerca solo «unclosed database»). Per la regola «avvisi nell'output sono rilievi» lo segnalo. Correzione: `with open(reg) as f: ...`. Codice del Task 1, fuori dal diff; la correzione è di una riga e il brief dello Step 4 chiede suite pulita.
2. `docs/verifiche/2026-10-23-p5-eval.md:29,35`: la colonna «Esito» dice «sotto soglia: difetto corretto» accanto a 0,75 e 1,00, e subito dopo la nota dice che tutti i 13 casi sono sopra soglia. La legenda sopra la tabella lo spiega, e la matrice del piano è chiara, quindi non inganna nessun numero; ma la riga letta da sola contraddice la conclusione. Suggerisco «sopra soglia dopo la correzione» (file del Task 14, fuori dal diff).
3. D19 («e2 cerca il testo reale di `reopen`») non compare nella rev 26: il testo («spec riaperto (…): fase spec_audit», `bin/tollgate_flow/l2acts.py:286`) non è in nessun punto della spec. È una voce del ledger «per la rev 26», quindi la omissione è letterale; il valore è basso (la spec 14 descrive i casi extra a livello di flusso, e il testo è già coperto dal test di e2). Decisione del controller: o una riga in 14 su e2, o chiudere la voce dichiarando che non ha un posto nella spec.
4. `docs/uso/limiti.md:107-109` e spec 1.2 riga 110: la voce `isolation: worktree` dice solo «Gli hook non li bloccano», che ripete il titolo. Il fatto utile (il subagente parte dal ramo predefinito e le sue modifiche non entrano nel ramo del lavoro) è in spec riga 577 ma non nel limite. Preesistente (era un elenco di due voci in 17), ma ora la voce ha un corpo.
5. Piano, sezione 7, ultimo paragrafo: «Prima del primo push le evidenze si cercano anche per forme di token, come ha fatto P5» — il primo push è già avvenuto (run CI 40252693867). Riformulare in «Prima di ogni pubblicazione».

### Dubbi del report, uno per uno

1. **ResourceWarning `unclosed file`:** rilievo Minor (n. 1). Non è un «unclosed database», quindi il criterio letterale dello Step 4 è soddisfatto, ma è rumore noto che resta.
2. **«sotto soglia: difetto corretto»:** non è un difetto della matrice; è un'etichetta ambigua nel rapporto del Task 14. Minor (n. 2), non blocca.
3. **Testo di `reopen` assente in rev 26:** Minor (n. 3), decisione del controller.
4. **Aggiunte a `test_docs.py` fuori brief (`/Users/`, ancore):** non è un rilievo. Sono minori del Task 12 che il ledger assegna al Task 15 (`task-15-contesto.md`, riga 209); il `~/` lasciato fuori è giustificato (`installazione.md` lo usa). Bene.
5. **Sezione 7 con minori del ledger fuori repo:** non è un rilievo. Il brief chiede «un solo elenco di ciò che resta, con il motivo», e ogni voce ne ha uno. Il piano non rimanda al ledger né a `.superpowers/`. Unica nota: mantenere i nomi dei file/test con precisione (verificabili nel repo) invece dei numeri di riga del ledger («P3b, righe 15, 17, 20») che un lettore futuro non può risolvere; non lo valuto come difetto perché è lo stile dei «Minori rinviati» già presente nel piano.
6. **Ultimo commit non provato in CI:** non è un rilievo. bf02e5c tocca solo documenti; `tests.test_docs` passa sulla testa. La matrice cita lo SHA vero provato (87cc62f) invece di attribuire il verde alla testa, ed `p5-ci.md` dichiara che il run dopo la revisione finale si aggiunge in chiusura.

### Valutazione

**Qualità del task:** Approvato.
**Motivo:** matrice, spec rev 26 e `limiti.md` sono coerenti tra loro e con i rapporti (numeri e citazioni verificati a campione e per intero sui nomi dei test); `test_limits_match_spec_1_2` e il resto di `test_docs` passano sulla testa. Restano cinque minori, nessuno bloccante.
