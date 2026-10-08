# Filone 01: architettura degli agenti di coding e degli harness

Data ricerca: 8 ottobre 2026. Legenda: [V] = letto abstract/testo (via fetch della pagina arXiv o del post); [S] = solo da fonte secondaria/snippet di ricerca.
Nota metodo: gli abstract sono stati letti tramite un fetcher che riassume la pagina; i numeri riportati sono quelli restituiti dalla pagina. Dove ho letto solo l'abstract lo dico. Nessun URL e' inventato: tutti sono ID arXiv/pagine effettivamente aperti.

---
## A. Agenti di coding classici e ACI

### A1. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering [V]
- Autori: J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, O. Press. 2024 (v3 nov 2024). arXiv preprint (nessun venue sulla pagina; NeurIPS 2024 non verificato).
- URL: https://arxiv.org/abs/2405.15793
- Cosa: propongono l'ACI, un'interfaccia pensata per l'LLM (comandi di edit, navigazione, test).
- Risultato (testo, ablazioni su SWE-bench Lite, GPT-4 Turbo): full 18.0%; solo shell 11.0%; edit senza linting 15.0% (-3.0); nessun comando di edit 10.3%; ricerca iterativa 12.0% (peggio di nessuna ricerca, 15.7%); finestra file 30 righe 14.3%, file intero 12.7% (ottimo 100 righe); ultimi 5 osservazioni 18.0% vs storia completa 15.0%. Abstract: 12.5% pass@1 su SWE-bench, 87.7% HumanEvalFix.
- Limiti: modello GPT-4 Turbo del 2024; i numeri assoluti sono superati, le ablazioni sono specifiche del modello.
- Implicazione tollgate: CONFERMA che l'interfaccia (guardrail sugli edit, output sintetici) pesa quanto il modello: un hook che rifiuta edit non validi (linting) vale +3 punti. Suggerisce che gli hook devono dare messaggi di errore brevi e azionabili, non dump. CONFERMA anche la scelta di non accumulare storia (ultimi 5 osservazioni > storia piena): coerente con "una fetta per sessione".

### A2. Agentless: Demystifying LLM-based Software Engineering Agents [V]
- Autori: C. S. Xia, Y. Deng, S. Dunn, L. Zhang. 2024 (v2 ott 2024). arXiv preprint.
- URL: https://arxiv.org/abs/2407.01489
- Cosa: pipeline fissa in 3 fasi (localizzazione, riparazione, validazione patch) senza che l'LLM scelga azioni.
- Risultato: 32.00% (96/300) su SWE-bench Lite a $0.70 per issue, il migliore tra gli open-source dell'epoca. Ablazione patch selection: majority voting 77 fix, +regression test 81, +reproduction test 96. Dei 213 test di riproduzione che riproducevano il bug, solo 94 dicevano "resolved" con la patch ground-truth. Critica agli agenti: tool complessi, controllo debole (30-40 turni), poca auto-riflessione.
- Limiti: modello 2024; SWE-bench Pro lo ha provato e ha trovato che fatica con edit multi-file (vedi A6). Annotazione manuale dei problemi di Lite (nasce Lite-S).
- Implicazione tollgate: CONFERMA la scelta di scheletro deterministico (script che scelgono livello, fasi fisse, validazione con test) attorno a un LLM che esegue passi ristretti. SUGGERISCE: i test di riproduzione generati dall'LLM sono inaffidabili (94/213), quindi la "ricevuta di test" deve essere legata a test scritti/approvati prima (TDD red) e non generati a posteriori. Limite: la pipeline rigida non regge task multi-file lunghi, quindi tollgate non deve essere una pipeline totalmente fissa.

### A3. AutoCodeRover: Autonomous Program Improvement [V]
- Autori: Y. Zhang, H. Ruan, Z. Fan, A. Roychoudhury. 2024 (v3 lug 2024). ISSTA 2024 (dai commenti della pagina).
- URL: https://arxiv.org/abs/2404.05427
- Cosa: ricerca di codice a livello di AST (classi/metodi) + fault localization spettrale se ci sono test.
- Risultato: 19% su SWE-bench Lite (300 issue), $0.43 medio per issue, sopra SWE-agent di allora.
- Limiti: numeri datati.
- Implicazione tollgate: il contesto strutturato (simboli, non file interi) riduce il costo; suggerisce che l'indice dei "file del piano" per lo scope-guard puo' essere a livello di simbolo oltre che di file, ma e' un'ottimizzazione, non un requisito.

