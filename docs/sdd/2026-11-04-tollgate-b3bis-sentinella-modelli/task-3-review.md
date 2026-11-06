# Revisione Task 3 (B3-bis): sezione [models] e controllo dei modelli

Commit rivisto: ff55402 (a62a9e9..ff55402). Sola lettura; un solo controllo eseguito (`load_config_text` con `files = [1]`, `[["a"]]`, `[true]`: tutti `ConfigError`, nessun crash nel filtro).

### Aderenza
- ✅ `DEFAULTS["models"]`, `components.models_check`, `MODELS_MAX_FILES = 20` (`config.py:13,90,98`).
- ✅ Filtro dei percorsi (D1, D9): assoluti, segmenti `.`/`..`/vuoti, `*`, `?`, caratteri fuori da alfanumerici e ` ._/-@+[]`; avviso con `repr` troncato a 80, senza a capo; tetto contato solo sulle voci valide, un solo avviso (`config.py:211-232`, test `config.py` ModelsSectionTest).
- ✅ D2: tipo sbagliato = `ConfigError` generico, nessun caso speciale (verificato anche per liste con elementi non stringa: la verifica di tipo di `_set_key` li ferma prima del filtro).
- ✅ `git.object_info_at` decide dal codice d'uscita, `_check_ref` prima, symlink = blob, test con locale italiano (`git.py:294-308`).
- ✅ D10: componente spento -> `[]`; `files` vuoto -> `[]` o solo il promemoria `ai`; `load_providers` solo dopo (`models_check.py:104-111`); test con radice senza `templates/`.
- ✅ File letti da `ref` con `object_info_at` -> tetto 256 KiB senza passare da `git.show` -> byte nullo; tipo non blob -> «non è un file» (`models_check.py:36-54`); test `test_reads_files_from_ref_not_worktree`, `test_binary_or_large_file_line` (asserisce che `show` non vede il file grande).
- ✅ Chiave: solo passata a `fetch`; nelle righe c'è il testo fisso di `FetchError` o il nome della classe; test con chiave dedicata, cache senza `sk-`, eccezione con la chiave nel testo.
- ✅ Righe: forma esatta della D13, ordine D6 (per modello di tutti i fornitori, per fornitore, generali), `MAX_LINES = 12` con «modelli: … e altri N avvisi» (`test_lines_capped`: 12 + 1).
- ✅ Una sola `Deadline(DEADLINE_S, clock)` creata dopo la lettura dei file; fornitori saltati con la riga D13 (`test_deadline_skips_remaining_providers`).
- ✅ Nessuna rete con componente spento, `files` vuoto, senza chiavi, o senza letterali (extra non richiesto, ragionevole).
- ✅ `models.parse_pages` (anche dentro `validate`), `git.object_info_at`, `git.show`, `modelsfetch.cached_pages` chiamati via modulo; patch dei test efficaci. Parametro `clock=` (D18). `fetch` finti a forma `fetch(provider, key, *, deadline)` (D8).
- ✅ Gate: `components_off` itera su `ctx.components`; il nuovo componente è `True` di default, quindi nessun test o voce del gate cambia.
- ❌ **`modelsfetch` importato in cima a `models_check`** (vedi Important 1).
- ⚠️ `start`/`cli` non ancora collegati (Task 4): non verificabile qui.

### Punti di forza
- `check` ha un solo punto di cattura, con la sola classe dell'eccezione nel messaggio: nessuna fuga di URL o chiave.
- `_plain` su nomi di file e ref; ID e pagina passano già da `models._plain` in `findings`.
- Test ben scritti: `no_network()`, radice del plugin temporanea, verifica che la cache non venga scritta con una forma sbagliata, che `show_cache=False` tolga solo la riga fresca, che la chiave dedicata prevalga.
- Il filtro dei percorsi è piccolo, in un solo posto, e testa sia le voci cattive sia le buone (`[id]`, spazio, `@+`).

### Rilievi

**Important**
1. `bin/tollgate_flow/models_check.py:17` — `from tollgate_flow import modelsfetch` in cima al modulo. Il brief del Task 2 (`task-2-brief.md:30`) e il suo report (riga 31) stabiliscono che `models_check` importa `modelsfetch` **dentro `check`**, perché `hooks/run` e `cli` non devono caricare `urllib`/`ssl` (`test_hook_run_does_not_load_models_net`, `cli.py` importa `models_check` solo nel ramo `models`) e per la nota D6 sull'ordine d'import sotto `no_network()`. Il test oggi passa solo perché nessuno importa ancora `models_check`; appena il Task 4 farà importare `models_check` a `start.py` in cima (o a `cli.py`), il modulo di rete entrerà in ogni processo di hook. Correzione: spostare l'import in `check` (o in `_check`) e passare il modulo/`FetchError` ai due helper, oppure importare in `_provider_lines`/`_wanted`/`_check` con import locale; i tipi nelle firme restano stringhe grazie a `from __future__ import annotations`. Aggiungere un test (processo figlio, come `test_hook_run_does_not_load_models_net`) che importa `models_check` e verifica che `modelsfetch` non sia in `sys.modules` finché non si chiama `check`.

**Minor**
2. `models_check.py:60` — uso della funzione privata `models._norm` da un altro modulo. Meglio una funzione pubblica in `models.py` (per esempio `matches_hint(hint, literal)`) che tenga insieme normalizzazione e `re.fullmatch`: la regola della D4 «sul letterale normalizzato» resta in un punto solo.
3. `models_check.py:84-86` — la riga «per fornitore» si separa dalle righe per modello assumendo che sia l'ultima di `findings` quando `matches and name != "anthropic"` (`models.py:254`). Funziona (e `_NOT_CHECKED` contiene tutti e tre i non-Anthropic), ma è un accoppiamento implicito: se `findings` cambia, una riga per modello finisce tra quelle per fornitore senza che nessun test lo noti per OpenAI e OpenRouter (c'è solo il caso Gemini). Meglio che `models.findings` esponga le due liste separate, o almeno un test per OpenAI e OpenRouter.
4. `tests/test_models_check.py:28-41` — `providers_toml()` deriva dal `templates/models.toml` vero (solo gli host sono sostituiti): `test_some_keys_missing_lines` asserisce l'elenco esatto di variabili del file vero. Il vincolo dice «radice temporanea con un `templates/models.toml` dagli host `.invalid`». Una copia scritta nel test (4 tabelle brevi) isolerebbe i test da modifiche future del file di dati.
5. `models_check.py:146` — «1 avvisi» con N=1 (la report lo dichiara; è la forma fissa della D13): accettabile, solo da sapere.
6. `config.py:208` — `str.isalnum()` ammette lettere e cifre non ASCII; coerente con «lettere, cifre» della D1, nessuna azione.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** implementazione solida e ben testata, aderente a D1-D13, D2, D8-D10, D18; ma l'import di rete in cima a `models_check` rompe il contratto del Task 2 (hook senza rete) e scoppierà al collegamento del Task 4. Basta una correzione piccola (Important 1); i Minor sono a scelta.
