# Report Task 3: `init` propone i profili approvati e presenti

Commit: `bfc6b6f` «tollgate B3: init propone i profili approvati e presenti nel repo». Status: DONE.

## Implementato
- `git.tree_sizes_at(repo, ref)` (`bin/tollgate_core/git.py`): `git ls-tree -r -l -z`, solo blob, sottomoduli saltati, riferimento assente `{}`, `_check_ref` come le altre.
- `bin/tollgate_flow/init.py`:
  - `EXCLUDED_PREFIXES` (una sola costante, per il Task 4), `SHOWN_FILES = 10`.
  - `ProfileProposal` (frozen: `text`, `lines`, `readme`).
  - `profile_blocks(files, current_text, plugin_root, *, detected=None)`: pura sui dati (D20, nessun git: un test mocka `git._proc`). Salta i frammenti non approvati; per un profilo già dichiarato solo righe di differenza (`rules`, `blocking_rules` aggiungi/togli, `paths` con D17, agenti ora presenti); per gli altri percorsi concreti `globs.escape(prefisso) + "/**"` (D4), prefissi annidati ridotti al più corto, `detected` aggiunto con percorso esatto se non coperto, agente mancante tolto con riga (decisione 12), avviso se `[profiles] active` contiene l'area, sovrapposizioni con i verticali dichiarati e chi vince (`profiles.vertical_for`, a parità vince il dichiarato per primo).
  - `propose(..., profiles_root=None)`: il testo si aggiunge dopo `with_mode`; righe anche nel ramo «nulla da aggiornare»; sezione nel `README.md` (dopo i passi). D2: `GitError` -> `profili non valutati: <motivo>` in righe e README, `code` 0; `FragmentError` -> `_refuse`. Se `current + blocchi` non passa `config.load_config_text`, i blocchi si scartano con lo stesso avviso (non previsto dal piano, difesa per toml con strutture insolite).
  - README: ogni sezione di profilo passa da `_plain` riga per riga e poi da `prbody.neutralize(..., max_len=4000)` (D8); sezione «Differenze e avvisi» per i profili dichiarati.
- `skills/init/SKILL.md` (passo 4, fuori da «Codici d'uscita», nessuna riga `- **<n>`) e `docs/uso/comandi.md`.

## Test
- `tests/test_git.py`: `test_tree_sizes_at`, `test_tree_sizes_at_skips_submodules_and_keeps_odd_names`.
- `tests/test_init.py`: `ProfileBlocksTest` (34) e `ProfilesProposeTest` (7), tutti i nomi del brief più i casi extra (blocking_rules, negazioni nei due ordini, `agent = ""`, detected, nessun frammento, niente git, README una riga per nota, senza newline finale). Gli esistenti restano sulla radice vera; `test_real_trees_light_no_profile` è nuovo.
- RED: dopo i test e prima del codice, `python3 -B -m unittest tests.test_git -k tree_sizes` -> `FAILED (errors=2)` (AttributeError `tree_sizes_at`); `python3 -B -m unittest tests.test_init.ProfileBlocksTest tests.test_init.ProfilesProposeTest` -> `Ran 40 tests ... FAILED (errors=41)` (`profile_blocks` e `profiles_root` assenti).
- GREEN mirati: `python3 -B -m unittest tests.test_git tests.test_init` -> `Ran 129 tests ... OK`; poi `tests.test_skill_contract tests.test_docs tests.test_layers tests.test_manifest tests.test_fragments tests.test_analysis_isolation` -> `Ran 96 tests ... OK`.
- Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`, uscita in `task-3-suite.out`: Python 3.11.16 `Ran 3311 tests in 4440.7s OK (skipped=2)`; Python 3.13.5 `Ran 3311 tests in 2037.8s OK`; `exit=0`. Nessun «unclosed».

## Bug trovati lavorando (corretti prima del commit)
- `_plain` su un testo multiriga trasformava gli a capo in `?`: ora riga per riga (`_fenced`); un secondo errore (variabile di ciclo `other` che oscurava la lista) è stato preso dalla stampa di prova e coperto da `test_readme_keeps_one_line_per_note` e `test_readme_declared_drift_section`.

## Scostamenti dal piano
- `git.tree_sizes_at` salta ogni voce non `blob`.
- `test_git_error_leaves_the_rest_of_the_proposal` con `--update` non legge `files/tollgate.toml` (non cambia, quindi non è nella proposta).
- Tra «aggiungi» ho previsto anche «togli» per voci con prefisso `R-<AREA>-` in `rules`/`blocking_rules` non più nella skill (il brief dice solo di confrontare).

## Autorevisione
Completo rispetto al brief e a D2, D4, D8, D14, D16, D17, D20. Nessun `approved` toccato, nessun `__pycache__`, nessuna rete, niente di privato nei file nuovi. `globs` non toccato. `detect_files` non c'è ancora (Task 4): `detected` è il solo aggancio.

## Dubbi
- Le righe di differenza dei profili dichiarati usano il formato `profilo <area>: [profiles.<area>] <chiave>: aggiungi <valore TOML>`; il Task 4 e la rev 29 possono citarlo così.
- Il test di `Ctrl-C` su pty non è stato rosso.

## Fix round 1

- A+B: `test_real_trees_light_no_profile` ora copia in un plugin temporaneo i frammenti veri (`fragments.load(ROOT)`) con una skill finta approvata per ciascuno e controlla tre alberi: quello che i test spingono (`DEFAULT_FILES` di `tests/hookkit.py` + `tollgate.toml`, non una copia a mano), quello installato (`install.files(ROOT, …)`) e quello installato dentro la cartella della proposta. Senza frammenti veri fa `skipTest` col motivo (oggi è l'unico test saltato). Verificato a mano con un `templates/profiles/ai.toml` provvisorio (poi rimosso, mai nel commit): il test passa attivo. Nota: asserisce `text == ""` e nessuna riga «proposto con»; la riga «nessun file … non proposto» è lecita.
- M1: `test_declared_profile_stale_rule_removal_reported` (`R-X-09` -> «togli»; `mia-regola` non compare).
- M2: `test_blocks_failing_validation_are_dropped` (`profile_blocks` mockato con testo non valido: code 0, nessun blocco nel toml, «profili non valutati» in righe e README, righe finte scartate).
- M3: rinominato `test_real_default_root_is_the_plugin`; ora un mock su `fragments.load` registra la radice e si asserisce che sia `ROOT`.
- M4: in `propose`, se `tree_sizes_at` dà `{}` si dice «profili non valutati: git non ha elencato nessun file di <rif>» invece di «nessun file … corrisponde» (`test_empty_tree_is_not_a_verdict_on_the_repo`).
- M5: la frase della skill `init` è divisa in due.
- RED: M2/M4 non avevano il ramo/test; M4 prima del codice dava «nessun file … non proposto» (verificato col test rosso nel primo lancio: `FAIL test_empty_tree_is_not_a_verdict_on_the_repo`, a causa anche dell'asserzione troppo larga poi corretta sul testo «corrisponde ai suoi percorsi»).
- GREEN: `python3.11 -B -m unittest tests.test_init tests.test_git tests.test_skill_contract tests.test_docs` -> `Ran 157 tests ... OK (skipped=1)`; stesso comando con `python3` (3.13) -> `Ran 157 tests ... OK (skipped=1)`.
