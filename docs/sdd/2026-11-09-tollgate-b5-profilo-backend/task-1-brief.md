### Task 1: Esclusione per frammento (`[detect] exclude`)

**Files:**
- Modify: `bin/tollgate_core/fragments.py` (`_parse`, `Fragment`), `bin/tollgate_flow/init.py` (`_match`, `concrete_for`, `profile_blocks`, `_drift`, `detect_files`), `docs/uso/comandi.md` (sezione di `/tollgate:init`: una frase sull'esclusione di un frammento)
- Test: `tests/test_fragments.py`, `tests/test_init.py`

**Interfaces:**
- Consumes: `fragments.parse_pattern`, `Fragment`, `FragmentError`, `load`, `load_approved` (B4); `init.concrete_for`, `_concrete_paths`, `detect_files`, `profile_blocks`, `EXCLUDED_PREFIXES` (B4).
- Produces:
  - `fragments.Fragment.exclude: tuple[str, ...]` (vuota se il frammento non ha la chiave), letta da `[detect] exclude` (decisione 4);
  - `init.concrete_for(path: str, patterns, exclude: Sequence[str] = ()) -> str | None` (stesso comportamento di B4 con `exclude` vuoto);
  - `init._concrete_paths(patterns, files, exclude=())`, `detect_files` e `_drift` che scartano i file sotto `fragment.exclude`.

- [ ] **Step 1: I test che falliscono** (radice temporanea, come i test di B4):
  - `tests/test_fragments.py`: `test_exclude_parsed` (`[detect] exclude = ["supabase/", "a/b/"]` → `Fragment.exclude == ("supabase/", "a/b/")`; frammento senza la chiave → `()`); `test_exclude_rejects_bad_forms` (per ognuno `FragmentError` con il nome del file **e** con un messaggio che parla della forma di `exclude`, non di una «chiave sconosciuta», che su `main` darebbe già un errore: `"supabase"` senza `/`, `"/supabase/"`, `"supa*/"`, `"../x/"`, `"./x/"`, `"a//b/"`, `""`, un valore non stringa, una lista con un intero, una stringa al posto della lista).
  - `tests/test_init.py`, in `ProfileBlocksTest`: `test_exclude_skips_paths_and_detect` (frammento `x` con `["**/handlers/**", "server/**"]`, `exclude = ["supabase/"]` e il marcatore `MARK`: `supabase/functions/a/handlers/h.ts` e `supabase/functions/b/index.ts` con `MARK` non entrano nei `paths` né nel conteggio dei file; `src/handlers/h.ts` e `server/app.py` sì); `test_exclude_only_for_its_fragment` (un secondo frammento `y` con `**/handlers/**` e senza `exclude` accende `supabase/functions/a/handlers/h.ts`); `test_exclude_respected_in_drift` (`[profiles.x]` già dichiarato, un file nuovo sotto `supabase/` non dà una riga «aggiungi»); `test_concrete_for_with_exclude` (`concrete_for("supabase/functions/a/handlers/h.ts", patterns, exclude=("supabase/",))` è `None`; senza `exclude` dà `supabase/functions/a/handlers/**`).
  Guardie già verdi su `main`, da tenere verdi: `test_detect_unknown_key_still_rejected` (`[detect] other = []` resta un errore); `test_concrete_for_exclude_default_is_b4` (con `exclude` omesso `concrete_for` dà gli stessi valori dei casi di `test_name_pattern_exact_paths`).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_fragments tests.test_init`.
- [ ] **Step 3: Il codice.** In `_parse` la chiave `exclude` di `[detect]` accanto a `content`, con una regex di forma (segmenti di `_SEGMENT`, `/` finale) e il messaggio che nomina il file; in `init` il controllo dei prefissi di `exclude` subito dopo quello di `EXCLUDED_PREFIXES` in `_match`, e lo stesso filtro sui file di `detect_files` e su `lighting`, `found` e i file nuovi di `_drift`. In `docs/uso/comandi.md` una frase: un frammento può escludere cartelle dalla proposta (senza nominare `backend`, che nasce nel Task 3 e che il Task 3 aggiunge alla frase).
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_fragments tests.test_init tests.test_rules_ai tests.test_rules_infra tests.test_docs`: PASS (i frammenti di `ai` e `infra` si caricano come prima). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B5: un frammento può escludere cartelle dalla proposta».

---

