### Task 11: Statusline e file del contesto

**Files:**
- Create: `statusline/ctx` (eseguibile, bash)
- Test: `tests/test_statusline.py`

**Interfaces:**
- Produces: `statusline/ctx [comando…]` (decisione 21):
  - legge tutto stdin;
  - ricava `session_id` e `context_window.used_percentage` con `python3 -c`, perché `jq` può mancare. Se non c'è Python cerca solo le due chiavi con `sed`, senza mai fallire;
  - scrive in modo atomico `<stato>/ctx/<session_id>.json` = `{"used_pct": <numero o null>}`. `<stato>` è `$TOLLGATE_STATE` solo se contiene `.tollgate-test`, altrimenti `~/.local/state/tollgate`;
  - esegue il comando passato con lo stesso stdin e ne restituisce l'uscita; senza comando non stampa nulla;
  - un `session_id` che non rispetta `^[A-Za-z0-9_-]+$` non scrive nulla.

- [ ] **Step 1: Test** (`test_statusline.py`):
  - `test_writes_used_pct` (input con `session_id: "s1"` e `used_percentage: 42` → `{"used_pct": 42}`);
  - `test_null_when_missing`;
  - `test_passes_stdin_to_wrapped_command` (comando `cat` → stdout uguale all'input);
  - `test_unsafe_session_ignored`;
  - `test_state_without_sentinel_not_used` (HOME temporanea);
  - `test_context_guard_reads_it` (con `hookkit.Lab`: dopo `ctx` con 60%, `PreToolUse Agent` → 2 con «contesto»; criterio 8).
- [ ] **Steps 2-4**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: statusline/ctx scrive il file del contesto».

---

