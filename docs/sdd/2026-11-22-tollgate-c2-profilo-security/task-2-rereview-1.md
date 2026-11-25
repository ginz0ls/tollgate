# Task 2, ri-revisione del giro di correzione 1 (`e27db19..c0a60df`)

Commit rivisto: `c0a60df`, «tollgate C2: sicurezza fin dal progetto, rifiniture dopo la revisione», un commit nuovo sopra `e27db19`, `Co-Authored-By: Claude Opus 5.5`. File letti dal pacchetto `review-e27db19..c0a60df.diff` (una volta) e con `git show c0a60df:<percorso>`; mai dal worktree vivo. Nessun test lanciato: le mutazioni B, F e G si verificano leggendo le asserzioni (vedi m1), e non avevo un dubbio che una esecuzione avrebbe sciolto.

Cosa ho controllato oltre al diff, con un controllo mirato per dubbio:
- **Identità delle copie**: `git grep -c -F` della frase intera su `c0a60df`. La frase di m2+m4 sta una volta in ognuno dei sei revisori del task; le due frasi di m3 una volta in ognuno dei sei implementatori; la frase di m7 una volta in `final-reviewer.md` e in `final-database.md`. Lo stat del commit dà una riga cambiata per file (due negli implementatori): nessun altro testo degli agenti cambia. `spec-adversary.md` non è nel commit.
- **Coerenza di m2 con il codice che legge il verdetto**: `bin/tollgate_analysis/verdicts.py:34-38` vuole `severity` tra le quattro, `rule` e `file` stringhe non vuote, `line` intero; `:79-81` blocca solo con `spec_compliance` non vuoto o con gravità bloccanti. Un rilievo `minor` con `file` il primo file del diff, `line` 1 e `rule` il passo del task è valido e non dà `changes`: «non chiede modifiche» è vero anche per tollgate.
- **Log della suite** `suite-task-2-fix-1.log`: `Ran 4366 tests … OK` su 3.11.16 e 3.13.5, `exit 0`, zero righe con «unclosed», «warning» o «avviso».

### Verdetti sui rilievi

**m1. I tre test nuovi non proteggevano il contenuto se spariva dal generico e dalle copie insieme; `ValueError` al posto di un'asserzione.** INDIRIZZATO.
- `tests/test_manifest.py:284-286` e `:295-296`: i cinque titoli in grassetto, in ordine, confrontati con `assertEqual` sulla lista delle voci. La mutazione B (prime tre voci tolte) dà una lista di due titoli: rosso.
- `tests/test_manifest.py:316-321`: la funzione `item` isola la voce e fa `assertEqual(len(items), 1, …)`; `:324-333` cerca nella voce del revisore del task `` `Sicurezza:` ``, «diff», «caso negato», «valori predefiniti». La mutazione F («`Sicurezza:` diff.») perde «caso negato»: rosso.
- `tests/test_manifest.py:337-341`: nel revisore finale «validato al confine», «segret», «caso negato». La mutazione G («caso negato.») perde «validato al confine»: rosso.
- `tests/test_manifest.py:353-357`: `assertEqual(len(items), 1, "voce sulla sicurezza assente o ripetuta")` prima di usare la voce, e «input dall'esterno» tra le parole cercate.
- Il report mostra B, F e G verdi con il test di `cf770f1` e rossi con il test nuovo (6, 6 e 2 fallimenti, con i nomi degli agenti), prima di toccare il testo degli agenti, e l'`AssertionError: 0 != 1` al posto del `ValueError`. Coerente con la lettura delle asserzioni.

**m2. Per la riga `Sicurezza:` assente mancavano `file`, `line` e gravità.** INDIRIZZATO.
- `agents/task-reviewer.md:48` (e riga 48 di `reviewer-ai`, `-backend`, `-database`, `-frontend`, `-infra`): «La sola riga assente è un rilievo `minor`, con `file` il primo file del diff, `line` 1 e `rule` il passo del task: non chiede modifiche. Un diff che smentisce la riga, o che ha uno di questi difetti, è un rilievo con la regola dell'area se ce n'è una, altrimenti con il passo del piano, e la gravità che gli dà la scala di «Standard del revisore».»
- Coerente con lo stesso agente: `:54` («`moderate` e `minor` sono note che non fermano il task»), `:56` (`file`, `line`, `rule` obbligatori; `rule` può essere il passo del piano), `:71` (esempio `"rule": "Task 3, passo 2"`), `:76` (`minor` tra le gravità, `line` intero). Nessuna contraddizione.
- Tenuto fermo da `tests/test_manifest.py:327-330`.

