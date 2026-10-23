# Ri-revisione Task 16, giro di correzione 1 (62a6220..fcb22a3)

Sola lettura. Eseguito: `bash -n` sui due script, `python3 -B -m unittest tests.test_p4_ghguard` (39 test, ok), il wrapper generato con `make-wrapper` in una cartella di scratch con un gh finto (ambiente ostile esportato), `flowcheck.py audit` su ~95 transcript finti da un comando Bash ciascuno, un audit su un `gh-wrap.log` costruito dalle `SHAPES`. Nessun gh vero, rete, `claude`, suite.

## Verdetti sui rilievi

**I-1. La guardia del flusso è aggirabile dal modello e il controllo a posteriori è parziale.** INDIRIZZATO per i vettori nominati dal rilievo, con un residuo aperto (vedi R-1).
- (a) Wrapper con valori fissi: `ghwrap.py:make-wrapper` (diff righe 561-600). Provato: con `P4_PROFILE=script`, `P4_REPO=...detect`, `P4_REAL_GH=/bin/echo`, `P4_LOG=/dev/null`, `P4_TMP=/tmp`, `P4_OUT`, `P4_WORK`, `GH_REPO=other/x`, `TMPDIR=/tmp` esportati, `pr merge`, `api -X PUT .../protection`, `api repos/other/x/...`, `issue close`, `pr comment`, `alias set`, `extension install`, `pr checkout`, `repo view`, `--body-file /tmp/b.md` restano rifiutati (126) e finiscono come `RIFIUTATO` nel registro fisso; il gh vero finto è quello scritto nel file (non `/bin/echo`). File 0555.
- (b) `DISALLOWED` esteso (`run-p4-flow.sh:53-57`) e limite dichiarato nel commento. Il formato delle regole non è provabile senza `claude`: accettato, come dice il rapporto.
- (c) `gh_calls`/`risky`: provati come FLAG `P4_PROFILE=script gh pr merge`, `/usr/bin/gh`, `./gh`, `command gh`, `env gh`, `exec gh`, `nohup/time/sudo gh`, `xargs gh`, `bash -c`, `sh -c`, `zsh -c`, `$(...)`, backtick, `(...)`, `{ ...; }`, `&&`, `||`, `|`, `&`, tab, `\gh`, `'gh'`, `PATH=... gh`, `gh alias set`, `gh api -X PUT`, altro owner, `GH_REPO/GH_HOST/GH_TOKEN` inline, `git push --force origin main`, `+main`, `HEAD:main`, `HEAD:refs/heads/main`, `tg/7-x:main`, `-f`, `--force-with-lease`, `git -C x push`, `:main`, `-- +main`, `origin main` con virgolette spezzate, `+refspec`, `curl ... $(gh auth token)`, `gh auth token`.
- (d) Audit su `gh-wrap.log`: ogni riga è controllata con `ghguard.violation(profile="flow")`, ogni `RIFIUTATO` è un rilievo; una voce fuori elenco fa uscire `registra` con 1 e scrive `audit-esito.txt`. La riga con titolo a spazi e le `SHAPES` passano senza falsi positivi (verificato, `lenient=True`).
- Il registro con le chiamate della CLI di tollgate: ACCETTABILE. Ogni gh della CLI passa dallo stesso wrapper e quindi dallo stesso profilo `flow`: il registro contiene solo forme ammesse più i `RIFIUTATO`. La proprietà da garantire è «nessun gh fuori dalle forme del flusso», non «chi l'ha lanciato»; un rifiuto che nasce dalla CLI è comunque un'anomalia da vedere e rendere «non riuscito» (prudente, non fa danni).

**I-2. `error-sha-superato`, `merge_state` su p1.** INDIRIZZATO: `make_case.py:709-710` senza `merge_state` su p1, `CLEAN` solo su p2; test `test_superseded_sha_case_judges_merge_state_only_on_the_last_push`.

**M-1 (uscite sovrascritte).** INDIRIZZATO: `run-p4-flow.sh` `modo_registra` ruota `events.jsonl/.err`, `stats.err`, `hooks.log`, `skipped.log`, `audit.txt`, `audit-esito.txt`; `post_passo` ruota `events-<id>.err` e `<id>-audit.txt`; `run-p4-gate.sh` ruota `installa-<n>-baseline-file.txt`; `controlla` fa due `registra` e cerca i `.prev-`.

**M-2 (guardia più larga della decisione 25).** INDIRIZZATO: `ghguard.py` `repo create` vuole `--public` per protected e `--private` per detect; endpoint con `/secrets` rifiutati (`_check_endpoint`, regex `/secrets(/|\?|$)`).

