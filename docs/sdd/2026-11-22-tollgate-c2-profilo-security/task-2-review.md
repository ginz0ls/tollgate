# Task 2: revisione (commit `cf770f1` sopra `0ae01de`)

Revisore in sola lettura. Letti: regole, brief, vincoli globali, decisione 20, report, pacchetto `review-0ae01de..cf770f1.diff`. I numeri di riga sono quelli dei file in `cf770f1`.

Controlli fuori dal diff, uno per rischio:
- **Il revisore del task vede davvero il campo `done` per intero?** `bin/tollgate_flow/taskcmd.py:272-286` (`_implementer_report`) e `bin/tollgate_analysis/brief.py:259-266`: il brief di revisione riporta ogni campo del report in chiaro, senza tagli. La riga `Sicurezza:` in fondo a `done` arriva al revisore.
- **Come si legge il blocco JSON del report?** `bin/tollgate_analysis/report.py:31-47`: `json.JSONDecoder().raw_decode`, rigoroso (vedi Minor 3).
- **`rules-base` ha regole sui segreti che la frase «regola dell'area, altrimenti passo del piano» salterebbe?** `git grep` di «segret», «password», «token» in `skills/rules-base/SKILL.md`: nessuna. La frase non scavalca regole base.
- **L0 usa un implementatore?** `skills/start/SKILL.md:41`: no, in L0 implementa la sessione (vedi Minor 8).
- **Prove di mutazione dei tre test nuovi**, in una copia `git archive cf770f1` in `/tmp/tollgate-rev-…`, poi cancellata; solo `python3 -B -m unittest tests.test_manifest` (base: 64 test, OK). Esiti sotto, in «Punti di forza» e nel Minor 1.

## Aderenza

- ✅ **File toccati**: i 16 agenti del brief, `docs/uso/comandi.md`, `tests/test_manifest.py`. `finding-verifier.md` e `spec-auditor.md` non compaiono nello stat. Un solo commit, oggetto come da Step 5, `Co-Authored-By: Claude Opus 5.5`.
- ✅ **Nessun altro testo degli agenti cambia**: il diff ha solo aggiunte, più la voce `done` di «Report finale» nei sei implementatori (una frase inserita, il resto della voce identico). Frontmatter e sezioni «Area» intatti. La voce `done` rientra nella decisione 20 («il campo `done` del report ha una riga `Sicurezza:`»).
- ✅ **Parola per parola nel generico e nelle copie**: le righe aggiunte sono identiche nei sei implementatori, nei sei revisori del task e nei due revisori finali (lette nel diff); `test_area_agents_derive_from_generic` lo conferma (mutazioni C, D, E, H).
- ✅ **Decisione 20, chi pianifica**: `spec-adversary.md:24` e `plan-adversary.md:26`, in «Cosa cercare», con le sette situazioni, le tre domande e «Se non lo dice, è un rilievo».
- ✅ **Decisione 20, chi implementa**: `implementer.md:55-64`, cinque punti e le due forme della riga; `implementer.md:120` richiama la riga nel campo `done`.
- ✅ **Decisione 20, chi rivede**: `task-reviewer.md:48` in «Parte 2: qualità» (riga `Sicurezza:` e diff contro di essa); `final-reviewer.md:31` in «Cosa controllare»; regola dell'area se c'è, altrimenti passo del piano.
- ✅ **D13**: la sezione è dopo `## Il lavoro` e, nelle copie, dopo la sezione «Area» (che precede «Il lavoro»: si vede nel contesto del diff), quindi fuori da essa. Nei paragrafi nuovi nessun id `R-…-NN` e nessuna delle tre frasi vietate. Gli avversari restano con un solo blocco JSON (la sezione «Chiusura» non è toccata).
- ✅ **Niente sezione obbligatoria nuova** del piano o della spec, niente in `rules-base`, nessun file approvato toccato, niente in `bin/`.
- ✅ **`docs/uso/comandi.md`**: una frase in `/tollgate:execute` (riga 34) e un paragrafo in `/tollgate:start` (riga 20).
- ✅ **I tre test con i nomi del piano**; RED riportato (14 fallimenti e 2 errori, solo i test nuovi), GREEN e suite: `suite-task-2.log` ha `Ran 4357 tests … OK` su 3.11.16 e 3.13.5, `exit 0`, nessuna riga con «warning», «unclosed» o «avviso».
- ⚠️ **`claude plugin validate --strict .`**: uscita 0 dichiarata nel report, non verificabile dal diff e non rilanciata (non lancio `claude`).
- ⚠️ **Lo script che ha applicato i paragrafi** non è nel commit (giusto così): l'identità delle copie la provo dal diff e dal test di deriva, non dallo script.

