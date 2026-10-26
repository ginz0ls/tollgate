# Task 7 - Revisione (base fe5d070, testa 51886dd)

Sola lettura sul pacchetto `review-fe5d070..51886dd.diff` e sul commit. Nessun test rilanciato: l'evidenza del report (34 test del file, `tests/run` verde su 3.11 e 3.x, RED documentato) è coerente con il conteggio reale (34 `def test_` in `tests/test_eval_kit.py`).

### Aderenza (✅ / ❌ con riferimenti; ⚠️ non verificabile)

1. Review Focus 1 (stato senza `TOLLGATE_*`): ✅
   - `scaffold.py:168-176` (`_make_env`): toglie `TOLLGATE_*`, `GIT_*`, `CLAUDE*` dall'ambiente ereditato e imposta `TOLLGATE_STATE` solo nei sottoprocessi. `scaffold.py:157-158`: `state=None` vale `home/.local/state/tollgate`, la cartella predefinita; la sentinella si scrive a `:244`.
   - `tests/test_eval_kit.py:220-233` costruisce con `state=None`, lancia CLI (`:57`, `run_env` senza `TOLLGATE_*`) e `hooks/run SessionStart` senza variabili e vede il lavoro. Il test è reale: non c'è modo di leggere lo stato senza risolvere la cartella predefinita.
   - `test_eval_kit.py:243-267`: `scaffold.main` in-process con `TOLLGATE_STATE` altrove e `CLAUDE_CONFIG_DIR` impostata. Verifica `os.environ` identico dopo, la cartella "altrove" con la sola sentinella, e nessun file (fuori da `.git` e dalla cartella di stato) di workspace e home che contenga `TOLLGATE_` o il percorso altrove. Copre sia il padre sia i file letti dall'agente.
2. Review Focus 6 (shim `gh`): ✅
   - `tests/evalbin/gh:7-11`: senza `HOME` o senza dati, `exit 1` con «gh finto dell'eval: dati assenti», prima di qualunque ricerca. `exec` è sempre sul python dello shim e su `tests/fakegh.py`: nessun `gh` vero è raggiungibile.
   - `test_eval_kit.py:358-373`: trappola nel `PATH` dopo `EVALBIN`, non chiamata; la prova di controllo mostra che senza shim sarebbe stata chiamata. Il test è solido.
   - `tests/evalbin/python3:4-11`: `/usr/bin/python3`, altrimenti il primo `python3` del `PATH` fuori da `/home/*` e fuori da sé; errore 127 se non c'è. Coerente col modello `probe-bin`. `test_python3_shim_runs_a_system_python` lo prova.
3. Strati: ✅
   - `scaffold.py` importa solo stdlib e `evals._kit.recipes`. `bin/` e `hooks/run` sono processi (`:194-199`). Eventi nella forma minima: `session_id` e `cwd` per primi, poi `hook_event_name`, `tool_name`, `tool_input`, e `tool_response` in coda per i Post (`:203-210`, `:213`, `:346-348`, `:425`).
   - `test_scaffold_writes_no_db_directly` (`:335-349`) è un'analisi AST su `KIT/*.py` che rifiuta `tollgate*`, `sqlite3`, `tests` e gli import relativi. I fixture non sono `.py` del kit ma dati. Il kit non scrive mai nel DB.
4. Primitive: ✅ con un rilievo minore (M1)
   - Ogni primitiva termina con `_check_phase` (`scaffold.py:475-482`) che legge `status --json` dal programma vero, e ha il suo `test_build_<ricetta>`; `test_every_recipe_has_a_build_test` (`:206-210`) lo impone.
   - Stati dichiarati verificati: fase, livello e `tasks` via `status` (`:93`, `:134`, `:140`, `:151-152`, `:160`, `:175`, `:184`, `:201`), `level_cap` (`:125`), ricevuta `verify` sullo sha di HEAD e verdetto `approved`, `finish_sha`, commit registrati da `hooks/run`, ref sul nudo e PR nel gh finto, giri di audit e atti consumati.
   - La sequenza di `task_done` (`:361-391`) è quella degli hook: lancio Agent, SubagentStart, commit con `agent_id`, `verify`, report 18.5, `review-prepare`, verdetto con sha e code letti dal brief, `task done`.
