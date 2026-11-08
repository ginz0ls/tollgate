# Report Task 1 (B4): forme dei pattern dei frammenti

Status: DONE

## Implementato (`bin/tollgate_core/fragments.py`)
- `Pattern(kind, name)` frozen; `parse_pattern` con una regex per forma (`folder`, `root_folder`, `name`), `fullmatch`.
- `Fragment.patterns` (stesso ordine di `paths`); `_parse` usa `parse_pattern`, `_PATTERN` rimosso.
- `load_approved(plugin_root)`; `rules` solleva `FragmentError` ("rules-<area>/SKILL.md: ...") con skill illeggibile.
- `init.py` non toccato (`_FOLDER_PATTERN` è del Task 2).

## Test (`tests/test_fragments.py`)
Nuovi: `test_parse_pattern_forms`, `test_parse_pattern_rejects`, `test_load_accepts_three_forms`, `test_load_approved_filters_unapproved`, `test_rules_unreadable_skill_raises`.
Aggiornati: `test_load_rejects_other_pattern_forms` (tolto `**/ai`, ora forma `name` valida per decisione 2); `test_rules_from_skill` (skill assente -> `FragmentError`, decisione 10). `tomlout_str` tolto: l'helper `q` delega a `tomlout.table`.

## TDD
RED (vecchio fragments.py): `python3 -B -m unittest tests.test_fragments` -> FAILED (failures=2, errors=29).
GREEN: 22 test OK; `tests.test_fragments tests.test_init tests.test_rules_ai` 165 test OK (2 skipped).
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3577 test OK (skipped=5); python3 (3.13.5) 3577 OK (skipped=3); nessun "unclosed".

## Scostamenti / dubbi
Nessuno. Il nome `name` conserva l'eventuale `*` finale (`Dockerfile*`).
