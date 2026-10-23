# Revisione Task 2 (commit 7102192, base bae003e)

## Aderenza
- ✅ `runner.py`: nomi della decisione 2, `run_one` con la firma di oggi annotata, `executed_ids`, `ids_commands` (ignora i percorsi, decisione 12). `verify.py` re-importa i nomi e conserva `_run_one`, `_report_path`, `_report_for` (scan).
- ✅ `ghcli.py`: `BOT_LOGINS` (V1), `ApiResult`, `api` (V2: codice dalla prima riga `HTTP/<v> <codice>`, corpo dopo `\r?\n\r?\n`, uscita non zero non è errore con riga di stato). D15: `paginate` senza `jq` → `ValueError`, `data` lista. `flow/gh.GhError is ghcli.GhError` (re-export, test in `test_ghcli.py`). Il fakegh riproduce la forma V2 (`tests/fakegh.py` `_api_status`).
- ✅ D1: `diff_violations(..., approved_spec=None)`, `finishcheck` calcola `(spec_path, sha)` e lo passa, `_own_document` sparita (grep: nessun residuo).
- ✅ D14: `diff_check -> DiffCheck`, `diff_findings = diff_check(...).violations`, `guard_config`/`is_docs_md` in `diffcheck` e importabili da `violations` (test `test_moved_names_importable_from_violations`); il controllo del collegamento simbolico resta in `violations` (`diff_violations` mette `registered=None` se il piano è un symlink).
- ✅ D17f: `FORBIDDEN` dell'analisi include `tollgate_gate` (`tests/test_analysis_isolation.py:8`).
- ✅ D21a: `test_gate_runtime_has_no_db` scopre i moduli con glob (`tests/test_layers.py` `gate_modules`) e importa in un processo pulito, asserendo l'assenza di `tollgate_core.db` e `sqlite3`.
- ✅ D2: `fetch_ref` passa il token solo in `GIT_CONFIG_COUNT/KEY_0/VALUE_0` del figlio (`git.py:423-437`); il test verifica argv senza token/`AUTHORIZATION`/`extraheader`, l'ambiente esatto e `.git/config` pulito.
- ✅ Strati: allowlist del gate (`GATE_CORE_ALLOWED` = `__init__`/VERSION, `clock`, `paths`, `git`, `config`, `runner`, `diffcheck`, `ghcli`), nucleo che non importa il gate (`UPPER` include `tollgate_gate`, eccezione `cli.py`), flusso può importare il gate. `imported_modules` risolve gli import relativi e `from pacchetto import x`; testato.
- ❌ D20 non completa: vedi Important 1.
- ⚠️ La suite verde (1788 test) e il RED non si verificano dal diff: affermazioni dell'implementatore, non rilanciate per regola.

