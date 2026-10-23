# Ri-revisione giro di correzione 1, Task 2 (02f9637..82a962b)

### Verdetti sui rilievi

**1. `git.blob_text` non chiamava `_check_ref`; assente dalla tabella del test; verificare le altre funzioni.** INDIRIZZATO.
- `bin/tollgate_core/git.py:311` `_check_ref(sha)` prima di `_proc`. `tests/test_git.py` riga `"blob_text"` aggiunta alla tabella di `test_refs_starting_with_dash_refused` (il test asserisce `run.assert_not_called()` e `GitError`).
- Controllo di tutte le funzioni di `git.py` a HEAD che ricevono un riferimento o uno SHA: `resolve_ref` (137), `changes` base/head (245-247), `diff_size` (272-274), `show` (290), `text_at` (via `show`), `blob_text` (311), `ls_files_at` (326), `blob_at` (336), `exists_at` (349), `rev_list` (358-359), `patch_id` (409-410), `fetch_ref` (429) sono coperte. `range_base` passa da `resolve_ref` (il controllo scatta su `f"{first_commit}^"`, che comincia con `-` se lo fa `first_commit`), `commit_changes` da `range_base` e `changes`. `default_branch`/`default_ref` costruiscono i riferimenti (`origin/...`). `blob_sha` e `worktree_text` ricevono percorsi (`blob_sha` usa `--`). `run`/`ok`/`_proc` sono primitive generiche. Nessuna funzione rimasta fuori.

**2. Ruling del controller: `GIT_TERMINAL_PROMPT=0` nell'ambiente del figlio di `fetch_ref`.** INDIRIZZATO.
- `git.py:430` imposta la variabile sempre (con o senza token); con token `env |=` aggiunge le tre `GIT_CONFIG_*`. `_proc` (riga 45) fonde `extra_env` sopra `os.environ`, quindi il valore arriva al processo.
- Asserzioni: `test_fetch_ref_passes_token_only_in_environment` (`env["GIT_TERMINAL_PROMPT"] == "0"`) e `test_fetch_ref_without_token_...` (stessa asserzione sul `env` realmente passato a `subprocess.run`, più assenza di `GIT_CONFIG_COUNT`). Il report indica `tests.test_git` 34 OK e suite verde su 3.11 e 3.13.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
