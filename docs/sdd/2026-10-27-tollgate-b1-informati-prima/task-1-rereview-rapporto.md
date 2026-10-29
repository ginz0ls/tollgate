# Ri-revisione del rapporto delle verifiche, Task 1 (sola lettura)

Confronto tra `task-1-review-rapporto.md` e `docs/verifiche/2026-10-27-b1-verifiche.md` attuale, con controlli mirati sulle evidenze.

### Verdetti sui rilievi

1. **Incoerenza V1/V6 su `Grep` non detta:** INDIRIZZATO. `verifiche.md:14` ora scrive che la regola di `Grep` content «resta dormiente finché `Grep` è fuori dal matcher, vedi B1-V6». Resta non esplicitato per intero cosa perde la regola 3.3 (le letture con `Grep` non contano; l'implementatore deve usare `Read`/`cat`): lo si deduce, non è scritto. Minor residuo, da dire nella ruling o nel Task 4.
2. **V6: soglia 300 ms non raggiungibile con la via breve:** INDIRIZZATO. `verifiche.md:19` etichetta «Deduzione, non misura», cita la differenza tra mediane (~65 ms), conclude che la via breve «resterà probabilmente sopra 300 ms» e che a ridurre i processi è togliere `Grep` dal matcher; la ruling di `progress.md` dichiara il costo. Non propone alternative (filtro in `hooks/run` prima di Python), ma il difetto (conclusione mancante) non esiste più.
3. **Serie V6 rumorosa usata come stabile:** INDIRIZZATO. Riportate mediana per metà (522,8 / 403,8, ricalcolate da `latenza.json`: coincidono) e minimo 309,4; dichiarata «seconda serie instabile» e nei Limiti «carico moderato… il Task 4 la rimisura». Il carico non è misurato durante le serie, ma è dichiarato come limite.
4. **V4: 301 senza evidenza:** INDIRIZZATO. `evidenze/b1/reindirizzamento-head.txt` contiene `HTTP/2 301` e `location: https://docs.python.org/3/library/json.html`, citato in Evidenza (`verifiche.md:8` e riga V4). Annotazione: è una trascrizione a mano del controller («Prova a mano»), non l'uscita grezza; accettabile, il rapporto la dichiara tale. L'argomento dei 116.112 byte è confermato in `hooks.jsonl`.
5. **V2: passo 10 invece di 12 e causa basata sul subagente:** INDIRIZZATO. Ora «risposta del passo 12» (corretto), «secondo il resoconto del subagente», «L'evidenza è la sola dichiarazione del subagente più l'assenza di eventi» (`grep mcp__ hooks.jsonl` = 0). Residuo: «abilitato (`claude plugin list`)» e «quanto visto il 27/10» non hanno evidenza archiviata (vedi sotto); «non impediscono il lancio» non cita `SubagentStart` come prova.

Minori di forma dichiarati corretti:
- `PostToolUseFailure` senza chiave `tool_response`: INDIRIZZATO (`verifiche.md:14`).
- `results` misti di `WebSearch`: INDIRIZZATO (riga V4: «elementi misti, oggetti con `content[]`… e stringhe di testo»).
- Percorsi relativi del `Grep`: INDIRIZZATO (riga V1: «Percorsi assoluti in `tool_input`, relativi alla `cwd` nel `tool_response` di `Grep`»).
- `README_MISSING` ✘: INDIRIZZATO (riga V7: ✘ vs avviso per `ICON_MISSING`; coincide con `valida-esito.txt`). Resta non fatto, ma non richiesto di nuovo, il controllo negativo di `approved`.

### Affermazioni nuove o residue senza evidenza

- Minor: «Il plugin context7 dell'utente è abilitato (`claude plugin list`)» (riga V2): nessun file in `evidenze/b1/` contiene l'uscita di `claude plugin list` (grep: solo `argv.txt` contiene «plugin list» per altro motivo). Archiviarla o riformulare come «dal contesto della sessione».
- Minor: «coerente con quanto visto il 27/10 nella sessione dell'utente (solo `authenticate` e `complete_authentication`)»: nessuna evidenza nel repo; affermazione di contesto.
- Minor: «Le voci `mcp__…` in `tools` non impediscono il lancio» senza citare `SubagentStart` in Evidenza.
- Minor: la formula «il grosso è l'avvio del processo Python» è ora segnata come deduzione: ok.

### Danni nuovi nel diff della correzione

Nessuno Critical/Important. Numeri riverificati: 30 eventi, 2.1.312, mediane per metà, 116.112 byte, nessun evento `mcp__`, chiavi dei campioni invariate (10).

### Osservazioni fuori ambito

Etichette D1/D5/D6/D15/D16 chiarite nella nota di `progress.md`; `read_missing`, identificativi veri e `ATTRIBUTE_UNNAMED_TOOLS` rinviati come minori deferiti: accettabile.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. (Restano tre Minor sulle affermazioni di contesto di V2, senza effetto sull'esito.)
