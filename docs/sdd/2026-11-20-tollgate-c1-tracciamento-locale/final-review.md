# Revisione finale del ramo `c1-tracciamento-locale` (055dc80..d03fc33)

Revisore: opus, sola lettura. Letti: il pacchetto del diff (codice di `bin/`, `hooks/`, `tests/`, `spikes/`, documenti; le evidenze a campione), `decisions.md`, `review-focus.md`, `coverage.md`, `global-constraints.md`, `fatti-verificati.md`, tutte le righe `Ruling:`, `Prova:` e `minor (deferred)` di `progress.md`, il rapporto della prova e `registro-1/` delle evidenze, il progetto di C (sezioni 2, 3, 6, 10, 14), il piano principale di C (le righe cambiate e le sezioni 1-3, 7, 8) e le righe nuove della spec del nucleo rev 36, confrontate con il codice.

Controlli eseguiti (solo test mirati e sonde pure, nessuna suite completa):
- `python3 -B -m unittest` su `test_check_stops`, `test_snapshot`, `test_sizes`, `test_worksize`, `test_ruling_cmd`, `test_turn`, `test_events`, `test_report`, `test_subagents`, `test_config`: 146 test, OK (con `PYTHONWARNINGS=error::ResourceWarning`);
- `test_wrapper.WrapperTest.test_ask_user_question_never_denied_by_failure`, `test_hook_engine.RunnerTest.test_ask_user_question_never_denied_by_runner_failure`, `test_hook_engine.AdapterTest.test_adapter_maps_ask_user_question`, `test_check_session`, `test_check_cli_calls`: 43 test, OK;
- sonda `W/sonda-finale/sonda_ruling_size.py` (funzioni pure, nessuno stato): etichette delle ruling e righe di `worksize.preview`;
- `/usr/bin/grep -raF` di `$(id -un)` e `$(hostname)` sui 121 file aggiunti o modificati dal ramo (evidenze comprese): 0 file; forme di token (`sk-ant-`, `gh?_`, `github_pat_`, `AKIA`) con `/usr/bin/grep -raE`: 0 file. Nelle evidenze restano percorsi con `USER` (come nelle prove di B).

## 1. Verdetto

**Approvato per il merge**, dopo il giro di correzione dei minori che la tabella di triage marca «da correggere» (tutti a basso costo). Nessun rilievo blocca.

**0 critical, 0 important, 6 minor** (rilievi nuovi miei), più un punto **da verificare** a mano (V1), senza gravità.

