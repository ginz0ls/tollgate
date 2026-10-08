# tollgate: specifica del nucleo (sotto-progetto A)

Data: 8 ottobre 2026.
Revisione: **8**. Il controllo autorevole è su GitHub (decisione dell'utente, 08/10/2026); la sezione 18 elenca le revisioni.
Stato: **in audit** (`docs/audit/2026-10-08-audit-spec-nucleo-stato.md`).
Fonti: `docs/REPORT-CONFRONTO-WORKFLOW.md`, `docs/COSA-TENERE.md` (voci 1-42, H1-H45, R1-R16, sezioni 9 e 10), `docs/RICERCA-PAPER.md`.

---

## 0. Glossario

| Termine | Significato |
|---|---|
| **lavoro** | Un'issue, oppure una fetta di un'issue. È una riga della tabella `work_items` |
| **fetta** | Una parte di un'issue troppo grande per una sola PR, elencata nel piano principale |
| **task del piano** | Un task di un piano di Superpowers (`### Task N`), eseguito da un implementatore |
| **base del lavoro** | Lo SHA da cui parte il ramo del lavoro (`work_base_sha`). Si può riallineare solo con un atto dell'utente |
| **base del subagente** | Lo SHA di quando un subagente è partito o ripreso (`agent_base_sha`) |
| **scope** | I file che il piano della fetta autorizza a creare o modificare. Le deroghe si contano a parte |
| **ricevuta** | Il risultato registrato di un comando di verifica su uno SHA |
| **deroga** | Un'eccezione dichiarata dall'agente su un file preciso, con motivo e costo (8.3) |
| **blocco** | Un arresto del lavoro con un tipo e un motivo, che chiude solo l'utente (8.3) |
| **chiave del repo** | URL remoto `origin` normalizzato |
| **repo attivo** | Un repo che ha `tollgate.toml` sulla punta del ramo predefinito di `origin`. **Negli altri repo tollgate non fa niente** |
| **cartella di stato** | `~/.local/state/tollgate`. Contiene DB, log, file del contesto e interruttore |
| **atto dell'utente** | Un'operazione registrata dall'hook `UserPromptExpansion` quando l'utente digita un comando `/tollgate:*` |
| **gate** | Il controllo che decide se una PR è pronta. Gira **su GitHub** (sezione 9); in locale ne gira una copia solo per dare un riscontro rapido |
| **verdetto del gate** | Lo stato `tollgate/verdict` pubblicato sul commit della PR da un workflow fidato (9.1) |
| **file di tollgate** | `tollgate.toml`, `.github/workflows/**`, `.github/actions/**`, `.github/tollgate/**` |

---

## 1. Scopo e modello di fiducia

tollgate è un plugin per Claude Code. Porta un lavoro **da un'issue GitHub a una PR verificata**; il merge lo fa sempre una persona, su GitHub.

Il flusso di lavoro resta quello di **Superpowers**: brainstorming → writing-plans → subagent-driven-development. tollgate aggiunge quello che manca e **sostituisce un unico passo**, la chiusura del ramo (`finishing-a-development-branch`), con `/tollgate:finish` (6.3).

### 1.1 Due livelli, con ruoli diversi

| Livello | Dove gira | A cosa serve | Cosa garantisce |
|---|---|---|---|
| **Guardrail locali** | Hook di Claude Code sulla macchina dell'utente | Fermare **subito** le scorciatoie e gli errori onesti del modello: test modificati, «fatto» senza prove, file fuori scope, effetti esterni non confermati, scrittura di codice dal coordinatore | **Nessuna garanzia contro un agente che lavora per aggirarli.** Un agente con Bash sulla stessa macchina può alterare DB, configurazione e processi locali (verificato dalla seconda revisione avversariale) |
| **Gate su GitHub** | Tre workflow più `tollgate-base` (9.1): `guard` e `verdict` usano la definizione del ramo predefinito e non eseguono codice della PR; `run` esegue il codice della PR senza permessi di scrittura. Più la protezione del ramo | Ricalcolare **da zero** i fatti della PR: comandi del gate, identificativi dei test della base, test-guard, coerenza dello scope, file di tollgate invariati | Una PR non entra nel ramo predefinito senza `guard` e `verdict` verdi e senza il merge dell'utente |

**Perché due livelli.** I guardrail evitano di arrivare alla PR con problemi che si potevano fermare subito, e la ricerca mostra che il comportamento più frequente è la scorciatoia, non l'attacco. Il gate dà la garanzia, perché gira dove l'agente non ha potere.

### 1.2 Cosa resta fuori dalla garanzia (dichiarato)

- **L'agente che usa le credenziali GitHub dell'utente** per agire al suo posto, per esempio facendo il merge o cambiando la protezione del ramo. I guardrail lo negano («best effort»). La mitigazione consigliata è dare all'agente un token separato con permessi ridotti (sezione 11).
- **Effetti esterni**: deploy, scritture su database e chiamate di rete hanno **un solo livello**, il guardrail locale. Quando arriva la PR l'effetto è già avvenuto.
- **Asserzioni rese più deboli senza cambiare il numero dei test** (per esempio `toBe(3)` che diventa `toBeTruthy()`): le cerca il revisore finale (R3), non il gate.
- **La qualità del giudizio dei revisori**: si può verificare che abbiano letto il materiale (8.6), non che abbiano giudicato bene.
- **Il codice della PR che, eseguito dai test, ne falsifica l'esito** (per esempio riscrivendo il report JUnit): il gate lo esegue, perché deve, in un job senza permessi. Il codice resta visibile nel diff.
- **Lo scope e le deroghe sono dichiarati dall'agente.** Il gate verifica che il diff sia **coerente** con piano e deroghe e li mostra; non può sapere se tu li avresti approvati. Gli atti locali (approvazioni) non sono verificabili da GitHub.
- **Il conteggio delle asserzioni si può compensare** aggiungendo asserzioni banali.
- **Una serie di PR L0** evita piano e revisione, una PR alla volta.
- **Il sabotaggio deliberato della CI.** Comprende i workflow aggiunti nella PR per pubblicare stati `tollgate/*` falsi o per chiedere permessi di scrittura. Qualunque workflow del repo pubblica come «GitHub Actions», quindi nella v1 la sorgente fissata non basta a escluderlo. Lo rendono visibile:
  - la protezione locale di `.github/workflows/**`;
  - il diff;
  - `guard`.

  La **modalità rinforzata**, con stati pubblicati solo da una GitHub App la cui chiave sta in un environment riservato al ramo predefinito, viene dopo la v1 (decisione dell'utente, 08/10/2026).

### 1.3 Fuori dal nucleo

| Cosa | Dove |
|---|---|
| Profili per tipo di file con i loro controlli; caricamento delle regole tramite hook (R8); controllo dell'esistenza dei pacchetti (R11); analisi statica nel profilo sicurezza (R12) | Sotto-progetto **B** |
| Sotto-issue e dipendenze su GitHub Projects, riconciliazione automatica, registrazione delle tue decisioni sui rilievi (R13) | Sotto-progetto **C** |
| Suite di eval completa con confronti e prove a componenti spenti, costo dei subagenti (R15), misura del contesto dei subagenti | Sotto-progetto **D** |
| Dashboard locale, avvio automatico da etichetta GitHub, portabilità verso altri harness, lezioni apprese, mutation testing, **modalità rinforzata del gate con GitHub App** | Dopo la v1 |

**Agganci già pronti per i sotto-progetti successivi.**
- Nel DB: la colonna `decisione_utente` e le tabelle `slices` ed `events`.
- In `tollgate.toml`: le sezioni `[profiles]` e `[components]`, quest'ultima come mappa aperta.
- Nella PR: un blocco JSON leggibile dalle macchine.
- Per i test: la variabile `TOLLGATE_STATE`.

---

## 2. Decisioni prese

| Tema | Decisione |
|---|---|
| Harness | Claude Code |
| Tracker | GitHub Issues, tramite `gh` |
| Autonomia | Interattiva. L'avvio automatico viene dopo |
| Flusso | Superpowers, dichiarato come dipendenza (11.1). `finishing-a-development-branch` è sostituito da `/tollgate:finish` |
| Struttura | Hook, script e una GitHub Action. Le skill gestiscono le parti che richiedono il modello; i passi deterministici li esegue `bin/tollgate` |
| Controllo autorevole | **Su GitHub** (sezione 9). I controlli locali sono guardrail |
| Stato locale | SQLite nella cartella di stato. Ci scrive solo il codice di tollgate |
| Pianificatore | Il coordinatore, cioè la sessione principale, che può fare domande |
| Revisione | Revisore finale e verificatore scritti da tollgate; in L2 specialisti esterni, se installati (sezione 10) |
| Merge | Solo l'utente, su GitHub |
| Livello | Lo script lo può solo alzare. Lo abbassa solo l'utente, con un atto e un motivo |
| Effetti esterni | Negati finché l'utente non li approva con un atto (8.5). Così funziona in ogni modalità di permesso, anche in `dontAsk`, dove le richieste di conferma vengono negate da sole |
| Pubblicazione | Privato ora, pubblico poi. Nel codice niente percorsi né nomi di progetti dell'utente |
| Lingua | Nomi in inglese per plugin, comandi, script e file; documentazione in italiano |
| Sistemi | Linux e macOS, Python ≥ 3.11 (per `tomllib`). Windows fuori dalla v1 |
| Requisiti del repo | Remote GitHub, `gh` autenticato, GitHub Actions attive, protezione del ramo predefinito (`/tollgate:init` la propone) |
| Repo senza test | Ammesso solo con `allow_no_tests = true` in `tollgate.toml`, mostrato nel riepilogo |

---

## 3. Struttura del plugin

```
tollgate/
  .claude-plugin/plugin.json        dependencies: superpowers
  .claude-plugin/marketplace.json   allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]
  skills/
    start/SKILL.md      /tollgate:start #N [L1|L2]                     anche il modello
    finish/SKILL.md     /tollgate:finish                               anche il modello
    status/SKILL.md     /tollgate:status   stato e atti in sospeso     anche il modello (sola lettura)
    init/SKILL.md       /tollgate:init     propone configurazione e gate  anche il modello (solo proposta)
    approve/SKILL.md    /tollgate:approve <oggetto> <id> [motivo]      solo l'utente
    resolve/SKILL.md    /tollgate:resolve <id> <nota>                  solo l'utente
    abandon/SKILL.md    /tollgate:abandon <lavoro>                     solo l'utente
    setup/SKILL.md      /tollgate:setup    configura la statusline     solo l'utente
    off/ on/            /tollgate:off, /tollgate:on                    solo l'utente
  agents/
    final-reviewer.md     revisore finale            tools: Read, Grep, Glob, Bash
    finding-verifier.md   verificatore               tools: Read, Grep, Glob, Bash
    plan-adversary.md     avversario del piano (L2)  tools: Read, Grep, Glob
    spec-adversary.md     avversario della spec (L2) tools: Read, Grep, Glob, WebFetch
    spec-auditor.md       audit a lenti della spec   tools: Read, Grep, Glob, WebFetch
    specialist-runner.md  esegue uno specialista che è una skill   tools: Read, Grep, Glob, Bash, Skill
  skills/spec-audit/    metodo dell'audit a lenti (versione di prd-audit incorporata, con l'accordo dell'autore)
  hooks/hooks.json      tutti gli hook (gli agenti dei plugin non possono averne)
  hooks/run             wrapper shell degli hook (7.1)
  bin/tollgate          CLI Python, solo libreria standard
  gate/                 workflow e copia del CLI che /tollgate:init propone di installare nel repo (sezione 9)
  statusline/statusline.sh
  templates/tollgate.toml
  tests/  evals/
```

«Solo l'utente» vuol dire `disable-model-invocation: true`, che impedisce al modello di invocarle (verificato), più la registrazione tramite `UserPromptExpansion` (7.2).

### 3.1 Sottocomandi di `bin/tollgate`

| Sottocomando | Chi lo chiama | Cosa fa |
|---|---|---|
| `start <N> [--level L1\|L2] [--slice K]` | La skill `start`, via Bash | Crea o riprende il lavoro (6.1) |
| `verify` | L'agente | Esegue `test_related` e scrive una ricevuta locale |
| `waiver add`, `block open` | L'agente | Deroghe e blocchi (8.3) |
| `review prepare`, `finish check`, `finish open-pr [--update]` | La skill `finish` | 6.3. `--update` aggiorna la PR esistente con un push normale, oppure con `--force-with-lease` solo dopo un `approve rebase` |
| `status`, `init --propose` | L'agente | Sola lettura, proposta di configurazione |
| `gate run`, `gate evaluate`, `gate guard`, `gate base-ids` | La copia locale (`finish check`) e i workflow (9.1) | Il gate. **Stesso codice nei due posti** |
| `hook <evento>` | Solo `hooks/run` | Gli hook. L'hook Bash nega le chiamate dirette dell'agente |

Atti dell'utente, fasi, ricevute e verdetti non hanno un sottocomando: li scrivono gli hook e le funzioni interne.

**Limite dichiarato.** Un agente può comunque importare il modulo Python o usare `TOLLGATE_STATE`. Riguarda solo i guardrail locali, perché il gate su GitHub non legge niente di locale (1.1).

### 3.2 Principi di design

- **Configurazione.**
  - **Sui rami `tg/*`**: `tollgate.toml` si legge dalla base del lavoro (`git show`).
  - **Altrove**: si legge dalla punta del ramo predefinito di `origin`.
  - **Mai** dal working tree.
- **Hook uniformi.** Ogni hook passa da `hooks/run`.
- **Componenti spegnibili.** Ogni componente si spegne da `[components]` (R10).
- **Ordine di preferenza.** Prima si estende quello che esiste, poi CLI e skill, solo alla fine nuovi strumenti (H44).

---

## 4. Ruoli

| Ruolo | Chi è | Cosa fa | Come è imposto |
|---|---|---|---|
| Utente | — | Sceglie se alzare il livello, approva spec e piano in L2, approva gli atti, risolve i blocchi, fa il merge | Atti registrati da `UserPromptExpansion`; merge su GitHub |
| Coordinatore | La sessione principale | Dialogo, brainstorming, spec, **piano**. Lancia i subagenti e legge solo verdetti e percorsi. **Non scrive codice**, tranne in L0 | In L1 e L2, fase `esecuzione`: Edit e Write sul codice negati senza `agent_id`. `agent_id` manca nella sessione principale ed è presente nei subagenti (verificato). Le scritture via Bash sono negate «best effort» (7.4) |
| Implementatore | Subagente di Superpowers, uno per task del piano | Scrive il codice di **un** task e fa il commit; **uno alla volta** | Scope, un solo scrittore, regola di `SubagentStop` |
| Revisore del task | Subagente di Superpowers | Controlla il task rispetto al piano | Se fa commit, valgono le regole dell'implementatore |
| Avversario della spec | `tollgate:spec-adversary`, solo L2 | Attacca la spec a contesto pulito, senza le motivazioni dell'autore, e verifica i fatti alla fonte. Il report è il messaggio finale, salvato dall'hook | Senza strumenti di scrittura né Bash |
| Auditor della spec | `tollgate:spec-auditor`, solo quando c'è un piano principale | Audit a lenti e punti di vista (metodo `spec-audit`), fino a due cicli vuoti per punto di vista, con un tetto | Come sopra |
| Avversario del piano | `tollgate:plan-adversary`, solo L2 | Attacca il piano; riceve piano e spec senza le motivazioni dell'autore. Il suo report è il messaggio finale, che l'hook salva su file | Senza strumenti di scrittura né Bash |
| Revisore finale | `tollgate:final-reviewer` | Rivede la fetta rispetto a piano, must-have e scope; cerca casi speciali scritti per i test e asserzioni indebolite (R3) | Brief generato dallo script e controllo delle letture (8.6); controllo di sola lettura (7.3) |
| Verificatore | `tollgate:finding-verifier` | Conferma ogni rilievo con prove (file, riga, motivo) oppure lo scarta | Come il revisore finale |

**Come si passa il lavoro.** Ogni subagente riceve un **brief su file** e restituisce un **report su file**, oppure un messaggio finale che l'hook salva. Al coordinatore torna al massimo un verdetto di 1-2K token più il percorso (R7).

---

## 5. Livelli

| Livello | Quando | Percorso |
|---|---|---|
| **L0** | Al massimo `l0_max_files` file (predefinito 2), `l0_max_lines` righe aggiunte più rimosse (predefinito 50) e `l0_max_bytes` byte (predefinito 4.000) nel diff dalla base del lavoro, senza percorsi sensibili né file binari | Implementazione diretta nella sessione, `verify`, `finish`. Niente brainstorming né piano |
| **L1** | Il caso normale | writing-plans → controllo della struttura del piano → esecuzione per task del piano → revisione finale |
| **L2** | Percorsi sensibili, etichette sensibili, issue di un autore che non collabora al repo, oppure tua scelta | brainstorming → spec → piano principale se serve più di una fetta → piano della fetta → avversario → tua approvazione → esecuzione → revisione finale con specialisti |

**Come si stima e come cambia.**
- **All'avvio** lo script calcola il livello minimo. Tu lo puoi alzare scrivendo `/tollgate:start #N L2`, e il comando digitato è registrato come atto. Il modello non lo può abbassare.
- **Durante il lavoro** si ricalcola sul diff dopo ogni Edit o Write (`PostToolUse`), a ogni `git commit` e a `finish`:
  - superate le soglie di L0 → il livello sale a L1 e la fase torna `piano`. Il codice resta bloccato finché un piano non è registrato, mentre i `.md` sotto `docs/superpowers/` restano scrivibili;
  - toccato un percorso sensibile → il livello sale a L2.
- **Abbassarlo**: solo tu, con `/tollgate:approve level <L> <motivo>`. L'atto finisce nella PR.
- **Il gate su GitHub** ricalcola il livello sul diff della PR e lo scrive nel riepilogo.

**Piano principale** (si crea solo se il lavoro non sta in una fetta):
- `plan-check` lo riconosce dall'intestazione `# Piano principale` e registra le fette in `slices`;
- ogni fetta è un lavoro a sé, con il suo piano scritto quando arriva il suo turno e la sua PR con «Part of #N»;
- `start #N` sceglie la fetta con il numero più basso tra quelle non chiuse le cui dipendenze sono chiuse;
- nel nucleo le fette restano sulla stessa issue.

---

## 6. Ciclo di vita

### 6.1 Avvio e piano

```
/tollgate:start #N [L1|L2]   (la skill chiama bin/tollgate start)
  0. prerequisiti   repo attivo; Python ≥ 3.11; Superpowers nell'intervallo atteso; remote GitHub,
                    gh autenticato, ramo predefinito con almeno un commit; gate installato
                    (workflow presente sul ramo predefinito). Se manca qualcosa: rifiuto con il motivo
                    e, per configurazione e gate, l'invito a /tollgate:init
  1. controlli      repo pulito; CI del ramo predefinito verde (se è rossa: avviso e conferma);
                    issue chiusa → avviso e conferma
  2. lavoro         lavoro esistente per (chiave del repo, issue, fetta)? → ripresa (12.3); altrimenti nuovo
  3. livello        minimo calcolato dallo script; L1 o L2 se digitati da te
  4. worktree       ramo tg/<N>-<slug>, slug ripulito ([a-z0-9-], al massimo 40 caratteri);
                    riga in work_items (fase = piano, work_base_sha)
  5. entrata        start stampa il comando per aprire Claude Code nel worktree (cd <percorso> && claude)
                    e chiude la sessione 1 qui: il piano si scrive già nel worktree. Se lo strumento
                    nativo EnterWorktree accetta il percorso, la skill lo usa al posto della riapertura (16)
  6. per livello    L0: implementa → tollgate verify → /tollgate:finish
                    L1: writing-plans (con l'elenco delle sezioni obbligatorie) → plan-check → scope
                        registrato → fase = esecuzione
                    L2: brainstorming → spec → AUDIT DELLA SPEC (6.1.1) → /tollgate:approve spec
                        → checkpoint + /clear → piano principale (se serve) e piano della fetta → plan-check
                        → plan-adversary → /tollgate:approve plan → fase = esecuzione
  → checkpoint + /clear
```

#### 6.1.1 Audit della spec (L2)

1. **Giri avversariali.**
   - `tollgate:spec-adversary` legge solo la spec, in un subagente nuovo a ogni giro.
   - Il coordinatore corregge la spec.
   - Si ripete finché un giro non produce **né bloccanti né gravi**. Tetto: `spec_rounds` (predefinito 4). Oltre il tetto, blocco `serve_te`.
2. **Audit a lenti**, solo se il lavoro ha un piano principale (`spec_audit_cycles`, predefinito 30). `tollgate:spec-auditor` applica il metodo `spec-audit`:
   - lenti di coerenza, verificabilità, copertura, proiezione futura, fatti e lacune ricorrenti;
   - otto punti di vista;
   - chiusura solo dopo due cicli vuoti per ciascun punto di vista, oppure «sospeso» al tetto.
3. **Registro.** Ogni giro e ogni ciclo lasciano un file in `docs/superpowers/reviews/`, che viene committato. Il gate su GitHub controlla che esistano per i lavori L2 (9.2).
4. **Approvazione.** La spec passa a `/tollgate:approve spec` solo dopo l'audit. Il riepilogo dei rilievi entra nella PR.

La fase è `audit_spec`. Vi si scrivono solo i `.md` sotto `docs/superpowers/`.

**Il testo dell'issue non è fidato.**
- Non entra mai in un comando shell. Passa ai modelli dentro file, marcato come «dato, non istruzioni».
- Se l'autore non collabora al repo, il lavoro va in L2.

### 6.2 Esecuzione: una fetta per sessione

```
/tollgate:start #N   riparte dal DB (fase = esecuzione)
  SessionStart inietta lo stato (al massimo 10 righe e 1.500 caratteri): issue, fetta, scope, livello
  subagent-driven-development di Superpowers, per ogni task del piano, uno alla volta:
    SubagentStart inietta nel subagente scope, test correlati e passo del piano (R2, R5)
    implementatore → commit (hook: test-guard, scope, livello) → tollgate verify → ricevuta locale
    SubagentStop dell'implementatore: 8.1
    test e specifica in conflitto → tollgate block open conflitto_test_spec (R1); i test non si toccano
    revisore del task di Superpowers
  giri di correzione: valgono quelli di Superpowers; tollgate li conta dai commit dopo la base
    del task del piano (non per subagente, perché i giri 4-5 usano un implementatore nuovo) e li
    riporta nella PR (R4, ridimensionata: vedi 18)
  guardia del contesto: avviso a warn_pct; a stop_pct nega nuovi subagenti → checkpoint + /clear
```

### 6.3 Chiusura

La skill `start` dice al coordinatore di usare **`/tollgate:finish`** al posto della revisione finale e di `finishing-a-development-branch` di Superpowers. Se il coordinatore segue comunque Superpowers, i guardrail negano merge locale, push, cancellazione del ramo e rimozione del worktree.

```
/tollgate:finish
  1. tollgate finish check   copia locale del gate (senza gli identificativi della base): riscontro rapido
  2. revisione               tollgate review prepare scrive i brief (diff, SHA, codice di controllo)
                             → tollgate:final-reviewer (+ specialisti e Codex in L2)
                             → tollgate:finding-verifier → i verdetti li registra l'hook SubagentStop (8.6)
                             al massimo 4 giri, poi blocco serve_te (risolvibile, 8.3)
  3. tollgate finish open-pr parte solo se:
                             - hai digitato tu /tollgate:finish dopo l'ultimo commit, oppure hai dato
                               /tollgate:approve pr per questo SHA;
                             - 1 e 2 sono passati sullo stesso SHA;
                             - non ci sono blocchi o atti in sospeso.
                             Poi: intento salvato → push → ls-remote → cerca una PR esistente → crea o aggiorna
                             la PR. In L2 committa anche il report dell'avversario in docs/superpowers/reviews/.
                             Descrizione: livello (ed eventuale abbassamento), ricevute locali, deroghe,
                             blocchi, verdetto, giri di correzione, effetti esterni approvati, periodi con
                             tollgate spento; in coda un blocco JSON in un commento HTML
  4. gate su GitHub          i workflow ricalcolano tutto (sezione 9); fase = pr_aperta
  5. merge                   lo fa l'utente su GitHub, con guard e verdict verdi
```

**Dopo l'apertura della PR.**
- Se il verdetto è rosso, oppure vuoi altre modifiche, `start #N` riporta il lavoro in `esecuzione`.
- Il successivo `/tollgate:finish` aggiorna la stessa PR con `open-pr --update`.
- Il push forzato è permesso solo a `open-pr --update`, dopo un `approve rebase`.

### 6.4 Dove valgono le regole

- **Repo non attivo**: tollgate non fa niente.
- **Repo attivo, fuori dai rami `tg/*`**: valgono solo i comandi distruttivi e la protezione dei file di tollgate (7.4).
- **Rami `tg/*`**: tutte le regole.
- **Come si determina il ramo**:
  - per gli strumenti di file, dal **repository del file** toccato (`file_path`);
  - per Bash, dalla directory effettiva del comando, compresi `cd` e `git -C`.
- **Worktree**:
  - `git worktree add` per un lavoro che ha già un worktree viene negato;
  - nei lavori attivi è negata la creazione di worktree da parte dei subagenti (`isolation: worktree` parte dal ramo predefinito, verificato). Si intercetta con l'evento `WorktreeCreate`, perché l'input di `Agent` non espone il campo `isolation` (verificato).

---

## 7. Hook (guardrail locali)

### 7.1 Come girano

Tutti gli hook stanno in `hooks/hooks.json`, sono di tipo `command` e passano dal wrapper `hooks/run`.

**Il problema.** Solo l'uscita 2 blocca. Con uscita 1, crash o timeout l'azione prosegue (verificato su hooks.md, 08/10/2026).

**Cosa fa il wrapper:**
1. Gestisce **prima di tutto** i comandi `/tollgate:on` e `/tollgate:off`: crea o cancella il file `OFF` nella cartella di stato, senza Python e senza DB.
2. Se esiste il file `OFF`, esce con 0 e registra in un file di testo nella cartella di stato che un hook è stato saltato. La PR riporta i periodi in cui tollgate era spento.
3. Se Python manca o è più vecchio del 3.11, esce con 2 e spiega il motivo, indicando `/tollgate:off`.
4. Esegue `bin/tollgate hook <evento>` con una scadenza interna (predefinito 20 s, sotto il `timeout` di `hooks.json`).
5. **Hook di controllo**: qualunque esito diverso da 0 o 2 diventa uscita 2, con il percorso del log e l'indicazione di `/tollgate:off`.
6. **Hook informativi e `SubagentStop`**: un errore diventa uscita 0 più un avviso. Per `SubagentStop` serve a non tenere in vita un subagente all'infinito quando il DB è rotto.

### 7.2 Tabella

| Evento | Filtro | Comportamento |
|---|---|---|
| `SessionStart` | `startup`, `resume`, `clear`, `compact`, `fork` | Informativo. Con un lavoro attivo inietta lo stato (al massimo 10 righe e 1.500 caratteri, R9) |
| `UserPromptExpansion` | comandi `tollgate:*` nella forma lunga e in quella breve | Registra l'**atto dell'utente**: approvazioni, risoluzioni, livello, abbandono, `finish`, statusline |
| `PreToolUse` | `Edit`, `Write`, `NotebookEdit` (`MultiEdit` se presente) | **Fasi `piano` e `approvazione`**: solo i `.md` sotto `docs/superpowers/`. **Fase `bloccato`**: come `piano`. **Fase `esecuzione`**: fuori scope → `deny` con l'istruzione per la deroga; codice scritto dalla sessione principale in L1 e L2 → `deny`. **File protetti** (7.4) → sempre `deny`. **Sempre permessi**: i `.md` sotto `docs/superpowers/` e i file sotto `.superpowers/` (ignorati da git). `.tollgate/waivers.toml` è negato a Edit e Write: lo scrive solo `tollgate waiver add`. **In L0** lo scope non si applica: vale il livello |
| `PostToolUse` | `Edit`, `Write`, `MultiEdit` | Ricalcola il livello. Se il file è un piano, esegue `plan-check` (7.5) |
| `PostToolUse` | `Bash` con `git commit` | Registra il commit creato (SHA prima e dopo) |
| `PreToolUse` | `Bash` | 7.4 |
| `PreToolUse` | `mcp__.*` | Strumenti non elencati in `[external_effects] mcp_allow` → trattati come effetto esterno (8.5) |
| `PreToolUse` | `Agent` | `context-guard`: a `stop_pct` → `deny`. **Un solo scrittore**: un nuovo `general-purpose` viene negato se un altro è attivo nel worktree; quelli in `[review] parallel_ok` e i `tollgate:*` possono lavorare in parallelo |
| `WorktreeCreate` | tutti | In un lavoro attivo → errore (blocca la creazione), con il percorso del worktree del lavoro |
| `SubagentStart` | tutti | Salva `agent_base_sha` (senza sovrascriverla se è una ripresa), l'impronta dei file tracciati e il tipo. Per gli implementatori inietta scope, test correlati e passo del piano. Conta le riprese per misurare i giri di correzione |
| `SubagentStop` | tutti | Implementatori: 8.1. Sola lettura: 7.3. Revisori e verificatore di tollgate: 8.6. Avversario: salva il report |

**`Stop` della sessione principale: nessun blocco.** Il gate è su GitHub.

### 7.3 Controllo di sola lettura

Vale per `tollgate:*`, per gli specialisti e per i subagenti in `[review] parallel_ok`.
- `SubagentStop` confronta i **file tracciati non ignorati**, escluse le cartelle di output dichiarate (`[review] output_dirs`, che contengono per esempio il report dei test), con l'impronta presa alla partenza.
- Se sono cambiati, il verdetto non vale e si apre un blocco `serve_te`.

### 7.4 Regole su Bash e file protetti

Valgono nei repo attivi, con l'ambito della sezione 6.4. Sono «best effort».

**File protetti**, negati a Edit e Write e alle scritture via Bash:
- `tollgate.toml`;
- `.github/workflows/**`, `.github/actions/**` e `.github/tollgate/**`;
- `.tollgate/waivers.toml` (solo tramite `tollgate waiver add`);
- `.claude/settings*.json` e `~/.claude/settings*.json`;
- `.claude/agents/**` e `.claude/hooks/**`;
- `.git/hooks/**` e `.git/config`;
- la cartella di stato;
- la cartella del plugin installato.

| Comando | Decisione |
|---|---|
| Su un ramo `tg/*`: `git push`, `gh pr create` | `deny` (push e PR li fa `tollgate finish open-pr`) |
| Ovunque nei repo attivi: `gh pr merge`, `gh api` con metodo diverso da GET | `deny` (effetto esterno, 8.5) |
| Ovunque: `git merge` di un ramo `tg/*` verso il ramo predefinito, `git branch -d/-D` di un ramo `tg/*`, `git worktree remove` del worktree di un lavoro, `git worktree add` per un lavoro che ha già un worktree | `deny` |
| Distruttivi: `push --force`, `reset --hard`, `--no-verify`, `rm -rf` fuori dal worktree | `deny` |
| Che alterano tollgate o la configurazione di Claude Code: `claude` e i suoi alias (anche `npx @anthropic-ai/claude-code`), `TOLLGATE_` nel comando, scrittura sui file protetti con qualunque mezzo riconoscibile (`sed -i`, `>`, `>>`, `tee`, `cp`, `mv`, `ln`, `install`, `touch`, `dd`, `sqlite3`, `python`, `node` con il percorso del file) | `deny` |
| `tollgate hook …` | `deny` |
| Scrittura di file di codice dalla sessione principale (L1 e L2, fase `esecuzione`), con redirect o `sed -i` | `deny` |
| Effetti esterni (8.5) | `deny` finché non c'è un atto |
| `git commit` (con o senza `-a`, anche dopo `git add` nella stessa riga) | test-guard, scope e livello sul **working tree più l'indice** rispetto alla base del lavoro; `deny` se mancano deroghe. Esenti dallo scope: `docs/superpowers/{specs,plans,reviews}/**/*.md`, `.tollgate/waivers.toml` e i lockfile il cui manifest è nello scope |

### 7.5 Controllo del piano (`plan-check`)

**Sezioni obbligatorie:**
- Fatti verificati (fatto / dove / conseguenza, su uno SHA);
- Decisioni (scelta / perché / costo se sbagliata);
- Interfacce;
- Must-have;
- Scope, ricavato da `Create:`, `Modify:` e `Test:` di ogni task;
- Punti di arresto;
- Rischi.

Il piano principale ha in più l'elenco delle fette con le dipendenze.

**Regole sullo scope:**
- ammessi solo **percorsi di file**: niente glob e niente cartelle; gli intervalli di righe si tolgono;
- al massimo `max_scope_files` file (predefinito 30);
- **una volta registrato, lo scope non cresce più modificando il piano**: ogni file in più richiede una deroga `scope`;
- il gate su GitHub riporta lo scope iniziale, quello finale e le modifiche al piano fatte dopo il primo commit di codice.

**Esito:**
- piano incompleto → `decision: block` con l'elenco di quello che manca. Il file resta scritto, ma il piano non viene registrato;
- la skill `start` dà al coordinatore l'elenco delle sezioni prima di writing-plans.

---

## 8. Ricevute, test-guard, deroghe, effetti esterni, revisori

### 8.1 Ricevute locali (guardrail)

- **Chi le produce**: solo `tollgate verify` e `finish check`.
- **Cosa registrano**:
  - SHA, comando risolto e codice d'uscita;
  - numero di test eseguiti e saltati, letto dal reporter (`[commands] report`);
  - durata e percorso del log.
- **Quando una ricevuta è verde**: codice d'uscita 0 e almeno un test eseguito. Con zero test è «vuota»; senza reporter è «senza conteggio».
- **Nessun test collegato**: se `test_related` non trova test per i file del diff, `verify` esegue i comandi del gate completi. La ricevuta «vuota» resta solo per i repo senza test, ammessi con `allow_no_tests`.
- **Worktree pulito**: si controlla prima di eseguire, sui file tracciati e su quelli non tracciati non ignorati.
- **Test instabili**: un solo nuovo tentativo; se il secondo passa, la ricevuta è segnata «instabile».

**Regola di `SubagentStop` per gli implementatori** (subagenti `general-purpose` con commit dopo la base del subagente):
- se dichiarano `DONE` o `DONE_WITH_CONCERNS` (stati di Superpowers), serve una ricevuta verde sull'ultimo commit;
- se dichiarano `BLOCKED` o `NEEDS_CONTEXT`, basta una ricevuta di qualunque esito oppure un blocco aperto;
- uno stato non riconosciuto vale come `DONE`;
- il contatore dei blocchi sta in un file nella cartella di stato. Dopo 2 blocchi si apre `serve_te` e il subagente può chiudere.

### 8.2 test-guard

Lo usano la riga `git commit` di 7.4 e il gate (9.2). Confronta con la base e segnala.

**Nei file di test** (`test_globs`; `fixture_globs` sono esclusi solo se contengono dati, non codice eseguibile):
- file cancellati, con rilevamento delle rinomine;
- **identificativi dei test** presenti nella base e assenti nella testa;
- asserzioni diminuite, contate escludendo commenti e stringhe;
- marcatori di salto aggiunti, cercati come parole intere: `skip_markers` predefiniti per JavaScript, TypeScript e Python, compresi `xdescribe`, `xtest`, `describe.skip`, `test.todo`, `test.fixme`, `pytest.skip(`, `skipif`, `xfail`.

**In tutto il repo:**
- soglie di copertura abbassate;
- file della CI modificati;
- **file che definiscono come girano i test** (`verification_globs`): configurazioni dei runner, file di setup, `conftest.py`, la parte `scripts` di `package.json`, gli script richiamati dai comandi del gate;
- snapshot e baseline visive aggiornati.

**Valori predefiniti di `test_globs`**: comprendono `__tests__/**`, `test/**`, `tests/**`, `e2e/**`, `*_test.py`, `test_*.py`, `*.test.*`, `*.spec.*`, `*_test.go`, `src/test/**`.

**Valori predefiniti di `skip_markers`, per linguaggio**: JavaScript e TypeScript (`xit`, `xdescribe`, `xtest`, `.skip`, `.only`, `.todo`, `.fixme`, `.skipIf`, `.runIf(false)`, `.fails`), Python (`pytest.skip(`, `skipif`, `xfail`, `@unittest.skip`), Go (`t.Skip`), Java (`@Disabled`, `@Ignore`), Rust (`#[ignore]`). B potrà estenderli per profilo.

### 8.3 Deroghe, blocchi e atti

**Deroghe** (`tollgate waiver add <tipo> <file> [--test <id>] --scelta --perche --costo`):
- **dove si scrivono**: in `.tollgate/waivers.toml` nel ramo, così il gate su GitHub le legge e le mostra;
- **granularità**: un file per deroga; per il tipo `test`, anche gli identificativi dei test coinvolti;
- **quando valgono**:
  - `scope` su un file che non è di test né sensibile: le prime 2 per fetta valgono subito;
  - `test`, `ci`, `soglia`, `comando` e ogni `scope` oltre la seconda: restano **in attesa** fino a `/tollgate:approve waiver <id>`;
- tutte compaiono nella PR e nel riepilogo del gate.

**Blocchi** (`tollgate block open <tipo> --motivo`):
- tipi: `serve_te`, `conflitto_test_spec`, `dipendenza`, `permesso`, `transitorio`;
- un blocco porta il lavoro in fase `bloccato`. Lo apre l'agente, perché fermarsi è sempre permesso; lo chiudi solo tu con `/tollgate:resolve <id> <nota>`;
- `conflitto_test_spec` è la via d'uscita quando un test contraddice la specifica (R1).

**Atti dell'utente**, ognuno con il suo effetto:

| Atto | Effetto |
|---|---|
| `approve spec` | La spec di L2, dopo l'audit, passa al piano |
| `approve plan` | Il piano di L2 passa in esecuzione |
| `approve waiver <id>` | La deroga diventa valida |
| `approve level <L> <motivo>` | Abbassa il livello |
| `approve effect <id>` | Permette **una volta** l'effetto esterno negato (8.5) |
| `approve finding <id> <motivo>` | Declassa o archivia un rilievo confermato (falso positivo) |
| `approve rounds <n>` | Concede altri giri di revisione finale dopo il tetto, fino a 8 in totale per lavoro. Oltre gli 8: `approve unverified` chiude la revisione come «non verificata», scritto nella PR |
| `approve rebase` | Riallinea `work_base_sha` al `merge-base` con il ramo predefinito, dopo un rebase fatto da te |
| `approve unverified` | Permette di aprire la PR con una ricevuta «non verificato» |
| `approve pr` | Permette ad `open-pr` di partire su questo SHA. Anche `/tollgate:finish` digitato da te vale solo per lo SHA di quel momento |
| `resolve <id> <nota>` | Chiude il blocco |
| `abandon <lavoro>` | Chiude il lavoro e libera la chiave per ricominciare |
| `off` / `on` | Interruttore |

### 8.4 Gli atti nel gate

Il gate su GitHub **non si fida degli atti locali** né dello stato delle deroghe: li legge dalla PR e dal ramo e li mostra come «dichiarati». **Ogni deroga dichiarata scioglie la violazione corrispondente nel verdetto**, e le deroghe di tipo `test`, `ci`, `soglia` e `comando` rendono rosso il controllo informativo `tollgate/attenzione` (9.2). La tua garanzia è che li vedi, evidenziati, prima del merge.

### 8.5 Effetti esterni

**Cosa conta come effetto esterno:**
- i comandi in `[external_effects] commands`;
- un elenco predefinito di eseguibili di rete e di deploy: `ssh`, `scp`, `rsync`, `psql`, `docker push`, `kubectl`, `terraform apply`, `aws`, `gcloud`, `az`, `vercel`, `netlify`, `firebase deploy`, `supabase` (scritture), `wrangler deploy`, `npm publish`;
- gli script in `project_scripts`;
- `curl` e `wget` con metodo diverso da GET o con dati;
- strumenti MCP non elencati;
- `bash -c`, `sh -c`, `eval`, `python -c`, `node -e` che contengono uno dei casi sopra;
- l'esecuzione di uno script **non tracciato nella base** (scritto durante il lavoro) con un interprete.

**Come funziona:**
- il primo tentativo viene **negato**, con un identificativo e il comando;
- tu digiti `/tollgate:approve effect <id>`; l'agente riprova e l'hook lo permette **una volta**, per quel comando esatto;
- il permesso si registra come intento, con una chiave di idempotenza (comando, lavoro, SHA);
- se lo stesso effetto si ripresenta sullo stesso SHA, il messaggio dice «già eseguito alle 10:42».

**Ripresa degli intenti in sospeso** (push e PR): `start` ricontrolla SHA e stato e ti chiede conferma prima di completarli.

### 8.6 Revisori: brief e verdetti

- `tollgate review prepare` scrive il brief di ogni revisore: diff, piano, must-have, SHA e un **codice di controllo** casuale.
- **Il verdetto vale solo se**:
  - riporta lo SHA e il codice di controllo;
  - il transcript del subagente (`agent_transcript_path`) mostra la lettura del brief e dei file del diff;
  - il controllo di sola lettura (7.3) è passato.
- I verdetti di `tollgate:final-reviewer` e `tollgate:finding-verifier` li registra l'hook `SubagentStop` dall'ultimo messaggio.
- **Verdetto**: una riga JSON `{"sha", "codice", "esito": "ok" | "da_correggere" | "serve_te", "rilievi": [...]}`. Un JSON assente o malformato vale come `serve_te`.

**Limite dichiarato.** Così si verifica che il revisore abbia letto il materiale, non che abbia giudicato bene.

---

## 9. Gate su GitHub (controllo autorevole)

### 9.1 Tre workflow più `tollgate-base`

`/tollgate:init` propone di installare nel repo una copia del CLI in `.github/tollgate/` e tre workflow:

| Workflow | Evento | Definizione | Esegue codice della PR? | Permessi | Cosa fa |
|---|---|---|---|---|---|
| `tollgate-guard` | `pull_request_target` | Ramo predefinito | **No**: checkout del solo ramo predefinito; gli oggetti della PR si scaricano con `git fetch` senza checkout | `contents: read`, `statuses: write` | Pubblica lo stato `tollgate/guard` sul commit della PR |
| `tollgate-run` | `pull_request` | Quella della PR, che però `guard` impone uguale alla base | Sì | Sola lettura, nessun segreto | Esegue `setup` e i comandi del gate sulla testa; carica come artefatti **solo** il report JUnit, il codice d'uscita e i conteggi. Nessun filtro `paths` o `branches`: gira per ogni PR |
| `tollgate-verdict` | `workflow_run` (al termine di `tollgate-run`) | Ramo predefinito (verificato) | **No**: usa il CLI e la configurazione del ramo predefinito. **Calcola da sé il diff** scaricando gli oggetti della PR con `git fetch`, senza checkout. Legge gli artefatti come **dati** in una cartella temporanea e non li esegue mai | `contents: read`, `statuses: write`, `pull-requests: write` | Pubblica sempre uno stato esplicito, `tollgate/verdict` e `tollgate/attenzione` (mai «saltato»), e il commento di riepilogo |

**Controlli di `verdict` prima di valutare:**
- l'esecuzione che l'ha avviato viene dal file atteso (`workflow_run.path`), dall'evento `pull_request` e dallo SHA che è **ancora** la testa della PR;
- la PR punta al ramo predefinito.

Se qualcosa non torna, pubblica `error` con il motivo. Le PR verso altri rami ricevono `verdict` «non applicabile»: la protezione vale sul ramo predefinito, dove arriveranno comunque.

**Artefatti** (dati non fidati):
- tetto di dimensione per file e in totale;
- estrazione in una cartella temporanea, rifiutando percorsi con `..` o assoluti;
- XML con `DOCTYPE` o entità rifiutato prima della lettura.

Un artefatto non valido produce lo stato `error` con il motivo, mai uno stato assente.

Il workflow di supporto **`tollgate-base`**: evento `push` sul ramo predefinito, codice fidato. Esegue i comandi del gate sul ramo predefinito e salva gli identificativi dei test in una cache con chiave lo SHA. Le cache del ramo predefinito si leggono dai workflow che girano nel suo contesto, come `verdict`. Se per quello SHA la cache manca, `verdict` calcola gli identificativi facendo il checkout della base, cioè con codice e dipendenze della base.

### 9.2 Cosa controllano

| Controllo | Dove | Esito |
|---|---|---|
| **File di tollgate invariati**: contenuto alla testa della PR uguale a quello sulla punta attuale del ramo predefinito | `guard` | **Bloccante**, salvo il percorso di aggiornamento (9.4) |
| Comandi del gate (`[commands] gate` e `gate` dei profili attivi) eseguiti da zero dopo `setup`: esito, test eseguiti | `run` → `verdict` | **Bloccante** se rossi, oppure «vuoti» senza `allow_no_tests` |
| **Identificativi dei test della base presenti ed eseguiti sulla testa**, salvo quelli coperti da una deroga `test` | `verdict` | **Bloccante** |
| test-guard sul diff della PR (8.2), per **tutte** le PR | `verdict` | **Bloccante** senza deroga dichiarata |
| Coerenza dello scope: ogni file del diff è nei piani della PR, tra gli esenti o in una deroga (solo PR da rami `tg/*`) | `verdict` | **Bloccante**. Senza piano e oltre le soglie di L0 → bloccante. Più di 2 deroghe `scope` → `attenzione` rosso |
| Livello ricalcolato. In L2 devono esserci spec, piano, report dell'audit della spec e report dell'avversario del piano sotto `docs/superpowers/` | `verdict` | Se mancano: `attenzione` rosso |
| Deroghe `test`, `ci`, `soglia`, `comando`; piano della testa diverso da quello del primo commit del ramo che lo contiene (la storia del ramo è riscrivibile: è un segnale, non una prova); lockfile cambiati senza manifest; test della base che falliscono sulla testa; PR da un ramo che non è `tg/*`; periodi con tollgate spento | `verdict` | `tollgate/attenzione` **rosso**, ma **non obbligatorio**: lo vedi evidenziato, decidi tu |

**Il riepilogo.**
- Il testo scritto dall'agente (corpo della PR, motivi delle deroghe, nomi dei file) entra nel riepilogo **neutralizzato**:
  - in blocchi di codice delimitati da una sequenza di backtick più lunga di qualunque sequenza contenuta;
  - con le menzioni `@` disattivate;
  - con una lunghezza massima.
- Il commento riporta lo SHA. `verdict` non lo aggiorna se quello SHA non è più la testa della PR.
- Le PR da rami che non sono `tg/*` (tue, di manutenzione) ricevono comandi del gate, identificativi della base e test-guard, ma non il controllo dello scope. `attenzione` lo segnala, perché il nome del ramo lo sceglie chi apre la PR.
- Per le PR di Dependabot i permessi dei workflow sono ridotti (verificato per `pull_request`). Se `verdict` non può pubblicare, la PR resta in attesa e la gestisci tu (13).

### 9.3 Protezione del ramo

`/tollgate:init` propone il comando `gh api` completo per il ramo predefinito:
- PR obbligatoria;
- controlli obbligatori `tollgate/guard` e `tollgate/verdict`, **con la sorgente fissata sull'app GitHub Actions**, così un job o uno stato con lo stesso nome creato altrove non li soddisfa;
- ramo aggiornato prima del merge (`strict`);
- regole valide anche per gli amministratori;
- push forzato e cancellazione vietati.

**Chi lo esegue.** Lo esegui tu. Per l'agente `gh api` con un metodo diverso da GET è un effetto esterno, negato «best effort» (7.4).

**Controllo all'avvio.** `start` legge la protezione con `gh api` (GET) e avvisa se manca qualcosa. La protezione vale per il ramo predefinito: le PR verso altri rami arrivano comunque lì.

### 9.4 Aggiornare configurazione e gate

Una PR da un ramo `tollgate-config/*` che contiene **solo** file di tollgate (più `.tollgate/waivers.toml`):
- passa `guard`, e `attenzione` è **sempre rosso**;
- è esente da test-guard e scope;
- riceve i comandi del gate come le altre PR.

Il riepilogo mostra:
- le chiavi di `tollgate.toml` cambiate, con quelle che **allentano** il gate in evidenza (componenti spenti, glob ridotti, `allow_no_tests`);
- se la copia del CLI in `.github/tollgate/` coincide con l'impronta pubblicata per quella versione del plugin.

Così aggiorni `tollgate.toml`, i workflow o la copia del CLI senza togliere la protezione. Il merge resta tuo. L'agente può preparare la PR, ma non unirla.

**Se il gate stesso è guasto**, per esempio quando `verdict` va in errore su ogni PR, la PR di riparazione è giudicata dal gate guasto. Procedura d'emergenza, solo tua:
1. disattivi temporaneamente i controlli obbligatori dalle impostazioni del repo;
2. fai il merge della riparazione da `tollgate-config/*`;
3. riattivi i controlli.

`start` segnala la protezione incompleta finché non la riattivi.

### 9.5 Costo

Ogni PR esegue `setup` e i comandi del gate una volta, sulla testa. La base usa la cache di `tollgate-base`; il costo raddoppia solo quando la cache manca. `base_test_ids` si può spegnere.

### 9.6 Servizi

Se i test richiedono servizi (un database, Supabase locale), `/tollgate:init` chiede quali e li mette nella proposta di `tollgate-run`. Se il gate non può girare in CI, `start` lo segnala. La scelta di togliere l'obbligo resta tua.

## 10. Revisione finale

| Livello | Revisori | Poi |
|---|---|---|
| L0 | Nessun agente | Gate su GitHub e merge tuo |
| L1 | `tollgate:final-reviewer` con la checklist dei profili attivi | `tollgate:finding-verifier` → verdetto |
| L2 | `tollgate:final-reviewer` + al massimo 3 specialisti, se installati, ognuno in un subagente: `pr-review-toolkit:pr-test-analyzer`, `pr-review-toolkit:silent-failure-hunter`, `security-review` tramite `tollgate:specialist-runner`. Codex come parere tramite `specialist-runner`, se installato (R16) | `tollgate:finding-verifier` → verdetto |

- **Specialisti esterni**: non sono dipendenze. Se mancano, la PR dice quali sono stati saltati.
- **Verificatore**: uno solo per giro. Controlla ogni rilievo separatamente con le sue prove, in ordine di gravità, fino a `max_findings` (predefinito 15). Quelli oltre il tetto vengono elencati come «non verificati» e non fermano la PR.
- **Rilievi che fermano la PR**: solo quelli confermati con gravità `bloccante` o `grave`, salvo un `approve finding`.
- **Giri e rebase**: se dopo un rebase il diff della fetta è identico (stesso `patch-id`), il verdetto precedente vale ancora e non si consuma un giro.
- **Tetto dei giri**: 4. Superato il tetto si apre un blocco `serve_te`, che chiudi con `approve rounds`, `approve finding` oppure `resolve`. `resolve` concede **un** giro in più. Massimo 8 giri per lavoro; oltre, `approve unverified`.
- **Revisione finale di Superpowers**: la skill `start` indica di saltarla. Se il coordinatore la fa comunque, il costo raddoppia ma non si perde nessun controllo.

---

## 11. Installazione e configurazione

### 11.1 Dipendenze

- **Superpowers** in `dependencies`, con intervallo `>=6.4.1 <7.0.0`. Se il suo marketplace non pubblica i tag di versione, la dipendenza si dichiara senza intervallo e la versione la controlla `start`.
- **`marketplace.json`** con `allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]` (formato verificato su plugins/dependencies.md).

### 11.2 `/tollgate:init`

Scrive una **proposta** in `docs/superpowers/tollgate-init/`:
- `tollgate.toml`;
- i tre workflow più `tollgate-base` e la copia del CLI, con i servizi richiesti dai test;
- il comando per la protezione del ramo;
- la configurazione consigliata per dare all'agente un **token GitHub separato**, con permessi su contenuti e PR ma senza amministrazione.

Tu rivedi i file, li copi al loro posto, li committi sul ramo predefinito **prima** di attivare la protezione, ed esegui il comando di protezione. Gli aggiornamenti successivi passano dal percorso 9.4.

### 11.3 `/tollgate:setup`

Un plugin non può impostare la statusline principale: dal suo `settings.json` valgono solo `agent` e `subagentStatusLine` (verificato). `/tollgate:setup` ti mostra la modifica da fare a `~/.claude/settings.json` per usare `statusline/statusline.sh`, che scrive la percentuale di contesto in `ctx/<session_id>.json`.

Senza statusline, oppure con una percentuale `null`, la guardia del contesto non blocca e `start` avvisa.

### 11.4 `tollgate.toml`

```toml
[project]
# il ramo base è il ramo predefinito di origin

[commands]
setup        = "npm ci"                      # installazione nell'ambiente pulito del gate
verify       = "npm run check"
test_related = "npx vitest related --run {files}"   # {files}: file del diff rispetto alla base del lavoro
gate         = ["verify"]
report       = "junit:reports/junit.xml"
timeout_s    = 900

[project_flags]
allow_no_tests = false

[levels]
sensitive_paths  = ["**/migrations/**", "src/**/auth/**"]
sensitive_labels = ["security", "database"]
l0_max_files = 2
l0_max_lines = 50
l0_max_bytes = 4000

[context]
warn_pct = 45
stop_pct = 55

[scope]
always    = []
lockfiles = { "package-lock.json" = "package.json", "pnpm-lock.yaml" = "package.json", "poetry.lock" = "pyproject.toml" }
max_scope_files = 30

[external_effects]
commands        = []                          # in aggiunta all'elenco predefinito
project_scripts = ["deploy", "release"]
mcp_allow       = []

[test_guard]
test_globs         = []                       # in aggiunta ai predefiniti
fixture_globs      = ["**/fixtures/**/*.json", "**/__snapshots__/**"]
ci_globs           = [".github/workflows/**"]
verification_globs = ["vitest.config.*", "vite.config.*", "vitest.setup.*", "jest.config.*", "playwright.config.*", ".mocharc.*", "tsconfig*.json", "conftest.py", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml", "Makefile", "scripts/check*"]   # in package.json: scripts, jest, vitest
skip_markers       = []                       # in aggiunta ai predefiniti

[spec_audit]
spec_rounds       = 4
spec_audit_cycles = 30

[review]
parallel_ok  = ["pr-review-toolkit:pr-test-analyzer", "pr-review-toolkit:silent-failure-hunter"]
output_dirs  = ["reports/", "coverage/"]
max_findings = 15

[severity]
bloccante = "dato sbagliato senza conferma, dati di altri utenti, azione eseguita due volte"
grave     = "un passo che fallirebbe così com'è scritto, o un comportamento sbagliato"
rilevante = "debito o attrito che emergerà più avanti"
minore    = "redazionale"

[retention]
retention_days = 30
events_days    = 180

[profiles]
active = ["base"]

[profiles.base]
paths       = ["**"]
gate        = []
checklist   = ""
specialists = []

[components]   # mappa aperta (R10)
scope_check = true
plan_check = true
test_guard = true
context_guard = true
subagent_receipt_gate = true
single_writer = true
readonly_check = true
reviewer_reads_check = true
final_review = true
spec_adversary = true
spec_audit = true
plan_adversary = true
specialists = true
base_test_ids = true
```

---

## 12. Stato locale

### 12.1 Il file

`tollgate.db` sta nella cartella di stato, uno per macchina: SQLite con `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout=5000`. **Serve ai guardrail e alla ripresa**, non al gate.

### 12.2 Tabelle

| Tabella | Colonne principali | Vincoli |
|---|---|---|
| `work_items` | id, chiave del repo, issue, issue madre, fetta, livello, abbassamento (motivo), fase, fase prima del blocco, ramo, worktree, `work_base_sha`, ultima sessione, date, abbandonato | univoco (chiave del repo, issue, fetta) tra i lavori non abbandonati |
| `slices` | lavoro del piano principale, numero, titolo, dipendenze, stato | univoco (lavoro, numero) |
| `scope` | lavoro, percorso, origine (`piano` o `deroga`), registrato il | |
| `receipts` | lavoro, sha, comando risolto, exit, test eseguiti e saltati, durata, log, prodotta da, stato | |
| `blocks` | lavoro, tipo, motivo, aperto, chiuso, risoluzione | |
| `subagents` | id, tipo, lavoro, `agent_base_sha`, impronta, inizio, fine, riprese, stato dichiarato | |
| `findings` | lavoro, giro, fonte, gravità, file, riga, testo, esito della verifica, `decisione_utente` | |
| `acts` | tipo (sezione 8.3), oggetto, id, ora, testo digitato | |
| `intents` | lavoro, azione, chiave di idempotenza, dati, stato, esito, ora | univoco (chiave) |
| `events` | registro in sola aggiunta | |
| `meta` | versione dello schema | |

Le deroghe stanno nel ramo (`.tollgate/waivers.toml`), non nel DB.

### 12.3 Fasi e ripresa

**Fasi:** `piano` (in L2 preceduta da `audit_spec`) → `approvazione` (solo L2) → `esecuzione` → `revisione` → `pr_aperta` → `chiuso`. Da `pr_aperta` si torna a `esecuzione` con `start #N`.
- Da qualunque fase si passa a `bloccato`, e si torna alla fase precedente con `resolve`.
- Quando il livello sale da L0 a L1 si torna a `piano`.

**Chi cambia fase:**
- `bin/tollgate`;
- gli hook (blocchi e atti);
- il tuo merge, rilevato con `gh` alla chiamata successiva.

**Ripresa.** `start` controlla worktree, SHA e intenti in sospeso; se qualcosa non corrisponde si ferma e chiede. `finish` riprende dal punto registrato se lo SHA non è cambiato.

**Due sessioni sullo stesso lavoro.** Se negli ultimi 10 minuti ci sono eventi di un'altra sessione, `start` avvisa e chiede conferma.

### 12.4 Pulizia e migrazioni

- **Pulizia**: i log dei lavori chiusi da più di `retention_days`, i file di contesto più vecchi di 7 giorni e gli eventi più vecchi di `events_days`.
- **Migrazioni**: in avanti, con una copia del DB prima di ciascuna.

---

## 13. Errori e casi limite

| Situazione | Comportamento |
|---|---|
| Script di controllo in errore, crash o timeout | Il wrapper esce con 2 e indica il log e `/tollgate:off` |
| `SubagentStop` in errore | Uscita 0 con un avviso, per non tenere in vita il subagente all'infinito |
| Python o DB rotti | `/tollgate:off` funziona senza Python né DB; i periodi spenti finiscono nella PR |
| Repo non attivo | tollgate non fa niente |
| Gate o protezione del ramo non installati | `start` si rifiuta (gate assente) o avvisa (protezione assente) |
| Effetto esterno nascosto in uno script non elencato | Limite dichiarato (1.2) |
| Effetto esterno | Negato fino a `/tollgate:approve effect` |
| Comando di verifica assente | «Non verificato»; serve `approve unverified`; il gate su GitHub fallisce comunque se il comando del gate manca |
| Zero test eseguiti | Ricevuta «vuota»; il gate fallisce |
| Test instabili | Un nuovo tentativo; la ricevuta è segnata «instabile» |
| Ramo predefinito andato avanti | Rebase fatto da te, poi `/tollgate:approve rebase`; `open-pr --update` fa il push forzato |
| Verdetto del gate rosso dopo l'apertura della PR | `start #N` riporta il lavoro in `esecuzione`; poi `finish` aggiorna la stessa PR |
| Aggiornare `tollgate.toml` o il gate | PR da `tollgate-config/*` (9.4) |
| Gate guasto | Procedura d'emergenza (9.4), solo tua |
| PR di Dependabot senza `verdict` | La gestisci tu: il gate non può pubblicare |
| Artefatto non valido o enorme | `verdict` pubblica `error` con il motivo |
| Test che richiedono servizi | Servizi nel workflow (9.6) |
| Task senza test collegati | `verify` esegue il gate completo |
| Lavoro impostato male | `/tollgate:abandon`, poi si ricomincia |
| Rilievo confermato ma falso | `/tollgate:approve finding` |
| Revisione oltre il tetto | `serve_te`, risolvibile con `approve rounds` (al massimo 8 giri) |
| Un revisore modifica il worktree | Verdetto non valido, `serve_te` |
| Due implementatori insieme | Il secondo viene negato |
| GitHub irraggiungibile | Le fasi locali continuano; `open-pr` aspetta; gli intenti restano in sospeso |
| Statusline assente o percentuale `null` | Guardia del contesto spenta, con un avviso |
| Specialisti esterni non installati | Saltati, e la PR lo dice |
| Sviluppo di tollgate con tollgate attivo | Il plugin installato e il repo di sviluppo sono cartelle diverse; in alternativa `/tollgate:off` |

---

## 14. Test del plugin

| Livello | Cosa | Come |
|---|---|---|
| Script | Sottocomandi, parser dei piani, test-guard (compresi gli attacchi delle revisioni avversariali), ricevute, gate | Test unitari con diff, piani, registri di Superpowers e report JUnit di esempio |
| Wrapper | Uscite 1, 127, eccezione e scadenza → 2 per i controlli e 0 per gli informativi; `OFF`; `on` e `off` senza Python | Test del wrapper con script finti |
| Hook | Ogni riga di 7.2 e 7.4 | Input JSON uguale a quello di Claude Code |
| Integrazione locale | `start → verify → finish`, ripresa, intenti, atti, rebase, abbandono | Repo git temporaneo, finto `gh`, `TOLLGATE_STATE` temporaneo |
| Gate | Workflow su un repo di prova su GitHub. Verde: PR pulita, PR da `tollgate-config/*` con soli file di tollgate, PR fatta a mano da un ramo non `tg/*`. `verdict` rosso: test tolti, `skip`, file fuori scope. `guard` rosso: `tollgate.toml` cambiato, workflow aggiunto o modificato fuori da `tollgate-config/*`. `attenzione` rosso: deroga `test`, piano diverso dal primo, PR da ramo non `tg/*`, ogni PR `tollgate-config/*`. `verdict` in `error`: artefatto con `../`, XML con entità, `workflow_run` con SHA non più in testa. `verdict` «non applicabile»: PR verso un ramo non predefinito | Repo di prova privato e PR create dalla suite |
| Comportamento | L'agente con tollgate rispetta gli obblighi | `claude plugin eval`, 3 esecuzioni per caso |
| CI | Tutto quanto sopra verde a ogni push | GitHub Action sul repo di tollgate |

**Casi di eval** (oltre a quelli sotto, uno per l'audit della spec: una spec con una contraddizione voluta → rilevata dall'avversario):
1. Implementatore DONE senza ricevuta → bloccato.
2. Test in conflitto con la specifica → `conflitto_test_spec`.
3. File fuori scope → negato, deroga.
4. Deploy → negato fino all'atto.
5. L0 che cresce → L1.
6. Fine di subagent-driven-development → `/tollgate:finish`, nessun merge locale.

---

## 15. Criteri di accettazione del nucleo

Ogni criterio è un'azione con un esito binario, verificato dal test indicato.

1. **Avvio.** In un repo attivo con il gate installato, `start #N` crea worktree, ramo `tg/N-<slug>` e riga `work_items`. Senza `tollgate.toml` o senza gate → rifiuto con il motivo (integrazione).
2. **Piano.** Un piano senza sezioni → `block` e nessuno scope. Un piano con glob o cartelle → `block`. Un piano completo → scope registrato. Un piano riscritto con un file in più dopo la registrazione → scope invariato (hook, script).
3. **Scope locale.** In `esecuzione`, Edit fuori scope → `deny`; dopo una deroga valida → permesso. In `piano` → solo i `.md` sotto `docs/superpowers/`. In L1, Edit di codice dalla sessione principale → `deny` (hook).
4. **Implementatore.** Con DONE e commit senza ricevuta verde → `block`; al terzo tentativo `serve_te`. Con BLOCKED e ricevuta rossa → chiude (hook).
5. **Commit.** Con `git add -A && git commit`: test cancellato, `xdescribe`, `pytest.skip(`, asserzione tolta (anche se sostituita da un commento) → `deny` senza deroga. `process.exit(` in codice non di test → nessuna segnalazione (hook, script).
6. **Comandi.** Effetti esterni (elenco, `curl -X POST`, `psql`, script non tracciato, MCP non permesso) → `deny`, poi permesso una volta dopo `approve effect`. Distruttivi, `git push` e `gh pr create` su `tg/*`, merge verso la base, `claude -p`, `TOLLGATE_STATE=…`, `touch` su file protetti → `deny`. In un repo non attivo, `git push` → permesso (hook).
7. **Subagenti.** A `stop_pct` → `deny`; con la percentuale `null` → permesso. Secondo `general-purpose` → `deny`. `isolation: worktree` in un lavoro attivo → `deny` (hook).
8. **Revisori.** Un verdetto senza codice di controllo, oppure da un revisore che non ha letto il brief → non valido. Un revisore che modifica un file tracciato → `serve_te`. JSON malformato → `serve_te`. Al 5° giro → `serve_te`, e dopo `approve rounds 1` → giro permesso (hook, integrazione).
9. **PR.** `open-pr` senza `/tollgate:finish` digitato da te e senza `approve pr` → rifiuto. Interruzione tra push e PR → `start` chiede conferma e non crea PR doppie (integrazione).
10. **Gate su GitHub.** Sul repo di prova, ogni caso della riga «Gate» della sezione 14 dà l'esito indicato. Una PR che aggiunge o modifica un workflow fuori da `tollgate-config/*` → `guard` rosso. Uno stato `tollgate/verdict` pubblicato da una sorgente diversa da GitHub Actions non soddisfa la protezione (gate).
11. **Protezione.** `start` legge la protezione con GET e segnala i campi mancanti di 9.3 (integrazione con finto `gh`).
12. **Atti.** Gli atti si registrano solo da `UserPromptExpansion`. Lo strumento Skill sulle skill riservate all'utente non produce atti (hook).
13. **Wrapper.** Uscita 1, 127, eccezione e scadenza → 2. `OFF` → tutto passa e il periodo viene registrato. `/tollgate:on` funziona con `OFF` presente (wrapper).
14. **Ricevute.** Zero test → «vuota» (script).
15. **Rebase e abbandono.** Dopo un rebase e `approve rebase`, scope e test-guard locali non segnalano i commit del ramo predefinito. `abandon` permette di ricominciare la stessa issue (integrazione).
16. **Componenti.** Ogni chiave di `[components]` a `false` spegne il suo comportamento (script, hook).
17. **Budget delle istruzioni.** Stato iniettato al massimo 10 righe e 1.500 caratteri (hook).
18. **Rinomine.** Un file di test rinominato con gli stessi test → nessuna segnalazione (script).
19. **Deroghe.** Una deroga `scope` su un file non sensibile vale subito; una `test` resta in attesa fino all'atto; il gate le mostra tutte, con `attenzione` rosso per le `test` (script, gate).
20. **Livelli.** L0 che supera le soglie → L1 e fase `piano`; un percorso sensibile → L2; `approve level` lo abbassa e la PR lo riporta (hook, integrazione).
21. **Dopo la PR.** Con il verdetto rosso, `start #N` → `esecuzione`; `finish` aggiorna la stessa PR. Dopo `approve rebase`, `open-pr --update` fa il push forzato; senza l'atto il push forzato è negato (integrazione).
22. **Effetti ripetuti.** Lo stesso effetto approvato e rieseguito sullo stesso SHA → il messaggio indica l'esecuzione precedente (hook).
23. **Interruttore.** Un periodo con `OFF` compare nella PR e rende rosso `attenzione` (wrapper, gate).

---
24. **Audit della spec.** In L2, `approve plan` e `approve spec` vengono rifiutati senza i report dell'audit della spec. Un giro con un bloccante obbliga a un nuovo giro; al tetto si apre `serve_te` (hook, integrazione).

## 16. Da verificare prima di scrivere codice

**Già verificato l'08/10/2026:**
- solo l'uscita 2 blocca; uscita 1, crash e timeout no;
- timeout predefinito di 600 s;
- `PostToolUse` con `block` non annulla l'azione;
- `UserPromptExpansion` scatta quando l'utente digita il comando `/skill`, e non quando il modello usa lo strumento Skill;
- `disable-model-invocation` blocca le chiamate del modello;
- lo strumento dei subagenti si chiama `Agent`, e gli agenti di un plugin hanno `agent_type` nella forma `plugin:nome`;
- `agent_id` c'è solo nei subagenti;
- `SubagentStart` può iniettare contesto;
- un subagente con `Skill` tra i suoi strumenti può usare le skill;
- `isolation: worktree` parte dal ramo predefinito;
- un plugin non può impostare la statusline;
- formato di `dependencies` e allowlist;
- `pull_request_target` gira nel contesto del ramo predefinito;
- in `dontAsk` le richieste di conferma vengono negate;
- `workflow_run` usa la definizione del ramo predefinito, ha token con permessi di scrittura e scarica gli artefatti dell'esecuzione che l'ha avviato (docs.github.com);
- l'input di `Agent` non contiene `isolation`; esiste l'evento `WorktreeCreate`.

**Ancora da verificare:**
- se un hook `deny` vale anche in `bypassPermissions`. È quasi certo, perché gli hook non sono permessi, ma va provato;
- se `UserPromptExpansion` scatta per le skill con `disable-model-invocation`: è l'ipotesi più forte, va provato;
- i campi di `agent_transcript_path` per riconoscere le letture del revisore;
- se `EnterWorktree` si può usare dentro la skill `start` (lo strumento chiede un'istruzione esplicita); altrimenti resta la riapertura di Claude Code nel worktree;
- se lo stato pubblicato da un job `workflow_run` con `GITHUB_TOKEN` risulta come sorgente «GitHub Actions» per la protezione del ramo;
- l'identificativo dell'app GitHub Actions da fissare nei controlli obbligatori;
- quale file di workflow usa `pull_request_target` per una PR verso un ramo non predefinito (base della PR o ramo predefinito);
- i permessi di `workflow_run` e `statuses: write` per le PR di Dependabot;
- se `WorktreeCreate` può bloccare la creazione di un worktree da parte di un subagente;
- se Superpowers pubblica i tag di versione;
- il formato dei report JUnit di vitest, jest e pytest e la stabilità degli identificativi dei test;
- il comando di revisione di codex-plugin-cc dentro un subagente.

---

## 17. Cosa resta aperto

È ripetuto qui perché nessuno lo scambi per una garanzia (1.2):
- l'agente che usa le credenziali GitHub dell'utente;
- gli effetti esterni hanno un solo livello di controllo;
- le asserzioni indebolite senza cambiare il numero dei test;
- la qualità del giudizio dei revisori;
- i guardrail locali sono «best effort»;
- il codice della PR che falsifica l'esito dei propri test;
- scope e deroghe dichiarati dall'agente;
- la compensazione del conteggio delle asserzioni;
- le serie di PR L0;
- il sabotaggio deliberato della CI, fino alla modalità rinforzata.

---

## 18. Revisioni

| Rev. | Data | Cosa |
|---|---|---|
| 1 | 08/10/2026 | Prima stesura |
| 2 | 08/10/2026 | Cicli 1-3 dell'audit (A-01 … A-25) |
| 3 | 08/10/2026 | Prima revisione avversariale (V-1 … V-36) e verifica sulla documentazione |
| 4 | 08/10/2026 | Cicli 5-10 (B-01 … B-17) |
| 5 | 08/10/2026 | Seconda revisione avversariale (W-1 … W-40) e decisione dell'utente: **gate su GitHub** come controllo autorevole, guardrail locali dichiarati «best effort». Tolte la prova di presenza e le parti del «controllo autorevole locale» che leggevano dal DB. Effetti esterni: diniego più atto, perché funzioni in ogni modalità di permesso. R4 ridimensionata: in Superpowers 6.4.1 i giri 1-3 riprendono lo stesso implementatore, quindi tollgate li conta e li riporta invece di imporre un tetto. Atti nuovi per i casi di blocco: `finding`, `rounds`, `rebase`, `abandon`, `pr`. Brief dei revisori con codice di controllo e verifica delle letture. Identificativi dei test della base controllati sulla testa. Deroghe nel ramo, con granularità per test. File protetti elencati. Python ≥ 3.11 |
| 6 | 08/10/2026 | Cicli 12-18 (C-01 … C-10) e terza revisione avversariale (X-1 … X-27): gate diviso in tre workflow (`guard` e `verdict` fidati e dal ramo predefinito, `run` senza permessi) più `tollgate-base` per la cache; sorgente dei controlli fissata su GitHub Actions; `guard` su tutti i workflow; deroghe come «dichiarate» con controllo `attenzione` non obbligatorio; scope dichiarato e controllo di coerenza; identificativi della base calcolati con codice e dipendenze della base; percorso `tollgate-config/*` per gli aggiornamenti; PR da rami non `tg/*`; transizione `pr_aperta → esecuzione` e `open-pr --update`; gate completo quando non ci sono test collegati e `allow_no_tests`; marcatori per Go, Java e Rust; giri contati dai commit; `resolve` che concede un giro e `approve unverified` oltre gli 8; `/tollgate:finish` legato allo SHA; `WorktreeCreate`; riapertura di Claude Code nel worktree come strada predefinita; protezione del ramo completa; servizi nel workflow; esenzioni dallo scope al commit; criteri 11 e 19-23 |
| 7 | 08/10/2026 | Quarta revisione avversariale (Y-1 … Y-22) e decisione dell'utente: la garanzia del gate nella v1 copre scorciatoie e manomissioni locali; il sabotaggio deliberato della CI è un limite dichiarato e la modalità rinforzata con GitHub App viene dopo la v1. `verdict` calcola da sé il diff, convalida esecuzione, SHA e ramo, pubblica sempre uno stato esplicito e tratta gli artefatti con limiti. PR `tollgate-config/*` esenti da test-guard e scope, con `attenzione` sempre rosso, chiavi che allentano il gate e impronta del CLI. Procedura d'emergenza; deroghe `scope` oltre 2 in `attenzione`; commento legato allo SHA e neutralizzato; `verification_globs` ampliati; verdetto riusato dopo un rebase con lo stesso `patch-id`; Dependabot; riferimenti e conteggi corretti |
| 8 | 08/10/2026 | Decisione dell'utente: **audit della spec** nel flusso di L2. Giri avversariali a contesto pulito fino a un giro senza bloccanti né gravi; audit a lenti (versione incorporata di prd-audit) quando c'è un piano principale; report committati e controllati dal gate; atto `approve spec`; fase `audit_spec` |
