# Task 1 (Step 1) - report dell'implementatore

## Cosa è stato fatto

1. **`spikes/gh-p4/ghguard.py`**: profilo `p5` (decisioni 20-22) e minori di P4.
   - Repo ammessi solo `ginz0ls/tollgate` (TOL) e `ginz0ls/tollgate-p4-detect` (DET); ogni argomento (anche dentro un testo) che nomina un altro `ginz0ls/<x>` è rifiutato (compreso `tollgate-p4-protected`). `gh api user`, `gh auth` diverso da `status`, segreti, visibilità, `repo delete`: rifiutati.
   - Operazioni per repo (`P5_REPO_OPS`): su TOL solo `run list|view|watch|download|rerun` e `api` in lettura; su DET anche `pr create|close|merge|view|list|comment`, `issue close|comment|view|list`. `repo create ginz0ls/tollgate --private` è l'unica forma di `repo create`.
   - Scritture `gh api`: (a) PATCH del corpo di `pulls/<n>` su DET con `-F body=@<file>` **solo per PR registrate**: `check -- pr create` annota `create` in `P5_PR_REGISTRY` (se manca il registro, o non è assoluto, il `pr create` è rifiutato), poi `ghguard.py register-pr <n>` consuma un `create` e scrive `pr <n>`; (b) PUT `actions/permissions` su DET con `-F enabled=true -F sha_pinning_required=true|false` e al più `-F allowed_actions=all|local_only|selected`.
   - Comandi git con la rete: `ghguard.py gitcheck [--dir D] -- <args>` (`git_violation`): `push [--delete] <url> <ramo>` (TOL: `main`, `p5-eval-ci`, `p5-probe-*`; delete solo `p5-probe-*`; DET: qualsiasi ramo semplice, mai delete; nessuna opzione, mai forzato), `ls-remote --tags https://github.com/actions/<azione>`, `fetch --depth 1 <azione> tag <tag>` solo sotto `P5_PINS`, `clone -q <url di detect> <dest>` solo sotto `P4_WORK`.
   - `log` e `comandi` leggono il profilo da `P4_PROFILE`; `comandi` controlla anche le righe `git-net dir=<d> <args>`.
   - Minori di P4: regex con `fullmatch` (un a-capo finale non passa), `int` solo cifre ASCII (`[0-9]+`, non `str.isdigit()`), `re.match(...$)` degli endpoint di PATCH/statuses con `fullmatch`. La PATCH "valida per qualsiasi PR" è stretta solo nel profilo `p5` (PR registrate); nei profili `script` e `flow` di P4 resta com'era (non esiste uno stato "stessa prova" lì): **da confermare**.
2. **Correzione del fallimento preesistente di `tests.test_p4_scripts.ControllaTest.test_task1_script_still_passes_after_the_common_library`** (ruling del controller): vedi sezione sotto.
3. **`spikes/p5/run-p5-checks.sh`** (modi `eval-sonda`, `ci-sonda`, `pins`, `detect-cache`, `detect-pin`, `raccogli`, `cerca-token`, `controlla`), `spikes/p5/fake/{gh,claude.py}`, `spikes/p5/ci-probe.yml`, `spikes/p5/probe-bin/sonda-shim`.
4. **Plugin sonda** `spikes/p5/probe-plugin/` (nome `sonda`, validato con `claude plugin validate`: passa), 4 casi: `nl-bash`, `nl-worktree`, `skill`, `ws-worktree` (VE12).
5. `docs/verifiche/evidenze/eval-p5/budget.tsv` con la sola intestazione (tab).
6. Test: `tests/test_p4_ghguard.py` (+33 test), `tests/test_p5_scripts.py` (nuovo, 44 test).

## Correzione del test preesistente di P4

