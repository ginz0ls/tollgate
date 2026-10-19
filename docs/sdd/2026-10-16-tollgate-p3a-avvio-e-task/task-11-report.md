# Task 11 - report

## Implementato
- `statusline/ctx` (bash, 100755): legge stdin (conserva il newline finale), ricava `session_id` e `context_window.used_percentage` con `python3 -c` (fallback `sed` se manca Python), scrive in modo atomico (`.tmp` + `mv`) `<stato>/ctx/<session_id>.json` = `{"used_pct": N|null}`, poi esegue `sh -c "$*"` con lo stesso stdin e ne restituisce l'uscita (C21). Senza argomenti non stampa nulla.
- `<stato>` è `$TOLLGATE_STATE` solo con `.tollgate-test`, altrimenti `~/.local/state/tollgate`.
- `session_id` fuori da `^[A-Za-z0-9_-]+$` (o vuoto) non scrive nulla. Valore non numerico (anche stringa o bool) diventa `null`.
- Ogni errore di parsing/scrittura: nessun file, il comando avvolto gira comunque (`write_ctx ... || true`).
- `tests/test_statusline.py`: 14 test (i 6 del brief più: float, non numerico, pipe C21, codice d'uscita, input non JSON, stato non scrivibile, nessun comando, eseguibile).

## TDD
- RED: `python3 -B -m unittest tests.test_statusline` prima del file `ctx`: `FAILED (failures=1, errors=17)`.
- GREEN: stesso comando: `Ran 14 tests ... OK`.
- Completo: `tests/run`: python3.11 e python3 (3.13.5), 969 test, OK in entrambi.
- Prova manuale del ramo senza Python (PATH con soli bash/sh/cat/sed/tr/mkdir/mv/rm/printf, stato temporaneo): `{"used_pct": 33.5}`.

## Scostamenti dal piano
Nessuno. Nessun test tocca lo stato o la configurazione reali (TempState + HOME temporanea).

## Dubbi
Nessuno.

## Fix round 1
- Important: il `session_id` è validato dentro Python con `re.fullmatch(r"[A-Za-z0-9_-]+")` (altrimenti nessun output e nessun file); Python emette una sola riga `<sid> <pct>`, quindi nessun valore può spezzarsi. `"a\nb"` e `"a\n77\n"` aggiunti a `test_unsafe_session_ignored`.
- Percentuale accettata solo tra 0 e 100 (fuori, `1e+20` e NaN -> null), in entrambi i rami. Nel ramo sed la regex richiede che il numero non sia seguito da `[0-9.eE]`, così `1e+20` non diventa `1`.
- Nuovi test: `test_null_when_out_of_range`, `test_without_python_uses_sed` (PATH ridotto senza python3, con 100, 150, -3, null, 1e+20 e id con newline).
- RED: `python3 -B -m unittest tests.test_statusline` -> `FAILED (failures=7)` prima della correzione. GREEN: `Ran 16 tests ... OK`.
- `tests/run`: python3.11 e python3 (3.13.5), 971 test, OK.