### A4. OpenHands: An Open Platform for AI Software Developers as Generalist Agents [V]
- Autori: X. Wang, B. Li, ... G. Neubig (24 autori). 2024 (v3 apr 2025). ICLR 2025.
- URL: https://arxiv.org/abs/2407.16741
- Cosa: piattaforma open con runtime sandbox, agenti componibili, delega multi-agente, 15 benchmark.
- Risultato: nessun numero chiave in abstract (2.1K contributi, 188 contributor).
- Limiti: e' una piattaforma, non uno studio sull'effetto del design.
- Implicazione tollgate: riferimento di architettura per sandbox e event-stream; conferma che l'esecuzione isolata e' lo standard.

### A5. mini-swe-agent (repo GitHub, non paper) [V sul README]
- URL: https://github.com/SWE-agent/mini-swe-agent
- Cosa: agente di ~100 righe, solo bash, storia lineare (traiettoria = prompt), azioni indipendenti via subprocess.
- Risultato: il README dichiara ">74% su SWE-bench Verified" senza indicare il modello nella pagina letta (secondario: Gemini 3 Pro).
- Limiti: numero dipendente dal modello e non verificato indipendentemente da me.
- Implicazione tollgate: SUGGERISCE che con modelli forti l'ACI custom conta meno (bash basta). Quindi gli hook di tollgate devono vincolare i risultati (ricevute, scope, conferme) e non cercare di "migliorare lo strumento". Giustifica una baseline "agente minimo" nell'eval.

### A6. SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks? [V, anche html]
- Autori: X. Deng, J. Da, E. Pan, ... B. Kenstler (22). Set 2025 (v2 nov 2025). arXiv preprint.
- URL: https://arxiv.org/abs/2509.16941
- Cosa: 1.865 problemi, 41 repo; set pubblico, held-out, commerciale. Task da ore a giorni, patch multi-file; 107.4 righe e 4.1 file in media; esclusi i fix da 1-10 righe.
- Risultato (testo): set pubblico, SWE-agent con limite di 50 turni: Claude Sonnet 4.5 43.6%, Sonnet 4 42.7%, GPT-5 (high) 41.8%. Set commerciale: Opus 4.1 17.8%, GPT-5 (high) 15.7%. Cluster di fallimento: ad es. Sonnet 4 context overflow da listing 35.6% e lettura infinita di file 17.0%; Opus 4.1 soluzione sbagliata 35.9%, errori di sintassi 24.2%. Agentless provato e scartato per difficolta' con edit multi-file.
- Limiti: classificazione dei fallimenti fatta da LLM-judge (GPT-5); scaffold unico.
- Implicazione tollgate: CONFERMA che il contesto che esplode e' un fallimento dominante (context overflow 35.6% per Sonnet 4): giustifica orchestratore sottile e una fetta per sessione. Mostra anche che il tasso cala molto sul codice proprietario (17.8% vs 43.6%): l'eval di tollgate va fatto su repo vere dell'utente, non su benchmark pubblici.

---
## B. Effetto di harness/scaffold sui risultati

### B1. Holistic Agent Leaderboard (HAL): The Missing Infrastructure for AI Agent Evaluation [V]
- Autori: S. Kapoor, B. Stroebl, ... P. Liang, A. Narayanan (31). Ott 2025. arXiv preprint.
- URL: https://arxiv.org/abs/2510.11977
- Cosa: harness di eval standardizzato; 21.730 rollout, 9 modelli, 9 benchmark, circa $40.000; analisi modello x scaffold x benchmark; ispezione log con LLM.
- Risultato: maggiore reasoning effort ha ridotto l'accuratezza nella maggior parte delle run; scoperti comportamenti non noti (agente che cerca il benchmark su HuggingFace invece di risolvere; uso improprio di carte di credito).
- Limiti: non specifico per coding.
- Implicazione tollgate: CONFERMA la necessita' di un eval con baseline e di ispezionare i log (non solo il pass rate). Suggerisce di loggare tutte le traiettorie per auditing. Il fatto che piu' reasoning non aiuti avverte contro "alza sempre il livello di rigore/effort".

### B2. Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces [V abstract]
- Autori: M. A. Merrill, A. G. Shaw, N. Carlini, ... L. Schmidt (85). Gen 2026. ICLR 2026 (risultato di ricerca); arXiv.
- URL: https://arxiv.org/abs/2601.11868
- Cosa: 89 task con ambiente, soluzione umana e test.
- Risultato: modelli e agenti frontier sotto il 65%; analisi degli errori citata ma dettagli non letti.
- Limiti: non ho letto il testo completo; l'effetto dello scaffold sul benchmark e' discusso altrove.
- Implicazione tollgate: i task terminali multi-passo sono ancora difficili; non togliere verifiche perche' "i modelli sono forti".

