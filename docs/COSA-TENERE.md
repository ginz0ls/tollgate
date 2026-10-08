# tollgate: cosa teniamo, cosa modifichiamo, cosa scartiamo

Data: 8 ottobre 2026.
Fonte: `docs/REPORT-CONFRONTO-WORKFLOW.md`, sezioni 0-10 e 13.
Stato: **proposta da rivedere**. Le voci 22 e 28 sono decise; le altre aspettano la tua revisione. Per cambiarne una basta citarne il numero.

---

## Decisioni già prese

| Tema | Decisione |
|---|---|
| Nome | **tollgate**. Nomi in inglese per plugin, comandi e script |
| Tracker | GitHub Issues |
| Harness | Claude Code. Portabilità verso altri harness: dopo |
| Autonomia | v1 interattiva. Avvio da etichetta GitHub con Action: dopo |
| Flusso | **Quello di Superpowers** (brainstorming → writing-plans → subagent-driven/executing → review). tollgate aggiunge solo quello che manca |
| Approccio | Hook più due comandi: `/tollgate:start #N` e `/tollgate:finish`. Lo stato esplicito sta in SQLite |
| Obblighi imposti dagli hook | Niente «fatto» senza ricevute; test non indebolibili; effetti esterni solo con la tua conferma; scope limitato ai file del piano |
| Deroghe | L'agente le registra e prosegue. **Oltre 2 per fetta si ferma e chiede a te**. Tutte compaiono nella PR |
| Livelli | L0 rapido, L1 standard, L2 alto. Li sceglie uno script, possono solo salire e tu puoi alzarli |
| Piano principale | Come in Perizie: si crea solo se il lavoro non sta in una fetta |
| Kanban | Ibrida: SQLite locale per il lavoro in corso, GitHub Issues e Projects per il lavoro deciso e accettato |
| Dashboard | Dopo la v1 |
| Profili v1 | Base, frontend, backend (Supabase edge, Cloudflare Worker, server locale), database, sicurezza, AI/LLM, bugfix |
| Pubblicazione | Privato ora, pubblico poi: nel codice niente percorsi né nomi dei tuoi progetti |
| Sotto-progetti | A nucleo → B profili → C kanban e ponte GitHub → D eval |
| Contesto | **Niente context rot**: ogni attività parte con un contesto pulito (gruppo 6) |

---

## 1. Regole imposte e prove

| # | Pezzo | Da | Proposta | Motivo |
|---|---|---|---|---|
| 1 | Ricevute dei comandi legate alla versione dei file | Orchestratore | **Modificare** | Si legano allo SHA del commit con worktree pulito, non all'hash di tutti i file. È più semplice, regge sui repo grandi e dà la stessa garanzia |
| 2 | I comandi li lancia il sistema: l'agente non può dichiarare «test verdi» | Orchestratore | **Tenere** | `tollgate verify` esegue solo i comandi dichiarati dal progetto |
| 3 | 8 controlli git: ramo, commit nuovo che discende dalla base, diff non vuoto, worktree pulito, push verificato con `ls-remote`, PR verificata | codex-workflow `worktree.py:43-87` | **Tenere quasi intero** | È la parte migliore di codex-workflow |
| 4 | SHA ricontrollato prima della PR | codex-workflow | **Tenere** | Rende verificabile che il revisore abbia solo letto, anche senza sandbox |
| 5 | Scope per task | Orchestratore | **Tenere** | Si ricava da `Create:` e `Modify:` dei piani Superpowers |
| 6 | Nessuna autorizzazione concessa in automatico | Orchestratore | **Tenere** | Per gli effetti esterni Claude Code ti chiede conferma |
| 7 | Skill obbligatorie lette e legate all'hash | Orchestratore | **Scartare** | Complesso, poco valore |
| 8 | Blocco della chiusura senza prove, per sessione | ralph-loop | **Modificare** | Solo sui subagenti che implementano, non su ogni tua risposta. Il funzionamento dell'hook va verificato sulla documentazione |
| 9 | Blocco del codice se prima non c'è un test che fallisce | tdd-guard | **Modificare** | Solo per i bugfix: test di riproduzione rosso → verde, con ricevuta di entrambi. Ovunque costa circa 3 volte i token senza migliorare la qualità |
| 10 | Blocco dei comandi distruttivi (force push, `reset --hard`, `--no-verify`, `rm -rf`) | cc-safety-net | **Tenere** | Coincide con le regole del CLAUDE.md globale |
| 11 | CI del ramo base verde prima di partire | lezione di Perizie (notturna rossa) | **Tenere** | Si controlla a `start` |
| 12 | Niente rete né credenziali quando l'agente legge testo non fidato | lethal trifecta | **Rimandare** | Nella v1 le issue le scrivi tu. Diventa obbligatorio con l'avvio automatico da GitHub |

