### Task 2: Analisi pura: forma della spec, file di approvazione e di report, recinti del piano

**Files:**
- Create: `bin/tollgate_analysis/specdoc.py`
- Modify: `bin/tollgate_analysis/approvals.py`, `bin/tollgate_analysis/plan.py`
- Test: `tests/test_specdoc.py`, `tests/test_approvals.py`, `tests/test_plan.py`

**Interfaces:**
- Produces in `specdoc.py`: `SLICES_SECTION = "Fette previste"`, `PITCH_SECTIONS = ("Tane di coniglio", "Cosa non fare")`; `slices(text: str) -> int`; `slice_titles(text: str) -> list[str]`; `pitch_problems(text: str) -> list[str]` (testo: «manca la sezione «## Cosa non fare» (spec L2, 6.2)»). Recinti saltati come in `plan.py`.
- Produces in `approvals.py`:
  - `REPORT_KINDS = ("spec-adversarial", "spec-lens", "plan-adversarial")`, `SEVERITIES = ("blocker", "major", "moderate", "minor")`;
  - `parse_header(text: str) -> dict | None` (lettore comune; `counts` in forma `{chiave: intero, …}` diventa un dizionario);
  - `parse_approval(text)` invariata nel contratto, sopra `parse_header`;
  - `parse_report_header(text) -> dict | None` (tipo in `REPORT_KINDS`, `number` intero ≥ 1, `counts` con le quattro chiavi intere ≥ 0);
  - `render_approval(fields: dict) -> str`, `render_report(fields: dict, body: str) -> str` (decisione 18);
  - `approval_listing(paths: list[str]) -> list[str]`: i percorsi `docs/superpowers/reviews/<n>/spec-approval.md` di un elenco;
  - `locate_spec_approval(files: Mapping[str, str], *, issue: int, spec_path: str, spec_blob: str | None) -> tuple[str, dict] | None` (decisione 13; restituisce percorso e intestazione);
  - `check_l2(files: Mapping[str, str], *, issue: int, spec_path: str | None, spec_blob: str | None, plan_path: str | None, plan_blob: str | None) -> list[str]` (decisione 15; `files` contiene **tutti** i file sotto `docs/superpowers/reviews/` dell'albero, con il testo).
- Produces in `plan.py`: `_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")` (decisione 17).

- [ ] **Step 1: Test** `test_specdoc.py`: `test_slices_counts_numbered_items` (tre voci → 3); `test_no_section_is_one`; `test_section_without_items_is_one`; `test_items_inside_fence_ignored`; `test_slice_titles`; `test_pitch_problems` (manca solo «Cosa non fare» → una riga che lo nomina; entrambe presenti → `[]`).
- [ ] **Step 2: Test** `test_approvals.py`:
  - `test_quoted_value_with_comment` (`sha: "abc" # nota` → `"abc"`; triage 30);
  - `test_render_parse_roundtrip_approval` e `test_render_parse_roundtrip_report` (stessi campi, `counts` compreso);
  - `test_report_header_rejects_bad_counts` (chiave mancante, intero negativo, `number` 0 → `None`);
  - `test_locate_own_then_other_issue` (approvazione propria con `path` uguale → la propria; senza, quella dell'issue 3 con `sha` uguale al blob; due candidati 3 e 5 → 3; `sha` diverso → `None`);
  - `test_check_l2_matrix` (tutto presente → `[]`; `plan-approval` con `spec_sha` vecchio → un problema; nessun `spec-adversarial-*.md` con `adversarial: closed` → un problema, con `adversarial: off` nessuno; `slices: 3` e `lens: closed` senza `spec-lens-*.md` → un problema; `lens: suspended` senza report → nessuno; report con intestazione non valida → non conta).
- [ ] **Step 3: Test** `test_plan.py::FenceIndentTest`: `test_fence_with_four_spaces_does_not_open` (un `### Task 9` dopo una riga `    ```` ` è un task vero; con 3 spazi resta dentro il recinto); `test_task_text_same_rule`.
- [ ] **Step 4: Fallimento** (`python3 -B -m unittest tests.test_specdoc tests.test_approvals tests.test_plan`), **implementazione, verifica, `tests/run`**.
- [ ] **Step 5: Commit** «tollgate P3c: forma della spec, intestazioni di approvazioni e report, recinti del piano».

---

