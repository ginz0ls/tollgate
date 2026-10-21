# Ri-revisione giro di correzione 1, Task 7 (57c79f0..dfe3938)

Controlli: diff, report, `actapply`/`l2acts`/`audit` correnti; eseguito `python3 -B -m unittest tests.test_actapply tests.test_l2acts` (83 test OK).

### Verdetti sui rilievi
1. **Duplicazione `l2acts` / `audit` / `actapply` (Important)**: INDIRIZZATO. `audit.py` espone `on`, `comp`, `work_base`, `work_config` (audit.py:146, unico caricamento della config usato da `_context` audit.py:416, `l2acts._cfg` l2acts.py:34, `actapply._config` actapply.py:32-37), `committed_blob`/`Uncommitted` (usati da `audit._committed` e `l2acts._committed`) e `plan_check(cfg, text)` (usato da `_decide_plan` e `approve_plan`). `l2acts._on`, la `_cfg` copiata, la sequenza blob e la chiamata `check_plan` non esistono più. Strati: `l2acts` importa solo `audit` e core/analysis; `actapply` importa `audit` e `l2acts`; nessun import di `actapply` in `l2acts`.
2. **`approve plan` con blob attuale (Minor)**: INDIRIZZATO. `_spec_approved` passa `spec_blob` a `locate_spec_approval` (l2acts.py:~190), con ripiego a `spec_blob=None` solo per distinguere «cambiata» da «assente». Test `test_later_slice_approval_with_current_sha_wins_over_stale_lower_issue` (due issue, la 3 stantia, la 5 attuale).
3. **`_resolve` con worktree nullo (Minor)**: INDIRIZZATO. actapply.py:60 `cfg = _config(...) if work["worktree"] else None`, `suspend_on_resolve` usa `config.DEFAULTS` (l2acts.py:267). Test `test_resolve_without_worktree_falls_back_to_default_caps`.
4. **`test_wrong_slice_count_refused` (Minor)**: INDIRIZZATO. Asserisce «la spec prevede 3 fette: /tollgate:approve spec 3».
5. **Test in `blocked` e spec non committata (Minor)**: INDIRIZZATO. `test_blocked_refused_pointing_to_resolve` per spec e plan, `test_uncommitted_spec_refused`.

Cambio segnalato `actapply._config`: regge. Chiamanti: `_resolve` writer (actapply.py:41), `_resolve` tetti (60, protetto da `if worktree`), `_approve_level` (217). Prima base o worktree assenti davano `TypeError` (`Path(None)`) o una config con base `None`; ora `ConfigError` convertito in `ActApplyError("configurazione non valida: ...")`. I test esistenti di `actapply` passano (83 OK, con `test_l2acts`); la suite completa è riportata verde dall'implementatore (1629 su 3.11 e 3.13).

### Danni nuovi nel diff della correzione
- **Minor**, audit.py:146-155: con `TOLLGATE_TEST_CONFIG` impostato la config non dipende dalla base, ma `work_config` rifiuta comunque se la base manca; prima `actapply._config` passava. Solo ambiente di test, nessun test rotto. Inoltre in `_approve_level` un lavoro senza worktree ora dice «configurazione non valida: il lavoro non ha un worktree» invece del messaggio successivo «lavoro senza base o worktree» (solo testo).

### Osservazioni fuori ambito
Altri moduli (`finalreview`, `openpr`, `taskcmd`, `finishcheck`, `sync`, audit.py:562) ripetono ancora `work_base_sha or default_ref` + `load_config`: candidati futuri a `work_config`, non toccati dal Task 7.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
