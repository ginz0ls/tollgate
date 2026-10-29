### Task 4: Registrazione delle letture dagli hook

**Files:**
- Modify: `bin/tollgate_hooks/model.py` (`INPUT_EVENTS`), `bin/tollgate_hooks/adapter.py` (`_kind`), `bin/tollgate_hooks/apply.py` (operazione `lookup`), `bin/tollgate_checks/_common.py` (`lookup_owner`), `hooks/hooks.json`, `hooks/run`
- Create: `bin/tollgate_checks/lookup_rec.py`, `tests/test_check_lookups.py`
- Test: `tests/test_hook_engine.py` (adattatore e operazioni), `tests/test_check_audit_round.py` (il conteggio di `apply.OPS`, oggi 28), `tests/test_wrapper.py` (`hooks/run`), `tests/test_manifest.py` (`hooks.json`)

**Interfaces:**
- Consumes: `lookups.record` (Task 2); `research.normalize_path`, `normalize_url`, `is_doc_tool`, `doc_library`, `ATTRIBUTE_UNNAMED`, `bash.read_targets` (Task 3).
- Produces:
  - evento d'ingresso `post_lookup`: `adapter._kind("PostToolUse", t)` lo restituisce per `Read`, `Grep`, `WebFetch`, `WebSearch` e per ogni `mcp__…` (non per `Glob`) (il modulo decide se è di documentazione); `PostToolUseFailure` non lo produce (una lettura fallita non conta);
  - operazione `record("lookup", work=, task=, agent_id=, kind=, target=)` (`apply.OPS` passa a 29);
  - `_common.lookup_owner(ctx, event) -> tuple[int, int] | None` (decisione 5: `(work, task)` dal subagente implementatore con un task; con `ATTRIBUTE_UNNAMED` e senza `agent_id`, solo per `WebFetch`, `WebSearch` e MCP, il task dell'implementatore `running` del lavoro che governa il `cwd`; altrimenti `None`);
  - modulo `tollgate_checks.lookup_rec`, `CHECK = {"api": 1, "events": ["post_lookup", "post_bash"], "component": "research_note", "order": 40}`: per `post_lookup` registra secondo la decisione 4 (`Grep` solo in modo `content` con `path` che è un file, più i file mostrati se il Task 1 li ha trovati; `WebFetch` con l'URL e l'eventuale URL finale letto da `event.raw`; `WebSearch` con la query come `target` e `kind` `search`; MCP di documentazione con `docs` e il `libraryId`); per `post_bash` registra i `read_targets` di ogni comando come `bash_read`, ma non se `event.hook_event == "PostToolUseFailure"`; solo per i lavori con `research = 1`.
  - `hooks.json`: matcher di `PostToolUse` `Edit|Write|MultiEdit|NotebookEdit|Bash|Agent|Skill|SubagentHandback|Read|Grep|WebFetch|WebSearch|mcp__.*` (senza `Grep` se scatta la soglia della decisione 15).
  - `hooks/run`: per `PostToolUse` con `tool_name` in `Read`, `Grep` e senza `agent_id` esce con 0 prima del controllo del repo attivo (decisione 15; solo se il Task 1 lo permette).
  - con la soglia della decisione 15 superata: la via breve di `post_lookup` nel runner (nessun `load_config` né `registry.load`), con il test `test_post_lookup_short_path_skips_config`.

- [ ] **Step 1: Test** `test_check_lookups.py` (con `tests/hookkit.py` e i campioni del Task 1, forma degli input uguale a quella reale):
  - `test_read_recorded_for_task` (implementatore del task 1 legge `src/app.py` → `lookups` ha `read src/app.py` per il task 1);
  - `test_read_by_other_task_not_counted` (Review Focus 1: implementatore del task 2 legge lo stesso file → il task 1 non lo ha);
  - `test_readonly_agent_reads_not_recorded` (un `tollgate:task-reviewer` legge → nessuna riga);
  - `test_main_session_read_not_recorded` (nessun `agent_id` → nessuna riga; con `ATTRIBUTE_UNNAMED` vero resta nessuna riga per `Read`);
  - `test_webfetch_recorded_normalized` (URL con frammento → riga `fetch` normalizzata; con l'URL finale nel `tool_response`, se B1-V4 l'ha trovato, due righe);
  - `test_websearch_is_search_only`;
  - `test_grep_on_file_recorded` (modo `content`); `test_grep_files_with_matches_not_recorded`;
  - `test_doc_mcp_recorded` (se B1-V2 ha dato un campione);
  - `test_bash_cat_recorded` (`post_bash` con `cat src/app.py` dall'implementatore → `bash_read src/app.py`); `test_failed_bash_cat_not_recorded` (lo stesso da `PostToolUseFailure` → nessuna riga);
  - `test_read_outside_worktree_not_recorded` (percorso nel checkout principale → nessuna riga);
  - `test_legacy_work_not_recorded` (`research = 0` → nessuna riga);
  - `test_unnamed_fetch_attributed_when_enabled` (solo con `ATTRIBUTE_UNNAMED`: `WebFetch` senza `agent_id` mentre l'implementatore del task 1 è `running` → riga del task 1; senza implementatore `running` → nessuna);
  - `test_failed_read_not_recorded` (`PostToolUseFailure` di `Read` → nessun evento d'ingresso).
  `test_hook_engine.py::test_post_lookup_kinds` (con `Glob` → nessun evento), `test_hook_engine.py::test_lookup_op`; il conteggio in `test_check_audit_round.py` passa a 29; `test_manifest.py::test_post_tool_use_matcher_has_lookups`; `test_wrapper.py::test_main_session_read_exits_early` (con uno stato che fallirebbe se Python partisse: nessuna riga in `hooks.log`, uscita 0) e `test_subagent_read_reaches_python`.
- [ ] **Step 2: Esegui i test** e controlla che falliscano.
- [ ] **Step 3: Implementa** evento, adattatore, modulo, operazione, matcher e uscita anticipata. Nel wrapper l'uscita anticipata legge `tool_name` e `agent_id` con `json_str`, come il ramo di `UserPromptSubmit`.
- [ ] **Step 4: `tests/run`** verde, e la misura della decisione 15 ripetuta con un `PostToolUse` di `Read` vero da subagente (50 invocazioni, mediana e 95° percentile nel report del task); con una mediana oltre 300 ms si applica la stessa conseguenza della decisione 15 (via breve, `Grep` fuori dal matcher), con una `Ruling:` e un giro di questo task.
- [ ] **Step 5: Commit** «tollgate B1: letture registrate dagli hook».

---

