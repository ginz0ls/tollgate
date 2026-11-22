# tollgate C1: tracciamento locale

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** La prima fetta di C. Tutto ciò che il futuro gestionale vorrà leggere si registra nello stato locale da subito, senza GitHub: la taglia del lavoro con la sua presa unica, le decisioni prese al posto dell'utente («ruling»), le domande dirette all'utente con la risposta, il costo in token dei subagenti, le decisioni sui rilievi; la storia degli eventi non si cancella più per difetto; una fotografia in JSON con versione dà lo stato di oggi.

**Architecture:** Quattro parti, nell'ordine.
1. **Stato.** Migrazione 7 (colonne della taglia e delle fette) e cinque tipi di evento nuovi nella busta 1.
2. **Storia.** `[retention] events_days = 0` vuol dire «mai»; con un numero di giorni gli eventi vecchi vanno prima in un archivio JSONL della cartella di stato.
3. **Registrazioni.** La taglia (funzione pura in `tollgate_analysis.worksize`, registrazione in `tollgate_core.sizes`) all'avvio, alla registrazione del piano, ad `approve spec <n>` e con l'atto `approve size`; il comando `ruling add`; un controllo degli hook su `AskUserQuestion`; l'evento `cost` alla chiusura di ogni subagente.
4. **Lettura.** `tollgate snapshot` e la pagina `docs/uso/gestionale.md`; una prova reale corta; la revisione 36 della spec.

**Tech Stack:** Python ≥ 3.11, solo libreria standard; `sqlite3`; `unittest` con `tests/run` (python3.11 e python3); `claude -p` solo nella prova reale del Task 9, dal controller.

