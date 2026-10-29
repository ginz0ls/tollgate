### Task 3: Analisi pure: nota di ricerca, percorsi, URL, letture da Bash

**Files:**
- Create: `bin/tollgate_analysis/research.py`, `tests/test_research.py`
- Modify: `bin/tollgate_analysis/bash.py` (`read_targets`), `tests/test_bash.py`

**Interfaces:**
- Consumes: i campioni `spikes/fixtures/hook-inputs/samples-b1.json` e le `Ruling:` del Task 1.
- Produces (tutto puro, nessun import di tollgate fuori da `tollgate_analysis`):
  - `RULES_BASE = "skills/rules-base/SKILL.md"`; `enforced(skill_text: str | None) -> bool` (decisione 8: frontmatter tra `---` iniziali con `approved:` non vuoto; `None`, testo senza frontmatter o campo vuoto → `False`); `APPROVAL_FILE = "skills/rules-base/APPROVED"` solo se B1-V7 lo impone (allora `enforced` riceve il testo di quel file: vero se non vuoto).
  - `HEREDOC_END = "NOTA_DI_RICERCA_FINE"` e `submit_command(program: str, task: int) -> str` (il comando completo con `<<'NOTA_DI_RICERCA_FINE'`, le quattro intestazioni di sezione e il delimitatore finale: lo usano brief e rifiuto).
  - `ATTRIBUTE_UNNAMED: bool` (valore dalla `Ruling:` del Task 1; predefinito `False`).
  - `DOC_MCP_TOOLS: tuple[str, ...]` (decisione 6) e `is_doc_tool(name: str) -> bool`; `doc_library(tool_input: dict) -> str | None` (il `libraryId` della chiamata, con il nome del parametro fissato dal Task 1).
  - `normalize_url(url: str) -> str | None` (decisione 4; `None` per uno schema diverso da `http`/`https` o un URL senza host).
  - `normalize_path(path: str, *, cwd: str, worktree: str) -> str | None` (percorso relativo POSIX al worktree, `None` se fuori; `~` non espanso: un percorso con `~` è `None`).
  - `Note(files: list[str], sources: list[Source], no_external: str | None, findings: str, problems: list[str])` con `Source(ref: str, kind: str, text: str)`, `kind` in `url`, `context7`; `parse_note(text: str) -> Note` (decisione 2; i problemi di forma stanno in `problems`, mai un'eccezione).
  - `check_note(note: Note, lookups: list[tuple[str, str]], *, worktree: str) -> list[str]` (decisione 3; `lookups` sono coppie `(kind, target)` già normalizzate; lista vuota = valida; i file dichiarati si normalizzano con `cwd = worktree`).
  - In `bash.py`: `read_targets(c: Cmd) -> list[str]` (decisione 4: argomenti non opzione di `cat`, `head`, `tail`, `less`, `sed -n`, e dopo il pattern per `grep` e `rg`; nient'altro, `wc` compreso).

- [ ] **Step 1: Test** `test_research.py`:
  - `test_enforced` (`approved: 2026-11-02` vero; `approved:` vuoto, frontmatter assente, `None` falsi; `approved` nel corpo e non nel frontmatter falso);
  - `test_url_forms` (Review Focus 3: `HTTPS://Docs.Python.org:443/3/library/tomllib.html#module-tomllib` e `https://docs.python.org/3/library/tomllib.html/` danno `https://docs.python.org/3/library/tomllib.html`; `https://docs.python.org/3/library/json.html` diverso; `?v=2` mantenuto; `ftp://x` e `file:///etc/passwd` → `None`);
  - `test_normalize_path_forms` (Review Focus 2: con `worktree = "/w"` e `cwd = "/w/src"`, `app.py`, `./app.py`, `/w/src/app.py` → `src/app.py`; `../../etc/passwd` → `None`; `/main/src/app.py` (checkout principale) → `None`; `~/x` → `None`);
  - `test_parse_note_complete` (nota con le tre sezioni, due file, una fonte URL e una `context7:/python/cpython`, findings di due righe: campi giusti, `problems == []`);
  - `test_parse_note_separators` (` — ` e ` - ` entrambi accettati come separatore della descrizione);
  - `test_parse_note_missing_sections` (senza «Letto nel progetto» o senza «Cosa ho trovato» → un problema che nomina la sezione);
  - `test_parse_note_both_sources_and_none` (fonti e «Nessuna fonte esterna» insieme → problema);
  - `test_parse_note_too_long` (oltre 8.000 caratteri → problema «nota oltre 8000 caratteri»);
  - `test_check_note_valid` (letture `read src/app.py` e `fetch <url>` → `[]`);
  - `test_check_note_source_not_read` (fonte dichiarata senza `fetch` → un problema che contiene l'URL normalizzato);
  - `test_check_note_file_not_read` (file dichiarato senza `read`, `grep` né `bash_read` → problema con il percorso);
  - `test_check_note_glob_does_not_count` (una lettura di tipo diverso dai tre di file, per esempio `search`, non basta);
  - `test_check_note_no_external_without_reason` (sezione presente e motivo vuoto → problema; con motivo e un file letto → `[]`);
  - `test_check_note_context7` (`context7:/python/cpython` con `docs /python/cpython` → `[]`; senza → problema);
  - `test_search_alone_not_a_source` (`search tomllib` senza `fetch` dell'URL dichiarato → problema);
  - `test_doc_tools` (i nomi di context7 trovati dal Task 1 → `True`; `mcp__github__create_issue` → `False`);
  - `test_doc_library` (dai campioni `mcp_docs` del Task 1, se presenti); `test_submit_command_quotes_delimiter` (il comando contiene `<<'NOTA_DI_RICERCA_FINE'` tra apici, termina con la riga del delimitatore e non contiene `TOLLGATE_`).
  `test_bash.py::test_read_targets` (`cat a b` → `a`, `b`; `sed -n 1,20p f` → `f`; `sed -i s/x/y/ f` → `[]`; `grep -n foo src/a.py` → `src/a.py`; `rg foo` → `[]`; `head -n 5 f` → `f`; `wc -l f` → `[]`; `echo f` → `[]`).
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** `research.py` e `read_targets`. Le espressioni e i nomi delle sezioni sono costanti del modulo (`SECTION_FILES = "Letto nel progetto"`, `SECTION_DOCS = "Documentazione"`, `SECTION_FOUND = "Cosa ho trovato"`, `SECTION_NONE = "Nessuna fonte esterna"`, `MAX_NOTE_CHARS = 8000`): i testi dei brief e dei rifiuti dei Task 6-8 le importano.
- [ ] **Step 4: `tests/run`** verde.
- [ ] **Step 5: Commit** «tollgate B1: analisi della nota di ricerca».

---

