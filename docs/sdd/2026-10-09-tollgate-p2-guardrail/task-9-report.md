# Task 9: Git in sola lettura: report

**Status:** DONE
**Commit:** `6a036f3` tollgate P2: accesso a git in sola lettura
**Base:** `975bb06`. **Ramo:** `p2-guardrail`. **Worktree:** `.claude/worktrees/p2-guardrail`.

## Implementato

- `bin/tollgate_core/git.py`: `GitError`, `Change`, `run`, `ok`, `toplevel`, `head`, `branch`,
  `common_dir`, `worktrees`, `main_worktree`, `local_branches`, `resolve_ref`, `default_ref`,
  `default_branch`, `origin_url`, `changes`, `commit_changes`, `diff_size`, `show`, `text_at`,
  `worktree_text`, `exists_at`, `blob_sha`, `rev_list`, `fingerprint`, `is_clean`, più i
  privati `_proc`, `_parse_z`, `_untracked`, `_text`, `_resolved`, `_excluded`. Firme e valori come nel brief.
- `tests/test_git.py`: i 6 test del brief (`test_toplevel_of_missing_path`, `test_changes_worktree_and_untracked`,
  `test_commits_and_text`, `test_default_ref_order`, `test_worktrees_and_branches`, `test_fingerprint_and_clean`)
  più 3 test aggiuntivi:
  - `test_toplevel_inside_git_dir` (C3): `.git/config`, `.git/hooks/pre-commit` (inesistente) e `wt/.git` (file di worktree) danno la radice corretta.
  - `test_toplevel_through_symlink`: percorsi attraverso un collegamento simbolico, dentro il repo e dentro `.git`.
  - `test_text_non_utf8_is_readable` (C11): `b"caff\xe8\n"` diventa `"caffè\n"`; un blob con `\0` resta `None`.

## Decisioni del controller (carry.md, Task 9)

- **C3 (`toplevel` dentro `.git`)**: implementato. Il percorso viene normalizzato (`os.path.abspath`, poi
  risoluzione dei collegamenti sulla parte esistente, la coda mancante resta lessicale). Se una componente
  si chiama `.git`, si usa l'ultima occorrenza e la sua cartella padre come punto di partenza. Altrimenti si
  risale alla prima cartella esistente. `git rev-parse --show-toplevel` da lì dà la radice. Un `.git` file
  (worktree collegato) dà il worktree.
- **C11 (decodifica di `_text`)**: implementato. Prima UTF-8 stretto, poi ripiego su Latin-1, che non può fallire.
  Il brief aveva `decode("utf-8", "replace")`: con `\xe8` dava `caff�`, cioè non leggibile. Ora
  `caff\xe8` diventa `caffè`.

## Scostamenti dal brief

- `toplevel` riscritto per C3 (il brief lo sbagliava per i percorsi dentro `.git`: restituiva `None`). Il
  nuovo corpo è 15 righe, con `_resolved` come helper.
- `_text`: ripiego Latin-1 invece di `replace` (C11, vedi sopra).
- `toplevel`: il `rev-parse` è ora `check=False` con `GitError` catturato, così un `git` mancante dà `None`
  e non un'eccezione fuori dal contratto.

## Evidenza TDD

**RED 1** (prima di `git.py`), `python3 -B -m unittest tests.test_git -v`:
```
ImportError: cannot import name 'git' from 'tollgate_core' (.../bin/tollgate_core/__init__.py)
```

**RED 2** (`git.py` come da brief, test C3/C11/symlink nuovi):
```
FAIL: test_text_non_utf8_is_readable  AssertionError: 'caff�\n' != 'caffè\n'
FAIL: test_toplevel_inside_git_dir    AssertionError: None != PosixPath('/tmp/tollgate git 9oqiqw9z/repo con spazi')
FAIL: test_toplevel_through_symlink   AssertionError: None != PosixPath('/tmp/tollgate git tlsm0fye/repo con spazi')
Ran 9 tests ... FAILED (failures=3)
```
I 6 test del brief passavano già con l'implementazione del brief.

**GREEN** (dopo il fix di `toplevel`, `_text`, `import os`), `python3 -B -m unittest tests.test_git -v`:
```
Ran 9 tests in 0.127s
OK
```

**Suite**, `tests/run` (PYTHONS: python3.11 e python3):
```
== Python 3.11.16
Ran 315 tests in 1.645s   OK
== Python 3.13.5
Ran 315 tests in 1.665s   OK
```
315 = 306 precedenti + 9 nuovi. Output pulito (solo i punti e `OK`). Nessun `__pycache__` nel repo.

## File cambiati

- `bin/tollgate_core/git.py` (nuovo)
- `tests/test_git.py` (nuovo)

Nessun altro file. `git status` pulito dopo il commit.

## Autorevisione

