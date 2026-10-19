# Revisione Task 2 (c301c86..511a449)

### Aderenza
- ✅ `sessions.py`: CLI_DIR, CLI_WINDOW_S, CliSessionError, note_cli_call (dizionario per sottocomando, tmp + os.replace, OSError inghiottito, sessioni non _SAFE ignorate), cli_session (resolve, finestra stretta, due messaggi) come decisione 2 e C8b/C8d.
- ✅ `cli_calls.py` (pre_bash, ordine 5): indice del programma (0 o 1 con python, C8c), argv registrato dopo il programma, segnale solo per start/act (C8a), diniego `coordinator_only` per start/task/act/status --checkpoint con agent_id (decisione 22), cwd = effective_dir.
- ✅ `apply.py` cli_call; OPS = 23 (verificato dal report con la suite).
- ✅ `acts.py`: riga programma per ogni tollgate:* non off/on, anche per atti rifiutati (C16); `out[-1]` è sempre un inject (tutti i rami di `_act` terminano con inject/_refuse).
- ✅ fakegh, FlowLab (composizione di Lab, set_gh, gh_calls, env con HOME temporanea), test_layers con ast anche nelle funzioni ed esenzione del solo cli.py (C1), FORBIDDEN con tollgate_flow (C19). Nessun test tocca stato/settings reali.
- ⚠️ Evidenza TDD: i test di sessions sono scritti dopo il codice (dichiarato); le suite complete verdi su 3.11 e 3.13 sono solo riportate, non rilanciate.
- ⚠️ off/on esclusi dalla riga programma: vedi Minor 1.

### Punti di forza
- Segnale robusto: merge per sottocomando, scrittura atomica, mai solleva; test per stato non scrivibile, 121 s, symlink, sessione non sicura.
- Il diniego ai subagenti copre anche la forma `python3 <bin>`; test positivi e negativi (verify/block open/status restano permessi).
- test_layers verifica anche il rilevatore (import dentro le funzioni).
- fakegh fallisce con 1 su richieste non previste: i test non passano in silenzio.
- Il report segnala onestamente il dubbio insteadOf.

### Rilievi

**Important**
1. `tests/hookkit.py` (Lab, ramo `origin_url`) + `tests/flowkit.py:30-31`: dubbio (2) CONFERMATO come rischio concreto. `git remote get-url origin` espande insteadOf (verificato: nel FlowLab `git.origin_url(main)` = percorso locale del bare, `repo_key` = «/tmp/tollgate lab …/origin»; `_common.repo_key_of(wt)` idem). `Lab(origin_url=...)` invece crea il lavoro con `repo_key("https://github.com/prova/flow.git")` = `github.com/prova/flow`. Quindi con `FlowLab(issue=N)` la chiave nel DB differisce da `repo_key(git.origin_url(repo))` usata da hook (`_common.py:74-76`, `orphan_tg`, usata in `session.py:25` e `writes.py:36`) e da `cli.current_repo_key` (`cli.py:19-25`): per quei percorsi il ramo `tg/N-*` risulta senza lavoro attivo (orphan), e `find_active(current_repo_key(...), N)` della CLI non troverebbe il lavoro creato dal banco. Il piano impone che la chiave sia ovunque `repo_key(git.origin_url(repo))`; il banco la viola. Il test `test_issue_param_creates_bound_work` non lo vede (controlla solo `bound_work` per sessione). Correzione (scelta nel Task 3, ma il banco va sistemato qui): far calcolare a `Lab` la chiave con `repo_key(git.origin_url(self.main))` (cioè la chiave reale vista dal codice) invece di `repo_key(origin_url)`; oppure far leggere a `git.origin_url` `config --get remote.origin.url` (in tal caso cambia il comportamento di produzione: decisione da portare al controller; per un repo reale senza insteadOf i due coincidono, ma con insteadOf utente la chiave cambierebbe tra versioni). Aggiungere un test: `FlowLab(issue=9)` → `work_items.repo_key == repo_key(git.origin_url(fl.main))` e `repo_key_of(fl.wt)` coincide.
2. Conseguenza per Task 3: `prereq.is_github` e `current_repo_key` non possono basarsi su `get-url` nel banco (l'URL github finto è visibile solo nella config). Va deciso con il controller prima del Task 3 (non è un difetto di questo diff, ma il banco lo rende bloccante).

**Minor**
1. `acts.py:25`: off/on esclusi dalla riga programma. C16 dice «OGNI command_name»; ma la skill `off` dice «Non eseguire comandi» e il wrapper spegne senza Python, il comportamento precedente era già `[]`, quindi l'esclusione è coerente. Da dichiarare al controller come scostamento dalla lettera di C16 (nessun test lo fissa: manca un test che off/on non riceve nulla, o che lo riceve).
2. `sessions.py` (note_cli_call): lettura-merge-scrittura non serializzata tra hook concorrenti della stessa sessione; il tmp resta se `os.replace` fallisce. Trascurabile (Bash sequenziale).
3. `sessions.py` cli_session: un `at` nel futuro passa; confronto di stringhe valido solo se `clock.fmt` ha formato fisso a larghezza costante (lo è, ma non c'è test che lo fissa).
4. `cli_calls.py:_subcommand`: primo argomento non-opzione; se in futuro un'opzione globale prende un valore (`--x val start`) sbaglia. Oggi non esistono tali opzioni.
5. `test_layers`: non intercetta import dinamici (`importlib`, `__import__`); limite accettabile, diverso da test_analysis_isolation.
6. Sessions: test scritti dopo il codice (TDD non seguito per quella parte, dichiarato).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** implementazione fedele a decisioni 2/22 e a carry, ma il banco FlowLab/Lab(origin_url) crea la chiave del repo con una funzione diversa da quella usata da hook e CLI, rendendo inaffidabili i test del flusso dei Task 3+. Va riallineata (e coperta da test) prima di procedere.
