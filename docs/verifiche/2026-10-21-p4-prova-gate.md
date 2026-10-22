# Prova reale del gate su GitHub (P4, criteri 10, 11 e 34)

Versioni: gh 2.46.0 (2025-01-13 Debian 2.46.0-3), tollgate 0.1.0 (`tollgate_core.VERSION`), git 2.47.3. Date: dal 21 al 22 ottobre 2026 (installazione il 21, casi e giri di correzione il 22).

Piano: Task 16 di P4, Step 1-4. Script: `spikes/run-p4-gate.sh` (`elenco`, `installa <repo>`, `protezione`, `caso <nome>`, `raccogli`, `controlla`),
`spikes/p4/make_case.py` (rami, file e corpo delle PR), `spikes/gh-p4/ghguard.py` (lista unica degli ammessi), `spikes/gh-p4/ghwrap.py` (gh con guardia).
Uscite grezze in `docs/verifiche/evidenze/gh-p4/` (mai cancellate: un file che esiste già si rinomina in `<nome>.prev-<tempo>`): `comandi.log`,
`installa-*`, `protezione-*`, `caso-<nome>-<ora>-*` (descrizione, `case.json`, corpi delle PR, stati con autore, commenti, forma di `GET pulls/<n>`, run e minuti),
`casi-righe.md`, `raccogli-*`.

**Esito: composito.** Gli ultimi esiti dei 37 casi sono tutti «riuscito», ma sette casi sono riusciti solo dopo uno o più tentativi non riusciti (`verde-config` al quarto tentativo, `verde-edit`, `verde-ramo-libero`, `verde-workflow-ci` e `attenzione-deroga-test` al terzo, `attenzione-piano-testo` e `attenzione-tetto-livello` al secondo). I 30 casi restanti sono riusciti al primo giro col codice dell'installazione. I tentativi non riusciti sono elencati sotto con la causa. Installazione, protezione e criteri 11 e 34: riusciti al primo tentativo registrato.

## Impianto

- Repo: `ginz0ls/tollgate-p4-protected` (pubblico, modalità `protected`) e `ginz0ls/tollgate-p4-detect` (privato, GitHub Free, modalità `detect`). Operazioni ammesse: decisione 25.
- Progetto di prova (`make_case.baseline_files`): `src/calc.py` con `tests/test_calc.py` (unittest, report JUnit con `tools/unittest_junit.py`), profilo `web` (`web/**`,
  comando con `|| true`), profilo `notes` (`notes/**`, comando che non esegue test), `allow_no_tests = false` su protected e `true` su detect.
- Installazione. Protected: progetto `25670ec`, installazione `0eebf77`, commit vuoto `166d728`. Detect: progetto `a40181f`, installazione `4c8bb58`, commit vuoto `6d399c9`. `init --propose` ha scritto la proposta in `docs/superpowers/tollgate-init/` (129 file) con modalità `protected` su protected (`protect.sh` presente) e `detect` su detect (`protect.sh` assente): `installa-*-modo.txt`, `installa-*-init.out`.
- Codice di tollgate nel repo pubblico: i repo sono stati creati il 21 ottobre 2026 alle 15:54:33Z (protected, `--public`) e 15:55:04Z (detect, `--private`) (`comandi.log`). La data dell'avviso all'utente e della richiesta di cancellazione del repo pubblico (decisione 25) non è registrata nelle evidenze di questo Task: non riportata qui, resta in capo al controller.
- Versioni di installazione nei repo di prova: protected è stato aggiornato col codice corretto due volte (vedi «Aggiornamenti di protected»); detect è rimasto col codice dell'installazione (nessun caso da ripetere lì).

## Installazione e protezione (criteri 11 e 34)