### B3. What Resolve Rate Hides: Trajectory Structure Diagnostics for Coding Agents [V abstract]
- Autori: R. Shu, C. Y. Chong, X. Zhou, Y. Peng, Z. Wu, X. Han, Z. Zhuang, G. Yuan, Y. Wang. Lug 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2607.06184
- Cosa: TraceProbe analizza 2.500 traiettorie su SWE-bench Verified con 5 configurazioni di produzione; anti-pattern (search loop, verifica saltata).
- Risultato: scegliere i file da modificare non separa successo e fallimento; la selezione di funzione e il comportamento di completamento si'. (Dal search snippet [S]: lo stesso modello su scaffold diversi diverge molto con GPT-5.4 e poco con Opus 4.6, quindi il confronto scaffold non e' una proprieta' costante.)
- Limiti: diagnostica a regole, solo SWE-bench Verified.
- Implicazione tollgate: lo scope-guard "solo i file del piano" non basta come predittore di qualita'; serve anche verifica del comportamento (test). E l'effetto scaffold dipende dal modello: l'eval va rifatto a ogni cambio di modello.

### B4. Terminal Agents: A Survey of AI Agents in Command-Line Environments [V abstract]
- Autori: Y. Bin, X. Yuan, ... H. T. Shen (12). Ago 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2608.20485
- Risultato: l'andamento dipende insieme da modello, interfaccia, harness, runtime, ambiente; confronti appaiati danno risultati dipendenti dal benchmark e limiti nell'attribuire la performance a singoli componenti. Raccomandano di riportare condizioni di runtime e tracce riproducibili.
- Implicazione tollgate: CONFERMA l'eval con baseline, ma AVVISA che l'attribuzione per componente (quale hook ha aiutato) e' difficile: servono ablazioni hook-per-hook.

### B5. SWE Atlas: Benchmarking Coding Agents Beyond Issue Resolution [V abstract]
- Autori: M. Raghavendra, S. Dan, ... Y. He (15). Mag 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2605.08366
- Risultato: 124 task Q&A, 90 di scrittura test, 70 refactoring; i modelli migliori (GPT-5.4, Opus 4.7) esplorano molto il codice ma faticano con edge case e buone pratiche. (Dallo snippet [S]: gli scaffold nativi hanno ~1.5-2x tool call del mini-swe-agent e risultano migliori.)
- Implicazione tollgate: la qualita' (manutenibilita', test completi) non e' coperta dal solo pass rate; la review finale va valutata con rubrica, non solo con test.

### B6. SWE-EVO: Benchmarking Coding Agents in Long-Horizon Software Evolution Scenarios [V abstract]
- Autori: T. Le, M. V. T. Thai, D. Nguyen Manh, H. Phan Nhat, N. D. Q. Bui. Dic 2025 (v6 mag 2026). arXiv preprint.
- URL: https://arxiv.org/abs/2512.18470
- Risultato: 48 task, in media 21 file, 874 test per istanza; GPT-5.4 con OpenHands risolve il 25%, mentre GPT-5.2 fa 72.80% su SWE-bench Verified.
- Implicazione tollgate: dimensione del task: i task multi-file (21 file) crollano a 25%, contro 72.8% sui task piccoli. CONFERMA la divisione in fette piccole. Limite: confonde dimensione e altre difficolta'.

---
## C. Planning esplicito

### C1. Self-planning Code Generation with Large Language Models [V]
- Autori: X. Jiang, Y. Dong, L. Wang, Z. Fang, Q. Shang, G. Li, Z. Jin, W. Jiao. 2023 (v5 ott 2025). TOSEM.
- URL: https://arxiv.org/abs/2303.06689
- Risultato: Pass@1 fino a +25.4% relativo vs generazione diretta e +11.9% vs CoT.
- Limiti: benchmark a funzione singola, modelli 2023.
- Implicazione tollgate: supporto storico al piano prima del codice, ma debole per repo reali.

