# Task 10: revisione (b3b875f..d03fc33, solo documenti)

Verdetto: **approvato**. Nessun Critical, nessun Important. Tre Minor.

## Perimetro
Il diff tocca quattro file, tutti documenti ammessi: spec del nucleo (50 righe), piano principale di C (14), piano C1 (8, solo tabella «Copertura» più una nota), progetto di C (2, la sola riga «Avanzamento» con la riga vuota). Nessun codice, nessun `docs/verifiche/`, nessun profilo. La spec non è riscritta fuori dalle sezioni richieste. `git status` pulito. `python3 -B -m unittest tests.test_docs`: 7 OK. Nessun percorso della macchina, nome utente o host nel diff (grep su `USER`, `/home/`, `ginz0ls`: zero risultati).

## Parte 1: aderenza ai requisiti

### Spec rev 36 contro il codice di `bin/`
Ho controllato ogni frase nuova sul codice del ramo.

- **6.1 taglia**: `worksize.propose` (`worksize.py:45-56`) ha le regole e le costanti come scritte (`MEDIUM_MIN_TASKS` 4, `MEDIUM_MIN_AREAS` 2, più fette → `large`, L2 → `medium`). `Signals(level, tasks, areas, slices)` e `Proposal(size, reason)` corrispondono. `areas` conta i verticali distinti (`worksize.py:59`). Le tre forme della riga sono in `preview` (`worksize.py:81-95`), e il ramo «strada vera» vale solo fuori da L2, come dice la spec. `sizes.decide` scrive un evento a ogni chiamata (`sizes.py:30-47`). `_write` riscrive quando cambia la taglia o chi decide (`sizes.py:17`, D12). `set_by_user` ha `cause = "act"`, `by = "user"`, `signals` nullo, `confirmed` vero (`sizes.py:57-63`). Le cause sono coerenti: `start.py:510`, `adopt.py:425/432/458`, `l2acts.py:179/252`, `hooks/apply.py:43` (solo quando il livello sale) e `:55`.
- **8.4**: `approve size` (`actapply.py:236-247`) rifiuta una taglia sconosciuta o un motivo mancante. `approve spec` scrive `slices` e decide nello stesso `db.tx` prima di `set_phase` (`l2acts.py:176-186`), con `confirmed=slices > 1`. `approve plan` decide dentro `if work["plan_sha"] != plan_blob`, subito dopo `register_plan` (`l2acts.py:241-255`, D10 e D19).
- **3.1 `ruling add`**: `RULING_TEXT_MAX` 1000, `HEREDOC_END` `RULING_FINE`, etichette senza distinzione di maiuscole, `perche`/`perché`, campo ripetuto o mancante e testo iniziale come rifiuto, uscita 2 senza lavoro o con un task inesistente, messaggio `ruling registrata (evento <seq>)`, `--by` agent/user (`ruling_cmd.py:18-112`). Lettura di stdin a `4 * 3 * 1000 + 1` (`cli.py:455`). D4: `cli_calls.py:62-78,151` nega `--by user`, `--by=user` e le abbreviazioni (`--b` in su), e lascia passare `--by agent` e l'assenza di `--by`.
- **3.1 `snapshot`**: i campi elencati coincidono con `snapshot._work` (`snapshot.py:66-78`). Il ramo senza DB sta prima di `open_db` e non crea niente (`cli.py:512-517`). `turn` viene da `turn.waiting_on` (`turn.py:19-25`). D7 è vero, perché il ramo con DB passa da `open_db`.
- **3.2 / 7.1 / 7.2**: `pre_question` e `post_question` sono in `EVENT_KINDS` (`model.py:10`) e fuori da `CONTROL_EVENTS` (`model.py:11`). `hooks/run:49-50` mette `CONTROL=no`. `runner._asks_user` calcola `control` in testa (`runner.py:202-213`). `hooks.json` e `adapter.py:11,15,50` hanno il matcher e la traduzione di `PostToolUseFailure`. `stops.py` ha i limiti 300/4/4 e le fonti `tool_response`/`tool_input`/`failure`/`none`, e `tool_use_id` nullo. `session.py` registra `session_start` con `{source}` e il lavoro anche appena legato (`session.py:26-27`).
- **7.2 `SubagentStop`/18.4 `cost`**: l'evento sta in `subagents.finish` (`subagents.py:96-102`), solo con un uso non vuoto (D3). I campi sono quelli della spec. `tokens` è `input + cache_creation + output` (`_common.py:76-83`, D21).
- **11.4**: default `events_days = 0` e `lookups_days = 180` (`config.py:92`), tetto 36500 con `ConfigError` (`config.py:126-129,188`). `archive_and_prune(conn, state, now, days)` scrive `archive/events-<primo>-<ultimo>.jsonl` e poi cancella `seq <= ultimo AND at < limite` (`events.py:81-101`). `housekeeping.py:39-42` usa `events_days > 0` per gli eventi e `lookups_days` per le letture. `prune_events` non esiste più.
- **12.2**: i vincoli `CHECK` di `SCHEMA_V7` (`db.py:199-205`) sono quelli scritti.
- **18.4**: la riga `**Tipi:**` coincide con `events.EVENT_TYPES`: verificato con uno script, insiemi uguali (38 nomi, differenza simmetrica vuota). `test_docs` lo fissa.
- **Piano principale, sezione 3**: `Signals`, `Proposal`, `preview`, `sizes.decide(conn, work, signals, *, cause, confirmed, now, session) -> str` (nel codice `confirmed` ha un default, il che non rende falsa la frase), `set_by_user`, `snapshot.build`, `archive_and_prune` e `waiting_on` esistono con quei nomi.

