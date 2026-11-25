# Task 3: revisione (`cf770f1..e27db19`)

Revisore: Fable. Commit rivisto: `e27db19` (letto dal pacchetto e con `git show e27db19:<percorso>`; il worktree vivo non è stato toccato). Le righe citate sono quelle dei file al commit `e27db19`.

### Aderenza

- ✅ **`Fragment.keep_paths: bool = False`** (`bin/tollgate_core/fragments.py:57`), in coda alla dataclass. L'unico punto che costruisce un `Fragment` è `_parse` (`fragments.py:113-114`; controllato con `git grep 'Fragment(' e27db19 -- bin tests`: nessun altro costruttore).
- ✅ **Chiave letta da `[detect] keep_paths`** accanto a `content` ed `exclude` (`fragments.py:95`, `106-108`). Una chiave sconosciuta di `[detect]` resta rifiutata (`test_detect_unknown_key_still_rejected` non è cambiato).
- ✅ **D7, tipo con `isinstance(valore, bool)`** (`fragments.py:107`); l'errore porta il nome del file («<file>: [detect] keep_paths deve essere true o false»).
- ✅ **Condizione unica** in `init.profile_blocks`: `f in mine or f not in taken or fragment.keep_paths` (`bin/tollgate_flow/init.py:392`), alla lettera quella dell'interfaccia. Vale per cartelle, nomi ed `ext` perché la forma la decide `concrete_for`, che resta in `and` davanti.
- ✅ **Commento della regola di I-1** dice la deroga (`init.py:383-386`).
- ✅ **I tre test di `tests/test_fragments.py`** (`:155`, `:159`, `:165`) e **i sei di `tests/test_init.py`** (`:1126`, `:1133`, `:1138`, `:1143`, `:1156`, `:1178`), compreso `test_keep_paths_lights_in_drift_too` di D7, costruito sul modello di `test_path_only_light_skipped_in_drift_too`.
- ✅ **Cosa non cambia.** Il commit tocca solo i quattro file del task. `vertical_for`, `task_routing`, `globs`, `parse_pattern`, `finalreview`, `reviews`, `dod`, `openpr`, `bin/tollgate_gate/` e i frammenti veri non sono nel diff. Nessuna forma di pattern nuova.
- ✅ **Strati.** `tollgate_flow.init` legge un campo di `tollgate_core.fragments`: la direzione è quella ammessa. Nessun import nuovo.
- ✅ **Test con la radice esplicita e pulizia.** `keep_paths_profiles` usa `PluginMixin.plugin` (`TemporaryDirectory` con `addCleanup`); il frammento `y` e la sua skill sono scritti dentro quella radice.
- ✅ **Commit unico**, con l'oggetto chiesto e la riga `Co-Authored-By` di opus.
- ✅ **Suite.** `suite-task-3.log`: 4366 test, `OK` due volte, `exit 0`, nessuna riga con `Warning`, `unclosed` o `Traceback`.
- ⚠️ **Sonda delle precedenze** (70 su 70): riportata dall'implementatore, non rilanciata da me (non riguarda il codice di questo task oltre la condizione, già provata sotto).

**Scostamento 1 (`test_keep_paths_does_not_change_other_fragment`): accettato.** Il blocco `[profiles.y]` è confrontato due volte (come TOML e come testo) ed è identico. Le righe in più di `y` sono solo gli avvisi di sovrapposizione con il blocco `x`, che con la chiave esiste: li scrive codice che il task non tocca (`init.py:428-437`), e il test li fissa uno per uno invece di ignorarli. Non è un cambio della proposta di `y`. Va notato che nel test il frammento con la chiave (`x`) viene prima dell'altro in ordine alfabetico, quindi gli avvisi cadono su `y`: è il caso più sfavorevole. Con il frammento vero l'ordine è l'opposto (`security` viene dopo gli altri cinque), quindi le righe degli altri cinque restano identiche anche lì e gli avvisi cadono sul blocco di `security`.

**Scostamento 2 (valori in più: `0`, `"true"`, `[true]`): accettato**, è dentro il requisito («solo `true` o `false`»).

**In più:** niente. **Frainteso:** niente.

### Rischi valutati (un controllo mirato ciascuno)

Le prove sono state fatte in una copia `git archive e27db19` in `/tmp/tollgate-rev-…`, cancellata alla fine.

1. **La condizione nuova scavalca `exclude`, `EXCLUDED_PREFIXES`, i documenti, i test o il limite di grandezza.** Lettura: `keep_paths` allenta solo il secondo termine dell'`and`; il primo (`concrete_for` → `_match`, `init.py:219`) rifiuta ancora i prefissi esclusi e l'`exclude` del frammento, e `candidates` (`init.py:377`) toglie già `EXCLUDED_PREFIXES`. I documenti li ferma `_match`. Test e limite di grandezza valgono solo per il rilevamento (`_is_detectable`), mai per l'accensione per percorso: un file di test o troppo grande non è mai in `taken`, quindi la chiave non cambia niente per loro. Prova: una sonda con `x` che ha `exclude = ["supabase/"]` e `keep_paths = true`, e file sotto `supabase/`, `.claude/`, un documento, un file grande, un file in una cartella di test, tutti assegnati a `y`. Esito: `x` propone esattamente gli stessi percorsi che propone senza alcun rilevamento (`pkg/supabase/auth/**`, `server/auth/**`, `server/tests/auth/**`); niente sotto `supabase/` alla radice né sotto `.claude/`. La chiave equivale quindi a «la regola di I-1 non si applica a questo frammento», e nient'altro.
2. **`_drift` e la proposta divergono.** Lettura: tutte e due ricevono lo stesso `lighting` (`init.py:397` e `:401`); `found` è calcolato una volta sola. Prova: `test_keep_paths_lights_in_drift_too` fallisce senza la condizione (mutazione A sotto).
3. **Un valore non booleano passa.** Mutazione B: sostituito `isinstance(keep_paths, bool)` con `keep_paths not in (True, False)`; `test_keep_paths_not_bool_rejected` fallisce per `1` e per `0`. Il test sorveglia davvero il tipo.
4. **Un test nuovo passa anche senza il codice nuovo.** Il RED del report non lo dimostra per `init.py`: i cinque test di `test_init.py` fallivano tutti alla lettura del frammento («chiave sconosciuta»), non sulla condizione. Mutazione A: tolto il solo `or fragment.keep_paths` da `init.py:392`, con `fragments.py` intatto. Falliscono `…lights_folder…`, `…lights_name…`, `…lights_ext…`, `…does_not_change_other_fragment` e `…lights_in_drift_too`; resta verde solo `test_without_keep_paths_rule_i1_unchanged`, come deve (fissa il comportamento di prima). Con il codice originale i sei test sono verdi.
5. **La proposta dell'altro frammento cambia.** Nella sonda del punto 1 il blocco di `y` è identico con e senza la chiave, in tutti e tre i casi di rilevamento.
6. **Un altro punto costruisce o legge `Fragment` senza il campo.** `git grep`: `keep_paths` compare solo in `fragments.py` e in `init.py:392`; nessun altro costruttore.

### Punti di forza

- Il cambio di produzione è minimo: una riga di condizione, tre di lettura della chiave. La regola di I-1 per chi non dichiara la chiave si riduce alla lettera a quella di prima.
- `test_without_keep_paths_rule_i1_unchanged` prova le tre forme una per una e insieme, e poi lo stesso albero senza rilevamento: dimostra che ciò che spegne `x` è proprio la regola di I-1 e non un difetto dell'albero di prova.
- `test_keep_paths_lights_in_drift_too` ha anche il controllo negativo (senza la chiave nessuna riga «paths: aggiungi»).
- `test_keep_paths_does_not_change_other_fragment` non nasconde la differenza nelle righe: la isola e la fissa.
- Il messaggio d'errore segue lo stile di quello di `exclude`, e il test controlla che non sia quello di «chiave sconosciuta».

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor:**

1. `tests/test_init.py:1108-1198`: nessun test del task fissa che `[detect] exclude` ed `EXCLUDED_PREFIXES` valgono ancora con `keep_paths` (vincolo copiato dal piano). Oggi regge per costruzione (rischio 1, provato con la sonda), ma un domani chi sposta la condizione dentro `concrete_for` o prima di essa non verrebbe fermato da un test con frammenti di prova; resterebbero solo i casi veri del Task 4 (S11, S12, S43). Correzione: un test con `x` che ha `exclude = ["supabase/"]` e `keep_paths = true`, un file `supabase/auth/a.ts` e uno `.claude/auth/b.ts` assegnati a `y`: nessun blocco `x`.
2. `task-3-report.md`, sezione RED: per i cinque test di `test_init.py` il rosso è un errore di lettura del frammento, quindi non prova che i test dipendano dalla condizione di `init.py:392`. La lacuna è chiusa dalla mutazione A di questa revisione; non serve altro lavoro, basta saperlo quando si legge il report.
3. `tests/test_init.py:1156-1176`: il test copre solo l'ordine in cui il frammento con la chiave precede l'altro (`x` prima di `y`). L'ordine del caso vero (l'altro frammento prima, `security` ultimo) non ha un test con frammenti di prova; lo copriranno i test `test_real_precedence_s<N>` del Task 4. Correzione facoltativa: un caso con il frammento della chiave chiamato in modo da venire dopo.

### Valutazione

**Qualità del task:** Approvato

**Motivo:** il codice fa esattamente ciò che chiedono l'interfaccia e D7, non tocca nulla di ciò che doveva restare fermo, e le due prove di mutazione mostrano che i test nuovi dipendono dal codice nuovo. I tre Minor sono di copertura e non cambiano il comportamento.