| Verifica | Atteso | Ottenuto | Evidenza |
|---|---|---|---|
| `init --propose` su protected (non protetto) | modalità `protected`, `protect.sh` proposto | riuscito: `mode = "protected"`, `protect.sh` presente | `installa-protected-modo.txt` |
| `init --propose` su detect | modalità `detect`, nessun `protect.sh` | riuscito: `mode = "detect"`, `protect.sh` assente | `installa-detect-modo.txt` |
| `tollgate-base` sul primo push (miss della cache) | job verde; su detect `tollgate/base` `success` | riuscito: protected `0eebf77` (job e run `success`); detect `4c8bb58` (job e run `success`, `tollgate/base` `success`). Su protected `tollgate-base` non pubblica lo stato `tollgate/base`: il segnale è il job | `installa-*-miss-base-conclusione.txt`, `installa-detect-miss-statuses.out` |
| `tollgate-base` sullo stesso albero (hit della cache) | job verde; su detect `tollgate/base` `success` | riuscito: protected `166d728` e detect `6d399c9` (job e run `success`; detect con `tollgate/base` `success`) | `installa-*-hit-base-conclusione.txt`, `installa-detect-hit-statuses.out` |
| Primo push (criterio 34) | nessuna issue di sentinel | riuscito su entrambi: «issue di sentinel aperte dopo il primo push: 0 (atteso 0)». Sul commit vuoto (hit) è stata aperta una sentinel, chiusa dopo la verifica: detect #2, protected #9 (titolo «tollgate: merge non verificato», 0 commenti) | `installa-*-miss-issue-sentinel.txt`, `installa-detect-hit-issue-2.out`, `installa-protected-hit-issue-9.out` |
| `protect.sh` | `app_id` letto dal check-run, PUT riuscita, GET della protezione completa | riuscito: «Protezione di main con app_id 15368 (controlli: tollgate/guard, tollgate/verdict)»; GET con `required_status_checks.strict` vero e contesti `tollgate/guard` e `tollgate/verdict`, `app_id` 15368, `enforce_admins` attivo | `protezione-protect.out`, `protezione-get.out` |
| Protezione con `strict` tolto a mano (controller) | `start` segnala il campo mancante | riuscito: `start` (issue #10) avvisa «protezione di main: manca ramo aggiornato obbligatorio (strict)»; sul detect (issue #3) avvisa «modalità rilevazione: il merge non è impedito» | `crit11-put-senza-strict.out`, `crit11-protected-start-senza-strict.out`, `crit11-detect-start.out` |
| Protezione rimessa completa (controller) | `start` senza avvisi riuscito: `protect.sh` rieseguito dopo la prova (10:31:20Z, PUT e GET riuscite); poi `start` (issue #106) senza alcun avviso sulla protezione, solo «stati di tollgate assenti sul predefinito» (atteso); issue chiusa | `comandi.log`, `crit11-protected-issue-completa.out`, `crit11-protected-start-completa.out`, `crit11-protected-issue-completa-close.err` |

L'avviso «stati di tollgate assenti sul predefinito» compare in entrambi gli `start` ed è atteso: sul `main` ci sono solo push diretti, senza PR con gli stati. Le issue di prova del criterio 11 (#3 su detect, #10 e #106 su protected) sono state chiuse (`crit11-*-issue-close.*`, `crit11-protected-issue-completa-close.*`).

## Casi (criterio 10 su protected, Step 4 su detect)

Un caso per riga: l'ultimo tentativo riuscito. «Atteso» e «Stati con autore» sono gli stati `tollgate/guard`, `tollgate/verdict`, `tollgate/attention` (ultimo stato per contesto) e, su protected, `mergeStateStatus`. L'autore è `github-actions[bot]` per tutti gli stati, tranne dove è scritto un altro utente. «Minuti» sono i minuti di Actions dei run di quel tentativo (somma di `run_duration_ms` dei `*-timing.out`; fatturati: 0). Nei casi con più righe (`error-sha-superato`, `detect-merge-rosso`) i minuti sono quelli del tentativo. Il tentativo è identificato dall'ora nel nome dei file `caso-<nome>-<ora>-*`.

| Caso | Repo | PR | SHA | Stati con autore | Atteso | Esito | Minuti | Note |
|---|---|---|---|---|---|---|---|---|
| verde-pulita | protected | #12 | `6c2beed822` | guard=success, verdict=success, attention=success, merge=CLEAN | guard=success, verdict=success, attention=success, merge=CLEAN | riuscito | 0.7 (3 run) |  |
| verde-edit | protected | #96 | `0ee64e20cd` | guard=success, verdict=success, attention=success, commenti «<!-- tollgate-verdict»=1, merge=CLEAN | guard=success, verdict=success, attention=success, un solo commento «<!-- tollgate-verdict», merge=CLEAN | composito (3 tentativi) | 1.1 (5 run) |  |
| verde-config | protected | #103 | `343a8275ea` | guard=success, verdict=success, attention=failure, merge=UNSTABLE | guard=success, verdict=success, attention=failure, merge=UNSTABLE | composito (4 tentativi) | 0.6 (3 run) |  |
| verde-ramo-libero | protected | #94 | `bea4372cb3` | guard=success, verdict=success, attention=failure, merge=UNSTABLE | guard=success, verdict=success, attention=failure, merge=UNSTABLE | composito (3 tentativi) | 0.5 (3 run) |  |
| rosso-test-tolti | protected | #20 | `726479fbed` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-skip | protected | #22 | `63d5a75ac0` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.8 (3 run) |  |
| rosso-fuori-scope | protected | #24 | `070a520be2` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.7 (3 run) |  |
| rosso-base-id | protected | #26 | `c63514981b` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-or-true | protected | #28 | `eb61caf2e2` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-livello | protected | #30 | `19163c6f39` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-l2-mancante | protected | #32 | `45c3917da6` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.5 (3 run) |  |
| rosso-deroga-altra-issue | protected | #34 | `5f1a180034` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-zero-test | protected | #36 | `631449d73d` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-piano-file-nuovo | protected | #38 | `95cb780b3b` | guard=success, verdict=failure, attention=failure, merge=BLOCKED | guard=success, verdict=failure, attention=failure, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| guard-wf-prt | protected | #40 | `4a9a936026` | guard=failure, verdict=failure, attention=success, merge=BLOCKED | guard=failure, verdict=failure, attention=*, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| guard-wf-run | protected | #42 | `a836ddf10c` | guard=failure, verdict=failure, attention=success, merge=BLOCKED | guard=failure, verdict=failure, attention=*, merge=BLOCKED | riuscito | 0.7 (3 run) |  |
| guard-wf-statuses | protected | #44 | `9e4786b76b` | guard=failure, verdict=failure, attention=success, merge=BLOCKED | guard=failure, verdict=failure, attention=*, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| guard-wf-writeall | protected | #46 | `9489a0b1dd` | guard=failure, verdict=failure, attention=success, merge=BLOCKED | guard=failure, verdict=failure, attention=*, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| guard-wf-ancora | protected | #48 | `004f6f941d` | guard=failure, verdict=failure, attention=success, merge=BLOCKED | guard=failure, verdict=failure, attention=*, merge=BLOCKED | riuscito | 0.7 (3 run) |  |
| guard-toml | protected | #50 | `c9311bbbec` | guard=failure, verdict=success, attention=success, merge=BLOCKED | guard=failure, verdict=success, attention=*, merge=BLOCKED | riuscito | 0.7 (3 run) |  |
| guard-verdict-yml | protected | #52 | `d906c73b23` | guard=failure, verdict=failure, attention=success, merge=BLOCKED | guard=failure, verdict=failure, attention=*, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| verde-workflow-ci | protected | #98 | `12869e5039` | guard=success, verdict=success, attention=failure, merge=UNSTABLE | guard=success, verdict=success, attention=failure, merge=UNSTABLE | composito (3 tentativi) | 0.7 (3 run) |  |
| attenzione-deroga-test | protected | #100 | `88c8da6eb5` | guard=success, verdict=success, attention=failure, merge=UNSTABLE | guard=success, verdict=success, attention=failure, merge=UNSTABLE | composito (3 tentativi) | 0.7 (3 run) |  |
| attenzione-piano-testo | protected | #87 | `f0cbb4d1d5` | guard=success, verdict=success, attention=failure, merge=UNSTABLE | guard=success, verdict=success, attention=failure, merge=UNSTABLE | composito (2 tentativi) | 0.6 (3 run) |  |
| attenzione-tetto-livello | protected | #89 | `03158fa820` | guard=success, verdict=success, attention=failure, merge=UNSTABLE | guard=success, verdict=success, attention=failure, merge=UNSTABLE | composito (2 tentativi) | 0.7 (3 run) |  |
| attenzione-zero-test | detect | #5 | `6d1574c907` | guard=success, verdict=success, attention=failure | guard=success, verdict=success, attention=failure | riuscito | 0.7 (3 run) |  |
| error-dotdot | protected | #62 | `960b2a3581` | guard=failure, verdict=error, attention=error, merge=BLOCKED | guard=failure, verdict=error, attention=error, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| error-entita | protected | #64 | `6e241b4a5d` | guard=failure, verdict=error, attention=error, merge=BLOCKED | guard=failure, verdict=error, attention=error, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| rosso-entita-tools | protected | #66 | `f03de8d7ff` | guard=success, verdict=failure, attention=success, merge=BLOCKED | guard=success, verdict=failure, attention=success, merge=BLOCKED | riuscito | 0.6 (3 run) |  |
| error-sha-superato | protected | #68 | `33873526d7` | guard=success, verdict=error, attention=error | guard=*, verdict=error, attention=error (verdict su A: error se la testa è già B; success se il run di A ha finito prima del push) | riuscito | 1.2 (6 run) | due righe: testa A superata da B, poi B |
| error-sha-superato | protected | #68 | `091676fba9` | guard=success, verdict=success, attention=success, merge=CLEAN | guard=success, verdict=success, attention=success, merge=CLEAN | riuscito | come sopra | due righe: testa A superata da B, poi B |
| error-due-pr | protected | #70 | `f8152dbf1b` | guard=error, verdict=error, attention=error, merge=BLOCKED | guard=error, verdict=error, attention=error, merge=BLOCKED | riuscito | 0.8 (4 run) |  |
| non-applicabile | protected | #73 | `09030223e7` | guard=none, verdict=none, attention=none | guard=none, verdict=none, attention=none | riuscito | 0.3 (2 run) |  |
| token-personale | protected | #75 | `0a24f0e7d5` | guard=success, verdict=success (ginz0ls), attention=success, merge=BLOCKED | guard=success, verdict=success, attention=success, merge=BLOCKED (verdict: l'ultimo stato è quello dell'utente (success), ma non vale per la protezione) | riuscito | 1.0 (3 run) |  |
| detect-pulita | detect | #7 | `f6274f2f32` | guard=success, verdict=success, attention=success | guard=success, verdict=success, attention=success | riuscito | 0.6 (3 run) |  |
| detect-closes | detect | #10 | `f2708119a3` | guard=success, verdict=failure, attention=success | guard=success, verdict=failure, attention=success | riuscito | 0.6 (3 run) |  |
| detect-merge-rosso | detect | #14 | `ecfa975058` | guard=success, verdict=failure, attention=success | guard=success, verdict=failure, attention=success | riuscito | 0.3 (1 run) | tre righe: verdict sul merge, sentinel, commenti |
| detect-merge-rosso | detect | #14 | `a9802100b3` | sentinel=failure, issue sentinel=1 | sentinel=failure, issue sentinel=1 | riuscito | come sopra | tre righe: verdict sul merge, sentinel, commenti |
| detect-merge-rosso | detect | n.d. (push diretto) | `3080fb2b23` | sentinel=failure, issue sentinel=1, commenti sull'issue=1 | sentinel=failure, issue sentinel=1, commenti sull'issue >= 1 | riuscito | come sopra | tre righe: verdict sul merge, sentinel, commenti |
| detect-push-diretto | detect | n.d. (push diretto) | `c0cf74c365` | sentinel=failure, issue sentinel=1 | sentinel=failure, issue sentinel=1 | riuscito | n.d. | nessun run con minuti registrati |

Gli «atteso» di `verde-config`, `verde-ramo-libero`, `verde-workflow-ci`, `attenzione-deroga-test`, `attenzione-piano-testo` e `attenzione-tetto-livello` riportano `UNSTABLE` e non `CLEAN` come nello scheletro iniziale del piano: è la correzione D-1 (vedi «Difetti e osservazioni»). Un caso con `attention=failure` ha il commento del bot con la voce da leggere ed è unibile (`UNSTABLE`), mentre `tollgate/guard` e `tollgate/verdict` restano i soli contesti obbligatori.

Nota: `detect-merge-rosso` unisce in `main` di detect un cambio con un test tolto ed è stato lanciato per ultimo tra i casi detect: i casi detect lanciati dopo partirebbero da una base degradata (gli identificativi della base non hanno `test_sottrai`). Un ripristino richiederebbe un commit nuovo, mai un reset.

### Tentativi non riusciti (causa)

Tutti i tentativi con esito «non riuscito» o senza esito, con la causa. Le righe di `casi-righe.md` sono lo storico completo; i file `*.prev-<tempo>` sono le rotazioni delle uscite ripetute.

| Caso | Tentativo (ora) | PR | SHA | Esito ottenuto | Causa |
|---|---|---|---|---|---|
| verde-edit | 20261022-123505 |  |  | NESSUN ESITO | nessun esito: `gh pr edit` fallito con gh 2.46.0 («GraphQL: Projects (classic) is being deprecated», `*-pr-edit.err`), il caso si è interrotto prima del controllo; D-2 (PATCH REST, f301c6e) |
| verde-edit | 20261022-175754 | #81 | `5d73fc010b` | non riuscito: tollgate/verdict: atteso success, ottenuto error; tollgate/attention: atteso success, ottenuto error; mergeStateStatus: atteso CLEAN, ottenuto BLOCKED | `tollgate/verdict` ed `attention` in `error` con «errore nel calcolo del gate: GhError: gh api --paginate: unexpected end of JSON input» (`*-p1-statuses.out`); il run `tollgate-guard` del secondo push è concluso `failure`; causa D-3 (500 a corpo vuoto su una lettura) |
| verde-config | 20261022-123258 | #14 | `017022a1eb` | non riuscito: mergeStateStatus: atteso CLEAN, ottenuto UNSTABLE | con `tollgate/attention` rosso GitHub dà `UNSTABLE`, non `CLEAN`: difetto D-1 del piano (atteso corretto, f301c6e) |
| verde-config | 20261022-172548 | #77 | `3ccec30b2a` | non riuscito: tollgate/guard: atteso success, ottenuto none; mergeStateStatus: atteso UNSTABLE, ottenuto BLOCKED | secondo il controller D-3: GitHub risponde 500 a corpo vuoto su una lettura (`commits/<sha>/pulls`); il run `tollgate-guard` conclude `failure` (`*-p1-runs.tsv`), il log del run per questo tentativo non è tra le evidenze |
| verde-config | 20261022-202647 | #92 | `1df8411fde` | non riuscito: tollgate/guard: atteso success, ottenuto none; mergeStateStatus: atteso UNSTABLE, ottenuto BLOCKED | `tollgate-guard` concluso `failure`; log del run in `vc-log.out`: «gate guard: gh api --method: unexpected end of JSON input»; D-4 (500 anche su una scrittura, ritentativi in c178f03) |
| verde-ramo-libero | 20261022-123355 | #16 | `757b4af457` | non riuscito: mergeStateStatus: atteso CLEAN, ottenuto UNSTABLE | con `tollgate/attention` rosso GitHub dà `UNSTABLE`, non `CLEAN`: difetto D-1 del piano (atteso corretto, f301c6e) |
| verde-ramo-libero | 20261022-174157 | #79 | `57caf744bb` | non riuscito: tollgate/guard: atteso success, ottenuto none; mergeStateStatus: atteso UNSTABLE, ottenuto BLOCKED | secondo il controller D-3: GitHub risponde 500 a corpo vuoto su una lettura (`commits/<sha>/pulls`); il run `tollgate-guard` conclude `failure` (`*-p1-runs.tsv`), il log del run per questo tentativo non è tra le evidenze |
| verde-workflow-ci | 20261022-125450 | #54 | `9dcf00cdf9` | non riuscito: mergeStateStatus: atteso CLEAN, ottenuto UNSTABLE | con `tollgate/attention` rosso GitHub dà `UNSTABLE`, non `CLEAN`: difetto D-1 del piano (atteso corretto, f301c6e) |
| verde-workflow-ci | 20261022-180437 | #83 | `740580dd44` | non riuscito: tollgate/guard: atteso success, ottenuto none; tollgate/verdict: atteso success, ottenuto error; tollgate/attention: atteso failure, ottenuto error; manca il commento del bot «<!-- tollgate-verdict»; mergeStateStatus: atteso UNSTABLE, ottenuto BLOCKED | `tollgate/verdict` ed `attention` in `error` («GhError: gh api --paginate: unexpected end of JSON input»), guard assente (run `failure`), nessun commento del bot; causa D-3 |
| attenzione-deroga-test | 20261022-125602 | #56 | `5c84538026` | non riuscito: mergeStateStatus: atteso CLEAN, ottenuto UNSTABLE | con `tollgate/attention` rosso GitHub dà `UNSTABLE`, non `CLEAN`: difetto D-1 del piano (atteso corretto, f301c6e) |
| attenzione-deroga-test | 20261022-183538 | #85 | `e83f157786` | non riuscito: tollgate/guard: atteso success, ottenuto none; mergeStateStatus: atteso UNSTABLE, ottenuto BLOCKED | secondo il controller D-3: GitHub risponde 500 a corpo vuoto su una lettura (`commits/<sha>/pulls`); il run `tollgate-guard` conclude `failure` (`*-p1-runs.tsv`), il log del run per questo tentativo non è tra le evidenze |
| attenzione-piano-testo | 20261022-125719 | #58 | `7ea78eb38a` | non riuscito: mergeStateStatus: atteso CLEAN, ottenuto UNSTABLE | con `tollgate/attention` rosso GitHub dà `UNSTABLE`, non `CLEAN`: difetto D-1 del piano (atteso corretto, f301c6e) |
| attenzione-tetto-livello | 20261022-125833 | #60 | `fbeee673b0` | non riuscito: mergeStateStatus: atteso CLEAN, ottenuto UNSTABLE | con `tollgate/attention` rosso GitHub dà `UNSTABLE`, non `CLEAN`: difetto D-1 del piano (atteso corretto, f301c6e) |

### Aggiornamenti di protected

Dopo le correzioni di D-3 e D-4 il codice di tollgate di protected è stato aggiornato due volte; per ciascuno: DELETE della protezione di `main`, push non forzato del nuovo codice (rami `tg/*` non toccati), `protect.sh`, issue di sentinel chiusa.

| Giro | Commit nel repo di prova | Issue di sentinel | Note |
|---|---|---|---|
| 4 (D-3) | `e75adcb` «aggiorna tollgate: letture di gh api ritentate sui 5xx (P4, giro 4)» | #90 chiusa | casi ripetuti: `verde-ramo-libero` #94, `verde-edit` #96, `verde-workflow-ci` #98, `attenzione-deroga-test` #100 |
| 5 (D-4) | `b86dc8d` «aggiorna tollgate: ritentativi delle scritture idempotenti (P4, giro 5)» | #101 chiusa | il primo `protect.sh` del giro è stato rifiutato perché `tollgate-base` non era ancora concluso sul commit; ripetuto dopo la conclusione. Caso ripetuto: `verde-config` #103 |

Evidenze: `aggiorna-*` (giro 4) e `aggiorna5-*` (giro 5); `aggiorna-protezione-prima.out` è la protezione letta prima della cancellazione. Il primo `aggiorna-issue-list` e `aggiorna-run-list` ha uscite ruotate in `*.prev-*`.

## Forme lette dal vero (voci di `carry.md`)

- `gh api --paginate --jq` su `statuses`: un oggetto JSON compatto per riga (`caso-*-statuses.out`: `context`, `created_at`, `creator`, `description`, `state`), ultimo stato per contesto in testa. `issues/<n>/comments`: una riga per commento con `body`, `id`, `user` (`caso-*-comments.out`). `-F body=@file` con `PATCH issues/comments/<id>`: nel caso `verde-edit` #96 dopo la modifica del corpo della PR resta un solo commento con il marcatore (commenti «<!-- tollgate-verdict»=1), quindi il commento è aggiornato e non duplicato.
- `GET pulls/<n>`: la risposta contiene i campi letti da `verdict` (`head.repo.full_name`, `head.sha`, `base.ref`, `body`, `state`), oltre a `merged`, `mergeable_state`, `title`, `user` e altri (`caso-*-pulls.out`). Il confronto riga per riga con `verdict.pr_from_rest` non è stato rieseguito su queste evidenze: non riportato come esito.
- `tollgate/base` su miss e su hit della cache: su detect `success` in entrambi i casi; su protected non c'è lo stato, vale il job (`installa-*-base-conclusione.txt`). Nel log del job protected in hit: «Cache mode: write», «Cache hit for: tollgate-ids-...», «Cache restored successfully» (`installa-protected-hit-base-log.out`).
- Cache mode dei job `workflow_run` (V4) riletta sul privato `detect`: non riuscita. Il log del job su detect non è stato scaricato in questa prova (c'è solo quello di protected); resta valido l'esito di V4 (`v4-*`).

## Minuti di Actions

Repo pubblico `protected`: 190 run, 3 693 s (circa 61,6 minuti), fatturati 0. Repo privato `detect`: 23 run, 352 s (circa 5,9 minuti), fatturati 0 (il campo `fatturati_ubuntu_ms` è 0 per tutti i run; la stima del piano era sotto i 200 minuti). (`raccogli-protected-minuti.txt`, `raccogli-detect-minuti.txt`)

## Difetti e osservazioni

- **D-1** (piano): con `tollgate/attention` rosso GitHub dà `mergeStateStatus` `UNSTABLE`, non `CLEAN`. Atteso corretto in f301c6e (con i test `tests/test_p4_make_case.py` e `tests/test_p4_ghguard.py`); casi ripetuti: `attenzione-piano-testo` (#87), `attenzione-tetto-livello` (#89) riusciti. Gli altri quattro casi con `attention=failure` sono stati ripetuti dopo D-2, D-3 e D-4.
- **D-2** (script): `gh pr edit` con gh 2.46.0 si rompe su una query GraphQL di Projects (classic); sostituito da una PATCH REST (f301c6e, con `tests/test_gh.py`). Primo `verde-edit` senza esito, ripetuto.
- **D-3** (codice di tollgate): GitHub risponde 500 a corpo vuoto su `commits/<sha>/pulls`; il guard e il verdict uscivano con «gh api --paginate: unexpected end of JSON input». Letture ritentate sui 5xx transitori: e7dd195 (test in `tests/test_ghcli.py` e `tests/test_gate_guard.py`) + aa1a0b3 (ritentativi solo per le letture vere); protected aggiornato con e75adcb. Casi ripetuti riusciti: `verde-ramo-libero` (#94), `verde-edit` (#96), `verde-workflow-ci` (#98), `attenzione-deroga-test` (#100).
- **D-4** (codice di tollgate): 500 anche su una scrittura (`gate guard: gh api --method: unexpected end of JSON input`, `vc-log.out`): POST degli stati e PATCH dei commenti ritentati, c178f03 (test in `tests/test_ghcli.py` e `tests/test_gate_guard.py`); protected aggiornato con b86dc8d. Caso ripetuto: `verde-config` riuscito al quarto tentativo (#103).
- I casi ripetuti sono solo quelli interessati dal difetto (nessun caso già riuscito è stato rifatto).
- Controllo dei comandi del controller (`raccogli-comandi-controllo.txt`): 1 397 comandi `gh` controllati (escluse 9 righe annotate «(controller...)»). Una **VIOLAZIONE**: `repo clone ginz0ls/tollgate-p4-protected /tmp/tollgate-p4/flow/protected -- -q`, «la cartella deve stare sotto P4_WORK». È un difetto del verificatore, non del modello né del flusso: il clone del flusso in `/tmp/tollgate-p4/flow` è imposto dal brief, mentre il controllo vuole `P4_WORK`. Corretto in 8fa32ba (`FlowCloneTest`: `ghguard.py` ammette esattamente `/tmp/tollgate-p4/flow/protected` per il solo repo protected); l'evidenza `raccogli-comandi-controllo.txt` è antecedente alla correzione e si riporta com'è. Due scarti da annotare: un `gh --version` superfluo del controller (etichetta `aggiorna-push`, `comandi.log` righe 1108-1109, 18:24:40Z; è la riga annotata «(controller...)») e un `gh pr edit` (il primo `verde-edit`, fallito, causa di D-2). Conteggio per comando: `gh api` 795, `gh run watch` 169, `gh pr view` 95, `gh pr create` 59, `gh issue close` 58, `gh issue create` 54, `gh pr close` 53, `gh run list` 23, `gh issue list` 19, `gh run view` 18, `gh pr list` 13, `gh run download` 12, `gh issue view` 9, `gh --version` 5 (`comandi.log` ne ha 6 righe: tre sonde iniziali del 21 ottobre alle righe 2, 104 e 127, la coppia annotata/registrata dell'`aggiorna-push` alle righe 1108-1109, che il controllo conta una volta, e una alle 19:24:57Z, riga 1329, legittima: è `gh_call raccogli-versione-gh --version` del modo `raccogli`, `spikes/run-p4-gate.sh:434`), `gh auth status` 4, `gh pr merge` 4, `gh repo clone` 3, `gh repo create` 2, `gh pr comment` 1, `gh pr edit` 1.
- `gh pr merge`: 4 chiamate registrate, tutte delle prove del gate: tre sonde del 21 ottobre su protected (PR #5 merge, #6 squash, #7 rebase) e `detect-merge-rosso` su detect (PR #14, squash). Il flusso con `claude -p` non ha unito la sua PR.

## Ciò che resta non esercitato

- Su detect, nessun caso del criterio 10 con la protezione di `main` (non esiste, modalità `detect`): i casi detect misurano solo gli stati e la sentinel.
- Il confronto di `verdict.pr_from_rest` con le risposte reali di `GET pulls/<n>` (campi presenti, non confronto automatico).
- La cache mode dei job `workflow_run` su un repo privato (log del job detect non scaricato).
- Il caso detect dopo `detect-merge-rosso` (base degradata): non esercitato per scelta.
- Tutto ciò che riguarda un repo con più contributori, fork o `pull_request_target` da fork: il modello è cooperativo, un solo utente.
