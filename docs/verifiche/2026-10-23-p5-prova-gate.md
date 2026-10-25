# Prova reale del gate su detect con azioni fissate, rivalutazione e sentinella (P5, Task 13)

Data: 25 ottobre 2026 (esecuzione dalle 19:24 alle 19:33 UTC). Esecuzione del controller con `spikes/run-p5-gate.sh` (modi `aggiorna`, `pin-on`, `caso <nome>`, `pin-off`, `raccogli`), repo `ginz0ls/tollgate-p4-detect` (privato, GitHub Free, modalità `detect`), gh 2.46.0 (`gate-raccogli-versione.txt`). Ogni comando di rete passa dal profilo `p5` di `spikes/gh-p4/ghguard.py`. Uscite grezze in `docs/verifiche/evidenze/p5/` con prefisso `gate-` (mai cancellate: un file già esistente si rinomina in `<nome>.prev-<tempo>`). Le righe «Ruling» del ledger sono decisioni del controller.

**Esito: pieno, nessun caso composito.** Tutti i cinque casi (`pulita-fissata` con la sua osservazione `pulita-fissata-cache`, `rifiuto-v4`, `rivalutazione`, `skip-ci`) e la procedura di aggiornamento sono riusciti al primo tentativo: `gate-tentativi.tsv` ha una sola riga per modo, tutte con codice d'uscita 0 (`aggiorna`, `pin-on`, i quattro `caso`, `pin-off`, e due `raccogli`, il secondo dopo la chiusura delle issue da parte del controller). Nessun tentativo fallito da elencare.

**Un errore di aggancio, dichiarato.** Per `pulita-fissata` lo script ha agganciato come run di `guard` il 40225794682 invece del 40225942870 (ripiego «il più recente negli ultimi 2 minuti»). Il 40225794682 è il `guard` della PR #17 (`tollgate-config/0.2.0`), partito prima di `pin-on`, con il workflow vecchio a `actions/checkout@v4` (`gate-log-gate-caso-pulita-fissata-20261025-202502-guard-40225794682.out`, riga 39). Il guard giusto è il 40225942870, ramo `tg/18-p5-gate-pulita-fissata-…`, letto dal controller: `gate-log-pulita-fissata-guard-giusto-40225942870.out` (`run_duration_ms` 11000, «Cache mode: read», checkout fissato per SHA). Gli **esiti** del caso restano validi, perché sono giudicati dagli stati sullo SHA della PR (autore `github-actions[bot]`); sono falsati solo i minuti di `gate-casi-righe.md` (0,6) e il log di guard filed sotto `gate-caso-pulita-fissata-…-guard-*`. Qui i minuti sono corretti (0,7) e quel run è attribuito alla procedura di aggiornamento. Ruling: lo script filtra i run per `headBranch` della PR e per evento prima del ripiego temporale.

## Versioni e impianto

| Voce | Valore |
|---|---|
| gh | 2.46.0 (2025-01-13 Debian 2.46.0-3) |
| tollgate | `tollgate-config/0.2.0` (versione proposta da `init --update`) |
| Azioni fissate (decisione 13) | checkout `3d3c42e5…` (v7.0.1), cache/restore `55cc8345…` (v6.1.0), upload-artifact `cf430e03…` (v7.0.2), download-artifact `9000827c…` (v8.0.2) |
| Runner | ubuntu-24.04 versione 20261012.334.1, runner 2.338.0 |
| `sha_pinning_required` all'inizio | `false` (`pin-on` lo ha letto e salvato fuori dal repo) |

Sequenza reale (`gate-tentativi.tsv`, UTC del 25/10/2026): `aggiorna` 19:24:29, `pin-on` 19:24:48, `pulita-fissata` 19:25:52, `rifiuto-v4` 19:26:29, `rivalutazione` 19:28:01, `skip-ci` 19:32:11, `pin-off` 19:32:25, `raccogli` 19:33:06 e 19:33:45.

## Casi

L'autore è `github-actions[bot]` per tutti gli stati. «Minuti» sono la somma di `run_duration_ms` dei run seguiti dallo script (l'API dei minuti fatturati dà 0 sui privati Free, quindi sono durate, non fatturazione). Colonne come nel rapporto di P4.

