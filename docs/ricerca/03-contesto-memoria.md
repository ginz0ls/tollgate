# Ricerca 03: contesto, memoria e degrado nelle sessioni lunghe (per tollgate)

Data: 2026-10-08. Legenda: [V] pagina aperta e letta (abstract o HTML/testo completo, indicato); [S] solo fonte secondaria (risultato di ricerca). Numeri riportati solo se letti nella fonte indicata. Le soglie marcate "INFERENZA" sono mie, non dei paper.

## A. Degrado con la lunghezza del contesto

### A1. Lost in the Middle: How Language Models Use Long Contexts [V, HTML]
- Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni, Liang. 2023, TACL. https://arxiv.org/abs/2307.03172
- Fatto: QA multi-documento (10/20/30 documenti) e key-value retrieval (75/140/300 coppie) variando la posizione dell'informazione rilevante. Modelli: LongChat-13B, MPT-30B-Instruct, GPT-3.5-Turbo (anche 16K), Claude-1.3 (anche 100K); GPT-4 su sottoinsieme.
- Risultato: curva a U (meglio inizio e fine). GPT-3.5-Turbo: closed-book 56.1%, oracolo 88.3%; con 20/30 documenti il caso peggiore (info a meta') scende sotto il closed-book. Calo oltre 20 punti secondo la posizione. Retriever-reader: da 20 a 50 documenti guadagno solo ~1.5% (GPT-3.5) e ~1% (Claude). Query ripetuta prima e dopo i dati porta il key-value a quasi 100%, ma non cambia il trend sul QA.
- Limiti: modelli del 2023; i modelli attuali sono molto meno sensibili (non misurato qui).
- Implicazione tollgate: nei brief ai subagenti mettere istruzioni e obiettivo all'inizio E ripeterli in coda; niente liste lunghe di documenti. Piu' contenuto non aiuta (plateau a 20 doc).

### A2. RULER: What's the Real Context Size of Your Long-Context Language Models? [V, HTML]
- Hsieh, Sun, Kriman, Acharya, Rekesh, Jia, Zhang, Ginsburg. 2024, COLM 2024. https://arxiv.org/abs/2404.06654
- Fatto: 13 task sintetici (NIAH multi-needle, multi-hop tracing, aggregazione, QA), 17 modelli.
- Risultato: solo circa meta' dei modelli mantiene prestazione soddisfacente a 32K pur dichiarando >=32K. Lunghezza "effettiva" (soglia 85.6%): GPT-4 64K su 128K dichiarati (96.6 a 4K, 81.2 a 128K); Llama3.1 70B 64K; Qwen2 72B 32K; Yi-34B 32K su 200K; Mistral-7B 16K su 32K. Distrattori estremi: Yi -40 punti a 256K. Da 1 a 8 query: circa -15 punti.
- Limiti: sintetico; modelli 2024; non misura posizione.
- Implicazione: la finestra dichiarata non e' la finestra utile. Il budget di lavoro va fissato molto sotto il massimo.

### A3. NoLiMa: Long-Context Evaluation Beyond Literal Matching [V, abstract]
- Modarressi, Deilamsalehy, Dernoncourt, Bui, Rossi, Yoon, Schuetze. 2025, ICML 2025. https://arxiv.org/abs/2502.05167
- Fatto: NIAH con minima sovrapposizione lessicale needle-domanda; 13 LLM con >=128K dichiarati.
- Risultato: a 32K, 11 modelli su 13 sotto il 50% del loro baseline corto; GPT-4o da 99.3% a 69.7% a 32K; forte sotto 1K token. Reasoning/CoT non eliminano il calo.
- Limiti: task sintetico; modelli del 2025 iniziale.
- Implicazione: il recupero semantico (non letterale) degrada gia' a ~32K. Nei brief usare gli stessi termini del codice (nomi file, simboli) invece di parafrasi.

### A4. Context Rot: How Increasing Input Tokens Impacts LLM Performance [V]
- Hong, Troynikov, Huber (Chroma). 14 luglio 2025, technical report. https://www.trychroma.com/research/context-rot
- Fatto: 18 LLM (GPT-4.1, Claude 4, Gemini 2.5, Qwen3); NIAH semantico, LongMemEval (circa 113k token vs circa 300 focalizzati), Repeated Words; 194.480 chiamate.
- Risultato: calo con la lunghezza in tutti gli esperimenti, piu' ripido con bassa similarita' needle-domanda; anche UN distrattore abbassa l'accuratezza, quattro peggio; haystack mescolato meglio di quello coerente; su LongMemEval prompt focalizzato sempre meglio del completo (gap maggiore per Claude, per astensioni); thinking aiuta ma non chiude il gap.
- Limiti (dichiarati): task semplici, lunghezza non separata dalla difficolta', meccanismi non spiegati, pochi topic. Report di un vendor di vector DB.
- Implicazione: dare al subagente solo il contesto focalizzato (task + file toccati), non la cronologia. Conferma il design "brief su file".

### A5. Context Length Alone Hurts LLM Performance Despite Perfect Retrieval [V, HTML]
- Du, Tian et al. (10 autori). 2025, arXiv:2510.05381 (venue non indicato). https://arxiv.org/abs/2510.05381
- Fatto: 5 LLM (Llama-3.1-8B, Mistral-7B, GPT-4o, Claude, Gemini) su VarSum, GSM8K, MMLU, HumanEval; riempimento con saggi, spazi bianchi, o token mascherati.
- Risultato: anche con distrattori sostituiti da whitespace o mascherati la prestazione cala: modelli aperti da -7.9% fino a -50% a 30K (es. Llama HumanEval -50.0 mascherato a 30K). Con whitespace e prove subito prima della domanda cali fino a ~20%. Mitigazione "recita prima le evidenze": GSM8K Mistral a 26.250 token da 35.5% a 66.7%; RULER GPT-4o fino a +4 punti.
- Limiti: solo 2 modelli aperti + 3 chiusi, 4 task; modelli chiusi spesso non testati sulla mitigazione; nel paper Claude indicato come 3.7-Sonnet nel testo e 3.5 in tabella (incoerenza).
- Implicazione: la sola lunghezza costa, indipendentemente da cosa c'e' dentro. Argomento piu' forte per "una fetta per sessione" e subagenti puliti. Mitigazione utile: far riassumere/citare le evidenze prima di agire (nei brief di review).

### A6. LongBench [V, abstract]
- Bai et al. (13 autori). 2023, ACL 2024. https://arxiv.org/abs/2308.14508
- 21 dataset, 6 categorie, bilingue; finding: la compressione/retrieval aiuta i modelli con debole capacita' long-context ma restano indietro. Poco rilevante per soglie; citato per completezza. Letto solo l'abstract.

### A7. Large Language Models Can Be Easily Distracted by Irrelevant Context [V, abstract]
- Shi, Chen, Misra, Scales, Dohan, Chi, Schaerli, Zhou. 2023, ICML 2023. https://arxiv.org/abs/2302.00093
- GSM-IC: aritmetica con informazione irrilevante; prestazione "decresce drasticamente". Mitigazioni: self-consistency, istruzione "ignora l'irrilevante". Numeri non letti (solo abstract).
- Implicazione: output grezzo dei comandi dentro il contesto = distrattori; conferma "output su file".

## B. Conversazioni multi-turno, istruzioni

### B1. LLMs Get Lost In Multi-Turn Conversation [V, HTML]
- Laban, Hayashi, Zhou, Neville. 2025, arXiv:2505.06120 (nessun venue peer-reviewed in pagina). https://arxiv.org/abs/2505.06120
- Fatto: 15 LLM, 6 task, oltre 200.000 conversazioni simulate; istruzione "sharded" in piu' turni vs completa in un turno.
- Risultato: calo medio 39% (circa 90% -> 65%). Attitudine (90mo percentile) -16% circa, inaffidabilita' +112%. Controllo Concat al 95.1% di Full, quindi non e' perdita d'informazione. Recap finale (GPT-4o 76.6 vs Sharded 59.1) e Snowball (65.3) recuperano in parte. Temperatura 0 non risolve (inaffidabilita' ~30%). Perdita gia' con 2+ turni. Consiglio degli autori: ripartire da una nuova conversazione con i requisiti consolidati.
- Limiti: utente simulato, task analitici, solo inglese.
- Implicazione: forte supporto a /clear + ripresa da DB con requisiti consolidati. Anche l'orchestratore, se accumula turni di chiarimento, degrada: consolidare la spec in un file e riavviare.

