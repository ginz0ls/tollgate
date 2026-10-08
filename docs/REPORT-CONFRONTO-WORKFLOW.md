# Report: workflow di sviluppo ad agenti, confronto completo e base per il plugin

Data: 8 ottobre 2026.
Input: `HANDOFF.md` (stessa cartella).
Stato: analisi. Nessun codice del plugin scritto: le decisioni aperte (sezione 12) restano dell'utente.

---

## 0. Sintesi in una pagina

**Domanda.** Quale workflow ad agenti è oggi il migliore, per ogni tipo di progetto? Cosa deve fare un plugin per superarli tutti?

**Risposta breve.**

1. **Nessuno dei sistemi analizzati, locali o pubblici, vince su tutto.** Ognuno eccelle su un asse:
   - Superpowers sulla disciplina del singolo agente;
   - Spec Kit sulle specifiche portabili;
   - GSD sul contesto nelle sessioni lunghe;
   - Compound Engineering sulla conoscenza che si accumula;
   - codex-workflow sui controlli git deterministici e sul gate umano in PR;
   - l'Orchestratore Goal sulle ricevute dei comandi legate alla revisione dei file;
   - il flusso Perizie sulla qualità di piani, ruling e revisioni in un progetto reale in produzione.
2. **Il buco comune è l'imposizione delle regole.** Tutti i plugin pubblici più usati (Superpowers, agent-skills, GSD, BMAD, Spec Kit) impongono le regole **solo con il prompt**. Il loro unico hook è un `SessionStart` che inietta testo. Le evidenze dicono che non basta:
   - con l'istruzione «non barare» il reward hacking resta al 70-80% sul task testato da METR;
   - le skill non partono nel 56% dei casi nei test di Vercel;
   - nel flusso Perizie la notturna è rimasta rossa per giorni senza che nessuno se ne accorgesse.
   Claude Code oggi ha oltre 30 eventi hook, con blocco tramite exit 2. Quasi nessuno li usa per i gate.
3. **Il secondo buco è la prova di efficacia.** Nessun concorrente dimostra con eval ripetibili che il suo workflow migliora il risultato rispetto a Claude Code senza plugin. Esiste `claude plugin eval`, che confronta con una baseline: è un vantaggio competitivo diretto.
4. **Il terzo buco è l'adattamento al tipo di progetto.** I workflow pubblici applicano lo stesso rituale a un bugfix, a una migrazione DB e a un prototipo. Le evidenze su TDD imposto, piani lunghi e revisioni multiple dicono che il rigore va proporzionato al rischio del cambiamento e ai percorsi toccati.

**Raccomandazione.** Costruire un plugin che sia **un harness di gate**, non un'altra collezione di skill. Il modello riprende:
- da codex-workflow: controlli git, verdetto a riga leggibile da macchina, gate PR con merge umano;
- dall'Orchestratore: ricevute legate all'hash, tetto di revisioni, scope per task verificato;
- da Perizie: piano magro, ruling con costo, punti di arresto, criterio di gravità, revisione avversariale;
- da Superpowers e GSD: ledger su disco, contesto fresco per subagente, verifica goal-backward.

Il tutto va imposto da hook, con **profili per tipo di progetto** scelti dai file toccati e una suite di eval che ne misuri l'effetto. Dettaglio nella sezione 10.

---

## 1. Perimetro, metodo, affidabilità

| Fonte | Come è stata analizzata | Affidabilità |
|---|---|---|
| Orchestratore Goal (`/home/crucco/MEGA/BIZ/VIBE/orchestratore-goal`) | Lettura completa di codice, docs, policy ed evidenze. **Test eseguiti: 102 OK in 10 s** (con fake, senza rete) | Alta |
| codex-workflow (`.../Company AgentOS/Hermesz/codex-workflow`) | Lettura completa di codice, prompt e docs. **Test eseguiti: 128 OK in 8 s** | Alta |
| Flusso Perizie (`.../Commercialista mombello/Piattaforma Perizie`) | Lettura di CLAUDE.md, piani, avvii, audit, todo, registri sdd e memoria. Metriche da `git log` e `wc` | Alta |
| Plugin installati (superpowers 6.4.1, agent-skills 0.6.9, GSD 1.9.4, plugin ufficiali) | Lettura dei sorgenti in `~/.claude/plugins/cache` e `~/.claude/get-shit-done` | Alta |
| Stato dell'arte online | WebSearch e WebFetch su fonti primarie (API GitHub, README, docs ufficiali) al 08/10/2026 | Media-alta. Le fonti secondarie sono segnalate |
| Evidenze empiriche (METR, Anthropic, arXiv, Fowler) | Lettura delle fonti primarie dove possibile | Media. Alcune cifre 2026 vengono da riassunti: le segnalo con **[S]** |
| Censimento GitHub | `gh api` su circa 98 repository verificati (stelle, push, licenza, archiviazione) | Alta sui metadati. Media sulle descrizioni, che non vengono dal codice |

Convenzioni: **[V]** = fonte primaria letta; **[S]** = fonte secondaria non verificata sull'originale; **[Inf]** = inferenza mia.

**Correzioni rispetto all'handoff.** L'analisi approfondita ha trovato fatti che l'handoff non riportava o che cambiano il giudizio:

| Tema | Handoff | Fatto verificato ora |
|---|---|---|
| codex-workflow, specialisti | «Gli specialisti si scelgono dalle label Jira» | `select_specialists` e `pm_decision` **non sono mai chiamati** fuori dai test (`specialists.py:10-29`, usati solo da `tests/test_worktree_models.py:130`). È codice morto |
| codex-workflow, piano | Fasi planning → development → review | **L'output del pianificatore non arriva né all'implementatore né al revisore.** `implement` riceve lo stesso `issue_context` del ticket (`coordinator.py:124-127`). Il revisore deve giudicare «against the plan» senza riceverlo |
| codex-workflow, isolamento | Non indicato | Codex gira con `--sandbox danger-full-access` (`codex.py:73-75`). Il confinamento è solo un controllo del `cwd` |
| codex-workflow, tetto | 10 bocciature | Corretto nel codice (`reviews.py:8`). `docs/troubleshooting.md:13` dice 5: la documentazione è incoerente |
| Orchestratore, test | «Le evidenze dichiarano 102 test» | Eseguiti: 102 OK |
| Perizie, `CLAUDE.md` | «enorme» | 193 righe ma **59.888 byte**, circa 18-20k token caricati a ogni sessione e in ogni subagente |
| Perizie, disciplina | Non quantificata | La notturna di `main` è fallita ogni notte dal 30/09 (pgTAP `21_relazione`), senza far girare app e Playwright. Scoperta solo in M2 (`CLAUDE.md:92`). La regola «nessun test esistente cambia» è stata derogata 6 volte nelle ultime 3 fette |

---

## 2. I tre sistemi di partenza, in profondità

### 2.1 Orchestratore Goal

**Cos'è.** Un controller Python solo stdlib (circa 1.700 righe più 1.400 di test). Pilota `codex app-server --stdio` via JSON-RPC. Ogni fase (piano, implementazione, audit, correzione) ha un thread Codex nuovo con un Goal nativo. **La continuazione dei turni è del runtime Codex: il controller non invia mai `turn/start`** (`control.py:47`).

**Macchina a stati** (`workflow.py:7-113`, `controller.py:32`):
- Fasi: `plan` (globale), poi per task `implement` → `audit` → `correct` → `audit`…
- Stati del task: `ready`, `running`, `waiting`, `complete`.
- Stati della run: `preparing`, `ready`, `running`, `pausing`, `paused`, `stopping`, `stopped`, `complete`, `recovery_required`.
- Un solo incarico per repository alla volta (`workflow.py:20-21`): niente parallelismo.

**Persistenza e ripresa.**
- SQLite in WAL con `synchronous=FULL`. Lo stato è un unico blob JSON. Gli eventi hanno un id idempotente e c'è una coda di comandi umani (`store.py:56-94`).
- **L'intento viene salvato prima dell'effetto**: prima `assignment/intent`, poi l'id del thread, poi `goal/activate_intent`, e solo dopo `thread/goal/set` (`controller.py:93-101`).
- Dopo un crash riprende lo stesso thread, ma solo se il modello restituito coincide con quello richiesto (`controller.py:221-248`).

**Garanzie imposte dal codice.** Questa è la parte di valore.

| Garanzia | Come | Dove |
|---|---|---|
| Ricevute dei comandi | Il controller osserva ogni `commandExecution` e salva comando, exit code, hash dell'output e flag `skipped`. La ricevuta vale solo se l'hash dei file in scope è uguale a inizio e fine comando e coincide con il checkpoint. Il modello non può dichiarare «test verdi» senza una ricevuta osservata | `controller.py:146-163`, `workflow.py:71-82` |
| Revisione = hash dei file | Contenuto e permessi di tutti i file, anche quelli ignorati da git. Rifiuta symlink, submodule e file oltre 20 MiB | `workspace.py:75-95` |
| Scope per task | `changed_paths` deve stare nello scope del task. Planner e auditor devono avere zero modifiche, altrimenti scatta un blocco globale | `reports.py:99-105` |
| Piano validato | Rifiuta requisiti inventati o omessi, scope fuori autorità e DAG ciclici | `workspace.py:31-71` |
| Richieste di autorità | Ogni richiesta del runtime diversa da un tool call viene rifiutata e apre una decisione umana. Mai approvazione automatica | `controller.py:129-134` |
| Skill legate all'hash | Le skill obbligatorie devono essere state lette (con hash) prima di poter consegnare un report | `reports.py:79-91` |
| Tetto revisioni | Profilo `local`: 1 prospettiva, tetto 4. Profilo `strict`: 8 prospettive, 10 lenti, tetto 30. Lo storico non si azzera | `audit.py:9-14, 61-62` |
| Risoluzione dei finding | Un finding si chiude solo dalla prospettiva che l'ha trovato e su una revisione nuova | `audit.py:106-112` |
| Permessi | Planner e audit `read-only`, writer `workspace-write`, rete spenta. Disabilitati MCP, hook, plugin, browser e web_search | `controller.py:68-80`, `native.py:16-30` |

**Gravità.** Le categorie sono `minore`, `rilevante`, `grave`, `bloccante`. Il codice distingue solo minore da non minore. Le definizioni sono nel prompt (prd-audit).

**Evidenze reali.**
- Fixture `add(a,b)` in 244 s, circa 96k token, una sola revisione.
- La fixture in profilo strict ha richiesto 16 cicli e circa 154k token.
- Provati: pausa e ripresa, `systemctl stop` con ripresa dello stesso thread.
- **Mai eseguito su un PRD reale.** Nessuna prova con Claude, nessuna run con un finding corretto davvero.

**Cosa dice della concorrenza** (`docs/RICERCA-GITHUB.md`): sono analizzati Oh My Codex/Ultragoal, Superpowers, GSD Core, GSD Pi, Ralph Orchestrator, backnotprop/orchestrator e Oh My ClaudeCode. La conclusione: **non installare insieme GSD, OMX e Superpowers**, perché ciascuno ha la propria conduzione. Lo prende come lezione: un solo coordinatore.

