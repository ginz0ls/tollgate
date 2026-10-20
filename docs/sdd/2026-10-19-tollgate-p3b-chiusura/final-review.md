# Revisione finale del ramo `p3b-chiusura` (cf4fe90..a29f588)

Revisore: opus, in sola lettura. Fonti: piano P3b (decisioni 1-26, Global Constraints), `decisions.md`, `review-focus.md`, `coverage.md`, `cautele.md`, `global-constraints.md`, il ledger `progress.md` con le righe `Ruling:`, `carry.md`, `preflight-scan.md`, spec rev 23, i rapporti del Task 1 e del Task 17, il diff dell'intero ramo e i sorgenti in `bin/` e `tests/`.

Comandi lanciati: la suite intera una sola volta, con `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`. Esito: 1396 test OK in 220 s, nessun `ResourceWarning`, quindi nessun «unclosed database». Ho poi lanciato un test di riproduzione mio, scritto nella scratchpad e non nel repo, per il rilievo I-1: conferma il guasto. Non ho modificato working tree, indice, HEAD o rami. L'unico file scritto è questo.

Ho controllato che il codice rispetti i ruling del ledger senza riaprirli: G1-G5, C2, C5, C6, C7, C8, C10, C13, C16, C17, C19, C20, C21, C24, C25, scope L2 di `finish check`, verificatore che omette id due volte, Important 1 del Task 9 (`review_unverified` e DoD), stato normalizzato di `prs_for_branch_prefix`, lease nell'autorizzazione, dubbio 1 del Task 10, rifiuto di `finish` in sessione non legata. Il codice li rispetta tutti. Due di questi ruling (C7 e C16) producono però, combinati con il controllo «rilievo senza esito» di `open-pr`, il vicolo cieco descritto in I-1. Non è un difetto dei ruling: manca un passo che li colleghi.

## Esito del Review Focus

| # | Esito | Evidenza |
|---|---|---|
| 1. `open-pr` interrotto | **Regge** | Se l'interruzione arriva dopo il push e prima di `pr create`, la ripetizione trova la PR aperta con `pr_for_branch` e passa da `pr edit` (`bin/tollgate_flow/openpr.py:200-205`, `:272-274`). Se arriva dopo il cambio di fase, la riprende il ramo `resume`, cioè `pr_open` con HEAD = `finish_sha` e l'intento `pr:<lavoro>:<sha>` ancora `requested` (`openpr.py:131-132`). L'atto si consuma per ultimo (`openpr.py:243-248`). Test: `tests/test_openpr.py:539` (`test_interrupted_after_push_no_duplicate_pr`), `:557` (PR creata e processo morto: edit e non create), `:572` (morte dopo `pr_open`). Residuo noto e accettato: un processo che muore tra `intents.complete` e `acts.consume` lascia l'atto `pending` (riga 46 del triage). |
| 2. Testo ostile nella PR | **Regge** | `prbody.neutralize` tronca ogni voce, spegne `@`, `<!--` e `-->` e mette il testo in un recinto più lungo di ogni sequenza di backtick (`bin/tollgate_analysis/prbody.py:63-79`). `prblock.render` sostituisce `<`, `>` e `&` con `\u00XX` (`prblock.py:27-31`) e `parse` legge l'ultimo blocco (`:34-48`). Il titolo viene dal ramo e mai dall'issue (`openpr.py:67-70`). Test: `tests/test_prbody.py:73`, che controlla un solo `<!-- tollgate`, nessuna `@utente`, un solo `-->`, il round-trip del blocco, il tetto di lunghezza e i recinti non richiudibili. I campi di `FIELDS` coincidono, nell'ordine, con l'esempio di 18.1. |
| 3. Revisore finale fermo per sola lettura | **Regge** | `awaiting_final` accetta anche le righe `interrupted` (`bin/tollgate_checks/_common.py:103-125`). Il controllo dell'impronta resta prima del verdetto (`bin/tollgate_checks/final_review.py:38-40`). Test: `tests/test_check_final_review.py:135` (`test_stale_interrupted_reviewer_verdict_counts`) e `:120` (un revisore `running` che ha cambiato file risulta `tampered`). Manca il test che combina `interrupted` e file cambiati (riga 40 del triage): lo stesso codice copre entrambi i casi, quindi è rinviabile. |
| 4. `sync` con «Update branch», conflitto e interruzione | **Regge** sui tre casi del focus, con il limite I-4 | I commit remoti si integrano con `--ff-only` e si registrano subito (`bin/tollgate_flow/sync.py:59-75`, `:186-189`). Con un conflitto si fanno `rebase --abort` e `_block`: base invariata, `phase_before_block` uguale alla fase di partenza, nessun intento `force_push` (`sync.py:190-200`, `:218-225`). Se `sync` si interrompe dopo il rebase, `complete_interrupted` riallinea senza ripetere il rebase (`sync.py:114-133`), chiamato da `start` prima della raccolta delle conferme (`bin/tollgate_flow/start.py:142-150`). Il push forzato richiede sempre l'intento e usa il lease (`openpr.py:194-198`, `:260-268`). Test: `tests/test_sync.py:153`, `:238`, `:197` (integrazione e poi conflitto) e `tests/test_start.py:789`. Limite: un'autorizzazione `force_push` con il lease vecchio non si rinnova mai e può bloccare per sempre il push (I-4). |
| 5. `adopt` con il ramo in un worktree o solo remoto | **Regge** | Un worktree che già ospita il ramo si riusa. Il ramo nel checkout principale e un worktree registrato ma senza cartella si rifiutano, senza `--force` (`bin/tollgate_flow/adopt.py:234-268`). Il ramo che esiste solo su origin si crea con `create_branch` sullo SHA remoto. Test: `tests/test_adopt.py:264` e `:278`, più `:296-312` (checkout principale, worktree mancante). |