**Spec:** il progetto di C `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md` (approvato dall'utente il 20/11/2026). È l'autorità: le scelte «utente» non si discutono, quelle «mia scelta» si correggono solo con un motivo scritto qui. Per C1 contano le sezioni 2 (obiettivi 1, 4, 7, 9.2, 9.3, 9.6), 3, 6, 10 e 14.

Poi il piano principale di C `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md` (sezione 2, riga C1; sezione 3, righe da C1; decisioni 2 e 6) e la spec del nucleo rev 35, sezioni 3.1, 3.2, 5 («Spec con più fette»), 6.1, 7.1, 7.2, 8.4, 11.4 (`[retention]`), 12.2, 18.4 e 20.

## Fatti verificati (20 novembre 2026, codice di `main` a `598bfd2`)

| Fatto | Fonte | Conseguenza qui |
|---|---|---|
| `events.EVENT_TYPES` è un `frozenset` chiuso; `record_event` rifiuta un tipo sconosciuto e prende `repo_key` e `issue` dal lavoro; la busta è `{"v": 1, seq, at, host, session, work, repo_key, issue, type, data}` | `bin/tollgate_core/events.py:12-41` | decisione 1; Task 1 |
| `test_spec_event_types_match_registry` confronta la riga `**Tipi:**` della spec 18.4 con `EVENT_TYPES` | `tests/test_docs.py:138-142` | Task 1 aggiorna quella riga della spec nello stesso commit |
| Lo schema arriva alla migrazione 6 (`MIGRATIONS`), con una copia del DB prima di ogni passo | `bin/tollgate_core/db.py:180-236` | Task 1: `SCHEMA_V7` |
| `[retention]` ha `retention_days = 30` ed `events_days = 180`; `housekeeping.run` (a ogni `start`, nuovo lavoro e ripresa: `start.py:241`) chiama `events.prune_events(conn, now, events_days)`, che cancella **tutti** gli eventi del DB più vecchi del limite (il DB è uno per macchina, la configurazione è del repo che parte), e `lookups.prune(..., days=events_days)` | `bin/tollgate_core/config.py:92`; `bin/tollgate_flow/housekeeping.py:26-49`; `bin/tollgate_core/events.py:78-81`; spec 11.4, righe 1345-1347. Il modello `templates/tollgate.toml` (16 righe) non ha `[retention]` | decisione 7; Task 2 |
| `start._create` calcola il livello e crea il lavoro con `phases.create_work`; le righe finali hanno `avviso: …` e per ultima `prossimo passo: EnterWorktree <percorso>` | `bin/tollgate_flow/start.py:456-527` | Task 3 |
| Il piano si registra in un solo punto, `scope.register_plan`, con tre chiamanti: l'operazione `plan` degli hook (da `post_edit._plan`, solo in L1), `l2acts.approve_plan` (L2) e `adopt._register_plan` | `bin/tollgate_core/scope.py:43-63`; `bin/tollgate_checks/post_edit.py:15-48`; `bin/tollgate_hooks/apply.py:231-234`; `bin/tollgate_flow/l2acts.py:236`; `bin/tollgate_flow/adopt.py:412-425` | decisione 2; Task 3 |
| `specdoc.slices(text)` conta le voci numerate di `## Fette previste` (1 senza sezione); `approve spec <n>` rifiuta se `n` non è quel numero, scrive `spec-approval.md` con `slices` e, con più fette, propone le issue | `bin/tollgate_analysis/specdoc.py:30-41`; `bin/tollgate_flow/l2acts.py:152-180` | Task 4 |
| Gli atti `approve` hanno l'oggetto in `acts.APPROVE_OBJECTS`; il target (secondo argomento) è in `checks/acts._TARGET_ARG`; `actapply.APPLIERS` applica `approve level` (tetto con motivo) e gli altri | `bin/tollgate_core/acts.py:12-13`; `bin/tollgate_checks/acts.py:12`; `bin/tollgate_flow/actapply.py:240-251` | Task 4 |
| `research submit` è il modello di un comando dell'implementatore: trova il lavoro dalla cartella (`sessions.work_for_path`), codici 0/1/2, righe su stdout o stderr; `cli_calls` nega ai subagenti solo `start`, `task`, `act`, `finish`, `review`, `audit`, `sync`, `adopt`, `cleanup`, `abandon`, `status --checkpoint` | `bin/tollgate_flow/research_cmd.py`; `bin/tollgate_core/cli.py:429-440` (dispatch di `research`); `bin/tollgate_checks/cli_calls.py:18-20` (`_COORDINATOR_ONLY`), `:103-114` (un comando che nomina tollgate e non si analizza è negato ai subagenti); spec 3.1 | decisione 5; Task 5 |
| Gli hook leggono gli strumenti da `adapter._PRE` e `_POST`; gli eventi d'ingresso sono in `model.INPUT_EVENTS`, quelli che possono negare in `CONTROL_EVENTS`; i matcher di `hooks/hooks.json` non hanno `AskUserQuestion`; un controllo registra un evento con `record("event", type=…, data=…, work=…)` | `bin/tollgate_hooks/adapter.py:10-13`; `bin/tollgate_hooks/model.py:7-11`; `hooks/hooks.json:6-7`; `bin/tollgate_hooks/apply.py:218` | decisione 4; Task 6 |
| Documentazione degli hook: `PreToolUse` può avere il matcher `AskUserQuestion`; `tool_input.questions` sono le domande, `answers` mappa il testo della domanda all'etichetta scelta (più scelte unite da virgole); `PostToolUse` ha `tool_response`, «la forma dipende dallo strumento», non descritta per `AskUserQuestion`. In una trascrizione di Claude Code di questa macchina il risultato ha le chiavi `questions`, `answers`, `annotations`. Con `claude -p` le domande dirette non si offrono senza un ospite dei permessi | `code.claude.com/docs/en/hooks` (letta il 20/11/2026); trascrizione locale (solo le chiavi) | decisione 4; Task 6, 9 |
| `subagent_finish` si emette in `subagent_stop.py` (`:27` in `_readonly`, la chiusura dei sola lettura generici, senza l'evento e senza token; `:88` implementatore senza lavoro o worktree; `:98`, `:108`, `:154`), `task_verdict.py` (`:50`, `:65`, `:69`), `final_review.py` (`:23`, `:50`, `:57`), `audit_round.py` (`:48`, `:61`, `:71`), `_common.tampered_records(row, work)` (`:76-81`, sola lettura che ha cambiato file, chiamata da `subagent_stop.py:26`, `task_verdict.py:48`, `final_review.py:40`, `audit_round.py:52`) e `_common.budget_cut_records` (`:343`, taglio di `maxTurns`, con i soli `totalTokens` di `PostToolUse Agent`, senza trascrizione). Un subagente senza riga o già chiuso esce con `[]` (`subagent_stop.py:68-71`) | `bin/tollgate_checks/` | decisione 3; Task 7 |
| `subagent_stop` conta i token con `report.transcript_tokens` (input + cache_creation + output, una volta per messaggio) e li passa a `subagents.finish` con l'operazione `subagent_finish`, che registra l'evento `subagent_stop`; le righe della trascrizione hanno `message.usage` e `message.model` | `bin/tollgate_analysis/report.py:87-108`; `bin/tollgate_checks/subagent_stop.py:95-154`; `bin/tollgate_core/subagents.py:78-95`; `bin/tollgate_hooks/apply.py:242-245` | decisione 3; Task 7 |
| `PostToolUseFailure` ha il matcher solo per le modifiche e `Bash`, e `adapter` la traduce solo per quelli | `hooks/hooks.json:8`; `bin/tollgate_hooks/adapter.py:44-49` | decisione 4; Task 6 |
| `adopt` crea sempre un lavoro nuovo (`create_work`) e legge `spec-approval.md`: prima quello dell'issue stessa (`approvals.approval_paths(issue)[0]`), poi, con `_approved_elsewhere`, quello di un'altra issue (la fetta 1 di una spec a più fette) | `bin/tollgate_flow/adopt.py:215-240`, `:346`, `:412-427` | decisione 2; Task 3 |
| Un lavoro L1 non arriva mai ad `approve spec`: l'atto vuole la fase `spec_audit` (`l2acts.py:153`), `reopen spec` vale solo in L2 (`:265-272`), un livello che sale non riporta la fase a `spec_audit` | `bin/tollgate_flow/l2acts.py`; `bin/tollgate_core/phases.py:233-268` | decisione 2 |
| Gli effetti in attesa stanno nella tabella `intents` con `action = 'effect'` e `state = 'requested'`, e l'id che l'utente digita in `approve effect` è `data.id` (`effects.effect_id`); nella stessa tabella stanno gli intenti `pr` e `sync` della CLI, anche loro `requested`, che non aspettano l'utente | `bin/tollgate_core/effects.py:16`, `:31-41`; `bin/tollgate_core/intents.py:13`, `:35-37` | decisione 8 |
| Il wrapper `hooks/run` tratta come controllo ogni `PreToolUse` (`CONTROL=yes`): senza Python, con un'uscita diversa da 0 e 2 o allo scadere esce con 2 e nega; `runner.run_hook` fa lo stesso (`_CONTROL_HOOKS = {"PreToolUse"}`, un input non valido → `_fail(control=True)`) | `hooks/run:15`, `:176-177`, `:212-215`; `bin/tollgate_hooks/runner.py:30`, `:55-59`, `:203-213`; spec 7.1 | decisione 4; Task 6 |
| Il tipo `session_start` è in `EVENT_TYPES` ma nessun punto di `bin/` lo registra: il controllo `checks/session.py` restituisce `expire_acts`, `bind`, `subagent_interrupt` e iniezioni | `bin/tollgate_core/events.py:14`; `bin/tollgate_checks/session.py:15-40` | decisione 4; Task 6 |
| In `post_edit.decide`, `_plan` è chiamato prima di `level_records` (`:60`, «un errore del livello non deve fermare il piano»); la riga `:66` decide solo l'ordine di applicazione (`level + plan`); `test_level_failure_does_not_block_plan_registration` lo fissa | `bin/tollgate_checks/post_edit.py:55-66`; `tests/test_check_post_edit.py:180-189` | decisione 2; Task 3 |
| Un subagente ripreso con `SendMessage` torna `running` sulla stessa riga (`resumes + 1`) e ha un altro `SubagentStop`; `transcript_tokens` legge la trascrizione per intero, e `subagents.tokens` si sovrascrive (`coalesce`) | `bin/tollgate_core/subagents.py:36-40`, `:78-95`; `bin/tollgate_analysis/report.py:87-108` | decisioni 3 e 8 |
| `registra` di `run-b1-flow.sh` esporta `TOLLGATE_STATE` dello stato di prova e salva `events.jsonl` e `status.json`; gli eventi che stampa li sceglie `spikes/b1/flowreg.py` (`WANTED`) | `spikes/run-b1-flow.sh:602-606`; `spikes/b1/flowreg.py:26` | Task 9 |
| `reviews.set_decision` è l'unico punto che scrive `findings.user_decision` e registra già l'evento `finding` con `confidence`, `verification`, `user_decision` e il motivo | `bin/tollgate_core/reviews.py:69-76` (`_log_finding`), `:269-286` (`set_decision`); `grep user_decision` su `bin/` | decisione 6; Task 7 |
| `status --json` è la sola fotografia di oggi: per repo, senza versione, con il testo dei blocchi | `bin/tollgate_core/cli.py:188-206` | decisione 8; Task 8 |
| Le evidenze contengono 169 copie dello stato (`…/home/.local/state/tollgate/tollgate.db`), tutte degli eval: 88 in `eval-b8/`, 81 in `eval-p5/`; nessuna delle prove reali | `find docs/verifiche/evidenze -name tollgate.db` | decisione 9; Task 8 (misura su copie in `/tmp`) |
| `spikes/run-b1-flow.sh` fa una prova reale di un lavoro L1 con `claude -p`, `gh` finto e `origin` nudo locale; `registra` stampa righe di `lookups`, eventi e stato | `spikes/run-b1-flow.sh:1-40`; `docs/verifiche/2026-11-12-b7-prova-flusso.md` | Task 9 |

**Da verificare prima del codice:** nulla sulle pagine. Lo scan pre-flight guarda i punti del «Review Focus» e i test che fissano i matcher di `hooks/hooks.json`, le chiavi di `[retention]` e le righe di `start`.

## Global Constraints

- **Codice e test.**
  - Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11.
  - Ogni task chiude con `tests/run` verde (`python3.11` e `python3`). Verifica finale come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`, senza «unclosed».
  - **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate fuori da sé; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`; il gate non importa i moduli nuovi.
  - Nessun modello di linguaggio nel codice (progetto 14): la presa della taglia sono regole.
- **Niente GitHub.** C1 non scrive né legge niente di nuovo su GitHub. Il testo delle ruling, delle domande e delle risposte resta nello stato locale (progetto 6, «Tutto locale»).
- **Cosa non cambia.**
  - La busta degli eventi resta alla versione 1: i tipi nuovi e i campi nuovi in `data` non la cambiano (spec 18.4).
  - Profili e regole approvati non si toccano: `skills/rules-*/SKILL.md`, `templates/profiles/*.toml`, `docs/profili/**`, `agents/*.md`.
  - Il gate (`tollgate_gate`) non cambia.
  - Un hook su `AskUserQuestion` non nega mai, nemmeno quando fallisce: il controllo delle fermate non sta in `CONTROL_EVENTS`, e il wrapper e `runner` non trattano quel `PreToolUse` come un controllo (decisione 4).
- **Prova reale** (Task 9): solo il controller, con `spikes/run-b1-flow.sh`, senza GitHub vero; circa 1-2 USD equivalenti sull'abbonamento, nessun addebito.
- **Cartelle temporanee dei test.** Ogni `mkdtemp` si chiude con `addCleanup`. Una cartella creata in `/tmp` ha un prefisso che comincia con `tollgate`. Nessuna asserzione che, se fallisce, stampi `os.environ`.
- **Il repo è pubblico.** Nei test e nei documenti niente nomi di progetti privati, nome utente, host, token. Nei test i nomi delle macchine sono finti (`macchina-prova`).
- **Stile.** Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che il progetto lascia a chi costruisce, o che il codice reale impone, con il costo se sbagliate. Il Task 10 le riporta nella revisione 36 della spec.

1. **Migrazione 7** (`db.SCHEMA_V7`):
   - `ALTER TABLE work_items ADD COLUMN size TEXT CHECK (size IS NULL OR size IN ('small','medium','large'))`;
   - `ALTER TABLE work_items ADD COLUMN size_by TEXT CHECK (size_by IS NULL OR size_by IN ('rules','user'))`;
   - `ALTER TABLE work_items ADD COLUMN slices INTEGER`.

   I lavori nati prima di C1 restano con `size` nullo: la fotografia li mostra con `size` nullo e nessuna regola li ricalcola da sola (come `work_items.research` di B1). Tipi nuovi in `EVENT_TYPES`: `size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost`. Costo: nessuno, tre colonne nullabili.
2. **La taglia** (progetto 3; mia scelta sulle soglie).
   - Nomi: `small`, `medium`, `large` nel codice e negli eventi; `piccolo`, `medio`, `grande` per l'utente (righe, atto).
   - **La presa** è una sola funzione pura: `tollgate_analysis.worksize.propose(signals: Signals) -> Proposal`, con `Signals(level: str, tasks: int, areas: int, slices: int)` e `Proposal(size: str, reason: str)`. Regole, nell'ordine: `slices > 1` → `large`; `level == "L2"` o `tasks >= MEDIUM_MIN_TASKS` (4) o `areas >= MEDIUM_MIN_AREAS` (2) → `medium`; altrimenti `small`. Il motivo è una frase per l'utente, per esempio «piano con 6 task su 2 aree».
   - **`areas`** è il numero di profili verticali distinti dei file dello scope (`worksize.areas(paths, profiles) -> int`, con `profiles.vertical_for`); un file del generico non conta.
   - **Quando** (`tollgate_core.sizes.decide`): all'avvio di un lavoro nuovo e in `adopt` (causa `start`; `tasks = 0`, `areas = 0`, `slices = 1`: quindi `small`, o `medium` in L2); alla registrazione del piano (causa `plan`, con i task e le aree dello scope; `slices` è `specdoc.slices(<testo del piano>)` in L1 e `work_items.slices` (o 1 se nulla) in L2, dove le fette le ha già fissate `approve spec`); quando il livello sale con l'operazione `level` degli hook (causa `level`; `tasks` dai task registrati, `areas = 0`, `slices` dalla colonna o 1); ad `approve spec <n>` (causa `approve_spec`, `slices = n`). In `adopt`, solo con il `spec-approval.md` corrente **dell'issue stessa** (`approvals.approval_paths(issue)[0]`) a più fette, anche `slices` dall'intestazione e `decide` con causa `approve_spec` e `confirmed` vero: il sì è già stato dato. Un'approvazione di un'altra issue (`_approved_elsewhere`: il lavoro è una fetta successiva) non cambia né `slices` né la taglia, come per la stessa fetta avviata con `start --spec`. Non nella ripresa.
   - **La riga ha tre forme**: (1) normale, `taglia: <applicata> — <motivo>`; (2) proposta `large` non autorizzata con la taglia applicata sotto `large`: in L1 la riga della strada (sotto), in L2 la forma normale; (3) taglia dell'utente diversa dalla proposta: `taglia: <applicata> (scelta dall'utente) — le regole proporrebbero <proposta>: <motivo>`. Con `current_by = 'user'` vale sempre la forma 3 (la 2 vale solo per una taglia delle regole). Con la taglia applicata già `large` (dopo `approve spec <n>`, o scelta dall'utente) la riga non dice mai «resta medio».
   - **La riga per l'utente** la compone una sola funzione pura, `worksize.preview(signals, current, current_by, *, cause, confirmed) -> Preview`, con `Preview(applied: str, line: str)`: la usa `sizes.decide` per decidere e registrare, e la usa `post_edit._plan` per l'iniezione, che si compone prima che le operazioni si applichino (`apply` non restituisce niente al controllo). Le due cose coincidono per costruzione, e un test lo fissa. Il record `plan` porta anche il livello della stessa modifica: `post_edit.decide` chiama prima `level_records` (nel `try` di oggi), ne ricava il livello nuovo (l'ultimo record `level`, altrimenti `work["level"]`; con un errore del livello vale `work["level"]`) e lo passa a `_plan`, che lo mette nel record e lo usa in `preview`; l'ordine di applicazione resta `level + plan` e `test_level_failure_does_not_block_plan_registration` resta com'è. `decide` per la causa `plan` usa quel valore: così la riga iniettata e l'evento coincidono anche quando il livello sale nella stessa modifica.
   - **Non scende mai da sola** e **`large` solo con `approve spec <n>`**: `decide` applica la proposta solo se è sopra la taglia attuale; se la proposta è `large` e la causa non è `approve_spec` con `n > 1`, applica `medium` e la riga dice la strada vera (progetto 3.2 e 5: le fette si leggono solo dalla spec approvata): in L1 «taglia proposta: grande — le fette diventano issue solo da una spec approvata: per averle, apri un'issue nuova per il lavoro a fette e avviala con /tollgate:start #<nuova> L2 (spec e /tollgate:approve spec <n>); questo lavoro resta medio e le fette restano un documento». Non si propone `abandon` e un riavvio sulla stessa issue: ramo e worktree restano dopo `abandon` e `start` sulla stessa issue può rifiutare o proporre `adopt` (spec 6.1, «ramo o PR remoti già esistenti»); in L2 non serve, perché le fette le dà `approve spec`. L'atto `approve spec <n>` con `n > 1` è il sì del progetto 3.2 e non ferma il lavoro.
   - **L'atto** `/tollgate:approve size <piccolo|medio|grande> <motivo>` **fissa** la taglia (`size_by = 'user'`), anche verso il basso: è la correzione dell'utente (progetto 3.2, «fissare»). `sizes.set_by_user` registra `size_decided` con `cause = "act"`, `by = "user"`, `confirmed` vero, `proposed` uguale alla taglia scelta, `signals` nullo e il motivo dell'utente in `reason`. Dopo `approve spec <n>` con `n > 1` su una taglia fissata dall'utente, `size_by` torna `rules` e l'evento ha `confirmed` vero. Con `size_by = 'user'` le regole continuano a proporre e a registrare `size_decided` (`proposed` diverso, `applied` uguale alla taglia dell'utente) ma non la cambiano; fa eccezione solo `approve spec <n>` con `n > 1`, che è un altro sì dell'utente. `approve size grande` è la scelta dell'utente sulla taglia, **non** l'autorizzazione a creare le fette: quella, per C5, è `slices > 1` scritto da `approve spec` (piano principale, sezione 3).
   - **`size_decided`** a ogni chiamata di `decide` e di `set_by_user`, anche quando la taglia non cambia: `data` = `{"proposed", "applied", "previous", "cause", "by": "rules"|"user", "reason", "signals": {"level", "tasks", "areas", "slices"}, "confirmed": bool | null}`, dove `by` è chi ha deciso la taglia applicata e `confirmed` è vero per un sì (`approve_spec` con `n > 1`, atto), nullo altrimenti. Sono i dati per confrontare in futuro un modello con le regole (progetto 3.3).
   - Costo se sbagliate: le soglie si cambiano in due costanti con i loro test; un lavoro di 3 task su un'area resta piccolo.
3. **Il costo è in token, per modello; niente dollari fuori dagli eval** (progetto 6: «senza inventare prezzi»; mia scelta). Alla chiusura di un subagente con trascrizione, `subagents.finish` registra dopo `subagent_stop` l'evento `cost` con `data` = `{"agent": <id>, "type", "task", "tokens", "by_model": {<modello>: {"input", "cache_creation", "cache_read", "output"}}, "usd": null, "source": "transcript"}`. `tokens` è il numero di oggi (`transcript_tokens`, senza `cache_read`); `by_model` tiene anche `cache_read` per chi vorrà dare un prezzo. Il costo per task e per lavoro si somma nella fotografia (decisione 8), non con eventi in più. Vale per **ogni** chiusura a `SubagentStop` con una trascrizione leggibile (`event.raw["agent_transcript_path"]`): implementatori (anche senza lavoro, `:88`), revisori dei task (`task_verdict`), revisori finali e verificatore (`final_review`), agenti dei giri di audit (`audit_round`), sola lettura generici (`_readonly`, `:27`) e sola lettura che hanno cambiato file (`tampered_records`). Per questo `_readonly` riceve l'evento, e `tampered_records` riceve token e uso calcolati da chi la chiama (in `task_verdict.py` e `final_review.py` la chiamata, `:48` e `:40`, precede oggi il calcolo dei token, `:50` e `:42`: `transcript_cost` va spostato prima); un helper unico `_common.transcript_cost(event) -> tuple[int, dict | None]` evita quattro letture diverse: i token restano quelli di oggi (`transcript_tokens`, 0 senza file, perché il ramo del budget confronta `tokens > cap`), l'uso è `None` senza file o con una trascrizione senza righe `usage` (`{}`). `tampered_records(row, work, *, tokens=None, usage=None)` riceve tutti e due. Restano senza `cost`, scritte una per una: il taglio di `maxTurns` di `budget_cut_records` (nessuna trascrizione, solo `totalTokens`), l'interruzione (`subagents.interrupt`) e una trascrizione assente o illeggibile. **Un `cost` è cumulativo per agente**: un subagente ripreso rilegge tutta la trascrizione e registra un `cost` nuovo, come `subagents.tokens` che si sovrascrive. La fotografia prende per ogni agente l'ultimo `cost` (il `seq` più alto) e somma gli agenti; la pagina d'uso lo dice. La prova del Task 9 guarda se una ripresa scrive sulla stessa trascrizione (`resumes` e token): se no, la regola si corregge con una ruling. **Il costo del lavoro è la somma dei subagenti**: la sessione principale (il coordinatore) non ha `SubagentStop` e resta fuori, e la pagina d'uso lo scrive come limite. I dollari degli eval restano nel loro registro (`evals/cost.py`, `budget.tsv`): gli eval girano in uno stato a sé e non diventano eventi `cost` dello stato della macchina. Costo se sbagliata: la bacheca di C4 mostra token, non dollari; un listino con fonte e data è nel «Dopo C» (voce 7).
4. **Le fermate dagli hook di `AskUserQuestion`** (mia scelta: dal codice, senza token).
   - Due eventi d'ingresso nuovi, `pre_question` (`PreToolUse`) e `post_question` (`PostToolUse` e `PostToolUseFailure`), dallo strumento `AskUserQuestion`; non sono in `CONTROL_EVENTS`. **Un `PreToolUse` di `AskUserQuestion` non è un controllo nemmeno quando l'hook fallisce**: il wrapper `hooks/run` legge `tool_name` (come legge `session_id`) e mette `CONTROL=no` per `AskUserQuestion`; in `runner.run_hook` `control` vale vero per ogni `PreToolUse` dalla prima riga fino a `to_event` (`runner.py:203-218`), e in quel tratto possono negare l'input illeggibile, la scadenza e un errore generico (`:211-215`, `:339-352`): la regola si calcola quindi una volta, in testa, `control = hook_event in _CONTROL_HOOKS and not _asks_user(stdin_text)`, dove `_asks_user` guarda la prima occorrenza di `"tool_name"` nel testo grezzo e vale vero se il suo valore è `"AskUserQuestion"` (la stessa regola di `json_str` del wrapper, con un'espressione regolare); dopo `to_event` vale `event.kind in CONTROL_EVENTS`, falso per `pre_question`. Il wrapper lascia passare un'uscita 2 di Python così com'è (`hooks/run:206-208`): per questo serve anche la parte di `runner`. Così Python assente, un errore o la scadenza danno un avviso, mai il diniego della domanda (spec 7.1 nella rev 36). I matcher di `PreToolUse`, `PostToolUse` e `PostToolUseFailure` in `hooks/hooks.json` ricevono `AskUserQuestion`; `adapter` traduce `PostToolUseFailure` di `AskUserQuestion` in `post_question`.
   - Il controllo `tollgate_checks/stops.py` registra `stop_asked` con `{"tool_use_id", "questions": [{"header", "question", "options": [<etichette>]}]}` e `stop_answered` con `{"tool_use_id", "answers": {<domanda>: <risposta>} | null, "source": "tool_response" | "tool_input" | "failure" | "none"}` (`failure` quando l'evento viene da `PostToolUseFailure`: domanda rifiutata o interrotta).
   - Le risposte si cercano prima in `tool_response.answers`, poi in `tool_input.answers`; se non ci sono, `answers` è nullo con `source = "none"`. Ogni stringa è tagliata a `STOP_TEXT_MAX` (300) caratteri; al più 4 domande e 4 opzioni per domanda.
   - Il lavoro è `_common.governing_work(ctx, event.cwd)`, anche nullo. Senza `tool_use_id` (non dovrebbe succedere: i campioni degli hook lo hanno in `PreToolUse` e `PostToolUse`, `spikes/b1/raccogli.py:149`) `stop_asked` si registra con `tool_use_id` nullo e non conta mai in `waiting`. Il «caso della fermata» del progetto è l'`header` della domanda.
   - **L'evento `session_start`** si registra davvero: il controllo `checks/session.py` aggiunge `record("event", type="session_start", work=<ctx.work["id"] se ctx.work non è nullo, compreso il lavoro che lo stesso hook lega con bind; altrimenti nullo>, data={"source": <source dell'input, se c'è>})`. Il tipo esiste già nella spec e in `EVENT_TYPES`.
   - **Una domanda resta in attesa** (fotografia, decisione 8) se e solo se: non ha una `stop_answered` con lo stesso `tool_use_id`; è l'ultima `stop_asked` della sua sessione; e dopo di lei non c'è un evento `act` né `session_start` **dello stesso lavoro** (l'utente ha digitato un comando o ha aperto una sessione, anche nuova, sul lavoro). Gli eventi dei subagenti e degli hook non la chiudono. Una domanda rifiutata la chiude `PostToolUseFailure`; un turno interrotto senza un comando né una sessione dopo resta in attesa fino al primo dei due (costo accettato: un'attesa che dura troppo, non una persa). Limite: una sessione nuova aperta dalla radice del repo non è legata al `SessionStart`, quindi il suo `session_start` ha `work` nullo e non chiude niente, e la ripresa con `/tollgate:start` non è un atto; la domanda di una sessione chiusa resta aperta fino al primo atto sul lavoro o a un `SessionStart` in una sessione legata (`/clear`, compattazione). La pagina d'uso lo scrive. La fotografia guarda solo i lavori, quindi una domanda senza lavoro non vi compare.
   - Costo se sbagliata: se `tool_response` ha un'altra forma, le risposte restano nulle e la prova vera di C6 lo mostra; la domanda resta registrata.
5. **Il comando delle ruling** (progetto 6, «Come si registrano le ruling», «sul modello di `research submit`»): `tollgate ruling add [--task K] [--by agent|user]`, con il testo da stdin in un heredoc con il delimitatore `'RULING_FINE'` (`ruling_cmd.HEREDOC_END`), come la nota di ricerca. Il testo ha tre campi: solo una riga che comincia con `cosa:`, `perché:` (anche `perche:`) o `costo:` apre un campo; ogni altra riga continua il campo aperto (anche una riga «Nota: …»), e un testo non vuoto prima del primo campo è un problema. Gli argomenti di Bash restano senza testo libero: apostrofi, `$` e backtick dentro il heredoc citato non toccano `bash.parse` e il ramo che nega ai subagenti un comando non analizzabile (`cli_calls.py:103-114`).
   - Trova il lavoro dalla cartella (`sessions.work_for_path`). Senza lavoro, oppure con un task inesistente, è un rifiuto (uscita 2). `--by` vale `agent` per difetto; `user` serve al coordinatore per registrare una scelta che l'utente ha dato in chat.
   - Ogni campo è obbligatorio e non vuoto, al più `RULING_TEXT_MAX` (1000) caratteri: oltre, rifiuto con il limite (meglio un rifiuto di una ruling tagliata). Da stdin si legge al più `4 * 3 * RULING_TEXT_MAX + 1` caratteri. Un campo ripetuto o mancante è un rifiuto.
   - Registra `ruling` con `data` = `{"what", "why", "cost", "by", "task"}`, stampa `ruling registrata (evento <seq>)` ed esce con 0.
   - Non è un comando del coordinatore: un subagente lo può lanciare (`cli_calls` non cambia; un test lo fissa). Il brief dell'implementatore (`tollgate_analysis.brief`) e la skill `execute` lo citano in una riga.
   - Costo se sbagliata: una ruling registrata due volte resta due eventi; è storia, non stato.
6. **Le decisioni sui rilievi** (progetto 6, R13). Il codice le registra già tutte: `reviews.set_decision` è l'unico punto che scrive `user_decision` ed emette `finding` con la confidenza, la verifica e il motivo. C1 non aggiunge un tipo: aggiunge un test che scorre i sorgenti di `bin/` e fallisce se un'altra riga scrive `user_decision`, e un test che `approve finding` produce l'evento con i campi. Le tre forme del progetto si leggono così: **declassato** è `user_decision = downgraded:<gravità>`, **archiviato** è `dismissed`, **accettato** è l'assenza di `approve finding`: il rilievo resta confermato e si corregge, e lo dice l'evento `finding` della verifica (`verification = confirmed`, `user_decision` nullo), che `SubagentStop` registra già. Costo: nessuno; chi taratura vorrà distinguere «accettato» da «non ancora deciso» guarda se il ciclo successivo è chiuso.
7. **La storia non si cancella** (progetto 6; mia scelta sulla forma).
   - `[retention] events_days` vale `0` per difetto, e `0` vuol dire «mai». Un numero negativo è un errore di configurazione (oggi un `0` cancellerebbe ogni evento: la forma vecchia non aveva senso).
   - Con `events_days > 0`, `events.archive_and_prune(conn, state, now, days) -> tuple[int, Path | None]` scrive prima gli eventi più vecchi del limite in `<cartella di stato>/archive/events-<primo seq>-<ultimo seq>.jsonl` (stessa forma di `tollgate events`, con `fsutil.write_atomic`), poi cancella solo `seq <= ultimo seq` con `at` sotto il limite. Se la scrittura fallisce non cancella niente.
   - Le letture registrate (`lookups`) non sono eventi: una chiave nuova `[retention] lookups_days = 180` le pota come oggi.
   - Costo se sbagliata: il DB cresce; la pagina d'uso dice quanto (Task 8).
8. **La fotografia** (progetto 10): `tollgate snapshot`, in sola lettura, stampa un JSON `{"v": 1, "at", "host", "works": [...]}` con i lavori non chiusi di tutti i repo del DB.
   - Per lavoro: `repo_key`, `issue`, `level`, `level_cap`, `size`, `size_by`, `slices`, `phase`, `phase_before_block`, `branch`, `pr_number`, `tasks` (`{stato: numero}`), `turn`, `waiting_user`, `waiting` (`[{"kind", "id"}]`), `cost` (`{"tokens", "by_task": {numero: token}}`, con l'ultimo `cost` di ogni agente: decisione 3), `created`, `updated`, `last_event_at`.
   - **Nessun testo libero** (motivi dei blocchi, ruling, domande): la fotografia si può mostrare ovunque, e il testo sta negli eventi. Fa eccezione `branch`, che nasce dal titolo dell'issue (`naming.branch_name`): su GitHub si vede già, e resta.
   - `turn` viene da una funzione pura, `tollgate_analysis.turn.waiting_on(facts: TurnFacts) -> str`:
     - `decision` se c'è almeno una cosa che aspetta una scelta dell'utente (`waiting` non vuoto): un blocco aperto (`{"kind": "block", "id": blocks.id}`), un effetto in attesa (`intents` con `action = 'effect'` e `state = 'requested'`: `{"kind": "effect", "id": <data.id, l'id che l'utente digita in approve effect>}`; gli intenti `pr` e `sync` no), una domanda in attesa con la regola della decisione 4 (`{"kind": "question", "id": tool_use_id}`);
     - `user` se il passo dopo è dell'utente: fase `pr_open` (il merge) o `approval` (`approve plan`). In `spec_audit` il passo dopo può essere un giro degli agenti o `approve spec`, e saperlo vuole la logica dei giri di `audit`: C1 lo conta `agent`, e C4 lo può affinare con un campo nuovo;
     - `agent` negli altri casi.

     `waiting_user` è il numero di voci di `waiting`, più uno se `turn` è `user`.
   - Senza DB stampa `{"v": 1, "at", "host", "works": []}` e non crea niente.
   - Versione: un campo nuovo non cambia `v`, uno tolto o cambiato sì (progetto 10). C4 aggiunge `queue`, C5 `depends_on`.
   - Costo se sbagliata: un campo mancante si aggiunge senza cambiare la versione.
9. **La pagina per il gestionale**, `docs/uso/gestionale.md`: i due comandi di sola lettura (`events --after-seq`, `snapshot`), la busta, i tipi nuovi con i loro `data`, le regole di versione, l'archivio, e quanto occupano gli eventi. Il progetto 6 chiede la misura «sullo stato reale di B»: lo stato vero della macchina non si legge (regole di cautela), e le uniche copie dello stato nel repo sono quelle degli eval (fatti). La misura si fa quindi su tre copie degli stati degli eval di B8, copiate in una cartella `mkdtemp(prefix="tollgate-")` in `/tmp` cancellata alla fine (mai dentro il repo né nel workspace): numero di eventi, byte di `data` più busta, byte per evento. La pagina dice che gli eval sono lavori corti e che i byte per evento servono a stimare un lavoro vero. Costo: la stima è meno precisa di una misura sullo stato reale.
10. **`sync` non nasce in C1** (piano principale, decisione 2). Costo: nessuno.
11. **La prova reale corta** (piano principale, decisione 6), con `spikes/run-b1-flow.sh` nel caso predefinito (L1, `rules-base` vera): `registra` stampa anche gli eventi `size_decided`, `cost` e `ruling` e salva `snapshot.json` con lo stesso ambiente di `status --json` (lo stato di prova, mai quello della macchina). Si guarda che il lavoro abbia la taglia all'avvio e dopo il piano, e un `cost` per subagente con `by_model` non vuoto. Le fermate non si vedono con `claude -p` (fatti): restano alla prova vera di C6. Costo: circa 1-2 USD equivalenti sull'abbonamento.
12. **Spec del nucleo, revisione 36** (Task 10): 3.1 (`ruling add`, `snapshot`), 3.2 (l'elenco chiuso degli eventi d'ingresso: `pre_question`, `post_question`), 6.1 (riga della taglia), 7.1 (`PreToolUse` di `AskUserQuestion` non è un controllo), 7.2 (gli hook di `AskUserQuestion`; `session_start` registrato), 8.4 (`approve size`), 11.4 (`[retention]`), 12.2 (colonne nuove, `events` non più potata per difetto), 18.4 (tipi e `data`), 20. La riga `**Tipi:**` di 18.4 cambia già nel Task 1.

## Review Focus

1. **Un hook su `AskUserQuestion` che solleva** o nega: deve registrare o tacere, mai fermare la domanda (un `pre_question` che nega spegnerebbe le fermate dell'utente), anche con Python assente, un errore del programma o la scadenza. Test nel Task 6: input senza `questions`, con `questions` non lista, con stringhe enormi, senza DB; `test_ask_user_question_never_denied_by_failure` sul wrapper.
2. **La potatura che perde eventi**: un errore di scrittura dell'archivio, un disco pieno, due `start` insieme. Test nel Task 2: scrittura che fallisce → nessuna cancellazione; due chiamate di fila → secondo archivio vuoto e nessuna cancellazione doppia; lettura, scrittura e cancellazione nella stessa transazione `BEGIN IMMEDIATE` (`db.tx`), così un secondo processo aspetta e non riscrive gli stessi eventi.
3. **Una taglia che scende da sola o diventa grande senza un sì**: piano riscritto dopo `reopen plan` con meno task; piano L1 con `## Fette previste` a tre voci. Test nel Task 3 e nel Task 4.
4. **Un lavoro nato prima di C1** (taglia nulla) in `approve spec`, nella fotografia, in `reopen plan`: niente errori, nessun ricalcolo silenzioso. Test nei Task 3, 4 e 8.
5. **La fotografia con testo libero o dati della macchina oltre `host`**: nessun motivo di blocco, nessun percorso del worktree. Test nel Task 8 che scorre il JSON e fallisce su `worktree`, `reason`, `what`, `question`.

## Mappa dei file

| File | Task |
|---|---|
| `bin/tollgate_core/db.py`, `bin/tollgate_core/events.py`, spec 18.4 (riga `**Tipi:**`) | 1 |
| `bin/tollgate_core/config.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/lookups.py` (solo il chiamante), `bin/tollgate_flow/housekeeping.py`, `bin/tollgate_core/paths.py` (se serve la cartella `archive`) | 2 |
| `bin/tollgate_analysis/worksize.py` (nuovo), `bin/tollgate_core/sizes.py` (nuovo), `bin/tollgate_flow/start.py`, `bin/tollgate_checks/post_edit.py`, `bin/tollgate_hooks/apply.py` (operazioni `plan` e `level`), `bin/tollgate_flow/l2acts.py` (`approve_plan`), `bin/tollgate_flow/adopt.py` | 3 |
| `bin/tollgate_flow/l2acts.py` (`approve_spec`), `bin/tollgate_core/acts.py`, `bin/tollgate_checks/acts.py`, `bin/tollgate_flow/actapply.py`, `skills/approve/SKILL.md`, `docs/uso/comandi.md` | 4 |
| `bin/tollgate_flow/ruling_cmd.py` (nuovo), `bin/tollgate_core/cli.py`, `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py`, `skills/execute/SKILL.md` | 5 |
| `bin/tollgate_hooks/model.py`, `bin/tollgate_hooks/adapter.py`, `bin/tollgate_hooks/runner.py`, `hooks/hooks.json`, `hooks/run`, `bin/tollgate_checks/stops.py` (nuovo), `bin/tollgate_checks/session.py` | 6 |
| `bin/tollgate_analysis/report.py`, `bin/tollgate_checks/subagent_stop.py`, `task_verdict.py`, `final_review.py`, `audit_round.py`, `bin/tollgate_hooks/apply.py`, `bin/tollgate_core/subagents.py` | 7 |
| `bin/tollgate_analysis/turn.py` (nuovo), `bin/tollgate_core/snapshot.py` (nuovo), `bin/tollgate_core/cli.py`, `docs/uso/gestionale.md` (nuovo), `docs/uso/comandi.md` | 8 |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `tests/test_b1_scripts.py`, `docs/verifiche/2026-11-20-c1-prova-flusso.md`, `docs/verifiche/evidenze/c1/` | 9 |
| spec del nucleo, progetto di C, piano principale di C | 10 |

### Task 1: Migrazione 7 e tipi di evento nuovi

**Files:**
- Modify: `bin/tollgate_core/db.py` (`SCHEMA_V7`, `MIGRATIONS`), `bin/tollgate_core/events.py` (`EVENT_TYPES`), spec del nucleo 18.4 (solo la riga `**Tipi:**`)
- Test: `tests/test_db.py` (anche `test_latest_version_is_6`, `:198-199`, che diventa `…_is_7`), `tests/test_events.py`

**Interfaces:**
- Produces: colonne `work_items.size`, `size_by`, `slices`; `db.latest_version() == 7`; tipi `size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost` in `events.EVENT_TYPES`.

- [ ] **Step 1: test che falliscono**
  - `test_migration_7_adds_size_columns`: dopo `open_db` su un DB nuovo `PRAGMA table_info(work_items)` ha `size`, `size_by`, `slices`; `latest_version() == 7`.
  - `test_migration_7_from_6_keeps_rows_and_backs_up`: un DB alla versione 6 con un lavoro migra a 7, il lavoro ha `size` nullo, esiste una copia `tollgate-*-migrazione-7.db`.
  - `test_size_check_constraint`: `UPDATE work_items SET size = 'enorme'` solleva `sqlite3.IntegrityError`; lo stesso per `size_by = 'modello'`.
  - `test_new_event_types_recorded`: per ogni tipo nuovo `record_event` restituisce un `seq` e `export_events` lo riporta con `v == 1`.
- [ ] **Step 2:** `python3 -B -m unittest tests.test_db tests.test_events` → FAIL (colonne e tipi mancanti).
- [ ] **Step 3:** `SCHEMA_V7` con le tre istruzioni della decisione 1, `(7, SCHEMA_V7)` in `MIGRATIONS`; i cinque tipi in `EVENT_TYPES`; la riga `**Tipi:**` di 18.4 con i cinque nomi tra backtick (il resto della spec lo scrive il Task 10).
- [ ] **Step 4:** gli stessi test e `tests.test_docs` → PASS; poi `tests/run`.
- [ ] **Step 5: commit** `tollgate C1: migrazione 7 e tipi di evento della taglia, delle ruling, delle fermate e del costo`.

### Task 2: La storia che non si cancella

**Files:**
- Modify: `bin/tollgate_core/config.py` (`DEFAULTS["retention"]`, controllo dei valori), `bin/tollgate_core/events.py` (`archive_and_prune`, `prune_events` resta per i test esistenti o diventa un involucro), `bin/tollgate_flow/housekeeping.py`. Il modello `templates/tollgate.toml` **non** cambia (non ha `[retention]`, e cambiarlo cambierebbe ciò che `init` copia): il significato di `0` e l'archivio li dicono la spec 11.4 (Task 10) e `docs/uso/gestionale.md` (Task 8)
- Test: `tests/test_config.py`, `tests/test_events.py`, `tests/test_start.py` (pulizie di `start`: `test_prune_events_error_does_not_skip_prune_bound`, `:1209`, simula un errore di `events.prune_events` e va spostato su `archive_and_prune` con `events_days > 0`; `test_malformed_sessions_do_not_skip_other_cleanups`, `:1188-1207`, si aspetta che un evento di 200 giorni sparisca con la configurazione caricata: riceve un `tollgate.toml` del repo di prova con `[retention] events_days = 180`, e allora l'evento va nell'archivio)

**Interfaces:**
- Produces: `events.archive_and_prune(conn, state, now, days: int) -> tuple[int, Path | None]` (eventi cancellati, file d'archivio o `None`); `events.ARCHIVE_DIR = "archive"`; chiavi `retention.events_days` (predefinito 0) e `retention.lookups_days` (predefinito 180).

- [ ] **Step 1: test che falliscono**
  - `test_events_days_default_is_never`: `Config` predefinita → `get("retention.events_days") == 0`, `get("retention.lookups_days") == 180` (sostituisce l'asserzione `180` di `tests/test_config.py:23`).
  - `test_events_days_negative_is_config_error`: `events_days = -1` → `ConfigError` con `retention.events_days` nel messaggio.
  - `test_housekeeping_never_prunes_with_zero`: eventi di 400 giorni fa, `housekeeping.run` con la configurazione predefinita → nessuna cancellazione, nessun file in `archive/`.
  - `test_archive_then_prune`: con `days = 30` e tre eventi vecchi e due nuovi, il file `archive/events-<s1>-<s3>.jsonl` ha tre righe uguali a `to_jsonl(export_events(...))` di quei tre, nel DB restano i due nuovi, il risultato è `(3, <percorso>)`.
  - `test_archive_write_failure_deletes_nothing`: `fsutil.write_atomic` che solleva `OSError` → l'errore risale (in `housekeeping` diventa l'avviso «pulizia non riuscita (eventi)») e il DB ha ancora tutti gli eventi.
  - `test_archive_twice_is_noop`: una seconda chiamata subito dopo → `(0, None)`.
  - `test_archive_holds_write_lock`: durante la scrittura del file (un `write_atomic` finto che controlla `conn.in_transaction`) la transazione è aperta.
  - `test_lookups_use_lookups_days`: `lookups.prune` riceve `days = lookups_days`, non `events_days`.
- [ ] **Step 2:** `python3 -B -m unittest tests.test_config tests.test_events tests.test_start` → FAIL.
- [ ] **Step 3:** la decisione 7. `archive_and_prune` legge gli eventi con `at < limite` ordinati per `seq`; senza eventi restituisce `(0, None)` senza toccare il disco; scrive il file con `fsutil.write_atomic` sotto `state.root / ARCHIVE_DIR` (creata con i permessi della cartella di stato); poi `DELETE FROM events WHERE seq <= ? AND at < ?`; lettura, scrittura del file e cancellazione stanno in un solo `db.tx(conn)` (lucchetto di scrittura preso subito), e se la scrittura solleva la transazione si annulla. `housekeeping.run` la chiama solo con `days > 0`. Il valore negativo si controlla dove `config` valida le chiavi (`_set_key` o un controllo dopo l'unione).
- [ ] **Step 4:** test del task → PASS; `tests/run`.
- [ ] **Step 5: commit** `tollgate C1: gli eventi non si cancellano per difetto; archivio prima della potatura`.

### Task 3: La presa della taglia, all'avvio e al piano

**Files:**
- Create: `bin/tollgate_analysis/worksize.py`, `bin/tollgate_core/sizes.py`
- Modify: `bin/tollgate_flow/start.py` (`_create`), `bin/tollgate_checks/post_edit.py` (`_plan`), `bin/tollgate_hooks/apply.py` (operazioni `plan` e `level`), `bin/tollgate_flow/l2acts.py` (`approve_plan`), `bin/tollgate_flow/adopt.py` (`_register_plan`)
- Test: `tests/test_worksize.py` (nuovo), `tests/test_sizes.py` (nuovo), `tests/test_start.py`, `tests/test_check_post_edit.py` (piano e livello dagli hook: `test_plan_registration_decides_size`, `test_l1_plan_with_three_slices_stays_medium`, `test_plan_after_reopen_does_not_shrink`, `test_reopen_plan_on_pre_c1_work`, `test_level_rise_raises_size`), `tests/test_l2acts.py`, `tests/test_adopt.py`

**Interfaces:**
- Produces:
  - `worksize.SIZES = ("small", "medium", "large")`, `worksize.LABELS = {"small": "piccolo", "medium": "medio", "large": "grande"}`, `MEDIUM_MIN_TASKS = 4`, `MEDIUM_MIN_AREAS = 2`;
  - `worksize.Signals(level: str, tasks: int, areas: int, slices: int)` e `worksize.Proposal(size: str, reason: str)` (`NamedTuple`);
  - `worksize.propose(signals: Signals) -> Proposal`, `worksize.areas(paths, profiles: dict[str, dict]) -> int`;
  - `worksize.Preview(applied: str, line: str)` e `worksize.preview(signals: Signals, current: str | None, current_by: str | None, *, cause: str, confirmed: bool = False) -> Preview`: la regola «mai giù, `large` solo con `approve spec <n>`, la taglia dell'utente resta» e la riga per l'utente (`taglia: medio — piano con 6 task su 2 aree`; con la proposta grande non applicata, la riga che indica la spec L2 e `approve spec <n>`);
  - `sizes.decide(conn, work: int, signals: Signals, *, cause: str, confirmed: bool = False, now, session=None) -> str`: chiama `preview` con la taglia della riga, registra `size_decided`, scrive `size` e `size_by` se `applied` è cambiata, restituisce `preview(...).line`;
  - `sizes.set_by_user(conn, work: int, size: str, reason: str, *, now, session=None) -> str` (lo usa il Task 4; registra con `cause = "act"`);
  - `sizes.CAUSES = ("start", "plan", "level", "approve_spec", "act")`; `decide` rifiuta `act`, che è solo di `set_by_user`.
- Consumes: le colonne del Task 1.

- [ ] **Step 1: test che falliscono** (`tests/test_worksize.py`, puri)
  - `test_small_by_default`: `propose(Signals("L1", 3, 1, 1)).size == "small"`.
  - `test_medium_thresholds`: `Signals("L1", 4, 1, 1)`, `Signals("L1", 1, 2, 1)`, `Signals("L2", 0, 0, 1)` → `medium`; `Signals("L0", 3, 1, 1)` → `small`.
  - `test_large_with_slices`: `Signals("L1", 1, 1, 3)` → `large`, motivo con «3 fette».
  - `test_reason_names_the_signals`: il motivo di `Signals("L1", 6, 2, 1)` contiene «6 task» e «2 aree».
  - `test_areas_counts_verticals_only`: con due profili (`ai` su `ai/**`, `infra` su `/vercel.json`) e i percorsi `ai/a.py`, `ai/b.py`, `vercel.json`, `README.md` → 2.
  - `test_preview_rules`: `preview(Signals("L1", 1, 1, 3), "small", "rules", cause="plan")` → `applied == "medium"` e la riga nomina `approve spec`; con `cause="approve_spec", confirmed=True` → `large`; `preview(Signals("L2", 9, 3, 1), "small", "user", cause="plan")` → `small` e la riga contiene «piccolo», «scelta dall'utente» e «medio»; `preview(Signals("L1", 1, 1, 3), "small", "user", cause="approve_spec", confirmed=True).applied == "large"`; `preview(Signals("L2", 5, 1, 3), "large", "rules", cause="plan")` → `large` e la riga senza «resta medio»; `preview(Signals("L1", 1, 1, 3), "large", "user", cause="plan")` → `large` e la riga senza «resta medio»; `preview(Signals("L1", 1, 1, 3), "small", "user", cause="plan")` → `small`, la riga contiene «piccolo» e «scelta dall'utente» e non contiene «resta medio».
- [ ] **Step 2: test che falliscono** (`tests/test_sizes.py`, con `TempState`)
  - `test_decide_records_event_and_sets_size`: su un lavoro nuovo `decide(..., Signals("L1", 0, 0, 1), cause="start")` → `size = 'small'`, `size_by = 'rules'`, un evento `size_decided` con `proposed`, `applied`, `previous` nullo, `signals`, `confirmed` nullo.
  - `test_never_goes_down`: `medium` poi una proposta `small` → resta `medium`, l'evento ha `applied == "medium"` e `proposed == "small"`.
  - `test_large_needs_a_yes`: proposta `large` con `cause="plan"` → `size = 'medium'`, la riga contiene `/tollgate:approve spec`; con `cause="approve_spec", confirmed=True` → `large` e `confirmed` vero.
  - `test_user_size_is_fixed`: `set_by_user(..., "small", "motivo")` su un lavoro `medium` → `small`, `size_by = 'user'`, evento con `cause == "act"`, `by == "user"`, `confirmed` vero; poi `decide` con proposta `medium` → resta `small`, l'evento ha `proposed == "medium"`, `applied == "small"`, `by == "user"`; poi `decide(..., Signals("L2", 0, 0, 3), cause="approve_spec", confirmed=True)` → `large`.
  - `test_decide_rejects_unknown_cause`: `cause="altro"` e `cause="act"` → `ValueError`.
  - `test_decide_line_equals_preview`: per tre casi la riga restituita da `decide` è uguale a `preview(...).line` calcolata con la taglia di prima.
- [ ] **Step 3: test che falliscono** (punti di chiamata)
  - `test_start_new_work_has_size_line` (`tests/test_start.py`): un lavoro nuovo L1 → `size = 'small'`, una riga `taglia: piccolo — …` prima di `prossimo passo:`; L2 → `medio`. La ripresa non registra un secondo `size_decided`.
  - `test_plan_registration_decides_size` (`tests/test_check_post_edit.py`): un piano L1 con 5 task registrato dall'hook → `size = 'medium'`, e l'iniezione ha la stessa riga che `decide` ha restituito (`taglia: medio — …`).
  - `test_l1_plan_with_three_slices_stays_medium` (Review Focus 3): un piano L1 con `## Fette previste` a tre voci → `medium`, riga con `approve spec`.
  - `test_plan_after_reopen_does_not_shrink` (Review Focus 3): `medium`, `reopen plan`, un piano di 1 task → resta `medium`.
  - `test_reopen_plan_on_pre_c1_work` (Review Focus 4): un lavoro con `size` nullo, `reopen plan` → nessun errore e nessun `size_decided`; il piano nuovo registrato dà la taglia.
  - `test_level_rise_raises_size`: un lavoro L1 `small` che sale a L2 con l'operazione `level` degli hook → `medium`, evento con `cause == "level"`; un `approve level` che abbassa non chiama `decide`.
  - `test_approve_plan_decides_size` (`tests/test_l2acts.py`): un evento `size_decided` con `cause = "plan"`.
  - `test_adopt_decides_size` (`tests/test_adopt.py`): un lavoro adottato ha `size` con un evento `cause = "start"`; con un piano registrato anche `cause = "plan"`; con il `spec-approval.md` corrente della stessa issue a tre fette `slices = 3`, `size = 'large'` e un evento `cause = "approve_spec"` con `confirmed` vero; la fetta 2 adottata con l'approvazione della fetta 1 (`_approved_elsewhere`) → `slices` nullo, `medium`, nessun evento `approve_spec`. Le righe di `adopt` finiscono ancora con `prossimo passo: EnterWorktree …` (`tests/test_adopt.py:106`): la riga della taglia va prima.
- [ ] **Step 4:** i file di test del task → FAIL.
- [ ] **Step 5:** `worksize` e `sizes` con le firme sopra (`sizes` importa `worksize`: `tollgate_core` può importare `tollgate_analysis`). In `start._create`, dopo `create_work`, `sizes.decide` con `cause="start"` in un `steps.run` messo prima di `incomplete = steps.failed` (`start.py:509-510`), così un errore diventa «registrazione incompleta» come le altre; la sua riga va tra le righe finali, prima di `prossimo passo:`. In `post_edit.decide` `level_records` passa prima di `_plan`, come dice la decisione 2, e `_plan(ctx, work, wt, rel, new_level)` riceve il livello (la lista dei record resta in una variabile con un altro nome, per esempio `level_out`). `new_level` serve **solo** al record `plan` e a `preview`: `check_plan(level=work["level"])` e la scelta tra il ramo L1 (`record("plan")`) e il ramo L2 (`plan_path`) restano sul livello di prima, come oggi, e la riga della taglia si aggiunge solo nel ramo L1, dove c'è una registrazione. In `post_edit._plan` la registrazione porta anche `level`, `areas` (calcolato con `worksize.areas(r.scope, ctx.config.profiles)`) e `slices` (`specdoc.slices(text)`), e l'iniezione aggiunge `worksize.preview(...).line` calcolata con `work["size"]` e `work["size_by"]`; l'operazione `plan` di `apply` chiama `sizes.decide` dopo `register_plan` nella stessa chiamata; `approve_plan` e `adopt._register_plan` fanno lo stesso con la loro configurazione. L'operazione `level` di `apply`, dopo `phases.set_level`, chiama `sizes.decide` con `cause="level"` solo se il livello è salito. In `adopt`, in un `step("taglia", …)` subito dopo `create_work` e prima di `_register_plan` (`adopt.py:362-383`: un errore diventa «registrazione incompleta» e l'ordine degli eventi è fisso), `decide` con `cause="start"`; con l'approvazione corrente **della stessa issue** letta da `adopt` (non quella di `_approved_elsewhere`, `:215-240`) e `slices > 1` nell'intestazione, `UPDATE work_items SET slices` e `decide` con `cause="approve_spec", confirmed=True`. Per saperlo, `_Evidence` riceve un campo `spec_own: bool`, vero solo quando `spec_header` viene da `approvals.approval_paths(issue)[0]` e non da `_approved_elsewhere`. Nessuna operazione nuova in `apply._OPS`.
- [ ] **Step 6:** test del task → PASS; `tests/run`.
- [ ] **Step 7: commit** `tollgate C1: la taglia del lavoro, proposta all'avvio e alla registrazione del piano`.

### Task 4: La taglia grande con `approve spec` e l'atto `approve size`

**Files:**
- Modify: `bin/tollgate_flow/l2acts.py` (`approve_spec`), `bin/tollgate_core/acts.py` (`APPROVE_OBJECTS`), `bin/tollgate_checks/acts.py` (`_TARGET_ARG`), `bin/tollgate_flow/actapply.py` (`APPLIERS` e il messaggio di `_pick`, `:268-269`, che elenca gli oggetti), `skills/approve/SKILL.md` (anche `argument-hint`), `docs/uso/comandi.md` (`test_every_skill_documented`, `tests/test_docs.py:79-95`, lega la pagina all'`argument-hint`)
- Test: `tests/test_l2acts.py`, `tests/test_acts.py`, `tests/test_check_acts.py`, `tests/test_actapply.py`, `tests/test_docs.py`, `tests/test_skill_contract.py` (se fissa gli oggetti della skill)

**Interfaces:**
- Consumes: `sizes.decide`, `sizes.set_by_user`, `worksize.LABELS` (Task 3).
- Produces: `work_items.slices` scritto da `approve spec`; l'atto `approve size <piccolo|medio|grande> <motivo>`.

- [ ] **Step 1: test che falliscono**
  - `test_approve_spec_records_slices_and_large`: spec con tre fette, `approve spec 3` → `work_items.slices = 3`, `size = 'large'`, evento `size_decided` con `cause = "approve_spec"` e `confirmed` vero; l'uscita ha la riga `taglia: grande — …` e continua come oggi (fase `plan`, proposta delle issue).
  - `test_approve_spec_single_slice_keeps_size`: `approve spec 1` su un lavoro L2 `medium` → `slices = 1`, resta `medium`.
  - `test_approve_spec_on_pre_c1_work` (Review Focus 4): lavoro con `size` nullo → nessun errore, `size` calcolata da `approve spec` (è una chiamata di `decide`, non un ricalcolo silenzioso).
  - `test_approve_size_act`: l'atto `approve size medio "piano più grande del previsto"` → `act apply` dà una riga con «medio», `size = 'medium'`, `size_by = 'user'`; `approve size enorme x` → rifiuto con i tre valori ammessi; senza motivo → rifiuto; l'atto si consuma sempre (spec 8.4).
  - `test_size_is_target_arg`: in `tests/test_check_acts.py` il target dell'atto `approve size medio x` è `medio`.
- [ ] **Step 2:** test del task → FAIL.
- [ ] **Step 3:** in `approve_spec`, dopo `set_phase`: `UPDATE work_items SET slices = ?` e `sizes.decide` con `Signals(level, <task registrati>, 0, slices)`, `cause="approve_spec"`, `confirmed = slices > 1`; la riga della taglia va nell'uscita prima di «Committa …». `"size"` in `APPROVE_OBJECTS` e in `_TARGET_ARG`; `actapply._approve_size` sul modello di `_approve_level` (parole italiane → nomi del codice con `worksize.LABELS` invertito; motivo obbligatorio). La skill `approve` elenca `size` con un esempio.
- [ ] **Step 4:** test del task → PASS; `tests/run`.
- [ ] **Step 5: commit** `tollgate C1: taglia grande con approve spec e atto approve size`.

### Task 5: Il comando `ruling add`

**Files:**
- Create: `bin/tollgate_flow/ruling_cmd.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `ruling`), `bin/tollgate_analysis/brief.py` (campo `ImplBrief.ruling_cmd` e una riga nel brief dell'implementatore), `bin/tollgate_flow/taskcmd.py` (riempie `ruling_cmd` come `verify_cmd`), `skills/execute/SKILL.md` (una riga per il coordinatore), `docs/uso/comandi.md`
- Test: `tests/test_ruling_cmd.py` (nuovo), `tests/test_cli.py`, `tests/test_check_cli_calls.py`, `tests/test_brief.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Produces: `ruling_cmd.parse_text(text: str) -> tuple[dict[str, str] | None, list[str]]` (i tre campi `what`, `why`, `cost` dalle righe `cosa:`, `perché:`/`perche:`, `costo:`, oppure i problemi); `ruling_cmd.add(state, cwd: Path, text: str, *, task: int | None, by: str, now=None) -> RulingResult` con `RulingResult(code: int, lines: list[str])`; `OK, REFUSED = 0, 2`; `RULING_TEXT_MAX = 1000`; `HEREDOC_END = "RULING_FINE"`; `ruling_cmd.BY = ("agent", "user")`; `ruling_cmd.command(program: str, task: int | None) -> str` (il heredoc da copiare, come `research.submit_command`).

- [ ] **Step 1: test che falliscono**
  - `test_parse_text`: `"cosa: usa la copia\nperché: l'utente non c'è\ncosto: nessuno"` → i tre campi, apostrofi intatti; un campo su due righe → unito; `perche:` accettato; una riga `Nota: vedi sopra` dopo `cosa:` resta dentro `what`; un campo mancante o ripetuto, o un testo prima del primo campo (`chi: x` come prima riga) → problemi, nessun campo.
  - `test_add_records_event`: dal worktree di un lavoro, `add(..., <testo con i tre campi>, task=None, by="agent")` → codice 0, riga `ruling registrata (evento <seq>)`, evento `ruling` con `data == {"what", "why", "cost", "by", "task": None}` e `work` del lavoro.
  - `test_add_with_task`: `task=2` su un lavoro con il task 2 → `data["task"] == 2`; `task=9` inesistente → codice 2.
  - `test_add_without_work_refused`: da una cartella fuori dai worktree → codice 2, «nessun lavoro attivo per questa cartella».
  - `test_add_rejects_empty_and_long_text`: un campo vuoto o di soli spazi → codice 2; uno di `RULING_TEXT_MAX + 1` caratteri → codice 2 con il limite nel messaggio; nessun evento.
  - `test_cli_ruling_add`: `tollgate ruling add --by user` con il testo su stdin → uscita 0; `--by modello` → errore di argparse (uscita 2).
  - `test_subagent_may_add_ruling` (`tests/test_check_cli_calls.py`): un `pre_bash` con `agent_id` e il comando di `ruling_cmd.command(...)` con un testo che contiene apostrofi, `$`, un backtick e le parole `task`, `review` e `start` (che `cli_calls.py:103-114` nega in un comando non analizzabile) non è negato; lo stesso dalla sessione principale.
  - `test_implementer_brief_mentions_ruling` (`tests/test_brief.py`): con `ruling_cmd` pieno il brief contiene `ruling add`, `--task` e `RULING_FINE`; senza, nessuna riga. In `tests/test_taskcmd.py` il brief scritto da `task start` contiene il programma quotato seguito da `ruling add`.
- [ ] **Step 2:** test del task → FAIL.
- [ ] **Step 3:** `ruling_cmd.add` sul modello di `research_cmd` (`db.open_db`, `sessions.work_for_path`, `tasks.get_task`, `events.record_event`; il DB si chiude sempre). In `cli.py` il sottocomando `ruling` con `add`, `--task` e `--by` (con `choices`), il testo da `sys.stdin.read(4 * 3 * RULING_TEXT_MAX + 1)`, righe su stdout con 0 e su stderr con 2. `ImplBrief` riceve `ruling_cmd: str | None = None` (`tollgate_analysis` non importa il nucleo: il testo del comando lo compone `taskcmd` con `paths.program_command`, come `verify_cmd`); con il campo pieno il brief ha una riga e il heredoc di `ruling_cmd.command(program, k)`: quando decidi qualcosa che il piano non dice, registralo così. La skill `execute` dice lo stesso al coordinatore, con `--by user` per una scelta data dall'utente in chat. `docs/uso/comandi.md` ha la voce del comando.
- [ ] **Step 4:** test del task → PASS; `tests/run`.
- [ ] **Step 5: commit** `tollgate C1: comando ruling add per le decisioni prese al posto dell'utente`.

### Task 6: Le fermate dagli hook di `AskUserQuestion`

**Files:**
- Create: `bin/tollgate_checks/stops.py`
- Modify: `bin/tollgate_hooks/model.py` (`INPUT_EVENTS`), `bin/tollgate_hooks/adapter.py` (`_PRE`, `_POST`, ramo di `PostToolUseFailure`), `hooks/hooks.json` (matcher di `PreToolUse`, `PostToolUse` e `PostToolUseFailure`), `hooks/run` (`CONTROL=no` per `AskUserQuestion`), `bin/tollgate_hooks/runner.py` (`control` dal nome dello strumento), `bin/tollgate_checks/session.py` (evento `session_start`)
- Test: `tests/test_check_stops.py` (nuovo), `tests/test_wrapper.py`, `tests/test_check_session.py`, `tests/test_hook_engine.py` (le mappe dell'adattatore, vicino alle righe 135-170: `test_adapter_maps_ask_user_question` e il caso `PostToolUseFailure`), `tests/test_manifest.py` (matcher di `hooks.json`)

**Interfaces:**
- Produces: eventi d'ingresso `pre_question` e `post_question`; `stops.STOP_TEXT_MAX = 300`; `stops.MAX_QUESTIONS = 4`, `stops.MAX_OPTIONS = 4`; eventi `stop_asked` e `stop_answered` con i `data` della decisione 4.

- [ ] **Step 1: test che falliscono**
  - `test_adapter_maps_ask_user_question`: un input `PreToolUse` con `tool_name = "AskUserQuestion"` diventa `pre_question`; `PostToolUse` diventa `post_question`.
  - `test_hooks_json_matches_ask_user_question`: i matcher di `PreToolUse`, `PostToolUse` e `PostToolUseFailure` contengono `AskUserQuestion`; `pre_question` non è in `CONTROL_EVENTS`; `PostToolUseFailure` di `AskUserQuestion` diventa `post_question`, e quello di `Read` resta `None`.
  - `test_stop_answered_on_failure`: `post_question` da `PostToolUseFailure` → `stop_answered` con `source == "failure"` e `answers` nullo.
  - `test_stop_asked_recorded`: due domande con `header`, `question` e tre opzioni → un evento `stop_asked` con `tool_use_id`, i due `header`, le etichette.
  - `test_stop_answered_from_tool_response`: `tool_response = {"questions": [...], "answers": {"D?": "Sì"}}` → `stop_answered` con `answers == {"D?": "Sì"}`, `source == "tool_response"`.
  - `test_stop_answered_from_tool_input` e `test_stop_answered_without_answers`: risposte solo in `tool_input.answers` → `source == "tool_input"`; nessuna → `answers` nullo, `source == "none"`.
  - `test_stop_texts_truncated`: una domanda di 5000 caratteri e 6 domande → testi di al più `STOP_TEXT_MAX`, 4 domande.
  - `test_stops_never_deny_or_raise` (Review Focus 1): `questions` assente, non lista, elementi non dizionari, `tool_response` stringa → nessun `deny`, nessuna eccezione; con `questions` illeggibile nessun evento; senza `tool_use_id` → `stop_asked` con `tool_use_id` nullo, che la fotografia non conta in `waiting`.
  - `test_ask_user_question_never_denied_by_failure` (`tests/test_wrapper.py`): un `PreToolUse` di `AskUserQuestion` con Python assente, con un'uscita 1 del programma e allo scadere → uscita 0 con l'avviso; lo stesso con `Bash` resta 2. In `runner` (`tests/test_hook_engine.py`): stdin `{"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", ` (JSON troncato) → uscita 0 con l'avviso; lo stesso troncato con `"tool_name": "Bash"` → uscita 2.
  - `test_session_start_recorded` (`tests/test_check_session.py`): un `SessionStart` in una sessione legata registra `session_start` con il lavoro; in una sessione nuova con `cwd` nel worktree (che lo stesso hook lega) con il lavoro; fuori da ogni worktree con `work` nullo.
  - `test_stop_event_has_work_when_bound`: in una sessione legata a un lavoro l'evento ha `work`; fuori da un lavoro `work` è nullo.
- [ ] **Step 2:** test del task → FAIL.
- [ ] **Step 3:** la decisione 4. `stops.py` con `CHECK = {"api": 1, "events": ["pre_question", "post_question"], "component": None, "order": 50}` e `decide(event, ctx)` che restituisce al più un `record("event", type=…, data=…, work=…)`. `model.INPUT_EVENTS` e `adapter` con `AskUserQuestion` nelle due mappe; `hooks.json` con `AskUserQuestion` aggiunto ai tre matcher; `stops` riconosce la provenienza da `event.hook_event == "PostToolUseFailure"`.
- [ ] **Step 4:** test del task → PASS; `tests/run`.
- [ ] **Step 5: commit** `tollgate C1: le domande dirette all'utente e le risposte negli eventi`.

### Task 7: Il costo dei subagenti e le decisioni sui rilievi

**Files:**
- Modify: `bin/tollgate_analysis/report.py` (`transcript_usage`), `bin/tollgate_checks/_common.py` (`transcript_cost`, `tampered_records(..., *, tokens=None, usage=None)`), `bin/tollgate_checks/subagent_stop.py` (`_readonly` riceve l'evento), `task_verdict.py`, `final_review.py`, `audit_round.py` (ogni `subagent_finish` con una trascrizione porta `tokens` e `usage`), `bin/tollgate_hooks/apply.py` (operazione `subagent_finish`), `bin/tollgate_core/subagents.py` (`finish`)
- Test: `tests/test_report.py`, `tests/test_check_common.py`, `tests/test_check_subagent_stop.py`, `tests/test_check_task_verdict.py`, `tests/test_check_final_review.py`, `tests/test_check_audit_round.py`, `tests/test_subagents.py`, `tests/test_reviews.py`

**Interfaces:**
- Produces: `report.transcript_usage(path) -> dict[str, dict[str, int]]` (per modello: `input`, `cache_creation`, `cache_read`, `output`; un messaggio contato una volta, come `transcript_tokens`; modello assente → chiave `"sconosciuto"`); `subagents.finish(..., usage: dict | None = None)` registra `cost` dopo `subagent_stop` quando `usage` non è `None`.

- [ ] **Step 1: test che falliscono**
  - `test_transcript_usage_by_model`: una trascrizione con due messaggi di `claude-sonnet-5-5` (uno ripetuto con lo stesso `id`) e uno senza `model` → due chiavi, il messaggio ripetuto contato una volta, `cache_read` presente; la somma di `input + cache_creation + output` è uguale a `transcript_tokens` sullo stesso file.
  - `test_transcript_usage_missing_file`: percorso inesistente → `{}`.
  - `test_cost_event_on_finish`: `subagents.finish(..., tokens=10, usage={"m": {...}})` → dopo `subagent_stop` un evento `cost` con `agent`, `type`, `task`, `tokens == 10`, `by_model`, `usd` nullo, `source == "transcript"`.
  - `test_no_cost_without_usage`: `usage=None` (interruzione) → nessun `cost`.
  - `test_subagent_stop_passes_usage` (`tests/test_check_subagent_stop.py`): nei rami «budget», «veti esauriti», «fatto», «implementatore senza lavoro» (`:88`), «sola lettura generico» (`_readonly`, `:27`) e «sola lettura che ha cambiato file» (`tampered_records`) il record `subagent_finish` ha `usage`, quando l'evento ha una trascrizione; senza trascrizione `usage` è `None` e non c'è `cost`.
  - `test_reviewers_pass_usage`: un test per modulo (`tests/test_check_task_verdict.py`, `tests/test_check_final_review.py`, `tests/test_check_audit_round.py`) con una trascrizione finta in `agent_transcript_path`: ogni `subagent_finish` che il modulo emette ha `usage` non vuoto.
  - `test_budget_cut_has_no_cost` (`tests/test_check_common.py`): `budget_cut_records` → `subagent_finish` senza `usage`, nessun `cost`.
  - `test_user_decision_written_only_by_set_decision` (`tests/test_reviews.py`, decisione 6): nessun file di `bin/` fuori da `tollgate_core/reviews.py` contiene `SET user_decision` (ricerca nel testo dei sorgenti).
  - `test_approve_finding_emits_finding_event`: `approve finding <id> minor <motivo>` → evento `finding` con `confidence`, `verification`, `user_decision == "downgraded:minor"`, `reason`.
- [ ] **Step 2:** test del task → FAIL (o PASS solo i due della decisione 6: si committano come guardia).
- [ ] **Step 3:** `transcript_usage` accanto a `transcript_tokens`, con la stessa lettura tollerante. In `subagent_stop`, `task_verdict`, `final_review` e `audit_round` token e uso si calcolano una volta con `_common.transcript_cost(event)` e vanno in ogni `record("subagent_finish", …)`, compresi `_readonly` e `tampered_records`; le chiusure elencate nella decisione 3 restano senza. L'operazione `subagent_finish` passa `usage=d.get("usage")`.
- [ ] **Step 4:** test del task → PASS; `tests/run`.
- [ ] **Step 5: commit** `tollgate C1: costo in token per subagente e per modello; guardia sulle decisioni dei rilievi`.

### Task 8: La fotografia per il gestionale

**Files:**
- Create: `bin/tollgate_analysis/turn.py`, `bin/tollgate_core/snapshot.py`, `docs/uso/gestionale.md`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `snapshot`), `docs/uso/comandi.md`
- Test: `tests/test_turn.py` (nuovo), `tests/test_snapshot.py` (nuovo), `tests/test_cli.py`, `tests/test_docs.py` (`test_docs_exist`, `:74-76`, fissa l'insieme delle pagine di `docs/uso/`: riceve `gestionale.md`; collegamenti)

**Interfaces:**
- Consumes: colonne del Task 1, eventi dei Task 3-7.
- Produces:
  - `turn.TurnFacts(phase: str, waiting: list[dict])` e `turn.waiting_on(facts: TurnFacts) -> str` (`"decision"`, `"user"`, `"agent"`); `turn.USER_PHASES = ("pr_open", "approval")`;
  - `snapshot.SNAPSHOT_VERSION = 1`; `snapshot.build(conn, *, now, host: str) -> dict`;
  - `snapshot.waiting_items(conn, work: int) -> list[dict]` (voci `{"kind": "block"|"effect"|"question", "id"}`).

- [ ] **Step 1: test che falliscono** (`tests/test_turn.py`)
  - `test_decision_wins`: `TurnFacts("pr_open", [{"kind": "block", "id": 3}])` → `decision`.
  - `test_user_phases`: `TurnFacts("pr_open", [])` e `TurnFacts("approval", [])` → `user`.
  - `test_agent_otherwise`: `TurnFacts("execution", [])` → `agent`.
- [ ] **Step 2: test che falliscono** (`tests/test_snapshot.py`)
  - `test_snapshot_shape`: un lavoro attivo con due task e un `cost` → `v == 1`, `works[0]` ha esattamente le chiavi della decisione 8, `cost.tokens` è la somma, per agente, dell'ultimo `cost` e `by_task` per numero.
  - `test_waiting_items`: nell'ordine, una `stop_asked` della sessione `A` con la sua `stop_answered`, un blocco aperto, un effetto in attesa (`intents` con `action = 'effect'`), un intento `pr` `requested`, un evento `subagent_stop` della sessione `B` e per ultima una `stop_asked` della sessione `B` senza risposta → tre voci (blocco, effetto con il suo `data.id`, domanda di `B`; l'intento `pr` no); `turn == "decision"`, `waiting_user == 3`.
  - `test_cost_last_per_agent`: due `cost` dello stesso `agent` (100 poi 250 token) e uno di un altro agente (50) → `cost.tokens == 300`.
  - `test_unanswered_question_expires`: una `stop_asked` senza risposta seguita da un `act` dello stesso lavoro → non è in `waiting`; seguita da un `session_start` di **un'altra** sessione sullo stesso lavoro → non c'è; seguita da una seconda `stop_asked` della stessa sessione → c'è solo la seconda; seguita solo da eventi `subagent_stop` e `cost` → c'è ancora.
  - `test_pr_open_counts_user`: fase `pr_open` senza attese → `turn == "user"`, `waiting_user == 1`.
  - `test_snapshot_has_no_free_text` (Review Focus 5): con un blocco dal motivo `segreto-di-prova`, una ruling e una domanda, il JSON serializzato non contiene `segreto-di-prova` né le chiavi `reason`, `what`, `question`, `worktree`.
  - `test_snapshot_pre_c1_work` (Review Focus 4): un lavoro con `size` nullo → `size` nullo, nessun errore.
  - `test_snapshot_skips_closed`: un lavoro `closed` non compare.
  - `test_cli_snapshot_without_db`: senza DB → `{"v": 1, ..., "works": []}` e il file del DB non viene creato.
- [ ] **Step 3:** test del task → FAIL.
- [ ] **Step 4:** la decisione 8. `snapshot.build` legge con query in sola lettura; `last_event_at` è l'`at` dell'ultimo evento del lavoro; `host` lo passa `cli` (`socket.gethostname()`), i test ne passano uno finto. In `cli.py` il sottocomando `snapshot` stampa `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)`.
- [ ] **Step 5: la pagina `docs/uso/gestionale.md`** (decisione 9): cosa leggere (`events --after-seq`, `snapshot`), la busta e la chiave tra più DB (`host`, `seq`; `repo_key`, `issue`), i cinque tipi nuovi con i `data`, la versione, l'archivio di `events_days`, le misure. La misura: copia tre stati di `docs/verifiche/evidenze/eval-b8/` in una cartella `mkdtemp(prefix="tollgate-")` di `/tmp`, conta gli eventi e i byte, scrive nella pagina i numeri, da dove vengono e il limite della decisione 9; la cartella si cancella. `docs/uso/comandi.md` ha la voce di `snapshot` e il collegamento alla pagina.
- [ ] **Step 6:** test del task → PASS (anche `tests.test_docs`); `tests/run`.
- [ ] **Step 7: commit** `tollgate C1: fotografia in JSON per il gestionale e pagina d'uso`.

### Task 9: Prova reale corta (implementatore, poi controller)

**Files:**
- Modify: `spikes/run-b1-flow.sh` (`registra`), `spikes/b1/flowreg.py` (un comando nuovo `eventi-c1`, che stampa su stdout come `eventi`: il modulo resta di sola lettura tranne `togli-pagine`; `WANTED` ed `eventi` non cambiano), `tests/test_b1_scripts.py`
- Create: `docs/verifiche/2026-11-20-c1-prova-flusso.md`, `docs/verifiche/evidenze/c1/flusso/`

- [ ] **Step 1 (implementatore): test che fallisce** `test_registra_lists_c1_events` in `tests/test_b1_scripts.py`, sul modo `controlla` o sulla funzione che `registra` usa: il comando nuovo `flowreg.py eventi-c1 <events.jsonl>` stampa su stdout i soli eventi `size_decided`, `cost` e `ruling`, con `data` di `size_decided` intero, e `registra` lo ridirige in `eventi-c1.jsonl` (per `cost` solo `tokens` e le chiavi di `by_model`); `registra` lo chiama dopo `eventi` e scrive `snapshot.json` con `tollgate snapshot` nello stesso ambiente di `status --json` (`TOLLGATE_STATE` dello stato di prova). Il test esistente di `eventi` (`tests/test_b1_scripts.py:1186-1189`) resta com'è.
- [ ] **Step 2 (implementatore):** la modifica a `registra` con `B1_FLOW_CASE` predefinito; una variabile nuova `B1_FLOW_EVIDENCE=<x>` sceglie la cartella delle evidenze `docs/verifiche/evidenze/<x>/flusso` e vince sulle scelte di `B1_FLOW_RULES` e `B1_FLOW_CASE` (senza, la cartella di oggi; `c1` per questa prova), con un test sul modo `controlla`. Test → PASS; `tests/run`; commit `tollgate C1: la prova reale mostra taglia e costo`.
- [ ] **Step 3 (controller, eccezione 1 delle istruzioni):** `controlla`, `prepara` (con `B1_FLOW_RULES=vere`), `passo1`, `passo2`, `registra`, con `B1_FLOW_EVIDENCE=c1`. Prima: `ANTHROPIC_API_KEY` non impostata (solo la presenza), `df -h /tmp` sopra 1 GB.
- [ ] **Step 4 (controller):** si guarda nelle evidenze: un `size_decided` con causa `start` e uno con causa `plan`; un `cost` per ogni chiusura con trascrizione della decisione 3, con `by_model` non vuoto e `tokens` uguale a quello di `subagent_stop`; se un subagente è stato ripreso, se i suoi `cost` crescono (trascrizione cumulativa, come vuole la decisione 3); la fotografia in `snapshot.json` (il controller non lancia `snapshot` da sé: senza lo stato di prova leggerebbe quello della macchina) con il lavoro, la taglia e il costo. Poi `togli-pagine` sulle trascrizioni copiate, la sostituzione di nome utente e host con `USER` e `HOST` in tutta `docs/verifiche/evidenze/c1/` (`python3 -B evals/scrub.py anonymize <cartella> <utente> <host>`, come le prove di B; `snapshot.json` e `events.jsonl` compresi, perché portano `host`), `/usr/bin/grep -raF` dei due valori (senza stamparli: deve essere vuoto) e lettura a mano. Nel ledger una riga per controllo che comincia con `Prova:` (passi, eventi visti, costo equivalente, pulizia delle evidenze).
- [ ] **Step 5 (implementatore sonnet, dopo il controllo del controller):** il rapporto `docs/verifiche/2026-11-20-c1-prova-flusso.md` sul modello di `docs/verifiche/2026-11-12-b7-prova-flusso.md`, con la riga `Esito:`, i passi, il costo equivalente e i punti non provati (le fermate, rinviate a C6). Commit `tollgate C1: prova reale corta`.

### Task 10: Revisione 36 della spec, progetto e piano principale

**Files:**
- Modify: spec del nucleo, progetto di C (riga di avanzamento), piano principale di C (stato, riga C1, sezione 3 con i nomi reali, sezione 8)

- [ ] **Step 1:** spec rev 36 con la decisione 12 (sezioni 3.1, 3.2, 6.1, 7.1, 7.2, 8.4, 11.4, 12.2, 18.4, 20); la sezione 20 elenca le dodici decisioni e le ruling del ledger che cambiano la spec.
- [ ] **Step 2:** il progetto di C ha una riga «Avanzamento» con C1 e il rapporto della prova; il piano principale ha lo stato, la riga C1 con «**Stato:** eseguita sul ramo `c1-tracciamento-locale`, in attesa del merge» (la parola «unita» la scrive solo il punto 5 di «Chiusura», dopo il merge), i nomi reali nella sezione 3 e i minori rinviati nella sezione 8.
- [ ] **Step 3:** la tabella «Copertura» di questo piano: per ogni riga, il nome del test che la prova esiste nel ramo (`grep -n` dei nomi); un nome cambiato si corregge qui con una nota.
- [ ] **Step 4:** `python3 -B -m unittest tests.test_docs` e `tests/run` → PASS; commit `tollgate C1: spec del nucleo rev 36 e piano principale aggiornato`.

## Copertura: punti del progetto destinati a C1 → task

| Punto del progetto (e del piano principale) | Task | Prova |
|---|---|---|
| 2 Obiettivo 1, 6: gli eventi nuovi escono da `tollgate events` | 1 | `test_new_event_types_recorded` |
| 2 Obiettivo 4, 3.1, 3.2 «Chi decide» (proposta e riga, piccolo e medio senza aspettare) | 3 | `test_start_new_work_has_size_line`, `test_plan_registration_decides_size` |
| 3.2 «Quando diventa grande, e qual è il sì» (`approve spec <n>` con n > 1; `size_decided` all'avvio e ad `approve spec`) | 4 | `test_approve_spec_records_slices_and_large` |
| 3.2 «Segnali» (fette, task, aree, L2; soglie con test) | 3 | `test_medium_thresholds`, `test_large_with_slices`, `test_areas_counts_verticals_only` |
| 3.2 «Crescita» (il livello sale, il piano aggiunge fette; grande solo con un sì; mai giù da sola) | 3 | `test_never_goes_down`, `test_large_needs_a_yes`, `test_level_rise_raises_size`, `test_l1_plan_with_three_slices_stays_medium`, `test_plan_after_reopen_does_not_shrink` |
| 3.2 «Scelta dell'utente» (l'atto fissa la taglia) | 3, 4 | `test_approve_size_act`, `test_user_size_is_fixed` |
| 8 «La macchina che l'ha avviato o adottato» (un lavoro adottato ha taglia e fette) | 3 | `test_adopt_decides_size_at_start` (`tests/test_adopt.py`; fette: `test_own_spec_approval_with_three_slices_is_a_yes`, `test_later_slice_keeps_slices_null_and_medium`, `test_l1_plan_with_three_slices_adopts_medium`) |
| 3.3 La presa: punto unico, segnali in ingresso, taglia e motivo in uscita, ogni proposta e correzione registrata | 3 | `test_reason_names_the_signals`, `test_decide_records_event_and_sets_size` |
| 6 `size_decided` | 3, 4 | come sopra |
| 6 `ruling` e «Come si registrano le ruling» (comando sul modello di `research submit`, quattro campi, la skill e il brief lo citano) | 5 | `test_parse_text`, `test_add_records_event`, `test_subagent_may_add_ruling`, `test_implementer_brief_mentions_ruling` |
| 6 `stop_asked`, `stop_answered` (con la risposta, anche rifiutata) | 6, 8 | `test_stop_asked_recorded`, `test_stop_answered_from_tool_response`, `test_stop_answered_on_failure`, `test_unanswered_question_expires` |
| 6 `cost` e «Dove sta il costo» (token per ogni subagente; dollari solo negli eval, nel loro registro) | 7 | `test_cost_event_on_finish`, `test_transcript_usage_by_model`, `test_reviewers_pass_usage` |
| 6 Decisioni sui rilievi come evento (accettato, declassato, archiviato), con confidenza e verifica | 7 | `test_approve_finding_emits_finding_event` (in `tests/test_actapply.py`, dove vive il flusso `approve finding`), `test_user_decision_written_only_by_set_decision` (`tests/test_reviews.py`); «accettato» = evento `finding` confermato senza `user_decision` (decisione 6) |
| 6 `sync` | rinviato a C4 (decisione 10; piano principale, decisione 2) | — |
| 6 «Tutto locale» | 5, 6, 8 | nessuna scrittura su GitHub nei task; `test_snapshot_has_no_free_text` |
| 6 «La storia non si cancella» («mai» per difetto, archivio JSONL, spazio misurato) | 2, 8 | `test_minimal_gets_defaults` (`tests/test_config.py`) e `test_housekeeping_never_prunes_with_zero` (`tests/test_start.py`), `test_archive_then_prune`, `test_archive_write_failure_deletes_nothing`; pagina d'uso |
| 10 Fotografia con versione, sola lettura, documentata in `docs/uso/` | 8 | `test_snapshot_shape`, `test_cli_snapshot_without_db`; `docs/uso/gestionale.md` |
| 4.3 «A chi tocca» (il calcolo locale; la scheda è di C4) | 8 | `test_decision_wins`, `test_user_phases`, `test_agent_otherwise` |
| 2 Anti-obiettivo «una cosa piccola con la cerimonia di una grande» | 3 | `test_small_by_default` (un lavoro piccolo non chiede niente all'utente) |
| 13 Test senza rete | tutti | nessun test nuovo usa `gh` |
| 14 Vincoli (stdlib, strati, suite, niente modelli, profili intatti, repo pubblico) | tutti | `tests/test_layers.py`; suite tre volte; revisione finale |
| Piano principale, decisione 6: prova reale corta | 9 | rapporto `docs/verifiche/2026-11-20-c1-prova-flusso.md` |
| Spec del nucleo: revisione 36 | 1 (riga `**Tipi:**`), 10 | `test_spec_event_types_match_registry` |

Nomi corretti dal Task 10 (grep `def <nome>` in `tests/`): `test_adopt_decides_size` è `test_adopt_decides_size_at_start`; `test_events_days_default_is_never` è diviso tra `test_minimal_gets_defaults` (il predefinito 0 e `lookups_days` 180) e `test_housekeeping_never_prunes_with_zero` (con 0 la pulizia non cancella); `test_approve_finding_emits_finding_event` sta in `tests/test_actapply.py` e non in `tests/test_reviews.py` (ruling del Task 7). Gli altri nomi esistono come scritti.

## Revisione del piano

Rivisto, insieme al piano principale e ai tre file di esecuzione, da un revisore opus a contesto pulito, in sola lettura, contro il progetto di C, il brief di scrittura, la spec rev 35 e il codice di `main` (`598bfd2`), in cinque giri (20-21/11/2026). Rilievi aperti per giro (critical, important, minor): 0/11/12, 0/4/15, 0/6/10, 0/2/9, 0/0/6. Tutti corretti nel testo, anche i sei minori dell'ultimo giro. Tra le correzioni più importanti: la riga della taglia composta da una funzione pura usata sia dall'hook sia dalla registrazione; il costo per ogni chiusura con trascrizione, cumulativo per agente; le domande dirette che nessun hook guasto può negare (wrapper e `runner`); la scadenza delle domande con `session_start` registrato; la taglia fissata dall'utente; `adopt` con la sola approvazione della stessa issue; il testo delle ruling da stdin.
