# Report Task 2 (B3): regole di area, scrittore TOML, frammenti

Status: DONE.

## Implementato
- `research.area_rules(skill_text, area)`: regex `^(R-<AREA>-\d{2})( \[blocca\])? \S` con `re.escape(area.upper())`; `base_rules` = `area_rules(text, "BASE")` (chiamanti invariati).
- `tollgate_analysis/tomlout.py`: `table(name, values)` per str, bool, list[str], dict[str,str] (tabella in linea); escape di `\`, `"`, `\b \t \n \f \r`, altri controlli e DEL come `\uXXXX`; chiavi non semplici tra virgolette (anche nel nome della tabella); altro tipo, chiavi non str: `TypeError`.
- `tollgate_core/fragments.py`: `Fragment`, `FragmentError`, `load`, `approved`, `rules`. Cartella `templates/profiles/`. Errori (sempre col nome del file): TOML illeggibile, nome non `[a-z0-9-]+`, nome riservato (`base`, `active`), sezioni diverse da `[profile]`/`[detect]`, chiavi fuori da `PROFILE_DEFAULTS`, `rules`/`blocking_rules`, pattern di `paths` non della forma `**/<cartella>/**`, `[detect] content` non lista di stringhe non vuote. `detect` assente: tupla vuota.

## Test
- RED: `python3 -B -m unittest tests.test_research tests.test_tomlout tests.test_fragments` -> 5 errori/fallimenti (`area_rules` assente, `tomlout` non importabile, `fragments` non importabile).
- GREEN: stessi file + `test_rules_base`, `test_analysis_isolation`, `test_layers`: 78 test OK (python3 3.13); i tre file nuovi anche con python3.11: 53 OK.
- Suite completa `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 e python3.13, 3265 test, OK (2138 s), nessun «unclosed» né avviso, EXIT 0.

## File
Modificati: `bin/tollgate_analysis/research.py`, `tests/test_research.py`. Nuovi: `bin/tollgate_analysis/tomlout.py`, `bin/tollgate_core/fragments.py`, `tests/test_tomlout.py`, `tests/test_fragments.py`.

## Scostamenti dal piano
Test in più del brief: `test_load_without_detect_is_empty_tuple`, `test_load_rejects_bad_shape`, `test_header_quotes_non_bare_name_parts`; `test_load_rejects_reserved_names` copre anche nomi non validi. Scelte mie: sezioni sconosciute nel frammento sono errore; la cartella cercata è `templates/profiles/` (decisione 2); cartella del pattern senza `/ * ? [ ] ! \`. In `test_fragment_profile_validates` il frammento di prova usa `agent`/`reviewer` nella forma D14 e `schema_version = 1`, `[gate] mode = "protected"`.

## Autorevisione
Brief e carry completi; nessun testo extra; isolamento di `tollgate_analysis` rispettato (test verde); nessun `__pycache__`; nessun `approved` toccato.

## Dubbi
Nessuno.

## Fix round 1
Uscita della suite completa del primo giro: salvata in `/home/USER/.claude/jobs/e28b8553/tmp/suite-t2.log`, copiata in `W/task-2-suite.out`.

Cambiato in `bin/tollgate_core/fragments.py`: (1) `paths` assente o vuoto è una `FragmentError` col nome del file (controllo dopo gli altri, così i test degli altri errori restano mirati); (2) il pattern rifiuta le cartelle `.` e `..` (lookahead `(?!\.{1,2}/)`). Test nuovi in `tests/test_fragments.py`: `test_load_rejects_missing_or_empty_paths`, `test_load_rejects_dot_folders`; `test_load_without_detect_is_empty_tuple` ora ha `paths`.

RED: `python3 -B -m unittest tests.test_fragments` (3.11 e 3.13): `FAILED (failures=5)`, «FragmentError not raised».
GREEN: `python3.11 -B -m unittest tests.test_fragments tests.test_layers tests.test_analysis_isolation tests.test_tomlout` e lo stesso con `python3`: `Ran 26 tests ... OK` entrambi. Suite completa non rilanciata (come da istruzioni).
