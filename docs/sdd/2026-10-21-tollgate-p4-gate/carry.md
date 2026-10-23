# Decisioni del controller portate nei task (carry)

Ogni voce nomina i task a cui si applica. Prima di lanciare un task il controller copia nel dispatch tutte le voci che lo nominano, in qualunque sezione.

## Task 1
- (Task 1) Proprietario fisso `ginz0ls` nello script: nessun `gh api user` (vietato dalla decisione 25).
- (Task 1) Sonde (workflow) solo su `ginz0ls/tollgate-p4-protected`; su `ginz0ls/tollgate-p4-detect` solo GET dell'API (V2 con 403, V9). `pulisci-sonde` resta valido su entrambi (sul privato non trova nulla da togliere e non fa commit vuoti).
- (Task 1) Clonare e fare fetch dei due repo è ammesso; i cloni di lavoro stanno in `/tmp/tollgate-p4/gh/` (non sono uscite), le uscite solo in `docs/verifiche/evidenze/gh-p4/` del worktree (o nella cartella data da una variabile d'ambiente nel modo `controlla`), mai cancellate.
- (Task 1) Modo `controlla`: nessuna rete. `PATH` con un `gh` finto che registra gli argomenti, remoti git verso repo nudi locali (base dell'URL in una variabile), uscite in una cartella temporanea; alla fine controlla che ogni comando registrato nomini solo i due repo e nessun `gh api user`, `gh auth` diverso da `status`, `gh repo delete`, `gh secret`, `--visibility`.
- (Task 1) Modi separati e ripetibili: ogni `vN` scrive i suoi file e termina; le attese sui run (`gh run list --json` + `gh run watch <id>`) stanno in una funzione dello script con un tetto di tempo. Ogni chiamata salva stdout, stderr e codice d'uscita in file distinti (V2 ne ha bisogno).
- (Task 1) Nessuna `${{ }}` nelle righe `run:` delle sonde (stessa regola dei workflow veri, decisione 17): i valori si leggono da `$GITHUB_EVENT_PATH` con `jq`/`python3`; le espressioni solo in `with:`, `if:`, `env:`. Le sonde salvano le chiavi e i valori non testuali (SHA, numeri, nomi di ramo e di file) in un artefatto, non i corpi.
- (Task 1) Il rapporto `docs/verifiche/2026-10-21-p4-verifiche.md` (Step 3) lo scrive lo stesso implementatore in un secondo giro, dalle uscite che il controller avrà raccolto; al primo lancio solo script, sonde e commit degli script.
- (Task 1) V3b (scan D2), sul privato `ginz0ls/tollgate-p4-detect`: sonda `probe-fetch.yml` (`pull_request_target`, permessi minimi `contents: read`), checkout del predefinito con `persist-credentials: false` e `fetch-depth: 0`; poi `git fetch origin refs/pull/<n>/head` (n dall'evento) prima senza credenziali, poi con il token in `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=http.https://github.com/.extraheader`, `GIT_CONFIG_VALUE_0="AUTHORIZATION: basic <base64 di x-access-token:$GH_TOKEN>"` (token da `env: GH_TOKEN: ${{ github.token }}`, mai stampato, mai nella riga di comando); salvare in artefatto i due codici d'uscita e se l'oggetto della testa è presente dopo ciascun fetch. Serve una PR sul privato. È l'unica sonda sul privato.
- (Task 1) V5b (scan D7), sul pubblico: PR A da ramo `a`, PR B da ramo `b` costruito sopra la testa di `a`, entrambe verso `main`, aperte insieme; `GET commits/<testa di a>/pulls` e `GET commits/<testa di b>/pulls` salvati (numero, `state`, `head.sha`, `base.ref`).

## Dallo scan pre-flight (D1-D21; testo completo delle ruling nel ledger)

### Task 2
- (Task 2, D1) `violations.diff_violations(..., *, components, approved_spec: tuple[str, str] | None = None)`: parametro facoltativo nuovo; `finishcheck` calcola `approved_spec` con `l2tree` come oggi (`_approved_spec_blob`) e lo passa; gli hook passano `None`. `tollgate_core` non importa mai `tollgate_gate` né `tollgate_flow` (salvo `cli.py`). `finishcheck._own_document` sparisce come dice il piano.
- (Task 2, D14) `diffcheck.diff_check(...) -> DiffCheck(violations: list[Violation], watched: list[str])` con gli stessi parametri di `diff_findings`; `diff_findings(...) = diff_check(...).violations` (firma del piano intatta). `guard_config` e `is_docs_md` si spostano in `diffcheck` e restano importabili da `violations` (li usano `tollgate_hooks/context.py` e `_common.py`). Il controllo del collegamento simbolico di `is_registered_plan` resta in `violations`; in `diffcheck` una riga di docstring spiega perché non serve (blob uguale a `plan_sha`).
- (Task 2, D15) `ghcli.api(paginate=True)` senza `jq` → `ValueError`; con `jq`, `ApiResult.data` è la lista dei valori decodificati (come `run_json_lines`).
- (Task 2, D17f) `tests/test_analysis_isolation.py`: `tollgate_analysis` non può importare né nominare `tollgate_gate`.
- (Task 2, D20) Una funzione sola `git._check_ref(ref)` (riferimento che comincia con `-` → `GitError`, nessun processo lanciato) usata da **ogni** funzione di `tollgate_core.git` che riceve un riferimento (`ls_files_at`, `text_at`, `blob_at`, `exists_at`, `rev_list`, `changes`, `diff_size`, …); `test_refs_starting_with_dash_refused` le copre tutte.
- (Task 2, D21a) `test_gate_runtime_has_no_db` scopre dinamicamente i moduli di `tollgate_gate` (così copre anche quelli dei task successivi).
- (Task 2, scan) `tollgate_core.verify` conserva gli alias privati (`_run_one`, `_report_path`) oltre ai nomi pubblici; `ghcli.GhError` e `tollgate_flow.gh.GhError` sono **la stessa classe**.
- (Task 2, D2) `tollgate_core.git.fetch_ref(repo, ref, *, token: str | None = None)`: con `token` passa l'intestazione `http.https://github.com/.extraheader` = `AUTHORIZATION: basic <base64 di x-access-token:token>` solo tramite le variabili d'ambiente `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0` del processo figlio, mai negli argomenti né in `.git/config`; `_check_ref` vale anche qui. (Forma confermata o corretta da V3b prima del lancio.)

### Task 3
- (Task 3, D10) Aggiornare al caso (a) `tests/test_approvals.py::LocateTest.test_locate_own_then_other_issue` e `tests/test_audit_prepare.py::SpecApprovalOfLaterSliceTest.test_helper_own_stale_approval`; `tests/test_l2tree.py` è un file **nuovo** (testa `tollgate_gate.l2tree` e il re-export di `tollgate_flow.l2tree`).
- (Task 3, D17a) `prref.issue_from_branch` è la sola fonte di `^tg/(\d+)-`: `tollgate_hooks/_common.py:16` e `tollgate_flow/closing.py:24` la usano, comportamento invariato (i loro test esistenti devono passare).

### Task 4
- (Task 4, D3) `prblock.FIELDS` riceve in coda `tasks_over` e `skills_absent` (difetto: liste vuote) e i rilievi accettano il campo `blocking`; `prblock.build` li accetta. Il Task 13 li riempie da `openpr.facts`. Aggiornare i test di `test_prblock.py` che confrontano l'elenco dei campi.
- (Task 4, D6) Violazione `base_ids`: `path` derivato dall'identificativo `classname::name` (il `classname` se contiene `/`; altrimenti modulo con i punti → percorso `.py`); violazioni raggruppate per `path`; copertura con `waivers.covers` (file o pattern, **tutti** gli identificativi).
- (Task 4, D13) Test in più: `test_plan_sha_absent_is_red`, `test_l0_without_plan_over_thresholds_is_red`. Chiave `task_over_max` in `GROUPS` con valore `"info"`.
- (Task 4, D17e) «`plan_sha` presente nella storia della testa» = `git log -n 1 --format=%H --find-object=<plan_sha> <testa> --` non vuoto, con una funzione in `tollgate_core.git` (non `cat-file -t`).
- (Task 4, D5) Una voce di `results.json` per i `setup` (nome `setup` o `profile:<p>:setup`) con `state = "red"` è trattata da `evaluate` come comando del gate rosso.

### Task 5
- (Task 5, D13) `test_every_group_key_is_produced`: ogni chiave di `attention.GROUPS` è prodotta da almeno un caso di `evaluate`, oppure sta in un insieme esplicito di chiavi prodotte altrove (per esempio `sentinel_open`), ognuna con il motivo in un commento.
- (Task 5, D17b, h) I file di tollgate vengono da `tollgate_analysis.protected.TOLLGATE_FILES` / `is_tollgate_file` (nessuna lista ripetuta). Due funzioni con nomi distinti: file di tollgate cambiati rispetto alla base del lavoro (locale, `guard_local`) e rispetto alla punta del predefinito (gate); un test ciascuna.

### Task 6
- (Task 6, D17c) Una sola costante `prbody.MAX_BODY`; `comment` la importa (niente `comment.MAX_BODY` separata, o al più un alias dello stesso oggetto).
- (Task 6, D19) Il testo non fidato dei diff sta solo in `Item.data`; `comment.render` non ha i parametri `plan_diff` e `approval_diff`.

### Task 7
- (Task 7, D4) `--publish` dei sottocomandi `gate` si rifiuta (messaggio, uscita non zero) se `GITHUB_ACTIONS` non vale `true`; il guardrail locale nega `tollgate gate … --publish` (regole su Bash di `tollgate_hooks`, come i comandi riservati di `cli_calls`), con test.
- (Task 7, D5) `gate run` esegue prima i `setup` (globali e dei profili attivi, configurazione della punta del predefinito), poi i comandi del gate; un `setup` fallito → voce `results.json` con `state = "red"`; i comandi del gate dopo un `setup` fallito non girano (voce `red` con motivo).
- (Task 7, D8) `gate base-ids` riceve `--root <cartella>`: la CLI viene dal checkout del predefinito, l'albero calcolato è quello del checkout in `--root` (merge-base), configurazione della punta del predefinito.
- (Task 7, D21c) `tollgate_gate.cli.main` trasforma `GhError`, `GitError`, `ConfigError`, `OSError` e `ValueError` di ingresso in messaggio e uscita non zero, un test ciascuna; ogni task successivo che aggiunge un sottocomando ne eredita la gestione.

### Task 8
- (Task 8, D2) Il `git fetch` della testa usa `tollgate_core.git.fetch_ref(..., token=$GH_TOKEN)`; mai il token negli argomenti.
- (Task 8, D17b) File di tollgate da `protected.TOLLGATE_FILES`.

### Task 9
- (Task 9, D2) Come Task 8 per il fetch.
- (Task 9, D7) `shared_sha_prs` conta solo le PR aperte verso il predefinito con `head.sha == sha`.
- (Task 9, D12) `tests/fakegh.py` tra i file del task (risposte nuove che usa).
- (Task 9, D16) `github.issue`: risposta con chiave `pull_request` → rosso «#M è una PR, non un'issue»; `state` in maiuscolo; test `test_closes_a_pr_number_is_red`.

### Task 10
- (Task 10, D12) `tests/fakegh.py` e `tests/test_start.py` tra i file: `test_start.py:300-305` va riscritto per `open_sentinel_issues`.

### Task 11
- (Task 11, D2) `fetch-depth: 0` in guard, verdict, sentinel, base (dove serve `merge-base` o diff); token per il fetch in `env: GH_TOKEN: ${{ github.token }}`, letto da Python.
- (Task 11, D8) Job `base` di `tollgate-run`: checkout del predefinito (CLI) con `persist-credentials: false` e checkout di `merge-base` in una sottocartella; `gate base-ids --root <sottocartella>`.
- (Task 11, D18b) `test_names_match_gate_files` controlla anche che `name:` di ogni workflow coincida col nome del file senza estensione (lo usa `workflow_run.workflows`).

### Task 13
- (Task 13, D11) Riscrivere `test_prblock.py` (`facts()`, `SPEC_ORDER`) e `test_fixtask.py:205-265` (commenti con `author.login` in `BOT_LOGINS`, marcatore con SHA, `gate:<sha del marcatore>`). `subagents.finish` e l'operazione `subagent_finish` accettano `size_reason: str | None = None`, altri chiamanti invariati. `events.EVENT_TYPES` riceve `skills_absent`. `size_reason` nel blocco = l'ultimo **non nullo** tra gli eventi `subagent_stop` del task.
- (Task 13, D17d) `openpr` espone una funzione pubblica per le etichette e `finishcheck` la usa.

### Task 15
- (Task 15, D18a) `test_skill_contract.py`: i sottocomandi `gate` citati si verificano contro `tollgate_gate.cli.build_parser()`, gli altri contro `tollgate_core.cli.build_parser()`.
- (Task 15, D21b) La skill `finish` distingue le righe di `attenzione` («da leggere», «informative») da quelle `[sì]`/`[no]`.

### Task 17
- (Task 17, D9) Rev 25: nomi `profile:<p>:<c>` del codice in 9.1-9.2 al posto di `<profilo>.<comando>`; `task_over_max` con `size_reason` informativo; spec 5 «Dove sta l'approvazione» riscritta per il caso (a) della decisione 22; 3.1 con `init --propose|--update` e i sottocomandi `gate run|evaluate|guard|base-ids|sentinel`; D4 (`--publish` solo in Actions) e D5 (`setup` nel gate), D7 (`head.sha`), D17e (`--find-object`).

## Dagli esiti del Task 1 (V1-V9; evidenze in `docs/verifiche/evidenze/gh-p4/`, rapporto `docs/verifiche/2026-10-21-p4-verifiche.md`)

- (Task 2, 8, 13, fakegh) V1: `ghcli.BOT_LOGINS = ("github-actions[bot]", "github-actions")` — REST (`GET issues/<n>/comments`) dà `user.login = "github-actions[bot]"` con `user.type = "Bot"`; `gh pr view --json comments` dà `author.login = "github-actions"`. `tests/fakegh.py` usa le stesse due forme a seconda della via.
- (Task 2, 12) V2: `gh api --include` su 403/404 scrive su stdout la riga di stato `HTTP/2.0 403 Forbidden` (terminata da `\n`), poi le intestazioni terminate da `\r\n`, una riga vuota `\r\n`, poi il corpo JSON (senza a capo finale); codice d'uscita 1; stderr `gh: <message> (HTTP <codice>)`. `ghcli.api(include=True)` legge il codice dalla prima riga (`HTTP/<versione> <codice> …`), il corpo dopo la prima riga vuota (accetta `\r\n\r\n` e `\n\n`), e non tratta l'uscita non zero come errore quando la riga di stato c'è. Senza `--include` e con errore lo stdout è il solo corpo JSON. Il gh finto riproduce questa forma esatta.
- (Task 8, 9, 11) V3: i campi dell'evento sono quelli presunti dal piano: `pull_request_target` → `number`, `action`, `pull_request.head.sha`, `.head.ref`, `.head.repo.full_name`, `.base.ref`; `workflow_run` → `workflow_run.path` (`.github/workflows/<file>.yml`), `.event` (`pull_request`), `.head_sha`, `.head_branch`, `.conclusion`, `.id`, `.pull_requests[]` con `number`, `base.ref`, `base.sha`, `head.ref`, `head.sha` (nessun `head.repo`).
- (Task 2, 8, 9, 10, 11) V3b: sul privato `git fetch origin refs/pull/<n>/head` dopo un checkout con `persist-credentials: false` fallisce (128); con `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=http.https://github.com/.extraheader`, `GIT_CONFIG_VALUE_0=AUTHORIZATION: basic <base64 di x-access-token:<token>>` riesce (0). Ruling D2 confermata: `git.fetch_ref(..., token=...)` così, token da `GH_TOKEN`.
- (Task 7, 9, 10, 11, 17) V4: i job `workflow_run` hanno «Cache mode: read»: `tollgate-verdict` **non salva mai** in cache (niente `actions/cache/save`, niente `--head-ids-out`, niente condizioni di salvataggio della testa); solo `tollgate-base` (push) salva `tollgate-ids-<albero>`. Review Focus 7: `test_head_ids_cached_only_on_success` diventa `test_verdict_never_writes_cache`. Rev 25: limite «identificativi della testa in cache» tolto da 1.2; 9.1 riga `tollgate-verdict` senza «Mette in cache … della testa»; 9.5 una suite della base per merge. (V4b: lettura della cache di `push` da `pull_request` e `workflow_run`, in corso.)
- (Task 9, 10) V5: `GET commits/<sha>/pulls` per un commit portato da merge, squash o rebase restituisce la PR unita (`state: closed`, `merged_at`, `base.ref`); per un push diretto `[]`; per un merge con commit di merge, sia il commit di merge sia il commit del ramo elencano la PR. V5b: per la testa di una PR elenca anche le PR impilate che la contengono (ruling D7: filtrare `head.sha == sha`).
- (Task 10, 12) V6: stati scritti con `GITHUB_TOKEN` da job `push` e `pull_request_target` hanno `creator.login = "github-actions[bot]"`; il check-run porta come `name` il **nome del job** (chiave del job o `name:` del job), `app.id = 15368`, `app.slug = "github-actions"`. I check-run dei job `workflow_run` stanno sullo SHA della punta del predefinito: `protect.sh` filtra per il nome esatto del job di `tollgate-base`, che deve essere unico tra i cinque workflow (per esempio job `tollgate-base`; i job degli altri workflow con nomi diversi).
- (Task 11) V7: sui runner `ubuntu-latest` `gh` è 2.102.0 e `env: GH_TOKEN: ${{ github.token }}` basta. Il codice resta compatibile con gh 2.46 (niente `--slurp`), perché la stessa CLI gira in locale.
- (Task 7, 16) V8: `upload-artifact@v4` rifiuta i percorsi con `..` (sia fuori sia dentro la cartella di lavoro: il passo fallisce); segue i collegamenti simbolici, anche assoluti, e li carica come file normali (il contenuto del bersaglio); `download-artifact@v4` estrae sotto `path:`. `artifacts.validate` resta com'è (difesa in profondità); il caso «`../`» del criterio 10 si costruisce con un `report` di `results.json` fuori da `junit/` (decisione 13).
- (Task 12) V9: `GET repos/<o>/<r>/actions/permissions` → `{"enabled": true, "allowed_actions": "all", "sha_pinning_required": false}` su entrambi i repo.
- (Task 7, 9, 10, 11) V4b: una cache salvata da un job `push` sul predefinito (`tollgate-base`) si ripristina in un job `pull_request` (`tollgate-run`, job `base`) e in un job `workflow_run` (`tollgate-verdict`). Il salvataggio su una chiave esistente fallisce: `tollgate-base` salva solo se il ripristino della stessa chiave non ha trovato nulla.
- (Task 10) V5: `GET commits/<sha>/pulls` subito dopo un merge può restare vuoto per qualche secondo (1-2 tentativi nelle prove): `gate sentinel` rilegge un elenco vuoto con una breve attesa (per esempio 3 tentativi a 5 s, iniettabili nei test) prima di dichiarare «merge non verificato».
- (Task 11, 12) V6, dalla revisione del Task 1: chi legge i check-run sullo SHA della punta del predefinito (`protect.sh`, `init`) cerca per **nome esatto del job e `app.id`**, perché sulla punta ci sono anche i check-run dei job `workflow_run` di altre PR.
- (Task 16) Dalla revisione del Task 1: rileggere V4 (Cache mode dei job `workflow_run`) anche sul privato `detect`; lo script del Task 16 confronta il numero della PR quando aggancia un run (niente ripiego «il più recente»), e non ripete un merge che ha già avuto effetto; le guardie su `gh` sono una lista di ammessi per coppia (comando, sottocomando) condivisa tra lo script e il controllo del modo `controlla` (lezione di I-1 del Task 1).
- (Task 5) Decisione 10, dalla revisione del Task 3: `spec_reviews_dir` dichiarato nel blocco diverso dalla cartella in cui la spec approvata è stata trovata → voce `approval_stale` nella famiglia `l2` di `evaluate`, con test.
- (Task 5, 13) Dalla revisione del Task 3: `check_l2_detail` e `l2tree.spec_approval` danno lo stesso giudizio (corrente / superata / mancante) per la spec, calcolato in un punto solo (dopo il giro di correzione del Task 3): la famiglia `l2` del gate e `finish check` lo leggono da lì.
- (Task 5) Dal Task 4: le chiavi `ci_waived_workflow` e `review_unverified` di `GROUPS` non sono ancora prodotte: il Task 5 le produce (`review_unverified` da `block["verdict"]["unverified"]`; `ci_waived_workflow` da una deroga `ci` che copre un workflow del progetto modificato) o le mette, con il motivo, nell'insieme esplicito di `test_every_group_key_is_produced`. Le famiglie nuove si aggiungono a `evaluate.FAMILIES` e le proprietà a `Context`, senza toccare quelle del Task 4.
- (Task 13) Dal Task 4: `test_openpr.py::test_facts_keys_match_block_fields` è stato allentato perché `openpr.facts` non riempie ancora `tasks_over` e `skills_absent`: il Task 13 torna al confronto esatto. In locale `Context.is_work` vale «blocco presente»: `finish check` passa sempre il blocco di `openpr.facts`.
- (Task 17) Dal Task 4: il percorso di una violazione `base_ids` toglie anche i segmenti finali con iniziale maiuscola del `classname` (classi di test: `tests.test_x.TestFoo` → `tests/test_x.py`), da scrivere in 8.3/18.2 della rev 25.
- (Task 5) Dalla revisione del Task 4: blocco assente o non valido su un ramo `tg/*` non dà ancora una voce rossa (`_scope` ritorna `None`): la voce «blocco JSON assente o non valido» è del Task 5 (decisione 6), con test.
- (Task 13) Dalla revisione del Task 4: il Task 13 deve riempire davvero `tasks_over` e `skills_absent` in `openpr.facts` e riportare `test_facts_keys_match_block_fields` al confronto esatto.
- (Task 5) Dalla ri-revisione del Task 4: `manual_must_have` (`evaluate.py:424`) mette nel `text` i nomi dei must-have, che vengono dal piano scritto dall'agente: vanno in `Item.data`; il `text` resta un testo fisso di tollgate (per esempio «must-have con test manuale: N»). Vale per ogni voce nuova del Task 5: nel `text` solo testi di tollgate, nomi dalla configurazione del predefinito o valori validati (numeri, SHA, percorsi controllati); tutto il resto in `data`.
- (Task 8, rev-t7) Un `setup` riuscito senza report ha stato `uncounted` in `results.json`: `evaluate` non lo tratta come comando rosso né come comando mancante.
- (Task 9, rev-t7) `artifacts.read_results` non restituisce `sha` né `config_sha` di `results.json`: il verdetto li confronta con lo SHA della testa e la punta del predefinito (rileggendoli, o estendendo `read_results`), con test.
- (Task 16, rev-t8) Il `gh` finto non valuta `--jq`: sul repo vero verificare il formato di `--paginate --jq` per `statuses`, `pr_comments`, `prs_for_commit` e `-F body=@file` con `PATCH issues/comments/<id>` (commento aggiornato, non duplicato).
- (Task 17, rev-t8) Rev 25: in 9.1 la riga di `tollgate-guard` dice «commento che spiega lo stato in attesa»; `guard` rosso pubblica `failure` (ruling Task 8 giro 1): riscrivere «commento che spiega perché `guard` è rosso».
- (Task 9, rerev-t8) `github.shared_sha_prs` è coperta solo tramite `guard`: il Task 9, che la riusa in `verdict.prechecks`, aggiunge un test unitario diretto (PR impilate, stessa testa, PR chiusa, base diversa).
- (Task 11, rev-t10) `tollgate-sentinel.yml` fa il checkout con `fetch-depth: 0`: con un checkout superficiale `before` non si risolve e ogni push risulterebbe forzato.
- (Task 11, rev-t10) In `detect`, `tollgate-base` lancia `base-ids --publish` anche quando la cache degli identificativi è già presente (cache hit), altrimenti `tollgate/base` non viene scritto su quel commit.
- (Task 12, impl-t11) I `services` del job `head` di `tollgate-run` hanno solo `image:` (niente `ports:` né `env:`): il Task 12 (spec 9.6) decide come renderli raggiungibili dal job sull'host (`ports:` dalla configurazione) e lo prova.
- (Task 17, rev-t11) Rev 25: in 9.1 `tollgate-base` ha due job con permessi distinti (`ids`: `contents: read`, nessun token, esegue la suite della base; `publish`: `statuses: write`, `issues: write`, non esegue codice del progetto); regola generale: nessun job che esegue codice del progetto ha un token con permessi di scrittura; limite dichiarato: `tollgate/base` può essere falsificato dal codice unito, la rilevazione resta alla sentinella. In 9.6 i servizi valgono per ogni job che esegue comandi del progetto.
- (Task 16, rev-t11) Sul repo vero verificare che il job `publish` di `tollgate-base` pubblichi `tollgate/base` da `ids.json` sia su miss sia su hit della cache.
- (Task 17, rerev-t11) Rev 25: dichiarare anche che il codice del job `ids` (codice unito sul predefinito) può leggere `ACTIONS_RUNTIME_TOKEN` e scrivere voci di cache `tollgate-ids-<albero>` nello scope del predefinito per alberi diversi dal proprio (commit vecchi senza voce): tocca solo `base_ids`, limite della decisione 12.
- (Task 16, impl-t9) Sul repo vero registrare la forma di `GET pulls/<n>` letta da `verdict` (`head.repo`, `head.sha`, `base.ref`, `body`, `state`) e confrontarla con `verdict.pr_from_rest`.
- (Task 16, controller) Lo script usa solo `spikes/gh-p4/ghguard.py` (lista unica degli ammessi della decisione 25) come involucro di ogni `gh` verso la rete; nessun `gh` diretto.

## Task 17 (dalla prova reale del Task 16)
- `gh pr edit` è rotto con gh 2.46 (GraphQL Projects classic): il corpo della PR si aggiorna con `gh api --method PATCH repos/{owner}/{repo}/pulls/<n> -F body=@file` (`bin/tollgate_flow/gh.py:pr_edit`). Allineare la spec rev 25 (righe ~514, ~1331, ~1501 G3) e le docstring di `bin/tollgate_flow/openpr.py:5` e `:259`, con la nota sulla versione di gh.
- Con `tollgate/attention` rossa e `guard`/`verdict` verdi GitHub dà `mergeStateStatus = UNSTABLE` (PR unibile): se la spec dice `CLEAN` per i verdi con attenzione, correggere.
- In `protected` `tollgate-base` non pubblica lo stato `tollgate/base` (il segnale è il job, `baseids.publish`): verificare che la spec lo dica.
- Task 17: spec — le letture di gh api ritentano sui 5xx transitori (3 tentativi, 2 s e 4 s), le scritture no (giro 4 del Task 16).
- Task 17: spec — ritentativi anche per POST statuses e PATCH di commento (idempotenti), mai per commenti nuovi e issue (giro 5 del Task 16).