**Limiti per tipo di progetto.** Funziona bene per le librerie e quasi per niente altrove:
- Frontend: niente browser.
- Backend: niente Docker, niente rete, comandi in background vietati.
- Infra: deploy vietato.
- Data/ML: file oltre 20 MiB respinti.
- Monorepo: ri-hash di tutto a ogni report.

### 2.2 codex-workflow (Hermes)

**Cos'è.** Un ponte Jira → Codex → GitHub in Python stdlib (3.574 righe più 2.097 di test). Ha due processi, `serve` per i webhook e `worker` per la coda SQLite, più gli adattatori.

**Flusso end-to-end.**
1. Webhook Jira firmato (HMAC-SHA256, finestra di timestamp opzionale).
2. Dedup su `(provider, event_id)`.
3. Coda `start_planning`.
4. Worktree su un ramo deterministico `workflow/<project>/<sha12(repo)>/<issue>`.
5. Fase `sol-planner`.
6. Fase `terra-developer`.
7. `verify_implementation`.
8. Fase `sol-reviewer`.
9. Verdetto.
10. Push più `ls-remote` sullo SHA esatto.
11. Ricerca di una PR aperta o creazione, poi verifica della PR.
12. `human_review`.
13. Webhook di merge GitHub da un umano autorizzato.
14. `sync_base --ff-only`, stato `done`, scheduling dei ticket sbloccati.

**Macchina a stati** (`transitions.py:8-25`): `new → planning → development → review → {development | human_review | escalated}`, poi `human_review → done`. Ogni transizione ha una operation key idempotente.

**I controlli git: la parte migliore, da portare quasi intera** (`worktree.py:43-87`):
1. Il ramo corrente è quello assegnato.
2. HEAD è un commit diverso dalla base e ne discende (`merge-base --is-ancestor`).
3. Il diff non è vuoto e non contiene solo file di sistema.
4. Nessun file `.workflow-bridge*` è committato.
5. Il worktree è pulito (`status --porcelain --untracked-files=all`).
6. `implementation_sha` viene salvato e ricontrollato prima della review e prima della PR. Se il revisore modifica qualcosa, la PR fallisce: **una revisione in sola lettura verificabile anche senza sandbox.**
7. Dopo il push, `ls-remote` deve restituire esattamente lo SHA atteso.
8. La PR viene verificata: `state=open`, head e base giusti, `head.sha == implementation_sha`.

**Verdetto.** Una riga `WORKFLOW_REVIEW: {"material_failure": bool, "summary": "..."}`, con fallback sull'ultima riga JSON (`coordinator.py:81-94`). Il tetto è di 10 bocciature, poi escalation. `grant-review-attempts` concede da 1 a 5 tentativi in più (`reviews.py`, `workflow.py:117-139`). Un difetto: un `JSONDecodeError` non è gestito e il job viene ritentato invece che rifiutato.

**Difetti gravi trovati.**
- Gli specialisti sono codice morto.
- **Il piano non viene mai passato** a chi implementa e a chi rivede.
- Sandbox `danger-full-access` mentre l'agente legge ticket non fidati: è la «lethal trifecta» di Willison.
- **Il bridge non esegue mai test, lint o build**: la qualità dipende interamente dal giudizio dei modelli.
- Il lease di 60 s è più corto del timeout di 900 s: con due worker si rischia una doppia esecuzione.
- Accoppiamento a Jira: `customfield_10014`, etichette italiane specifiche, nomi di modello cablati.
- Prompt dei ruoli di 3-5 righe, nessuna skill.

**Peso dell'infrastruttura.** Circa 1.330 righe servono all'avvio da evento (webhook, firma, config, adattatori, riconciliazione) e circa 1.450 al workflow vero. In un plugin la prima metà sparisce: **si riutilizzano circa 400 righe di logica** (worktree, reviews, verdetto, idempotenza).

### 2.3 Flusso Perizie

**Cos'è.** Una metodologia, non un software: spec → piano generale → piano di fetta → prd-audit → revisione avversariale → P1 → `subagent-driven-development` → revisione finale → verifica completa → dry-run → deploy → merge ff-only → P2. **È l'unico dei tre in produzione**:
- 390 commit in 14,7 giorni;
- 20 fette (A-O con sottofette);
- test pgTAP passati da 503 a 933, test app da 304 a 528.

**Gli artefatti, con il formato che vale la pena standardizzare.**
- **Piano magro** (dalla fetta L, 279-960 righe; i piani A-K erano 1.300-4.200 righe, di cui il 53-84% codice). Sezioni:
  - Fatti verificati sul codice (tabella fatto / dove / conseguenza, su uno SHA preciso);
  - Global Constraints;
  - Decisioni con colonne **Scelta / Perché / Costo se sbagliata**;
  - Interfacce con firme esatte («firme che possono cambiare, e solo queste»);
  - SQL e testi fissati parola per parola;
  - Review Focus come scenari d'attacco;
  - File structure;
  - Task senza corpo del codice;
  - Punti di arresto;
  - Rischi.
- **Ruling** `R-n: scelta — perché — costo se sbagliato`. Sono stati 25-33 per fetta. Trasformano ogni decisione autonoma in un debito visibile.
- **Punti di arresto con semantica fissa**:
  - P1: approvazione del piano;
  - P2: chiusura;
  - P3: deriva di contratto (firme, test fuori elenco, bundle, criterio di arrivo);
  - P4: spesa o modelli veri;
  - P-D: anomalia di deploy.
- **Criterio di gravità tarato sul progetto** (`docs/audit/2026-10-07-audit-piano-fetta-m-stato.md:5`). Bloccante = cifra entrata senza conferma, dato di altri, azione doppia. Grave = passo che fallirebbe com'è scritto. E così via.
- **Registro SDD** (`.superpowers/sdd/<piano>/progress.md`). Contiene una prima riga di identità, una scansione preliminare delle interfacce e righe `Task / Ruling / minor (deferred) / fix round i/5 / Final`. Intorno ci sono brief, report e diff di revisione su file.
- **Revisione avversariale.** Un revisore a contesto fresco riceve l'artefatto e il contratto, **senza le motivazioni dell'autore**. Restituisce una tabella `# / Parte / Gravità / Attacco / Esito` più gli «attacchi che il piano ferma».
- **Deploy in ordine**: dry-run mostrato, push della migrazione, pgTAP sul remoto, funzioni da un elenco chiuso derivato dagli import, `secrets list`, prova con un utente vero, merge ff-only.

**Cosa ha funzionato** (misurato):
- revisioni finali con pochi rilievi (M2 0/0/7, O 0/0/6);
- piani magri, che hanno eliminato il doppio lavoro;
- scansione preliminare, che trova incoerenze del piano prima di partire.

**Cosa ha ceduto.** È la lezione più importante per il plugin.
- **Tutto è prompt.** La cartella `.claude/` del progetto è vuota: niente hook, niente permessi.
- Notturna rossa per giorni senza che nessuno se ne accorgesse.
- Le regole «invariato» sono state derogate 6 volte in 3 fette: P3 funziona da registro, non da freno.
- Un fatto sbagliato nel piano: «DeepSeek non legge immagini», mentre le legge.
- Fetta M troppo grande, divisa durante il lavoro.
- **I fatti sono duplicati in 5-6 posti** (spec, piani, avvio, `CLAUDE.md`, `todo.md`, memoria). `CLAUDE.md` pesa circa 18-20k token in ogni sessione e subagente.
- Costo in token alto: più di 10 spawn Opus per fetta e circa 50k righe di diff di revisione.
- Il registro SDD è git-ignored, quindi la sola copia versionata è il riassunto in `todo.md`.

---

## 3. I plugin di workflow installati in locale

| | Superpowers 6.4.1 | agent-skills 0.6.9 | GSD 1.9.4 |
|---|---|---|---|
| Filosofia | Pipeline disciplinata con regole ferree e tabelle anti-razionalizzazione | Catalogo dell'intero ciclo di vita, un gate per fase | Gestione a fasi, orchestratore sottile, contesto fresco per subagente |
| Unità di lavoro | Task da 2-5 minuti | Task in `tasks/plan.md` | Fase → piano di 2-3 task (circa il 50% del contesto) → wave |
| Imposizione | Prompt, 1 hook `SessionStart` (~3,2 KB), script `task-done` che chiude solo con exit 0 | Prompt, 1 hook `SessionStart` (~10,4 KB, richiede `jq`) | Prompt e `config.json` (gates, safety). Hook solo per gli aggiornamenti |
| Isolamento | Worktree (skill) e subagente per task | Persona read-only, nessun worktree | Subagente per piano, nessun worktree |
| Revisione | Task reviewer, fix loop con tetto 5 ed escalation di modello, review del ramo | `/review` a 5 assi, `/ship` con 3 persona parallele e GO/NO-GO più rollback | plan-checker (3 iterazioni), verifier goal-backward (esiste / sostanziale / collegato) |
| Gravità | Critical / Important / Minor | Critical / Required / Optional / Nit / FYI | blocker / major / minor / cosmetic |
| Gate umano | Forte a monte (HARD-GATE), poi «rulings, not stalls» | Uno per fase; `/build auto` con un'approvazione | Configurabile per step |
| Memoria | Ledger `.superpowers/sdd/` + git | Checkbox in `todo.md` | `STATE.md`, pause/resume |
| Multi-motore | Ampio (Codex, Cursor, Gemini, …) | Ampio | Solo Claude Code |

**Pezzi migliori da riusare:**
1. ledger su disco con chiusura solo a test verdi (Superpowers);
2. brief, report e diff passati come **file** ai subagenti (Superpowers);
3. fix loop con tetto ed escalation del modello (Superpowers);
4. verifica goal-backward a tre livelli e `must_haves` dal piano alla verifica (GSD);
5. classificazione spike / bounded / architectural che può solo salire (Superpowers);
6. Definition of Done separata dagli acceptance criteria, `/constraints` contro i controlli indeboliti (agent-skills);
7. fan-out di revisori con regola di salto esplicita per diff piccoli (agent-skills `/ship`: ≤2 file, <50 righe, nessuna superficie sensibile);
8. punteggio di confidenza 0-100 con soglia 80 per filtrare i falsi positivi (plugin ufficiale `code-review`);
9. Stop hook con stato per `session_id` (plugin ufficiale `ralph-loop`): l'unico enforcement vero visto in locale;
10. regole dichiarative di blocco su file `.local.md` (`hookify`).

**Conflitti se installati insieme.**
- Due meta-skill iniettate a ogni sessione, ciascuna convinta di governare le altre.
- Tre cartelle di stato diverse (`docs/superpowers/`, `tasks/`, `.planning/`).
- Quattro scale di gravità.
- Posizioni opposte sull'ambiguità: Superpowers decide e registra, agent-skills e GSD si fermano.