### B2. How Many Instructions Can LLMs Follow at Once? (IFScale) [V, HTML]
- Jaroslawicz, Whiting, Shah, Maamari (Distyl AI). 2025, NeurIPS 2025 (listing). https://arxiv.org/abs/2507.11538
- Fatto: 10-500 istruzioni di inclusione di keyword in un report, 20 modelli.
- Risultato: migliore 68.9% (Gemini 2.5 Pro) a 500 istruzioni; Claude Sonnet 4 42.9%, Opus 4 44.6%, GPT-4.1 48.9%. Pattern: soglia (gemini-2.5-pro 98.4% a 100, 84.8% a 250), lineare (GPT-4.1 95.4% a 100, 74.0% a 250), esponenziale. Bias verso le istruzioni precoci (primacy), errori di omissione dominanti.
- Limiti: istruzioni banali (keyword), un solo tipo di task.
- Implicazione: le regole di tollgate in CLAUDE.md/prompt vanno contate: poche decine al massimo, le piu' importanti per prime, il resto imposto da hook (non da prosa).

## C. File di contesto per agenti

### C1. Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents? [V, HTML v1]
- Gloaguen, Muendler, Mueller, Raychev, Vechev (ETH). arXiv:2602.11988, feb 2026; ICLR 2026. https://arxiv.org/abs/2602.11988
- Fatto: AGENTbench (138 istanze Python, 12 repo con file di contesto scritti da sviluppatori) + SWE-bench Lite (300). Claude Code/Sonnet-4.5, Codex GPT-5.2 e 5.1-mini, Qwen Code. Condizioni: nessun file, generato da LLM, scritto da umani.
- Risultato: file LLM-generati peggiorano in 5 casi su 8; risoluzione media -0.5% (SWE-bench Lite) e -2% (AGENTbench); passi +2.45/+3.92; costo +20%/+23%. File umani: meglio di quelli LLM per tutti e 4 gli agenti, meglio del nessun-file per tutti tranne Claude Code; costo fino a +19%. Le panoramiche del codebase non fanno trovare prima i file giusti. Rimuovendo tutta la documentazione, i file LLM aiutano (+2.7%): duplicano la documentazione esistente. Le istruzioni sono seguite alla lettera (uv 1.6 volte per istanza se citato vs <0.01). Raccomandazione: omettere file LLM-generati; solo requisiti minimi (tooling specifico).
- Limiti: quasi solo Python; solo successo misurato; il paper stesso ha incoerenze (4% nell'introduzione vs 2% nella sezione 4.2).
- Implicazione: CLAUDE.md/AGENTS.md di tollgate corti, scritti a mano, solo comandi build/test e vincoli non deducibili; MAI generati con /init; niente mappe di directory. Ogni riga e' un obbligo che l'agente eseguira' (e paghera' in passi e costo).

