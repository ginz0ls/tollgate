# Task 6 - Analisi: test-guard

**Status:** DONE
**Commit:** bf5c315 tollgate P2: test-guard con identificativi statici per linguaggio

## Implementato
- `bin/tollgate_analysis/scan.py`: `js_tokens`, `js_code` (stringhe come `S`), `py_code` (usa `tokenize`; `None` su errore di tokenizzazione, incluso `ERRORTOKEN` per stringa non chiusa).
- `bin/tollgate_analysis/testids.py`: `language`, `test_ids` con rami JS (vitest con `" > "`, jest con `" "`, frame di `describe`/`suite`/`context`, `x*` e `.skip/.todo/.fixme` come saltati), Python (`ast`, funzioni `test*`, classi `Test*` o che ereditano da `*TestCase`, decoratori con `skip|xfail`), Go (`func TestX`).
- `bin/tollgate_analysis/testguard.py`: `DEFAULT_TEST_GLOBS`, `Violation`, `Change`, `GuardConfig`, `GuardResult`, `check`. Confronti dei percorsi solo con `globs.match_any`; nessun uso di `globs.compile`. Nessun import di `tollgate_core`, `tollgate_hooks`, `tollgate_checks`.
- `tests/test_testids.py` e `tests/test_testguard.py`: contenuto del brief alla lettera, tranne il caso Latin-1 (vedi sotto).

## Evidenza TDD
- RED: prima del codice, `python3 -B -m unittest tests.test_testids tests.test_testguard -v` termina con `Ran 2 tests ... FAILED (errors=2)` (import dei moduli mancanti). Il messaggio completo non è stato riportato in questo report.
- GREEN: `python3 -B -m unittest tests.test_testids tests.test_testguard -v` dà `Ran 18 tests in 0.012s` / `OK`.

## Test
- `tests/run`, python 3.11.16: `Ran 229 tests in 3.751s` / `OK`.
- `tests/run`, python 3.13.5: `Ran 229 tests in 4.130s` / `OK`.
- 229 = 211 preesistenti + 18 nuovi. Nessun `__pycache__` nel repo (esecuzione con `-B`).
- Il test di isolamento di `tollgate_analysis` è incluso nella suite e passa.

## File cambiati
- `bin/tollgate_analysis/scan.py` (nuovo)
- `bin/tollgate_analysis/testids.py` (nuovo)
- `bin/tollgate_analysis/testguard.py` (nuovo)
- `tests/test_testids.py` (nuovo)
- `tests/test_testguard.py` (nuovo)

## Scostamenti dal piano
- `test_binary_and_latin1_do_not_crash` (decisione C11 di `carry.md`): nel brief il file Latin-1 era il literal `"caff\xe8"`, cioè già un `str`, quindi non passava per byte non UTF-8. Ora il test parte da `raw = b"x = 'caff\xe8'\n"`, verifica con `assertRaises(UnicodeDecodeError)` che `raw.decode("utf-8")` fallisce, e passa a `check` il testo `raw.decode("latin-1")`. Motivo: `Change` riceve `str`; la decodifica dei byte è responsabilità del livello git (Task 9, `git._text`), che resta da coprire con il test C11 di quel task. Il test di Task 6 dimostra che il testo Latin-1 non fa crashare né `check` né `py_code`/`test_ids`.
- Nessun altro scostamento: codice e test sono quelli del brief.

## Autorevisione
- Completezza: presenti tutte le funzioni, classi e costanti elencate in «Produces» (`js_tokens`, `js_code`, `py_code`, `language`, `test_ids`, `DEFAULT_TEST_GLOBS`, `Violation`, `Change`, `GuardConfig`, `check`, `GuardResult`).
- Mappa dei `kind` → `waiver_type`: `test_deleted`, `test_id_missing`, `asserts_decreased`, `skip_added`, `unparsable`, `fixture_changed` → `test`; `ci_changed` → `ci`; `threshold_lowered` → `threshold`; `verification_changed` → `command`. Conforme al brief.
- Verificato a mano il frame dei `describe` (chiusura su `}` con `frames[-1][1] >= depth`) e il caso `xdescribe`, che marca come saltati anche i test figli e quindi produce anche `test_id_missing` (il test usa `assertIn`, quindi resta valido).
- `py_code` non solleva su stringhe non chiuse: `ERRORTOKEN` in 3.11, `TokenError` in 3.12+.

## Dubbi
- L'API riceve testo (`str`), non byte: il rischio di decodifica (byte non UTF-8 in file reali) va gestito dal chiamante, cioè dal Task 9. Se nel Task 9 la decodifica usasse `errors="strict"` senza ripiego, un file Latin-1 finirebbe in `None`; conviene verificarlo lì.
- `_test_file` per `status == "D"` ricava `ids` da `base[0].values()` e lascia la tupla vuota se la base non si legge. Comportamento coerente con il brief, ma i `ids` di `test_deleted` possono essere vuoti per file non parsabili.