Causa: `run-p4-checks.sh controlla` rigioca `docs/verifiche/evidenze/gh-p4/comandi.log` con `ghguard.py comandi`, che prende `P4_OUT` = cartella del registro; i percorsi registrati (`-D`, `--body-file`, `-F body=@`) sono quelli del vecchio worktree `…/.claude/worktrees/p4/docs/verifiche/evidenze/gh-p4/…`, fuori da `P4_OUT` corrente, e `_infile`/`outdir` li rifiutano.
Correzione (solo nel rigioco, `check_comandi`): i soli prefissi `<qualsiasi>/.claude/worktrees/<nome>/docs/verifiche/evidenze/<cartella del registro>` si riportano alla cartella corrente del registro prima del controllo. Le regole della guardia per i comandi nuovi non cambiano; le evidenze di P4 non sono toccate. Prefissi diversi (`/etc/…`, `/home/u/docs/…`, un'altra cartella di evidenze, `..`) restano rifiutati.
RED: su a9b37e3 `python3.11 -m unittest tests.test_p4_scripts.ControllaTest.test_task1_script_still_passes_after_the_common_library` fallisce (VIOLAZIONE «valore non ammesso per -D: /home/…/worktrees/p4/…»); nuovo test `ReplayOfCommittedEvidenceTest.test_paths_of_an_old_worktree_pass_from_any_checkout_path` fallisce con la guardia di HEAD.
GREEN: stesso test di P4: `Ran 1 test … OK`; il rigioco passa anche da una copia senza spazi fuori da `.claude/worktrees/` (provato), e `ReplayOfCommittedEvidenceTest` (2 test) passa con nomi di checkout con spazi, senza spazi e dentro `.claude/worktrees/`.

## RED / GREEN (guardia)

- RED: con `ghguard.py` di HEAD (copia in scratch) `tests.test_p4_ghguard` non si importa (`AttributeError: module 'ghguard' has no attribute 'TOL'`); e in particolare `violation(['issue','close','٣',…])` e `violation(['pr','view','3\n',…])` danno `None` (accettati) con la vecchia guardia, `serve un numero…` con la nuova.
- GREEN: `python3.11 -B -m unittest tests.test_p4_ghguard` -> `Ran 79 tests … OK` (46 preesistenti verdi, 33 nuovi).
- `tests/test_p5_scripts.py`: scritto dopo lo script (lo script è esplorativo); non ho un RED storico per questi test. GREEN: `Ran 44 tests … OK (skipped=2: PyYAML assente con 3.11)`.

## Ricerca di token (cerca-token / ci-sonda)

`TOKEN_PATTERN='gh[pos]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|sk-ant-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}'`, `git grep -l -I -E` su `git rev-list --all` a blocchi di 40 revisioni; stampa solo `TROVATO <12 caratteri del commit> <percorso>`; esce 1 se ce n'è uno. **Scostamento**: prefisso + almeno 8 caratteri (16 per AKIA), non il prefisso nudo, perché il prefisso nudo compare in testi e regex (piani, `prepara-auth.out` di P4 con `gho_***` mascherato).
Prova con `git grep` (non con lo script) sulla storia di oggi: **un solo file noto**, `tests/test_git.py` (riga 279, una stringa `ghs_…` di una fixture), nella storia e nell'albero. Col prefisso nudo comparirebbero anche i due piani P5 in `docs/superpowers/plans/`, `docs/sdd/2026-10-21-tollgate-p4-gate/task-1-review.md` e `docs/verifiche/evidenze/gh-p4/prepara-auth.out`(+`.prev-…`) (testo mascherato).
Il controller decide: se `tests/test_git.py:279` è una fixture, ripartire con `P5_TOKEN_ALLOW_PATHS=tests/test_git.py` (ammissione **esplicita**: ogni uso è stampato e scritto come `AMMESSO` in `token-scan.txt`; per percorso, vale per ogni commit). Senza la variabile lo script si ferma sempre: fail-closed.
Durata: ~10-20 s per ogni blocco di 40 commit; 326 commit -> da 1 a 3 minuti.

## Scostamenti dal piano / dal brief e perché

- `git clone` di detect (in `$WORK/detect`) e `git clone --branch main <P5_SOURCE_DIR>` locale (clone di `main` dal repo locale, nessuna rete): per aprire PR su detect serve la storia di `main`; `gh repo clone` non è tra le operazioni p5. **Da confermare dal controller** (lettura del solo repo di prova già ammesso in push). Se non va, VG1/VG2 non si possono fare con questo script.
- VE1: `dependencies` copiato da `.claude-plugin/plugin.json` di tollgate (forma a oggetti `{"name","marketplace"}`), non la forma `["superpowers"]` del brief: è quella da provare davvero.
- Aggiunti `--threshold 0` e `--keep-temp` a ogni `claude plugin eval` (la soglia 1.0 darebbe uscita 1 anche a sonda riuscita, e non distinguerebbe errori veri).
- `ci-sonda`: ramo `p5-probe-ci` (con suffisso data se esiste già sul repo); workflow con `actions/setup-python@v5` (la maggiore corrente la stabilisce `pins`, VC2).
- `raccogli` chiama `claude --version`, `bwrap`, `socat`, `jq` direttamente (non sono `gh`), `gh --version` solo via guardia.
- Nessun `gh repo clone` né `gh api user`: il proprietario è fisso `ginz0ls`.

## Aggiunte del controller (messaggio successivo)

1. **VE12**: caso `ws-worktree`, scaffold dedicato: `$HOME/proj` come checkout principale, `git worktree add "$ws" -b tg/1-sonda` nel workspace vuoto; il prompt fa `git status`, `git log`, un `git commit` e `git log && echo SONDA-WS-$((40+2))`; grader sulla trace (`tg/1-sonda`, `SONDA-WS-42`), `file_exists ws-file`, registro hook con `SessionStart` e `PreToolUse` (cwd). Hook `SessionStart` aggiunto (stessa regola: solo i valori elencati e i nomi delle variabili).
2. **D18 (a)**: `hooks/post.py` (PostToolUse di Bash) restituisce `additionalContext` `SONDA-CONTESTO-POST…`; grader `regex` su `trace` in `nl-bash`.
3. **D18 (b)**: lo stesso hook scrive `scritto-da-hook.md` nella cartella dell'evento (solo se non esiste); grader `file_exists` true e `regex` con `target: files` in `nl-bash`.
4. **D10**: `eval-sonda` fa girare anche `sonda-radice-tmp` (caso `skill`, `--ablation none`) su una copia del plugin in `/tmp/tollgate-eval-target-sonda/` (variabile `P5_TMP_TARGET`, `rot` se esiste), con `probe-bin` copiato lì e messo in testa al `PATH`. VE3 (`PLUGIN_ROOT_READABLE`, `ENV_CLAUDE_PLUGIN_ROOT`) dirà quale radice si legge.
Ordine di `eval-sonda` (6 invocazioni, tetto 3 USD ciascuna o il residuo): `sonda-nl-bash` (with-without, VE7), `sonda-nl-worktree`, `sonda-ws-worktree`, `sonda-skill`, `sonda-radice-tmp`, `sonda-ve1-dependencies`.

## Autorevisione

- Completezza: tutte le richieste del brief e del controller coperte; il budget (`budget.tsv`) si aggiorna dopo ogni invocazione prima di valutare l'uscita; senza costo leggibile scrive `COSTO-IGNOTO.txt` e si ferma (e ogni invocazione successiva rifiuta finché il file c'è).
- Il tetto `--max-cost-usd` = min(3, 80 - somma di costUsd), per difetto ai centesimi; residuo < 0,01 USD o riga illeggibile -> rifiuta senza lanciare.
- `controlla` prova: ricerca di token (sporco/pulito/ammesso), `ci-sonda` che non crea il repo con token nella storia, ritentativo del 500, ripristino di `sha_pinning_required` anche dopo un fallimento (push rifiutato da un hook del nudo), tetto 1.50 con 78.5 speso, tetto esaurito (claude non parte), costo ignoto (niente dopo), shim in testa al `PATH`, copia dei file della sonda, ogni comando gh registrato passa da `ghguard.py log` p5 e dal `comandi.log`, prove negative gh (44) e git (16), ogni `plugin eval` con tutti i flag.
- I file della sonda scrivono in `$HOME/.local/state/sonda`, mai in quello di tollgate; lo scaffold rifiuta una HOME con `.claude/settings.json` o `.local/state/tollgate`.
- Dubbi: (1) formato reale delle cartelle `--keep-temp` ignoto: `copy_run_files` cerca nei percorsi stampati da claude e, in alternativa, i file della sonda nuovi sotto `$TMPDIR` o `/tmp`; (2) i grader `file_exists` con glob su cartelle nascoste (`.claude/worktrees/…`) possono non agganciare: per questo ci sono il percorso esatto e il glob; (3) `claude plugin eval` potrebbe rifiutare `EnterWorktree` in `allowed_tools` (è proprio VE6, per questo ha un caso suo); (4) le credenziali git per il push HTTPS a GitHub non le gestisce lo script.

