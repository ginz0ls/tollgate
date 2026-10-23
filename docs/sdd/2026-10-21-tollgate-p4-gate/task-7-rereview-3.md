### Verdetti sui rilievi
- **N-3 (`encoding="bogus"` → `LookupError`)**: INDIRIZZATO. `parse_junit` (`bin/tollgate_analysis/junit.py:~92-95`) rilancia `JunitError` e converte `ExpatError`, `LookupError`, `UnicodeError` in `JunitError`. Verificato: `encoding="bogus"` dà `JunitError: unknown encoding: bogus`; `validate` e `read_results` restituiscono il problema `junit/a.xml: XML non valido: unknown encoding: bogus`, senza eccezioni. `runner.run_one` (`runner.py:133`) cattura già `JunitError`: esito `red`, `junit=None`. Test: `test_unknown_or_bad_encoding_is_junit_error`, `test_bogus_xml_encoding_is_a_problem`, `test_bogus_report_encoding_is_a_red_run_not_an_exception`, `test_any_exception_at_the_boundary_is_a_problem`, `test_load_returns_none_on_any_exception`; eseguiti `tests.test_junit tests.test_runner tests.test_gate_artifacts`: 36 OK.
- **N-4 (`stat()` non protetto)**: INDIRIZZATO. Nel giro dei file `artifacts.py` (`try/except OSError` attorno a `p.stat()`, problema per file e `continue`); nel giro dei JUnit `is_symlink/is_file/stat` sono dentro il `try` esistente. Test `test_stat_failure_after_is_file_is_a_problem`.

### Verifiche richieste
- Cattura ampia solo al bordo esterno: `_check`, `read_results`, `baseids.load` catturano `Exception` (non `BaseException`; `KeyboardInterrupt` passa), restituiscono `f"{type(e).__name__}: {e}"` (`load`: `None`), con commento di una riga. Le funzioni interne (`_check_tree`, `_read_results`, `_load`) restano senza cattura ampia.
- `junit.py`: la modifica tocca solo il ramo `except`; i JUnit validi non passano da lì, quindi l'esito è invariato. Il vecchio caso `ExpatError` produce lo stesso `JunitError` con lo stesso messaggio. `JunitError` sollevato dai gestori è rilanciato com'è (è un `ValueError`, non sottoclasse di `LookupError`/`UnicodeError`).
- Chiamanti di `parse_junit` (grep): `runner.py:133` (cattura `JunitError`, ora ne beneficia), `artifacts.py:99` e `:134` (catturano `ValueError`, compatibile), test di `flowkit`/`junit`. Nessuna incoerenza.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- `runner.py:133` cattura solo `JunitError`: un `RecursionError` da `parse_junit` non sarebbe gestito (XML annidato 100000 livelli è accettato da expat, quindi non riproducibile; solo nota).
- `artifacts.py:134` cattura ancora la lista stretta, ma sta dentro `_check`/`read_results`, quindi coperto dal confine.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
