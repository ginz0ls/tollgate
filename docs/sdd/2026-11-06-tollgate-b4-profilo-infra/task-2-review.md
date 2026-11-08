# Revisione Task 2 (6d7f81e..b42c25e)

### Aderenza
- ✅ Decisione 3: `_match` (`bin/tollgate_flow/init.py`) prova prima le cartelle da sinistra (`folder` e `root_folder` solo al segmento 0), poi `name` sul solo nome del file con `fnmatch.fnmatchcase`; il percorso esatto passa da `globs.escape`. `_concrete_paths` toglie le cartelle coperte da una più corta e i percorsi esatti coperti da una cartella proposta (`globs.match_any`).
- ✅ Decisione 4: `DOC_EXTENSIONS` in minuscolo, `_is_doc` con `ext.lower()`; i documenti saltano le cartelle, un nome con `*` non li accende, un nome letterale sì.
- ✅ Decisione 18: `EXCLUDED_PREFIXES` con `.github/workflows/` e `.github/actions/`; `_match` li esclude per prima, quindi `.github/tollgate/`, `.claude/`, `docs/superpowers/tollgate-init/` non accendono nemmeno i nomi di file. `docker/Dockerfiles/` non accende (nome solo sul file).
- ✅ Decisione 10: `profile_blocks` e `propose` usano `fragments.load_approved`; il `FragmentError` di `fragments.rules` arriva al `except` già presente in `propose`.
- ✅ D11: `proposed` entra in `vertical` per i frammenti successivi; `test_overlap_between_two_new_profiles_reported` esiste ed è sensato (lo scostamento «vince y», 3 segmenti contro 2, è corretto).
- ✅ `_drift` usa `fragment.patterns`, rispetta le negazioni (testato per i nomi), non duplica: dopo che l'utente applica la riga il file è coperto da `match_any`.
- ✅ Nessuna scrittura di `tollgate.toml`: solo testo proposto in coda. Strati: nessun import nuovo di hooks/checks (solo `fnmatch`, già importato).
- ✅ D15: nella sezione di `/tollgate:init` di `docs/uso/comandi.md` le tre frasi non introducono «solo l'utente», «Argomenti:» nuovi né nomi nudi del programma. Nessun messaggio nuovo in `bin/`.
- ✅ Test: tutti quelli del brief presenti; `test_install_dir_does_not_light_profile` confronta la tupla a 5 voci; i test di B3 non risultano toccati. `python3 -B -m unittest tests.test_init`: 123 OK (rieseguito). Test su radice temporanea (`self.plugin(...)`), salvo `test_real_…`, nessuna dipendenza dall'ambiente.
- ⚠️ Non verificabile dal diff: la suite completa (riportata verde dall'implementatore). Nel working tree ci sono modifiche non committate a `bin/tollgate_analysis/bash.py` e `tests/test_bash.py`, estranee a questo task (Task 3).

### Punti di forza
- `concrete_for`/`_concrete_paths` sono l'unico punto della logica, usato da `profile_blocks` e `_drift`: niente duplicazione.
- Copertura dei casi limite scelti bene (cartelle con nome simile, escape, maiuscole, documenti, prefissi esclusi, negazioni, sovrapposizioni).

### Rilievi
Critical: nessuno. Important: nessuno.

Minor
- `tests/test_init.py` (test_name_pattern_exact_paths): `[...].__len__()` al posto di `len(...)`.
- `bin/tollgate_flow/init.py` `_match`: gli insiemi `folders`/`roots` si ricalcolano per ogni file; irrilevante oggi, ma si possono calcolare una volta per profilo.
- Il report dice che il codice è stato scritto prima dei test (RED ricostruito dopo): scostamento di processo, nessun effetto sul risultato.
- `test_concrete_for_none_without_a_form` non copre `concrete_for` su un file di `EXCLUDED_PREFIXES` (coperto indirettamente da `test_name_pattern_skips_excluded_prefixes`).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** Specifica delle decisioni 2-4, 10, 11, 16, 18 rispettata alla lettera, logica centralizzata, test mirati e verdi; solo rifiniture minori.
