### Task 7: `gate run`, `gate base-ids` e artefatti

**Files:**
- Create: `bin/tollgate_gate/run.py`, `bin/tollgate_gate/baseids.py`, `bin/tollgate_gate/artifacts.py`, `bin/tollgate_gate/cli.py`, `tests/test_gate_run.py`, `tests/test_gate_artifacts.py`
- Modify: `bin/tollgate` (smistamento di `gate` prima di importare `tollgate_core.cli`, decisione 1), `bin/tollgate_core/cli.py` (una riga dell'aiuto), `tests/test_cli.py`

**Interfaces:**
- Consumes: `runner` (Task 2), `config.load_config_at`.
- Produces: `run.run(repo: Path, *, config_sha: str, base_sha: str, out: Path, environ: Mapping[str, str], applicable: bool) -> int` (scrive `out/results.json`, `out/junit/`, `out/logs/`; 0 sempre che il file sia scritto, 1 solo se non si può scrivere; lo stato lo decide `verdict`); `baseids.compute(repo, *, config_sha, sha, out, environ) -> dict` (il formato della decisione 12) e `baseids.load(path, *, tree: str) -> dict[str, set[str]] | None` (per comando, decisione 12) (`None` se illeggibile o con `tree` diverso); `artifacts.validate(root: Path, *, max_file=50 * 2**20, max_total=200 * 2**20) -> list[str]`, `artifacts.read_results(root) -> tuple[list[CommandResult] | None, bool, list[str]]` (risultati, `applicable`, problemi); `cli.main(args) -> int` per `gate run|base-ids|guard|evaluate|sentinel` (gli ultimi tre nei Task 8-10).
- CLI: `tollgate gate run --event <file> --out <dir>`, `tollgate gate base-ids --sha <sha> --out <dir> [--event <file>] [--publish]`. `gate run` legge dall'evento `pull_request.base.ref`, la punta del predefinito (`repository.default_branch`, `git rev-parse origin/<predefinito>`) e scrive `applicable: false` se la PR non punta al predefinito, senza eseguire nulla. Il sottocomando `gate` non apre il DB e non crea la cartella di stato: `bin/tollgate gate …` non carica `tollgate_core.cli`.

- [ ] **Step 1: Test** `test_gate_run.py`: `test_results_shape` (banco con un comando che scrive JUnit: `results.json` con i campi della decisione 13, JUnit copiato); `test_not_applicable_runs_nothing`; `test_config_from_default_tip_not_head` (la testa cambia `[commands]` → si eseguono i comandi del predefinito); `test_no_state_created` (il vero `bin/tollgate gate run` lanciato come processo, con `HOME` e `TOLLGATE_STATE` temporanei e `PYTHONVERBOSE` per elencare i moduli caricati: nessuna cartella creata, né `tollgate_core.db` né `sqlite3` caricati); `test_base_ids_format_and_tree` (`ids` come mappa comando → identificativi, letta da `load` come `dict[str, set[str]]`); `test_load_rejects_other_tree`.
- [ ] **Step 2: Test** `test_gate_artifacts.py`: `test_dotdot_absolute_symlink_rejected`; `test_report_path_in_results_json_rejected` (`"report": "../x.xml"`, assoluto, fuori da `junit/`); `test_size_limits` (con limiti piccoli passati per parametro); `test_xml_entity_rejected` (criterio 10 `error`); `test_valid_dir`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: gate run e base-ids senza stato, artefatti validati».

---

