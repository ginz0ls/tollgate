# Task 4 - Report

## Implementato
- `bin/tollgate_core/violations.py` (nuovo): `guard_config`, `is_docs_md`, `locked_docs`, `scope_exempt`, `is_registered_plan`, `waiver_file`, `diff_violations` (componenti con default acceso, C15). Nessun import di checks/hooks/flow.
- `_common.py`: `is_docs_md`/`locked_docs` alias, `scope_exempt`, `commit_violations`, `_is_registered_plan` delegano; firme a base di `ctx` invariate. `Ctx.guard_config` e `Ctx.waiver_file` delegano.
- `verify.py`: `dod_commands`, `GateRun`, `run_gate`; `run_verify` usa gli stessi passi interni (`_guarded`/`_gate`). Le ricevute portano `produced_by`; `states` e `junits` per ogni comando (anche `related`, se eseguito).

## Scostamenti / scelte
- `run_gate` senza alcun comando restituisce `ok=False, sha=None` ("nessun comando del gate da eseguire", C17); `run_verify` mantiene il comportamento precedente (flag interno `strict`).
- Il prefisso dei messaggi è `tollgate <produced_by>:` (per verify resta `tollgate verify:`).
- `run_gate` non aggiunge da solo i `dod`: il chiamante passa `extra=dod_commands(cfg, files)`.

## Test
- `tests/test_violations.py` (5 test, incluso C23: attesi espliciti + uguaglianza con `_common.commit_violations`), `tests/test_verify.py::RunGateTest` (5 test).
- RED: `RunGateTest` falliva con AttributeError (`run_gate`/`dod_commands` assenti); GREEN dopo l'implementazione.
- Suite hook invariata e verde senza modificare i test; `tests/test_layers.py` verde.
- tests/run: python3.11 e python3, 1088 test OK.
