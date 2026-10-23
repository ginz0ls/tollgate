# Report Task 16 (script della prova reale, senza esecuzione)

Implementatore: Claude Sonnet 5.5. Nessuno script è stato eseguito contro GitHub; di `run-p4-gate.sh` e `run-p4-flow.sh` ho lanciato solo `bash -n` e il modo `controlla`
(rete assente, `gh` finto davanti nel PATH, nessun `claude`). Del Task 1 ho rilanciato `controlla` (regressione della libreria comune).

## File

| File | Cosa |
|---|---|
| `spikes/run-p4-gate.sh` | Step 1: modi `elenco`, `installa <repo>`, `protezione`, `caso <nome>`, `raccogli`, `controlla` |
| `spikes/run-p4-flow.sh` | Step 5: modi `issue`, `prepara`, `shim`, `passo1`, `passo2`, `passo3`, `attendi`, `passo4`, `registra`, `controlla` |
| `spikes/p4/make_case.py` | 37 casi (rami, file, piano, blocco da `prblock.render`, deroghe); `judge` che confronta l'ottenuto con l'atteso |
| `spikes/gh-p4/common.sh` | libreria comune estratta da `run-p4-checks.sh` (guardie, `gh_call`, `git_call`, clone, `wait_run`) più stati, commenti e run di una PR |
| `spikes/gh-p4/ghguard.py` | lista unica degli ammessi: tre scritture `gh api` esatte, `--body-file`, `pr list --head`, profilo `flow` |
| `spikes/gh-p4/ghwrap.py`, `bin/gh` | gh con guardia: espande `{owner}/{repo}`, aggiunge `--repo`, controlla con ghguard, registra, passa al gh vero |
| `spikes/gh-p4/flowcheck.py` | controlli del flusso: gh e comandi Bash del modello, shim, eventi `veto`/`effect_*`, sessioni, forme di gh di tollgate |
| `spikes/gh-p4/fakegh.sh` | il gh finto condiviso dai due `controlla` |
| `spikes/gh-p4/run-p4-checks.sh` | solo l'estrazione verso `common.sh` (nessun cambio di comportamento; `controlla` ok, comandi veri del Task 1 ancora ammessi) |
| `tests/test_p4_make_case.py`, `tests/test_p4_ghguard.py`, `tests/test_p4_scripts.py` | test (nessuna rete) |
| `docs/verifiche/2026-10-21-p4-prova-gate.md`, `...-prova-flusso.md` | scheletri dei rapporti, con la tabella dei casi preriempita (nome, repo, esito atteso) |

## Cosa fa ogni modo

