# Report Task 1 - esclusione per frammento

Implementato `[detect] exclude`: `fragments.Fragment.exclude` (regex `_EXCLUDE`, segmenti di `_SEGMENT` con `/` finale, errore che nomina file ed `exclude`); `init._match`, `concrete_for`, `_concrete_paths`, `_is_detectable`, `detect_files`, `_drift`, `profile_blocks` filtrano i prefissi. Frase in `docs/uso/comandi.md` senza nominare `backend`.

Test nuovi: test_exclude_parsed, test_exclude_rejects_bad_forms, test_detect_unknown_key_still_rejected, test_concrete_for_exclude_default_is_b4, test_concrete_for_with_exclude, test_exclude_skips_paths_and_detect, test_exclude_only_for_its_fragment, test_exclude_respected_in_drift, test_detect_files_honours_exclude (D3, D4).

RED: `python3 -B -m unittest tests.test_fragments tests.test_init` -> failures=10, errors=7. GREEN: stesso comando + test_rules_ai/infra/docs: 235 test OK.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3.11 3677 OK (skipped=7), 3.13 3677 OK (skipped=5), nessun "unclosed".

Scostamento: nel test del piano il percorso `server/**` esce come `/server/**` (forma root_folder di B4): atteso aggiornato.
Dubbi: nessuno.