**Il plugin deve avere un solo stato, una sola scala, un solo coordinatore.** L'Orchestratore arrivava alla stessa conclusione.

---

## 4. Stato dell'arte online (ottobre 2026)

### 4.1 Plugin e metodologie per Claude Code

Stelle lette dall'API GitHub il 08/10/2026.

| Progetto | Stelle | Ultima release | In una riga | Punto debole noto |
|---|---|---|---|---|
| obra/superpowers | ~296k | v6.4.2, 25/09/2026 | Metodologia completa a skill auto-attivanti. Nel marketplace ufficiale Anthropic | Solo prompt. Costo sui task piccoli (corretto in parte da v6.3-6.4). La README non è allineata (cita ancora la «two-stage review») |
| github/spec-kit | ~140k | v1.1.2, 07/10/2026 | `constitution → specify → plan → tasks → implement → converge`, più flussi bugfix (`assess → fix → test`) e valutazione di idee | Prolisso. L'agente ignora la spec e duplica classi esistenti (Böckeler) |
| addyosmani/agent-skills | ~103k | 0.6.12, 03/10/2026 | 25 skill e 9 comandi, `/build auto` con un'approvazione | Nessun isolamento, nessun ledger |
| ruvnet/ruflo (ex claude-flow) | ~74k | v3.55.0 | Meta-harness a sciami | Un audit indipendente sostiene che circa il 97% dei tool MCP sia uno stub [S, non confermato] |
| GSD → open-gsd/gsd-core | 64k (vecchio repo) / ~10k (nuovo) | Archiviato e migrato | Contesto fresco, onde parallele, `STATE.md` | Migrazione del repo, cerimonia |
| BMAD-METHOD | ~54k | v6.12.1 | Agile «AiDD» a skill, processo proporzionato | Pesante, molta documentazione |
| wshobson/agents | ~40k | — | Catalogo di 94 plugin e 202 agenti | Non è una metodologia |
| claude-task-master | ~28k | 0.43.1 | Task manager via MCP | Licenza Commons Clause |
| EveryInc/compound-engineering | ~25k | v3.30.4 | brainstorm → plan → work → simplify → review → **compound** | Poche verifiche indipendenti |
| SuperClaude | ~24k | v4.3.0 (marzo) | 30 comandi, 20 agenti, 7 modi | Attività in calo |
| automazeio/ccpm | ~8k | marzo 2026 | PRD → epic → GitHub Issues → worktree paralleli | Poco attivo |
| buildermethods/agent-os | ~5k | v3.0.0 | Ora iniezione di standard del codebase | Cambio di posizionamento |

### 4.2 Funzioni native di Claude Code (v2.1.293, 07/10/2026)

Contano più di qualsiasi plugin, perché **sono il substrato su cui il nostro plugin può imporre le regole con codice**:

- **Hook**: oltre 30 eventi, tra cui `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `PreCompact`, `PermissionRequest`, `InstructionsLoaded`. Gli handler possono essere `command`, `http`, `mcp_tool`, `prompt` o `agent`. **L'exit 2 blocca** e `PreToolUse` può riscrivere l'input.
- **Subagenti**: `tools` e `disallowedTools`, `model`, `permissionMode`, `isolation: worktree`, `hooks`, `skills`, `maxTurns`, `memory`.
- **Worktree**: l'isolamento è applicato dal codice. Blocca Edit e Write verso il checkout principale (ma non `cp` o i redirect della shell).
- **Dynamic workflows**: orchestrazione in JavaScript con `agent()`, `pipeline()`, `parallel()`, risultati validati da uno schema JSON, distribuibili nei plugin. **Il piano vive nel codice, non nel contesto del modello.**
- **`claude plugin eval`**: casi con grader (regex, chiamata di tool, rubrica) e **confronto con la baseline senza plugin**.
- **`/goal`**: Stop hook di tipo prompt. **Il valutatore non esegue comandi e non legge file**: giudica solo la conversazione. Non va usato come gate di completamento.
- **Code Review ufficiale** (Team ed Enterprise, preview): flotta di agenti più un passo di verifica sul codice reale, `REVIEW.md`, 15-25 dollari a review. **Non blocca mai il merge.**
- **Routines e `/schedule`** (preview cloud): trigger a orario, API o eventi GitHub. È la risposta all'autonomia a sessione chiusa senza scrivere un worker.
- **Agent teams**: sperimentali, con limiti noti.

### 4.3 Altri strumenti agentici

| Strumento | Idea distintiva | Lezione |
|---|---|---|
| Kiro (AWS) | `requirements.md` / `design.md` / `tasks.md`, onde di task, hook `PreToolUse/PostToolUse/PostFileSave/Stop`, Quick Spec | Anche l'unico IDE spec-driven ha capito che servono gli hook. Ma per un bug piccolo genera 4 user story e 16 criteri |
| OpenAI Codex | AGENTS.md, subagenti, hook, skill, plugin, sandbox configurabile | Convergenza delle primitive con Claude Code: un plugin multi-motore è fattibile per skill e prompt, non per gli hook |
| Copilot cloud agent | VM effimera, un ramo e una PR per task, 59 minuti massimo | Il gate umano sta in PR, come in codex-workflow |
| Jules | Piano approvato prima di toccare il codice, VM | Gate sul piano |
| Aider | Architect (propone) ed editor (applica) | Separazione tra pianificare e agire. Il progetto è in calo |
| Roo Code | Modi e Memory Bank | **Chiuso il 15/05/2026**, archiviato: i «modi» da soli non sono bastati |
| Devin, Factory, Amp, Augment, OpenHands | Agenti cloud, missioni, macchine effimere | Documentazione pubblica superficiale, non verificabili a fondo |
| Tessl | Da «spec come sorgente» a registry di skill valutate [S] | Il mercato si sposta sulle **skill valutate** |

---

## 5. Censimento dei progetti GitHub

**Metodo.** Stelle, ultimo push, licenza e flag «archived» sono stati letti con `gh api` il 08/10/2026 su circa 98 repository, tutti verificati. Ho scartato gli URL che rispondevano 404, i fork spacciati per originali e le liste spam.

**Limite.** Le colonne «cosa fa» e «da rubare» vengono dalla descrizione GitHub e dalla conoscenza generale, non dalla lettura del codice. Fanno eccezione i progetti già analizzati nelle sezioni 3 e 4.

Alcune stelle sembrano anomale (superpowers 296k, ECC 275k): sono riportate come lette.

Le date senza anno sono del 2026.

### 5.1 Plugin, skill e metodologie (spec → piano → esecuzione → review)

| Progetto | Repo | ★ | Ultimo push | Cosa fa | Da rubare |
|---|---|---|---|---|---|
| superpowers | obra/superpowers | 296k | 10-06 | Metodologia a skill completa | Disciplina tramite skill auto-attivanti |
| everything-claude-code | affaan-m/ECC | 275k | 10-05 | Raccolta massiva di skill, memoria e sicurezza | Apprendimento continuo («instincts») |
| spec-kit | github/spec-kit | 141k | 10-07 | SDD con constitution, più di 30 agenti | Formato degli artefatti come standard di fatto |
| agent-skills | addyosmani/agent-skills | 103k | 10-03 | SDLC in comandi slash | UX a comandi |
| ruflo (ex claude-flow) | ruvnet/ruflo | 74k | 10-07 | Sciami multi-agente | Cautela: audit sui tool stub |
| **OpenSpec** | Fission-AI/OpenSpec | 71k | 10-07 | SDD con **delta spec** archiviate | Spec incrementali, adatte al codice esistente |
| oh-my-openagent | code-yeongyu/oh-my-openagent | 70k | 10-07 | Harness OpenCode con keyword «ultrawork» | Una parola chiave attiva l'intero workflow |
| BMAD-METHOD | bmad-code-org/BMAD-METHOD | 54k | 10-07 | Ruoli agili e handoff | Modalità brownfield |
| oh-my-claudecode | Yeachan-Heo/oh-my-claudecode | 40k | 10-07 | Orchestrazione «teams-first» per Claude Code | Keyword che attivano pipeline |
| wshobson/agents | wshobson/agents | 40k | 10-05 | Marketplace multi-harness | Un sorgente, adattatori per harness |
| oh-my-codex | Yeachan-Heo/oh-my-codex | 33k | 10-06 | Hook e team per Codex | Stesso pattern portato su Codex |
| claude-task-master | eyaltoledano/claude-task-master | 28k | 04-28 | Task da PRD via MCP | Grafo delle dipendenze |
| planning-with-files | OthmanAdi/planning-with-files | 27k | 10-06 | Pianificazione persistente su file | Piano su file a prova di crash |
| compound-engineering | EveryInc/compound-engineering-plugin | 25k | 10-07 | plan → work → review → compound | Lezioni scritte per il ciclo successivo |
| SuperClaude | SuperClaude-Org/SuperClaude_Framework | 24k | 09-27 | Comandi, persona, MCP | Modalità attivate da flag |
| context-engineering-intro | coleam00/context-engineering-intro | 14k | 03-16 | Template PRP | — |
| GSD Core | open-gsd/gsd-core | 10k | 10-07 | Successore di GSD | Fasi a contesto fresco |
| ccpm | automazeio/ccpm | 8,4k | 03-18 | GitHub Issues e worktree paralleli | Issue come fonte di verità |
| agent-os | buildermethods/agent-os | 5,5k | 10-07 | Standard del codebase nelle spec | Estrazione degli standard |
| spec-workflow-mcp | Pimzino/spec-workflow-mcp | 4,3k | 07-03 | MCP con dashboard di approvazione | Dashboard web delle spec |
| claude-code-workflows | OneRedOak/claude-code-workflows | 3,9k | 10-06 | Review di design, sicurezza e codice, con Action | Review di design con Playwright |
| claude-code-spec-workflow | Pimzino/claude-code-spec-workflow | 3,9k | 2025-09 | Requirements → Design → Tasks | Riferimento storico |
| conductor | gemini-cli-extensions/conductor | 3,8k | 09-01 | Contesto in file versionati | — |
| cc-sdd | gotalab/cc-sdd | 3,7k | 09-23 | Gate per fase, poi esecuzione lunga | Approvazione e poi autonomia |
| claudex-loop | chaseai-yt/claudex-loop | 2,8k | 09-06 | Piano in 4 fasi con review avversariale di Codex | Revisore di un altro motore |
| agentic-project-management | sdi2200262/agentic-project-management | 2,4k | 06-08 | Gestione di progetto multi-agente | — |
| PRP | Wirasm/prp | 2,3k | 10-02 | Product Requirement Prompt con validazione | Loop di validazione |
| trailofbits/claude-code-config | trailofbits/claude-code-config | 2,1k | 08-24 | Default di sicurezza | Configurazione prudente |
| spec-kitty | spec-kitty/spec-kitty | 1,7k | 10-07 | SDD con governance | — |
| context-engineering-kit | NeoLabHQ/context-engineering-kit | 1,7k | 08-26 | Skill per la qualità del contesto | — |
| claude-workflow-v2 | CloudAI-X/claude-workflow-v2 | 1,4k | 10-06 | Agenti, skill e hook in un pacchetto | — |
| gsd-pi | open-gsd/gsd-pi | 1,3k | 10-07 | Variante con runtime autonomo | — |
| **moai-adk** | modu-ai/moai-adk | 1,2k | 10-07 | Plan/run/sync con gate **«TRUST 5»** | Gate di qualità con nome e fissi |
| cavekit | JuliusBrussee/cavekit | 1,1k | 08-14 | SDD compresso, «Frozen» | — |
| shinpr/claude-code-workflows | shinpr/claude-code-workflows | 691 | 10-01 | Esplorazione limitata all'approvato | — |
| shotgun | shotgun-sh/shotgun | 688 | 06-02 | Spec ancorate al codebase | — |
| smart-ralph | tzachbon/smart-ralph | 557 | 09-16 | SDD, Ralph e compattazione | — |
| metaswarm | dsifry/metaswarm | 419 | 06-19 | Multi-agente che si auto-migliora | — |
| claude-night-market | athola/claude-night-market | 342 | 10-06 | 23 plugin con hook TDD e flussi git/PR | Plugin piccoli e componibili |
| aiwg | jmagly/aiwg | 220 | 10-05 | Artefatti SDLC strutturati | — |

### 5.2 Awesome-list e marketplace

| Lista | Repo | ★ | Note |
|---|---|---|---|
| anthropics/skills | anthropics/skills | 180k | Skill ufficiali |
| awesome-claude-skills | ComposioHQ/awesome-claude-skills | 77k | — |
| awesome-claude-code | hesreallyhim/awesome-claude-code | 55k | Lista di riferimento |
| awesome-copilot | github/awesome-copilot | 40k | — |
| claude-plugins-official | anthropics/claude-plugins-official | 38k | Directory ufficiale |
| awesome-agent-skills | VoltAgent/awesome-agent-skills | 35k | Più di 1000 skill |
| vercel-labs/skills | vercel-labs/skills | 33k | Loader universale |
| claude-code-templates | davila7/claude-code-templates | 32k | CLI di installazione |
| awesome-claude-code-subagents | VoltAgent/awesome-claude-code-subagents | 26k | — |
| awesome-claude-plugins | quemsah/awesome-claude-plugins | 1,4k | Indice con metriche di adozione |
| awesome-agent-orchestrators | andyrewlee/awesome-agent-orchestrators | — | Circa 253 orchestratori, solo in parte catalogati qui |

### 5.3 Ticket o issue → agente → PR

| Progetto | Repo | ★ | Ultimo push | Cosa fa | Da rubare |
|---|---|---|---|---|---|
| OpenHands | OpenHands/OpenHands | 90k | 10-07 | Agente con resolver GitHub, SDK, server | Separazione tra sandbox e SDK |
| Aider | Aider-AI/aider | 49k | 05-22 | Pair programming da terminale | Repo-map |
| **Symphony** | openai/symphony | 28k | 09-15 | Spec di orchestrazione: ogni task una run isolata | Contratto ticket → run |
| SWE-agent | SWE-agent/SWE-agent | 20k | 10-06 | Risoluzione di issue | Agent-Computer Interface |
| Plandex | plandex-ai/plandex | 15,7k | 2025-10 | Grandi progetti, fermo | Sandbox di diff |
| Aperant | AndyMik90/Aperant | 14,6k | 06-14 | Coding autonomo multi-sessione | — |
| open-swe | langchain-ai/open-swe | 10,8k | 10-07 | Agente asincrono cloud | — |
| claude-code-action | anthropics/claude-code-action | 9,4k | 10-07 | `@claude` su issue e PR | Trigger da menzione |
| mini-swe-agent | SWE-agent/mini-swe-agent | 8,3k | 10-06 | Agente in 100 righe | Minimalismo |
| Sweep | sweepai/sweep | 7,7k | 2025-09 | Diventato plugin JetBrains | Ha abbandonato il modello issue → PR |
| **gh-aw** | github/gh-aw | 5,4k | 10-08 | Workflow agentici in Markdown compilati in Actions | Permessi minimi per workflow |
| Devon | entropy-research/Devon | 3,5k | 2025-05 | Fermo | — |
| background-agents | ColeMurray/background-agents | 3,3k | 10-07 | Agenti in background | — |
| auto-code-rover | AutoCodeRoverSG/auto-code-rover | 3,1k | 2025-04 | Localizzazione del guasto su AST | — |
| Agentless | OpenAutoCoder/Agentless | 2,1k | 2024-12 | Localizza → ripara → valida, senza agente | Pipeline deterministica |
| run-gemini-cli | google-github-actions/run-gemini-cli | 2,1k | 08-21 | Action per Gemini | — |
| patchwork | patched-codes/patchwork | 1,6k | 08-24 | Step di workflow componibili | — |
| codex-action | openai/codex-action | 1,3k | 10-05 | Action per Codex | — |
| loki-mode | asklokesh/loki-mode | 1,1k | 10-07 | Issue o spec → PR | — |
| cyrus | cyrusagents/cyrus | 846 | 10-07 | Agente per Linear, Slack, GitHub | Delega da Linear |
| no_human | no-human-ai/no_human | 330 | 10-05 | Da ticket a PR rivista, in locale | — |
| contrabass | junhoyeo/contrabass | 224 | 07-17 | Symphony in Go | — |
| sortie | sortie-ai/sortie | 196 | 10-08 | Ticket → sessione di agente | — |
| orbi | orbi-build/orbi | 195 | 10-06 | Label → implementazione → review indipendente → merge → release | Pipeline fino alla release |

### 5.4 Orchestratori paralleli e worktree

| Progetto | Repo | ★ | Ultimo push | Idea distintiva |
|---|---|---|---|---|
| Orca | stablyai/orca | 87k | 10-08 | Ambiente per flotte di agenti paralleli |
| claude-code-router | musistudio/claude-code-router | 38k | 09-26 | Routing di Claude Code verso altri modelli |
| vibe-kanban | BloopAI/vibe-kanban | 28k | 09-19 | Card = worktree = agente |
| Beads | gastownhall/beads | 28k | 10-07 | Memoria e tracker a grafo su git per agenti |
| opcode | winfunc/opcode | 22k | 09-18 | Checkpoint e timeline di sessione |
| Paseo | getpaseo/paseo | 20k | 10-07 | Controllo da desktop e mobile |
| Gas Town | gastownhall/gastown | 18k | 09-29 | Ruoli gerarchici, issue su Beads |
| Superset | superset-sh/superset | 15k | 10-07 | IDE per oltre 100 agenti |
| claude-code-ui | siteboon/claudecodeui | 14k | 10-07 | UI web e mobile |
| agent-orchestrator | OrchestratorInc/agent-orchestrator | 12,9k | 10-07 | Dal piano al merge con CI e review su Kanban |
| humanlayer | humanlayer/humanlayer | 11,7k | 06-19 | Human-in-the-loop strutturato |
| claude-squad | smtg-ai/claude-squad | 8,6k | 08-20 | tmux + worktree |
| emdash | generalaction/emdash | 5,9k | 10-07 | Ticket da Linear, GitHub, Jira, GitLab |
| container-use | dagger/container-use | 4,1k | 09-21 | Container e branch per agente |
| Squad | bradygaster/squad | 3,3k | 10-06 | Team di agenti per repo |
| Crystal → Nimbalyst | stravu/crystal → nimbalyst/nimbalyst | 3,1k / 1,8k | 10-07 | Sessioni parallele visuali |
| AgentsMesh | AgentsMesh/AgentsMesh | 2,4k | 09-23 | Scheduling su più macchine |
| mcp_agent_mail | Dicklesworthstone/mcp_agent_mail | 2,2k | 09-29 | Caselle di posta tra agenti |
| agent-teams-ai | 777genius/agent-teams-ai | 2,2k | 10-08 | Messaggistica tra agenti |
| dmux | standardagents/dmux | 1,8k | 08-16 | Branch e pane per agente |
| ccmanager | kbwo/ccmanager | 1,3k | 10-07 | Rilevamento dello stato della sessione |
| gascity | gastownhall/gascity | 1,3k | 10-07 | SDK estratto da Gas Town |
| parallel-code | johannesjo/parallel-code | 1k | 10-07 | Agenti affiancati con worktree |
| kandev | kdlbs/kandev | 909 | 10-08 | Review in Kanban |
| claude_code_agent_farm | Dicklesworthstone/claude_code_agent_farm | 920 | 09-21 | Più di 20 agenti in parallelo |
| uzi | devflowinc/uzi | 582 | 2025-06 | Fermo |
| cezar | open-mercato/cezar | 524 | 10-07 | Workflow e agente scelti per task |
| ntm | Dicklesworthstone/ntm | 454 | 10-07 | Pane tmux leggeri |
| terragon-oss | terragon-labs/terragon-oss | 259 | 2026-02 | Servizio chiuso, codice rilasciato |
| Sculptor | imbue-ai/sculptor | 236 | 10-07 | Agenti paralleli |
| amux | andyrewlee/amux | 162 | 10-06 | TUI |
| ccswarm | nwiizo/ccswarm | 153 | 09-14 | Sciame con worktree |

### 5.5 Multi-motore, loop autonomi, harness

| Progetto | Repo | ★ | Ultimo push | Idea distintiva |
|---|---|---|---|---|
| opencode | anomalyco/opencode | 212k | 10-07 | Agente open source, client e server separati |
| Codex CLI / Gemini CLI | openai/codex · google-gemini/gemini-cli | 128k / 107k | 10-07 | CLI ufficiali con skill e plugin |
| Cline / Kilo | cline/cline · Kilo-Org/kilocode | 70k / 28k | 10-07 | Agenti IDE (Roo Code archiviato) |
| goose | aaif-goose/goose | 55k | 10-07 | Recipe riutilizzabili |
| **codex-plugin-cc** | openai/codex-plugin-cc | 34k | 07-08 | Plugin ufficiale OpenAI: Codex come revisore o delegato dentro Claude Code |
| Archon | coleam00/Archon | 24k | 10-07 | Harness con workflow YAML deterministici |
| ralph | snarktank/ralph | 22k | 2026-02 | Loop con `prd.json` e `progress.txt` |
| loop-engineering | cobusgreyling/loop-engineering | 11k | 10-07 | Vocabolario e pattern dei loop |
| omnigent | omnigent-ai/omnigent | 10,7k | 10-08 | Meta-harness, ruoli per motore |
| ralph-claude-code | frankbria/ralph-claude-code | 9,7k | 10-07 | Criteri di uscita dal loop |
| Claude Agent SDK | anthropics/claude-agent-sdk-python | 8,2k | 10-07 | Base per orchestratori |
| Continuous-Claude-v3 | parcadei/Continuous-Claude-v3 | 3,9k | 2026-01 | Ledger e handoff di contesto |
| claude_codex_bridge | SeemSeam/claude_codex_bridge | 3,6k | 10-07 | Claude orchestra, Codex esegue |
| ralph-orchestrator | mikeyobrien/ralph-orchestrator | 3,2k | 10-05 | Ruoli che cambiano nel loop |
| ralphy | michaelshimeles/ralphy | 3k | 2026-02 | Loop multi-motore |
| myclaude | stellarlinkco/myclaude | 2,8k | 05-04 | Wrapper multi-motore |
| ralph-tui | subsy/ralph-tui | 2,5k | 09-04 | — |
| open-ralph-wiggum | Th0rgal/open-ralph-wiggum | 1,9k | 06-02 | — |
| how-to-ralph-wiggum | ghuntley/how-to-ralph-wiggum | 1,8k | 01-11 | Origine della tecnica |
| ai-devkit | codeaholicguy/ai-devkit | 1,6k | 10-07 | Memoria locale condivisa |
| ralphex | umputun/ralphex | 1,5k | 10-05 | Review multi-passata dopo l'esecuzione |
| continuous-claude | AnandChowdhary/continuous-claude | 1,4k | 09-27 | Loop che apre una PR e aspetta la CI |
| bernstein | sipyourdrink-ltd/bernstein | 1,4k | 10-07 | Governance dichiarativa |
| Fusion | Runfusion/Fusion | 1,3k | 10-06 | Software factory multi-nodo |
| claude-council | hex/claude-council | 848 | 10-06 | Stessa domanda a più agenti |
| ralph-loop-agent | vercel-labs/ralph-loop-agent | 840 | 09-16 | Loop come libreria SDK |
| claude-review-loop | hamelsmu/claude-review-loop | 724 | 03-15 | Review incrociata con Codex |
| claudexor | razzant/claudexor | 496 | 10-07 | Rotazione tra motori in base alle quote |
| machinist | owainlewis/machinist | 492 | 10-06 | — |
| LoopTroop | looptroop-ai/LoopTroop | 159 | 10-07 | Consiglio di LLM per il piano |

### 5.6 Review, verifica, guardrail

| Progetto | Repo | ★ | Ultimo push | Idea distintiva |
|---|---|---|---|---|
| PR-Agent | The-PR-Agent/pr-agent | 13k | 10-07 | `/review /improve /describe` |
| claude-code-security-review | anthropics/claude-code-security-review | 6,3k | 2026-02 | Review di sicurezza sul diff |
| claude-code-hooks-mastery | disler/claude-code-hooks-mastery | 3,9k | 2026-03 | Libreria di esempi di hook |
| vibium | VibiumDev/vibium | 2,9k | 10-07 | Livello di verifica per agenti |
| **tdd-guard** | nizos/tdd-guard | 2,4k | 10-05 | **Hook che blocca il codice senza un test fallito** |
| **cc-safety-net** | kenryu42/cc-safety-net | 1,6k | 10-08 | Hook che blocca comandi git e file distruttivi |
| kodus-ai | kodustech/kodus-ai | 1,5k | 10-07 | Review self-hosted con regole di team |
| hooks-multi-agent-observability | disler/claude-code-hooks-multi-agent-observability | 1,5k | 2026-02 | Telemetria dagli eventi hook |
| agent-qa | vostride/agent-qa | 902 | 08-03 | QA con memoria |
| karanb192/claude-code-hooks | karanb192/claude-code-hooks | 533 | 10-04 | Hook per sicurezza, costi, osservabilità |
| mira | miracodeai/mira | 358 | 09-30 | Review con indice del repo |
| sloppy | Heyosseus/sloppy | 154 | 10-05 | Rilevatori del debito lasciato dagli agenti |

### 5.7 Archiviati, rinominati, fermi

- **Archiviati.**
  - `gsd-build/get-shit-done` e `gsd-2`, spostati su `open-gsd/gsd-core`.
  - `RooCodeInc/Roo-Code`, `codegen-sh/codegen`, `All-Hands-AI/openhands-resolver`, `wshobson/commands`, `catlog22/Claude-Code-Workflow`, `google-gemini/gemini-cli-action`.
- **Rinominati.**
  - Crystal → Nimbalyst.
  - sst/opencode → anomalyco/opencode.
  - claude-flow → ruflo.
  - Sweep → plugin JetBrains.
- **Fermi da oltre 6 mesi.** Plandex, Pimzino/claude-code-spec-workflow, uzi, Devon, AutoCodeRover, Agentless.
- **Prodotti chiusi**, quindi non in tabella: Conductor (Melty), Kiro, Tessl, CodeRabbit, Greptile, Devin, Copilot coding agent.

### 5.8 Cosa cambia il censimento nelle conclusioni

1. **L'enforcement con hook esiste, ma solo in pezzi singoli.** Lo fanno tdd-guard, cc-safety-net e i gate TRUST 5 di moai-adk (questi ultimi non verificati nel codice). **Nessun workflow completo spec → PR lo usa come spina dorsale.** La tesi della sezione 0 regge e si rafforza: si possono comporre pezzi già provati.
2. **OpenSpec (71k) va aggiunto ai riferimenti per le spec.** Le *delta spec* risolvono il problema brownfield che Spec Kit ha (sezione 4.1) e che Perizie ha affrontato a mano con i «Fatti verificati».
3. **Il revisore di un altro motore è un pattern ufficiale.** OpenAI pubblica `codex-plugin-cc` per usare Codex come revisore dentro Claude Code (34k). claudex-loop e claude-review-loop fanno lo stesso. Coerente con «revisore con modello diverso» (sezione 10) e con la decisione aperta sul motore.
4. **Ticket → run isolata ha ormai una spec pubblica** (OpenAI Symphony, 28k). Se la v1 dovrà avere autonomia da tracker, conviene allinearsi a quel contratto invece di reinventare la coda di codex-workflow.
5. **La categoria più affollata è l'orchestrazione parallela** (Orca, vibe-kanban, agent-orchestrator, Gas Town). **Non conviene competere lì**: il plugin deve funzionare *dentro* questi strumenti, perché ogni agente in un worktree può avere i nostri hook.
6. **Il formato degli artefatti conta più dello strumento.** Spec Kit, OpenSpec e BMAD hanno ciascuno decine di migliaia di stelle. Conviene un formato del piano magro esportabile o compatibile, non un formato proprietario.

---

## 6. Confronto complessivo

### 6.1 Matrice per dimensione

Voti da ★ a ★★★★★. Sono un giudizio dell'analista, motivato dalle sezioni sopra.

| Dimensione | Orchestratore | codex-workflow | Perizie | Superpowers | agent-skills | GSD | Spec Kit | Kiro |
|---|---|---|---|---|---|---|---|---|
| Imposizione delle regole con codice | ★★★★★ | ★★★★ | ★ | ★★ | ★ | ★ | ★ | ★★★ |
| Qualità di piani e specifiche | ★★ | ★ | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★★ | ★★★ |
| Revisione (profondità, gravità, anti-falsi positivi) | ★★★★ | ★★ | ★★★★★ | ★★★★ | ★★★ | ★★★ | ★★ | ★★ |
| Verifica eseguita davvero (test, build, browser) | ★★★★ (ricevute, solo shell) | ★ | ★★★★ (pgTAP, Playwright, notturna) | ★★★ | ★★ | ★★★ | ★★ | ★★ |
| Isolamento | ★★★★★ | ★★★ (git sì, sandbox no) | ★★ | ★★★★ | ★ | ★★ | ★ | ★★★ |
| Gate umano ben posizionato | ★★★ | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★ | ★★★ | ★★★ |
| Memoria e conoscenza di progetto | ★ | ★ | ★★★ (ricca ma gonfia) | ★★★ | ★★ | ★★★★ | ★★★ | ★★ |
| Ripresa da crash e compattazione | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★ | ★★★★ | ★★ | ★★ |
| Autonomia a sessione chiusa | ★★★★ | ★★★★ | ★ | ★ | ★★ | ★★ | ★ | ★★ |
| Adattamento al tipo di progetto | ★ | ★ | ★★ | ★★★ | ★★ | ★★ | ★★ | ★★ |
| Costo in token | ★★★ | ★★★★ | ★ | ★★★ | ★★★ | ★★★ | ★★ | ★★★ |
| Maturità e prova reale | ★ | ★ | ★★★★★ | ★★★★★ | ★★★★ | ★★★★ | ★★★★ | ★★★★ |
| **Prova di efficacia misurata** | ★★ (fixture) | ★ | ★★ (metriche a mano) | ★★ (test di skill) | ★★ (eval su routing) | ★ | ★ | ★ |

**Lettura.**
- Le colonne «codice» (Orchestratore, codex-workflow) vincono su imposizione e ripresa, ma non sono mai state in produzione.
- Le colonne «metodologia» (Perizie, Superpowers, GSD) vincono su qualità e maturità, ma si reggono sulla disciplina.
- **Nessuno ha cinque stelle su «prova di efficacia» né su «adattamento al tipo di progetto».** È lo spazio libero.

### 6.2 Chi è il migliore, caso per caso

| Caso | Migliore disponibile oggi | Perché | Cosa gli manca |
|---|---|---|---|
| Progetto full-stack in produzione con DB, Docker, deploy (tipo Perizie) | **Flusso Perizie** (Superpowers SDD con prd-audit e ruling) | L'unico provato su uno stack reale con dry-run e deploy ordinato | Hook, monitor della CI, contesto snello |
| Libreria o pacchetto puro | **Orchestratore Goal** (concettualmente), Superpowers in pratica | Ricevute legate all'hash e scope verificato sono ideali per test isolati | Diff dell'API pubblica, mutation testing |
| Team con tracker e revisione in PR | **codex-workflow** come modello, Copilot agent e Code Review nativo come prodotti | Il gate umano sta dove il team guarda già | Test eseguiti, piano passato agli agenti |
| Sessioni lunghe e progetti a fasi | **GSD Core** | Contesto fresco, `STATE.md`, wave | Isolamento, enforcement |
| Specifiche condivise con più agenti o IDE | **Spec Kit** | Standard di fatto, flussi bug e idea | Verbosità, nessun gate eseguito |
| Bugfix | **Spec Kit (bugfix)** o Superpowers `systematic-debugging` | Verdetto `verified/partial/failed`, test di riproduzione | Blocco reale contro la cancellazione dei test |
| Prototipo e hackathon | **Nessun workflow** (Claude Code nudo) o `gsd:quick` | Ogni cerimonia costa più di quanto rende | Salire di profilo quando il prototipo diventa prodotto |
| Apprendimento cumulativo del team | **Compound Engineering** | `/ce-compound` scrive le lezioni dove servono | Verifica di cosa si scrive (rischio di gonfiare il contesto, come in Perizie) |
| Frontend e UI | Nessuno specifico. Playwright Test Agents più Chrome DevTools MCP | Verifica visuale reale | Gate visuale nel workflow, baseline protette |
| IaC e DB in produzione | Nessuno specifico | — | `plan` come gate, apply solo umano, hook di blocco |

---

## 7. Evidenze empiriche: cosa funziona davvero

Riassunto della ricerca. Gli URL completi sono nell'appendice B.

| Tema | Evidenza | Conseguenza per il plugin |
|---|---|---|
| Produttività percepita | METR 2025: -19% di tempo con AI, mentre gli sviluppatori credevano +20% [V]. Follow-up 2026 inaffidabile per selezione [V] | Misurare con metriche oggettive, mai con impressioni |
| Test verdi ≠ codice mergiabile | METR 2026: circa metà delle PR che passano SWE-bench Verified non sarebbe accettata dai manutentori [V] | Il gate non può essere solo «test verdi»: servono revisione indipendente, diff minimo e convenzioni |
| L'harness conta | Su Terminal-Bench 2.0, +13-17 punti cambiando solo l'harness [S] | Il valore del plugin sta nei gate, nel contesto e nelle condizioni di stop |
| Reward hacking | METR: o3 al 30,4% su RE-Bench; con «do not cheat» resta al 70-80% sul task testato [V] | **Le istruzioni non bastano.** Hook che proteggono test, soglie e CI |
| TDD imposto | Böckeler: TDD con circa 3x i token e qualità non migliore [V]. TDAD: il prompt TDD procedurale aumenta le regressioni, una **mappa codice-test** le riduce del 70% [V] | TDD obbligatorio solo per bugfix e contratti. Altrove serve un verificatore eseguibile più la mappa test-impatto |
| Revisione | Cognition: un revisore dedicato a contesto pulito trova circa 2 bug per PR, di cui il 58% gravi [V]. Anthropic: un revisore spinto a cercare trova sempre qualcosa, e inseguire tutto porta a over-engineering [V] | Un revisore a contesto fresco con soglia di gravità. Un panel solo ad alto rischio. Filtro di confidenza |
| Multi-agente | Anthropic: circa 15x i token, con resa su ricerca breadth-first, meno sul coding [V]. Cognition: scritture parallele generano decisioni incompatibili [S] | Subagenti per esplorazione, review e verifica. Implementazione parallela solo su file disgiunti con interfacce fissate |
| File di contesto | ICLR 2026: AGENTS.md generati da LLM peggiorano il risultato e costano oltre il 20% in più [V] | Contesto passivo piccolo, scritto da umani. Regole per modulo con `globs` |
| Skill vs contesto | Vercel: skill non invocate nel 56% dei casi; un indice da 8 KB in AGENTS.md arriva al 100% [V] | **Le regole critiche non vanno affidate all'auto-attivazione delle skill**: vanno negli hook o in un indice sempre caricato |
| Sessioni lunghe | Anthropic: initializer, `feature_list.json` con `passes` booleani, file di progresso, una feature alla volta [V] | Ledger con stato verificabile, una fetta per sessione |
| Sicurezza | Veracode: il 45% dei task generati introduce vulnerabilità OWASP [S]. Slopsquatting: 19,7% di pacchetti inesistenti [S]. Lethal trifecta [V] | SAST, secret scan, verifica dell'esistenza dei pacchetti. Niente rete né credenziali quando si legge input non fidato |
| Dimensione dei task | SWE-bench Pro: in media 107 righe su 4,1 file per task [V] | Fetta = un'unità verificabile di quell'ordine. Il tetto di circa 500 righe di piano proposto nell'handoff è coerente |

---

## 8. Profili per tipo di progetto

È il punto «per ogni caso di programmazione». Un plugin «migliore» non applica lo stesso rituale ovunque: **compone i gate in base ai percorsi toccati dal diff e al rischio del cambiamento.**

### 8.1 Matrice gate per tipo

Legenda: **O** = obbligatorio (imposto da hook), **C** = consigliato, **D** = disattivato.

Una base è comune a tutti i profili:
- build, typecheck e lint;
- suite esistente verde;
- secret scan;
- **guardia anti-indebolimento** (nessuna cancellazione o skip di test, nessuna soglia abbassata, nessuna modifica alla CI senza ruling);
- commit atomici.

| Profilo | Rilevato da | Gate O | Gate C | D | Umano obbligatorio su |
|---|---|---|---|---|---|
| Frontend web | `package.json` con react/vue/svelte/vite, `*.tsx` | E2E Playwright sui flussi toccati, screenshot confrontato, axe a11y | Visual regression, Lighthouse/Web Vitals, review a contesto fresco | Mutation, spec lunga | Nuove baseline visive, giudizio estetico |
| Backend/API | `openapi.*`, rotte, server | Contratto OpenAPI, integrazione su dipendenze reali (testcontainers), review di authz | Schemathesis, Pact, mutation sul diff | Mock dei propri servizi | Contratto pubblico, modello di autorizzazione |
| DB e migrazioni | `migrations/`, `supabase/`, `prisma/` | Migrazione su DB effimero o branch, lint DDL (squawk), test RLS (pgTAP), up/down o rollback | Dry-run su copia dei dati, panel di revisori | Qualsiasi esecuzione su DB persistente | Ogni migrazione verso ambienti persistenti (P-D) |
| IaC/DevOps | `*.tf`, `k8s/`, `helm/`, workflow CI | `validate`, `plan` read-only, policy as code (OPA/Checkov) | Stima dei costi, drift | **Ogni `apply/destroy` autonomo** (bloccato da hook) | Sempre sull'apply |
| Mobile | `Podfile`, `build.gradle`, `pubspec.yaml`, RN | Build, unit test, smoke su simulatore | E2E su simulatore, snapshot | Loop di build stretti | Dispositivo reale, store |
| Data/ML/LLM | `.ipynb`, `dvc.yaml`, eval | Seed e ambiente fissi, eval versionata, **test set sigillato** (hook in sola lettura) | Giudice LLM calibrato, pass^k | Modifiche allo scoring | Metriche e casi limite |
| Libreria | `pyproject`/`Cargo`/`package.json` con `exports` | Diff dell'API pubblica, compatibilità, esempi della documentazione eseguiti | Property-based, mutation sul diff | Refactor opportunistici | Bump semver |
| Bugfix (tipo di task) | Richiesta o issue con label bug | **Test di riproduzione rosso → verde** (ricevuta di entrambi), causa radice, diff minimo | Review leggera | Spec e piano | — |
| Refactor/legacy | Richiesta, diff ampio senza cambi di comportamento | Characterization test prima, passi piccoli con suite verde, nessun cambio funzionale misto | Codemod AST, fan-out | Cambi funzionali | Perimetro |
| Sicurezza (superficie) | Percorsi auth, crypto, pagamenti, segreti | SAST (Semgrep/CodeQL), audit dipendenze con verifica di esistenza, review dedicata | Threat model, panel | Rete e credenziali in fasi con input non fidato | Sempre |
| Performance | Richiesta | Baseline e misura prima/dopo con varianza, correttezza invariata | Flamegraph, budget in CI | Ottimizzazioni senza profilo | — |
| Prototipo | Flag esplicito | Build, smoke, secret scan | Un check visivo | Spec, review multi-agente, mutation, piani | Promozione a prodotto (passaggio a profilo superiore) |
| Game/3D | `project.godot`, Unity, three.js | Build, playtest deterministico (seed, tempo) | Screenshot-diff, budget del frame time | Test non deterministici | «Game feel» |
| Embedded | Toolchain cross, `*.ld` | Cross-build, analisi statica (MISRA), simulatore | Hardware-in-the-loop | Flashing autonomo | Tutto ciò che tocca l'hardware |

### 8.2 Livelli di rigore (ortogonali al profilo)

| Livello | Quando (deciso da uno script, non dal modello) | Fasi |
|---|---|---|
| **L0 Rapido** | Diff descrivibile in una frase, ≤2 file, <50 righe, nessuna superficie sensibile | Implementa, gate base, commit |
| **L1 Standard** | Più file o codice poco noto | Piano magro, implementazione, verifica eseguita, review a contesto fresco, PR |
| **L2 Alto** | Auth, pagamenti, migrazioni, IaC, dati personali, API pubblica, interfacce tra fette | Spec, piano magro più audit e revisione avversariale, P1, esecuzione per task, review finale, panel, gate umano prima di ogni effetto esterno |

Le regole di passaggio sono queste:
- il livello **può solo salire**, come il ratchet di Superpowers;
- un gate non eseguibile (per esempio niente simulatore iOS) diventa **«non verificato, serve umano»** nel report, mai «passato».

---

## 9. Dove nessuno arriva: le opportunità

1. **Gate imposti da hook che eseguono davvero** test, build e browser, e li legano allo SHA o all'hash dell'albero. L'Orchestratore lo fa solo per Codex, codex-workflow non esegue niente e i plugin di workflow pubblici lo chiedono solo nel prompt. Esistono hook isolati (tdd-guard, cc-safety-net, sezione 5.6), ma nessun workflow completo è costruito sopra di essi.
2. **Guardia anti-reward-hacking.** Test, soglie, CI e baseline visive sono in sola lettura per l'implementatore. Ogni deroga diventa un ruling tipizzato con contatore, e oltre una soglia scatta lo stop. Perizie ha mostrato che la deroga «invariato» senza freno diventa la norma.
3. **Profilo composito per i percorsi toccati.** Nessun concorrente lo fa: BMAD e Superpowers v6.3 scalano solo sulla «dimensione».
4. **Eval del plugin contro la baseline** con `claude plugin eval` e pass^k. Nessun concorrente dimostra di funzionare: sarebbe l'argomento più forte per dire «il migliore».
5. **Un solo stato, una sola scala di gravità, un solo coordinatore.** È la conclusione dell'Orchestratore e il problema dei plugin installati insieme.
6. **Contesto minimo e vivo.** Indice sempre caricato di pochi KB, regole per modulo con `globs`, ruling e fatti in un'unica fonte con controllo dei duplicati. Contrasta l'anti-pattern `CLAUDE.md` di 60 KB di Perizie e lo studio ICLR.
7. **Monitor della salute del ramo base.** Se la CI o la notturna di `main` è rossa, la fetta successiva non parte. Avrebbe evitato i giorni di notturna rotta in Perizie.
8. **Piano passato davvero e verificato** (correzione del difetto di codex-workflow), con `must_haves` che scendono fino al verificatore (GSD).

---

## 10. Blueprint raccomandato del plugin

> È una proposta di architettura derivata dall'analisi, non una decisione. Va passata da `superpowers:brainstorming` → specifica → piano magro dopo le risposte della sezione 12.

### 10.1 Principio

**Skill per l'intenzione, hook per l'obbligo, script per i fatti, file per lo stato.**

| Strato | Contenuto | Origine |
|---|---|---|
| Skill (`SKILL.md` più `references/` per ruolo) | Grafo delle fasi, prompt ricchi per ruolo (pianificatore, implementatore, revisore, avversario, verificatore), template del piano magro, formato dei ruling, criterio di gravità | Perizie, Superpowers, GSD |
| Hook | `PreToolUse`: blocca push, `gh pr create` e deploy senza ricevuta valida; blocca la modifica di test, CI e soglie fuori ruling; blocca `apply`, `destroy` e `db push` senza P-D. `SubagentStop` / `TaskCompleted`: verifica git e scope prima di accettare il lavoro. `Stop`: rifiuta «fatto» senza ricevute verdi sullo SHA corrente. `PostToolUse` su Bash: registra le ricevute. `SessionStart`: indice di pochi KB | Orchestratore (ricevute, scope), codex-workflow (git), `ralph-loop`, `security-guidance` |
| Script (`bin/`) | `verify-git`, `receipt`, `scope-check`, `plan-lint` (sezioni obbligatorie, tetto di righe, niente codice fuori dalle sezioni «fissato»), `profile-detect`, `ledger`, `drift-check` (firme esportate contro quelle dichiarate), `base-health` (CI di main) | codex-workflow `worktree.py`, Orchestratore `workspace.py`/`audit.py`, Perizie P3 |
| Subagenti | Implementatore con `isolation: worktree`; revisore e avversario con soli tool di lettura e **modello diverso dall'implementatore** quando possibile; verificatore che esegue i gate | Superpowers, Orchestratore |
| Orchestrazione | Livello L2: dynamic workflow (piano nel codice, output a schema, verifica avversariale). L0 e L1: inline | Funzione nativa |
| Stato | Una cartella (es. `.workflow/`) con `ledger.md`, `receipts.jsonl`, `rulings.md`, `profile.json`. **Versionata** in forma compatta, non git-ignored | Superpowers, GSD, Anthropic harness |
| Tracker | Adattatore sottile con le sei operazioni di `JiraAdapter`. GitHub Issues via `gh` di default | codex-workflow `adapters.py:48-66` |
| Gate finale | PR più merge umano, verdetto a riga JSON con gravità, file e riga, tetto di 4 revisioni poi escalation | codex-workflow, Orchestratore |
| Misura | `evals/` con task per profilo, grader deterministici, baseline senza plugin, pass^k | `claude plugin eval` |

### 10.2 Il flusso, per livello

```
L0  richiesta ─► profile-detect ─► implementa ─► gate base (hook) ─► commit
L1  richiesta ─► profile-detect ─► piano magro (plan-lint) ─► [P1 opzionale]
               ─► implementatore in worktree ─► SubagentStop: verify-git + scope + ricevute
               ─► revisore a contesto fresco (verdetto JSON) ─► ≤4 giri ─► PR ─► merge umano