I punti del brief cercati apposta, con l'esito:
- hook che nega su `AskUserQuestion`: no. Il wrapper (`hooks/run:48-51`) e `runner.run_hook` (`runner.py:213`, `_asks_user`) mettono `control` falso prima di ogni ramo che può negare; dopo `to_event` vale `event.kind in CONTROL_EVENTS`, falso per `pre_question`; `stops.decide` non nega e non inietta; `adapter.render` non dà mai `permissionDecision allow`. I test del wrapper (Python assente, uscite 1 e 127, eccezione, scadenza) e del runner (JSON troncato, `_Timeout`, errore generico) passano, con il controllo negativo su `Bash` che resta 2;
- potatura senza archivio: no. `events.archive_and_prune` legge, scrive e cancella in un solo `BEGIN IMMEDIATE`, cancella solo `seq <= ultimo` con `at < limite` (lo stesso insieme letto), un errore di scrittura risale prima del `DELETE`; `seq` è `AUTOINCREMENT`, quindi i nomi dei file non si ripetono; `prune_events` non esiste più;
- taglia che scende da sola o diventa grande senza un sì: no (`worksize.preview`: `applied = current` se il rango attuale è pari o superiore; `large` solo con `approve_spec` confermato o con l'atto dell'utente; `adopt` solo con il `spec-approval.md` della stessa issue);
- tipo fuori da `EVENT_TYPES` o busta con `v` diverso da 1: no (`record_event` rifiuta, `ENVELOPE_VERSION` invariato);
- testo libero o dati della macchina nella fotografia: nessun testo libero; `repo_key` può essere un percorso della macchina con un `origin` locale (F6);
- subagente che non può registrare una ruling, o comando del coordinatore che diventa permesso: no (`ruling` non è in `_COORDINATOR_ONLY`; solo `--by user` è negato; `_COORDINATOR_ONLY` invariato);
- costo che conta due volte o non coincide con `subagent_stop`: no (un messaggio per id, vale l'ultima riga; `tokens` del `cost` è la stessa variabile di `subagent_finish`; la prova lo conferma: 49528 e 32293 in tutti e due gli eventi). Il costo per task però non comprende i revisori del task (F1);
- test che dipende in silenzio dalle variabili della macchina: nessuno trovato tra i test nuovi (stato da `TempState`/`FlowLab`, host finto `macchina-prova`, `socket.gethostname` sostituito dove si confronta);
- frase della spec o del piano che non corrisponde al codice: tre già nel ledger (Task 10) e F5;
- token, nome utente o host nelle evidenze e nei file nuovi: nessuno.

## 2. Rilievi

**F1 — minor.** `bin/tollgate_core/snapshot.py:55-69` (`_cost`), `bin/tollgate_core/subagents.py:96-101`, `docs/uso/gestionale.md:46` e `:58-63`.
- **Cosa.** `cost.by_task` somma solo i `cost` con `task` non nullo, e il `task` viene dalla riga del subagente: il revisore del task (`tollgate:task-reviewer`) ha `task` nullo, quindi il suo costo entra nel totale del lavoro ma non nel task che ha rivisto. Nella prova: 32293 token su 81821 (il 39%) fuori da `by_task` (`registro-1/snapshot.json`, `events.jsonl` seq 24).
- **Perché.** Il progetto 6 chiede il costo «per subagente, per task e per lavoro»; un gestionale che legge `by_task` come «quanto è costato il task» sottostima ogni task. La pagina d'uso non lo dice (lo dice solo il rapporto della prova), e gli eventi `cost` già registrati non portano il task del revisore: l'informazione manca anche dalla storia.
- **Come correggere.** Il più economico: una riga nei «Limiti noti» di `gestionale.md` («`by_task` conta i subagenti legati a un task, cioè gli implementatori; i revisori del task stanno solo nel totale»). Meglio, a costo basso: in `task_verdict.decide` il task è noto (`found = work, task`), quindi l'operazione `subagent_finish` può portare un `cost_task` che `subagents.finish` usa per `data.task` del solo evento `cost` (la riga del subagente e `subagent_stop` restano come sono), con un test.

**F2 — minor.** `bin/tollgate_flow/ruling_cmd.py:22-23`.
- **Cosa.** L'etichetta `perchè:` (accento grave, la grafia sbagliata più comune in italiano) non è riconosciuta: la riga diventa la continuazione del campo `cosa` e il rifiuto dice «manca il campo «perché:»», anche se l'autore crede di averlo scritto. Verificato con la sonda (`perchè` e `Perchè` → rifiuto; `perché`, `perche`, `PERCHÉ` → ok).
- **Perché.** Nessuna perdita (è un rifiuto), ma un agente può ripetere lo stesso errore e non registrare la ruling.
- **Come correggere.** `perch[eéè]` nell'espressione e `"perchè": "why"` in `_FIELD`, con `unicodedata.normalize("NFC", line)` prima del confronto (chiude anche il minore rinviato del Task 5 sull'NFD); un caso nel test di `parse_text`.

**F3 — minor.** `bin/tollgate_hooks/apply.py:36-44` (`_level`), `bin/tollgate_checks/_common.py:333-334`.
- **Cosa.** Quando il livello sale (L1 → L2) l'operazione `level` chiama `sizes.decide` e la taglia può salire da piccolo a medio, ma la riga che `decide` restituisce si perde: l'utente vede «il lavoro sale a L2», non la taglia nuova.
- **Perché.** Il progetto 3.2 («Crescita»: «tollgate propone la taglia sopra») e la regola della riga («la scrive in una riga, con il motivo»): la taglia cambia in silenzio, e l'evento c'è solo nello stato. Il piano (decisione 2) non chiede la riga per la causa `level`, quindi non è un difetto rispetto al piano, solo rispetto al progetto.
- **Come correggere.** In `level_records` comporre la riga con la funzione pura `worksize.preview` (segnali `new`, task registrati, 0 aree, `slices` o 1) e aggiungerla al testo dell'iniezione esistente, come fa `post_edit._plan`; un test che la riga iniettata coincide con l'evento.

