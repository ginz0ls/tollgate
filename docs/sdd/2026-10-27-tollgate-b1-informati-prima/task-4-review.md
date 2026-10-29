# Revisione Task 4 (bac69cd, «letture registrate dagli hook»)

Rischi controllati fuori dal diff (uno per rischio): (a) `tests/test_layers.py` e import di `tollgate_core` verso `tollgate_analysis` (già presente in `audits.py`, `reviews.py`, `verify.py`, ecc.): nessun ciclo né violazione; (b) ordine delle chiavi in `spikes/fixtures/hook-inputs/samples-b1.json` (`agent_id` è la prima chiave, quindi `json_str` del wrapper lo trova prima di `tool_input`/`tool_response`; i contenuti dei file letti sono in JSON con virgolette escapate, quindi `"agent_id"` dentro una lettura non combacia); (c) `runner._fail` e `CONTROL_EVENTS` (`post_lookup` non è di controllo: ogni errore dà uscita 0 con avviso); (d) `sessions.work_for_path`. Test eseguiti (background, `python3 -B`): `test_check_lookups`, `test_wrapper`, `test_layers`, `test_manifest`, `test_hook_engine`, `test_check_audit_round`: 187 test OK, nessun avviso. Albero pulito, nessun `__pycache__` nel commit.

## Aderenza