5. `target.build`: ✅ per `__pycache__`, `dependencies`, `evals/`, `tests/evalbin/`, `tests/fakegh.py`, repo intatto. ⚠️/Minor sullo "nient'altro tolto" (M2).
   - `target.py:529-535`: una lista di esclusione (`.git`, `.github`, `.claude`, `.superpowers`, `docs`, `spikes`, `tests`, `node_modules`, `reports`) invece di "tutto tranne `__pycache__` e `dependencies`". Il codice di runtime non legge `docs/`, `spikes/` né `.github/` (grep su `bin`, `hooks`, `skills`, `agents`, `templates`, `gate`, `statusline`); `templates/` e `gate/` sono copiate. Funzionalmente corretto, ma è una scelta più larga del testo del carry.
   - Il repo non si tocca; la cartella di uscita si riscrive solo con il marcatore o se vuota; rifiuta uscite dentro o sopra la radice (`:543-553`, testato in `:431-444`).
6. Igiene: ✅ con ⚠️.
   - `.origin.git/` e i segnaposto in `.git/info/exclude` (`scaffold.py:130-132`, scritto prima del `git add -A` del commit base, `:283-291`). Per `.claude/` la scelta è `/.claude/*`, motivata nel codice e nel report, e in linea col brief. `test_sandbox_placeholders_and_origin_excluded` (`:283-288`) verifica che il workspace resti pulito.
   - `PYTHONDONTWRITEBYTECODE=1` (`:175`), CLI con `-B` (`:198`), `sys.dont_write_bytecode` (`:110`), script senza import relativi. `test_runs_as_script_from_a_copy_without_pycache` e `test_kit_has_no_case_files` lo provano.
   - File aggiunti espliciti (`git add -- <percorsi>`, `:322`). Unica eccezione, il commit `base` con `-A` (`:291`), su un albero appena copiato dai fixture con l'exclude già scritto: accettabile.
   - Rifiuto di una HOME vera: euristico, solo `.claude/settings.json` (`:234-236`). Vedi M3.
   - ⚠️ `_check_places` (`:239-240`) esige il workspace vuoto. I fatti della sandbox (I1) dicono che i segnaposto compaiono nella cartella di partenza, ma le fonti non dicono se prima o dopo lo scaffold. Se fossero presenti prima, ogni scaffold reale fallirebbe con «non è vuoto». Non verificabile dal diff; va confermato al primo giro del Task 14 (o con la prova a secco del Task 8).
7. `Recipe` con 4 campi in più (`change`, `audit_rounds`, `acts`, `finish`): ✅
   - Ammessi dal carry ("può ricevere i campi che servono"). Tutti usati dalle ricette e validati da `__post_init__` (`recipes.py:44-57`). `issue` e `issue_title` hanno default, e `issue_title` resta sul campo che fissa lo slug come da brief. Le firme del brief sono rispettate; nessun campo superfluo.
   - `CORRECT_PATHS` vuoto (`:80`): atteso, lo riempiono i Task 8-10.
8. Esito VE12/D1: ✅ riportato in modo coerente
   - Il report indica `adopt` e non `start`. Nel codice `adopt.py` riusa il worktree esistente (`_worktree`, `:266-278`) e `start.py` crea il worktree sempre sotto `.claude/worktrees/`. I limiti dichiarati (stato ricostruito dal ramo, task `pending`) sono onesti e coincidono con le ruling successive del controller (D1 definitivo: il legame con `adopt` non si usa nei casi). Non l'ho rieseguito: ⚠️ la prova è nello script della scratchpad, non nel repo.

Ruling del controller dopo il report: tutte e tre rispettate. Il dubbio 1 (`start` può scrivere `tollgate.defaultBranch`) non cambia il codice. Il dubbio 2 (`finish open-pr` in L1/L2, giri sul piano) è rimandato ai task dei casi, e il banco rifiuta con un errore chiaro `finish open-pr` fuori da L0 (`recipes.py:55-57`).

### Punti di forza