## Per il controller

Prima: Step 0 (precondizioni). Poi, dalla radice del worktree (percorso con spazi: virgolette):

```
R="/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p5"; cd "$R"
bash spikes/p5/run-p5-checks.sh controlla          # già verde; nessuna rete
```
1. `bash spikes/p5/run-p5-checks.sh eval-sonda` - 6 invocazioni di `claude plugin eval` (costo atteso pochi USD; ognuna max 3 USD). Guardare: `docs/verifiche/evidenze/eval-p5/budget.tsv`, in ogni cartella `<ora>-<etichetta>/`: `result.json` (VE8: campi costo/durata/token), `aggregate-result.json`, `report.html`, `stderr.txt` (rifiuti: `not granted`, errori di caricamento di `EnterWorktree`), `files/…` (esiti.txt, sonda-hooks.jsonl, sonda-scaffold.txt, hooks.jsonl sotto `.local/state/sonda`). `sonda-ve1-dependencies` = VE1; `sonda-radice-tmp` vs `sonda-skill` = D10. Se compare `COSTO-IGNOTO.txt` non lanciare altro.
2. `P5_TOKEN_ALLOW_PATHS=tests/test_git.py bash spikes/p5/run-p5-checks.sh ci-sonda` (o prima `bash spikes/p5/run-p5-checks.sh cerca-token` da solo; senza la variabile si ferma su `tests/test_git.py`). Crea `ginz0ls/tollgate` privato (una volta), spinge `main` e `p5-probe-ci*`, attende il run (`P5_WAIT_MAX` predefinito 3000 s). Guardare `docs/verifiche/evidenze/p5/`: `token-scan.txt`, `ci-repo-*`, `ci-push-*.err`, `ci-riepilogo.txt` (righe `sonda: rc=… durata=…` per ciascuna delle 4 combinazioni), `ci-log.out`, `ci-view.out`.
3. `bash spikes/p5/run-p5-checks.sh pins` - `pins.tsv` (SHA dereferenziati per maggiore), `pins-motore.tsv` (`using`, per decidere v4 o successiva).
4. `bash spikes/p5/run-p5-checks.sh detect-cache` (VG1): `cache-mode.txt`, `cache-pr.env`, `cache-verdict-log.out`. La PR si chiude da sola (trap).
5. `bash spikes/p5/run-p5-checks.sh detect-pin` (VG2, dopo `pins` per avere anche la controprova a SHA): `pin-iniziale.out`, `pin-on.*`, `pin-v4-log-failed.out`, `pin-v4-view.out`, `pin-sha-*`, `pin-dopo.out`. Alla fine deve stampare `sha_pinning_required rimesso a … (verificato)`; se stampa «RIPRISTINO NON VERIFICATO» rimetterlo a mano.
6. `bash spikes/p5/run-p5-checks.sh raccogli` - versioni, minuti di Actions (`raccogli-minuti.txt`), residuo (`raccogli-budget.txt`).
Tutte le uscite stanno in `docs/verifiche/evidenze/p5/` e `eval-p5/`, i file esistenti diventano `.prev-<ora>`; `comandi.log` ha ogni `gh` (anche i sondaggi di `gh_q`, dal giro 1) e `git-net` eseguito: `P4_PROFILE=p5 python3 -B -I spikes/gh-p4/ghguard.py comandi docs/verifiche/evidenze/p5/comandi.log` lo ricontrolla.
Variabili utili: `P5_WAIT_MAX`, `P5_POLL`, `P5_TOKEN_ALLOW_PATHS`, `P5_SOURCE_DIR`, `P5_TMP_TARGET`, `P5_EVAL_TIMEOUT` (secondi per invocazione, 1800).

