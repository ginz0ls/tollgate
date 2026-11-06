# Revisione Task 1: confronto puro dei modelli (a7db942)

### Aderenza
- ✅ Interfacce del brief: `PROVIDERS`, `ModelInfo` frozen con i sette campi, `ModelsFormatError(ValueError)`, `parse_pages`, `literals`, `used`, `gemini_family`, `findings` con la firma richiesta (`models.py:12,38-45,157,196,209,235`).
- ✅ Decisione 2: charset `{1,127}` dopo il primo carattere (`models.py:15`), `@` escluso, tre tipi di virgolette scansionate in modo indipendente (l'apostrofo di un commento non copre le virgolette), `_norm` su elenco e letterali (`models.py:56-60`), eccezione `claude-…` / `gemini-<cifra>` (`models.py:226-232`).
- ✅ Carry Step 0 (a): regola degli alias implementata solo per Anthropic (`models.py:205-209`), riga «alias di …» (`models.py:219`); `test_alias_and_vertex_ids_not_flagged` presente.
- ✅ Decisione 3: Anthropic (line, active, deprecated, epoca, `line` null), Gemini (variante/versione numerica, suffissi, stabilità, `*-latest`), OpenAI/OpenRouter solo ritiro; righe «non controllato» una per fornitore e solo con modelli in uso (`models.py:244-255`).
- ✅ Decisione 13: forme delle righe per modello e per fornitore; `_plain` identico a `init._plain` (`bin/tollgate_flow/init.py:85`) su ID, file, page; data ridotta a `AAAA-MM-GG`.
- ✅ D19: `gemini-3.7-flash-preview-tts` instabile (`models.py:75`) e mai proposto (`test_gemini_newer_stable_only`); `(3,)` più vecchia di `(3, 6)` (`test_gemini_shorter_version_is_older`).
- ✅ D20: `lifecycle` non stringa -> non stabile, non in ritiro (`models.py:104-107`, `test_parse_anthropic`, `test_anthropic_non_string_lifecycle_never_newer_nor_retiring`).
- ✅ Vincoli: solo `re` e `dataclasses`, nessuna rete, nessun import di tollgate; nessuna chiave nei test; ID dei test inventati (salvo `claude-3-opus-20240229` e `gemini-2.5-flash-preview-09-2025`, citati dal brief stesso).
- ✅ Evidenza dei test: `task-1-suite.out` leggibile, 3431 test OK su 3.11 e 3.13, EXIT=0, nessun ResourceWarning.
- ⚠️ Non verificabile dal diff: `test_analysis_isolation` e `test_layers` (le dichiara verdi il report; coerente con gli import del file).

### Punti di forza
- Modulo piccolo, puro, con un solo punto di neutralizzazione; catena `used -> findings` provata end-to-end da `run()` nei test.
- Test oltre il brief e centrati sul comportamento (alias più recente, solo Anthropic, newer sceglie il più nuovo, letterali non a cavallo di riga, controllo `\x1b`/`\n`/`\x07`).
- Pagine finte inventate, nessun testo dei fornitori.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `models.py:98,104` `line` stringa vuota: `family=""` non è `None`, quindi `_newer_anthropic` (`models.py:178`) confronterebbe tra loro modelli con `line` vuota. Correggere con `_text(...) or None`.
2. `models.py:219,222` ID e `retires` di un elenco esterno non hanno tetto di lunghezza (il letterale invece è al più 128). `_plain` toglie i controlli ma non limita: una riga può essere enorme. Valutare un troncamento in `_plain` o al Task 3/4 (tetto righe).
3. `models.py:196,235` il parametro `literals` oscura la funzione `literals` nello stesso modulo (leggibilità; la firma è però imposta dal brief).
4. `tests/test_models.py:343` `assertRaises(Exception)` troppo largo: usare `dataclasses.FrozenInstanceError`.
5. `models.py:128,141` OpenAI e OpenRouter hanno `stable=False` per tutti i modelli: ininfluente oggi, ma chi in futuro filtrasse su `stable` li escluderebbe tutti. Documentarlo nel docstring di `ModelInfo` o nel Task 2/3.
6. `models.py:178-180` il confronto `created` è fra stringhe: vale solo con formati omogenei (RFC 3339 di Anthropic, oggi vero).
7. Il report dice di dare per scontato che `findings` riceva `infos` di un solo fornitore: nel Task 2 il chiamante deve rispettarlo (`used` indicizza per `_norm(id)` senza guardare `provider`).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti, decisioni 2, 3, 13 e i carry D19/D20/alias sono implementati e coperti da test che asseriscono il comportamento; nessun difetto bloccante, solo rifiniture minori.