| Caso | Repo | PR | SHA | Stati con autore | Atteso | Esito | Minuti |
|---|---|---|---|---|---|---|---|
| `pulita-fissata` | detect | #19 (`tg/18-p5-gate-pulita-fissata-20261025-202502`) | `9565f3157f` | guard=success, verdict=success, attention=success (tutti `github-actions[bot]`) | guard=success, verdict=success, attention=success | riuscito | 0,7 (3 run: guard 40225942870 11 s, run 40225942726 13 s, verdict 40225962034 16 s = 40 s); registrato 0,6 con il guard sbagliato (9 s) |
| `pulita-fissata-cache` | detect | #19 | `9565f3157f` | job `tollgate-verdict` (40225962034): «Cache mode: read»; job `tollgate-guard` (40225942870): «Cache mode: read» | «Cache mode: read» (VG1) | riuscito | come sopra |
| `rifiuto-v4` | detect | nessuna PR (ramo `p5-gate-rifiuto-v4-20261025-202603`) | `d8e9b65803` | run 40226016168 conclusione `failure` in «Set up job», dopo 5 s | run rifiutato con messaggio «must be pinned to a full-length commit SHA» | riuscito | 0,1 (1 run, 5 s) |
| `rivalutazione` | detect | #20 (`tg/18-p5-gate-rivalutazione-20261025-202640`) | `d9e3d60a3c` | `tollgate/verdict` dopo la modifica del corpo: `pending` (github-actions[bot], 19:27:35Z) poi `success` (github-actions[bot], 19:27:54Z); alla fine guard=success, verdict=success, attention=success (tutti bot) | `pending` (guard su `edited`) poi `success`, tutti bot (decisione 15) | riuscito | 0,2 (1 run seguito, 11 s: la prima corsa; i run dopo la modifica non sono contati) |
| `skip-ci` | detect | partenza PR #21 (`p5-gate-skip-ci-base-20261025-202813`, `fa4eb99abe`) unita con squash; poi due push diretti su `main` | saltato `6d9462e417` (`[skip ci]`), normale `650a6d774f` | saltato `tollgate/sentinel`=failure, normale=failure, partenza=success; run di sentinella: sul saltato 0, sul normale 1 (40226429685); issue di sentinella aperte 1 (#22), commenti 0 | saltato=failure, normale=failure, partenza=success, nessun run sul saltato, una sola issue che nomina il saltato | riuscito | 0,8 (2 run: sentinella sulla partenza 40226232025 11 s, sentinella sul normale 40226429685 35 s) |

Note per caso, tutte dalle evidenze:

- **pulita-fissata.** Il lavoro `tg/18-…` chiude l'issue #18 (aperta dal controller), quindi `attention` è verde. Il log di `verdict` mostra anche `download-artifact@9000827c…` con `digest-mismatch: error` e cache ripristinata («Cache hit for: tollgate-ids-45dac5f5…»).
- **rifiuto-v4.** Messaggio esatto in `gate-caso-rifiuto-v4-20261025-202603-v4-log-failed.out`: «The action actions/checkout@v4 is not allowed in ginz0ls/tollgate-p4-detect because all actions must be pinned to a full-length commit SHA.» Stesso messaggio e stesso passo («Set up job») della sonda VG2 di `docs/verifiche/2026-10-23-p5-verifiche.md`.
- **rivalutazione.** Ordine reale degli stati `tollgate/verdict` dopo la modifica del corpo, dal più vecchio (`gate-caso-rivalutazione-20261025-202640-ordine.txt`): `pending` poi `success`, entrambi dal bot, 19 secondi tra i due. Il `pending` è prima del `success`: decisione 15 confermata, nessun caso in cui `verdict` resti `pending`.
- **skip-ci.** Il commit saltato (`6d9462e417`) non ha run di sentinella; il commit normale successivo (`650a6d774f`) sì. La sentinella (`tollgate-sentinel`) ha aperto l'issue #22 «tollgate: merge non verificato» che elenca **entrambi** i commit (`6d9462e417` e `650a6d774f`, «nessuna PR unita nel ramo predefinito contiene il commit»), 0 commenti. I vecchi `failure` di P4 su detect non hanno falsato la prova: il segnale cercato è il più recente, e la partenza (PR #21) aveva lasciato `success`. Prima del caso le issue di sentinella aperte erano 0 (`gate-caso-skip-ci-20261025-202813-issue-prima.txt`).

