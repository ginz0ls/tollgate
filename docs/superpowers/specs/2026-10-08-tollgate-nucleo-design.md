# tollgate: specifica del nucleo (sotto-progetto A)

Data: 8 ottobre 2026.
Revisione: **21**: esiti delle verifiche P2 (`docs/verifiche/2026-10-09-p2-verifiche.md`): eventi d'ingresso `post_agent`, `post_skill` e `prompt_submit` (taglio di `maxTurns` in background e alla ripresa); `record` come operazione. Decisioni del piano P2 riportate in questa revisione: 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15 e 22; ruling del controller di P2 sulle sezioni 3.2, 6.2, 6.3, 6.6, 7.1, 7.4, 8.1-8.5, 11.3, 12.2, 18.2 e 18.5. Revisione 20: esiti delle verifiche P0 (`docs/verifiche/2026-10-08-p0-esiti.md`): ripresa degli implementatori per nome, taglio di `maxTurns` riconosciuto in `PostToolUse Agent`, modalità del gate riconosciuta dal messaggio della GET di protezione, forma degli identificativi JUnit per strumento, comandi `!` fuori dagli hook. Revisione 19: must-have legati ai test, `tollgate stats`, `attenzione` diviso tra «da leggere» e «informative» (decisione dell'utente dopo l'analisi dei problemi d'uso). Revisione 18: pratiche delle software house (task piccoli, standard del revisore, disaccordo istruito, budget per task, Definition of Done, report a campi fissi, spec con «cosa non fare»), da `docs/RICERCA-ORGANIZZAZIONE.md` (decisione dell'utente). Revisione 17: profili verticali e trasversali, precedenza per specificità, CI del progetto non più protetta. Revisione 16: implementatori e revisori per area, specialisti finali in L2, tetto di 3 skill. Il catalogo dei profili è in `2026-10-08-tollgate-profili-verticali.md`. La revisione 14 ha chiuso l'audit come «sospeso»; i residui sono nel file di stato. Le revisioni precedenti sono nella sezione 20.
Stato: **audit sospeso, pronta per il piano** (`docs/audit/2026-10-08-audit-spec-nucleo-stato.md`).
Fonti: `docs/REPORT-CONFRONTO-WORKFLOW.md`, `docs/COSA-TENERE.md`, `docs/RICERCA-PAPER.md`. I codici R e H usati nel testo sono spiegati nella sezione 19.

---

## 0. Glossario

**Lavoro e repo**

| Termine | Significato |
|---|---|
| **lavoro** | Un'issue GitHub portata fino a una PR. È una riga di `work_items`. Nel nucleo **un'issue corrisponde a un lavoro e a una PR** |
| **lavoro attivo** | Un lavoro non chiuso e non abbandonato. Le regole complete valgono in due casi: **nelle sessioni legate al lavoro**, su qualunque ramo e in qualunque directory, e **per ogni comando nel suo worktree** (6.6) |
| **sessione legata** | Una sessione registrata in `work_items.sessions`: quella che ha eseguito `start` sul lavoro e ogni sessione il cui `SessionStart` ha la directory dentro il worktree del lavoro. Il legame non si scioglie con un `cd` |
| **sessione viva** | Una sessione con almeno un evento negli ultimi `stale_minutes`. È l'unica soglia usata per le sessioni |
| **ciclo vuoto** | Un giro o ciclo di audit senza rilievi `moderate` o più gravi. Ha `outcome: empty` anche se contiene rilievi `minor` |
| **coordinatore** | La sessione principale di Claude Code, che parla con l'utente |
| **implementatore** | `tollgate:implementer` o `<plugin>:implementer-<area>` (6.3), e per sicurezza **ogni** altro subagente che non è nell'elenco di sola lettura (4) |
| **task del piano** | Un task di un piano scritto con writing-plans (`### Task N`). Lo esegue `tollgate:execute` (6.3) |
| **giro di correzione** | Un nuovo lancio di `tollgate:implementer` sullo stesso task dopo che il revisore del task ha chiesto modifiche. Contato in `tasks.fix_rounds` |
| **SHA di un file** | Lo SHA del blob (`git hash-object`), non del commit: resta uguale dopo un rebase o un merge squash |
| **base del lavoro** | Lo SHA da cui parte il ramo (`work_base_sha`). Si riallinea solo con `sync` o con un atto dell'utente |
| **base del subagente** | Lo SHA del momento in cui un subagente parte (`agent_base_sha`). Una ripresa non la cambia: i commit «nuovi» di un implementatore sono tutti quelli dalla sua prima partenza |
| **chiave del repo** | L'URL di `origin` normalizzato: senza protocollo né `.git`, in minuscolo (`github.com/proprietario/nome`) |
| **repo attivo** | Un repo con `tollgate.toml` sulla punta del ramo predefinito di `origin` (7.1). **Negli altri repo tollgate non fa niente** |
| **cartella di stato** | `~/.local/state/tollgate`: contiene DB, log, file del contesto e interruttore. È una per macchina: `OFF` spegne tollgate in tutti i repo e in tutte le sessioni |
| **file di tollgate** | `tollgate.toml`, `.github/workflows/tollgate-*.yml`, `.github/actions/tollgate-*/**`, `.github/tollgate/**`. Gli altri workflow sono codice del progetto: profilo `ci` ad alto rischio e controlli di `guard` (9.2) |
| **file protetti** | I file di tollgate, più `.tollgate/waivers/**`, `docs/superpowers/reviews/**` (li scrivono solo hook e CLI), le impostazioni di Claude Code, `.git/hooks/**`, `.git/config`, la cartella di stato e i plugin installati sotto `~/.claude/plugins/` (7.4) |

**Flusso e controlli**

| Termine | Significato |
|---|---|
| **fase** | `spec_audit`, `plan`, `approval`, `execution`, `review`, `pr_open`, `closed`, `blocked` (12.3) |
| **livello** | Quanto rigore richiede il lavoro: L0, L1 o L2 (5). Non va confuso con i «due livelli di controllo» della sezione 1 |
| **scope** | I file che il piano autorizza a creare o modificare. Le deroghe si contano a parte |
| **ricevuta** | Il risultato registrato di un comando di verifica su uno SHA. Stati possibili: `green`, `red`, `empty`, `uncounted`, `unverified` (8.1) |
| **deroga** | Un'eccezione dichiarata su un file, con motivo e costo (8.3) |
| **blocco** | Un arresto del lavoro con un tipo (`needs_you`, `test_spec_conflict`, `dependency`, `permission`, `transient`). Lo chiude l'utente |
| **veto dell'hook** | La risposta `deny` o `block` di un hook. È una cosa diversa dal blocco del lavoro |
| **atto dell'utente** | Un'operazione registrata quando l'utente digita un comando `/tollgate:*` (8.4) |
| **in attesa** | Una deroga che aspetta `approve waiver`, o un effetto esterno vietato che aspetta `approve effect`. `open-pr` rifiuta finché ce n'è uno |
| **intento** | Un'azione esterna (push, PR, effetto) registrata prima di eseguirla, così una ripresa non la ripete |
| **ciclo di revisione** | Un passaggio di revisione finale che produce un verdetto (10). È diverso dai «giri di correzione» dei task del piano e dai «giri avversariali» sulla spec |
| **verdetto** | L'esito JSON di un revisore di tollgate: `ok`, `needs_fix` o `needs_you` |
| **gate** | Il controllo che decide se una PR è pronta. Quello che conta gira **su GitHub** (9); in locale ne gira una copia, solo per avere un riscontro rapido |
| **modalità del gate** | `protected`: la protezione del ramo impedisce il merge senza controlli verdi. `detect`: la protezione non è disponibile (repo privato con GitHub Free) e `tollgate-sentinel` **rileva dopo** i merge e i push non verificati (9.3). La misura `init` con le credenziali dell'utente e la scrive in `[gate] mode`; tutti gli altri la leggono da lì |
| **controllo obbligatorio** | Uno stato GitHub richiesto dalla protezione del ramo: `tollgate/guard`, `tollgate/verdict` |
| **attenzione** | Lo stato `tollgate/attention`: diventa rosso quando c'è qualcosa da leggere prima del merge. **Non** è obbligatorio |
| **gravità** | La gravità di un rilievo: `blocker`, `major`, `moderate` o `minor`, definite in `[severity]` |
| **must-have** | Le proprietà che il lavoro deve avere per dirsi fatto, elencate nella sezione `## Must-have` del piano. Il revisore finale le controlla una per una |
| **checkpoint** | Il file `docs/superpowers/reviews/<N>/checkpoint.md`, scritto da `tollgate status --checkpoint [--note <testo>]`: fase, file chiave, prossimo passo, note del coordinatore. `SessionStart` lo inietta dopo un `/clear` |
| **`patch-id`** | L'impronta di `git patch-id --stable` sul diff dalla base: due rami con lo stesso `patch-id` contengono le stesse modifiche anche dopo un rebase |
| **lenti e punti di vista** | Il metodo dell'audit della spec (6.2). Le lenti sono dieci: coerenza verticale, orizzontale e interna, verificabilità, criteri osservabili, copertura, proiezione futura, fatti, lacune ricorrenti, completezza. I punti di vista sono otto: chi esegue, chi usa, chi attacca, chi paga, chi arriva dopo, lo scettico, il caso limite, chi integra |

**Lingua.** Comandi, file, fasi, stati, tipi e colonne sono in inglese. I testi rivolti all'utente e la documentazione sono in italiano.

---

## 1. Scopo e modello di fiducia

tollgate è un plugin per Claude Code. Porta un lavoro **da un'issue GitHub a una PR verificata**. Il merge lo fa sempre una persona, su GitHub.

Il flusso usa **Superpowers** per brainstorming e writing-plans, e i suoi TDD e debugging dentro gli implementatori. **L'esecuzione del piano è di tollgate**: `tollgate:execute` prende il posto di subagent-driven-development (6.3), da cui deriva (licenza MIT, fonte citata nella skill). La revisione finale e la chiusura del ramo sono `/tollgate:finish` (6.4, 10).

**Perché un'esecuzione propria.** subagent-driven-development lancia implementatori e revisori come subagenti `general-purpose` anonimi: tollgate dovrebbe capire chi è chi leggendo il prompt, esentarne gli script e bloccarne la revisione finale, e ogni versione nuova di Superpowers lo romperebbe. Con agenti propri il tipo arriva negli hook come `agent_type` (`tollgate:implementer`), e il riconoscimento è deterministico.

### 1.1 Due livelli di controllo

| | Dove gira | A cosa serve | Cosa garantisce |
|---|---|---|---|
| **Guardrail locali** | Hook di Claude Code, sulla macchina dell'utente | Fermano **subito** le scorciatoie e gli errori onesti del modello: test modificati, «fatto» senza prove, file fuori scope, effetti esterni non approvati, codice scritto dal coordinatore | **Nessuna garanzia contro un agente che lavora apposta per aggirarli.** Con Bash sulla stessa macchina può alterare DB, configurazione e processi locali (attacchi documentati in `docs/audit/2026-10-08-revisione-avversariale-2-spec-nucleo.md`) |
| **Gate su GitHub** | I workflow di 9.1, più la protezione del ramo quando c'è | Ricalcolano **da zero** i fatti della PR: comandi del gate, identificativi dei test della base, test-guard, coerenza dello scope, file di tollgate invariati | In modalità `protected`: una PR non entra nel ramo predefinito senza `tollgate/guard` e `tollgate/verdict` verdi e senza il merge dell'utente. In modalità `detect`: ogni commit che entra nel ramo predefinito senza quei controlli verdi viene **segnalato dopo**, con uno stato rosso sul commit e un'issue (9.3) |

### 1.2 Cosa resta fuori dalla garanzia

Questi limiti sono dichiarati:
- **L'agente che usa le credenziali GitHub dell'utente.** Lo limitano i guardrail e il token separato consigliato (11.2). In modalità `protected` non può però soddisfare la protezione pubblicando lui `tollgate/verdict`: la sorgente è fissata su GitHub Actions, e uno stato pubblicato con un altro token non conta (verificato in P0, 9.3).
- **I comandi `!` digitati dall'utente** nel prompt di Claude Code non passano da nessun hook (verificato in P0): possono cambiare file e ramo senza i guardrail locali. Il gate su GitHub ricalcola comunque i fatti della PR.
- **Gli effetti esterni.** Hanno un solo livello di controllo: quando arriva la PR sono già avvenuti.
- **Il codice scritto nel lavoro ed eseguito in locale** dai test o da `verify`, con l'ambiente ripulito (8.1).
- **Asserzioni rese più deboli o compensate con asserzioni banali.** Le cerca il revisore finale (R3).
- **La qualità del giudizio dei revisori.**
- **Il codice della PR che falsifica l'esito dei propri test.** Resta visibile nel diff.
- **Scope e deroghe sono dichiarati dall'agente.** Il gate ne verifica la coerenza, non la legittimità. Gli atti locali non sono verificabili da GitHub.
- **Le PR da rami che non sono `tg/*`** ricevono dal gate solo i controlli sui test, con `attenzione` rosso.
- **Una serie di PR L0.**
- **Il sabotaggio deliberato della CI**, per esempio workflow aggiunti per pubblicare stati falsi. La modalità rinforzata con GitHub App arriva dopo la v1.
- **In modalità `detect` il merge non è impedito, solo rilevato.** Su un repo privato con GitHub Free la protezione del ramo non esiste, e nemmeno i rulesets (verificato su docs.github.com, «GitHub's plans», e in P0: entrambe le API rispondono 403). L'agente con le credenziali dell'utente potrebbe anche coprire la segnalazione; la cronologia degli stati del commit resta comunque visibile.

### 1.3 Fuori dal nucleo

| Cosa | Dove |
|---|---|
| Profili per tipo di file con i loro controlli (R8, R11, R12) | Sotto-progetto **B**. Il contratto è già nel nucleo (11.4) |
| **Piano principale e fette**, sotto-issue, kanban con GitHub Projects, riconciliazione, decisioni dell'utente sui rilievi (R13) | Sotto-progetto **C**. Nel nucleo si usa un'issue per fetta, con il contratto minimo di 5 |
| Eval completi, prove a componenti spenti, costo e contesto dei subagenti (R15) | Sotto-progetto **D** |
| Gli agenti concreti per area (frontend, sicurezza, database…) e i loro profili | Sotto-progetto **B**. Il nucleo dà il contratto (`skills`, `agent`, `reviewer`, `reviewer_skills`, `final_specialist`, `kind`, `cross`, `dod`) e l'instradamento (6.3) |
| Revisori specialisti esterni in L2, Codex come revisore, controllo delle letture dei revisori | Dopo la v1 |
| Modalità rinforzata con GitHub App, dashboard, avvio da etichetta, portabilità, lezioni apprese, mutation testing | Dopo la v1 |

**Agganci già pronti per i sotto-progetti:**
- `events` con tipi definiti (18.4);
- `acts` con sorgente e autore;
- `subagents` con token e durata;
- `findings.user_decision`;
- il contratto dei profili;
- `[components]` come mappa aperta;
- il blocco JSON versionato nella PR (18.1);
- il registro dei controlli e l'adattatore dell'harness (3.2);
- le variabili per i test (3.1).

---

## 2. Decisioni prese

| Tema | Decisione |
|---|---|
| Harness | Claude Code. Il codice separa l'adattatore per Claude Code dal modello interno |
| Tracker | GitHub Issues, tramite `gh` |
| Autonomia | Interattiva |
| Flusso | Superpowers per brainstorming, writing-plans, TDD e debugging (11.1); esecuzione con `tollgate:execute`; chiusura con `/tollgate:finish` |
| Unità di lavoro | Un'issue = un lavoro = una PR |
| Controllo autorevole | Su GitHub; i controlli locali sono guardrail |
| Garanzia v1 | Scorciatoie e manomissioni locali |
| Stato locale | SQLite nella cartella di stato |
| Pianificatore | Il coordinatore |
| Audit della spec | In L2: giri avversariali sempre; audit a lenti quando la spec prevede più fette (6.2) |
| Revisione | Revisore finale e verificatore di tollgate (10) |
| Specializzazione | **Profili verticali**: ogni area ha un implementatore e un revisore del task propri, con skill, prompt, strumenti e modello propri, a tutti i livelli; lo specialista **sostituisce** l'agente generico, quindi non aggiunge subagenti. Nella revisione finale gli specialisti si **aggiungono** al revisore generale solo in L2 e solo per i profili con `final_specialist` valorizzato: `security` e `database`, più `ci` che usa lo specialista di `security` (scelta dell'utente sulla CI, revisione 17). Al massimo 3 skill obbligatorie per agente. Decisione dell'utente, 08/10/2026. Coerente con `docs/ricerca/06-revisori-specializzati.md`: nessun revisore in più, contesto e regole diversi per area, verifica per rilievo invariata (nota in `docs/RICERCA-PAPER.md`, 2.12) |
| Merge | Solo l'utente, su GitHub |
| Livello | Lo script lo alza; lo abbassa solo l'utente, con un atto |
| Effetti esterni | Negati finché non c'è un atto, oppure ammessi da un'eccezione in sola lettura (8.5) |
| Pubblicazione | Privato ora, pubblico poi |
| Lingua | Identificatori in inglese; testi in italiano |
| Sistemi | Linux e macOS, Python ≥ 3.11 |
| Requisiti del repo | Remote GitHub, `gh` autenticato, Actions attive. Protezione del ramo se il piano la offre, altrimenti modalità `detect` (9.3) |
| Repo privati senza Pro | Supportati in modalità `detect`: rilevazione dopo, non impedimento (decisione dell'utente, 08/10/2026) |
| Repo senza test | Solo con `allow_no_tests = true`: `empty` vale come `green`, sempre con `attenzione` rosso |

---

## 3. Struttura del plugin

```
tollgate/
  .claude-plugin/plugin.json        dependencies: superpowers
  .claude-plugin/marketplace.json   allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]
  skills/
    start/      /tollgate:start #N [L1|L2]           anche il modello
    finish/     /tollgate:finish                     anche il modello
    status/     /tollgate:status                     anche il modello (sola lettura)
    init/       /tollgate:init [--update]            anche il modello (solo proposta)
    approve/    /tollgate:approve <oggetto> ...      solo l'utente (firme in 8.4)
    resolve/    /tollgate:resolve <id> <nota>        solo l'utente
    reopen/     /tollgate:reopen spec|plan <motivo>  solo l'utente (6.2)
    sync/       /tollgate:sync                       solo l'utente
    adopt/      /tollgate:adopt #N                   solo l'utente
    abandon/    /tollgate:abandon #N                 solo l'utente
    cleanup/    /tollgate:cleanup                    solo l'utente
    setup/      /tollgate:setup                      solo l'utente
    off/ on/    /tollgate:off [ore], /tollgate:on    solo l'utente
    execute/    esecuzione del piano, un task alla volta   anche il modello (6.3)
    spec-audit/ metodo dell'audit a lenti (versione di prd-audit incorporata, con l'accordo dell'autore)
  agents/
    implementer.md        tools: Read, Edit, Write, Bash, Grep, Glob, Skill
    task-reviewer.md      tools: Read, Grep, Glob, Bash
    final-reviewer.md     tools: Read, Grep, Glob, Bash
    finding-verifier.md   tools: Read, Grep, Glob, Bash
    plan-adversary.md     tools: Read, Grep, Glob
    spec-adversary.md     tools: Read, Grep, Glob, WebFetch
    spec-auditor.md       tools: Read, Grep, Glob, WebFetch
  hooks/hooks.json   hooks/run
  bin/tollgate          CLI Python, solo libreria standard
  gate/                 workflow (9.1) e copia del CLI proposti da init
  statusline/statusline.sh   templates/tollgate.toml   tests/   evals/
```

«Solo l'utente» vuol dire due cose: la skill ha `disable-model-invocation: true` (verificato), e l'atto viene registrato da `UserPromptExpansion` (8.4).

**Modello degli agenti.** Ogni agente di tollgate dichiara un `model` predefinito nel suo file; `[review] models` lo sostituisce per agente. Senza dichiarazione l'agente erediterebbe il modello della sessione, di solito il più costoso.

| Agente | Modello predefinito | Perché |
|---|---|---|
| `implementer` | `inherit` | `tollgate:execute` può indicare un modello per task (`model` di `Agent`), come faceva subagent-driven-development: più economico per i task meccanici |
| `task-reviewer` | `sonnet` | Revisione di un solo task, diff piccolo |
| `final-reviewer` | `inherit` | Il giudizio sull'intero ramo è il punto in cui un modello più debole costa di più (subagent-driven-development usa il più capace per la stessa revisione) |
| `spec-adversary`, `plan-adversary` | `inherit` | Pochi giri, alto impatto |
| `spec-auditor` | `sonnet` | Fino a 30 cicli: il costo domina |
| `finding-verifier` | `sonnet` | Verifica puntuale di rilievi già formulati |



### 3.1 Sottocomandi di `bin/tollgate`

| Sottocomando | Chi lo chiama | Cosa fa |
|---|---|---|
| `start <N> [--level]` | Skill `start` | 6.1 e 12.4 |
| `verify` | Agente | 8.1 |
| `waiver add`, `block open` | Agente | 8.3 |
| `review prepare`, `finish check`, `finish open-pr [--update]` | Skill `finish` | 6.4. Il push forzato è ammesso solo dentro `sync`, o una volta dopo `approve rebase` |
| `act apply <id>` | Skill `approve` | Applica un atto `approve` registrato: per `approve spec` e `approve plan` scrive il file di approvazione (18.3) |
| `status`, `init --propose`, `init --update` | Agente | Sola lettura, oppure proposte scritte dalla CLI in `docs/superpowers/tollgate-init/` |
| `sync`, `adopt`, `cleanup`, `abandon` | La skill omonima, **dopo** l'atto | L'hook registra solo l'atto (8.4), senza rete e senza lavoro lungo. La skill lancia il sottocomando, che rifiuta se non trova un atto `pending`, non scaduto, della stessa sessione e con lo stesso oggetto, e lo consuma. 6.5 e 12.4 |
| `db restore` | L'utente, **solo dal terminale** (nessuna skill) | 12.1. Non richiede un atto: funziona solo se il DB non supera `PRAGMA integrity_check` e chiede conferma su un terminale interattivo |
| `task start <k> [--fix]`, `task start --from-findings <ciclo>`, `task start --from-gate`, `task review-prepare <k>`, `task done <k>` | Skill `execute` | Gestiscono `tasks` con le transizioni di 6.3: lancio dell'implementatore e brief, task di correzione dai rilievi, brief del revisore del task, chiusura |
| `stats [--since <data>] [--work <N>]` | Utente, agente | Sola lettura, dagli eventi: tempo per lavoro e per fase, veti per regola, blocchi `needs_you`, deroghe e `approve finding` (gli «scavalcamenti»), ore con tollgate spento, token per lavoro e per agente, giri di correzione e cicli di revisione. Serve a vedere con i numeri se tollgate rallenta più di quanto protegge; la kanban di C e gli eval di D partono da qui |
| `events --after-seq <n>` | C, D, strumenti esterni | Esporta in JSONL, ordinati per `seq`, gli eventi con `seq` maggiore di `n`, con la busta di 18.4. È l'unico contratto di lettura: il DB è privato di tollgate e lo schema può cambiare con le migrazioni. La chiave di un evento tra più DB è (`host`, `seq`) |
| `gate run`, `gate evaluate`, `gate guard`, `gate base-ids` | `finish check` e i workflow | Stesso codice in locale e su GitHub |
| `status --checkpoint` | Skill e coordinatore | Scrive il checkpoint (0) |
| `hook <evento>` | Solo `hooks/run` | Adattatore per Claude Code |

**Variabili per i test.** Sono `TOLLGATE_STATE`, `TOLLGATE_GH` (un finto `gh`) e `TOLLGATE_TEST_CONFIG`. Hanno effetto solo se nella cartella di `TOLLGATE_STATE` c'è il file sentinella `.tollgate-test`, che la suite di test crea in una cartella temporanea. Il guardrail nega `TOLLGATE_` nei comandi Bash.

**Limite.** Un agente può comunque importare il modulo Python. Questo riguarda solo i guardrail locali.

### 3.2 Principi di design

**Configurazione.**
- Nei lavori: `tollgate.toml` si legge dalla base del lavoro.
- Altrove: dalla punta del ramo predefinito di `origin`.
- Mai dal working tree.
- `start` e `finish` fanno prima `git fetch origin`.
- Gli hook non usano mai la rete.

**Registro dei controlli.** Ogni controllo è un modulo in `bin/tollgate_checks/` con una costante `CHECK = {"api": 1, "events": [...], "component": "...", "order": n}` e una funzione `decide(event, ctx) -> decision`. I moduli girano in ordine di `order`; il nome rompe solo i pareggi. Un modulo con `api` diversa non viene caricato e il suo evento riceve `deny` con un avviso: un controllo che manca non deve passare in silenzio. B aggiunge moduli senza toccare quelli esistenti.

**Eventi d'ingresso** (elenco chiuso, diverso dai tipi di log di 18.4): `session_start`, `prompt_expansion`, `pre_edit`, `post_edit`, `pre_bash`, `post_bash`, `pre_agent`, `pre_send_message`, `pre_mcp`, `subagent_start`, `subagent_stop`, `subagent_handback`, `post_agent`, `post_skill`, `prompt_submit` (`UserPromptSubmit`). Ognuno porta `session`, `cwd`, `agent_id`, `agent_type` e l'input dello strumento così come arriva.

**Contesto** (`ctx`, in sola lettura): la configurazione risolta (base del lavoro o punta del predefinito), letture in sola lettura per ogni tabella di 12.2 (`work_items`, `tasks`, `scope`, `receipts`, `subagents`, `acts`, `intents`, `blocks`, `findings`), un accesso a git (diff dalla base, file, impronte) e l'ora. Un modulo non scrive mai nel DB: chiede di farlo con `record`. `ctx.approved_waivers(work)` restituisce gli id delle deroghe che hanno un atto `approve waiver` nel lavoro, in qualunque stato dell'atto (decisione 10 del piano P2): è l'API che P3 usa per `open-pr`.

**Decisioni:** `allow`, `deny <motivo>`, `inject <testo>`, `record <operazione> <data>`: un'operazione di un elenco chiuso del motore, che scrive anche il suo evento di 18.4. Si combinano così: il primo `deny` vince; gli `inject` si concatenano in ordine dentro il budget (6.3); i `record` vengono scritti tutti, anche dopo un `deny`.

**Adattatore dell'harness.** Traduce l'input degli hook in eventi d'ingresso e la decisione nella risposta di Claude Code. D aggiunge un adattatore per un altro harness senza toccare i moduli.

**Altre regole.**
- Componenti spegnibili (R10).
- I pattern di percorsi usano il dialetto di `.gitignore`, implementato una volta in `tollgate_analysis/globs.py`. I pattern di comandi (`[external_effects] allow`, comandi configurati) seguono fnmatch: `*` attraversa `/`.
- Prima si estende ciò che esiste (H44).

---

## 4. Ruoli

| Ruolo | Chi è | Cosa fa | Come è imposto |
|---|---|---|---|
| Utente | — | Alza il livello, approva spec e piano in L2, approva gli atti, risolve i blocchi, fa il merge | Atti dell'utente; merge su GitHub |
| Coordinatore | Sessione principale | Dialogo, brainstorming, spec, piano, avvio dei subagenti. **Non scrive codice**, tranne in L0 | In L1 e L2, fase `execution`: Edit e Write sul codice negati se manca `agent_id`, che c'è solo nei subagenti (verificato) |
| Implementatore | L'implementatore del profilo del task, oppure `tollgate:implementer` (6.3); ogni altro subagente **non** elencato in `[review] readonly_agents` è trattato allo stesso modo | Un task del piano alla volta, con TDD e le skill dei profili del task | Brief scritto dalla CLI, scope, scrittore unico, skill usate, `SubagentStop` (8.1) |
| Revisore del task | Il revisore del profilo del task, oppure `tollgate:task-reviewer` (6.3) | Controlla il task: aderenza al brief e qualità (rubrica derivata da subagent-driven-development), più le regole dell'area | Sola lettura (7.3); verdetto JSON (18.5) |
| Specialista finale | L'agente `final_specialist` dei profili attivi che ne dichiarano uno, solo in L2 | Revisione dell'intero ramo per la sua area, in aggiunta al revisore finale | Sola lettura; i suoi rilievi passano dal verificatore come gli altri (10) |
| Avversario della spec, auditor della spec, avversario del piano | `tollgate:spec-adversary`, `tollgate:spec-auditor`, `tollgate:plan-adversary` | 6.2 | Niente scrittura, niente Bash |
| Revisore finale | `tollgate:final-reviewer` | Confronta il lavoro con piano, must-have e scope; cerca casi speciali e asserzioni indebolite (R3) | Brief scritto dallo script; controllo di sola lettura (7.3) |
| Verificatore | `tollgate:finding-verifier` | Conferma o scarta ogni rilievo registrato | Brief scritto dallo script dalla tabella `findings` (8.6) |

**Come si passano il lavoro.** Brief su file in ingresso, report su file o messaggio finale salvato dall'hook in uscita. Al coordinatore tornano al massimo 1-2K token più il percorso del report (R7). Il lavoro di un subagente resta sotto circa 30K token di contesto: brief e skill precaricate si dimensionano su questo, e la soglia si tara con gli eval di D (R7, `docs/ricerca/03-contesto-memoria.md`).

---

## 5. Livelli

| Livello | Quando | Percorso |
|---|---|---|
| **L0** | Diff dalla base entro 2 file, 50 righe aggiunte più rimosse, 4.000 byte; niente percorsi sensibili né binari | Implementazione nella sessione, `verify`, `finish` |
| **L1** | Il caso normale | writing-plans → `plan-check` → esecuzione → revisione finale |
| **L2** | Percorsi sensibili, etichette sensibili, autore esterno al repo, oppure tua scelta | brainstorming → spec → audit della spec → `approve spec` → piano → avversario → `approve plan` → esecuzione → revisione finale |

**Come si calcola il livello.** È il **massimo** tra tre valori:
- il livello ricalcolato sul diff, dopo ogni Edit o Write, a ogni `git commit` e a `finish`;
- quello stimato all'avvio da etichette e autore dell'issue;
- quello che hai digitato tu.

**Abbassamento.** `/tollgate:approve level <L> <motivo>` fissa un tetto. Il tetto resta finché il diff non tocca un percorso sensibile nuovo, e viene scritto nella PR.

**L0 che cresce.** Il lavoro sale a L1 e la fase torna a `plan`.

**Nel gate.**
- Il blocco JSON della PR porta il livello dichiarato.
- Il gate calcola il minimo dai percorsi e dalle etichette dell'issue (lette con una GET da «Closes #N»).
- Se il livello dichiarato è sotto il minimo senza un tetto dichiarato → `verdict` rosso; con un tetto dichiarato → `attenzione` rosso (9.2).

**Spec con più fette.** La spec le elenca nella sezione `## Fette previste`, come elenco numerato (`1. <titolo>`): il numero di voci è il numero di fette, e senza sezione le fette sono 1. Dopo `approve spec`:
1. `start` propone **un'issue per fetta**: le crei tu, oppure le crea l'agente dopo il tuo `approve effect`;
2. il lavoro corrente continua con la prima fetta;
3. le altre diventano lavori a sé, **dopo il merge della prima** (la spec approvata deve stare sul ramo predefinito), e partono con `/tollgate:start #M --spec <percorso>`: lo digiti tu, quindi è un dato fidato. `start` accetta `--spec` solo se sul ramo predefinito ci sono la spec e il suo file di approvazione (`spec-approval`, 18.3) con lo stesso SHA della spec; allora la fase iniziale è `plan` e `work_items.spec_path` registra il percorso. Se la spec è cambiata dopo l'approvazione, `start` lo dice e propone di partire da `spec_audit`, con un nuovo giro e una nuova `approve spec`. Il testo dell'issue non decide mai la fase.

Il collegamento tra le issue è compito di C.

---

## 6. Ciclo di vita

### 6.1 Avvio

```
/tollgate:start #N [L1|L2] [--spec <percorso>]
  0. prerequisiti   repo attivo; Python ≥ 3.11; Superpowers nell'intervallo; remote GitHub e gh;
                    ramo predefinito con commit; gate installato; CLI in .github/tollgate/ della
                    stessa versione del plugin (altrimenti avviso e init --update). Se manca: rifiuto.
                    Scrive il ramo predefinito in `git config tollgate.defaultBranch` (7.1)
  1. controlli      checkout principale pulito; stati obbligatori del ramo predefinito verdi
                    (altrimenti avviso e conferma); issue chiusa → avviso e conferma; ramo o PR remoti
                    già esistenti per l'issue → li mostra e propone di adottarli
  2. lavoro         lavoro attivo per (repo, issue) → ripresa (12.4); ramo locale tg/<N>-* senza
                    riga (crash durante un avvio) → propone adopt invece di creare -2;
                    altrimenti nuovo lavoro
  3. livello        5
  4. worktree       tg/<N>-<slug> (slug [a-z0-9-], ≤ 40, con -2… se esiste); poi la riga in
                    work_items, nella stessa transazione della fase iniziale:
                    L0 execution, L1 plan, L2 spec_audit (con --spec valido: plan)
  5. entrata        la skill entra nel worktree con EnterWorktree (accetta un worktree
                    esistente, 16); la sessione è già legata perché ha eseguito start (0).
                    Se EnterWorktree non riesce, stampa «cd <percorso> && claude» e chiude qui
                    la sessione di avvio: la nuova sessione si lega al suo SessionStart
```

**In ripresa i passi 0 e 1 cambiano.** Restano rifiuti solo «repo attivo» e «Python». Rete assente, `gh` non raggiungibile, stati del ramo predefinito non verdi e checkout principale sporco diventano avvisi. Il checkout principale sporco è sempre e solo un avviso, anche al primo avvio: tollgate non lo usa.

**L'issue non è fidata.** Il suo testo passa ai modelli dentro file, marcato come dato, e non entra mai in un comando shell. Se l'autore è esterno al repo, il lavoro va in L2.

### 6.2 Spec e piano

**brainstorming non arriva a writing-plans da solo.** In 6.4.1 brainstorming passa a writing-plans appena l'utente approva la spec in chat (verificato, `brainstorming/SKILL.md`). In `spec_audit` e `approval` la scrittura sotto `docs/superpowers/plans/` è negata, e la skill `start` dice al coordinatore di fermarsi dopo la spec e far partire l'audit. Un piano si registra solo in fase `plan`.

```
L2, spec_audit: brainstorming → spec (con «Fette previste») → giri avversariali
                → [audit a lenti se le fette previste sono più di una] → /tollgate:approve spec
L1 e L2, plan:  checkpoint + /clear → writing-plans (la skill dà le intestazioni, 7.5) → plan-check
                L1 → scope e plan_sha registrati → execution
                L2 → plan-adversary (il piano si corregge) → approval → /tollgate:approve plan
                     → scope e plan_sha registrati alla versione approvata → execution
```

**Audit della spec.**
0. **Forma della spec in L2.** Oltre a «Fette previste», la spec ha le sezioni `## Tane di coniglio` (punti incerti che possono far esplodere il lavoro, con la scelta fatta per ciascuno) e `## Cosa non fare` (ciò che resta fuori, anche se sembra utile). L'avversario della spec le controlla: una tana di coniglio senza scelta è un rilievo `major` (Shape Up, il «pitch»).
1. **Giri avversariali.** A ogni giro `tollgate:spec-adversary` riparte in un subagente nuovo e chiude con una riga JSON (18.3). Il coordinatore corregge la spec. Si va avanti finché un giro non trova né `blocker` né `major`. Il tetto è `spec_rounds` (4): se il quarto giro trova ancora `blocker` o `major`, si apre `needs_you`, e `resolve` lo chiude come **«avversariale sospeso»**.
2. **Audit a lenti.** Parte solo se «Fette previste» è maggiore di 1. Prima del primo ciclo la skill mostra il costo (da 16 a `spec_audit_cycles` cicli, più i giri avversariali) e chiede conferma. Se non confermi, si apre `needs_you`, e `resolve` lo chiude come «audit a lenti sospeso». Segue il metodo `spec-audit`: dieci lenti, otto punti di vista, un ciclo per ogni subagente nuovo. Al coordinatore torna solo il riepilogo.
   - L'audit si chiude quando ogni punto di vista ha dato due cicli vuoti (0) di fila.
   - Il tetto è `spec_audit_cycles` (30). Al tetto si apre `needs_you`, e `resolve` lo chiude come **«audit a lenti sospeso»**.
3. **Report.** `SubagentStop` salva ogni giro in `docs/superpowers/reviews/<N>/<kind>-<n>.md` (18.3). Lo stato dell'audit a lenti sta in `docs/superpowers/reviews/<N>/spec-lens-stato.md`, che `SubagentStop` rigenera dalla tabella `spec_audit` a ogni ciclo. L'`outcome` di ogni report lo calcola l'hook da `counts`, non lo dichiara il subagente. Il coordinatore committa i report insieme a spec e piano.
4. **Approvazione.** `/tollgate:approve spec <fette>`: digiti il numero di fette, che deve essere uguale a quello di «Fette previste». È accettato solo se valgono **entrambe** le condizioni:
   - l'ultimo giro avversariale non ha `blocker` né `major`, oppure è «avversariale sospeso»;
   - con più di una fetta, l'audit a lenti è chiuso oppure «audit a lenti sospeso». Con una fetta sola questa condizione non si applica.

   La spec del lavoro è il primo file nuovo sotto `docs/superpowers/specs/` nel ramo; il primo giro avversariale la registra in `work_items.spec_path`. `approve spec` è accettato solo se lo SHA della spec nell'ultimo giro o ciclo, di qualunque tipo, coincide con quello attuale. Se l'audit a lenti ha portato correzioni, l'ultimo passo è un giro avversariale di conferma sulla versione finale.

   Poi `act apply` scrive `docs/superpowers/reviews/<N>/spec-approval.md` (18.3), che il coordinatore committa con la spec. È la prova versionata dell'approvazione: la usano `start --spec`, `adopt` e il gate. `approve plan` scrive allo stesso modo `plan-approval.md`.

   **Blocco dopo l'approvazione.** La spec non si modifica più da `approve spec`; il piano non si modifica più dalla registrazione dello scope (in L1 dopo `plan-check`, in L2 ad `approve plan`). Il blocco vale solo nelle fasi successive a quella dell'approvazione: in `spec_audit` la spec resta modificabile anche se `spec-approval.md` esiste, e dopo `reopen` torna modificabile il documento riaperto. `approve plan` rifiuta se lo SHA attuale della spec non è quello di `spec-approval`. Per modificarli serve `/tollgate:reopen spec|plan <motivo>` (8.4): la fase torna a `spec_audit` o a `plan`, l'approvazione precedente resta come storico ma non vale più, e lo scope si registra di nuovo con il nuovo piano. Il brief dei task e `review prepare` leggono il piano alla versione registrata (`plan_sha`), non dal working tree.

   **Componenti spenti.** Con `spec_adversary`, `spec_audit` o `plan_adversary` a `false`, la condizione corrispondente non si applica, il file di approvazione lo riporta e il gate dà `attenzione` rosso (9.2).
5. **Piano in L2.** `tollgate:plan-adversary` segue lo stesso schema dei giri avversariali, con tetto `plan_rounds` (2) e `resolve` → «avversario del piano sospeso». Il passaggio `plan → approval` lo fa la CLI quando l'ultimo giro è pulito o sospeso. `approve plan` è accettato solo in `approval`.

### 6.3 Esecuzione

```
execution (sessione pulita)
  SessionStart: stato e checkpoint (≤ 10 righe, ≤ 1.500 caratteri)
  /tollgate:execute (o la skill execute invocata dal modello):
    0. prima del task 1: controllo del piano (task che si contraddicono, file condivisi),
       con le decisioni, in `status --checkpoint --note`
    per ogni task k in `tasks` (popolata dal piano alla registrazione dello scope), in ordine:
      tollgate task start k → brief in .tollgate-run/<N>/task-k.md (testo del task, scope,
        test correlati R2, must-have collegati, skill da usare, istruzione «prima di DONE
        esegui tollgate verify»); sceglie anche il tipo di implementatore (sotto). Il piano è letto a `plan_sha`. Un task può indicare i must-have che
        soddisfa con una riga `Must-have: M1, M3`; senza, il brief li contiene tutti
      Agent <tipo scelto da task start> con il percorso del brief e il `name` scritto nel brief
        (tg-<N>-t<k>; tg-<N>-t<k>-r<giro> per un implementatore nuovo dei giri 4-5)
        → SubagentStart associa il
        subagente al task (lo scrittore unico rende l'associazione univoca) e inietta il
        promemoria del passo (R5), al massimo 2.000 caratteri (R9)
      implementatore: TDD → commit (hook: test-guard, scope, livello) → tollgate verify
        → report a campi fissi (18.5), entro il budget del task (sotto)
      SubagentStop: 8.1; conflitto tra test e specifica → block open test_spec_conflict (R1)
      PostToolUse Agent, al ritorno: registra la coppia nome → agent_id per le riprese e
        riconosce il taglio di maxTurns (sotto)
      tollgate task review-prepare k → brief del revisore con l'intervallo di SHA del task
        (tasks.commits, riempito da PostToolUse Bash) e un codice
      Agent <revisore scelto da task start> con il brief → verdetto (18.5) con SHA e codice;
        SubagentStop lo associa al task in `review`
      approved → tollgate task done k (rifiuta senza verdetto approved sull'ultimo SHA del task)
      changes → giro di correzione: tollgate task start k --fix; giri 1-3 riprendono lo
        stesso implementatore con SendMessage verso il suo nome (SubagentStart e SubagentStop
        scattano di nuovo, con lo stesso agent_id), 4-5 ne lanciano uno nuovo con model
        inherit; al quinto senza approved → needs_you
  guardia del contesto: avviso a warn_pct; a stop_pct nessun nuovo subagente → checkpoint + /clear;
    dopo il /clear execute riprende dal primo task non chiuso in `tasks`
  fine dei task → /tollgate:finish (finish check rifiuta se un task non è done)
  correzioni dopo la revisione finale (needs_fix) → tollgate task start --from-findings <ciclo>:
    un task nuovo k+1 con il brief scritto dai rilievi confermati, nello stesso scope,
    senza toccare il piano. Dopo una PR con verdict rosso: task start --from-gate, con il
    commento del gate passato come dato
```

**Skill e implementatori per area.** I profili del task sono quelli il cui `paths` contiene almeno uno dei file `Create:`/`Modify:`/`Test:` del task (stessa regola di attivazione di 9.2, applicata al task).
- **Verticali e trasversali:** un profilo `kind = "vertical"` è un'area di codice e può avere agenti; un profilo `kind = "cross"` (accessibilità, performance) non ha agenti e aggiunge i suoi `reviewer_skills` ai revisori dei verticali che lo elencano in `cross`.
- **Un file, un profilo verticale.** Se un file corrisponde a più profili verticali vince il pattern **più specifico**: quello con più segmenti di percorso letterali (senza `*`); a parità, il primo dichiarato in `tollgate.toml`. `init` mostra le sovrapposizioni sui file reali del repo.
- **Skill:** il brief dell'implementatore elenca l'unione dei campi `skills` di quei profili, al massimo 3; quello del revisore elenca l'unione dei `reviewer_skills`, al massimo 3. Se l'unione supera 3, `plan-check` lo segnala e `plan-adversary` chiede di dividere il task. Ogni implementatore usa in più le skill comuni di `tollgate:implementer` (TDD, debugging, verifica), che non contano nel tetto. `SubagentStop` controlla che l'implementatore abbia invocato ognuna (eventi `PostToolUse` dello strumento `Skill` con il suo `agent_id`); se ne manca una, veto con l'elenco, come per la ricevuta (8.1). Una skill non installata non blocca: il brief la segna come assente e `attenzione` lo riporta.
- **Implementatore e revisore per area, a tutti i livelli:** se i profili del task dichiarano **un solo** `agent` non vuoto, `task start` sceglie quell'agente, e allo stesso modo `reviewer` per il revisore del task; con zero, o con agenti diversi (task a cavallo di più aree), sceglie `tollgate:implementer` e `tollgate:task-reviewer` con l'unione delle skill, e `plan-adversary` segnala il task come candidato a essere diviso. In L0 non ci sono subagenti: la sessione principale riceve nel promemoria le skill dei profili toccati.
- **Cosa rende diverso un implementatore per area:** prompt con le regole dell'area, strumenti propri (campo `tools`; un server MCP si dichiara a livello di progetto, perché i subagenti di plugin ignorano `mcpServers`, 16), modello proprio. Deriva dallo stesso testo di `tollgate:implementer` e ne mantiene gli obblighi (TDD, `verify`, stati, report). Un nome di ruolo senza contesto o strumenti diversi non giustifica un agente a sé (ricerca, filone 6).
- **Vincoli per gli agenti dei profili:** l'implementatore si chiama `<plugin>:implementer-<area>` e non è mai in `readonly_agents`; vale per lui tutto ciò che vale per `tollgate:implementer` (scope, scrittore unico, ricevuta, sola scrittura dopo `task start`). Il revisore si chiama `<plugin>:reviewer-<area>` e lo specialista finale `<plugin>:final-<area>`: entrambi entrano automaticamente in `readonly_agents`. Un agente per area funziona anche senza le sue skill (non installate su quella macchina): sono un rinforzo, non una dipendenza.
- **Catalogo.** I profili verticali concreti (aree, percorsi, comandi, agenti, skill, checklist) sono definiti in `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md` e realizzati dal sotto-progetto B.

**Dimensione e budget del task** (task piccoli: Google small CLs, GitLab, DORA small batches; budget fisso: Shape Up).
- **Dimensione.** A `task review-prepare` si misurano le righe aggiunte più rimosse del task, esclusi lockfile e file generati. Oltre `task_lines_warn` (200) il brief del revisore lo segnala; oltre `task_lines_max` (500) il report dell'implementatore deve contenere una motivazione, e `attenzione` lo riporta. Test e codice stanno nello stesso task; un refactoring va in un task a sé. `plan-adversary` segnala i task del piano che toccano più di `task_files_warn` (8) file.
- **Budget.** Ogni implementatore ha `maxTurns` nel frontmatter (predefinito `[tasks] max_turns`, 60) e un tetto di token per livello (`[tasks] max_tokens`). Superato il budget, il task va in `blocked` con un `needs_you` che propone di dividerlo: niente «ancora un giro» automatico.
  - **Taglio di `maxTurns`.** Claude Code interrompe il subagente **senza** `SubagentStop` (verificato in P0). Lo riconosce `PostToolUse Agent`: `tool_response.harnessNoteCount` ≥ 1 e il **primo** blocco di `content`, scritto da Claude Code e separato dall'output del subagente, comincia con «NOTE: this agent stopped at its». Il testo del subagente da solo non basta, così non può simulare il taglio. `PostToolUse Agent` chiude anche la riga in `subagents` (`ended`, stato `cut`), come farebbe `SubagentStop`: senza, lo scrittore unico resterebbe occupato per `stale_minutes`. `tollgate:execute` lancia gli implementatori in primo piano, perché i task sono in sequenza, e `PreToolUse Agent` nega `run_in_background` per l'implementatore. Il taglio in background e durante una ripresa con `SendMessage` non produce né `SubagentStop` né un `PostToolUse` con il taglio (verificato in P2, 16): si riconosce da `UserPromptSubmit`: il `prompt` deve **cominciare** con `<task-notification>`, e si esamina **blocco per blocco** (più notifiche nello stesso prompt si contano separatamente). Un blocco è un taglio se il suo `<summary>` contiene «stopped at its N-turn limit»; `<task-id>` è l'`agent_id` e `<subagent_tokens>`, se c'è, è il conteggio dei token. Una notifica citata in mezzo al prompt di un utente non taglia nulla. L'evento d'ingresso `prompt_submit` (3.2) esce subito con 0 se il prompt non comincia con `<task-notification>`. Ogni taglio chiude la riga in `subagents` (`cut`), sempre. Il task con quell'`agent_id` passa in `blocked` con `needs_you` (budget superato) solo se il componente `task_budget` è acceso. `stale_minutes` resta la rete di sicurezza: un implementatore senza eventi diventa `interrupted` e il task torna `pending`.
  - **Token.** Si sommano gli `usage` del transcript (`agent_transcript_path`) a `SubagentStop`, prima che il task lasci `running`: così il tetto vale anche per un implementatore che chiude con DONE. Il conteggio è `input_tokens + cache_creation_input_tokens + output_tokens` sui messaggi unici per `message.id`: `cache_read_input_tokens` è escluso, perché riconta l'intero contesto a ogni turno (decisione 20 del piano P2). `tool_response.totalTokens` di `PostToolUse Agent`, presente solo in primo piano, serve come riscontro nelle statistiche.
- **Report a campi fissi.** Il messaggio finale dell'implementatore ha i campi di 18.5 (stato, fatto, test, file, dubbi, cosa resta, motivazione della dimensione). Un report senza i campi obbligatori è **non valido**: veto con l'elenco dei campi mancanti, che conta tra i 2 veti di 8.1. Serve a chi riprende il task: note strutturate riducono il costo della ripresa (arXiv 2606.02875).

**Transizioni di `tasks.state`.**

| Da | Evento | A |
|---|---|---|
| `pending` | `task start k` | `running` |
| `running` | `SubagentStop` con DONE o DONE_WITH_CONCERNS e ricevuta `green` | `review` (con DONE_WITH_CONCERNS i dubbi vanno nel brief del revisore) |
| `running` | `SubagentStop` con BLOCKED | `blocked`, con un blocco del lavoro (`needs_you` o il tipo dichiarato) |
| `running` | `SubagentStop` con NEEDS_CONTEXT | `running`: il coordinatore risponde riprendendo lo stesso implementatore; non consuma un giro |
| `running` | budget superato: `PostToolUse Agent` con il taglio di `maxTurns`, oppure token oltre `max_tokens` a `SubagentStop` (prima delle altre righe di `SubagentStop`) | `blocked`, con un blocco `needs_you` che propone di dividere il task |
| `running` | implementatore `interrupted` | `pending` di nuovo, senza consumare un giro |
| `review` | verdetto `changes` e `task start k --fix` | `running`, `fix_rounds` + 1 |
| `review` | verdetto `approved` e `task done k` | `done` |
| `blocked` | blocco chiuso | `pending` |

`task start k` senza `--fix` è ammesso solo da `pending`.

`.tollgate-run/` è ignorata da git: `start` la scrive in `$(git rev-parse --git-common-dir)/info/exclude`, che non richiede commit. È fuori dallo scope. I giri di correzione (R4) sono `tasks.fix_rounds`: li conta la CLI a ogni `task start --fix`, non un'euristica sugli hook.

**In `execution`, in L1 e L2, l'unico subagente che scrive è l'implementatore scelto da `task start` (`tollgate:implementer` o `<plugin>:implementer-<area>`) e lanciato dopo `task start`.** `PreToolUse Agent` nega gli altri tipi che non sono in `readonly_agents` e un implementatore senza un `task start` in sospeso. **`PreToolUse SendMessage`** applica le stesse regole alle riprese, che non passano da `Agent` (verificato, pagina sub-agents). La ripresa indica il destinatario con il **nome** dato al lancio (`tool_input.to`, verificato in P0), per questo `PreToolUse Agent` nega il lancio di un implementatore senza il `name` del brief, e `PreToolUse SendMessage` risolve il nome con la tabella nome → `agent_id` che `PostToolUse Agent` registra per ogni subagente lanciato con un nome (`subagents.name`, 12.2). In `execution` un nome mai registrato vale come un implementatore senza `task start`: `deny`. Verso un implementatore la ripresa è ammessa solo con un `task start --fix` in sospeso per il suo task, oppure per rispondere a NEEDS_CONTEXT; verso un subagente che scrive e non è l'implementatore del task è negata. Così subagent-driven-development, se il coordinatore lo invocasse per abitudine, non può lanciare né riprendere implementatori. writing-plans chiude i piani con un rimando a subagent-driven-development: la skill `start` dice di usare `/tollgate:execute`, e il veto lo ricorda.

### 6.4 Chiusura

`tollgate:execute` termina con `/tollgate:finish`. Se il coordinatore usa invece la chiusura di Superpowers, i guardrail negano merge, push, cancellazione del ramo e rimozione del worktree.

```
/tollgate:finish
  1. finish check   copia locale del gate (senza identificativi della base). Verde → fase review;
                    rosso → resta in execution con l'elenco dei problemi
  2. revisione      solo L1 e L2: review prepare → final-reviewer → review prepare dai rilievi
                    registrati → finding-verifier → verdetti registrati da SubagentStop (8.6)
                    needs_fix → execution: task start --from-findings (6.3); il finish
                    successivo è un nuovo ciclo di revisione
  3. open-pr        solo se: c'è un atto `finish` legato allo SHA di HEAD (8.4), oppure approve pr
                    per quello SHA; si spinge esattamente quello SHA; 1 e (in L1 e L2) 2 sono passati sullo stesso SHA;
                    non ci sono blocchi né elementi in attesa (0); ogni rilievo registrato ha un esito.
                    Poi: intento → push → ls-remote → PR esistente? → crea o aggiorna, con il
                    blocco JSON (18.1)
  4. gate           9; fase pr_open
  5. merge          tuo, su GitHub
```

### 6.5 Dopo la PR

| Situazione | Cosa succede |
|---|---|
| Verdetto rosso o altre modifiche | `start #N` → `execution` → `task start --from-gate` → `finish` aggiorna la stessa PR |
| Ramo predefinito andato avanti (`strict`), anche dopo «Update branch» su GitHub | `/tollgate:sync`: integra i commit remoti della PR, fa il rebase sul ramo predefinito, riallinea la base, rilancia `finish check` e `open-pr --update` con `--force-with-lease`. Se il `patch-id` è lo stesso, il verdetto vale ancora. **Con un conflitto:** `rebase --abort`, base e fase invariate, blocco `needs_you` con le due strade (risolvere tu il rebase fuori da Claude e poi `approve rebase`, oppure abbandonare). **Interrotto a metà:** `sync` registra prima un intento con gli SHA di partenza e di arrivo. La ripresa trova il rebase in corso e propone `--abort`, oppure trova l'intento con il rebase finito e completa il riallineamento della base. `sync` registra i commit riscritti, così `PostToolUse Bash` non li tratta come nuovi |
| Merge o chiusura senza merge | Rilevati con `gh` alla chiamata successiva, da qualunque fase: `closed`, oppure ti chiede cosa fare |

### 6.6 Dove valgono le regole

| Dove | Quali regole |
|---|---|
| Repo non attivo | Nessuna |
| Repo attivo, sessione non legata a un lavoro, fuori dai worktree dei lavori | Le righe «Repo attivo» di 7.4, più i file protetti in `PreToolUse` Edit e Write. È l'unico elenco valido |
| **Sessione legata a un lavoro attivo** (0), su qualunque ramo e in qualunque directory, e **ogni comando dentro il worktree** di un lavoro attivo | **Tutte.** Il nome del ramo non conta. Sono negati il cambio e la rinomina del ramo nel worktree, le scritture nel checkout principale e il push o la PR di qualunque ramo fuori da `open-pr` |

**Altri lavori.** Una sessione legata che scrive nel worktree di un **altro** lavoro attivo è negata. Fuori dai worktree dei lavori (per esempio in una cartella temporanea) la scrittura passa. I file protetti valgono rispetto a **ogni** radice: il repo più vicino, il worktree e il checkout principale.

**Come si riconosce il ramo.**
- Per i file, dal loro repository.
- Per Bash, dalla directory effettiva, compresi `cd` e `git -C`.

**Worktree.**
- `git worktree add` doppio → negato.
- Un subagente con `isolation: worktree` parte dal ramo predefinito (verificato). `WorktreeCreate` sostituisce la creazione e non si può usare per filtrarla (verificato). Le modifiche fatte lì non entrano nel ramo del lavoro.

---

## 7. Hook (guardrail locali)

### 7.1 Il wrapper `hooks/run`

**Il problema.** Solo l'uscita 2 blocca. Un'uscita 1, un crash o un timeout lasciano passare (verificato su hooks.md, 08/10/2026).

**Cosa fa il wrapper, in ordine:**
1. `/tollgate:on` e `/tollgate:off [ore]` creano o cancellano `OFF`, con una scadenza facoltativa, senza passare da Python né dal DB. Dal terminale vale lo stesso `touch ~/.local/state/tollgate/OFF`: ogni messaggio di errore del wrapper lo riporta alla lettera, così l'uscita d'emergenza non dipende da `UserPromptExpansion`. Il messaggio di `/tollgate:off` e `/tollgate:on` esce su stdout come `systemMessage` e `additionalContext`: su stderr, con uscita 0, il modello non lo riceve. Le ore valgono da 1 a 9999; un valore diverso spegne senza scadenza e il messaggio lo dice.
2. Se `OFF` è attivo: esce con 0, scrive l'avviso «tollgate spento» su stderr e registra il salto in `skipped.log`. `OFF` si controlla prima della ricerca del repo attivo, di Python e di ogni logica di tollgate; dall'input il wrapper legge solo `command_name` e `command_args` per `/tollgate:on|off` e, per `UserPromptSubmit`, la presenza di `<task-notification>` (decisione 5 del piano P2).
3. Controlla in shell, senza rete, se il repo è attivo: cerca `tollgate.toml` su `origin/<tollgate.defaultBranch>` (scritto da `init` e `start`), poi su `origin/HEAD`, `origin/main` e `origin/master`. Se il repo non è attivo esce con 0. Se non trova nessun riferimento remoto esce con 0 e avvisa: il repo è trattato come non attivo. Un repo non attivo resta attivo per una sessione che ha il segnalino `<cartella di stato>/bound/<session_id>`: l'hook lo scrive quando la sessione si lega a un lavoro, così le regole valgono in ogni cartella (6.6), e `start` lo pulisce per le sessioni chiuse (decisione 22 del piano P2). `start` rifiuta di partire se il wrapper non vedrebbe il repo come attivo.
4. Se manca Python ≥ 3.11: un hook di controllo esce con 2 e spiega perché; un hook informativo esce con 0 con un avviso (decisione 1 del piano P2: un `SubagentStop` che uscisse con 2 terrebbe vivo il subagente).
5. Lancia `bin/tollgate hook <evento>` con una scadenza interna (`[hooks] timeout_s`, predefinito 20 s). Python imposta `signal.alarm` su quella scadenza, come configurata. Il wrapper legge `timeout_s` dal riferimento remoto e tiene un cane da guardia a `timeout_s + 2` secondi, con `timeout_s` limitato a 85 s: il tetto vale solo per il cane da guardia (al più 87 s), con i descrittori chiusi, perché un processo orfano non tenga aperta la pipe di Claude Code. `hooks.json` dichiara `timeout: 90` (decisione 4 del piano P2).
6. **Hook di controllo** (`PreToolUse`: `pre_edit`, `pre_bash`, `pre_agent`, `pre_send_message`, `pre_mcp`; decisione 1 del piano P2): qualunque esito diverso da 0 o 2 diventa 2.
7. **Hook informativi** (tutti gli altri eventi: `SessionStart`, `UserPromptExpansion`, `UserPromptSubmit`, `PostToolUse`, `SubagentStart`, `SubagentStop`): un errore diventa 0, con un avviso. Così un DB guasto non blocca mai i comandi `/tollgate:*`; l'atto in quel caso non viene registrato e la skill lo dice.

Ogni messaggio d'errore riporta il percorso assoluto di `bin/tollgate` e il comando `touch` per `OFF`.

### 7.2 Tabella

| Evento | Filtro | Comportamento |
|---|---|---|
| `SessionStart` | `startup`, `resume`, `clear`, `compact`, `fork` | Se la directory è dentro il worktree di un lavoro attivo, lega la sessione al lavoro (0). Inietta lo stato e il checkpoint. Segna come `interrupted` i subagenti `running` **di sessioni non vive** (0); mai in base alla sola origine «precedente» |
| `UserPromptExpansion` | comandi `tollgate:*`, forma lunga e breve | Registra l'atto (8.4) da `command_name`, che è sempre nella forma lunga, e `command_args` |
| `PreToolUse` | `Edit`, `Write`, `NotebookEdit`, `MultiEdit` | In `spec_audit`, `plan`, `approval`, `blocked`, `review` e `pr_open`: solo `.md` sotto `docs/superpowers/` (in `spec_audit` e `approval` non sotto `plans/`; mai spec e piano bloccati, 6.2); per correggere il codice dopo `finish` si torna in `execution` con `start`. In `execution`: fuori scope → `deny`; codice scritto dalla sessione principale in L1 o L2 → `deny`. In L0 non c'è scope: scrive la sessione principale, e il superamento delle soglie di 5 porta a L1. File protetti → `deny`, anche quando sono `.md` sotto `docs/superpowers/reviews/`. Sempre ammessi: gli altri `.md` sotto `docs/superpowers/` e `.superpowers/` |
| `PostToolUse` | `Edit`, `Write`, `MultiEdit` | Ricalcola il livello; sui piani lancia `plan-check` (7.5) |
| `PostToolUse` | `Skill` | Se lo invoca un implementatore (`agent_id`), registra la skill per il suo task (6.3) |
| `PostToolUse` | `Bash` | In una sessione legata o nel worktree: se `HEAD` ha commit nuovi non registrati (anche da `merge`, `cherry-pick`, `revert`, `am`), li registra e fa girare test-guard e scope su di essi; una violazione apre un blocco `needs_you`. Se il ramo del worktree è cambiato, apre `needs_you`. È il controllo a valle che copre i comandi non riconosciuti da 7.4 |
| `PreToolUse` | `Bash` | 7.4 |
| `PreToolUse` | `mcp__.*` | Effetto esterno, se lo strumento non è in `mcp_allow` (8.5) |
| `PreToolUse` | `Agent` | Guardia del contesto. **Scrittore unico**: nessun nuovo implementatore se un altro è `running` nel worktree. Un subagente senza eventi da più di `stale_minutes` (30) diventa `interrupted`, anche se la sua sessione è viva: è un subagente bloccato. In `execution` (L1, L2) ammette come scrittore solo il tipo scelto da `task start` per il task in sospeso (`tollgate:implementer` o l'implementatore per area, 6.3), con il `name` scritto nel brief e senza `run_in_background` |
| `PostToolUse` | `Agent` | Registra il nome → `agent_id` (`tool_input.name`, `tool_response.agentId`) del subagente lanciato con un nome. Riconosce il taglio di `maxTurns` (6.3): chiude la riga in `subagents` e porta il task dell'implementatore in `blocked` con `needs_you` (budget superato). In auto mode e in primo piano porta anche il report in `tool_response.handbackReport.text` |
| `PreToolUse` | `SendMessage` | Ripresa di un subagente: risolve `tool_input.to` con la tabella dei nomi, o come `agent_id` se coincide con uno noto, e applica le stesse regole di `Agent` sullo scrittore (6.3). Inviato dalla sessione principale (input senza `agent_id`) verso un destinatario mai registrato, in `execution` → `deny`. Inviato da un subagente verso il coordinatore o verso un subagente di sola lettura: ammesso. Un implementatore ha sempre un nome registrato, perché `PreToolUse Agent` nega il lancio senza |
| `SubagentStart` | tutti | Salva `agent_base_sha` (senza sovrascriverla alla ripresa), l'impronta dei file e il tipo; per l'implementatore del task (generico o per area) lo associa al task in sospeso; inietta il contesto (6.3) |
| `SubagentStop` | tutti | Implementatori: prima il tetto di token dal transcript (6.3), poi 8.1. Sola lettura: 7.3. Revisore del task: verdetto in `tasks` (18.5). Revisori finali: 8.6. Avversari e auditor: salva il report. Ignora gli eventi con `agent_type` vuoto o con un `agent_id` mai visto a `SubagentStart`: sono subagenti interni di Claude Code (visti in P0) |
| `PostToolUse` | `SubagentHandback` | In auto mode il report del subagente arriva con questo strumento (verificato in tools-reference, dalla v2.1.271). L'adattatore ne salva `tool_input.message` come messaggio finale del subagente. In auto mode `SubagentStop` non ha `last_assistant_message` (verificato in P0): la fonte primaria è questa, e per i subagenti in primo piano `PostToolUse Agent` ha lo stesso testo in `handbackReport` |

`Stop` della sessione principale: nessun veto.

### 7.3 Controllo di sola lettura

Vale per `readonly_agents`. `SubagentStop` confronta i file tracciati e quelli non tracciati e non ignorati, escludendo `output_dirs`, con l'impronta presa alla partenza. Se sono cambiati, il verdetto non vale e si apre `needs_you`.

### 7.4 Regole su Bash

L'ambito è quello di 6.6. Le regole sono «best effort».

| Ambito | Comando | Decisione |
|---|---|---|
| Lavoro attivo | `git push`, `gh pr create` di qualunque ramo; nel worktree `git switch`, `git checkout <ramo>`, `git checkout -b/-B`, `git branch -m/-M`; scritture nel checkout principale | `deny`. I casi che sfuggono al riconoscimento li prende `PostToolUse Bash` (7.2) |
| Lavoro attivo | `git commit` (con `-a` o con `git add` nella stessa riga) | test-guard, scope e livello su working tree più indice; `deny` se mancano deroghe. Esenti dallo scope: `docs/superpowers/**/*.md` tranne `reviews/**` (protetto) e spec e piano già approvati, `.tollgate/waivers/<N>.toml` del lavoro, i file di `[scope] always` e i lockfile il cui manifest è nello scope |
| Lavoro attivo | Scrittura di codice dalla sessione principale (L1, L2) con redirect o `sed -i` | `deny` |
| Repo attivo | Merge di un ramo `tg/*` verso il predefinito, `git branch -d/-D` e `git worktree remove` di un lavoro attivo, `git worktree add` doppio | `deny` |
| Repo attivo | Effetti esterni (8.5): `gh pr merge` e `gh` in scrittura (`api` con `-X` non GET, `-f`, `-F`, `--input`, `graphql` con `mutation`; `pr create`, `pr edit`, `pr review`, `pr close`, `release`, `workflow run`, `secret`, `project`, `issue edit`, `issue close` e `issue create`) | `deny` fino all'atto |
| Repo attivo | `git push` verso il ramo predefinito, in entrambe le modalità; `push --force` fuori da `open-pr` e `sync`, `reset --hard`, `--no-verify`, `rm -rf` fuori dal worktree | `deny`. L'hotfix passa da un ramo e da una PR (9.4) |
| Repo attivo | `claude` e i suoi alias, `TOLLGATE_` nel comando, `tollgate hook`, scrittura sui file protetti | `deny` |

**Rimozioni che toccano file protetti.** `rm`, `rmdir`, `mv`, `git rm`, `unlink` e `find -delete` su una cartella che contiene file protetti sono negati, anche quando il file è raggiunto solo da un glob. **`core.hooksPath` è negato a ogni livello di configurazione**, anche con l'opzione compatta `-c`. Vale anche per una sessione non legata.

### 7.5 `plan-check`

**Il piano del lavoro** è il primo file sotto `docs/superpowers/plans/` creato nel ramo del lavoro (assente nella base) che supera `plan-check` **in fase `plan`**. Viene registrato in `work_items.plan_path`. I piani di lavori già chiusi sono nella base e vengono ignorati; un altro piano nuovo nel ramo non cambia lo scope e porta `attenzione` rosso nel gate («piano diverso dal primo»). Il piano deve contenere queste intestazioni esatte di secondo livello:
- `## Fatti verificati`
- `## Decisioni`
- `## Interfacce`
- `## Must-have`
- `## Scope`
- `## Punti di arresto`
- `## Rischi`

Le intestazioni si cambiano in `[plan] required_sections`, e i profili possono aggiungerne altre.

**Must-have legati ai test** (L1 e L2). Nella sezione `## Must-have` ogni voce ha la forma `M<n>. <proprietà> — test: <identificativo>` (uno o più identificativi, nella forma `classname::name` del report JUnit). La forma dipende dallo strumento (verificata in P0, stabile tra esecuzioni):

| Strumento | `classname` | `name` | Esempio |
|---|---|---|---|
| vitest | percorso del file dalla radice del progetto | blocchi e test uniti da ` > ` | `src/date.test.ts::format > handles UTC` |
| jest con jest-junit configurato da `init` (11.2) | percorso del file dalla radice del progetto | blocchi e test uniti da uno spazio | `src/date.test.js::format handles UTC` |
| pytest | modulo con i punti, più la classe se c'è | nome della funzione | `tests.test_x::test_a`, `tests.test_x.TestGroup::test_a` |

`plan-check` rifiuta un must-have senza test. Così, quando approvi il piano, approvi anche **quali test dimostrano** che il lavoro fa ciò che volevi: il gate verifica una cosa decisa da te, non solo la coerenza del lavoro con se stesso. Un must-have che non si può verificare con un test (per esempio una proprietà visiva) porta `— test: manuale` e finisce tra le voci «da leggere» di `attenzione`.

**Lo scope del piano.**
- Si ricava da `Create:`, `Modify:` e `Test:` di ogni task (formato verificato in writing-plans, righe 100-102).
- Solo file: niente pattern, niente cartelle; gli intervalli di righe vengono tolti.
- Al massimo 30 file.
- Una volta registrato **non cresce**: per file in più servono deroghe; per cambiare il piano, `reopen plan` (6.2).

**Piano incompleto.** Riceve il veto con l'elenco di ciò che manca. Il file resta scritto ma non viene registrato.

---

## 8. Ricevute, test-guard, deroghe, atti, effetti, revisori

### 8.1 Ricevute locali

- **Chi le produce**: solo `verify` e `finish check`.
- **Ambiente**: ripulito, con le sole variabili di `[commands] env_allow`, senza `.env`, token o stringhe di connessione.
- **Cosa registrano**: SHA, comando risolto, uscita, test eseguiti e saltati, durata, log.
- **Conteggio dei test**: si legge da `report`, oppure da `report_related` per i test correlati. Il file di report si cancella prima di ogni esecuzione.
- **Stati**: `green` (uscita 0, almeno un test e nessun `failure` o `error` nel report), `red` (uscita diversa da 0, **oppure** report con `failure` o `error` anche con uscita 0: copre `|| true`), `empty` (nessun test), `uncounted` (nessun `report` configurato; con un `report` configurato e assente lo stato è `red`), `unverified` (manca il comando). Nessun nuovo tentativo automatico: un rosso resta rosso.
- **`allow_no_tests = true`**: `empty` vale come `green` sia in locale sia nel gate, sempre con `attenzione` rosso. `uncounted` vale come `green` solo se il comando ha uscita 0 **e** non ha un `report` configurato; se il report è configurato e manca, resta rosso.
- **Nessun test correlato**: si esegue il gate completo.
- **Worktree pulito**: si controlla prima di eseguire, escludendo `output_dirs`.
- **`{files}`**: ogni nome passa per `shlex.quote`, e i file cancellati sono esclusi.

**`SubagentStop` per gli implementatori.**
- Con `DONE` o `DONE_WITH_CONCERNS` e commit nuovi: devono essere `green` **tutti** i comandi del gate sull'ultimo commit, con la stessa regola della Definition of Done (8.7), oppure una ricevuta `green` dei test correlati (`related`) sullo stesso commit. Un gate solo parziale non basta.
- Con `DONE` o `DONE_WITH_CONCERNS`, nessun commit e impronta dei file cambiata rispetto alla partenza: veto, «committa e verifica».
- Senza commit e senza modifiche: passa.
- Con `BLOCKED` o `NEEDS_CONTEXT` basta una ricevuta qualunque, oppure un blocco aperto.
- Uno stato non riconosciuto rende il report non valido (18.5): non vale come `DONE`, e il componente `report_fields` lo mette in veto.
- Dopo 2 veti si apre `needs_you` e il subagente chiude. Alla ripresa i veti tornano a zero; per un subagente di sola lettura l'impronta si prende di nuovo alla ripresa (7.3).

### 8.2 test-guard

Gira in locale al `git commit` e nel gate dentro `verdict`.

**Nei file di test** (`test_globs` più quelli dei profili attivi):
- file cancellati, riconoscendo le rinomine;
- identificativi della base che mancano nella testa. In locale si ricavano per analisi statica: `describe`/`it`/`test` in JS e TS, `def test_*` e classi `Test*` in Python, `func Test*` in Go. L'analisi statica produce la stessa forma del JUnit di ogni strumento (7.5), così i due insiemi si confrontano. Nel gate vengono dal report JUnit. Gli identificativi della base sono i soli test **eseguiti e non saltati** nella base; nella testa uno `skipped` conta come **mancante**;
- asserzioni diminuite (`assert_markers` per linguaggio). Salti e asserzioni si contano sia sul codice senza commenti e stringhe sia sul testo grezzo, e vale il caso peggiore: un errore dello scanner non nasconde un indebolimento (fail-closed);
- marcatori di salto aggiunti, solo a parola intera:
  - JS e TS: `xit`, `xdescribe`, `xtest`, `.skip`, `.only`, `.todo`, `.fixme`, `.skipIf`, `.runIf(false)`, `.fails`;
  - Python: `pytest.skip(`, `pytest.mark.skip` (con o senza parentesi, compreso `skipif`), `xfail`, `@unittest.skip`, `skipIf`, `skipUnless`;
  - Go: `t.Skip`;
  - Java: `@Disabled`, `@Ignore`;
  - Rust: `#[ignore]`.

**In tutto il repo:**
- soglie di copertura abbassate o rimosse, anche se commentate: una chiave conta come abbassata se lo è in una delle due letture (pulita o grezza). I file di copertura noti (`.nycrc`, `.coveragerc`, `setup.cfg` e simili) si controllano in ogni cartella del repo, non solo alla radice;
- CI modificata;
- snapshot e fixture aggiornati (`fixture_globs`);
- `verification_globs` (configurazione di test e copertura): queste modifiche non bloccano, ma richiedono una deroga `command`, valida subito e sempre visibile in `attenzione`;
- `verification_watch` (file di progetto che possono toccare i test, come `package.json`, `pyproject.toml`, `Makefile`, `tsconfig*.json`): nessuna deroga, solo un elenco nel commento del gate. Il caso `|| true` lo copre lo stato `red` di 8.1, non questo elenco.

**`test_globs` predefiniti:**
- `**/__tests__/**`, `**/test/**`, `**/tests/**`, `**/e2e/**`;
- `**/*_test.py`, `**/test_*.py`, `**/*.test.*`, `**/*.spec.*`;
- `**/*_test.go`, `**/src/test/**`.

### 8.3 Deroghe e blocchi

**Deroghe** (`tollgate waiver add <tipo> <file> [--test <id>] --choice --why --cost`):
- **dove**: in `.tollgate/waivers/<N>.toml` (18.2), un file per issue, scritto solo dalla CLI. Il gate legge **solo** il file dell'issue della PR (9.2), e solo se il suo campo `branch` è il ramo della PR: le deroghe di un lavoro già mergiato non valgono per gli altri. `attenzione` elenca tutte le deroghe in vigore in quel file, anche quelle già presenti nella base;
- **granularità**: un file per deroga; per il tipo `test` si indicano anche gli identificativi;
- **`scope` su file non sensibili**: le prime 2 valgono subito. Dalla terza serve `approve waiver` e compare `attenzione`;
- **`command`**: vale subito ed è sempre in `attenzione`;
- **`test`, `ci`, `threshold`**: restano in attesa fino ad `approve waiver`;
- **`--pattern <glob>`** (codemod): una sola deroga per molti file, sempre in attesa e in `attenzione`;
- **in locale** una deroga dichiarata scioglie la violazione anche se è ancora in attesa: il commit passa, e `open-pr` rifiuta finché ci sono deroghe in attesa (decisione 9 del piano P2). Nel gate restano in `attenzione`;
- **deroga scritta a mano da te** in una PR manuale: va nel file dell'issue chiusa dalla PR, e il gate la tratta come qualunque deroga dichiarata.

**Blocchi** (`tollgate block open <tipo> --reason`):
- portano la fase a `blocked`;
- li apre l'agente e li chiudi tu;
- se ce ne sono più di uno, la fase precedente torna solo quando si chiude l'ultimo.

### 8.4 Atti dell'utente

Li registra `UserPromptExpansion` quando digiti il comando. Il tipo di atto viene da `command_name`, sempre nella forma lunga (`tollgate:approve`) anche quando digiti la breve, e gli argomenti da `command_args` (verificato in P0, anche per le skill con `disable-model-invocation`). L'atto registra `source`, `actor`, sessione, lavoro della sessione (se legata), oggetto e testo digitato. `source` è un elenco aperto: il nucleo usa `claude-code`, D aggiunge gli altri harness. Ogni atto ha uno `state` (`pending`, `consumed`, `expired`). Gli atti che autorizzano una volta sola (`finish`, `approve effect`, `approve pr`, `approve rebase`, `sync`, `adopt`, `cleanup`, `abandon`) diventano `consumed` quando la CLI li usa, e la CLI li accetta solo se sono dello stesso lavoro e dello stesso oggetto (issue, SHA o identificativo); per `adopt` e `cleanup`, che si danno da una sessione non legata, il lavoro è `null`. Tutti tranne `finish` vanno usati nella stessa sessione e scadono dopo `[acts] ttl_minutes` (10). **`finish` non scade a tempo e non è legato alla sessione:** è legato allo SHA di HEAD del lavoro e decade appena HEAD è diverso (nuovo commit, reset, rebase), così sopravvive anche al `/clear` della guardia del contesto, perché tra il comando e `open-pr` passano `finish check` e la revisione, che durano più di 10 minuti. Un secondo `/tollgate:finish` sullo stesso SHA riprende dal ciclo registrato, senza aprirne uno nuovo.

**Oggetto e target** (decisione 15 del piano P2). `approve <oggetto> [<target>]`: il target è il secondo argomento per `waiver`, `effect`, `finding`, `level`, `rounds` e `spec` (numero di fette); per `pr` è lo SHA di HEAD; per `plan`, `rebase` e `unverified-*` non c'è target. `reopen spec|plan <motivo>` ha come oggetto `spec` o `plan`. `resolve <id> <nota>` ha come target `<id>`, anche `writer`. `adopt #N` e `abandon #N` hanno come target `N`. `finish` lega il lavoro della sessione e lo SHA di HEAD. Tutti gli argomenti restano in `args`. Un `approve waiver` vale in ogni stato del suo atto (`pending`, `consumed`, `expired`): approvare una deroga non la consuma, quindi la scadenza di questa tabella non la tocca (decisione 10 del piano P2).

| Atto | Effetto |
|---|---|
| `finish` | Digitare `/tollgate:finish` autorizza `open-pr` per lo SHA corrente (6.4) |
| `approve spec <fette>` | L2: la spec passa al piano; scrive `spec-approval.md` (6.2) |
| `approve plan` | L2, solo in `approval`: il piano passa all'esecuzione; scrive `plan-approval.md`; registra scope e `plan_sha` |
| `reopen spec\|plan <motivo>` | Toglie valore all'approvazione o alla registrazione e riporta la fase a `spec_audit` o `plan` (6.2) |
| `approve waiver <id>` | La deroga diventa valida |
| `approve level <L> <motivo>` | Fissa un tetto al livello (5) |
| `approve effect <id>` | L'effetto esterno è permesso una volta |
| `approve finding <id> <gravità\|dismiss> <motivo>` | Declassa un rilievo confermato alla gravità indicata (`user_decision = downgraded:<gravità>`) o lo archivia (`dismissed`) |
| `approve rounds <n>` | Concede `n` cicli di revisione in più in una volta (al massimo 8 cicli in totale, contando tutti i cicli) e chiude il blocco del tetto. Le richieste oltre 8 sono rifiutate |
| `approve unverified-review` | Oltre gli 8 cicli, chiude la revisione come «non verificata», e lo scrive nella PR |
| `approve unverified-tests` | Permette la PR con una ricevuta `unverified` |
| `approve rebase` | Dopo un conflitto risolto da te: riallinea `work_base_sha` al `merge-base`, chiude il blocco del `sync`, riporta la fase a `execution` e autorizza **un** `open-pr --update` con push forzato |
| `approve pr` | Permette `open-pr` su questo SHA |
| `resolve <id> <nota>` | Chiude il blocco. Al tetto della revisione concede **un** ciclo (per più cicli: `approve rounds`). Al tetto dei giri avversariali: «avversariale sospeso» (o «avversario del piano sospeso»). Al tetto dell'audit a lenti: «audit a lenti sospeso» |
| `resolve writer` | Segna `interrupted` gli implementatori `running` del lavoro. Serve quando una sessione caduta risulta ancora viva e blocca lo scrittore unico |
| `sync` | 6.5 |
| `adopt #N` | 12.4 |
| `abandon #N` | Chiude il lavoro |
| `cleanup` | Cancella rami e worktree dei lavori chiusi, dopo averti mostrato l'elenco |
| `off [ore]`, `on` | Interruttore |

**Nel gate gli atti sono «dichiarati».** Le deroghe dichiarate sciolgono la violazione. `test`, `ci`, `threshold`, `command`, le deroghe per pattern e gli `scope` oltre il secondo fanno diventare rosso `attenzione`. `approve unverified-tests` e `approve level` arrivano al gate solo dal blocco JSON della PR (18.1).

### 8.5 Effetti esterni

**Cosa conta come effetto esterno:**
- `[external_effects] commands`;
- un elenco predefinito: `ssh`, `scp`, `rsync`, `psql`, `docker push`, `kubectl`, `terraform apply`, `aws`, `gcloud`, `az`, `vercel`, `netlify`, `firebase deploy`, `supabase` in scrittura, `wrangler deploy`, `npm publish`;
- `project_scripts`;
- `curl` e `wget` con metodo diverso da GET o con dati;
- strumenti MCP non permessi;
- `gh` in scrittura;
- shell annidate che contengono uno di questi;
- script dentro il repo o il worktree che non sono tracciati nella base.

**Non è un effetto esterno** `bin/tollgate` stesso, riconosciuto dal percorso reale (risolto, senza collegamenti) sotto la cartella del plugin. Uno script con lo stesso nome dentro il worktree non è esente. Con `tollgate:execute` non servono altre esenzioni: gli script di subagent-driven-development non vengono più lanciati.

**Eccezioni in sola lettura.** `[external_effects] allow` contiene pattern di comandi che passano senza atto. La responsabilità di quell'elenco è tua.

**Come funziona:**
1. veto, con un identificativo;
2. `/tollgate:approve effect <id>`;
3. l'effetto passa una volta, per quel comando esatto. L'atto si consuma a `PostToolUse Bash`, quando il comando è partito, non a `PreToolUse`: un comando negato non consuma nulla. Per MCP, che non ha `PostToolUse`, l'atto si consuma a `PreToolUse`;
4. il permesso diventa un intento, con chiave (comando, lavoro, SHA);
5. se lo stesso effetto si ripete sullo stesso SHA, ti avvisa con «già eseguito alle…».

**Intenti in sospeso alla ripresa.** Prima si controllano SHA e stato, poi ti viene chiesta conferma.

### 8.6 Revisori

- **Brief del revisore**: lo scrive `review prepare`, con diff, piano, must-have, SHA e un codice di controllo casuale.
- **Standard del revisore** (Google, standard della revisione): si approva se il cambiamento **migliora la salute del codice**, anche se non è perfetto. Solo i rilievi `blocker` e `major` chiedono modifiche (per i rilievi che citano una regola dei profili: solo le regole marcate `[blocca]`); `moderate` e `minor` sono note che non fermano il task né la PR.
- **Disaccordo istruito** (arXiv 2608.18167): il prompt del revisore gli chiede di cercare difetti, non di confermare il lavoro, e ogni rilievo deve citare una prova: file e riga, e la regola violata (`R-…` del profilo) o il passo del piano. Un rilievo senza prova viene scartato dal verificatore. Il verificatore fa da critico: conferma o scarta ogni rilievo, senza discutere con il revisore.
- **Brief del verificatore**: lo genera dalla **tabella `findings`**, cioè da tutti i rilievi registrati.
- **Validità del verdetto**: deve contenere SHA e codice, e deve aver superato il controllo di sola lettura.
- **Formato**: quelli di 18.5, per il revisore e per il verificatore. Un JSON assente o malformato vale `needs_you`.
- **`open-pr` rifiuta** se un rilievo registrato non ha esito, salvo quelli oltre `max_findings`.

### 8.7 Definition of Done

Il lavoro che non rispetta la Definition of Done non conta (Scrum Guide 2020; GitLab). Ogni voce è verificabile da un comando o da un dato del DB, mai da un giudizio.

| Voce | L0 | L1 | L2 | Come si verifica |
|---|---|---|---|---|
| Ricevuta `green` sullo SHA (o `allow_no_tests`) | sì | sì | sì | `receipts` |
| test-guard e scope senza violazioni non derogate | sì | sì | sì | hook e gate |
| Ogni task `done` con verdetto `approved` del revisore del task | — | sì | sì | `tasks` |
| Nessun rilievo `blocker` o `major` confermato senza `approve finding` | — | sì | sì | `findings` |
| Ogni must-have ha i suoi test eseguiti e verdi nella ricevuta finale (`— test: manuale` va tra le voci «da leggere») | — | sì | sì | piano e report JUnit; il gate lo ricalcola dal JUnit |
| Skill dei profili usate | — | sì | sì | `tasks.skills_used` |
| Spec e piano approvati, report avversariali presenti | — | — | sì | file di approvazione (18.3) |
| Specialisti finali passati | — | — | sì | `findings` per fonte |
| Voci in più dei profili attivi (`dod = [...]`, nomi di comandi) | sì | sì | sì | ricevute dei comandi |

`finish check` calcola la DoD e la stampa voce per voce; `open-pr` rifiuta se una voce manca. Il gate ricalcola le voci che può vedere (ricevute, test-guard, scope, file di approvazione); le altre arrivano dal blocco JSON come dichiarate (18.1, campo `dod`).

---

## 9. Gate su GitHub

### 9.1 I workflow

| Workflow | Evento | Definizione | Codice della PR? | Permessi | Cosa fa |
|---|---|---|---|---|---|
| `tollgate-guard` | `pull_request_target` | Ramo predefinito | No: checkout solo del predefinito, oggetti della PR con `git fetch` | `contents: read`, `statuses: write`, `pull-requests: write` | Pubblica `tollgate/guard` e, se serve, un commento che spiega lo stato in attesa |
| `tollgate-run` | `pull_request` | Quella della PR, che `guard` impone uguale | Sì | Sola lettura, nessun segreto | `setup` e comandi del gate sulla testa; carica come artefatti solo report, uscite e conteggi. Nessun filtro `paths` o `branches`, ma esce subito se la PR non punta al ramo predefinito. `concurrency` per PR con `cancel-in-progress` |
| `tollgate-verdict` | `workflow_run` al termine di `run` | Ramo predefinito (verificato) | No: calcola da sé il diff con `git fetch` e legge gli artefatti come dati in una cartella temporanea | `contents: read`, `statuses: write`, `pull-requests: write`, `actions: read` (artefatti del run: necessario nei repo privati, verificato in P0), `issues: read` (stato ed etichette dell'issue) | Pubblica `tollgate/verdict` e `tollgate/attention`, sempre espliciti, più il commento. Mette in cache, per albero, gli identificativi dei test della testa |
| `tollgate-base` | `push` sul predefinito | Ramo predefinito | No | `contents: read`, `statuses: write`, `issues: write` | Mette in cache, per SHA e per albero, gli identificativi dei test della base. Se l'albero è già in cache (merge squash di una testa verificata) non riesegue la suite. In `detect` pubblica `tollgate/base` sul commit; se la suite fallisce lo stato è rosso e `tollgate-base` stesso commenta l'issue di `sentinel` (permesso `issues: write` in più) |
| `tollgate-sentinel` | `push` sul predefinito | Ramo predefinito | No | `contents: read`, `statuses: write`, `issues: write`, `pull-requests: read` | Per ogni commit nuovo (l'intervallo `before...after` del push) chiede `GET /repos/{o}/{r}/commits/{sha}/pulls`. Se il commit non viene da una PR mergiata, o se la testa di quella PR non aveva `tollgate/guard` e `tollgate/verdict` verdi: stato `tollgate/sentinel` rosso sul commit e un commento sull'**unica** issue aperta «tollgate: merge non verificato» (la crea se non c'è). Ignora il commit che introduce per la prima volta il proprio workflow. Gira in entrambe le modalità; in `protected` intercetta le forzature degli amministratori |

**Controlli di `verdict` prima di valutare.**
- `workflow_run.path` è quello atteso.
- L'evento è `pull_request`.
- Lo SHA è ancora la testa della PR, che si trova anche per SHA quando `pull_requests` è vuoto.
- La PR punta al ramo predefinito.

Se qualcosa non torna pubblica `error`. Le PR verso altri rami ricevono «non applicabile».

**PR di Dependabot.** Il `workflow_run` che segue il `run` di una PR di Dependabot riceve i permessi dichiarati e i segreti normali del repo, non quelli di Dependabot (verificato in P0). `verdict` funziona quindi senza casi speciali. Per lo stesso motivo un `workflow_run` del progetto vedrebbe i segreti anche per le PR di Dependabot: è un motivo in più per cui `guard` lo vieta (9.2).

**Base senza cache.** Un job senza permessi di scrittura (`persist-credentials: false`) calcola gli identificativi con il codice della base.

**Artefatti.** Massimo 50 MB per file e 200 MB in totale. Sono rifiutati i percorsi con `..`, i percorsi assoluti e i file XML con `DOCTYPE` o entità. In questi casi lo stato è `error`.

**Stato in attesa.** `tollgate/verdict` lo pubblica solo `verdict`. Finché manca, la protezione blocca il merge.

### 9.2 Cosa controllano

| Controllo | Dove | Esito |
|---|---|---|
| File di tollgate uguali alla punta del predefinito | `guard` | Obbligatorio, salvo 9.4 |
| Workflow del progetto nuovi o modificati: nessuno dichiara `statuses: write` o `checks: write`, usa `pull_request_target` o `workflow_run`, o manca del blocco `permissions` | `guard` | Rosso: così un workflow aggiunto in una PR non può pubblicare stati falsi. Le altre modifiche alla CI passano, con la deroga `ci` (8.3) e `attenzione` rosso |
| Comandi del gate (globali e dei profili attivi), da zero | `run` → `verdict` | Rosso se `red` (compreso un report con `failure` o `error`), `empty` o `uncounted` senza `allow_no_tests`, `unverified` senza `approve unverified-tests` dichiarato |
| **Issue della PR.** Per un ramo `tg/<N>-*`: N dal nome del ramo, uguale a «Closes #N» e a `issue` nel JSON, issue aperta. Per gli altri rami: da «Closes #N», issue aperta | `verdict` | Rosso se non torna: senza issue valida non si legge nessuna deroga |
| Identificativi della base eseguiti sulla testa (uno `skipped` è mancante), salvo deroghe `test` | `verdict` | Rosso |
| test-guard sul diff, per tutte le PR | `verdict` | Rosso se manca la deroga |
| Scope: coerenza con il **piano unico** del lavoro, letto alla versione registrata (`plan` e `plan_sha` nel JSON, 18.1), con gli esenti e con le deroghe. Solo per le PR dei lavori | `verdict` | Rosso. Senza piano e oltre le soglie di L0 → rosso. Piano in testa diverso da `plan_sha`: `attenzione` rosso con il diff nel commento |
| File di approvazione (L2): il loro `sha` è quello della spec e del piano in testa | `verdict` | `attenzione` rosso con il diff se non coincidono |
| Livello dichiarato contro minimo. In L2: spec, piano e report dell'avversario sempre; report a lenti solo se le fette previste sono più di una; intestazioni valide (18.3). Per una fetta successiva alla prima, i report della spec si cercano in `spec_reviews_dir` sul ramo predefinito | `verdict` | **Rosso** se il livello è sotto il minimo senza un tetto dichiarato, o se manca un report o un file di approvazione L2 richiesto. Con un tetto dichiarato: `attenzione` rosso. Un componente spento in `[components]` (letto dal ramo predefinito) toglie il report corrispondente e dà `attenzione` rosso. Si verifica che i file esistano, non la loro qualità |
| Deroghe da segnalare (8.4), piano diverso dal primo, lockfile senza manifest, test della base che falliscono sulla testa, PR non `tg/*`, PR `tollgate-config/*`, periodi con tollgate spento dichiarati, `allow_no_tests` attivo, tetto di livello, revisione «non verificata», audit «sospesi», rilievi confermati declassati o archiviati, `approve unverified-tests`, task oltre `task_lines_max` con `size_reason`, skill dei profili segnate come assenti | `verdict` | `attenzione` rosso, non obbligatorio, con l'elenco nel commento visibile (il blocco JSON è un commento HTML che GitHub non mostra). I file di `verification_watch` toccati sono solo elencati nel commento. Le voci sono divise in due gruppi (sotto) |

**Profili attivi** = quelli elencati in `[profiles] active` più quelli il cui `paths` tocca il diff, calcolati con la configurazione del ramo predefinito. Il livello minimo del gate è il massimo tra quello calcolato da percorsi ed etichette e i `min_level` dei profili attivi. I comandi di un profilo si chiamano `<profilo>.<comando>` in ricevute, artefatti e JSON.

**Due gruppi di `attenzione`.** Per non abituarsi a ignorarlo, il commento mette in cima le voci **«da leggere»**, quelle che cambiano cosa garantisce la PR: deroghe `test`, `ci`, `threshold`, `command` e per pattern; livello sotto il minimo con tetto; revisione «non verificata» e audit «sospesi»; rilievi `blocker`/`major` declassati o archiviati; `approve unverified-tests`; must-have con `— test: manuale`; merge non verificati segnalati da `sentinel`; periodi con tollgate spento. Tutto il resto (deroghe `scope` entro il secondo, `allow_no_tests`, `verification_watch`, task oltre `task_lines_warn`, skill assenti, PR non `tg/*`, PR `tollgate-config/*`) è **«informativo»**, in un blocco richiudibile. `tollgate/attention` diventa rosso solo se c'è almeno una voce «da leggere»; con sole voci informative resta verde con una nota.

**Il commento.** Riporta lo SHA e non viene aggiornato se lo SHA non è più la testa. Il testo che viene dall'agente è neutralizzato: va in blocchi di codice con un recinto più lungo di qualunque sequenza di backtick contenuta, le menzioni sono disattivate e c'è una lunghezza massima.

### 9.3 Protezione del ramo e modalità del gate

**Come si sceglie la modalità.** La lettura della protezione (`GET /repos/{o}/{r}/branches/{b}/protection`) richiede il permesso di amministrazione in lettura, che il token consigliato per l'agente non ha (verificato su docs.github.com). Per questo la misura **solo `init`**, eseguito con le credenziali dell'utente:
- HTTP 403 con il messaggio «Upgrade to GitHub Pro or make this repository public to enable this feature.» → `detect`;
- HTTP 200 → `protected`, con la protezione già presente: `init` segnala i campi mancanti;
- HTTP 404 con il messaggio «Branch not protected» → `protected`: il repo può avere la protezione ma non ce l'ha ancora, e `init` propone il comando;
- ogni altro 403 (per esempio permessi mancanti, con lo stesso codice del primo caso) o qualunque altra risposta → «non determinata»: `init` lo dice e chiede all'utente di rilanciarlo con le sue credenziali. Mai `protected` per esclusione.

Le risposte sono quelle osservate in P0. Il piano dell'account non si usa: `GET /user` restituisce `plan: null` senza lo scope `user`. I rulesets non sono un'alternativa su un repo privato con Free: la loro API risponde con lo stesso 403.

La modalità va in `[gate] mode` di `tollgate.toml`, quindi cambia solo con una PR `tollgate-config/*`. `start`, il blocco JSON della PR e `/tollgate:status` la leggono da lì; `work_items.gate_mode` ne è una copia presa all'avvio. Se il piano GitHub cambia, si rilancia `init --update`.

**In `detect`:** gli stessi workflow, più `tollgate-sentinel` che diventa l'unico controllo dopo il merge. `start` mostra a ogni avvio «modalità rilevazione: il merge non è impedito». Restano negati in locale, in qualunque sessione del repo attivo, il push sul ramo predefinito e `gh pr merge` (7.4), come guardrail. Le issue di `sentinel` le chiudi tu su GitHub dopo averle lette; chiuderle dall'agente è un effetto esterno. `start` legge le issue aperte «tollgate: merge non verificato» e le mostra.

**In `protected`,** `/tollgate:init` propone il comando `gh api` completo:
- PR obbligatoria;
- controlli obbligatori `tollgate/guard` e `tollgate/verdict`, con la sorgente fissata su GitHub Actions (`app_id`). Funziona anche per gli stati di commit: uno stato pubblicato con un token personale lascia la PR bloccata (verificato in P0). Il comando proposto da `init` non scrive `app_id` a mano: lo legge, quando lo lanci, dal check-run di `tollgate-base` sul commit che installa i workflow (15368 per GitHub Actions su github.com), e si ferma se non lo trova. Per questo si lancia dopo quel commit (11.2). Omettere `app_id` non toglie la sorgente: GitHub tiene l'ultima vista. «Qualunque sorgente» si ottiene solo con `-1`, che `init` non propone mai;
- `strict`;
- regole valide anche per gli amministratori;
- niente push forzato né cancellazione.

Il comando lo esegui tu. `start` prova a leggere la protezione e segnala i campi mancanti; se non ha i permessi per leggerla, lo dice e prosegue.

### 9.4 Aggiornamenti, emergenze e hotfix

**Aggiornare tollgate.** Si usa una PR da `tollgate-config/*` che contiene solo file di tollgate e file sotto `.tollgate/waivers/`.
- Passa `guard`.
- È esente da test-guard e scope.
- `attenzione` è sempre rosso.
- Il riepilogo mostra le chiavi che allentano il gate e l'impronta del CLI.
- L'agente non scrive i file: `init --update` prepara la proposta e tu li copi.

**Emergenza (gate guasto).** Il merge di riparazione fa scattare `tollgate-sentinel`: è atteso. Solo tu puoi:
1. disattivare i controlli obbligatori;
2. fare il merge della riparazione;
3. riattivare i controlli.

**Hotfix urgente.** Una PR fatta a mano da un ramo non `tg/*` ottiene i controlli sui test e `attenzione` rosso. È la corsia d'emergenza dichiarata. Va fatta fuori da Claude Code o da una sessione non legata a un lavoro: in una sessione legata il push di altri rami è negato (6.6).

### 9.5 Costo

| Quando | Cosa gira |
|---|---|
| Ogni push sulla PR | `guard` in parallelo a `run` (`setup` + gate), poi `verdict`. `guard` e `verdict` sono brevi |
| Ogni push sul ramo predefinito | `tollgate-base` (suite completa) e `tollgate-sentinel` (breve) |
| Cache della base assente | La base va eseguita di nuovo |

**Stima.** Per ogni merge sul ramo predefinito: `base` + `gate` × (PR aperte che `strict` rende vecchie e che vanno risincronizzate). `init` misura la durata di `finish check` e mostra la stima in minuti al mese per un ritmo di merge che indichi tu. Riferimento: GitHub Free include 2.000 minuti al mese per i repo privati (docs.github.com, «About billing for GitHub Actions»).

`base_test_ids` si può spegnere; senza, `tollgate-base` non gira.

### 9.6 Servizi

`/tollgate:init` chiede quali servizi servono ai test e li mette in `tollgate-run`. Se il gate non può girare in CI, `start` lo segnala.

---

## 10. Revisione finale

| Livello | Revisori |
|---|---|
| L0 | Nessuno |
| L1 | `final-reviewer` con la checklist dei profili attivi → `finding-verifier` sui rilievi registrati → verdetto |
| L2 | Come L1, più gli specialisti finali dei profili attivi che ne dichiarano uno (`final_specialist`), in parallelo al revisore generale; tutti i rilievi vanno allo stesso verificatore |

**Verificatore.** Uno per ciclo. Esamina i rilievi in ordine di gravità fino a `max_findings` (15); quelli oltre il limite restano «non verificati».

**Cosa ferma la PR.** I rilievi confermati `blocker` o `major`, salvo un `approve finding`. `moderate` e `minor` vanno nel commento della PR come note (standard del revisore, 8.6).

**Cicli di revisione.**
- Tetto di 4, contando **solo i cicli con rilievi confermati**. Il `needs_you` si apre alla fine del quarto ciclo con rilievi confermati.
- Il blocco si scioglie con `approve rounds`, `approve finding` o `resolve`.
- Massimo 8 cicli, contando **tutti** i cicli; oltre serve `approve unverified-review`.
- I cicli sono registrati in `review_cycles` (12.2).
- Dopo un rebase con lo stesso `patch-id` non serve un nuovo ciclo.

C'è una sola revisione finale: `tollgate:execute` non ne ha una propria.

---

## 11. Installazione e configurazione

### 11.1 Dipendenze

- **Superpowers** (versione minima 6.4.1), per brainstorming, writing-plans, TDD e debugging. Di Superpowers tollgate usa solo il formato del piano (`### Task N`, `Create:`/`Modify:`/`Test:`), che `plan-check` verifica. In `dependencies` va **senza `version`** (verificato in P2, 16): la documentazione risolve i vincoli sui tag `<plugin>--v<versione>`, mentre Superpowers ha solo `v6.4.1` e `v6.4.2`, e con un repository proprio l'installazione potrebbe fallire («has no git tag satisfying»). La versione minima la controlla `start` leggendo il `plugin.json` di Superpowers (P3). `plugin.json` si convalida con `claude plugin validate`.
- **`marketplace.json`** con l'allowlist tra marketplace.

### 11.2 `/tollgate:init`

**La proposta**, scritta in `docs/superpowers/tollgate-init/`, contiene:
- `tollgate.toml`;
- i workflow, con i servizi;
- il CLI e la sua impronta;
- la modalità del gate misurata (9.3) e, in `protected`, il comando per la protezione del ramo;
- la stima dei minuti di Actions (9.5);
- per i progetti con jest, la configurazione di jest-junit che mette il file nell'identificativo: `classNameTemplate = "{filepath}"` e `titleTemplate = "{classname} {title}"`. Con quella predefinita due test omonimi in file diversi hanno lo stesso identificativo, e un test cancellato in un file sarebbe coperto dall'omonimo di un altro (7.5, verificato in P0);
- la configurazione consigliata di un **token GitHub separato per l'agente**: contenuti, PR e issue, senza amministrazione né `project`. Il token per C lo definirà C.

**I tuoi passi:** copi i file, li committi sul predefinito **prima** di attivare la protezione, poi lanci il comando. Il commit fa partire `tollgate-base`, dal cui check-run il comando legge `app_id` (9.3).

### 11.3 `/tollgate:setup`

Un plugin non può impostare la statusline principale (verificato). `/tollgate:setup` ti mostra la modifica da fare a `~/.claude/settings.json`. La statusline scrive il file `<cartella di stato>/ctx/<session_id>.json` nella forma `{"used_pct": <numero o null>}` (decisione 13 del piano P2). File assente, illeggibile o con `null` non bloccano nulla: la guardia del contesto, in quel caso, non interviene.

### 11.4 `tollgate.toml`

```toml
schema_version = 1

[project]
allow_no_tests = false

[commands]
setup          = "npm ci"
verify         = "npm run check"
test_related   = "npx vitest related --run {files}"
gate           = ["verify"]                 # nomi di chiavi di [commands]
report         = "junit:reports/junit.xml"  # una stringa per tutti i comandi del gate, o una mappa { nome = "junit:…" }
report_related = "junit:reports/junit-related.xml"
env_allow      = ["PATH", "HOME", "LANG", "CI", "NODE_ENV"]
timeout_s      = 900

[gate]
mode = "protected"   # protected | detect: lo scrive init dopo averlo misurato (9.3)

[acts]
ttl_minutes = 10

[hooks]
timeout_s = 20

[levels]
sensitive_paths  = ["**/migrations/**", "**/auth/**"]
sensitive_labels = ["security", "database"]
l0_max_files = 2
l0_max_lines = 50
l0_max_bytes = 4000

[context]
warn_pct = 45
stop_pct = 55

[plan]
required_sections = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope", "Punti di arresto", "Rischi"]
max_scope_files   = 30

[scope]
always    = []                               # file ammessi in ogni piano (es. CHANGELOG.md)
lockfiles = { "package-lock.json" = "package.json", "pnpm-lock.yaml" = "package.json", "poetry.lock" = "pyproject.toml" }

[external_effects]
commands        = []
project_scripts = ["deploy", "release"]
allow           = []                         # pattern di comandi in sola lettura
mcp_allow       = []

[test_guard]
test_globs         = []                      # in aggiunta ai predefiniti (8.2)
fixture_globs      = ["**/fixtures/**/*.json", "**/__snapshots__/**"]
ci_globs           = [".github/workflows/**"]
verification_globs = ["**/vitest.config.*", "**/vitest.setup.*", "**/jest.config.*", "**/playwright.config.*", "**/.mocharc.*", "**/conftest.py", "**/pytest.ini", "**/tox.ini", "**/setupTests.*", "**/.coveragerc", "**/.nycrc*", "**/cypress.config.*", "**/karma.conf.*", "**/.env.test", "scripts/check*"]
verification_watch = ["**/package.json", "**/vite.config.*", "**/tsconfig*.json", "**/setup.cfg", "**/pyproject.toml", "**/Makefile", "**/.babelrc", "**/babel.config.*", "**/.swcrc", "**/.npmrc"]
skip_markers       = []
assert_markers     = []

[spec_audit]
spec_rounds       = 4
plan_rounds       = 2
spec_audit_cycles = 30

[tasks]
task_lines_warn = 200
task_lines_max  = 500
task_files_warn = 8
max_turns       = 60
max_tokens      = { L0 = 0, L1 = 400000, L2 = 800000 }   # 0 = nessun tetto

[review]
readonly_agents = ["tollgate:task-reviewer", "tollgate:final-reviewer", "tollgate:finding-verifier", "tollgate:plan-adversary", "tollgate:spec-adversary", "tollgate:spec-auditor", "Explore"]
output_dirs     = ["reports/", "coverage/"]
max_findings    = 15
stale_minutes   = 30
models          = {}   # es. { "tollgate:spec-auditor" = "sonnet" }; vuoto = model del file dell'agente

[severity]   # da adattare al progetto
blocker  = "perdita o esposizione di dati, azione eseguita due volte, sicurezza compromessa"
major    = "un comportamento sbagliato o un passo che fallirebbe così com'è"
moderate = "debito o attrito che emergerà più avanti"
minor    = "redazionale"

[retention]
retention_days = 30
events_days    = 180

[profiles]
active = []          # vuoto = attivazione per paths sul diff; nomi = sempre attivi

[profiles.base]      # contratto di un profilo (B ne aggiunge altri)
kind           = "vertical"   # vertical | cross (6.3)
cross          = []   # profili trasversali le cui regole si aggiungono al revisore
paths          = ["**"]
setup          = ""   # gira dopo il setup globale; i profili in ordine di nome
commands       = {}   # comandi propri del profilo: { nome = "comando" }
gate           = []   # nomi di chiavi di commands del profilo
test_related   = ""
report         = ""   # come [commands] report: stringa o mappa per nome
test_globs     = []
skip_markers   = []
assert_markers = []
plan_sections  = []
min_level      = "L0"
dod            = []   # nomi di comandi del profilo che entrano nella Definition of Done (8.7)
checklist      = ""   # percorso di un file con la checklist per il revisore finale
skills         = []   # skill che ogni implementatore deve usare sui task di questo profilo
agent          = ""   # implementatore per area, "<plugin>:implementer-<area>" (6.3)
reviewer       = ""   # revisore del task per area, "<plugin>:reviewer-<area>"
reviewer_skills = []  # skill del revisore del task, al massimo 3
final_specialist = "" # solo L2: specialista della revisione finale, "<plugin>:final-<area>"; vuoto = nessuno

[components]         # mappa aperta (R10)
scope_check = true
plan_check = true
test_guard = true
context_guard = true
subagent_receipt_gate = true
single_writer = true
readonly_check = true
final_review = true
spec_adversary = true
spec_audit = true
plan_adversary = true
base_test_ids = true
sentinel = true
task_size = true        # 6.3: soglie di righe e file
task_budget = true      # 6.3: maxTurns e tetto di token
definition_of_done = true  # 8.7
must_have_tests = true  # 7.5: ogni must-have legato a un test
report_fields = true    # 18.5: report a campi fissi
reviewer_standard = true   # 8.6: standard del revisore e disaccordo istruito
spec_pitch = true       # 6.2: «Tane di coniglio» e «Cosa non fare»
```

Le soglie della revisione 18 vengono da pratiche pensate per le persone (Google, GitLab, DORA, Shape Up) e non sono misurate sugli agenti: si regolano in `[tasks]` e si tarano con le misure del sotto-progetto D. Quando un lavoro si ferma, `status` dice **quale** tetto l'ha fermato (budget del task, giri di correzione o cicli di revisione).

---

## 12. Stato locale

### 12.1 Il file

- `tollgate.db` sta nella cartella di stato, uno per macchina.
- SQLite in modalità WAL, con `synchronous=FULL` e `busy_timeout=5000`.
- A ogni cambio di fase viene fatta una copia in `backup/` con la API di backup di SQLite (non copiando il file, che in WAL non è coerente); si tengono le ultime 10.
- **DB guasto.** Gli hook di controllo escono con 2 e indicano l'interruttore; gli hook informativi e `UserPromptExpansion` escono con 0 (7.1). Il ripristino si fa **dal terminale**: `<percorso assoluto>/bin/tollgate db restore`, riportato in ogni messaggio d'errore. Non richiede un atto, perché il DB degli atti è quello guasto; funziona solo se `PRAGMA integrity_check` fallisce e chiede conferma su un terminale interattivo. Un agente potrebbe simulare un terminale, ma l'impatto è nullo: serve un DB già corrotto, e il ripristino porta a una copia precedente. Sposta da parte il DB guasto e ripristina l'ultima copia integra. Se nessuna copia è valida, parte da un DB vuoto e ti indica `/tollgate:adopt` per ogni lavoro con un ramo `tg/*`.

### 12.2 Tabelle

| Tabella | Colonne principali | Vincoli |
|---|---|---|
| `work_items` | id, repo_key, issue, level, level_cap (con motivo), phase, phase_before_block, branch, worktree, work_base_sha, gate_mode, spec_path, plan_path, sessions, created, updated, closed_reason | univoco (repo_key, issue) tra i lavori attivi |
| `scope` | work, path, origin, registered_at | |
| `receipts` | work, sha, command, resolved_command, exit, tests_run, tests_skipped, duration, log, produced_by, state | |
| `blocks` | work, type, reason, opened, closed, resolution | |
| `subagents` | id, name, type, work, task, agent_base_sha, fingerprint, started, ended, resumes, declared_status, state, tokens, duration | |
| `review_cycles` | work, number, sha, patch_id, outcome, findings_confirmed, counted | |
| `findings` | id, work, cycle, source, severity, confidence, file, line, text, verification, verification_reason, user_decision | univoco (work, id) |
| `spec_audit` | work, kind, number, viewpoint, counts, outcome, report_path | |
| `acts` | act_id, type, object, at, typed_text, source, actor, session, work, state, expires_at, consumed_at | |
| `intents` | work, action, idempotency_key, data, state, outcome, at | univoco (idempotency_key) |
| `tasks` | work, number, kind (`plan`, `fix`), source (task del piano, ciclo dei rilievi o gate), state (`pending`, `running`, `review`, `done`, `blocked`), fix_rounds, implementer, agent_type, reviewer_type, skills_required, skills_used, commits, verdict, review_code | univoco (work, number) |
| `events` | seq, v, at, host, session, work, repo_key, issue, type, data (18.4) | `seq` monotono per DB; sola aggiunta; l'unica cancellazione è la potatura oltre `events_days` |
| `meta` | schema_version | |

Le deroghe non sono nel DB: stanno nel ramo, in `.tollgate/waivers/<N>.toml`.

**Migrazione 2** (decisione 7 del piano P2; le migrazioni successive restano solo in avanti). Servono dati che lo schema 1 non ha:
- `session_seen(session, last_seen)`: ogni hook la aggiorna, per la sessione viva (0);
- `subagents.last_seen` (subagente fermo da più di `stale_minutes`), `subagents.vetoes` (i 2 veti di 8.1) e `subagents.report` (il report arrivato con `SubagentHandback` prima di `SubagentStop`);
- `tasks.pending` (`launch` o `resume`): il `task start` in sospeso di 6.3, scritto da `tasks.assign`;
- `work_items.level_cap_paths`: il tetto di livello resta finché il diff non tocca un percorso sensibile nuovo (5).

**Chiavi sconosciute in `tollgate.toml`:** ignorate con un avviso, così B può aggiungere chiavi di profilo. Una chiave nota con un tipo sbagliato è un errore.

### 12.3 Fasi

| Livello | Sequenza |
|---|---|
| L0 | `execution` → `review` (solo `finish check`) → `pr_open` → `closed` |
| L1 | `plan` → `execution` → `review` → `pr_open` → `closed` |
| L2 | `spec_audit` → `plan` → `approval` → `execution` → `review` → `pr_open` → `closed` |

**Passaggi in avanti con condizione:** `execution` → `review` solo con `finish check` verde.

**Ritorni ammessi:**
- `review` con `needs_fix` → `execution`;
- `review` → `execution` con `start`, per correggere prima di `open-pr` (anche in L0);
- `pr_open` → `execution`, con `start` o `sync`;
- `plan`, `approval`, `execution` → `spec_audit`, con `reopen spec`;
- `approval`, `execution` → `plan`, con `reopen plan`;
- L0 che cresce → `plan`;
- da qualunque fase → `blocked`, e poi indietro alla fase precedente quando si chiude l'ultimo blocco;
- da qualunque fase → `closed`, quando viene rilevato il merge o la chiusura.

Ogni altra transizione viene rifiutata.

### 12.4 Ripresa, adozione, pulizia

**Ripresa** (`start` su un lavoro attivo):
- controlla worktree e SHA. Worktree assente (per esempio un crash durante l'avvio): lo ricrea sul ramo esistente, o sulla base se manca anche il ramo;
- rebase in corso nel worktree (un `sync` interrotto): propone `rebase --abort`;
- accetta il worktree sporco e propone un commit di lavoro in corso;
- segna come `interrupted` i subagenti `running` delle sessioni non vive (0), con la stessa regola di `SessionStart`;
- chiede conferma per gli intenti in sospeso;
- senza rete riparte con un avviso.

**Adozione** (DB perso).
- Su un ramo `tg/*` che non ha riga nel DB, gli hook negano tutto tranne i `.md` sotto `docs/superpowers/` e indicano `/tollgate:adopt #N`.
- `adopt` ricostruisce il lavoro da ramo, piano, deroghe, report, file di approvazione e PR esistente. Regola: **senza prova nel ramo, la fase torna a quella che precede l'atto mancante.**

| Dato | Fonte | Se manca |
|---|---|---|
| Livello | Ricalcolato sul diff, più le etichette | — |
| Tetto di livello | Blocco JSON della PR, se c'è | Perso: serve un nuovo `approve level` |
| `approve spec`, `approve plan` | `spec-approval.md`, `plan-approval.md` | Fase `spec_audit` o `approval` |
| Scope | Il piano del lavoro (7.5) | Fase `plan` |
| Deroghe | `.tollgate/waivers/<N>.toml` | — |
| Deroghe approvate | Nessuna | Tornano in attesa: serve un nuovo `approve waiver` |
| Blocchi aperti, cicli di revisione | Nessuna | Persi; i rilievi si rifanno con un nuovo `finish` |
| Fase dopo la PR | PR aperta → `pr_open` | — |
- Gli intenti non si ricostruiscono: gli effetti già eseguiti risultano non eseguiti, quindi ripeterli richiede un nuovo atto.

**Pulizia.**
- `start` cancella log e file di contesto vecchi.
- `/tollgate:cleanup` cancella rami e worktree dei lavori chiusi.

**Migrazioni.** Solo in avanti, con una copia prima di ciascuna.

**Due sessioni sullo stesso lavoro.** Se un'altra sessione è viva (0), `start` avvisa e chiede conferma. Se una sessione caduta risulta ancora viva e il suo implementatore blocca lo scrittore unico, il veto di `PreToolUse Agent` indica `/tollgate:resolve writer`.

---

## 13. Errori e casi limite

| Situazione | Comportamento |
|---|---|
| Controllo in errore, crash o timeout | Uscita 2, con il log, l'invito a `/tollgate:off` e il comando da terminale `touch ~/.local/state/tollgate/OFF` |
| `SubagentStop` in errore | Uscita 0 con avviso |
| Python o DB rotti | `/tollgate:off` funziona senza nessuno dei due |
| DB guasto | `bin/tollgate db restore` dal terminale (12.1) |
| `OFF` dimenticato | Avviso a ogni hook; scadenza facoltativa |
| `origin/HEAD` assente | Si prova `main` e poi `master`; se manca anche quello, avviso |
| Gate assente | `start` rifiuta |
| Protezione assente per il piano (privato con Free) | Modalità `detect`, con avviso a ogni avvio (9.3) |
| Protezione disponibile ma incompleta | `start` avvisa con i campi mancanti |
| Merge o push non verificati sul predefinito | `tollgate-sentinel`: stato rosso e issue; `start` li mostra |
| Versione del CLI diversa | Avviso e `init --update` |
| Effetto esterno | Veto fino all'atto, oppure eccezione in sola lettura |
| Comando di verifica assente | Ricevuta `unverified`, serve `approve unverified-tests` |
| Zero test | `empty`; il gate fallisce salvo `allow_no_tests`, con cui vale `green` e `attenzione` rosso |
| Comando di check con `\|\| true` | Il report con `failure` o `error` dà `red` (8.1) |
| Conflitto durante `sync` | `rebase --abort`, `needs_you` (6.5) |
| Ramo predefinito avanzato | `/tollgate:sync` |
| Verdetto rosso dopo la PR | `start` → `execution` → `finish` |
| PR chiusa senza merge | Ti chiede cosa fare |
| Sessione persa | I subagenti diventano `interrupted` |
| DB perso | `/tollgate:adopt` |
| Codemod su molti file | Deroga per pattern |
| PR enorme | Revisione entro `max_findings`; meglio dividerla in più issue (5) |
| Hotfix urgente | Corsia d'emergenza (9.4) |
| Aggiornare tollgate, gate guasto | 9.4 |
| PR di Dependabot | È una PR non `tg/*`: riceve i controlli sui test e `attenzione` rosso. `workflow_run` parte anche per Dependabot, con i permessi dichiarati (verificato in P0, 9.1): `verdict` arriva come per ogni altra PR |
| Artefatto non valido | `error` |
| Servizi per i test | 9.6 |
| Due macchine sulla stessa issue | `start` vede ramo e PR remoti e propone l'adozione |
| Rete assente | Ripresa con avviso; gli hook non usano mai la rete |
| Più fette | Un'issue per fetta (5) |
| Sviluppare tollgate con tollgate attivo | Cartelle diverse, oppure `/tollgate:off` |

---

## 14. Test del plugin

| Livello | Cosa | Come |
|---|---|---|
| Script | Sottocomandi, `plan-check`, test-guard per linguaggio, ricevute, gate, transizioni, `adopt` | Test unitari |
| Wrapper | Uscite, `OFF` con scadenza, repo non attivo | Script finti |
| Hook | Ogni riga di 7.2 e 7.4, con l'ambito di 6.6 | Input JSON uguale a quello di Claude Code |
| Integrazione | Avvio, ripresa, adozione, `finish`, `sync`, intenti, atti | Repo git temporaneo, `TOLLGATE_GH`, `TOLLGATE_STATE` |
| Gate | I casi del criterio 10 | Repo di prova **pubblico** (modalità `protected`, gratuita) e repo di prova privato con GitHub Free (modalità `detect`) |
| Comportamento | L'agente rispetta gli obblighi | `claude plugin eval`, 3 esecuzioni per caso |
| CI | Tutto quanto sopra | GitHub Action sul repo di tollgate |

**Casi di eval:**
1. DONE senza ricevuta → veto.
2. Conflitto tra test e specifica → `test_spec_conflict`.
3. Fuori scope → veto e deroga.
4. Deploy → veto fino all'atto.
5. L0 che cresce → L1.
6. Fine dei task di `tollgate:execute` → `/tollgate:finish`.
7. Spec con una contraddizione → trovata dall'avversario.
8. Cambio di ramo per sfuggire alle regole → veto.
9. Il coordinatore invoca subagent-driven-development in `execution` → il lancio di un implementatore `general-purpose` viene negato e il veto indica `tollgate:execute`.

---

## 15. Criteri di accettazione del nucleo

Ogni criterio è un'azione con un esito binario.

1. **Avvio.** In un repo attivo con il gate, `start` crea worktree, ramo e riga. Senza `tollgate.toml` o senza gate → rifiuto con il motivo. Con ramo o PR remoti già presenti → proposta di adozione (integrazione).
2. **Piano.**
   - Senza le intestazioni esatte → veto e nessuno scope.
   - Con pattern o cartelle → veto.
   - Completo → scope registrato.
   - Riscritto con un file in più → scope invariato (hook).
3. **Scope.** In `execution` un file fuori scope → `deny`, e dopo la deroga passa. In `plan` sono ammessi solo i `.md` sotto `docs/superpowers/`. In L1 il codice scritto dalla sessione principale → `deny` (hook).
4. **Implementatore.** In `execution` (L1): `general-purpose` → `deny`; `tollgate:implementer` senza `task start` → `deny`; `SendMessage` a un implementatore senza `task start --fix` in sospeso → `deny`; `tollgate:implementer` lanciato senza il `name` del brief, o con `run_in_background`, → `deny`; `SendMessage` verso un nome mai registrato → `deny`; `SendMessage` verso il nome dell'implementatore con `task start --fix` in sospeso → ammesso, e `SubagentStart` non sovrascrive `agent_base_sha`; `task done` senza verdetto `approved` → rifiuto; dopo `task start 2 --fix` per tre volte → `tasks.fix_rounds = 3`. Un subagente di qualunque tipo fuori da `readonly_agents`, con DONE e senza ricevuta `green` → veto; al terzo tentativo `needs_you`. Con DONE, file modificati e nessun commit → veto. Con BLOCKED e ricevuta rossa → chiude (hook).
5. **Commit.** Con `git add -A && git commit`, questi casi → `deny`:
   - test cancellato;
   - `xdescribe` o `pytest.skip(` aggiunti;
   - asserzione tolta, anche se sostituita da un commento;
   - test in `src/__tests__/` cancellato.

   `process.exit(` → nessuna segnalazione (hook, script).
6. **Comandi.**
   - Effetti esterni, `gh pr edit`, `gh api graphql` con `mutation`, script del repo non tracciato → veto; dopo l'atto passano una volta.
   - Comando in `allow` → passa.
   - Distruttivi, `claude -p`, `TOLLGATE_STATE=…` → `deny`.
   - In un repo non attivo `git push` passa (hook).
7. **Ambito.** In una **nuova sessione avviata nel worktree** dopo `start`: `git switch -c altro` → `deny`; `git checkout -B altro` → `deny`; push di un ramo non `tg/*` → `deny`; dopo `cd` nel checkout principale, Edit lì → `deny` e `gh pr create` → `deny`. Un `git merge` nel worktree che porta un test cancellato → blocco `needs_you` (hook).
8. **Subagenti.**
   - A `stop_pct` → `deny`.
   - Con valore `null` → permesso.
   - Secondo implementatore → `deny`.
   - Subagente fermo oltre `stale_minutes` → `interrupted`, e un nuovo implementatore è permesso (hook).
9. **Revisori.**
   - Verdetto senza codice → non valido.
   - Revisore che modifica file → `needs_you`.
   - JSON malformato → `needs_you`.
   - Rilievo senza esito → `open-pr` rifiuta.
   - Fine del quarto ciclo con rilievi confermati → `needs_you`; `approve rounds 1` → un ciclo in più.
   - In auto mode, verdetto consegnato con `SubagentHandback` → letto e valido.
   - Ciclo senza rilievi confermati → non conta (hook, integrazione).
10. **Gate su GitHub.** Sul repo di prova:
    - **verdi**: PR pulita; PR `tollgate-config/*` (con `attenzione` rosso); PR fatta a mano da un ramo non `tg/*` (con `attenzione` rosso);
    - **`verdict` rosso**: test tolti, `skip`, file fuori scope, identificativo della base mancante, `"check": "vitest run || true"` con un test che fallisce, livello sotto il minimo senza tetto, report L2 mancante;
    - **deroghe**: una deroga nel file di un'altra issue non scioglie la violazione;
    - **`tollgate/sentinel` rosso e issue aperta**: push diretto sul predefinito; merge di una PR con `verdict` rosso (nel repo `detect`);
    - **`guard` rosso**: `tollgate.toml` cambiato, `tollgate-verdict.yml` modificato fuori da `tollgate-config/*`, workflow del progetto aggiunto con `statuses: write`, con `checks: write`, con `pull_request_target`, con `workflow_run`, oppure senza `permissions`;
    - **verde con `attenzione`**: workflow del progetto modificato con `permissions: contents: read` e deroga `ci`;
    - **`attenzione` rosso**: deroga `test`, piano diverso dal primo, tetto di livello dichiarato, `allow_no_tests` con zero test;
    - **`error`**: `../` in un artefatto, XML con entità, SHA superato;
    - **«non applicabile»**: PR verso un ramo non predefinito.

    In `protected`, uno stato `tollgate/verdict` pubblicato con un token personale non soddisfa la protezione (gate).
11. **Protezione e modalità.** Su un repo privato con GitHub Free `init` sceglie `detect` e `start` lo mostra; su un repo pubblico non ancora protetto (404 «Branch not protected») sceglie `protected` e propone il comando; su un repo pubblico protetto sceglie `protected` e `start` segnala i campi mancanti di 9.3 (integrazione, gate).
12. **PR.** Senza un atto `finish` successivo all'ultimo commit e senza `approve pr` → rifiuto. Un `finish` seguito da una revisione di più di 10 minuti → PR aperta; un commit dopo `finish` → l'atto decade. Un atto `finish` di un altro lavoro → rifiuto; dopo `/clear` lo stesso `finish` vale ancora. Interruzione tra push e PR → nessuna PR doppia (integrazione).
13. **Atti.** Solo da `UserPromptExpansion`; lo strumento Skill non produce atti (hook).
14. **Wrapper.**
    - Hook di controllo: 1, 127, eccezione o scadenza → 2.
    - Hook informativi e `SubagentStop` → 0.
    - Repo non attivo senza Python → 0.
    - `OFF` → passa, con avviso e registrazione; `OFF` scaduto → regole attive (wrapper).
15. **Ricevute.** Zero test → `empty`. Report vecchio → cancellato prima di eseguire. Una variabile non in `env_allow` non arriva a `verify` (script).
16. **Sync.**
    - Dopo un avanzamento del ramo predefinito, anche con un merge remoto sulla PR: ramo aggiornato, base riallineata, PR aggiornata.
    - Stesso `patch-id` → nessun ciclo consumato.
    - Push forzato senza `sync` o `approve rebase` → `deny`.
    - Rebase con conflitto → `rebase --abort`, `work_base_sha` e fase invariati, `needs_you`.
    - `tollgate sync` senza un atto `sync` non consumato → rifiuto (integrazione).
17. **Adozione e ripristino.** Dopo aver cancellato il DB, gli hook su `tg/*` negano e indicano `adopt`. Dopo `adopt` su un lavoro L2 in `execution`: con `plan-approval.md` la fase resta `execution`, senza torna `approval`; le deroghe approvate tornano in attesa. Con il DB corrotto e `OFF` attivo, `db restore` dal terminale ripristina l'ultima copia integra; lanciato senza terminale interattivo, rifiuta (integrazione).
18. **Componenti.** Ogni chiave di `[components]` impostata a `false` spegne il suo modulo (script, hook).
19. **Budget.** Lo stato iniettato è al massimo 10 righe e 1.500 caratteri (hook).
20. **Rinomine.** Un file di test rinominato con gli stessi test → nessuna segnalazione (script).
21. **Deroghe.** Gli `scope` valgono subito fino al secondo; un `test` resta in attesa; una deroga per pattern resta in attesa ed è in `attenzione` (script, gate).
22. **Livelli.**
    - L0 oltre le soglie → L1 e `plan`.
    - Percorso sensibile → L2.
    - Il tetto di `approve level` resta finché il diff non tocca un percorso sensibile nuovo.
    - Livello dichiarato sotto il minimo senza tetto → `verdict` rosso; con tetto → `attenzione` (hook, integrazione, gate).
23. **Effetti ripetuti.** Stesso effetto sullo stesso SHA → l'avviso cita l'esecuzione precedente (hook).
24. **Audit della spec.**
    - `approve spec` rifiutato se l'ultimo giro ha `blocker` o `major`; accettato dopo un giro pulito.
    - Quarto giro ancora con `blocker` o `major` → `needs_you`; `resolve` → «avversariale sospeso» nella PR.
    - Con «Fette previste» = 1 l'audit a lenti non parte; con 3 parte, e `approve spec 3` è rifiutato finché l'audit a lenti non è chiuso o sospeso. `approve spec 1` su una spec con 3 fette → rifiuto.
    - Dopo `approve spec`, `spec-approval.md` esiste con lo SHA della spec; un Edit dell'agente su quel file o sulla spec → `deny`. Spec modificata dopo l'ultimo giro → `approve spec` rifiutato.
    - `start #M --spec <percorso>` con una spec approvata sul ramo predefinito → fase `plan`; senza report di approvazione → rifiuto.
    - Una correzione `major` azzera il contatore del punto di vista che l'ha trovata (hook, integrazione).
25. **Fasi.** Le transizioni fuori da 12.3 vengono rifiutate (script).
26. **Da correggere.** `needs_fix` → `execution`; il `finish` successivo consuma un ciclo (integrazione).
27. **Neutralizzazione.** Una deroga con ``` e `@utente` nel testo non produce markdown attivo né menzioni (gate).
28. **Ripresa.** Worktree sporco → ripresa con proposta di commit. Interruzione dopo `finish check` → si riparte dal ciclo registrato. Senza rete e con il checkout principale sporco → ripresa con avvisi. Worktree assente → ricreato. Con due sessioni vive, la seconda non segna `interrupted` l'implementatore della prima (integrazione).
29. **Profili.** Un profilo con `paths = ["web/**"]` è attivo solo se il diff tocca `web/`, e il suo `gate` viene eseguito (script, gate).
30. **Senza test.** Con `allow_no_tests = true` e zero test: DONE passa, il gate è verde con `attenzione` rosso (hook, gate).
31. **Fasi dopo `finish`.** In `review` e `pr_open` un Edit su un file di codice → `deny`; `finish check` rosso → la fase resta `execution` (hook, integrazione).
32. **Marcatori e skipped.** `@pytest.mark.skip` aggiunto → `deny` al commit; un identificativo della base `skipped` nel JUnit della testa → `verdict` rosso (hook, gate).
33. **Issue e deroghe nel gate.** Una PR `tg/7-x` con «Closes #3» (issue già chiusa, con deroghe nella base) → `verdict` rosso e nessuna deroga applicata (gate).
34. **Modalità.** `init` con un token senza amministrazione → «non determinata», mai `protected`. In `detect`, `git push origin main` da una sessione non legata → `deny`. Il primo push che installa `tollgate-sentinel` non apre l'issue (integrazione, gate).
35. **Componenti spenti.** Con `spec_audit = false` e tre fette, `approve spec 3` è accettato senza audit a lenti e il gate dà `attenzione` rosso, non `verdict` rosso (integrazione, gate).
36. **Piano registrato nel gate.** Piano modificato dopo la registrazione in modo da includere un file in più → quel file è fuori scope nel gate e `attenzione` mostra il diff del piano (gate).
37. **Flusso dopo l'approvazione.** In `spec_audit` la scrittura di un piano → `deny`. In L2 il piano corretto da `plan-adversary` → `plan_sha` è quello di `approve plan`. Edit sulla spec in fase `plan` dopo `approve spec` → `deny`; `reopen spec` → fase `spec_audit` e nuova approvazione richiesta. `needs_fix` → `task start --from-findings` crea un task `fix` senza toccare il piano (hook, integrazione).
38. **Profili verticali.** Con un profilo `web` (`paths = ["web/**"]`, `skills = ["ui-ux-pro-max"]`, `agent = "probe:implementer-frontend"`, `reviewer = "probe:reviewer-frontend"`): in L1 un task su `web/` → `task start` sceglie `probe:implementer-frontend` e `probe:reviewer-frontend`; `tollgate:implementer` su quel task → `deny`; DONE senza aver invocato `ui-ux-pro-max` → veto. Un task su `web/` e `api/` con due agenti diversi → `tollgate:implementer` con l'unione delle skill. In L2 un profilo con `final_specialist` attivo → lo specialista gira insieme a `final-reviewer`, e i suoi rilievi passano dal verificatore. Due profili verticali che coprono lo stesso file: vince quello con più segmenti letterali, a parità il primo dichiarato. Un profilo `cross` aggiunge i suoi `reviewer_skills` al revisore dei verticali che lo elencano. Un task con più di 3 skill nell'unione → `plan-check` lo segnala. `reviewer-<area>` e `final-<area>` sono in `readonly_agents`, `implementer-<area>` no (hook, integrazione).
39. **Task piccoli e budget.** Un task con 600 righe e senza `size_reason` → report non valido; con `size_reason` → `attenzione` lo riporta. Un implementatore oltre `max_tokens`, anche se chiude con DONE e ricevuta `green`, o che esaurisce `maxTurns` → task `blocked` e `needs_you`; al taglio di `maxTurns`, che non produce `SubagentStop`, la riga del subagente è chiusa e un nuovo implementatore è ammesso subito; un report del subagente che contiene «stopped at its 2-turn limit» non è scambiato per un taglio; `status` dice quale tetto ha fermato il lavoro. Un report senza i campi obbligatori → veto (hook, integrazione).
40. **Revisione.** Un rilievo `minor` non porta il task a `changes`; un rilievo senza `rule`, oppure senza file e riga → scartato dal verificatore (integrazione).
41. **Definition of Done.** `finish check` stampa la DoD voce per voce; con un task non `done` → `open-pr` rifiuta. Una spec L2 senza `## Cosa non fare` → rilievo dell'avversario (integrazione).
42. **Must-have legati ai test.** Un piano L1 con un must-have senza `— test:` → `plan-check` rifiuta. Con `M1 — test: tests.test_x::test_a` (forma JUnit di pytest, 7.5) e quel test assente o rosso nella ricevuta finale → la DoD non passa e `open-pr` rifiuta; il gate ricalcola la stessa voce dal JUnit (script, gate).
43. **Statistiche.** Dopo un lavoro con due veti, un `needs_you` e un'ora di `OFF`, `tollgate stats --work N` riporta esattamente quei numeri, più tempo per fase e token (script).
44. **`attenzione` a due gruppi.** Una PR con sola deroga `scope` entro la seconda → `tollgate/attention` verde con nota; con una deroga `test` → rosso, e la deroga `test` compare in cima nel gruppo «da leggere» (gate).

---

## 16. Da verificare prima di scrivere codice

**Già verificato l'08/10/2026.**

| Cosa | Esito |
|---|---|
| Uscite degli hook | Solo l'uscita 2 blocca; timeout predefinito di 600 s |
| `PostToolUse` con `block` | Non annulla l'azione |
| `UserPromptExpansion` | Scatta sul comando digitato, non sullo strumento Skill |
| `disable-model-invocation` | Funziona |
| Strumento dei subagenti | Si chiama `Agent`; `agent_type` dei plugin ha la forma `plugin:nome` |
| `agent_id` | Presente solo nei subagenti |
| `SubagentStart` | Può iniettare contesto |
| Subagenti e skill | Un subagente con lo strumento Skill può usare le skill |
| `isolation: worktree` | Parte dal ramo predefinito; non compare nell'input di `Agent`; `WorktreeCreate` sostituisce la creazione |
| Statusline | Il plugin non può impostarla |
| `dependencies` | Formato confermato |
| `pull_request_target` e `workflow_run` | Usano la definizione del ramo predefinito; `workflow_run` ha un token di scrittura e scarica gli artefatti |
| `dontAsk` | Nega le richieste di conferma |
| Formato dei piani di Superpowers | Confermato |

**Verificato l'08/10/2026, cicli 31-38.**

| Cosa | Esito |
|---|---|
| Protezione del ramo sui repo privati | Solo con Pro o Team (docs.github.com, «GitHub's plans»); gli environments con revisori solo sui repo pubblici con Free |
| Token con scoping per ramo | Non esiste: `Contents: write` scrive su ogni ramo |
| Commit → PR | `GET /repos/{o}/{r}/commits/{sha}/pulls`, permesso «Pull requests: read» |
| Minuti di Actions | Free 2.000 al mese, Pro 3.000 |
| `SubagentHandback` | Esiste, solo in auto mode, dalla v2.1.271 (tools-reference) |
| `SubagentStart` | Riceve solo `agent_id` e `agent_type`, non il prompt |
| `PreToolUse` su `Agent` | `tool_input` contiene `prompt`, `description`, `subagent_type`, `model`, e `name` e `run_in_background` quando il chiamante li passa (P0) |

**Verificato in P0, l'08/10/2026** (rapporto in `docs/verifiche/2026-10-08-p0-esiti.md`; Claude Code 2.1.294, sessioni `-p` e interattive, repo di prova su GitHub Free).

| Cosa | Esito | Dove incide |
|---|---|---|
| Ripresa con `SendMessage` | `SubagentStart` e `SubagentStop` scattano di nuovo, con lo stesso `agent_id`. `tool_input` ha `to` (il **nome** dato al lancio), `message`, `summary`; `tool_response` ha `resumedAgentId` | 6.3, 7.2 |
| `SubagentHandback` e `last_assistant_message` | In auto mode `SubagentStop` non ha `last_assistant_message`; il report è in `tool_input.message` di `SubagentHandback` e, in primo piano, in `tool_response.handbackReport` di `PostToolUse Agent`. In modalità manuale `last_assistant_message` c'è | 7.2 |
| Taglio di `maxTurns` (primo piano) | Nessun `SubagentStop`; `PostToolUse Agent` con stato `completed`, `harnessNoteCount` 1 e un primo blocco di `content` «NOTE: this agent stopped at its N-turn limit…» | 6.3, 7.2 |
| Token dei subagenti | `usage` nel transcript; `PostToolUse Agent` in primo piano ha `totalTokens`, in background solo `agentId`. In primo piano `SubagentStop` arriva **prima** di `PostToolUse Agent` | 6.3 |
| `deny` in `bypassPermissions` | Rispettato | — |
| `UserPromptExpansion` | Scatta anche con `disable-model-invocation` e con la forma breve; `command_name` è sempre la forma lunga | 8.4 |
| Comandi `!` | Non passano da nessun hook | 1.2 |
| `skills:` e `mcpServers` negli agenti di plugin | `skills:` precarica la skill; `mcpServers`, `hooks`, `permissionMode` e `initialPrompt` sono ignorati (documentazione) | 6.3, catalogo dei profili |
| `EnterWorktree` | Accetta un worktree esistente; `tool_response` ha `worktreePath` e `worktreeBranch`; da lì il `cwd` degli hook è il worktree | 6.1 |
| Subagenti interni | `SubagentStop` con `agent_type` vuoto e senza `SubagentStart`: da ignorare | 7.2 |
| Protezione e rulesets su un repo privato Free | 403 «Upgrade to GitHub Pro or make this repository public to enable this feature.» per entrambi. Repo che si può proteggere ma non protetto: 404 «Branch not protected». `plan` illeggibile senza lo scope `user` | 9.3 |
| `actions: read` in `workflow_run` | Necessario per gli artefatti nei repo privati, non nei pubblici | 9.1 |
| `pull_request_target` verso un ramo non predefinito | Scatta e usa sempre la definizione del ramo predefinito | 9.2 |
| Sorgente fissata per gli stati di commit | Funziona: con `app_id` 15368 uno stato pubblicato con un token personale lascia la PR bloccata, uno di `github-actions[bot]` la sblocca | 1.2, 9.3 |
| Dependabot e `workflow_run` | Il `workflow_run` riceve i permessi dichiarati e i segreti normali | 9.1 |
| Tag di Superpowers | `v6.4.1` e `v6.4.2`, senza il nome del plugin; la documentazione chiede `<plugin>--v<versione>` (vedi P2) | 11.1 |
| JUnit di vitest, jest e pytest | Identificativi stabili; forma diversa per strumento; jest-junit senza il file con la configurazione predefinita | 7.5, 8.2, 11.2 |

**Verificato in P2, il 09/10/2026** (rapporto in `docs/verifiche/2026-10-09-p2-verifiche.md`; Claude Code 2.1.295).

| Cosa | Esito | Dove incide |
|---|---|---|
| Taglio di `maxTurns` per un subagente in background (E7) e alla ripresa con `SendMessage` (E8) | Nessun `SubagentStop`. `maxTurns` riparte da zero a ogni ripresa. Il taglio si riconosce da `UserPromptSubmit` con `prompt` `<task-notification>` che contiene «stopped at its N-turn limit»; `<task-id>` è l'`agent_id`. `PostToolUse SendMessage` non porta il taglio | 6.3, 7.2 |
| Input reali di `Write`, `Edit`, `Skill` e `Write` di un subagente (E9) | Campioni in `spikes/fixtures/hook-inputs/samples.json`. Con un permesso negato `PreToolUse` scatta e `PostToolUse` no | 7.2 |
| `dependencies` con `version` (D1) | I vincoli si risolvono sui tag `<plugin>--v<versione>` (documentazione); Superpowers ha solo `v6.4.1` e `v6.4.2`. Nessun `version`; ripiego di 11.1. Dipendenza tra marketplace: `allowCrossMarketplaceDependenciesOn`. Convalida: `claude plugin validate` | 11.1 |
| `additionalContext` e uscita 2 (D2, documentazione) | `additionalContext` vale per `SessionStart`, `SubagentStart` (contesto del subagente), `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`. Uscita 2: blocca `PreToolUse`, impedisce `SubagentStop`, mostra stderr al modello in `PostToolUse` | 7.2 |
| `MultiEdit` e `NotebookEdit` (D3, documentazione) | `NotebookEdit` esiste, con `notebook_path`; `MultiEdit` non è documentato | 7.2 |

**Ancora da verificare:**
- la forma dell'input di `NotebookEdit` osservata in un hook.

---

## 17. Cosa resta aperto

Sono le voci di 1.2, più due:
- i subagenti con `isolation: worktree` non vengono bloccati;
- i guardrail locali sono «best effort».

---

## 18. Formati

**Regola comune di versione** (blocco JSON, deroghe, report, eventi): un campo nuovo non cambia `schema_version`; un campo tolto o cambiato di significato sì. Chi legge ignora i campi, i valori di enum e i tipi di evento che non conosce. Ogni verdetto e ogni riga JSON dei subagenti porta `"v": 1`.

### 18.1 Blocco JSON nella PR

Va in un commento HTML `<!-- tollgate {...} -->`.

```json
{
  "schema_version": 1,
  "tollgate_version": "x.y.z",
  "issue": 42,
  "level": "L1",
  "level_minimum": "L1",
  "level_cap": null,
  "level_cap_reason": null,
  "gate_mode": "protected",
  "plan": "docs/superpowers/plans/2026-10-08-nome.md",
  "plan_sha": "…",
  "spec": null,
  "spec_reviews_dir": null,
  "plan_reviews_dir": null,
  "spec_audit": {"adversarial": null, "lens": null},
  "head_sha": "…",
  "receipts": [{"command": "verify", "state": "green", "tests_run": 120}],
  "waivers_file": ".tollgate/waivers/42.toml",
  "blocks": [],
  "acts": [{"act_id": "a-17", "type": "approve", "object": "waiver", "target": "w-42-3", "at": "…"}],
  "dod": {"L": "L1", "items": {"receipt": true, "tasks_approved": true, "must_have": true}},
  "verdict": {"outcome": "ok", "cycles": 1, "findings_confirmed": 0, "unverified": false},
  "findings": [{"id": "f-1-3", "severity": "major", "confidence": 0.8, "verification": "confirmed", "user_decision": null}],
  "fix_rounds": {"2": 1},
  "subagents": {"count": 7, "tokens": 412000},
  "effects": [{"command_hash": "…", "at": "…"}],
  "components_off": [],
  "off_periods": []
}
```

`spec_audit.adversarial` e `spec_audit.lens` valgono `null` (non applicabile), `closed`, `suspended` o `off` (componente spento). `fix_rounds` viene da `tasks.fix_rounds` (6.3), con il numero del task come chiave. `plan_sha` è lo SHA del piano al momento della registrazione dello scope. Gli atti in `acts` usano `act_id`, come in 12.2. `spec_reviews_dir` è la cartella dei report e del file di approvazione della spec: `docs/superpowers/reviews/<N>/` del lavoro che ha approvato la spec (la prima fetta); lo scrive `open-pr` da `work_items.spec_path`. `plan_reviews_dir` è la cartella dei report dell'avversario del piano del lavoro corrente. C e D leggono questo blocco senza parsare il testo libero della PR.

### 18.2 `.tollgate/waivers/<N>.toml`

Un file per issue. Il gate legge solo quello dell'issue chiusa dalla PR.

```toml
schema_version = 1
issue = 42
branch = "tg/42-nome"

[[waiver]]
id = "w-42-1"            # w-<issue>-<n>
type = "scope"            # scope | test | ci | threshold | command
file = "src/util/date.ts" # oppure pattern = "src/**/*.ts" (sempre in attesa)
tests = []                # per type = "test": identificativi
choice = "…"
why = "…"
cost = "…"
declared_by = "agent"     # agent | user
```

Regole (rev 21):
- `file` è relativo alla radice del worktree. `waiver add` con un percorso assoluto dentro il worktree lo rende relativo; fuori dal worktree è rifiutato.
- Per `type = "test"` serve `--test` con gli identificativi; senza, il comando è rifiutato.
- Una deroga con `tests` copre una violazione con identificativi solo se sono elencati **tutti** gli identificativi della violazione.

### 18.3 Intestazione dei report

```yaml
---
schema_version: 1
kind: spec-adversarial   # spec-adversarial | spec-lens | plan-adversarial | spec-approval | plan-approval
number: 2
viewpoint: null          # per spec-lens: uno degli otto punti di vista
spec_sha: "…"
counts: {blocker: 0, major: 1, moderate: 3, minor: 2}
outcome: findings        # findings | empty | suspended: lo calcola l'hook da counts (0)
---
```

Avversari e auditor chiudono il loro messaggio finale con una riga JSON con gli stessi campi. L'hook la legge.

I file `spec-approval` e `plan-approval` li scrive solo `act apply`, con questi campi al posto di `number`, `viewpoint`, `counts` e `outcome`: `path` (spec o piano), `sha` (del file approvato), `spec_sha` (solo per il piano: la spec su cui si basa), `slices` (solo per la spec), `adversarial` e `lens` (`closed`, `suspended`, `off` o `null`), `act_id`, `approved_at`.

### 18.4 Eventi

**Busta** (versione 1): `{"v": 1, "seq", "at", "host", "session", "work", "repo_key", "issue", "type", "data"}`. `host` è il nome della macchina: il DB è uno per macchina, e C e D possono unire più DB. `work` è l'identificativo locale; tra DB diversi vale la coppia (`repo_key`, `issue`). Un campo nuovo in `data` non cambia `v`; un campo tolto o cambiato sì.

**`data` dei tipi principali:** `phase_change` {from, to, cause}; `act` {act_id, type, object, target, args, source, actor}; `task_change` {number, kind, state, fix_rounds, verdict}; `finding` {id, cycle, severity, confidence, verification, user_decision}; `veto` {event, rule, reason}; `receipt` {sha, command, state, tests_run}; `subagent_stop` {id, type, task, declared_status, tokens}; `review_cycle` {number, outcome, findings_confirmed}; `spec_audit_round` {kind, number, viewpoint, outcome}; `effect_requested` e `effect_executed` {command_hash, id}. Gli altri tipi hanno `data` vuoto o con i soli identificativi dell'oggetto.

**Tipi:** `session_start`, `act`, `phase_change`, `level_change`, `scope_registered`, `waiver_added`, `block_opened`, `block_closed`, `commit`, `receipt`, `subagent_start`, `subagent_stop`, `veto`, `effect_requested`, `effect_executed`, `review_cycle`, `pr_opened`, `pr_updated`, `merge_detected`, `sentinel_alert`, `spec_audit_round`, `act_expired`, `task_change`, `finding`, `off`, `on`.

### 18.5 Rilievi e verdetti

**Revisore finale:** `{"sha", "code", "outcome": "ok" | "needs_fix" | "needs_you", "findings": [{"severity", "confidence": 0-1, "file", "line", "rule", "text"}]}`, dove `rule` è la regola `R-…` violata o il passo del piano (8.6). L'identificativo lo assegna `SubagentStop`: `f-<ciclo>-<n>`.

**Report dell'implementatore** (ultimo messaggio, un blocco JSON): `{"v": 1, "task": k, "status": "DONE" | "DONE_WITH_CONCERNS" | "BLOCKED" | "NEEDS_CONTEXT", "done": "…", "tests": "comando ed esito", "files": [...], "must_have": ["M1"], "concerns": "…", "left": "…", "size_reason": null}`. `size_reason` è obbligatorio oltre `task_lines_max`. Uno `status` fuori dai quattro valori rende il report non valido (fail-closed).

**Revisore del task:** `{"v": 1, "task": k, "sha", "code", "outcome": "approved" | "changes", "spec_compliance": ["missing" | "extra"] (vuoto se aderente), "findings": [{"severity", "file", "line", "rule", "text"}]}`. Vale solo con lo SHA e il codice del brief di `task review-prepare`. `rule` è la regola violata (`R-…`) o il passo del piano: senza, il rilievo non vale.

**`user_decision`:** `null`, `downgraded:<gravità>` o `dismissed`.

**Verificatore:** `{"sha", "code", "results": [{"id", "verification": "confirmed" | "rejected" | "unverified", "reason"}]}`. Un rilievo senza risultato resta senza esito. `approve finding <id>` usa lo stesso identificativo. C usa `confidence` e `user_decision` per tarare la soglia (R13).

---

## 19. Codici di riferimento

| Codice | Significato |
|---|---|
| R1 | Via d'uscita «test e specifica in conflitto» |
| R2 | Test correlati nel contesto dell'implementatore |
| R3 | La ricevuta non basta: il revisore cerca test indeboliti e casi speciali |
| R4 | Giri di correzione contati e riportati |
| R5 | Promemoria del passo del piano |
| R6 | Controllo della struttura del piano (`plan-check`, 7.5) |
| R7 | Soglie del contesto e ritorni brevi dei subagenti |
| R8, R11, R12 | Regole dei profili via hook; esistenza dei pacchetti; analisi statica (B) |
| R9 | Budget delle istruzioni iniettate (6.3, criterio 19) |
| R10 | Componenti spegnibili |
| R13 | Decisioni dell'utente sui rilievi, per tarare la soglia di confidenza (C) |
| R14 | Non usato nel nucleo (vedi `docs/COSA-TENERE.md`) |
| R15 | Costo dei subagenti (D) |
| R16 | Il revisore Codex dà solo un parere e non modifica il codice: si applica quando Codex entra come revisore, dopo la v1 (1.3) |
| H44 | Prima estendere, poi CLI e skill, solo alla fine nuovi strumenti |

L'elenco completo è in `docs/COSA-TENERE.md`.

---

## 20. Revisioni

| Rev. | Data | Cosa |
|---|---|---|
| 1-4 | 08/10/2026 | Prima stesura; cicli 1-10 |
| 5 | 08/10/2026 | Gate su GitHub come controllo autorevole |
| 6 | 08/10/2026 | Gate diviso in più workflow |
| 7 | 08/10/2026 | Garanzia v1 limitata alle scorciatoie |
| 8 | 08/10/2026 | Audit della spec in L2 |
| 9 | 08/10/2026 | Fasi e transizioni |
| 10 | 08/10/2026 | Riscrittura con i cicli 22-29 e le decisioni dell'utente: fette rinviate a C; specialisti, Codex e controllo delle letture dopo la v1; regole legate al lavoro attivo e non al nome del ramo; implementatore = ogni subagente non in sola lettura; verificatore alimentato dai rilievi registrati; ambiente ripulito; `pending` solo da `verdict`; `interrupted`; ripresa sporca e offline; `adopt`, `sync`, `cleanup`; eccezioni in sola lettura; `OFF` con scadenza; tetto persistente e livello dichiarato nella PR; contratto dei profili; atti con sorgente e autore; registro dei controlli; formati; codici; glossario; identificatori in inglese; dialetto gitignore |
| 11 | 08/10/2026 | Correzioni puntuali dai cicli 31-38: sessioni legate al lavoro; regole di scrittura in `review` e `pr_open`; script dei plugin non sono effetti esterni; `approve spec` richiede anche l'audit a lenti con più fette; modalità `detect` e `tollgate-sentinel` per i repo privati con GitHub Free; `sync` atomico eseguito dalla skill dopo l'atto; `interrupted` solo per sessioni non vive; `allow_no_tests`; `red` con report in errore (`\|\| true`); deroghe per issue; controllo a valle dei commit e dei cambi di ramo; task e giri di correzione dal prompt di `Agent`; `SubagentHandback`; contratto minimo delle fette; `db restore`; ripresa con avvisi; `flaky` tolto; due insiemi di file di verifica; stima dei minuti; modello degli agenti; busta degli eventi; campi del JSON |
| 12 | 08/10/2026 | Correzioni puntuali dai cicli 39-46: permessi di `verdict` (`actions`, `issues`); modalità misurata solo da `init` e scritta in `[gate] mode`; file `spec-approval` e `plan-approval` scritti dalla CLI; `docs/superpowers/reviews/**` protetto; `approve spec <fette>`; atti legati a sessione, lavoro e oggetto, con scadenza; atto `finish`; `approve rebase` monouso; `resolve writer`; `db restore` dal terminale senza atto; `UserPromptExpansion` non blocca mai; push sul predefinito negato in tutto il repo attivo; livello sotto il minimo coerente (`verdict` rosso); componenti spenti → `attenzione`; `pytest.mark.skip` e `skipped` come mancante; issue della PR verificata e deroghe legate al ramo; formato di rilievi e verdetti (18.5); contratto dei profili; registro dei controlli; busta con `repo_key` e `issue`; cache per albero; `tollgate/base` in `detect`; `sentinel` con un'issue sola; tabella di `adopt`; modelli predefiniti degli agenti; `schema_version` di deroghe e report; chiavi sconosciute; criteri 32-35 |
| 13 | 08/10/2026 | Decisione dell'utente: `tollgate:execute` con `tollgate:implementer` e `tollgate:task-reviewer` al posto di subagent-driven-development (tolte esenzione degli script, estrazione del task dal prompt e blocco della revisione finale di SDD; tabella `tasks`; solo `tollgate:implementer` scrive in `execution`). Correzioni dei cicli 47-50: `finish` legato allo SHA e non al tempo; approvazioni legate al contenuto (SHA blob, spec e piano bloccati dopo l'approvazione, `plan_sha` nel gate); `spec_path` della prima fetta; identificativi della base solo eseguiti e non saltati; `tollgate-base` commenta l'issue; `spec-lens-stato.md` rigenerato dall'hook e `outcome` calcolato; `db restore` solo da terminale; uscita al rifiuto del costo dell'audit; registro con eventi d'ingresso e `ctx`; `events --json`; `user_decision`; namespace dei comandi dei profili e `min_level`; casi gravi in `attenzione`; regola comune di versione; criterio 36 |
| 14 | 08/10/2026 | Correzioni dei cicli 51-54: `PreToolUse SendMessage` per le riprese; transizioni di `tasks` e precondizioni di `task start`/`task done`; `task review-prepare` con SHA e codice; task di correzione da rilievi e gate (`--from-findings`, `--from-gate`); `reopen spec|plan` e transizioni in 12.3; piano registrato solo in fase `plan`, in L2 ad `approve plan`; brainstorming fermato prima di writing-plans; spec bloccata da `approve spec`; brief e revisione dal piano a `plan_sha`; `finish` legato a HEAD e non alla sessione; `.tollgate-run/` in `info/exclude`; `events --after-seq` con `seq`; tipi `task_change` e `finding`; `ctx` con tutte le tabelle; `order` e moduli rifiutati; `confidence` nel JSON; criterio 37. Audit chiuso come sospeso |
| 15 | 08/10/2026 | Decisione dell'utente: specializzazione per area. Campi `skills` e `agent` nel contratto dei profili; skill nel brief e controllate da `SubagentStop` tramite `PostToolUse Skill`; in L2 implementatore per area scelto da `task start` quando il task tocca un solo profilo con `agent`; agenti concreti in B; criterio 38 |
| 16 | 08/10/2026 | Decisione dell'utente: profili verticali. Implementatore e revisore del task per area a tutti i livelli (sostituiscono i generici); specialisti finali in L2 solo per i profili con `final_specialist` (sicurezza e database); tetto di 3 skill obbligatorie per agente; campi `reviewer`, `reviewer_skills`, `final_specialist`; catalogo in un documento a parte; criterio 38 riscritto |
| 17 | 08/10/2026 | Decisioni dell'utente: profili `vertical` e `cross` con campo `cross`; precedenza al pattern più specifico; file di tollgate ristretti ai workflow `tollgate-*`, workflow del progetto controllati da `guard` (permessi ed eventi) e coperti dal profilo `ci`; verifica di `skills:` e `mcpServers` negli agenti di plugin |
| 18 | 08/10/2026 | Decisione dell'utente, da `docs/RICERCA-ORGANIZZAZIONE.md`: dimensione e budget del task (`[tasks]`), report dell'implementatore a campi fissi, standard del revisore e disaccordo istruito con regola citata, Definition of Done per livello (8.7, campo `dod` dei profili e del JSON), spec L2 con «Tane di coniglio» e «Cosa non fare»; criteri 39-41; ogni pratica è un componente spegnibile in `[components]`, e `status` indica quale tetto ha fermato il lavoro |
| 19 | 08/10/2026 | Decisione dell'utente dopo l'analisi dei problemi d'uso: must-have legati ai test (7.5, 8.7, componente `must_have_tests`); `tollgate stats` dagli eventi (3.1); voci di `attenzione` divise in «da leggere» e «informative», con lo stato rosso solo per le prime (9.2); criteri 42-44 |
| 20 | 08/10/2026 | Esiti delle verifiche P0 (`docs/verifiche/2026-10-08-p0-esiti.md`). Conseguenze K1-K12 approvate dall'utente; le aggiunte emerse applicandole (nome `-r<giro>`, implementatori in primo piano senza `run_in_background`, `app_id` letto al lancio del comando, `EnterWorktree` in 6.1, prefisso `v` in P2) e le correzioni della revisione finale del ramo (token letti a `SubagentStop`, riga del subagente chiusa al taglio, riconoscimento del taglio dal blocco dell'harness, `handbackReport`, `SendMessage` dalla sessione principale, riga Dependabot di 13) sono state elencate all'utente prima del merge. Contenuto: implementatori lanciati con un nome fisso e ripresi per nome, tabella nome → `agent_id` (`subagents.name`); `PostToolUse Agent` per il taglio di `maxTurns`; token dal transcript a `SubagentStop`; `SubagentHandback` fonte primaria in auto mode; subagenti interni ignorati; atti da `command_name`; comandi `!` tra i limiti di 1.2; forma JUnit degli identificativi per strumento e configurazione di jest-junit in `init`; modalità riconosciuta da codice e messaggio della GET di protezione (404 «Branch not protected» → `protected`); sorgente fissata con `app_id` letto dal check-run di `tollgate-base`; ingresso nel worktree con `EnterWorktree`, con il ripiego «cd && claude»; PR di Dependabot in 9.1; `mcpServers` ignorato; sezione 16 aggiornata; riga Dependabot di 13; criteri 4, 10, 11, 39 e 42 |
| 21 | 09/10/2026 | Esiti delle verifiche P2 (`docs/verifiche/2026-10-09-p2-verifiche.md`): taglio di `maxTurns` in background e alla ripresa riconosciuto da `UserPromptSubmit` con `<task-notification>`; tag delle `dependencies` nella forma `<plugin>--v<versione>`, quindi nessun `version` per Superpowers; `additionalContext` per evento; eventi d'ingresso `post_agent`, `post_skill` e `prompt_submit`; `record <operazione>` come operazione di un elenco chiuso; decisioni del piano P2 riportate 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15 e 22; sezioni toccate: 3.2 (pattern di percorsi e di comandi, `Ctx.approved_waivers` come API per P3), 6.2 (blocco di spec e piano solo dopo l'approvazione), 6.3 (taglio riconosciuto per prompt che comincia con `<task-notification>`, blocco per blocco; riga sempre `cut`), 6.6 (sessione legata negata in un altro lavoro; file protetti per ogni radice), 7.1 (classificazione degli hook, Python mancante, scadenza con `signal.alarm` e cane da guardia, `OFF` con `off.log`, segnalino `bound/`, messaggi su stdout), 7.4 (rimozioni che toccano file protetti; `core.hooksPath` negato), 8.1 (report configurato e assente → `red`; gate completo come la DoD; veti azzerati alla ripresa; stato non riconosciuto → report non valido), 8.2 (salti e asserzioni sul testo grezzo; soglie abbassate anche se commentate), 8.3 (deroghe in locale anche se in attesa), 8.4 (oggetto e target degli atti; `approve waiver` in ogni stato), 8.5 (consumo a `PostToolUse Bash`, MCP a `PreToolUse`), 11.1, 11.3 (forma del file del contesto), 12.2 (migrazione 2), 16, 18.2 (`file` relativo, `--test`, identificativi completi), 18.5 (status fuori dai quattro valori), 20; sezione 16 aggiornata |