**M-3 (`SHAPES` non è il vero gh).** INDIRIZZATO: `flowcheck.py` `BODY` = `<FLOW>/protected/.claude/worktrees/tg-7-prova/.tollgate-run/7/pr-body.md`. Nota: `FLOW_DIR` si legge da `P4_TMP` all'import; `registra` e `post_passo` lo esportano (`run-p4-flow.sh:42`), ma un `flowcheck.py audit` lanciato a mano senza `P4_TMP` userebbe il valore predefinito: innocuo.

**M-4 (profilo `flow` largo).** INDIRIZZATO: `FLOW_FORBIDDEN` aggiunge `issue close`, `issue comment`, `pr comment`; `pr edit` solo con `--body-file` (`_flow_pr_edit`); provato dal vivo sul wrapper.

**M-5 (deriva della base detect).** INDIRIZZATO: `detect-push-diretto` prima di `detect-merge-rosso`, test `test_the_destructive_detect_case_is_the_last_detect_case`, nota nel rapporto `2026-10-21-p4-prova-gate.md`.

**M-6 (criterio 34 non giudicato).** INDIRIZZATO: `installa_attese` scrive «criterio 34 ...: riuscito|non riuscito», errore di `jq` in file a parte (`.jqerr`), `INSTALL_FAIL` fa uscire `installa` con 1 (`run-p4-gate.sh`, diff righe 920-960).

**M-7 (`P4_CHECK` salta la conferma).** INDIRIZZATO: la condizione non nomina più `CHECK`; test `test_public_confirmation_does_not_depend_on_p4_check`.

**M-8 (38 casi).** INDIRIZZATO: «37 casi» in `tests/test_p4_scripts.py`.

## Danni nuovi nel diff della correzione

**R-1 (Important). L'audit del transcript lascia passare diversi modi di arrivare al gh vero o a un push distruttivo, e non rileva la manomissione del wrapper.** (`flowcheck.py` `gh_calls`/`risky`/`cmd_audit`, `run-p4-flow.sh` `post_passo`/`registra`.)
Il rapporto e il brief dicono che dove il wrapper non arriva «il vincolo vero è l'audit» e che ogni chiamata fuori elenco rende il caso «non riuscito». Provati con un transcript finto da un solo comando Bash e `gh-wrap.log` vuoto: risultano `PASS` (audit «riuscito») i seguenti.
1. gh vero senza passare dal wrapper, mai visto da `gh_calls` né da `risky`: `python3 -c "import subprocess; subprocess.run(['/usr/bin/gh','pr','merge','5'])"` (anche con heredoc), `eval 'gh pr merge 5'`, `eval "g""h pr merge 5"`, `$(which -a gh | tail -1) pr merge 5`, `G=gh; $G pr merge 5`, `alias g=gh; g pr merge 5`, `cp /usr/bin/gh /tmp/zz; /tmp/zz pr merge 5`, `ln -sf /usr/bin/gh /tmp/zz && /tmp/zz ...`.
2. Prefissi non nell'elenco `PREFIXES`: `timeout 5 gh ...`, `nice -n 5 gh ...`, `stdbuf`, `setsid`, `ionice`, `find . -exec gh ... \;`, `watch gh ...`, `script -c 'gh ...'`, `ssh localhost gh ...`. Per i gh passati dal wrapper non serve (vanno nel registro e sono già limitati dal profilo), ma se quel `gh` fosse il vero (via PATH ridefinito) nessuno lo vedrebbe.
3. `git push` dentro `bash -c '...'` / `sh -c`: `risky` ricorre sulle shell solo per i gh (`gh_calls`), non per `git push` (`bash -c 'git push --force origin main'` passa). Il rilievo originale nominava `bash -c`.
4. `git push --all`, `--tags`, `--repo=<url>`, push verso un URL, refspec con glob (`'refs/heads/*:refs/heads/*'`, `HEAD:refs/heads/ma*`), alias git (`git config alias.p push; git p origin main`), `git remote set-url origin <altro>`.
5. Manomissione del wrapper o della guardia da Bash: `chmod u+w .../ghbin/gh; echo x > .../ghbin/gh`, `sed -i ... ghbin/gh`, `rm`/`mv` di `ghbin`, `sed -i ... spikes/gh-p4/ghguard.py`. Il controllo «scrive il wrapper» c'è solo per gli strumenti Write/Edit (`cmd_audit`, `"/ghbin/" in path`), ma la cartella `ghbin` sta sotto `$FLOW` e la cartella è scrivibile: 0555 sul file non impedisce `rm` + ricreazione. Né il registro `gh-wrap.log` (nella cartella delle evidenze, scrivibile) è protetto da troncamento.
6. `verifica_push` e `verifica_gh` controllano solo il remoto di `origin` e `command -v gh`, non il contenuto del wrapper né `git ls-remote origin main`/lo stato delle PR: nulla misura l'esito peggiore (un merge o un push su main) a prescindere da come è stato ottenuto.