**m3. «Riga» dentro una stringa JSON invitava ad andare a capo.** INDIRIZZATO.
- `agents/implementer.md:64`: «La riga sta in fondo alla stessa stringa di `done`, senza andare a capo: un a capo vero dentro un valore JSON rende il report illeggibile.» Stessa frase alla riga 70 di `implementer-ai.md` e alla 72 di `-backend`, `-database`, `-frontend`, `-infra`.
- `agents/implementer.md:120` (126 in `-ai`, 128 nelle altre quattro): «con in fondo, nella stessa stringa e senza andare a capo, la riga `Sicurezza:` …».
- Coerente con «Report finale» (`:112-125`): un solo blocco JSON, `done` resta una stringa. Tenuto fermo da `tests/test_manifest.py:299` e `:311`.

**m4. Il test del caso negato che il piano non elenca poteva essere letto come `extra`.** INDIRIZZATO.
- `agents/task-reviewer.md:48` e le cinque copie, ultima frase della voce: «Ciò che la sezione «Sicurezza fin dal progetto» chiede all'implementatore (per esempio il test del caso negato) non è `extra`.» Coerente con `:37` (definizione di `extra`) e `:75`. Tenuto fermo da `tests/test_manifest.py:331-332`.

**m6. Il piano doveva ridire ciò che la spec approvata dice già.** INDIRIZZATO.
- `agents/plan-adversary.md:26`: «… e cosa succede con un input ostile; basta che lo dica la spec approvata a cui il piano rimanda, senza ripeterlo. Se non lo dicono né il piano né la spec approvata, è un rilievo.» Coerente con `:12` (l'avversario legge la spec approvata) e con `:20` (ciò che la spec chiede e il piano non fa resta un rilievo della prima voce: la frase nuova toglie solo l'obbligo di ripetere). Un solo blocco JSON nella chiusura, non toccata. `spec-adversary.md` invariato. Tenuto fermo da `tests/test_manifest.py:359-361`.

**m7. Due voci sulla sicurezza nel revisore finale, possibile doppio rilievo.** INDIRIZZATO.
- `agents/final-reviewer.md:31` e `agents/final-database.md:31`: «Un difetto si segnala una volta sola, anche se riguarda pure «Qualità e architettura», con la regola dell'area se ce n'è una, altrimenti con il passo del piano.» La voce «Qualità e architettura» (`:30`) è intatta. Tenuto fermo da `tests/test_manifest.py:339-340`.

**m8. «Vale in ogni lavoro» prometteva più di quanto la frase elencava.** INDIRIZZATO.
- `docs/uso/comandi.md:20`: «vale in ogni lavoro con agenti (L1 e L2) …», e in coda «In L0 implementa la sessione, senza agenti, e la riga non c'è.»

Il report nomina i test, il comando (`python3 -B -m unittest tests.test_manifest tests.test_docs`, 71 test, OK) e l'output RED (15 fallimenti, solo i tre test nuovi) e GREEN. `claude plugin validate --strict .` con uscita 0 è dichiarato e non verificabile dal diff (non lancio `claude`).

### Danni nuovi nel diff della correzione

Nessuno Critical né Important.

- **Minor. `tests/test_manifest.py:421` (`test_reviewers_cite_base_rules`) si è indebolito senza essere toccato.** Cerca «si segnala una volta sola» in tutto il testo di `final-reviewer.md`. Prima del giro la frase stava solo in «Standard del revisore» (`agents/final-reviewer.md:38`, sul difetto della nota di ricerca); ora la contiene anche la voce nuova (`:31`). Se la frase sulla nota di ricerca sparisse, il test resterebbe verde. Correzione a costo minimo: cercare lì «un suo difetto si segnala una volta sola», oppure restringere alla sezione «Standard del revisore». Non blocca.
- **Minor. `agents/task-reviewer.md:48` (e copie): «passo del task» e «passo del piano» nella stessa voce.** La frase sulla riga assente dice «`rule` il passo del task» (parole della decisione del controller), quella dopo «il passo del piano», come `:56`. L'esempio `"Task 3, passo 2"` (`:71`) copre le due letture e per tollgate è la stessa cosa (una regola che non comincia con `R-`), quindi nessun effetto pratico. Segnalo e basta.
- **Minor. `agents/task-reviewer.md:48` (e copie): «la sezione «Sicurezza fin dal progetto»» nomina una sezione che il revisore non ha.** La sezione è nel file dell'implementatore; nel revisore lo stesso titolo è una voce di elenco. «Chiede all'implementatore» e i cinque punti elencati nella stessa voce bastano a capirla. Segnalo e basta.

### Osservazioni fuori ambito

- I controlli nuovi delle frasi di m6 e m7 cercano poche parole («spec approvata», «si segnala una volta sola»): tengono ferma la presenza della frase, non il suo senso. Stesso limite di ogni test su testo, già discusso in m1; qui le copie sono protette dal test di deriva.
- m5 («dati» largo nella seconda forma della riga) resta com'è per decisione del controller: non rivisto.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.

Tre Minor nuovi, nessuno blocca. L'unico con una correzione utile è il primo (`tests/test_manifest.py:421`), una riga di test: si può fare ora o portare al Task 7, che copia questi paragrafi negli agenti di `security`.