### Altre richieste del brief
- **Sezione 20**: la riga 36 elenca le dodici decisioni e i ruling che toccano la spec (D3, D4, D5, D7, D10, D19, D12, D16, D20, D21), più i limiti scritti. Controllati uno per uno contro il ledger: D1, D2, D6, D8, D9, D11, D13-D15, D17 e D18 non toccano la spec (test, script, pagina d'uso, metodo). Nessun ruling che cambia la spec manca.
- **Scelte «utente» del progetto di C**: il diff aggiunge solo la riga «Avanzamento» (2 righe aggiunte, nessuna cancellata).
- **Piano principale**: riga «Stato» in testa (21 novembre) e riga C1 con «**Stato:** eseguita sul ramo `c1-tracciamento-locale`, in attesa del merge». «Unita» non compare riferita a C1. La sezione 3 ha i nomi reali. La sezione 8 ha una sola frase di rimando al triage, senza elenco di minori (ruling del Task 10). I rimandi alla spec dicono «revisione 35 (36 dopo C1)».
- **Tabella «Copertura»**: ho verificato con `grep "def <nome>"` tutti i nomi nel testo del piano. Esistono tutti nei file indicati, compresi `test_adopt_decides_size_at_start`, `test_minimal_gets_defaults` (asserisce `events_days` 0 e `lookups_days` 180), `test_housekeeping_never_prunes_with_zero`, `test_approve_finding_emits_finding_event` (`tests/test_actapply.py`) e `test_user_decision_written_only_by_set_decision` (`tests/test_reviews.py`). I vecchi nomi restano solo nella nota di correzione. La nota è chiara e dice che gli altri nomi esistono come scritti.
- **Rapporto della prova**: i dati citati (esito riuscita, due `size_decided`, due `cost`, 0,93 USD, nessun addebito) coincidono con `docs/verifiche/2026-11-20-c1-prova-flusso.md`.

## Parte 2: qualità

### Minor
1. **Intestazione e sezione 20 non coincidono sul ruling D19.** L'elenco dell'intestazione della rev 36 (spec, riga 3) cita «D3, D4, D5, D7, D10, D12, D16, D20, D21». La riga 36 della sezione 20 cita anche D19 (ripetizione di `approve plan`). È solo coerenza interna. Va aggiunto D19 all'intestazione.
2. **7.2, riga `PreToolUse` di `AskUserQuestion`: manca un comportamento reale.** `stops.decide` non registra nessun `stop_asked` se l'input non ha domande leggibili (`stops.py:55-57`, ritorna `[]`). La riga dice solo che «registra `stop_asked`» e che senza `tool_use_id` registra con `tool_use_id` nullo. Un `PostToolUse` invece registra sempre `stop_answered`. La frase non è falsa, ma incompleta.
3. **6.1, «Quando»: manca `adopt` per le cause `plan` e `approve_spec`.** `adopt` decide con causa `start` (a livello base), con `approve_spec` e `confirmed` quando c'è l'approvazione della stessa issue a più fette (`adopt.py:425-433`), e con `plan` alla registrazione del piano (`adopt.py:458`). La spec dice «in `adopt` (causa `start`…)». Le altre due strade sono coperte da frasi più in basso («Un'approvazione di un'altra issue…», «alla registrazione del piano»), ma un lettore non vede che `adopt` può produrre tre eventi.

## Rischi controllati e non verificabili
- Forma reale di `tool_response` di `AskUserQuestion`: non verificabile in locale; la spec lo dice (limite scritto, prova di C6). ⚠️
- Nessuna suite lanciata (regole di cautela): ho eseguito solo `tests.test_docs` e controlli mirati su codice e nomi dei test.
