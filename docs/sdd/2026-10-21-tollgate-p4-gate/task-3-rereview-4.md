# Task 3: ri-revisione del giro di correzione 4

Diff `b02b53b..00065d7`. Verifiche con `python3 -B` e PyYAML 6.0.1 (solo come lettore di confronto), nello scratchpad.

### Verdetti sui rilievi
**Rilievo aperto (Important): l'esenzione degli scalari a blocco scatta anche per un `|` finale dentro un flusso su più righe** — INDIRIZZATO. `workflows.py` `_scan`: le righe che aprono un flusso sono rosse («collezione a flusso su più righe»); l'intestazione di blocco è cercata solo con `clean_start and not flow_here and not quote and not depth` e `_BLOCK_HEADER` fa `fullmatch` con `|`/`>` come intero valore di `chiave:` o `- `. Gli esempi del revisore (`a: b - |` + `, "\x73tatuses": write}` e la variante `!!str` / `pull_request_target`) sono rossi (test `test_flow_collection_over_several_lines_fails_closed`).
**Ruling, regola 1 (rosso per ogni flusso non chiuso sulla riga di apertura)** — INDIRIZZATO per costruzione: `depth and flow_here` a fine riga produce il rosso; `[`/`{` aprono fuori flusso solo a inizio nodo, quindi `run: echo ${{ x }}` resta testo.
**Ruling, regola 2 (intestazione solo fuori da flusso aperto e solo se `|`/`>` è l'intero valore)** — INDIRIZZATO: vedi sopra. Rientro del nodo e del contenuto coerenti con PyYAML (`min_indent = indent+1`, `|N` = base+N).

### Danni nuovi nel diff della correzione
Nessuno. Controlli mirati sulle ipotesi di stato che non si chiude o di rientro sbagliato:
- `x: a` + `  - |` + riga con `"\x73tatuses": write` (la riga `- |` è continuazione di uno scalare semplice, il blocco dello scanner salta righe che YAML legge come testo): PyYAML dà errore, quindi nessuna evasione; le righe saltate sono comunque dentro lo scalare e non possono contenere `: `.
- Riga vuota più rientrata della prima riga di contenuto (YAML fissa il rientro sul massimo): il testo seguente è un errore di parsing per YAML, non una struttura valida.
- Blocco con `- |` dentro `permissions:`: letto come lista di testo, nessun `statuses` reale.
- Stringa doppia su più righe `name: "a` / `  b": |`, `'a''`, `#` in flusso, `a:"b"` e `{"a":"b", "pull_request_\x74arget":1}`: tutti rossi dove PyYAML legge un evento vietato.
- Confronto differenziale mio (300000 testi casuali da frammenti con `|`, `|2`, `"`, `''`, `[`, `{`, `&`, `!!`, `#`, escape `\x73tatuses`/`\x74arget`, rientri): 0 casi in cui PyYAML legge `statuses`/`checks: write` o un evento vietato e `problems()` è `[]`.

### Osservazioni fuori ambito
- Già dichiarata nel report: valori spazzatura non `write` non rossi (`checks: read]x`), da `_SCOPE`/`_next_value`.
- Conservatività accettata dal ruling: un workflow con flusso su più righe è rosso.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
