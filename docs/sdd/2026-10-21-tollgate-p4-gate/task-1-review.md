# Revisione del Task 1 (P4): verifiche reali su GitHub

Pacchetto: `review-t1-b40284e..bae003e.diff` (4 commit: d2378bd, b8987b2, 6b4a1b4, bae003e). Evidenze controllate a campione in `docs/verifiche/evidenze/gh-p4/`. Nessuna rete, nessun `gh`, suite non rilanciata.

### Aderenza

- ✅ Decisione del controller «proprietario fisso `ginz0ls`, nessun `gh api user`»: `spikes/gh-p4/run-p4-checks.sh:25-27` (OWNER/PROT/DET fissi), `guard_args` rifiuta `user` e `/user` (`:53`), `check_gh_log` lo ricontrolla (`:708`). `comandi.log` non contiene `api user`.
- ✅ Repo ammessi: `repo_ok` (`:106`), endpoint `repos/<uno dei due>` (`:148-151`), `--repo` obbligatorio per `pr|issue|run` (`:59`), `check_remote` prima di ogni `git` di rete. In `comandi.log` ogni `gh api` nomina solo i due repo; i soli `repo create|clone` sono i quattro attesi; `auth status` (2) e `pr merge` (3, solo sul pubblico). Nessuna operazione vietata eseguita in realtà.
- ✅ Sonde solo su `protected`, eccetto V3b su `detect` (`probe-fetch.yml`, installata solo da `modo_v3b`, `:403-421`). `pulisci-sonde` tocca entrambi i repo con un commit senza riscrivere la storia (`pulisci-protected.txt`, `pulisci-detect.txt`).
- ✅ Nessuna cancellazione di uscite: `rot` rinomina in `.prev-<tempo>` (`:171-175`, 17 file `.prev` presenti); l'unico `rm` è `git rm` delle sonde. Stdout, stderr e rc in file distinti (`gh_call`, `git_call`). Comandi manuali del controller annotati in `comandi.log` («a mano»).
- ✅ Nessuna `${{ }}` nelle righe `run:` (controllo `check_workflows`; riletti a mano i cinque YAML: le espressioni stanno solo in `with:` e `env:`). Artefatti con chiavi e valori non testuali; il corpo del commento non viene mai salvato.
- ✅ Segreti: `grep` su tutte le evidenze per `gh[opsur]_…` e `github_pat_` è vuoto; `prepara-auth.out` ha il token mascherato (`gho_****`); nei log dei job compare solo `AUTHORIZATION: basic ***` (checkout). In `probe-fetch.yml:1006-1010` il base64 è calcolato in `$(…)`, mascherato con `::add-mask::` prima dell'uso, passato solo con `GIT_CONFIG_*` come variabili d'ambiente del comando (mai in argv); `fetch-auth.log` non contiene l'header.
- ✅ Tutti gli esiti V1-V9, V3b, V4b, V5b del rapporto sono sostenuti dai file citati (controllati uno per uno, dettaglio sotto), tranne gli errori segnalati nei rilievi.
- ✅ Rapporto con tabella `Id | Fatto | Esito | Evidenza | Conseguenza`, versioni (`gh` locale e runner, `claude`), minuti (32 run da 414 s sul pubblico, 1 da 9 s sul privato: `raccogli-minuti.txt`, `raccogli-timing-detect-39631102348.out`), sei righe «da correggere nel Task N».
- ⚠️ Non verificabile dal diff: che le `Ruling:` corrispondenti siano nel ledger (il rapporto dice di sì); il commit bae003e senza `tests/run` (nota del controller, non contato).