## Procedura di aggiornamento 9.4 (`aggiorna`)

Eseguita nel clone fresco di detect con `bin/tollgate init --update`.

| Passo | Ottenuto | Evidenza |
|---|---|---|
| `init --update` | modalità del gate `detect`; proposta di 38 file in `docs/superpowers/tollgate-init/`; ramo suggerito `tollgate-config/0.2.0` | `gate-aggiorna-init.out` |
| Ramo e PR | PR #17, ramo `tollgate-config/0.2.0`, SHA `f6de46341c`; solo i file proposti (`git add -- <file>`, mai `-A`) | `gate-aggiorna-pr.env`, `gate-aggiorna-staging.txt` |
| Stati sulla PR | guard=success (19:23:26Z), verdict=success (19:23:41Z), **attention=failure** (19:23:42Z, «1 voci da leggere: vedi il commento»), tutti `github-actions[bot]` | `gate-aggiorna-statuses.out` |
| Merge | `--squash`, merge commit `d606e4cba5`, stato `MERGED` | `gate-aggiorna-merge-sha.txt`, `gate-aggiorna-merge-stato.out` |
| Dopo il merge | `tollgate/sentinel`=success (19:24:06Z, «controllato fino a qui»), `tollgate/base`=success (19:24:19Z, «suite della base verde») | `gate-aggiorna-merge-statuses.out` |

`attention=failure` è l'esito atteso per un ramo `tollgate-config/*` (il ramo non è `tg/<N>-…`): la procedura è proseguita con il merge perché `guard` e `verdict` erano `success`. Run seguiti: `tollgate-run` sulla PR (40225794322, 10 s), sentinella sul merge (40225845695, 10 s), base sul merge (40225845683, 23 s). Il guard della PR #17 è il 40225794682 (9 s, ancora a `actions/checkout@v4` perché precedente a `pin-on`, «Cache mode: read»), quello agganciato per errore a `pulita-fissata`.

Lettura fuori dall'elenco delle decisioni 20 e 21: `bin/tollgate init --update` esegue **internamente** un `git fetch origin` (`gitw.fetch`), che non passa da `ghguard.py gitcheck` e quindi non compare in `comandi.log`; è una lettura sul repo detect, la stessa che faceva `init --propose` in P4. Il resto delle letture di `init --update` (protezione di `main`) passa dal wrapper `gh` con guardia `p5`.

## Osservazioni dai log dei job

Fonte: `gate-raccogli-osservazioni.txt` e i `gate-log-*.out`.

