### Task 3: `start` su un lavoro nuovo

**Files:**
- Create: `bin/tollgate_flow/gitw.py`, `bin/tollgate_flow/gh.py`, `bin/tollgate_flow/prereq.py`, `bin/tollgate_flow/housekeeping.py`, `bin/tollgate_flow/start.py`
- Create: `bin/tollgate_analysis/naming.py`
- Modify: `bin/tollgate_core/sessions.py` (`prune_bound`), `bin/tollgate_core/cli.py` (sottocomando `start`)
- Test: `tests/test_naming.py`, `tests/test_prereq.py`, `tests/test_start.py`

**Interfaces:**
- Consumes:
  - core: `phases.create_work`, `phases.find_active`, `db.backup`, `active.register(state, repo, extra=[wt])`, `sessions.mark_bound`, `sessions.cli_session`, `events.prune_events`, `config.load_config`, `git.default_branch`, `git.resolve_ref`, `git.local_branches`, `git.exists_at`;
  - analysis: `level.labels_level`, `level.max_level`.
- Produces in `naming.py` (puro):
  - `slug(title: str) -> str`;
  - `branch_name(issue: int, title: str, taken: set[str]) -> str`;
  - `implementer_name(issue: int, task: int, round_: int = 0) -> str`, che dà `tg-<N>-t<k>`, oppure `tg-<N>-t<k>-r<round>` per `round_ >= 4`.
- Produces in `gitw.py` (scrittura, con `subprocess` e timeout di 120 s per `fetch`):
  - `fetch(repo) -> bool`: falso senza rete, mai un'eccezione;
  - `worktree_add(repo, path, *, branch, start_point, new_branch: bool)`;
  - `add_excludes(repo, lines: list[str])`: righe nuove in `info/exclude` della cartella comune, senza duplicati;
  - `set_config(repo, key, value)`;
  - `remote_branches(repo, pattern) -> list[str]` (con `ls-remote --heads origin`, falso senza rete).

  Errore: `gitw.GitWriteError`.
- Produces in `gh.py`:
  - `GH_ENV = "TOLLGATE_GH"`;
  - `gh_cmd(state) -> list[str]`: `[TOLLGATE_GH]` se `paths.test_env` lo dà, altrimenti `["gh"]`;
  - `run_json(state, repo, args) -> object`;
  - `Issue(number, title, body, state, labels, author_association)`;
  - `issue(state, repo, n) -> Issue`;
  - `prs_for_branch_prefix(state, repo, prefix) -> list[dict]`;
  - `commit_state(state, repo, sha) -> str | None`;
  - `sentinel_issues(state, repo) -> list[dict]`.

  Errore `gh.GhError` (gh assente, uscita diversa da 0, JSON non valido).
- Produces in `prereq.py`:
  - `SUPERPOWERS_RANGE = ((6, 4, 1), (8, 0, 0))`;
  - `GATE_FILES` (decisione 8);
  - `superpowers_version(claude_dir: Path) -> tuple[int, int, int] | None`;
  - `gate_status(repo, ref) -> tuple[list[str], str | None]`: file mancanti e versione;
  - `is_github(repo) -> bool`: legge `git config --get remote.origin.url` **grezzo**, perché `git remote get-url` espande `insteadOf`. La chiave del repo resta ovunque `repo_key(git.origin_url(repo))`, la stessa che usano gli hook;
  - `skill_installed(name: str, *, claude_dir: Path, worktree: Path | None) -> bool` (decisione 16; la usa il Task 6).
- Produces in `housekeeping.py`: `run(conn, state, cfg, *, now) -> list[str]`, che restituisce righe di avviso. Fa:
  - `events.prune_events(events_days)`;
  - `sessions.prune_bound(conn, state, now=now, stale_minutes=...)`: toglie i segnalini delle sessioni non vive e non presenti tra le `sessions` di un lavoro attivo;
  - `backup/.tmp-*` più vecchi di un'ora;
  - `logs/*` e `ctx/*` più vecchi di `retention_days`;
  - `cli/*` più vecchi di un giorno.
