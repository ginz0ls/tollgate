# tollgate: specifica del nucleo (sotto-progetto A)

Data: 8 ottobre 2026.
Revisione: **10**, riscritta con i cicli 22-29 dell'audit e con le decisioni dell'utente sul perimetro. Le revisioni precedenti sono nella sezione 20.
Stato: **in audit** (`docs/audit/2026-10-08-audit-spec-nucleo-stato.md`).
Fonti: `docs/REPORT-CONFRONTO-WORKFLOW.md`, `docs/COSA-TENERE.md`, `docs/RICERCA-PAPER.md`. I codici R e H usati nel testo sono spiegati nella sezione 19.

---

## 0. Glossario

**Lavoro e repo**

| Termine | Significato |
|---|---|
| **lavoro** | Un'issue GitHub portata fino a una PR. È una riga di `work_items`. Nel nucleo **un'issue corrisponde a un lavoro e a una PR** |
| **lavoro attivo** | Un lavoro non chiuso e non abbandonato. Le regole complete valgono in due casi: **nella sessione che l'ha avviato o ripreso**, su qualunque ramo, e **nel suo worktree** (6.6) |
| **coordinatore** | La sessione principale di Claude Code, che parla con l'utente |
| **implementatore** | **Ogni** subagente che non è nell'elenco di sola lettura (4) |
| **task del piano** | Un task di un piano di Superpowers (`### Task N`) |
| **base del lavoro** | Lo SHA da cui parte il ramo (`work_base_sha`). Si riallinea solo con `sync` o con un atto dell'utente |
| **base del subagente** | Lo SHA del momento in cui un subagente parte o riprende (`agent_base_sha`) |
| **chiave del repo** | L'URL di `origin` normalizzato: senza protocollo né `.git`, in minuscolo (`github.com/proprietario/nome`) |
| **repo attivo** | Un repo con `tollgate.toml` sulla punta del ramo predefinito di `origin` (7.1). **Negli altri repo tollgate non fa niente** |
| **cartella di stato** | `~/.local/state/tollgate`: contiene DB, log, file del contesto e interruttore |
| **file di tollgate** | `tollgate.toml`, `.github/workflows/**`, `.github/actions/**`, `.github/tollgate/**` |
| **file protetti** | I file di tollgate, più `.tollgate/waivers.toml`, le impostazioni di Claude Code, `.git/hooks/**`, `.git/config`, la cartella di stato e il plugin installato (7.4) |

**Flusso e controlli**

| Termine | Significato |
|---|---|
| **fase** | `spec_audit`, `plan`, `approval`, `execution`, `review`, `pr_open`, `closed`, `blocked` (12.3) |
| **livello** | Quanto rigore richiede il lavoro: L0, L1 o L2 (5). Non va confuso con i «due livelli di controllo» della sezione 1 |
| **scope** | I file che il piano autorizza a creare o modificare. Le deroghe si contano a parte |
| **ricevuta** | Il risultato registrato di un comando di verifica su uno SHA. Stati possibili: `green`, `red`, `empty`, `uncounted`, `flaky`, `unverified` (8.1) |
| **deroga** | Un'eccezione dichiarata su un file, con motivo e costo (8.3) |
| **blocco** | Un arresto del lavoro con un tipo (`needs_you`, `test_spec_conflict`, `dependency`, `permission`, `transient`). Lo chiude l'utente |
| **veto dell'hook** | La risposta `deny` o `block` di un hook. È una cosa diversa dal blocco del lavoro |
| **atto dell'utente** | Un'operazione registrata quando l'utente digita un comando `/tollgate:*` (8.4) |
| **intento** | Un'azione esterna (push, PR, effetto) registrata prima di eseguirla, così una ripresa non la ripete |
| **ciclo di revisione** | Un passaggio di revisione finale che produce un verdetto (10). È diverso dai «giri di correzione» dei task del piano e dai «giri avversariali» sulla spec |
| **verdetto** | L'esito JSON di un revisore di tollgate: `ok`, `needs_fix` o `needs_you` |
| **gate** | Il controllo che decide se una PR è pronta. Quello che conta gira **su GitHub** (9); in locale ne gira una copia, solo per avere un riscontro rapido |
| **controllo obbligatorio** | Uno stato GitHub richiesto dalla protezione del ramo: `tollgate/guard`, `tollgate/verdict` |
| **attenzione** | Lo stato `tollgate/attention`: diventa rosso quando c'è qualcosa da leggere prima del merge. **Non** è obbligatorio |
| **gravità** | La gravità di un rilievo: `blocker`, `major`, `moderate` o `minor`, definite in `[severity]` |
| **lenti e punti di vista** | Il metodo dell'audit della spec (6.2). Le lenti sono dieci: coerenza verticale, orizzontale e interna, verificabilità, criteri osservabili, copertura, proiezione futura, fatti, lacune ricorrenti, completezza. I punti di vista sono otto: chi esegue, chi usa, chi attacca, chi paga, chi arriva dopo, lo scettico, il caso limite, chi integra |

**Lingua.** Comandi, file, fasi, stati, tipi e colonne sono in inglese. I testi rivolti all'utente e la documentazione sono in italiano.

---

## 1. Scopo e modello di fiducia

tollgate è un plugin per Claude Code. Porta un lavoro **da un'issue GitHub a una PR verificata**. Il merge lo fa sempre una persona, su GitHub.

Il flusso resta quello di **Superpowers**: brainstorming → writing-plans → subagent-driven-development. tollgate aggiunge quello che manca e **sostituisce un unico passo**: la chiusura del ramo (`finishing-a-development-branch`) diventa `/tollgate:finish` (6.4).

### 1.1 Due livelli di controllo

| | Dove gira | A cosa serve | Cosa garantisce |
|---|---|---|---|
| **Guardrail locali** | Hook di Claude Code, sulla macchina dell'utente | Fermano **subito** le scorciatoie e gli errori onesti del modello: test modificati, «fatto» senza prove, file fuori scope, effetti esterni non approvati, codice scritto dal coordinatore | **Nessuna garanzia contro un agente che lavora apposta per aggirarli.** Con Bash sulla stessa macchina può alterare DB, configurazione e processi locali (attacchi documentati in `docs/audit/2026-10-08-revisione-avversariale-2-spec-nucleo.md`) |
| **Gate su GitHub** | I workflow di 9.1, più la protezione del ramo | Ricalcolano **da zero** i fatti della PR: comandi del gate, identificativi dei test della base, test-guard, coerenza dello scope, file di tollgate invariati | Una PR non entra nel ramo predefinito senza `tollgate/guard` e `tollgate/verdict` verdi e senza il merge dell'utente |

### 1.2 Cosa resta fuori dalla garanzia