**F4 — minor.** `bin/tollgate_core/config.py:126-129`, `bin/tollgate_flow/housekeeping.py:30`, `:39-42`; spec 11.4 (riga 1417); `docs/uso/gestionale.md:68`.
- **Cosa.** Le tre chiavi di `[retention]` accettano 0 (ruling D5), ma lo 0 vuol dire tre cose diverse: `events_days = 0` è «mai»; `lookups_days = 0` cancella subito le letture di tutti i lavori chiusi; `retention_days = 0` cancella a ogni `start` tutti i file di `logs/` e `ctx/`. Inoltre il limite è del `tollgate.toml` del repo che parte, mentre il DB è uno per macchina: un repo con `events_days = 30` archivia e toglie dal DB gli eventi di tutti i repo della macchina.
- **Perché.** Chi legge «0 = mai» per gli eventi può scrivere `lookups_days = 0` per tenere le letture, e le perde. La portata del limite su tutta la macchina c'era già prima di C1 (fatti verificati), ma ora la pagina per il gestionale promette la storia completa e non dice che un solo repo può accendere la potatura per tutti (l'archivio la tiene, quindi niente va perso).
- **Come correggere.** Una frase nella spec 11.4 e in `gestionale.md`: «0 vuol dire "mai" solo per `events_days`; per `lookups_days` e `retention_days` vuol dire "subito"» e «il limite vale per gli eventi di tutti i repo dello stato della macchina». In alternativa (scelta di chi costruisce) trattare 0 come «mai» anche per `lookups_days`.

**F5 — minor.** Spec del nucleo, riga 1532 (12.2, «Migrazione 7»), e piano C1, decisione 1 (riga 79).
- **Cosa.** «la fotografia (3.1) li mostra «non calcolata»»: la fotografia dà `"size": null`, nessun testo «non calcolata» (`snapshot.py:80`, `test_snapshot_pre_c1_work`).
- **Perché.** Un gestionale che segue la spec cercherebbe una stringa che non arriva. `gestionale.md:61` dice giusto («`size` è nullo»).
- **Come correggere.** Nella spec: «la fotografia (3.1) li mostra con `size` nullo».

