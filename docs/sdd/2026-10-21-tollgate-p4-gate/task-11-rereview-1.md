# Ri-revisione Task 11, giro di correzione 1 (5475e54..8c3b417)

Revisore: opus. Ho letto le cautele, le regole, il brief, il carry, la revisione, il ruling del giro 1 (con il vincolo `BASE_JOB`), i ruling in `progress.md` (compreso quello sull'albero al posto dello `sha`), il «Fix round 1» del report e il diff. Fuori dal diff ho fatto solo letture mirate: `gate/workflows/tollgate-base.yml` com'è a 8c3b417, `cli._field`/`_default_tip`/`GateUsageError`, `github.set_status`, `runner.ids_commands`, `run.STATES`.

Ho eseguito un solo test mirato: `python3 -B -m unittest tests.test_gate_workflows tests.test_gate_sentinel.BasePublishFromTest tests.test_gate_sentinel.BasePublishProtectedErrorTest`. Risultato: 36 test, OK. Il working tree contiene modifiche non committate del Task 12 (`init.py`, `install.py`, `fakegh.py`, `test_init.py`) e non le ho valutate.

### Verdetti sui rilievi

**C-1: `tollgate-base` eseguiva la suite del progetto in un job con `statuses: write`, `issues: write` e `GH_TOKEN`.** INDIRIZZATO.
- `tollgate-base.yml:15-47`: il job `ids` ha `permissions: {contents: read}` a livello di job. Questi permessi sostituiscono per intero quelli del workflow (righe 6-9). Il job non ha `GH_TOKEN`, `github.token` né `secrets.*`. Lancia `gate base-ids` senza `--publish` e solo sul miss (riga 35), salva la cache solo sul miss e carica sempre `ids.json` (`if: always()`, `if-no-files-found: ignore`).
- `tollgate-base.yml:48-70`: il job `tollgate-base` (`needs: ids`, `if: always()`) fa un solo checkout, del predefinito, con `persist-credentials: false`. Scarica l'artefatto sotto `runner.temp` con `continue-on-error: true` ed esegue una sola riga `run:`, `gate base-publish … --publish`. Non c'è `setup` e non c'è nessun comando del progetto.
- Da dove viene la CLI che pubblica: `python3 .github/tollgate/bin/tollgate`, dal checkout della punta del predefinito, che sul push coincide con il commit spinto (o con uno successivo). Un commit spinto può sostituirla. Però lo stesso commit sostituisce anche `.github/workflows/tollgate-base.yml`, perché sul `push` GitHub legge il workflow dal commit spinto. Sostituire la CLI quindi non dà niente in più rispetto al limite già intrinseco del predefinito. In più `.github/tollgate/bin` è un file di tollgate, coperto da guard e da `FINGERPRINT`.
- La strada di C-1 era codice di una PR verificata (test, aiuti di test, `setup`) che girava col token. Ora quel codice gira solo in `ids`, che non ha token di scrittura. Python avvia la CLI con `sys.path[0]` uguale alla cartella dello script, non alla cartella di lavoro. Nel job di pubblicazione girano solo `git rev-parse` e `gh api`, che non leggono hook né configurazione dal repo. Resta il limite dichiarato: il codice unito può falsificare `ids.json`. Non vedo niente di più grave, salvo la nota sulla cache più sotto, che esisteva già prima della correzione.
- `baseids.read_result` (`baseids.py:108-127`) è fail-closed. Rifiuta un collegamento simbolico, un file non regolare, un file oltre `MAX_IDS_FILE`, un JSON non valido o annidato a fondo (`RecursionError` ricade in `except Exception`), una versione diversa, un albero diverso, un `commands` che non è un dict, nomi fuori dai comandi di `ids_commands` della configurazione e stati fuori da `run.STATES`. Lo SHA su cui scrive è sempre `after` dell'evento di GitHub (`cli.py:216`), mai un valore dell'artefatto. L'issue è sempre quella di sentinella (`report_sentinel`). Nel testo dell'issue entrano solo i nomi che stanno nella configurazione del predefinito. Il nome ostile `x`\n# evil` è rifiutato (test `test_hostile_json_is_error`).
- Confronto dell'albero: `publish_from` calcola `rev-parse after^{tree}` sul checkout fidato e lo confronta con `data["tree"]`, come prevede il ruling. Su un cache hit `ids` carica l'`ids.json` ripristinato, che ha lo stesso albero, e `tollgate/base` viene pubblicato (`test_valid_data_publishes_the_status_even_from_a_cache_hit`). Un artefatto mancante o non valido dà `error` in `detect` e codice 1 in ogni modalità (`test_missing_artifact_is_error`, `test_other_tree_is_error`, `test_symlink_and_oversize_are_error`, `BasePublishProtectedErrorTest`).
- `--publish` non c'è più in `base-ids` (`cli.py:158-165`): passarlo dà l'errore di argomento (exit 2, `test_publish_refused_outside_actions`). `base-publish` ha `allow_abbrev=False` e `_require_actions`. Il guardrail di `cli_calls` vale anche per `base-publish` (`test_check_cli_calls.py:533`). Nessun workflow usa più `base-ids --publish`, e `test_run_lines_pass_the_cli_parser` lo garantirebbe comunque, perché la forma vecchia non supera il parser.
- Vincolo `BASE_JOB`: la chiave del job di pubblicazione è `tollgate-base`, il job `ids` ha un nome diverso, e `test_publish_job_name_is_the_one_protection_reads` lega il nome a `protection.BASE_JOB`.
- Test richiesti dal ruling: ci sono tutti. `test_no_job_runs_project_commands_with_write_or_token` controlla i permessi effettivi di ogni job, anche quelli ereditati, più `GH_TOKEN` e `github.token`, e conta 3 job. `test_base_ids_job_is_read_only_and_publish_job_runs_no_project_code` completa il controllo.

**I-1: i servizi mancavano dove gira la suite della base.** INDIRIZZATO. `install.py:277,316-331` inserisce lo stesso blocco nei segnaposto di `head` e `base` di `tollgate-run` (`tollgate-run.yml:486`) e di `ids` di `tollgate-base` (`tollgate-base.yml:19`). Il numero di segnaposto per workflow è fissato (`SERVICES_WORKFLOWS`), e un conteggio diverso solleva un errore. Le porte del Task 12 entrano nello stesso blocco. `test_services_go_in_every_job_that_runs_the_suite` pretende blocchi identici nei tre job e assenti negli altri. `test_init.py` è aggiornato di conseguenza.

**M-1: `re.match` con `$` accettava un `\n` finale.** INDIRIZZATO. `fullmatch` in `install.py:300,303,344`. Coperto dai test con `"main\n"`, `"x\n"` e `"db\n"`.

**M-2: valori senza virgolette nello YAML, immagine con `:` finale.** INDIRIZZATO. `install.py:306` scrive nome e immagine tra virgolette singole, `tollgate-base.yml:5` e `tollgate-sentinel.yml` scrivono il ramo tra virgolette singole, e `image.endswith(":")` viene rifiutato. Le regex escludono `'`, quindi le virgolette non si possono chiudere. Test: rami `true`, `123`, `null`, `on`; servizio `true`; immagine `postgres:` rifiutata.

**M-3: il test non difendeva «espressioni solo in `with:`, `if:`, `concurrency:`, `env:`».** INDIRIZZATO. `test_expressions_only_in_allowed_places`.

**M-5: nessun test diceva che verdict non ha `if:` sulla conclusione.** INDIRIZZATO. `test_verdict_has_no_condition_on_conclusion`: nessun `if:` con `conclusion`, nessun `if:` a livello di job, e la parola `conclusion` assente da tutto il file.

**M-6: i flag dei `run:` non erano confrontati con il parser.** INDIRIZZATO. `test_run_lines_pass_the_cli_parser` controlla 7 invocazioni. Un errore del parser dà `SystemExit`, che unittest registra come errore.

**M-7: `test_token_only_in_env` non vedeva `secrets.GITHUB_TOKEN`.** INDIRIZZATO.

**M-8: push forzato documentato.** INDIRIZZATO. Commento in `tollgate-base.yml:10-13`.

(M-4 e M-9 sono rinviati dal ruling: non li valuto.)

### Danni nuovi nel diff della correzione

- **Minor**, `tests/test_gate_workflows.py`, `test_token_only_in_env`: il corpo dell'`if` è rientrato di 12 spazi in più rispetto allo stile del file, con la continuazione disallineata. È Python valido e il comportamento è corretto, ma è solo un difetto di formattazione.
- **Minor**, `baseids.publish_from`: un `ConfigError` (configurazione del predefinito illeggibile) o un `GitError` (`after` irraggiungibile, il caso di M-8) risale fino a `cli.main`. Il risultato è codice 1 senza stato `tollgate/base`, non `error`. Il job resta rosso e la sentinella copre il caso. Non contraddice il ruling, che chiede `error` solo per l'artefatto, ma la descrizione dello stato non c'è.

Nessun danno Critical o Important.

### Osservazioni fuori ambito

- Cache del predefinito scrivibile dal codice di `ids` (esisteva già prima della correzione, il diff non la cambia). Il job `ids` esegue codice del progetto e ha l'`ACTIONS_RUNTIME_TOKEN`, raggiungibile con `sudo` dalla memoria del runner. Con quel token può salvare voci `tollgate-ids-<albero>` con lo scope del predefinito per alberi diversi dal proprio, per esempio quelli di commit vecchi del predefinito la cui voce non esiste o è stata espulsa dopo 7 giorni. `tollgate-verdict` e il job `base` di `tollgate-run` le leggono come identificativi della base di altre PR. È appena oltre il limite dichiarato («il codice unito falsifica `ids.json`» del proprio albero). L'effetto resta confinato alla famiglia `base_ids` e non dà alcun token di scrittura. Prima del giro valeva lo stesso, perché il vecchio `tollgate-base` eseguiva la suite nel job che salvava la cache. Suggerisco di dichiararlo nella rev 25 insieme al limite.
- `actions/download-artifact@v4` nel job privilegiato estrae uno zip prodotto da un job non fidato. Il path traversal (CVE-2024-42471) è corretto dalla v4.1.3, e `@v4` punta all'ultima versione. Va bene finché non si fissa una versione più vecchia.
- In `protected`, con una suite rossa, `publish_from` restituisce 0, quindi il job `tollgate-base` è verde. Il docstring di `publish` dice «il segnale è il job». Il comportamento era lo stesso con `base-ids` prima del giro (Task 10).

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
