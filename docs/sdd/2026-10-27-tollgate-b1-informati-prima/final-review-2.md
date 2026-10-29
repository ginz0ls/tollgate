# Revisione finale 2 del ramo `b1-informati-prima`, dopo le correzioni (HEAD 9f0fac0)

Revisore: verdetto finale in sola lettura. Ho letto `final-fix-brief.md`, le ruling in fondo a `progress.md` (righe 155-161), `final-fix-report.md`, `final-rereview-1.md`, il diff `4faeb17..4545b93` (codice, agenti, skill, script, documenti) e la «Seconda corsa» del rapporto della prova (`docs/verifiche/2026-10-27-b1-prova-flusso.md`, commit 9f0fac0). Ho eseguito solo test mirati a HEAD: `tests.test_brief`, `test_wrapper`, `test_check_lookups`, `test_check_research_gate`, `test_research_cmd`, `test_skill_contract` e `test_lookups`, 207 test OK. La suite intera non l'ho rilanciata.

## Verdetti su I1 e I2

**I1: chiuso.** Il revisore e il giro `--fix` ora ricevono l'esito della nota.
- `bin/tollgate_flow/taskcmd.py:344-359`: `_review_prepare` passa `research_valid` e `lookups.last_problems(...)`. I problemi ci sono solo se la nota esiste e non è valida.
- `bin/tollgate_analysis/brief.py:204-222`: con `usable = has_note and research_valid`, una nota non valida conta come mancante. Con l'interruttore acceso il revisore apre `major` più `missing`; con l'interruttore spento `moderate`, senza `missing`. L'esito e i problemi stanno in un secondo recinto (`_outcome_block`), e il recinto si calcola anche sui problemi.
- `taskcmd.py:178-192` e `brief.py:122-129`: nel giro `--fix` con una nota non valida il brief dice «la nota non è valida: correggila e consegnala di nuovo prima di modificare» e riporta l'esito nel recinto.
- `lookups.last_problems` (`bin/tollgate_core/lookups.py:194`) guarda solo gli eventi dopo l'ultimo `plan_reset`. `agents/task-reviewer.md` spiega al revisore come trattare l'esito.
- La seconda prova reale conferma il comportamento: nel brief del revisore compare il blocco «Esito del controllo di tollgate» con `esito: valida`.