**F6 — minor.** `docs/uso/gestionale.md:48`; `bin/tollgate_core/snapshot.py:78`; `bin/tollgate_core/paths.py:68-83`.
- **Cosa.** La pagina dice che «una fotografia si può quindi mostrare ovunque», ma `repo_key` è l'URL di `origin` normalizzato: con un `origin` su un percorso locale è un percorso della macchina. Nella prova: `"repo_key": "/tmp/tollgate-b1/origin"` (`registro-1/snapshot.json`); con un `origin` nella cartella dell'utente conterrebbe il nome utente.
- **Perché.** Il punto del brief «dati della macchina nella fotografia». Con un `origin` su GitHub (il caso d'uso vero) `repo_key` è `github.com/<proprietario>/<repo>`, senza utente né porta: l'impatto resta ai repo con un remoto locale.
- **Come correggere.** Una riga nei «Limiti noti» di `gestionale.md` («`repo_key` è l'`origin` normalizzato: con un remoto locale è un percorso della macchina»). C4, che porta la fotografia su GitHub, deve comunque filtrare `repo_key` con la lista «non va mai» del progetto 7: lo si può scrivere tra i rinvii della sezione 8.

**V1 — da verificare (senza gravità).** `hooks/hooks.json:6` (il matcher di `PreToolUse` riceve `AskUserQuestion`).
- **Il fatto che manca.** Nessuna prova del ramo mostra una domanda diretta vera con un hook `PreToolUse` su `AskUserQuestion` acceso: con `claude -p` lo strumento non c'è (prova del Task 9), e la prova dal vivo è rinviata a C6. Dopo il merge l'hook gira nelle sessioni interattive dell'utente da subito, prima di C6. Il codice non può negare né iniettare un `allow`; resta da vedere che Claude Code 2.1.329, con un hook `PreToolUse` che esce con 0 e senza uscita su quello strumento, mostri la domanda e consegni le risposte come senza hook.
- **Come verificarlo.** Prima o subito dopo il merge, una sessione interattiva in un repo di prova con tollgate attivo: far fare al modello una domanda con `AskUserQuestion`, rispondere, e guardare che la risposta arrivi al modello e che `tollgate events` abbia `stop_asked` e `stop_answered` con le risposte (e quale `source`). Costo: pochi minuti, nessuna chiamata a pagamento oltre la sessione. Se la domanda si rompe, `/tollgate:off` la ripristina subito, e il rimedio è togliere `AskUserQuestion` dal matcher di `PreToolUse` (le domande si leggerebbero solo a `PostToolUse`).

## 3. Triage dei `minor (deferred)` del ledger

| # | Task | Rilievo | Esito | Motivo |
|---|---|---|---|---|
| 1 | 1 | `test_new_event_types_recorded` non controlla che `export_events` restituisca `data` intatto | nessuna azione | `export_events` è generico e invariato, e i test della fotografia e della prova leggono già `data` degli eventi nuovi. |
| 2 | 2 | `fsutil.write_atomic` non fa `fsync`: dopo un'interruzione di corrente l'archivio può mancare con il `DELETE` già durevole | da correggere | È il Review Focus 2 e il rimedio è piccolo: un `fsync` del file (e della cartella) nell'archivio prima del `DELETE`, senza toccare gli altri chiamanti dell'helper, con un test che lo controlla con un mock di `os.fsync`. |
| 3 | 2 | import `fsutil` inutile nel sottoprocesso di `ConcurrencyTest.test_three_writers` | da correggere | Una riga di test, nessun rischio. |
| 4 | 2 | nessun test con due processi veri su `archive_and_prune` né con un archivio già presente con lo stesso nome | nessuna azione | Il lucchetto è `db.tx` (`BEGIN IMMEDIATE`), già provato con più processi, e con `seq` `AUTOINCREMENT` lo stesso nome vuol dire lo stesso intervallo di eventi immutabili, quindi un file uguale. |
| 5 | 2 | `archive_and_prune` carica in memoria tutte le righe; un `archive/` con permessi più larghi non si corregge | nessuna azione | A circa 335 byte per evento anche centomila eventi sono pochi MB, e `archive/` sta nella cartella di stato già a `0700`. |
| 6 | 3 | operazione `plan` in due transazioni: se `decide` fallisce dopo `register_plan` mancano l'evento della taglia e l'iniezione «piano registrato» | rinviato | Serve un errore di SQLite proprio tra le due chiamate, e il rimedio (`register_plan(advance=False)` e `decide` in un `db.tx`, `set_phase` fuori) cambia l'ordine della fase in un punto delicato: meglio con il lavoro sul piano di C5. |
| 7 | 3 | in `adopt` la taglia «start» usa il livello prima del tetto: con un tetto che abbassa il motivo dice «livello L2» | da correggere | Non è solo il motivo: un lavoro adottato con tetto L1 resta medio per sempre (la taglia non scende), e basta decidere la taglia dopo il passo del tetto leggendo il livello dal DB. |
| 8 | 3 | in `approve_plan` la riga della taglia sta dopo «poi /tollgate:execute.» | da correggere | Riordino di una riga, coerente con `approve_spec`, dove la taglia sta prima di «Committa…». |
| 9 | 3 | manca un test diretto dell'operazione `level` con un livello uguale o più basso | da correggere | Un test corto che fissa il ramo «non sale, non decide» di `_level`. |
| 10 | 3 | TDD non stretto sui punti di chiamata | nessuna azione | Riguarda il processo; i test asseriscono il comportamento e sono nel ramo. |
| 11 | 4 | un ritentativo di `approve spec` dopo un errore di `set_phase` registra un secondo `size_decided` | nessuna azione | Evento doppio con la taglia giusta, solo dopo un errore raro: è storia, come una ruling ripetuta (decisione 5). |
| 12 | 4 | `tests/test_check_acts.py`: una riga di `test_refused_forms_are_not_recorded` oltre 100 caratteri | da correggere | Una riga da spezzare. |
| 13 | 4 | nessun test che `approve size grande` lasci `slices` invariato e non proponga le issue | da correggere | È il contratto di C5 (piano principale, sezione 3: solo `slices > 1` autorizza le fette) e un test lo fissa con poco. |
| 14 | 4 | il sì alle fette su una taglia fissata dall'utente lascia `size_by = 'rules'` | nessuna azione | È ciò che dicono la decisione 2, la ruling D12 e la spec rev 36, e il progetto 3.2 fa di `approve spec <n>` il sì dell'utente: confermato. |
| 15 | 5 | nessun RED registrato (test scritti dopo il codice) | nessuna azione | Processo dichiarato; i test ci sono e il giro di correzione ha registrato il RED di I1. |
| 16 | 5 | `cli_calls.py:95`, `name != "-"` ridondante con `len(name) >= 3` | da correggere | Togliere una condizione morta, nessun rischio. |
| 17 | 5 | etichette con «é» in forma NFD non riconosciute | da correggere | Si chiude con la stessa modifica di F2 (normalizzazione NFC delle righe). |
| 18 | 6 | `_asks_user`/`json_str` dipendono dall'ordine delle chiavi (`tool_name` prima di `tool_input`) | rinviato | L'ordine reale dell'input si vede solo dal vivo (C6), il wrapper fa la stessa assunzione da B, e il caso guasto richiede un'inversione delle chiavi, uno strumento con una chiave `tool_name` e insieme un errore dell'hook. |
| 19 | 6 | nessun test che `Bash` con un `tool_name` annidato resti un controllo | da correggere | È il lato di sicurezza della stessa regola: un caso in `test_ask_user_question_never_denied_by_runner_failure`. |
| 20 | 6 | `session.py`: il campo `source` di `session_start` non è controllato né tagliato | da correggere | Tenerlo solo se è una stringa e tagliarlo (per esempio a 32 caratteri), come fa `stops._text`. |
| 21 | 6 | `stops._answers`: il taglio a 300 caratteri può fondere due chiavi uguali nei primi 300; un valore non stringa diventa `""` | nessuna azione | Due domande dello stesso turno uguali per 300 caratteri non sono realistiche, e il taglio è la regola scritta della decisione 4. |
| 22 | 5 | riga molto lunga nel caso nuovo di `tests/test_ruling_cmd.py` | da correggere | Una riga da spezzare. |
| 23 | 7 | la formula `input + cache_creation + output` è scritta due volte (`report.py`, `_common.py`) | da correggere | Un helper in `report` (per esempio `new_tokens(usage)`) usato da tutti e due toglie la seconda copia. |
| 24 | 7 | `_readonly` e l'implementatore senza lavoro passano `tokens = 0` senza trascrizione (prima `None`) | da correggere | Passare `None` quando l'uso è `None` in quei due rami (il ramo del tetto resta con 0) tiene distinti «non so» e «zero» nella storia, con poco. |
| 25 | 7 | `test_user_decision_written_only_by_set_decision` cerca il testo esatto `"SET user_decision"` | da correggere | Un'espressione regolare `SET\s+user_decision` (anche su più righe) rende la guardia della decisione 6 robusta. |
| 26 | 7 | `test_unreadable_path_has_no_usage` usa una cartella, non un errore a metà lettura (che `_messages` non prende) | nessuna azione | Comportamento di prima di C1; un errore di I/O a metà file in un hook informativo diventa un avviso, non un diniego. |
| 27 | 8 | `snapshot._questions` rilegge tutte le `stop_answered` del DB per ogni lavoro | da correggere | Con gli eventi che non si cancellano più la scansione cresce; calcolare l'insieme una volta in `build` è una modifica di poche righe. |
| 28 | 8 | con `events_days > 0` gli eventi archiviati escono dal DB, quindi `cost.tokens`, `by_task` e `last_event_at` possono scendere o diventare nulli; la pagina non lo dice | da correggere | Una riga nei «Limiti noti» di `gestionale.md`. |
| 29 | 8 | la misura in `gestionale.md` non nomina il percorso `docs/verifiche/evidenze/eval-b8/`, i tre stati usati né lo schema 6 | da correggere | Rende la misura ripetibile con una frase. |
| 30 | 8 | `cli.py` chiama `socket.gethostname()` in due rami e ricompone a mano la busta vuota | nessuna azione | Prescritto da D15 e innocuo. |
| 31 | 9 | l'intestazione di `run-b1-flow.sh` e il modo `controlla` non nominano i due file nuovi di `registra` (`B1_FLOW_EVIDENCE` è nominata solo tra le uscite) | da correggere | Una riga nell'elenco di `registra` dell'intestazione. |
| 32 | 9 | `eventi-c1` riduce un `cost` con `data` malformato a `tokens: null, by_model: []` senza avviso | nessuna azione | Strumento della prova; il valore nullo nell'evidenza è già un segnale leggibile. |
| 33 | 9 | il rapporto non nomina i due `veto` del passo1 (seq 4 `coordinator`, seq 5 `plan_check`) | da correggere | Una riga che dice che sono voluti evita che un lettore li prenda per un difetto. |
| 34 | 9 | «restano solo i token e i nomi dei modelli» vale per `eventi-c1.jsonl`; `events.jsonl` ha il dettaglio | da correggere | Una frase inesatta in un rapporto di evidenze. |
| 35 | 9 | «anonimizzati 8 file» è ambiguo (la cartella ne ha 41) | da correggere | «8 file modificati dall'anonimizzazione». |
| 36 | 9 | il rapporto non cita l'esito di `claude plugin validate` (`validate/validate-1.txt`) | da correggere | Una riga con l'esito. |
| 37 | 10 | l'intestazione della rev 36 non cita D19 tra le ruling | da correggere | La riga 20 la nomina già («D10 e D19»): allineare l'intestazione. |
| 38 | 10 | la riga 7.2 su `PreToolUse` di `AskUserQuestion` non dice che senza domande leggibili `stop_asked` non si registra (`stops.py:55-57`) | da correggere | È una frase della spec che non corrisponde al codice. |
| 39 | 10 | in 6.1 «in `adopt` (causa `start`…)» omette che `adopt` decide anche con le cause `plan` e `approve_spec` | da correggere | Come sopra: la spec deve dire tutti e tre i punti (`adopt.py:421-463`). |

Totale: 26 da correggere, 2 rinviati, 11 nessuna azione. Per la sezione 8 del piano principale («Rinvii dalle fette chiuse»): le righe 6 e 18, più, se la si vuole lì, la nota di F6 per C4 (`repo_key` sotto la lista «non va mai»).

## 4. Le scelte del piano marcate «mia scelta» e le ruling

- **Soglie delle taglie e «grande solo con un sì».** Reggono: 4 task o 2 aree per il medio sono costanti con i loro test; `large` solo da `approve spec <n>` con `n > 1` (o dall'atto dell'utente) è proprio il sì del progetto 3.2, e un piano L1 con `## Fette previste` resta medio con la riga che dice la strada vera. Nessuna contestazione. Un'osservazione: la taglia sale anche col livello, ma senza riga (F3).
- **Costo in token per modello, senza dollari.** Regge ed è fedele al progetto 6 («senza inventare prezzi»); `by_model` tiene `cache_read` per chi darà un prezzo. Il «cumulativo per agente» non si è potuto osservare (nessuna ripresa nella prova): resta da guardare in C6. Il costo per task va completato con i revisori o scritto come limite (F1).
- **Fermate dagli hook di `AskUserQuestion`.** La scelta di leggerle dal codice è giusta, e la doppia protezione wrapper + `runner` è costruita bene. Resta il dubbio dal vivo (V1) e la forma di `tool_response` (ruling D16, già accettata come costo).
- **`events_days = 0` come «mai» e l'archivio.** Regge ed è il progetto 6. Va solo scritto che lo 0 non vale «mai» per le altre due chiavi e che il limite di un repo vale per tutto lo stato della macchina (F4).
- **Forma della fotografia e di «a chi tocca».** Regge: niente testo libero, versione, campi nuovi senza cambiare `v`; `spec_audit` contato `agent` è una semplificazione scritta e affinabile in C4. Per `repo_key` vedi F6.
- **Ruling del controller.** Nessuna da contestare. D4 (negare `--by user` ai subagenti) e D21 (togliere `prune_events`) migliorano il piano; D3, D10, D12, D19 chiudono casi limite veri; la ruling sulla sezione 8 dopo il triage è corretta rispetto alle istruzioni. D5 ha un effetto collaterale solo di documentazione (F4).

## 5. Osservazioni positive

- La riga della taglia e l'evento nascono dalla stessa funzione pura (`worksize.preview`), e l'iniezione del piano usa il livello della stessa modifica: coincidono per costruzione, e la prova lo mostra.
- Il «mai negare una domanda» è difeso in due strati, con test che fanno anche il controllo negativo su `Bash`.
- L'archivio prima della potatura in una sola transazione, con `prune_events` tolta: non resta nessuna primitiva che cancella senza archiviare.
- `transcript_cost` legge la trascrizione una volta e dà gli stessi token a budget, `subagent_stop` e `cost`.
- Il comando delle ruling tiene il testo libero fuori dagli argomenti di Bash (heredoc citato), e il test D11 prova che il corpo non viene analizzato come comando.
- La fotografia ha un test che scorre tutte le chiavi e cerca un segreto di prova; la prova reale ha numeri che quadrano tra eventi, fotografia e rapporto.
- Evidenze pulite: nessun nome utente, host o forma di token nei 121 file del ramo.
