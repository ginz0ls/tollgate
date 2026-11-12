# Ri-revisione giro 1, Task 4

### Verdetti sui rilievi
1. **`assertNotIn("/home/", text)` stampa la pagina; nessun'altra asserzione deve poter stampare nome utente, host o percorso della home.** NON INDIRIZZATO. Il punto specifico è corretto: `tests/test_rules_frontend.py:632` ora è `assertFalse("/home/" in text, "<messaggio fisso>")`, e gli `assertIn/assertNotIn` della classe sulla pagina sono convertiti. Ma restano nove `assertRegex(text, ...)` in `test_page_explains_what_changes` (righe 514, 515, 523, 529, 530, 532, 534, 537, 540, più 545 su `text.lower()`): `assertRegex` in caso di fallimento stampa l'intero testo della pagina, quindi, se la pagina contenesse un percorso della home, un fallimento lo stamperebbe. Non è convertito anche il gruppo del rapporto (`:406-410`, `assertNotIn`/`assertIn` su celle di `sources`/`text`, che stampano la cella intera). Il rilievo chiedeva che nessuna asserzione dei test della pagina o del rapporto potesse stampare questi dati: il difetto esiste ancora.
2. **Termini spiegati la prima volta.** INDIRIZZATO. `docs/profili/frontend.md` glossario: voci Profilo, Percorso esatto, Client delle API, CDN, Loader; `test_page_explains_the_terms` controlla `**Percorso esatto**`, `**Profilo**`, `**Loader**`, `**CDN**`, `**Client delle API**`.
3. **Punto 10 e riga delle esclusioni: database con B7, fino ad allora punto 19.** INDIRIZZATO. Riga delle esclusioni e punto 10 della pagina riscritti come richiesto.
4. **Punto 12: costo in una riga e «parte sicura», primo periodo non ambiguo.** INDIRIZZATO. Il periodo iniziale definisce la rotta di sole risorse; costo e «parte sicura» spiegati (punto 12 della pagina).
5. **Aghi per P14, P35, P32, P33.** INDIRIZZATO. In `test_page_brings_the_open_choices_to_the_user` aggiunti «finché non arriva il profilo del database», `` `web/api/` ``, `` `index.module.css` ``, «foglio di stile». Nota: gli ultimi due aghi sono generici; «foglio di stile» compare già nel glossario, ma l'ago è limitato alla sezione «Da decidere tu», quindi accettabile.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti: il n. 1 (restano `assertRegex(text, ...)` su testo di pagina a `tests/test_rules_frontend.py:514-545` e le asserzioni sulle celle del rapporto a `:406-410`, che in caso di fallimento stampano il testo intero). Rimedio: `self.assertTrue(re.search(pattern, text), "manca un testo atteso")` (e analogo per `assertNotIn/assertIn` del rapporto).
