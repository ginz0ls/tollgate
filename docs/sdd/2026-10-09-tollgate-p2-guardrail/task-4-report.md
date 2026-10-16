# Task 4 - Analisi: pattern, file protetti, profili, plan-check

**Status:** DONE
**Commit:** `50c3f62` tollgate P2: analisi di pattern, file protetti, profili e plan-check
**Ramo:** p2-guardrail (worktree `.claude/worktrees/p2-guardrail`)

## Implementato

- `bin/tollgate_analysis/__init__.py`: docstring del pacchetto.
- `bin/tollgate_analysis/globs.py`: dialetto `.gitignore` (`is_pattern`, `literal_segments`, `compile` con cache, `match`, `match_any`), una sola implementazione per tutto il progetto (spec 3.2).
- `bin/tollgate_analysis/protected.py`: `TOLLGATE_FILES`, `REPO_PROTECTED`, `is_tollgate_file`, `is_protected` (rel nel repo + radici assolute).
- `bin/tollgate_analysis/profiles.py`: `vertical_for` (più segmenti letterali vince, a parità il primo dichiarato), `active_profiles`, `task_skills`, `min_level`.
- `bin/tollgate_analysis/plan.py`: `PlanTask`, `MustHave`, `PlanCheck` (con `.ok`), `check_plan`, `TEST_SEP = "— test:"`, `SKILL_CAP = 3`. Il parser ignora i blocchi di codice recintati, così le intestazioni finte dentro i fence non contano.
- `bin/tollgate_core/config.py`: avviso `profilo attivo non dichiarato: <nome>` in `load_config_text`, prima del controllo su `gate.mode`. Il test di config usa `load_config_text` (decisione C4 del carry).
- Test: `tests/test_globs.py`, `tests/test_protected.py`, `tests/test_profiles.py`, `tests/test_plan.py`, `tests/test_analysis_isolation.py` (nuovi); `tests/test_config.py` (test aggiunto nella classe `LoadTextTest`).

## Test ed esiti

Comando RED: `python3 -B -m unittest tests.test_globs tests.test_protected tests.test_profiles tests.test_plan tests.test_analysis_isolation tests.test_config`

Esito RED (estratto):
- `ModuleNotFoundError: No module named 'tollgate_analysis'` su `test_protected`, `test_profiles`, `test_plan`; `test_globs` in errore di import.
- `AssertionError: 'profilo attivo non dichiarato: web' not found in []` su `test_active_profile_not_declared_warns`.
- Riepilogo: `Ran 29 tests ... FAILED (failures=1, errors=3)`.
- `test_analysis_isolation` passava già in RED: senza pacchetto il test non ha file da ispezionare. È un limite del test, non un falso verde: diventa significativo appena il pacchetto esiste (ora ispeziona i 5 moduli).

Comando GREEN: `python3 -B -m unittest tests.test_globs tests.test_protected tests.test_profiles tests.test_plan tests.test_analysis_isolation tests.test_config -v`
- `Ran 44 tests ... OK`

Suite completa: `tests/run`
- `== Python 3.11.16` ... `Ran 175 tests in 3.072s` ... `OK`
- `== Python 3.13.5` ... `Ran 175 tests in 3.467s` ... `OK`
- 155 test preesistenti più 20 nuovi.
- Nessun `__pycache__` in `bin/` e `tests/` (verificato con `find`).

## File cambiati

- Nuovi: `bin/tollgate_analysis/{__init__,globs,protected,profiles,plan}.py`, `tests/test_{globs,protected,profiles,plan,analysis_isolation}.py`.
- Modificati: `bin/tollgate_core/config.py`, `tests/test_config.py`.

## Scostamenti dal piano

Nessuno nel codice. I file sono quelli del brief, senza modifiche al contenuto. Ho applicato solo la decisione C4 del carry (`load_config_text` invece di `config.load_config_text`).

## Autorevisione

- Completezza: tutti i produces del brief presenti con le firme indicate (`globs.compile/match/match_any/is_pattern/literal_segments`, `protected.TOLLGATE_FILES/REPO_PROTECTED/is_tollgate_file/is_protected`, `profiles.vertical_for/active_profiles/task_skills/min_level`, `plan.PlanTask/MustHave/PlanCheck/check_plan/TEST_SEP`).
- Isolamento: `tollgate_analysis` importa solo la standard library e se stesso (`from . import ...`). Il test AST lo verifica su tutti i moduli del pacchetto.
- Nessun test tocca `~/.local/state/tollgate`, nessuna rete, nessun `claude`.
- Nomi in inglese, messaggi all'utente in italiano.

## Dubbi

- `globs.compile` ha lo stesso nome di `re.compile`: è voluto dal brief e il `# noqa: A001` lo segnala. Dentro il modulo la chiamata a `re.compile` è qualificata, quindi nessuna collisione.
- `check_plan` controlla i must-have con test solo per `level` L1 e L2 (come da brief). A L0 i must-have senza test passano, e il test `test_must_have_without_test` lo copre.
- Il limite di 3 skill è un warning, non un problema, come richiesto dal test `test_more_than_three_skills_is_warning`.

## Fix round 1

Commit: `6db3590` tollgate P2: globs come wildmatch di git, escape, negazione; isolamento rafforzato (fix round 1)