- Completezza: tutte le firme del brief presenti; C3 e C11 coperti da test.
- Review Focus 3: percorsi con spazi (il repo di test è `repo con spazi`, nella cartella `tollgate git ...`); collegamenti simbolici (test dedicato); file inesistenti (`test_toplevel_of_missing_path`, e `.git/hooks/pre-commit` che non esiste).
- Confronto con il worktree: `worktrees`, `main_worktree`, `common_dir` restituiscono percorsi risolti (`Path.resolve()`); i test confrontano con `.resolve()`.
- Nessun repo creato nel repo: i test usano solo cartelle temporanee.

## Dubbi (non bloccanti)

- `toplevel` usa l'ultima componente `.git` del percorso. Un repo annidato in una cartella che si chiama `.git`
  (caso raro) verrebbe attribuito alla cartella sbagliata. Non ho aggiunto un test: non è nello scope.
- Se la cartella che dovrebbe possedere `.git` non esiste (es. `/x/nuovo/.git/y`), `toplevel` risale alla prima cartella esistente. Il risultato può essere un repo esterno. Coerente con la regola «prima cartella esistente» del brief.
- Il ripiego Latin-1 interpreta un blob non UTF-8 come Latin-1 anche se non è Latin-1 (es. Windows-1252 con simboli). Il testo resta leggibile, ma alcuni caratteri possono essere sbagliati. È la scelta per C11.

## Fix round 1

**Commit:** `9334bf3` tollgate P2: git in sola lettura, fix round 1 (indice, timeout, fingerprint, driver)

Ogni punto è partito da un test RED osservato prima della correzione.

- **I1 (indice non toccato).** RED: `AssertionError: Tuples differ` su (byte dell'indice, mtime) dopo `changes`. `GIT_OPTIONAL_LOCKS=0` da sola non basta: `git diff <commit>` (col working tree) riscrive `.git/index` col refresh anche con quella variabile. Sonda: `status` con `--no-optional-locks` e `ls-files` non scrivono; `diff` sì. Correzione: `_private_index(repo)` copia l'indice reale (`rev-parse --path-format=absolute --git-path index`, quindi vale anche per i worktree) in una cartella temporanea e passa `GIT_INDEX_FILE` ai diff col working tree (`changes` e `diff_size` senza `head`). `_proc` passa `GIT_OPTIONAL_LOCKS=0` e `--no-optional-locks` (opzione globale, prima di `-C`, quindi vale anche per `status`). Test: `test_read_only_leaves_index_untouched`.
- **I2 (timeout).** RED: `TimeoutExpired` non convertita. Correzione: `GIT_TIMEOUT_S = 10` come default di `_proc(timeout=...)`; `TimeoutExpired` diventa `GitError("git <args>: timeout dopo 10 s")`. `ok` e `toplevel` catturano già `GitError`. Test: `test_timeout_becomes_git_error`.
- **I3 (fingerprint).** RED: `OSError: [Errno 40] Too many levels of symbolic links` (link ciclico) e `PermissionError` (chmod 0). Correzione: `except OSError` → digest `"illeggibile"`, dopo `FileNotFoundError` e `IsADirectoryError`. Test: `test_fingerprint_survives_symlink_loop`, `test_fingerprint_survives_unreadable_file` (saltato se girato come root; qui eseguito).
- **M1 (lettura a blocchi).** RED: `AssertionError: letto tutto` (`_untracked` usava `read_bytes`). Correzione: `_scan(path)` legge 8000 byte per il NUL, poi conta le righe a blocchi da 64 KiB. Test: `test_untracked_is_scanned_in_blocks` (100001 righe; un NUL oltre il byte 8000 non rende il file binario).
- **M2 (driver e fsmonitor).** RED: `True is not false` su `diff.external` e `core.fsmonitor` (sentinella creata da `changes`/`diff_size`). Correzione: `_proc` lancia con `-c core.fsmonitor=false`; i diff ricevono `--no-ext-diff --no-textconv`. Test: `test_external_diff_driver_never_runs`, `test_fsmonitor_hook_never_runs`. Ciascuno ha un controllo con git diretto che fa scattare lo script, quindi non è un falso verde. Lo script sta in una cartella senza spazi (git lancia questi comandi tramite shell). Il primo tentativo era un falso verde: il fsmonitor non scattava senza modifiche, e lo script con spazi nel percorso non partiva.

**Test mirato:** `python3 -B -m unittest tests.test_git`: `Ran 16 tests ... OK`.
**Suite:** `tests/run` (python3.11 e python3.13): `Ran 322 tests` su entrambi, `OK`, output pulito, nessun `__pycache__`.
**File:** `bin/tollgate_core/git.py`, `tests/test_git.py`.

**Scostamenti dal coordinatore:**
- `--no-optional-locks` è globale (prima di `-C`), non argomento di `status`: è un'opzione di git, non del sottocomando.
- L'indice viene copiato a ogni diff col working tree. Il costo cresce con la dimensione dell'indice. È l'unico modo trovato per evitare la riscrittura di `.git/index` (vedi I1).
- `show` (usato da `text_at`) non cattura il timeout: propaga `GitError`, come `run`.

**Autorevisione:** nessun file cambiato oltre `git.py` e `test_git.py`. Il worktree collegato è verificato a parte: `--git-path index` punta a `.git/worktrees/wt-1/index`, `changes` e `diff_size` corretti.
