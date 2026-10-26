# Revisione Task 12 (bb519ec..4625ac3)

### Aderenza
- ✅ Sei file di `docs/uso/` + `README.md`, contenuti come da decisione 19. Nessuna em dash, nessun `/home/` o `MEGA`.
- ✅ Documentazione contro codice (controlli mirati): argument-hint di tutte le 16 skill (test); `run.sh` (selettori, `--runs`, `--a-secco`, rifiuto di `--output-dir/--json/--report/--publish*`, tetto 80 USD, prenotazione `?`, uscite 0/1/2/3/4/64, TMPDIR fuori da /tmp, bersaglio `/tmp/tollgate-eval-target`, soglia 0.66, modello, flock); `ci.yml` (matrice 3.11/3.13, `tollgate src`, `ResourceWarning`, "unclosed database", SHA da PINS controllati da `tests/test_ci_workflow.py:81`); casi eval (9 spec + e1,e3,e4,e5, `runs: 3`); `experimental.evals` in plugin.json; messaggi citati (`GitHub Actions spente`, `modalità rilevazione`, `nulla da aggiornare`, `configurazione del gate cambiata dopo il run`, 403 "Upgrade to GitHub Pro", 404 "Branch not protected", "non determinata"); chiavi `base_ids_from_run`, `base_ids_missing_command`, `existing_workflow_rules`; `statusline/ctx` e `statusline.sh` esistono; default 20 merge/mese; cleanup 10 minuti; intervallo Superpowers 6.4.1..<8 (`prereq.py:12`); `marketplace.json`.
- ✅ `limiti.md`: il corpo delle cinque voci chiuse da P5 combina con le decisioni 14 (M-1), 15 (M-3), 16 (M-4) e col codice (`guard.py:22-23` pending su opened/edited/reopened, `sentinel.py` risalita dall'ultimo stato del bot, pin per SHA, `PINS`). Nessuna promessa non mantenuta trovata.
- ✅ `status` (`cli.py:195-232`, `:435-460`): riga dei limiti con percorso assoluto da `Path(__file__)`, stampata anche senza DB e con lista vuota, mai in `--json` (ramo `[]` e ramo con DB), frase detect solo se `_detect_active` (stessa query di `_status`: stessi filtri `closed` e `repo_key`). Test eseguiti: `tests.test_docs` (6 OK), `tests.test_cli -k status` (8 OK).
- ✅ `re.M` in `tests/test_eval_cases.py:1098`: serve perché la riga dei limiti è ora l'ultima; `$` con `re.M` trova ancora la riga "task: 2 done" e non maschera il caso (la stringa resta ancorata a fine riga). I grader di `evals/*/case.yaml` non leggono l'uscita di `status` in testo (lo scaffold usa `status --json`, `scaffold.py:500`; s2 chiede solo di riferire lo stato).
- ✅ `test_limits_match_spec_1_2` usa `assertEqual` su due differenze di insieme (uguaglianza vera, con guardia `> 20` contro letture vuote).
- ⚠️ `sha_pinning_required` (emergenze) e il fatto che `claude plugin` ammetta quei comandi `/plugin` non si verificano dal repo.

### Punti di forza
Testi scritti dal codice, con numeri e messaggi esatti; il test delle skill controlla anche la coerenza "solo l'utente" col frontmatter; il test di `status` copre fuori repo, senza DB e `--json`.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `docs/uso/limiti.md` (titoli delle voci "Le azioni dei workflow sono fissate alla versione maggiore", "Il verdetto precedente ... resta valido durante la rivalutazione", "Identificativi della base senza voce per un comando"): letti da soli dicono il contrario di quanto vale dalla 0.2.0 (il corpo li corregge). È voluto dal ruling del controller (titoli rev 25 fino al Task 15): il Task 15 deve riscriverli insieme alla spec.
2. `limiti.md`: i titoli hanno punteggiatura incoerente (alcuni con punto finale, alcuni minuscoli, alcuni con backtick) e la sezione "## Gli eval e i guardrail locali" raggruppa due limiti dei guardrail che con gli eval non c'entrano; meglio "I guardrail locali" nel Task 15. Il test normalizza, quindi non lo vede.
3. `tests/test_docs.py` (`test_no_local_paths`, `test_relative_links_exist`): ignorano `/Users/`, `~/`, `C:\` e non verificano le ancore (`#la-cli` in `comandi.md`); i link a file nel testo senza sintassi markdown non sono controllati. Nessun buco oggi, solo difesa più stretta.
4. `eval-e-ci.md`: "almeno due grader su tre valgono in media" è una resa della soglia 0.66 che dipende dal numero di grader per caso; non verificata per ogni caso.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** documentazione esatta rispetto a codice e decisioni controllate; riga di `status` e frase detect corrette e testate; `re.M` non maschera niente e nessun grader dipende dalla coda di `status`. Restano solo rifiniture, due delle quali per il Task 15.
