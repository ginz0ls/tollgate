# Pre-flight scan del piano P2 (guardrail)

Piano: `docs/superpowers/plans/2026-10-09-tollgate-p2-guardrail.md` (8851 righe, 20 task). Autorità: spec rev 21 (nel frattempo il Task 1 è stato eseguito e committato: `3da986d`, `fb338d9`, quindi la spec letta è già la 21, non la 20) e piano principale, sezione 3.

## Metodo e limiti

- Ho letto il piano per intero e ho estratto in una copia di lavoro (fuori dal repo, nel scratchpad) tutti i blocchi di codice e di test, applicati alla lettera sopra il codice reale di P1 (`bin/tollgate_core/`, `tests/`), con i campioni aggiornati di `samples.json`. Ho poi eseguito l'intera suite su Python 3.13 e 3.11 (354 test, anche con `-W error::ResourceWarning`).
- Esito: con il codice del piano **applicato verbatim** falliscono 4 test (3 di P1 per il conflitto 1, 1 nuovo per il conflitto 4). Con tre correzioni minime (conflitti 1 e 4) la suite è verde su entrambe le versioni. Quindi i test del piano, nel complesso, non falliscono per errori di codice: i problemi veri sono di altro tipo (conflitti con la spec, buchi di copertura, comportamenti non provati dai test).
- Ho scritto sonde di prova (fuori dal repo) per i punti 3, 7, 8, 9 della lista conflitti: i risultati citati sono eseguiti, non dedotti, salvo dove è scritto «per lettura del codice».
- Non verificabile da qui: il comportamento reale di Claude Code (ancoraggio dei matcher di `hooks.json`, effetto reale di `additionalContext`), `claude plugin validate`, forma degli identificativi Go, installazione del plugin.

---

## 1. Tabella per coppie di task

Colonne: Task A | Task B | cosa produce A / cosa consuma B | esito. Le righe sono raggruppate; dove una riga copre più simboli, tutti sono stati incrociati col codice effettivamente eseguito.

