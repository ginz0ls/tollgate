# Revisione Task 11 (fc23d3f)

### Aderenza
- ✅ Interfaccia decisione 21: legge stdin, scrive atomico (`.tmp` + `mv -f` nella stessa cartella) `ctx/<sid>.json` = `{"used_pct": N|null}`; sentinella `.tollgate-test` (statusline/ctx:11-14); `sh -c "$*"` con lo stesso stdin (C21, statusline/ctx:43); senza comando exit 0 e nessun output (:42).
- ✅ Nessuna iniezione: `session_id` e percentuale non entrano mai in un comando, viaggiano via stdin e `printf '%s'`. Il `case` su `sid` (:34) impedisce `../` e separatori; la percentuale è validata (`null | [0-9]*`) e nel ramo Python viene da `json.dumps` di un numero. Verificato: `inf`/`1e400` e negativi diventano `null`.
- ✅ Mai fallire: errori nel parsing/scrittura non fermano il comando avvolto (test con `ctx` file, input non JSON); exit code del comando avvolto restituito (provato `exit 7`); stdout intatto; stdin integro con 500 KB (provato `wc -c` = 500072; `echo hi` con input grande: exit 0, nessun errore).
- ✅ Test mai sullo stato reale: TempState + HOME temporanea (anche il ramo senza sentinella). Coerente con la skill setup (`"<radice>/statusline/ctx" '<comando>'`, una sola stringa) e con il lettore `bin/tollgate_checks/agents.py:18-19` (`ctx/<session>.json`, `used_pct`).
- ⚠️ Ramo senza Python solo provato a mano dall'implementatore (nessun test automatico); non rieseguito.

### Punti di forza
Preservazione del newline finale (`printf x`), 14 test che vanno oltre il brief (pipe, exit code, stato non scrivibile, input non JSON), rimozione del `.tmp` in caso di errore, `|| true` difensivo.

### Rilievi
**Important**
- statusline/ctx:20-25 e :29-30: `session_id` con newline non viene scartato come prescritto da decisione 21 (`^[A-Za-z0-9_-]+$`). Python stampa `sid` e `pct` su righe separate, e `sed -n 1p/2p` li ricostruisce male. Riprodotto: `session_id="a\nb"` scrive `ctx/a.json` con `null`; `session_id="a\n77\n"` scrive `ctx/a.json` = `{"used_pct": 77}` (forgiato). Non è fuori dalla cartella `ctx` e l'input viene da Claude Code, quindi lo sfruttamento è improbabile, ma il requisito "id non valido non scrive nulla" è violato e può sovrascrivere il file di un'altra sessione. Correzione: validare il `sid` in Python con `re.fullmatch(r"[A-Za-z0-9_-]+", sid)` (stampare riga vuota altrimenti), oppure emettere un solo oggetto JSON/riga (`json.dumps([sid, v])`) e non separare per riga; aggiungere un subTest con `"a\nb"` in `test_unsafe_session_ignored`.

**Minor**
- tests/test_statusline.py: nessun test per il ramo senza Python (`sed`); basterebbe un PATH ridotto senza `python3`. Nello stesso ramo `tr -d '\n'` + regex greedy prende l'ultima occorrenza di `"session_id"`/`"used_percentage"` ovunque nel JSON (campi annidati con lo stesso nome); accettabile come ripiego.
- statusline/ctx:34 vs :36: `pct` come `1e+20` è accettato (JSON valido, il lettore lo confronta con soglie); nessun limite 0-100. Trascurabile.
- I `.tmp` orfani (`.sid.PID.tmp`) in caso di kill: verificare che `housekeeping.py:44` li potata (non controllato).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Implementazione solida e sicura sul piano dell'iniezione, dei percorsi, dell'exit code e dello stdin, ma la validazione del `session_id` si aggira con un newline, contro la decisione 21; correzione piccola, più un test.
