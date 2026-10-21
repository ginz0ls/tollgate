# Revisione Task 6: report dei giri a SubagentStop (ff9de1b..e095d4a)

### Aderenza
- ✅ `audit_round.py` (ordine 15, `component: None`): riga JSON con `parse_round_json`, `outcome` calcolato dall'hook, veti al più 2 poi `subagent_finish` + `needs_you` con i soli nomi dei problemi (`auditrules` non mette valori nei problemi; test `reason_has_no_raw_values`), manomissione con `readonly_check` → `tampered_records`, componente spento → solo `subagent_finish`. `subagent_finish` precede sempre `audit_report` (D13).
- ✅ Un solo proprietario per agente (rischio 1): `subagent_stop.py:~71` salta se `awaiting_audit`; i tipi dei tre agenti sono in `review.readonly_agents` (`config.py:73-75`), quindi il ramo salta davvero. Rami: valido, non valido (2 veti + chiusura), manomesso, componente spento → `audit_round` e basta; giro superato / started < opened → `awaiting_audit` None → `_readonly` come un agente qualunque (test tardivo); riga `interrupted` → `subagent_stop` esce già per `state != running`, `audit_round` la chiude. Nessun ramo scoperto o doppio.
- ✅ `awaiting_audit` (`_common.py`): decisione 4, ripiego `governing_work` (punto c, testato).
- ✅ `audit_report` (`apply.py`): rilettura del giro (veto «giro non più aperto»), scrittura atomica tmp + `os.replace`, `OSError` → veto «report non scritto», giro aperto (D13, due test: cartella occupata da file e percorso occupato da cartella), stato lenti rigenerato, tetti con `audits.cap_reason` (D19), `OPS` = 28.
- ✅ Tetti (rischio 4): `len(audits.rounds)` esclude gli aperti e i `superseded` (`audits.py:80`); lenti `==` (test oltre il tetto non riapre); avversariale/piano `>=` e non pulito, con i rilievi meccanici già sommati ai conteggi.
- ✅ Decisione 8 / criterio 41: `major` per sezione mancante solo su `spec-adversarial`, con `spec_pitch` acceso, sul blob del giro (non sul worktree).
- ✅ D1, D20: `report_round` con la firma richiesta, `lab.now = opened + 1 s` assegnato (nessun attributo nuovo), docstring con la nota sul ritorno indietro. D14: test tardivo con spec committata prima dello start, giro 2 da `audit.prepare(..., now=)`, nessuna modifica ai file tra start e stop, commento presente.
- ✅ Test mirato rilanciato: `python3 -B -m unittest tests.test_check_audit_round` → 34 OK, nessun rumore. Suite non rilanciata (regola); evidenza del report coerente.
- ⚠️ Layering: `tests/test_layers.py` non rilanciato; `audit_round` importa solo analysis/core/hooks.model e non scrive nulla (solo `record`): coerente a vista.

### Punti di forza
Il modulo è corto e lineare; la scrittura è tutta in `apply` come impongono i vincoli. Il report scrive il messaggio non fidato in un recinto con `brief.fence`/`DATA_NOTE` e lo tronca. Test ben mirati ai rischi (agente tardivo con asserzione sui veti prima/dopo, valori grezzi, file di report committabile ma protetto, due modi di fallire la scrittura, giro non più aperto chiamando l'op direttamente).

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `tests/test_check_audit_round.py:~21` (rischio 2): `info/exclude` con `.tollgate-run/` solo in `RoundCase.lab`. Serve solo quando un `audit prepare` (che scrive il brief) cade tra lo `started` e lo stop di un agente già partito (scenari di agente tardivo). `report_round` avvia e ferma nella stessa chiamata, quindi i banchi dei Task 7, 8, 9, 15 che passano da `prepare` → `report_round` non ne hanno bisogno; chi simula un secondo giro con un agente in volo, o manomissioni, sì. Costo di spostarlo in `FlowLab.__init__` basso e fedele alla produzione (`start` lo scrive): consigliato farlo al primo task che ne ha bisogno, evitando di duplicare la riga di `RoundCase`.
2. `apply.py:~_write_atomic`: `except OSError` non copre `UnicodeEncodeError` (surrogati isolati in `last_assistant_message` decodificato da JSON). Il runner lo cattura come `ValueError` («registrazione non applicata», giro aperto, nessun crash), ma resta un file `.<nome>.tmp` vuoto in `reviews/<N>/` (verificato: `write_text` lo crea prima di fallire). Correzione: `except (OSError, ValueError)` nella pulizia, oppure codifica con `errors="replace"` del messaggio.
3. `audit_round.py:~_mechanical`: se `git.blob_text` non legge il blob, i rilievi meccanici spariscono in silenzio (il giro risulta più pulito). Caso quasi impossibile (lo SHA è del giro), ma un `deny`/veto sarebbe più onesto.
4. `apply.py` (`report non scritto`): l'unico segnale è un evento `veto`; il coordinatore non riceve nulla perché l'agente è già `done` (come da D13, quindi non è un difetto del task). Da ricordare nel Task 7: `audit prepare` deve rendere visibile il giro aperto con agente chiuso.
5. Nessun `fsync` prima di `os.replace` e nome tmp fisso: accettabile per file rigenerabili.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e voci di carry (D1, D13, D14, D19, D20, punto c) rispettati e verificati sul diff e con il test mirato; un solo proprietario per ogni agente in ogni ramo, tetti contati correttamente. Solo rifiniture Minor.
