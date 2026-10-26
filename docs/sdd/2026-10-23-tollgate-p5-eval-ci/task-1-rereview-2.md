# Ri-revisione del giro 2 del Task 1 (30f9b6f..9d5c802)

Letti: regole, ve-analisi, «Fix round 2» del report, diff. Nessuno script eseguito.

### Verdetti sui rilievi

1. **`copy_run_files` copia da cartelle sigillate solo trace, settings senza credenziali, file della sonda, nient'altro.** INDIRIZZATO.
   `run-p5-checks.sh` `copy_one_run`: `chmod 700 "$run"` e `"$run/sealed"`, poi copia `out/trace.jsonl`; `config/settings.json` solo se il grep (TOKEN_PATTERN + chiavi token/api_key/secret/password con valore stringa) non trova nulla, altrimenti scrive `settings-non-copiato.txt`; da `sealed/home/cwd` solo `find -type f` con la lista `SONDA_FILES` (niente symlink, `-size -300k`); dalla home sigillata solo tre percorsi fissi (`hooks.jsonl`, `bin-sonda.txt`, `installed_plugins.json`). `.bashrc` e `altro.txt` finti non vengono copiati (controllo in `modo_controlla` e `test_eval_evidence_is_kept...`). `cp -n`. Il test della copia con credenziali è coperto (`P5_FAKE_SETTINGS_TOKEN`). Dal modo automatico le cartelle sono solo quelle `kept <dir>:` di stderr/stdout filtrate da `*/claude-eval-*`.
2. **Modo `raccogli-corse <dir>...` con evidenza dedotta da `tracePath`.** INDIRIZZATO. `modo_raccogli_corse` con `jq` su `tracePath` che inizia con `<corsa>/`; salta e lo dice se non c'è corrispondenza. Provato in `controlla` (mv di `corse`, poi raccolta).
3. **`python3` nello shim verso `/usr/bin/python3` o primo fuori da `/home`.** INDIRIZZATO. `probe-bin/python3:4-11`; copiato anche nel target in `/tmp` (`cp -a probe-bin/.`, riga 325); `ProbeBinTest` lo prova contro un pyenv finto con 127 e verifica che `sonda-shim` giri.
4. **`P5_EVAL_TMPDIR` fuori da `/tmp`, `/var/tmp`, `/dev/shm`, passato come `TMPDIR` al solo eval.** INDIRIZZATO. `eval_tmpdir` (rifiuta quei prefissi fuori da `controlla`, 700), `TMPDIR="$evtmp"` solo nel prefisso del comando `timeout ... claude` dentro la subshell (riga 272 del nuovo file); nessuna modifica a sandbox/permessi/`--allow-tools`.
5. **`nl-bash`: `cd` e passi nello stesso comando, più `pwd` separato.** INDIRIZZATO. `nl-bash/case.yaml` passi 3-5; test di forma aggiornato; i grader (WT-OK nel worktree, NEGATO/AMMESSO) restano coerenti.

### Danni nuovi nel diff della correzione

- **Important** — `run-p5-checks.sh` `modo_raccogli_corse` / `copy_one_run`: il `chmod 700` colpisce QUALSIASI cartella passata a `raccogli-corse`, perché il vincolo `*/claude-eval-*` c'è solo in `copy_run_files`. L'unica barriera è che un `result.json` abbia una `tracePath` che inizia con `<dir>/`: qualunque antenato di una corsa (`/tmp`, `~/.cache`, la cartella `P5_EVAL_TMPDIR`) la soddisfa, e allora `chmod 700 <dir> <dir>/sealed` (se esiste) viene eseguito su una cartella non `claude-eval-*`. Correzione: in `modo_raccogli_corse` (o in `copy_one_run`) rifiutare quando `basename "$run"` non corrisponde a `claude-eval-*`; nel `case` di `copy_run_files` usare `*/claude-eval-*` solo sul basename (oggi `/x/claude-eval-a/b` passa).
- **Minor** — `copy_one_run`: la scansione di credenziali vale solo per `settings.json`; `trace.jsonl` e i file della sonda copiati non passano per `TOKEN_PATTERN`. Rischio basso (le credenziali sono negate all'agente), ma una passata `grep -E "$TOKEN_PATTERN"` sulla cartella `corse/` prima di chiudere, con rifiuto della copia, sarebbe a costo zero.
- **Minor** — `eval_tmpdir`: il rifiuto di `/tmp` ecc. è un confronto di stringa; un percorso con `..` o un link simbolico verso `/tmp` lo aggira (nessun danno se non per errore dell'operatore).

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Rilievi ancora aperti. I cinque rilievi richiesti sono indirizzati, ma il controllo specifico chiesto («il `chmod` tocchi solo cartelle `claude-eval-*`») non regge nel modo `raccogli-corse` (danno Important sopra). Correzione di due righe. Il resto passa.