### C2. AGENTS.md outperforms skills in our agent evals [V]
- Jude Gao (Vercel). 27 gen 2026, blog. https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Fatto: eval su API Next.js 16 fuori dal training. Pass rate: baseline 53%; skill default 53% (skill mai invocata nel 56% dei casi); skill con istruzioni esplicite 79%; indice docs da 8KB in AGENTS.md 100% (da 40KB iniziali).
- Limiti (dichiarati): una sola suite, un framework, "working theory", vendor che promuove il proprio CLI, sensibile alla formulazione.
- Implicazione/CONTRADDIZIONE parziale: la conoscenza passiva e compatta batte il caricamento on-demand quando l'agente non sa di dover cercare. Per tollgate: le skill/profili non vanno lasciati alla decisione del modello: l'hook o l'orchestratore deve iniettare il profilo giusto nel brief (iniezione deterministica), con indice piccolo (<=8KB come ordine di grandezza visto).

## D. Compattazione, riassunto, memoria

### D1. The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management [V, HTML v3]
- Lindenbauer, Slinko, Felder, Bogomolov, Zharov (JetBrains Research/TUM). arXiv:2508.21433, 2025; NeurIPS 2025 (listing). https://arxiv.org/abs/2508.21433
- Fatto: SWE-agent su SWE-bench Verified, 5 configurazioni. Masking: finestra M=10 turni, osservazioni piu' vecchie sostituite da segnaposto. Summary: N=21 turni, ultimi 10 intatti.
- Risultato: costo circa -50% per entrambi (es. Qwen3-Coder 480B: raw 53.4%/$1.29; masking 54.8%/$0.61; summary 53.8%/$0.64). Summary allunga le traiettorie (+15% Qwen3-Coder). Su Gemini 2.5 Flash thinking entrambi peggiorano (40.4 -> 36.4 / 31.4). Ibrido: -7% costo vs masking, -11% vs summary. Costo del riassunto 0.65%-7.2% del costo istanza.
- Limiti: solo SWE; finestra da ritarare per scaffold (OpenHands richiede retuning); trigger fissi.
- Implicazione: la tecnica piu' semplice (nascondere i vecchi output dei tool, tenere le azioni) basta. In tollgate "output su file" e' gia' una forma di masking: il contesto contiene il percorso e 1-3 righe, non l'output.