## Fix round 1

Rilievi M1-M9 e lacuna di evidenza (la revisione era Approvato, nessun Critical/Important).
- **M1** `ghguard._infile` nel profilo p5 ammette solo `P4_OUT` e `P4_WORK` (niente `/tmp`, `$TMPDIR`); test `P5Round1Test.test_p5_body_files_only_from_out_and_work_never_tmp` (script/flow invariati).
- **M2** filtri `--jq`/`-q` del profilo p5: rifiutati `env`, `$ENV`, `input`, `inputs`, `input_filename`, `debug`, `stderr`, `$__…` (regex `JQ_FORBIDDEN`); i filtri normali (`.total_count`, `.[] | {context,state}`, `.inputs_count`) passano; test `test_p5_jq_filters_cannot_read_the_environment_or_other_input`.
- **M3** (non in elenco, ma gratuito): `comandi` in p5 esegue `_foreign_repo` sulla riga originale prima della riscrittura dei prefissi dei worktree; `_foreign_repo` ignora un `.git` finale (URL di `git-net`). Test `test_comandi_replay_does_not_hide_a_foreign_repo_behind_the_rewrite`.
- **M4** `CACHE_PR` assegnato dentro `open_pr_detect` subito dopo il parsing del numero. In `controlla`: il `gh` finto, con `P5_FAKE_LOCK_REGISTRY=1`, rende il registro di sola lettura dopo l'apertura, `register-pr` fallisce e il trap deve chiudere la PR: «detect-cache: PR chiusa dal trap dopo un errore».
- **M5** lo script toglie anche `GH_ENTERPRISE_TOKEN` e `GITHUB_ENTERPRISE_TOKEN` (oltre a `GH_HOST`, `GH_REPO`); NON `GH_TOKEN`, `GITHUB_TOKEN`, `GH_CONFIG_DIR`. Il `gh` finto registra quelle quattro variabili in `gh.log.env`; il test lancia `controlla` con `GH_HOST=altro.example GH_REPO=x/y GH_ENTERPRISE_TOKEN=a GITHUB_ENTERPRISE_TOKEN=b` e verifica che non arrivino mai.
- **M6** con costo ignoto si scrive anche la riga `…\t?\t?\t<caso>` in `budget.tsv`; `budget_cap` la rifiuta (fail-closed); `controlla` prova che, tolto `COSTO-IGNOTO.txt`, `eval-sonda` non lancia comunque `claude`. Dopo il controllo a mano il controller deve correggere la riga (e togliere `COSTO-IGNOTO.txt`).
- **M7** `P5_ONLY=etichetta,etichetta` (etichette: sonda-nl-bash sonda-nl-worktree sonda-ws-worktree sonda-skill sonda-radice-tmp sonda-ve1-dependencies); le altre sono «saltata»; un'etichetta sconosciuta ferma lo script prima di lanciare. Provato in `controlla` (2 invocazioni registrate).
- **M8** `GIT_TERMINAL_PROMPT=0` nell'ambiente di ogni `git` di rete; prova dinamica: il nudo di `tollgate` ha un hook `pre-receive` che registra la variabile ricevuta (deve essere `0`).
- **M9** `gh_q` ridefinita nello script (profilo p5): passa dalla guardia **e** scrive in `comandi.log`; quindi ora ogni `gh` eseguito è registrato (test: le righe `gh run list` di `comandi.log` = quelle del registro del `gh` finto). Il `comandi.log` dei sondaggi è più lungo (una riga per sondaggio).
- Aggiornato il comando del controller: per riprendere `eval-sonda` dopo un costo ignoto, `P5_ONLY=sonda-nl-worktree,sonda-ws-worktree,sonda-skill,sonda-radice-tmp,sonda-ve1-dependencies bash spikes/p5/run-p5-checks.sh eval-sonda`.

