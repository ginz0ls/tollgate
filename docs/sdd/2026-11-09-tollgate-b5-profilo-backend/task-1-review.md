# Revisione Task 1 (3599245) - esclusione per frammento

### Aderenza
- ✅ `Fragment.exclude: tuple[str, ...]`, default `()` (`bin/tollgate_core/fragments.py:50`); chiave letta in `_parse` (righe 89-100) con `_EXCLUDE` costruita sui segmenti di `_SEGMENT` più `/` finale (riga 25). Le dieci forme errate del piano sono respinte (segmento non vuoto, `*?[]!\` vietati, `.`/`..` vietati dal lookahead). Il messaggio nomina file ed `exclude`; `other` dà ancora «sconosciuta».
- ✅ D4: `_match` e `_is_detectable` prendono `exclude` (`init.py:~211`, `~257`); `concrete_for` e `_concrete_paths` lo passano; `detect_files` usa `fragment.exclude`; `profile_blocks` filtra `lighting` e `found`; `_drift` riceve liste già filtrate. Con `exclude` vuoto `startswith(())` è False: comportamento di B4 invariato.
- ✅ L'esclusione vale solo per il frammento che la dichiara (letta da `fragment.exclude`); `ai` e `infra` non cambiano; non tocca `_OPS`, né gli strati, né scrive `tollgate.toml`.
- ✅ D3: i due test di guardia sono nuovi (`tests/test_fragments.py`, `tests/test_init.py` `test_concrete_for_exclude_default_is_b4`); `test_load_rejects_bad_shape` invariato.
- ✅ D4: `test_detect_files_honours_exclude` in `DetectTest` con repo git vero, con confronto senza e con `exclude`.
- ✅ D5: nessun marcatore di contenuto né nome Supabase diverso da `supabase/` nei testi nuovi di `bin/`. Frase in `docs/uso/comandi.md` senza `backend` e senza «tollgate init» nudo.
- ✅ Scostamento dichiarato (`/server/**`, forma root_folder di B4) coerente col comportamento esistente.
- ⚠️ Evidenza della suite (3677 OK su 3.11 e 3.13) solo dal report; non rilanciata come da regole.

### Punti di forza
- Modifica chirurgica, firme retrocompatibili (`exclude=()`), nessuna nuova struttura.
- Test su tutti i punti toccati: parse, forme errate con asserzione sul messaggio, solo-il-proprio-frammento, drift, detect su git vero.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `init.py:218,260`: `tuple(exclude)` ricostruito a ogni file; innocuo, ma si può normalizzare una volta (`Fragment.exclude` è già tupla).
2. `init.py:369-372`: `skip` e `concrete_for(..., fragment.exclude)` duplicano il controllo dei prefissi con `_match`; accettabile (due liste diverse), ma `_drift` passa `fragment.exclude` a `_concrete_paths` su file già filtrati (ridondante, innocuo).
3. `fragments.py:25`: `[^/...]` ammette anche newline nei segmenti di `exclude`; forma TOML improbabile, nessun danno.
4. Nessun test con due prefissi o con un prefisso a più segmenti (`a/b/`) nel comportamento di `init` (il parse lo copre); aggiunta facoltativa.
5. Documentazione della chiave nella spec 11.4 non fatta qui: da lasciare al Task 9, come da decisione 4.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e decisioni D3-D5 rispettati, comportamento B4 invariato con `exclude` vuoto, test che asseriscono il comportamento reale; solo rifiniture Minor.
