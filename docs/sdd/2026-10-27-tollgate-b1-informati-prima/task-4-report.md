# Task 4 — Letture registrate dagli hook: report

Commit `bac69cd` «tollgate B1: letture registrate dagli hook». Status: DONE.

## Cosa è stato fatto
- `post_lookup` in `model.INPUT_EVENTS`; `adapter._kind`: `PostToolUse` di Read, Grep, WebFetch, WebSearch, `mcp__*` (non Glob); `PostToolUseFailure` non lo produce.
- **Regola unica** in `bin/tollgate_core/lookups.py` (strato core, importa solo `tollgate_analysis`): `observed()` (Read, Grep solo `output_mode == "content"` esplicito su un file esistente, WebFetch con `code >= 400` escluso, WebSearch `search`, MCP di documentazione `docs` col libraryId), `observed_bash()` (`bash.read_targets`, cartella effettiva via `bash.effective_dir`, solo file esistenti nel worktree), `owner()` (decisione 5 + ripiego `ATTRIBUTE_UNNAMED_TOOLS`, letto a ogni chiamata). Percorsi risolti con `Path.resolve()` (worktree e file) prima di `normalize_path` (D14).
- Proprietario: il subagente ha un `task` e il suo tipo è l'`agent_type` di quel task, che è `running` (un revisore ha tipo diverso e task in `review`); il lavoro del subagente deve coincidere con quello della cartella. Ripiego senza `agent_id` (solo per gli strumenti in `ATTRIBUTE_UNNAMED_TOOLS`): l'unico implementatore `running` non fermo (`subagents.is_stale`), altrimenti None.
- `_common.lookup_owner(ctx, event)`: `lookups.owner` + nessuna lettura per un agente di sola lettura (`ctx.readonly`).
- Modulo `tollgate_checks/lookup_rec.py` (`CHECK` del brief) per `post_lookup` e `post_bash` (non per `PostToolUseFailure`), solo lavori con `research = 1`; operazione `lookup` in `apply` (`OPS` = 29).
- **Via breve** nel runner (`runner._record_lookup`, ramo `event.kind == "post_lookup"` subito dopo la creazione dell'evento): niente `load_config`, `registry.load`, controllo del repo; lavoro dalla cartella dell'evento (`sessions.work_for_path`), `subagents.touch`, `lookups.owner`, `lookups.observed`, `lookups.record`. Scrive direttamente nel DB con `lookups.record` perché non passa dal registro: il divieto di scrivere vale per i moduli, non per il runner. La logica è quella di `lookup_rec` (una funzione, `lookups.observed`). **La via breve non legge `[components]`: registra anche con `research_note` spento.** Per i lavori con `research = 0` non registra. Un errore di registrazione dà uscita 0 con avviso su stderr (`test_error_in_recording_is_informative`).
- `hooks/hooks.json`: matcher di `PostToolUse` + `Read|WebFetch|WebSearch|mcp__.*` (senza `Grep`, come da D5).
- `hooks/run`: uscita anticipata per `PostToolUse` di `Read`, `Grep`, `WebFetch`, `WebSearch`, `mcp__*` senza `agent_id` (dopo `json_str`, prima di OFF e repo attivo). Variabile `UNNAMED_TOOLS=""` che rispecchia `research.ATTRIBUTE_UNNAMED_TOOLS`; un test confronta le due.
- `tests/hookkit.py`: `Lab(research=)`, `SAMPLES_B1`, `sample_b1(name, phase, **changes)`, `Lab.lookup(...)`.
- `spikes/b1/latenza.py`: lavoro con `research=True` e un task `running` per l'implementatore, serie `post_read_subagent`; `tests/test_b1_scripts.py` aggiornato (3 serie, e verifica che la lettura sia davvero in `lookups`).

## Dove sta la funzione comune (strati)
`tollgate_core/lookups.py`: né `tollgate_hooks` né `tollgate_checks` la possiedono, entrambi importano il core (`tests/test_layers.py` verde). `lookups.py` ora importa `tollgate_analysis` (`bash`, `research`) e `subagents`: già ammesso per il core.

## Scostamenti dal piano
- `hooks.json` senza `Grep` e via breve: conseguenza della decisione 15 già decisa dal controller (carry). La misura sotto è sotto soglia (mediana 250 ms < 300 ms), quindi la via breve non era strettamente obbligata dalla misura; è stata costruita come da carry. Se il controller preferisce, `Grep` può rientrare nel matcher (`test_manifest.test_post_tool_use_matcher_has_lookups` lo documenta fuori).
- Il test `test_main_session_read_not_recorded` vale con l'insieme vuoto (assertisce la costante vuota).
- `Lab.lookup` e non `Lab.read`: un solo metodo per i campioni B1.

## Test
RED (HEAD + nuovi test, in una copia sotto `/tmp/tollgate-b1-t4/red`): `tests.test_check_lookups` errore di import (manca `lookup_rec`); `test_wrapper`, `test_hook_engine`, `test_manifest`, `test_check_audit_round`: 20 fallimenti + 1 errore (`test_main_session_read_exits_early`, `test_post_lookup_kinds`, `test_mapping`, `test_post_tool_use_matcher_has_lookups`, `test_ops_count_is_29`, `test_lookup_op`...).
GREEN: `python3 -B -m unittest tests.test_check_lookups tests.test_wrapper tests.test_manifest tests.test_hook_engine tests.test_check_audit_round tests.test_layers tests.test_b1_scripts` verde (44 test nuovi in `test_check_lookups`, più i nuovi di wrapper, manifest, motore, conteggio 29).
Suite: `tests/run` → python3.11: 3024 test OK (2 skipped); python3 (3.13.5): 3024 test OK. Output pulito (la riga «guard: la PR è avanzata…» è l'output già esistente di un test del gate).

Test richiesti dal brief e dal carry presenti: read_recorded_for_task, read_by_other_task_not_counted, readonly_agent_reads_not_recorded, main_session_read_not_recorded, webfetch_recorded_normalized, webfetch_error_code_not_recorded, websearch_is_search_only, grep_on_file_recorded, grep_files_with_matches_not_recorded, grep_on_dir_not_recorded, grep_default_mode_not_recorded, doc_mcp_recorded, bash_cat_recorded, failed_bash_cat_not_recorded, read_outside_worktree_not_recorded, legacy_work_not_recorded, unnamed_fetch_attributed_when_enabled, unnamed_ambiguous_writers_not_attributed, unnamed_readonly_agent_ignored, failed_read_not_recorded, post_lookup_short_path_skips_config, test_post_lookup_kinds, test_lookup_op, ops count 29, matcher, wrapper (`main_session_read_exits_early`, `main_session_websearch_exits_early`, `subagent_read_reaches_python`, confronto con la costante). In più: cd di Bash (D13), bersagli cartella/inesistenti non registrati, collegamento simbolico del worktree nei due versi e verso l'esterno (D14), `unnamed_stale_writer_ignored`, modulo `lookup_rec` con `Grep` su evento diretto.

## Misura di latenza (B1-V6 / D15 al Task 4)
`python3 -B spikes/b1/latenza.py --root /tmp/tollgate-b1-t4/r{1,2} --runs 50` (una invocazione di riscaldamento scartata), macchina quasi scarica (load ~1.2):
| serie | mediana | p95 |
|---|---|---|
| PostToolUse Read da subagente (via breve, scrive in `lookups`), corsa 1 | 249.8 ms | 262.9 ms |
| idem, corsa 2 | 250.7 ms | 272.2 ms |
| PostToolUse Bash `cat` da subagente (percorso completo, `lookup_rec`), corse 1 e 2 | 289.4 ms | 311.4 / 303.6 ms |
| PostToolUse Read senza `agent_id` (uscita anticipata) | 7.6 / 7.8 ms | 8.3 / 8.5 ms |
Sotto la soglia di 300 ms per `Read`. Il Bash da subagente è a 289 ms, vicino alla soglia; non è un evento `post_lookup` e non è coperto dalla soglia della decisione 15, ma costa quanto prima più la scrittura di `lookup_rec` solo se riconosce una lettura.

## Dubbi
- La via breve non rispetta `[components] research_note = false` (da carry, dichiarato). `lookup_rec` sì.
- `Grep` fuori dal matcher: la `Grep` di un implementatore oggi non si registra nel flusso vero (solo in test con eventi diretti), quindi un file letto solo con `Grep content` va riletto con `Read`. Con mediana a 250 ms si potrebbe rimetterlo nel matcher: decisione del controller.
- `bash.read_targets` non conta `cat < f`; i bersagli di Bash contano solo se esistono come file nel worktree al momento del PostToolUse.
