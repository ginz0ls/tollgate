# Task 1, report dell'implementatore (script e sonde, senza rete)

## Cosa c'è
- `spikes/gh-p4/run-p4-checks.sh` (eseguibile): modi `prepara`, `v1` ... `v9`, `raccogli`, `pulisci-sonde`, `controlla`.
- `spikes/gh-p4/workflows/probe-{target,run,verdict,base}.yml`: installati solo su `ginz0ls/tollgate-p4-protected`.
- Il rapporto `docs/verifiche/2026-10-21-p4-verifiche.md` NON c'è: lo scrivo nel secondo giro dalle uscite del controller.

## Regole di sicurezza dello script
- Proprietario fisso `ginz0ls`; nessun `gh api user`.
- `guard_args` gira prima di OGNI `gh`: solo `--version`, `auth status`, `repo create|clone|view` sui due repo, `pr|issue|run` con `--repo` ammesso, `api` solo in lettura (nessun `-X`, `-f`, `-F`, `--input`, `graphql`) con endpoint `repos/<uno dei due>/...`. `--visibility`, `repo delete`, `secret`, `auth` diverso da `status` fermano lo script. Provato con 11 casi (vedi sotto). **Precisazione (fix round 1):** «`api` solo in lettura» e il resto dell'elenco valgono per i comandi effettivamente usati (`comandi.log`: 146 comandi `gh`, nessuno fuori elenco) e per come la guardia era scritta al primo giro, che era più permissiva di così (confrontava token esatti, nessuna tabella dei sottocomandi); è stata rafforzata dopo l'esecuzione, vedi «Fix round 1».
- `check_remote` prima di ogni `git` che spinge/scarica: il remoto del clone deve essere `https://github.com/<repo>(.git)` o `git@github.com:<repo>.git` (nel modo `controlla`, solo la base locale).
- Uscite in `docs/verifiche/evidenze/gh-p4/` (o `P4_OUT`), mai cancellate: un file già presente si rinomina in `<nome>.prev-<tempo>` (`rot`). Ogni chiamata salva `<etichetta>.out`, `.err`, `.rc`; ogni comando è anche in `comandi.log`. Cloni in `/tmp/tollgate-p4/gh/{protected,detect}` (`P4_WORK`).
- Nessuna `${{ }}` nelle righe `run:` delle sonde: lo verifica `controlla` (e la sintassi YAML con PyYAML). Le sonde salvano chiavi e valori non testuali (SHA, numeri, nomi di ramo/file, login), non i corpi.
- Variabili: `P4_OUT`, `P4_WORK`, `P4_WAIT_MAX` (tetto per ogni run, default 600 s), `P4_POLL` (10 s), `P4_RETRY_SLEEP` (5 s). `P4_CHECK`/`P4_GIT_BASE` sono per `controlla`.

## Verifiche eseguite
`bash -n spikes/gh-p4/run-p4-checks.sh`: esito 0 (stampa BASH_N_OK).