Test: `python3.11 -B -m unittest tests.test_p4_ghguard` -> `Ran 82 tests … OK`; `tests.test_p5_scripts` -> `Ran 50 tests … OK (skipped=2)`.

### Evidenza di `tests/run` completo (lacuna)
`tests/run` lanciato una volta in background dopo il giro 1:
```
== Python 3.11.16
Ran 2551 tests in 690.953s
OK (skipped=2)
== Python 3.13.5
Ran 2551 tests in 685.888s
OK
```
(Anche il primo lancio, prima del giro 1, era verde: 2542 test in 922.321s con 3.11 e 2542 test in 689.270s con 3.13.)

## Fix round 2

Esiti dell'esecuzione (`ve-analisi.md`): corse tenute in `/tmp/claude-eval-<sigla>/` con `home/` e `tmp/` sigillati in `sealed/` (000); Bash della sandbox in sola lettura (ipotesi: `//tmp` in `denyWrite` prevale); `python3` del PATH = shim di pyenv (127).
- `copy_run_files` riscritta: legge da stderr/stdout le righe «kept <dir>:», per le sole cartelle `*/claude-eval-*` fa `chmod 700 <dir> <dir>/sealed` e copia in `<invocazione>/corse/<sigla>/`: `trace.jsonl`; `settings.json` (solo se non contiene forme di token né chiavi `token|apikey|secret|password` con valore; altrimenti non lo copia e scrive `settings-non-copiato.txt`); i file della sonda di `sealed/home/cwd` (`sonda-*`, `esiti.txt`, `scritto-da-hook.md`, `ws-file`, `NEGATO`, `AMMESSO`, `WT-OK`, `EW-OK`, `SONDA-WRITE`, anche nei worktree); `sealed/home/.local/state/sonda/{hooks.jsonl,bin-sonda.txt}`; `sealed/home/.claude/plugins/installed_plugins.json`. Nient'altro dalla home sigillata (provato: `altro.txt`, `.bashrc` non copiati). Rimossa la vecchia ricerca euristica sotto `/tmp`. `cartelle-tenute.txt` sostituisce `cartelle-candidate.txt`.
- Modo **`raccogli-corse <dir>...`**: stessa copia per corse già fatte; la cartella di evidenza è quella il cui `result.json` ha una `tracePath` dentro la corsa (`jq`); senza corrispondenza salta e lo dice. Uso: `bash spikes/p5/run-p5-checks.sh raccogli-corse /tmp/claude-eval-6p3nnx /tmp/claude-eval-ALyAef /tmp/claude-eval-JUnd0s /tmp/claude-eval-IH4GbK /tmp/claude-eval-aAxqaU /tmp/claude-eval-xC9L1e /tmp/claude-eval-xUpQvI` (`cp -n`: non sovrascrive).
- `probe-bin/python3`: esegue `/usr/bin/python3` (se c'è, altrimenti il primo `python3` del PATH fuori da `/home` e dalla cartella dello shim; 127 se non c'è). Il PATH di chi lancia resta com'era dopo lo shim. Vale anche per la copia in `/tmp/tollgate-eval-target-sonda/probe-bin`.
- `eval_run` passa `TMPDIR=$P5_EVAL_TMPDIR` (predefinito `$HOME/.cache/tollgate-p5-eval-tmp`, creato 700) al solo `claude plugin eval`; rifiutato se sotto `/tmp`, `/var/tmp`, `/dev/shm` (non nel modo `controlla`, che usa una cartella temporanea); il valore (con `$HOME` al posto del percorso) è in `tmpdir.txt` di ogni invocazione. Nessuna modifica alla sandbox né ai permessi.
- `nl-bash`: passo 3 in un solo comando `cd .claude/worktrees/sonda-wt && touch WT-OK && pwd`, passo 4 comando separato con solo `pwd` (persistenza), passo 5 `sonda-shim`.
- `fake/claude.py` ora riproduce il formato reale (`kept <dir>:`, `out/trace.jsonl`, `config/settings.json`, `sealed/` 000, dir 500, `tracePath` nel JSON).
- Test: `ProbeBinTest` (shim di python3 contro un pyenv finto che esce con 127; sonda-shim), controlla (copia da cartella sigillata, niente di troppo, `raccogli-corse`, settings con credenziali, `P5_EVAL_TMPDIR` usato) e verifiche di forma. `tests.test_p5_scripts` + `tests.test_p4_ghguard`: `Ran 137 tests … OK (skipped=2)`.
- `tests/run` (una volta): 3.11 `Ran 2556 tests … OK (skipped=2)`; python3 (3.13) `Ran 2556 tests … OK`.

