# Report Task 11

Implementati: gate/workflows/tollgate-{guard,run,verdict,base,sentinel}.yml, bin/tollgate_gate/install.py, tests/test_gate_workflows.py (19 test).

## TDD
RED: con install.py e gate/ spostati fuori dal repo, `python3 -B -m unittest tests.test_gate_workflows` -> ImportError: cannot import name 'install' from 'tollgate_gate' (Ran 1 test, FAILED errors=1).
Primo GREEN: 18/19; fallito test_fetch_depth_where_history_is_needed (il secondo checkout di base, del solo commit, e' superficiale di proposito): corretto il test, che guarda il checkout del predefinito. Poi 19/19.
GREEN: `tests/run`: python3.11 2195 test OK, python3 (3.13.5) 2195 test OK.

## Scelte e scostamenti
- Layout job `base` di run e job di tollgate-base: checkout del predefinito in `trusted` (CLI fidata, fetch-depth 0), `base` = commit da misurare (merge-base / GITHUB_SHA), `gate base-ids` con working-directory trusted e `--root "$GITHUB_WORKSPACE/base"`.
- Chiave di cache del job `base` di run: serve la testa per il merge-base, quindi un terzo checkout `head` (testa della PR, fetch-depth 0, persist-credentials false, solo dati, nessun codice eseguito; comandi solo `git -C head merge-base/rev-parse`). Cosi' nessun fetch autenticato.
- tollgate-verdict: nessun cache/save, nessun --head-ids-out. La chiave per il restore richiede l'albero di merge-base: passo `key` con `git fetch origin $HEAD_SHA` autenticato via GIT_CONFIG_COUNT/KEY/VALUE in env (V3b), `continue-on-error`; se fallisce (es. testa da fork) il restore e' saltato e `evaluate` usa l'artefatto.
- tollgate-base: restore, poi `base-ids --publish` SEMPRE, poi cache/save solo su miss (V4b).
- Nomi dei job: `tollgate-guard`, `head`/`base` (run), `tollgate-verdict`, `tollgate-base`, `tollgate-sentinel` (per V6, check-run `tollgate-base`).
- `install.files`: valida il ramo (`^[A-Za-z0-9_][A-Za-z0-9._/-]*$`) e servizi (nome/immagine) prima di scriverli in YAML senza virgolette; segnaposto `    # __SERVICES__` nel job `head`, sostituito col blocco `services:` (solo `image:`) o rimosso. VERSION e FINGERPRINT con newline finale.
- test_names_match_gate_files controlla anche `name:` == nome del file e `workflow_run.workflows`.

## Dubbi
1. `workflows.problems` NON puo' dare `[]` per guard, verdict, base, sentinel: rifiuta per costruzione `pull_request_target`, `workflow_run` e `statuses: write`, che 9.1 impone. Il test `test_workflows_have_no_unexpected_problems` scarta solo quei tre problemi attesi e pretende zero altri (parser, àncore, tab, permissions mancante); `tollgate-run` e' pulito del tutto (`problems == []`, anche con i servizi).
2. Cache hit in tollgate-base: `gate base-ids --publish` ricalcola sempre la suite (la CLI non pubblica da ids in cache). Quindi la cache serve solo a decidere il salvataggio; il calcolo non e' saltato su hit. Per saltarlo servirebbe una opzione nuova nella CLI (es. pubblicare da ids.json).
3. I `services` senza `ports:` non sono raggiungibili da localhost nel job che gira sull'host del runner; il blocco ha solo `image:` come da brief. Task 12 / spec 9.6 dovra' decidere porte ed env.
4. Il passo `key` di verdict fa `git fetch origin <sha>`: per teste di fork fallisce (previsto, fallback artefatto).

## Fix round 1

C-1: `tollgate-base.yml` diviso in `ids` (permissions contents: read, nessun GH_TOKEN, checkout di `github.sha`, cache restore, `gate base-ids` solo su miss, cache save solo su miss, upload sempre di `tollgate-ids/ids.json`) e `tollgate-base` (needs ids, if always(), statuses/issues write, solo checkout del predefinito, download sotto runner.temp con continue-on-error, `gate base-publish --ids ... --event ... --publish`). Il job di pubblicazione ha la chiave `tollgate-base` (= `protection.BASE_JOB`).
- Nuovo `gate base-publish` (cli.py, `baseids.publish_from`, `baseids.read_result`): lettura fail-closed (simlink, dimensione, JSON, versione, albero, nomi dei comandi tra quelli di `runner.ids_commands`, stati in `run.STATES`); invalido o assente -> stato `error` in detect e codice 1 in ogni modalita'. Il controllo e' sull'ALBERO di `after`, non sullo `sha` del file: su un cache hit lo `sha` e' quello del commit che ha riempito la cache. Scostamento dal ruling («sha coincida»), voluto.
- `--publish` tolto da `base-ids` (ora argomento sconosciuto, exit 2); `MAX_IDS_FILE` spostato in baseids e riusato da verdict.
- Test: job `ids` senza write ne' token; nessun job con `gate run`/`gate base-ids` ha permessi write o GH_TOKEN (3 job); `base-publish`: valido (anche da cache hit), verde, senza --publish, artefatto mancante/albero diverso/JSON ostile/simlink/oversize -> error, protected -> nessuna scrittura e exit 1, handler CLI, `--publish` fuori da Actions rifiutato, abbreviazioni -> exit 2, guardrail cli_calls su base-publish. Sentinel e tollgate-base non usano piu' `--publish` su base-ids.
- Il checkout di `ids` e' su `github.sha` e la CLI gira da li' (senza token): la CLI fidata della pubblicazione e' un checkout separato del predefinito.

I-1: `install.files` mette lo stesso blocco `services:` (con `ports` del Task 12) in `head` e `base` di tollgate-run e in `ids` di tollgate-base; un solo codice (`_render`, conteggio dei segnaposto per workflow). Test: blocchi identici nei tre job, solo in quelli.

Minori: M-1 fullmatch (test "main\n", "db\n"); M-2 valori tra virgolette singole (test rami true/123/null/on, servizio `true`, immagine `postgres:` rifiutata); M-3 test espressioni solo in with/env/concurrency/if; M-5 test verdict senza if sulla conclusione; M-6 test righe run passate al parser della CLI (7 invocazioni); M-7 `secrets.GITHUB_TOKEN` vietato; M-8 commento in tollgate-base.yml.
Toccati anche tests/test_init.py (due asserzioni del Task 12 sul formato dei file generati: virgolette singole e servizi anche in tollgate-base).

RED: prima del codice 9 fallimenti e 1 errore in tests.test_gate_workflows (27 test). GREEN: `tests/run` python3.11 2279 OK, python3 (3.13.5) 2279 OK.