Corsa `controlla` (cartella: `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/6196ff63-38d8-4a02-ada3-ddb16bd01d50/scratchpad/p4-controlla`, uscita completa in `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/6196ff63-38d8-4a02-ada3-ddb16bd01d50/scratchpad/controlla-uscita.txt`):
```
cartella del controllo: <scratchpad>/p4-controlla
modo prepara: ok
modo v1: ok
modo v2: ok
modo v3: ok
modo v4: ok
modo v5: ok
modo v6: ok
modo v7: ok
modo v8: ok
modo v9: ok
modo raccogli: ok
modo pulisci-sonde: ok
--- registro dei comandi gh
comandi gh registrati: 87
     2  gh --version
    37  gh api
     1  gh auth status
     1  gh pr close
     1  gh pr comment
     5  gh pr create
     2  gh pr list
     3  gh pr merge
     1  gh pr view
     2  gh repo clone
     2  gh repo create
     8  gh run download
    12  gh run list
     5  gh run view
     5  gh run watch
--- remoti dei cloni
  protected -> <scratchpad>/p4-controlla/remote/ginz0ls/tollgate-p4-protected.git
  detect -> <scratchpad>/p4-controlla/remote/ginz0ls/tollgate-p4-detect.git
--- uscite attese
  tutte presenti
--- nel banco di prova, i rami e i commit
cd528ed togli i workflow sonda (tollgate P4)
72c2e37 sonda v5 push diretto 20261021-170920
017e09f sonda v5-rebase
b7ec394 squash p4-v5-squash-20261021-170920
aa7c083 merge p4-v5-merge-20261021-170920
8ea9b90 sonda v4 push 20261021-170920
6b2278b sonda v5-merge
ca30444 sonde tollgate P4: workflow delle verifiche
7a8dd29 init
CONTROLLA: ok
```
`controlla` verifica: `bash -n`, nessuna espressione in `run:`, YAML valido, 12 modi senza errori, registro del `gh` finto (nessun repo diverso dai due; nessun `api user`, `auth` ≠ `status`, `repo delete`, `secret`, `--visibility`, nessun `api` in scrittura, ogni `pr|run|issue` con `--repo`), remoti dei cloni nel banco locale, presenza delle uscite attese.

Guardie provate a mano (ciascuna ferma lo script con errore): `api user`, `auth login`, `repo delete`, `repo create other/x`, `api repos/ginz0ls/other/...`, `pr list` senza `--repo`, `api -X POST`, `secret set`, `--visibility`; le chiamate legittime passano.

Limite onesto: la corsa finta non prova il comportamento reale di GitHub (campi JSON, tempi, nomi dei run). Punti che dipendono dal vero e che il controller deve tenere d'occhio: (1) `wait_run` trova il run per sha o ramo, con ripiego sul più recente creato negli ultimi 2 minuti per `probe-target` e `probe-verdict` (non sappiamo che `head_sha` abbiano); (2) la struttura di `gh run download` (con un solo artefatto va nella cartella, con più artefatti in sottocartelle: gli script cercano per nome file con entrambi i percorsi).

## Sonde (cosa fa ciascuna)
- **probe-target** (`pull_request_target`, checkout del predefinito, `statuses: write`): chiavi e valori non testuali dell'evento (V3); `git fetch origin refs/pull/<n>/head` e confronto con `head.sha` (V3); `gh --version` e `gh api repos/<r>` con `GH_TOKEN` (V7); POST di uno stato `probe/target` e lettura di `creator.login` (V6). Artefatto `probe-target` con `info.json`, `event-keys.json`, `fetch.log`.
- **probe-run** (`pull_request`): ripristina la cache `probe-v4-<tag>` (V4, `cache-hit` in `info.json`); chiavi dell'evento; tre upload con `continue-on-error` e `if-no-files-found: error`: `probe-run-dotdot-out` (`../probe-outside.txt`), `probe-run-dotdot-in` (`sub/../keep.txt`), `probe-run-symlink` (cartella con un collegamento assoluto a `/etc/hostname` e uno relativo) (V8); artefatti `probe-run-main` e `probe-run-info` (esiti degli upload).
- **probe-verdict** (`workflow_run` di probe-run, `issues/pull-requests/statuses: write`, checkout del predefinito): scarica i tre artefatti V8 sotto `$RUNNER_TEMP/dl/...` con `path:` (esiti in `info.json`, albero in `listing.txt`); salva la cache `probe-v4-<tag>` (V4); chiavi di `workflow_run` (V3); scrive un commento sulla PR con `GITHUB_TOKEN` e legge `user.login/type/id` (V1); stato `probe/verdict` (V6). Artefatto `probe-verdict-info`.
- **probe-base** (`push` su main): ripristina la cache (V4, job push); `gh` e `gh api` (V7); stato `probe/base` sul commit (V6). Job con id `base` e nome predefinito (il check-run si chiamerà `base`: V6 lo conferma). Artefatto `probe-base-info`.
- La chiave di cache usa il contenuto di `.github/probe-tag` (scritto da `prepara`, tolto da `pulisci-sonde`), così una ripetizione dopo `pulisci-sonde` + `prepara` non trova voci vecchie.

