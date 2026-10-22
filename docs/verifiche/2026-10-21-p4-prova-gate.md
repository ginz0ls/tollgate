# Prova reale del gate su GitHub (P4, criteri 10, 11 e 34)

Versioni: gh [da compilare], tollgate [da compilare] (`tollgate_core.VERSION`), git [da compilare]. Data: [da compilare].

Piano: Task 16 di P4, Step 1-4. Script: `spikes/run-p4-gate.sh` (`elenco`, `installa <repo>`, `protezione`, `caso <nome>`, `raccogli`, `controlla`),
`spikes/p4/make_case.py` (rami, file e corpo delle PR), `spikes/gh-p4/ghguard.py` (lista unica degli ammessi), `spikes/gh-p4/ghwrap.py` (gh con guardia).
Uscite grezze in `docs/verifiche/evidenze/gh-p4/` (mai cancellate: un file che esiste già si rinomina in `<nome>.prev-<tempo>`): `comandi.log`,
`installa-*`, `protezione-*`, `caso-<nome>-<ora>-*` (descrizione, `case.json`, corpi delle PR, stati con autore, commenti, forma di `GET pulls/<n>`, run e minuti),
`casi-righe.md`, `raccogli-*`.

**Esito: [da compilare: riuscito / composito / non riuscito].** Un caso non ottenuto si scrive «non riuscito» con la causa, mai «riuscito»; un esito ottenuto in più
tentativi si dichiara composito.

## Impianto

- Repo: `ginz0ls/tollgate-p4-protected` (pubblico, modalità `protected`) e `ginz0ls/tollgate-p4-detect` (privato, GitHub Free, modalità `detect`). Operazioni ammesse: decisione 25.
- Progetto di prova (`make_case.baseline_files`): `src/calc.py` con `tests/test_calc.py` (unittest, report JUnit con `tools/unittest_junit.py`), profilo `web` (`web/**`,
  comando con `|| true`), profilo `notes` (`notes/**`, comando che non esegue test), `allow_no_tests = false` su protected e `true` su detect.