- Produces in `start.py`:
  - `StartResult(code: int, lines: list[str], worktree: Path | None, work: int | None)`;
  - `start(state, cwd: Path, issue: int, *, level: str | None, confirm: bool, reopen_execution: bool, claude_dir: Path, now=None) -> StartResult`.

  Codici: 0 = fatto, 1 = rifiuto, 3 = serve conferma (decisione 6). L'ultima riga con codice 0 è `prossimo passo: EnterWorktree <percorso>`.
- CLI: `tollgate start N [--level L1|L2] [--confirm] [--reopen-execution]`. Stampa `lines` ed esce con `code`. La sessione arriva da `cli_session(state, cwd, "start")`.

Ordine dei passi di `start` per un lavoro nuovo (spec 6.1). Ogni rifiuto riporta il motivo:
1. `git.toplevel(cwd)` e il checkout principale (`git.main_worktree`). Se `cwd` non è in un repo git, rifiuto.
2. `gitw.fetch`. Senza rete, al primo avvio, il rifiuto è «senza rete non si avvia un lavoro nuovo».
3. Ramo predefinito (`git.default_branch`). Senza commit, rifiuto. `set_config tollgate.defaultBranch`.
4. `tollgate.toml` su `origin/<predefinito>`: se manca, rifiuto («repo non attivo»). Poi `load_config`.
5. Prerequisiti, ognuno con il suo rifiuto:
   - Superpowers nell'intervallo (decisione 7);
   - `origin` su `github.com`;
   - `gh auth status` con uscita 0;
   - gate installato: un file mancante dà il rifiuto, una versione diversa un avviso.
6. Controlli:
   - checkout principale sporco: avviso;
   - stato del commit predefinito diverso da `success`: chiede conferma;
   - issue chiusa: chiede conferma;
   - `[gate] mode = "detect"`: avviso «modalità rilevazione: il merge non è impedito» più le issue di `sentinel` aperte.
7. Lavoro attivo per (repo, N): si passa alla ripresa (Task 4). Ramo locale `tg/<N>-*`, ramo remoto `tg/<N>-*` o PR da `tg/<N>-*`: rifiuto con `/tollgate:adopt #<N>`.
8. Livello: il massimo tra `--level`, `labels_level(labels, sensitive_labels)` e `L2` se `author_association` non è `OWNER`, `MEMBER` o `COLLABORATOR`.
9. Ramo con `naming.branch_name` (prende i rami locali e remoti). `worktree_add` con `new_branch=True` da `origin/<predefinito>`. Poi `create_work` con `session`, `branch`, `worktree`, `work_base_sha` (SHA di `origin/<predefinito>`) e `gate_mode`, seguito da `db.backup(conn, state, "start")`.
10. Registrazioni:
    - `active.register(state, main, extra=[wt])`;
    - `sessions.mark_bound`;
    - `gitw.add_excludes` (decisione 4);
    - `.tollgate-run/<N>/issue.md` con titolo, etichette e corpo come dato non fidato (spec 6.1);
    - `housekeeping.run`.

- [ ] **Step 1: Test di `naming`** (`tests/test_naming.py::NamingTest`):
  - `slug("Aggiungi l'export CSV!")` == `"aggiungi-l-export-csv"`;
  - `slug("Città più veloce 🚀")` == `"citta-piu-veloce"`;
  - `slug("$(rm -rf ~)")` == `"rm-rf"`;
  - `slug("")` == `"issue"`;
  - `len(slug("a" * 80)) == 40`;
  - `branch_name(7, "Demo", {"tg/7-demo"})` == `"tg/7-demo-2"`;
  - `implementer_name(7, 3)` == `"tg-7-t3"`;
  - `implementer_name(7, 3, 4)` == `"tg-7-t3-r4"`;
  - `implementer_name(7, 3, 2)` == `"tg-7-t3"`.
