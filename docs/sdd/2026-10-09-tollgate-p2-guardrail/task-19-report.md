# Task 19 - report

## Implementato
- `bin/tollgate_checks/subagent_stop.py` (evento `subagent_stop`, ordine 20): ordine dei controlli per un implementatore: tetto di token (`task_budget`) -> report a campi fissi (`report_fields`) -> dimensione (`task_size`) -> ricevuta (`subagent_receipt_gate`) -> skill dei profili -> transizione del task. Veti contati in `subagents.vetoes`; al terzo `SubagentStop` (dopo 2 veti) chiude, task `blocked` e `needs_you`. Sola lettura con impronta cambiata (`readonly_check`) -> `tampered` + `needs_you`.
- Nessuna nuova operazione `record`: `subagent_veto`, `subagent_finish`, `task`, `block` esistevano gia in `apply.py`.

## Scostamenti dal piano
1. Carry Task 19: il controllo agisce solo se `subagents.state == 'running'`. Una riga gia chiusa (`cut` da `post_agent`/`prompt_submit`, `done`, ecc.) non viene riscritta ne vetata.
2. Decisione 24: `_receipt_ok` accetta una ricevuta `related` green sull'ultimo commit; altrimenti richiede green tutte le ricevute non `related` (almeno una). Il piano usava `all()` su tutte: una `related` `empty` (che ripiega sul gate completo) o rossa avrebbe vetato anche con gate green.
3. Il report con status sconosciuto da' il messaggio «status sconosciuto» invece di un elenco vuoto di campi mancanti; `declared_status` e' `None` se il report non e' valido.
4. Impronta: confronto con `review.output_dirs`, le stesse esclusioni di `subagent_start` (che prende l'impronta di partenza). Estratto in `_fingerprint_changed`.

## Test (`tests/test_check_subagent_stop.py`, 26 test: 15 del piano + 11 aggiunti)
Aggiunti: riga `cut` non riscritta (stato e task invariati), riga chiusa ignorata, `related` green con gate rosso, `related` empty con gate green, `related` rossa da sola, status sconosciuto, conteggio veti e testo «veto 1 di 2», DONE_WITH_CONCERNS, skill richiesta mancante (poi presente), BLOCKED con blocco aperto, `readonly_check` spento.

- RED (modulo spostato): `python3 -B -m unittest tests.test_check_subagent_stop` -> `Ran 15 tests ... FAILED (failures=10)` (es. `AssertionError: 0 != 2`).
- GREEN: stesso comando con il modulo -> `Ran 26 tests ... OK`.
- `tests/run`: python3.11 e python3 (3.13.5), 621 test, OK.
- `python3.11 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 621 test, OK (due volte).

## Dubbi
- Una prima esecuzione di `tests/run` ha mostrato `FAILED (failures=1)` (output troncato dal `tail`, test non identificato). Quattro riesecuzioni complete successive (due `tests/run`, due con `-W error::ResourceWarning`) sono verdi. Possibile test intermittente preesistente, da tenere d'occhio.
- C12 come da piano: un subagente non di sola lettura senza task (es. `general-purpose` in fase plan) riceve fino a 2 veti se non chiude con il report JSON.

## Fix round 1
1. Gate parziale: `dod.receipt_verdict(rows, head, allow, required)` e' ora l'unico punto della regola (comandi richiesti tutti presenti e green); `dod._receipt` lo usa su `receipts.latest` (comportamento invariato, `counts_green` al posto della copia di `ok`). `subagent_stop._receipt_ok` calcola i comandi richiesti con `verify.gate_commands` (profili attivi sui file cambiati dalla base del lavoro, come `verify`) e chiama `receipt_verdict` sulle ricevute non `related`; una `related` green basta ancora (decisione 24).
2. Falso `tampered` alla ripresa: `subagents.start(..., refresh_fingerprint=False)`; `subagent_start` lo passa vero per un subagente di sola lettura ripreso (via record `subagent_start`, `apply.py` inoltrato). `agent_base_sha` resta fisso; gli implementatori non riprendono l'impronta.
3. `subagents.start` azzera `vetoes` alla ripresa.
4. `test_tokens_over_cap_block_even_with_green` usa `TemporaryDirectory` con `addCleanup`.
- Test aggiunti (7): `GateCompletenessTest` (gate parziale, comando estraneo, gate completo, related), `ResumeTest` (revisore ripreso dopo commit altrui `done` senza blocco, base_sha fisso, veti azzerati).
- RED: `python3 -B -m unittest tests.test_check_subagent_stop` -> `Ran 33 tests ... FAILED (failures=4)` (partial gate, foreign command, resume vetoes, resumed reviewer).
- GREEN: stesso comando -> `Ran 33 tests ... OK`. `tests/run` (3.11 e 3.13.5): 628 test OK. `python3.11 -B -W error::ResourceWarning` suite intera: 628 OK.
- Rimossi i `__pycache__` in `bin/*/` (preesistenti, non committati); solo `python3 -B`.
