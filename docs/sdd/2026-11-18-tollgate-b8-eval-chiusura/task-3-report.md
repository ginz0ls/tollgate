# Task 3 — report dell'implementatore

Commit: `7618110` «tollgate B8: campagne degli eval, WebFetch per dominio, trace ripulite e conteggi della nota».
Status: DONE_WITH_CONCERNS (vedi dubbi).

## Cosa è stato fatto
- `evals/cost.py`: `Campaign`, `CAMPAIGNS` (`p5` 80, `b8` 20), `campaign_of`, `budget_path(campaign="b8")`; `campaign` in coda a `spent`, `remaining`, `reserve`, `add` (con `path` il tetto è quello della campagna); `--campagna` per ogni sottocomando (nome sconosciuto: 64); nuovo `info` (cartella e tetto su due righe, D7). `TOTAL_USD` e `DEFAULT_BUDGET` rimossi.
- `evals/run.sh`: `--campagna` (anche `=`); cartella e tetto da `cost.py info`, domini da `scrub.py domains`; messaggio «tetto di N USD della campagna X esaurito»; `--allow-tools Bash Write Edit "WebFetch(domain:…)"… WebSearch` per ogni campagna diversa da `p5`; uscita 5; `scrub_evidence` (flowreg `togli-pagine`, `strip-web`, `strip-bash`, `anonymize`) dopo la copia e anche sui due rami dell'uscita 3; `nota.md` da `research_counts.py` dopo `cost table`; in TEST_MODE valori finti `TOLLGATE_EVAL_FAKE_USER/HOST` (D6), fuori da TEST_MODE `id -un` e `hostname` e le due variabili sono rifiutate.
- `evals/scrub.py` (nuovo): `WEB_DOMAINS = ("ai.google.dev", "vercel.com")`, `strip_web_results` (D4), `strip_bash_web`, `anonymize`, `main` con `domains`, `strip-web`, `strip-bash`, `anonymize` (uscita 2 per valori corti o riservati, senza toccare niente e senza stampare i valori). Riusa `flowreg._placeholder`, `_content_text`, `_swap_saved`, `PAGE_PLACEHOLDER` e `bash.parse`.
- `evals/research_counts.py` (nuovo): `count(run_dir)` (chiavi `note_ok`, `note_ko`, `reminders`, `switch_unreadable`, `research_vetoes`, `lookups_<kind>` per i sei tipi), `immutable=1`, rifiuto con `-wal` (`WalError`), zero senza tabelle (D16), `table`/`main` (le corse senza stato sono elencate sotto la tabella).
- `tests/test_eval_cases.py`: `_Session._do_fetch` (D9: `_use("WebFetch", {"url"})`, `PostToolUse` con `{"code": 200, "result": …}`, poi `_result`) e `FetchStepTest`.
- `docs/uso/eval-e-ci.md`: campagne, tetto di B8, permessi web, pulizia delle trace, uscita 5; nessun link al rapporto di B8 (D12); conto dei casi aggiornato a oggi (tredici con corsa vera; i tre nuovi li conterà il Task 4 / 8).
- `.gitignore` (lock di `eval-b8`), `docs/verifiche/evidenze/eval-b8/budget.tsv` (sola intestazione).
- `eval-p5/budget.tsv` invariato: `git hash-object` 3749b1e70b8c… prima e dopo; nessun file sotto `eval-p5/` toccato.

## Test
RED: i test nuovi su un `git archive` di HEAD con i file di test copiati sopra (cartella temporanea poi cancellata):
`python3 -B -m unittest tests.test_eval_run.CostTest tests.test_eval_cases.FetchStepTest tests.test_eval_run.GitignoreTest` →
`ImportError: cannot import name 'research_counts' from 'evals'` (modulo assente) e `FetchStepTest` rosso senza `_do_fetch`; `FAILED (errors=2)`.
GREEN: `python3 -B -m unittest tests.test_eval_run tests.test_eval_kit tests.test_b1_scripts tests.test_p5_scripts` → 341 test OK.
Suite intera: `PYTHONWARNINGS=error::ResourceWarning tests/run` → `Ran 4126 tests … OK (skipped=13)` (python3.11) e `OK (skipped=11)` (python3), `exit 0` (`suite-task-3.log`).