L2  come L1 + spec + audit/avversario sul piano + P1 obbligatorio + esecuzione per task
               + review finale + panel per superficie + P-D su effetti esterni
```

### 10.3 Pezzo per pezzo: da dove viene

| Pezzo | Fonte | Riferimento |
|---|---|---|
| Verifica git (ramo, discendenza, commit nuovo, albero pulito) | codex-workflow | `worktree.py:43-75` |
| SHA della review ricontrollato prima della PR | codex-workflow | `coordinator.py:233-235, 399` |
| Push con `ls-remote`, ricerca della PR esistente, verifica della PR | codex-workflow | `worktree.py:77-87`, `adapters.py:241-285` |
| Verdetto a riga JSON | codex-workflow | `coordinator.py:81-94` (da estendere con gravità, file e riga, e gestire il `JSONDecodeError`) |
| Ricevute legate all'hash dell'albero | Orchestratore | `controller.py:146-163`, `workflow.py:71-82` |
| Scope per task e piano con copertura e DAG | Orchestratore | `reports.py:99-105`, `workspace.py:31-71` |
| Tetto revisioni non azzerabile, finding chiuso solo da chi l'ha aperto | Orchestratore | `audit.py:9-14, 106-112` |
| Nessuna autorità concessa in automatico | Orchestratore | `controller.py:129-134` |
| Piano magro, Fatti verificati, Decisioni con costo | Perizie | piano O, sezioni `:48`, `:89` |
| Ruling, punti di arresto P1-P4/P-D | Perizie | `tasks/todo.md`, piano O `:484-495` |
| Criterio di gravità del progetto | Perizie, prd-audit | `docs/audit/...-fetta-m-stato.md:5` |
| Revisione avversariale senza le motivazioni dell'autore | Perizie | `docs/audit/...revisione-avversariale-fetta-m.md` |
| Ledger con chiusura solo a test verdi | Superpowers | `executing-plans/scripts/task-done` |
| Brief, report e diff su file | Superpowers | `subagent-driven-development` |
| Verifica goal-backward a tre livelli | GSD | `agents/gsd-verifier.md` |
| Filtro di confidenza ≥80 | plugin `code-review` | `commands/code-review.md:20-26` |
| GO/NO-GO con rollback, regola di salto | agent-skills `/ship` | `ship.toml:71` |
| Compound (lezioni scritte dove servono) | Compound Engineering | con un tetto di dimensione, per non ripetere il `CLAUDE.md` gonfio di Perizie |

### 10.4 Cosa NON fare

- Non scrivere un controller o servizio (SQLite, systemd, webhook): Claude Code ha già hook, subagenti, workflow e `/schedule`.
- Non iniettare una meta-skill da 10 KB a ogni sessione, né usare `EXTREMELY_IMPORTANT` come meccanismo di enforcement.
- Non chiedere codice completo nei piani.
- Non usare `/goal` come gate di completamento: il suo valutatore non esegue nulla.
- Non convivere con Superpowers, agent-skills e GSD attivi in contemporanea senza decidere chi conduce.
- Non dichiarare capacità non implementate (caso ruflo, e gli specialisti morti di codex-workflow).

---

## 11. Rischi del progetto plugin

| Rischio | Probabilità | Mitigazione |
|---|---|---|
| Hook troppo rigidi che bloccano lavoro legittimo | Alta | Ogni blocco ha una via d'uscita tracciata (ruling con costo e contatore) e test sugli hook |
| Costo in token come Perizie | Media | Livelli L0, L1, L2 scelti da script. Revisore e panel solo dove serve. Modelli per ruolo |
| Multi-motore: gli hook valgono solo per Claude Code | Certa | Le skill sono condivise (`~/.agents/skills`). Gli script in `bin/` sono richiamabili anche da Codex. Gli hook Codex esistono ma con un'API diversa: serve un adattatore |
| Rilevamento del profilo sbagliato | Media | Profilo mostrato all'avvio, correggibile, può solo salire |
| Funzioni native in preview (workflows, routines, code review) che cambiano | Media | Dipendere solo da hook e subagenti, stabili. Il resto è opzionale |
| «Il migliore» non dimostrato | Alta senza eval | Suite di eval dal giorno uno, pubblicata con i risultati |

---

## 12. Decisioni aperte (dell'utente)

Dall'handoff, ancora aperte:
1. **Tracker di partenza**: GitHub Issues, Jira, o entrambi dietro un adattatore?
2. **Autonomia a sessione chiusa**: requisito della v1 o fase successiva? (`/schedule` o routines cloud la rendono possibile senza un worker.)
3. **Motore**: solo Claude Code, o anche Codex?

Nuove, emerse da questa analisi:
4. **Ambito della v1 per profili**: tutti i profili della sezione 8 o un sottoinsieme? Il mio suggerimento [Inf]: base comune più frontend, backend/API, DB e bugfix, cioè quelli dei vostri progetti reali.
5. **Rapporto con i plugin esistenti**: il nostro plugin sostituisce Superpowers e agent-skills nel flusso, oppure li richiama come «conoscenza» restando l'unico coordinatore?
6. **Pubblicazione**: plugin privato o pubblico su marketplace? Cambia il peso da dare a eval, documentazione e multi-motore.
7. **Correzioni al metodo Perizie** (handoff, sezione 7): applicarle prima a Perizie o incorporarle direttamente nel plugin?

---

## Appendice A: file locali principali

- Orchestratore:
  - `goal_orchestrator/{controller,workflow,audit,reports,workspace,store,native,runs}.py`
  - `docs/{PRD,DECISIONI,DA-RISOLVERE,RICERCA-GITHUB}.md`
  - `evidence/`
- codex-workflow:
  - `workflow_bridge/{worktree,coordinator,workflow,transitions,reviews,specialists,adapters,codex,store,security}.py`
  - `prompts/*.txt`
  - `docs/*.md`
- Perizie:
  - `CLAUDE.md`
  - `docs/superpowers/plans/`
  - `docs/avvio-fetta-o.md`
  - `docs/audit/2026-10-07-*`
  - `tasks/todo.md`
  - `.superpowers/sdd/*/progress.md`
- Plugin:
  - `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1`
  - `~/.claude/plugins/cache/addy-agent-skills/agent-skills/0.6.9`
  - `~/.claude/get-shit-done`
  - `~/.claude/skills/prd-audit`

## Appendice B: fonti web principali

**Plugin, metodologie e progetti GitHub**
- obra/superpowers: https://github.com/obra/superpowers · release notes https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md
- github/spec-kit: https://github.com/github/spec-kit
- addyosmani/agent-skills: https://github.com/addyosmani/agent-skills
- GSD Core: https://github.com/open-gsd/gsd-core
- BMAD-METHOD: https://github.com/bmad-code-org/BMAD-METHOD
- Compound Engineering: https://github.com/EveryInc/compound-engineering-plugin
- ruflo, audit dei tool: https://github.com/ruvnet/ruflo/discussions/1513
- Marketplace ufficiale Anthropic: https://github.com/anthropics/claude-plugins-official
- Roo Code (archiviato): https://github.com/RooCodeInc/Roo-Code

**Documentazione Claude Code**
- Hook: https://code.claude.com/docs/en/hooks
- Subagenti: https://code.claude.com/docs/en/sub-agents
- Skill: https://code.claude.com/docs/en/skills
- Plugin: https://code.claude.com/docs/en/plugins-reference
- Eval dei plugin: https://code.claude.com/docs/en/plugin-evals
- Workflow: https://code.claude.com/docs/en/workflows
- Worktree: https://code.claude.com/docs/en/worktrees
- `/goal`: https://code.claude.com/docs/en/goal
- Code review: https://code.claude.com/docs/en/code-review
- Routines: https://code.claude.com/docs/en/routines
- Agent teams: https://code.claude.com/docs/en/agent-teams
- Best practices: https://code.claude.com/docs/en/best-practices

**Altri strumenti**
- Kiro: https://kiro.dev/docs/specs/ · https://kiro.dev/docs/hooks/
- GitHub Copilot coding agent: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent
- Aider: https://aider.chat/docs/usage/modes.html

**Evidenze**
- METR, studio 2025: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- METR, aggiornamento 2026: https://metr.org/blog/2026-02-24-uplift-update/
- METR, PR non mergiabili: https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/
- METR, reward hacking: https://metr.org/blog/2025-06-05-recent-reward-hacking/
- SWE-bench Pro: https://arxiv.org/html/2509.16941v2
- Fowler/Böckeler su TDD: https://martinfowler.com/articles/exploring-gen-ai/tdd-in-the-agent-loop.html
- Fowler/Böckeler su SDD: https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- TDAD: https://arxiv.org/html/2603.17973v1
- Cognition, multi-agenti: https://cognition.com/blog/multi-agents-working
- Anthropic, sistema di ricerca multi-agente: https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic, building effective agents: https://www.anthropic.com/research/building-effective-agents
- Anthropic, context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, harness per agenti long-running: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, eval per agenti: https://anthropic.com/engineering/demystifying-evals-for-ai-agents
- AGENTS.md (ICLR 2026): https://arxiv.org/pdf/2602.11988
- Vercel, AGENTS.md contro skill: https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Willison, lethal trifecta: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/

**Profili per tipo di progetto**
- Playwright Test Agents: https://playwright.dev/docs/test-agents
- Supabase branching: https://supabase.com/docs/guides/deployment/branching
- Neon branching: https://neon.com/docs/introduction/branching

---

## 13. Aggiornamento dell'8 ottobre: decisioni e approfondimenti

### 13.1 Decisioni prese dall'utente

| Tema | Decisione |
|---|---|
| Tracker | **GitHub Issues** |
| Autonomia a sessione chiusa | v1 solo interattiva. **Da fare dopo**: avvio da etichetta GitHub tramite Action |
| Harness | **Si parte da Claude Code**. **Da fare dopo**: nucleo portabile (skill, script, git hook, controlli GitHub) e adattatori per altri harness |
| Profili | Da tarare sul lavoro reale (13.2). Il backend deve coprire anche un backend locale senza Supabase |
| Kanban | Richiesta dall'utente. **Ibrida SQLite locale + GitHub Projects** (13.3), confermata |
| Dashboard | **Da fare dopo** la v1. Nella v1 solo la base dati che la alimenterà (13.3, 13.4) |
| Profilo AI/LLM | **Incluso nella v1** (13.5) |

### 13.2 Su cosa si lavora davvero (sainapse-v3)

Il campione è `VIBE/SITO SAINAPSE/sainapse-v3`: 1.798 commit dal 05/11/2025 al 08/10/2026.

**Dove cade il lavoro.**
- Il 27% dei commit è `fix`.
- I file toccati, in ordine:
  - pagine cliente, preventivi e dashboard: circa 32%;
  - documentazione: circa 24%;
  - edge function: circa 12%;
  - test e guardie: circa 8%;
  - migrazioni: circa 6%;
  - CI e script: circa 5%;
  - 3D: circa 3%.
- Negli ultimi 3 mesi crescono sicurezza, parte legale e DPA, e guardie.
- AI e LLM compaiono in circa il 15-20% dei commit.

**Come si verifica oggi.** Il progetto ha già un sistema di verifica:
- `npm run verifica`, circa 85 s: guardie ast-grep, ESLint, gate, typecheck e test con DB;
- un hook `PostToolUse` che lancia le guardie dopo ogni modifica;
- `test:db` su Supabase locale per branch.

Playwright non c'è: le verifiche visive passano da Chrome DevTools MCP.

**Backend locale senza Supabase.** In questo progetto non esiste, salvo il Cloudflare Worker `workers/private-gate` (si avvia con `wrangler dev`) e gli script `tsx` e Python.

**Conseguenze per il plugin.**
- Il plugin deve **orchestrare e riusare** i comandi di verifica del progetto, non reinventarli. Serve un file di configurazione per progetto che dichiari quali comandi usa ogni profilo.
- Il profilo backend ha varianti per tipo di runtime:
  - edge function Supabase;
  - Worker Cloudflare;
  - server locale generico (Node o Python, eventualmente con Docker Compose).

  Per ogni variante il profilo definisce comando di avvio, health check e test di integrazione.

### 13.3 La kanban di Hermes e la proposta

**Com'è fatta in Hermes.**
- È una funzione **nativa di Hermes Agent**: un SQLite in `~/.hermes/kanban.db`.
- **Stati**: `triage`, `todo`, `scheduled`, `ready`, `running`, `blocked`, `review`, `done`, `archived`.
- **Presa in carico**: atomica, con lease di 15 minuti e heartbeat.
- **Dipendenze**: un task figlio parte solo quando il padre è chiuso.
- **Blocchi tipizzati**: `dependency`, `needs_input`, `capability`, `transient`.
- **Circuit breaker** dopo 2 fallimenti.
- **Accesso**: dashboard web, CLI e 15 tool per gli agenti.
- **Collegamenti esterni**: nessun ponte con GitHub o Jira.

**Da riprendere.**
- **Lo stato lo scrive il ponte, non l'agente.** «L'agente ha finito» non vuol dire «accettato».
- Blocchi tipizzati.
- Presa in carico con lease.
- Riconciliazione periodica, perché gli hook sono best-effort.

**Proposta.** Usare **GitHub Projects v2 come kanban**:
- colonne uguali alle fasi del workflow;
- campo «Stato» aggiornato dagli script del plugin a ogni transizione, con `gh project item-edit`;
- automazioni native per chiudere i task: PR unita → Done.

Pro e contro:
- **A favore**: niente infrastruttura, una sola fonte di verità, consultabile da telefono.
- **Contro**: rate limit, scope `project`, nessuna vista di sessioni e token.

**Revisione dopo la domanda dell'utente («sicuro niente SQLite?»).** La proposta «solo GitHub» ha tre limiti concreti:
- **la presa in carico non è atomica**: GitHub non offre un «prendi solo se libero». Due sessioni in worktree parallele possono prendere la stessa issue;
- **lo stato fine è troppo fitto per GitHub**: heartbeat, fasi interne, round di revisione, token e costi. Scriverlo su GitHub costa chiamate, rate limit e rumore nel board;
- **la dashboard (da fare dopo) ha comunque bisogno di un archivio locale**. Partire con un JSONL vuol dire migrarlo dopo.

**Proposta ibrida, come Hermes più un ponte verso GitHub.**

| Dove | Cosa contiene | Chi è la fonte di verità |
|---|---|---|
| SQLite locale (`sqlite3` di Python, nessuna dipendenza, modalità WAL) | presa in carico con lease e heartbeat, fase interna, blocchi tipizzati, eventi, round di revisione, costi | **il lavoro in corso**: chi ci lavora ora e come sta andando |
| GitHub Issues + Projects | cosa fare, colonna del board, PR, merge | **il lavoro deciso e accettato**: cosa va fatto e cosa è stato accettato |

Regole:
- scrivono nel DB solo gli script del plugin, mai l'agente direttamente;
- verso GitHub vanno solo le transizioni significative (cambio di colonna, blocco «serve te», PR aperta);
- all'avvio e periodicamente gli script riconciliano: issue chiusa o PR unita su GitHub prevale sul DB;
- se il DB si perde, si ricostruisce da GitHub più l'esportazione degli eventi.

### 13.4 Dashboard locale (riferimento: Archon)

**Archon oggi** (MIT, circa 23,6k stelle, v0.11.1) **non è più un command center.** È un motore di workflow YAML con Web UI, che vede **solo le run che lancia lui** tramite il Claude Agent SDK. Il suo pack `sdlc` (`archon-ship`: issue → piano → PR rivista) è un'**alternativa all'intero plugin**, non una dashboard.

**Le alternative.**
- **Kanban con raccolta dei propri dati**:
  - Orchestrator.inc: Apache-2.0, kanban derivata da sessione, PR e CI;
  - Kandev: AGPL;
  - Orca: MIT.
- **Osservabilità via hook**: disler, senza licenza, esempio datato.
- **Nativo**: `claude agents` (agent view), con stato via `claude agents --json`.
- **Da evitare**: Vibe Kanban, il cui servizio cloud ha chiuso ad aprile 2026.

**Proposta (opzione B).**
- GitHub Projects come kanban.
- Una **dashboard locale leggera** alimentata dagli hook del plugin, che mostra:
  - sessioni attive;
  - «in attesa di te»;
  - fase del workflow;
  - costi via OpenTelemetry;
  - worktree;
  - link a issue e PR.
- Gli eventi finiscono nel SQLite locale della 13.3, così la dashboard spenta non fa perdere nulla e, quando arriverà, legge un archivio già pieno.
- **La dashboard non avvia né ferma agenti**: per quello c'è `claude agents` / `claude --bg`.

**Stima** (dell'analista): 3-6 giorni per eventi e vista live, più 1-2 per la sincronizzazione con Projects.

**Tempi.** Decisione dell'utente: la dashboard arriva **dopo la v1**.

### 13.5 Profili della v1

Ogni profilo si attiva in base ai file toccati e usa i comandi dichiarati nel file di configurazione del progetto.

| Profilo | Si attiva su | Cosa controlla |
|---|---|---|
| **Base** (sempre) | qualunque modifica | comando di verifica del progetto, lint, typecheck sui file toccati, test esistenti, nessun test rimosso senza motivo |
| **Frontend** | componenti, pagine, stili | test dei componenti, build, verifica visiva nel browser su desktop e mobile |
| **Backend** | edge function, Worker, server | tre varianti (edge function Supabase, Worker Cloudflare con `wrangler dev`, server locale generico Node o Python, eventualmente con Docker Compose). Per ciascuna: avvio, health check, test di integrazione |
| **Database** | migrazioni, policy, schema | migrazione su DB locale (Supabase locale o Postgres generico), controlli RLS e permessi, dry-run mostrato all'utente prima di toccare un DB reale |
| **Sicurezza** | auth, gate, dati personali, parte legale | revisione di sicurezza sul diff e livello di rigore alto |
| **AI/LLM** | prompt, chiamate a modelli, agenti, giudici | vedi sotto |
| **Bugfix** (si somma agli altri) | issue di tipo bug | prima un test che riproduce il bug, poi la correzione |

**Profilo AI/LLM, tarato su sainapse-v3.** Cosa c'è oggi nel progetto:
- molte edge function chiamano modelli: la pipeline `lap-run-pipeline` con i suoi agenti, `chatbot-judge`, `chatbot-lead-extract`, `chatbot-sentiment-batch`, `analyze-website`, `gemini-proxy`;
- tracciamento opzionale con Langfuse (`langfuse-ingest`, `_shared/langfuse.ts`);
- un set di riferimento `eval/gold_v1_raw.json` con 14 conversazioni, **non collegato a nessun test automatico**.

Cosa controlla il profilo:
- **eval prima e dopo**: se la modifica tocca un prompt o la logica di un agente, il set di casi di riferimento gira sulla versione vecchia e su quella nuova e l'esito confronta i punteggi. Un peggioramento oltre soglia blocca come un test rosso;
- **output strutturato**: ogni risposta che il codice interpreta passa da uno schema validato, con test sui casi malformati;
- **robustezza della chiamata**: timeout, retry, fallback e messaggio d'errore gestito;
- **chiavi e costi**: nessuna chiave lato client, ID del modello dichiarato in configurazione, stima di token e costo per chiamata;
- **prompt injection**: l'input dell'utente non finisce mai nelle istruzioni di sistema senza separazione, con casi di test dedicati.

Il primo lavoro concreto per questo profilo è trasformare `eval/gold_v1_raw.json` in un eval eseguibile.

**Fuori dalla v1**: 3D, release e deploy.