| Task A | Task B | Cosa produce A / cosa consuma B | Esito |
|---|---|---|---|
| 1 | 8 | `samples.json`: `PostToolUse-Agent-maxturns-cut`, `PostToolUse-Agent-foreground-manual` (già da P0) / `test_report.test_turn_cut_from_real_sample` (righe 3441-3448) | ok |
| 1 | 12 | Chiavi nuove `PreToolUse-Write`, `PostToolUse-Write`, `PreToolUse-Edit`, `PostToolUse-Edit`, `PostToolUse-Skill`, `PreToolUse-Write-subagent` (presenti, verificate) / `hookkit.sample` (4830-4847), che ora non usa più il ripiego | ok |
| 1 | 12 | Esito D2 / `adapter.INJECT_MODE` (5267-5269) | conflitto minore: `SubagentStop: "stderr"` non è visibile al modello con uscita 0 (conflitto 6) |
| 1 | 13 | Esito D1 («no», nessun `version`) / `plugin.json` (6245-6256) | conflitto minore: il blocco di codice contiene ancora `version` (conflitto 5) |
| 1 | 12, 13, 18 | Esito E7/E8 e spec rev 21 (3.2 riga 232, 6.3 riga 411): evento d'ingresso `prompt_submit` / niente nel piano | conflitto che blocca (conflitto 2) |
| 2 | P1 | `db.MIGRATIONS` con migrazione 2 / `db._migrate` (`bin/tollgate_core/db.py:147-166`) e test P1 sui backup | conflitto che blocca (conflitto 1) |
| 2 | 3 | `db.latest_version()`, `tasks.add_task`, colonne `tasks.skills_required` / `scope.register_plan`, test | ok |
| 2 | 12 | `sessions.touch/alive/bound_work/work_for_path/mark_bound`, `subagents.start/touch/get/set_name/set_report/add_veto/finish/interrupt/by_name/running`, `tasks.take_pending` / `context.py`, `apply.py`, `runner.py` | ok, firme identiche |
| 2 | 18, 19 | `subagents.is_stale` (riga 699) / `agents.live_writers` (8158) | ok per il codice; `is_stale` manca dall'elenco **Produces** del Task 2 (riga 284): solo documentale |
| 2 | 18 | `tasks.assign(..., pending=)` , `tasks.PENDING` / test (8003, 8051, 8083) | ok |
| 3 | 10 | `receipts.add(..., exit_code=...)` / `verify.run_verify` (4473-4489) | ok |
| 3 | 12 | `scope.paths/register_plan/set_plan_path`, `effects.*`, `offlog.import_log` / `context.scope`, `apply._OPS`, `runner` (5744) | ok |
| 3 | 16 | `effects.effect_key/effect_id/get/request/mark_executed/executed_at` / `tollgate_checks/effects.py` (7497-7578) | ok |
| 3 | 19 | `receipts.latest(conn, work, sha)`, `any_since` / `subagent_stop` (8694-8705) | ok |
| 3 | 10 | Regola «`uncounted` verde con `allow_no_tests` e uscita 0»: scritta due volte, `dod._receipt.ok` (1237-1242) e `verify.counts_green` (4399-4401) | ok, ma duplicazione di una regola di business (nessuna Single Source of Truth) |
| 3 | 13 | `offlog._LINE` (1197) / righe scritte dal wrapper (6130-6136, 6146) | ok: `…T..:..:..000000Z off [epoch]` e `… on` combaciano |
| 4 | 5, 6, 8 | `globs.match/match_any` / `level.sensitive_in`, `testguard.check`, `waivers.covers` | ok; `test_analysis_isolation` (1500-1528) conferma che `tollgate_analysis` non importa il resto |
| 4 | 10, 12, 15 | `profiles.active_profiles/task_skills/min_level`, `plan.check_plan(kwargs)` / `verify.gate_commands`, `context.guard_config`, `post_edit._plan`, `_common.level_records` | ok |
| 4 | P1 | `config.load_config_text` + avviso `profili attivi` / `tests/test_config.py` | conflitto minore (conflitto 4: il test usa un nome non importato) |
| 5 | 9, 15 | `level.FileChange` e attributi / `git.Change` (3862-3869), `level_records` | ok (duck typing: `path, added, removed, binary, old_path`) |
| 5 | 10, 19 | `junit.parse_junit`, `Junit` / `verify._run_one`, `report` | ok |
| 6 | 8 | `testguard.Violation` / `waivers.covers` (usa `waiver_type`, `kind`, `ids`) | ok |
| 6 | 12, 17 | `GuardConfig(...)`, `Change`, `check` / `context.guard_config` (5423-5436), `_common.commit_violations` (7789-7813) | ok |
| 6 | 15 | `Violation("out_of_scope", ...)` aggiunto dal Task 15 (riga 2129) / `writes.py` 7064 | ok |
| 7 | 16 | `bash.parse/…/effect_reason/script_path/text_danger` / `bash_rules.py`, `effects.py` | ok per i nomi; lacune di riconoscimento (conflitto 7) |
| 8 | 11, 12, 15 | `waivers.parse/dumps/next_id/path_for/unresolved/Waiver/WaiverFile` / `waiver_cli`, `context.waiver_file`, `writes` | ok |
| 8 | 18, 19 | `report.is_turn_cut/parse_report/transcript_tokens` / `post_agent`, `subagent_stop` | ok |
| 9 | 10-19 | `git.toplevel/head/branch/changes/commit_changes/diff_size/rev_list/fingerprint/is_clean/…` | ok per firme; `git.toplevel` ritorna `None` per percorsi sotto `.git/` (conflitto 3) |
| 10 | 11, 12 | Modifiche successive a `cli.py` (verify, waiver/block, hook): le ancore indicate (`dopo events`, `prima di conn = db.open_db`, `dopo if args.cmd is None:`) esistono e combaciano | ok |
| 10 | 12 | `tests/helpers.make_origin_repo` / `hookkit.Lab` (4855), `test_wrapper` (5927) | ok |
| 10 | 19 | `verify.counts_green` / `subagent_stop` (8695) | ok |
| 12 | 13 | `bin/tollgate hook <evento>` / wrapper | ok |
| 12 | 14-19 | `Event`, `Decision`, `record(op, **data)`, `Ctx`, `hookkit.Lab/sample/DROP`; operazioni `record` usate dai moduli: `subagent_name, subagent_report, subagent_finish, task, block, subagent_veto, skill_used, commit, task_commit, effect_request, effect_execute, subagent_interrupt, subagent_start, phase, level, expire_acts, bind, act, plan, plan_path` | ok: tutte presenti in `apply.OPS`, campi dei dati combaciano |
| 12 | 13 | `runner._off_active` (formato `until=<epoch>`) / wrapper (6126) | ok |
| 13 | 12 | `bound/<sessione>` scritto da `sessions.mark_bound` / letto dal wrapper (6167) e dal runner (5740) | ok, con il caso di sessione vuota (conflitto 10) |
| 14 | 15 | `_common.locked_docs/is_docs_md/orphan_tg/governing_work/explain` / `writes.py` | ok |
| 15 | 17 | `_common.scope_exempt/level_records` / `commit.py`, `post_bash.py`, `_common.commit_violations` | ok; il Task 17 aggiunge import a metà file di `_common.py` (stile) |
| 16 | 17 | `bash_rules` (ordine 20), `commit` (25), `effects` (30): tutti su `pre_bash` | ok: il primo `deny` vince, i `record` si scrivono comunque |
| 18 | 19 | `agents.live_writers`, `subagents.finish(state="cut"/"budget"/"tampered")` / `subagent_stop` | ok, `STATES` lo permette |
| 18 | 14 | `SubagentStart`: `take_pending` / `tasks.assign` nei test | ok |
| 20 | 13 | `hooks/run` e `bin/tollgate` veri / `tests/test_criteria_p2.py` | ok |
| 20 | spec/piano principale | Elenco decisioni da riportare in rev 21: titolo Files (riga 8746) dice 1, 6, 7, 13, 15, 22; Step 3 (8826-8831) cita anche 4, 5, 9, 10, 11; l'intestazione «Decisioni» (riga 31) dice 1, 2, 6, 7 | ok funzionalmente, tre elenchi incoerenti (conflitto 12) |
| Tutti | P1 (funzioni usate) | Verificate nel codice reale con la firma usata: `phases.create_work/bind_session/set_phase/set_level/open_block/get_work/SEQUENCES/_FORWARD_CONDITION/BLOCK_TYPES/TransitionError`, `acts.record_act/find_usable/consume/expire_stale/invalidate_finish/ACT_TYPES/APPROVE_OBJECTS/ActError`, `tasks.add_task/task_event/add_skill_used/get_task/TaskTransitionError`, `events.record_event`, `db.open_db/tx/backup/DbError/DbCorrupt/BIN_PATH/restore_hint/latest_version`, `config.load_config/load_config_text/ConfigError/ConfigNotFound/Config.get/.profiles`, `paths.resolve_state/State/repo_key/ensure_dirs`, `clock.fmt/parse/now`, `dod.compute_dod` | ok |
| Colonne migrazione 2 | usi | `session_seen`, `subagents.last_seen/vetoes/report`, `tasks.pending`, `work_items.level_cap_paths`, indice `subagents_work` | ok: tutte usate come definite (`level_cap_paths` solo letta da `_common.level_records`, 6968; la scrive P3) |

