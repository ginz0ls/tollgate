# Task 2 report (in attesa dell'esito della suite completa, vedi in fondo)

## Implementato
- `bin/tollgate_flow/init.py`: `EXCLUDED_PREFIXES` con `.github/workflows/` e `.github/actions/`; `DOC_EXTENSIONS`; `_match`/`concrete_for`/`_concrete_paths(patterns, files)` (sostituiscono `_FOLDER_PATTERN`, `_names`, `_folder_prefix`); `_drift` e `profile_blocks` usano `fragment.patterns`; `profile_blocks` e `propose` leggono con `fragments.load_approved`; D11: i profili proposti prima entrano in `vertical` per le sovrapposizioni dei successivi.
- `docs/uso/comandi.md`: tre frasi nella sezione di `/tollgate:init` (forme, documenti, cartelle di GitHub). Nessuna trappola D15 (nessun «solo l'utente», «Argomenti:», nome nudo).
- `tests/test_init.py`: tutti i test del brief + `test_concrete_for_none_without_a_form`; `test_install_dir_does_not_light_profile` confronta la tupla a 5 voci (motivo: decisione 18); `test_real_trees_light_no_profile` con l'albero «file spinti dalla CLI».

## TDD
RED (vecchio init.py, test nuovi): `Ran 50 tests ... FAILED (failures=11, errors=3)` su `tests.test_init.ProfileBlocksTest`. Il codice è stato scritto prima dei test; il RED è stato poi ricostruito rimettendo temporaneamente `init.py` di HEAD.
GREEN: `python3 -B -m unittest tests.test_init tests.test_fragments tests.test_rules_ai tests.test_docs tests.test_manifest tests.test_layers` -> `Ran 248 tests ... OK (skipped=2)`.

## Scostamenti dal piano
- `test_overlap_between_two_new_profiles_reported`: con `src/x/y/a.py` vince `y` (3 segmenti letterali contro 2), non `x`: il test asserisce «vince y» e che la riga di `y` nomini `«x»`.
- Cartella al livello 0: forma `folder` e `root_folder` danno la stessa stringa (`/x/**`), come già in B3 (`globs.escape("x")`).

## Dubbi
Nessuno.

## Esiti finali
- Prima corsa della suite: exit 1 solo per `tests.test_cli.CliTest.test_db_restore_interactive_eof_and_ctrl_c` (instabile sotto carico). Ripetuto da solo: OK con python3.11 e OK con python3.
- Seconda corsa `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3604 test OK su python3.11 e python3, exit 0.