Questi limiti sono dichiarati:
- **L'agente che usa le credenziali GitHub dell'utente.** Lo limitano i guardrail e il token separato consigliato (11.2).
- **Gli effetti esterni.** Hanno un solo livello di controllo: quando arriva la PR sono già avvenuti.
- **Il codice scritto nel lavoro ed eseguito in locale** dai test o da `verify`, con l'ambiente ripulito (8.1).
- **Asserzioni rese più deboli o compensate con asserzioni banali.** Le cerca il revisore finale (R3).
- **La qualità del giudizio dei revisori.**
- **Il codice della PR che falsifica l'esito dei propri test.** Resta visibile nel diff.
- **Scope e deroghe sono dichiarati dall'agente.** Il gate ne verifica la coerenza, non la legittimità. Gli atti locali non sono verificabili da GitHub.
- **Le PR da rami che non sono `tg/*`** ricevono dal gate solo i controlli sui test, con `attenzione` rosso.
- **Una serie di PR L0.**
- **Il sabotaggio deliberato della CI**, per esempio workflow aggiunti per pubblicare stati falsi. La modalità rinforzata con GitHub App arriva dopo la v1.

### 1.3 Fuori dal nucleo

| Cosa | Dove |
|---|---|
| Profili per tipo di file con i loro controlli (R8, R11, R12) | Sotto-progetto **B**. Il contratto è già nel nucleo (11.4) |
| **Piano principale e fette**, sotto-issue, GitHub Projects, riconciliazione (R13) | Sotto-progetto **C**. Nel nucleo si usa un'issue per fetta (5) |
| Eval completi, prove a componenti spenti, costo e contesto dei subagenti (R15) | Sotto-progetto **D** |
| Specialisti esterni in L2, Codex come revisore, controllo delle letture dei revisori | Dopo la v1 |
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
| Flusso | Superpowers (11.1); `finishing-a-development-branch` → `/tollgate:finish` |
| Unità di lavoro | Un'issue = un lavoro = una PR |
| Controllo autorevole | Su GitHub; i controlli locali sono guardrail |
| Garanzia v1 | Scorciatoie e manomissioni locali |
| Stato locale | SQLite nella cartella di stato |
| Pianificatore | Il coordinatore |
| Audit della spec | In L2: giri avversariali sempre; audit a lenti quando la spec prevede più fette (6.2) |
| Revisione | Revisore finale e verificatore di tollgate (10) |
| Merge | Solo l'utente, su GitHub |
| Livello | Lo script lo alza; lo abbassa solo l'utente, con un atto |
| Effetti esterni | Negati finché non c'è un atto, oppure ammessi da un'eccezione in sola lettura (8.5) |
| Pubblicazione | Privato ora, pubblico poi |
| Lingua | Identificatori in inglese; testi in italiano |
| Sistemi | Linux e macOS, Python ≥ 3.11 |
| Requisiti del repo | Remote GitHub, `gh` autenticato, Actions attive, protezione del ramo |
| Repo senza test | Solo con `allow_no_tests = true`, mostrato in `attenzione` |

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
    sync/       /tollgate:sync                       solo l'utente
    adopt/      /tollgate:adopt #N                   solo l'utente
    abandon/    /tollgate:abandon #N                 solo l'utente
    cleanup/    /tollgate:cleanup                    solo l'utente
    setup/      /tollgate:setup                      solo l'utente
    off/ on/    /tollgate:off [ore], /tollgate:on    solo l'utente
    spec-audit/ metodo dell'audit a lenti (versione di prd-audit incorporata, con l'accordo dell'autore)
  agents/
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

### 3.1 Sottocomandi di `bin/tollgate`

| Sottocomando | Chi lo chiama | Cosa fa |
|---|---|---|
| `start <N> [--level]` | Skill `start` | 6.1 e 12.4 |
| `verify` | Agente | 8.1 |
| `waiver add`, `block open` | Agente | 8.3 |
| `review prepare`, `finish check`, `finish open-pr [--update]` | Skill `finish` | 6.4. Il push forzato è ammesso solo dopo `sync` o `approve rebase` |
| `status`, `init --propose`, `init --update` | Agente | Sola lettura, oppure proposte scritte dalla CLI in `docs/superpowers/tollgate-init/` |
| `sync`, `adopt`, `cleanup`, `abandon` | Hook dell'atto dell'utente | 6.5 e 12.4 |
| `gate run`, `gate evaluate`, `gate guard`, `gate base-ids` | `finish check` e i workflow | Stesso codice in locale e su GitHub |
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

**Registro dei controlli.** Ogni controllo è un modulo che dichiara evento, componente e ordine. B aggiunge moduli senza toccare quelli esistenti.

**Adattatore dell'harness.** L'input degli hook diventa un evento interno; la decisione interna diventa la risposta di Claude Code.

**Altre regole.**
- Componenti spegnibili (R10).
- I pattern usano ovunque il dialetto di `.gitignore`.
- Prima si estende ciò che esiste (H44).

---

## 4. Ruoli

| Ruolo | Chi è | Cosa fa | Come è imposto |
|---|---|---|---|
| Utente | — | Alza il livello, approva spec e piano in L2, approva gli atti, risolve i blocchi, fa il merge | Atti dell'utente; merge su GitHub |
| Coordinatore | Sessione principale | Dialogo, brainstorming, spec, piano, avvio dei subagenti. **Non scrive codice**, tranne in L0 | In L1 e L2, fase `execution`: Edit e Write sul codice negati se manca `agent_id`, che c'è solo nei subagenti (verificato) |
| Implementatore | Ogni subagente **non** elencato in `[review] readonly_agents` | Un task del piano alla volta | Scope, scrittore unico, `SubagentStop` (8.1) |
| Revisore del task | Subagente di Superpowers | Controlla il task | Se fa commit, è trattato come implementatore |
| Avversario della spec, auditor della spec, avversario del piano | `tollgate:spec-adversary`, `tollgate:spec-auditor`, `tollgate:plan-adversary` | 6.2 | Niente scrittura, niente Bash |
| Revisore finale | `tollgate:final-reviewer` | Confronta il lavoro con piano, must-have e scope; cerca casi speciali e asserzioni indebolite (R3) | Brief scritto dallo script; controllo di sola lettura (7.3) |
| Verificatore | `tollgate:finding-verifier` | Conferma o scarta ogni rilievo registrato | Brief scritto dallo script dalla tabella `findings` (8.6) |

**Come si passano il lavoro.** Brief su file in ingresso, report su file o messaggio finale salvato dall'hook in uscita. Al coordinatore tornano al massimo 1-2K token più il percorso del report (R7).

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
- Se il livello dichiarato è sotto il minimo senza un tetto dichiarato → `attenzione` rosso.

**Spec con più fette.** La spec le elenca nella sezione «Fette previste». Dopo `approve spec`:
1. `start` propone **un'issue per fetta**: le crei tu, oppure le crea l'agente dopo il tuo `approve effect`;
2. il lavoro corrente continua con la prima fetta;
3. le altre diventano lavori a sé, con la spec già sul ramo predefinito, e partono dalla fase `plan`.

Il collegamento tra le issue è compito di C.

---

## 6. Ciclo di vita

### 6.1 Avvio