## Piano per il controller (in che ordine, cosa esce, attese)
Prerequisiti: `gh auth status` con scope `repo` e `workflow`. Lancio: `spikes/gh-p4/run-p4-checks.sh <modo>` dal worktree.

| Ordine | Modo | Cosa fa (operazioni della decisione 25) | Attese | File di uscita attesi (in `gh-p4/`) |
|---|---|---|---|---|
| 1 | `prepara` | `auth status`, versioni di gh e claude (`claude --version`, locale), per ciascun repo `api repos/<r>`, se 404 `repo create` (protected `--public`, detect `--private`, `--add-readme`), clone; nel pubblico commit e push su main di 4 workflow e `probe-tag` | nessuna sui run (il push di main fa partire una prima `probe-base`, non si aspetta) | `prepara-auth.*`, `prepara-versione-gh.*`, `prepara-versione-claude.out`, `prepara-<n>-esiste.*`, `prepara-<n>-crea.*`, `clone-<n>.*`, `prepara-push-protected.*`, `prepara-sonde-sha.txt` |
| 2 | `v1` | PR1 (ramo `p4-v1-<ts>`), commento utente, attende e scarica in sequenza `probe-target`, `probe-run`, `probe-verdict`; poi `pr list`, `pr view --json comments`, `api issues/<n>/comments` | 3 run in serie, tetto 600 s ciascuno (tipico 1-3 min) | `v1-pr.env`, `v1-{target,run,verdict}-{runs,watch,view,download}.*`, `-runid.txt`, `v1-*-artifacts-<id>/`, `v1-pr-list.out`, `v1-pr-view-comments.out`, `v1-api-comments.out`, `v1-login.txt` (V1) |
| 3 | `v2` | 4 GET di protezione (detect e protected, con e senza `--include`) | nessuna | `v2-{detect,protected}{,-senza-include}.{out,err,rc}` (V2) |
| 4 | `v3` | dopo v1: riepilogo dei campi degli eventi dagli artefatti e `git fetch origin refs/pull/<n>/head` dal clone | nessuna | `v3-riepilogo.jsonl`, `v3-fetch-pull*.{out,err,rc}` (V3) |
| 5 | `v4` | dopo v1: PR2, attende `probe-run` (cache in job pull_request); commit e push su main, attende `probe-base` (cache in job push); chiude PR2 | 2 run | `v4-pr.env`, `v4-push.env`, `v4-{run,base}-*`, `v4-*-artifacts-<id>/info.json` con `cache_hit` (V4) |
| 6 | `v5` | 3 PR da main, merge con `--merge`, `--squash`, `--rebase` (con ripetizioni), push diretto; per ogni commit nuovo `api commits/<sha>/pulls` (fino a 4 tentativi) | solo ripetizioni brevi (5 s) | `v5-shas.txt`, `v5-riepilogo.tsv` (kind, sha, PR con `merged_at` e `base`), `v5-<tipo>-<sha8>.{out,err,rc,tentativi}` (V5) |
| 7 | `v6` | dopo v1 (e v4, v5): GET statuses e check-runs di PR1, del push di v4 e dei commit di v5 | **aspettare che le `probe-base` dei push di v5 siano finite** (un paio di minuti dopo v5), altrimenti mancano check-run | `v6-*-statuses.out`, `v6-*-check-runs.out`, `v6-riepilogo.txt` (login, nome del check-run, `app.id`) (V6) |
| 8 | `v7` | nessuna rete: legge gli `info.json` di v1 e v4 | nessuna | `v7-riepilogo.txt` (versione di gh, esito di `gh api` con `GH_TOKEN`, immagine del runner) (V7) |
| 9 | `v8` | dopo v1: `api actions/runs/<id>/artifacts`, `run download -n` dei tre artefatti, albero trovato | nessuna | `v8-artefatti.out`, `v8-dl-*`, `v8-find.txt`, `v8-listing-verdict.txt` (V8) |
| 10 | `v9` | 2 GET di `actions/permissions` | nessuna | `v9-{protected,detect}.{out,err,rc}` (V9) |
| 11 | `raccogli` | elenchi di run e PR, `run_duration_ms` di ogni run | nessuna | `raccogli-*.out`, `raccogli-minuti.txt` |
| 12 | `pulisci-sonde` | su entrambi i repo: `git rm` delle sonde e di `probe-tag`, un commit, push su main; sul privato "nulla da togliere" | nessuna | `pulisci-<n>.txt`, `pulisci-push-<n>.*` |