### D2. ACON: Optimizing Context Compression for Long-horizon LLM Agents [V, HTML v2]
- Kang, Chen, Han, Inan, Wutschitz, Chen, Sim, Rajmohan (KAIST/Microsoft/Cambridge). arXiv:2510.00615, 2025; ICLR 2026 e ICML 2026 (listing). https://arxiv.org/abs/2510.00615
- Fatto: linee guida di compressione ottimizzate confrontando traiettorie riuscite senza compressione e fallite con; AppWorld, OfficeBench, 8-objective QA; gpt-4.1.
- Risultato: picco token -26% (AppWorld 9.93k -> 7.33k, accuratezza 56.0 -> 56.5), -32% OfficeBench (76.84 -> 74.74), -54% QA (10.35k -> 4.71k). Baseline: FIFO 5 turni 45.8, retrieval 27.4, LLMLingua 39.3, prompting ingenuo 43.5 su AppWorld. Compressore distillato mantiene >95%. La compressione della storia puo' AUMENTARE il costo perche' rompe la cache KV. Soglie moderate migliori (4096 token storia, 1024 osservazioni).
- Limiti: quasi solo modelli GPT; overhead e latenza.
- Implicazione: una compattazione generica (prompt ingenuo) perde ~12 punti (43.5 vs 56.5): non affidarsi alla compattazione automatica di Claude Code come strategia; meglio stato esplicito su DB. Contesti di lavoro di ordine 5-10k token erano sufficienti in questi benchmark.

### D3. Agentic Context Engineering (ACE): Evolving Contexts for Self-Improving Language Models [V, abstract + HTML v3]
- Zhang, Hu, Upasani et al. (13 autori; Stanford, SambaNova, Berkeley). arXiv:2510.04618, ICLR 2026. https://arxiv.org/abs/2510.04618
- Fatto: il contesto come "playbook" aggiornato con generazione, riflessione, curatela a delta; +10.6% agenti, +8.6% finanza (claim degli autori). AppWorld (DeepSeek-V3.1): ReAct 42.4 -> 59.5 online.
- Fenomeni chiave: brevity bias e context collapse: riscrivere tutto il contesto a ogni passo lo ha fatto passare da 18.282 token (accuratezza 66.7) a 122 token (57.1) in un passo, sotto il baseline 63.7. Limiti: dipende da un Reflector forte e da feedback affidabile (FiNER online senza etichette -3.4 vs base).
- Implicazione: i riassunti riscritti ogni volta perdono dettagli. Lo stato di ripresa (DB) deve essere aggiornato a delta (append/patch), mai riscritto integralmente da un LLM.

### D4. MemGPT: Towards LLMs as Operating Systems [V, abstract]
- Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez. 2023, arXiv:2310.08560. https://arxiv.org/abs/2310.08560
- Memoria a livelli (contesto principale vs esterna) con gestione "virtual context". Nessun numero letto.
- Implicazione: concettualmente e' il pattern DB + file di tollgate (contesto = RAM, DB/file = disco); non porta soglie.

### D5. Evaluating Context Compression for AI Agents [V; vendor]
- Factory Research. 16 dic 2025, blog. https://factory.com/news/evaluating-compression (redirect da factory.ai)
- Probe-based, giudice GPT-5.2, 36.611 messaggi da sessioni reali. Punteggi 0-5: Factory 3.70, Anthropic 3.44, OpenAI 3.35. "Artifact trail" (quali file toccati) debole per tutti: 2.19-2.45.
- Limiti: valutazione del proprio prodotto, un solo giudice, nessuna significativita'.
- Implicazione: dopo compattazione l'agente dimentica cosa ha modificato. In tollgate l'elenco dei file toccati va in DB/git, non nella memoria della conversazione.