- Tutto lo stato nasce dal programma vero (CLI e `hooks/run` come processi) e ogni build si autoverifica con `status --json` sulla fase attesa (`scaffold.py:475`): una ricetta che non arriva dove dichiara fallisce subito, non al Task 14.
- La separazione ambiente-del-sottoprocesso / ambiente-del-padre è netta e provata con un confronto esatto di `os.environ` e una scansione dei file della corsa.
- Fail-closed dello shim provato con una trappola che si dimostra funzionante.
- Guardie utili: cartella di stato non vuota, workspace non vuoto, uscita di `target.build` col marcatore, `__post_init__` che rifiuta combinazioni incoerenti.
- Nome e posta di git nella configurazione locale del checkout (`:288-290`) perché la HOME della corsa non ha `.gitconfig`: caso reale visto e coperto da test.
- Output pulito, nessun `__pycache__` nel commit.

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**

- M1 `tests/test_eval_kit.py:68-73` e usi a `:94`, `:103`, `:126-129`, `:135`, `:141`, `:154`, `:163-169`, `:177`, `:179`, `:191-193`, `:257`: molti dettagli si asseriscono leggendo il DB in sola lettura (`plan_path`, `implementer`, `receipts`, `acts`, `spec_audit`, `events`). La lente chiede di leggere con `status --json` o equivalente. Per fase, livello e conteggio dei task `status` basta ed è usato; per il resto il test è accoppiato allo schema. Dove possibile prova lo stesso fatto con un comando del programma, come già fa `:195` con `audit prepare`. Altrimenti lascia la lettura, ma nel docstring di `:5` il motivo è già dichiarato. Non è un difetto del kit, che in sé non tocca il DB.
- M2 `evals/_kit/target.py:529-535`: l'esclusione di `.github`, `docs`, `spikes`, `reports`, `node_modules`, `.superpowers` va oltre "nient'altro tolto" e il test `:412-429` la fissa. Non rompe nulla (il runtime non legge quelle cartelle), ma il controller dovrebbe confermarla, perché una futura dipendenza del plugin da `docs/` si romperebbe in silenzio solo nella copia valutata. Un test che esegua `hooks/run` e `bin/tollgate --version` dalla copia la renderebbe sicura (oggi `test_runs_as_script_from_a_copy_without_pycache` lo fa per lo scaffold).
- M3 `evals/_kit/scaffold.py:234-236`: il rifiuto di una HOME vera guarda solo `.claude/settings.json`. Una HOME vera senza quel file (profilo nuovo, altro utente) riceverebbe in silenzio `installed_plugins.json`, `.tollgate-eval/` e lo stato. Più robusto: rifiutare se `home` coincide con la home dell'utente del sistema (`pwd.getpwuid(os.getuid()).pw_dir`) e se esiste già `.claude/plugins/installed_plugins.json`. Vale la cautela "mai toccare `~/.claude/plugins/`".
- M4 `scaffold.py:193-195`: `_hook` accetta solo l'uscita 0, ma ignora l'eventuale stdout JSON di un `deny` con uscita 0. Se un hook rifiutasse un evento dello scaffold, la build proseguirebbe e lo scoprirebbe solo `_check_phase`, con un messaggio meno chiaro. Registrare nell'errore l'ultimo output del hook basterebbe.
- M5 Nessun test dice "nessuna scrittura fuori da `workspace`, `home` e `state` ricevuti" (lente 6); è garantito solo per `.local` (`:241`). Un test che confronti l'elenco della cartella temporanea padre prima e dopo la build lo fisserebbe a basso costo.
- M6 `test_eval_kit.py:212-216` ripete il limite di tempo già asserito in `KitCase.build` (`:52`); innocuo.

### Valutazione

**Qualità del task:** Approvato

**Motivo:** I requisiti e le tre ruling successive sono rispettati e provati dal programma vero. Review Focus 1 e 6 sono coperti da test che asseriscono davvero, gli strati sono rispettati e la VE12/D1 è riportata fedelmente. Restano solo rifiniture (M1-M6), e un ⚠️ da chiudere al primo giro reale: il workspace vuoto richiesto da `_check_places` contro i segnaposto della sandbox.