## Punti di forza

- Il testo nuovo si appoggia a ciò che l'agente ha già: il revisore finale è condizionato («dove il diff tocca input dall'esterno, accessi, dati o segreti»), l'implementatore ha la seconda forma della riga per i task che non toccano la sicurezza, e il revisore del task giudica «il diff contro di essa»: un task di sola documentazione chiude con una riga e non è spinto a inventare lavoro.
- Nessun conflitto con le regole su cosa blocca: la voce nuova non fissa una gravità, quindi resta la scala del revisore (`[blocca]` per le regole dei profili, calibrazione per il passo del piano). Il revisore finale non riceve la riga `Sicurezza:` (è sul report, che è del revisore del task): coerente con «tu non apri rilievi su di esse».
- La scelta «anche quando nessun profilo di sicurezza è attivo» invece di nominare `security` regge l'unione parziale della decisione 19.
- I test falliscono davvero se un paragrafo sparisce **da una copia**. Mutazioni provate: voce tolta da `reviewer-ai` (C), da `final-database` (D), paragrafo di chiusura tolto da `implementer-infra` (E), richiamo nella voce `done` tolto da `implementer-backend` (H): ogni volta rosso sia il test nuovo sia il test di deriva, con il nome dell'agente. Voce tolta da `plan-adversary` (I): rosso.
- `test_reviewers_check_security_line` itera su `FINAL_AREAS`: `final-security` del Task 7 sarà coperto senza toccare il test.

## Rilievi

### Critical

Nessuno.

### Important

Nessuno.

### Minor

1. **`tests/test_manifest.py:292-294`, `:317-318`, `:323-324`, `:337`: le parole cercate non proteggono il contenuto se sparisce dal generico e dalle copie insieme.** Mutazioni rimaste verdi (64 test, OK): (B) tolte le prime tre voci della sezione da tutti e sei gli implementatori, perché «input», «segreti» e «caso negato» stanno anche nel paragrafo di chiusura; la docstring dice «con i cinque punti» ma il test ne tiene fermi due; (F) voce dei sei revisori del task ridotta a «`Sicurezza:` diff»; (G) voce dei due revisori finali ridotta a «caso negato.». Il test di deriva non aiuta: confronta le copie con il generico, non il generico con la decisione. Inoltre, tolta la voce da un avversario, il test dà `ValueError` di spacchettamento e non un'asserzione leggibile (`:335`). Le parole sono quelle dello Step 1 del piano, quindi non è uno scostamento. Correzione: cercare i cinque titoli in grassetto delle voci (`**Input non fidato validato al confine**` e gli altri), nel revisore del task «caso negato» e «valori predefiniti» oltre a `` `Sicurezza:` ``, nel revisore finale «validato al confine» e «segret», negli avversari «input dall'esterno» (la condizione che evita rilievi inventati) e `assertEqual(len(items), 1)` prima di usare la voce.