## Fix round 3

- **Important (recinto di `chmod`)**: nuova `run_dir_ok`, chiamata come prima cosa da `copy_one_run` (quindi da `copy_run_files` e da `raccogli-corse`, che la chiama anche prima di cercare l'evidenza): risolve con `realpath -e` e accetta solo un `basename` `claude-eval-?*` che sia figlio diretto di `/tmp` o della cartella temporanea dell'eval (`P5_EVAL_TMPDIR` o predefinita, risolta). Niente `chmod`, niente copia per il resto (`/x/claude-eval-a/b`, `sealed`, `/tmp`, la cartella temporanea stessa, un collegamento simbolico a una cartella fuori posto, una cartella `claude-eval-*` altrove). Il `case` non ancorato di `copy_run_files` è sparito. `controlla` prova 7 cartelle non valide: rifiutate, modo dei permessi invariato (500/0/500), niente in `corse/`.
- **Token in trace e file della sonda**: `cp_checked` applica `TOKEN_PATTERN` a ogni file prima di copiarlo (trace, file di `cwd`, stato della sonda, registro plugin); se lo trova non lo copia e scrive `file-non-copiati.txt` nella cartella della corsa (senza il testo); gli altri file si copiano. `controlla` con `P5_FAKE_TRACE_TOKEN=1`: trace non copiata e registrata, `esiti.txt` sì, nessun token nelle evidenze.
- **`eval_tmpdir`**: il controllo di `/tmp`, `/var/tmp`, `/dev/shm` è sul percorso risolto (`realpath -m` prima di creare, `realpath -e` dopo): `/var/tmp/../tmp/y`, `/dev/shm/../shm/z`, `/tmp/../tmp/w` e un collegamento a `/tmp` sono rifiutati prima di lanciare `claude` (provato con `P5_CHECK=0` e `claude` finto che non parte).
- Test: `tests.test_p5_scripts` `Ran 58 … OK (skipped=2)`. `tests/run` (una volta): 3.11 `Ran 2559 tests … OK (skipped=2)`; python3 (3.13) `Ran 2559 tests … OK`.

## Step 3 e 4
Rapporto `docs/verifiche/2026-10-23-p5-verifiche.md` ed evidenze (`p5/` 924 KB, `eval-p5/` 2,8 MB, 391 file, nessuno sopra 10 MB; nessun token; registri degli hook solo con le chiavi ammesse) committati. `tests/run` lanciato prima del commit: 3.11 Ran 2559 OK, python3 Ran 2559 OK.