- Installazione: [da compilare: SHA del progetto, SHA dell'installazione, SHA del commit vuoto; `init --propose` (uscita), modalità proposta, `protect.sh` presente su protected e assente su detect].
- Codice di tollgate nel repo pubblico dal [da compilare]; avvisato l'utente: [da compilare]. Cancellazione del repo pubblico chiesta all'utente il [da compilare] (decisione 25).

## Installazione e protezione (criteri 11 e 34)

| Verifica | Atteso | Ottenuto | Evidenza |
|---|---|---|---|
| `init --propose` su protected (non protetto) | modalità `protected`, `protect.sh` proposto | | `installa-protected-modo.txt` |
| `init --propose` su detect | modalità `detect`, nessun `protect.sh` | | `installa-detect-modo.txt` |
| `tollgate-base` sul primo push (miss della cache) | job verde; su detect `tollgate/base` `success` | | `installa-*-miss-*` |
| `tollgate-base` sullo stesso albero (hit della cache) | job verde; su detect `tollgate/base` `success` | | `installa-*-hit-*` |
| Primo push su detect (criterio 34) | nessuna issue di sentinel | | `installa-detect-miss-issue-sentinel.txt` |
| `protect.sh` | `app_id` letto dal check-run, PUT riuscita, GET della protezione completa | | `protezione-*` |
| Protezione con `strict` tolto a mano (controller) | `start` segnala il campo mancante | | [da compilare] |
| Protezione rimessa completa (controller) | `start` senza avvisi | | [da compilare] |

## Casi (criterio 10 su protected, Step 4 su detect)

Un caso per riga; «atteso» e «ottenuto» sono gli stati `tollgate/guard`, `tollgate/verdict`, `tollgate/attention` (ultimo stato per contesto, con l'autore) e, su protected,
`mergeStateStatus`. «Minuti» sono i minuti di Actions dei run della PR (`*-runs.tsv`).

| Caso | Repo | PR | SHA | Stati con autore | Atteso | Esito | Minuti | Note |
|---|---|---|---|---|---|---|---|---|
| verde-pulita | protected | | | | guard=success, verdict=success, attention=success, merge=CLEAN | | | |
| verde-edit | protected | | | | guard=success, verdict=success, attention=success, merge=CLEAN | | | |
| verde-config | protected | | | | guard=success, verdict=success, attention=failure, merge=CLEAN | | | |
| verde-ramo-libero | protected | | | | guard=success, verdict=success, attention=failure, merge=CLEAN | | | |
| rosso-test-tolti | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-skip | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-fuori-scope | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-base-id | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-or-true | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-livello | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-l2-mancante | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-deroga-altra-issue | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-zero-test | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| rosso-piano-file-nuovo | protected | | | | guard=success, verdict=failure, attention=failure, merge=BLOCKED | | | |
| guard-wf-prt | protected | | | | guard=failure, verdict=failure, attention=*, merge=BLOCKED | | | |
| guard-wf-run | protected | | | | guard=failure, verdict=failure, attention=*, merge=BLOCKED | | | |
| guard-wf-statuses | protected | | | | guard=failure, verdict=failure, attention=*, merge=BLOCKED | | | |
| guard-wf-writeall | protected | | | | guard=failure, verdict=failure, attention=*, merge=BLOCKED | | | |
| guard-wf-ancora | protected | | | | guard=failure, verdict=failure, attention=*, merge=BLOCKED | | | |
| guard-toml | protected | | | | guard=failure, verdict=success, attention=*, merge=BLOCKED | | | |
| guard-verdict-yml | protected | | | | guard=failure, verdict=failure, attention=*, merge=BLOCKED | | | |
| verde-workflow-ci | protected | | | | guard=success, verdict=success, attention=failure, merge=CLEAN | | | |
| attenzione-deroga-test | protected | | | | guard=success, verdict=success, attention=failure, merge=CLEAN | | | |
| attenzione-piano-testo | protected | | | | guard=success, verdict=success, attention=failure, merge=CLEAN | | | |
| attenzione-tetto-livello | protected | | | | guard=success, verdict=success, attention=failure, merge=CLEAN | | | |
| attenzione-zero-test | detect | | | | guard=success, verdict=success, attention=failure | | | |
| error-dotdot | protected | | | | guard=failure, verdict=error, attention=error, merge=BLOCKED | | | |
| error-entita | protected | | | | guard=failure, verdict=error, attention=error, merge=BLOCKED | | | |
| rosso-entita-tools | protected | | | | guard=success, verdict=failure, attention=success, merge=BLOCKED | | | |
| error-sha-superato | protected | | | | guard=success, verdict=success, attention=success, merge=CLEAN | | | |
| error-due-pr | protected | | | | guard=error, verdict=error, attention=error, merge=BLOCKED | | | |
| non-applicabile | protected | | | | guard=none, verdict=none, attention=none | | | |
| token-personale | protected | | | | guard=success, verdict=success, attention=success, merge=BLOCKED | | | |
| detect-pulita | detect | | | | guard=success, verdict=success, attention=success | | | |
| detect-closes | detect | | | | guard=success, verdict=failure, attention=success | | | |
| detect-merge-rosso | detect | | | | sentinel=failure | | | |
| detect-push-diretto | detect | | | | sentinel=failure | | | |

Nota: `detect-merge-rosso` unisce in `main` di detect un cambio con un test tolto e va lanciato per ultimo tra i casi detect: i casi detect lanciati dopo partono da una base degradata (gli identificativi della base non hanno `test_sottrai`). Un ripristino richiederebbe un commit nuovo, mai un reset.

## Forme lette dal vero (voci di `carry.md`)

- `gh api --paginate --jq` su `statuses`, `issues/<n>/comments`: formato dell'uscita: [da compilare]. `-F body=@file` con `PATCH issues/comments/<id>` (commento aggiornato, non duplicato): [da compilare].
- `GET pulls/<n>`: forma letta da `verdict` (`head.repo`, `head.sha`, `base.ref`, `body`, `state`) e confronto con `verdict.pr_from_rest`: [da compilare] (`caso-*-pulls.out`).
- `tollgate/base` su miss e su hit della cache: [da compilare].
- Cache mode dei job `workflow_run` (V4) riletta sul privato `detect`: [da compilare].

## Minuti di Actions

Repo privato `detect`: [da compilare] minuti fatturati (stima del piano: sotto i 200). Repo pubblico: non fatturati. (`raccogli-*-minuti.txt`)

## Difetti e osservazioni

[da compilare: ogni difetto del piano o del codice, con il commit e il test che lo copre, e il caso ripetuto]

## Ciò che resta non esercitato

[da compilare]
