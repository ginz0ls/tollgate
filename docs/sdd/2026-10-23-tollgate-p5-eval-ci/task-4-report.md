# Task 4 — report dell'implementatore

Commit: `0c40787` «tollgate P5: gate, voce per i comandi della base mancanti, config per blob, minori del calcolo». Ramo `p5-eval-ci`.
`tests/run`: python3.11 2603 test OK (2 saltati), python3 (3.13.5) 2603 OK; output pulito.

## Cosa
- **M-1 (decisione 14, D14)**: `attention.GROUPS["base_ids_missing_command"] = READ`; `baseids.BaseIds(ids, commands)` + `baseids.load_full` (`load` la chiama); `commands` assente nel file = `{}`, non mappa o stato fuori da `run.STATES` = `None`; `GateInputs.base_commands` (default `None`); `verdict._base_ids` ritorna `BaseIds` e `inputs_from_github` riempie `base_ids` e `base_commands` (cache e artefatto del run). `evaluate.base_ids`: per ogni `ctx.required` con `spec.report` non vuoto, `_base_command_missing` (assente da `ids`; con stati noti: `empty`/`uncounted`/`unverified`/senza stato/`red` con `ids` vuoti = setup fallito; `red` con JUnit no). Nomi (dalla configurazione) in `data`. Skill `skills/finish/SKILL.md:32` aggiornata.
- **M-5 (decisione 17)**: `verdict._config_changed(repo, config_sha, tip)`: `config_sha` deve essere 40-64 esadecimali (dato non fidato), antenato della punta (`git merge-base --is-ancestor` via `git.ok`), e blob di `tollgate.toml` (`git.blob_at`, ls-tree) presente e uguale nei due commit; ogni dubbio = cambiato.
- **M-9**: `AgreementTest.test_agreement_from_real_gate_inputs`.
- **Minori**: `workflows._SCOPE` (valore attaccato ai due punti), `prref._visible` (citazioni e commenti HTML anche multi-riga o non chiusi), `waivers._ID` (`\Z`, `[0-9]`), `comment._one_line` (`](` → `]​(`), `evaluate._command` (testo «dichiarato green ma senza codice di uscita»), `evaluate()` cattura `GitError`, `OSError`, `ValueError`, `runner.run_one` cattura `OSError` nella lettura del report (nota nel log), `init._MODE_LINE` (apici singoli), `evaluate.base_path(test_id, exists=None)` (sceglie il primo percorso che esiste nella base, memoizzato per percorso; senza `exists` l'euristica di prima).

## Evidenza TDD (RED poi GREEN)
RED (prima del codice), comandi:
- `python3 -B -m unittest tests.test_workflows tests.test_prref tests.test_waivers tests.test_gate_comment`: `FAILED (failures=37)` (sub-test di `test_flow_mapping_without_space_is_red` x4, `test_unknown_permission_value_is_red` x20, `test_closes_in_quote_or_html_comment_ignored` x8, `test_id_with_trailing_newline_rejected` x1, `test_markdown_links_and_images_inert` x3 + i 3 elencati).
- `python3 -B -m unittest tests.test_runner tests.test_init.ModeRewriteTest`: `FAILED (failures=1, errors=2)`; il runner dà `OSError: [Errno 5] Input/output error` (traceback), `with_mode` dà `'[gate]\nmode = "detect"\nmode = \'protected\'\n'` (chiave duplicata).
- `python3 -B -m unittest tests.test_gate_evaluate tests.test_gate_run tests.test_gate_github`: `FAILED (failures=5, errors=23)`: `TypeError` per `base_commands`/`load_full`/`_config_changed`/`exists` assenti; `FAIL` per `test_exit_none_declared_green_has_warning`, `test_base_path_follows_files_in_base`, `test_commands_of_the_base_reach_the_gate [cache]`, `test_config_sha_ancestor_is_accepted`, `test_merge_not_touching_toml_is_not_error`.
- `test_prblock.test_findings_carry_blocking_field`: riscritto sul produttore vero (`openpr.facts` da `FlowLab` con due rilievi, uno `R-1` non bloccante e uno `piano:*` bloccante). Verificato per mutazione: tolto `"blocking"` da `bin/tollgate_flow/openpr.py:429-433` il test dà `KeyError: 'blocking'`; ripristinato (file senza diff).
GREEN: gli stessi comandi, `OK` (`tests.test_gate_evaluate tests.test_gate_run tests.test_gate_github`: 224 test OK; i quattro file di analisi + runner/init/prblock: OK); gruppo `test_layers test_skill_contract test_criteria_p4 test_finishcheck test_gate_sentinel test_gate_guard test_gate_run test_gate_github test_gate_evaluate`: 400 OK; poi `tests/run` completo.

## Test per voce del brief
- Step 1: `BaseIdsTest` in `test_gate_evaluate.py` (`test_missing_command_in_ids_is_read_attention`, `test_command_not_green_in_base_is_read_attention`, `test_old_config_cache_without_new_command`, `test_command_without_report_gives_no_item`, `test_base_ids_from_run_carries_commands`, più `test_command_red_with_junit_or_green_gives_no_item`, `test_missing_command_data_lists_only_configured_names`, `test_base_path_follows_files_in_base`, `test_base_path_uppercase_segment`); `test_gate_run.py::BaseIdsTest.test_load_full_returns_commands`; `test_gate_github.py::BaseIdsTest.test_commands_of_the_base_reach_the_gate` (cache e artefatto dal `verdict`); `test_groups_follow_decision_7` con la chiave nuova. `CoverageTest.test_every_group_key_is_produced` verde.
- Step 2: `test_gate_github.py::ConfigShaTest` (5 test del brief + `test_config_changed_is_a_bool_and_fail_closed`). Merge vero a due genitori per `test_merge_not_touching_toml_is_not_error`.
- Step 3: tutti presenti, vedi sopra.
- Step 4: `test_criteria_p4.py::AgreementTest.test_agreement_from_real_gate_inputs`: `GateLab` (stessa configurazione e file della `FlowLab`, `plan_text(tasks=1)`, stessi cinque commit), `gate run` come processo per gli artefatti, `verdict.inputs_from_github` (configurazione della punta, merge-base, blocco del corpo, artefatti), `gate evaluate --publish` come processo (verdetto `failure`), `finish check` su `FlowLab`: chiavi rosse uguali (`out_of_scope`, `test_deleted`) e `plan_changed` assente. È un test di guardia: passa subito (nessun codice da cambiare).

## Scostamenti dal piano e decisioni
1. **D16**: `statuses: bogus` in forma a blocco era già rosso. Il test `test_unknown_permission_value_is_red` copre anche la forma a flusso senza spazio (`{statuses:bogus}`, `{checks:admin}`…), che oggi NON era rossa: premessa vera, stesso difetto di `test_flow_mapping_without_space_is_red`. Le forme a blocco restano come regressione già verde (dichiarato).
2. `test_exit_none_declared_green_has_warning`: l'«avviso» è il testo della voce rossa (`command_red`) con «dichiarato green ma senza codice di uscita»; nessuna voce `attenzione` nuova (il comando è già rosso). Un `red` dichiarato con uscita assente non cambia testo (è il caso del setup saltato).
3. `base_path` ha un parametro `exists` (invece del solo test): scelta dal rilievo M-2 di P4 (`task-4-review.md`), il brief chiede solo `test_base_path_uppercase_segment`. Costo: una `git cat-file -e` per percorso candidato, solo sugli id mancanti.
4. `closes_issue`: «citazione» = riga che comincia con `>` dopo gli spazi; non tratto i blocchi di codice (non richiesto).
5. `_one_line` spegne `](` con uno ZWSP: `![z]` resta senza `(` e non è un'immagine; i riferimenti `[x][ref]` e gli URL nudi non sono toccati (fuori dal brief).
6. `_config_changed` usa `git.blob_at` (ls-tree) invece di `rev-parse <sha>:tollgate.toml`: stesso risultato, già con le garanzie delle funzioni di `tollgate_core.git`; `config_sha` forzato a esadecimale prima di ogni chiamata a git.
7. Le fixture che passano `base_ids={}` (MustHave) ricevono ora anche la voce nuova (attenzione), ma i test guardano `ev.red` o `attention[0]` e restano verdi.

## Autorevisione
Completo rispetto a brief e D4/D14/D16/decisione 17; strati rispettati (`tests/test_layers.py` verde: `tollgate_gate` usa solo `git`, niente `db`/`sqlite3`); un solo calcolo del gate (voce in `evaluate`); testo non fidato: i nomi in `data` vengono da `ctx.required` (configurazione), mai da `ids.json`; nessun argomento di git/gh da testo non fidato (`config_sha` validato).

## Dubbi
- La voce nuova rende `tollgate/attention` rosso finché la base non ha girato il comando (costo dichiarato nella decisione 14). Con `base_commands` ignoto (file senza `commands`) tutti i comandi con report risultano «mancanti».
- `finish check` locale non produce mai `base_ids_missing_command` (base_ids è None): la chiave sta nella riga «da leggere» della skill solo perché il test del contratto la richiede.
