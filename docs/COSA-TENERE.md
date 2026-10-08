# tollgate: cosa teniamo, cosa modifichiamo, cosa scartiamo

Data: 8 ottobre 2026.
Fonte: `docs/REPORT-CONFRONTO-WORKFLOW.md`, sezioni 0-10 e 13.
Stato: **proposta da rivedere**. Le voci 22 e 28 sono decise; le altre, incluse le H del gruppo 7, aspettano la tua revisione. Per cambiarne una basta citarne il numero.

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
| 8 | Blocco della chiusura senza prove, per sessione | ralph-loop | **Modificare** | Hook `SubagentStop` che blocca **solo i subagenti che hanno prodotto commit senza una ricevuta verde su quel commit**. Il criterio è un fatto, non il nome: Superpowers lancia implementatore e revisore entrambi come `general-purpose`, quindi il tipo di agente non basta a distinguerli. Verificato sulla documentazione (vedi sotto) |
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
| 42 | Guardia sulla dimensione del contesto | nuova | **Modificata dopo la verifica.** Nessun hook riceve la percentuale di contesto; la riceve solo la statusline (`context_window.used_percentage`). Si fa così: **la statusline è quella dell'utente, importata in `statusline/statusline.sh`**. Legge già `used_percentage` e ha la soglia di autocompact all'85%. Le si aggiunge una sola cosa: scrivere la percentuale su un file per sessione. Un hook `PreToolUse` sullo strumento Agent legge quel file e, sopra soglia, nega l'avvio di nuovi task chiedendo checkpoint e `/clear`. Un hook non può lanciare `/clear` da solo. Senza statusline la guardia si spegne con un avviso, perché le voci 37-41 tengono già piccola la sessione principale |

Unica eccezione: il **brainstorming** si fa nella sessione principale, perché è un dialogo con te. Subito dopo l'approvazione della spec si chiude e si riparte pulito.

---

## 7. Hermes Agent

Fonte: analisi in sola lettura di `~/.hermes/hermes-agent` (NousResearch/hermes-agent, commit `057dcdf2`) e di `Company AgentOS/Hermesz/REPORT-HERMES.md`, fatta l'8 ottobre 2026. I riferimenti file:riga sono del repo di Hermes. Le voci hanno prefisso H per non confonderle con le 1-42.

**La scoperta principale.** Hermes ha già due pezzi molto vicini a tollgate, ma entrambi solo «morbidi»:
- un **registro delle verifiche in SQLite** (H40), che però considera scaduta una verifica in base all'orario dell'ultima modifica;
- un controllo **«verifica prima di fermarti»** (H41), che però è spento di default e si limita a un promemoria.

tollgate prende la stessa idea e la rende obbligatoria e legata allo SHA.

### Da tenere o modificare