Note per il controller:
- Ordine consigliato: prepara, v1, v2, v4, v5, (attesa), v6, v3, v7, v8, v9, raccogli, pulisci-sonde. v3, v7, v8 si possono ripetere senza effetti sulla rete (v3 e v8 fanno solo letture/fetch).
- Un modo ripetuto non perde nulla: le uscite precedenti diventano `*.prev-<tempo>`. Ripetere v1 crea una nuova PR (e la cache esiste già: V4 va letto sulla prima corsa).
- Le sonde `probe-verdict` di PR2 e delle PR di v5 tentano di salvare la stessa chiave di cache: avviso atteso, non errore.
- I commit sul pubblico sono solo sonde (nessun codice di tollgate): decisione 25.
- Il modo `raccogli` scrive «minuti non fatturati» per il pubblico: da confermare su GitHub; il privato non ha run.
- Un fatto non ottenuto va scritto «non determinato» con la causa (il modo lo fa quando manca un artefatto o un run non compare entro il tetto).

## Scostamenti dal piano
- Nessun TDD classico (script di shell con modo di controllo); la prova è la corsa `controlla`.
- `v1` produce anche i dati di V3, V4 (salvataggio), V6, V7, V8: `v3`, `v7`, `v8` sono riepiloghi sulle uscite già scaricate, con in più le letture di `v8` e il fetch di `v3`.
- Il commento dell'utente è scritto con `gh pr comment` (operazione ammessa); il commento del bot da `probe-verdict`.

## Suite e commit
`tests/run` (python3.11 e python3 3.13.5, `set -e`): exit 0, 1753 test OK nell'ultimo giro (468 s), nessun `__pycache__`, `git status` pulito dopo il commit.

---
# Aggiunta: V3b e V5b (secondo commit)

