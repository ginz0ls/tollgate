# tollgate, nucleo: piano principale

Data: 8 ottobre 2026.
Spec: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21). La spec dice **cosa** fa tollgate e perché; questo documento dice **in che ordine** si costruisce e **quale piano** copre ogni parte della spec. Il codice e i passi stanno nei piani specifici P0-P5.

Stato: P0 chiuso l'8 ottobre 2026 (`2026-10-08-tollgate-p0-verifiche.md`; esiti in `docs/verifiche/2026-10-08-p0-esiti.md`, applicati nella revisione 20 della spec). Nessun esito ha smentito un fatto portante: le sezioni 3 e 4 restano valide, con le note della matrice aggiornate. P1 chiuso il 9 ottobre 2026 sul ramo `p1-fondamenta` (merge su `main` in attesa dell'OK dell'utente; piano `2026-10-08-tollgate-p1-fondamenta.md`; 124 test verdi su Python 3.11 e 3.13). P2 chiuso il 9 ottobre 2026 sul ramo `p2-guardrail` (merge su `main` in attesa dell'OK dell'utente; piano `2026-10-09-tollgate-p2-guardrail.md`; 641 test verdi su Python 3.11 e 3.13, nessun `ResourceWarning`; matrice dei criteri nella sezione 4). P3-P5 da scrivere.

---

## 1. Regole

1. **Un piano specifico alla volta.** P(n+1) si scrive solo quando P(n) è chiuso, partendo dal codice reale e dalle interfacce che P(n) ha davvero prodotto.
2. **Dopo P0 questo documento si rivede.** Gli esiti delle verifiche possono cambiare il disegno (sezione 16 della spec): prima di scrivere P1 si aggiornano la spec (nella prima revisione libera) e, se serve, le sezioni 3 e 4 di questo documento.
3. **Ogni piano specifico chiude con i suoi criteri.** Un piano è chiuso quando i criteri di accettazione che la matrice (sezione 4) gli assegna passano come test, e la sua revisione finale non ha rilievi `blocker` o `major` aperti.
4. **Si costruisce con Superpowers, non con tollgate.** `tollgate:execute` non esiste finché P3 non è chiuso: P1-P5 si eseguono con subagent-driven-development o executing-plans. Dal momento in cui il nucleo funziona si può usarlo su se stesso, in una cartella diversa da quella di sviluppo (spec, sezione 13).
5. **Una correzione della spec scoperta durante un piano** si registra come nuova revisione della spec, non solo nel piano.
6. **Questo documento si aggiorna alla chiusura di ogni piano**: stato in testa, sezione 2, e le righe della matrice eventualmente spostate.

---

## 2. Sequenza

| Piano | Obiettivo | Richiede | Consegna | Finito quando |
|---|---|---|---|---|
| **P0 Verifiche** | Provare le 14 voci aperte della sezione 16 (compreso `skills:` negli agenti di plugin) | Spec rev 19 | Rapporto `docs/verifiche/2026-10-08-p0-esiti.md`; nuova revisione della spec | Ogni voce di 16 ha esito `sì`, `no` o `non determinato`, e le conseguenze approvate sono nella spec |
| **P1 Fondamenta** | La libreria su cui poggia tutto: configurazione, DB, eventi, fasi, task, atti | P0 chiuso | `bin/tollgate` con i sottocomandi di base; pacchetto `tollgate_core` | Test unitari verdi; criteri 25 e la parte DB del 17 |
| **P2 Guardrail** | Gli hook locali e le analisi pure che userà anche il gate | P1 | Wrapper `hooks/run`, adattatore, registro dei controlli, `verify`, `waiver`, `block`; pacchetto `tollgate_analysis`; `plugin.json`, `hooks.json` | Ogni riga di 7.2 e 7.4 testata con input JSON reale di Claude Code; criteri della colonna P2 |
| **P3 Flusso** | Il ciclo completo in locale: dall'issue alla PR, con l'instradamento ai profili verticali, la Definition of Done e i budget dei task | P2 | Skill, agenti, `start`, `execute` e `task`, `finish`, `open-pr`, `sync`, `adopt`, `cleanup`, `abandon`, `reopen`, audit della spec | Test di integrazione su repo git temporaneo con `TOLLGATE_GH` finto; criteri della colonna P3 |
| **P4 Gate** | Il controllo autorevole su GitHub | P2 (analisi), P3 (blocco JSON della PR) | `gate run/evaluate/guard/base-ids`, i cinque workflow, `init` con la misura della modalità | I casi del criterio 10 sui due repo di prova (`protected` e `detect`); criteri della colonna P4 |
| **P5 Eval e CI** | La prova che tollgate migliora il risultato, e la CI del plugin | P3, P4 | I 9 casi di `claude plugin eval`, la Action di CI del repo di tollgate, documentazione d'uso | Eval con 3 esecuzioni per caso; CI verde |