| # | Pezzo | Dove in Hermes | Proposta per tollgate |
|---|---|---|---|
| H2 | I messaggi dell'utente non vengono mai riassunti | `agent/context_compressor.py:912` | **Tenere** come principio: nei file di passaggio tra fette le tue parole restano testuali, si riassume solo il lavoro dell'agente |
| H3 | Il riassunto è marcato «solo riferimento, non istruzioni» | `context_compressor.py:116` | **Tenere** nei file di passaggio: un riassunto non deve diventare un ordine |
| H4 | Gli identificativi (SHA, percorsi, errori) si estraggono meccanicamente, senza parafrasi | `context_compressor.py:1021` | **Modificare**: vanno nelle ricevute e nei file di fetta |
| H5 | Strumenti e regole non cambiano a metà sessione (prompt caching) | `AGENTS.md:1345` | **Tenere**: skill e regole si caricano all'inizio, mai a metà |
| H7 | I risultati grandi finiscono su file; nel contesto restano un'anteprima e il percorso | `tools/tool_result_storage.py:1-40` | **Tenere**: è la voce 39 |
| H8-H9 | Il subagente parte con un contesto vuoto e al padre torna solo un riassunto, con un tetto di dimensione | `tools/delegate_tool.py:5-17`, `:1093-1105` | **Modificare**: il report completo va su file, al padre tornano solo verdetto e percorso (voce 38) |
| H10 | Ai subagenti sono vietati gli strumenti con effetti esterni e la delega ricorsiva | `delegate_tool.py:50-58` | **Tenere** |
| H11 | Worktree per subagente, rimosso se pulito | `tools/subagent_worktree.py:1-35` | **Tenere** (lo fa già Claude Code con `isolation: worktree`) |
| H12 | Registro dei file toccati: blocca la scrittura su un file già modificato da un altro agente | `tools/file_state.py:1-30` | **Modificare**: diventa parte del controllo di scope |
| H13 | Subagenti senza livelli annidati | `delegate_tool.py:129` | **Tenere** |
| H15 | Descrizione delle skill al massimo 60 caratteri | `AGENTS.md:1020` | **Tenere** per le skill di tollgate |
| H18 | Scansione delle skill esterne contro esfiltrazione e injection | `tools/skills_guard.py:1-30` | **Tenere** come idea per dopo |
| H19-H20 | Memoria con un tetto in caratteri, fotografata a inizio sessione e controllata contro le injection | `tools/memory_tool.py:1-23`, `:228-260` | **Tenere** l'idea per i file di stato iniettati a `start` (voce 41) |
| H22 | Elenco di comandi pericolosi che richiedono approvazione | `tools/approval.py:909` | **Modificare**: diventa l'elenco degli effetti esterni (voce 6) |
| H23 | Un elenco minimo di blocchi che nessuna modalità può aggirare | `approval.py:430-455` | **Tenere**: in L2 nessuna deroga li supera |
| H24 | Il file di configurazione è protetto anche da `sed`, `tee` e `>` | `approval.py:358-372` | **Tenere**: `tollgate.toml` e gli hook non sono modificabili dall'agente, altrimenti il gate si spegne da solo |
| H26 | Scrittura limitata sotto una cartella radice | `agent/file_safety.py:93` | **Modificare**: la radice diventa l'elenco dei file del piano (voce 5) |
| H28 | Hook shell con lo stesso contratto di Claude Code; possono fallire «chiusi» | `agent/shell_hooks.py:1-75` | **Tenere**: gli hook di gate di tollgate falliscono chiusi, cioè se si rompono bloccano invece di lasciar passare |
| H32 | File sentinella che mette in pausa solo il lavoro nuovo | `agent/estop.py:1-20` | **Tenere**: un file `PAUSE` |
| H34-H35 | Ogni task della kanban parte in una sessione nuova, con un contesto costruito dal DB e con dei tetti | `hermes_cli/kanban_db.py:10709`, `:11004` | **Tenere** per dopo: è il modello dell'avvio automatico da GitHub |
| H36 | Un worker non può fermarsi senza dichiarare «completato» o «bloccato»; dopo 2 promemoria è una violazione | `agent/kanban_stop.py:1-12` | **Tenere**: è l'obbligo di fine fetta |
| H37 | Revisione con «richiedi modifiche» che torna all'implementatore | `kanban_db.py:6490` | **Tenere**: corrisponde alla review di Superpowers |
| H38-H39 | Eval con fixture deterministiche e risposta nota | `evals/compaction/`, `evals/readtool/` | **Modificare**: confronto con e senza tollgate su task fissi, misurando i «fatto» falsi e le PR riaperte (sotto-progetto D) |
| H40 | Registro delle verifiche in SQLite | `agent/verification_evidence.py:116-150` | **Modificare**: la ricevuta vale per uno SHA, non per un orario, che è aggirabile |
| H41 | «Verifica prima di fermarti» dopo modifiche al codice, ignorando `.md` e `.txt` | `agent/verification_stop.py:140-250` | **Modificare**: bloccante invece che promemoria, e scelto in base al profilo |
| H42 | `hermes verify`: preparazione, build, test, avvio, controllo che risponda, poi registrazione | `agent/verify/runner.py:1-40` | **Tenere** come modello di `tollgate verify` e delle varianti backend del sotto-progetto B |
| H43 | Si ferma dopo N fallimenti identici di fila | `agent/tool_guardrails.py:1-50` | **Tenere**: interruttore automatico sui cicli di correzione |
| H44 | Prima estendere ciò che c'è, poi CLI e skill, poi tool, solo alla fine plugin | `AGENTS.md:182-211` | **Tenere** come regola di design |

