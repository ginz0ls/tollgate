# Revisione Task 11 (62ab387): evals/run.sh, evals/cost.py, tests/test_eval_run.py

Letti: regole, cautele, vincoli, review-focus, brief, carry, report, diff. Controllati a mano contro i JSON/trace reali di `docs/verifiche/evidenze/eval-p5/20261023T201225Z-sonda-nl-bash/` (forma di `result.json`, `tracePath`, messaggio `init`, ultimo `result` con `usage`, riga «kept …» in `stderr.txt`) e contro `.claude-plugin/plugin.json` (nome `tollgate`). Nessun `claude`, nessuna esecuzione di `run.sh`.

## Aderenza

- ✅ Tetto: `cost remaining` prima di tutto (`run.sh:380-383`), `--max-cost-usd "$cap"` (`:419`), residuo < 0.01 o registro illeggibile -> claude non parte. `remaining()` tratta `?`, NaN, negativi, righe corte, intestazione sbagliata come residuo 0 (`cost.py:69-99`). Arrotondamento per difetto ai centesimi.
- ✅ Costo registrato con uscite 1/2/124 se c'è `result.json` (`run.sh:440`), e con `?` se manca, è vuoto o malformato (`cost.py:122-126`, `run.sh:435-439`); `cost add` non ha altre vie d'uscita silenziose (intestazione diversa: eccezione -> uscita 3, ma il registro resta con intestazione sbagliata e quindi residuo 0 al giro dopo).
- ✅ Plugin non caricato: riga di costo scritta prima, poi uscita 4 con il messaggio richiesto (`run.sh:519-522`).
- ✅ `--no-publish`, `--allow-tools Bash Write Edit`, `--output-dir/--json/--report` fissi, rifiuto di `--output-dir`, `--json`, `--report`, `--publish`, `--publish-report` (anche forma `=`) e di ogni opzione sconosciuta prima di qualunque azione (`run.sh:341-354`). Caso inesistente, `/`, `..`, caso senza tag spec/extra: rifiuto. Ablazione dal tag corretta.
- ✅ `timeout`, stdin da `/dev/null`, stdout/stderr su file, bersaglio via `target.py`, shim in testa al PATH, `TMPDIR` fuori da /tmp con `realpath` prima e dopo, stampa di comando/residuo/costo/nuovo residuo.
- ✅ Copia delle corse tenute: `run_dir_ok` accetta solo `claude-eval-?*` figlie dirette di `$evtmp` (più stretto dell'originale), chmod solo su quella cartella e su `sealed`; `cp_checked` con lo stesso `TOKEN_PATTERN` dello script del Task 1 (`spikes/p5/run-p5-checks.sh:121`); regex «kept» coerente con la riga reale (`⚠ kept /home/…/claude-eval-JGdbCR: home/ …`).
- ✅ Controllo plugin: la forma reale di `init.plugins` è `[{name, path, source}]`; il braccio con plugin ha `sonda`/`tollgate` per nome, il braccio senza ha solo i `cc-plugin-*` builtin: il controllo aggiunto sul braccio senza plugin non dà falsi positivi sui dati reali.
- ✅ VE8: `costUsd`/`durationSeconds` al livello alto; `tracePath = …/claude-eval-X/out/trace.jsonl` quindi `parts[-3]` è giusto; token dall'ultimo `result` (`usage.input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`) combaciano con la trace reale; il test su `result.json` reale della sonda esiste.
- ✅ Niente `local.py` (decisione 9 (b) non scattata).
- ⚠️ Non verificabile senza claude vero: se `costUsd` di alto livello includa `judgeCostUsd` (nelle 12 corse delle sonde vale sempre 0; i casi di `evals/` non usano giudici LLM, quindi oggi non incide). `cost table` somma `costUsd + judgeCostUsd` per run, `budget.tsv` usa il totale: possibile scarto futuro, vedi Minor 4.
- ⚠️ Il nome «plugin» nel braccio con plugin per la corsa vera (`tollgate`) coincide col manifest; non provato dal vivo.

## Punti di forza

- Fail-closed ben pensato: `?` = residuo 0, e il test `test_missing_result_stops_and_asks` prova anche che il giro dopo è rifiutato.
- Il controllo di `run_dir_ok` è più stretto del modello; ignora cartelle tenute estranee (test dedicato).
- Il `claude` finto replica la forma reale dei JSON/trace e le cartelle sigillate (modo 000), quindi chmod e copia sono esercitati davvero; `test_tmpdir_refused_under_tmp` prova il rifiuto senza bypass, con `..` e collegamento simbolico.
- Decisione sulla copia in bash coerente col modello congelato.

## Rilievi

### Critical
Nessuno.

### Important

1. **Nessuna registrazione del costo se `run.sh` viene interrotto mentre `claude` gira** (`run.sh:428-431`; manca ogni `trap`). Ctrl-C (SIGINT al gruppo in primo piano: claude muore, poi muore anche la shell dello script che ha visto il figlio terminare per SIGINT), chiusura del terminale (SIGHUP), `kill <pid>` dello script, sessione del controller che scade: lo script esce prima di `cost add`, quindi i dollari già spesi (e le corse tenute) non entrano in `budget.tsv` e il residuo del giro dopo è sovrastimato. È proprio la via «claude parte e il costo non entra nel registro» che il tetto deve chiudere (carry: «qualunque sia l'uscita»). Correzione: o scrivere prima del lancio una riga di prenotazione con `?` e sostituirla con `add` a fine corsa, o installare `trap … INT TERM HUP` (e `EXIT` con flag «registrato») che chiama `cost add … ` (con `?` se manca il JSON) prima di uscire; aggiungere un test (claude finto che dorme, `SIGTERM` allo script per PID, riga `?` presente).
2. **Le variabili che spostano registro, evidenze e bersaglio valgono anche nelle corse vere, senza avviso** (`run.sh:327-329`, `cost.py:51-52`). Un `TOLLGATE_EVAL_BUDGET` rimasto esportato da una sessione di test (o un refuso) punta a un registro vuoto: residuo 80 pieno, la spesa va in un altro file e il tetto complessivo salta, senza che l'output dica quale registro è in uso (il preambolo stampa solo il residuo e la cartella d'uscita). Lo stesso per `TOLLGATE_EVAL_EVIDENCE` (cartella d'uscita non più quella della decisione 23). Correzione: stampare nel preambolo il percorso del registro usato, e onorare `TOLLGATE_EVAL_BUDGET`/`_EVIDENCE`/`_TARGET` solo con `TOLLGATE_EVAL_TEST_MODE=1`, altrimenti rifiutare (uscita 64) se sono impostate e diverse dai predefiniti; un test che prova il rifiuto senza TEST_MODE.

   Sul quesito `TOLLGATE_EVAL_TEST_MODE`: da solo il flag (salta il rifiuto di /tmp, `run.sh:393,398`) non fa uscire denaro dal tetto, al peggio la corsa fallisce nella sandbox; è accettabile **purché** sia l'unico interruttore e gate anche le tre variabili sopra (così diventa il solo punto da sorvegliare, e lo si può stampare in rosso nel preambolo quando è attivo). L'alternativa più pulita è togliere il bypass: i test mettono `TOLLGATE_EVAL_TMPDIR` in una cartella non sotto /tmp (es. dentro `ROOT` ignorata da git o in `$XDG_CACHE_HOME` temporaneo), ma richiede di creare cartelle fuori da `tempfile`; non lo ritengo obbligatorio.

### Minor

1. `run.sh:428`: `timeout` senza `-k`: se claude ignora SIGTERM, l'invocazione non finisce mai e il costo non si registra (stesso effetto di Important 1). Usare `timeout -k 30`.
2. Due `run.sh` in parallelo leggono lo stesso residuo e possono sommare oltre il tetto; basta un `flock` su `budget.tsv.lock` per tutta l'invocazione o un avviso in cima. Se sono sempre sequenziali dal controller, documentarlo.
3. `run.sh:435-439` e `cost.py:122`: una qualunque uscita di claude senza `result.json` (anche un banale errore di opzione, nessuna spesa) azzera il tetto fino a correzione a mano. È fail-closed voluto dal brief; solo da dire al controller nel report/uso (il messaggio lo dice già).
4. `cost.py:122`: usare come costo `max(costUsd, somma di costUsd+judgeCostUsd dei run)` renderebbe il registro robusto se `costUsd` di alto livello non includesse il giudice (⚠ sopra).
5. `run.sh:479`: `chmod 700 "$run/sealed"` e `cp` di `out/trace.jsonl`/`config/settings.json` seguono collegamenti simbolici; i file del workspace invece sono presi con `find -type f` (corretto). Aggiungere `[ -L … ]` o `chmod -h`/test `! -L` su `sealed`, `trace.jsonl`, `settings.json`.
6. `cp_checked` e la scansione dei token coprono solo la forma delle 4 regex del Task 1; `stdout.txt`, `stderr.txt`, `report.html`, `result.json` finiscono nella cartella delle evidenze senza scansione (nelle evidenze reali del Task 1 c'è lo stesso comportamento). Valutare di far girare `TOKEN_PATTERN` anche su questi prima del commit delle evidenze.
7. `cost.py:245-246`: una corsa senza `tracePath` (errore/timeout) è saltata senza segnalazione; se tutte lo sono, `plugin-check` esce 0 senza aver controllato nulla. Stampare «n corse verificate» o segnalare quando il numero è 0.
8. Con `plugin-check` fallito (uscita 4) `tabella.md` non viene scritta; scriverla comunque aiuta a leggere cosa è successo.
9. La riga «kept» con percorsi con spazi o `:` non è gestita (nota già nel report): l'effetto è un falso «trace assente» e uscita 4, quindi fail-loud, non denaro. Con `$HOME` senza spazi non scatta.
10. Tempo/robustezza: `TOLLGATE_EVAL_TIMEOUT` non è validato (valore non numerico: `timeout` esce 125, nessun result, riga `?`, tetto azzerato per un refuso). Validare come `--runs`.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** impianto del tetto solido sulle uscite 1/2/timeout/result mancante o malformato/plugin non caricato, e coerente con la forma reale dei JSON; ma manca ogni trap per le interruzioni (spesa non registrata) e le variabili di spostamento del registro/evidenze sono attive e silenziose nelle corse vere. Due correzioni piccole e testabili.