## 2. Piani e decisioni

| # | Pezzo | Da | Proposta | Motivo |
|---|---|---|---|---|
| 13 | Piano magro: Fatti verificati, Decisioni con costo, Interfacce, Punti di arresto, Rischi | Perizie | **Modificare** | `writing-plans` resta com'è. Quando il piano viene salvato, un hook lo controlla e lo rimanda indietro se mancano queste sezioni |
| 14 | Ruling e deroghe | Perizie | **Già deciso** | Tetto di 2 per fetta, poi decidi tu |
| 15 | Punti di arresto P1-P4 e P-D | Perizie | **Modificare** | Si riducono a meccanismi che esistono già. P1 = approvazione del piano in L2. P2 = merge tuo. P3 = deroga. P4 e P-D = effetti esterni con conferma |
| 16 | Una sola scala di gravità, tarata sul progetto | Perizie, prd-audit | **Tenere** | Bloccante, grave, rilevante, minore, con le definizioni in `tollgate.toml` |
| 17 | Revisione avversariale del piano senza le motivazioni dell'autore | Perizie | **Tenere in L2** | Subagente in sola lettura |
| 18 | Scansione delle interfacce prima di partire | Perizie | **Tenere** | Diventa la sezione «Fatti verificati» all'inizio di ogni fetta |
| 19 | Fatti in un posto solo, CLAUDE.md piccolo | lezione di Perizie | **Tenere** | Avviso se CLAUDE.md supera una soglia di dimensione |
| 20 | Verifica dal risultato atteso a ritroso: esiste, è sostanziale, è collegato | GSD | **Tenere** | Un verificatore a `finish` controlla i must-have del piano |
| 21 | Specifiche incrementali (delta spec) | OpenSpec, Spec Kit | **Scartare per la v1** | Basta la spec di Superpowers |
| 22 | Lezioni scritte per il ciclo successivo | Compound Engineering | **Deciso: dopo la v1** | Con un tetto di dimensione, per non gonfiare il contesto |
| 23 | Classificazione spike, bounded, architectural | Superpowers | **Convivenza** | Il livello di tollgate sceglie da quale skill si entra; la classificazione di Superpowers resta dentro |

## 3. Revisione

| # | Pezzo | Da | Proposta | Motivo |
|---|---|---|---|---|
| 24 | Verdetto su una riga JSON con gravità, file e riga | codex-workflow | **Tenere** | Gestendo il JSON malformato, che in codex-workflow è un bug |
| 25 | Tetto di 4 giri di revisione finale che non si azzera; un rilievo lo chiude solo chi l'ha aperto | Orchestratore | **Tenere** | Sulla revisione finale. Il ciclo di correzione per task resta quello di Superpowers |
| 26 | Filtro di confidenza ≥80 contro i falsi positivi | plugin code-review | **Tenere** | Evita di rincorrere rilievi deboli, che portano a over-engineering |
| 27 | Panel di più revisori | agent-skills `/ship` | **Tenere solo in L2 con profilo sicurezza** | Costa molto: va usato dove serve |
| 28 | Revisore con un motore diverso (Codex) | codex-plugin-cc | **Deciso: opzionale** | Se codex-plugin-cc è installato si usa in L2, altrimenti c'è un revisore Claude a contesto fresco |

## 4. Stato, ripresa, GitHub