### Da scartare

- Compressione e riassunto automatico del contesto (H1, H6): tollgate evita il context rot con sessioni corte, non comprimendo.
- Skill che l'agente crea o modifica da solo senza approvazione, e la loro pulizia automatica (H16, H17). Torneranno con le lezioni apprese dopo la v1, sempre approvate da te.
- Approvazione dei comandi decisa da un LLM (H25): un gate deve essere deterministico.
- Modalità «tutto permesso» (yolo).
- Repo git ombra per i checkpoint (H27): bastano git e i worktree.
- Cron, gateway Telegram, middleware, tool search, ricerca nello storico delle sessioni (H21, H30, H31, H33, H45).

### Lezioni dal REPORT-HERMES.md

1. **Il prompt di sistema è un budget di attenzione.** Hermes è passato da 28 a 5 tool e da 88,7 a 18,4 KB. Per tollgate: poche skill, descrizioni brevi, e una misura di quanto pesa il plugin nel contesto.
2. **La cronologia vince sulle istruzioni.** Se cambi una regola, la sessione in corso continua a comportarsi come prima. È un altro motivo per avere una sessione pulita per ogni fetta.
3. **Due regole ragionevoli possono combinarsi male.** Servono test su scenari reali, non solo una prova per ogni regola.
4. **I confini si scrivono come divieti espliciti**, e servono controlli meccanici: un modello non sospetta l'assurdo.
5. **Un task scritto una volta e letto testualmente non si deteriora**, mentre uno riformulato a ogni passaggio sì. Quindi l'issue e il piano si leggono così come sono scritti.
6. **Le regole valgono solo se qualcosa le impone.** Hermes non le impone tra processi separati.
7. **SQLite in modalità WAL si degrada su dischi di rete e FUSE.** Per tollgate: il DB sta in `CLAUDE_PLUGIN_DATA` (sotto `~/.claude`), su disco locale. Le cartelle di MEGA oggi non sono sincronizzate (verificato con l'utente l'8 ottobre 2026), quindi i worktree restano nella posizione predefinita.
8. **Un solo processo scrive nel DB per volta**, con un lock non bloccante.

## 8. Modifiche dalla ricerca scientifica (accettate l'8 ottobre 2026)

Fonte: `docs/RICERCA-PAPER.md`, sezione 3. Prevalgono sulle voci precedenti dove le contraddicono.

