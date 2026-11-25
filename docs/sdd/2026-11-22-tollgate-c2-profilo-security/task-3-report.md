# Task 3: report dell'implementatore (opus)

**Status:** DONE
**Commit:** `e27db19` tollgate C2: keep_paths, un frammento che accende i suoi percorsi anche per i file trovati da un altro

## Cosa ho fatto

- `bin/tollgate_core/fragments.py`: campo `Fragment.keep_paths: bool = False` in coda alla dataclass (l'unico punto di costruzione, `_parse`, lo passa per posizione). In `_parse` la chiave `keep_paths` entra nelle chiavi ammesse di `[detect]` accanto a `content` ed `exclude`. Il valore si controlla con `isinstance(valore, bool)` (D7): `1`, `0`, `"sì"`, `"true"`, `[true]` danno `FragmentError` con il nome del file: «<file>: [detect] keep_paths deve essere true o false».
- `bin/tollgate_flow/init.py`, `profile_blocks`: la condizione di `lighting` diventa `f in mine or f not in taken or fragment.keep_paths`. È una sola e vale per tutte le forme (cartelle, nomi, `ext`), perché `concrete_for` resta il filtro della forma. Il commento della regola di I-1 dice la deroga. `_drift` riceve lo stesso `lighting`, quindi la deroga vale anche nella deriva (D7).
- Non cambiano `vertical_for`, `task_routing`, `globs`, `parse_pattern`, `finalreview`, il gate, né alcun frammento vero.

## Test

Nuovi in `tests/test_fragments.py` (`FragmentsTest`): `test_keep_paths_default_false`, `test_keep_paths_true_read` (anche `false` esplicito), `test_keep_paths_not_bool_rejected` (cinque valori, con il nome del file, la parola `keep_paths` e non «sconosciuta»).

Nuovi in `tests/test_init.py` (`ProfileBlocksTest`), con l'helper `keep_paths_profiles(keep=True)`. Usa una radice temporanea di `PluginMixin.plugin` (radice del plugin esplicita, `TemporaryDirectory` con `addCleanup`) e due frammenti: `x` con `["**/auth/**", "**/guard.ts", "**/*.mjs"]` più `[detect] keep_paths = true`, e `y` con `["**/server/**"]` più un marcatore. I test:
- `test_keep_paths_lights_folder_of_file_found_by_other`: `server/auth/{login,token}.ts`, tutti e due rilevati da `y`: `x` propone `server/auth/**`, `y` propone `/server/**`.
- `test_keep_paths_lights_name_of_file_found_by_other`: `server/guard.ts` dà a `x` il percorso esatto.
- `test_keep_paths_lights_ext_of_file_found_by_other`: `server/app.mjs` dà a `x` il pattern `**/*.mjs`.
- `test_without_keep_paths_rule_i1_unchanged`: lo stesso albero senza la chiave (le tre forme una per una e tutte insieme) non dà nessun blocco `x` e dà la riga «nessun file». Senza rilevamento `x` si accende come prima, il che prova che la regola è proprio quella di I-1.
- `test_keep_paths_does_not_change_other_fragment`: il blocco `[profiles.y]` è identico con e senza la chiave, sia come TOML letto sia come testo. Lo è anche la riga «proposto con». Si veda lo scostamento 1.
- `test_keep_paths_lights_in_drift_too` (D7): con `x` già dichiarato, `init --update` propone `paths: aggiungi "server/auth/**" (1 file)`; senza la chiave nessuna riga «paths: aggiungi».

### RED

`python3 -B -m unittest tests.test_fragments tests.test_init` prima del codice:
```
ERROR: test_keep_paths_default_false ... AttributeError: 'Fragment' object has no attribute 'keep_paths'
ERROR: test_keep_paths_true_read ... FragmentError: ai.toml: chiave sconosciuta in [detect]: keep_paths
ERROR: test_keep_paths_does_not_change_other_fragment ... FragmentError: x.toml: chiave sconosciuta in [detect]: keep_paths
ERROR: test_keep_paths_lights_ext_of_file_found_by_other ... (idem)
ERROR: test_keep_paths_lights_folder_of_file_found_by_other ... (idem)
ERROR: test_keep_paths_lights_in_drift_too ... (idem)
ERROR: test_keep_paths_lights_name_of_file_found_by_other ... (idem)
FAIL: test_keep_paths_not_bool_rejected (5 subTest) ... 'sconosciuta' unexpectedly found in 'ai.toml: chiave sconosciuta in [detect]: keep_paths'
Ran 273 tests in 109.170s
FAILED (failures=5, errors=7)
```
`test_without_keep_paths_rule_i1_unchanged` era già verde, come deve essere: fissa il comportamento di oggi.

### GREEN

`python3 -B -m unittest tests.test_fragments tests.test_init`, con `python3` e con `python3.11`:
```
Ran 273 tests in 90.628s
OK
Ran 273 tests in 93.146s
OK
```
Comprende `FrontendPrecedenceTest` e `DatabasePrecedenceTest`, che non ho toccato.

Suite completa, `PYTHONWARNINGS=error::ResourceWarning tests/run` (log in `W/suite-task-3.log`):
```
Ran 4366 tests in 3453.257s
OK (skipped=13)
Ran 4366 tests in 3028.112s
OK (skipped=11)
exit 0
```
Nessun «unclosed», nessun ResourceWarning.

## Sonda delle precedenze

`bash "W/sonda-preflight/rilancia.sh" HEAD`, lanciata dopo il commit, rc=0:
```
keep_paths: del codice (Task 3); frammento security: CANDIDATO della sonda; keep_paths del frammento = True
...
ESITO: 70 casi su 70 uguali alla tabella; S67 uguale; casi in più: 12 su 12 come attesi dallo scan
```

## File cambiati

`bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py`, `tests/test_fragments.py`, `tests/test_init.py`. Nient'altro, e nessun `__pycache__`.

## Scostamenti dal piano

1. Il brief chiede che, in `test_keep_paths_does_not_change_other_fragment`, la proposta dell'altro frammento sia identica con e senza la chiave. Il blocco `[profiles.y]` e la riga «proposto con» lo sono. Con la chiave, però, nelle righe di `y` compaiono anche le sovrapposizioni con il blocco `x`, che ora esiste («server/auth/login.ts corrisponde anche a «x»: vince x», e «vince y» per `server/app.mjs`). Non sono un cambio della proposta di `y`: sono l'avviso, già previsto dal codice, che due profili nuovi si sovrappongono. Mostrano anche l'effetto voluto dalla decisione 4 (come S53 e S61: la cartella più lunga di `x` vince sulla cartella di `y`). Il test confronta quindi le righe di `y` tolte quelle di sovrapposizione con `x`, e fissa anche le quattro righe di sovrapposizione attese.
2. In `test_keep_paths_not_bool_rejected` ho aggiunto ai valori del brief (`"sì"`, `1`) anche `0`, `"true"` e `[true]`, perché il controllo non deve accettare né interi né stringhe. È un costo nullo.

## Autorevisione

- Completezza: i tre test di `test_fragments.py` e i sei di `test_init.py` (i cinque del brief più quello di D7) ci sono; la condizione è una sola per tutte le forme; il commento dice la deroga; il controllo del tipo usa `isinstance(valore, bool)`.
- Il messaggio d'errore segue lo stile di quello di `exclude` (nome del file, sezione, chiave).
- Per i cinque frammenti veri la proposta è identica, perché `keep_paths` è falsa e la condizione si riduce a quella di prima. La sonda e i test delle precedenze restano verdi.
- I test provano il comportamento di `profile_blocks` sui suoi dati (blocchi TOML e righe), non dettagli interni.

## Dubbi

Nessuno bloccante. Il solo punto da guardare in revisione è lo scostamento 1.
