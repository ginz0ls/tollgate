### Verdetti sui rilievi
- **N-1 (`RecursionError` su JSON molto annidato)**: INDIRIZZATO. `RecursionError` aggiunto in `_load_results` (`artifacts.py:36`), nelle due letture JUnit (`artifacts.py:90`, `:119`) e in `baseids.load` (`baseids.py:~45`). Provato con `"[" * 100000` e `'{"a":' * 100000`: `read_results` e `baseids.load` restituiscono problemi o `None`, nessuna eccezione. Test `test_deeply_nested_results_json_is_a_problem` e `test_load_rejects_deeply_nested_json`.
- **N-2 (doppia lettura di `results.json`)**: INDIRIZZATO. `read_results` usa `_check` (`artifacts.py:60-96`, `:104`), una sola lettura; se `data is None` restituisce problemi senza `TypeError`. Test `test_results_json_is_read_once`.

### Danni nuovi nel diff della correzione
Nessuno introdotto dal diff. Resta pero un buco dello stesso tipo, che il ruling chiedeva di chiudere («nessuna lettura solleva con un ingresso ostile»):
- **Important, N-3** `artifacts.py:88` e `:117` (via `bin/tollgate_analysis/junit.py:~95`). Un JUnit con dichiarazione XML `encoding="bogus"` fa sollevare `LookupError: unknown encoding` da `parser.Parse` (non e' `ExpatError`, non e' `ValueError`, non e' `OSError`). Verificato: `read_results` su una cartella con `junit/a.xml` = `<?xml version="1.0" encoding="bogus"?><a/>` e `results.json` valido alza `LookupError`; `validate` fa lo stesso. Il file e' prodotto dalla PR (non fidato). Correzione minima: `LookupError` nei due `except` di `artifacts.py` (o convertirlo in `JunitError` in `parse_junit`, dove il difetto nasce: lo stesso `runner.py:133` ne soffre). Test: JUnit con `encoding="bogus"`.
- **Minor, N-4** `artifacts.py:~65` e `~86`: `p.stat()` dopo `is_file()` nel `os.walk` e nel ciclo JUnit non e' protetto; un file rimosso tra controllo e `stat` alza `FileNotFoundError` (finestra stretta, artefatto scaricato non vivo). Non bloccante.

Controllati e privi di problemi: JSON non UTF-8 (`UnicodeDecodeError` e' `ValueError`), XML annidato 100000 livelli (expat, ok), `state` non hashable (STATES e' tuple, ok), voce con annidamento ~900 nel `repr` (ok), `tests_run` enorme, report che e' una cartella (`OSError`), `baseids.load` su non UTF-8 e su cartella.

### Osservazioni fuori ambito
`LookupError` nasce in `tollgate_analysis/junit.py` (P2), usato anche da `tollgate_core/runner.py:133`.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti. N-1 e N-2 sono indirizzati, ma resta un danno Important di stesso tipo (N-3, `LookupError` da encoding XML sconosciuto nei JUnit), correzione di una riga con test.