P3 e P4 dipendono entrambi da P2 e sono in parte indipendenti: P4 può partire quando P3 ha fissato il blocco JSON della PR (18.1).

---

## 3. Interfacce tra i piani

Sono i punti in cui un piano consegna e un altro si appoggia. **I nomi li fissa il piano che li produce**, e il piano successivo li copia dal codice, non da qui. Dopo la chiusura di ogni piano questa sezione si aggiorna con i nomi reali: per P1 e P2 sono sotto; quelli di P3-P5 restano indicativi.

### Pacchetti

| Pacchetto | Piano | Responsabilità |
|---|---|---|
| `tollgate_core` | P1 | Moduli `paths` (cartella di stato), `clock`, `config`, `db` (DB e migrazioni), `events`, `phases`, `tasks`, `acts`, `dod`, `stats`, `cli` (entrata `bin/tollgate`) |
| `tollgate_analysis` | P2 | Funzioni pure, senza DB né rete: piano e scope, livello, test-guard, JUnit, deroghe, regole sui comandi Bash |
| `tollgate_checks` | P2 | I moduli del registro (spec 3.2): `CHECK` e `decide(event, ctx)` |
| `tollgate_hooks` | P2 | Motore degli hook: adattatore dell'harness (`adapter`), contesto in sola lettura (`context`), registro (`registry`), runner, operazioni `record` (`apply`, `model`) |
| `tollgate_flow` | P3 | Operazioni con git e `gh`: avvio, ripresa, task, finish, open-pr, sync, adopt |
| `tollgate_gate` | P4 | Calcolo del gate da zero, guard, identificativi della base, sentinel |

Regola: `tollgate_analysis` non importa mai `tollgate_core`. Così il gate su GitHub (P4) usa le stesse analisi della copia locale senza portarsi dietro il DB (spec 3.1: «stesso codice in locale e su GitHub»).

### Contratti