---

## 2. Tabella per task

| Task | Coerenza interna (test previsti vs codice previsto; file creati vs toccati dopo) | Esito |
|---|---|---|
| 1 | Già eseguito e committato (`3da986d`, `fb338d9`). Il rapporto `docs/verifiche/2026-10-09-p2-verifiche.md` contiene due «conseguenze per il piano» che il piano non ha assorbito: `prompt_submit` e dipendenza senza `version`. | ok per sé; origina i conflitti 2, 5, 6 |
| 2 | Test e codice coerenti (`MigrationV2Test`, sessioni, subagenti, `tasks.assign`). Ma la migrazione 2, aggiunta in fondo a `MIGRATIONS`, fa fare a `_migrate` un backup `migrazione-2` anche su un DB appena creato (il ciclo passa per la 1 e poi `current>0`): rompe `tests/test_db.py:59-62` (`test_fresh_db_makes_no_backup…`), `tests/test_db.py:71-85` (`test_migration_makes_backup_first` aggiunge una seconda migrazione numero 2, ora duplicata, quindi niente tabella `extra` né backup) e `tests/test_phases.py:96-100` (conta 2 backup invece di 1). Il piano ritocca solo le righe 39 e 56 di `test_db.py` (riga 289). Il passo 10 (`tests/run` verde, 768-771) non può riuscire. | conflitto 1 (blocca) |
| 3 | `scope`, `receipts`, `effects`, `offlog`, `dod._receipt`: test e codice coerenti, nessun test vuoto. Il Modify di `dod.py` combacia con la funzione esistente; l'import di `receipts` in `test_dod.py` va aggiunto (il piano lo dice). | ok |
| 4 | `globs/protected/profiles/plan`: tutti i test passano; i casi di `globs` sono corretti sul dialetto gitignore. Il test aggiunto a `tests/test_config.py` (1532-1538) usa `config.load_config_text`, ma il file importa solo `load_config_text` (righe 6-8): `NameError`. Il passo 8 (`tests/run`) non riesce finché non si corregge. | conflitto 4 (minore) |
| 5 | `level`, `junit`: coerenti, test significativi (soglie, binario, tetto, entità XML). | ok |
| 6 | `scan/testids/testguard`: coerenti. `test_binary_and_latin1_do_not_crash` (2289-2293) non prova il latin-1: passa stringhe già decodificate, mentre la decodifica con `replace` sta in `git._text` (4057-4060), mai coperta. Le aggiunte di fixture nuove sono trattate come «aggiornate» (`fixture_changed` anche per `status="A"`, 2643-2645): non è in contrasto con la spec («aggiornati»), ma costringe a una deroga per ogni fixture nuova. | ok con test debole (conflitto 11) |
| 7 | `bash.py`: coerente coi test; nessun crash su 90 comandi di prova (fuzz delle funzioni di classificazione). Lacune di riconoscimento sul comportamento reale (vedi conflitto 7). | ok con lacune (conflitto 7) |
| 8 | `waivers`, `report`: coerenti con 18.2 e 18.5 (campi obbligatori del report corrispondono a 6.3: `must_have` e `size_reason` non obbligatori, `size_reason` imposto oltre `task_lines_max` nel Task 19). | ok |
| 9 | `git.py`: test su repo con spazi, rinomine, non tracciati, worktree, impronta. `toplevel` ritorna `None` per percorsi dentro `.git/` (la cartella non è un work tree): è la causa del conflitto 3. `_parse_z` e `commit_changes` su commit radice funzionano. | ok per i test; origina il conflitto 3 |
| 10 | `verify`: test coerenti. Il passo 6 (4521) attribuisce la prova «config dalla base» a `test_missing_command_is_unverified`; la prova vera è `test_config_read_from_work_base` (4296-4303). Con un lavoro senza `work_base_sha` (permesso da `create_work`) `base` vale `None` e `git.changes(root, None, …)` solleva `TypeError` (riga 4454): caso limite, P3 imposta sempre la base. | ok (conflitto 11 per la nota, 13 per il limite) |
| 11 | `waiver_cli`: test coerenti; nessuna normalizzazione del percorso in `--file` né obbligo di `--test` per `type=test` (4655-4685): una deroga con percorso non relativo alla radice o senza identificativi non copre mai nulla, in silenzio. | ok con lacuna (conflitto 13) |
| 12 | Motore: 14 test passano. `test_malformed_input_missing_fields` (5081-5086) accetta `(0, 2)` per un caso deterministico (il primo dà sempre 2 per il modulo finto con `api` 2): asserisce quasi nulla. Il rilievo P1 «corruzione dopo l'apertura» (riga 71) è dichiarato coperto, ma `test_corrupt_db` (5112-5126) corrompe prima di aprire, quindi passa da `DbCorrupt` e non dal ramo `sqlite3.DatabaseError` (5821-5825), mai provato. `INJECT_MODE["SubagentStop"]="stderr"` (5269) è invisibile al modello. `INPUT_EVENTS` (5203-5205) e `_PLAIN` (5263) non hanno `prompt_submit`. Sessione vuota: `marker = bound/""` coincide con la cartella `bound` (5740). | conflitti 2, 6, 10, 11 |
| 13 | Wrapper e manifest: 13 test passano. `plugin.json` ha `version` nella dipendenza (6253) contro D1; `test_manifest` non lo controlla. `test_manifest.test_hooks_json` fissa per uguaglianza l'insieme degli eventi (6044-6045) senza `UserPromptSubmit`. `json_str` (6112-6115) prende l'ultima occorrenza e ignora l'annidamento. Ore di `/tollgate:off` ricavate da cifre (6122): `08` fa abortire lo script per aritmetica ottale, `0.5` diventa 5 ore. `license`/`author` (6249-6251) senza decisione né file `LICENSE` nel repo: non verificabile. | conflitti 2, 5, 10 |
| 14 | `session`, `acts`: 12 test passano; oggetto e target degli atti combaciano con la decisione 15 e con 8.4. Nessun test vuoto. | ok |
| 15 | `writes`, `post_edit`, `_common`: 18 test passano. Nessun test tocca `.git/hooks` o `.git/config` e il percorso sotto `.git` bypassa sia la protezione sia la regola del checkout principale (probe: Write su `<main>/.git/hooks/pre-commit` e `.git/config` → uscita 0 sia da sessione legata sia non legata). `level_records` conta i file non ignorati in `output_dirs`. | conflitti 3, 9 |
| 16 | `bash_rules`, `effects`: 15 test passano. Stesso buco `.git` nel ramo `is_protected(…, ctx.protected_roots(r))` con `r = git.toplevel(p)` (7398-7400): `echo x > .git/hooks/pre-commit` → 0. Lacune di riconoscimento (conflitto 7). `script_path` mette in veto anche `./node_modules/.bin/…` e qualunque binario non tracciato (7538-7552), coerente con 8.5 alla lettera ma di forte attrito. | conflitti 3, 7, 14 |
| 17 | `commit`, `post_bash`: 13 test passano. `post_bash` torna presto se non ci sono commit nuovi (7898-7899): un `git reset --soft` avanti e indietro tra due SHA, senza commit nuovi, lascia un `finish` di nuovo utilizzabile (probe: `pending` e `find_usable` vero dopo il ritorno a SHA A), contro il vincolo 3 del piano principale. Commit con file di `output_dirs` non ignorati: scope e livello li contano. | conflitti 8, 9 |
| 18 | `agents`, `send_message`, `subagent_start`, `post_agent`, `skills`, `handback`: 10 test passano. Il taglio di `maxTurns` è riconosciuto solo da `PostToolUse Agent` (primo piano): niente per il taglio dopo una ripresa con `SendMessage` (giri di correzione 1-3), che la spec rev 21 affida a `prompt_submit`; la riga dell'implementatore resta `running` e blocca lo scrittore unico per `stale_minutes`. `SubagentStart` inietta il promemoria dell'implementatore a ogni subagente non di sola lettura, in qualunque fase (8296-8303). | conflitti 2, 12 |
| 19 | `subagent_stop`: 9 test passano. Report, ricevuta e dimensione sono imposti a **ogni** subagente non di sola lettura, anche senza task (8663-8680): in fase `plan` o in L0 un `general-purpose` riceve fino a 2 veti e poi un `needs_you` (conforme al glossario «implementatore», ma con rischio di falsi blocchi). La ricevuta usa `all(counts_green)` su tutte le ricevute dello SHA (8695): un `verify` rosso e un `related` verde sullo stesso SHA danno veto, coerente con la decisione 24. | conflitto 12 |
| 20 | Test end-to-end dal wrapper vero: 4 test passano. Nessun test asserisce nulla di vuoto. Bookkeeping delle decisioni incoerente (vedi tabella coppie). Il passo 2 elenca la copertura per criterio ma non include `prompt_submit`. | ok (conflitti 2 e 12 per le omissioni) |