Test nuovi in `tests/test_eval_run.py`: `test_default_campaign_is_b8`, `test_p5_campaign_keeps_80_and_its_registry`, `test_cap_message_names_campaign`, `test_b8_grants_web_tools`, `test_grants_follow_web_domains`, `test_campaign_folder_follows_cost_info`, `test_unknown_campaign_rejected`, `test_run_strips_web_results_from_traces`, `test_strip_failure_exits_5`, `test_anonymizer_failure_exits_5`, `test_run_anonymizes_copied_runs`, `test_run_anonymizes_on_unknown_cost`, `test_run_writes_research_counts`, `StripWebResultsTest` (D4, incluse 8 trace di P5 committate: invariate), `StripBashWebTest`, `AnonymizeTest` (testo e `.db` in WAL, CLI senza valori in uscita, rifiuto di valori corti/riservati), `ResearchCountsTest` (stato vero costruito con `db.open_db`; nessun file creato; `-wal` rifiutato; senza tabelle zero), `GitignoreTest`, `CostTest.test_campaigns_and_default` e `test_cli_campaign_option`, `DryRunRealRegistryTest.test_p5_registry_untouched_by_b8` (e la classe punta al registro vero di `b8`). Gli otto test di D5 passano a `p5` con gli stessi numeri; `test_env_paths_need_test_mode` copre anche `TOLLGATE_EVAL_FAKE_USER/HOST`. Nome utente e host nei test sono solo `utente-prova` e `macchina-prova`: mai quelli veri.

## Step 4: prove a secco (`task-3-asecco.txt`)
- `evals/run.sh --a-secco s1-done-senza-ricevuta`: registro e evidenze in `…/evidenze/eval-b8`, `campagna: b8 (tetto 20 USD)`, `residuo del tetto: 20.00 USD`, `--allow-tools Bash Write Edit WebFetch(domain:ai.google.dev) WebFetch(domain:vercel.com) WebSearch`, `--max-cost-usd 20.00`.
- `evals/run.sh --a-secco --campagna p5 s1-done-senza-ricevuta`: registro e evidenze in `…/eval-p5`, `campagna: p5 (tetto 80 USD)`, `residuo del tetto: 70.93 USD`, `--allow-tools Bash Write Edit`, `--max-cost-usd 70.93`.

## Scostamenti dal piano e scelte
- **TDD**: ho scritto il codice prima dei test (ordine sbagliato); il RED sopra è stato ricostruito dopo, su un'esportazione di HEAD. Il rosso è reale ma non è quello «vissuto» passo per passo.
- `cost.py info` stampa due righe (cartella, tetto con `%g`: `20`, `80`); la forma non era fissata dal brief.
- `research_counts.count` prende la cartella della corsa (`runs/<corsa>`), `main` la cartella d'uscita; le corse senza `tollgate.db` sono elencate sotto la tabella.
- Uscita 5 anche sul ramo del costo ignoto se l'anonimizzazione fallisce (il messaggio ricorda che la riga «?» resta).
- `anonymize`: la parola intera è `\b` (host senza distinzione tra maiuscole e minuscole), quindi `macchina-prova-2` diventa `HOST-2`: nessun residuo del valore. I BLOB non si toccano (il brief dice colonne di testo). `strip_bash_web` giudica gli argomenti dopo `bash.parse` (il corpo di un heredoc non conta) ed esclude `research submit`.
- `strip_web_results` sostituisce anche la chiave `url` di `tool_use_result` (D4 dice «ogni stringa»): l'indirizzo resta nel segnaposto del blocco.

## Dubbi
- `bin/tollgate_analysis/__pycache__/` compare come non tracciato: non è mio (`scrub.py` imposta `dont_write_bytecode` prima dell'import), probabilmente dei revisori. Non è nel commit.
- Il conto dei casi in `eval-e-ci.md` (tredici) dovrà essere riallineato dopo il Task 4.
- Lo stato dei veti conta solo `veto` con `data.rule == "research_gate"`; verificato sul codice di `runner.py:330`, non su una corsa vera.

## Fix round 1
- I1: `evals/scrub.py` `strip_bash_web` giudica il testo grezzo del comando (heredoc e here-string compresi): il risultato di ogni `Bash` che nomina un dominio di `WEB_DOMAINS` (parola intera: `notvercel.com` no) è sostituito, salvo la consegna della nota (`research submit`, anche con heredoc che nomina il dominio) e un `sed`, riconosciuti dopo `bash.parse` (ogni comando letto è l'uno o l'altro; un comando illeggibile non è esente). Tolti `FETCH_PROGRAMS` e `_FETCH_RAW`.
- Test: `StripBashWebTest.test_strip_bash_web` ora copre `python3 - <<EOF`, `python3 <<<`, `xargs curl`, `perl -e` (sostituiti: 7 in tutto) e un dominio simile (invariato), più i casi di prima. Nuovo `AnonymizeTest.test_anonymize_real_tollgate_schema` (stato creato con `db.open_db`, host in `events.host`, casa in `data`, `integrity_check` ok, niente `-wal`/`-shm`, valori finti spariti; il `migrate.lock` di `open_db` è ignorato).
- Comandi: `python3 -B -m unittest tests.test_eval_run tests.test_eval_cases` → 179 test OK (`task-3-fix1-mirati.log`); `PYTHONWARNINGS=error::ResourceWarning tests/run` → `OK (skipped=11)`, `exit 0` (`suite-task-3-fix1.log`).