### D6. Effective context engineering for AI agents [V]
- Rajasekaran, Dixon, Ryan, Hadfield (Anthropic Applied AI). 29 set 2025. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Contesto = risorsa finita con rendimenti decrescenti; compattazione, note strutturate, sub-agenti con finestra pulita che restituiscono ~1.000-2.000 token, retrieval just-in-time. Nessuna soglia numerica di sessione.
- Implicazione: allineato al design; il ritorno di un subagente va limitato a ~1-2k token (+ riferimento al file report).

### D7. Context Engineering for AI Agents: Lessons from Building Manus [V]
- Yichao "Peak" Ji. 18 lug 2025. https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- Hit rate della cache KV, rapporto input:output circa 100:1, differenza di prezzo circa 10x tra token cache e non; non togliere/aggiungere tool a meta' run (mascherare); file system come memoria; compressione reversibile (tieni l'URL); todo.md ricitato per limitare il drift su ~50 chiamate; tenere gli errori nel contesto.
- Implicazione: prefisso stabile (niente timestamp nel prompt iniziale); /clear azzera la cache ma e' accettabile, i subagenti con brief fisso beneficiano di prefisso identico.

## E. Contesto a livello di repository

### E1. RepoCoder [V, abstract]
- Zhang, Chen, Zhang, Keung, Liu, Zan, Mao, Lou, Chen. EMNLP 2023. https://arxiv.org/abs/2303.12570
- Retrieve-and-generate iterativo; +oltre 10% sulla baseline In-File in tutti i setting (da abstract; per-setting non letto). Implicazione: il contesto del repo si recupera on-demand per task, non si precarica.

### E2. CodeRAG-Bench: Can Retrieval Augment Code Generation? [V, HTML v2]
- Wang, Asai, Yu, Xu, Xie, Neubig, Fried. arXiv:2406.14497, NAACL 2025 Findings. https://arxiv.org/abs/2406.14497
- Il retrieval aiuta (GPT-4o SWE-bench 2.3 -> 30.7 con documenti gold; 21.7 con retrieval reale) ma puo' danneggiare (DeepSeekCoder-7B HumanEval 70.1 -> 53.0). Top-5 documenti ottimale; piu' documenti a basso rango aggiungono rumore; il codice locale del repo batte le fonti esterne.
- Limiti: solo Python; metodi vanilla.
- Implicazione: nei brief, al massimo ~5 riferimenti mirati (file/simboli) per task; non scaricare cartelle.

### E3. Aider repo map [V, documentazione ufficiale]
- https://aider.chat/docs/repomap.html. Mappa di file e simboli piu' referenziati, ranking su grafo, budget di default 1k token (--map-tokens). Nessun numero di efficacia in pagina.
- Implicazione: una mappa compatta (~1k token) generata da tool (non da LLM) e' una alternativa ai "panorami" nei CLAUDE.md, che C1 dice inefficaci. Da valutare: non c'e' evidenza sperimentale qui.

## F. Tool/skill caricati progressivamente

### F1. Introducing advanced tool use on the Claude Developer Platform [V; vendor]
- Bin Wu e team Anthropic. 24 nov 2025. https://www.anthropic.com/engineering/advanced-tool-use
- 58 tool da 5 server = circa 55K token; con Tool Search ~8.7K totali (-85%). Accuratezza MCP eval (interne): Opus 4 49% -> 74%, Opus 4.5 79.5% -> 88.1%. Fallimenti tipici: tool con nomi simili.
- Limiti: test interni, non indipendenti.
- Implicazione: meno definizioni visibili = scelta migliore e contesto libero. Conferma "nessuna meta-skill grande iniettata". Auditare i server MCP del progetto: ognuno costa token a ogni turno.

### F2. RAG-MCP [V, HTML]
- Gan, Sun. arXiv:2505.03275, 2025. https://arxiv.org/abs/2505.03275
- Tabella: RAG-MCP 43.13% con 1084 token di prompt vs tutti nel prompt 13.62% con 2133.84. Degrado qualitativo oltre ~30 tool, dominano i fallimenti oltre ~100 (analisi imprecisa).
- Limiti: 20 prove per baseline, un modello (qwen-max), nessun intervallo di confidenza, valutatore incoerente. Evidenza debole.
- Implicazione: indicativo, non usare come numero: tenere i tool attivi sotto ~30 e' un'euristica, non un risultato solido.

