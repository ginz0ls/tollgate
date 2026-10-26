# Ri-revisione giro di correzione 1, Task 13 (7c9addc..6f97ba1)

Letto: regole, cautele, rilievi, decisioni del controller (progress.md righe 214-215), report «Fix round 1», diff, e per contesto `_parse`, `_registry_lines`, `check_comandi`, `gh_call` di common.sh. Eseguiti solo `bash -n` (ok) e `python3 -B -m unittest tests.test_p5_scripts.IssueCreateGuardTest` (3 test OK).

### Verdetti sui rilievi
1. **Fetch interno di `init --update` fuori da gitcheck**: la ruling lo manda nel rapporto del controller, nessun cambio di codice richiesto. Nessuna modifica nel diff; resta da riportarlo nel rapporto. NON in ambito del codice (da fare a mano).
2. **Letture senza ritento (`statuses`, `wait_run`, `close_open_prs`)**: INDIRIZZATO. `run-p5-gate.sh:140-168`: `gh_call` di common.sh rinominato `gh_call_once` via `declare -f | sed '1s/…/'` (la funzione `gh_call` di common.sh, riga 42, parte con `gh_call`, la sostituzione e' valida; `bash -n` ok). Le funzioni di common.sh risolvono `gh_call` a runtime, quindi `statuses`/`wait_run` e la lettura di `close_open_prs` (riga 77) ritentano. Ritento solo se `is_read` e solo su `HTTP 5xx` con tetto `RETRIES`.
   Scritture mai ritentate: `is_read` ammette solo `pr|issue view|list`, `run list|view` e `api` senza `--method|-X|-f|-F|--input|--field|--raw-field`. Verificati i siti: `pr create` (229), `pr merge` (379, 631), PATCH `api --method` (568), `pr close` (79), `--version` (718), `run watch`, `run rerun`, `issue create` finiscono tutti in `gh_call_once`. La PUT di permessi usa `gh_write_idem` -> `gh_call_once_idem` (idempotente, stesso corpo), come prima. Nessuna scrittura non idempotente ritentata. Anche le forme di scrittura che la guardia lascia passare (`--method`, `-X`, `-f`, `-F`, `--input`, token esatti in `_api_write_parts`) sono tutte tra i flag che escludono `is_read`.
3. **Minuti doppi in `rivalutazione`**: INDIRIZZATO. Tolto il secondo `track` (diff, ex riga 493); resta `track "$label-prima-run"` (riga ~559); nessun riferimento a `$label-dopo-run` in script o test.
4. **`net_push` provato solo dal testo**: INDIRIZZATO. `modo_controlla` chiama davvero `net_push` con `main`, `a:b`, `+main`, `-f`, vuoto, in subshell con `ALLOW_MAIN_PUSH=0`, e segnala `NET_PUSH NON RIFIUTATO` se non muore; il test controlla la riga di esito e l'assenza del marcatore. `die` in subshell fa uscire la subshell, quindi la prova e' reale (la `die` precede `git_net`).
5. **Rilievo 4 (tabella verbi per modo) e 6 (gh finto nello script)**: non accolti dalla ruling, restano come erano (Minor, non bloccano).

### Estensione `issue create` (verdetto: CORRETTA, nei limiti richiesti)
- Solo detect: `P5_REPO_OPS[TOL]` non la contiene, `[DET]` si; repo estranei fermati da `_foreign_repo` e `KINDS["repo"]`; `--repo` obbligatorio (`_parse`, "serve esattamente un --repo"). Test: tollgate, protected, senza repo.
- Titolo: `ghguard.py:_issue_create_problem` richiede il prefisso «prova P5: » (in lenient «prova P5:») e non vuoto dopo il prefisso; ultimo `--title` vince come in gh. Divergenze tra il mio parse e `_parse` vanno solo verso il rifiuto (es. `--body --title …`).
- Senza opzioni in piu': `SPECS[("issue","create")]` ammette solo `--title`, `--body`, `--body-file` (+ repo). `--assignee`, `--label`, `--project`, `--web`, `-t`, `-b`, `--template`, `--recover` ecc. falliscono in `_parse` ("opzione non ammessa"); posizionali vietati; `--body-file` solo `infile` (cartella ammessa). Esattamente uno tra `--body` e `--body-file`.
- Tetto 2: `note_issue_create` conta le righe `issue` nel registro `P5_PR_REGISTRY` (percorso assoluto obbligatorio), annotate in `main` dopo il via libera della guardia (consuma anche se la creazione poi fallisce: lato sicuro). Le righe `issue` non interferiscono con `create`/`pr N` (`registered_prs` e `register_pr` filtrano con regex e `startswith("pr ")`). Provato dal test (0,0,1; senza registro 1).
- Non apre altro: il ramo e' `if (first, second) == ISSUE_CREATE` dentro `P5_SPECS`; `issue close|comment` restano quelli di prima; `gh api` non toccato (`_check_api_write_p5` invariata: solo PATCH di PR registrata e PUT permessi); profili `script`/`flow` invariati (`SPECS` e `FLOW_FORBIDDEN` non modificati). Lo script non crea issue; la negativa `issue create --repo $DET --title x` (riga 1022) resta rifiutata.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important.
- Minor: i commenti di `run-p5-gate.sh:17` e `:273` dicono ancora «`issue create` non e' ammesso» (ora lo e' per il controller, con le condizioni sopra): stantii, da allineare.
- Minor: `check_comandi` (rilettura di comandi.log, lenient) non applica il tetto di 2: ammette qualsiasi numero di righe `issue create` conformi. Il tetto vale al momento dell'esecuzione (`check`), quindi non e' un buco, ma il controllo a posteriori non lo riconta.

### Osservazioni fuori ambito
- `docs/verifiche/evidenze/p5/comandi.log` modificato nel working tree dal controller: non toccato.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Resta da fare a mano il punto 1 (fetch interno di `init --update` nel rapporto del controller) e i due Minor stantii sopra, non bloccanti.
