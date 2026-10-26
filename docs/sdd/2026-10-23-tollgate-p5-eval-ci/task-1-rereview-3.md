# Ri-revisione del giro 3 del Task 1 (9d5c802..001d0d8)

Letti: regole, rilievi aperti del giro 2, «Fix round 3» del report, diff. Eseguito solo `bash -n` su `run-p5-checks.sh` (ok). Nessuno script lanciato.

### Verdetti sui rilievi

1. **(Important) `chmod 700` e copia solo su cartelle `claude-eval-*` figlie dirette di `/tmp` o del `TMPDIR` dell'eval, percorso risolto, anche da `raccogli-corse`.** INDIRIZZATO.
   `run-p5-checks.sh` `run_dir_ok` (righe 190-200): `realpath -e`, basename `claude-eval-?*`, parent uguale a `/tmp` o al `P5_EVAL_TMPDIR`/predefinito risolto con `realpath -m`. `copy_one_run` (riga 215) la chiama prima di qualunque `chmod`/`mkdir`/`cp`; `modo_raccogli_corse` (riga 260) la chiama prima di cercare l'evidenza. Il `case` non ancorato di `copy_run_files` è sostituito dal solo `copy_one_run`. Poiché il basename e il parent si leggono sul percorso risolto, `/x/claude-eval-a/b`, `sealed`, `/tmp`, la cartella temporanea, i collegamenti verso cartelle fuori posto e le `claude-eval-*` altrove sono rifiutati. `controlla` prova 7 casi, conta 7 rifiuti, verifica i modi invariati (500 0 500) e che nulla sia copiato; test `test_raccogli_corse_refuses_anything_...`.
2. **(Minor) `TOKEN_PATTERN` su ogni file copiato.** INDIRIZZATO.
   `cp_checked` (righe 203-210) usa `grep -aqE "$TOKEN_PATTERN"`; usata per trace, file di `cwd`, tre file di stato della sonda e registro plugin. Il file con token non si copia, si annota in `file-non-copiati.txt` senza il testo; gli altri si copiano. Provato con `P5_FAKE_TRACE_TOKEN=1` (token costruito a runtime nel finto) e controllo che nessun `ghp_bbbb` resti nelle evidenze; test `test_a_token_in_the_trace_...`. Le uniche copie non passanti per `cp_checked` sono le `settings.json`, che hanno già il proprio grep più largo.
3. **(Minor) `eval_tmpdir` con percorso risolto contro `..` e collegamenti.** INDIRIZZATO.
   `eval_tmpdir`: `realpath -m` prima di creare e rifiuto su `/tmp`, `/var/tmp`, `/dev/shm`; poi `mkdir`/`chmod 700` sul risolto, `realpath -e` e secondo controllo; stampa il percorso risolto (usato come `TMPDIR` e come parent per `run_dir_ok`). `controlla` prova 5 percorsi (`/tmp/x`, `/var/tmp/../tmp/y`, `/dev/shm/../shm/z`, collegamento a `/tmp`, `/tmp/../tmp/w`), verifica motivo del rifiuto e che `claude` non sia partito; test `test_eval_tmpdir_is_compared_after_realpath`.

### Danni nuovi nel diff della correzione

Nessuno Critical/Important. Annotazione Minor non bloccante: `run_dir_ok` accetta anche una `claude-eval-*` figlia di `/tmp` non creata dall'eval (per scelta esplicita del rilievo); `grep` su file illeggibile restituisce 2 e lascia passare a `cp`, che fallirebbe comunque.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