| # | Pezzo | Da | Proposta | Motivo |
|---|---|---|---|---|
| 29 | Si salva l'intenzione prima di agire (push, PR) | Orchestratore | **Tenere** | Dopo un crash nessuna azione viene ripetuta due volte |
| 30 | Prima di creare una PR si cerca se ne esiste già una | codex-workflow | **Tenere** | Stessa ragione |
| 31 | SQLite in modalità WAL con scrittura sicura | Orchestratore | **Tenere** | Più sessioni in parallelo senza corrompere il DB |
| 32 | Presa in carico con scadenza, blocchi tipizzati, dipendenze | Hermes | **Tenere nel sotto-progetto C** | — |
| 33 | Registro dei task di Superpowers | Superpowers | **Tenere com'è** | Il riepilogo versionato va nella descrizione della PR, non in un file ignorato da git come in Perizie |
| 34 | Adattatore del tracker | codex-workflow | **Modificare** | Nella v1 solo GitHub, dietro un'interfaccia sottile: Jira si aggiunge dopo |
| 35 | Webhook, worker e coda sempre attivi | codex-workflow | **Scartare** | Per l'avvio automatico useremo GitHub Action o Routines |
| 36 | Eval contro Claude Code senza plugin | `claude plugin eval` | **Tenere nel sotto-progetto D** | È la prova che tollgate migliora davvero il risultato |

## 5. Da scartare del tutto

- Specialisti e ruoli dichiarati ma non usati dal codice (codex-workflow).
- `/goal` come controllo di completamento: il suo valutatore non esegue niente.
- Una meta-skill da 10 KB caricata a ogni sessione.
- Più agenti che scrivono in parallelo sugli stessi file.
- TDD obbligatorio ovunque.
- Sciami di agenti (ruflo).
- Un motore di workflow proprio (Archon).
- Specifiche gonfie per lavori piccoli (Kiro: 16 criteri per un bug).

## 6. Contesto pulito (requisito di base)

| # | Regola | Da | Come la applichiamo |
|---|---|---|---|
| 37 | La sessione principale coordina e basta | GSD | Non legge codice né log. Lavora solo con stato (DB), brief e report su file, così il suo contesto resta piccolo per tutta la fetta |
| 38 | Ogni attività parte con un subagente nuovo | Superpowers (subagent-driven), Orchestratore (un thread per fase) | Task, review, verifica e revisione avversariale ricevono un brief su file e restituiscono un report su file. Nella sessione principale torna solo un riepilogo di poche righe |
| 39 | L'output dei comandi va su file | Superpowers `task-done` | `tollgate verify` salva i log completi e mostra solo l'esito e le ultime righe |
| 40 | Una fetta per sessione | Anthropic (sessioni lunghe), lezione di Perizie | A fine fetta `finish` salva lo stato e suggerisce `/clear`. Il `start` successivo riparte dal DB. Lo stesso vale tra spec approvata e piano |
| 41 | Avvio con il minimo indispensabile | evidenze ICLR 2026 e Vercel | Nessuna meta-skill caricata a ogni sessione. All'avvio entrano solo poche righe: issue, fase, livello, prossimo passo |
| 42 | Guardia sulla dimensione del contesto | nuova | Sopra una soglia, un hook impedisce di avviare nuovi task e chiede un checkpoint e `/clear`. **Da verificare**: se e come un hook può misurare il contesto (per esempio dalla dimensione del transcript) |

Unica eccezione: il **brainstorming** si fa nella sessione principale, perché è un dialogo con te. Subito dopo l'approvazione della spec si chiude e si riparte pulito.

---

## Prossimi passi

1. Tu rivedi questo documento e indichi i numeri da cambiare.
2. Rivedo la sezione 2 del design (il ciclo di vita del task) con il gruppo 6 dentro: ogni passaggio di fase diventa un punto in cui si può ripartire da zero.
3. Poi le sezioni rimanenti del design: hook e ricevute, schema del DB, gestione degli errori, test.
4. Spec scritta in `docs/superpowers/specs/`, revisione tua, poi piano con `writing-plans`.