```
/tollgate:start #N [L1|L2]
  0. prerequisiti   repo attivo; Python ≥ 3.11; Superpowers nell'intervallo; remote GitHub e gh;
                    ramo predefinito con commit; gate installato; CLI in .github/tollgate/ della
                    stessa versione del plugin (altrimenti avviso e init --update). Se manca: rifiuto
  1. controlli      checkout principale pulito; stati obbligatori del ramo predefinito verdi
                    (altrimenti avviso e conferma); issue chiusa → avviso e conferma; ramo o PR remoti
                    già esistenti per l'issue → li mostra e propone di adottarli
  2. lavoro         lavoro attivo per (repo, issue) → ripresa (12.4); altrimenti nuovo lavoro
  3. livello        5
  4. worktree       tg/<N>-<slug> (slug [a-z0-9-], ≤ 40, con -2… se esiste); fase iniziale:
                    L0 execution, L1 plan, L2 spec_audit (le fette successive alla prima: plan)
  5. entrata        stampa «cd <percorso> && claude» e chiude qui la sessione di avvio; se
                    EnterWorktree accetta il percorso, la skill lo usa al posto (16)
```

**L'issue non è fidata.** Il suo testo passa ai modelli dentro file, marcato come dato, e non entra mai in un comando shell. Se l'autore è esterno al repo, il lavoro va in L2.

### 6.2 Spec e piano

```
L2, spec_audit: brainstorming → spec (con «Fette previste») → giri avversariali
                → [audit a lenti se le fette previste sono più di una] → /tollgate:approve spec
L1 e L2, plan:  checkpoint + /clear → writing-plans (la skill dà le intestazioni, 7.5) → plan-check
                → scope registrato; L1 → execution; L2 → plan-adversary → approval
                → /tollgate:approve plan → execution
```

**Audit della spec.**
1. **Giri avversariali.** A ogni giro `tollgate:spec-adversary` riparte in un subagente nuovo e chiude con una riga JSON (18.3). Il coordinatore corregge la spec. Si va avanti finché un giro non trova né `blocker` né `major`. Il tetto è `spec_rounds` (4); superato il tetto si apre un blocco `needs_you`.
2. **Audit a lenti.** Parte solo se «Fette previste» è maggiore di 1 e segue il metodo `spec-audit`: dieci lenti, otto punti di vista, un ciclo per ogni subagente nuovo. Al coordinatore torna solo il riepilogo.
   - L'audit si chiude quando ogni punto di vista ha dato due cicli vuoti di fila.
   - Una correzione `moderate` o più grave azzera il contatore del punto di vista che l'ha trovata.
   - Il tetto è `spec_audit_cycles` (30). Superato il tetto l'audit è «sospeso», si apre `needs_you`, e `resolve` lo accetta come sospeso.
3. **Report.** `SubagentStop` salva ogni giro in `docs/superpowers/reviews/<N>/<tipo>-<n>.md` (18.3). Lo stato dell'audit a lenti sta in `stato.md`. Il coordinatore committa i report insieme a spec e piano.
4. **Approvazione.** `approve spec` è accettato solo se l'ultimo giro avversariale non ha `blocker` né `major`, oppure se l'audit è stato accettato come sospeso.

### 6.3 Esecuzione

```
execution (sessione pulita)
  SessionStart: stato (≤ 10 righe, ≤ 1.500 caratteri)
  subagent-driven-development, un task del piano alla volta:
    SubagentStart inietta nell'implementatore scope, test correlati, passo del piano (R2, R5)
      e l'istruzione «prima di dichiarare DONE esegui tollgate verify»
    implementatore → commit (hook: test-guard, scope, livello) → tollgate verify → ricevuta
    SubagentStop: 8.1; conflitto tra test e specifica → block open test_spec_conflict (R1)
    revisore del task (Superpowers)
  giri di correzione: quelli di Superpowers, contati da tollgate e riportati nella PR (R4)
  guardia del contesto: avviso a warn_pct; a stop_pct nessun nuovo subagente → checkpoint + /clear
```

### 6.4 Chiusura

La skill `start` dice al coordinatore di usare `/tollgate:finish` al posto della revisione finale e della chiusura di Superpowers. Se lo dimentica, i guardrail negano merge, push, cancellazione del ramo e rimozione del worktree.

```
/tollgate:finish
  1. finish check   copia locale del gate (senza identificativi della base); fase review
  2. revisione      solo L1 e L2: review prepare → final-reviewer → review prepare dai rilievi
                    registrati → finding-verifier → verdetti registrati da SubagentStop (8.6)
                    needs_fix → execution: correzioni come nuovi task nello stesso scope; il
                    finish successivo è un nuovo ciclo di revisione
  3. open-pr        solo se: hai digitato /tollgate:finish dopo l'ultimo commit, oppure c'è
                    approve pr per lo SHA; 1 e (in L1 e L2) 2 sono passati sullo stesso SHA;
                    non ci sono blocchi né atti in sospeso; ogni rilievo registrato ha un esito.
                    Poi: intento → push → ls-remote → PR esistente? → crea o aggiorna, con il
                    blocco JSON (18.1)
  4. gate           9; fase pr_open
  5. merge          tuo, su GitHub
```

### 6.5 Dopo la PR

| Situazione | Cosa succede |
|---|---|
| Verdetto rosso o altre modifiche | `start #N` → `execution` → `finish` aggiorna la stessa PR |
| Ramo predefinito andato avanti (`strict`), anche dopo «Update branch» su GitHub | `/tollgate:sync`: integra i commit remoti della PR, fa il rebase sul ramo predefinito, riallinea la base, rilancia `finish check` e `open-pr --update` con `--force-with-lease`. Se il `patch-id` è lo stesso, il verdetto vale ancora |
| Merge o chiusura senza merge | Rilevati con `gh` alla chiamata successiva, da qualunque fase: `closed`, oppure ti chiede cosa fare |

### 6.6 Dove valgono le regole

| Dove | Quali regole |
|---|---|
| Repo non attivo | Nessuna |
| Repo attivo, sessione senza lavoro attivo, fuori dai worktree dei lavori | Comandi distruttivi e file protetti |
| **Sessione che ha avviato o ripreso un lavoro attivo**, su qualunque ramo e in qualunque directory, e **ogni comando dentro il worktree** di un lavoro attivo | **Tutte.** Il nome del ramo non conta. Sono negati il cambio e la rinomina del ramo nel worktree, le scritture nel checkout principale e il push o la PR di qualunque ramo fuori da `open-pr` |

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
1. `/tollgate:on` e `/tollgate:off [ore]` creano o cancellano `OFF`, con una scadenza facoltativa, senza passare da Python né dal DB.
2. Se `OFF` è attivo: esce con 0, scrive l'avviso «tollgate spento» su stderr e registra il salto in un file.
3. Controlla in shell, senza rete, se il repo è attivo: cerca `tollgate.toml` su `origin/HEAD`, poi su `origin/main` e `origin/master`. Se il repo non è attivo esce con 0. Se non trova nessun riferimento remoto, avvisa.
4. Se manca Python ≥ 3.11: esce con 2 e spiega perché.
5. Lancia `bin/tollgate hook <evento>` con una scadenza interna (`[hooks] timeout_s`, predefinito 20 s).
6. **Hook di controllo**: qualunque esito diverso da 0 o 2 diventa 2.
7. **Hook informativi e `SubagentStop`**: un errore diventa 0, con un avviso.

### 7.2 Tabella