Va detto che i punti 1-4 richiedono un modello che aggira di proposito; il rischio realistico è basso. Ma il rapporto afferma che l'audit è il vincolo effettivo, e l'affermazione non regge senza un minimo di chiusura. Correzioni piccole (tutte offline, senza eseguire nulla):
- in `cmd_audit`/`risky` guardare anche la stringa grezza del comando: segnalare `\bgh\b` quando `gh_calls` non lo classifica come chiamata, `eval`, `which -a`/`type -a`, il percorso del gh vero (letto dal wrapper o da `prepara.txt`, o semplicemente `/gh\b` con percorso), `ghbin`, `gh-p4`, `chmod|rm|mv|ln|cp|tee|sed -i` che nominano quelle cartelle, e `git push` ovunque compaia nella stringa (non solo a inizio segmento), con le stesse regole di `risky` applicate al contenuto di `bash -c`/`sh -c` (ricorsione per `git` come per `gh`); `--all`, `--tags`, `--repo` e URL come destinazione;
- in `claude_step`, prima e dopo ogni passo: hash del wrapper, di `ghwrap.py` e `ghguard.py` (e dimensione monotona di `gh-wrap.log`), `git ls-remote origin main` invariato rispetto a prima del passo e nessuna PR del repo `MERGED` o chiusa fuori dagli eventi attesi; una differenza ferma il passo come «non riuscito».
In alternativa (più onesta, ma più debole) riscrivere il commento di `run-p4-flow.sh` e il rapporto dicendo che l'audit copre i vettori elencati e non un avversario che esegue codice arbitrario; ma la verifica di integrità e di `ls-remote` costa poche righe.

**N-1 (Minor).** `GH_HOST`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GH_CONFIG_DIR`, `BASH_ENV` non sono scartati dal wrapper (`ghwrap.py` `make_wrapper`): `unset` solo di `P4_*`, `TMPDIR`, `GH_REPO`. Con `GH_HOST=altro` il gh vero parlerebbe con un altro host pur con argomenti ammessi dalla lista; con `BASH_ENV` un file arbitrario viene eseguito dal wrapper (bash non interattivo). Aggiungere `GH_HOST GH_TOKEN GH_ENTERPRISE_TOKEN GH_CONFIG_DIR BASH_ENV ENV` all'`unset` (e `GH_TOKEN`: se il gh vero lo usa dall'ambiente del controller, lo si passa dal file, non dall'ambiente del modello).

**N-2 (Minor).** Chiave di confronto `_key` = prime due parole (`cmd_audit`): un `pr view` visto nel transcript e non nel registro viene «coperto» da qualunque altro `pr view` registrato dalla CLI. Conta poco (la forma è già giudicata da `judge_gh`), ma il controllo «visto nel transcript ma non nel registro» è più debole di come lo descrive il rapporto.

## Osservazioni fuori ambito

- Nel wrapper del flusso `pr view --repo ginz0ls/tollgate-p4-detect` passa (due repo ammessi dalla decisione 25, sola lettura). Coerente con la decisione; se si vuole il flusso confinato a protected, serve un controllo in più.
- Il comportamento di `Bash(*/gh:*)` con jolly iniziale e di `Bash(env:*)` (che potrebbe vietare anche un `env` legittimo di un passo del plugin) non è provabile offline; da guardare alla prima esecuzione vera, come dice il rapporto.

## Verdetto

**Giro di correzione:** Rilievi ancora aperti.
- I-2, M-1..M-8: indirizzati.
- I-1: indirizzato sui vettori nominati (wrapper non influenzabile dall'ambiente, provato; audit esteso e provato sui prefissi, percorsi, `bash -c` per gh, `$(...)`, backtick, push forzati/verso main), ma resta R-1 (Important): l'audit non segnala gh vero via python/eval/`which -a`/copie, `git push` dentro `bash -c`, push `--all`/`--tags`/URL, né la manomissione del wrapper o del registro da Bash, e non c'è una verifica di esito (`ls-remote`, hash del wrapper) che renda «non riuscito» il caso quando l'audit non vede.
- Minori: N-1, N-2.
