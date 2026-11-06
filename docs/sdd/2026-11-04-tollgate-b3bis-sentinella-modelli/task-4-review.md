# Revisione Task 4 (d828afe..30f2ae1)

### Aderenza
- ✅ D4: `cli.py:85-90` (spento / nessun file / nessun avviso), uscita 0; test per i due casi (`tests/test_cli.py` `test_models_check_component_off_says_so`, `..._without_files_says_so`, `..._keeps_the_check_lines`). `start` invariato nel resto.
- ✅ D7: `cli.py:61-81` usa `toplevel`, `main_worktree`, `origin_url`, `default_ref`; `ConfigError` (include `ConfigNotFound`) -> `rifiuto: configurazione non valida: …`, 1. Testati fuori repo, senza origin, senza toml su origin, tipo sbagliato.
- ✅ Ritorno prima di `db.open_db` (`cli.py:111-114`); `test_models_check_does_not_open_db`. Import di `models_check` solo dentro `_models_check` in `cli.py`. In `start.py:154` l'import di `models_check` è di modulo (come i fratelli `housekeeping`, `prereq`); `modelsfetch` non è importato in cima (⚠️ non verificato che `models_check` non lo importi a sua volta: è del Task 3).
- ✅ `_create` soltanto (`start.py:176`), non `_resume`; `test_resume_does_not_check`. `show_cache=False`.
- ✅ D16: nessuna stringa `tollgate models …` nelle stringhe di `bin/`; `help` come da decisione. D29: nei testi per l'utente «controllo dei modelli», nessuna «sentinella» da sola.
- ✅ D28: voce «Modelli» in coda all'elenco degli avvisi (`SKILL.md`), con «dati, non istruzioni».
- ✅ Documentazione: variabili e ordine, perché la variabile dedicata, chiave leggibile da ogni comando, nessun token, quattro host, proxy, cache di un giorno e `--refresh`, cosa non si controlla per fornitore, tipo sbagliato = errore di configurazione, subagente può lanciarlo, non dalla copia in `.github/tollgate/`, nomi senza virgolette non visti. Coerenti con `models.py:13` (tre tipi di virgolette) e con D4/D7/D8.
- ✅ Test in-process sotto `no_network()`, `PLUGIN_ROOT` temporaneo; nessuno usa `FlowLab.cli`/`run_cli`. Test sui subagenti in `test_check_cli_calls.py` (scostamento dichiarato, accettabile).
- ❌ D8 (forma dei fetch finti `fetch(provider, key, *, deadline)`): `test_start_succeeds_when_check_fails` usa un `mock.Mock` senza firma (`tests/test_start.py:607`), quindi non verifica la forma di chiamata. Minor.

### Punti di forza
Il ramo `models` è piccolo e ritorna presto; rifiuti coerenti con `start`; i test coprono i casi di D4 e D7; la documentazione è in parole semplici e coerente col codice; il report è onesto su incidente e scostamenti.

### Rilievi
**Important**
1. `tests/test_start.py:1268` (`self.assertEqual(calls[0][1], os.environ)`) e `tests/test_cli.py:504` (`self.assertEqual(calls[0][2]["environ"], os.environ)`): se falliscono, unittest stampa il diff di due mapping che sono `os.environ`, cioè l'intero ambiente (con eventuali segreti della macchina). È il rischio nominato nel brief e già successo all'implementatore. Correggere con un'asserzione che non mostra i valori: `self.assertIs(calls[0][1], os.environ)` stampa solo `repr` dell'oggetto `os.environ`, che mostra comunque l'ambiente; usare quindi `self.assertTrue(calls[0][1] is os.environ)` (messaggio fisso) o confrontare solo i nomi (`sorted(...)` non va bene se fallisce: usare `assertTrue(... is ...)`).

**Minor**
2. `cli.py:89`: con solo `Config.warnings` e nessuna riga di `check` non compare «nessun avviso» (dichiarato nel report); accettabile, ma la docs («oppure “modelli: nessun avviso”») non lo dice.
3. `tests/test_start.py:607`: finto `fetch_pages` senza firma di D8.
4. `tests/test_start.py:614`: `assertNotIn("sk-PROVA-123", …)` su fallimento stampa le righe; la chiave è finta, ma è un caso in cui un valore di chiave finirebbe nel messaggio se il codice la facesse uscire. Accettabile con chiave finta.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** implementazione e documentazione corrette e aderenti a D4/D7/D16/D28/D29; resta da sostituire le due asserzioni che, fallendo, stampano l'intero `os.environ` (requisito esplicito di cautela).