| Evento | Filtro | Comportamento |
|---|---|---|
| `SessionStart` | `startup`, `resume`, `clear`, `compact`, `fork` | Inietta lo stato del lavoro. Segna come `interrupted` i subagenti di sessioni precedenti che non hanno mai chiuso |
| `UserPromptExpansion` | comandi `tollgate:*`, forma lunga e breve | Registra l'atto (8.4) |
| `PreToolUse` | `Edit`, `Write`, `NotebookEdit`, `MultiEdit` | In `spec_audit`, `plan`, `approval` e `blocked`: solo `.md` sotto `docs/superpowers/`. In `execution`: fuori scope → `deny`; codice scritto dalla sessione principale in L1 o L2 → `deny`. File protetti → `deny`. Sempre ammessi: `.md` sotto `docs/superpowers/` e `.superpowers/`. In L0 vale il livello |
| `PostToolUse` | `Edit`, `Write`, `MultiEdit` | Ricalcola il livello; sui piani lancia `plan-check` (7.5) |
| `PostToolUse` | `Bash` con `git commit` | Registra il commit |
| `PreToolUse` | `Bash` | 7.4 |
| `PreToolUse` | `mcp__.*` | Effetto esterno, se lo strumento non è in `mcp_allow` (8.5) |
| `PreToolUse` | `Agent` | Guardia del contesto. **Scrittore unico**: nessun nuovo implementatore se un altro è `running` nel worktree. Un subagente senza eventi da più di `stale_minutes` (30) diventa `interrupted` |
| `SubagentStart` | tutti | Salva `agent_base_sha` (senza sovrascriverla alla ripresa), l'impronta dei file e il tipo; inietta il contesto (6.3) |
| `SubagentStop` | tutti | Implementatori: 8.1. Sola lettura: 7.3. Revisori: 8.6. Avversari e auditor: salva il report |

`Stop` della sessione principale: nessun veto.

### 7.3 Controllo di sola lettura

Vale per `readonly_agents`. `SubagentStop` confronta i file tracciati e quelli non tracciati e non ignorati, escludendo `output_dirs`, con l'impronta presa alla partenza. Se sono cambiati, il verdetto non vale e si apre `needs_you`.

### 7.4 Regole su Bash

L'ambito è quello di 6.6. Le regole sono «best effort».

| Ambito | Comando | Decisione |
|---|---|---|
| Lavoro attivo | `git push`, `gh pr create` di qualunque ramo; `git switch`, `git checkout -b`, `git branch -m` nel worktree; scritture nel checkout principale | `deny` |
| Lavoro attivo | `git commit` (con `-a` o con `git add` nella stessa riga) | test-guard, scope e livello su working tree più indice; `deny` se mancano deroghe. Esenti dallo scope: `docs/superpowers/**/*.md`, `.tollgate/waivers.toml` e i lockfile il cui manifest è nello scope |
| Lavoro attivo | Scrittura di codice dalla sessione principale (L1, L2) con redirect o `sed -i` | `deny` |
| Repo attivo | Merge di un ramo `tg/*` verso il predefinito, `git branch -d/-D` e `git worktree remove` di un lavoro attivo, `git worktree add` doppio | `deny` |
| Repo attivo | Effetti esterni (8.5): `gh pr merge` e `gh` in scrittura (`api` con `-X` non GET, `-f`, `-F`, `--input`, `graphql` con `mutation`; `pr edit`, `pr review`, `release`, `workflow run`, `secret`, `project`, `issue edit` e `issue create`) | `deny` fino all'atto |
| Repo attivo | `push --force` fuori da `open-pr`, `reset --hard`, `--no-verify`, `rm -rf` fuori dal worktree | `deny` |
| Repo attivo | `claude` e i suoi alias, `TOLLGATE_` nel comando, `tollgate hook`, scrittura sui file protetti | `deny` |

### 7.5 `plan-check`

È un piano qualunque file `docs/superpowers/plans/*.md`. Deve contenere queste intestazioni esatte di secondo livello:
- `## Fatti verificati`
- `## Decisioni`
- `## Interfacce`
- `## Must-have`
- `## Scope`
- `## Punti di arresto`
- `## Rischi`

Le intestazioni si cambiano in `[plan] required_sections`, e i profili possono aggiungerne altre.

**Lo scope del piano.**
- Si ricava da `Create:`, `Modify:` e `Test:` di ogni task (formato verificato in writing-plans, righe 100-102).
- Solo file: niente pattern, niente cartelle; gli intervalli di righe vengono tolti.
- Al massimo 30 file.
- Una volta registrato **non cresce**: se il piano cambia, servono deroghe.

**Piano incompleto.** Riceve il veto con l'elenco di ciò che manca. Il file resta scritto ma non viene registrato.

---

## 8. Ricevute, test-guard, deroghe, atti, effetti, revisori

### 8.1 Ricevute locali

- **Chi le produce**: solo `verify` e `finish check`.
- **Ambiente**: ripulito, con le sole variabili di `[commands] env_allow`, senza `.env`, token o stringhe di connessione.
- **Cosa registrano**: SHA, comando risolto, uscita, test eseguiti e saltati, durata, log.
- **Conteggio dei test**: si legge da `report`, oppure da `report_related` per i test correlati. Il file di report si cancella prima di ogni esecuzione.
- **Stati**: `green` (uscita 0 e almeno un test), `empty` (nessun test), `uncounted` (manca il report), `flaky` (verde al secondo tentativo), `unverified` (manca il comando).
- **Nessun test correlato**: si esegue il gate completo.
- **Worktree pulito**: si controlla prima di eseguire, escludendo `output_dirs`.
- **`{files}`**: ogni nome passa per `shlex.quote`, e i file cancellati sono esclusi.

**`SubagentStop` per gli implementatori che hanno fatto commit.**
- Con `DONE` o `DONE_WITH_CONCERNS` serve una ricevuta `green` sull'ultimo commit.
- Con `BLOCKED` o `NEEDS_CONTEXT` basta una ricevuta qualunque, oppure un blocco aperto.
- Uno stato non riconosciuto vale come `DONE`.
- Dopo 2 veti si apre `needs_you` e il subagente chiude.

### 8.2 test-guard

Gira in locale al `git commit` e nel gate dentro `verdict`.

**Nei file di test** (`test_globs` più quelli dei profili attivi):
- file cancellati, riconoscendo le rinomine;
- identificativi della base che mancano nella testa. In locale si ricavano per analisi statica: `describe`/`it`/`test` in JS e TS, `def test_*` e classi `Test*` in Python, `func Test*` in Go. Nel gate vengono dal report JUnit;
- asserzioni diminuite (`assert_markers` per linguaggio, contate senza commenti e stringhe);
- marcatori di salto aggiunti, solo a parola intera:
  - JS e TS: `xit`, `xdescribe`, `xtest`, `.skip`, `.only`, `.todo`, `.fixme`, `.skipIf`, `.runIf(false)`, `.fails`;
  - Python: `pytest.skip(`, `skipif`, `xfail`, `@unittest.skip`;
  - Go: `t.Skip`;
  - Java: `@Disabled`, `@Ignore`;
  - Rust: `#[ignore]`.

**In tutto il repo:**
- soglie di copertura abbassate;
- CI modificata;
- snapshot aggiornati;
- `verification_globs`: queste modifiche non bloccano, ma richiedono una deroga `command`, valida subito e sempre visibile in `attenzione`.

