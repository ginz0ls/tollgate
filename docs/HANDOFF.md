# Handoff: confronto dei flussi ad agenti e plugin da costruire

Data: 8 ottobre 2026.
Stato: **analisi conclusa, nessuna implementazione avviata**. Tre decisioni dell'utente sono aperte (sezione 6): finché non arrivano, non si progetta né si scrive codice.
Destinatario: un agente nuovo, con contesto pulito, che riprende da qui.

> **Documento storico.** Stato all'8 ottobre 2026 (mattina). Le decisioni della sezione 6 sono state prese e il progetto è un repository git. Le decisioni in vigore sono in `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 18); per riprendere il lavoro si parte da quella e dal piano principale `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
Sede del progetto (decisione dell'utente, 08/10): `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow`, cartella autonoma. Non è ancora un repository git. L'analisi è nata in una sessione della Piattaforma Perizie. I percorsi assoluti dei tre progetti stanno nella sezione 2; nel resto del documento i percorsi relativi si riferiscono alla cartella del progetto di cui si parla.

## 1. Cosa ha chiesto l'utente

In una sola conversazione, in quest'ordine:

1. Confrontare l'**Orchestratore Goal** (`/home/crucco/MEGA/BIZ/VIBE/orchestratore-goal`) con il flusso usato per la **Piattaforma Perizie** (questo repository): approccio migliore, pro e contro.
2. Aggiungere al confronto **codex-workflow** (`/home/crucco/MEGA/BIZ/VIBE/Company AgentOS/Hermesz/codex-workflow`). È nato per Hermes con Jira, ma va valutato pensando a **un plugin generico, non solo per Hermes, costruito da noi come skill**.
3. Un parere sul metodo di Perizie: **prima il piano generale, poi un piano dettagliato per ogni fetta**.
4. Questo documento.

Il documento non autorizza lavoro: il prossimo passo lo decide l'utente.

## 2. Progetti considerati e fonti lette

### Cartelle dei tre progetti (percorsi assoluti)

**Orchestratore Goal**: `/home/crucco/MEGA/BIZ/VIBE/orchestratore-goal` (repository git locale, senza remoto)
- `goal_orchestrator/`: controller (`controller.py`, `workflow.py`, `audit.py`, `native.py`, `rpc.py`, `store.py`, `workspace.py`, `models.py`…)
- `tests/`: suite `unittest`
- `docs/`: PRD, decisioni, mancanze, ricerca sulle alternative, handoff d'origine; `docs/audit/` con i rapporti dell'audit
- `policy/`: `local-review.md` (revisione predefinita), `prd-audit/SKILL.md` e `ADATTAMENTO.md` (audit esteso), `source-hashes.json`
- `skills/`: copie delle skill usate dagli agenti (`incremental-implementation`, `test-driven-development`, `source-driven-development`, `code-review-and-quality`)
- `integration/orchestratore-goal/SKILL.md`: skill per invocarlo da Codex o Claude Code
- `evidence/`: matrice di accettazione e prove native (JSON e MD)
- `tasks/`: `todo.md`, `plan.md`
- `.runs/`: run di prova sulle fixture sintetiche (`native-e2e/`, `local-simple-proof/`)
- `.tools/codex-0.161.0/`: runtime Codex locale

**codex-workflow (Hermes)**: `/home/crucco/MEGA/BIZ/VIBE/Company AgentOS/Hermesz/codex-workflow` (sottocartella del repository git `/home/crucco/MEGA/BIZ/VIBE/Company AgentOS`, remoto `ginz0ls/company-agentos`)
- `workflow_bridge/`: ponte (`coordinator.py`, `worker.py`, `workflow.py`, `transitions.py`, `reviews.py`, `specialists.py`, `hierarchy.py`, `adapters.py`, `codex.py`, `worktree.py`, `security.py`, `server.py`, `store.py`, `reconciliation.py`…)
- `prompts/`: un prompt per ruolo (`sol-planner`, `terra-developer`, `sol-reviewer`, `security-`, `testing-`, `docs-specialist`)
- `tests/`: suite `unittest`
- `docs/`: `architecture.md`, `operations.md`, `setup.md`, `troubleshooting.md`, `canonical-source.md`
- `systemd/`: unità `workflow-bridge.service` e `workflow-bridge-worker.service` (disattivate)
- `deploy/nginx-hermes-webhooks.conf`, `scripts/git-askpass.sh`
- `config.example.json`, `config.evminmax.example.json`: configurazioni d'esempio, senza segreti
- Accanto, non letti: `../REPORT-HERMES.md`, `../docs/`, `../sales-department/` (pacchetto separato, vedi `docs/canonical-source.md`)

**Piattaforma Perizie**: `/home/crucco/MEGA/BIZ/VIBE/Commercialista mombello/Piattaforma Perizie` (repository git, remoto `ginz0ls/piattaforma-perizie`)
- `CLAUDE.md`: regole del progetto e lezioni di tutte le fette
- `docs/superpowers/specs/`: specifica (fonte di verità)
- `docs/superpowers/plans/`: due piani generali (`2026-09-24-modulo-perizie-piano-generale.md`, `2026-10-07-assistente-operativo-piano-generale.md`) e i piani delle fette A–O
- `docs/avvio-fetta-*.md`: istruzioni per l'agente che esegue ogni fetta
- `docs/audit/`: audit della specifica e dei piani L e M, con le revisioni avversariali
- `docs/validazione-mombello.md`: decisioni da validare col dominio (Z-…)
- `docs/misure/`, `docs/valutazioni/`: misure e valutazioni dei modelli
- `tasks/todo.md`: stato, ruling e rilievi di ogni fetta
- `.superpowers/sdd/`: registri di `subagent-driven-development` (fuori da git)
- Memoria di Claude Code: `/home/crucco/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Commercialista-mombello-Piattaforma-Perizie/memory/`
- Skill globali usate dal flusso: `~/.claude/skills/` (`prd-audit` e altre) e i plugin `superpowers` e `agent-skills`

### File letti (da rileggere se serve un dettaglio)

I percorsi sono relativi alla cartella del progetto.

| Sistema | File |
|---|---|
| Orchestratore Goal | `README.md`, `AGENTS.md`, `docs/PRD.md`, `docs/DECISIONI.md`, `docs/DA-RISOLVERE.md`, `docs/RICERCA-GITHUB.md`, `docs/HANDOFF.md`, `policy/local-review.md`, `evidence/ACCEPTANCE.md`, `evidence/local-review.md`, `tasks/todo.md` |
| codex-workflow | `README.md`, `docs/architecture.md`, `docs/operations.md`, `docs/canonical-source.md`, `prompts/*.txt`, `config.example.json`, `workflow_bridge/specialists.py`, `workflow_bridge/reviews.py` |
| Perizie | `CLAUDE.md`, `docs/superpowers/plans/*` (piani generali e delle fette), `docs/avvio-fetta-o.md`, `docs/audit/2026-10-07-audit-piano-fetta-m-stato.md`, memoria del progetto (`fetta-o-stato`, `piani-magri`, `decisioni-su-delega`) |

I test dell'Orchestratore e di codex-workflow **non sono stati eseguiti**: i numeri sotto vengono dalle loro evidenze e dal conteggio delle righe.

## 3. I tre sistemi: fatti verificati

### Orchestratore Goal
- Controller Python con la sola libreria standard: circa 1.700 righe in `goal_orchestrator/`, 1.400 di test. Le evidenze dichiarano 102 test (`docs/DA-RISOLVERE.md`).
- Motore: **Codex app-server**, un Goal nativo e un thread nuovo per ogni fase (piano, implementazione, revisione, correzione). Claude Code è solo documentato, mai provato (`README.md`, «Integrazione Codex e Claude Code»).
- Stato in SQLite e servizio systemd utente: continua a IDE chiuso, riprende dallo stesso thread dopo un crash.
- Garanzie applicate dal codice: worktree dedicato, pianificatore e revisore in sola lettura, rete spenta, skill ed evidenze legate agli hash, revisione locale con un massimo di 4 revisioni (`policy/local-review.md`). In alternativa c'è `--audit strict` (prd-audit, 30 cicli).
- **Vietati** push, deploy e migrazioni remote. Consegna = worktree verificato, senza commit.
- Provato **solo su fixture sintetiche** (`add(a,b)`, COMPLETE in 244 s, `evidence/local-review.md`). La run reale «Legal MCP» è in pausa e non conclusa (`evidence/usage-limit-resume.md:60`).
- Storia: è partito con l'audit esteso obbligatorio (fino a 27/30 cicli sul proprio codice). Poi l'utente ha chiesto «ok semplifica ma fai in modo che funzioni» (`docs/DECISIONI.md`, punto 6): da 16 passate obbligatorie a una revisione completa.

### codex-workflow (Hermes)
- Ponte **Jira → Hermes → Codex → GitHub**, Python con la sola libreria standard: circa 3.600 righe in `workflow_bridge/`, 2.100 di test.
- Ingresso: webhook Jira autenticato. Una coda durevole in SQLite (lease, chiavi di idempotenza) è servita da un worker systemd separato.
- Fasi `new → planning → development → review → human_review → done`, specchiate negli stati Jira. Ruoli fissi: Sol pianifica e rivede, Terra implementa.
- Controlli nel codice: prima della revisione HEAD deve discendere dalla base, il ramo deve essere quello assegnato e il worktree pulito. Dopo la revisione: push, verifica con `ls-remote`, PR creata e riletta. **«Completata» solo dopo un merge su GitHub fatto da un umano autorizzato.**
- Il revisore chiude con una riga leggibile da macchina: `WORKFLOW_REVIEW: {"material_failure": …}` (`prompts/sol-reviewer.txt`). Il tetto è di 10 bocciature, poi escalation (`reviews.py:8`). Gli specialisti (sicurezza, test, documentazione) si scelgono dalle label Jira (`specialists.py:12`).
- Prompt dei ruoli di 3-5 righe, **nessuna skill**.
- Stato: per il README è un *«inactive local scaffold… not production-ready»*. I servizi systemd sono disattivati e i percorsi della documentazione appartengono a un'altra macchina (`/home/ecivini/...`).

### Flusso Perizie
- Sequenza: specifica → piano generale → piano magro per ogni fetta → `prd-audit` del piano e revisione avversariale a contesto fresco → `docs/avvio-fetta-X.md` → `superpowers:subagent-driven-development` (implementatore e revisore Opus per ogni task) → revisione di tutta la fetta → `--dry-run` mostrato all'utente → deploy → `merge --ff-only` (ramo per fetta, N1).
- Decisioni prese su delega dell'utente, registrate come ruling («scelta — perché — costo se sbagliato»). Ci si ferma solo ai punti di arresto (P1–P4, P-D).
- **In produzione**: 390 commit dal 23/09 al 07/10, fette A–O distribuite.
- Dimensioni dei piani: generali di 80 e 69 righe; fette A–K da 1.300 a 4.200 righe (codice completo); fette L–O da 280 a 960 righe (piani magri, dal 30/09).
- Revisione avversariale dei piani: N 0 critici, 12 importanti, 14 minori; O 1 critico, 10 importanti, 11 minori. Durante l'esecuzione di O, comunque, 31 ruling (R-1…R-31).

## 4. Conclusioni del confronto

| | Orchestratore Goal | codex-workflow | Flusso Perizie |
|---|---|---|---|
| Gate finale | Revisione indipendente con hash | **PR e merge umano** | Coordinatore, `--dry-run` all'utente, deploy |
| Imposizione delle regole | Codice | Codice | Prompt e disciplina del coordinatore |
| Autonomia a sessione chiusa | Sì | Sì (da webhook) | No |
| Stack con Docker, servizi locali, deploy | **No** (rete spenta, deploy vietato) | Push e PR sì, deploy no | Sì |
| Skill e conoscenza del progetto | Skill legate agli hash, nessuna memoria di progetto | Nessuna | Molta, anche troppa (`CLAUDE.md`) |
| Tetto di revisioni | 4 | 10 | Nessuno |
| Maturità | Fixture sintetiche | Non attivo | Produzione |

Il parere dato all'utente:
- **Perizie e progetti simili** (Docker, Supabase locale, deploy, molte decisioni di dominio): il flusso Perizie resta il migliore. L'Orchestratore non farebbe nemmeno girare i test: `supabase start`, Edge Runtime, server finto sulla porta 54399, Playwright.
- **Orchestratore**: adatto a task delimitati con test isolati (pacchetti puri come `packages/motore`, librerie, script).
- **codex-workflow**: il punto forte è il gate umano messo dove il team guarda già (Jira, PR, Discord). Il punto debole sono i ruoli poveri (niente skill, nessun criterio di gravità). Inoltre più di metà del codice serve all'avvio da evento (webhook, firma, deduplica, coda, riconciliazione).

## 5. Proposta: il plugin costruito come skill

Vincolo di fondo: **una skill non è un servizio**. Sono istruzioni e script che girano dentro una sessione. Divisione proposta:

| Pezzo | Dove va |
|---|---|
| Grafo delle fasi, ruoli, criteri di gravità del progetto, formato del verdetto | Skill: `SKILL.md` più `references/` con un prompt per ruolo, ricco come le revisioni di Perizie |
| Controlli deterministici: HEAD discende dalla base, worktree pulito, ricevuta di revisione legata allo SHA, scope dei file | Script del plugin, resi obbligatori dagli **hook** (es. `PreToolUse` che blocca `git push`/`gh pr create` senza ricevuta valida). È il modo di ottenere «il controllo non vive nel workspace dell'agente» senza scrivere un controller |
| Isolamento | Subagenti con `isolation: "worktree"`; revisore con i soli strumenti di lettura |
| Tracker | Adattatore sottile: GitHub Issues con `gh` (default proposto), Jira via MCP o API come opzione. Il grafo delle fasi non conosce il tracker |
| Gate umano | PR e merge umano, come codex-workflow |
| Autonomia | Fuori dalla skill: `/schedule` (agenti cloud a orario) o un piccolo worker esterno che apre una sessione per ticket |
| Conoscenza del progetto | Un file di regole per progetto passato a ogni ruolo («Regole già emerse» di Perizie) e un registro dei ruling |

Cosa prendere da ciascuno:
- **codex-workflow**: gate PR e merge umano, riga di verdetto leggibile da macchina, controllo «commit reale, ramo giusto, worktree pulito».
- **Orchestratore**: ricevute legate allo SHA, tetto basso (4 revisioni), una decisione pendente invece di un sì automatico per ogni richiesta di autorità in più.
- **Perizie**: skill vere per ogni ruolo, criteri di gravità del progetto (vedi `docs/audit/2026-10-07-audit-piano-fetta-m-stato.md`, «Criterio di gravità»), ruling, punti di arresto, piani magri.

Fuori dalla prima versione: webhook, coda SQLite, servizio systemd. Servono solo all'avvio da evento.

## 6. Decisioni aperte (all'utente, non prenderle su delega)

1. **Tracker di partenza**: GitHub Issues, Jira, o entrambi dietro un adattatore?
2. **Autonomia a sessione chiusa**: requisito della prima versione o fase successiva? Se è un requisito, servono `/schedule` o un worker, e l'esperienza di codex-workflow su coda e idempotenza torna utile.
3. **Motore**: solo Claude Code, o anche Codex? Le skill in `~/.agents/skills/` sono condivise con Codex (`~/.claude/CLAUDE.md`), mentre gli hook sono propri di Claude Code.

## 7. Parere sul metodo di Perizie (piano generale e piani delle fette)

Da tenere: il dettaglio scritto subito prima dell'esecuzione, sul codice reale («Fatti verificati» riverificati su HEAD); un piano generale breve che tiene dipendenze, interfacce, copertura della specifica e punti di arresto; le decisioni prese nel piano, non da chi esegue.

Problemi osservati:
1. **Decisioni rimandate alla fetta dopo** e sparse nelle tabelle (es. piano L, L11 e L12: «la fetta M decide»).
2. **Il piano diventa anche il resoconto** (differenze «Eseguito» riscritte nel piano O). Gli stessi fatti stanno in cinque posti: specifica, piani, `avvio-fetta-X.md`, `CLAUDE.md`, `tasks/todo.md`. Un `CLAUDE.md` enorme pesa su ogni sessione e su ogni subagente.
3. **Rischio di dominio**: tutte le decisioni sono «bozze da validare col dottor Mombello», ormai fino a Z-233 in `docs/validazione-mombello.md`. Quindici fette poggiano su decisioni non confermate.
4. **Fette troppo grandi**: M si è dovuta dividere in M1 e M2 durante il lavoro.

Correzioni proposte, **non ancora approvate né applicate**:
- tetto di circa 500 righe per il piano di una fetta; oltre, si divide nel piano generale;
- revisione avversariale del piano solo per migrazioni, sicurezza e interfacce fra fette;
- piano congelato all'approvazione: le differenze vanno solo in ruling e `todo.md`;
- sezione «Aperti per la fetta X» nel piano generale, da svuotare prima di approvare il piano di X;
- punto di controllo con Mombello ogni 2-3 fette, sulle 5-10 decisioni che reggono le altre;
- sfoltire `CLAUDE.md` spostando le note delle fette chiuse in `.claude/rules/*.md` con `globs:`.

## 8. Cosa non fare

- Non avviare l'Orchestratore né codex-workflow su progetti reali. Il primo dichiara che nessun PRD reale va eseguito implicitamente (`AGENTS.md`), il secondo non è attivo.
- Non modificare `orchestratore-goal` né `codex-workflow`: qui sono stati solo letti.
- Non toccare `CLAUDE.md` di Perizie né i piani finché l'utente non approva le correzioni della sezione 7.
- Non scrivere codice del plugin prima delle risposte della sezione 6. Il percorso previsto è: `superpowers:brainstorming` → specifica → piano magro.

## 9. Primo passo per chi riprende

Leggere questo documento, poi chiedere all'utente le tre decisioni della sezione 6 (una per volta se non sono chiare) e dove applicare per prime le correzioni della sezione 7. Rileggere i file della sezione 2 solo quando serve un dettaglio, non per ricostruire il confronto.