Verifiche campione sulle evidenze (file citato, esito):
- V1: `v1-pr-view-comments.out` (`author.login` = `github-actions`, `NONE`), `v1-api-comments.out`/`v1-login.txt` (`github-actions[bot]`, `Bot`), `probe-verdict-info/info.json` (id 41898282); `v1-pr-list.out`, `raccogli-pr.out` (`mergedAt` valorizzato per #5-#7, `CLEAN`/`UNKNOWN`).
- V2: `v2-detect.out` in `od -c`: prima riga con `\n`, intestazioni con `\r\n`, corpo senza a capo finale; `v2-detect.err`/`.rc`, `v2-protected.err`, `v2-detect-senza-include.*`. Esatto come scritto.
- V3: `v1-target-artifacts-*/probe-target/event-keys.json` e `info.json` (`fetched_equals_head: true`), `v1-verdict-artifacts-*/probe-verdict-info/event-keys.json` (`path`, `event`, `pull_requests[]` con `base`).
- V3b: `v3b-fetch-artifacts-*/probe-fetch/info.json` (`fetch_anon_rc` 128, `fetch_auth_rc` 0, `head_present_before_fetch: yes`), `fetch-anon.log`, `fetch-auth.log`. Il limite «la presenza dell'oggetto non prova nulla, vale il codice d'uscita» è dichiarato bene.
- V4/V4b: `v4-log-39630168903.txt` (`Cache mode: read`, `cache write denied: token has no writable scopes`, `Cache save failed` ma passo `success`), `v4-caches.out` (`total_count: 0`), `v4b-riepilogo.txt` (hit `true`, valore = `32fb324…` = SHA di `v4b-push.env`), `Cache mode` write/read nei sei log.
- V5/V5b: `v5-riepilogo.tsv`, `v5-*.tentativi` (4 per il diretto, 2 per merge/squash/rebase, 1 per il commit della PR), `v5b-riepilogo.txt` (testa di A restituisce #2 e #3).
- V6: `v6-riepilogo.txt` (creator `github-actions[bot]` per base, target, verdict; `verdict` ×3 sullo SHA del push di v4, nessun `verdict` sullo SHA della PR1; `app.id` 15368).
- V7: `v7-riepilogo.txt` (2.102.0, `image_os` ubuntu24, due versioni di immagine). V8: i due messaggi `Invalid pattern` in `v4-log-39630136017.txt:197,209`, `Artifact not found` in `v4-log-39630168903.txt:143,159`, `v8-find.txt` (solo file normali), `link-assoluto` = hostname del runner. V9: `v9-*.out`.

### Punti di forza

- Guardie a due livelli (preventiva in `guard_args`, a posteriori in `check_gh_log` sul registro del `gh` finto) e prova a mano di 9 casi negati; il modo `controlla` copre tutti i 15 modi e controlla anche remoti dei cloni, YAML e uscite attese.
- Onestà sui limiti: V3b (oggetto già presente), V4 (passo `success` con scrittura negata), «non provato su fork». Le conclusioni del controller (V3b, V4b, V5b) sono state le più utili: V4 e V5b smentiscono davvero decisioni 12 e 5.
- Le sonde non portano codice di tollgate né testo non fidato; `persist-credentials: false` e permessi minimi ovunque; la chiave di cache con tag evita risultati falsi in ripetizione.
- Tutti gli esiti riportati tornano con le evidenze; le conseguenze per il piano sono giuste (vedi sotto per i due ritocchi).

### Rilievi

**Critical:** nessuno.

**Important**

- **I-1: la guardia non è una lista di ammessi, e il testo del report la descrive più stretta di com'è** (`spikes/gh-p4/run-p4-checks.sh:41`, `:45-57`, `:692-720`). (a) Il divieto di scrittura di `gh api` confronta solo token esatti: `--method=POST`, `-XPOST`, `-fstate=x`, `--field=…`, `--raw-field=…`, `--input=…` passano, e ognuno rende la chiamata una scrittura; il rapporto dell'implementatore dichiara «api solo in lettura». (b) Per `pr|issue|run` nessun sottocomando è controllato: passerebbero `gh run delete|cancel|rerun`, `gh pr review|ready|checkout|lock`, `gh issue delete|transfer|pin`, fuori dalla decisione 25 (ammessi: `pr create|edit|close|merge|view|list|comment`, `issue create|close|comment|view|list`, `run list|view|download|watch`). (c) `gh repo create` accetta ogni opzione tranne `--visibility` (es. `--source`, `--push`, `--homepage`, `--template`). (d) un endpoint come `repos/ginz0ls/tollgate-p4-protected/../../user` supera il confronto per prefisso. Anche `check_gh_log` ripete gli stessi buchi (stessa lista `WRITE_OPTS`, nessun controllo dei sottocomandi, `--repo=…` non letto). Lo script oggi non usa nulla di tutto ciò, quindi nessun danno avvenuto (verificato su `comandi.log`), ma è esattamente il rischio per cui la guardia esiste. Correzione: tabella di ammessi per coppia (`pr create|edit|close|merge|view|list|comment`, …), rifiuto di ogni argomento che inizi per `-X`, `-f`, `-F`, `--method`, `--field`, `--raw-field`, `--input` (anche con `=` o attaccato), rifiuto di `..` nell'endpoint, whitelist di opzioni per `repo create` (`--public|--private|--add-readme`); riusare la stessa tabella in `check_gh_log` (oggi sono due liste da tenere allineate a mano).
- **I-2: errore di fatto nel rapporto, contraddetto dal file che cita** (`docs/verifiche/2026-10-21-p4-verifiche.md:21`, sezione «Repo e stato finale»). Il rapporto assegna a `protected` il commit `349020d` e a `detect` il commit `a0c1e5f`; `pulisci-protected.txt` contiene `a0c1e5f…` e `pulisci-detect.txt` contiene `349020d…`: i due sono scambiati. Correggere.

**Minor**

- **M-1: V4 è scritto più generale di quanto provato** (rapporto, riga V4 e riga «da correggere» della decisione 12). La prova è su un `workflow_run` innescato da un workflow `pull_request`, su repo pubblico; il privato (`detect`) e un `workflow_run` innescato da `push` non sono stati provati. Per il disegno basta (`tollgate-verdict` è proprio del primo tipo), ma conviene scrivere l'ambito esatto, e annotare per il Task 16 che il privato va riletto (il messaggio `token has no writable scopes` suggerisce una regola legata all'evento). Inoltre «entrambe le corse, 15:56 e 16:23» cita il solo `v4-log-39630168903.txt`: il 16:23 è `v4b-log-verdict-39634363221.txt:31`, da aggiungere all'evidenza.
- **M-2: `wait_run` può agganciare un run estraneo** (`run-p4-checks.sh:195-207`). `since` parte 2 minuti prima dell'attesa e il ripiego accetta «qualunque run creato dopo `since`» (per target e verdict); nel flusso del controller più PR ravvicinate (v5, v5b, v4b) producono verdict concorrenti. Nei dati questo non è avvenuto (v1: PR 1, v4b: PR 8, coerenti con gli `info.json`), ma lo script non lo verifica. Correzione: dopo il download confrontare `pr_number` di `probe-verdict-info/info.json` (e `number` di `event-keys.json`) con `PR_NUM` e scrivere «non determinato» se differiscono.
- **M-3: `merge_pr` ripete `gh pr merge` fino a 5 volte** (`:400-407`): se il primo tentativo ha unito ma ha dato errore di rete, il secondo fallisce con «già unita» e il modo segna «merge fallito» pur avendo unito. Non successo; basta leggere lo stato (`pr view --json state`) prima di ripetere.
- **M-4: conseguenza V6 incompleta** (rapporto, riga V6). Oltre al nome univoco del job di `tollgate-base`, vale lo stesso per ogni lettore dei check-run sulla punta del predefinito (sentinel, `protect.sh`): tutti i `verdict` dei `workflow_run` si accumulano lì, quindi vanno cercati per nome esatto e `app.id`, mai «il primo check-run». Una riga in più al Task 12/11.
- **M-5: nelle evidenze finiscono percorsi locali** (`v8-find.txt` contiene `/home/crucco/MEGA/BIZ/…` e l'hostname del runner nei `link-assoluto`): innocui, ma il repo è condiviso; se si vuole evitarlo, `find -printf '%P'` relativo.
- **M-6: copertura dell'esito V5 per il rebase**: il rapporto cita il commit riscritto `5eb103d` ma la PR #7 non è provata anche per il commit originale della PR (come invece per il merge, `0fbc78d`). Non cambia la decisione 16.

### Valutazione

**Qualità del task:** Da correggere (correzioni piccole e senza impatto sui fatti).
**Motivo:** I fatti e le conclusioni del rapporto sono sostenuti dalle evidenze e le conseguenze per il piano sono giuste, nessuna operazione vietata è stata eseguita e nessun segreto è trapelato. Restano da sistemare la guardia di `guard_args`/`check_gh_log`, che è più permissiva di quanto dichiarato (I-1), e lo scambio dei due commit di pulizia nel rapporto (I-2).