**`test_globs` predefiniti:**
- `**/__tests__/**`, `**/test/**`, `**/tests/**`, `**/e2e/**`;
- `**/*_test.py`, `**/test_*.py`, `**/*.test.*`, `**/*.spec.*`;
- `**/*_test.go`, `**/src/test/**`.

### 8.3 Deroghe e blocchi

**Deroghe** (`tollgate waiver add <tipo> <file> [--test <id>] --choice --why --cost`):
- **dove**: in `.tollgate/waivers.toml` (18.2), scritte solo dalla CLI;
- **granularità**: un file per deroga; per il tipo `test` si indicano anche gli identificativi;
- **`scope` su file non sensibili**: le prime 2 valgono subito. Dalla terza serve `approve waiver` e compare `attenzione`;
- **`command`**: vale subito ed è sempre in `attenzione`;
- **`test`, `ci`, `threshold`**: restano in attesa fino ad `approve waiver`;
- **`--pattern <glob>`** (codemod): una sola deroga per molti file, sempre in attesa e in `attenzione`;
- **deroga scritta a mano da te** in una PR manuale: il gate la tratta come qualunque deroga dichiarata.

**Blocchi** (`tollgate block open <tipo> --reason`):
- portano la fase a `blocked`;
- li apre l'agente e li chiudi tu;
- se ce ne sono più di uno, la fase precedente torna solo quando si chiude l'ultimo.

### 8.4 Atti dell'utente

Li registra `UserPromptExpansion` quando digiti il comando, con `source` (`claude-code`), `actor`, oggetto e testo digitato.

| Atto | Effetto |
|---|---|
| `approve spec` | L2: la spec passa al piano (6.2) |
| `approve plan` | L2: il piano passa all'esecuzione |
| `approve waiver <id>` | La deroga diventa valida |
| `approve level <L> <motivo>` | Fissa un tetto al livello (5) |
| `approve effect <id>` | L'effetto esterno è permesso una volta |
| `approve finding <id> <motivo>` | Declassa o archivia un rilievo confermato |
| `approve rounds <n>` | Concede altri cicli di revisione (al massimo 8 in totale) e chiude il blocco del tetto. Le richieste oltre 8 sono rifiutate |
| `approve unverified-review` | Oltre gli 8 cicli, chiude la revisione come «non verificata», e lo scrive nella PR |
| `approve unverified-tests` | Permette la PR con una ricevuta `unverified` |
| `approve rebase` | Riallinea `work_base_sha` al `merge-base` |
| `approve pr` | Permette `open-pr` su questo SHA |
| `resolve <id> <nota>` | Chiude il blocco. Al tetto della revisione concede un ciclo; al tetto dell'audit lo accetta come «sospeso» |
| `sync` | 6.5 |
| `adopt #N` | 12.4 |
| `abandon #N` | Chiude il lavoro |
| `cleanup` | Cancella rami e worktree dei lavori chiusi, dopo averti mostrato l'elenco |
| `off [ore]`, `on` | Interruttore |

**Nel gate gli atti sono «dichiarati».** Le deroghe dichiarate sciolgono la violazione. `test`, `ci`, `threshold`, `command`, le deroghe per pattern e gli `scope` oltre il secondo fanno diventare rosso `attenzione`.

### 8.5 Effetti esterni

**Cosa conta come effetto esterno:**
- `[external_effects] commands`;
- un elenco predefinito: `ssh`, `scp`, `rsync`, `psql`, `docker push`, `kubectl`, `terraform apply`, `aws`, `gcloud`, `az`, `vercel`, `netlify`, `firebase deploy`, `supabase` in scrittura, `wrangler deploy`, `npm publish`;
- `project_scripts`;
- `curl` e `wget` con metodo diverso da GET o con dati;
- strumenti MCP non permessi;
- `gh` in scrittura;
- shell annidate che contengono uno di questi;
- script non tracciati nella base.

**Eccezioni in sola lettura.** `[external_effects] allow` contiene pattern di comandi che passano senza atto. La responsabilità di quell'elenco è tua.

**Come funziona:**
1. veto, con un identificativo;
2. `/tollgate:approve effect <id>`;
3. l'effetto passa una volta, per quel comando esatto;
4. il permesso diventa un intento, con chiave (comando, lavoro, SHA);
5. se lo stesso effetto si ripete sullo stesso SHA, ti avvisa con «già eseguito alle…».

**Intenti in sospeso alla ripresa.** Prima si controllano SHA e stato, poi ti viene chiesta conferma.

### 8.6 Revisori

- **Brief del revisore**: lo scrive `review prepare`, con diff, piano, must-have, SHA e un codice di controllo casuale.
- **Brief del verificatore**: lo genera dalla **tabella `findings`**, cioè da tutti i rilievi registrati.
- **Validità del verdetto**: deve contenere SHA e codice, e deve aver superato il controllo di sola lettura.
- **Formato**: `{"sha", "code", "outcome": "ok" | "needs_fix" | "needs_you", "findings": [...]}`. Un JSON assente o malformato vale `needs_you`.
- **`open-pr` rifiuta** se un rilievo registrato non ha esito, salvo quelli oltre `max_findings`.

---

## 9. Gate su GitHub

### 9.1 I workflow

| Workflow | Evento | Definizione | Codice della PR? | Permessi | Cosa fa |
|---|---|---|---|---|---|
| `tollgate-guard` | `pull_request_target` | Ramo predefinito | No: checkout solo del predefinito, oggetti della PR con `git fetch` | `contents: read`, `statuses: write` | Pubblica `tollgate/guard` e, se serve, un commento che spiega lo stato in attesa |
| `tollgate-run` | `pull_request` | Quella della PR, che `guard` impone uguale | Sì | Sola lettura, nessun segreto | `setup` e comandi del gate sulla testa; carica come artefatti solo report, uscite e conteggi; nessun filtro `paths` o `branches` |
| `tollgate-verdict` | `workflow_run` al termine di `run` | Ramo predefinito (verificato) | No: calcola da sé il diff con `git fetch` e legge gli artefatti come dati in una cartella temporanea | `contents: read`, `statuses: write`, `pull-requests: write` | Pubblica `tollgate/verdict` e `tollgate/attention`, sempre espliciti, più il commento |
| `tollgate-base` | `push` sul predefinito | Ramo predefinito | No | `contents: read` | Mette in cache, per SHA, gli identificativi dei test della base |

**Controlli di `verdict` prima di valutare.**
- `workflow_run.path` è quello atteso.
- L'evento è `pull_request`.
- Lo SHA è ancora la testa della PR, che si trova anche per SHA quando `pull_requests` è vuoto.
- La PR punta al ramo predefinito.

Se qualcosa non torna pubblica `error`. Le PR verso altri rami ricevono «non applicabile».

**Base senza cache.** Un job senza permessi di scrittura (`persist-credentials: false`) calcola gli identificativi con il codice della base.

**Artefatti.** Massimo 50 MB per file e 200 MB in totale. Sono rifiutati i percorsi con `..`, i percorsi assoluti e i file XML con `DOCTYPE` o entità. In questi casi lo stato è `error`.

**Stato in attesa.** `tollgate/verdict` lo pubblica solo `verdict`. Finché manca, la protezione blocca il merge.

### 9.2 Cosa controllano