## Fix round 1

**Commit:** c30d181 tollgate P2: test-guard, regex e template nello scanner, soglie rimosse, rete fail-closed (fix round 1)

### Important 1 - scanner JS/TS (`scan.py`)
- (a) Regex letterali: una `/` apre una regex se il token precedente è punteggiatura in `( , = : [ ! & | ? { } ; + - * % < > ~ ^` (anche `=>`, che finisce con `>`), oppure una parola chiave della lista, oppure è inizio file. La regex finisce alla `/` non escapata fuori da `[...]`, più i flag. Il contenuto non apre stringhe né commenti. Una regex che va a capo non è una regex (ripiego a punteggiatura).
- (b) Template: pila `braces` per i `${`; i template annidati e gli apici dentro `${}` non sfasano lo stato. I segmenti testuali emettono `str`, il codice interno token normali.
- (c) Apice JSX: `js_tokens(text, jsx=...)` e `js_code(text, jsx=...)`; con `jsx` vero, un `'` con lettera prima e dopo, non preceduto da parola chiave, non apre una stringa. Il flag è attivo per `.jsx`/`.tsx` (`testids._js`, `testguard._code`). In JSX, `/` dopo `<` è un tag di chiusura, non una regex.
- Test (rosso prima, poi verde): `test_expect_removed_after_tricky_lexing` e `test_skip_added_after_tricky_lexing` su cinque prefissi (regex con apice, regex con `//` in classe, `return /"/`, template annidato con apice, JSX con `don't`), con `it.skip` e `xit` aggiunti e `expect` tolto; `test_regex_literal_is_not_a_string`, `test_template_nested_quotes_do_not_shift_state`.
- `test_division_is_not_a_regex` passava già prima della correzione (non regressione).

### Important 2 - soglie (`testguard.py`)
- Una chiave presente nella base e assente nella testa vale come abbassata a 0 (`_lowered`).
- `_strip_comments` (`//`, `/* */`, `#`, `;` a inizio riga, rispettando le stringhe che non attraversano le righe) prima di leggere le soglie.
- `COVERAGE_CONFIG_GLOBS` (`.nycrc`, `.nycrc.json`, `.nycrc.yml`, `.coveragerc`, `jest.config.*`, `vitest.config.*`, `pyproject.toml`, `setup.cfg`, `package.json`, ovunque nel repo): il controllo delle soglie gira anche su questi file, anche se cancellati (testa vuota).
- Test: `test_threshold_removed_from_package_json`, `test_commented_threshold_counts_as_removed`, `test_nycrc_lowered`, `test_coverage_config_deleted`.

### Rete fail-closed (d)
- Asserzioni e salti contati sia sul codice ripulito sia sul testo grezzo; si tiene il caso peggiore (diminuzione massima per le asserzioni, aumento massimo per i salti).
- Test: `test_skip_still_flagged_when_python_scanner_fails` (con `py_code` simulato a `None` dà `skip_added` + `unparsable`).

### Minor
1. Se `py_code` restituisce `None` sulla testa, si emette `unparsable` invece di uscire in silenzio; il conteggio grezzo resta attivo.
2. Le f-string (3.12+) sono scartate come su 3.11 (`FSTRING_START`/`FSTRING_END` con profondità). Test: `test_fstring_expression_not_counted` (su 3.13 era rosso).
3. `test_binary_deleted_test` (`Change("D", "tests/a.test.ts", ..., binary=True)`) aggiunto; passava già col codice precedente.
4. Marcatori Python aggiunti: `.skipTest(`, `\bSkipTest\b` (copre `raise SkipTest` e `raise unittest.SkipTest`), `pytest.importorskip(`. Test: `test_python_skip_markers` su quattro forme.

### TDD
- RED: prima del codice, `python3 -B -m unittest tests.test_testids tests.test_testguard` dà `FAILED (failures=20)` su 31 test (20 rossi, tra cui i nuovi di scanner e di testguard). Il test `binary` e la divisione passavano già.
- GREEN: stesso comando, `Ran 31 tests` / `OK`.

### Test
- `tests/run`, python 3.11.16: `Ran 242 tests in 3.852s` / `OK`.
- `tests/run`, python 3.13.5: `Ran 242 tests in 4.270s` / `OK`.
- 242 = 229 precedenti + 13 nuovi. Nessun `__pycache__`.

