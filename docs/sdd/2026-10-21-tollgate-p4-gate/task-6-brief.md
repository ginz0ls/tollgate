### Task 6: Commento del gate e tetto del corpo della PR

**Files:**
- Create: `bin/tollgate_gate/comment.py`, `tests/test_gate_comment.py`
- Modify: `bin/tollgate_analysis/prbody.py`, `tests/test_prbody.py`

**Interfaces:**
- Produces in `comment.py`: `MARKER_PREFIX = "<!-- tollgate-verdict"` (uguale a `fixtask.GATE_MARKER`, controllato da un test), `GUARD_PREFIX = "<!-- tollgate-guard"`, `MAX_BODY = 60000`; `marker(sha: str) -> str`; `marker_sha(body: str) -> str | None` (40 esadecimali, altrimenti `None`); `render(sha: str, ev: Evaluation, *, plan_diff: str = "", approval_diff: str = "") -> str`; `render_guard(sha: str, problems: list[str]) -> str`.
- Produces in `prbody.py`: `MAX_BODY = 60000`; `render(...)` invariata nella firma, con il tetto totale (le sezioni si accorciano voce per voce, il blocco JSON resta intero e ultimo).

- [ ] **Step 1: Test** `test_gate_comment.py`: `test_marker_first_line_with_sha`; `test_marker_sha_rejects_bad` (SHA corto, maiuscole non esadecimali, assente); `test_groups_order` (le voci «da leggere» prima, le informative in `<details>`); `test_neutralized` (criterio 27: una deroga con ```` ``` ```` e `@utente` nel testo → recinto più lungo, nessuna menzione attiva, nessun `-->`); `test_cap` (1.000 voci lunghe → `len(body) <= MAX_BODY` e «troncato»); `test_marker_matches_fixtask`.
- [ ] **Step 2: Test** `test_prbody.py::test_total_cap_keeps_block` (riga 47: 200 rilievi da 2.000 caratteri → corpo entro `MAX_BODY`, `prblock.parse` restituisce il blocco intero).
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P4: commento del gate con lo SHA nel marcatore; tetto del corpo della PR».

---