| Controllo | Dove | Esito |
|---|---|---|
| File di tollgate uguali alla punta del predefinito | `guard` | Obbligatorio, salvo 9.4 |
| Comandi del gate (globali e dei profili attivi), da zero | `run` → `verdict` | Rosso se `red`, `empty` (senza `allow_no_tests`) o `uncounted` |
| Identificativi della base eseguiti sulla testa, salvo deroghe `test` | `verdict` | Rosso |
| test-guard sul diff, per tutte le PR | `verdict` | Rosso se manca la deroga |
| Scope: coerenza con il **piano unico** del lavoro (indicato nel JSON e presente nel primo commit del ramo che lo contiene), con gli esenti e con le deroghe. Solo per le PR dei lavori | `verdict` | Rosso. Senza piano e oltre le soglie di L0 → rosso |
| Livello dichiarato contro minimo. In L2: spec, piano e report dell'avversario sempre; report a lenti solo se le fette previste sono più di una; intestazioni valide (18.3) | `verdict` | `attenzione` rosso se manca qualcosa. Si verifica che esistano, non la loro qualità |
| Deroghe da segnalare (8.4), piano diverso dal primo, lockfile senza manifest, test della base che falliscono sulla testa, PR non `tg/*`, PR `tollgate-config/*`, periodi con tollgate spento dichiarati | `verdict` | `attenzione` rosso, non obbligatorio |

**Profili attivi** = quelli il cui `paths` tocca il diff, calcolati con la configurazione del ramo predefinito.

**Il commento.** Riporta lo SHA e non viene aggiornato se lo SHA non è più la testa. Il testo che viene dall'agente è neutralizzato: va in blocchi di codice con un recinto più lungo di qualunque sequenza di backtick contenuta, le menzioni sono disattivate e c'è una lunghezza massima.

### 9.3 Protezione del ramo

`/tollgate:init` propone il comando `gh api` completo:
- PR obbligatoria;
- controlli obbligatori `tollgate/guard` e `tollgate/verdict`, con la sorgente fissata su GitHub Actions se la protezione lo permette per gli stati di commit (16);
- `strict`;
- regole valide anche per gli amministratori;
- niente push forzato né cancellazione.

Il comando lo esegui tu. `start` legge la protezione con una GET e segnala i campi mancanti.

### 9.4 Aggiornamenti, emergenze e hotfix

**Aggiornare tollgate.** Si usa una PR da `tollgate-config/*` che contiene solo file di tollgate e `.tollgate/waivers.toml`.
- Passa `guard`.
- È esente da test-guard e scope.
- `attenzione` è sempre rosso.
- Il riepilogo mostra le chiavi che allentano il gate e l'impronta del CLI.
- L'agente non scrive i file: `init --update` prepara la proposta e tu li copi.

**Emergenza (gate guasto).** Solo tu puoi:
1. disattivare i controlli obbligatori;
2. fare il merge della riparazione;
3. riattivare i controlli.

**Hotfix urgente.** Una PR fatta a mano da un ramo non `tg/*` ottiene i controlli sui test e `attenzione` rosso. È la corsia d'emergenza dichiarata.

### 9.5 Costo

| Quando | Cosa gira |
|---|---|
| Ogni push sulla PR | `run` (`setup` + gate), poi `guard` e `verdict`, che sono brevi |
| Ogni push sul ramo predefinito | `tollgate-base` |
| Cache della base assente | La base va eseguita di nuovo |

`base_test_ids` si può spegnere.

### 9.6 Servizi

`/tollgate:init` chiede quali servizi servono ai test e li mette in `tollgate-run`. Se il gate non può girare in CI, `start` lo segnala.

---

## 10. Revisione finale

| Livello | Revisori |
|---|---|
| L0 | Nessuno |
| L1 e L2 | `final-reviewer` con la checklist dei profili attivi → `finding-verifier` sui rilievi registrati → verdetto |

**Verificatore.** Uno per ciclo. Esamina i rilievi in ordine di gravità fino a `max_findings` (15); quelli oltre il limite restano «non verificati».

**Cosa ferma la PR.** I rilievi confermati `blocker` o `major`, salvo un `approve finding`.

**Cicli di revisione.**
- Tetto di 4, contando **solo i cicli con rilievi confermati**.
- Al tetto si apre `needs_you`, che si scioglie con `approve rounds`, `approve finding` o `resolve`.
- Massimo 8 cicli; oltre serve `approve unverified-review`.
- Dopo un rebase con lo stesso `patch-id` non serve un nuovo ciclo.

La revisione finale di Superpowers si salta, come indica la skill `start`.

---

## 11. Installazione e configurazione

### 11.1 Dipendenze

- **Superpowers** con l'intervallo `>=6.4.1 <7.0.0`. Se mancano i tag di versione, la dipendenza va senza intervallo e la versione la controlla `start` leggendo il `plugin.json` di Superpowers.
- **`marketplace.json`** con l'allowlist tra marketplace.

### 11.2 `/tollgate:init`

**La proposta**, scritta in `docs/superpowers/tollgate-init/`, contiene:
- `tollgate.toml`;
- i workflow, con i servizi;
- il CLI e la sua impronta;
- il comando per la protezione del ramo;
- la configurazione consigliata di un **token GitHub separato per l'agente**: contenuti, PR e issue, senza amministrazione né `project`. Il token per C lo definirà C.

**I tuoi passi:** copi i file, li committi sul predefinito **prima** di attivare la protezione, poi lanci il comando.

### 11.3 `/tollgate:setup`

Un plugin non può impostare la statusline principale (verificato). `/tollgate:setup` ti mostra la modifica da fare a `~/.claude/settings.json`. La statusline scrive il file `ctx/<session_id>.json`. Senza statusline, o con un valore `null`, la guardia del contesto non blocca.

### 11.4 `tollgate.toml`

```toml
schema_version = 1

[project]
allow_no_tests = false

[commands]
setup          = "npm ci"
verify         = "npm run check"
test_related   = "npx vitest related --run {files}"
gate           = ["verify"]                 # nomi di chiavi di [commands] o di un profilo
report         = "junit:reports/junit.xml"
report_related = "junit:reports/junit-related.xml"
env_allow      = ["PATH", "HOME", "LANG", "CI", "NODE_ENV"]
timeout_s      = 900

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
verification_globs = ["**/vitest.config.*", "**/vite.config.*", "**/vitest.setup.*", "**/jest.config.*", "**/playwright.config.*", "**/.mocharc.*", "**/tsconfig*.json", "**/conftest.py", "**/pytest.ini", "**/tox.ini", "**/setup.cfg", "**/pyproject.toml", "**/Makefile", "**/.babelrc", "**/babel.config.*", "**/.swcrc", "**/setupTests.*", "**/.coveragerc", "**/.nycrc*", "**/cypress.config.*", "**/karma.conf.*", "**/.npmrc", "**/.env.test", "scripts/check*"]
skip_markers       = []
assert_markers     = []

[spec_audit]
spec_rounds       = 4
spec_audit_cycles = 30

[review]
readonly_agents = ["tollgate:final-reviewer", "tollgate:finding-verifier", "tollgate:plan-adversary", "tollgate:spec-adversary", "tollgate:spec-auditor"]
output_dirs     = ["reports/", "coverage/"]
max_findings    = 15
stale_minutes   = 30

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
paths          = ["**"]
setup          = ""
gate           = []
test_related   = ""
report         = ""
test_globs     = []
skip_markers   = []
assert_markers = []
plan_sections  = []
min_level      = "L0"
checklist      = ""   # percorso di un file con la checklist per il revisore finale

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
```

