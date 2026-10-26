# Ri-revisione giro 1 del Task 1 (dcd0485..30f9b6f)

Letto il diff una volta, il report ("Fix round 1") e il codice toccato. Controlli: `bash -n` sullo script (ok); `controlla` lanciato una volta in scratchpad con `GH_HOST`, `GH_REPO`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN` impostati: uscita 0, "CONTROLLA: ok", con le righe nuove (PR chiusa dal trap, riga `?`, fail-closed, P5_ONLY 2 invocazioni, variabili non arrivate, GIT_TERMINAL_PROMPT=0). Nessun `claude` o `gh` vero, nessuna rete.

### Verdetti sui rilievi

- **M1 — `--body-file` da `/tmp`/`$TMPDIR` nel profilo p5**: INDIRIZZATO. `ghguard.py:_infile` ora ritorna per p5 solo `_under(P4_OUT) or _under(P4_WORK)` prima del ramo con le cartelle temporanee; `script` invariato; test `P5Round1Test.test_p5_body_files_only_from_out_and_work_never_tmp` (`/tmp`, `$TMPDIR` largo, `..`, `/etc`).
- **M2 — `--jq`/`-q` con `env`/`$ENV`**: INDIRIZZATO. `_check_api_read` rifiuta in p5 il valore che corrisponde a `JQ_FORBIDDEN` (`env`, `input(s)`, `input_filename`, `debug`, `stderr`, `$ENV`, `$__…`) con confini di parola; `--jq` esiste solo in `gh api` (`API_VALUED`, unico uso) e le forme `--jq=…`/`-qX` sono già rifiutate come opzioni sconosciute. Test su 13 filtri vietati x 2 opzioni e 6 ammessi (`.inputs_count`, `.environment_name`, `.reinput`). È una lista di divieti, non di ammessi (vedi osservazioni).
- **M3 — rigioco `comandi` che nasconde un repo estraneo**: INDIRIZZATO. `check_comandi` esegue `_foreign_repo` sulla riga grezza prima di `moved.sub` (solo p5); `_foreign_repo` ignora un `.git` finale così le righe `git-net` con URL dei due repo passano (confermato da `controlla`, che rigioca il registro). Test `test_comandi_replay_does_not_hide_a_foreign_repo_behind_the_rewrite` con la riga manomessa della revisione.
- **M4 — PR orfana se `open_pr_detect` muore dopo `pr create`**: INDIRIZZATO. `CACHE_PR="$PR_NUM"` subito dopo il controllo del numero (`run-p5-checks.sh:315`), prima di `register-pr`; l'assegnazione fuori è tolta; `open_pr_detect` ha un solo chiamante (`:456`, con `trap close_cache_pr EXIT`). Prova dinamica in `controlla`: registro reso sola lettura dal `gh` finto, `register-pr` fallisce, `pr close` aumenta ("PR chiusa dal trap dopo un errore", riprodotto da me).
- **M5 — togliere solo `GH_HOST`, `GH_REPO`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`; restano `GH_TOKEN`, `GITHUB_TOKEN`, `GH_CONFIG_DIR`**: INDIRIZZATO. `unset` a `run-p5-checks.sh:~32` elenca esattamente le quattro (più le `GIT_*` preesistenti), nessuna delle tre da tenere. Il `gh` finto registra le quattro in `gh.log.env`; il test passa i valori sporchi a `controlla` e richiede che ogni campo sia vuoto; riprodotto da me (esce "non arrivano mai").
- **M6 — riga `?` in `budget.tsv` a costo ignoto**: INDIRIZZATO. Prima del `die` si scrive `ora<TAB>etichetta (abl)<TAB>?<TAB>?<TAB>caso`; `COSTO-IGNOTO.txt` resta. `controlla` toglie `COSTO-IGNOTO.txt` e verifica che `eval-sonda` non lanci comunque `claude` (budget_cap rifiuta la riga): fail-closed anche senza il file.
- **M7 — `P5_ONLY`**: INDIRIZZATO. `eval_run` salta le etichette non elencate prima di `ensure_budget` e di qualunque costo; `modo_eval_sonda` convalida le etichette contro `EVAL_LABELS` (le sei usate in `:261-280`, verificate una per una) prima di lanciare; un'etichetta sconosciuta ferma. Test: 2 righe `sonda-skill (none)`, `sonda-ve1-dependencies (none)`, errore su etichetta sbagliata, "saltata" nel log.
- **M8 — `GIT_TERMINAL_PROMPT=0`**: INDIRIZZATO. `genv=(env GIT_TERMINAL_PROMPT=0)` in `git_net`, unico punto per la rete; prova dinamica con `pre-receive` sul nudo di tollgate che registra il valore ricevuto (`0`), riprodotta.
- **M9 — `gh_q` non registrato**: INDIRIZZATO. `gh_q` ridefinita dopo `. common.sh`: `guard_args`, `log_cmd`, `gh`. Test: le righe `gh run list` di `comandi.log` uguali a quelle del `gh` finto. Il comportamento di esecuzione (stderr scartato, stdin chiuso) è identico all'originale di `common.sh`; P4 non toccato.
- **Lacuna: evidenza di `tests/run` completo**: INDIRIZZATO. Il report riporta l'uscita: 3.11 "Ran 2551 tests … OK (skipped=2)", 3.13 "Ran 2551 tests … OK", più il giro precedente (2542). Coerente col diff: +9 test (3 in `test_p4_ghguard`, 6 in `test_p5_scripts`) e skip=2 solo sul 3.11 (i due test YAML senza PyYAML). Non rilanciata, come da regole.

### Danni nuovi nel diff della correzione

Nessuno Critical/Important. Minor:
- `tests/test_p5_scripts.py` (`test_gh_is_only_called_through_the_guarded_helpers`): l'esenzione per le righe che cominciano per `gh_q()` esenta l'intera riga, che contiene un `gh "$@"` nudo (voluto, è la definizione). Un `gh` nudo aggiunto sulla stessa riga non verrebbe visto. Rischio basso.
- `JQ_FORBIDDEN` è una lista di divieti: oggi copre le uscite verso l'ambiente (`env`, `$ENV`) che erano il rischio nominato; altre funzioni di gojq non sono vietate, ma lo script p5 non usa `--jq` con filtri esterni.

### Osservazioni fuori ambito

- Dopo il controllo a mano di un costo ignoto, il controller deve correggere la riga `?` in `budget.tsv` e togliere `COSTO-IGNOTO.txt` (il report lo dice). `evals/cost.py` del Task 11 dovrà tollerare o rifiutare esplicitamente la riga `?` finché esiste.
- Restano M10/M11 della revisione (scelte del controller / da guardare alla prima esecuzione).

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
