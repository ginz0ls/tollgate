### Task 2: Regole di area, scrittore TOML e frammenti

**Files:**
- Modify: `bin/tollgate_analysis/research.py`
- Create: `bin/tollgate_analysis/tomlout.py`, `bin/tollgate_core/fragments.py`, `tests/test_tomlout.py`, `tests/test_fragments.py`
- Test: `tests/test_research.py`

**Interfaces:**
- Consumes: `research.enforced(text)`, `research.base_rules(text)`, `config.PROFILE_DEFAULTS`, `config.load_config_text(text)`.
- Produces:
  - `research.area_rules(skill_text: str, area: str) -> tuple[set[str], set[str]]`;
  - `tomlout.table(name: str, values: dict) -> str` (decisione 8);
  - `fragments.Fragment` (dataclass frozen: `area: str`, `profile: dict`, `detect: tuple[str, ...]`, `skill_path: Path`, `source: Path`);
  - `fragments.FragmentError(ValueError)` con il nome del file nel messaggio;
  - `fragments.load(plugin_root) -> list[Fragment]` (ordinati per `area`; cartella assente → `[]`; un frammento illeggibile, con un nome riservato o non valido, con chiavi fuori da `PROFILE_DEFAULTS`, o con `rules`/`blocking_rules` è una `FragmentError`);
  - `fragments.approved(fragment) -> bool` (`research.enforced` sul testo della skill; skill assente o illeggibile → `False`);
  - `fragments.rules(fragment) -> tuple[list[str], list[str]]` (ordinati, da `area_rules`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_research.py`: `test_area_rules_extracts_prefix` (un testo con `R-AI-01 [blocca] …`, `R-AI-02 …` e una riga `R-BASE-01 …` → `({"R-AI-01","R-AI-02"}, {"R-AI-01"})` per `area="ai"`); `test_area_rules_ignores_inline_mentions` (un id citato a metà riga non conta); `test_real_base_rules_unchanged` (`base_rules(t) == area_rules(t, "BASE")` sul testo vero di `skills/rules-base/SKILL.md`).
  - `tests/test_tomlout.py`: `test_round_trip` (un dizionario con stringhe con `"`, `\`, a capo, tabulazione, DEL e accenti, un `bool`, una lista di stringhe vuota e piena, un `dict` di stringhe con una chiave `lint:fix` → `tomllib.loads(table("profiles.ai", d))["profiles"]["ai"] == d`); `test_rejects_other_types` (`int`, `float`, `None`, lista di numeri → `TypeError`).
  - `tests/test_fragments.py` (radice temporanea): `test_load_reads_profile_and_detect`; `test_load_missing_dir_is_empty`; `test_load_rejects_unknown_key`; `test_load_rejects_rules_in_fragment`; `test_load_rejects_reserved_names` (`base.toml`, `active.toml`); `test_load_rejects_other_pattern_forms` (un pattern che non è `**/<cartella>/**` → `FragmentError`, decisione 5); `test_load_rejects_unreadable` (TOML non valido → `FragmentError` col nome del file); `test_approved_needs_approved_skill` (skill assente, senza `approved`, con `approved: 2026-11-01`); `test_rules_from_skill`; `test_fragment_profile_validates` (il `[profile]` con le `rules` calcolate, scritto con `tomlout.table` in `[profiles.x]`, passa `config.load_config_text` senza avvisi).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `area_rules` con la regex `^(R-<AREA>-\d{2})( \[blocca\])? \S` (`<AREA>` = `re.escape(area.upper())`); `base_rules` la chiama. `tomlout` per la decisione 8. `fragments` in `tollgate_core` (legge file del plugin; importa `tollgate_analysis.research` e `config`), con `skill_path = plugin_root / "skills" / f"rules-{area}" / "SKILL.md"`.
- [ ] **Step 4: Verifica.** I file di test: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: regole di area dal testo, scrittore TOML e frammenti di profilo».

---