### File cambiati
- `bin/tollgate_analysis/scan.py`, `bin/tollgate_analysis/testguard.py`, `bin/tollgate_analysis/testids.py`, `tests/test_testguard.py`, `tests/test_testids.py`.

### Limiti residui (da decidere nel controllo)
- Il flag `jsx` è solo per `.jsx`/`.tsx`, come da controller. Un `.js` con JSX non ha la regola dell'apice: il conteggio grezzo copre comunque l'aggiunta di salti, ma un'asserzione tolta potrebbe non essere vista se lo scanner si sfasa.
- `/` dopo `)` o `]` resta una divisione: una regex che segue `)` (es. `if (x) /re/.test(y)`) non è riconosciuta. Caso raro; coperto dal conteggio grezzo per i salti.
- `_strip_comments` tratta `#` come commento anche dentro un valore non quotato in formati non JSON (YAML con `#` nel valore): una soglia dopo `#` sulla stessa riga può sfuggire.

## Fix round 2

**Commit:** 68c57bd tollgate P2: commenti per formato nelle soglie, stringhe a fine riga, soglie fail-closed (fix round 2)

### Important - regressione di `_strip_comments` su INI/TOML/YAML (`testguard.py`)
- Causa: il giro 1 toglieva `/* */` e `//` in ogni file. In `.coveragerc` il glob `*/tests/*` apriva un commento di blocco che cancellava il resto del file, `fail_under` compreso.
- (a) `_strip_comments(text, path)` è ora per formato. Per `.js`, `.cjs`, `.mjs`, `.ts`, `.cts`, `.mts`, `.json`, `.jsonc` toglie `//` e `/* */`. Per tutti gli altri (`.coveragerc`, `setup.cfg`, `.toml`, `.yml`/`.yaml`, `.nycrc` senza estensione) toglie solo `#` e `;` quando sono a inizio riga o preceduti da spazio o tabulazione. Le stringhe non attraversano le righe.
- (b) `_lowered(base, head, path)` calcola le soglie sia sul testo pulito sia su quello grezzo, per base e testa. Una chiave presente nella base e assente nella testa, o abbassata, in una delle due letture conta come violazione (unione dei casi peggiori).
- Test (rosso prima del codice, poi verde):
  - `test_coveragerc_lowered_after_star_slash_glob`: `.coveragerc` con `*/tests/*`, `fail_under` da 80 a 10, dà `threshold_lowered`.
  - `test_setup_cfg_lowered_after_star_slash_glob`: stesso caso in `setup.cfg` con `[coverage:report]`.
  - `test_unchanged_coveragerc_with_star_slash_glob_is_clean`: `.coveragerc` invariato con `*/tests/*` non dà violazioni (passava anche prima, è un test di regressione).
  - `test_commented_threshold_in_nycrc_json_counts_as_removed`: `//` su `.nycrc.json` continua a valere come commento (passava già).
- Scostamento: `test_commented_threshold_counts_as_removed` usava `//` su `packages/web/.nycrc`. Per la regola (a) `.nycrc` senza estensione non è C-like, quindi lì `//` non è un commento. Il test ora usa `#` su `.nycrc`. Il caso `//` è coperto su `.nycrc.json`.

### Minor - stringhe non terminate (`scan.py`)
- Una stringa `'` o `"` non terminata finisce a fine riga, come in JS. Un possessivo JSX come `<p>users' list</p>` non sfasa più il resto del file.
- Test (rosso prima, verde dopo): `test_unterminated_string_ends_at_line_end` in `tests/test_testids.py`. Dopo la `'` non terminata, il token `it` della riga successiva compare.
- I template restano fuori da questa regola: una backtick può andare su più righe.

### TDD
- RED: `python3 -B -m unittest tests.test_testids tests.test_testguard` prima del codice: `FAILED (failures=3)` su 36 test, cioè i tre test di `.coveragerc`, `setup.cfg` e della stringa a fine riga.
- GREEN: stesso comando, `Ran 36 tests` / `OK`.

### Test
- `tests/run`, python 3.11.16: `Ran 247 tests in 1.655s` / `OK`.
- `tests/run`, python 3.13.5: `Ran 247 tests in 1.551s` / `OK`.
- 247 = 242 precedenti + 5 nuovi. Nessun `__pycache__`.

### File cambiati
- `bin/tollgate_analysis/scan.py`, `bin/tollgate_analysis/testguard.py`, `tests/test_testguard.py`, `tests/test_testids.py`.

### Limiti residui
- Nei formati non C-like, un `#` preceduto da spazio dentro un valore non quotato (es. `omit = a #b`) viene letto come commento. Per la lettura grezza della rete fail-closed questo non nasconde soglie: la soglia resta visibile nel testo grezzo.
