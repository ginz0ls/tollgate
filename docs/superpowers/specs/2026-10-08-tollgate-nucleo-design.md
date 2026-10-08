# tollgate: specifica del nucleo (sotto-progetto A)

Data: 8 ottobre 2026.
Revisione: **4** (correzioni dell'audit, vedi la sezione 17).
Stato: **in audit** (`docs/audit/2026-10-08-audit-spec-nucleo-stato.md`).
Fonti: `docs/REPORT-CONFRONTO-WORKFLOW.md`, `docs/COSA-TENERE.md` (voci 1-42, H1-H45, R1-R16, sezione 9), `docs/RICERCA-PAPER.md`.

---

## 0. Glossario

| Termine | Significato |
|---|---|
| **lavoro** | Un'issue, oppure una fetta di un'issue. È una riga della tabella `work_items` |
| **task del piano** | Un task di un piano di Superpowers (`### Task N`), eseguito da un implementatore |
| **base del lavoro** | Lo SHA da cui parte il ramo del lavoro (`work_base_sha`) |
| **base del subagente** | Lo SHA di quando un subagente è partito (`agent_base_sha`) |
| **scope** | L'insieme dei file che il piano della fetta autorizza a creare o modificare, più le deroghe |
| **chiave del repo** | URL remoto `origin` normalizzato. Se manca, la radice comune di git (`git rev-parse --git-common-dir`) |
| **cartella di stato** | `${TOLLGATE_STATE:-~/.local/state/tollgate}`. Contiene DB, log, file del contesto e interruttore |
| **repo attivo** | Un repo che ha `tollgate.toml` sulla punta del ramo base. **Negli altri repo tollgate non fa niente** |
| **atto dell'utente** | Un'operazione registrata dall'hook `UserPromptExpansion` quando l'utente digita un comando `/tollgate:*` |

---

## 1. Scopo

tollgate è un plugin per Claude Code. Porta un lavoro **da un'issue GitHub a una PR verificata**; il merge lo fa sempre una persona, su GitHub.

Il flusso di lavoro resta quello di **Superpowers**: brainstorming → writing-plans → subagent-driven-development. tollgate aggiunge solo quello che manca e **sostituisce un unico passo**, la chiusura del ramo (`finishing-a-development-branch`), che diventa `/tollgate:finish` (6.3).

**Cosa aggiunge.**
1. **Obblighi imposti da codice**, non chiesti nel prompt:
   - niente «fatto» senza ricevute;
   - i test non si possono indebolire **in modo strutturale**: file cancellati, casi in meno, asserzioni in meno, `skip` e `only` aggiunti, soglie abbassate, CI o configurazione dei test modificate. Gli indebolimenti dentro le asserzioni li cerca il revisore finale (R3), perché nessun controllo strutturale li vede;
   - effetti esterni solo con conferma;
   - modifiche limitate ai file del piano.
2. **Livelli di rigore** (L0, L1, L2) scelti da uno script in base al rischio della modifica.
3. **Contesto pulito per ogni attività**, così il contesto non si degrada nelle sessioni lunghe.
4. **Prove prodotte dagli script**, mai dichiarate dal modello.

**Limiti strutturali, dichiarati.**
- Gli hook di Claude Code vedono le chiamate agli strumenti, **non i processi figli** (verificato, 8.4).
- Un hook blocca solo uscendo con codice 2; un crash o un timeout lasciano passare (verificato, sezione 7).
- Un modello con accesso a Bash può in teoria importare il codice di tollgate e scrivere nel DB.

Per questo ogni obbligo ha **due livelli di controllo**:
- **un controllo anticipato negli hook**, «best effort», che ferma gli errori onesti e la maggior parte dei tentativi;
- **un controllo autorevole sul risultato**, a `git commit` e a `finish`: diff dalla base, eventi, rilancio dei comandi (8.4). Non dipende da quello che gli hook hanno visto.

**Quando il nucleo funziona.** Lo stabiliscono i criteri della sezione 14, ciascuno con il suo test.

### 1.1 Fuori dal nucleo

| Cosa | Dove |
|---|---|
| Profili per tipo di file (frontend, backend in 3 varianti, database, sicurezza, AI/LLM, bugfix) con i loro controlli; caricamento delle regole tramite hook (R8); controllo dell'esistenza dei pacchetti (R11); analisi statica nel profilo sicurezza (R12) | Sotto-progetto **B** |
| Sotto-issue e dipendenze su GitHub Projects, presa in carico tra macchine (su GitHub, non nel DB locale), riconciliazione automatica, registrazione delle tue decisioni sui rilievi (R13) | Sotto-progetto **C** |
| Suite di eval completa con confronti e prove a componenti spenti, costo dei subagenti (R15), misura del contesto dei subagenti | Sotto-progetto **D** |
| Dashboard locale, avvio automatico da etichetta GitHub, portabilità verso altri harness, lezioni apprese, mutation testing | Dopo la v1 |

**Agganci già pronti per i sotto-progetti successivi.**
- Nel DB: colonne `lease_*` (presa in carico **solo locale**) e `decisione_utente`, tabella `slices`, tabella `events`.
- In `tollgate.toml`: la sezione `[profiles]` e la sezione `[components]`, che è una **mappa aperta** (B potrà aggiungere chiavi).
- Variabili d'ambiente `TOLLGATE_STATE` e `TOLLGATE_CONFIG` per DB e configurazione temporanei, che servono agli eval di D.

---

## 2. Decisioni prese

| Tema | Decisione |
|---|---|
| Harness | Claude Code |
| Tracker | GitHub Issues, tramite `gh` |
| Autonomia | Interattiva. L'avvio automatico viene dopo |
| Flusso | Superpowers `>=6.4.1 <7.0.0`, dichiarato come dipendenza. Un cambio di versione maggiore va verificato a mano sul formato del registro di subagent-driven-development. `finishing-a-development-branch` è sostituito da `/tollgate:finish` |
| Struttura | Hook e script. Le skill gestiscono le parti che richiedono il modello; i passi deterministici li esegue `bin/tollgate` |
| Stato | SQLite locale nella cartella di stato. Ci scrive solo il codice di tollgate (CLI e hook) |
| Pianificatore | Il coordinatore, cioè la sessione principale, che può fare domande |
| Revisione | Revisore finale e verificatore scritti da tollgate; in L2 specialisti esterni, se installati (sezione 9) |
| Merge | Solo l'utente, su GitHub. L'agente non fa mai merge, neanche con conferma |
| Livello | Lo script lo può solo alzare. Lo può abbassare **solo l'utente**, con un atto registrato e un motivo |
| Pubblicazione | Privato ora, pubblico poi. Nel codice niente percorsi né nomi di progetti dell'utente |
| Lingua | Nomi in inglese per plugin, comandi, script e file; documentazione in italiano |
| Sistemi | Linux e macOS (il wrapper degli hook è uno script shell). Windows fuori dalla v1 |
| Requisiti del repo | Remote GitHub e `gh` autenticato |

---

## 3. Struttura del plugin

```
tollgate/
  .claude-plugin/plugin.json        dependencies: superpowers (intervallo di versioni)
  .claude-plugin/marketplace.json   allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]
  skills/
    start/SKILL.md      /tollgate:start #N                          anche il modello
    finish/SKILL.md     /tollgate:finish                            anche il modello
    status/SKILL.md     /tollgate:status   stato e atti in sospeso  anche il modello (sola lettura)
    init/SKILL.md       /tollgate:init       propone tollgate.toml  anche il modello (solo proposta)
    approve/SKILL.md    /tollgate:approve <oggetto> <id> [motivo]   solo l'utente
    resolve/SKILL.md    /tollgate:resolve <id> <nota>               solo l'utente
    setup/SKILL.md      /tollgate:setup      configura la statusline solo l'utente
    off/ on/            /tollgate:off, /tollgate:on                 solo l'utente
  agents/
    final-reviewer.md     revisore finale            tools: Read, Grep, Glob, Bash
    finding-verifier.md   verificatore per rilievo   tools: Read, Grep, Glob, Bash
    plan-adversary.md     avversario del piano (L2)  tools: Read, Grep, Glob
    specialist-runner.md  esegue uno specialista che è una skill (es. security-review)
  hooks/hooks.json      tutti gli hook (gli agenti dei plugin non possono averne)
  hooks/run             wrapper shell degli hook (7.1)
  bin/tollgate          CLI Python, solo libreria standard
  statusline/statusline.sh  statusline dell'utente, più la scrittura della % di contesto
  templates/tollgate.toml
  tests/  evals/
```

«Solo l'utente» vuol dire `disable-model-invocation: true`, più la registrazione tramite `UserPromptExpansion` (7.2).

**Chi può chiamare quali sottocomandi di `bin/tollgate`.**

| Chi | Sottocomandi |
|---|---|
| **L'agente**, via Bash | `verify`, `waiver add`, `block open`, `status`, `init --propose`, `finish check`, `finish open-pr` |
| **Solo gli hook** | `hook <evento>` |
| **Solo gli atti dell'utente** | approvazioni, risoluzioni, abbassamento del livello, interruttore. Li scrive l'hook `UserPromptExpansion`, e il CLI non ha sottocomandi per farlo |

Non esiste nessun sottocomando per scrivere una ricevuta, cambiare fase o registrare un verdetto. Sono funzioni interne.

L'hook Bash nega `tollgate hook …` chiamato dall'agente. Il limite: un modello può comunque importare il modulo Python. Lo copre il controllo autorevole: `finish check` riesegue tutto (8.4).

**Principi di design.**
- **Accesso al DB.** Solo il codice di tollgate apre il DB.
- **Hook uniformi.** Ogni hook passa da `hooks/run`, che chiama `bin/tollgate hook <evento>` con l'input JSON di Claude Code su stdin.
- **Componenti spegnibili.** Ogni componente si spegne da `tollgate.toml` (R10).
- **Configurazione letta dalla base.** `tollgate.toml` si legge dal commit `work_base_sha` (`git show`), mai dal working tree. `TOLLGATE_CONFIG` la sovrascrive solo nei test e negli eval.
- **Ordine di preferenza.** Prima si estende quello che esiste, poi CLI e skill, solo alla fine nuovi strumenti (H44).

---

## 4. Ruoli

| Ruolo | Chi è | Cosa fa | Come è imposto |
|---|---|---|---|
| Utente | — | Conferma il livello, approva spec e piano in L2, approva deroghe oltre il tetto, risolve blocchi, abbassa il livello, fa il merge | Atti registrati da `UserPromptExpansion` |
| Coordinatore | La sessione principale | Dialogo, brainstorming, spec, **piano**. Lancia i subagenti e legge solo verdetti e percorsi. **Non scrive codice**, tranne in L0 | In L1 e L2, fase `esecuzione`: Edit e Write sul codice negati se manca `agent_id` (cioè se a scrivere è la sessione principale) |
| Implementatore | Subagente nuovo per ogni task del piano (quello di Superpowers) | Scrive il codice di **un** task del piano e fa il commit. È l'unico che scrive codice, **uno alla volta** | Scope, un solo scrittore, regola di `SubagentStop` |
| Revisore del task | Subagente di Superpowers | Controlla il task rispetto al piano | Se fa commit, valgono le regole dell'implementatore |
| Avversario del piano | `tollgate:plan-adversary`, solo L2 | Attacca il piano; riceve piano e spec senza le motivazioni dell'autore | Senza strumenti di scrittura né Bash |
| Revisore finale | `tollgate:final-reviewer` | Rivede la fetta rispetto a piano, must-have e scope; cerca casi speciali scritti per i test e asserzioni indebolite (R3) | Controllo di sola lettura (7.3) |
| Verificatore | `tollgate:finding-verifier` | Per ogni rilievo: lo conferma con prove (file, riga, motivo) oppure lo scarta | Controllo di sola lettura (7.3) |
| Script | `bin/tollgate` | Producono i fatti: ricevute, controllo dei test, livello, scope, fasi, PR | — |

**Come si passa il lavoro.** Ogni subagente riceve un **brief su file** e restituisce un **report su file**. Al coordinatore torna al massimo un verdetto di 1-2K token più il percorso del report (R7).

**I verdetti non passano dal coordinatore.** L'hook `SubagentStop` legge i verdetti di `tollgate:final-reviewer` e `tollgate:finding-verifier` dall'ultimo messaggio del subagente (`last_assistant_message`) e li registra lui.

---

## 5. Livelli

Il livello lo calcola `bin/tollgate`.

| Livello | Quando | Percorso |
|---|---|---|
| **L0** | Al massimo `l0_max_files` file (predefinito 2) e `l0_max_lines` righe (predefinito 50) nel diff dalla base del lavoro, nessun percorso sensibile | Implementazione diretta nella sessione, `verify`, `finish`. Niente brainstorming né piano |
| **L1** | Il caso normale | writing-plans → controllo della struttura del piano → esecuzione per task del piano → revisione finale |
| **L2** | Percorsi sensibili, etichette sensibili, oppure tua scelta | brainstorming → spec → piano principale se serve più di una fetta → piano della fetta → avversario → tua approvazione → esecuzione → revisione finale con specialisti |

**Come si stima e come cambia.**
- **All'avvio**: il livello si stima da etichette e testo dell'issue; tu confermi o alzi.
- **Durante il lavoro**: si ricalcola sul diff dalla base del lavoro dopo ogni Edit o Write (`PostToolUse`), a ogni `git commit` e a `finish`.
  - superate le soglie di L0 → il livello sale a L1 e **la fase torna `piano`**. Il codice resta bloccato finché un piano non è registrato; i documenti sotto `docs/superpowers/` restano scrivibili;
  - toccato un percorso sensibile → il livello sale a L2.
- **Abbassarlo**: lo script non lo abbassa mai. Puoi farlo solo tu, con `/tollgate:approve level <L> <motivo>`, che viene registrato e finisce nella PR. Serve per i falsi positivi, come `docs/auth/README.md` che corrisponde a `**/auth/**`.
- **Il controllo autorevole** è quello sul diff a commit e a `finish`, perché vede anche le modifiche fatte via Bash.

**Piano principale** (si crea solo se il lavoro non sta in una fetta):
- `plan-check` lo riconosce dall'intestazione `# Piano principale` e registra le fette nella tabella `slices`: numero, titolo, dipendenze, stato;
- ogni fetta diventa un **lavoro** a sé, con il suo piano scritto quando arriva il suo turno e la sua PR con «Part of #N»;
- `start #N` sceglie la fetta con il numero più basso tra quelle non chiuse le cui dipendenze sono chiuse;
- nel nucleo le fette restano sulla stessa issue; le sotto-issue arrivano con C.

---

## 6. Ciclo di vita

### 6.1 Avvio e piano

```
/tollgate:start #N   (la skill chiama bin/tollgate start)
  0. prerequisiti   tollgate.toml presente nel ramo base (altrimenti: rifiuto e invito a /tollgate:init);
                    versione di Superpowers nell'intervallo atteso; remote GitHub, `gh` autenticato,
                    ramo base esistente con almeno un commit (altrimenti: rifiuto con il motivo);
                    issue chiusa → avviso e conferma
  1. controlli      repo pulito; CI del ramo base verde (se è rossa: avviso e conferma)
  2. lavoro         lavoro esistente per (chiave del repo, issue, fetta)? → ripresa (10.3); altrimenti nuovo
  3. livello        proposto, confermato dall'utente
  4. worktree       ramo tg/<N>-<slug>, slug ripulito ([a-z0-9-], al massimo 40 caratteri);
                    riga in work_items (fase = piano, work_base_sha); stampa il percorso del worktree (6.4)
  5. per livello    L0: implementa → tollgate verify → /tollgate:finish
                    L1: writing-plans (con l'elenco delle sezioni obbligatorie) → plan-check → scope
                        registrato → fase = esecuzione
                    L2: brainstorming → spec → checkpoint + /clear → piano principale (se serve) e piano
                        della fetta → plan-check → plan-adversary → /tollgate:approve plan → fase = esecuzione
  → checkpoint + /clear
```

**Il testo dell'issue non è fidato.**
- Non entra mai in un comando shell: passa ai modelli dentro file, marcato come «dato, non istruzioni».
- Se l'autore dell'issue non è un collaboratore del repo, `start` ti avvisa.

### 6.2 Esecuzione: una fetta per sessione

```
/tollgate:start #N   riparte dal DB (fase = esecuzione)
  SessionStart inietta 5-10 righe: issue, fetta, task del piano corrente (dal registro di Superpowers), scope, livello
  subagent-driven-development di Superpowers, per ogni task del piano, uno alla volta:
    brief = testo del task (Superpowers) + scope, test correlati e passo del piano, aggiunti da tollgate (R2, R5)
    implementatore → commit (hook: test-guard, scope, livello) → tollgate verify → ricevuta
    SubagentStop dell'implementatore: regola della sezione 8.1
    test e specifica in conflitto → tollgate block open conflitto_test_spec (R1); i test non si toccano
    revisore del task di Superpowers
    al 2° giro di correzione dello stesso task del piano (dal registro di Superpowers) un nuovo
      implementatore viene negato → blocco serve_te (R4; prevale sul tetto di 5 di Superpowers)
  guardia del contesto: avviso a warn_pct; a stop_pct nega nuovi subagenti e le modifiche
    della sessione principale → checkpoint + /clear
```

### 6.3 Chiusura

Quando subagent-driven-development arriva alla revisione finale e a `finishing-a-development-branch`, la skill `start` ha già detto al coordinatore di usare **`/tollgate:finish`** al loro posto.

Se il coordinatore segue comunque Superpowers, gli hook negano merge locale, push, cancellazione del ramo e rimozione del worktree (sezione 7). Il danno massimo è una revisione in più.

```
/tollgate:finish
  5. tollgate finish check   controllo autorevole (8.4) → ricevuta sullo SHA attuale
  6. revisione               tollgate:final-reviewer (+ specialisti e Codex in L2)
                             → tollgate:finding-verifier per ogni rilievo
                             → i verdetti li registra l'hook SubagentStop
                             al massimo 4 giri di revisione finale di tollgate, poi serve_te
  7. tollgate finish open-pr verifica nel DB che 5 e 6 siano passati sullo stesso SHA e che non ci siano
                             blocchi o approvazioni in sospeso;
                             intento salvato → push → ls-remote → cerca una PR esistente → crea la PR
                             descrizione: livello (ed eventuale abbassamento), ricevute, deroghe, blocchi,
                             verdetto, commit fuori controllo, effetti esterni confermati;
                             in coda un blocco JSON in un commento HTML, leggibile da C e dalla dashboard
  8. merge                   lo fa l'utente su GitHub; la fetta successiva parte in una sessione nuova
```

### 6.4 Dove lavora la sessione

- La sessione di esecuzione **deve avere il worktree come directory di lavoro**. Ci entra in uno di due modi:
  - aprendo Claude Code nel worktree (`cd <percorso> && claude`), anche dopo un `/clear`;
  - usando lo strumento nativo per entrare nel worktree, se è adatto (sezione 15).
- Il lavoro attivo si ricava dal ramo `tg/<N>-*` della directory di lavoro, non dal `session_id`, che cambia a ogni `/clear`.
- `git worktree add` mentre esiste già un worktree per lo stesso lavoro viene negato, con il percorso esistente. Così using-git-worktrees di Superpowers non ne crea un secondo.
- **Dove valgono le regole.**
  - In un repo che non è attivo, tollgate non fa niente: il plugin è installato per tutti i progetti e non deve disturbare gli altri.
  - In un repo attivo ma fuori dai rami `tg/*` valgono solo i comandi distruttivi e la protezione dei file di tollgate (configurazione, cartella di stato, file del plugin). La configurazione si legge dalla punta del ramo base.
  - Push, merge, PR, scope, livelli ed effetti esterni sono regolati **solo sui rami `tg/*`**, più i merge verso la base fatti da un ramo `tg/*`.

---

## 7. Hook

### 7.1 Come girano gli hook

Tutti gli hook stanno in `hooks/hooks.json`, sono di tipo `command` e passano dal wrapper `hooks/run`.

**Il problema da risolvere.** Secondo la documentazione solo l'uscita con codice 2 blocca. Con codice 1, con un crash o con un timeout, l'azione prosegue (verificato su code.claude.com/docs/en/hooks.md, 08/10/2026).

**Cosa fa il wrapper:**
1. Se esiste il file `OFF` nella cartella di stato, esce con 0 senza fare altro: è l'interruttore, e funziona anche quando Python o il DB sono rotti.
2. Esegue `bin/tollgate hook <evento>` con una scadenza interna (predefinito 20 s, comunque sotto il `timeout` dichiarato in `hooks.json`).
3. Per gli **hook di controllo**: qualunque esito diverso da 0 o 2 (eccezione, codice 127, scadenza) diventa **uscita 2**, con il messaggio «tollgate: errore interno», il percorso del log e l'indicazione di `/tollgate:off`.
4. Per gli **hook informativi**: un errore diventa uscita 0.

Ogni hook scrive un evento in `events`.

### 7.2 Tabella degli hook

| Evento | Filtro | Comportamento | Voci |
|---|---|---|---|
| `SessionStart` | `startup`, `resume`, `clear`, `compact`, `fork` | Informativo. Con un lavoro attivo inietta al massimo 10 righe e 1.500 caratteri di stato (budget R9); senza lavoro attivo non aggiunge niente | 41, R5, R9 |
| `UserPromptExpansion` | comandi `/tollgate:approve`, `/tollgate:resolve`, `/tollgate:off`, `/tollgate:on`, `/tollgate:setup` | Registra l'**atto dell'utente**: approvazione, risoluzione, abbassamento del livello, interruttore (file `OFF`, scritto direttamente dal wrapper senza Python), configurazione della statusline. Il modello non può generarlo, perché scatta solo quando digiti tu il comando | 14, R1 |
| `PreToolUse` | `Edit`, `Write`, `NotebookEdit` (`MultiEdit` se presente) | **Fasi `piano` e `approvazione`**: solo i file `.md` sotto `docs/superpowers/`. **Fase `esecuzione`**: file fuori scope → `deny` con l'istruzione per la deroga; in L1 e L2, scrittura sul codice da parte della sessione principale (senza `agent_id`) → `deny`; file protetti → sempre `deny`. **Sempre permessi**: i file `.md` sotto `docs/superpowers/`, i file sotto `.superpowers/` (che però, se finiscono in un commit, a `finish` contano come fuori scope) e i file in `[scope] always` alle condizioni della sezione 11. **In L0** lo scope non si applica: vale il livello | 5, H24 |
| `PostToolUse` | `Edit`, `Write`, `MultiEdit` | Ricalcola il livello sul diff. Se il file è un piano (`docs/superpowers/plans/*.md`), esegue `plan-check`: se manca qualcosa → `decision: block` con l'elenco (il file resta scritto ma il piano non viene registrato); se è completo registra scope e fette | 13, R6 |
| `PreToolUse` | `Bash` | Tabella 7.4 | 6, 10 |
| `PreToolUse` | `mcp__.*` | Strumenti MCP che non sono in `[external_effects] mcp_allow` → `ask`. Si possono permettere solo gli strumenti in sola lettura | 6 |
| `PreToolUse` | `Agent` | `context-guard`: a `stop_pct` → `deny`. **Un solo scrittore**: un nuovo `general-purpose` viene negato se un altro `general-purpose` è attivo nello stesso worktree; i subagenti `tollgate:*` e quelli in `[review] parallel_ok` possono lavorare in parallelo. **R4**: dopo il 2° giro di correzione dello stesso task del piano un nuovo implementatore viene negato | 42, R4, R7 |
| `SubagentStart` | tutti | Salva `agent_base_sha`, l'impronta di `git status`, il tipo e l'ora | 8 |
| `SubagentStop` | tutti | Implementatori: 8.1. Subagenti di sola lettura: 7.3. Verdetti di `tollgate:final-reviewer` e `tollgate:finding-verifier`: lettura e registrazione | 8, H36 |

**`Stop` della sessione principale: nessun blocco.** Il gate è `finish`.

### 7.3 Controllo di sola lettura

Per `tollgate:*`, per gli specialisti e per i subagenti in `[review] parallel_ok`, `SubagentStop` confronta l'ultimo commit e l'impronta di `git status` con quelli registrati alla partenza.
- Se sono cambiati, il verdetto del subagente non vale e si apre un blocco `serve_te`: «un revisore ha modificato il worktree».
- È lo stesso principio del ricontrollo dello SHA prima della PR in codex-workflow.

### 7.4 Regole su Bash

Valgono solo nei repo attivi, con l'ambito della sezione 6.4. Sono «best effort»: il controllo autorevole è quello della sezione 8.4.

| Comando | Decisione |
|---|---|
| Su un ramo `tg/*`: `git push`, `gh pr create`, `gh pr merge`. Ovunque: `git merge` di un ramo `tg/*` verso il ramo base, `git branch -d/-D` di un ramo `tg/*`, `git worktree remove` del worktree di un lavoro, `git worktree add` per un lavoro che ha già un worktree | `deny` |
| Distruttivi: `push --force`, `reset --hard`, `--no-verify`, `rm -rf` fuori dal worktree | `deny` |
| Che disattivano o alterano tollgate: `claude plugin disable/uninstall`; scrittura (`sed -i`, `>`, `>>`, `tee`, `cp`, `mv`, `sqlite3`) su impostazioni di Claude Code, `tollgate.toml`, cartella di stato o file del plugin | `deny` |
| `tollgate hook …` | `deny` |
| Effetti esterni: comandi in `[external_effects] commands`; script in `project_scripts`; `curl` e `wget` con metodo diverso da GET o con dati; `gh api` con metodo diverso da GET; `bash -c`, `sh -c`, `eval`, `python -c` che contengono uno dei comandi elencati | `ask`, con registrazione dell'effetto (8.5) |
| `git commit` (con o senza `-a`, anche dopo `git add` nella stessa riga) | test-guard, scope e livello sul **working tree più l'indice** rispetto alla base del lavoro; `deny` se mancano deroghe |

### 7.5 Sezioni obbligatorie del piano

`plan-check` controlla queste sezioni:
- Fatti verificati (fatto / dove / conseguenza, su uno SHA);
- Decisioni (scelta / perché / costo se sbagliata);
- Interfacce;
- Must-have;
- Scope, ricavato da `Create:`, `Modify:` e `Test:` di ogni task. Il parser toglie gli intervalli di righe (`file.py:123-145` diventa `file.py`);
- Punti di arresto;
- Rischi.

Il piano principale ha in più l'elenco delle fette con le loro dipendenze. Le sezioni sono configurabili. Il formato dei task resta quello di Superpowers.

La skill `start`, quando passa a writing-plans, dà al coordinatore l'elenco di queste sezioni, così il piano non viene rimandato indietro al primo tentativo.

---

## 8. Ricevute, test-guard, deroghe, effetti esterni e controllo autorevole

### 8.1 Ricevute

- **Chi le produce**: solo `tollgate verify` e `tollgate finish check`, che eseguono i comandi di `tollgate.toml`. Durante il lavoro `verify` esegue `test_related` sui file del diff rispetto alla base del lavoro; `finish check` esegue i comandi del gate (8.4).
- **Cosa registrano**:
  - SHA e worktree pulito;
  - **il comando risolto**: per `npm run x` il testo dello script preso da `package.json` in quello SHA;
  - codice d'uscita e durata;
  - **numero di test eseguiti e saltati**, letto dal reporter JSON o JUnit configurato in `[commands] report`;
  - percorso del log.
- **Quando una ricevuta è verde**:
  - codice d'uscita 0 **e almeno un test eseguito**;
  - con zero test eseguiti la ricevuta è «vuota», mai verde;
  - se il reporter non è configurato, la ricevuta è «senza conteggio» e lo dice la PR.
- **Nel contesto**: solo l'esito più le ultime righe.
- **Worktree pulito**:
  - si controlla **prima** di eseguire, su file tracciati e su file non tracciati che non sono ignorati;
  - i file prodotti dai test durante l'esecuzione non invalidano la ricevuta.
- **Quando sono valide**: SHA uguale all'ultimo commit.
- **Test instabili**: un solo nuovo tentativo; se al secondo passa, la ricevuta è segnata «instabile».
- **Comando mancante**: la ricevuta dice «non verificato», mai «passato».

**Regola di `SubagentStop` per gli implementatori** (subagenti `general-purpose` che hanno fatto commit dopo la base del subagente):
- se l'ultimo messaggio dichiara `DONE` o `DONE_WITH_CONCERNS` (stati di Superpowers), serve una **ricevuta verde** sull'ultimo commit;
- se l'ultimo messaggio dichiara `BLOCKED` o `NEEDS_CONTEXT`, basta **una ricevuta di qualunque esito oppure un blocco aperto**, anche con il worktree sporco;
- se lo stato dichiarato non si riconosce, vale come `DONE`;
- se la condizione non è soddisfatta → `block` con il motivo;
- il contatore dei blocchi è nel DB (`subagents.blocchi`), indipendente da `stop_hook_active`: dopo 2 blocchi si apre un blocco `serve_te` e il subagente può chiudere;
- i subagenti senza commit non vengono toccati.

### 8.2 test-guard

Confronta il diff con la base del lavoro e segnala, **solo nei file di test** (`test_globs`, esclusi `fixture_globs`):
- file di test cancellati (con rilevamento delle rinomine: un file rinominato non è cancellato);
- casi di test diminuiti, contati **per nome del test** in tutto il repo: un test spostato o rinominato di file non conta come tolto;
- asserzioni diminuite (`assert_markers`);
- `skip` e `only` aggiunti, cercati come parole intere (`\bxit\(`, `\.skip\(`), così `exit(` non scatta.

E segnala in tutto il repo:
- soglie di copertura abbassate;
- file della CI modificati (`ci_globs`);
- **file che definiscono come girano i test** modificati (`command_files`: `package.json` per la sola parte `scripts`, configurazioni di vitest, jest, pytest, tox, `pyproject.toml` per le sezioni dei test);
- snapshot o baseline visive aggiornati.

I pattern sono in `tollgate.toml`, con valori predefiniti per JavaScript, TypeScript e Python. Ogni modifica segnalata richiede una deroga che nomina il file.

### 8.3 Deroghe e blocchi

**Deroghe** (`tollgate waiver add <tipo> <file> --scelta --perche --costo`):
- tipi: `scope`, `test`, `ci`, `soglia`, `comando`;
- **un file per deroga**: niente glob e niente cartelle;
- **tetto**: le prime 2 per fetta valgono subito; dalla terza la deroga resta «in attesa» finché non dai `/tollgate:approve waiver <id>`;
- le deroghe di tipo `comando` (modifiche a `command_files`) restano **sempre** in attesa della tua approvazione, perché cambiano il significato delle ricevute;
- **dove compaiono**: tutte nella PR.

**Blocchi tipizzati** (`tollgate block open <tipo> --motivo`): `serve_te`, `conflitto_test_spec`, `dipendenza`, `permesso`, `transitorio`.
- un blocco porta il lavoro in fase `bloccato`;
- lo chiudi tu con `/tollgate:resolve <id> <nota>`, e il lavoro torna alla fase precedente;
- `conflitto_test_spec` è la via d'uscita prevista quando un test contraddice la specifica (R1): **l'agente non modifica il test**, si ferma e ti chiede.

### 8.4 Controllo autorevole sul risultato

`tollgate finish check` non si fida di quello che gli hook hanno o non hanno visto, e ricontrolla tutto sul **diff dalla base del lavoro**:
1. **scope**: ogni file modificato è nello scope, in `[scope] always`, oppure ha una deroga valida;
2. **test-guard**: sul diff completo;
3. **livello**: ricalcolato, perché può essere salito;
4. **`tollgate.toml`**: invariato rispetto alla base; se è cambiato si blocca;
5. **comandi**: il comando risolto di ogni comando del gate coincide con quello della base, oppure c'è una deroga `comando` approvata;
6. **prova di presenza**: ogni commit tra la base e l'ultimo commit ha un evento `git commit` registrato dall'hook. I commit senza evento sono «commit fuori controllo»: vengono elencati e la PR si apre solo dopo `/tollgate:approve presence <sha>`;
7. **atti in sospeso**: nessuna deroga o approvazione in attesa, nessun blocco aperto;
8. **ricevute**: riesegue i comandi del gate (`[commands] gate`, predefinito `["verify"]`, più i comandi `gate` dei profili attivi) e usa solo le ricevute che produce lui stesso. Il conteggio dei test si legge dal reporter di quei comandi.

### 8.5 Effetti esterni

- Ogni effetto esterno a cui rispondi sì (`ask`) viene registrato come **intento con esito** e con una chiave di idempotenza: comando, lavoro e SHA.
- Se lo stesso effetto si ripresenta sullo stesso SHA, l'hook lo segnala nella richiesta di conferma: «già eseguito alle 10:42».
- **Ripresa degli intenti in sospeso** (`push`, `crea PR`): `start` non li completa da solo. Prima ricontrolla SHA e stato, poi ti chiede conferma.

---

## 9. Revisione finale

| Livello | Revisori | Poi |
|---|---|---|
| L0 | Nessun agente | Ricevute e merge tuo |
| L1 | `tollgate:final-reviewer` con la checklist dei profili attivi (nel nucleo: solo il profilo base) | `tollgate:finding-verifier` → verdetto |
| L2 | `tollgate:final-reviewer` + al massimo 3 specialisti scelti in base ai profili attivi, **ognuno in un subagente con il suo contesto**, se installati: `pr-review-toolkit:pr-test-analyzer`, `pr-review-toolkit:silent-failure-hunter`, `security-review` eseguito da `tollgate:specialist-runner`. Codex come parere, se installato (R16) | `tollgate:finding-verifier` → verdetto |

**Codex.** Si invoca tramite `tollgate:specialist-runner`, con il comando di revisione documentato di codex-plugin-cc (da verificare, sezione 15). Il suo parere passa dal verificatore come quello di ogni altro revisore.

**Specialisti non installati.** Gli specialisti esterni **non sono dipendenze**: `pr-review-toolkit` non ha una versione semver da fissare. Se mancano, la PR dice quali specialisti sono stati saltati.

**Il verificatore.** C'è **un solo subagente verificatore per giro di revisione**. Controlla ogni rilievo separatamente, con le sue prove, e li tratta in ordine di gravità fino a `max_findings` (predefinito 15). I rilievi oltre il tetto vengono elencati come «non verificati» e non fermano la PR, ma li trovi nella PR.

**La revisione finale di Superpowers.** subagent-driven-development fa già una revisione finale dell'intero ramo. La skill `start` indica al coordinatore di saltarla e andare a `/tollgate:finish`. Se la fa comunque, il costo raddoppia ma non si perde nessun controllo. Il costo si misura in D.

**Verdetto.**
- Una riga JSON: `{"esito": "ok" | "da_correggere" | "serve_te", "rilievi": [{gravita, file, riga, testo, verificato}]}`.
- **Gravità**: `bloccante`, `grave`, `rilevante`, `minore`, con le definizioni del progetto in `tollgate.toml`.
- **JSON assente o malformato**: conta come esito `serve_te`, mai come «ok».
- **Tetto di 4 giri** della revisione finale di tollgate: il contatore non si azzera.
- **Rilievi che fermano la PR**: solo quelli **confermati** dal verificatore con gravità `bloccante` o `grave`. I `rilevante` e `minore` vengono elencati nella PR.

---

## 10. Stato

### 10.1 Il file

- `tollgate.db` sta nella cartella di stato: uno per macchina.
- SQLite con `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout=5000`.
- Ci scrive solo il codice di tollgate.

### 10.2 Tabelle

| Tabella | Colonne principali | Vincoli |
|---|---|---|
| `work_items` | id, chiave del repo, issue, issue madre, fetta, livello, livello abbassato (sì/no e motivo), fase, fase prima del blocco, ramo, worktree, `work_base_sha`, ultima sessione, `lease_owner` e `lease_until` (non usati nel nucleo; presa in carico solo locale, per C), date | univoco (chiave del repo, issue, fetta) |
| `slices` | lavoro del piano principale, numero, titolo, dipendenze, stato | univoco (lavoro, numero) |
| `scope` | lavoro, percorso, origine (`piano` o `deroga`) | |
| `receipts` | lavoro, sha, worktree pulito, comando, comando risolto, exit, test eseguiti, test saltati, durata, log, `prodotta_da` (`verify` o `finish`), stato (`verde`, `rossa`, `vuota`, `senza_conteggio`, `instabile`, `non_verificato`) | |
| `waivers` | lavoro, tipo, file, scelta, perché, costo, stato (`valida`, `in_attesa`, `approvata`), approvata da | |
| `blocks` | lavoro, tipo, motivo, aperto, chiuso, risoluzione | |
| `subagents` | id, tipo, lavoro, `agent_base_sha`, impronta di `git status`, inizio, fine, stato dichiarato, blocchi ricevuti | |
| `findings` | lavoro, giro, fonte, gravità, file, riga, testo, esito della verifica, `decisione_utente` (per R13) | |
| `approvals` | oggetto (`plan`, `waiver`, `block`, `presence`, `level`, `unverified`), id, ora, testo del comando dell'utente | |
| `intents` | lavoro, azione, chiave di idempotenza, dati, stato, esito, ora | univoco (chiave di idempotenza) |
| `events` | registro in sola aggiunta: ora, sessione, lavoro, tipo, dati JSON | |
| `meta` | versione dello schema | |

**Percentuale di contesto.** La statusline la scrive in `ctx/<session_id>.json` nella cartella di stato, non nel DB.

### 10.3 Fasi e ripresa

**Fasi:** `piano` → `approvazione` (solo L2) → `esecuzione` → `revisione` → `pr_aperta` → `chiuso`.
- Da qualunque fase si passa a `bloccato`, e da lì si torna alla fase precedente.
- Quando il livello sale da L0 a L1 si torna a `piano`.

**Chi cambia fase:**
- `bin/tollgate` (`start`, `finish`);
- l'hook `UserPromptExpansion`, per i tuoi atti;
- il tuo merge, rilevato con `gh` alla chiamata successiva.

L'agente non cambia mai fase.

**Ripresa.** `start` controlla:
- che il worktree esista;
- che lo SHA nel DB corrisponda al ramo;
- quali intenti sono in sospeso (8.5).

Se qualcosa non corrisponde si ferma e chiede.

**`finish` interrotto.** Se `finish` si ferma a metà, per esempio per la guardia del contesto, riprende dal punto registrato nel DB (controllo fatto su quello SHA, giro di revisione N) dopo `/clear`, purché lo SHA non sia cambiato.

**Due sessioni sullo stesso lavoro.** Se un'altra sessione ha registrato eventi su quel lavoro negli ultimi 10 minuti, `start` ti avvisa e chiede conferma.

### 10.4 Pulizia e migrazioni

- **Pulizia**: a ogni `start` vengono cancellati i log delle ricevute dei lavori chiusi da più di `retention_days` (predefinito 30) e i file di contesto più vecchi di 7 giorni. Gli eventi si conservano per `events_days` (predefinito 180).
- **Migrazioni**: `meta.version`, con migrazioni in avanti applicate all'avvio e una copia del DB prima di ogni migrazione.
- **Traccia permanente**: sta nella descrizione della PR, non nel DB.

---

## 11. `tollgate.toml` (nel ramo base del progetto)

Si crea con `/tollgate:init`. L'agente scrive una **proposta** in `docs/superpowers/tollgate.toml.proposta`; tu la rivedi, la copi in `tollgate.toml` e la committi sul ramo base. Senza il file `start` si rifiuta di partire. Fuori dai rami `tg/*` valgono comunque le regole valide ovunque.

```toml
[project]
base_branch = "main"

[commands]
verify       = "npm run check"               # verifica completa: lint, typecheck, test
test_all     = "npx vitest run"
test_related = "npx vitest related --run {files}"
gate         = ["verify"]                    # comandi rieseguiti da finish check
report       = "junit:reports/junit.xml"     # da dove leggere il numero di test
timeout_s    = 900

[levels]
sensitive_paths  = ["**/migrations/**", "src/**/auth/**"]
sensitive_labels = ["security", "database"]
l0_max_files = 2
l0_max_lines = 50

[context]
warn_pct = 45
stop_pct = 55

[scope]
# file ammessi anche fuori dal piano; un lockfile è ammesso solo se il suo manifest è nello scope
always   = []
lockfiles = { "package-lock.json" = "package.json", "pnpm-lock.yaml" = "package.json", "poetry.lock" = "pyproject.toml" }

[external_effects]
commands        = ["supabase db push", "supabase functions deploy", "wrangler deploy", "npm publish"]
project_scripts = ["deploy", "release"]
mcp_allow       = []                          # strumenti MCP in sola lettura, permessi senza conferma

[test_guard]
test_globs    = ["**/*.test.*", "**/*.spec.*", "tests/**/test_*.py"]
fixture_globs = ["**/fixtures/**", "**/__snapshots__/**"]
ci_globs      = [".github/workflows/**"]
command_files = ["package.json", "vitest.config.*", "jest.config.*", "pytest.ini", "tox.ini", "pyproject.toml"]
skip_markers  = ["\\bxit\\(", "\\.skip\\(", "\\.only\\(", "@pytest\\.mark\\.skip"]
assert_markers = ["\\bexpect\\(", "\\bassert\\b"]

[review]
parallel_ok  = ["pr-review-toolkit:pr-test-analyzer", "pr-review-toolkit:silent-failure-hunter"]
max_findings = 15

[severity]   # lette dal revisore e dal verificatore
bloccante = "dato sbagliato senza conferma, dati di altri utenti, azione eseguita due volte"
grave     = "un passo che fallirebbe così com'è scritto, o un comportamento sbagliato"
rilevante = "debito o attrito che emergerà più avanti"
minore    = "redazionale"

[retention]
retention_days = 30
events_days    = 180

[profiles]   # contratto di estensione per il sotto-progetto B; nel nucleo esiste solo "base"
active = ["base"]

[profiles.base]
paths      = ["**"]                          # file che attivano il profilo
gate       = []                              # comandi del gate aggiuntivi
checklist  = ""                              # file con la checklist per il revisore finale
specialists = []                             # specialisti per L2

[components]  # mappa aperta (R10): ogni componente si può spegnere; B potrà aggiungere chiavi
scope_check = true
plan_check = true
test_guard = true
context_guard = true
subagent_receipt_gate = true
single_writer = true
fix_round_cap = true
presence_check = true
readonly_check = true
final_review = true
plan_adversary = true
specialists = true
```

---

## 12. Errori e casi limite

| Situazione | Comportamento |
|---|---|
| Script di controllo che va in errore, in crash o in timeout | Il wrapper esce con 2: l'azione viene bloccata e il messaggio indica il log e `/tollgate:off` |
| Python o DB irrimediabilmente rotti | `/tollgate:off` scrive il file `OFF` senza passare da Python né dal DB; tutti gli hook lasciano passare |
| `tollgate.toml` assente | Il repo non è attivo: tollgate non fa niente. `start` si rifiuta e invita a `/tollgate:init` |
| Repo senza remote GitHub, `gh` non autenticato, ramo base assente o vuoto | `start` si rifiuta con il motivo |
| Issue già chiusa | Avviso e conferma |
| `finish` interrotto dalla guardia del contesto | Riprende dopo `/clear` dal punto registrato |
| Effetto esterno nascosto in uno script del progetto | Va elencato in `project_scripts`. Per i commit lo copre la prova di presenza; **per i deploy resta un limite noto** |
| Strumento MCP non elencato | `ask` |
| Comando di verifica assente | «Non verificato»; `finish` richiede `/tollgate:approve unverified`, scritto nella PR |
| Zero test eseguiti | Ricevuta «vuota», mai verde |
| Test instabili | Un nuovo tentativo, poi la ricevuta è segnata «instabile» |
| Timeout dei test | Il test vale come fallito |
| CI del ramo base rossa | Avviso e conferma, scritti nella PR |
| Ramo base andato avanti con conflitti | Blocco `serve_te`, nessun rebase automatico |
| Implementatore che dichiara DONE senza ricevuta verde | 2 blocchi, poi `serve_te` |
| Due implementatori insieme | Il secondo viene negato |
| Un revisore modifica il worktree | Verdetto non valido, `serve_te` |
| Due sessioni sullo stesso lavoro | Avviso e conferma |
| DB occupato per più di 5 secondi | Errore: il wrapper blocca |
| GitHub irraggiungibile | Le fasi locali continuano; `start` su un'issue nuova e `finish open-pr` si fermano; gli intenti restano in sospeso |
| Piano modificato dopo la registrazione | Ricontrollo; in L2 il piano torna in approvazione |
| Un lavoro L0 cresce | Sale a L1 e torna in fase `piano` |
| Falso positivo che porta in L2 | Puoi abbassare il livello con un atto e un motivo |
| `tollgate.toml` modificato nel ramo | Non ha effetto (la configurazione si legge dalla base); `finish` blocca |
| Modifica ai file che definiscono i comandi dei test | Deroga `comando`, sempre in attesa della tua approvazione |
| Coordinatore che prova a chiudere con `finishing-a-development-branch` | Merge, push, cancellazione del ramo e rimozione del worktree negati; il messaggio rimanda a `/tollgate:finish` |
| Statusline non configurata o percentuale assente (`null`) | La guardia del contesto non blocca; `start` avvisa e suggerisce `/tollgate:setup` |
| Superpowers fuori dall'intervallo di versioni | `start` si rifiuta e lo dice |
| Specialisti esterni non installati | Saltati, e la PR lo dice |
| Sessione fuori dal worktree del lavoro | Valgono solo le regole valide ovunque; `start` stampa il percorso |
| Worktree o DB che non corrispondono a git | Si ferma e chiede |
| Merge fatto ma DB non aggiornato | Vince GitHub alla chiamata successiva |
| Sviluppo di tollgate con tollgate attivo | Il repo di tollgate non è il percorso del plugin installato. Si sviluppa con il plugin installato da un'altra cartella, oppure con `/tollgate:off` |

---

## 13. Test del plugin

| Livello | Cosa | Come |
|---|---|---|
| Script | Tutti i sottocomandi di `bin/tollgate`, parser dei piani, test-guard, ricevute | Test unitari con diff, piani, registri di Superpowers e report JUnit di esempio |
| Wrapper | Uscite 1, 127, eccezione e scadenza diventano 2 per gli hook di controllo e 0 per quelli informativi; il file `OFF` lascia passare tutto | Test del wrapper con script finti |
| Hook | Ogni riga delle tabelle 7.2 e 7.4 decide `allow`, `deny`, `ask` o `block` come previsto | Input JSON uguale a quello di Claude Code; si controllano risposta e codice d'uscita |
| Integrazione | `start → verify → finish`, ripresa, intenti, prova di presenza, configurazione dalla base, comandi risolti | Repo git temporaneo, un finto `gh` nel PATH, `TOLLGATE_STATE` e `TOLLGATE_CONFIG` temporanei |
| Comportamento | L'agente con tollgate rispetta gli obblighi | Pochi casi di `claude plugin eval`, 3 esecuzioni ciascuno |
| CI | Tutto quanto sopra verde a ogni push | GitHub Action sul repo di tollgate |

**Casi di eval nel nucleo:**
1. Un implementatore dichiara DONE senza ricevuta verde → bloccato; `finish` senza ricevuta verde → nessuna PR.
2. Test in conflitto con la specifica → blocco `conflitto_test_spec`, test intatto.
3. Modifica fuori scope → negata, deroga registrata.
4. Comando di deploy → richiesta di conferma.
5. Lavoro L0 che cresce → livello L1 e fase `piano`.
6. Fine di subagent-driven-development → `/tollgate:finish`, nessun merge locale.

---

## 14. Criteri di accettazione del nucleo

Ogni criterio dice cosa si fa, cosa si deve osservare e quale test lo verifica.

1. **Avvio.** `start #N` su un repo con `tollgate.toml` → esistono worktree, ramo `tg/N-<slug>` e riga `work_items`; il livello viene proposto e il percorso stampato. Senza `tollgate.toml` → rifiuto con l'invito a `/tollgate:init` (integrazione).
2. **Piano.** Un piano senza le sezioni obbligatorie → `decision: block` con l'elenco di quello che manca e nessuno scope registrato. Un piano completo → scope registrato, intervalli di righe tolti. Un piano principale → fette registrate (hook, script).
3. **Scope.** In fase `esecuzione`, Edit fuori scope → `deny`; dopo `waiver add` per quel file → permesso. In fase `piano` → permessi solo i file sotto `docs/superpowers/`. In L1, Edit del codice dalla sessione principale → `deny` (hook).
4. **Implementatore.** Con DONE, commit e senza ricevuta verde → `block`, e al 3° tentativo `serve_te`. Con BLOCKED e ricevuta rossa → chiude (hook, integrazione).
5. **Commit.** `git add -A && git commit` con un test cancellato, uno `skip` aggiunto o un'asserzione in meno → `deny` senza deroga; `process.exit(` aggiunto in codice non di test → nessun falso positivo (hook, script).
6. **Comandi.** Effetti esterni elencati, `curl -X POST`, `gh api -X DELETE` e strumenti MCP non permessi → `ask`. Distruttivi, `git push`, `gh pr create`, `gh pr merge`, merge locale verso la base, cancellazione dei rami `tg/*`, rimozione del worktree, `claude plugin disable` e `sed -i tollgate.toml` → `deny` (hook).
7. **Subagenti.** Con la percentuale di contesto a `stop_pct` → `deny` sui nuovi subagenti. Con un `general-purpose` attivo → `deny` sul secondo. Dopo il 2° giro di correzione di un task del piano → `deny` sul nuovo implementatore. Con la percentuale `null` → nessun blocco (hook).
8. **PR.** `finish open-pr` apre la PR solo se `finish check` è passato sullo stesso SHA, se il verdetto registrato dall'hook non ha rilievi confermati `bloccante` o `grave` e se non ci sono atti in sospeso. Con un JSON di verdetto malformato → `serve_te`. Al 5° giro di revisione → `serve_te` (integrazione).
9. **Ripresa.** Con l'interruzione tra push e creazione della PR, `start` chiede conferma, cerca la PR esistente e non ne crea una doppia (integrazione).
10. **Configurazione e comandi.** `tollgate.toml` modificato nel ramo → comportamento invariato e `finish check` fallisce. Lo script `check` cambiato in `package.json` → deroga `comando` in attesa e `finish check` fallisce senza approvazione (integrazione).
11. **Prova di presenza.** Un commit fatto senza passare dall'hook → elencato come «commit fuori controllo» e PR ferma fino a `/tollgate:approve presence` (integrazione).
12. **Atti dell'utente.** Approvazioni, risoluzioni, abbassamento del livello e interruttore si registrano solo da `UserPromptExpansion`. Le stesse operazioni tentate dall'agente con lo strumento Skill o via Bash non hanno effetto o vengono negate (hook).
13. **Errori degli hook.** Uscita 1, uscita 127, eccezione o scadenza dello script di controllo → uscita 2 del wrapper. Con il file `OFF` → tutto passa (wrapper).
14. **Ricevute.** Zero test eseguiti → ricevuta «vuota» e non verde (script).
15. **Sola lettura.** Un revisore che modifica il worktree → verdetto scartato e `serve_te` (hook).
16. **Componenti.** Ogni chiave di `[components]` impostata a `false` spegne il suo comportamento, e c'è un test per ciascuna (script, hook).
17. **Repo non attivo.** In un repo senza `tollgate.toml`, `git push` e `gh pr create` passano e nessun hook aggiunge contesto (hook).
18. **Rinomine.** Un file di test rinominato con gli stessi test → nessuna segnalazione (script).
19. **Budget delle istruzioni.** Le righe iniettate da `SessionStart` sono al massimo 10 e 1.500 caratteri, misurato da un test (hook).

---

## 15. Da verificare sulla documentazione prima di scrivere codice

**Già verificato l'08/10/2026** (code.claude.com/docs/en/hooks.md e /plugins/components.md):
- solo l'uscita 2 blocca; uscita 1, crash e timeout lasciano passare;
- timeout predefinito di 600 s per gli hook `command`;
- `PostToolUse` con `decision: block` aggiunge il motivo ma non annulla l'azione;
- il comando `/skill` digitato dall'utente fa scattare `UserPromptExpansion`, con `prompt` testuale e `command_name`;
- lo strumento dei subagenti si chiama `Agent`;
- per gli agenti di un plugin, `agent_type` è `plugin:nome` e va filtrato con `^…$`;
- **un plugin non può impostare la statusline principale**: dal suo `settings.json` valgono solo `agent` e `subagentStatusLine`. Per questo c'è `/tollgate:setup`.

**Ancora da verificare:**
- `SubagentStart`: può aggiungere contesto al subagente? Se non può, il brief di Superpowers basta.
- `PreToolUse`: semantica di `updatedInput` e di `defer`.
- `UserPromptExpansion` scatta anche per le skill con `disable-model-invocation: true` digitate dall'utente?
- Il campo `agent_id` è assente nella sessione principale e presente nei subagenti (lo usa la regola «il coordinatore non scrive codice»)?
- Un subagente può usare lo strumento Skill (serve a `specialist-runner`)? In alternativa: l'opzione `context: fork` delle skill.
- Lo strumento nativo per entrare in un worktree: si adatta a un worktree creato da `start`?
- Il formato di `dependencies` e di `allowCrossMarketplaceDependenciesOn`, e il vincolo di versione su Superpowers.
- La stabilità del formato del registro di subagent-driven-development (`Task <N>: fix round <R>/5`), da cui dipende R4. Va fissato l'intervallo di versioni di Superpowers.
- Il formato dei reporter JUnit e JSON di vitest, jest e pytest, per contare i test.
- Il comando di revisione di codex-plugin-cc e se si può eseguire dentro un subagente.

---

## 16. Cosa resta aperto

Questi limiti restano anche dopo le correzioni. Sono dichiarati qui perché nessuno li scambi per garanzie.
- **Deploy dentro uno script del progetto non elencato**: nessun controllo li vede.
- **Un modello che importa il codice di tollgate e scrive nel DB**: durante il lavoro non lo vede nessuno. Al gate non conta, perché `finish check` riesegue tutto e usa solo le sue ricevute.
- **Asserzioni rese più deboli senza cambiarne il numero** (per esempio `toBe(3)` che diventa `toBeTruthy()`): le può trovare solo il revisore (R3).

---

## 17. Revisioni

| Rev. | Data | Cosa |
|---|---|---|
| 1 | 08/10/2026 | Prima stesura |
| 2 | 08/10/2026 | Correzioni dei cicli 1-3 dell'audit (A-01 … A-25) |
| 3 | 08/10/2026 | Correzioni della revisione avversariale (V-01 … V-36) e verifica sulla documentazione: wrapper degli hook con uscita 2 e interruttore senza Python; atti dell'utente via `UserPromptExpansion`; statusline configurata dall'utente; specialisti esterni opzionali; comandi risolti e conteggio dei test nelle ricevute; file dei comandi sotto test-guard; test-guard su working tree più indice, solo nei file di test, con parole intere e conteggio delle asserzioni; effetti esterni via MCP, curl, gh api e shell annidate; intenti idempotenti con conferma alla ripresa; livello abbassabile solo dall'utente; `/tollgate:init`; glossario; chiave del repo e vincoli di unicità; coordinatore senza scrittura di codice in L1 e L2; controllo di sola lettura dei revisori; deroghe per singolo file; issue trattata come dato non fidato; override di stato e configurazione per i test; criteri riscritti come azione, osservazione e test; sezione «Cosa resta aperto» |
| 4 | 08/10/2026 | Correzioni dei cicli 5-10 (B-01 … B-17): tollgate inerte nei repo senza `tollgate.toml` e regole su push e merge limitate ai rami `tg/*`; comandi del gate configurabili; un verificatore per giro con tetto; intervallo di versioni di Superpowers; prerequisiti del repo; rinomine; `finish` riprendibile; contratto dei profili per B; Codex tramite `specialist-runner`; blocco JSON nella PR; file sempre permessi più ristretti; lockfile legati al manifest |
