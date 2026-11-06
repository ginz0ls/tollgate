### Task 1: Confronto puro dei modelli

**Files:**
- Create: `bin/tollgate_analysis/models.py`, `tests/test_models.py`

**Interfaces:**
- Produces:
  - `models.PROVIDERS = ("anthropic", "gemini", "openai", "openrouter")`;
  - `models.ModelInfo` (dataclass frozen: `provider: str`, `id: str`, `family: str | None`, `stable: bool`, `created: str | None`, `retires: str | None`, `retiring: bool`);
  - `models.ModelsFormatError(ValueError)`;
  - `models.parse_pages(provider: str, pages: list[dict]) -> list[ModelInfo]` (una forma inattesa è `ModelsFormatError`; un elemento senza `id`/`name` stringa si salta);
  - `models.literals(text: str) -> set[str]` (decisione 2);
  - `models.used(literals: set[str], infos: list[ModelInfo]) -> list[tuple[str, ModelInfo]]` (coppie letterale → modello, con le normalizzazioni e gli alias della decisione 2);
  - `models.gemini_family(model_id: str) -> tuple[str, tuple[int, ...]] | None` (decisione 3);
  - `models.findings(provider: str, matches: list[tuple[str, ModelInfo]], infos: list[ModelInfo], literals: set[str], *, where: dict[str, str], page: str) -> list[str]` (`where`: letterale → file dichiarato in cui compare; righe nella forma della decisione 13).

- [ ] **Step 0 (controller): i fatti da verificare.** Con `WebFetch` sulle pagine indicate in «Da verificare prima del codice»: (a) gli alias di Anthropic nell'elenco; (b) la variabile d'ambiente di OpenRouter. In più (c) la forma degli ID di OpenAI sulla pagina dei modelli, per `hint` (decisione 4): la forma scelta non deve accettare nomi che cominciano con `claude-` o `gemini-` (lo controlla `test_real_providers_file_loads`). Scrivi gli esiti in una `Ruling:` con gli URL e passali nel brief dei Task 1 e 2. Se (a) dice che gli alias compaiono, il test `test_alias_and_vertex_ids_not_flagged` resta (la regola non scatta mai); se (b) non trova un nome, in `env` resta la sola variabile dedicata.
- [ ] **Step 1: I test che falliscono** (`tests/test_models.py`, pagine finte costruite nel test, mai testo dei fornitori):
  - `test_literals_quotes_and_charset` (`"claude-x-5"`, `'gemini-3.6-flash'`, `` `gpt-x` `` presi; `"due parole"`, `""`, `"claude-x-5@20260101"` e un letterale di 200 caratteri no); `test_literals_ignore_comments_without_quotes` (anche `# l'agente usa "claude-x-5"`: l'apostrofo non si accoppia con le virgolette e `claude-x-5` si vede);
  - `test_parse_anthropic` (`line`, `lifecycle`, `created_at`, `retires_at` → `ModelInfo`; `stable` solo con `active`; `retiring` con `deprecated`); `test_parse_gemini_strips_models_prefix`; `test_parse_openai_shutdown_date`; `test_parse_openrouter_expiration_date`; `test_parse_wrong_shape_raises` (`data` non lista, `models` non lista, pagina non dizionario → `ModelsFormatError`);
  - `test_used_exact_match_and_prefixes` (`"anthropic:claude-x-5"` e `"models/gemini-3.6-flash"` riconosciuti contro un elenco che ha `claude-x-5` e `models/gemini-3.6-flash`; `"claude"` e `"gemini-cli"` no);
  - `test_alias_and_vertex_ids_not_flagged` (elenco con `claude-x-4-5-20250101`: il letterale `"claude-x-4-5"` vale come quell'ID, con la riga «alias di claude-x-4-5-20250101», e non dà «non è nell'elenco»; `"claude-x-4-5@20250101"` non è un candidato);
  - `test_anthropic_newer_same_line` (in uso `a-old` `sonnet` 2026-01; nell'elenco `a-new` `sonnet` `active` 2026-09 e `b-newer` `opus` 2026-10 → una riga che nomina `a-new`, nessuna su `b-newer`); `test_anthropic_newer_skipped_without_line_or_epoch_date`; `test_anthropic_deprecated_with_date`; `test_anthropic_deprecated_newer_not_from_deprecated` (un `deprecated` più nuovo non è proposto);
  - `test_gemini_family_parse` (`gemini-3.6-flash` → `("flash", (3, 6))`; `gemini-3.6-flash-lite` → `("flash-lite", (3, 6))`; `gemini-2.0-flash-001` → `("flash", (2, 0))`; `gemini-3.8-flash-tts` → `("flash-tts", (3, 8))`; `gemini-2.5-flash-preview-09-2025` → `("flash", (2, 5))`; `gemini-flash-latest` e `gemini-embedding-001` → `None`); `test_gemini_newer_stable_only` (in uso `gemini-3.5-flash`; nell'elenco `gemini-3.6-flash`, `gemini-3.7-flash-preview-…` e `gemini-3.9-flash-tts` → la riga nomina solo `gemini-3.6-flash`); `test_gemini_version_numeric` (`3.10` è più nuovo di `3.9`); `test_gemini_latest_no_newer`; `test_gemini_retirement_not_checked_line` (una sola riga «ritiro non controllato», con `page`);
  - `test_openai_shutdown_and_not_checked`, `test_openrouter_expiration_and_not_checked` (riga di ritiro con la data; una riga «più nuovo non controllato» per fornitore);
  - `test_unknown_prefix_only_for_versioned_names` (`"claude-x-5"` e `"claude-3-opus-20240229"` assenti dall'elenco di Anthropic e non alias → «non è nell'elenco»; `"claude-code"` e `"gemini-cli"` no);
  - `test_line_forms` (ogni riga prodotta ha una delle forme per modello o per fornitore della decisione 13; nessuna riga per un fornitore senza modelli in uso; un ID con un carattere di controllo esce neutralizzato); `test_lines_ordered_model_first` (le righe per modello precedono quelle per fornitore).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_models`: FAIL (modulo assente).
- [ ] **Step 3: Il codice.** `models.py` per le decisioni 2, 3 e 13. Le date si confrontano come stringhe ISO 8601 (ordinabili); l'epoca è una data che comincia con `1970-01-01`. Il modulo non importa nulla di tollgate (la neutralizzazione dei testi è una funzione sua, sul modello di `init._plain`).
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_models tests.test_analysis_isolation tests.test_layers`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: confronto puro dei modelli con gli elenchi ufficiali».

---

