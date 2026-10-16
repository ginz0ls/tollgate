# Task 5 - Analisi: livello e JUnit

**Status:** DONE
**Commit:** 7410a39 tollgate P2: analisi del livello e lettura sicura del JUnit

## Implementato
- `bin/tollgate_analysis/level.py`: `LEVELS`, `FileChange`, `max_level`, `sensitive_in`, `diff_level`, `labels_level`, `next_level`. Usa solo `globs.match_any`; nessun import di `tollgate_core`, `tollgate_hooks` o `tollgate_checks`.
- `bin/tollgate_analysis/junit.py`: `JunitError`, `Junit`, `parse_junit`. Rifiuta a monte qualunque `<!DOCTYPE` o `<!ENTITY` (regex sui byte, case-insensitive), poi parsa con `xml.etree.ElementTree`. Gli identificativi sono `classname::name`; un caso con `<skipped/>` va in `ids_skipped` e non in `ids_run`; `failure` o `error` lo portano in `ids_failed`.
- `tests/test_level.py` e `tests/test_junit.py`: il contenuto è quello del brief, alla lettera.

## Evidenza TDD
- RED: prima del codice, `python3 -B -m unittest tests.test_level tests.test_junit -v` termina con `ModuleNotFoundError: No module named 'tollgate_analysis.junit'` e `FAILED (errors=2)`.
- GREEN: `python3 -B -m unittest tests.test_level tests.test_junit -v` dà `Ran 9 tests ... OK`.

## Test
- `tests/run`, python 3.11.16: `Ran 202 tests ... OK` (193 preesistenti più 9 nuovi).
- `tests/run`, python 3.13.5: `Ran 202 tests ... OK`.
- Output pulito, nessun `__pycache__` (esecuzione con `-B`).
- Il test di isolamento di `tollgate_analysis` (`tests/test_analysis_isolation.py`) passa.

## File cambiati
- `bin/tollgate_analysis/level.py` (nuovo)
- `bin/tollgate_analysis/junit.py` (nuovo)
- `tests/test_level.py` (nuovo)
- `tests/test_junit.py` (nuovo)

## Scostamenti dal piano
Nessuno. Codice e test sono quelli del brief. Nessuna voce di `carry.md` riguardava il Task 5.

## Autorevisione
- Completezza: tutte le funzioni e le classi elencate in «Produces» sono presenti con le firme indicate.
- `next_level`: verificati a mano i tre casi del test (tetto che tiene, nuovo percorso sensibile che lo supera, nessun tetto).
- `junit`: il rifiuto di DOCTYPE/ENTITY avviene prima del parsing, quindi l'espansione di entità non è mai raggiunta.

## Dubbi
- `junit.parse_junit` rifiuta i DOCTYPE con una regex sui byte grezzi. Un report legittimo che contiene la stringa `<!DOCTYPE` dentro un CDATA verrebbe rifiutato. È un falso positivo accettabile per un report JUnit, ma è una scelta da tenere presente.
- `FileChange.status` non è usato dalla logica (il brief lo richiede come campo): resta disponibile per il Task 9.

## Fix round 1

**Commit:** b9a778e tollgate P2: JUnit con expat e tetto di dimensione (fix round 1)

1. DOCTYPE/entità con qualunque codifica. `junit.py` non usa più `ElementTree`: parsa con `xml.parsers.expat` e gli handler `StartDoctypeDeclHandler`, `EntityDeclHandler` e `ExternalEntityRefHandler` sollevano `JunitError` prima di qualunque espansione. Il regex sui byte resta come primo filtro, non come unica protezione.
   - Test RED: UTF-16 con BOM e DOCTYPE con entità (`test_utf16_bom_doctype_rejected`) fallisce con il vecchio codice. UTF-8 con BOM e DOCTYPE (`test_utf8_bom_doctype_rejected`) passa già col regex, quindi copre solo il ramo del filtro.
   - `test_doctype_rejected_by_parser_alone` disattiva il regex (patch di `junit._DANGER`) e verifica che il parser rifiuti da solo UTF-8 e UTF-16. Fallisce con il vecchio codice.
   - `test_utf16_and_utf8_bom_without_doctype_parse`: documenti validi con BOM UTF-16 e UTF-8 restano parsabili (`total=4`).
2. Tetto di dimensione: `MAX_BYTES = 32 * 1024 * 1024`, parametro `max_bytes` opzionale su `parse_junit`. Messaggio: «report JUnit troppo grande». Test: `test_size_limit` (RED: `TypeError` sul parametro) con un limite ridotto, più la verifica della costante.
3. Radice diversa da `testsuite`/`testsuites`: `JunitError` (`test_wrong_root_rejected`, RED: restituiva `total=0`). Aggiunto anche il rifiuto di un `testcase` annidato (`test_nested_testcase_rejected`), perché il nuovo parser tiene un solo caso aperto.
4. Byte vuoti e non decodificabili: `test_empty_bytes_rejected`, `test_undecodable_bytes_rejected`. Passano già, il test fissa il comportamento.
5. Docstring di `level.diff_level`: contratto di `changes` (include i file non tracciati) e di `diff_bytes` (diff unificato dalla base più la dimensione dei file nuovi non tracciati, decisione 18).

Il dubbio sul falso positivo del regex del report precedente non vale più come descritto: il regex ora è solo un filtro iniziale, e il parser rifiuta il DOCTYPE anche se il regex non lo vede.

Test (eseguiti dopo il fix):
- `python3 -B -m unittest tests.test_junit tests.test_level -v`: `Ran 18 tests ... OK`
- `tests/run`, python 3.11.16: `Ran 211 tests ... OK`
- `tests/run`, python 3.13.5: `Ran 211 tests ... OK`