2. **`agents/task-reviewer.md:48` (e copie): per la riga assente non c'è `file`, `line` né gravità.** Lo stesso file dice che un rilievo senza `file`, `line` o `rule` «non vale e viene scartato»; per la nota di ricerca è il brief a dare `file`, `line` e gravità, qui niente. Per una riga che manca in un task senza profilo non esiste nemmeno un passo del piano da citare. Il revisore sceglierà a caso un file del diff e una gravità: con `major` un task corretto torna indietro per una riga del report (un giro di opus e uno di Fable). È il primo dubbio dichiarato dall'implementatore, e la decisione 20 tace: serve una scelta del controller. Proposta a costo minimo, una frase in coda alla voce: la sola riga assente è una nota (`minor`), sul primo file del diff alla riga 1, con `rule` il passo del task; chiede modifiche solo il diff che smentisce la riga o che ha un difetto.

3. **`agents/implementer.md:64` e `:120` (e copie): «chiude con la riga», «con in fondo la riga» dentro una stringa JSON.** Il report si legge con un decodificatore rigoroso (`report.py:39-43`): un a capo vero dentro `"done"` rende il blocco illeggibile, e il veto che ne segue elenca i campi mancanti, non l'a capo. Un modello di solito scrive `\n`, ma «riga» invita ad andare a capo. Correzione: aggiungere «nella stessa stringa, senza andare a capo» oppure parlare di «frase finale `Sicurezza: …`»; la prova del Task 9 cerca comunque `Sicurezza:`.

4. **`agents/implementer.md:49` contro `:59` e `agents/task-reviewer.md:37`: il test del caso negato che il piano non elenca.** Il passo 1 dice «esattamente ciò che il task specifica», la sezione nuova chiede un test in più; il revisore del task ha `extra` («funzioni non richieste») in `spec_compliance`, che da solo dà `changes`. La voce nuova del revisore chiede quello stesso test, quindi un revisore coerente non lo segna, ma nessuna frase lo dice. Correzione possibile: nella voce del revisore, «ciò che la sezione chiede non è `extra`». Da decidere se vale una frase in più in sei file.

5. **`agents/implementer.md:64`: «dati» nella seconda forma è largo** (quasi ogni task tocca dati), mentre gli avversari dicono «dati personali». Un revisore pignolo può leggere «un diff che la smentisce» su qualunque task che legge un file. Il testo è quello della decisione 20, alla lettera: imposto dalla decisione, lo segnalo e basta.

6. **`agents/plan-adversary.md:26`: il piano deve ridire ciò che la spec approvata dice già.** In L2 l'avversario del piano legge anche la spec; così com'è, un piano che non ripete chi accede e quali dati tocca riceve un rilievo anche se la spec lo dice. Formula della decisione 20 («la spec o il piano … dice»), quindi imposto; il costo è qualche giro in più (il preflight D2 lo prevede già per la prova del Task 9). Una via: «il piano, o la spec approvata a cui rimanda».

7. **`agents/final-reviewer.md:30-31` (e `final-database.md`): due voci sulla sicurezza.** «Qualità e architettura» nomina già «sicurezza»; la voce nuova la segue. Nel generico non c'è la frase «un difetto si segnala una volta sola» (c'è solo nelle sezioni «Area»): possibile doppio rilievo sullo stesso difetto. Non si può togliere «sicurezza» dalla voce vecchia (nessun altro testo cambia); basterebbe «una volta sola» nella voce nuova.

8. **`docs/uso/comandi.md:20`: «vale in ogni lavoro»**, poi la frase elenca solo L2 e «L1 e L2». In L0 implementa la sessione, senza agenti (`skills/start/SKILL.md:41`): niente sezione, niente riga, niente revisore. La frase è esatta nei dettagli ma l'apertura promette di più. Correzione: «vale in ogni lavoro con agenti (L1 e L2)», oppure dire che in L0 non c'è.

## Valutazione

**Qualità del task:** Approvato.

**Motivo:** il commit fa ciò che la decisione 20 e D13 chiedono, senza toccare altro testo, con paragrafi identici nelle copie e test che diventano rossi quando un paragrafo sparisce da una copia. Gli otto Minor sono rifiniture; il 2 (riga assente senza `file`, `line` e gravità) e il 3 (a capo dentro `done`) meritano una scelta del controller perché riguardano testo che gira in ogni lavoro, e l'1 si corregge in poche righe di test.