## Rilievi

### Critical

Nessuno.

### Important

**I-1. Un rilievo senza esito di un ciclo che non è l'ultimo blocca `open-pr` per sempre, e nessun atto lo sblocca.**
Codice: `bin/tollgate_flow/openpr.py:175-177` (la query cerca `verification IS NULL` in tutti i cicli), `bin/tollgate_core/reviews.py:85-95` (`supersede` non tocca i rilievi), `bin/tollgate_flow/finalreview.py:91-92` (con `review_unverified` non si lancia più nulla) e `bin/tollgate_flow/actapply.py:153-165`.

*Guasto, riprodotto.* Il revisore finale del ciclo 1 riporta un rilievo `major` e lo stadio passa a `verify`. Prima che parta il verificatore HEAD cambia: per esempio un commit del coordinatore in `review`, oppure `start --reopen-execution` seguito da una correzione e da un nuovo `/tollgate:finish`. `review prepare` chiude il ciclo 1 come `superseded`, ma il rilievo `f-1-1` resta con `verification` nullo. Il ciclo 2 si chiude `ok` e l'atto `finish` è valido. A quel punto:
- `open-pr` esce con 1: «rifiuto: rilievo f-1-1 senza esito: lancia … review prepare»;
- `review prepare` risponde «revisione già superata (ciclo 2)»;
- `approve finding` accetta solo i rilievi `confirmed`;
- `approve unverified-review` non tocca i rilievi.

Resta solo `abandon`. Il test di riproduzione l'ho scritto nella scratchpad e non sta nel repo. La stessa trappola scatta con C7. Prendiamo l'ottavo ciclo in `verify`, con il verificatore che per due volte omette degli id (blocco «verificatore senza esito»). L'utente dà `approve unverified-review`, che è ammesso perché i cicli sono 8, e poi `resolve`. Da qui `review prepare` stampa soltanto «revisione non verificata», mentre `open-pr` continua a rifiutare per i rilievi `f-8-*` senza esito.

*Correzione.* `reviews.supersede` porta a `unverified` (motivo «ciclo superato») i rilievi del ciclo ancora senza esito. `approve unverified-review` fa lo stesso sui rilievi senza esito dell'ultimo ciclo (motivo «revisione non verificata»). La spec 8.6 («open-pr rifiuta se un rilievo registrato non ha esito») va precisata così nella rev 24. Servono due test: il caso riprodotto qui sopra, e `unverified-review` con l'ottavo ciclo in `verify`. In alternativa si può limitare la query di `open-pr` al ciclo che vale per HEAD (`review.cycle`), come fa già la DoD con la decisione 15. Così però nel blocco 18.1 resterebbero rilievi con `verification` nullo, quindi preferisco la prima strada.