## G. Sub-agenti con contesto isolato

### G1. How we built our multi-agent research system [V; vendor]
- Anthropic. https://www.anthropic.com/engineering/multi-agent-research-system (titolo esatto non letto nella pagina; la pagina e' quella indicata)
- Multi-agente (Opus 4 lead + Sonnet 4) +90.2% sulla eval interna vs Opus 4 singolo; su BrowseComp l'utilizzo di token spiega 80% della varianza (3 fattori = 95%); agenti ~4x token di una chat, multi-agente ~15x. Piano salvato in memoria esterna perche' oltre 200K si tronca; subagenti scrivono su filesystem e restituiscono riferimenti. Deleghe vaghe causano lavoro duplicato. Limiti dichiarati: i task di coding hanno meno parallelizzazione; male per task con contesto condiviso o molte dipendenze.
- Implicazione: un subagente per task e' coerente (brief con obiettivo, formato output, confini), ma il costo in token puo' essere un multiplo. Prevedere budget e non spawnare per task banali (regole di scala dello sforzo).

## Soglie numeriche proposte (INFERENZA dalle evidenze sopra, da tarare con misure su tollgate)

| Cosa | Soglia suggerita | Base |
|---|---|---|
| Contesto di lavoro del subagente | obiettivo sotto ~30K token totali | NoLiMa (32K: 11/13 modelli <50% baseline), RULER (meta' dei modelli non regge 32K), Du et al. (cali gia' a 7.5K-30K) |
| Orchestratore: avviso | ~40% della finestra dichiarata o ~60-80K token assoluti, il minore | Lunghezza effettiva ~meta' della dichiarata (RULER) |
| Orchestratore: stop, salvataggio stato e /clear | ~50-60% della finestra, non all'auto-compact | Fonti secondarie [S] indicano auto-compact di Claude Code a circa 83.5% con buffer ~33K, non verificato su documentazione ufficiale; ACON/ACE mostrano perdite con compressione ingenua |
| Ritorno di un subagente all'orchestratore | 1-2K token + percorso file | Anthropic context engineering |
| Frontiera masking | tenere ultimi ~10 turni di osservazioni | Complexity Trap (M=10, da ritarare) |
| File di contesto | poche decine di righe, solo comandi e vincoli non deducibili | AGENTS.md study, IFScale |
| Riferimenti per brief | <=5 file/simboli | CodeRAG-Bench |
| Tool/MCP attivi | quanto meno possibile; definizioni totali sotto ~10K token | Advanced tool use (55K per 58 tool) |

## Evidenze che CONTRADDICONO o complicano le scelte di tollgate
1. Vercel (C2): la conoscenza passiva e compatta batte le skill caricate on-demand (skill mai invocata nel 56% dei casi). Rischio per i "profili per tipo di file" se dipendono dal fatto che il modello li carichi: serve iniezione deterministica da hook.
2. Multi-agent (G1): ~15x token e poca idoneita' al coding con contesto condiviso; "un subagente per task + review + verifica" moltiplica il costo. Va misurato.
3. ACON (D2) e Manus (D7): riavviare la sessione e comprimere la storia rompe la cache KV e puo' aumentare il costo; /clear a ogni fetta ha un costo di ricarica.
4. Complexity Trap (D1): il riassunto LLM non batte il masking semplice e allunga le traiettorie; quindi il "riassunto" per la ripresa non deve essere un LLM che riscrive, ma stato strutturato.
5. AGENTS.md study (C1): anche i file umani aiutano poco (non per Claude Code) e costano fino a +19%; le "poche righe di stato all'avvio" e ogni istruzione vanno giustificate con misure.
6. Factory (D5): il tracciamento degli artefatti dopo compattazione e' debole per tutti; la ripresa da DB deve contenere esplicitamente i file toccati.
7. Lost in the Middle (A1) e' del 2023: i modelli attuali sono meno sensibili; non usare come motivo principale.

## Non trovato / non letto
- Studi su ACE/summarization specifici per coding agent oltre D1, D5; "CodeRAG" come sistema distinto non cercato separatamente (usato CodeRAG-Bench).
- Documentazione ufficiale sulla soglia di auto-compact di Claude Code: solo [S].
- Per LongBench, MemGPT, RepoCoder, Shi et al. letti solo gli abstract.
