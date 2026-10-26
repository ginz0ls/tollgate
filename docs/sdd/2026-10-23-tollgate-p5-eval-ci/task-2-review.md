# Revisione Task 2 (6cb106d)

### Aderenza
- ✅ Decisione 11: i tre test costruiscono il percorso in `mkdtemp(prefix="tollgate sp ")` con `addCleanup` (`tests/test_check_cli_calls.py` ~42-45) o confrontano con `program_command(...)` (`tests/test_prstate.py:73`, `tests/test_taskcmd.py:~80`). Controprova senza spazi dichiarata nel report (copia rsync, non `git clone`: scostamento minore, giustificato).
- ✅ `ci.yml`: `push`/`pull_request`, `permissions: contents: read` unico, concurrency con `cancel-in-progress: true`, matrice 3.11/3.13, `timeout-minutes: 60`, `ubuntu-latest`, checkout `path: "tollgate src"` + `working-directory`, passo suite identico alla forma di D10 con `shell: bash` (D5), passo «unclosed database», nessuna `${{ }}` nei `run:`. I test lo asseriscono (`tests/test_ci_workflow.py`), incluso `workflows.problems(text) == []`.
- ✅ Carry: D5 (`test_suite_step_fails_when_tests_fail`), `test_p4_scripts` coperto, ruling di Node 24 (v7).
- ❌/⚠️ Decisione 12: la causa è trovata ma la correzione indebolisce il test e codifica come accettabile un difetto del prodotto (rilievo I-1).
- ⚠️ `test_task1_script_still_passes_after_the_common_library` rosso su tutti e 4 i job del runner (report, nota): spiegato con il ramo di prova clonato da `main` senza la riscrittura di `ghguard`. Non verificabile dal diff; se il Task 2 gira in CI su un ramo il cui `main` remoto è vecchio, la CI del ramo resta rossa. Il controller deve verificare che la CI su `p5-eval-ci` lo passi.

### Punti di forza
- Indagine seria: carico, 100 corse strumentate, distribuzione delle copie, prova deterministica con lo stesso errore dei runner; nessun ritentativo.
- Causa del terzo instabile (`detect-merge-rosso`) corretta alla radice (nome file unico per caso), con test RED/GREEN che riproduce lo stesso `ts` (`tests/test_p4_make_case.py` aggiunto).
- Mutazione provata sul `shell: bash`; test del workflow letti con le stesse funzioni di `test_gate_workflows`.

### Rilievi

**Important I-1 — `tests/test_db.py:380-398` (e `bin/tollgate_core/db.py:208-212,290`): il test è stato indebolito e il difetto del prodotto è diventato «comportamento documentato».**
- Storia: il test nasce in 8125473 (C1 della revisione finale di P2) e asseriva `glob("tollgate-*-migrazione-2.db")` non vuoto e tutte integre: cioè «una migrazione concorrente di un DB v1 con righe lascia una copia di backup pre-migrazione valida». Ora asserisce solo «esiste una qualunque copia, ≤ KEEP_BACKUPS, integra». Una copia di un DB già migrato, o una copia più recente qualsiasi, soddisfa il nuovo test: non garantisce più la copia pre-migrazione, che è lo scopo del backup in `_migrate`. Il nuovo `test_migration_copies_older_than_the_retention_window_are_pruned` (396-402) poi asserisce come atteso l'esito peggiore (`[]` copie `migrazione-2`).
- Difetto del prodotto, verificato sul codice: `_migrate` fa `backup(...)` prima di prendere il lucchetto e prima del ricontrollo della versione (`db.py:211-214`), quindi ogni processo concorrente copia a ogni passo (MIGRATIONS arriva a 5: fino a 4 copie per processo, 16 con 4 processi). `backup` pota per nome le più vecchie oltre 10 (`db.py:290`); l'unica copia davvero pre-migrazione è la prima in ordine di nome, cioè la prima a essere cancellata dalle copie ridondanti dei processi successivi (che copiano un DB già migrato). Risultato: una migrazione di un DB con dati può lasciare solo copie post-migrazione, nessun punto di ritorno. Con più hook concorrenti al primo avvio dopo un aggiornamento è un caso reale, non teorico. La potatura per ritenzione è voluta in generale, ma non quando le copie che si potano sono quelle della stessa migrazione.
- Correzione: nel codice, non nel test. Ad esempio rileggere la versione sotto il lucchetto prima di copiare (copiare solo se il passo è ancora da fare, spostando `backup` dentro `tx` o ricontrollando `_version` subito prima), e/o non potare le copie `migrazione-*` più recenti dell'ultimo avvio. Poi il test originale (copia `migrazione-2` non vuota, integra, con la riga) torna valido e può diventare più forte: la copia pre-migrazione contiene la riga e ha `schema_version` 1. Se il controller sceglie di non toccare il prodotto in P5, il rinvio va esplicitato (voce in «Dopo la v1») e il test non deve dichiarare la potatura come garanzia.
- Nota: `assertLessEqual(len(copies), KEEP_BACKUPS)` (386) è tautologico (la potatura lo garantisce).

**Minor M-1 — `.github/workflows/ci.yml:11-13` / `tests/test_ci_workflow.py:~33`:** il gruppo `ci-${{ github.ref }}` separa `refs/heads/x` (push) da `refs/pull/N/merge` (PR): push e PR dello stesso ramo non si annullano. Accettabile, ma il test asserisce solo `cancel-in-progress` e non il gruppo.

**Minor M-2 — `ci.yml:17` `fail-fast: false`, non richiesto.** Ragionevole (le due versioni vanno viste entrambe, in linea con il carry sui due fallimenti per versione) e innocuo; non lo asserisce nessun test. Lo accetto, va solo citato in 1.2/10 se si descrive la CI.

**Minor M-3 — `tests/test_ci_workflow.py` (`test_actions_use_current_major_versions`):** uguaglianza esatta su `["actions/checkout@v7","actions/setup-python@v7"]`: si rompe volutamente al Task 3 (SHA). È dichiarato nel report; il Task 3 deve sostituirlo con `PinTest` su `PINS`, non lasciarlo. Il nome promette «versioni correnti» ma verifica stringhe fisse.

**Minor M-4 — `suite.log` scritto in `tollgate src/`:** innocuo sul runner; già annotato dal report.

**Minor M-5 — controprova senza spazi** su copia rsync e non su `git clone .` come da brief: un file non tracciato ma necessario potrebbe passare inosservato. Minore, il commit è pulito.

### Altre verifiche richieste
- `spikes/p4/make_case.py:789,803` e `tests/test_p4_make_case.py` (~91-105): correzione giusta e minima; il nome file non è letto altrove (grep: solo `spikes/gh-p4/run-p4-checks.sh` ha un file diverso). Il test usa lo stesso `ts` per due casi: riproduce la causa. ✅
- Spazio in `fail-fast`: vedi M-2. `test_actions_use_current_major_versions`: vedi M-3.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** CI, tre test di D11 e fix di `make_case` sono corretti e ben provati, ma la correzione di `BackupRaceTest` toglie al test la garanzia di una copia pre-migrazione e ratifica come accettabile una potatura che, per la ridondanza dei backup di `_migrate`, può cancellare l'unica copia pre-migrazione: il difetto va corretto nel codice (D12 ammette «nel test o nel codice») e il test originale ripristinato.