| # | Modifica | Dove | Note |
|---|---|---|---|
| R1 | Via d'uscita «test e specifica in conflitto»: un blocco con un tipo preciso che ferma l'agente e lo manda da te | Nucleo | Integra le deroghe (voce 14) e H36 |
| R2 | Test correlati alla modifica nel brief e in `verify`; suite completa a `finish` | Nucleo | **Ridimensionata**: niente grafo nostro, si usa il comando del progetto (`vitest related`, `jest --findRelatedTests`, `pytest-testmon`) dichiarato in `tollgate.toml` |
| R3 | La ricevuta è necessaria ma non sufficiente: il revisore finale cerca casi speciali scritti per i test e test indeboliti | Nucleo | Integra le voci 1, 20, 24 |
| R4 | Al massimo 2 giri di correzione automatica per task, poi contesto pulito o passaggio a te | Nucleo | **Ridimensionata (rev. 5 della spec)**: in Superpowers 6.4.1 i giri 1-3 riprendono lo stesso implementatore, che un hook non può fermare. Vale il tetto di Superpowers; tollgate conta i giri e li riporta nella PR |
| R5 | A ogni nuovo task un hook rimette nel contesto il passo corrente del piano e il suo scope | Nucleo | Poche righe |
| R6 | In L1 controllo automatico della struttura del piano; la rilettura a contesto pulito resta in L2 | Nucleo | **Ridimensionata** |
| R7 | Soglie del contesto della sessione principale: avviso al 45%, stop al 55%. Subagente sotto circa 30K token; ritorno al padre di 1-2K token più il percorso del report | Nucleo | Soglie configurabili, da tarare con gli eval. Sostituiscono l'85% della statusline nella voce 42 |
| R9 | Budget di istruzioni: si misura quanti token aggiunge tollgate a ogni sessione, con un tetto | Nucleo | — |
| R10 | Ogni componente si può spegnere da `tollgate.toml` | Nucleo | Base delle prove con un componente spento alla volta negli eval |
| R14 | Le domande di chiarimento dipendono dal livello: L0 non passa dal brainstorming | Nucleo | **Ridimensionata**: le domande le fa già Superpowers |
| R16 | Il revisore Codex dà solo un parere, non modifica il codice | Nucleo | Integra la voce 28 |
| R8 | Le regole dei profili si caricano tramite hook, non con l'attivazione automatica delle skill | Sotto-progetto B | — |
| R11 | Un hook su ogni installazione controlla che il pacchetto esista e quanto è vecchio | Sotto-progetto B | Profilo base |
| R12 | Analisi statica (SAST) e test di sicurezza obbligatori nel profilo sicurezza | Sotto-progetto B | — |
| R13 | Le osservazioni della revisione si registrano come accettate o rifiutate, per tarare la soglia di confidenza | Sotto-progetto C | — |
| R15 | Negli eval si misura il costo dei subagenti: uno per task contro task piccoli raggruppati | Sotto-progetto D | — |

## 9. Ruoli e revisione (decisi l'8 ottobre 2026)

