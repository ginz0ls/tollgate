# Revisione Task 1 (B2): interruttore pronto per l'accensione

Diff fbf7068..d9ca5de letto per intero. Test mirato rilanciato: `python3 -B -m unittest tests.test_research tests.test_lookups tests.test_check_research_gate tests.test_brief` -> 125 test OK.

### Aderenza
- ✅ Valori negativi: `research.py:38` (`_YAML_EMPTY` con `no`, `off`, `n`) e `research.py:57-58` (apici tolti prima del confronto, senza maiuscole). `"false"` quotato ora è falso. Test `test_enforced_refuses_no_off_n` copre gli otto valori negativi e le due date/stringhe vere.
- ✅ `rules_switch` (`lookups.py:170-180`): assente `(False, None)`, altro `OSError` `(False, "<classe>: <messaggio>")`; `rules_enforced` = `rules_switch(root)[0]` (`lookups.py:183-185`), firma invariata; frase «è di B2» tolta. Test `lookups` come da brief.
- ✅ `events.EVENT_TYPES` (`events.py:19`); nessuna operazione nuova in `_OPS` (l'evento passa da `record("event", ...)`); `research_gate` non scrive nel DB. Strati rispettati (`research_gate` importa solo `lookups`, `tollgate_core`; `lookups` importava già `research`).
- ✅ `_UNREADABLE` (`research_gate.py:22-24`): testo identico alla decisione 5.
- ✅ Interruttore letto una volta, prima del controllo della nota (`research_gate.py:102`); errore portato a `decide` anche con nota valida (`:104-105`); mai un `deny` per l'errore (il `deny` resta solo con `enforced`, che con errore è sempre falso).
- ✅ Evento una volta per lavoro dopo l'ultimo `plan_reset` (`research_gate.py:145-147`, `work_events` filtra su `seq > max(plan_reset)`, `_common.py:198-203`). `PostToolUseFailure` e L0 invariati; nessun avviso doppio.
- ✅ A `pre_*` l'`_UNREADABLE` si antepone solo quando c'è l'avviso normale (`:138-142`); con nota valida nessun `inject` (test `logged_with_valid_note`).
- ✅ `brief._review_research` (`brief.py:214`): `b.no_changes and not usable`; test nuovo. Il caso nota valida e senza modifiche prosegue come prima (invariato).
- ⚠️ Esito della suite completa (3173 test, 3.11 e 3.13) è solo nel report, non rilanciato per regola.

### Punti di forza
- Modifica chirurgica; `_verdict` conserva i casi esistenti restituendo una tupla a 4 con `error` None dove non serve.
- I test usano un errore reale (cartella al posto del file) invece di mock, e verificano sia l'unicità dell'evento sia il caso file assente (nessun evento, nessun avviso extra).
- Il report dichiara il RED con i sorgenti precedenti e il GREEN.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor:**
1. `tests/test_check_research_gate.py` (`test_unreadable_switch_warns_and_logs_once`): non verifica che `_UNREADABLE` preceda l'avviso normale, né che la seconda modifica (già avvisata, `research_reminder` registrato) non inietti di nuovo il testo; copertura del caso «già avvisato + errore = nessun `inject` a pre» assente. Aggiungere un `assertLess(find("non si legge"), find(WARNING))` e un'asserzione sull'`inject` della seconda modifica.
2. `research.py:57`: le stringhe quotate `"null"`, `"~"`, `"|"` ora valgono vuoto (prima, quotate, erano vere). Coerente con il requisito per `"false"`, ma è un cambio di comportamento non coperto da un test; inoffensivo.
3. `lookups.py:183` docstring di `rules_enforced` cita «`task review`», mentre il chiamante è `taskcmd.py:353` (che alimenta il brief di review): lieve imprecisione.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** tutti i requisiti della decisione 5, 6 e del brief sono implementati e provati con test che esercitano l'errore reale; nessun difetto di comportamento, di strati o di contratto (nessuna operazione nuova, chiamanti di `rules_enforced` invariati). Restano solo rifiniture di copertura.