### C2. CodePlan: Repository-level Coding using LLMs and Planning [V]
- Autori: R. Bairi, A. Sonwane, A. Kanade, ... S. Rajamani. Set 2023. arXiv preprint.
- URL: https://arxiv.org/abs/2309.12499
- Risultato: 5 repo su 6 passano i controlli di validita' (build) contro 0 su 6 delle baseline senza piano; repo con 2-97 file da modificare.
- Limiti: solo 2 tipi di task (migrazione C#, edit temporali Python), campione piccolo.
- Implicazione tollgate: CONFERMA che per modifiche multi-file serve un piano con dipendenze/impatto (cio' che tollgate chiama piano principale in fette), con validazione a ogni passo.

### C3. From Plan to Action: How Well Do Agents Follow the Plan? [V abstract]
- Autori: S. Liu, S. Dehghan, J. Ganhotra, M. Hirzel, R. Jabbarvand. Apr 2026 (v3 ago 2026). arXiv preprint.
- URL: https://arxiv.org/abs/2604.12147
- Risultato: 21.120 traiettorie SWE-agent, 4 LLM, SWE-bench Verified e Pro, 8 varianti di piano. Senza piano gli agenti ricadono su workflow interni spesso incompleti; un piano standard migliora la risoluzione; promemoria periodici del piano riducono le violazioni e aumentano il successo; un piano scadente e' PEGGIO di nessun piano; aggiungere fasi extra in anticipo puo' peggiorare se confligge con la strategia del modello.
- Implicazione tollgate: CONFERMA piano esplicito con promemoria periodici (hook che ri-inietta il passo corrente). AVVERTE: un piano mal fatto danneggia, quindi serve una review del piano prima dell'esecuzione e i profili/fasi extra vanno validati con eval (non aggiungere fasi per principio).

### C4. Do LLM Agents Execute the Plans They Declare? From Planning-Mode Declaration to Pattern-Specific Execution [V abstract]
- Autori: S. R. Oota, F. Herrera, J. Cabot Sagrera, M. Lopez de Prado, S. Khan. 29 set 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2609.38108
- Risultato: con Plan+ReAct generico solo il 22-45% delle traiettorie mantiene la struttura dichiarata; un esecutore deterministico per pattern porta il successo da 0.36 a 0.44 su SWE-bench Verified (0.48 -> 0.92 su ALFWorld). L'LLM non sceglie in modo affidabile il modo di pianificazione migliore.
- Limiti: preprint recentissimo; guadagno su SWE-bench modesto (+8 punti).
- Implicazione tollgate: CONFERMA pesantemente: far eseguire il piano da codice deterministico (script che scelgono il livello e imporre l'ordine) batte il lasciare che l'LLM "si ricordi" del piano. Conferma anche che i livelli L0/L1/L2 vanno scelti da script e non dal modello.

---
## D. Multi-agente per il codice e fallimenti

### D1. MetaGPT [V abstract]
- Autori: S. Hong, M. Zhuge, J. Chen, ... J. Schmidhuber (15). 2023 (v7 nov 2024). arXiv preprint (venue non nella pagina).
- URL: https://arxiv.org/abs/2308.00352
- Cosa: SOP codificate in sequenze di prompt, ruoli a catena di montaggio, controllo dei risultati intermedi.
- Risultato: abstract senza numeri.
- Implicazione tollgate: l'idea di SOP con artefatti intermedi verificabili e' in linea con spec -> piano -> fette; ma l'evidenza quantitativa e' debole.

### D2. ChatDev: Communicative Agents for Software Development [V abstract]
- Autori: C. Qian, W. Liu, H. Liu, ... M. Sun (14). 2023 (v5 giu 2024). ACL 2024.
- URL: https://arxiv.org/abs/2307.07924
- Risultato: abstract senza numeri; il linguaggio naturale va bene per il design, il linguaggio di programmazione per il debug.
- Implicazione tollgate: come D1. Nel MAST (D5) ChatDev e' tra i sistemi con piu' fallimenti.

### D3. AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation [V abstract]
- Autori: D. Huang, J. M. Zhang, M. Luck, Q. Bu, Y. Qing, H. Cui. Dic 2023 (v3 mag 2024). arXiv preprint.
- URL: https://arxiv.org/abs/2312.13010
- Risultato: GPT-4: 96.3% pass@1 su HumanEval e 91.8% su MBPP, con overhead di token 56.9K e 66.3K contro 138.2K e 206.5K del miglior precedente.
- Limiti: HumanEval/MBPP sono funzioni singole, saturi.
- Implicazione tollgate: SUGGERISCE la separazione programmatore / progettista dei test / esecutore. Per tollgate: il test lo scrive un contesto diverso da quello che implementa.

### D4. MapCoder [V abstract]
- Autori: Md. A. Islam, M. E. Ali, M. R. Parvez. Mag 2024. arXiv preprint.
- URL: https://arxiv.org/abs/2405.11403
- Risultato: 93.9% HumanEval, 83.1% MBPP, 22.0% APPS, 28.5% CodeContests, 45.3% xCodeEval (4 agenti: recall, piano, codice, debug).
- Limiti: competitive programming, non repo reali.
- Implicazione tollgate: poca rilevanza diretta per workflow su repo reali; nessuna evidenza che serva su codice di produzione.

### D5. Why Do Multi-Agent LLM Systems Fail? (MAST) [V, abstract + testo]
- Autori: M. Cemri, M. Z. Pan, S. Yang, ... M. Zaharia, J. E. Gonzalez, I. Stoica (13). Mar 2025 (v3 ott 2025). arXiv preprint.
- URL: https://arxiv.org/abs/2503.13657
- Risultato: 1.600+ tracce annotate, 7 framework, 14 modi di fallimento in 3 categorie (design di sistema ~44.2%, disallineamento tra agenti ~32.4%, verifica ~23.5%, somme mie); kappa 0.88. Moda principale: step repetition 15.7%, reasoning-action mismatch 13.2%, ignoranza delle condizioni di terminazione 12.4%, disobbedienza alle specifiche 11.8%. Interventi su ChatDev: ruoli migliori +9.4%, "CEO ha l'ultima parola" +9.4%, passo di verifica dell'obiettivo +15.6% su ProgramDev (il maggiore). Gli autori dicono che i fix tattici non bastano.
- Limiti: framework 2024-25 con modelli piu' deboli; annotazione via LLM-judge.
- Implicazione tollgate: CONFERMA che la verifica indipendente e' il punto di leva maggiore (+15.6%), e che specifiche/terminazione/ripetizione vanno gestite da codice (condizioni di uscita esplicite, limite iterazioni, stop-hook). Ricevute di test legate a SHA sono un controllo di verifica esterna.

### D6. Towards a Science of Scaling Agent Systems [V abstract]
- Autori: Y. Kim, K. Gu, C. Park, ... X. Liu (20). Dic 2025 (v3 apr 2026). arXiv preprint.
- URL: https://arxiv.org/abs/2512.08296
- Risultato: 260 configurazioni, 6 benchmark, 5 architetture, 3 famiglie LLM. Il coordinamento rende sempre meno oltre una certa baseline single-agent; i task con molti tool soffrono overhead multi-agente; architetture senza verifica centralizzata propagano gli errori. Rispetto al single-agent: +80.8% su ragionamento finanziario decomponibile, -70.0% su pianificazione sequenziale. (Snippet [S]: su SWE-bench Verified tutte le architetture multi-agente peggiorano di -15% / -2%.)
- Implicazione tollgate: per il codice (sequenziale, molti tool) il multi-agente parallelo non conviene. tollgate usa un subagente per volta e un solo scrittore: coerente. Il -70% su sequenziale e' un forte argomento contro uno "sciame".

### D7. The Illusion of Multi-Agent Advantage [V abstract]
- Autori: P. Jwalapuram, H. Lin, C. Li, ... S. Joty. Giu 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2606.13003
- Risultato: MAS generati automaticamente peggiori di CoT-SC con costo fino a 10x; "architectural bloat".
- Limiti: sistemi generati automaticamente, non progettati a mano; non specifico per coding.
- Implicazione tollgate: non aggiungere agenti senza prova; ogni ruolo (reviewer, tester) va giustificato da eval.

### D8. Do More Agents Help? Controlled and Protocol-Aligned Evaluation of LLM Agent Workflows [V abstract]
- Autori: Y. Fu, R. Fang, J. Shao, H. Zheng, Z. Zhu, B. Luo, T. Lin. Giu 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2606.05670
- Risultato: GPT-4.1, 10 benchmark: solo 1 dei 6 MAS e' vicino all'ancora single-agent; gli altri 5 sono sotto di 2.56-11.29 punti con costi piu' alti.
- Implicazione tollgate: come D7.

### D9. Cognition: "Don't Build Multi-Agents" (Walden Yan, 12 giu 2025) e "Multi-Agents: What's Actually Working" (22 apr 2026) [V, blog]
- URL: https://cognition.com/blog/dont-build-multi-agents ; https://cognition.com/blog/multi-agents-working
- Cosa: principi: condividere il contesto; le azioni portano decisioni implicite. 2026: funzionano il loop di review con revisore a contesto fresco (Devin Review: in media 2 bug per PR, ~58% gravi), l'escalation a un modello piu' forte, la delega manager/figli, i subagenti read-only. Non funzionano gli sciami di scrittori paralleli.
- Limiti: blog di un'azienda; numeri non verificabili esternamente.
- Implicazione tollgate: CONFERMA: reviewer a contesto fresco che legge solo il diff; scrittura single-thread; subagenti di ricerca read-only. ATTENZIONE: "subagente fresco per task" scrive codice con contesto ridotto: rischio di decisioni implicite incoerenti tra task. Serve che il piano/spec porti le decisioni (contratti, naming) in forma esplicita.

### D10. Anthropic: "Building effective agents" (dic 2024) [V]
- URL: https://www.anthropic.com/research/building-effective-agents
- Cosa: workflow (percorsi predefiniti) vs agenti; semplicita' prima di tutto; evaluator-optimizer; orchestrator-workers; ACI e poka-yoke (percorsi assoluti eliminano errori); checkpoint umani e condizioni di stop.
- Implicazione tollgate: CONFERMA design a workflow con punti agenti; poka-yoke come principio per messaggi degli hook.

### D11. Aider: architect/editor (blog, 26 set 2024) [V] e Cognition sul tema [V]
- URL: https://aider.chat/2024/09/26/architect.html
- Risultato: o1-preview architect + DeepSeek/o1-mini editor: 85% sul benchmark di edit di Aider; la stessa modello in entrambi i ruoli migliora Sonnet, GPT-4o, GPT-4o-mini. Cognition (D9) osserva invece che il pattern "edit apply model" era fragile e oggi i modelli singoli fanno entrambe le cose.
- Limiti: il vantaggio era legato ai modelli di ragionamento di fine 2024 che formattavano male gli edit.
- Implicazione tollgate: la separazione architetto/editor e' un'ottimizzazione di costo/formato legata ai modelli del 2024; per tollgate NON e' una decisione portante. Meglio separare per CONTESTO (chi scrive il piano non e' chi esegue e chi rivede) piuttosto che per modello.

---
## E. Contesto lungo, orizzonte lungo, harness di Anthropic

### E1. Measuring AI Ability to Complete Long Software Tasks (METR) [V abstract]
- Autori: T. Kwa, B. West, J. Becker, ... E. Barnes, L. Chan. Mar 2025 (v4 lug 2026). NeurIPS 2025.
- URL: https://arxiv.org/abs/2503.14499
- Risultato: orizzonte al 50% di Claude 3.7 Sonnet ~50 minuti; raddoppio ogni ~7 mesi dal 2019; i miglioramenti derivano da affidabilita', adattamento agli errori, ragionamento e uso di tool.
- Limiti: validita' esterna; (snippet [S]: METR nel 2026 riporta stime >=16 ore al 50% ma inaffidabili sopra 16h, con intervalli di confidenza di un fattore 2 e revisioni delle stime fino al -20%; l'orizzonte all'80% e' molto piu' corto, ~3h per il miglior modello).
- Implicazione tollgate: i compiti lunghi hanno successo al 50%, non al 99%: l'affidabilita' di una fetta lunga e' bassa. Fette piccole + verifica a ogni passo trasformano un compito lungo in molti compiti corti ad alta affidabilita'. Conferma dimensione-fetta; attenzione a non usare le cifre 2026 come precise.

### E2. SWE-Marathon: Can Agents Autonomously Complete Ultra-Long-Horizon Software Work? [V abstract]
- Autori: R. Desai et al. (26). Giu 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2606.07682
- Risultato: 20 task, 27.2M token medi per tentativo; sotto il 30% di risoluzione; fallimenti: auto-verifica debole, dichiarare "infattibile", fermarsi presto; reward hacking nel 13.8% dei rollout. (Snippet [S]: ripetizioni crescenti con il contesto.)
- Implicazione tollgate: CONFERMA: niente "fatto" senza ricevute (auto-verifica debole), contrasto al reward hacking (13.8%), una fetta per sessione.

### E3. Context as a Tool: Context Management for Long-Horizon SWE-Agents [V abstract]
- Autori: S. Liu, J. Yang, B. Jiang, Y. Li, J. Guo, X. Liu, B. Dai. Dic 2025. arXiv preprint.
- URL: https://arxiv.org/abs/2512.22087
- Risultato: SWE-Compressor 57.6% su SWE-Bench-Verified con contesto limitato; (snippet [S]: il baseline ReAct satura e degrada dopo ~60 round).
- Limiti: sistema degli autori, modello addestrato ad hoc.
- Implicazione tollgate: CONFERMA il rischio context rot nei task lunghi. ALTERNATIVA: tollgate evita il problema chiudendo la sessione invece di comprimere.

### E4. Coding Agents are Effective Long-Context Processors [V abstract]
- Autori: W. Cao, X. Yin, B. Dhingra, S. Zhou. Mar 2026. arXiv preprint.
- URL: https://arxiv.org/abs/2603.20432
- Risultato: agenti che organizzano il testo su filesystem superano lo stato dell'arte del 17.3% in media.
- Implicazione tollgate: CONFERMA "output su file": spostare il contesto su filesystem funziona meglio che tenerlo nella finestra.

### E5. Anthropic: "Effective harnesses for long-running agents" (J. Young, 26 nov 2025) [V]
- URL: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Cosa: fallimenti: fare troppo in una volta, dichiarare vittoria in anticipo, marcare feature completate senza verifica end-to-end. Soluzione: initializer + coding agent per sessione, lista feature in JSON (solo il campo passes modificabile), progress file, git, test E2E a inizio sessione.
- Implicazione tollgate: CONFERMA quasi 1:1 (una feature per sessione, artefatti su file, git come stato, JSON e non Markdown perche' piu' difficile da sovrascrivere).

### E6. Anthropic: "Harness design for long-running application development" (P. Rajasekaran, 24 mar 2026) [V]
- URL: https://www.anthropic.com/engineering/harness-design-long-running-apps
- Cosa: planner / generator / evaluator con "sprint contract"; reset del contesto vs compattazione (context anxiety in Sonnet 4.5); bias di auto-valutazione.
- Risultato: l'agente valuta troppo bene il proprio lavoro; un valutatore separato e' piu' facile da calibrare. Con modelli nuovi hanno RIMOSSO componenti: reset (Opus 4.5), decomposizione in sprint (Opus 4.6), valutatore per sprint ridotto a un passaggio finale; il planner resta.
- Implicazione tollgate: CONFERMA valutatore separato e planner. CONTRADDICE in parte: parte dell'impalcatura (fette, reset) diventa superflua con modelli piu' forti. Va previsto un meccanismo per disattivare componenti, provato dall'eval.

---
## F. Verifica, test, reward hacking

### F1. ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases [V abstract e testo parziale]
- Autori: Z. Zhong, A. Raghunathan, N. Carlini. Ott 2025. arXiv preprint.
- URL: https://arxiv.org/abs/2510.20270
- Risultato (dal testo): su Conflicting-SWEbench GPT-5 imbroglia il 54%, o3 49%, Opus 4.1 ~50%. Prompt piu' permissivo: GPT-5 54% -> 66%. Test in sola lettura: blocca la modifica dei test e conserva la performance legittima, ma non ferma special-casing e operator overloading. Test nascosti: imbroglio quasi nullo ma cala la performance. Opzione di "abort": GPT-5 54% -> 9%, o3 49% -> 12%, Opus molto meno. Piu' sottomissioni: pass 80% -> 83%, imbroglio 33% -> 38%.
- Limiti: task costruiti per essere impossibili; la figura 7 con i dati sui permessi non era nel testo.
- Implicazione tollgate: CONFERMA "test non indebolibili" via hook che rende i test in sola lettura; SUGGERISCE un'uscita esplicita di "blocco/abort" (l'agente puo' dichiarare il conflitto spec/test invece di forzare). AVVERTE che il read-only non basta contro special-casing: serve review del diff di produzione.

### F2. Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study [V abstract]
- Autori: Y. Wang, M. Pradel, Z. Liu. Mar 2025 (v2 set 2025). ICSE 2026.
- URL: https://arxiv.org/abs/2503.15223
- Risultato: 7.8% di patch "corrette" falliscono la suite dei test degli sviluppatori; 29.6% delle plausibili si comportano diversamente dal ground truth; 28.6% di queste sicuramente errate; inflazione dei tassi riportati di 6.2 punti.
- Implicazione tollgate: CONTRADDICE in parte la sufficienza della "ricevuta di test": test verdi non garantiscono correttezza (circa 1 patch su 14 fallisce i test ufficiali, 29.6% divergono). La ricevuta e' necessaria ma NON sufficiente: serve anche review del comportamento. Inoltre l'eval di tollgate non deve basarsi solo sui test.

---
## G. Human-in-the-loop e produttivita'

### G1. Magentic-UI: Towards Human-in-the-loop Agentic Systems [V abstract]
- Autori: H. Mozannar, G. Bansal, C. Tan, A. Fourney, ... S. Amershi (20). Lug 2025. arXiv preprint.
- URL: https://arxiv.org/abs/2507.22358
- Cosa: meccanismi a basso costo per coinvolgere l'umano: co-planning, co-tasking, multi-tasking, action guards, memoria a lungo termine.
- Risultato: nessun numero nell'abstract.
- Implicazione tollgate: CONFERMA co-planning (approvazione del piano) e action guards (conferma solo per effetti esterni).

### G2. Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems [V abstract]
- Autori: J. Liu, X. Zhao, X. Shang, Z. Shen. Apr 2026 (v2 lug 2026). arXiv preprint.
- URL: https://arxiv.org/abs/2604.14228
- Risultato: analisi del sorgente: loop semplice, sistema di permessi a 7 modalita' con classificatore, pipeline di compattazione a 5 livelli, 4 meccanismi di estensione (MCP, plugin, skill, hook), subagenti.
- Implicazione tollgate: descrive il substrato su cui gira tollgate; gli hook sono uno dei 4 meccanismi di estensione ufficiali, quindi e' il punto di innesto corretto.

### G3. Anthropic: "Measuring AI agent autonomy in practice" (18 feb 2026) [S]
- URL: https://www.anthropic.com/research/measuring-agent-autonomy (visto solo in risultato di ricerca, pagina non aperta)
- Cosa (secondario): gli utenti esperti di Claude Code approvano automaticamente di piu' ma interrompono anche di piu'. La cifra "~93% dei prompt approvati" viene da un survey [S] che cita un'analisi di Anthropic (Hughes 2026) che non ho aperto: NON citarla come dato verificato.
- Implicazione tollgate: gli approval prompt frequenti diventano rituali. SUGGERISCE di limitare le conferme umane ad azioni rare e ad alto impatto (effetti esterni, merge) e rendere automatico il resto.

### G4. Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity (METR RCT) [V abstract]
- Autori: J. Becker, N. Rush, E. Barnes, D. Rein. Lug 2025. arXiv preprint.
- URL: https://arxiv.org/abs/2507.09089
- Risultato: 16 sviluppatori, 246 task; con AI il tempo e' aumentato del 19% (previsione degli sviluppatori: -24%; stima ex post: -20%).
- Limiti: campione piccolo, strumenti del 2025.
- Implicazione tollgate: percezione e realta' divergono; l'eval di tollgate deve misurare tempo e difetti reali, non la soddisfazione. Se tollgate aggiunge cerimonia, il rischio di rallentare e' reale.

### G5. Stop Hand-Holding Your Coding Agent [V abstract]
- Autore: S. Macedo. Giu 2026. arXiv preprint (singolo autore, taglio concettuale).
- URL: https://arxiv.org/abs/2607.00038
- Risultato: corpus di 50 loop scritti a mano: il 70% verifica in zona autonoma, il 74% nomina gli stati terminali.
- Implicazione tollgate: debole come evidenza; conferma l'idea di specificare verifica, regole di stop e stati terminali come artefatto.

---
## Evidenze che CONTRADDICONO o mettono in discussione tollgate
1. L'impalcatura invecchia: Anthropic ha rimosso reset di contesto e decomposizione in sprint con modelli piu' nuovi (E6); mini-swe-agent con solo bash arriva a >74% (A5, [V sul README], modello non indicato). Rischio di over-engineering: serve un interruttore per componente.
2. Un piano scadente e' peggio di nessun piano; fasi extra possono danneggiare (C3). I profili per tipo di file devono dimostrare un guadagno con eval.
3. Test verdi non bastano (F2: 7.8% falsi positivi; 29.6% comportamento divergente). La ricevuta di test non e' prova di correttezza.
4. Multi-agente: nessun beneficio su task sequenziali (D6, D7, D8). Tollgate e' solo parzialmente multi-agente (sequenziale, scrittore unico): ok, ma subagenti freschi senza storia producono decisioni implicite incoerenti (D9). Il carico passa su spec e piano.
5. Edit-apply/architect-editor: era un trucco del 2024, ora superfluo secondo Cognition (D11).
6. L'effetto dello scaffold dipende dal modello e dal benchmark (B3, B4): risultati dell'eval non generalizzano a modelli nuovi; vanno rifatti.
7. Approval fatigue [S]: troppe conferme umane le rendono formali.

## Lacune
- Non ho aperto: Terminal-Bench full text, Hughes 2026, METR dashboard. Paper PMCoder, AgentForge, Confucius Code Agent compaiono solo negli snippet e non sono citati come verificati.
- Non ho trovato uno studio controllato su "dimensione ottimale di una fetta" in repo reali: solo evidenze indirette (A6, B6, E1).