**Ruoli.**
- **Coordinatore.** È la sessione principale. Parla con te, fa il brainstorming, **scrive spec e piano** (non c'è un subagente pianificatore), lancia i subagenti e legge solo i verdetti. Non scrive codice, tranne in L0.
- **Implementatore.** Un subagente nuovo per ogni task. È l'unico che scrive codice, un task alla volta.
- **Revisore del task.** Quello di Superpowers, in sola lettura, dopo ogni task.
- **Avversario del piano.** Solo in L2, in sola lettura, riceve piano e spec senza le motivazioni di chi li ha scritti.
- **Script.** `verify`, `test-guard` e `state` producono i fatti; gli hook li fanno rispettare.

**Revisione finale** (fonte: `docs/ricerca/06-revisori-specializzati.md`).

| Livello | Chi rivede |
|---|---|
| L0 | Nessun agente: ricevute degli script e merge tuo |
| L1 | **Revisore finale di tollgate** con la checklist dei profili attivi → **verificatore di tollgate per ogni problema segnalato** (conferma con prove o scarta) → verdetto JSON |
| L2 | Revisore finale di tollgate + **specialisti di Anthropic** scelti in base ai profili attivi, al massimo 3, ognuno con il suo contesto: sicurezza → `/security-review`; test → `pr-review-toolkit:pr-test-analyzer`; backend → `pr-review-toolkit:silent-failure-hunter`. Più Codex come parere, se installato → stesso verificatore → verdetto JSON |

**Decisioni.**
- **Revisore finale e verificatore li scrive tollgate.** Sono gli unici che conoscono piano, scope, must-have e ricevute, cercano i trucchi sui test (R3) e restituiscono il verdetto JSON che il gate legge.
- **Il verificatore per ogni problema sostituisce il filtro di confidenza ≥80** (voce 26). La ricerca indica che conta la verifica con prove, non il numero di revisori né il punteggio di confidenza.
- **Gli specialisti sono di Anthropic** (`pr-review-toolkit`, licenza Apache 2.0, e `/security-review`), dichiarati come dipendenza con un intervallo di versioni. Il gate dipende solo dal verificatore di tollgate. Ogni specialista si può spegnere (R10). Sostituisce la voce 27.
- **Il plugin `code-review` di Anthropic non si usa come gate.** Serve a commentare le PR e per scelta scarta copertura dei test e sicurezza; inoltre cambia nel tempo. Il `/code-review` integrato in Claude Code resta solo come passata extra opzionale.
- **In L1 non ci sono revisori specializzati.** Non ci sono prove di beneficio e il costo è alto. La soglia sotto cui basta un revisore va misurata negli eval.

## 10. Dove sta il controllo autorevole (deciso l'8 ottobre 2026)

**Decisione: su GitHub.**
- **Come funziona**: una GitHub Action, con il workflow letto dal ramo base, ricalcola in un ambiente pulito i comandi del gate, test-guard e scope sul diff della PR. La protezione del ramo richiede quel controllo verde e il merge lo fai tu.
- **Il ruolo degli hook locali**: diventano **guardrail** contro scorciatoie ed errori onesti, cioè test modificati, «fatto» senza prove, file fuori scope. Fermano il problema subito, senza aspettare la PR.

**Perché.** La seconda revisione avversariale ha mostrato che un agente con Bash sulla stessa macchina può alterare tutto quello che è locale: DB, variabili d'ambiente, un Claude figlio che si spaccia per te, la configurazione dei test. Sulla macchina dell'agente nessun controllo è inattaccabile.

**Limite residuo, dichiarato.** Resta fuori dalla v1 il caso dell'agente che usa le tue credenziali GitHub per agire al posto tuo (merge, etichette). Lo limitano gli hook locali e la raccomandazione di dargli un token separato con permessi ridotti.

## 11. Audit della spec nel flusso (deciso l'8 ottobre 2026)

In L2 la spec passa da un **audit prima del piano**:
- **giri avversariali a contesto pulito**, finché un giro non produce più né bloccanti né gravi;
- **audit a lenti**, con una versione di `prd-audit` incorporata in tollgate, quando c'è un piano principale.

**Perché.** Nell'audit della spec di tollgate i revisori avversariali a contesto pulito hanno trovato i difetti più gravi (7, 10, 4 e 4 bloccanti, in calo a ogni giro), e l'audit a lenti ha coperto il resto. Il metodo ha funzionato.

## Verifica sulla documentazione ufficiale (8 ottobre 2026)

Fonti: [hooks](https://code.claude.com/docs/en/hooks.md), [sub-agents](https://code.claude.com/docs/en/sub-agents.md), [statusline](https://code.claude.com/docs/en/statusline.md), [plugin components](https://code.claude.com/docs/en/plugins/components.md), [dependencies](https://code.claude.com/docs/en/plugins/dependencies.md), [plugin evals](https://code.claude.com/docs/en/plugin-evals.md). Ho controllato anche il codice di Superpowers 6.4.1 installato.

| Domanda | Risposta | Effetto su tollgate |
|---|---|---|
| `SubagentStop` sa quale subagente si ferma? | Sì: riceve `agent_id`, `agent_type`, `agent_transcript_path`, `last_assistant_message`, `stop_hook_active`. Il matcher filtra su `agent_type`. `decision: "block"` tiene in vita il subagente e gli passa `reason` come istruzione successiva | Voce 8 fattibile. Superpowers però usa `general-purpose` sia per chi implementa sia per chi rivede (`implementer-prompt.md:6`, `task-reviewer-prompt.md:11`), quindi il criterio diventa «ha fatto commit senza ricevuta» |
| Gli agenti di un plugin possono avere hook propri nel frontmatter? | **No**: per sicurezza gli agenti dei plugin ignorano `hooks`, `mcpServers` e `permissionMode` | Tutti gli hook vanno in `hooks/hooks.json` del plugin |
| Rischio di loop con `Stop` | Esiste `stop_hook_active`. Dopo 8 blocchi di fila Claude Code chiude comunque il turno (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) | Ogni hook di stop controlla `stop_hook_active` e blocca solo se la condizione è risolvibile |
| Un hook conosce il riempimento del contesto? | **No.** Lo riceve solo la statusline (`used_percentage`, `context_window_size`). Il formato del transcript non è documentato. Un hook non può lanciare `/clear` o la compattazione: `PreCompact` può solo bloccarla | Voce 42 riscritta con il ponte statusline → file → hook |
| `PreToolUse` | Decisioni `allow`, `deny`, `ask`, `defer`. Exit 2 blocca. Il filtro `if` accetta una regola come `Bash(git *)` o `Edit(*.ts)`, ma è «best effort» | Effetti esterni con `ask`, cioè con la conferma nativa (voce 6). Il filtro sui comandi Bash non è a prova di aggiramento: il controllo finale resta a `finish` e sulla PR |
| `PostToolUse` può rimandare indietro un file appena scritto? | Sì, con `decision: "block"` e `reason`, oppure con exit 2 | Voce 13 fattibile: il piano salvato senza le sezioni obbligatorie torna indietro |
| `SessionStart` | Matcher `startup`, `resume`, `clear`, `compact`. Il contesto aggiunto ha un limite di 10.000 caratteri | Voce 41: bastano poche righe di stato |
| `TaskCompleted` | Esiste e con exit 2 impedisce di segnare una task come completata. Non è documentato se scatta alla fine di un subagente | Non ci appoggiamo: usiamo `SubagentStop` |
| Un plugin può dipendere da Superpowers? | Sì: `dependencies` in `.claude-plugin/plugin.json`, anche con un vincolo di versione | Dichiariamo `superpowers` con un intervallo di versioni |
| Dove salvare i dati del plugin | Gli hook ricevono `CLAUDE_PLUGIN_ROOT` e `CLAUDE_PLUGIN_DATA`; quest'ultima persiste tra gli aggiornamenti | Il DB SQLite va in `CLAUDE_PLUGIN_DATA` invece che in `~/.local/state/tollgate` |
| Tipi di handler degli hook | `command`, `http`, `mcp_tool`, `prompt`, `agent` (quest'ultimo sperimentale) | Usiamo solo `command`. `http` servirà per la dashboard |
| `claude plugin eval` | Esiste. Struttura `evals/<caso>/prompt.md` più `graders/`. 3 esecuzioni per caso, soglia predefinita 1.0 | Base per il sotto-progetto D |

Ancora da rileggere sulla pagina completa prima di scrivere codice: `updatedInput` e la semantica di `defer` in `PreToolUse`, i campi di input di `PreCompact`, e **se un plugin può impostare la statusline** o se serve un comando di installazione che la configuri in `settings.json`.

Note sulla statusline importata, da decidere prima della versione pubblica:
- interroga `api.anthropic.com/api/oauth/usage` con il token OAuth locale. È un endpoint non documentato, quindi va bene per uso personale ma è da rendere opzionale nella versione pubblica;
- a ogni aggiornamento scrive l'intero input JSON in `statusline.log`, che cresce senza limite.

## Prossimi passi

1. Tu rivedi questo documento e indichi i numeri da cambiare.
2. Rivedo la sezione 2 del design (il ciclo di vita del task) con il gruppo 6 dentro: ogni passaggio di fase diventa un punto in cui si può ripartire da zero.
3. Poi le sezioni rimanenti del design: hook e ricevute, schema del DB, gestione degli errori, test.
4. Spec scritta in `docs/superpowers/specs/`, revisione tua, poi piano con `writing-plans`.