**I-2. `sync` in `execution` con un task che ha commit ma non è `done` gli guasta l'intervallo di revisione.**
Codice: `bin/tollgate_flow/sync.py:164-168`, che ammette `execution` senza guardare i task, `sync.py:78-85` (`_record_commits` registra soltanto eventi `commit`, non `tasks.commits`), `bin/tollgate_flow/taskcmd.py:209-218` (`_range`) e `bin/tollgate_checks/task_verdict.py:26-35` (`_task_files`).

*Guasto.* Il task 2 è `running` o in `review`, con `tasks.commits = [c2]`, e l'utente digita `/tollgate:sync` perché `main` è andato avanti (la skill dice «fase `execution` o `pr_open`»). Il rebase riscrive `c2` in `c2'`, ma `tasks.commits` resta `[c2]`. Poi `task review-prepare 2` calcola `_range` come `c2^..HEAD`. Il vecchio `c2` è ancora nel database degli oggetti, quindi `c2^` si risolve e cade sulla base vecchia. Diff e brief del revisore del task comprendono allora tutto ciò che `main` ha portato tra la base vecchia e quella nuova. Lo stesso intervallo decide i profili attivi in `task_verdict._task_files`, quindi anche quali regole `[blocca]` valgono. La rev 23 dice «i commit riscritti non si riattribuiscono ai task, già `done`», ma il codice non garantisce questa premessa. In più `sync` non controlla che non ci sia un implementatore in corso nel worktree che sta riscrivendo.

*Correzione.* `sync` rifiuta in `execution` quando un task è `running` o `review` (oppure non `done` con `commits` non vuoto), o quando c'è un subagente scrittore `running` sul lavoro. Il messaggio: «chiudi o riporta in attesa il task k, poi /tollgate:sync». L'alternativa è rimappare `tasks.commits` per `patch-id`, ma costa di più. Serve un test in `tests/test_sync.py` con un task in `review` e commit: rifiuto, e HEAD invariato.

**I-3. `pr_for_branch` prende anche le PR da fork con lo stesso nome di ramo. `open-pr` ne riscrive il corpo e `adopt` ne ripristina il tetto di livello.**
Codice: `bin/tollgate_flow/gh.py:143-151` (`pr list --head <ramo>` senza filtro sul repo di testa), `openpr.py:200-209` e `:272-274`, `adopt.py:101-127`. È la riga 42 del triage, che qui diventa più grave.

*Guasto.* Il nome del ramo è prevedibile: `tg/<N>-<slug del titolo pubblico>`. Chiunque può aprire da un fork una PR con quella testa prima di `finish open-pr`. `gh pr list --head` filtra per nome e non per proprietario, e `pr_for_branch` sceglie il numero più alto. Ne seguono due guasti:
- `open-pr` trova la PR del fork `OPEN` e fa `gh pr edit <n> --body-file`: scrive il blocco 18.1, con DoD e `head_sha` del lavoro, sulla PR di un altro, poi registra quel numero in `work_items.pr_number`. La PR vera non si apre.
- Dopo un DB perso, `adopt` legge `level_cap` dal blocco JSON di quella PR, un testo controllato da chi l'ha aperta. `_cap_from_block` controlla solo `issue`, quindi il lavoro riparte con un tetto `L0` e salta revisione finale e task.

*Correzione.* `pr_for_branch` chiede anche `isCrossRepository` (oppure `headRepositoryOwner`) e scarta le PR da fork; `fakegh` deve conoscere il campo. Per difesa ulteriore, dopo il push `open-pr` modifica una PR esistente solo se il suo `headRefOid` coincide con lo SHA spinto. Servono un test con una PR da fork per `open-pr` (si apre la nostra) e uno per `adopt` (il tetto non si ripristina).

**I-4. Un'autorizzazione `force_push` con il lease vecchio non si rinnova mai: dopo «Update branch» il push resta impossibile.**
Codice: `bin/tollgate_flow/sync.py:105-109` (con un'autorizzazione già presente non ne crea una nuova), `bin/tollgate_core/intents.py:203-219` e `openpr.py:262-268` (il lease viene dall'autorizzazione; `take_force` scatta solo dopo un push riuscito). È la riga 57 del triage, e il guasto è reale.

*Guasto.*
1. `sync` riscrive HEAD in `H1` ed esce con 3 (serve una nuova revisione). L'autorizzazione ha `lease = R1`, il vecchio push.
2. Su GitHub qualcuno preme «Update branch» e il remoto diventa `R2 = merge(R1, main')`.
3. `/tollgate:finish` arriva a `open-pr`: il remoto ha divergenza e l'autorizzazione esiste, quindi parte `push --force-with-lease=…:R1`, che git rifiuta perché il remoto è `R2`. L'autorizzazione resta valida.
4. `/tollgate:sync` vede `R2` divergente (non è noto e non è antenato) e apre `needs_you`. L'utente integra a mano e dà `resolve`.
5. Il nuovo `sync` rifà il rebase, che toglie di nuovo il merge. `_realign` trova l'autorizzazione vecchia ancora `authorized` e non la rinnova.
6. Ogni `open-pr` successivo rispinge con lease `R1` e fallisce.

Non c'è un'uscita: `approve rebase` richiede il blocco di un conflitto del rebase.

*Correzione.* In `_realign`, se c'è un'autorizzazione `authorized`, il suo `lease` si aggiorna alla punta remota appena letta. In alternativa la vecchia si marca come superata e se ne crea una nuova. Quando il push con lease fallisce, il messaggio di `open-pr` deve indicare `/tollgate:sync`. Serve un test: autorizzazione con lease `R1`, remoto avanzato e già integrato, nuovo `sync` riuscito, poi `open-pr` che spinge.

### Minor (nuovi)

**m1. Il corpo della PR non mostra i rilievi `unverified`, compresi i `blocker` e i `major` che il verificatore non ha potuto provare o che stanno oltre `max_findings`** (`openpr.py:324-332`, che prende solo i `confirmed`). Si vedono solo nel blocco JSON, che GitHub non mostra. *Correzione:* aggiungere a `prbody.render` una sezione «Rilievi non verificati», neutralizzata come le note. Costa poco; altrimenti va a P4, nel commento `attenzione`.

**m2. `finish check` non trasforma `git.GitError` e `OSError` in un rifiuto** (`bin/tollgate_flow/finishcheck.py:63`). Dalla CLI l'errore arriva all'`except` finale di `cli.main` ed esce con 1 e «tollgate: …» su stderr. La skill `finish` (§1) legge però 1 come «rosso, mostra le voci [no]». *Correzione:* aggiungere le due eccezioni all'`except` di `check`, che esce con 2.

**m3. `approve rebase` non registra come eventi `commit` i commit riscritti dal rebase fatto a mano** (`actapply.py:184`; `sync` invece li registra). Se tra il rebase fatto fuori da Claude e `act apply` gira un qualunque Bash nel worktree, `post_bash` usa ancora la base vecchia. Vede allora i commit di `main` come nuovi del lavoro, ne calcola le violazioni (scope) e apre un `needs_you` con veto. *Correzione:* dopo `set_base`, chiamare la stessa registrazione di `sync._record_commits`.

**m4. Sync dopo il rifiuto di `finish check`** (`sync.py:232-235`). Se `finish check` rifiuta (task non chiusi, codice 2), `sync` stampa «finish check non è verde dopo il rebase» anche se non si tratta di un rosso. *Correzione:* distinguere `REFUSED` da `RED` nel messaggio.

**m5. Skill e codice.**
- `skills/sync/SKILL.md` dice «fase `execution` o `pr_open`», ma il codice ammette anche `review` con la PR (`sync.py:165`).
- `skills/adopt/SKILL.md` dice che in `pr_open` la PR si aggiorna con `/tollgate:sync`. Dopo `adopt` però i task sono `pending`, quindi `finish check` dentro `sync` rifiuta, con l'atto già consumato. La strada giusta è `start --reopen-execution` e poi la riesecuzione dei task.

**m6. Spec rev 23, 12.4: per gli orfani di `cleanup` la spec dice «rami `tg/*`», il codice `tg/<N>-*`** (`bin/tollgate_flow/closing.py:24`, `:144-147`). È la riga 63 del triage: la nota prevista per la rev 23 non c'è.

## Triage dei minori rinviati (82 righe di `deferred-minors.md`)

**Da correggere prima del merge: 5 righe.**

| Righe | Decisione | Motivo |
|---|---|---|
| 42 | **Prima del merge** (è I-3) | PR da fork: corpo riscritto su una PR altrui e tetto di livello preso da un testo non fidato. |
| 57 | **Prima del merge** (è I-4) | Il lease non rinnovato produce un vicolo cieco dopo «Update branch». |
| 58, 59 | **Prima del merge** | `adopt` può dare un livello più basso di quello che darebbe `start`. Una issue di un autore esterno passa in L1, contro la spec 5 e 6.1 («autore esterno → L2»), anche se `adopt.py:187` legge già l'issue (`author_association`). Con l'issue illeggibile si continua con il solo diff, mentre per la PR illeggibile si rifiuta. *Correzione:* `author_association` fuori da `TRUSTED_AUTHORS` dà L2; con l'issue illeggibile si rifiuta, come per la PR. |
| 63 | **Prima del merge** (solo testo) | La spec 12.4 descrive gli orfani in modo diverso dal codice (m6): P4 e P5 leggerebbero una regola sbagliata. È una parola da cambiare. |

**Rinviabili: 77 righe.**

| Righe | Decisione | Dove |
|---|---|---|
| 1, 2, 3, 80 | Rinviabili: script e rapporto, nessun effetto sul plugin. | nessuno |
| 4 | Rinviabile: nomi dei campi di `gh` da verificare con il `gh` vero (G4). | P4 (primo uso reale) |
| 5, 51, 55, 67, 73, 77, 82 | Rinviabili: test mancanti o deboli; il codice regge alla lettura. | P3c |
| 6, 7, 14, 16, 35 | Rinviabili: docstring, indentazione, riga lunga, variabile inutile, messaggio con `None`. | nessuno (con il primo ritocco) |
| 8 | Rinviabile: serve un `OSError` nella cartella di stato; accettato da C2. | nessuno |
| 9 | Rinviabile: accettato dalla decisione 2. | nessuno |
| 10, 11 | Rinviabili: i chiamanti rispettano le precondizioni di `close_cycle` (verificato in `finalreview._resume`, `apply._review_report`, `_finding_verify`, `_approve_finding`). | P5 |
| 12 | Rinviabile: un declassamento verso l'alto è una scelta dell'utente, ed è documentato in `effective_severity`. | nessuno |
| 13 | Rinviabile: le chiavi degli intenti sono costruite solo dal codice. | P5 |
| 15, 17, 20, 61, 66, 70, 75 | Rinviabili: posizione dei test, processo, accoppiamento o duplicazione senza guasto. | nessuno / P5 |
| 18, 19 | Rinviabili: comportamento voluto (fail-closed) o caso teorico. | nessuno |
| 21 | Rinviabile: un nome di agente con `\n` finale è un caso artificioso; `fullmatch` costa nulla. | P3c |
| 22, 23, 24, 25 | Rinviabili: copertura e messaggi ripetuti. | P3c |
| 26, 28 | Rinviabili: duplicazione e un `git.changes` in più. | P5 |
| 27, 44 | Rinviabili: i JSON vengono dal DB e li scrive solo il codice; rompersi richiede un DB guasto. | P5 |
| 29, 45, 53, 65 | Rinviabili: passi non atomici con conseguenze innocue (un evento che manca, un atto lasciato a scadere). | nessuno |
| 30 | Rinviabile: il guasto è fail-closed (approvazione non riconosciuta); i file di approvazione li scrive P3c. | P3c |
| 31, 32 | Rinviabili: test e docstring. | P3c |
| 33 | Rinviabile, e ormai superata: `_resume` legge i must-have una volta per `prepare` (`finalreview.py:146-147`). | nessuno |
| 34, 36 | Rinviabili: chiarezza del brief (SHA del ciclo dopo un rebase, `issue.md` assente). | P3c |
| 37, 41 | Rinviabili: casi rari, protetti dal codice per ciclo. | nessuno |
| 38, 39, 40 | Rinviabili: più severo, non meno; traccia di un riporto scartato; test. | P3c |
| 43 | Rinviabile: messaggio ripetuto. | nessuno |
| 46 | Rinviabile: accettato; la ripetizione aggiorna la stessa PR. | nessuno |
| 47 | Rinviabile: con 15 verifiche per ciclo il corpo resta sotto il limite di GitHub; il tetto complessivo serve con il blocco di P4. | P4 |
| 48 | Rinviabile: «Closes #N» in testa al corpo è la forma che GitHub riconosce. | nessuno |
| 49, 50 | Rinviabili: casi stretti (ciclo superato e oltre 8 cicli, piano illeggibile dopo `supersede`). Per la 50 basta catturare `ValueError` in `apply_act`; si può fare insieme a I-1. | P3c |
| 52, 54, 74, 76 | Rinviabili: costanti duplicate, motivo solo nell'atto, euristica fissata dal test, un solo tetto indicato. | P5 |
| 56 | Rinviabile: serve un processo morto in una finestra stretta, e il guasto è un blocco in più. | P5 |
| 60, 62 | Rinviabili: casi rari, con un messaggio da migliorare. | P3c |
| 64 | Rinviabile e senza oggetto: `git worktree remove` toglie da sé la registrazione; `prune` non serve. | nessuno |
| 68, 69 | Rinviabili: contratto con il gate (SHA nel marcatore, autore del commento). Oggi nessun commento marcato viene dal gate e il testo resta in un recinto. Da fissare. | P4 |
| 71, 72 | Rinviabili: instradamento e gravità mostrata dopo `approve finding`. | P3c |
| 78, 79 | Rinviabili: testo morto nella skill `start` e forma del comando negli agenti di P3a. | P3c |
| 81 | Rinviabile: nei ritorni anticipati il legame della sessione non serve (lavoro chiuso, `--confirm` da ripetere, rifiuto). | nessuno |

## Declined to judge

- Fiducia nel corpo della PR scritto da collaboratori dello stesso repo, come fonte del tetto in `adopt`: è una scelta della spec 12.4 e della decisione 18. Ho giudicato solo il caso dei fork (I-3).
- Nomi reali dei campi JSON di `gh` (G4) e formato di `--paginate --jq`: senza rete non si verificano.
- Semantica del gate di P4 (marcatore `<!-- tollgate-verdict`, «attenzione», ricalcolo della DoD): fuori dal perimetro di P3b.
- Percorso L2 da `spec_audit` ad `approval`, file di approvazione e avversari: appartengono a P3c.
- Uso interattivo di `/tollgate:finish` e comportamento del modello nella prova reale (Task 17): ho letto il rapporto, non l'ho ripetuto (`claude` vietato).
- Concorrenza tra due sessioni sullo stesso segnale: accettata da C21.
- Sensibilità di `patch-id --stable` agli spazi e al contesto: scelta della spec 6.5 e della decisione 17.
- Qualità dei prompt di `final-reviewer` e `finding-verifier`: ho controllato solo che siano coerenti con il formato 18.5 e con il parser.
- Prestazioni: `sync` esegue il gate dentro `finish check`, e `review prepare` rilegge il piano.

## Verdetto

**Non pronto al merge.** Le condizioni:

1. Correggere I-1, I-2, I-3 e I-4, ciascuno con il test indicato. I-3 chiude la riga 42 e I-4 la riga 57.
2. Correggere le righe 58-59 (livello di `adopt` per un autore esterno e per l'issue illeggibile) e la riga 63 (testo della spec 12.4).
3. Riportare nella rev 24 della spec il nuovo esito dei rilievi superati o non verificati (8.6 e 10), il rifiuto di `sync` con task in corso (6.5) e il filtro delle PR da fork (6.4).
4. Rilanciare `tests/run` con `python3.11` e `python3`.

I minori m1-m5 sono consigliati, perché costano poco, ma non bloccano il merge. Il resto della struttura regge: strati, transazioni, atti, intenti, testo non fidato, DoD, contratto 18.1, segnale della CLI e risorse.
