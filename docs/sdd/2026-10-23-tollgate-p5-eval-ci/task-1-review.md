# Revisione Task 1 (Step 1) — script, sonda, guardia p5 e test senza rete

Pacchetto letto: `review-a9b37e3..dcd0485.diff` (una lettura). Controlli mirati fuori dal diff, ciascuno per un rischio nominato:
- 79 casi di prova diretti su `ghguard.violation(..., profile="p5")` (opzioni ripetute/abbreviate, `\n`, `GINZ0LS`, endpoint con `..`/query/`%2e`, `--jq`, PUT/PATCH in tutte le forme): 0 divergenze dalle attese. Eseguiti con `python3 -B -I` su cartelle in scratchpad (nessun `gh`, nessuna rete).
- `ghguard.py comandi` sul registro committato `docs/verifiche/evidenze/gh-p4/comandi.log` da questo checkout (percorso con spazi): passa (rischio: correzione del test dipendente dal percorso).
- `yaml.safe_load` dei 4 `case.yaml` e di `ci-probe.yml` con `python3` 3.13 (PyYAML presente): tutti validi. Con 3.11 i 2 test YAML sono saltati: lacuna colmata.
- `git grep` della stessa espressione di token su `HEAD`: un solo file, `tests/test_git.py` (riga 279, fixture `ghs_…` di un test), come riferito.
- Campi di `claude plugin eval` confrontati con `plugin-evals-doc.md` (righe 359-379, 441-457): `--scaffold`, `--keep-temp`, `--threshold`, `--case`, `--ablation`, `--output-dir`, `--report`, `--json <percorso>.json`, `costUsd`/`durationSeconds` di primo livello e `cases[].name` esistono.

## Aderenza (✅ / ❌; ⚠️ non verificabile)

