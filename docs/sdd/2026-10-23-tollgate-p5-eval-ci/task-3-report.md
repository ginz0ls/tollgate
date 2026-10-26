# Report Task 3: azioni fissate per SHA, versione 0.2.0

Status: DONE. Commit: vedi `git log -1` sul ramo p5-eval-ci.

## Cosa
- `gate/workflows/PINS` (nuovo): `<azione> <tag> <sha>`, una riga per azione (cache/restore e cache/save separate, stesso SHA). Valori da `docs/verifiche/evidenze/p5/pins.tsv`.
- Cinque workflow del gate e `.github/workflows/ci.yml`: ogni `uses:` e' `azione@<sha> # vX.Y.Z`.
- `VERSION = "0.2.0"`; `plugin.json`: version 0.2.0 e `"experimental": {"evals": "evals"}`.
- Test: `PinTest` (4 test, in `tests/test_gate_workflows.py`, con `pins()`, `uses_of()`, `PINNED`); `test_ci_workflow_pinned` al posto di `test_actions_use_current_major_versions`; `test_init.py::test_proposal_workflows_pinned`; `test_manifest.py::test_experimental_evals`; `test_prereq.py:61,80` su `VERSION`.
- D16: la versione di plugin.json legata a `VERSION` e' gia' `tests/test_manifest.py::test_plugin_json` (righe 53-58), non duplicata. `tests/test_prblock.py:16` resta (dato).

## RED / GREEN
RED: `python3 -B -m unittest tests.test_gate_workflows.PinTest tests.test_ci_workflow tests.test_manifest tests.test_prereq` con i test e senza PINS: 57 test, failures=2 errors=4 (`test_every_uses_pinned` "actions/checkout@v4", `test_no_major_tag_left`, PINS mancante, `KeyError: 'experimental'`).
GREEN: stessi test dopo il fissaggio: OK (47 test per PinTest + ci + manifest). Un primo errore mio: `test_pins_match_file` pretendeva che PINS contenesse solo azioni dei cinque workflow, ma setup-python e' solo in ci.yml; il test ora somma gli `uses` di ci.yml.
Suite: `tests/run` (python3.11: 2576 test OK, skipped=2; python3 3.13.5: 2576 test OK), exit 0.

## claude plugin validate --strict .
`✔ Validation passed`; un solo avviso (non bloccante, preesistente): ICON_MISSING (nessuna icona del plugin). `experimental.evals` accettato anche se la cartella `evals/` non esiste ancora.

## Cambi incompatibili letti (cloni in /tmp/tollgate-p5-pins, solo `git show`/`diff`, nessuna rete)
- checkout v4.4.0 -> v7.0.1: `action.yml` cambia solo `node20` -> `node24`. v6: credenziali in un file separato sotto `$RUNNER_TEMP` (irrilevante: tutti gli step hanno `persist-credentials: false`). v7: rifiuto del checkout di PR da fork in `pull_request_target`/`workflow_run` (`allow-unsafe-pr-checkout`); in `src/unsafe-pr-checkout-helper.ts` la logica e' identica a v4.4.0 (cambia solo l'import `.js`), quindi nessuna differenza di comportamento. Il checkout di `verdict` e `guard` e' del ramo predefinito (repo base, ref non `refs/pull/*`): non scatta. Il checkout dell'head della PR avviene solo in `tollgate-run` (`pull_request`, non toccato dal blocco). Nessun adattamento. Nota: accetta anche SHA a 64 caratteri.
- cache v4.3.0 -> v6.1.0 (anche restore/ e save/): solo `node24`. v5 richiede runner >= 2.327.1 (ubuntu-latest ok). v6: ESM; v6.1.0: gestisce l'errore di scrittura con token in sola lettura e abbassa a debug l'avviso «Cache save failed» in save-only (compatibile con le garanzie: nessun salvataggio da `verdict`, restore in sola lettura). Nessun input cambiato.
- upload-artifact v4.6.2 -> v7.0.2: nuovo input `archive` (default `true`, invariato); `include-hidden-files` gia' false di default da v4.4 (invariato); `node24`. Percorsi sotto `${{ runner.temp }}` invariati. Nessun adattamento.
- download-artifact v4.3.0 -> v8.0.2: nuovi input `skip-decompress` (default false) e `digest-mismatch` (default **error**: prima era solo un avviso). Con `name` l'artefatto singolo finisce sempre in `path` (invariato; ora vale anche con un solo artefatto trovato). Gli step di `verdict` e `base` hanno `continue-on-error: true`: un digest non coincidente ora fa fallire lo step (annotazione rossa) invece di un avviso, e `gate evaluate` legge comunque quanto trovato come prima. Scelta: lasciato il default `error` (piu' severo, non altera le garanzie); se il controller preferisce il comportamento vecchio basta `digest-mismatch: warn`.
- setup-python v4.9.1 -> v7.1.0: `node16` -> `node24` (v6, runner >= 2.327.1); nuovi input `mirror`, `mirror-token`, `freethreaded`, `pip-version` (default invariati); v7 solo ESM. `ci.yml` usa solo `python-version`. Nessun adattamento.
- Nessun file mancante nei tag scaricati; non ho scaricato nulla.

Nessun `with:` modificato. Nessun cambio che alteri percorsi degli artefatti, cache in sola lettura nei `workflow_run` o assenza di salvataggi da `verdict`.

## File
`gate/workflows/PINS` (nuovo); `gate/workflows/tollgate-{guard,run,verdict,base,sentinel}.yml`; `.github/workflows/ci.yml`; `bin/tollgate_core/__init__.py`; `.claude-plugin/plugin.json`; `tests/test_gate_workflows.py`, `test_ci_workflow.py`, `test_init.py`, `test_manifest.py`, `test_prereq.py`.

## Scostamenti
- `tests/test_workflows.py:13` (`actions/checkout@v4` in un testo di prova per `workflows.problems`) resta: e' un dato di test, non un workflow reale.
- I test di `start` con `0.0.9` (`tests/test_start.py:220-232`) e `prereq.GATE_FILES` (6 voci) restano verdi; i banchi usano gia' `VERSION`.
- PINS ha tre righe di commento iniziali (ignorate da `pins()`).

## Autorevisione / dubbi
Tutti i 21 `uses:` verificati dal test contro PINS; nessun `@v` rimasto. Dubbio unico: `digest-mismatch` (sopra). Nessun docs aggiornato (spec/rev 26 e doc sono di altri task).