---

## 3. Elenco dei conflitti

Conteggio: **3 che bloccano, 13 minori** (16 in totale).

### Bloccano

**1. La migrazione 2 rompe tre test di P1 e crea un backup su un DB nuovo.** Task 2.
- Righe del piano: 326-346 (Step 3), 289 (si modificano solo le righe 39 e 56 di `tests/test_db.py`), 768-771 (Step 10).
- Codice P1: `bin/tollgate_core/db.py:147-166` (`_migrate`: `if current > 0: backup(...)` dentro il ciclo, quindi anche dopo aver creato lo schema 1 nella stessa apertura); `tests/test_db.py:59-62`, `71-85`; `tests/test_phases.py:96-100`.
- Spec: 12.1 e riga 1098 («Migrazioni. Solo in avanti, con una copia prima di ciascuna»): la copia serve a proteggere dati esistenti, e P1 ha fissato con un test che un DB nuovo non ne fa. Eseguito: 3 fallimenti (`test_fresh_db_makes_no_backup_and_reopen_is_idempotent`, `test_migration_makes_backup_first`, `test_set_phase_records_and_backs_up`).
- Gravità: blocca (Step 10 del Task 2 non può essere verde).
- Proposta: aggiungere al Task 2 la modifica di `_migrate` (`fresh = current == 0` letto prima del ciclo, backup solo se `not fresh`) e la modifica di `test_migration_makes_backup_first` (usare `db.latest_version() + 1` come numero della migrazione finta e cercare `*migrazione-3*.db`). Aggiungere `bin/tollgate_core/db.py` (`_migrate`) e `tests/test_db.py:71-85` all'elenco **Files** del Task 2.

