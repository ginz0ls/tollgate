# Revisione Task 1 (B4): forme dei pattern dei frammenti

### Aderenza
- ✅ `Pattern` frozen, `parse_pattern` con una regex per forma e `fullmatch` (`bin/tollgate_core/fragments.py:15-39`). Verificato a mano il comportamento sui casi del brief: `<nome>` richiede lettera, almeno 2 caratteri prima dell'eventuale `*`, un solo `*` finale; `.`/`..`/`x`/`a*`/`Dockerfile**` rifiutati.
- ✅ `_parse` usa `parse_pattern` per ogni voce, `patterns` nello stesso ordine di `paths`; voce non stringa o `paths` non lista: errore con nome file (`fragments.py:82-88`). `paths` vuoto ancora errore dedicato.
- ✅ `load_approved` = filtro di `load` con `approved`, stesso ordine (`fragments.py:118`).
- ✅ `rules` solleva `FragmentError` con `rules-<area>/SKILL.md` (`fragments.py:127-130`). Unico chiamante, `init.py:342`, viene dopo `approved`, quindi non regredisce.
- ✅ Strati rispettati (nessun nuovo import); `_PATTERN` rimosso senza altri riferimenti; `tomlout_str` tolto e sostituito da `tomlout.table` (`tests/test_fragments.py:30`). Nessun `__pycache__` nel commit (2 file).
- ✅ Test: tutti quelli del brief presenti, con la lista completa dei rifiuti; i due aggiornati con il motivo corretto.
- ⚠️ Suite completa (3577 test, due interpreti) dichiarata dal report, non rilanciata.

### Punti di forza
Diff minimo e chirurgico, regex leggibili, `**/ai` come `name` documentato nei test. Messaggio di errore aggiornato alle tre forme.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `fragments.py:16-17`: `[^/*?\[\]!\\]+` ammette il newline (e caratteri di controllo) nel segmento di cartella, es. `a\n/**` -> `root_folder` `"a\n"`. Comportamento già presente con la vecchia regex e non vietato dal piano; da valutare un'esclusione di `\n` se si vuole difesa in profondità.
2. `fragments.py:82-83`: il ramo `[None]` per `paths` non lista è un po' contorto; un controllo `isinstance(paths, list)` prima della comprensione sarebbe più chiaro. Solo leggibilità.
3. `test_load_accepts_three_forms` non asserisce il rifiuto di un pattern `name` non valido in `load` (coperto per le altre forme da `test_load_rejects_other_pattern_forms`, che contiene ancora `**/*.sql`): copertura sufficiente.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e interfacce del brief rispettati alla lettera, test mirati e coerenti, nessun effetto collaterale sui chiamanti; solo rifiniture minori.
