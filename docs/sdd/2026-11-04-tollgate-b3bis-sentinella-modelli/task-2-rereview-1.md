# Task 2 — ri-revisione del giro di correzione 1 (4c2a176..a62a9e9)

### Verdetti sui rilievi
1. **RecursionError di JSON annidato -> FetchError("risposta non JSON") fuori dall'except.** INDIRIZZATO. `modelsfetch.py:_get_json` ultimo `except (ValueError, RecursionError)` ritorna il motivo; `fetch_pages` solleva fuori dall'except (`__context__`/`__cause__` None). Test `test_deeply_nested_json_is_fetch_error` (200k parentesi; asserisce testo, context e cause None); eseguito: OK.
2. **`test_environment_proxy_ignored` asserisce davvero.** INDIRIZZATO. `tests/test_modelsfetch.py` (~riga 405): tre variabili di proxy nell'ambiente; nessun `ProxyHandler` con proxy, nessun gestore con `proxy_open`, `handle_open["https"]` uguale a `[HTTPSHandler]`. Eseguito: OK.
3. **Timeout ridotto a `deadline.left()` nelle letture, o motivazione.** INDIRIZZATO (motivazione). Il report dice che con la libreria standard non c'è modo pulito di cambiare il timeout del socket sotto la risposta e quantifica lo sforamento (massimo `timeout`, 5 s per lettura bloccata). Motivazione plausibile e onesta; l'apertura usa già `min(timeout, deadline.left())`.
4. **Risposta chiusa quando il gestore dei redirect solleva.** INDIRIZZATO. `_RefuseRedirect._refuse` chiude `fp` prima di sollevare; `redirect_request` delega a `_refuse`. Test `test_redirect_handler_closes_response` copre entrambe le vie (`fp.closed` vero); eseguito: OK.
5. **Cache: temporaneo unico, `os.replace`, pulizia, chiave mai nel file; nessuna garanzia persa.** INDIRIZZATO. `_write_cache` usa `mkstemp` nella stessa cartella, `os.replace`, `unlink` del temporaneo in caso di errore, `mkdir(parents=True)` mantenuto. Test `test_cache_temp_names_are_unique_and_removed_on_failure` (nomi diversi, cartella pulita) e il preesistente `test_cache_write_failure_does_not_break_result` (cartella vuota dopo il fallimento); `test_key_never_in_errors_lines_or_cache` invariato. Confronto con `fsutil.write_atomic`: nemmeno quella faceva fsync; la cartella è creata in entrambe; i permessi passano da quelli di umask (0644) a 0600 di `mkstemp`: più stretti, nessuna perdita.
6. **`test_gemini_order` rinominato `test_real_…`.** INDIRIZZATO. Ora `test_real_gemini_order`.

### Danni nuovi nel diff della correzione
Nessuno. Minor trascurabile: in `_write_cache`, se `os.fdopen` stesso fallisse (praticamente impossibile) il descrittore resterebbe aperto; non blocca.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