### 1. Classi `[...]` (globs.py)
- `]` in testa, anche dopo `[!` o `[^`, è letterale: `[]a]`, `[!]x]`.
- `\]` e `\` escape dentro la classe. Ogni carattere del corpo passa da `_lit` (escape `\xHH`/`\UHHHHHHHH`), quindi `[`, `&`, `~`, `|`, `^`, `-` non producono né `FutureWarning` né errori di regex.
- Classi POSIX (`[:alpha:]`, `[:digit:]`, ecc.): mappate su intervalli ASCII. Nome sconosciuto → pattern non valido.
- Intervallo vuoto (`[z-a]`) → classe che non corrisponde a nulla, senza eccezioni. `[a-]` resta letterale.
- Pattern non valido (`[` non chiuso, `\` finale, POSIX sconosciuta) → `compile` ritorna `None`, `match` ritorna `False`, nessuna eccezione.
- Ogni classe è preceduta da `(?!/)`: `[/]` e `[!x]` non corrispondono mai a `/`.

### 2. Negazione ed escape
- `match_any` applica la regola di git: l'ultimo pattern che corrisponde decide; un `!` che corrisponde esclude il percorso. `match` su un pattern che comincia con `!` ritorna `False`: da solo una negazione non seleziona nulla.
- `\` escapa il carattere successivo (`\*x`, `\!a`).
- `a**b` vale `*` (non attraversa `/`); `**` è speciale solo come segmento intero.
- `globs.escape(path)`: escapa `*?[]\`; un `!` iniziale è escapato. Un percorso senza `/` viene ancorato con `/` iniziale, altrimenti `x.py` corrisponderebbe anche a `a/x.py`. Il test verifica `match(escape(p), p)` su casi con `*`, `[`, `!`, `?`, `\`, `[id]`, `**`.
- Test: `test_closing_bracket_first_is_literal`, `test_escaped_closing_bracket_and_literal_brackets`, `test_posix_classes`, `test_reversed_range_matches_nothing_without_error`, `test_invalid_patterns_never_match_and_do_not_raise`, `test_invalid_patterns_emit_no_warning`, `test_slash_never_matched_by_classes`, `test_backslash_escapes_next_char`, `test_double_star_inside_segment_is_single_star`, `test_leading_bang_is_negation_not_a_match`, `test_negation_last_match_wins`, `test_escape_makes_literal_path`.

### 3. Isolamento (tests/test_analysis_isolation.py)
- Il test verifica `assertIn("globs.py")` e almeno 5 file, quindi non passa a vuoto.
- Il rilevatore (`violations`) controlla import statici, `importlib.import_module("tollgate_core")` e `__import__` (riconosciuti dalla stringa costante), e stringhe uguali a un nome vietato o che cominciano con «<nome>.».
- Test `test_detector_catches_static_and_dynamic_references`: prova il rilevatore su casi sintetici positivi e negativi, così il controllo non è solo verde.

### 4. `is_pattern` e scope (plan.py)
- `is_pattern(s)` ora è vero solo per `*` o `?`. `app/[id]/page.tsx` è un nome letterale e viene accettato nello scope. Test: `test_brackets_in_scope_are_literal_names`, `test_question_mark_in_scope_rejected`, `test_is_pattern_only_star_and_question`.
- `literal_segments` continua a contare `[` come glob, così `web/[id]/**` ha 1 segmento letterale per la specificità dei profili (`test_brackets_count_as_glob_for_specificity`).
- Riferimento: il controller ha citato `plan.py:573`, ma il file ha 146 righe. L'uso di `is_pattern` è a `plan.py:125`.
- Confronto dello scope con `globs`: `bin/tollgate_core/scope.py` (Task 3) salva i percorsi così come sono e non li confronta con i pattern (`paths()` restituisce un set). Nessun uso di `globs` in `bin/tollgate_core/`. Quindi in questo task non serve `globs.escape` lì. Il confronto dello scope con i file modificati avverrà nel controllo di scope del Task 15: lì va usato `globs.escape` per i percorsi registrati che contengono `*`, `?` o `[`. Da riportare a Task 15.

### 5. Minor: `tests/test_config.py`
- `test_active_profile_declared_gives_no_warning`: profilo dichiarato e attivo, `cfg.warnings == []`. Passa già prima della correzione ed è una guardia di regressione.

### Test e comandi
- RED: `python3 -B -m unittest tests.test_globs tests.test_plan tests.test_analysis_isolation tests.test_config` → `Ran 56 tests ... FAILED (failures=12, errors=11)`. Fallivano i 23 casi nuovi (per es. `re.error` su `[]a]` e `[!]x]`, `FutureWarning` su `[[:alpha:]]`, `is_pattern("app/[id]/page.tsx")` ritornava `True`). Il test di config sul profilo dichiarato passava già.
- GREEN mirato: `python3 -B -m unittest tests.test_globs tests.test_protected tests.test_profiles tests.test_plan tests.test_analysis_isolation tests.test_config` → `Ran 62 tests ... OK`.
- Suite: `tests/run` → `== Python 3.11.16 ... Ran 193 tests ... OK`, `== Python 3.13.5 ... Ran 193 tests ... OK`. Nessun warning, nessun `__pycache__`.

### File cambiati
- `bin/tollgate_analysis/globs.py` (riscritto il traduttore, aggiunti `escape` e la gestione della negazione in `match_any`).
- `tests/test_globs.py`, `tests/test_analysis_isolation.py`, `tests/test_plan.py`, `tests/test_config.py`.
