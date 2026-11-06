Task 2: minor (deferred): D22 — cache dei modelli con le pagine grezze (fino a 10 × 8 MiB per fornitore), non potata da `housekeeping.run`.
Task 3: minor (deferred): D25 — un `KeyboardInterrupt` durante il controllo lascia il lavoro creato senza la riga «prossimo passo» (la ripresa lo completa).
Task 1: minor (deferred): models.py:98,104 — `line` stringa vuota dà `family=""` (confronta tra loro modelli senza linea): usare `or None`.
Task 1: minor (deferred): models.py:219,222 — ID e date da elenchi esterni senza tetto di lunghezza nelle righe (solo `_plain`).
Task 1: minor (deferred): models.py:196,235 — il parametro `literals` oscura la funzione omonima (firma imposta dal brief).
Task 1: minor (deferred): tests/test_models.py:343 — `assertRaises(Exception)` troppo largo (FrozenInstanceError).
Task 1: minor (deferred): models.py:128,141 — OpenAI e OpenRouter con `stable=False` per tutti: da documentare.
Task 1: minor (deferred): models.py:178-180 — confronto di `created` tra stringhe: regge solo con formati omogenei (RFC 3339 di Anthropic).
Task 2: minor (deferred): ogni HTTPError 3xx (anche 304) diventa «redirect rifiutato».
Task 2: minor (deferred): `no_network()` non blocca `socket.getaddrinfo` (nessuna connessione possibile senza socket, ma una risoluzione DNS sì).
Task 2: minor (deferred): la cache non ha un tetto complessivo (vedi anche D22).
Task 2: minor (deferred): una lettura bloccata può sforare la scadenza di al più `timeout` (5 s): il timeout del socket non si riduce dopo l'apertura.
Task 2: minor (deferred): `_write_cache` — se `os.fdopen` fallisse, il descrittore di `mkstemp` resterebbe aperto.
Task 3: minor (deferred): con N=1 la riga di taglio dice «… e altri 1 avvisi» (forma fissa della decisione 13).
Task 3: minor (deferred): models_check.py — perse le annotazioni di tipo `Provider` in `_wanted`/`_provider_lines` (modulo importato in locale).
Task 4: minor (deferred): `assertNotIn("sk-PROVA-123", …)` mostra le righe al fallimento (chiave finta: innocuo).
Task 5: minor (deferred): un SIGKILL di `tests/run` lascia una `tollgate-run-*` (la toglie la pulizia delle 24 ore).
Task 7: minor (deferred): se l'uscita della seconda corsa contiene una chiave, `refresh.txt` (già controllato) resta salvato.
Task 7: minor (deferred): il caso positivo `/tmp/tollgate-b3bis` non è coperto dai test (toccherebbe la cartella vera della prova).
Task 7: minor (deferred): la ricerca del valore finto nei test esclude `repo/.git` senza motivo (oggi non nasconde casi).
Task 7: minor (deferred): nessun controllo del proprietario su un `/tmp/tollgate-b3bis` già esistente (utenza singola).
Task 4: minor (deferred): docs/uso/comandi.md dice che la copia del gate in `.github/tollgate/` «non contiene» `models check`: in realtà `install.files` copia tutto `bin/` ma non `templates/` (il codice c'è, manca il file dei fornitori → «controllo non riuscito»). Segnalato dal Task 8.
Task 8: minor (deferred): spec 11.4 dice che `--refresh` ignora la cache, ma con la rete fallita la cache (anche scaduta) si usa comunque come ripiego (ruling del Task 2); manca una nota sui `retired` non richiesti e sul costo degli alias `~` di OpenRouter.
Task 8: minor (deferred): la spec nomina «la pagina dei modelli di OpenRouter» senza l'URL di templates/models.toml.
