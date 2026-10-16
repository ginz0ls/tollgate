# Task 8: Analisi: deroghe e report dell'implementatore

**Status:** DONE

**Commit:** `8871a33` tollgate P2: deroghe e report dell'implementatore; fix round 1 in `975bb06`

## Implementato

- `bin/tollgate_analysis/waivers.py`: `TYPES`, `Waiver`, `WaiverFile`, `parse` (TOML validato, `ValueError` su input non valido), `dumps` (escape di `"`, `\` e caratteri di controllo), `next_id`, `status` (`valid` | `pending`), `covers`, `unresolved`, `path_for`. Le corrispondenze su percorsi usano `globs.match`; il confronto del `file` è letterale.
- `bin/tollgate_analysis/report.py`: `STATUSES`, `REQUIRED`, `ImplReport` con `.valid`, `parse_report` (ultimo oggetto JSON con chiave `status`), `is_turn_cut` (campo `harnessNoteCount` >= 1 più prefisso `NOTE: this agent stopped at its` sul primo blocco), `transcript_tokens` (input + cache_creation + output, una volta per `message.id`; `cache_read` escluso).
- `tests/test_waivers.py` e `tests/test_report.py`: il contenuto del brief, senza modifiche.

## Test

- RED (prima dei moduli): `python3 -B -m unittest tests.test_waivers tests.test_report -v` → errore di import su `tollgate_analysis.waivers` e `tollgate_analysis.report` (il brief indicava `ModuleNotFoundError`; l'errore è `ImportError` perché il pacchetto esiste già).
- GREEN mirato: 10 test, OK.
- Suite completa `tests/run`: `python3.11` (3.11.16) e `python3` (3.13.5), 297 test ciascuno (287 + 10), OK, output pulito.
- Isolamento (`test_analysis_isolation`): passa, i moduli importano solo stdlib e `tollgate_analysis`.

## Verifiche sui nomi del Task 6

- `testguard` produce `waiver_type` in {`test`, `ci`, `command`, `threshold`}: tutti in `waivers.TYPES`.
- `scope` non è prodotto da `testguard` (sta nel controllo di scope, fuori da questo task): è in `TYPES` come nel brief.
- Il kind `test_id_missing` è quello usato da `covers` per il confronto degli `ids`.

## Scostamenti dal piano

Nessuno. Il codice è quello del brief. `carry.md` non ha voci per il Task 8.

## Autorevisione

- Completezza: tutti i produces del brief (`TYPES`, `Waiver`, `WaiverFile`, `parse`, `dumps`, `next_id`, `status`, `covers`, `unresolved`, `path_for`, `STATUSES`, `REQUIRED`, `ImplReport`, `parse_report`, `is_turn_cut`, `transcript_tokens`) sono presenti con le firme indicate.
- Campione reale: `PostToolUse-Agent-maxturns-cut` ha `harnessNoteCount: 1` e `content[0].text` che inizia con il prefisso atteso; il test usa l'input reale e passa.
- Il caso «fake» di `test_turn_cut_from_real_sample` supera per il controllo su `harnessNoteCount` (il campione normale ha 0), non per il prefisso del testo: il test non isola il solo prefisso. Non modificato, perché il brief lo fissa.

## Dubbi per la revisione

1. Chiuso dal fix round 1: lo stato sconosciuto ora rende il report non valido (fail-closed).
2. `covers` confronta `file` in modo letterale e i `pattern` con `globs.match`; `globs.escape` non serve per i percorsi registrati. Da verificare solo se il Task 15 passerà un percorso con `[ ]` come pattern.
3. `parse` non rifiuta stringhe vuote per `file`/`pattern`. Non richiesto dal brief, non cambiato.

## Fix round 1

Richiesta del controller, da fare in TDD (un test che fallisce per ogni punto, poi la correzione).

- **I1 (decisione 9, nessun cambio di comportamento):** `unresolved` accetta anche le deroghe `pending`. Docstring aggiornato con il riferimento alla decisione 9. Test `test_pending_waiver_still_covers_locally`: deroga `test` con `pattern="**"` risulta `pending` in `status` e copre la violazione in `unresolved`. Il test passava già perché documenta il comportamento voluto.
- **I2 (`covers`):** se la violazione ha `ids`, servono tutti in `w.tests`, per ogni `kind` (incluso `test_deleted`). Senza `ids` basta una deroga dello stesso tipo sullo stesso file o pattern. Test `test_test_deleted_needs_all_ids` (RED: `True is not false`) e `test_violation_without_ids_needs_same_type_and_path` (già verde, documenta il caso).
- **I3 (`report.py`, fail-closed):** `status` normalizzato con `strip().upper()`; uno stato fuori da `STATUSES` dà `unknown_status=True` e `valid=False`. Il test del brief `test_unknown_status_counts_as_done` è stato sostituito da `test_unknown_status_is_invalid`. Test aggiunti: `test_status_is_normalized` (`" blocked "` diventa `BLOCKED`, valido).
- **I4 (`transcript_tokens`):** `_count` conta solo `int` non `bool`; stringhe, liste, `1e999` (float infinito) e bool si saltano. Test `test_transcript_tokens_skips_malformed_usage`: atteso 2 (solo `input_tokens: 2`). RED: `ValueError: invalid literal for int()`.
- **I5 (`parse`):** `waiver` non lista solleva `ValueError` in italiano. Test `test_parse_rejects_non_list_waiver` con `waiver = 5` e con `[waiver]` come tabella singola. RED: `TypeError`.
- **Minore, `parse_report`:** preferisce l'oggetto con tutti i campi `REQUIRED`. Test `test_prefers_object_with_all_required_fields` con `extra: {"status": "BLOCKED"}` (RED: restituiva `BLOCKED`).
- **Minore, `waivers.parse`:** id duplicati rifiutati. Test `test_parse_rejects_duplicate_ids` (RED: nessun errore).
- **Minore, `is_turn_cut`:** `harnessNoteCount` deve essere `int` e non `bool`. Test `test_turn_cut_requires_int_count_and_prefix`: `harnessNoteCount=1` con testo diverso dà `False`; `harnessNoteCount=True` dà `False`.

**Comando:** `python3 -B -m unittest tests.test_waivers tests.test_report`
**Esito RED:** 6 failure e 2 error sui test nuovi (prima della correzione).
**Esito GREEN:** `Ran 19 tests ... OK`.

**Comando:** `tests/run` (python3.11 e python3)
**Esito:** `Ran 306 tests` su entrambi, `OK`, output pulito (306 = 297 precedenti + 9 nuovi).

**File:** `bin/tollgate_analysis/waivers.py`, `bin/tollgate_analysis/report.py`, `tests/test_waivers.py`, `tests/test_report.py`.