- [ ] **Step 2: Test di `prereq`** (`tests/test_prereq.py`):
  - `test_superpowers_version_from_registry` (7.0.0 → `(7, 0, 0)`);
  - `test_superpowers_missing_or_malformed` (registro assente o JSON rotto → `None`);
  - `test_gate_status` (repo con i 5 workflow e `VERSION` `0.1.0` → `([], "0.1.0")`; senza `tollgate-run.yml` → quel file è tra i mancanti);
  - `test_skill_installed` (plugin con `skills/x/SKILL.md` → vero; `~/.claude/skills/y/SKILL.md` → vero; skill inesistente → falso).
- [ ] **Step 3: Test di `start`** (`tests/test_start.py::StartNewTest`, con `FlowLab`):
  - `test_start_creates_work_in_path_with_spaces`: `cli("start", "7")` dal checkout principale. Si verificano:
    - uscita 0 e l'ultima riga comincia con `prossimo passo: EnterWorktree`;
    - il ramo `tg/7-<slug>` esiste;
    - il worktree sta sotto `.claude/worktrees/`;
    - senza `--level` e senza etichette sensibili la riga ha `level == "L0"` e `phase == "execution"`; con `start 8 --level L1` su un'altra issue, `level == "L1"` e `phase == "plan"`;
    - `work_base_sha` uguale a `origin/main` e la sessione tra le `sessions`;
    - `bound/sess-flow` esiste;
    - `active/` contiene il worktree;
    - `info/exclude` contiene le tre righe una sola volta anche dopo un secondo `start` su un'altra issue;
    - in `backup/` c'è una copia `*-start.db`.
  - `test_refusals`, uno per sottocaso con il motivo nell'uscita:
    - senza `tollgate.toml` su origin → 1 «non attivo»;
    - senza gate (`FlowLab(gate=False)`) → 1 con il nome del file mancante;
    - Superpowers 6.3.0 → 1;
    - Superpowers 8.0.0 → 1;
    - `gh auth status` che fallisce → 1;
    - origin non GitHub → 1.
  - `test_confirmations`: issue chiusa → 3 con «conferma» e nessuna riga creata; con `--confirm` → 0. Stato del predefinito `failure` → 3.
  - `test_branch_without_row_proposes_adopt`: ramo locale `tg/7-x` → 1 con `/tollgate:adopt #7` e nessun `tg/7-*-2`. Ramo remoto `tg/7-y` → stesso esito.
  - `test_level_from_labels_and_author`: etichetta `security` → L2 (`spec_audit`); `author_association: "NONE"` → L2; `--level L2` → L2.
  - `test_detect_mode_warning`: `mode = "detect"` → la riga «modalità rilevazione» e il titolo dell'issue di `sentinel`.
  - `test_hostile_issue_title_and_body`: titolo `` `$(touch /tmp/PWNED)` ";rm -rf ~" `` e corpo con ```` ``` ```` e `@utente`. Si verificano:
    - ramo `[a-z0-9-]`;
    - `/tmp/PWNED` non esiste;
    - in `issue.md` il recinto è più lungo di ogni sequenza di backtick del corpo;
    - la riga «DATO NON FIDATO» precede il corpo;
    - nessuna chiamata a `fakegh` contiene il titolo.
  - `test_no_session_signal_refuses`: `bin/tollgate start 7` senza segnale → 1 «sessione non riconosciuta».
  - `test_housekeeping`: segnalino `bound/` di una sessione morta tolto, quello di una sessione legata tenuto; `backup/.tmp-x` di 2 ore fa tolto; `ctx/` oltre `retention_days` tolto.
- [ ] **Step 4: Verificare il fallimento**, **Step 5: implementare**, **Step 6: verificare** con `python3 -B -m unittest tests.test_naming tests.test_prereq tests.test_start`, poi `tests/run`.
- [ ] **Step 7: Commit** «tollgate P3a: start su un lavoro nuovo (prerequisiti, worktree, riga, registri, pulizie)».

---

