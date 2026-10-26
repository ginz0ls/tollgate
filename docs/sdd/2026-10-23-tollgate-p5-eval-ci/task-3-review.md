# Revisione Task 3 (6352aa9..8f92827)

### Aderenza
- ✅ Ogni `uses:` dei cinque workflow e di `ci.yml` (21) rispetta `^[\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$` (grep inverso vuoto); nessun `@v\d` rimasto in `gate/`, `.github/`, `bin/`.
- ✅ SHA e tag uguali a `PINS` e a `pins.tsv`: controllati checkout v7.0.1 `3d3c42e5…`, cache v6.1.0 `55cc8345…`, upload-artifact v7.0.2 `cf430e03…`, download-artifact v8.0.2 `9000827c…`, setup-python v7.1.0 `6d4fd22b…` (tutti e cinque presenti in `pins.tsv`). Sono le maggiori più recenti su node24 come da ruling (carry, decisione 13), non la v4.
- ✅ `init --propose` copia i workflow di `gate/workflows/`: `test_proposal_workflows_pinned` confronta i `uses:` e passa; `--update` usa lo stesso `install.py:94`.
- ✅ `VERSION` e `plugin.json` a 0.2.0; `experimental.evals` = `"evals"`; D16 rispettata (nessun duplicato di `test_manifest.py:53-58`, `test_prblock.py:16` resta); `test_prereq.py` su `VERSION`.
- ✅ Sostituito (non affiancato) `test_actions_use_current_major_versions` con `test_ci_workflow_pinned`. I test con `startswith("actions/…@")` restano validi e verdi. Eseguiti: PinTest, test_ci_workflow, test_manifest, test_init.FilesTest: 52 OK.
- ✅ Cambi incompatibili verificati di persona sui cloni (`git diff` di `action.yml` e `src/`): checkout solo `node20→node24` in action.yml; upload-artifact solo input `archive` (default true) e node24; cache solo node24; download-artifact aggiunge `skip-decompress` (false) e `digest-mismatch` (default error), `name` con un solo artefatto finisce sempre in `path`; setup-python (cloni con soli v4.9.1 e v7.1.0, v5/v6 non disponibili) usato solo con `python-version`. Nessun input usato dai workflow è tolto o rinominato. Percorsi sotto `runner.temp`, cache in sola lettura dei job `workflow_run` e `persist-credentials: false` non cambiano. Checkout v7: il blocco `assertSafePrCheckout` scatta solo con `pull_request_target`/`workflow_run` da fork; `verdict`/`guard` fanno checkout del ramo predefinito, `tollgate-run` è `pull_request`. Il report è esatto.
- ⚠️ Nuovo in checkout v7 non citato nel report: `tryGetRepositoryObjectFormat` (una chiamata API col token per rilevare sha256, "try", non fatale) e `testRef` che fallisce se `ref` non punta al `commit` atteso. I nostri `ref` sono SHA o ramo senza `commit` esplicito: nessun impatto atteso, ma si vede solo girando su GitHub (Task 13).

### Punti di forza
- `pins()` unica fonte per test del gate, della CI e di init; `test_pins_match_file` chiude anche il verso inverso (PINS senza azioni inutilizzate).
- RED registrato prima del fissaggio; errore del proprio test (setup-python solo in ci.yml) dichiarato e corretto.
- Report onesto sul punto di `digest-mismatch`.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `gate/workflows/tollgate-verdict.yml:21,29` e `tollgate-base.yml`: la ruling dice che con `digest-mismatch: error` «verdict pubblica `error` per artefatto non valido». In v8.0.2 (`src/download-artifact.ts`) l'artefatto con digest diverso viene comunque scaricato ed estratto, poi lo step fallisce; `continue-on-error` lo assorbe e `gate evaluate` non vede l'esito dello step, quindi legge il contenuto non coincidente come prima (con la v4 era un avviso). Non peggiora rispetto a v4 e non è una regressione, ma la motivazione della ruling non è realizzata dal workflow: se si vuole fail-closed vero serve `outcome` dello step o validazione dello schema in `evaluate`. Da annotare per il Task 13/12, non da correggere qui.
2. `tests/test_gate_workflows.py` `test_every_uses_pinned`: l'ultima asserzione `any(...)` è debole (basta un workflow con `uses`); meglio asserire per ogni workflow che i `uses` non siano vuoti o il conteggio atteso. `uses_of` non gestisce `uses:` quotato, ma `PINNED` lo rifiuterebbe comunque (fail-closed).

### Valutazione
**Qualità del task:** Approvato. **Motivo:** pin, PINS, versione e test corrispondono ai requisiti e al ruling; i cambi incompatibili dichiarati sono confermati sui cloni e nessuno altera percorsi, cache o credenziali; restano due Minor.