**I2: chiuso.** `skills/setup/SKILL.md:19` propone per prime le regole `WebFetch(domain:…)` nel `.claude/settings.json` del progetto. Dice in una frase il rischio di un `WebFetch` libero (dati portati fuori nell'URL, istruzioni ostili nelle pagine, nessun controllo di tollgate). Le voci globali restano una scelta dell'utente, a suo rischio, proposte solo se le chiede. La frase falsa «sono gratis… non scrivono niente» non c'è più. Spec 11.3 (riga 1067) e decisione 18 del piano B1 (riga 51) sono allineate. La regex di `test_setup_proposes_web_permissions` è più stretta, e due test nuovi controllano l'ordine dominio/globale e la frase del rischio.

## Difetti nuovi

Critical: nessuno. Important: nessuno.

Ho controllato i punti richiesti:
- **Uscita anticipata di `hooks/run` (righe 56-65).** L'elenco è fisso, sei tipi `tollgate:`. Il confronto `case " $LISTA " in *" $AGENT_TYPE "*` ha l'espansione tra virgolette, quindi i caratteri jolly non funzionano. Un tipo vuoto, sconosciuto o `tollgate:implementer` passa da Python. `post_lookup` ha un solo consumatore, la via breve del runner, e il suo unico effetto in più era `subagents.touch`. Un tipo estraneo può al massimo far registrare meno letture, mai di più. La prova reale non registra letture del revisore.
- **Via breve e `lookups.tracked_work` (`lookups.py:107`).** Con `agent_id` prende il lavoro del subagente, non chiuso, con `research` attivo e worktree esistente. `owner` (`lookups.py:136-152`) vuole ancora un task `running` con lo stesso `agent_type` e `row["work"] == work`, quindi l'attribuzione non si allarga. Togliere la guardia `subagents.get(...) is not None` prima di `touch` (`runner.py`) è sicuro, perché `tracked_work` restituisce `None` se il subagente non esiste.
- **Avviso dopo una riconsegna non valida (`research_gate.py:66-73`).** Conta l'ultimo evento del task tra `research_reminder` e `research_note`, in ordine di `seq`. Una consegna non valida riporta all'avviso. Una consegna valida esce prima (riga 98). Il caso L0 con `task None` (riga 88) non cambia, perché nessuna nota ha `task` nullo.
- **Recinti nei brief, `research show` (`research_cmd.py:136-141`).** `DATA_NOTE` e il recinto di `brief.fence` ci sono. La dipendenza `tollgate_flow` → `tollgate_analysis` è una direzione ammessa.
- **Limite della nota e ordine DB-file (`research_cmd.py:93-118`, `cli.py:389-392`).** La lettura di stdin ha un tetto (`4 × MAX + 1`). `check_note` valuta il testo intero, quindi una nota troppo lunga resta non valida, e nel DB si salvano solo i primi `MAX_NOTE_CHARS` caratteri. Il DB e l'evento vengono prima del file. Se il file non si scrive, il messaggio lo dice e `path` vale `None`, che `cli` non usa.
- **Funzione unica dell'interruttore (`lookups.py:170`).** Gate e `taskcmd` passano le stesse radici di prima. Con qualunque `OSError` l'interruttore vale ancora spento, come chiede la ruling 157.
- **Copia del plugin (`spikes/run-b1-flow.sh:151`).** Copia solo i file tracciati e lascia fuori le cartelle di sviluppo con le esclusioni di pathspec. Un file non tracciato nella radice non entra, e c'è il test.

Minor nuove (3, oltre alle 3 di `final-rereview-1.md`, che condivido e non ripeto):
1. **Minor, `bin/tollgate_flow/research_cmd.py:105-110`.** Prendiamo una riconsegna in cui il file non si scrive: la copia `research-<k>.md` della consegna precedente resta con il testo e la riga `esito:` vecchi. Il brief di `--fix` (`brief.py:122-129`) indica proprio quel percorso, e anche `show` lo restituisce quando il file esiste (`research_cmd.py:139-141`). L'esito vero arriva comunque dal DB, nel brief e in `show`, quindi il danno si limita a un file non aggiornato, e serve un errore di disco. Correzione possibile: se la scrittura fallisce, cancellare il file vecchio, oppure aggiungere al messaggio «la copia su file è quella di prima».
2. **Minor, `spikes/run-b1-flow.sh:151-153`.** Quando un file tracciato è stato cancellato dal working tree, `tar -T -` fallisce, ma la pipeline non ha `pipefail` e il `|| die` guarda solo il `tar -xf` finale: la copia resta parziale senza nessun messaggio. L'ha già segnalato la ri-revisione come nota. Lo ripeto come minor perché lo script tornerà in B8.
3. **Minor, `brief.py:214-217`.** La via breve «la nota non era richiesta» vale solo con `no_changes` e senza nota. In un task senza modifiche, una nota consegnata ma non valida con l'interruttore acceso porta ancora a `major` più `missing`. Il caso è raro, perché senza modifiche il passo non chiede la nota. Per coerenza con la minor 3 la regola potrebbe essere «con `no_changes` niente rilievo della nota».

## Valutazione delle ruling prese dopo la revisione

- **Ruling 159, prima il DB e poi il file.** Approvata. Gate, brief e `show` leggono la nota dal DB, quindi il DB è la fonte giusta da scrivere per prima. Il rifiuto di prima (codice 2 con niente salvato) costringeva a consegnare di nuovo per un difetto del solo file di comodo. L'unico costo è la minor nuova 1, il file vecchio che resta dopo un errore di disco.
- **Ruling 160, elenco fisso dei tipi di sola lettura.** Approvata. Era la variante sicura: un tipo sconosciuto passa da Python e `owner` lo filtra, mentre un prefisso avrebbe escluso anche un futuro implementatore `tollgate:*`. `Explore` e `general-purpose` costano ancora 250-500 ms per lettura nei repo attivi. Il costo è dichiarato e rinviato a B8: va bene.
- **Ruling 150, D8 precisata.** Approvata. Il codice legge l'interruttore a ogni modifica (`research_gate.py:100`), la rev 27 lo descrive, e il messaggio di rifiuto dice cosa fare. Accendere il blocco a metà task è il comportamento più prudente, ed è coerente con la decisione 8.
- Le ruling 155-157 e 161 (I2, giro unico, rinvii 13 e 31 nella sezione 9 del piano principale, seconda prova reale) sono applicate come scritte. La sezione 9 elenca i rinvii 13 e 31 come obbligatori nel task di B2 che crea `rules-base`.

## Ready to merge?

**Yes.** I1 e I2 sono chiusi a HEAD, e le correzioni non hanno introdotto difetti critical o important. Le minor che restano (3 della ri-revisione e 3 nuove qui sopra) non bloccano il merge: si possono aggiungere ai rinvii di B2 o B8. La suite è verde (3166 test su 3.11 e 3.13, anche con `-W error::ResourceWarning`) e la prova reale ripetuta sul codice corretto è riuscita senza difetti del prodotto.
