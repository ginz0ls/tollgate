# Task 5 — report dell'implementatore

Commit: `b02b53b` «tollgate P4: calcolo del gate (livello, L2, issue, DoD dichiarata, componenti)» (base `fcd85e1`). File: `bin/tollgate_gate/evaluate.py` (438 -> 866 righe), `tests/test_gate_evaluate.py`.

## Cosa ho implementato

Nuove famiglie in `FAMILIES` (dopo quelle del Task 4, nell'ordine `level, l2, issue, declared, notes, lockfiles, workflow_rules, guard_local`) e nuove proprietà di `Context` (`is_config_branch`, `diff_level`, `min_level`).

- `level` (famiglia `level`): minimo = max(diff, etichette dell'issue, `min_level` dei profili attivi, calcolato come `open-pr`, anche sui file cancellati). Sotto il minimo senza tetto valido: rosso `level_below_minimum`; con `level_cap` in `LEVELS`: `level_cap` («da leggere», motivo in `data`). Livello dichiarato fuori da `LEVELS`: rosso `level_invalid`. Un tetto che non è un livello non nasconde il rosso.
- `l2`: file letti dall'albero della testa (`l2tree.collect`), `check_l2_detail(..., components=ctx.components)` (rilievo I-9). `missing` -> un solo rosso `l2_missing` (conteggio nel `text`, problemi in `data`); `stale` o `spec_reviews_dir` diversa dalla cartella dell'approvazione trovata -> `approval_stale` con il diff (spec e piano, dal blob approvato se è nella storia della testa, altrimenti «diff non disponibile»). Lo stato della spec viene da `approvals.judge_spec` (lo stesso di `check_l2_detail` e di `l2tree.spec_approval`). `audit_off` e `audit_suspended` dal blocco `spec_audit` (solo L2).
- `issue` (solo GitHub): ramo `tg/N-*`: `block_missing` (decisione 6), `block_issue_mismatch`, `closes_mismatch`, `issue_invalid` (assente o non aperta). Altri rami: `not_tg_branch` + `no_issue` (info) o, con «Closes #M», issue M aperta. Ramo `tollgate-config/*`: la sola `tollgate_config` con le chiavi di `tollgate.toml` cambiate (base -> testa, via `tomllib`) e il `FINGERPRINT` in `data`. `diff` salta test-guard e scope per i rami di configurazione.
- `declared` (solo GitHub, salta con `definition_of_done = false`): voci `false` di `dod.items` diverse da `receipt, guard_scope, must_have, approvals` (ricalcolate) -> `dod_false`; rilievi (decisione 11, `f-<c>-<n>` dell'ultimo ciclo, `blocking` assente = bloccante, anche con `unverified`) -> `finding_blocking`; archiviati o declassati sotto `major` (qualunque ciclo) -> `findings_overridden`.
- `notes` (solo GitHub): `sentinel_open` (dagli ingressi, anche senza blocco), `review_unverified`, `off_periods`, `task_over_warn`, `task_over_max` (con il motivo in `data`), `skills_absent`.
- `lockfiles`: `lockfile_without_manifest` (manifest nella stessa cartella, da `scope.lockfiles`).
- `workflow_rules`: `ci_waived_workflow` (deroga `ci` che copre un workflow del progetto modificato, via `waivers.covers`); su GitHub `existing_workflow_rules` (workflow già presenti non toccati dal diff che violano `workflows.problems`).
- `guard_local` (solo locale): rosso `guard_local` per i file di tollgate cambiati rispetto alla base del lavoro; rosso `guard_workflow` per i workflow del progetto cambiati che violano le regole.
- Funzioni pubbliche (D17b h): `tollgate_files_in_work(changes)` (locale, sui `Change` del lavoro) e `tollgate_files_changed(repo, base_ref, head_ref)` (gate, albero della punta del predefinito contro la testa, include cancellati e spostati). Entrambe usano `protected.is_tollgate_file`: nessuna lista ripetuta, nessun `TOLLGATE_FILE_GLOBS` esposto.
- `manual_must_have` (Task 4): `text` fisso «must-have con test manuale: N», nomi in `data`; adattato il test esistente.
- Ogni nuova voce: nel `text` solo testi di tollgate o numeri/valori validati (livelli, numeri di issue, nomi di componenti dalla configurazione); tutto il resto in `data`.

`_over_l0` ora usa `ctx.diff_level` (stesso calcolo, nessun cambiamento di comportamento); `_plan_diff` delega a `_text_diff` (generico).

## Test (`tests/test_gate_evaluate.py`, 111 test nel modulo)

`LevelTest`, `L2Test`, `IssueTest`, `DeclaredTest`, `NotesTest`, `LockfileTest`, `WorkflowWaiverTest`, `TollgateFilesTest`, `LocalTest`, `CoverageTest` (`test_every_group_key_is_produced`, D13): il modulo ha un wrapper `evaluate` che registra le chiavi di `attenzione` prodotte (`SEEN`); in esecuzione isolata il test riesegue le altre classi per raccoglierle. Nessuna chiave è prodotta fuori da `evaluate` (anche `sentinel_open` viene dagli ingressi), quindi non c'è insieme di eccezioni.

## Evidenza TDD

RED 1 (test scritti, nessun codice): `python3 -B -m unittest tests.test_gate_evaluate` -> `ImportError: cannot import name 'tollgate_files_changed' from 'tollgate_gate.evaluate'`.
RED 2 (aggiunte solo le due funzioni sui file di tollgate): `Ran 110 tests in 14.349s`, `FAILED (failures=41)`, nessun errore: tutti i test delle nuove famiglie (LevelTest, L2Test, IssueTest, DeclaredTest, NotesTest, LockfileTest, LocalTest, WorkflowWaiverTest, CoverageTest) più `test_manual_must_have_is_attention`.
GREEN: `python3 -B -m unittest tests.test_gate_evaluate` -> `Ran 111 tests ... OK`; `tests/run` (python3.11 poi python3, `set -e`): `Ran 1944 tests in 415.767s`, `OK` per entrambi; `test_layers` verde (nessun import di `db` o `sqlite3`; nuovi import solo `tomllib`, `re`, `posixpath` e moduli di `tollgate_analysis`).

## Scostamenti dal piano e scelte da segnalare

1. `block_missing` sta nella famiglia `issue` (non in `declared`): deve valere anche con `definition_of_done = false`, che salta `declared`.
2. `level_cap` si emette solo quando il livello dichiarato è sotto il minimo (9.2: «con un tetto dichiarato: `attenzione` rosso» è detto in quel contesto). Un tetto con livello sopra il minimo non genera voce.
3. `l2` giudica il livello dichiarato (non il massimo con il minimo): sotto il minimo c'è già il rosso `level_below_minimum`.
4. `notes`, `issue`, `declared` e `existing_workflow_rules` girano solo su GitHub (decisione 3); `level`, `l2`, `ci_waived_workflow`, `lockfiles` anche in locale.
5. Un rilievo con id non nel formato `f-<c>-<n>` conta come dell'ultimo ciclo (fail-closed).
6. `task_over_max` è informativo anche senza `size_reason` (in locale il report sarebbe già non valido); `tasks_over` con `lines <= task_lines_max` -> `task_over_warn`.
7. `tests/test_gate_evaluate.py` supera ora le 1000 righe: da valutare uno spacchettamento in un task successivo (non fatto: fuori dal task).

## Autorevisione

Brief e voci di `carry.md` del Task 5 coperti (D13, D17b h, decisione 10 `spec_reviews_dir`, `judge_spec`, `ci_waived_workflow`/`review_unverified` prodotte, blocco assente rosso, nomi dei must-have in `data`). Nessun `__pycache__`, nessun cambio ai moduli di altri strati, nessuna rete. Dubbi: solo i punti 1-3 sopra (scelte di interpretazione, reversibili con una riga).

## Fix round 1

Base `00065d7`. Modifiche in `bin/tollgate_gate/evaluate.py` e `tests/test_gate_evaluate.py`.

- I-1: `Context.is_config_branch` richiede `not pr.cross_repo`; un ramo `tollgate-config/*` da fork vale come ramo qualunque (`not_tg_branch`, `no_issue`, test-guard e scope attivi). Test `test_config_branch_from_a_fork_is_a_manual_pr` (fork: `test_deleted` rosso; stesso repo: nessun rosso `diff`).
- I-2: `_findings` fail-closed: se `verdict` manca, non è un dizionario o `cycles` non è un intero, nessun rilievo bloccante si scarta. Test `test_blocking_finding_without_usable_verdict_is_red` (assente, `cycles` stringa, `verdict` non dizionario; con `blocking: False` nessun rosso).
- Ruling `level_cap`: emesso ogni volta che il blocco dichiara un tetto valido (testo diverso se il livello è sotto il minimo o no); il rosso `level_below_minimum` resta solo senza tetto. Test `test_cap_is_reported_even_above_the_minimum`.
- Test di pinning aggiunti (già verdi sul codice esistente): `test_block_missing_on_tg_is_red_even_with_dod_off`, `test_moved_tollgate_file_counts_by_its_old_name`.

RED (`python3 -B -m unittest tests.test_gate_evaluate`, prima del codice): `Ran 116 tests in 40.674s`, `FAILED (failures=5)`: i tre sotto-casi di `test_blocking_finding_without_usable_verdict_is_red`, `test_config_branch_from_a_fork_is_a_manual_pr`, `test_cap_is_reported_even_above_the_minimum`.
GREEN: stesso comando dopo il codice: `Ran 116 tests in 38.023s`, `OK`. `tests/run` in primo piano: python3.11 `Ran 1954 tests in 558.173s OK`; python3 (3.13.5) `Ran 1954 tests in 560.990s OK`; exit 0.
