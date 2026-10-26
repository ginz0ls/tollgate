# Task 13 - report dell'implementatore: `spikes/run-p5-gate.sh` e i suoi test

Stato: lo script e i test sono scritti e provati SOLO con `bash -n` e col modo `controlla` (gh finto, nudo locale, git vero).
Nessun altro modo è stato eseguito, nessun `gh` vero, nessuna rete, nessun `claude`.

## Cosa ho fatto

- `spikes/run-p5-gate.sh` (nuovo, eseguibile): modi `elenco`, `aggiorna`, `pin-on`, `pin-off`, `caso <nome>`, `raccogli`, `controlla`.
  Struttura e helper presi da `spikes/run-p4-gate.sh` e `spikes/p5/run-p5-checks.sh` (git_net, gh_read, fresh_branch, trap per le PR
  aperte); `spikes/gh-p4/common.sh` per `gh_call`, `wait_run`, `await_statuses`, `statuses`. Profilo `p5` di `ghguard.py`
  (`P4_PROFILE=p5`, `P5_PR_REGISTRY=$OUT/prs-aperte.txt`): NON ho dovuto estendere `ghguard.py` (ogni forma che serve c'è già).
- Le uscite vanno in `docs/verifiche/evidenze/p5/`, tutte con prefisso `gate-` (nessun nome in comune con quelle di Task 1; `rot` rinomina
  sempre, non si cancella mai niente). File di sintesi: `gate-casi-righe.md` (una riga del rapporto per tentativo, stesse colonne di P4,
  minuti = somma delle durate dei run seguiti, perché l'API dei minuti fatturati è 0 sui privati Free), `gate-tentativi.tsv` (ora, modo,
  codice d'uscita di OGNI tentativo, anche i rifiutati: da lì il controller decide «composito»), `gate-runs.tsv` (run seguiti, per `raccogli`).
  `comandi.log` riceve all'inizio di ogni modo una riga `(modo <nome>)` che `ghguard.py comandi` ignora.
- `tests/test_p5_scripts.py`: aggiunte `GateScriptShapeTest` (8 test sul testo dello script) e `GateControllaTest` (un solo `controlla`, ~20 s,
  10 test sui suoi esiti e sul registro dei comandi per modo).
- Il `gh` finto è nello script stesso (heredoc di `write_fake_gh`), non in un file a parte: il brief elencava solo due file. Il finto ricava
  stati, merge (commit-tree sul nudo) e stato di sentinella dallo stato dei repo nudi (stessa regola di `sentinel.run`, con `[skip ci]`).

## Modi e codici d'uscita

| Modo | Cosa fa | Codici |
|---|---|---|
| `aggiorna` | clone fresco di detect; `bin/tollgate init --update` (wrapper gh con guardia p5, stato di prova); ramo `tollgate-config/<VERSION>` (suffisso `-<ora>` se esiste); copia e `git add -- <file>` dei SOLI file di `files/` (e `git rm` dei soli file tracciati sotto `.github/tollgate/` elencati in «Da cancellare», altrimenti si ferma); commit; push; PR (corpo in OUT, registrata); attesa di guard e verdict (tetto `P5_WAIT_MAX`); se non sono entrambi `success` NON unisce e chiude la PR; `pr merge --squash`; SHA del merge da `pr view --json state,mergeCommit`; attesa di sentinel e base sul merge | 0 ok; 1 errore; **4** init non propone nulla (nessuna PR) |
| `pin-on` | legge `actions/permissions`, salva `PIN_INIT` e `PIN_ACTIONS` in `${P5_GATE_STATE:-~/.cache/tollgate-p5-gate/pin-iniziale.env}` (fuori dal repo), PUT con `sha_pinning_required=true`, verifica | 0; **2** se lo stato esiste già (non sovrascrive mai il valore iniziale); 1 |
| `pin-off` | rimette il valore salvato (3 tentativi), lo rilegge; se coincide archivia lo stato in `<stato>.rimesso-<epoch>` (mai cancellato) | 0; **2** senza stato («mi rifiuto», nessuna PUT); **3** rimessa non verificata |
| `caso pulita-fissata` | richiede pin acceso; PR `tg/<N>-p5-gate-pulita-fissata-<ora>` costruita con `make_case.py build detect-pulita` (ramo rinominato, caso riscritto con jq); attende guard/verdict/attention; giudica con `make_case.py judge` (stati con autore e commento del bot); log del run di verdict: riga «Cache mode: read» (seconda riga del rapporto `pulita-fissata-cache`) | 0; 1 caso non riuscito; 6 issue di sentinella aperta |
| `caso rifiuto-v4` | richiede pin acceso; ramo `p5-gate-rifiuto-v4-<ora>` con un workflow a `actions/checkout@v4`; atteso: run `failure` e messaggio «must be pinned to a full-length commit SHA» in `--log-failed` | 0 / 1 |
| `caso rivalutazione` | PR verde come sopra; conta gli stati `tollgate/verdict` (k); PATCH REST del corpo (`-F body=@file`); attende `k+2` stati e l'ultimo non pending; registra l'ordine reale con autore e ora in `…-ordine.txt`; riuscito se il primo nuovo è `pending`, l'ultimo `success`, tutti del bot (decisione 15). Se resta `pending` lo dice (verdict prima di guard) e NON rilancia niente | 0 / 1 |
| `caso skip-ci` | (1) PR di ramo libero con un file in `notes/`, verde, unita `--squash`: è il push controllato; richiede sentinel `success` sul merge. (2) clone fresco (fetch/pull non sono ammessi), commit con `[skip ci]` e `push main`; attesa `P5_SETTLE` (120 s); commit normale e `push main`; attesa della sentinella su di esso. Giudizio: S `failure`, N `failure`, partenza ancora `success`, nessun run di sentinella su S, almeno uno su N, UNA issue di sentinella aperta che nomina S e non nomina la partenza. NON chiude l'issue (la chiude il controller) | 0 / 1 |
| `raccogli` | `gh --version`, run/PR/issue aperte, permessi; minuti dai run seguiti; `run view --log` (fallback `--log-failed`) di ogni run in `gate-runs.tsv`; `gate-raccogli-osservazioni.txt` con le righe su digest/mismatch/Cache mode/checkout; stato finale (PR aperte, `sha_pinning_required`, issue, stato pin); `ghguard.py comandi` sul registro; scansione di forme di token nei file `gate-*` (esce 1 se ne trova) | 0 / 1 |
| `controlla` | vedi sotto | 0 / 1 |

`pin-on`/`pin-off` e i casi non partono mai da soli: nessuna chiamata a `pin-off` dentro i casi. Nessun trap rimette il pin (sono modi separati
voluti dal controller).

## Elenco esatto dei comandi di rete per modo (da `comandi.log` di una corsa di `controlla`, SHA/numeri/percorsi normalizzati)

`git-net` = `ghguard.py gitcheck` poi git con `GIT_TERMINAL_PROMPT=0`. `<D>` = `https://github.com/ginz0ls/tollgate-p4-detect.git`, `<R>` = `--repo ginz0ls/tollgate-p4-detect`.

**aggiorna**
- git: `clone -q <D> <WORK>/gate-detect`; `push <D> tollgate-config/0.2.0` (o `…-<ora>`)
- gh: `api repos/…/branches/tollgate-config/0.2.0` (esistenza); `pr create <R> --base main --head tollgate-config/0.2.0 --title … --body-file …`; `api --paginate …/commits/<sha>/statuses?per_page=100 --jq …`; `run list <R> --workflow tollgate-run.yml|tollgate-sentinel.yml|tollgate-base.yml --limit 30 --json …`; `run watch <id> <R> --exit-status`; `run view <id> <R> --json …`; `api …/actions/runs/<id>/timing`; `pr merge <n> <R> --squash`; `pr view <n> <R> --json state,mergeCommit`; (in caso di errore) `pr view … --json state` + `pr close`
- tramite `bin/tollgate init --update` (wrapper con guardia p5): `api --include repos/…/branches/main/protection` (lettura) e **un `git fetch origin` interno a tollgate** (lettura, non passa da `gitcheck`: lo fa `gitw.fetch`; stessa cosa che faceva `init --propose` in P4)

**pin-on**: `api repos/…/actions/permissions` (GET, con ritentativo sui 5xx); `api --method PUT repos/…/actions/permissions -F enabled=true -F sha_pinning_required=true [-F allowed_actions=<iniziale>]`; GET di verifica. Nessun git.

**pin-off**: stesse due forme, PUT con `sha_pinning_required=<iniziale salvato>` (fino a 3 tentativi), GET di verifica. Nessun git.

**caso pulita-fissata**: GET `actions/permissions`; git `clone`, `push <D> tg/<N>-p5-gate-pulita-fissata-<ora>`; `issue list <R> --state open --limit 100 --json number,title`; `issue view <N> <R> --json number,title,state`; `pr create …`; `run list/watch/view` + `api …/timing` per tollgate-guard.yml, tollgate-run.yml, tollgate-verdict.yml; `run view <id> <R> --log`; `api --paginate …/statuses…`; `api --paginate …/issues/<pr>/comments?per_page=100 --jq …`; `pr view <n> --json state` + `pr close <n>` alla fine.

**caso rifiuto-v4**: GET `actions/permissions`; git `clone`, `push <D> p5-gate-rifiuto-v4-<ora>`; `run list/watch/view` + `api …/timing` per `p5-gate-rifiuto-v4.yml`; `run view <id> <R> --log-failed`. Nessuna PR.

**caso rivalutazione**: come pulita-fissata (senza GET dei permessi) più `api --method PATCH repos/…/pulls/<n> -F body=@<OUT>/<file>` (n registrata dalla guardia), altri `api --paginate …/statuses…`; `pr close` alla fine.

**caso skip-ci**: git `clone`, `push <D> p5-gate-skip-ci-base-<ora>`, secondo `clone`, **`push <D> main` due volte** (commit `[skip ci]`, poi commit normale); `issue list <R> --state open …` (prima e dopo); `issue view <N> <R> --json number,title,state,body,comments` (la sentinella); `pr create`, `pr merge <n> <R> --squash`, `pr view … --json state,mergeCommit`; `run list <R> --workflow tollgate-sentinel.yml --limit 30 --json …` (anche per contare i run per SHA), `run watch`, `run view --json`, `api …/timing`; `api --paginate …/statuses…` su base, merge, S e N. Nessun `issue close`.

**raccogli**: `--version`; `run list <R> --limit 200 --json …`; `pr list <R> --state all|open --limit 200 --json …`; `issue list <R> --state open --limit 100 --json number,title`; GET `actions/permissions`; `api …/actions/runs/<id>/timing` e `run view <id> <R> --log` (fallback `--log-failed`) per ogni riga di `gate-runs.tsv`.

Non emessi da nessun modo (verificato dal registro e dai test): `pr edit`, `issue create|close|comment`, `pr comment`, `repo *`, `auth *`, `push --force|-f|--delete|--mirror|--all|+ref|ref:ref`, `fetch`/`pull` di rete, `ls-remote`, qualunque cosa su `tollgate-p4-protected` o su `ginz0ls/tollgate`. Il solo `push main` è in `caso_skip_ci` (`ALLOW_MAIN_PUSH=1`, una sola volta nel testo). Nessun ramo si cancella.

## `controlla`

Nessuna rete: `gh` finto in testa al PATH (`command -v gh` verificato), nudo locale di detect con il progetto di prova di P4 (`make_case.py baseline detect`), git vero con `GIT_CONFIG_*` che reindirizza `https://github.com/ginz0ls/` al nudo (solo se `P5_CHECK=1`; `no_rewrite_rules` resta attivo). Sequenza: rifiuti (`pin-off` senza stato, caso sconosciuto, caso senza pin) -> `aggiorna` -> `pin-on` (+ secondo `pin-on` rifiutato senza perdere il valore iniziale) -> i quattro casi -> caso con issue di sentinella aperta (rifiutato, codice 6) -> `pin-off` -> `raccogli`. Poi: nessuna PR aperta, un solo commit `[skip ci]` e due soli push diretti su main, `ghguard.py log` sul registro del finto, `ghguard.py comandi` su `comandi.log` (0 RIFIUTATO), nessun push forzato/`--delete`/`pr edit`/`issue close|create`, prova negativa gh (22 comandi vietati fermati, 23 legittimi ammessi: tra i vietati `pr edit`, `issue create`, `pr merge` senza flag, PATCH di una PR non registrata, PUT con `sha_pinning_required=maybe`, DELETE, `api user`, `tollgate-p4-protected`), prova negativa git (14 fermati: force, `+main`, `main:main`, `--delete`, `--mirror`, `--all`, `pull`, `fetch`, `ls-remote`, altri repo), uscite attese presenti, origin del clone ancora l'URL vero.

## Scostamenti dal piano e scelte da conoscere

1. **Issue per `pulita-fissata` e `rivalutazione`.** `gh issue create` non è nella decisione 21 e il profilo `p5` non lo ammette, ma un lavoro `tg/<N>-*` valido ha bisogno di «Closes #N» su un'issue aperta (altrimenti `attention` è rossa: `not_tg_branch`, `no_issue`). Lo script non apre issue: prende `P5_ISSUE` oppure l'unica issue aperta con titolo che comincia per «prova P5». **Il controller deve aprire a mano un'issue «prova P5: ...» su detect** (con annotazione «(controller...)») prima dei due casi, e passarla in `P5_ISSUE`. L'issue resta aperta tra un caso e l'altro perché le due PR si chiudono senza essere unite. Senza issue lo script si ferma con un messaggio che lo dice.
2. **Rami `tg/<N>-p5-gate-<caso>-<ora>`** per i due casi verdi (non `p5-gate-<caso>-<ora>` puro): il gate riconosce il lavoro dal prefisso `tg/<N>-` (decisione 8); senza, `attention` sarebbe rossa. Gli altri rami seguono `p5-gate-<caso>-<ora>`; `aggiorna` usa `tollgate-config/<VERSION>` (prefisso richiesto da `is_config_branch`), con suffisso `-<ora>` al secondo tentativo.
3. **Il push controllato di `skip-ci`** è il merge di una PR di ramo libero (file `notes/p5-skip-ci-base-<ora>.md`), non un push diretto (che darebbe `failure`) né un riuso del merge di `aggiorna`. Si presume che guard e verdict siano verdi per quella PR (come `verde-ramo-libero` e `attenzione-zero-test` di P4); se non lo sono, la riga dice «non riuscito» e non unisce.
4. **`fetch`/`pull` non esistono** nel profilo git: per vedere main dopo un merge lo script riclona detect (`rot` del vecchio clone). Per questo `skip-ci` clona due volte.
5. Il caso di P4 `detect-pulita` lascia «Closes #N» e un piano nel ramo; `make_case.py build` fa `git commit` dei file di `feature_files()` sopra main: se main di detect avesse già esattamente quei file il commit fallirebbe ("nothing to commit") e il caso si ferma con l'errore di `make_case`. Dopo `detect-merge-rosso` di P4 (che ha unito `feature_files(sottrai=False)`) i file differiscono per `test_sottrai`, quindi il commit c'è; è un'assunzione da verificare nel primo giro reale.
6. **Aggancio dei run**: `guard` e `verdict` si cercano col ripiego «il più recente negli ultimi 2 minuti» (come Task 1, `pull_request_target`/`workflow_run` non hanno la testa della PR come `head_sha` garantito), subito dopo l'apertura della PR; `tollgate-run` per SHA. Se un run non compare, l'attesa va al tetto (`P5_WAIT_MAX`, 900 s) e si procede: i minuti di quel run non entrano nella riga. In `rivalutazione` si segue solo il run di `tollgate-run` della prima valutazione (i minuti della seconda sono fuori dalla riga; `raccogli` dà il totale dei run seguiti).
7. `raccogli` salva `run view --log` di tutti i run seguiti (anche lunghi): se un file contiene forme di token lo segnala (esce 1) senza stamparne il testo.
8. **Vincolo del controller**: `init --update` esegue un `git fetch origin` proprio, fuori da `gitcheck` (sola lettura verso detect).
9. Un pin lasciato acceso da un tentativo fallito resta acceso: `pin-off` è l'unico modo di rimetterlo (e l'unico che legge lo stato). Prima del primo `pin-on` verificare che non esista `~/.cache/tollgate-p5-gate/pin-iniziale.env`.

## Evidenza TDD

RED: i test `GateScriptShapeTest`/`GateControllaTest` sono stati scritti dopo la prima versione dello script e fatti girare finché l'unico stato
accettato fosse verde; la prima corsa di `controlla` ha trovato un bug reale (`local d=… prop="$d/…"` nella stessa istruzione: «d: variabile non assegnata»,
`modo aggiorna: FALLITO`, 5 uscite attese mancanti, `CONTROLLA: FALLITO`), corretto. Le prime corse dei test hanno dato 3 fallimenti, tutti di
asserzione dei test (codice del controllo contato come codice dello script; ordine dei modi nel dizionario; frammento di testo), corretti nei test.

GREEN: `python3 -B -m unittest tests.test_p5_scripts.GateScriptShapeTest tests.test_p5_scripts.GateControllaTest` -> `Ran 19 tests in 22.4s OK`.
`bash -n spikes/run-p5-gate.sh` -> ok. `bash spikes/run-p5-gate.sh controlla` -> `CONTROLLA: ok` (rc 0, stderr vuoto).

## Suite completa e commit

`tests/run` (una volta, in background, uscita su file): `== Python 3.11.16` -> `Ran 2881 tests in 1278.7s OK (skipped=2)`; `== Python 3.13.5` (python3) ->
`Ran 2881 tests in 1253.1s OK`; rc 0. L'unico testo estraneo sull'uscita è la riga «guard: la PR è avanzata dopo l'evento…» stampata da
`tests/test_finalreview.py` (preesistente, non dei test di questo task). Nessun `__pycache__` nel repo (i due creati da un mio comando
senza `-B` sono stati tolti prima del commit); `git status` prima di `git add`: solo `spikes/run-p5-gate.sh` e `tests/test_p5_scripts.py`.

Commit: `7c9addc tollgate P5: script della prova reale su detect (azioni fissate, rivalutazione, skip ci)` (2 file, +1415).

## Dubbi per il controller

- Serve un'issue aperta «prova P5: ...» su detect (P5_ISSUE) prima di `pulita-fissata` e `rivalutazione` (scostamento 1).
- Le assunzioni 3 e 5 (PR di ramo libero verde per il push controllato; commit non vuoto di `detect-pulita` su main di detect) si verificano solo nel primo giro reale.
- Non so se `gh run view --log` su un run rifiutato in «Set up job» dia il messaggio su stdout: l'evidenza di Task 1 (`pin-v4-log-failed.out`) dice di sì per `--log-failed`; lo script legge stdout e stderr.

## Fix round 1

- `spikes/gh-p4/ghguard.py` (profilo p5): `gh issue create` ammesso solo su `ginz0ls/tollgate-p4-detect`, titolo che comincia per «prova P5: » (non vuoto), esattamente uno tra `--body` e `--body-file`, nessuna altra opzione (`--assignee`, `--label`, `--project`, `--web` rifiutati da `_parse`); al più 2 per prova (righe `issue` in `P5_PR_REGISTRY`, contate da `check`). Lo script NON crea issue (resta `P5_ISSUE`).
- `run-p5-gate.sh`: `gh_call` di common.sh è ora `gh_call_once`; il nuovo `gh_call` ritenta sui 5xx le sole letture (`pr|issue view|list`, `run list|view`, `api` senza scrittura), quindi anche `statuses`, `wait_run` e `close_open_prs`. Scritture (create, merge, PATCH, close) mai ritentate; `run watch` non è una lettura (esce 1 su un run rosso). La PUT dei permessi resta ritentata (idempotente).
- `rivalutazione`: tolto il secondo `track` dello stesso run (minuti non doppi).
- `controlla`: esegue davvero `net_push` verso `main` e verso rami `a:b`, `+main`, `-f`, vuoto fuori da skip-ci: devono morire.
- Test: `IssueCreateGuardTest` (caso ammesso, altro repo, altro titolo, titolo vuoto, senza/doppio body, opzioni in più, limite di 2 e registro obbligatorio) e `test_net_push_is_really_refused_outside_skip_ci`.
- Esito: test mirati 30 OK; `tests/run` python3.11 2885 OK (skipped=2), python3 2885 OK, rc 0.
- Nota: `docs/verifiche/evidenze/p5/comandi.log` risulta modificato da una riga del controller (`issue list … 2026-10-24`): non l'ho toccato né committato.

## Fix round 2

- `run-p5-gate.sh`: `wait_run` ridefinito. Con ripiego=1 (guard `pull_request_target`, verdict `workflow_run`) cerca prima per `headBranch` uguale al ramo della PR e per `event` (7° argomento di `track`); un run di un altro ramo non si prende mai. Senza run del ramo entro il tetto restituisce 1 con un messaggio, e `pulita-fissata` aggiunge la riga `pulita-fissata-aggancio` «non riuscito: run di guard non trovato (minuti incompleti)». Con ripiego=0 resta per SHA o per ramo.
- Commenti corretti (righe 17 e 273): `issue create` è ammesso dalla guardia solo al controller, lo script non lo usa.
- `controlla`: il `gh` finto restituisce anche un run più recente (id più alto) di un altro ramo, `tollgate-config/0.2.0`, con lo stesso evento. Il controllo verifica che guard e verdict agganciati abbiano id < 900000. Test `test_runs_are_matched_by_branch_not_by_recency`.
- Esito: test mirati 21 OK; `tests/run` python3.11 2886 OK (skipped=2), python3 2886 OK, rc 0. Non toccati né committati i file in `docs/verifiche/evidenze/p5/`.

## Fix round 3

- Verdict (`workflow_run`, headBranch e headSha del predefinito): `wait_run` con ripiego=2 prende il PRIMO run di `tollgate-verdict.yml` con evento `workflow_run` e `createdAt` >= fine (`updatedAt`) del `tollgate-run` della PR (8° argomento di `wait_run`, 7° di `track`), ordinando per `createdAt`, mai il più recente; nessun filtro per ramo né per SHA. Se il run di `tollgate-run` non si trova (o la sua fine non si legge) il verdict è «non determinato» e non si cerca. Guard: invariato (headBranch della PR + `pull_request_target`).
- Il `gh` finto: i verdict `workflow_run` hanno headBranch `main` e headSha = testa di main; la lista contiene uno creato prima della fine del run (id 800000+), il giusto (00:06) e uno più recente di un'altra PR (id 900000+). `controlla` verifica che guard e verdict agganciati abbiano id < 800000.
- `rivalutazione`: lo script non aggancia nessun run di verdict né di guard: segue solo il `tollgate-run` della prima valutazione (per SHA della testa, evento `pull_request`) e il secondo verdict lo segue solo dagli stati `tollgate/verdict` dello SHA della PR (conteggio k+2, ultimo non pending), quindi non può prendere run di altre PR; i minuti del secondo verdict e del guard su `edited` non entrano nella riga (`raccogli` dà il totale dei run seguiti).
- Esito: test mirati 21 OK; `tests/run` python3.11 2886 OK (skipped=2), python3 2886 OK, rc 0. File di `docs/verifiche/evidenze/p5/` non toccati.
