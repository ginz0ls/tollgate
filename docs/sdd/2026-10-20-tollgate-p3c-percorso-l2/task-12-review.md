# Revisione Task 12 (170a6d0..6cc4f31)

### Aderenza
- ✅ Righe 34 e 36: `brief.py` (nota di rebase se `sha != head`), `FinalBrief.issue_file: str | None`, `finalreview._issue_file`; test in `test_brief.py` e `test_finalreview.py` (rebase vero con stesso patch-id).
- ✅ Riga 49 (decisione 25, spec 8.4): `actapply._approve_finding` ricalcola il ciclo del rilievo se chiuso (non solo l'ultimo) e chiude il blocco dei cicli. Test con ciclo 1 su 4, esito dell'ultimo intatto.
- ✅ Riga 50: `ValueError` diventa `ActApplyError` con la decisione già scritta; test.
- ✅ Riga 51, 67, 73: solo test, presenti con i nomi del brief.
- ⚠️ Riga 55: 4 test presenti, ma `test_ff_only_failure_blocks` ha nome e asserzioni in contrasto (vedi I-2). `test_intent_recorded_before_rebase` spia davvero `gitw.rebase` e legge l'intento `requested`: buono.
- ✅ Righe 60 e 62: avviso con punte diverse; `sqlite3.Error` in `acts.consume` dà `INCOMPLETE` (= 4), «lavoro creato, atto non consumato», nessun «rifiuto:».
- ❌ Riga 71: instradamento instabile risolto, ma con un insieme di file più largo di quello del task (I-1).
- ✅ Riga 72: formato «[major (originale blocker)]» accettabile: il brief del piano dice solo «originale tra parentesi se diversa». Regola duplicata in `brief._effective_severity` per rispettare gli strati, con commento: giusto.
- ✅ Riga 82: criterio 26 asserisce codice 1 e che ogni riga sia «rifiuto:»; helper `prepare_needs_fix_cycle`; `test_second_finish_is_new_cycle` usa `self.review`/`self.cli`/`self.open_pr` (hook e CLI vere), ciclo 2 `ok`, PR aperta.
- ✅ Carry T10: `UnicodeDecodeError` in `audit.ERRORS`; tre test (vedi M-1). `text_at` ripiega già su Latin-1 (Task 11), quindi con un file non UTF-8 vero prepare non rifiuta: coerente con la decisione 20; il rifiuto è provato solo col mock.
- ✅ Carry T11: `active_profile_names` con `head` nullo dà `[]` senza chiamare `changes`; due test (con `mock` su `changes`).
- Valutazione dei punti segnalati dall'implementatore: riga 71 (DB senza traccia dei rilievi del task) la scelta di instradare sul DB è ragionevole ma il filtro è sbagliato; riga 72 accettata; riga 55 il comportamento (rifiuto, intento chiuso «non riuscito», atto pending) è giusto contro spec 6.5 e decisione 17 (solo i rami divergenti danno `needs_you`), ma il nome del test è sbagliato.

### Punti di forza
- RED documentato per le righe con codice; test che verificano comportamento reale (rebase vero, spia sull'ordine dell'intento, rollback con `assign` che solleva).
- `test_gate_fence_longer_than_any_backtick_run` asserisce il recinto esatto (6 backtick; 7 nel brief).
- Riga 60/62 coerenti con `start`; nessun rifiuto dopo `create_work`.

### Rilievi

**Important**
- **I-1 `bin/tollgate_flow/taskcmd.py:73-76` (`_fix_files`)**: la query `verification = 'confirmed' AND blocking = 1` non filtra la gravità. `blocking` è `is_blocking` (`verdicts.py:91-101`, `reviews.py:166`): è 1 per qualunque rilievo con regola di piano o senza regola, anche `moderate`/`minor`. Il task di correzione invece nasce da `reviews.blocking_open` (`fixtask.py:41`), che richiede gravità effettiva blocker/major. Quindi i file di rilievi `moderate`/`minor` con regola `piano:…` entrano nell'instradamento (agente e revisore di profilo sbagliati) senza essere nel task. Prima della modifica `blocking_open` escludeva questi rilievi. Il test `test_routing_stable_after_dismiss` non lo vede: il suo MINOR ha regola `R-9` nota, quindi `blocking = 0`. Correzione: aggiungere `AND severity IN ('blocker','major')` (gravità dichiarata, non effettiva: la decisione 25 vuole l'insieme di creazione) e un test con un `moderate` con regola `piano:task 1` in un file di un altro profilo.
- **I-2 `tests/test_sync.py` (`SyncEdgeTest.test_ff_only_failure_blocks`)**: il nome dice «blocks», il docstring dice «ferma `sync`», le asserzioni verificano `sync.REFUSED`, intento chiuso `executed` con esito «non riuscito», atto `pending`, nessun blocco `needs_you`. Il comportamento è corretto (spec 6.5/decisione 17), il nome inganna chi legge i test e il report. Rinominare in `test_ff_only_failure_refuses` (e correggere il docstring), oppure asserire esplicitamente l'assenza di blocchi aperti (`blocks WHERE closed IS NULL` = 0) per fissare il contratto.

**Minor**
- **M-1 `tests/test_audit_prepare.py` (`NonUtf8Test`, primi due test)**: `try/except AuditError: pass` più `assertIn(r.code, (OK, REFUSED))` accettano qualsiasi esito; non fissano che cosa fa `prepare` con un file non UTF-8 committato (col ripiego Latin-1 va avanti). Asserire l'esito atteso, o dichiararlo nel docstring.
- **M-2 `bin/tollgate_flow/taskcmd.py:73`**: un rilievo archiviato o declassato PRIMA della creazione del task entra comunque nell'instradamento (lo dichiara l'implementatore). Accettabile, ma senza test che lo fissi.
- **M-3 `actapply.py` (riga 50)**: nel caso `superseded` il blocco dei cicli resta aperto e l'atto non si consuma; il messaggio dice perché. Nessun test sull'atto dopo il rifiuto.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** l'instradamento di `_fix_files` (riga 71) include file di rilievi non bloccanti per gravità, una regressione rispetto a `blocking_open` che il test non copre; il nome di `test_ff_only_failure_blocks` contraddice ciò che asserisce. Il resto (righe 34-62, 72, 82, carry) è corretto e ben testato.
