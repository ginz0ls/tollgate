### Verdetti sui rilievi
**Important: il guard verde riscriveva in «risolto» il commento rosso di qualunque SHA** — INDIRIZZATO. `guard.py:141-145`: la riscrittura richiede `is_guard_red(text)` e `comment.guard_marker_sha(text) == head`; altrimenti il commento resta intatto (marcatore compreso, perché `render_guard_resolved` non viene chiamato). Test negativo `test_green_guard_keeps_red_comment_of_another_sha` (`tests/test_gate_guard.py`, dopo r.398): rosso su X, guard verde su Y, `comments() == [red]`, marcatore ancora con lo SHA X, stato `success` su Y. Il test di stesso SHA resta.
**Minor: GhError in edit_comment dopo il success** — INDIRIZZATO. `test_edit_comment_failure_after_green_status_is_a_message`: patch di `github.edit_comment` con `GhError`, `cli.main` esce 1, messaggio su stderr, nessun «Traceback», `success` già scritto. Il codice non è cambiato perché `cli.py:160` già cattura `GhError` (verificato): il test fissa il comportamento.
**Minor: riga corta in tests/fakegh.py:48** — INDIRIZZATO. Paragrafo ricomposto (diff, 3 righe), solo docstring.
**Verifica di `comment.guard_marker_sha`** — OK. Regex ancorata con `match` su `body.lstrip()`: `GUARD_PREFIX` (escape) + ` sha=` + esattamente 40 `[0-9a-f]` + ` -->`; ogni altra forma (SHA corto, maiuscolo, 41 caratteri, marcatore mancante) dà `None`, quindi nessuna riscrittura (fail-closed). L'autore non è controllato dentro la funzione, ma l'unico chiamante usa il commento restituito da `github.bot_comment` (`github.py:174-176`), che accetta solo `user.login` in `ghcli.BOT_LOGINS` e prefisso uguale: un commento utente con marcatore falso non arriva mai alla funzione. Il corpo è usato solo per il confronto, mai interpolato.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna. (Il test non ha un caso diretto di marcatore malformato su `guard_marker_sha`; non blocca.)

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