| Produce | Consuma | Contratto |
|---|---|---|
| P1 | P2, P3, P4 | Caricamento di `tollgate.toml` da un riferimento git (base del lavoro o punta del predefinito), con `schema_version`, chiavi sconosciute ignorate con avviso, errore sui tipi sbagliati (spec 11.4). `config.load_config(state, repo, ref, env=None) -> Config`; senza git: `load_config_text(text, source)` e `load_config_at(repo, ref)`. Errori: `ConfigError`, `ConfigNotFound` |
| P1 | P2, P3 | Apertura del DB nella cartella di stato, con WAL, `busy_timeout`, migrazioni solo in avanti, backup con la API di SQLite (spec 12.1). `paths.resolve_state(env=None) -> State`; `db.open_db(state) -> Connection`; `db.tx(conn)` (context manager); `db.backup(conn, state, reason) -> Path`; `db.integrity_ok(path) -> bool`; `db.restore(state, *, interactive, confirm) -> str`. Errori: `DbError` (blocchi, I/O), `DbCorrupt` (solo file corrotto: SQLITE_CORRUPT/NOTADB), `DbTooNew`. Il passaggio a WAL è ritentato sotto contesa |
| P1 | P2, P3, P5 | Registrazione di un evento con la busta di 18.4 e `seq` monotono; esportazione in JSONL (`tollgate events --after-seq N`). `events.record_event(conn, type_, data=None, *, now, session=None, work=None, host=None) -> int` (il `seq`); `events.export_events(conn, after_seq) -> list[dict]`; `events.to_jsonl(items)`; `events.prune_events(conn, now, events_days) -> int` (chiamante: `start` in P3) |
| P1 | P2, P3 | Transizioni di fase (12.3) e di `tasks.state` (6.3) che rifiutano tutto ciò che non è in tabella. `phases.set_phase(conn, state, work, to, cause, *, now, session=None)`; `open_block(conn, state, work, type_, reason, *, now, session=None) -> int`; `close_block(conn, state, block_id, resolution, *, now, session=None) -> str`; `tasks.task_event(conn, work, number, event, *, now, session=None) -> str`. Chiudere un lavoro (`set_phase(..., "closed", ...)`) chiude anche i suoi blocchi aperti. Errori: `TransitionError`, `TaskTransitionError`. Anche: `phases.create_work(conn, *, repo_key, issue, level, now, session=None, branch=None, worktree=None, work_base_sha=None, gate_mode=None, spec_path=None, from_approved_spec=False) -> int` (errore `WorkExists` se esiste un lavoro attivo per quel repo e issue), `find_active(conn, repo_key, issue)` e `find_latest(conn, repo_key, issue)` (riga o `None`), `bind_session(conn, work, session, *, now)`, `set_level(conn, work, level, *, now, session=None)`; `tasks.add_task(conn, work, number, *, source, kind="plan", skills_required=None, now, session=None)`, `tasks.add_skill_used(conn, work, number, skill)` |
| P1 | P2, P3 | Atti: registrazione, legame a sessione/lavoro/oggetto, scadenza, consumo; `finish` legato allo SHA di HEAD (8.4). `acts.record_act(conn, *, type_, object_=None, target=None, args=None, typed_text, source="claude-code", actor=None, session, work=None, head_sha=None, now, ttl_minutes) -> str`; `find_usable(conn, *, type_, object_=None, target=None, work, session, now, head_sha=None)` restituisce una riga di `acts` o `None`; `consume(conn, act_id, *, type_, object_=None, target=None, now, work, session, head_sha=None)` controlla tipo, oggetto e target (`ActError` se non coincidono, `None` incluso), lavoro, sessione, scadenza e, per `finish`, l'HEAD; `expire_stale(conn, *, now, session=None) -> list[str]`; `invalidate_finish(conn, work, head_sha, *, now, session=None) -> list[str]`. `session` è obbligatoria per ogni atto tranne `finish`. Un `finish` decade se esiste un evento `commit` dello stesso lavoro più recente dell'atto. Errore: `ActError` |
| P1 | P2, P3, P4 | Definition of Done dai dati (8.7): `dod.compute_dod(conn, work, *, head_sha, allow_no_tests, required_commands, external=None, profile_items=None) -> list[DodItem]`, dove `required_commands` sono i comandi del gate più i `dod` dei profili (la voce `receipt` è falsa se uno non ha ricevuta sullo SHA o se la lista è vuota); `dod.dod_passes(items) -> bool` (falso su lista vuota) |
| P1 | P2, P3 | Statistiche dagli eventi (criterio 43): `stats.compute_stats(conn, *, now, work=None, since=None) -> dict`, dove `work` è l'id interno del lavoro. Gli intervalli di fase si costruiscono da tutti gli eventi e si tagliano sulla finestra; i conteggi puntuali sono filtrati da `since` |
| P1 | P2, P3 | Sottocomandi di `bin/tollgate`: `status [--json]`, `stats [--since AAAA-MM-GG] [--work N]` (`N` è il numero dell'issue nel repo corrente; il comando lo risolve con `find_latest` nell'id interno), `events [--after-seq N]`, `db restore` (solo da terminale). A P3 restano `status --checkpoint` (decisione 6 del piano P1: scrive in `docs/superpowers/reviews/<N>/` del worktree) e la chiamata a `prune_events` da `start` |
| P1 | P2, P3 | **Vincoli per chi scrive nel DB.** (1) Scrivere solo con le funzioni di `tollgate_core`; il vincolo «dentro `db.tx`» vale quando si compongono più chiamate o si scrive SQL: le funzioni di `tollgate_core` aprono già la loro transazione e `db.tx` annidata non ha savepoint, quindi dentro una `tx` composta non si catturano eccezioni. (2) `set_phase`, `open_block` e `close_block` vanno chiamati fuori da una transazione, perché fanno la copia del DB dopo il commit. (3) Ogni commit visto dagli hook va registrato come evento `commit`: l'atto `finish` ne dipende. Gli hook chiamano inoltre `acts.invalidate_finish` ogni volta che vedono un HEAD diverso dallo SHA di un `finish` in attesa, oltre a registrare l'evento `commit`. (4) Passare sempre `required_commands` (comandi del gate e `dod` dei profili) e `profile_items` a `compute_dod`. (5) Gli hook gestiscono `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni |
| P2 | P3, P4 | Analisi pure, senza DB né rete (`tollgate_analysis`): `plan.check_plan(text, *, required_sections, max_scope_files, must_have_tests, level, profiles, active_always)` (7.5); `level.diff_level`, `level.max_level`, `level.next_level`, `level.labels_level` (5); `testguard.check` con `GuardConfig` (8.2); `junit.parse_junit` e `Junit` (forma degli identificativi per strumento, 7.5); `waivers.parse`, `waivers.dumps`, `waivers.status`, `waivers.covers`, `waivers.unresolved`, `waivers.next_id`, `waivers.path_for` (18.2); `bash.parse`, `bash.destructive`, `bash.write_targets`, `bash.removal_targets`, `bash.is_push`, `bash.is_commit`, `bash.hooks_path_override` (7.4); `report.parse_report`, `report.is_turn_cut`, `report.transcript_tokens` (18.5); `profiles.task_skills`, `profiles.active_profiles` (6.3) |
| P2 | P3, P4 | Ricevute, verifica e scope (`tollgate_core`): `verify.run_verify(state, wt, *, related, now, environ)`; `verify.gate_commands(cfg, files)` (comandi del gate più i `gate` dei profili attivi, spec 8.1 e 8.7); `receipts.add`, `receipts.latest`, `receipts.any_since`; `dod.receipt_verdict(rows, head_sha, allow_no_tests, …)`, la sola logica delle ricevute, usata anche da `SubagentStop` (8.1); `scope.register_plan(conn, state, work, …, plan_tasks, advance, now)`; `git.changes(repo, base, *, head, exclude)` e `git.diff_size(…)`; `globs.escape(path)` (dialetto gitignore, 3.2) |
| P2 | P3 | Subagenti e sessioni (`tollgate_core`): `subagents.start(conn, *, agent_id, type_, session, work, task, base_sha, fingerprint, now, refresh_fingerprint=False)` (`refresh_fingerprint` solo alla ripresa di un subagente di sola lettura, 7.3); `subagents.get`, `set_name`, `set_report`, `add_veto`, `finish`, `by_name`, `running`, `is_stale`, `interrupt`; `sessions.touch`, `sessions.alive`, `sessions.bound_work`, `sessions.work_for_path`, `sessions.mark_bound` (segnalino `bound/`, decisione 22 del piano P2); `tasks.assign(conn, work, number, implementer=, agent_type=, pending=, now=)` con `pending` = `launch` o `resume` (6.3), `tasks.take_pending`, `tasks.add_task`, `tasks.add_skill_used`, `tasks.add_commit`, `tasks.task_event` |
| P2 | P3 | Effetti e atti (`tollgate_core`): `effects.effect_key`, `effects.effect_id` (`e-` più 8 caratteri esadecimali, decisione 14), `effects.request`, `effects.mark_executed`, `effects.get`, `effects.executed_at`; `acts` come in P1, con `consume` a `PostToolUse Bash` per gli effetti (8.5); `Ctx.approved_waivers(work)` (3.2, API per P3) |
| P2 | P3, P4 | Registro dei controlli (`tollgate_hooks`): `model.allow()`, `model.deny(reason, rule=)`, `model.inject(text)`, `model.record(op, **data)`; `apply.OPS` (insieme dei nomi delle operazioni `record`, letto dal file), `apply.apply(conn, state, ctx, decision)`; `_common.budget_cut_records(ctx, agent_id, tokens)` (taglio di `maxTurns`, 6.3); un modulo di `tollgate_checks` ha `CHECK = {"api", "events", "component", "order"}` e `decide(event, ctx)` |
| P2 | P3 | **Vincoli per P3.** (1) `task start` scrive il brief con `name` uguale a `tasks.implementer`, perché `PreToolUse Agent` lo controlla alla lettera; (2) la statusline scrive `<cartella di stato>/ctx/<session_id>.json` con `used_pct` (11.3, decisione 13); (3) `start` pulisce i segnalini `bound/` delle sessioni chiuse (decisione 22); (4) `open-pr` rifiuta con deroghe in attesa (`waivers.status`) e con effetti in `requested` (decisione 9); (5) `approve level` scrive `work_items.level_cap_paths` (decisione 7); (6) i verdetti dei revisori e i report degli avversari sono moduli nuovi di `tollgate_checks` per `subagent_stop`, che devono controllare `subagents.state != 'tampered'`; (7) `task start` chiama `tasks.assign` con `pending` (`launch`, o `resume` per le riprese, decisione 7) |
| P3 | P4 | Blocco JSON della PR (18.1), report e file di approvazione (18.3), verdetti (18.5) |
| P4 | P3 | `gate run` locale usato da `finish check` |

---

## 4. Matrice di copertura

### Sezioni della spec

| Sezione | Piano | Note |
|---|---|---|
| 0 Glossario | tutti | I nomi del glossario sono i nomi nel codice |
| 1 Scopo e modello di fiducia | — | Guida; i limiti di 1.2 diventano testo di `status` e della documentazione (P5) |
| 2 Decisioni | tutti | Vincoli globali di ogni piano |
| 3 Struttura del plugin | P2 (`plugin.json`, `hooks.json`), P3 (skill e agenti) | `marketplace.json` in P3 |
| 3.1 Sottocomandi | P1 (scheletro, `status`, `stats`, `db restore`, `events`), P2 (`hook`, `verify`, `waiver`, `block`), P3 (`start`, `task`, `finish`, `sync`, `adopt`, `cleanup`, `abandon`, `act apply`), P4 (`gate`, `init`) | Variabili di test con sentinella `.tollgate-test`: P1 |
| 3.2 Principi, registro, adattatore | P1 (configurazione), P2 (registro, adattatore, eventi d'ingresso, `ctx`) | |
| 4 Ruoli | P3 | Agenti e brief; agenti concreti per area in B |
| 5 Livelli | P2 (calcolo), P3 (tetto con `approve level`, fette con `--spec`), P4 (minimo nel gate) | |
| 6.1 Avvio | P3 | |
| 6.2 Spec e piano, audit della spec | P3 | Skill `spec-audit`, agenti avversari e auditor, file di approvazione, `reopen` |
| 6.3 Esecuzione | P1 (`tasks`), P2 (controllo delle skill usate, `PostToolUse Skill`), P3 (`execute`, `task`, agenti, instradamento ai profili, dimensione e budget del task, report a campi fissi) | Implementatori in primo piano con un nome fisso, ripresi per nome (rev 20) |
| 6.4 Chiusura | P3 | `finish check` usa `gate run` di P4: in P3 si usa una versione locale minima, sostituita in P4 |
| 6.5 Dopo la PR | P3 | |
| 6.6 Dove valgono le regole | P2 | |
| 7.1 Wrapper | P2 | |
| 7.2 Tabella degli hook | P2 | Righe di rev 20: `PostToolUse Agent` (nome → `agent_id`, taglio di `maxTurns` con chiusura del subagente), token a `SubagentStop`, `PreToolUse SendMessage` per nome, `SubagentHandback` unica fonte in auto mode, subagenti interni ignorati |
| 7.3 Sola lettura | P2 | |
| 7.4 Regole su Bash | P2 | |
| 7.5 `plan-check` | P2 | |
| 8.1 Ricevute | P2 | |
| 8.2 test-guard | P2 (analisi e hook), P4 (nel gate) | |
| 8.3 Deroghe e blocchi | P2 | |
| 8.4 Atti | P1 (modello), P2 (registrazione via hook), P3 (skill e consumo) | Atto da `command_name` e `command_args` (P0, rev 20) |
| 8.5 Effetti esterni | P2 | |
| 8.6 Revisori | P3 | Standard del revisore e disaccordo istruito (rev 18) |
| 8.7 Definition of Done | P1 (calcolo dai dati), P3 (`finish check`), P4 (voci ricalcolate nel gate) | |
| 9.1-9.6 Gate su GitHub | P4 | |
| 10 Revisione finale | P3 | |
| 11.1 Dipendenze | P2 | I tag esistono con il prefisso `v`; P2 verifica se il risolutore di `dependencies` lo accetta (spec 16), altrimenti il ripiego di 11.1 |
| 11.2 `init` | P4 | |
| 11.3 `setup` e statusline | P3 | Riusa `statusline/statusline.sh` |
| 11.4 `tollgate.toml` | P1 (caricamento e validazione), P4 (`init` lo propone) | |
| 12.1-12.3 Stato locale | P1 | |
| 12.4 Ripresa, adozione, pulizia | P1 (migrazioni), P3 (ripresa, `adopt`, `cleanup`) | |
| 13 Errori e casi limite | P2, P3, P4 | Ogni riga va nel piano che possiede il meccanismo |
| 14 Test del plugin | tutti (test), P5 (eval e CI) | |
| 16 Da verificare | P0 e P2 (chiuse) | Esiti delle due voci verificate nel Task 1 di P2 (`docs/verifiche/2026-10-09-p2-verifiche.md`): (a) prefisso `v` in `dependencies`: i tag sono `<plugin>--v<versione>` e Superpowers ha solo `v6.4.1` e `v6.4.2`, quindi nessun `version` per Superpowers (11.1); (b) taglio di `maxTurns` in background e durante una ripresa: nessun `SubagentStop`, riconosciuto da `UserPromptSubmit` con `<task-notification>` (6.3) |
| 17 Cosa resta aperto | P5 | Documentazione dei limiti |
| 18.1 Blocco JSON | P3 (scrittura), P4 (lettura) | |
| 18.2 Deroghe | P2 | |
| 18.3 Report e approvazioni | P3 | |
| 18.4 Eventi | P1 | |
| 18.5 Rilievi e verdetti | P3 | |

### Criteri di accettazione (sezione 15)

| Criterio | Piano | | Criterio | Piano |
|---|---|---|---|---|
| 1 Avvio | P3 | | 20 Rinomine | P2 |
| 2 Piano | P2 | | 21 Deroghe | P2, P4 |
| 3 Scope | P2 | | 22 Livelli | P2, P3, P4 |
| 4 Implementatore | P2 (hook), P3 (`task`) | | 23 Effetti ripetuti | P2 |
| 5 Commit | P2 | | 24 Audit della spec | P3 |
| 6 Comandi | P2 | | 25 Fasi | P1 |
| 7 Ambito | P2 | | 26 Da correggere | P3 |
| 8 Subagenti | P2 | | 27 Neutralizzazione | P4 |
| 9 Revisori | P3 | | 28 Ripresa | P3 |
| 10 Gate su GitHub | P4 | | 29 Profili | P2, P4 |
| 11 Protezione e modalità | P4 | | 30 Senza test | P2, P4 |
| 12 PR | P3 | | 31 Fasi dopo `finish` | P2, P3 |
| 13 Atti | P2 | | 32 Marcatori e skipped | P2, P4 |
| 14 Wrapper | P2 | | 33 Issue e deroghe nel gate | P4 |
| 15 Ricevute | P2 | | 34 Modalità | P2 (push negato), P4 |
| 16 Sync | P3 | | 35 Componenti spenti | P3, P4 |
| 17 Adozione e ripristino | P1 (`db restore`), P3 (`adopt`) | | 36 Piano registrato nel gate | P4 |
| 18 Componenti | P2, P3, P4 | | 37 Flusso dopo l'approvazione | P2 (hook), P3 |
| 19 Budget | P2 | | 38 Profili verticali | P2 (hook), P3 (`task start`, revisione) |
| | | | 39 Task piccoli e budget | P2 (`SubagentStop`), P3 |
| | | | 40 Revisione | P3 |
| | | | 41 Definition of Done | P3, P4 |
| | | | 42 Must-have legati ai test | P2 (`plan-check`), P3, P4 |
| | | | 43 Statistiche | P1 |
| | | | 44 `attenzione` a due gruppi | P4 |

Casi di eval (spec 14, 1-9): P5.

### Prove dei criteri di P2 (Task 20)

Formato `file::Classe.metodo`, con `tests/` come radice. Le parti marcate «Resta a» non sono coperte da P2 e passano al piano indicato. I test marcati «nuovo» sono stati aggiunti nel Task 20 nel modulo che possiede il codice.

| Criterio | Test che lo dimostra | Resta a |
|---|---|---|
| 2 Piano | `test_plan.py::PlanCheckTest.test_missing_section`; `test_plan.py::PlanCheckTest.test_pattern_or_dir_rejected`; `test_check_post_edit.py::PlanCheckHookTest.test_complete_plan_registers_scope`; `test_check_post_edit.py::PlanCheckHookTest.test_incomplete_plan_vetoed_and_not_registered`; `test_scope.py::ScopeTest.test_register_twice_rejected_and_scope_unchanged`; `test_check_writes.py::ExecutionL1Test.test_locked_plan` | |
| 3 Scope | `test_check_writes.py::ExecutionL1Test.test_scope`; `test_check_commit.py::CommitTest.test_out_of_scope_then_waiver`; `test_check_writes.py::PhasesTest.test_plan_phase`; `test_check_writes.py::ExecutionL1Test.test_coordinator_cannot_write_code` | |
| 4 Implementatore | `test_check_agents.py::PreAgentTest.test_general_purpose_denied_with_execute_hint`; `test_check_agents.py::PreAgentTest.test_implementer_rules`; `test_check_agents.py::PreAgentTest.test_profile_agent_replaces_generic_implementer` (nuovo); `test_check_agents.py::StartAndResumeTest.test_name_registry_and_send_message`; `test_check_agents.py::StartAndResumeTest.test_start_associates_task_and_keeps_base_on_resume`; `test_check_agents.py::StartAndResumeTest.test_needs_context_resume_allowed` | `task done` senza `approved` e il terzo `task start --fix` (P3) |
| 5 Commit | `test_check_commit.py::CommitTest.test_deleted_test`; `test_check_commit.py::CommitTest.test_deleted_js_test_in_dunder_tests`; `test_check_commit.py::CommitTest.test_pytest_skip_added`; `test_check_commit.py::CommitTest.test_mark_skip_added`; `test_check_commit.py::CommitTest.test_assertion_replaced_by_comment`; `test_check_commit.py::CommitTest.test_process_exit_is_fine`; `test_testguard.py::TestGuardTest.test_xdescribe_added` | `xdescribe` non ha un test a livello di hook: il commit chiama la stessa `testguard.check`, coperta dal modulo |
| 6 Comandi | `test_check_effects.py::EffectsTest.test_other_effects`; `test_check_effects.py::EffectsTest.test_veto_act_once_then_warning`; `test_check_effects.py::EffectsTest.test_allowed`; `test_check_effects.py::EffectsTest.test_untracked_ignored_script_is_still_an_effect`; `test_check_bash.py::BoundSessionTest.test_destructive_and_forbidden`; `test_bash.py::ClassifyTest.test_claude_and_tollgate`; `test_check_bash.py::RepoLevelTest.test_inactive_repo_push_passes` | |
| 7 Ambito | `test_check_bash.py::BoundSessionTest.test_branch_changes_in_worktree`; `test_check_bash.py::BoundSessionTest.test_push_and_pr_denied`; `test_check_writes.py::ExecutionL1Test.test_main_checkout_is_denied`; `test_check_post_bash.py::PostBashTest.test_merge_bringing_deleted_test_opens_needs_you` | |
| 8 Subagenti | `test_check_agents.py::PreAgentTest.test_context_guard`; `test_check_agents.py::PreAgentTest.test_single_writer_and_stale`; `test_subagents.py::SubagentsTest.test_is_stale_uses_last_seen_then_started` | |
| 13 Atti | `test_check_acts.py::ActsTest.test_skill_tool_does_not_create_acts`; `test_check_acts.py::ActsTest.test_non_tollgate_and_status_are_not_acts` | |
| 14 Wrapper | `test_wrapper.py::WrapperTest.test_control_errors_become_2`; `test_wrapper.py::WrapperTest.test_timeout_becomes_2`; `test_wrapper.py::WrapperTest.test_informative_errors_become_0`; `test_wrapper.py::WrapperTest.test_inactive_repo_exits_0_without_running`; `test_wrapper.py::WrapperTest.test_without_python`; `test_wrapper.py::WrapperTest.test_off_on_and_expiry` | |
| 15 Ricevute | `test_verify.py::VerifyUnitTest.test_receipt_state` (zero test: `empty`); `test_verify.py::VerifyRunTest.test_old_report_is_removed_before_run` (nuovo: report vecchio cancellato, report configurato assente → `red`); `test_verify.py::VerifyRunTest.test_green_receipt_and_clean_env` (variabile fuori da `env_allow` non visibile); `test_verify.py::VerifyUnitTest.test_clean_env` | |
| 18 Componenti | Una chiave per test, con la chiave a `false` e il controllo spento: `test_check_writes.py::ExecutionL1Test.test_scope_component_off` (`scope_check`); `test_check_post_edit.py::PlanCheckHookTest.test_plan_component_off` (`plan_check`); `test_check_commit.py::CommitTest.test_test_guard_component_off` (`test_guard`); `test_check_subagent_stop.py::ReceiptGateOffTest.test_done_without_receipt_passes` (`subagent_receipt_gate`); `test_check_subagent_stop.py::ReadonlyOffTest.test_tampering_ignored_when_component_off` (`readonly_check`); `test_check_agents.py::PromptSubmitCutTest.test_budget_component_off_still_closes_row_without_block` (`task_budget`); `test_components_p2.py::ContextGuardOffTest.test_context_over_stop_passes_when_off` (`context_guard`, nuovo); `test_components_p2.py::SingleWriterOffTest.test_second_writer_passes_when_off` (`single_writer`, nuovo); `test_components_p2.py::TaskSizeOffTest.test_big_task_without_size_reason_passes_when_off` (`task_size`, nuovo); `test_components_p2.py::ReportFieldsOffTest.test_invalid_report_passes_when_off` (`report_fields`, nuovo); `test_components_p2.py::MustHaveTestsOffTest.test_must_have_without_test_registers_when_off` (`must_have_tests`, nuovo) | |
| 19 Budget | `test_criteria_p2.py::EndToEndTest.test_session_start_injects_state` (hooks/run vero); `test_hook_engine.py::RunnerTest.test_inject_budget_session_start` | |
| 20 Rinomine | `test_testguard.py::TestGuardTest.test_rename_with_same_tests` | |
| 21 Deroghe | `test_check_commit.py::CommitTest.test_pending_test_waiver_lets_commit_pass`; `test_check_commit.py::CommitTest.test_out_of_scope_then_waiver`; `test_waivers.py::WaiversTest.test_pending_waiver_still_covers_locally` | Deroga per pattern in `attenzione` (P4) |
| 22 Livelli | `test_check_post_edit.py::LevelTest.test_l0_grows_to_l1_and_plan`; `test_check_post_edit.py::LevelTest.test_sensitive_path_goes_l2`; `test_level.py::LevelTest.test_cap_holds_until_new_sensitive_path` | Livello dichiarato sotto il minimo → `verdict` rosso (P4) |
| 23 Effetti ripetuti | `test_check_effects.py::EffectsTest.test_veto_act_once_then_warning` (avviso «già eseguito alle»); `test_check_effects.py::EffectsTest.test_new_sha_is_a_new_effect_without_warning` | |
| 29 Profili | `test_profiles.py::ProfilesTest.test_active_and_skills`; `test_verify.py::VerifyUnitTest.test_gate_commands_with_profiles` | `gate` del profilo eseguito nel gate (P4) |
| 30 Senza test | `test_check_subagent_stop.py::AllowNoTestsTest.test_empty_receipt_counts`; `test_dod.py::DodTest.test_empty_needs_allow_no_tests` | `attenzione` rosso nel gate (P4) |
| 31 Fasi dopo `finish` | `test_check_writes.py::PhasesTest.test_review_and_pr_open` | `finish check` rosso riporta a `execution` (P3) |
| 32 Marcatori e `skipped` | `test_check_commit.py::CommitTest.test_mark_skip_added`; `test_check_commit.py::CommitTest.test_pytest_skip_added`; `test_testguard.py::TestGuardTest.test_pytest_mark_skip_added` | `skipped` nel JUnit della testa → `verdict` rosso (P4) |
| 34 Modalità | `test_check_bash.py::DetectModePushTest.test_push_default_branch_denied_in_detect` (nuovo: `detect`, sessione non legata); `test_check_bash.py::RepoLevelTest.test_push_to_default_branch` | `init` con token senza amministrazione; primo push con `tollgate-sentinel` (P4) |
| 37 Flusso dopo l'approvazione | `test_check_writes.py::PhasesTest.test_spec_audit_no_plans`; `test_check_common.py::LockedDocsTest.test_spec_locked_after_approval_in_later_phase`; `test_check_common.py::LockedDocsTest.test_spec_unlocked_after_reopen_spec_keeps_history_file`; `test_check_common.py::LockedDocsTest.test_plan_locked_after_registration_in_execution`; `test_check_common.py::LockedDocsTest.test_plan_unlocked_after_reopen_plan` | `needs_fix` → `task start --from-findings`; `plan_sha` di `approve plan` in L2 (P3) |
| 38 Profili verticali | `test_check_subagent_stop.py::WebProfileSkillTest.test_done_without_profile_skill_vetoes` (nuovo: skill del profilo `web` dal piano al veto); `test_check_subagent_stop.py::ExtraTest.test_required_skill_missing_vetoes`; `test_check_agents.py::PreAgentTest.test_profile_agent_replaces_generic_implementer` (nuovo) | `task start` che sceglie gli agenti dal profilo; unione delle skill di due profili; `final_specialist` (P3) |
| 39 Task piccoli e budget | `test_check_subagent_stop.py::BudgetAndSizeTest.test_size_reason_required_over_max`; `test_check_subagent_stop.py::BudgetAndSizeTest.test_tokens_over_cap_block_even_with_green`; `test_check_agents.py::PromptSubmitCutTest.test_background_cut_closes_row_budgets_task_and_blocks`; `test_check_agents.py::PostAgentExtraTest.test_foreground_cut_records_tokens`; `test_report.py::ReportTest.test_turn_cut_requires_int_count_and_prefix`; `test_report.py::ReportTest.test_missing_fields` | `status` che dice quale tetto ha fermato il lavoro (P3) |
| 42 Must-have legati ai test (`plan-check`) | `test_plan.py::PlanCheckTest.test_must_have_without_test`; `test_plan.py::PlanCheckTest.test_manual_test_allowed`; `test_check_post_edit.py::PlanCheckHookTest.test_pattern_and_must_have_without_test`; `test_components_p2.py::MustHaveTestsOffTest.test_must_have_without_test_registers_when_off` (nuovo) | Ricalcolo della voce dal JUnit in DoD e nel gate (P3, P4) |

Criteri 1, 9-12, 16, 17, 24-28, 33, 35, 36, 40, 41, 43, 44: non assegnati a P2 dalla tabella sopra.

**Controllo.** Ogni sezione da 0 a 18 e ogni criterio da 1 a 44 ha almeno un piano. Un criterio assegnato a più piani è chiuso solo quando l'ultimo di quei piani lo fa passare.

---

## 5. Rischi della sequenza

| Rischio | Effetto | Come si gestisce |
|---|---|---|
| P0 smentisce un fatto portante (E1 ripresa, E4/I2 atti) | Cambia 6.3 o 8.4 | P1 non parte finché la spec non è aggiornata (regola 2) |
| `finish check` in P3 senza il gate completo | Doppio lavoro tra P3 e P4 | In P3 una versione minima dietro la stessa interfaccia di `gate run`, sostituita in P4 |
| Le interfacce di P1 si rivelano scomode in P2-P4 | Riscritture | P1 espone poche funzioni con test; le modifiche passano da una nuova revisione delle sue interfacce, non da scorciatoie |
| Testare gli hook senza Claude Code vero | Test che passano su input finti | Gli input JSON dei test di P2 vengono dai log reali della sonda di P0: campioni in `spikes/fixtures/hook-inputs/samples.json`, log completi anonimizzati in `docs/verifiche/evidenze/hook/` |
| Costo degli eval in P5 | Token e tempo | 3 esecuzioni per caso, come da spec; il costo si misura e si riporta |

---

## 6. Già decise per i sotto-progetti successivi

**Profili verticali (sotto-progetto B).** Il catalogo è in `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: 13 profili verticali e 2 trasversali, con le regole `tollgate:rules-<area>` distillate da fonti citate e **riviste dall'utente** prima di entrare nel plugin, e gli agenti `implementer-<area>`, `reviewer-<area>`, `final-<area>`. Il nucleo (P2, P3) consegna il contratto e l'instradamento; B scrive regole e agenti. Le bozze delle regole si possono preparare in parallelo a P1-P4, perché non toccano il codice del nucleo.

**Pratiche delle software house rimandate:**

Non sono nel nucleo perché richiedono la kanban (C) o dati accumulati nel tempo (D), ma sono **decise**, non scartate (`docs/RICERCA-ORGANIZZAZIONE.md`):

| Id | Pratica | Dove |
|---|---|---|
| C1 | Limite al lavoro in corso con regola pull | C |
| C2 | Metriche di flusso (tempo di ciclo, throughput, età dei lavori, rework) dagli eventi | C |
| C3 | Obiettivo per milestone con scope rinegoziabile | C |
| C4 | Prima i lavori più incerti; stato esplorazione/esecuzione | C |
| D1 | Post-mortem automatici che propongono regole per `rules-<area>`, approvate dall'utente | Dopo la v1 |
| D2 | Misura del team contro l'agente singolo a parità di token | D |
