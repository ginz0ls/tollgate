# Report Task 1: pattern per estensione (ext)

Commit: vedi `git log -1` su b6-profilo-frontend ("tollgate B6: pattern per estensione nei frammenti e nella proposta").

## Implementato
- `fragments.py`: `_EXT`, quarta forma in `parse_pattern`, commento di `Pattern.kind`, messaggio di `_parse` con le quattro forme.
- `init.py`: `_match` prova `ext` per ultima (non documenti, confronto esatto sul suffisso), `concrete_for` lo restituisce senza escape, `_concrete_paths` lo tiene (un valore per estensione).
- `docs/uso/comandi.md`: una frase sui pattern per estensione.

## Test (D6)
- `test_load_rejects_other_pattern_forms` (tests/test_fragments.py:93): uscito `**/*.sql`.
- `test_parse_pattern_rejects` (:182): usciti `**/*.sql`, `**/*.json`, `**/*.Dockerfile`.
- Tutti e tre entrati in `test_ext_pattern_parsed` (con `tsx` e `CSS`).
- Nuovi: test_ext_pattern_parsed, test_ext_rejects_bad_forms (fragments); test_existing_forms_unchanged, test_concrete_for_ext, test_ext_proposed_once, test_ext_not_proposed_when_folder_covers_all, test_ext_in_drift, test_content_found_file_covered_by_ext, test_exclude_multi_segment_prefix (init); ExtPatternPrecedenceTest con i 4 test di guardia (profiles).

## TDD
RED: `python3 -B -m unittest tests.test_fragments tests.test_init tests.test_profiles` -> failures=14, errors=7 (solo i test nuovi di fragments/init; guardie verdi).
GREEN: stesso comando + test_rules_ai/infra/backend/docs/layers -> 320 test OK (skipped=7).
Suite: `tests/run` con ResourceWarning=error: python3.11 e 3.13 OK, 3773 test, exit 0 (suite-task-1.log).

## Scostamento dal piano
`test_exclude_multi_segment_prefix`: non asserisco che `apps/api` sia assente dall'elenco «lo accendono N file», perché `lit` è calcolato a runtime con `globs.match_any` e `**/*.tsx` copre anche `apps/api/x.tsx` (decisione 2); asserisco che `apps/api/x.tsx` da solo non propone nulla e che i `paths` sono `["**/*.tsx"]`.

## Dubbi
Nessuno.
