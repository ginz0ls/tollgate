### Task 3: Sezione `[models]` e controllo completo

**Files:**
- Modify: `bin/tollgate_core/config.py`, `bin/tollgate_core/git.py`
- Create: `bin/tollgate_flow/models_check.py`, `tests/test_models_check.py`
- Test: `tests/test_config.py`, `tests/test_git.py`

**Interfaces:**
- Consumes: Task 1 e 2; `git.show(repo, ref, path) -> bytes | None`; `config.Config.get`.
- Produces:
  - `config.DEFAULTS["models"] = {"files": []}`, `config.DEFAULTS["components"]["models_check"] = True`;
  - `git.object_info_at(repo, ref, path) -> tuple[str, int] | None` (tipo e dimensione con `git cat-file`; percorso assente → `None`);
  - `models_check.PLUGIN_ROOT` (come `init.PLUGIN_ROOT`); `models_check.MAX_LINES = 12`; `models_check.DEADLINE_S = 20`; `models_check.MAX_FILE_BYTES = 256 * 1024`; `config.MODELS_MAX_FILES = 20` (decisione 1);
  - `models_check.check(state: State, repo: Path, ref: str, cfg: Config, *, environ: Mapping[str, str], now, plugin_root: Path | None = None, refresh: bool = False, show_cache: bool = True, fetch=None, clock=None) -> list[str]` (righe senza il prefisso `avviso:`; `plugin_root=None` → `models_check.PLUGIN_ROOT` letto al momento della chiamata; `models.parse_pages`, `git.object_info_at`, `git.show` e `modelsfetch.cached_pages` si chiamano sempre attraverso il loro modulo, anche dentro il `validate`, così i `mock.patch` dei test li sostituiscono; `show_cache=False`, che passa `start`, toglie la riga della cache fresca (decisione 7); non solleva mai: un'eccezione inattesa dà la sola riga «controllo non riuscito»).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_config.py`: `test_models_files_default_empty`; `test_models_files_type_checked` (un numero → `ConfigError` come le altre liste); `test_bad_paths_dropped_with_warning` (`"/etc/x"`, `"../x"`, `"src/*.py"`, `"a\nb.py"`, `"a;b.py"` tolti, ognuno con un avviso senza a capo; `"src/ai/models.py"`, `"app/[id]/models.ts"` e `"my dir/m.py"` restano); `test_models_files_capped` (25 voci → 20, con un avviso); in `tests/test_git.py` `test_object_info_at` (file, cartella, assente); `test_models_check_component_default_true`.
  - `tests/test_models_check.py` (sotto `no_network()`; repo git temporaneo con `origin` nudo come i lab esistenti; `fetch` finto; radice del plugin temporanea con un `templates/models.toml` dagli host `https://<nome>.invalid`): `test_component_off_no_network`; `test_no_files_no_network`; `test_no_files_with_ai_profile_reminds`; `test_reads_files_from_ref_not_worktree`; `test_missing_file_line`; `test_binary_or_large_file_line` (il file grande non passa da `git.show`); `test_folder_entry_line` («non è un file»); `test_no_key_at_all_one_line_no_network` (`files` non vuoto, nessuna chiave: una sola riga con le quattro variabili dedicate, il `fetch` finto mai chiamato); `test_some_keys_missing_lines` (chiave solo per Anthropic, file con `"gemini-3.6-flash"` e `"claude-x-5"`: una riga «manca la chiave» per Gemini, nessuna per OpenAI e OpenRouter); `test_one_provider_fails_other_reports`; `test_corrupt_cache_refetched`; `test_deadline_skips_remaining_providers` (`clock` finto: dopo il primo fornitore la scadenza è passata → riga «saltato, tempo del controllo finito» per gli altri); `test_lines_capped` (20 avvisi → 12 righe più «… e altri 8 avvisi»); `test_check_never_raises` (`fetch` che solleva `RuntimeError`, `parse_pages` che solleva `ModelsFormatError` (riga «forma inattesa» per quel fornitore), `git.object_info_at` e `git.show` che sollevano → righe, nessuna eccezione); `test_end_to_end_anthropic_newer_and_deprecated` (un file con due modelli, elenco finto: le due righe attese); `test_plugin_root_resolved_at_call` (`mock.patch.object(models_check, "PLUGIN_ROOT", …)` è la radice usata); `test_fresh_cache_line_hidden_when_asked` (con `show_cache=False` la riga della cache fresca non c'è, quella della rete fallita sì).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `config`: la sezione e il componente nelle `DEFAULTS`, il filtro dei percorsi della decisione 1 con avvisi in `Config.warnings`. `models_check`: componente → file da `ref` (tetto e binari) → letterali (con `where`) → chiavi (decisione 4) → per ogni fornitore con chiave, finché la `Deadline` lo permette, `cached_pages`, `parse_pages`, `used`, `findings` → riga per il fornitore che fallisce → tetto delle righe.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_config tests.test_models_check`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: sezione [models] e controllo dei modelli del progetto».

---