**2. Manca l'evento d'ingresso `prompt_submit` richiesto dalla spec rev 21.** Task 12, 13, 18 (e 20).
- Righe del piano: 33 (decisione 1: elenco degli hook informativi), 5203-5206 (`INPUT_EVENTS`), 5263-5264 (`_PLAIN`), 6044-6045 e 6230-6240 (`hooks.json` e `test_manifest`, che fissa l'insieme esatto dei sei eventi), 7953 e 8309-8352 (`post_agent`, solo primo piano), 5486 (`registry._validate` rifiuta eventi fuori da `INPUT_EVENTS`).
- Spec: riga 4 (rev 21 elenca `prompt_submit`), riga 232 (elenco chiuso 3.2, con `prompt_submit` (`UserPromptSubmit`)), riga 411 (6.3: un controllo porta il task con quell'`agent_id` in `blocked` con `needs_you` e chiude la riga in `subagents`; `stale_minutes` resta la rete), riga 1333 (§16, esiti E7/E8); rapporto `docs/verifiche/2026-10-09-p2-verifiche.md`, «Conseguenze per il piano P2».
- Effetto: senza di esso, il taglio di `maxTurns` durante un giro di correzione ripreso con `SendMessage` (E8: nessun `SubagentStop`, nessun `PostToolUse` con il taglio, `maxTurns` riparte da zero a ogni ripresa) non è riconosciuto; la riga resta `running` e il PreToolUse Agent nega i nuovi lanci per 30 minuti.
- Gravità: blocca (la spec è l'autorità e il piano non la implementa).
- Proposta: (a) `INPUT_EVENTS` + `_PLAIN["UserPromptSubmit"]="prompt_submit"`, `prompt_submit` informativo (mai `deny`, mai uscita 2: un `UserPromptSubmit` con 2 bloccherebbe il prompt dell'utente); (b) voce `UserPromptSubmit` in `hooks.json` senza matcher e in `test_manifest`; (c) nuovo modulo `tollgate_checks/prompt_submit.py` (ordine 20), che esce subito se il prompt non contiene `<task-notification>`, altrimenti riconosce `stopped at its N-turn limit`, legge `<task-id>` come `agent_id`, e registra `subagent_finish(cut)`, `task budget_exceeded`, `block needs_you` (componente `task_budget`); (d) test con il campione `UserPromptSubmit-none` e `prompt` sostituito con il testo di E7/E8 riportato nel rapporto (non esiste un campione reale della notifica); (e) `INJECT_MODE["UserPromptSubmit"]="context"`.

**3. Percorsi sotto `.git/` sfuggono alla protezione dei file e alla regola del checkout principale.** Task 15, 16 (con la causa in Task 9 e 12).
- Righe del piano: 7019-7021 (`writes.py`: `repo = git.toplevel(p)` e `ctx.protected_roots(repo)`), 7035-7040 (regola checkout principale con `repo is not None`), 7398-7400 (`bash_rules`: `r = git.toplevel(p)`), 5438-5448 (`protected_roots`: i percorsi di `hooks` e `config` si aggiungono solo con `repo` non nullo), 3895-3907 (`git.toplevel`: `rev-parse --show-toplevel` fallisce dentro `.git` e ritorna `None`).
- Spec: riga 32 (file protetti: `.git/hooks/**`, `.git/config`), 7.4 riga 536 (scrittura sui file protetti, `deny`), 6.6 riga 469 (file protetti in Edit e Write), riga 470 (scritture nel checkout principale negate).
- Eseguito (Lab): Write su `<main>/.git/hooks/pre-commit` e `<main>/.git/config` → uscita 0 da sessione legata e da sessione non legata; `echo x > .git/hooks/pre-commit`, `echo x >> .git/config`, `touch .git/hooks/pre-push` dal checkout principale → 0. Un hook in `.git/hooks` è esecuzione di codice arbitrario fuori da tollgate; `core.hooksPath` via `git config` passa comunque (best effort, 7.4).
- Gravità: blocca (riga esplicita della spec, buco reale, un test unitario di `is_protected` con `abs_roots` lo nasconde).
- Proposta: calcolare i `abs_roots` dal repo del contesto (toplevel del `cwd` dell'evento o del worktree del lavoro), non dal `toplevel` del bersaglio; in `git.toplevel` ripiegare su `rev-parse --git-common-dir` quando il percorso è dentro un `.git`; aggiungere in Task 15 e 16 i test: Write/Edit su `.git/hooks/x` e `.git/config`, redirect e `touch` su `.git/hooks`, sia legati sia non legati. Per `git config core.hooksPath` valutare un divieto esplicito (richiede decisione dell'utente).

### Minori

**4. Test di `config` con nome non importato.** Task 4.
- Righe: 1532-1538 (`config.load_config_text`); `tests/test_config.py:6-8` importa solo `load_config_text`. `NameError` al passo 8 (`tests/run`), eseguito.
- Spec: nessuna. Gravità: minore. Proposta: usare `load_config_text(...)` nel test.

**5. `plugin.json` dichiara ancora `version` in `dependencies`.** Task 13.
- Righe: 6252-6254 (e 6243, che prevede di toglierla con D1 «no»). Esito D1 nel rapporto: «no», senza `version`; spec 11.1 (rev 21): in `dependencies` va senza `version`; il vincolo minimo 6.4.1 lo controlla `start` (P3). Con `version` l'installazione fallisce («has no git tag satisfying»). `test_plugin_json` (6059-6066) non verifica l'assenza.
- Inoltre `license: "MIT"` e `author` (6249-6251) sono una scelta non documentata (nel repo non c'è `LICENSE`): non verificabile, da confermare con l'utente.
- Gravità: minore. Proposta: togliere `version` dal blocco di codice, aggiungere `assertNotIn("version", dep)`, chiedere licenza e autore.

**6. `INJECT_MODE["SubagentStop"] = "stderr"` non ha effetto.** Task 12.
- Righe: 5269 (e le note accodate dal runner a 5792 e 5807 per gli hook informativi). Rapporto D2: con uscita 0 lo stderr va solo nel log di debug; per `SubagentStop` vale solo l'uscita 2 (il piano la usa già per i veti).
- Gravità: minore. Proposta: per `subagent_stop` e `subagent_handback` non iniettare (la scelta del rapporto) e scrivere gli avvisi in un log, oppure usare `additionalContext`, documentato anche per `SubagentStop`.

**7. Lacune di riconoscimento nei comandi Bash (best effort, 7.4), verificate.** Task 7, 16.
- (a) `git push origin HEAD` e `git push -u origin HEAD` dal checkout principale su `main` → 0 (`push_targets` ritorna `["HEAD"]`, 3018-3026 e 7416-7418): la riga «push verso il ramo predefinito» non si applica; non c'è rete a valle. (b) `bash -lc '…'` non è riconosciuto come `-c` (2952-2957): un `git push` annidato passa in sessione legata (il test, 7188-7191, prova solo `-c`). (c) `git commit -n` (forma breve di `--no-verify`) passa (3076-3082). (d) Le redirezioni numerate (`2>&1`, `2>/dev/null`) lasciano un argomento spurio «2» (2930-2937): `cp a b 2>&1` ha come bersaglio di scrittura «2» invece di `b`, `rm -rf build 2>/dev/null` aggiunge `/r/wt/2`.
- Spec: 7.4 («best effort») e la riga 7.2 `PostToolUse Bash`. Gravità: minore (sessioni legate già negano ogni push; manca solo il ramo predefinito da sessione non legata e i bersagli di scrittura).
- Proposta: risolvere `HEAD` nel ramo corrente (`git.branch(edir)`); riconoscere `-c` anche come flag combinato (`-lc`, `-ic`); aggiungere `-n` per `commit`; scartare in `flush()` i token composti da sole cifre seguiti da redirezione. Aggiungere test.

**8. Un `finish` pendente non decade se HEAD cambia senza commit nuovi.** Task 17.
- Righe: 19 (vincolo globale), 7898-7899 (`post_bash`: `if not new: return out`). Piano principale, sezione 3, vincolo 3: gli hook chiamano `acts.invalidate_finish` ogni volta che vedono un HEAD diverso dallo SHA di un `finish` in attesa. Eseguito: `finish` su A, `reset --soft HEAD~1`, `reset --soft A` → l'atto è ancora `pending` e `find_usable` lo restituisce.
- Gravità: minore (serve un reset non `--hard`, che 7.4 consente). Proposta: in `post_bash` aggiungere una `record` che chiama `invalidate_finish(work, HEAD)` quando HEAD differisce da un `finish` in attesa, con test.

**9. `review.output_dirs` non esclusa da livello, scope e test-guard.** Task 15, 17.
- Righe: 6957 (`level_records`: `git.changes(wt, base)`), 7783-7813 (`commit_violations`), 4009-4031 (`_untracked`). Spec 8.1/7.3 trattano `output_dirs` come non rilevante per la pulizia e l'impronta. Eseguito (repo senza `reports/` nel `.gitignore`): in L0, due file modificati più `reports/junit.xml` e `reports/other.xml` → il commit è negato con «il diff ha superato le soglie di L0» e in L1 `reports/junit.xml` dà una violazione di scope.
- Gravità: minore (la prova dei test ha `reports/` ignorato). Proposta: escludere `output_dirs` (e `.tollgate-run/`) da `level_records`, `diff_size` e `commit_violations`, oppure far verificare a `init` (P4) che siano ignorate; aggiungere un test senza `.gitignore`.

**10. Il wrapper legge i campi con `sed` in modo fragile e `off` accetta ore dubbie.** Task 12, 13.
- Righe: 6112-6115 (`json_str` prende l'ultima occorrenza `"chiave": "…"` della riga, ignorando l'annidamento: verificato che con `"cwd":"/tmp"` dentro `tool_input` di uno strumento `mcp__*` la cwd letta è `/tmp`, e un repo non legato risulta non attivo, con uscita 0), 6122-6126 (`HOURS` da sole cifre: `08` abortisce lo script con errore aritmetico, verificato; `0.5` diventa 5 ore, `1.5` 15), 5740-5741 (con `session_id` vuoto `marker` è la cartella `bound`, che esiste: gli hook fuori dai repo aprono il DB).
- Spec 7.1 (punti 1-3). Gravità: minore. Proposta: leggere la prima occorrenza, con `cwd` solo al primo livello; validare `command_args` con `^[0-9]+$` e forzare la base 10 (`10#$HOURS`); in `run_hook` ignorare il segnalino se la sessione è vuota.

**11. Test deboli o con riferimenti sbagliati.** Task 6, 10, 12.
- `test_malformed_input_missing_fields` accetta `(0, 2)` (5083) per un caso che dà sempre 2; `test_binary_and_latin1_do_not_crash` (2289-2293) non usa byte non UTF-8 e la decodifica di `git._text` non è provata; il ramo `sqlite3.DatabaseError` di `run_hook` (5821-5825) non ha test, ma la tabella dei rilievi di P1 (riga 71) lo dà per coperto; la nota del Task 10 (4521) cita il test sbagliato.
- Gravità: minore. Proposta: fissare `assertEqual(..., 2)`, aggiungere un caso con byte `\xe8` in `test_git` e uno che danneggi il DB dopo l'apertura (con un modulo che alza `sqlite3.DatabaseError`), correggere la nota.

**12. Controlli di implementatore applicati a qualunque subagente non di sola lettura, senza task.** Task 18, 19 (più bookkeeping del Task 20).
- Righe: 8296-8303 (promemoria in `SubagentStart`), 8663-8680 e 8689-8712 (`SubagentStop`: report, dimensione, ricevuta, skill, sempre). Il glossario (riga 22 della spec) dice «ogni altro subagente che non è nell'elenco di sola lettura», quindi è conforme, ma un `general-purpose` in fase `plan` o in L0 riceve due veti e poi un `needs_you`, che apre un blocco.
- Anche: `Task 20` titolo Files (8746), Step 3 (8826-8831) e intestazione «Decisioni» (riga 31) citano tre elenchi diversi di decisioni per la rev 21; `Ctx.approved_waivers` (5412-5418) non è usato da nessun modulo di P2 (codice morto fino a P3).
- Gravità: minore. Proposta: limitare i controlli al subagente associato a un task (`row["task"]` non nullo, con `take_pending`) o alla fase `execution` di L1 e L2, e chiedere all'utente se la lettura più larga del glossario è voluta; allineare i tre elenchi di decisioni; documentare `approved_waivers` come API per P3 o toglierlo.

**13. Robustezza e duplicazioni minori.** Task 10, 11, 15-16.
- `verify.run_verify` con un lavoro privo di `work_base_sha`: `base=None` e `TypeError` in `git.changes` (4454); `waiver_cli.add_waiver` non normalizza il percorso e non richiede `--test` per `type=test` (4655-4685), per cui la deroga non copre mai nulla; `_inside` duplicata alla lettera in `writes.py` (7007-7008) e `bash_rules.py` (7373-7374), più la variante in `commit.py` (7846) e in `sessions.work_for_path`; la regola di `uncounted` sta in due punti (conflitto 3 della tabella coppie).
- Gravità: minore. Proposta: usare `ref` quando `work_base_sha` è nullo; normalizzare `file` in relativo alla radice del worktree e rifiutare `type=test` senza `--test`; spostare `_inside` in `_common.py` e riusarla.

**14. Il veto sugli script non tracciati colpisce anche binari ignorati da git.** Task 16.
- Righe: 7538-7552 (`_script_reason`): `./node_modules/.bin/vitest run` e `python3 tools/y.py` (script nuovo del lavoro) danno «effetto esterno». Spec 8.5 («script dentro il repo o il worktree che non sono tracciati nella base») lo prevede alla lettera, ma `node_modules/.bin`, `.venv/bin` e gli output di build sono ignorati da git.
- Gravità: minore (attrito, non errore). Proposta, da decidere con l'utente: esentare i percorsi ignorati (`git check-ignore`), lasciando il veto per i file non tracciati e non ignorati.

**15. Il Task 1 ha registrato esiti che aggiornano anche la spec 6.3 oltre al piano, ma il piano non li cita.** Task 18, 20.
- La spec rev 21 (riga 411) ora dice che il taglio in background e alla ripresa **non** è più «da verificare»; il piano, alla riga 7953 e in `post_agent`, descrive ancora il solo taglio in primo piano e il Task 20, Step 3, non elenca 6.3 fra le sezioni da riscrivere (ma la riga 411 è già nella spec). Documentale, collegato al conflitto 2.
- Gravità: minore. Proposta: aggiornare la descrizione del Task 18 con il modulo `prompt_submit` e citare 6.3 nel Task 20.

**16. Documentazione delle interfacce incompleta.** Task 2, 12.
- `subagents.is_stale` è usata da Task 18 (8158) ma non compare tra i **Produces** del Task 2 (riga 284); `Mappa dei file` (83-125) non nomina `tests/test_analysis_isolation.py`, `tests/test_wrapper.py`, `tests/test_manifest.py`, `tests/test_criteria_p2.py`, `tests/test_components_p2.py`.
- Gravità: minore. Proposta: aggiungerle.