---

## 12. Stato locale

### 12.1 Il file

- `tollgate.db` sta nella cartella di stato, uno per macchina.
- SQLite in modalità WAL, con `synchronous=FULL` e `busy_timeout=5000`.
- A ogni cambio di fase viene fatta una copia in `backup/`; si tengono le ultime 10.

### 12.2 Tabelle

| Tabella | Colonne principali | Vincoli |
|---|---|---|
| `work_items` | id, repo_key, issue, level, level_cap (con motivo), phase, phase_before_block, branch, worktree, work_base_sha, sessions, created, updated, closed_reason | univoco (repo_key, issue) tra i lavori attivi |
| `scope` | work, path, origin, registered_at | |
| `receipts` | work, sha, command, resolved_command, exit, tests_run, tests_skipped, duration, log, produced_by, state | |
| `blocks` | work, type, reason, opened, closed, resolution | |
| `subagents` | id, type, work, agent_base_sha, fingerprint, started, ended, resumes, declared_status, state, tokens, duration | |
| `findings` | work, cycle, source, severity, file, line, text, verification, user_decision | |
| `spec_audit` | work, kind, number, viewpoint, counts, outcome, report_path | |
| `acts` | type, object, id, at, typed_text, source, actor | |
| `intents` | work, action, idempotency_key, data, state, outcome, at | univoco (idempotency_key) |
| `events` | at, session, work, type, data | sola aggiunta |
| `meta` | schema_version | |

Le deroghe non sono nel DB: stanno nel ramo, in `.tollgate/waivers.toml`.

### 12.3 Fasi

| Livello | Sequenza |
|---|---|
| L0 | `execution` → `review` (solo `finish check`) → `pr_open` → `closed` |
| L1 | `plan` → `execution` → `review` → `pr_open` → `closed` |
| L2 | `spec_audit` → `plan` → `approval` → `execution` → `review` → `pr_open` → `closed` |

**Ritorni ammessi:**
- `review` con `needs_fix` → `execution`;
- `pr_open` → `execution`, con `start` o `sync`;
- L0 che cresce → `plan`;
- da qualunque fase → `blocked`, e poi indietro alla fase precedente quando si chiude l'ultimo blocco;
- da qualunque fase → `closed`, quando viene rilevato il merge o la chiusura.

Ogni altra transizione viene rifiutata.

### 12.4 Ripresa, adozione, pulizia

**Ripresa** (`start` su un lavoro attivo):
- controlla worktree e SHA;
- accetta il worktree sporco e propone un commit di lavoro in corso;
- segna come `interrupted` i subagenti delle sessioni che non sono più vive;
- chiede conferma per gli intenti in sospeso;
- senza rete riparte con un avviso.

**Adozione** (DB perso).
- Su un ramo `tg/*` che non ha riga nel DB, gli hook negano tutto tranne i `.md` sotto `docs/superpowers/` e indicano `/tollgate:adopt #N`.
- `adopt` ricostruisce il lavoro da ramo, piano, deroghe, report e PR esistente.
- Gli intenti non si ricostruiscono: gli effetti già eseguiti risultano non eseguiti, quindi ripeterli richiede un nuovo atto.

**Pulizia.**
- `start` cancella log e file di contesto vecchi.
- `/tollgate:cleanup` cancella rami e worktree dei lavori chiusi.

**Migrazioni.** Solo in avanti, con una copia prima di ciascuna.

**Due sessioni sullo stesso lavoro.** Se un'altra sessione viva ha registrato eventi negli ultimi 10 minuti, `start` avvisa e chiede conferma.

---

## 13. Errori e casi limite

| Situazione | Comportamento |
|---|---|
| Controllo in errore, crash o timeout | Uscita 2, con il log e l'invito a `/tollgate:off` |
| `SubagentStop` in errore | Uscita 0 con avviso |
| Python o DB rotti | `/tollgate:off` funziona senza nessuno dei due |
| `OFF` dimenticato | Avviso a ogni hook; scadenza facoltativa |
| `origin/HEAD` assente | Si prova `main` e poi `master`; se manca anche quello, avviso |
| Gate o protezione assenti | `start` rifiuta, oppure avvisa |
| Versione del CLI diversa | Avviso e `init --update` |
| Effetto esterno | Veto fino all'atto, oppure eccezione in sola lettura |
| Comando di verifica assente | Ricevuta `unverified`, serve `approve unverified-tests` |
| Zero test | `empty`; il gate fallisce salvo `allow_no_tests` |
| Ramo predefinito avanzato | `/tollgate:sync` |
| Verdetto rosso dopo la PR | `start` → `execution` → `finish` |
| PR chiusa senza merge | Ti chiede cosa fare |
| Sessione persa | I subagenti diventano `interrupted` |
| DB perso | `/tollgate:adopt` |
| Codemod su molti file | Deroga per pattern |
| PR enorme | Revisione entro `max_findings`; meglio dividerla in più issue (5) |
| Hotfix urgente | Corsia d'emergenza (9.4) |
| Aggiornare tollgate, gate guasto | 9.4 |
| PR di Dependabot senza `verdict` | La gestisci tu |
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
| Gate | I casi del criterio 10 | Repo di prova privato |
| Comportamento | L'agente rispetta gli obblighi | `claude plugin eval`, 3 esecuzioni per caso |
| CI | Tutto quanto sopra | GitHub Action sul repo di tollgate |

**Casi di eval:**
1. DONE senza ricevuta → veto.
2. Conflitto tra test e specifica → `test_spec_conflict`.
3. Fuori scope → veto e deroga.
4. Deploy → veto fino all'atto.
5. L0 che cresce → L1.
6. Fine di subagent-driven-development → `/tollgate:finish`.
7. Spec con una contraddizione → trovata dall'avversario.
8. Cambio di ramo per sfuggire alle regole → veto.

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
4. **Implementatore.** Un subagente di qualunque tipo fuori da `readonly_agents`, con DONE e senza ricevuta `green` → veto; al terzo tentativo `needs_you`. Con BLOCKED e ricevuta rossa → chiude (hook).
5. **Commit.** Con `git add -A && git commit`, questi casi → `deny`:
   - test cancellato;
   - `xdescribe` o `pytest.skip(` aggiunti;
   - asserzione tolta, anche se sostituita da un commento;
   - test in `src/__tests__/` cancellato.

   `process.exit(` → nessuna segnalazione (hook, script).
6. **Comandi.**
   - Effetti esterni, `gh pr edit`, `gh api graphql` con `mutation`, script non tracciato → veto; dopo l'atto passano una volta.
   - Comando in `allow` → passa.
   - Distruttivi, `claude -p`, `TOLLGATE_STATE=…` → `deny`.
   - In un repo non attivo `git push` passa (hook).