## Rischi controllati
1. `resolve_ref`/`patch_id` ora sollevano `GitError` per un riferimento con `-`. Controllo: grep di tutti i chiamanti in `bin/`. Tutti passano riferimenti con prefisso fisso (`origin/{b}`, `refs/heads/{b}`, `refs/remotes/origin/{b}`, `f"{sha}^"`), l'uscita di `default_ref` (sempre `origin/...`) o SHA/base dal DB (`openpr.py:80`, `finalreview.py:98,119`). Nessuno può ricevere un nome che inizia per `-`, nessuno si affida a `None` per un riferimento di quel tipo: nessuna regressione. Il solo cambio osservabile è `range_base("-x")`, da `EMPTY_TREE` a `GitError`: irrilevante.
2. Import tolto da `tollgate_flow/gh.py` (`json`, `os`, `subprocess`, `Path`, `paths`). Controllo: grep nel resto di `gh.py` (nessun uso residuo), grep in `bin/` e `tests/` di `gh.json|gh.os|gh.subprocess|gh.paths|gh._run` patchato (nessuno; l'unico `mock.patch.object(..., "_run")` è su `gitw`, `tests/test_start.py:411`) e uno script AST degli import inutilizzati sui file toccati (solo i re-export marcati `noqa`). Sicuro. Resta il fatto che `gh.run_json` ora chiama `ghcli.run`, non `gh._run`: nessun test lo patcha.
3. Equivalenza di `diff_violations` prima/dopo. Controllo: lettura del vecchio e del nuovo corpo nel diff. Logica identica: stessi filtri su `output_excludes`, stessa condizione `level != "L0" and plan_sha`, `locked` calcolato solo quando c'è controllo di scope, piano registrato esente a parità di blob (ora via `git.blob_at`/`blob_sha` invece di `rev-parse`, equivalente per un blob), spec approvata confrontata con il blob a `head_ref` (prima a `HEAD`: in `finishcheck` `head_ref == sha == HEAD`, quindi uguale). Ma `test_same_result_as_diff_violations` (`tests/test_diffcheck.py:41`) NON confronta due cammini indipendenti: `diff_violations` chiama `diffcheck.diff_findings`, quindi il confronto copre solo la preparazione dei dati (scope, piano, `locked`, `waiver_file`), che il test ricostruisce a mano; la logica centrale è la stessa in entrambi i rami. Garanzia reale: la suite esistente di `test_violations`/`test_finishcheck`, rimasta invariata e verde secondo il report.

## Punti di forza
- Estrazione fedele, con re-export che lasciano invariati tutti i chiamanti; nessun file di flusso o hook toccato oltre a `finishcheck`.
- `_check_ref` unica; test che prova l'assenza di processi lanciati (`run.assert_not_called()`) su 15 chiamate, con sotto-test nominati.
- Test degli strati robusti (import relativi, import dentro le funzioni, `from pacchetto import modulo`), più verifica a runtime in un interprete pulito.
- Test dell'`api` con il finto fedele a V2, compreso il separatore solo `\n`, il corpo vuoto, l'assenza di riga di stato.

## Rilievi
### Critical
Nessuno.

### Important
1. `bin/tollgate_core/git.py:309` `blob_text(repo, sha)` riceve un riferimento (SHA) e lo passa a `git cat-file blob <sha>` senza `_check_ref`; D20 chiede `_check_ref` in OGNI funzione del modulo che riceve un riferimento e `test_refs_starting_with_dash_refused` dichiara di coprirle tutte (la lista dei 15 non include `blob_text`). Gli SHA arrivano da record scritti nel repo (`audit_round.py:30` `rnd["sha"]`, `taskcmd.py:34`), quindi non sono sicuri per costruzione. Correzione: `_check_ref(sha)` in `blob_text` e aggiungere `"blob_text"` alla tabella del test.

### Minor
1. `bin/tollgate_core/ghcli.py:96` (`decode_json_values`, usata da `api(paginate=True)`): rifiuta ogni valore che non sia un oggetto. D15 dice «lista dei valori decodificati»; un `--jq '.[].name'` darebbe `GhError`. Va bene per gli usi noti (oggetti), ma conviene documentarlo nel docstring di `api` o ammettere i valori scalari per `paginate`.
2. `bin/tollgate_flow/gh.py:25` `_run_checked` ripete il formato di `ghcli._failed` (`ghcli.py:58`): una riga duplicata, da far chiamare a `_failed` quando si tocca il file.
3. `bin/tollgate_core/diffcheck.py:68` `_blob_at_head` e `bin/tollgate_core/violations.py:85` `is_registered_plan` calcolano lo stesso blob con due percorsi diversi (ls-tree con guardia `is_file` contro `rev-parse`/`hash-object`). La differenza è dichiarata nel docstring di modulo e coperta dal controllo del symlink in `violations`, ma resta una duplicazione concettuale: tenerla presente quando il gate passerà `head_ref=None` senza worktree reale.
4. `bin/tollgate_core/git.py:423` `fetch_ref`: nessun `GIT_TERMINAL_PROMPT=0`; in locale senza credenziali git potrebbe attendere input fino ai 120 s di timeout. Nel gate non succede. Aggiungere la variabile in `extra_env` è a costo nullo.
5. `tests/test_diffcheck.py:41`: il nome `test_same_result_as_diff_violations` promette più di quanto verifichi (vedi rischio 3); rinominare in «diff_violations prepara i dati del lavoro» o aggiungere un confronto con valori attesi fissi per i casi spec approvata/piano cambiato passando per `finishcheck`.

## Valutazione
**Qualità del task:** Da correggere
**Motivo:** estrazione fedele e ben testata, tutti i rischi nominati risultano innocui; resta un solo buco rispetto alla D20 (`blob_text` senza `_check_ref` e fuori dal test che dichiara di coprire tutte le funzioni), correzione di due righe.
