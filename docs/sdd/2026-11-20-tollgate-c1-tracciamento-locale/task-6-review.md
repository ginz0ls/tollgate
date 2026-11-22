# Revisione Task 6 (86d5b7b): fermate dagli hook di AskUserQuestion

Letto: regole, brief, decisione 4, review-focus 1, fatti, report, pacchetto di revisione. Codice letto con `git show 86d5b7b:`; test mirati lanciati su una copia `git archive` in cartella temporanea (cancellata): `tests.test_check_stops test_check_session test_manifest test_wrapper test_hook_engine`, 148 test OK. Prova a mano di `_asks_user` e di `json_str` (copiata dal wrapper) su input annidati.

### Aderenza
- ✅ `pre_question`/`post_question` in `model.INPUT_EVENTS`, non in `CONTROL_EVENTS` (model.py:11; test_hook_engine nuovo).
- ✅ Adattatore: `_PRE`, `_POST` e ramo `PostToolUseFailure` (adapter.py), Read resta `None`.
- ✅ Tre matcher di `hooks.json` con `AskUserQuestion` (test_manifest nuovo).
- ✅ Wrapper: `CONTROL=no` per `PreToolUse` di `AskUserQuestion` dopo `INPUT=` e dopo la definizione di `json_str` (hooks/run:50-53). Con Python assente, uscita 1/127/raise, scadenza: avviso e 0; `Bash` resta 2 (test_wrapper). Uscita 2 del programma passa com'è, come da decisione 4; il runner non la produce per quel caso.
- ✅ Runner: `control` calcolato in testa con `_asks_user` (runner.py:203-213); input troncato, `_Timeout` ed errore generico danno 0 con avviso; `Bash` 2. Dopo `to_event` `control = event.kind in CONTROL_EVENTS` (falso per `pre_question`). Le altre `_fail(True, ...)` (multi-repo) sono solo per `_TARGET_KINDS`, irraggiungibili qui. Nessun controllo caricato ha `pre_question` che neghi; un controllo rotto con `events=None` non nega più (control falso).
- ✅ Regola del testo grezzo, input annidati provati: `tool_input.command` con `"tool_name": "AskUserQuestion"` (le virgolette nel JSON sono escapate, quindi non combacia), `tool_use_id` e `cwd` con la stringa dentro: in runner e in awk restano `Bash`/controllo.
- ✅ `stops.py`: `data` esattamente come decisione 4; testi a 300, 4 domande, 4 opzioni; `source` in `tool_response|tool_input|failure|none`; legge da `event.raw` (D16) tollerante a ogni forma; mai `deny` né `inject` né eccezione; senza domande leggibili nessun evento; `tool_use_id` nullo se assente; `work` da `governing_work`.
- ✅ `session_start` registrato in `session.py` con `work` = `ctx.work` (anche quello legato dallo stesso hook) o nullo, prima dei rami di ritorno; test dei tre casi.
- ✅ `stop_asked`/`stop_answered` sono già in `EVENT_TYPES` (events.py:22). Nessun riferimento vietato a modelsfetch.
- ⚠️ Non verificato: forma reale di `tool_response` di `AskUserQuestion` (nessun campione; costo già accettato in decisione 4).

### Punti di forza
- Regola calcolata una volta sola in `run_hook`, identica a `json_str` del wrapper; il commento lo dice.
- Test del runner coprono troncato, scadenza ed errore generico con il confronto a `Bash`; il test del wrapper copre quattro modalità di errore e Python assente.
- `stops.py` piccolo, una responsabilità, senza duplicazioni; `_text` centralizza il taglio.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. hooks/run:50 e runner.py:203-207: la regola guarda la prima occorrenza di `"tool_name"` nel testo grezzo. Se un giorno Claude Code mettesse `tool_input` prima di `tool_name`, un `mcp__*` con `tool_input = {"tool_name": "AskUserQuestion"}` non sarebbe più un controllo (provato: `_asks_user` dà True). Oggi `tool_name` precede `tool_input` (stessa assunzione già scritta in `json_str`); non c'è un'altra strada praticabile senza `jq`. Si potrebbe fissare l'ordine con un test sui campioni degli hook.
2. Nessun test fissa il caso richiesto «`Bash` con `"tool_name": "AskUserQuestion"` dentro `tool_input` resta un controllo» (né nel wrapper né nel runner): il comportamento è corretto (provato a mano) ma senza guardia contro regressioni (es. un futuro regex meno stretto). Aggiungere un caso a `test_ask_user_question_never_denied_by_failure` e uno a `test_hook_engine`.
3. session.py (riga aggiunta con `event.raw.get("source")`): `source` non è controllato né tagliato; un valore non stringa o enorme finirebbe così nei `data`. Tollerabile (viene dall'harness), ma `str`-con-taglio sarebbe coerente con `stops._text`.
4. stops.py `_answers`: il taglio a 300 può fondere due chiavi diverse in una; valori non stringa diventano `""` senza segnalazione. Accettabile per la decisione 4.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** Tutti i requisiti della decisione 4 e di D16 sono verificati sul diff e con 148 test mirati; wrapper e runner non negano mai `AskUserQuestion` in nessuna delle strade cercate, e `Bash` resta un controllo anche con `tool_name` annidato. Restano solo rifiniture Minor.