1. Guardia `p5` (`spikes/gh-p4/ghguard.py`)
   - ✅ Due soli repo: `kind repo` è un confronto esatto con `P5_REPOS` (`ghguard.py:136`), `_foreign_repo` (`:474`) rifiuta qualunque `ginz0ls/<altro>` in qualsiasi argomento, anche dentro un testo. `tollgate-p4-protected`, `ginz0ls/tollgate-p4-protected-x`, `GINZ0LS/...`, `.git`: rifiutati (provato).
   - ✅ Operazioni per repo (`P5_REPO_OPS`, `:424`): su tollgate solo `run list|view|watch|download|rerun`; su detect anche `pr create|close|merge|view|list|comment`, `issue close|comment|view|list`. `pr merge` solo con `--merge|--squash|--rebase`, mai `--admin`/`--delete-branch`/`--auto`; `pr close` senza `--delete-branch`; nessun `pr edit`/`issue create`.
   - ✅ `gh api user`, `/user`, `graphql`, `orgs/`, `users/`: rifiutati (l'endpoint deve cominciare per `repos/<uno dei due repo>`); `gh auth` solo `["auth","status"]` esatto (niente `--show-token`); `repo create` solo `["repo","create","ginz0ls/tollgate","--private"]` esatto; `repo delete/edit/view/clone`, `secret`, `variable`, `workflow`, `release`: rifiutati.
   - ✅ Scritture `gh api`: `_check_api_write_p5` ammette solo (a) PATCH `repos/<detect>/pulls/<n>` con `-F body=@<file>` e `n` registrato, (b) PUT `repos/<detect>/actions/permissions` con `enabled=true`, `sha_pinning_required=true|false` e al più `allowed_actions=all|local_only|selected`. Metodo assente (gh passerebbe a POST se ci sono campi) → rifiutato; `-f`, `--input`, campi extra, `/`, `?`, `/selected-actions`, `/workflow`, metodo in minuscolo, metodo ripetuto: rifiutati. DELETE/POST/PATCH di visibilità: rifiutati.
   - ✅ PATCH «stessa prova»: `pr create` passato da `check` annota `create` nel registro (rifiuta senza `P5_PR_REGISTRY` assoluto), `register-pr <n>` consuma un `create`; una PR non registrata non si può modificare. Provato anche via CLI (`tests/test_p4_ghguard.py` P5ApiWritesTest).
   - ✅ Vie di fuga: `fullmatch` ovunque (`\n` finale, cifre Unicode: rifiutati); `--repo` ripetuto, `-R` ripetuto o misto, `-Rvalore`, `-R=valore`, `--rep` abbreviato, `--` : rifiutati o conteggiati; endpoint con `..`, `//`, `%2e/%2f/%5c/%00`, segmento `.`, caratteri fuori classe, `/secrets`: rifiutati. `-XPOST`, `--method=…`, `--field`, `--raw-field`: instradati sul ramo scritture e rifiutati. Ogni `pr|issue|run` esige esattamente un `--repo/-R`: la cartella corrente non è mai repo implicito.
   - ✅ `GH_REPO`/`GH_HOST`: lo script li toglie (`run-p5-checks.sh:34`) prima di caricare `common.sh`. ⚠️ La guardia non li controlla (non può: è chiamata da chi ha già l'ambiente) e nessun test asserisce che lo script li tolga (vedi M5).
   - ✅ Minori di P4 (`$`, `isdigit`, PATCH di qualunque PR nel solo p5): corretti. Il restringimento è solo nel profilo p5; script/flow invariati, dichiarato nel report «da confermare». È coerente con la decisione 22 («nel profilo p5 solo le PR aperte dal controller»).

2. Chiamate `gh` e `git` di rete dello script
   - ✅ Nessun `gh` nudo: il test `test_gh_is_only_called_through_the_guarded_helpers` lo asserisce per riga e la mia grep conferma (solo `gh_call/gh_read/gh_q/gh_write_idem`, tutti su `guard_args`, `common.sh:12`).
   - ✅ Ogni `git` con la rete passa da `git_net` (`run-p5-checks.sh:57`): `ghguard.py gitcheck` prima, poi `no_rewrite_rules` (rifiuta `url.*.insteadOf` globali/di sistema), poi git. `git_violation` (`ghguard.py:553`): push solo `<url esatto di tollgate|detect> <ramo>`, nessuna opzione (quindi mai `-f`, `+ref`, `a:b`, `--tags`, `--all`, `--mirror`, `-u`); su tollgate solo `main`, `p5-eval-ci`, `p5-probe-*` (≥1 carattere dopo il prefisso); `--delete` solo `p5-probe-*` su tollgate e mai su detect; `ls-remote --tags` e `fetch --depth 1 … tag <vN>` solo sulle 5 azioni e fetch solo sotto `P5_PINS`; `clone -q <url detect> <dest>` solo sotto `P4_WORK`. `main` viene spinto dal clone locale di `main` di `P5_SOURCE_DIR` (`:340`), «com'è».
   - ✅ Ricerca di token: `cerca_token` (`:120`) è chiamata in `modo_ci_sonda` prima di `gh repo create` (`:324`) e di ogni push (`:340`), si ferma con `die`, stampa solo `TROVATO <12 car. del commit> <percorso>`; `git grep -l` non emette il testo, lo stderr va in un file temporaneo cancellato. Provato dal modo `controlla` con una forma di token costruita a runtime (non compare nei log). Ambito: `git rev-list --all` (superset di `main`).
   - ✅ Nessuna cancellazione su detect (la guardia rifiuta `push --delete` su detect e ogni `api … DELETE`); lo script non cancella nemmeno i rami `p5-probe-*` di tollgate.

3. `claude plugin eval` (`eval_run`, `:205-245`, unico punto di chiamata, asserito da `test_exactly_one_claude_eval_command_with_every_precaution`)
   - ✅ `--no-publish`, `--trust-plugin`, `--runs 1`, `--model claude-sonnet-5-5`, `--scaffold`, `--keep-temp`, `--max-cost-usd "$cap"`; `cap` = `budget_cap` = min(3, 80 − somma di `costUsd`), in centesimi per difetto; riga illeggibile o residuo < 0,01 → `die` senza lanciare `claude` (provato: tetto 1.50 con 78.5 speso, tetto esaurito senza avvio di `claude`).
   - ✅ La riga di `budget.tsv` si scrive dopo ogni invocazione per qualunque codice d'uscita, purché `result.json`/`aggregate-result.json` portino `costUsd` e `durationSeconds`; altrimenti `COSTO-IGNOTO.txt`, `die`, e ogni invocazione successiva rifiuta (`:209`). Intestazione e formato come richiesti (`ora<TAB>invocazione<TAB>costUsd<TAB>durationSeconds<TAB>casi`).
   - ✅ `--threshold 0` in più (dichiarato): evita l'uscita 1 a sonda riuscita; accettabile, non allenta alcuna cautela.

4. Hook e evidenze
   - ✅ `hooks/record.py` registra solo `HOME, PATH, CLAUDE_CONFIG_DIR, CLAUDE_PLUGIN_ROOT, PWD, TMPDIR` come valori, più i NOMI delle variabili e delle chiavi dell'evento; non registra `tool_input` né il transcript (test con un valore segreto di prova che non compare). `bin/sonda` e gli scaffold stampano valori solo di `HOME`, `CLAUDE_CONFIG_DIR`, `CLAUDE_PLUGIN_ROOT`, `TMPDIR`, cartella corrente, e `compgen -e` (nomi). Gli scaffold si rifiutano se la `HOME` ha `~/.claude/settings.json` o `~/.local/state/tollgate` (prima di scrivere); la sonda scrive solo in `$HOME/.local/state/sonda`, mai in quello di tollgate.
   - ✅ `copy_run_files` copia solo file con nomi della sonda sotto `$TMPDIR`/`/tmp`, mai dal repo o dalle cartelle di uscita.
   - ⚠️ Il valore di `PATH` del chiamante finisce nelle evidenze (è nominato, quindi ammesso, ma contiene i percorsi locali dell'utente): accettato dalla decisione 20 per i percorsi in `docs/`. Il contenuto di `stdout.txt`, `report.html`, `result.json` (trace) non è verificabile prima dell'esecuzione.

5. `detect-pin` (`:520-570`)
   - ✅ `PIN_TOUCHED=1` prima del PUT di accensione (`:539`), `trap restore_pin EXIT` e `trap 'exit 130' INT TERM` installati subito dopo la lettura del valore iniziale; il ripristino ritenta 3 volte, rilegge e verifica `sha_pinning_required`; se non verificato stampa «RIPRISTINO NON VERIFICATO» ed esce 3; il ripristino ripete anche `allowed_actions` iniziale. Il modo `controlla` prova lo scenario fallito (push rifiutato da un hook del nudo) e il valore rimesso. Resta fuori solo `kill -9`.

6. Correzione del test dipendente dal percorso (`ghguard.py:645-655`)
   - ✅ Cambia solo `check_comandi` (rigioco di un registro), non `violation()`/`git_violation()`: nessun comando nuovo è accettato in più al momento dell'esecuzione. Prefissi ammessi solo `…/.claude/worktrees/<nome>/docs/verifiche/evidenze/<stessa cartella del registro>`; `/etc`, `/home/u/docs/…`, altra cartella di evidenze e `..` restano rifiutati (test `ReplayOfCommittedEvidenceTest`). Confermato sul registro P4 reale (passa). ⚠️ Una debolezza residua del solo rigioco in M3.

7. Requisiti di `carry.md` / brief
   - ✅ VE1 in invocazione separata con `dependencies` copiato da `.claude-plugin/plugin.json`; hook solo con variabili nominate; `--keep-temp`; `budget.tsv` per ogni invocazione; tetto min(3, residuo); VE12 (`ws-worktree`, `SessionStart`); `additionalContext` di PostToolUse in `trace`; file scritto da un hook (`file_exists` + `regex target: files`); sonda anche da `/tmp/tollgate-eval-target-sonda/` con `probe-bin` copiato e in testa al `PATH` (solo per il caso `skill`; ho letto «casi base» come questo caso, ⚠️ da confermare); test preesistente corretto senza riscrivere le evidenze di P4.
   - ✅ Modi del brief tutti presenti; `cerca-token` è in più ma minimo e riusa `cerca_token`, accettabile.
   - ❌ Nessuna evidenza di `tests/run` completo né di una corsa con `python3` oltre la 3.11 (regola di chiusura dei task, `global-constraints.md`): il report riporta solo le esecuzioni mirate. ⚠️ Non verificabile: il controller la lanci prima di dichiarare chiuso il task.

## Punti di forza

- Guardia con lista chiusa, `fullmatch`, controllo del repo su ogni argomento e registro delle PR a due tempi (`create` annotato dal `check`, numero registrato dopo): disegno stretto e ben coperto (33 test nuovi in `test_p4_ghguard.py`, più CLI).
- `git_net` unico punto per la rete, con `gitcheck` + `no_rewrite_rules` + un test che vieta ogni git di rete fuori dal helper; modo `controlla` completo con nudi locali, `gh` e `claude` finti, prove negative (44 gh, 16 git) e rigioco dell'intero `comandi.log` con la guardia.
- Fail-closed sul denaro: residuo, riga illeggibile, `COSTO-IGNOTO.txt` bloccano ogni invocazione successiva; ripristino del pinning verificato e provato anche nel ramo d'errore.
- Il report è onesto: dichiara gli scostamenti (soglia del token, `--threshold 0`, clone di detect) e i dubbi.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

- **M1 — `--body-file`/`-F body=@` leggono da `/tmp` e da `$TMPDIR` anche nel profilo p5** (`ghguard.py:82-106`, `_infile` → `_temp_roots`). Lo script usa solo `--body` testuale e non fa PATCH, quindi il profilo p5 non ha bisogno di quel canale; con un `TMPDIR` largo (per esempio la home) un file qualsiasi finirebbe come corpo di una PR su detect. Correzione: nel profilo p5 `_infile` ammette solo `P4_OUT` e `P4_WORK` (e un test).
- **M2 — `--jq`/`-q` accettano qualunque espressione** (`ghguard.py:43,330`). `gojq` espone `env`/`$ENV`: `gh api … --jq env` scriverebbe l'ambiente (token compresi) in un file di evidenza che poi si committa. Lo script p5 non usa `--jq`, quindi oggi non è raggiungibile. Correzione: nel profilo p5 rifiutare `env`, `$ENV`, `input`, `input_filename` nel filtro (o limitare i caratteri).
- **M3 — il rigioco `comandi` può nascondere un riferimento a un repo estraneo** (`ghguard.py:652-655`). La regex di riscrittura accetta spazi dentro i segmenti, quindi in un registro manomesso `--body-file /a ginz0ls/tollgate-p4-protected/.claude/worktrees/q/docs/verifiche/evidenze/p5/x.md` diventa `<cartella>/x.md` e passa (provato in scratchpad; senza il travestimento la stessa riga è rifiutata). Non tocca l'esecuzione (la guardia viva vede la riga vera) e serve un registro manomesso, quindi è Minor. Correzione: eseguire `_foreign_repo` (nel profilo p5) sulla riga originale prima della riscrittura, o vietare `ginz0ls/` nei segmenti riscritti.
- **M4 — PR orfana su detect se `open_pr_detect` muore dopo `gh pr create`** (`run-p5-checks.sh:287-304,444`). `CACHE_PR` si assegna solo dopo il ritorno di `open_pr_detect`; un errore nel parsing del numero o nella registrazione lascia la PR aperta e il trap non la chiude. Correzione: assegnare `CACHE_PR="$PR_NUM"` dentro `open_pr_detect` subito dopo il parsing (prima di `register-pr`).
- **M5 — nessun test che lo script tolga `GH_REPO`/`GH_HOST`** (`run-p5-checks.sh:34`; `tests/test_p5_scripts.py`). È la sola difesa da quella via di fuga, e `GH_CONFIG_DIR`, `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN` non sono tolti (`ghwrap.py` di P4 li scarta). Correzione: aggiungere un test che lancia `controlla` con `GH_HOST=altro.example GH_REPO=x/y` e verifica che i `gh` finti non li vedano; valutare di togliere anche le altre.
- **M6 — costo ignoto: nessuna riga in `budget.tsv`** (`run-p5-checks.sh:229-233`). Con `claude` che esce senza JSON si scrive solo `COSTO-IGNOTO.txt`; la spesa eventuale non compare nel registro e, dopo la verifica a mano, serve cancellare il file e scrivere la riga a mano. Se «la riga qualunque sia l'uscita» va letto in modo stretto, scrivere una riga con `costUsd` = `?`: `budget_cap` la rifiuta già, quindi il fail-closed resta.
- **M7 — `eval-sonda` non si può riprendere da un caso** (`:242-270`). Se la prova 2 (`nl-worktree`, con `EnterWorktree` in `allowed_tools`: lo strumento non è tra quelli elencati nella documentazione, riga 347) fa uscire `claude` senza JSON, la sequenza si ferma per «costo ignoto» e dopo lo sblocco rilanciare `eval-sonda` rifà e ripaga le prove 1. Esito plausibile, perché VE6 serve proprio a scoprirlo. Correzione: una variabile `P5_ONLY` (elenco di etichette) o un modo per caso.
- **M8 — `git` senza `GIT_TERMINAL_PROMPT=0`** (`:57-86`). Se le credenziali HTTPS non sono configurate (il report lo dice, dubbio 4), git può chiedere username su `/dev/tty` invece di fallire. Correzione: aggiungere `GIT_TERMINAL_PROMPT=0` a `genv`.
- **M9 — `comandi.log` non contiene i `gh` dei sondaggi** (`gh_q` di `common.sh:49` non registra): il report dice «ogni `gh` eseguito» in `comandi.log`. Passano comunque tutti dalla guardia; basta correggere la frase del report o far registrare `gh_q` (solo per p5).
- **M10 — `ammissione per percorso` dei token** (`:120-150`, `P5_TOKEN_ALLOW_PATHS`): ammette `tests/test_git.py` in ogni commit; un token vero aggiunto dopo in quello stesso file passerebbe stampato come `AMMESSO`. Scelta esplicita del controller, ma il controller sappia che oggi `ghs_…` è l'unico caso (riga 279) e che la deroga non guarda il contenuto.
- **M11 — il confine `copy_run_files` dipende da `TMPDIR`** (`:183-205`): se `claude plugin eval` mette le cartelle `--keep-temp` in `/tmp` mentre `TMPDIR` punta altrove (come in questa sessione), le cerca solo nei percorsi stampati, e con `--json` l'esecuzione è silenziosa. Il report lo dichiara (dubbio 1); da guardare all'esito della prima prova.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** La guardia p5 e la disciplina di rete dello script soddisfano i sei punti richiesti: lista chiusa di repo e operazioni, nessuna via di fuga trovata in 79 prove dirette, ogni `gh` e ogni `git` di rete passano dal controllo, tetto di spesa e ripristino del pinning fail-closed e provati, correzione del test P4 limitata al rigioco. Restano solo rilievi Minor (irrigidire `--body-file`/`--jq` in p5, rigioco, test su `GH_HOST`, ripresa per caso, PR orfana). Prima di chiudere il task resta da eseguire `tests/run` completo con `python3.11` e `python3`, di cui il report non porta evidenza.