7. **Ambito.** In un lavoro attivo: `git switch -c altro` → `deny`; push di un ramo non `tg/*` → `deny`; dopo `cd` nel checkout principale, Edit lì → `deny` (hook).
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
   - Quinto ciclo con rilievi → `needs_you`; `approve rounds 1` → un ciclo in più.
   - Ciclo senza rilievi confermati → non conta (hook, integrazione).
10. **Gate su GitHub.** Sul repo di prova:
    - **verdi**: PR pulita; PR `tollgate-config/*` (con `attenzione` rosso); PR fatta a mano da un ramo non `tg/*` (con `attenzione` rosso);
    - **`verdict` rosso**: test tolti, `skip`, file fuori scope, identificativo della base mancante;
    - **`guard` rosso**: `tollgate.toml` cambiato, workflow aggiunto fuori da `tollgate-config/*`;
    - **`attenzione` rosso**: deroga `test`, piano diverso dal primo, livello dichiarato sotto il minimo;
    - **`error`**: `../` in un artefatto, XML con entità, SHA superato;
    - **«non applicabile»**: PR verso un ramo non predefinito.

    Se la verifica di 16 conferma la sorgente per gli stati di commit: uno stato pubblicato con un token personale non soddisfa la protezione (gate).
11. **Protezione.** `start` segnala i campi mancanti di 9.3 (integrazione).
12. **PR.** Senza `/tollgate:finish` digitato e senza `approve pr` → rifiuto. Interruzione tra push e PR → nessuna PR doppia (integrazione).
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
    - Push forzato senza `sync` o `approve rebase` → `deny` (integrazione).
17. **Adozione.** Dopo aver cancellato il DB, gli hook su `tg/*` negano e indicano `adopt`. Dopo `adopt`, scope e deroghe sono ricostruiti (integrazione).
18. **Componenti.** Ogni chiave di `[components]` impostata a `false` spegne il suo modulo (script, hook).
19. **Budget.** Lo stato iniettato è al massimo 10 righe e 1.500 caratteri (hook).
20. **Rinomine.** Un file di test rinominato con gli stessi test → nessuna segnalazione (script).
21. **Deroghe.** Gli `scope` valgono subito fino al secondo; un `test` resta in attesa; una deroga per pattern resta in attesa ed è in `attenzione` (script, gate).
22. **Livelli.**
    - L0 oltre le soglie → L1 e `plan`.
    - Percorso sensibile → L2.
    - Il tetto di `approve level` resta finché il diff non tocca un percorso sensibile nuovo.
    - Livello dichiarato sotto il minimo → `attenzione` (hook, integrazione, gate).
23. **Effetti ripetuti.** Stesso effetto sullo stesso SHA → l'avviso cita l'esecuzione precedente (hook).
24. **Audit della spec.**
    - `approve spec` rifiutato se l'ultimo giro ha `blocker` o `major`; accettato dopo un giro pulito.
    - Al quarto giro con bloccanti → `needs_you`; `resolve` → «sospeso» nella PR.
    - Con «Fette previste» = 1 l'audit a lenti non parte; con 3 parte.
    - Una correzione `major` azzera il contatore del punto di vista che l'ha trovata (hook, integrazione).
25. **Fasi.** Le transizioni fuori da 12.3 vengono rifiutate (script).
26. **Da correggere.** `needs_fix` → `execution`; il `finish` successivo consuma un ciclo (integrazione).
27. **Neutralizzazione.** Una deroga con ``` e `@utente` nel testo non produce markdown attivo né menzioni (gate).
28. **Ripresa.** Worktree sporco → ripresa con proposta di commit. Interruzione dopo `finish check` → si riparte dal ciclo registrato (integrazione).
29. **Profili.** Un profilo con `paths = ["web/**"]` è attivo solo se il diff tocca `web/`, e il suo `gate` viene eseguito (script, gate).

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

**Ancora da verificare:**
- `deny` in `bypassPermissions`;
- `UserPromptExpansion` per le skill con `disable-model-invocation` e per la forma breve;
- `EnterWorktree` dentro la skill `start`;
- sorgente fissata per gli stati di commit e identificativo dell'app GitHub Actions;
- `pull_request_target` verso un ramo non predefinito;
- permessi di Dependabot per `workflow_run`;
- tag di versione di Superpowers;
- report JUnit di vitest, jest e pytest, e stabilità degli identificativi.

---

## 17. Cosa resta aperto

Sono le voci di 1.2, più due:
- i subagenti con `isolation: worktree` non vengono bloccati;
- i guardrail locali sono «best effort».

---

## 18. Formati

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
  "plan": "docs/superpowers/plans/2026-10-08-nome.md",
  "spec": null,
  "reviews_dir": null,
  "head_sha": "…",
  "receipts": [{"command": "verify", "state": "green", "tests_run": 120}],
  "waivers_file": ".tollgate/waivers.toml",
  "blocks": [],
  "acts": [{"type": "approve", "object": "waiver", "id": "w-3", "at": "…"}],
  "verdict": {"outcome": "ok", "cycles": 1, "findings_confirmed": 0},
  "fix_rounds": {"Task 2": 1},
  "effects": [{"command_hash": "…", "at": "…"}],
  "off_periods": []
}
```

### 18.2 `.tollgate/waivers.toml`

```toml
[[waiver]]
id = "w-1"
type = "scope"            # scope | test | ci | threshold | command
file = "src/util/date.ts" # oppure pattern = "src/**/*.ts" (sempre in attesa)
tests = []                # per type = "test": identificativi
choice = "…"
why = "…"
cost = "…"
declared_by = "agent"     # agent | user
```

### 18.3 Intestazione dei report

```yaml
---
kind: spec-adversarial   # spec-adversarial | spec-lens | plan-adversarial
number: 2
viewpoint: null          # per spec-lens: uno degli otto punti di vista
spec_sha: "…"
counts: {blocker: 0, major: 1, moderate: 3, minor: 2}
outcome: findings        # findings | empty | suspended
---
```

Avversari e auditor chiudono il loro messaggio finale con una riga JSON con gli stessi campi. L'hook la legge.

### 18.4 Tipi di evento

`session_start`, `act`, `phase_change`, `level_change`, `scope_registered`, `waiver_added`, `block_opened`, `block_closed`, `commit`, `receipt`, `subagent_start`, `subagent_stop`, `veto`, `effect_requested`, `effect_executed`, `review_cycle`, `pr_opened`, `pr_updated`, `merge_detected`, `off`, `on`.

---

## 19. Codici di riferimento

| Codice | Significato |
|---|---|
| R1 | Via d'uscita «test e specifica in conflitto» |
| R2 | Test correlati nel contesto dell'implementatore |
| R3 | La ricevuta non basta: il revisore cerca test indeboliti e casi speciali |
| R4 | Giri di correzione contati e riportati |
| R5 | Promemoria del passo del piano |
| R6 | Controllo della struttura del piano |
| R7 | Soglie del contesto e ritorni brevi dei subagenti |
| R8, R11, R12 | Regole dei profili via hook; esistenza dei pacchetti; analisi statica (B) |
| R9 | Budget delle istruzioni iniettate |
| R10 | Componenti spegnibili |
| R13 | Decisioni dell'utente sui rilievi (C) |
| R15 | Costo dei subagenti (D) |
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
