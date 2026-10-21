### Task 3: Analisi pura dell'audit

**Files:**
- Create: `bin/tollgate_analysis/auditrules.py`
- Test: `tests/test_auditrules.py`

**Interfaces:**
- Produces in `auditrules.py` (nessuna dipendenza da tollgate):
  - `VIEWPOINTS` e `VIEWPOINT_LABELS` (decisione 6); `SEVERITIES = ("blocker", "major", "moderate", "minor")`;
  - `outcome(counts: dict) -> str` (`empty` o `findings`, decisione 4); `is_clean(counts: dict) -> bool` (`blocker + major == 0`);
  - `RoundJson(valid: bool, problems: list[str], counts: dict | None)` e `parse_round_json(text: str, *, kind: str, number: int, code: str, spec_sha: str, plan_sha: str | None, viewpoint: str | None) -> RoundJson` (decisione 5; cerca l'ultimo JSON con la chiave `counts` con `report.json_candidates`, che sta in `tollgate_analysis`);
  - `LensState(cycles: dict[str, list[str]], streak: dict[str, int], closed: bool, total: int)` e `lens_state(rows: list[tuple[str, str]]) -> LensState` (righe `(viewpoint, outcome)` dei cicli chiusi non `superseded`, in ordine);
  - `next_viewpoint(state: LensState, last: str | None) -> str` (ad audit aperto il primo con contatore < 2 dopo `last`, in ordine circolare; ad audit chiuso semplicemente il successivo di `last`: serve ai cicli di conferma, decisione 3);
  - `render_lens_status(state: LensState, *, issue: int, cap: int, suspended: bool) -> str` (tabella `Punto di vista | Cicli | Vuoti di fila | Ultimo esito`, più «stato: aperto|chiuso|sospeso», cicli fatti e tetto).

- [ ] **Step 1: Test** `test_auditrules.py`:
  - `test_outcome_and_clean` (`moderate: 1` → `findings` ma pulito; `major: 1` → non pulito; solo `minor` → `empty`);
  - `test_round_json_valid_and_matrix` (codice, numero, tipo, SHA, `viewpoint` sbagliati → non valido con il problema; `counts` con stringa o negativo → non valido; JSON assente → «manca la riga JSON del giro (18.3)»; `outcome` dichiarato ignorato; `plan_sha` richiesto solo per `plan-adversarial`; ultimo JSON vince);
  - `test_major_resets_viewpoint_counter` (criterio 24: `executor` vuoto, vuoto, poi `major` → contatore 0);
  - `test_closed_needs_two_empty_each` (16 cicli vuoti, due per punto di vista → chiuso; 15 → aperto);
  - `test_next_viewpoint_rotates_and_repeats_findings` (primo `executor`; dopo `executor` con rilievi e gli altri a 2, torna `executor`; ad audit chiuso dopo `integrator` dà `executor`);
  - `test_render_lens_status_has_all_viewpoints`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: regole pure dell'audit (esiti, punti di vista, riga JSON del giro)».

---

