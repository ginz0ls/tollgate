### Task 2: Dati dei fornitori, client HTTP e cache

**Files:**
- Create: `templates/models.toml`, `bin/tollgate_flow/modelsfetch.py`, `tests/test_modelsfetch.py`
- Modify: `tests/helpers.py`

**Interfaces:**
- Consumes: `models.PROVIDERS` (Task 1); `paths.State`.
- Produces:
  - `modelsfetch.Provider` (dataclass frozen: `name`, `url`, `host`, `paging`, `auth`, `headers: dict[str, str]`, `env: tuple[str, ...]`, `page`, `hint: str`, un'espressione regolare, vuota = nessuna forma);
  - `modelsfetch.ProvidersError(ValueError)`; `modelsfetch.load_providers(plugin_root: Path) -> dict[str, Provider]` (decisioni 5 e 9);
  - `modelsfetch.api_key(provider: Provider, environ: Mapping[str, str]) -> str | None` (decisione 4);
  - `modelsfetch.FetchError(Exception)` (solo i testi della decisione 5);
  - `modelsfetch.Deadline` (`Deadline(seconds, clock=time.monotonic)`, metodi `left() -> float` e `check()` che solleva `FetchError("tempo scaduto")`);
  - `modelsfetch.build_opener() -> urllib.request.OpenerDirector`;
  - `modelsfetch.fetch_pages(provider: Provider, key: str, *, deadline: Deadline, opener=None, timeout: float = 5.0, max_bytes: int = 8 * 1024 * 1024, max_pages: int = 10) -> list[dict]` (`opener=None` → `build_opener()` al momento della chiamata);
  - `modelsfetch.CACHE_HOURS = 24`; `modelsfetch.cached_pages(state: State, provider: Provider, key: str, *, now, deadline: Deadline, validate: Callable[[list[dict]], object], refresh: bool = False, fetch=None) -> tuple[list[dict], str | None]` (`validate` è chiamata sulle pagine nuove prima di scrivere la cache; se solleva, la cache non si scrive e l'eccezione esce) (`fetch=None` → `modelsfetch.fetch_pages` cercata al momento della chiamata, così un `mock.patch` del modulo la sostituisce; seconda voce: `None` se l'elenco viene dalla rete, altrimenti la riga di cache della decisione 13 senza il prefisso `modelli: <fornitore>: `; senza cache e con la rete fallita solleva `FetchError`);
  - in `tests/helpers.py`: `MODEL_KEY_VARS` (tutte le variabili della decisione 4) e il context manager `no_network()` che toglie quelle variabili da `os.environ` e sostituisce `socket.socket` e `socket.create_connection` con un finto che solleva `AssertionError("rete in un test")`.

- [ ] **Step 1: I test che falliscono** (`tests/test_modelsfetch.py`, sotto `no_network()`; `opener` finto con `open(request, timeout)` che registra la richiesta e restituisce una risposta finta con `status`, `headers`, `read(n)`, oppure solleva):
  - `test_real_providers_file_loads` (`load_providers(ROOT)` dà i quattro fornitori, `url` `https`, Gemini con `auth = "x-goog-api-key"`, Anthropic con `anthropic-version`); `test_providers_file_rejects_bad_urls_keys_and_providers` (radice temporanea: `http`, utente nell'URL, porta, `key=` nella query, chiave sconosciuta, fornitore in più o mancante → `ProvidersError`);
  - `test_real_hosts_not_in_bin` (nessun file sotto `bin/` contiene un host di `templates/models.toml`);
  - `test_api_key_order` (dedicata prima di quella standard; vuota saltata; nessuna → `None`; Gemini: `GOOGLE_API_KEY` prima di `GEMINI_API_KEY`);
  - `test_bearer_and_version_headers`; `test_gemini_key_in_header_not_url`;
  - `test_anthropic_pages_followed` (`has_more` vero e `last_id` → seconda richiesta con `after_id`); `test_gemini_pages_followed` (`nextPageToken` → `pageToken`); `test_page_cap` (11 pagine possibili → `FetchError("troppe pagine")`);
  - `test_fetch_errors_are_fetch_errors` (401, 403, 429, 500, `TimeoutError`, `URLError`, HTML, JSON non valido → `FetchError` con il testo fisso della decisione 5); `test_redirect_refused` (l'`opener` di `build_opener()`: il suo gestore dei redirect solleva `FetchError("redirect rifiutato")`); `test_environment_proxy_ignored` (con `https_proxy` nell'ambiente l'`opener` non usa proxy); `test_other_host_refused` (una pagina successiva o una richiesta costruita verso un host diverso da `provider.host` → `FetchError`); `test_body_over_cap_stops` (lettura a pezzi: si ferma oltre `max_bytes`);
  - `test_deadline_stops_between_chunks_and_pages` (orologio finto: la scadenza passa dopo il primo pezzo o la prima pagina → `FetchError("tempo scaduto")`);
  - `test_key_never_in_errors_lines_or_cache` (chiave `sk-PROVA-123`; i finti errori **la contengono** apposta, nel messaggio di un `URLError` e nelle intestazioni di un `HTTPError`: il `FetchError` che ne esce non la ha in `str` né in `repr`, e ha `__context__` e `__cause__` uguali a `None`; il file di cache scritto dopo un successo non la contiene);
  - `test_cache_fresh_used` (entro 24 ore niente rete, seconda voce «elenco dalla cache del <data>»); `test_cache_stale_refetched`; `test_corrupt_cache_refetched`; `test_refresh_ignores_cache`; `test_failed_fetch_keeps_and_uses_cache` (seconda voce «rete non riuscita (…), elenco dalla cache del <data>»); `test_cache_written_atomically`; `test_cache_not_written_when_validate_fails`; `test_future_cache_is_stale`; `test_patched_fetch_is_used` (`mock.patch("tollgate_flow.modelsfetch.fetch_pages")` è quello che `cached_pages` chiama);
  - `test_hooks_do_not_reach_models_net` (analisi degli import come `tests/test_layers.py` sui moduli di `tollgate_hooks` e `tollgate_checks`; per `hooks/run`, il testo non nomina `modelsfetch` né `models_check`); `test_hook_run_does_not_load_models_net` (in un processo figlio, come `test_gate_runtime_has_no_db`, senza lanciare nessun comando: si importano `tollgate_core.cli`, `tollgate_hooks.runner` e tutti i moduli di `tollgate_checks`, poi `tollgate_flow.modelsfetch` non è in `sys.modules`; nessuno stato vero toccato; per questo `models_check` importa `modelsfetch` dentro `check`, e `cli.py` importa `models_check` solo nel ramo `models`);
  - `test_no_network_helper` (`no_network()` toglie le variabili e fa fallire `socket.create_connection`); `test_model_key_vars_match_providers_file` (`helpers.MODEL_KEY_VARS` è l'unione delle `env` di `templates/models.toml`).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice e i dati.** `templates/models.toml` con i valori della tabella «Fatti verificati», della decisione 9 e dello Step 0 del Task 1 (`url` con `limit=1000` per Anthropic e `pageSize=1000` per Gemini; `page`: per Anthropic https://platform.claude.com/docs/en/about-claude/model-deprecations, per Gemini https://ai.google.dev/gemini-api/docs/deprecations, per OpenAI https://developers.openai.com/api/docs/deprecations, per OpenRouter https://openrouter.ai/docs/guides/overview/models.md: gli indirizzi già in «Dove informarsi» di `rules-ai`). `modelsfetch.py` per le decisioni 5, 7 e 9. Nessun `print`, nessun log. `no_network()` in `tests/helpers.py`.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_modelsfetch tests.test_layers tests.test_rules_ai`: PASS (`test_real_markers_not_in_tollgate_bin` invariato e verde). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: dati dei fornitori, client HTTP stretto e cache degli elenchi».

---

