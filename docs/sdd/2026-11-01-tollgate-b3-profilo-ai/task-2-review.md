# Revisione Task 2 (B3): regole di area, scrittore TOML, frammenti

### Aderenza
- ✅ `research.area_rules(skill_text, area)` con regex `^(R-<AREA>-\d{2})( \[blocca\])? \S`, `re.escape(area.upper())`; `base_rules` = `area_rules(text,"BASE")` (research.py, diff). Tre test del brief presenti (`AreaRulesTest`, `test_real_base_rules_unchanged` sul SKILL.md vero).
- ✅ `tomlout.table` (decisione 8): str/bool/list[str]/dict[str,str] in linea; escape di `\`, `"`, controlli e DEL; chiavi non semplici tra virgolette; altro tipo -> `TypeError` (anche chiavi non str). `bool` controllato prima di `int` (non esiste ramo int). Round trip e rifiuti testati, inclusa chiave `lint:fix`.
- ✅ `fragments`: `Fragment` frozen, `FragmentError(ValueError)` col nome del file, `load` ordinato, cartella assente -> `[]`, nome riservato/non valido, chiavi fuori da `PROFILE_DEFAULTS`, `rules`/`blocking_rules` rifiutate, pattern diversi da `**/<cartella>/**` rifiutati (decisione 5), TOML illeggibile (OSError/Unicode/Decode), `approved` via `research.enforced` (skill assente -> False), `rules` ordinate; `skill_path` come da brief.
- ✅ D14: `test_fragment_profile_validates` ha `schema_version = 1`, `[gate] mode = "protected"`, agent/reviewer nella forma `tollgate:implementer-ai` / `tollgate:reviewer-ai`, asserisce `warnings == []` e le regole.
- ✅ Strati: `tomlout` importa solo `re`; `fragments` (core) importa analysis e config, consentito.
- ✅ Nessun `approved` toccato, nessun `__pycache__` nel diff, nessun nome privato.
- ⚠️ Evidenza della suite completa (3265 test, due interpreti) solo dichiarata nel report; non rilanciata come da regole.
- Scostamento minore: il test del brief `test_load_rejects_reserved_names` è stato esteso/rinominato in `..._and_invalid_names` (copre più del richiesto, accettabile).

Le tre scelte dell'implementatore:
1. Sezioni diverse da `[profile]`/`[detect]` = errore: giusta. I frammenti sono file del plugin, non dell'utente; un refuso di sezione sarebbe altrimenti silenzioso. Coerente con "chiavi sconosciute = errore" del brief.
2. `templates/profiles/`: non è una scelta, è la decisione 2. Corretto.
3. Caratteri vietati nella cartella (`/ * ? [ ] ! \`): ragionevole e coerente con "forma `**/<cartella>/**`" e con `globs.escape` a valle. Lascia passare `.` e `..` (vedi Minor).

### Punti di forza
- `base_rules` ridotto a una riga: nessuna duplicazione, chiamanti invariati.
- Scrittore TOML piccolo, con escape completo (DEL e `\uXXXX`) e test di round trip reale con `tomllib`.
- Errori sempre col nome del file; controllo del nome prima della lettura; `is_file()` filtra directory finte.
- Test di forma ampi (otto forme di pattern, cinque nomi, forme errate di `[detect]`).

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `fragments.py:66` `paths = profile.get("paths", [])`: un frammento senza `paths` passa; scritto poi in `[profiles.x]` da `init` darebbe il default `["**"]` di `PROFILE_DEFAULTS` (profilo che si accende su ogni file). Per decisione 5 `init` deriva i percorsi dai pattern, quindi un frammento senza pattern non ha senso: valutare di imporre `paths` non vuoto per `kind = "vertical"` (o gestirlo nel Task 3).
2. `fragments.py:16` `_PATTERN` accetta cartelle `.` e `..` (`**/../**`) e nomi con spazi: innocuo ma inutile; escludere `.`/`..` con una riga se si vuole.
3. `fragments.py:92-95` `rules()` su skill assente/illeggibile restituisce `([], [])` senza segnale: il chiamante (Task 3) deve chiamarla solo dopo `approved()`; da ricordare nel Task 3 (con regole vuote un profilo bloccherebbe nulla).
4. `research.py` (regex ereditata): una riga `R-AI-01 [blocca]` senza testo dopo non è marcata bloccante (`( \[blocca\])? \S` retrocede e conta `[` come testo). Comportamento di base già esistente, invariato; segnalato per il Task 5 (ogni regola deve avere testo dopo `[blocca]`).
5. `tests/test_fragments.py:129` `tomlout_str` duplica l'escape: si può scrivere il pattern con `tomlout.table("profile", {"paths":[pat]})` ed evitare l'helper.
6. `tomlout.table` divide `name` sui `.`: una parte con punto non è esprimibile (non serve oggi).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e D14 soddisfatti sul diff, strati rispettati, test sul comportamento reale; solo rifiniture minori (la più utile: il frammento senza `paths`).
