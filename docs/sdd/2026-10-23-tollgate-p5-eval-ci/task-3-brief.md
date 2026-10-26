### Task 3: Azioni fissate per SHA, versione 0.2.0

**Files:**
- Create: `gate/workflows/PINS`
- Modify: `gate/workflows/tollgate-{guard,run,verdict,base,sentinel}.yml`, `.github/workflows/ci.yml`, `bin/tollgate_core/__init__.py` (`VERSION = "0.2.0"`), `.claude-plugin/plugin.json` (`"version": "0.2.0"`, `"experimental": {"evals": "evals"}`), `tests/test_gate_workflows.py`, `tests/test_init.py`, `tests/test_manifest.py`

**Interfaces:**
- Consumes: esiti VC2.
- Produces: `PINS` (`<azione> <tag> <sha>`, una riga per azione); funzione di test `pins() -> dict[str, tuple[str, str]]` in `tests/test_gate_workflows.py`, riusata da `test_ci_workflow.py`.

- [ ] **Step 1: Test** `PinTest`: `test_every_uses_pinned` (ogni `uses:` dei cinque workflow nella forma `^[\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$`); `test_pins_match_file` (azione, SHA e commento uguali a `PINS`); `test_no_major_tag_left` (nessun `@v` nei workflow); i test esistenti che cercano `startswith("actions/checkout@")` restano verdi. `test_ci_workflow.py::test_ci_workflow_pinned` (Review Focus 5). `test_init.py::test_proposal_workflows_pinned` (i workflow scritti da `init --propose` in `files/` hanno gli stessi `uses:` di `gate/workflows/`, Review Focus 5). `test_manifest.py::test_version_matches_core` (`plugin.json` `version` == `tollgate_core.VERSION`) e `test_experimental_evals`.
- [ ] **Step 2: Fallimento, fissaggio, `tests/run`;** `claude plugin validate --strict .` (esito nel report: è l'unico `claude` vero ammesso a un implementatore, come in P4, perché non lancia il modello). I valori `"0.1.0"` scritti a mano nei test (`tests/test_prereq.py:61,80` e gli altri che `grep -rn '0\.1\.0' tests/` trova) passano a `tollgate_core.VERSION` o restano fissi solo dove provano una versione vecchia.
- [ ] **Step 3: Commit** «tollgate P5: azioni dei workflow fissate per SHA, versione 0.2.0».

---

