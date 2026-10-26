# Revisione Task 4 (8f92827..0c40787)

### Aderenza
- ✅ M-1 / D14: `attention.py:204` (gruppo READ), `evaluate.py:445-457` `_base_command_missing`, `evaluate.py:475-482` voce con i nomi (da `ctx.required`, configurazione, non da `ids.json`) in `data`; `baseids.py:251-296` `BaseIds`/`load_full` (`load` la chiama); `model.py:568` `base_commands`; `verdict.py:661,671,723-725`. Regola D14 rispettata: `red` con JUnit non dà la voce; `base_commands is None` = sola presenza in `ids`.
- ✅ (1) Cache P4 già scritte: `compute` scriveva già `commands` (baseids.py:245, contesto), quindi le cache P4 reali hanno gli stati. Una cache di albero con configurazione più vecchia manca il comando nuovo da `ids` -> voce «da leggere» (non rosso), coperto da `test_old_config_cache_without_new_command`. Un `ids.json` senza il campo `commands` dà `{}` (non `None`, baseids.py:291-296), quindi ogni comando con report risulta mancante: è la lettura letterale di D14 («stato assente = mancante»), esito «da leggere», giusto e fail-closed; il file non è prodotto da P4 (solo fatto a mano). Il docstring di `model.py:550-552` («None: non noto») descrive solo il caso locale/test. `base_test_ids = false`: `base_ids` esce prima (evaluate.py:465) -> nessuna voce, corretto.
- ✅ (2) M-5 / decisione 17: `verdict.py:637-649`. `config_sha` non str o non 40-64 hex -> cambiato; `==tip` -> invariato; `merge-base --is-ancestor` via `git.ok` (GitError -> False -> cambiato); blob via `git.blob_at` (None se manca il ref o il file); assente in uno dei due -> cambiato. Nessun argomento di git da testo non fidato: l'hex è validato prima. Un `GitError` residuo (timeout) in `blob_at` esce da `inputs_from_github` ma è preso dal confine `except Exception` di `verdict.py:218` -> stato `error` esplicito: fail-closed. Test: i 5 del brief, merge a due genitori vero, e `test_config_changed_is_a_bool_and_fail_closed`.
- ✅ (4) M-9 `tests/test_criteria_p4.py:87-151`: è un test vero. Le due parti usano codice di produzione diverso (GateLab + `gate run` come processo + `inputs_from_github` + `gate evaluate` come processo, contro FlowLab + `finish check` con lo spy su `evaluate`); confronta l'insieme delle chiavi rosse (`keys`, riga 75) e per famiglia, e asserisce che `out_of_scope` e `test_deleted` siano presenti, quindi non passa per vuoto. Dichiarato nel report che passa subito (test di guardia): accettabile per M-9. Limite: confronta solo le voci rosse, non quelle di `attenzione` (tranne `plan_changed`).
- ✅ Strati: `tollgate_gate` usa `git`, nessun `db`/`sqlite3`; un solo calcolo (voce in `evaluate.base_ids`, gruppo in `GROUPS`; `CoverageTest` verde per il report).
- ✅ (5) `skills/finish/SKILL.md:32` aggiunge la chiave all'elenco «da leggere» con le chiavi di `attention`; lo stesso elenco già contiene `base_ids_from_run`, `ci_waived_workflow`, ecc., che in locale non compaiono mai, e il testo dice «con le chiavi di `tollgate_gate.attention`». Il testo per il modello resta corretto; la frase «Ripetuto sullo stesso SHA…» non è toccata.
- ✅ Minori: tutti presenti (`workflows._SCOPE`, `prref._visible`, `waivers._ID` con `\Z` e `.match` ai due punti d'uso, `comment._link`, `exit=None` dichiarato green, `evaluate()` cattura `OSError`/`ValueError`, `runner` cattura `OSError`, `init._MODE_LINE`, `base_path`). D16 dichiarato (forma a blocco già verde, forma a flusso senza spazio no).
- ⚠️ Non rieseguito `tests/run` (evidenza del report: 2603 OK su 3.11 e 3.13).

### Punti di forza
- La logica M-1 sta in una funzione piccola e pura, con i casi di D14 tutti distinti e un test per ciascuno.
- `_config_changed` è fail-closed su ogni ramo e il test del merge è un merge vero a due genitori.
- Il test di M-9 passa dagli ingressi veri e non da fixture.
- `test_findings_carry_blocking_field` riscritto sul produttore vero, con mutazione verificata.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `evaluate.py:485-488,500` + `git.exists_at` (git.py:348-350): gli identificativi di `ids.json` (con `BASE_FROM_RUN` l'artefatto è prodotto dal run della PR, quindi non fidato) diventano il percorso in `git cat-file -e <base_sha>:<path>`. Non è un'iniezione di opzioni (il prefisso è lo SHA) ma sfiora la regola «mai testo non fidato in argomenti di git», e il numero di processi è proporzionale ai percorsi distinti (un `ids.json` fino a 50 MB può farne decine di migliaia: al peggio un timeout del job, quindi fail-closed). Correggere con un tetto sui percorsi verificati (oltre il tetto, euristica) o leggendo una volta l'elenco dei file della base (`ls-tree -r`). L'`exists` non è necessario per il test del brief, ma serve a disambiguare `pkg.Models` da una classe: scelta ragionevole, non fuori ambito.
2. `baseids.py:291-296` / `model.py:550`: un file senza `commands` dà `{}` e non `None`, quindi il ramo «sola presenza in `ids`» di `_base_command_missing` (evaluate.py:453) non si raggiunge mai dal percorso di produzione. Coerente con D14 (stato assente = mancante), ma il docstring del modello e la riga del report sul caso «ignoto» vanno allineati, e meriterebbe un test su un `ids.json` reale senza `commands`.
3. `comment.py:322,349`: `_LINK` spegne `[x](y)` ma non `[x][ref]`, `<url>` o gli URL nudi (dichiarato nel report, fuori dal brief).
4. `test_criteria_p4.py:75`: l'accordo confronta solo le chiavi rosse; le voci di `attenzione` comuni non sono confrontate.
5. `validazione hex` (`verdict.py:615`): accetta solo minuscole 40-64; un SHA di GitHub è sempre minuscolo, quindi nessun problema. Scelta necessaria (dato non fidato verso git), non fuori ambito.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** M-1, M-5, M-9 e i minori sono implementati come da brief e da D4/D14/D16/decisione 17, con test che falliscono senza il codice e senza violare gli strati; restano solo rifiniture Minor (fan-out di `exists_at` su ids non fidati, caso `commands` assente).
