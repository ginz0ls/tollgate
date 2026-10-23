### Task 12: `init`, misura della modalità, protezione letta da `start`

**Files:**
- Create: `bin/tollgate_gate/protection.py`, `bin/tollgate_flow/init.py`, `templates/tollgate.toml`, `tests/test_protection.py`, `tests/test_init.py`
- Modify: `bin/tollgate_core/cli.py` (`init --propose|--update`), `bin/tollgate_flow/start.py`, `tests/test_start.py`, `tests/fakegh.py` (risposte della GET di protezione e dei check-run)

**Interfaces:**
- Produces in `protection.py`: `classify(status: int | None, message: str) -> str` (decisione 18), `REQUIRED_FIELDS`, `missing(data: dict, *, contexts=REQUIRED_CONTEXTS) -> list[str]` (PR obbligatoria, i due controlli con `app_id` diverso da `-1`, `strict`, `enforce_admins`, niente push forzato né cancellazione), `protection_body(app_id: int) -> dict`, `ProtectionRead(kind, missing, note)`, `read(state, cwd, branch) -> ProtectionRead`.
- Produces in `init.py`: `propose(state, cwd, *, update: bool, merges_per_month: int, services: dict[str, str], now=None) -> InitResult(code, lines, folder)`; codici `OK` 0, `REFUSED` 1.
- CLI: `tollgate init --propose [--merges-per-month N] [--service NOME=IMMAGINE]...`, `tollgate init --update`.

- [ ] **Step 1: Test** `test_protection.py` (con le forme di V2 e di P0): `test_classify` (403 «Upgrade to GitHub Pro…» → `detect`; 403 «Must have admin rights to Repository.» → `undetermined`; 200 → `protected`; 404 «Branch not protected» → `protected_unset`; `None` (rete) → `undetermined`); `test_missing_fields` (protezione senza `strict` e con `app_id: -1` → due voci); `test_body_never_minus_one`.
- [ ] **Step 2: Test** `test_init.py`: `test_detect_proposal` (criterio 11: 403 → `tollgate.toml` con `mode = "detect"`, nessun `protect.sh`); `test_protected_unset_proposes_command` (404 → `protected`, `protect.sh` che legge `.app.id` dal check-run di `tollgate-base` e si ferma se manca); `test_token_without_admin_undetermined` (criterio 34: nessun file con `protected`, messaggio che chiede le credenziali dell'utente); `test_files_tree` (i file di `install.files`, `README.md` con i passi in ordine: copia, commit sul predefinito, poi `protect.sh`); `test_minutes_estimate` (con ricevute nel DB e senza); `test_jest_junit_hint`; `test_update_only_changed_files` (`--update` con una versione vecchia sul predefinito → solo i file diversi e il ramo `tollgate-config/<versione>`); `test_existing_workflow_violations_listed` (decisione 15: un workflow già presente con `statuses: write` compare nel `README.md`); `test_untrusted_names` (un nome di servizio con caratteri non ammessi è rifiutato: `^[a-z0-9-]+$` per il nome, immagine senza spazi).
- [ ] **Step 3: Test** `test_start.py::ProtectionTest`: `test_protected_missing_fields_warned` (criterio 11, terza parte); `test_unreadable_protection_continues`; `test_detect_does_not_read_protection`; `test_actions_disabled_warned` (9.6: `enabled: false` → avviso; risposta illeggibile → nota).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: init con la misura della modalità e la proposta dei file; protezione letta da start».

---