- **Checkout v7 per SHA.** Tutti i workflow aggiornati usano `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`, scaricato con «Download action repository … (SHA:3d3c42e5…)» e con `fetch-depth: 0`; funziona con `sha_pinning_required` acceso (guard giusto, `verdict`, `run`, `base`, `head`, `sentinel`). L'unico `checkout@v4` visto girare è quello del guard della PR #17, prima di `pin-on`.
- **`digest-mismatch: error` di download-artifact v8.** Il valore predefinito appare nei passi `actions/download-artifact@9000827c…` di `tollgate-base` (merge di #17, run 40225845683) e di `tollgate-verdict` (40225962034, due volte). Il passo ha scaricato `tollgate-ids` e calcolato lo SHA256 dell'artefatto scaricato, senza errori: nessun mismatch si è verificato. Conferma il ruling sul `digest-mismatch: error` predefinito (fail-closed), che qui non ha avuto occasione di scattare.
- **Cache per job.** «Cache mode: read» nei job `tollgate-guard` (40225794682, 40225942870) e `tollgate-verdict` (40225962034), cioè nei job da `workflow_run`: vincolo VG1 confermato anche con le azioni fissate. «Cache mode: write» in `head`, `base` di `tollgate-run`, in `tollgate-base`, `tollgate-sentinel` e nel workflow di prova. Prima corsa di `tollgate-base` dopo l'aggiornamento: «Cache not found for input keys: tollgate-ids-45dac5f53c749…»; nei run successivi «Cache restored successfully» con `cache/restore@55cc8345…`.
- **Upload.** `upload-artifact@cf430e03…` stampa «SHA256 digest of uploaded artifact is …» nei job `head` e `ids`.

## Stato finale di detect e registro

`gate-raccogli-stato-finale.txt` (dopo la chiusura delle issue da parte del controller):

| Voce | Valore |
|---|---|
| PR aperte | 0 (atteso 0) |
| `sha_pinning_required` | `false`, come all'inizio (`pin-off` rc 0, verificato con GET: `{"enabled":true,"allowed_actions":"all","sha_pinning_required":false}`) |
| Issue aperte | nessuna |
| File di stato di `pin-on`/`pin-off` | assente (consumato da `pin-off`) |

Issue create dal controller con `gh issue create`, ammesse dalla decisione dell'utente del 25/10/2026 (al più 2, solo dal controller, solo su `ginz0ls/tollgate-p4-detect`, titolo «prova P5: <caso>»): **una sola di due**, #18 «prova P5: pulita-fissata e rivalutazione» (19:24:55Z). Serviva a `pulita-fissata` e `rivalutazione` per il «Closes #18» dei rami `tg/18-…`. La sentinella ha aperto da sé la #22, nel caso `skip-ci`. Il controller ha chiuso #22 e #18 con `gh issue close` (19:33:19Z e 19:33:20Z), **senza commento**: la guardia rifiuta `--comment`.

Registro dei comandi (`comandi.log`, esaminato da `ghguard.py comandi`): 259 comandi controllati (`gate-raccogli-comandi-controllo.txt`), compresi quelli delle prove precedenti del Task 1. Nel periodo del Task 13: un solo `issue create`, due `issue close`, due `pr merge` (#17 e #21), due push diretti su `main` (i due del caso `skip-ci`, il commit `[skip ci]` e il normale). Il `fetch` interno di `init --update` non compare (vedi sopra).

## Minuti di Actions

Fonte: `gate-raccogli-minuti.txt`, che registra 10 run e 143 s. Correzione per l'aggancio sbagliato: il run 40225794682 (9 s) resta, come guard di #17, nei minuti dell'aggiornamento; va aggiunto il guard 40225942870 (11 s) di `pulita-fissata`. Run seguiti: 11, **154 s, circa 2,6 minuti**.

| Gruppo | Run (s) | Totale |
|---|---|---|
| `aggiorna` | run 10, guard 9, sentinella 10, base 23 | 52 s |
| `pulita-fissata` | guard 11, run 13, verdict 16 | 40 s |
| `rifiuto-v4` | 5 | 5 s |
| `rivalutazione` | 11 | 11 s |
| `skip-ci` | sentinella partenza 11, sentinella normale 35 | 46 s |

Non sono contati i run non seguiti dallo script (per esempio il `verdict` della PR #17, i run di `guard` e `verdict` dopo la modifica del corpo in `rivalutazione`, i run della PR #21): la cifra è un minimo. Il campo fatturato dell'API `timing` è 0 ms (privati Free).

## Aggancio dei run e suo limite

Durante la prova lo script agganciava `guard` e `verdict` col ripiego «il più recente negli ultimi due minuti», e per `pulita-fissata` ha preso il guard della PR #17. Dopo la prova (commit `ef3f8d2` e `7f499d9`) l'aggancio è cambiato: `guard` (`pull_request_target`) si cerca per ramo della PR; `verdict` è il primo run `workflow_run` di `tollgate-verdict.yml` creato dopo la fine del run di `tollgate-run.yml` della PR. Sul vero la regola sceglie il run giusto (`tollgate-run` 40225942726 finito alle 19:25:24Z, verdict 40225962034 creato alle 19:25:26Z). Un run `workflow_run` porta il ramo e lo SHA del predefinito, non quelli della PR, quindi con due PR valutate in parallelo il verdict di un'altra PR creato in quell'intervallo verrebbe preso al suo posto: lo script presume una sola PR in valutazione alla volta, come in questa prova. L'aggancio serve solo ai minuti e ai log salvati; gli esiti dei casi si giudicano dagli stati sullo SHA della PR.