**run-p4-gate.sh** (uscite in `docs/verifiche/evidenze/gh-p4/`, `comandi.log` condiviso; un file esistente si rinomina `.prev-<tempo>`, mai cancellato; prima di ogni git di rete si controlla il remoto)
- `elenco`: i casi con repo, stati attesi, descrizione (`make_case.py list`).
- `installa protected|detect`: su protected richiede `P4_CONFERMA_PUBBLICO=1` (il controller lo imposta dopo aver avvisato l'utente). Clone, scrive il progetto di prova (`make_case.py baseline`), commit e push su main; `bin/tollgate init --propose --merges-per-month 20` nel clone con `TOLLGATE_STATE` di prova (sentinella, mai `~/.local/state/tollgate`), `gh` con guardia e `TOLLGATE_GH` tolta; salva `README.md`, `protect.sh`, `protection.json`, elenco di `files/` e la modalità proposta (protected: `protect.sh` presente; detect: assente, altrimenti si ferma); copia `files/`, commit «installa tollgate (P4)», push; attende `tollgate-base` e `tollgate-sentinel` sullo SHA (miss della cache) e registra stati (con autore) e issue di sentinel (criterio 34: attese 0); poi un commit vuoto spinto direttamente (stesso albero: hit della cache), stessa attesa; l'issue di sentinel che questo push diretto apre (sentinel segnala ogni commit senza PR, in entrambe le modalità) si registra e si **chiude** con `issue close`, perché `sentinel_open` è una voce di `attenzione` di ogni PR successiva. Idempotente: non ripete un push che ha già effetto.
- `protezione` (solo protected): `protect.sh <sha di origin/main>` dentro `gh` con guardia (ammesse solo `api --paginate --jq` sui check-run e la PUT di `branches/main/protection` con `--input` da un file temporaneo), poi `GET branches/main/protection`.
- `caso <nome>`: crea l'issue (per `detect-closes` anche una seconda, chiusa), costruisce i commit con `make_case.py build`, esegue le operazioni (push `<sha>:refs/heads/<ramo>`, `pr create --body-file`, `sleep`, `wait`, `edit`, `wait_count`, `post_status`, `merge` solo se la PR non è già unita, `direct`: push diretto su main solo su detect), poi per ogni SHA giudicato: attesa degli stati con tetto `P4_WAIT_MAX` (900 s), dei commenti e dell'issue di sentinel; raccolta di stati con autore (`--paginate --jq`), commenti, forma di `GET pulls/<n>`, `mergeStateStatus` (si ripete finché non è `UNKNOWN`), run e minuti; `judge` produce la riga del rapporto in `casi-righe.md`. Il run si aggancia per numero della PR in `pull_requests` (guard e run: `headSha` e numero; il run di verdict, che ha `headSha` del predefinito e nessuna PR, per finestra del run che contiene lo stato `tollgate/verdict` del bot: mai «il più recente»). A fine caso chiude le PR aperte e l'issue.
- `raccogli`: run, PR e timing dei due repo, minuti totali e fatturati, controllo di `comandi.log` con ghguard.
- `controlla`: bare repo locali, `gh` finto, tutti i modi (installa x2, protezione, ogni caso o quelli in `P4_CHECK_CASES`, raccogli); registro dei `gh` del finto e `comandi.log` passati da ghguard; la PUT di protezione registrata ha `app_id` positivo e `strict`; remoti dei cloni nel banco; righe del rapporto tutte «riuscito»; nessuna attesa andata a tetto.

**run-p4-flow.sh** (uscite in `.../evidenze/gh-p4/flusso/`; `claude -p` solo in `claude_step`, solo da `/tmp/tollgate-p4/flow`, sempre con `--plugin-dir`; il controllo è nello script e in un test)
- `issue`: crea l'issue di prova (`dividi(a, b)`); in alternativa `P4_FLOW_ISSUE=<N>`.
- `prepara`: clone di protected in `/tmp/tollgate-p4/flow/protected`, stato con la sentinella, `shim/gh` (finto, `tests/fakegh.py`) e `ghbin/gh` (gh con guardia); verifica che tollgate sia installato su origin/main. Niente `rm`: un clone esistente resta.
- `shim`: senza rete, il modello lancia `command -v gh` e `echo $PATH`; `flowcheck.py shim` confronta l'uscita del tool, letta dallo `stream-json`, con `$SHIM/gh`.
- `passo1`, `passo2`, `passo3`: `/tollgate:start #N L1` dal checkout; piano e `/tollgate:execute` dal worktree; `/tollgate:finish` dal worktree. Ognuno controlla prima `git remote get-url --push origin`, `TOLLGATE_GH` non impostata, primo `gh` del PATH, e dopo confronta i gh del modello (`ghguard`, profilo `flow`, e repo) e gli eventi `veto`/`effect_*` con l'atteso (nessun `effect_*` prima di `open-pr`, al più 2 coppie dopo): su un gh rivolto ad altro o su eventi inattesi si ferma.
- `attendi`: aggancia la PR del ramo con testa uguale allo SHA locale (numero più alto, stesso repo), attende stati e commento `<!-- tollgate-verdict sha=<testa> -->`, salva stati, commenti, `GET pulls/<n>`, merge state, run e minuti; esito in `attendi-esito.txt`, uscita 1 se non è guard e verdict `success`.
- `passo4`: solo se verdict è rosso: `/tollgate:start #N` dal checkout, poi dal worktree `task start --from-gate` con un solo giro.
- `registra`: versione di `claude`, sessioni (id e cartella), eventi, `stats` (token), `status`, log degli hook, `ricapitolo.txt`.
- `controlla`: nessun `claude` (`claude_step` scrive il comando in `*.argv` e un `stream-json` di esempio, e simula l'effetto di passo1 e passo3 sul banco locale); stampa i comandi `claude` che verrebbero lanciati, i gh che il flusso di tollgate fa davvero (12) e i gh vietati (11), ognuno passato da ghguard; prova anche il ramo del verdict rosso con `passo4`.

## Casi (`make_case.py list`)

36 casi del piano più `verde-edit` (il commento del verdetto si aggiorna con PATCH sullo stesso SHA, non si duplica: verifica `-F body=@file`). Per i 27 casi che il calcolo del gate sa giudicare, il test `OracleTest` costruisce il caso in un repo locale con il progetto di prova e l'installazione di tollgate, esegue `gate run` (i comandi veri), `guard.check` e `evaluate.evaluate`, e confronta gli stati con quelli attesi: **le attese non sono ipotesi**. Voci del piano da correggere (decisione dell'oracolo):

1. **`vitest run || true`**: il comando di gate si legge dal predefinito, non dalla PR, quindi una PR non può mettere `|| true`. Ho messo `|| true` nel comando del profilo `web` del progetto di prova (`unittest … || true`): una PR che aggiunge un test fallente in `web/` dà `command_red` dal JUnit (esito: verdict rosso).
2. **«error»: XML con entità da `tools/`**: non arriva a `error`. `run_one` scarta il report che non si legge e il comando risulta `red` senza copiare l'XML negli artefatti. Due casi: `rosso-entita-tools` (come da piano, atteso **rosso** `command_red`) e `error-entita` (la PR cambia la copia di `gate run` installata in `.github/tollgate/bin/tollgate_gate/run.py`, che `tollgate-run` esegue dal checkout della testa: scrive un XML con entità in `junit/`, atteso `error`; guard rosso perché cambia un file di tollgate). Provato in locale: `artifacts.validate` lo rifiuta.
3. **`../` in un artefatto** (`error-dotdot`): stessa via, un `report` di `results.json` con `..`; provato in locale. Guard rosso per lo stesso motivo.
4. **`allow_no_tests` con zero test** richiede `allow_no_tests = true`, ma il progetto del piano ha `false`: su protected il caso dà **rosso** (`rosso-zero-test`, `command_empty`); l'attenzione rossa (`no_tests_counted`) si prova solo su detect, dove `allow_no_tests = true` (`attenzione-zero-test`). Scostamento dichiarato: i due repo hanno `tollgate.toml` diversi su quella sola riga.
5. **«verde con attenzione» (workflow con `contents: read` e deroga `ci`)**: `waiver_ci` e `ci_waived_workflow` sono voci «da leggere», quindi `tollgate/attention` è rosso: atteso verdict verde e attention rosso, come per gli altri casi di «attenzione rosso».
6. **Stati dei casi su detect**: `tollgate/guard` gira anche su detect (il guard non guarda la modalità) e dà `success`.
7. **Sentinel**: gira in entrambe le modalità. Il commit vuoto per la prova dell'hit della cache lo segnala; per questo `installa` chiude l'issue (vedi sopra) e `detect-merge-rosso`/`detect-push-diretto` chiudono a fine caso le issue che hanno aperto. In `detect-merge-rosso` il push diretto che segue il merge prova «commento sulla stessa issue» (una sola issue aperta, almeno un commento).
8. **Cache degli identificativi**: i casi con `attention=success` presumono il ripristino della cache di `tollgate-base` per l'albero di merge-base; senza hit compare `base_ids_from_run` (voce «da leggere») e l'attenzione sarebbe rossa. È una verifica in più, non un errore dello script.

## Come si lancia (controller)

```
bash spikes/run-p4-gate.sh controlla          # tutti i casi, senza rete (~4 minuti); P4_CHECK_CASES="a b" per una scelta
bash spikes/run-p4-gate.sh installa detect
P4_CONFERMA_PUBBLICO=1 bash spikes/run-p4-gate.sh installa protected   # dopo aver avvisato l'utente (decisione 25)
bash spikes/run-p4-gate.sh protezione
bash spikes/run-p4-gate.sh caso verde-pulita   # un caso per volta; label caso-<nome>-<ora>
bash spikes/run-p4-gate.sh raccogli
bash spikes/run-p4-flow.sh controlla
bash spikes/run-p4-flow.sh issue; bash spikes/run-p4-flow.sh prepara; ... shim, passo1, passo2, passo3, attendi, [passo4], registra
```
`P4_WAIT_MAX` (900), `P4_POLL` (10), `P4_MODEL` (sonnet), `PLUGIN_LINK=1` (link senza spazi per `--plugin-dir`).

## `bash -n` e `controlla`

`bash -n` su `run-p4-gate.sh`, `run-p4-flow.sh`, `common.sh`, `fakegh.sh`, `bin/gh`, `run-p4-checks.sh`: nessun errore (anche in `tests/test_p4_scripts.py::test_syntax`).

`run-p4-gate.sh controlla` (tutti i 37 casi): tutti i modi `ok`; 3.220 gh controllati dal registro del finto e 702 da `comandi.log`, nessuna violazione, nessun `RIFIUTATO`; PUT di protezione con `app_id` 15368 e `strict`; righe del rapporto tutte «riuscito» (una per SHA giudicato).
`run-p4-flow.sh controlla`: tutti i modi `ok`, `uguali: sì` per lo shim, `esito: riuscito` e, con verdict rosso, `non riuscito` e `passo4` eseguito; 12 gh del flusso ammessi, 11 vietati.

## Test

`tests/run` verde con python3.11 e python3 (vedi sotto per l'esito finale). Nuovi: `test_p4_make_case.py` (casi, file, corpo leggibile da `prblock.parse`, oracolo, casi `error` con la copia di `gate run` cambiata), `test_p4_ghguard.py` (ammessi e rifiutati: scritture esatte, `--body-file`, profilo flow, wrapper con un gh vero finto, flowcheck), `test_p4_scripts.py` (`bash -n`, `claude -p` solo in `run-p4-flow.sh`, nessun `rm -r`/kill/force negli script, `controlla` di Task 1, gate con 8 casi scelti, flow).
TDD: i test e il codice sono nati insieme per gli script di shell (non c'è un RED significativo per uno script che non si può eseguire contro GitHub); per `ghguard` le forme rifiutate sono nei test e prima delle modifiche non erano ammesse né testate.

## Scostamenti dal piano e dubbi

- Riga `Co-Authored-By` del commit: Claude Sonnet 5.5 (il mio modello), non Opus 5.5 come nel dispatch.
- `run-p4-checks.sh` modificato (estrazione di funzioni): fuori dal brief, ma il brief lo prevedeva («estrai una libreria comune se serve»); regressione verificata (`controlla` ok, `comandi.log` del Task 1 ancora ammesso, test).
- Tempo di `tests/run`: +~1 minuto per python (i `controlla` sono nei test; esito finale: `tests/run` verde con python3.11 e python3 (2369 test)).
- Non esercitato: il controllo dei veti `veto` del flusso reale (gli eventi attesi sono un'ipotesi: `effect_*` assenti prima di `open-pr`, al più 2 coppie dopo); la scrittura `-F body=@file` con `PATCH` e `GET pulls/<n>` sul repo vero (`verde-edit` e le uscite `*-pulls.out` le registrano); `claude -p` mai lanciato.
- Rischio: `sentinel_open` e `base_ids_from_run` possono rendere rosso `attention` dei casi per cause che lo script prova a evitare ma non può garantire.

## Giro 1

Base 62a6220. Solo `bash -n` e `controlla`; mai rete, gh vero o claude.

**I-1 (guardia vincolante nel passo `claude -p`).**
- `ghwrap.py make-wrapper` genera `ghbin/gh` con profilo `flow`, repo protected, gh vero, registro e cartella dei file di ingresso scritti nel file (sola lettura, 0555); il file scarta `P4_*`, `TMPDIR` e `GH_REPO` dell'ambiente. `prepara` lo genera; `claude_step` toglie `P4_PROFILE/P4_REPO/P4_REAL_GH/P4_LOG` dall'ambiente del passo. Nel profilo flow i file di ingresso (`--body-file`) valgono solo sotto `P4_TMP` (= `$FLOW`): né `/tmp`, né `TMPDIR`, né `P4_OUT`.
- `DISALLOWED`: aggiunti `git push --force|-f|--force-with-lease|--mirror|--delete`, `git push origin main|master|+`, `*/gh`, `command gh`, `env`, `exec`, `xargs` e l'impostazione inline di `P4_*`. Limite documentato nello script: il formato `Bash(prefisso:*)` non ha jolly a metà comando né copre ogni forma (`git push origin tg/7-x:main`, `bash -c`), perciò il vincolo vero è l'audit.
- `flowcheck.py`: `gh_calls` riconosce gh dopo assegnazioni, `env`, `command`, `exec`, `xargs`, percorsi, `bash -c`, `$(...)` e backtick, dentro `&&`/`;`/`|` (tokenizzazione shlex con operatori); `risky` segnala `git push` forzato/`+refspec`/`--mirror`/`--delete`/verso main e master, nomi `P4_*`, gh per percorso o dietro un prefisso; `audit` confronta `gh-wrap.log` con le forme del profilo flow, ogni gh del transcript con l'elenco e con il registro del wrapper, e segnala scritture al wrapper. `post_passo` lo lancia dopo ogni passo (STOP) e `registra` lo lancia alla fine: una voce fuori elenco rende `registra` non riuscito (`audit-esito.txt`: «audit: non riuscito (n voci fuori elenco)»).
- Test: `GeneratedWrapperTest` (ambiente ostile: `P4_PROFILE=script`, `P4_REPO`, `P4_REAL_GH`, `P4_LOG`, `P4_TMP`, `GH_REPO`, `TMPDIR` non cambiano niente), `FlowCheckTest` (ogni aggiramento della revisione in un transcript finto, audit pulito, chiamata mai passata dal wrapper, rifiutate del wrapper, scrittura sul wrapper), `controlla` del flusso con transcript ostile (`/usr/bin/gh pr merge`, push forzato verso main) e verifica che l'audit lo segnali.

**I-2.** `error-sha-superato`: `merge_state` solo su p2; test `test_superseded_sha_case_judges_merge_state_only_on_the_last_push`.

**Minori.** M-1: `registra` ruota anche `events.jsonl/.err`, `stats.err`, `hooks.log`, `skipped.log`, audit; `installa-<n>-baseline-file.txt` ruotato; `controlla` fa due `registra` e verifica i `.prev-`. M-2: `repo create` `--public` solo per protected e `--private` solo per detect; endpoint con `/secrets` rifiutati. M-3: `SHAPES` usa `<FLOW>/protected/.claude/worktrees/tg-7-prova/.tollgate-run/7/pr-body.md`. M-4: il profilo flow vieta `issue close`, `issue comment`, `pr comment` e ammette `pr edit` solo con `--body-file`. M-5: `detect-push-diretto` prima di `detect-merge-rosso` (ultimo detect, test sull'ordine) e nota nello scheletro del rapporto. M-6: il criterio 34 è giudicato («criterio 34 (n): riuscito|non riuscito», `installa` esce 1 se non riuscito, errore di `jq` in un file a parte; il finto mostra l'issue di sentinel solo quando serve). M-7: tolto `P4_CHECK` dalla conferma sul pubblico (test: `P4_CHECK=1` senza `P4_CONFERMA_PUBBLICO` si ferma prima di clonare). M-8: «37 casi».

**Test.** Nuovi in `test_p4_ghguard`, `test_p4_make_case`, `test_p4_scripts`; RED confermato sui test di guardia e wrapper prima delle correzioni (20 fallimenti e 28 errori). `tests/run` su python3.11 e python3: esito sotto.

**Dubbi.** Il formato delle regole `--disallowedTools` non si può provare senza `claude`; l'audit è il vincolo effettivo. Il registro del wrapper contiene le chiamate della CLI di tollgate oltre a quelle del modello: l'audit controlla la forma, non l'autore.

Esito finale: `tests/run` verde con python3.11 e python3 (2394 test).

## Giro 2

Base fcb22a3. Solo `bash -n`, `controlla` e test offline con gh finto e repo git bare locali sotto una cartella temporanea; mai rete, gh vero, claude, token.

**R-1, ruling: la garanzia è la verifica dello stato.**
- Nuovo `spikes/gh-p4/flowstate.py`. `claude_step` fa un'istantanea prima e una dopo ogni passo (`<id>-stato-prima/`, `<id>-stato-dopo/`, con rotazione) e le confronta (`<id>-stato.txt`); una differenza dà «NON RIUSCITO» e uscita 3, e ferma lo script.
  - hash sha256 di `ghbin/gh`, `ghwrap.py`, `ghguard.py`, `flowcheck.py`, `flowstate.py`, `common.sh` e dello script stesso;
  - copia di `gh-wrap.log` dentro l'istantanea (troncare dopo non cancella ciò che è già copiato) e controllo che il nuovo cominci con il vecchio;
  - `git fetch` e `git ls-remote origin` completo: `main` invariato, nessun ref cancellato, nuovi o aggiornati solo `refs/heads/tg/*` (ignorati i `refs/pull/*` di GitHub), un `tg/*` aggiornato deve avere il vecchio SHA come antenato (`merge-base --is-ancestor`), altrimenti «push forzato»;
  - PR (`pr list --state all`), issue (`issue list --state all`) e protezione di `main`, letti in sola lettura dal gh con guardia del controller (profilo script): nessuna PR non più aperta o unita, nessuna PR nuova non aperta o non verso main, nessuna issue chiusa o nuova, protezione identica.
- Test RED prima (modulo assente): `tests/test_p4_flowstate.py` con repo bare locali: push su main, push forzato su `tg/*`, cancellazione di un ref, ref non `tg/*` o tag, main cancellato, hash cambiato o file sparito, registro troncato o riscritto, copia del registro, PR unita o chiusa, PR nuova fuori da main, issue chiusa o nuova, protezione cambiata, stato GitHub illeggibile. `controlla` del flusso simula quattro manomissioni (hash del wrapper, registro troncato, push su main, ref non `tg/*`) e verifica che il passo esca non zero con «STATO CAMBIATO» e «NON RIUSCITO».
- Audit dei comandi (`risky`, segnale): anche `git push` in qualunque punto della stringa grezza (dentro `bash -c`, heredoc), `git config` di alias/remote/url e `git remote set-url|add|…`, `eval`, `python -c`, e `chmod|rm|mv|ln|cp|tee|truncate|dd|install|sed -i|>` che nominano `ghbin`, `gh-p4`, `gh-wrap`, `ghwrap`, `ghguard`, `flowcheck`, `flowstate`, `run-p4`. Un `git push` semplice ora è segnalato (la skill vieta il push da Bash).
- Modello di minaccia dichiarato nel commento di `run-p4-flow.sh` e nello scheletro del rapporto (sezione «Modello di minaccia e garanzia»): cooperativo; argini e audit; garanzia = verifica dello stato, che rileva e ferma, non previene.

**N-1.** Il wrapper scarta anche `GH_HOST`, `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`, `GH_CONFIG_DIR`, `BASH_ENV`, `ENV` (valori mai letti: il test li imposta a un valore finto e controlla solo i nomi delle variabili viste dal gh finto).

**N-2.** Il confronto transcript/registro usa la riga intera con segnaposto espansi e `--repo` aggiunto (come la scrive il wrapper), con un contatore: una chiamata nel transcript consuma una riga del registro. Test: un `pr view` diverso non copre, la stessa riga serve due volte per due chiamate.

**Dubbio.** Scartare `GH_TOKEN` e `GH_CONFIG_DIR` dal wrapper fa fallire il flusso (in modo visibile, auth) se il controller autentica gh con una variabile d'ambiente invece che con la configurazione di gh: scritto nel commento dello script.

Esito finale giro 2: `tests/run` verde con python3.11 e python3 (2421 test).

## Correzioni dopo l'esecuzione

Difetti del piano emersi dalla prima esecuzione reale del controller; nessuna evidenza toccata.

**D-1.** In `make_case.py` l'attesa di `mergeStateStatus` si ricava da una regola (`merge_for`): `guard` o `verdict` non verdi -> `BLOCKED`; verdi con `attention` rossa o in errore -> `UNSTABLE`; tutto verde -> `CLEAN`; ogni attesa dei casi su protected usa `DERIVE` (solo `token-personale` resta `BLOCKED` scritto, perché è la negazione della regola). I sei casi con attention rossa (verde-config, verde-ramo-libero, verde-workflow-ci, attenzione-deroga-test, attenzione-piano-testo, attenzione-tetto-livello) attendono `UNSTABLE`. Test: la regola vale per tutte le attese su protected (almeno 25 controlli) e i sei casi.

**D-2.** `bin/tollgate_flow/gh.py:pr_edit` aggiorna il corpo con `gh api --method PATCH repos/{owner}/{repo}/pulls/<n> -F body=@<file>` (il numero è un intero, un errore di gh resta un `GhError`). `tests/fakegh.py` emula la PATCH (il guasto simulato resta `fail=["pr edit"]`); i test di `test_openpr` e `test_sync` contano le PATCH al posto di `pr edit`; `test_gh` verifica gli argomenti esatti, che un guasto lasci il corpo e resti `GhError`, e che il numero non intero sia rifiutato. Guardrail del modello (`bash.py`) non toccati: la CLI non passa dagli hook. `run-p4-gate.sh`, op `edit` di `verde-edit`: stessa forma. `ghguard.py`: ammessa solo `api --method PATCH repos/ginz0ls/tollgate-p4-protected/pulls/<intero> -F body=@<file>` (profilo script: cartelle già ammesse; profilo flow: sotto `$FLOW`), nessun altro campo o endpoint, detect no; `pr edit` ora vietato nel profilo flow; il registro dei comandi (spazi nel percorso) la legge. `flowcheck.SHAPES` ha la forma REST. Test RED prima in `test_p4_ghguard` (forma ammessa, `-f title=`, secondo campo, `pulls/1/merge`, `issues/1`, detect, altro owner, `-F body=testo`, file fuori cartella).

Incluse così come sono le modifiche non committate del controller a `run-p4-flow.sh`, `flowstate.py` e `2026-10-21-p4-prova-flusso.md`.

Esito: `tests/run` verde con python3.11 e python3 (2430 test).

## Giro 4 — ritentativi delle letture di `gh api` sui 5xx transitori

**Commit**: e7dd195 «tollgate P4: le letture di gh api ritentano sui 5xx transitori di GitHub (Task 16, giro 4)».

**Cosa**
- `bin/tollgate_core/ghcli.py`: unico punto di decisione `_run_retrying(state, repo, args)`, usato da `api`, `run_json` e `run_json_lines`. Lettura = argomenti che cominciano con `api` senza `--method`/`-X` (anche `--method=…`, `-XPOST`); `api(method="GET")` non aggiunge `--method`, quindi rientra nella stessa regola. Transitorio (`_transient`) = uscita non zero con stderr che contiene `HTTP 5dd` o `unexpected end of JSON input`, oppure con `--include` una riga di stato >= 500. 3 tentativi, attese `RETRY_DELAYS_S = (2, 4)` col sonno da `_sleep = time.sleep` (sostituibile nei test). Dopo l'ultimo tentativo l'ultima risposta passa al codice di sempre: stesso `GhError` e stesso testo, e con `include` lo stesso `ApiResult`. Il timeout (`GhError` sollevato da `run`) non si ritenta; 4xx, `pr …` e scritture nemmeno. Docstring del modulo e di `api` aggiornate.
- `tests/fakegh.py`: chiave `api_flaky` `{"<percorso senza ?query>": ["<stderr>", ...]}`: ogni `gh api` su quel percorso consuma un messaggio, lo scrive su stderr ed esce con 1 senza stdout; finita la lista risponde normalmente (documentata nella docstring).

**Test** (prima rossi: 11 errori, `_sleep` assente; poi verdi)
- `tests/test_ghcli.py`, `RetryTest` (con `run` sostituito): GET 500 poi ok (2 chiamate, attesa [2]); paginate con `unexpected end of JSON input` poi ok; sempre 500 → `GhError` «gh api p/x: gh: Server Error (HTTP 500)», 3 chiamate, attese [2, 4]; POST/PATCH/PUT/DELETE con 500 → 1 chiamata; `include` con 403/404 → risultato, 1 chiamata, e con riga di stato 502 → ritenta; 404/422 senza include → 1 chiamata; timeout → 1 chiamata; `run_json_lines` lettura ritenta, con `--method POST`, `-X POST`, `--method=POST` e `pr list` no; `run_json` lettura ritenta, `pr create` no.
- `tests/test_ghcli.py`, `FakeGhFlakyTest`: `api_flaky` del finto, un errore poi la risposta, lista consumata nel file dei dati.
- `tests/test_gate_guard.py::test_transient_500_on_commit_pulls_is_retried`: `commits/<sha>/pulls` risponde una volta `unexpected end of JSON input` → `tollgate/guard` pubblicato `success`, una sola attesa di 2 s.

**Suite**: `tests/run` verde: Python 3.11.16, 2441 test OK; Python 3.13.5, 2441 test OK.

**Minori della ri-revisione** (commit aa1a0b3 «tollgate P4: ritentativi solo per le letture vere e attese brevi nei test (Task 16, giro 4, minori)»)
- M4-1: `_WRITE_FLAGS` comprende anche `-f`, `-F`, `--field`, `--raw-field`, `--input`, perché con questi gh passa a POST anche senza `--method`. Il controllo è per prefisso, quindi copre anche `-fk=v`, `--field=…`, `--raw-field=…`, `--input=…`, `--method=…` e `-XPOST`. Test `RetryTest.test_api_field_arguments_make_a_write`: 500 → 1 chiamata con ciascuna forma, via `run_json` e via `api(fields|file_fields|input_file)`.
- M4-2: `RETRY_DELAYS_ENV = "TOLLGATE_GH_RETRY_DELAYS"` (aggiunta a `paths.TEST_ENVS`) è letta con `paths.test_env`, quindi vale solo nello stato di test. Contiene le attese separate da virgole e il numero di attese decide il numero di tentativi. `tests/flowkit.py` la imposta a `"0,0"` nell'ambiente dei sottoprocessi del banco: `test_init.py::ModeTest::test_token_without_admin_undetermined` passa da circa 8 s a circa 2,5 s. Test: `RetryTest.test_delays_from_test_env_only_in_test_mode` (stato di test → attese [0, 0.5]; stesso ambiente con stato non di test → [2, 4]) e `FlowLabTest.test_env_makes_gh_retries_wait_zero`. `RetryTest` ora usa uno stato `TempState` vero e toglie la variabile dall'ambiente in `setUp`.
- Prima rossi (11 errori in test_ghcli, 1 in test_flowkit), poi verdi. Suite: `tests/run` verde, 2444 test OK su Python 3.11.16 e su 3.13.5.

## Giro 5 — ritentativi per le scritture idempotenti dichiarate

**Commit**: «tollgate P4: ritentativi anche per stati e modifiche di commenti, scritture idempotenti (Task 16, giro 5)» (vedi `git log`).

**Cosa**
- `bin/tollgate_core/ghcli.py`: `api(..., retry=False)` è un parametro nuovo. `_run_retrying(..., idempotent=False)` resta l'unico punto che decide: si ritenta se la chiamata è una lettura (come nel giro 4) oppure se è `idempotent`. Le condizioni sono quelle di prima: stessi transitori, 3 tentativi, stesse attese, stesso errore finale. `run_json*` non cambiano e le GET si ritentano a prescindere dal parametro.
- `bin/tollgate_gate/github.py`: `retry=True` (con un commento di una riga sul perché) solo in `set_status` (POST `statuses/<sha>`) e nel PATCH di un commento esistente in `upsert_comment`. Restano senza ritentativo `comment_issue` (anche quando la chiama `upsert_comment` per un commento nuovo), `create_issue` e tutto il resto.
- `tests/fakegh.py`: `api_flaky` accetta anche la chiave `"<METODO> <percorso>"`, valida solo per quel metodo. Serve perché la GET dei commenti e il POST di un commento nuovo hanno lo stesso percorso.

**Test** (prima rossi: 2 errori e 4 fallimenti; poi verdi)
- `test_ghcli.RetryTest.test_write_declared_idempotent_is_retried`: POST con `retry=True`, 500 a corpo vuoto poi ok → 2 chiamate, attesa [2]. PATCH sempre 500 → `GhError` «gh api --method: gh: Server Error (HTTP 500)», 3 chiamate, attese [2, 4]. POST di default → 1 chiamata.
- `test_ghcli.RetryTest.test_retry_true_keeps_4xx_final`: 422 con `retry=True` → 1 chiamata.
- `test_gate_guard.GithubTest`: `test_set_status_retries_transient_500`; `test_new_comment_and_issue_are_not_retried` (`comment_issue` e `create_issue` con 500 → 1 chiamata ciascuno, `GhError`, nessun commento); `test_upsert_patch_is_retried_but_new_comment_post_is_not`.
- `test_gate_guard.RunTest.test_transient_500_on_guard_status_post_is_retried`: il POST di `tollgate/guard` risponde una volta 500 a corpo vuoto, poi `success` viene pubblicato.

**Suite**: `tests/run` verde, 2450 test OK su Python 3.11.16 e su 3.13.5.
