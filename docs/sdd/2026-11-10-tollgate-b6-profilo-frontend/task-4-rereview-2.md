# Ri-revisione giro 2, Task 4

### Verdetti sui rilievi
1. **Le asserzioni sul testo della pagina, della skill e del rapporto che stampano il testo intero vanno convertite in `assertTrue(re.search(...), "<messaggio fisso>")` / `assertFalse(...)`, senza indebolire i test.** INDIRIZZATO.
   - Pagina: tutti gli `assertRegex(text, ...)` di `test_page_explains_what_changes` (`tests/test_rules_frontend.py:516-556`) sono ora `assertTrue(re.search(<stesso pattern>, text), "manca un passo atteso nel testo")`. Pattern identici riga per riga nel diff, compreso `text.lower()` a `:556`. Gli altri controlli della pagina (`:525`, `:532`, `:549`, `:555`, `:558-559`, `:564`, `:582`, `:591`, `:605`, `:615`, `:628`, `:634`, `:648-654`) hanno già messaggio fisso; `:592` ha il messaggio e confronta due interi.
   - Rapporto: `:408-412` (celle di `sources`/`text`) sono `assertFalse/assertTrue(x in cella, "<messaggio fisso>")`, stessa condizione di prima (`assertNotIn` diventa `assertFalse(... in ...)`, `assertIn` diventa `assertTrue(... in ...)`).
   - Skill: i due `assertRegex(flat, ...)` di `test_sources_section` (`:234-239`) sono convertiti con pattern invariati.
   - Nessun test indebolito: stessi pattern, stesse condizioni, stessi `subTest`.
   - Le asserzioni rimaste che possono stampare qualcosa (`:384`, `:438`, `:451`, `:464` stampano una sola cella; `:428-430` una riga di tabella; `:386`, `:441-442`, `:455-456`, `:468`, `:473` insiemi di id o nomi) non stampano il testo intero della pagina o del rapporto, né il nome utente, l'host o la home (il controllo privato è a `:636-654`, a messaggi fissi).

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- Restano `assertIn/assertNotIn(needle, <testo della skill>)` nei test del Task 3, non toccati dal giro: `:234` e `:239-240` (`fonti`/`flat`), `:246`, `:249` (`informarsi`), `:252` (`skill_text()` intero), `:313`. In caso di fallimento stampano la sezione o l'intera skill. La skill è un file versionato del repo, senza dati privati, e il criterio del rilievo riguarda la pagina e il rapporto: non blocca. Se si vuole uniformità, convertirli con lo stesso schema in un giro a parte.
- Alcune righe nuove superano i 100 caratteri (`:408-412`) e le continuazioni dei `re.search` multilinea hanno rientro non allineato (`:536-538`, `:542-543`): solo estetica.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