## Nuovi modi
- **v3b** (sul PRIVATO `ginz0ls/tollgate-p4-detect`, unica sonda sul privato): copia `probe-fetch.yml` in detect, commit e push su main (solo se c'è una differenza), apre una PR (ramo `p4-v3b-<ts>`), attende il run `probe-fetch`, scarica l'artefatto, chiude la PR. Uscite: `v3b-push-sonda.*`, `v3b-push.*`, `v3b-pr-create.*`, `v3b-pr.env`, `v3b-fetch-{runs,watch,view,download,runid}`, `v3b-fetch-artifacts-<id>/info.json`, `v3b-pr-close.*`, `v3b-riepilogo.txt`.
- **probe-fetch.yml** (`pull_request_target`, `contents: read`): checkout del predefinito con `persist-credentials: false` e `fetch-depth: 0`; `git fetch origin refs/pull/<n>/head` (n da `$GITHUB_EVENT_PATH`, nessuna espressione in `run:`) prima senza credenziali, poi con `GIT_CONFIG_COUNT/KEY_0/VALUE_0` (header `AUTHORIZATION: basic <base64 di x-access-token:$GH_TOKEN>`, `::add-mask::` sul base64, token solo da `env: GH_TOKEN`, mai stampato né in argv). `info.json`: `head_present_before_fetch` (il checkout con `fetch-depth: 0` potrebbe già avere l'oggetto, essendo il ramo della PR nello stesso repo: va letto per capire il valore degli altri due), `fetch_anon_rc`, `head_present_after_anon`, `fetch_auth_rc`, `head_present_after_auth`.
- **v5b** (pubblico): PR A da `p4-v5b-a-<ts>`, PR B da `p4-v5b-b-<ts>` costruito sopra la testa di A, entrambe verso main e aperte insieme; `GET commits/<testa A>/pulls` e `<testa B>/pulls` (fino a 4 tentativi); riepilogo con numero, `state`, `head.sha`, `base.ref`; poi chiude A e B. Uscite: `v5b-pr.env`, `v5b-pulls-testa-{a,b}.{out,err,rc,tentativi}`, `v5b-riepilogo.txt`, `v5b-pr-close-{a,b}.*`. Va lanciato prima che una PR venga unita (non unisce mai nulla).

## Scostamenti
- `open_pr` ora accetta il repo (`protected`/`detect`) e un ramo di partenza; `prepara` copia solo le quattro sonde del pubblico (non `probe-fetch`). `pulisci-sonde` toglie `probe-fetch.yml` da detect con lo stesso meccanismo (nessun cambiamento di codice).
- La regola «sonde solo sul pubblico» è rivista come da istruzione: sul privato, workflow solo `probe-fetch` e solo tramite `v3b`.

## Ordine aggiornato per il controller
prepara, v1, v2, **v5b**, v4, v5, (attesa delle probe-base dei push di v5), v6, v3, **v3b**, v7, v8, v9, raccogli, pulisci-sonde. (v5b prima di v5 e di ogni merge; v3b è indipendente e si può lanciare in qualunque momento dopo prepara.)

## Verifiche
`bash -n` ok; YAML di `probe-fetch.yml` valido; nessuna `${{ }}` in `run:` (controllato da `controlla`). Corsa `controlla` (14 modi): ok, 102 comandi gh finti, nessuno fuori dai due repo né vietato, tutte le uscite attese presenti, remoti nel banco locale. Uscita in `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/6196ff63-38d8-4a02-ada3-ddb16bd01d50/scratchpad/controlla-uscita2.txt`.

---
# Aggiunta: V4b (terzo commit)

Fatto da provare: dove si può scrivere una cache (nei job `workflow_run` il salvataggio risulta success ma viene negato).

## Sonde (le v4 restano)
Ogni sonda ha un passo `tag4b` che legge `.github/probe-v4b-tag` (`none` se manca; i passi v4b hanno `if: steps.tag4b.outputs.tag != 'none'`, quindi senza il file non fanno nulla).
- **probe-base** (push su main): scrive `probe-cache-v4b/value.txt` con `$GITHUB_SHA` e SALVA con `actions/cache/save@v4` (`continue-on-error`), chiave `probe-v4b-<tag>`. `info.json` riceve `v4b_tag` e `v4b_save` (esito del passo; ricordare che l'esito è success anche con scrittura negata: il messaggio sta nel log del run, che il controller legge con `gh run view --log` se serve).
- **probe-run** (pull_request) e **probe-verdict** (workflow_run): RIPRISTINANO la stessa chiave con `actions/cache/restore@v4` in `probe-cache-v4b`; `info.json` riceve `v4b_tag`, `v4b_cache_hit`, `v4b_matched_key`, `v4b_value` (contenuto di `value.txt` o `none`).

## Modo v4b
Scrive il tag (data e ora) in `.github/probe-v4b-tag`, commit e push su main; attende `probe-base` (`v4b-base`); apre una PR (`v4b-pr-create`, `v4b-pr.env`); attende e scarica `probe-run` (`v4b-run`) e `probe-verdict` (`v4b-verdict`); chiude la PR; scrive `v4b-riepilogo.txt` (per ogni `info.json`: `v4b_tag`, `v4b_save`, `v4b_cache_hit`, `v4b_matched_key`, `v4b_value`). Uscite: `v4b-push-main.*`, `v4b-push.env` (SHA e TAG), `v4b-{base,run,verdict}-{runs,watch,view,download,runid}`, `v4b-*-artifacts-<id>/`, `v4b-pr-close.*`. Tre run in serie, tetto 600 s ciascuno.
`pulisci-sonde` toglie ora anche `.github/probe-v4b-tag`. Il push su main fa partire anche altri workflow (nessun problema).

## Ordine aggiornato per il controller
prepara, v1, v2, v5b, v4, **v4b**, v5, (attesa delle probe-base dei push di v5), v6, v3, v3b, v7, v8, v9, raccogli, pulisci-sonde. v4b è indipendente da v1 e v4 (tag nuovo a ogni corsa).

## Verifiche
`bash -n` ok; YAML dei quattro workflow valido; nessuna `${{ }}` in `run:`. `controlla` (15 modi): ok, 119 comandi gh finti, nessuno fuori dai due repo né vietato, uscite attese presenti (anche `v4b-pr.env`, `v4b-push.env`, `v4b-riepilogo.txt`). Uscita in `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/6196ff63-38d8-4a02-ada3-ddb16bd01d50/scratchpad/controlla-uscita3.txt`. Limite: nella corsa finta i campi v4b sono `null` (gli artefatti sono finti).

---
# Step 3-4

- Letto da me, file per file, ogni esito di V1-V9, V3b, V4b, V5b nelle evidenze di `docs/verifiche/evidenze/gh-p4/` (non mi sono fidato del messaggio): tutti i fatti indicati dal controller sono confermati. Dettaglio e righe di conferma nel rapporto `docs/verifiche/2026-10-21-p4-verifiche.md` (tabella con 12 righe, versioni, repo, stato finale, minuti, sei righe «da correggere»).
- Fatti in più che ho trovato leggendo e scritto nel rapporto: `gh` sui runner è 2.102.0 (locale 2.46.0); `author.login` di `pr view` è `github-actions` senza `[bot]`; i check-run dei job `workflow_run` stanno sullo SHA della punta del predefinito (tre `verdict` accanto a `base`); la testa della PR era già nel clone prima del fetch in V3b (la prova regge sul codice d'uscita); `upload-artifact` rifiuta anche `sub/../keep.txt`; il campo `billable.total_ms` del privato vale 0 anche per 9 s; `sha_pinning_required` esiste in `actions/permissions`; l'indicizzazione di `commits/<sha>/pulls` può richiedere qualche secondo (nota per il Task 11).
- Controlli prima del commit: nessun token `gh[opsu]_` nelle evidenze (grep ricorsivo vuoto), nessun `__pycache__`. Le evidenze contengono l'hostname del runner nei file `link-assoluto` (dato innocuo, è l'esito di V8).
- `tests/run` non rilanciato: solo documenti ed evidenze, nessun codice né test toccato dall'ultimo giro verde.

## Correzione sul `tests/run` dello Step 4
Il commit `bae003e` è stato fatto prima di lanciare `tests/run` (errore mio: avevo dichiarato di saltarlo). Rilanciato dopo, senza toccare nulla: primo tentativo interrotto dal mio `timeout` di 1500 s (macchina carica, exit 124, nessun test fallito nell'output); secondo tentativo con tetto 3500 s: `tests/run` (python3.11 e python3) exit 0, «Ran 1788 tests in 782.045s, OK». Nessun amend: il commit resta com'è, i file committati non cambiano.

---
# Fix round 1

**I-1, guardia a lista di ammessi, una sola fonte.** Nuovo `spikes/gh-p4/ghguard.py`: la funzione `violation(args)` ammette solo queste coppie, con opzioni ed elenchi chiusi:
- `--version` (da solo); `auth status` (esattamente, niente `--show-token`);
- `repo create <uno dei due>` con solo `--public|--private` (esattamente una) e `--add-readme`; `repo clone <uno dei due> [dir] [-- -q]`; `repo view <uno dei due>`;
- `pr create|edit|close|merge|view|list|comment`, `issue create|close|comment|view|list`, `run list|view|download|watch`, sempre con `--repo`/`-R` (anche `--repo=`) uno dei due; `pr merge` rifiuta `--admin` e `--auto`;
- `api`: solo `--include`, `--paginate`, `--silent`, `--jq|-q <valore>` e un endpoint; **ogni altra opzione che cominci con `-` è rifiutata** (quindi `-XPOST`, `--method=POST`, `-fk=v`, `-F`, `--field=`, `--raw-field=`, `--input=`, `-H` in qualunque forma); l'endpoint deve stare sotto `repos/<uno dei due>` (il nome intero, non un prefisso), senza segmenti vuoti, `.` o `..` e senza `%2e`, `%2f`, `%5c`, `\`.
`guard_args` in bash chiama `python3 -I ghguard.py check -- <argomenti>`; `check_gh_log` chiama `python3 -I ghguard.py log <registro>`: stessa funzione, niente più due liste. Tolti da `run-p4-checks.sh` `repo_ok` e la vecchia logica.
Prova negativa in `controlla` (`check_negativi`): 45 comandi vietati (le forme del rilievo e altre: `api` con `--method=POST`, `-XPOST`, `-fstate=x`, `--field=`, `--raw-field=`, `--input=`, `-F`, `-H`, endpoint con `..`, `//`, `%2e%2e`, repo con nome prefisso; `run delete|cancel|rerun`, `pr review|ready|checkout`, `pr merge --admin`, `issue delete|transfer|pin`, `repo create` con `--source`, `--push`, altro repo, senza visibilità, con `--visibility`; `repo delete|edit|fork`; `auth login|refresh`, `auth status --show-token`; `secret`, `ssh-key`, `extension`, `pr|run list` senza `--repo`, altro repo): ognuno passato a `guard_args` si ferma, e lo stesso registro passato a `check_gh_log` dà una violazione per comando.
Sanità sui dati veri: i 146 comandi `gh` di `comandi.log` (esclusa l'annotazione «(controller…)» di una riga) sono tutti ammessi dalla nuova tabella.

**I-2, rapporto.** `docs/verifiche/2026-10-21-p4-verifiche.md:21`: scambiati i commit di pulizia; ora `pulisci-protected.txt` = `a0c1e5f`, `pulisci-detect.txt` = `349020d` (riletti sui file). Controllati anche gli altri SHA del rapporto (`76d561a`, `0fbc78d`, `513f61b`, `5eb103d`, `cea7a38`, `216898c`, `e21bc2c`, `32fb324`, `c03b433`): compaiono nelle evidenze citate.

**Verifiche.** `bash -n spikes/gh-p4/run-p4-checks.sh`: 0. `controlla` (15 modi): ok, 119 comandi finti ammessi, «guard_args: 45 fermati su 45; check_gh_log: 49 violazioni su 45» (alcuni comandi vietati hanno più di una violazione), remoti nel banco, uscite attese presenti (uscita in `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/6196ff63-38d8-4a02-ada3-ddb16bd01d50/scratchpad/controlla-uscita4.txt`). `tests/run`: vedi sotto.
`tests/run` (python3.11 e python3): exit 0, «Ran 1788 tests in 418.223s, OK», lanciato prima del commit del fix round 1; nessun `__pycache__`.
Nota: il commit 48b624b conteneva per errore `spikes/gh-p4/__pycache__` (creato da un import senza `-B` nella mia verifica); tolto con un commit nuovo (`git rm`), nessun amend.

---
# Fix round 2

**I-1 residuo, `pr|issue|run` a elenco chiuso** (`spikes/gh-p4/ghguard.py`, riscritto; `guard_args` e `check_gh_log` lo usano ancora entrambi).
- Per ogni coppia (comando, sottocomando) una specifica con opzioni con valore (tipo del valore), flag e posizionali. Solo le opzioni che lo script usa (più quelle minime della decisione 25): `pr create` (`--base --head --title --body`), `pr edit`, `pr close`, `pr merge` (esattamente una tra `--merge|--squash|--rebase`, niente `--admin`, `--auto`, `--delete-branch`), `pr view`/`pr list` (`--json --state --limit`), `pr comment` (`--body`; `--body-file` vietato), `issue create|close|comment|view|list`, `run list` (`--workflow --limit --json`), `run view` (`--json --log --log-failed`), `run watch` (`--exit-status`), `run download` (`-D|--dir`, `-n|--name`).
- Esattamente un `--repo`/`-R`, in qualunque forma (`--repo X`, `--repo=X`, `-R X`, `-RX` attaccato), con valore uno dei due repo; due specifiche, anche uguali, sono rifiutate.
- Posizionali: numeri (run e issue) oppure numero o nome di ramo semplice `[A-Za-z0-9._/-]`, senza `:`, `#`, `..`, senza trattino iniziale (PR); URL e `altro/x#1` cadono.
- `-D` (anche attaccato) e la cartella di `repo clone` devono essere percorsi assoluti normalizzati sotto `P4_OUT` e `P4_WORK` (lo script li esporta da `$OUT` e `$WORK`).
- Endpoint di `api`: caratteri solo `[A-Za-z0-9._~/?&=%:,@+-]`, nessun `..`, `//`, segmento `.`, `%2e|%2f|%5c|%00` sull'intero endpoint, query compresa.
- Minori: nuova modalità `ghguard.py comandi <comandi.log>` (formato `<ora> gh <argomenti>`; legge i valori con spazi in modo tollerante; esclude con motivo le righe annotate «(controller…)», comandi a mano non dello script); commento nel modulo sulle scritture `gh api` della decisione 25 (`POST statuses`, `PUT|DELETE branches/main/protection`): non servono a questo script e restano vietate qui, da aggiungere come coppie esplicite con endpoint fisso se servissero.
- `controlla`: la prova negativa passa da 45 a 71 comandi vietati (aggiunti tutti gli esempi della ri-revisione: `pr view` con URL e con `altro/x#1`, `-Raltro/x`, doppio `--repo`, `--repo=altro/x`, `--body-file`, `-D /etc`, `-D` con `..`, `api …?x=1/../../`, `%2e%2e`, `//`, `./`, `pr merge` senza o con due modalità, `--delete-branch`, `run view --exit-status`, `run download -n ../x`, `repo clone` fuori da `P4_WORK`, ecc.) e una prova positiva (10 comandi legittimi devono passare). Nuovo passo: tutti i comandi veri di `docs/verifiche/evidenze/gh-p4/comandi.log` passano la guardia (138 controllati, 9 righe «(controller…)» escluse); il passo è riproducibile con `python3 -B -I spikes/gh-p4/ghguard.py comandi docs/verifiche/evidenze/gh-p4/comandi.log`.
- Tutti gli `python3` dello script girano con `-B`; nessun `__pycache__` creato.

**Verifiche.** `bash -n spikes/gh-p4/run-p4-checks.sh`: 0. `controlla` (15 modi): ok; «guard_args: 71 fermati su 71; check_gh_log: 75 violazioni su 71» (alcuni vietati hanno più violazioni), «comandi legittimi ammessi: 10 su 10», 138 comandi veri ammessi, remoti nel banco, uscite attese presenti (uscita: `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/6196ff63-38d8-4a02-ada3-ddb16bd01d50/scratchpad/controlla-uscita5.txt`).
`tests/run` (python3.11 e python3): exit 0, «Ran 1820 tests in 405.567s, OK», lanciato prima del commit del fix round 2.