- ✅ Evento `post_lookup`: `model.py:12`, `adapter.py:14-15,41-42` (Read, Grep, WebFetch, WebSearch, `mcp__*`; non Glob); `PostToolUseFailure` non lo produce (`adapter.py` ramo Failure invariato; `test_post_lookup_kinds`, `test_failed_read_not_recorded`).
- ✅ Operazione `lookup`, `apply.OPS` = 29 (`apply.py:272-274`; `test_ops_count_is_29` e `test_lookup_op`, che asserisce riga, sessione, dedup e `ValueError` per `kind` sconosciuto).
- ✅ `_common.lookup_owner` (`_common.py:192-199`) come da brief: delega a `lookups.owner`, in più nessuna lettura a un agente di sola lettura.
- ✅ Modulo `lookup_rec` con `CHECK` identico al brief (`lookup_rec.py:14-15`); `post_bash` registra i `read_targets` come `bash_read` dalla cartella effettiva (`bash.effective_dir`, D13), solo file esistenti nel worktree, non su `PostToolUseFailure` (`lookup_rec.py:20-21`); solo `research = 1`.
- ✅ Una sola logica di cosa registrare: `lookups.observed` / `observed_bash` / `owner` (`lookups.py:56-139`), usate sia da `runner._record_lookup` (`runner.py:174-198`) sia da `lookup_rec.decide`. Nessuna duplicazione della regola di registrazione. Strati rispettati: la funzione sta nel core, `tollgate_hooks` e `tollgate_checks` importano il core; `test_layers` verde.
- ✅ `Read` fallito non conta (nessun evento d'ingresso); `WebFetch` con `code >= 400` non conta (`lookups.py:82-84`, `test_webfetch_error_code_not_recorded`); `WebFetch` solo l'URL chiesto, normalizzato (`test_webfetch_redirect_records_only_requested_url`); `WebSearch` solo `kind=search`, mai una fonte (`test_websearch_is_search_only`); MCP di documentazione `docs` col solo libraryId (`test_doc_mcp_recorded`, `test_other_mcp_not_recorded`); `Grep` solo con `output_mode == "content"` esplicito e `path` che è un file esistente (`lookups.py:75-80`; test su `grep_content_dir`, `grep_default`, `grep_files`, senza path).
- ✅ Attribuzione (Review Focus 1): `_implementer_task` (`lookups.py:115-122`) richiede task non nullo e `agent_type` del subagente uguale a quello del task `running`; un revisore (tipo diverso) non possiede letture; `row["work"] == work` impedisce l'attribuzione tra lavori diversi; sessione principale senza `agent_id` scartata con l'insieme vuoto `ATTRIBUTE_UNNAMED_TOOLS` (D1). Ripiego con insieme non vuoto: un solo implementatore vivo, non fermo, altrimenti None (tre test).
- ✅ D14: `Path.resolve()` di worktree e file prima di `normalize_path` (`lookups.py:46-56`); test con collegamento che esce, e worktree dietro collegamento nei due versi.
- ✅ `hooks.json`: matcher `…|SubagentHandback|Read|WebFetch|WebSearch|mcp__.*`, senza `Grep` (carry D5; `test_post_tool_use_matcher_has_lookups`).
- ✅ `hooks/run:50-61`: uscita anticipata per `PostToolUse` di Read, Grep, WebFetch, WebSearch, `mcp__*` senza `agent_id`, dopo il solo `cat` di stdin e il ramo `UserPromptSubmit`, prima di OFF, di `git -C` e di Python; l'elenco `UNNAMED_TOOLS` è confrontato con la costante da un test (`test_early_exit_list_matches_unnamed_tools_constant`) e il ramo con strumento nell'elenco è provato (`test_unnamed_tool_in_list_reaches_python`). `test_main_session_read_exits_early` usa un Python che uscirebbe con 7: l'uscita anticipata è davvero provata.
- ✅ Errore di registrazione informativo (spec 7.1): `event.kind` non è in `CONTROL_EVENTS`, quindi `_fail(control=False)` dà uscita 0 con avviso; `test_error_in_recording_is_informative` asserisce uscita 0 e il testo in stderr. Anche `db.open_db` fallito e `sqlite3.Error` passano dai rami di `run_hook` con `control=False`.
- ✅ Via breve (carry D5): niente `load_config` né `registry.load` (`test_post_lookup_short_path_skips_config` con mock che fallisce se chiamati); nel flusso vero tocca il subagente (`subagents.touch`, `test_short_path_touches_the_subagent`).
- ✅ Via breve e componente spento: la via breve non legge `[components]` e registra anche con `research_note` spento, mentre `lookup_rec` (registro) rispetta `component`. È coerente con il carry del Task 4 (D5), che lo prescrive e chiede di scriverlo nel report (fatto: `runner.py:177-180`, report «Dubbi»). Non è un difetto: la registrazione è una scrittura innocua che non produce rifiuti, e gli effetti sul rifiuto sono nel controllo di B1-Task 7 che rispetta l'interruttore. Il comportamento è però asimmetrico tra `Read` (sempre) e `Bash cat` (solo con componente acceso): vedi rilievo M4.
- ✅ Lavori `research = 0` non registrano (`test_legacy_work_not_recorded`, anche per Bash); `Glob` non è una lettura.
- ✅ `tests/hookkit.py`: `Lab(research=)`, `SAMPLES_B1`, `sample_b1` come da carry D4.
- ✅ Test richiesti dal brief e dal carry tutti presenti (elenco del report verificato sul diff); asseriscono contenuto (task, kind, target, agent_id), non solo l'assenza di errori.
- ✅ Misura di latenza fatta con `spikes/b1/latenza.py` e radice temporanea propria; ruling già presa sulle conseguenze (non è un rilievo).
- ⚠️ Non verificabile dal diff: i valori 250 ms / 289 ms (macchina carica diversamente al mio giro). Si veda M1 sulla validità della serie.

## Punti di forza

- Un'unica funzione per «cosa è una lettura», con firma pura (`observed(tool, tool_input, tool_response, cwd=, worktree=)`) e testabile senza DB; `owner` separato.
- Rispetto rigoroso dell'attribuzione: il test `test_read_by_other_task_not_counted` e quello del revisore chiudono il rischio 1 del Review Focus.
- Il wrapper è difensivo: nessun git né Python per la sessione principale, con test che lo provano con uno stato che farebbe fallire Python.
- Casi limite coperti: collegamenti simbolici, `..`, forme `./`, cartelle e file mancanti per Bash, `cd`, `Grep` senza path, URL non http, MCP diversi.
- Le scelte «dormienti» (insieme vuoto, Grep) sono parametrizzate, non cancellate, e provate con eventi diretti.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

- **M1 — `spikes/b1/latenza.py:~150-165` (serie `post_read_subagent`) misura il percorso di sola lettura.** Dopo l'invocazione di riscaldamento ogni `Read` dello stesso file è già in `lookups`, quindi `lookups.record` esce al `SELECT` senza `INSERT` né commit. Il «250 ms (scrive in `lookups`)» del report è la latenza del caso ripetuto; la prima lettura di un file (la più comune) ha in più una scrittura con commit. Scenario: un implementatore che legge file sempre nuovi paga più di 250 ms a lettura. Non cambia la ruling (la via breve resta), ma il numero riportato va letto come limite inferiore; correggere variando il file letto a ogni iterazione, o dicendolo nel report.
- **M2 — Preambolo duplicato tra `runner._record_lookup` (`runner.py:184-190`) e `lookup_rec.decide` (`lookup_rec.py:22-29`).** La regola «lavoro non nullo, `research`, worktree esistente» è scritta due volte (la regola di cosa registrare no). Con il registro in produzione fuori gioco per `post_lookup` il rischio è la divergenza futura: chi cambia una condizione ne dimentica una. Una funzione di core `lookups.recordable_work(work)` basterebbe.
- **M3 — `runner._record_lookup` usa `cfgmod.DEFAULTS["review"]["stale_minutes"]` (`runner.py:192`) e non `ctx.stale_minutes` della configurazione del repo.** Conta solo nel ripiego senza `agent_id` (oggi spento), ma il valore configurato dall'utente è ignorato quando si accenderà. Segnalarlo con un commento accanto alla costante, o leggere la configurazione solo in quel ramo.
- **M4 — Mancano due test che fissano il comportamento dichiarato.** Nessun test asserisce che la via breve registra con `[components] research_note = false` (è la deroga voluta dal carry: va fissata, altrimenti un refactor la cambia senza accorgersene), né che `lookup_rec` (post_bash) non registra a componente spento. In più `lookup_rec.decide` per `post_lookup` non è raggiungibile dal runner in produzione (il runner esce prima del registro); è coperto solo da `test_grep_direct_event_through_the_module`. Va bene per il carry, ma il docstring (`lookup_rec.py:3-5`) lo dice solo a metà: aggiungere i due test.
- **M5 — La via breve non esegue `sessions.touch` né `offlog.import_log`** (`runner.py:~225` salta il corpo comune). Per una lettura di subagente è scelta voluta per la latenza e il `touch` del subagente c'è; ⚠️ non verificabile dal diff se qualcosa dipende da `sessions.touch` aggiornato dalle letture (nessun uso nei test del Task 4). Inoltre trova il lavoro dalla sola cartella (`sessions.work_for_path`), mentre `lookup_rec` usa `governing_work` (il lavoro legato alla sessione): se un implementatore avesse `cwd` fuori dal worktree, la via breve non registra. Prescritto dal carry («lavoro dalla cartella dell'evento»), da tenere presente per il Task 9.
- **M6 — Rifinitura.** `runner.py` importa `tollgate_analysis` con due righe (`import bash` e `import research`) invece di una; `tests/test_check_lookups.py` ha un parametro `tstate` mai usato in `start_impl`.

## Valutazione

**Conformità alla spec/brief/carry:** Conforme (✅). Nessun requisito mancante né in più; la deroga della via breve a `[components]` è quella prescritta dal carry.

**Qualità del task:** **Approvato.** **Motivo:** una sola regola di registrazione condivisa, strati rispettati, attribuzione e uscita anticipata provate con test che asseriscono davvero; errori di registrazione sempre informativi. Restano solo rifiniture minori (M1-M6), nessuna da fare prima di proseguire.
