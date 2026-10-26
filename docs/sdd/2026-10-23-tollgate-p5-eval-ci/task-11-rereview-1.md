# Ri-revisione Task 11, giro 1 (62ab387..7c5265d)

### Verdetti sui rilievi
- **I1 (spesa non registrata se run.sh muore)**: INDIRIZZATO. `cost.py reserve` scrive la riga `?` prima di claude (`run.sh` ~riga 150, `cost.py` reserve), `add --reserved` la sostituisce cercando ora+etichetta+`?` (mai un'altra invocazione, il flock ne ammette una sola); scrittura atomica `_write_atomic` (tmp nella stessa cartella + `os.replace`); senza result o senza costo la riga `?` resta. Nessuna via per cui claude parta senza riga: se `reserve` fallisce, `die 1`. Test `test_interrupt_leaves_reservation` e altri.
- **I2 (variabili di spostamento senza TEST_MODE)**: NON INDIRIZZATO nel suo effetto reale, vedi danno nuovo N1. Il rifiuto delle tre variabili in `run.sh:29-33` e il preambolo funzionano, ma `run.sh:37` esporta sempre `TOLLGATE_EVAL_BUDGET` (anche al valore predefinito) e `cost.py:budget_path` lo rifiuta senza TEST_MODE.
- Minor accolti: `timeout -k 30` e validazione di TOLLGATE_EVAL_TIMEOUT prima di prenotare: indirizzati. `flock -n` su fd 9 per tutta l'invocazione, fd chiuso per claude (`9>&-`), `add` incluso: indirizzato. Massimo tra costUsd e somma per corsa (`run_cost`): indirizzato. Collegamenti simbolici non seguiti (`real_dir`/`real_file`, `run_dir_ok`): indirizzato. Scansione token su stdout/stderr/result.json/report.html con costo già registrato e uscita 4: indirizzato. `plugin-check` senza trace controllata -> problema/uscita 4: indirizzato. `tabella.md` scritta anche a controllo fallito: indirizzato.

### Danni nuovi nel diff della correzione
- **N1 (Important, blocca l'uso reale)**: `evals/run.sh:37` fa `export TOLLGATE_EVAL_BUDGET="${...:-$root/.../budget.tsv}"` sempre; `evals/cost.py` `budget_path()` esce 64 se la variabile è impostata e `TOLLGATE_EVAL_TEST_MODE != 1`, senza confrontarla col predefinito. Verificato in sola lettura: `env -u TOLLGATE_EVAL_TEST_MODE TOLLGATE_EVAL_BUDGET=<percorso predefinito> python3 -B evals/cost.py remaining` -> messaggio di rifiuto, rc=64. Quindi in una corsa vera il primo `cost remaining` (`run.sh` ~riga 90) fallisce e lo script esce 1 con «budget.tsv illeggibile»: fail-closed, nessuna spesa, ma lo strumento non parte mai fuori dai test. Nessun test lo copre (tutti usano TEST_MODE=1; il test del rifiuto esce prima di cost.py). Correzione: in `cost.py` accettare la variabile se uguale a DEFAULT_BUDGET (o esportarla solo in TEST_MODE), più un test di `cost.py remaining`/di un giro con `claude` finto senza TEST_MODE (es. scambiando i percorsi con un repo di prova non è possibile: basta verificare che `cost remaining` con il valore predefinito esportato non esca 64).
- Minor: il file di lock `budget.tsv.lock` nasce accanto al registro in `docs/verifiche/evidenze/eval-p5/`; va ignorato in git o non committato.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti: I2 (per N1, l'esportazione del registro predefinito fa rifiutare `cost.py` fuori da TEST_MODE, quindi nessuna corsa vera parte). I1 e i minor accolti indirizzati.
