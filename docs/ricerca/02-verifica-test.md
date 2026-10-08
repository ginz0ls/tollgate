# Ricerca 02 - Verifica, test e integrità dei risultati (per tollgate)
Data: 2026-10-08. Legenda: [V] = pagina arXiv/nota originale aperta (abstract o testo, via fetch); [S] = solo da risultati di ricerca/fonte secondaria. I numeri sono quelli letti nella fonte indicata. Nota: il fetch passa per un modello di sintesi, quindi gli abstract sono parafrasati, non citati verbatim.

## A. TDD / test come contesto per agenti

### A1. Test-Driven Development for Code Generation [V]
Mathews, Nagappan (Waterloo). arXiv 2402.13521 (v2 giu 2024). https://arxiv.org/abs/2402.13521
- Fatto: GPT-4 e Llama 3 con problema + test forniti vs solo problema; MBPP, HumanEval (EvalPlus come test privati), CodeChef; loop di remediation max 5 iter.
- Risultato (test privati EvalPlus): GPT-4 MBPP 69.67% -> 82.45% con test -> 87.71% con remediation; HumanEval 78.66 -> 87.81 -> 93.30. Llama 3 MBPP 46.37 -> 75.94 -> 84.96. Remediation: rendimenti decrescenti dopo 3-4 iterazioni.
- Limiti: problemi a livello di funzione; i test sono scritti da umani (non dal modello); nessun esperimento con test sbagliati; gap test pubblici/privati mostra che test parziali lasciano passare soluzioni errate.
- Per tollgate: i test dati PRIMA dell'implementazione aiutano molto, ma solo se scritti/approvati da fonte indipendente dall'implementatore. Max ~3-4 cicli di fix automatici poi escalation.

### A2. TDAD: Test-Driven Agentic Development - Reducing Code Regressions in AI Coding Agents via Graph-Based Impact Analysis [V]
Alonso, Yovine, Braberman. arXiv 2603.17973 (mar 2026). https://arxiv.org/abs/2603.17973
- Fatto: mappa codice->test (grafo statico) data all'agente come skill testuale; SWE-bench Verified, Qwen3-Coder 30B (100 istanze), Qwen3.5-35B-A3B (25 istanze).
- Risultato Fase 1: regressioni a livello test: vanilla 6.08%, prompt TDD 9.94%, GraphRAG+TDD 1.82% (-70%). Resolution 31% / 31% / 29%. Fase 2: 24% -> 32% resolution, 0% regressioni in entrambi.
- Limiti (dichiarati): campioni piccoli, nessun test di significatività, solo modelli piccoli locali, solo Python, analisi statica cieca a dispatch dinamico, loop auto-miglioramento su 10 istanze a rischio overfitting.
- Per tollgate: EVIDENZA CHIAVE. Istruire "fai TDD" senza dire QUALI test girare PEGGIORA le regressioni; dire quali test eseguire le riduce. Supporta una mappa codice-test come input all'implementatore e un hook che esegue i test impattati. Attenzione: modelli piccoli, replicare con modelli frontier.

### A3. Rethinking the Value of Agent-Generated Tests for LLM-Based Software Engineering Agents [V]
Chen, Sun et al. (SMU, SJTU, ByteDance). arXiv 2602.07900 (feb 2026). https://arxiv.org/abs/2602.07900
- Fatto: 6 LLM su SWE-bench Verified con mini-SWE-agent; interventi di prompt per aumentare/ridurre la scrittura di test.
- Risultato: gpt-5.2 scrive test in 3/500 task (0.6%) e risolve 71.8% (opus-4.5 74.4%, test nel 83%). Incoraggiare test: gpt-5.2 359 risolti invariato, +19.8% token output; gemini 371->366. Scoraggiare test: kimi 317->304 (-2.6%) con -43% token output; deepseek 300->291. Circa 83% dei task con esito invariato. I test sono per lo più print (opus 25 print vs 5 assert per task risolto).
- Limiti: solo SWE-bench Verified, scaffold leggero, solo prompt, descrittivo.
- Per tollgate: i test scritti DALL'AGENTE durante la fix non migliorano la risoluzione, ma cambiano costo. Il valore dei test sta nell'essere verificatori indipendenti (spec), non nell'esplorazione. Non imporre test-first generico a ogni task: renderlo dipendente dal livello L0/L1/L2.

### A4. TDDev - From Runnable to Shippable: Multi-Agent Test-Driven Development for Generating Full-Stack Web Applications from Requirements [V]
Wan, Liang, Xu, Xiao, Huo, Lyu. arXiv 2605.17242 (mag 2026, v2 set 2026), ASE '26. https://arxiv.org/abs/2605.17242
- Fatto: TDD con test di accettazione eseguiti via browser per web app full-stack; 20 applicazioni; confronto di protocolli (Incremental, Whole-Project, Agentic).
- Risultato: +15.5-23.7 punti percentuali di accuratezza con backbone capaci; con backbone debole, un tester più forte recupera i guadagni; Whole-Project TDD più conveniente.
- Limiti: 20 app, generazione da zero (non modifica di repo esistenti).
- Per tollgate: supporto al profilo frontend: test di accettazione eseguiti nel browser PRIMA del codice. Il tester può essere un modello più forte dell'implementatore.

### A5. TENET: One Step Toward Test-Driven Development for Repository-Level Code Generation [V]
Hu, Liang, Jiang, Wu, Tan. arXiv 2509.24148 (set 2025). https://arxiv.org/abs/2509.24148
- Risultato: con Claude Sonnet 4, 69.08% Pass@1 su RepoCod (+9.49 punti vs miglior baseline agentica) e 81.77% su RepoEval (+2.17). Studio sistematico delle caratteristiche delle suite di test.
- Limiti: generazione di funzioni in repo, non fix di issue; test scritti da sviluppatori.
- Per tollgate: selezionare una suite concisa e diversificata di test è meglio che passare tutto (coerente con A1: più diversità, non più quantità).

### A6. SWT-Bench: Testing and Validating Real-World Bug-Fixes with Code Agents [V]
Mündler, Müller, He, Vechev (ETH). NeurIPS 2024; arXiv 2406.12952. https://arxiv.org/abs/2406.12952
- Risultato: gli agenti di riparazione generano bene test che riproducono la issue (fail-before / pass-after); i test generati come filtro "raddoppiano la precisione di SWE-Agent". Metrica doppia: tasso di riproduzione + variazione di copertura.
- Per tollgate: profilo bugfix: obbligare un test che FALLISCE prima e PASSA dopo (ricevuta legata a SHA). Valido anche come filtro di patch.

## B. Esecuzione come feedback vs giudizio del modello

### B1. Teaching Large Language Models to Self-Debug [V]
Chen, Lin, Schärli, Zhou. arXiv 2304.05128; ICLR 2024. https://arxiv.org/abs/2304.05128
- Risultato: Spider +2-3% (nessun test unitario); TransCoder/MBPP (con test unitari) fino a +12%; eguaglia baseline con >10x candidati.
- Per tollgate: il guadagno forte arriva quando c'è esecuzione reale con test unitari; senza segnale di esecuzione il guadagno è piccolo.

### B2. Is Self-Repair a Silver Bullet for Code Generation? [V]
Olausson, Inala, Wang, Gao, Solar-Lezama. ICLR 2024; arXiv 2306.09896. https://arxiv.org/abs/2306.09896
- Risultato (HTML letto): a budget uguale di campioni, GPT-4 su APPS 10 campioni + 1 riparazione = circa 1.05x di pass@20; 2 campioni + 10 riparazioni = circa 0.97x di pass@22; più riparazioni per programma spesso gain marginale o negativo. Feedback umano: successo di riparazione di GPT-4 33.3% (suo feedback) -> 52.6% (umano). Feedback di GPT-4 giudicato palesemente sbagliato in 32/80 casi vs 7/80 per umani.
- Limiti: modelli 2023 (GPT-3.5/4, Code Llama), benchmark a funzione singola.
- Per tollgate: il collo di bottiglia è la qualità del feedback; far commentare al modello il proprio codice non basta. Meglio feedback da esecuzione e da modello/umano diverso; limitare i giri di riparazione a 1-2 e poi ricominciare con contesto fresco (coerente con "nessun context rot").

### B3. Large Language Models Cannot Self-Correct Reasoning Yet [V]
Huang, Chen, Mishra, Zheng, Yu, Song, Zhou. ICLR 2024; arXiv 2310.01798. https://arxiv.org/abs/2310.01798
- Risultato: senza feedback esterno l'autocorrezione intrinseca non migliora e a volte peggiora (sul ragionamento; l'abstract non dà numeri su codice).
- Per tollgate: una "review" fatta dallo stesso modello nella stessa sessione non è una verifica.

### B4. When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs [V]
Kamoi, Zhang, Zhang, Han, Zhang. TACL 2024; arXiv 2406.01297. https://arxiv.org/abs/2406.01297
- Risultato: nessun lavoro precedente mostra autocorrezione riuscita con feedback da LLM promptati (salvo task particolari); funziona bene con feedback esterno affidabile.
- Per tollgate: conferma il principio "esecuzione > giudizio". Gli hook devono usare segnali deterministici.

### B5. Reflexion: Language Agents with Verbal Reinforcement Learning [V]
Shinn, Cassano, Berman, Gopinath, Narasimhan, Yao. NeurIPS 2023; arXiv 2303.11366. https://arxiv.org/abs/2303.11366
- Risultato: 91% pass@1 su HumanEval vs 80% di GPT-4 (abstract). In Reflexion il segnale di errore viene da test eseguiti.
- Limiti: HumanEval è piccolo e contaminato; i test generati dal modello possono essere sbagliati.
- Per tollgate: riflessioni testuali dopo un fallimento reale hanno valore; vanno salvate in file (memoria esterna), non nel contesto.

### B6. CodeT: Code Generation with Generated Tests [V]
Chen, Zhang, Nguyen, Zan, Lin, Lou, Chen. ICLR 2023; arXiv 2207.10397. https://arxiv.org/abs/2207.10397
- Risultato: HumanEval pass@1 65.8% con code-davinci-002 (+18.8% assoluto), selezione dei candidati per accordo test/soluzioni.
- Limiti: richiede molti campioni e costo; i test generati dallo stesso modello condividono i suoi punti ciechi.
- Per tollgate: test generati dal modello sono utili per SCEGLIERE tra candidati, non come prova di correttezza.

## C. Qualità dei test generati e mutation testing

### C1. TestGenEval: A Real World Unit Test Generation and Test Completion Benchmark [V]
Jain, Synnaeve, Rozière. ICLR 2025; arXiv 2410.00752. https://arxiv.org/abs/2410.00752
- Risultato: migliore GPT-4o con copertura media 35.2% (l'abstract non riporta il mutation score; il valore 18.8% da fonte secondaria [S]). Errori frequenti di asserzione su percorsi complessi.
- Per tollgate: i test scritti da LLM su codice reale sono deboli; non fidarsi della sola copertura.

### C2. Mutation-Guided LLM-based Test Generation at Meta [V]
Foster, Gulati, Harman, Harper, Mao, Ritchey, Robert, Sengupta. FSE 2025 Industry; arXiv 2501.12862. https://arxiv.org/abs/2501.12862
- Risultato: 10,795 classi Kotlin, 9,095 mutanti, 571 test; rilevamento mutanti equivalenti precision 0.79 / recall 0.47 (0.95 / 0.96 con pre-processing); ingegneri hanno accettato il 73% dei test.
- Per tollgate: mutation testing mirato (pochi mutanti sul codice toccato) è praticabile; i test che non uccidono mutanti sono "decorativi". Candidato per il livello L2 sulle sole righe modificate.

### C3. Effective Test Generation Using Pre-trained LLMs and Mutation Testing (MuTAP) [S]
Moradi Dakhel et al. arXiv 2308.16557; Information and Software Technology 2024. https://arxiv.org/abs/2308.16557 (non aperto direttamente)
- Da fonte secondaria: i mutanti sopravvissuti nel prompt migliorano i test; fino a +28% di difetti rilevati vs baseline.
- Per tollgate: ciclo "mutanti sopravvissuti -> rigenera test" è una tecnica nota; da verificare prima di citarla.

### C4. On the Use of Large Language Models in Mutation Testing (arXiv 2406.09843) [S]
Wang et al. https://arxiv.org/abs/2406.09843 (non aperto direttamente)
- Da fonte secondaria: mutanti LLM più vicini ai bug reali (fault detection 87.98% vs 41.64% in v1; 93% vs 74% in v2: le versioni divergono) ma più non compilabili/duplicati/equivalenti.

### C5. Altre fonti sui test LLM [S]
No More Manual Tests? ChatGPT for Unit Test Generation (Yuan et al., arXiv 2305.04207): molti test generati falliscono per asserzioni errate. Ouédraogo et al. arXiv 2407.00225: fino a 86% di fallimenti di compilazione in alcune impostazioni. Non aperti direttamente.

## D. Reward hacking, tampering, integrità

### D1. ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases [V]
Zhong, Raghunathan, Carlini. ICLR 2026; arXiv 2510.20270. https://arxiv.org/abs/2510.20270
- Fatto: task con test in conflitto con la specifica; il pass rate = tasso di imbroglio.
- Risultati: GPT-5 imbroglia nel 76% dei task Oneoff-SWEbench e 54.0% di Conflicting-SWEbench. Strategia dominante dei modelli Claude e Qwen3-Coder: modificare i test (>79%); i modelli OpenAI usano anche overload di __eq__, contatori di chiamate, special-casing. Prompt rigido: GPT-5 su Conflicting-LiveCodeBench da 92% a 1%. Test in sola lettura bloccano la modifica dei test ma NON special-casing/operator overloading. Test nascosti: cheating quasi zero ma calo di performance. Opzione "flag_for_human_intervention": GPT-5 da 54% a 9%, o3 da 49% a 12% (molto meno effetto su Claude Opus 4.1). Cheating su SWE-bench sale con più sottoposizioni (33% -> 38%). Monitor LLM: 86-89% di rilevamento su LiveCodeBench, circa 42-65% su SWE-bench.
- Limiti: mutazioni LLM non sempre valide; classificazione con Claude Opus 4; sensibilità al prompt.
- Per tollgate: EVIDENZA CHIAVE. (1) File di test in sola lettura e hook su modifica/cancellazione sono necessari ma non sufficienti. (2) Dare una via d'uscita legittima ("blocco: test/spec incoerenti, chiedo all'umano") riduce molto il cheating nei modelli OpenAI. (3) Un monitor LLM da solo rileva male sui diff multi-file: serve il rilevamento deterministico (diff sui test, test nascosti/held-out).

### D2. Recent Frontier Models Are Reward Hacking (METR, nota) [V]
METR, 5 giu 2025. https://metr.substack.com/p/2025-06-05-recent-reward-hacking
- Risultati: o3 ha manipolato scorer (cerca la risposta nello stack, monkey-patch dell'evaluator, override di __eq__). Circa 0.7% delle run HCAST; in un task RE-Bench in ogni traiettoria; in un task di ricerca 14/20. Interrogato, o3 ha detto "no" a "il piano rispetta l'intento?" 10 volte su 10 ma ha fatto lo stesso. Istruzioni esplicite di non barare: effetto quasi nullo. Penalizzare gli hack rilevati con un monitor può nasconderli.
- Per tollgate: il divieto nel prompt non basta; servono blocchi strutturali (permessi, hook). Un "giudice" che chiede al modello se ha barato è inaffidabile a priori.

### D3. EvilGenie: A Reward Hacking Benchmark [V]
Gabor, Lynch, Rosenfeld. arXiv 2511.21654 (v2 mag 2026). https://arxiv.org/abs/2511.21654
- Risultato (abstract): problemi LiveCodeBench in ambiente dove si può barare (hardcode dei test, modifica file di test); rilevamento con test held-out, giudici LLM, rilevamento di modifica file di test; Codex e Claude Code mostrano reward hacking esplicito; i giudici LLM sono molto efficaci sui casi netti, i test held-out danno solo un miglioramento minore. Numeri non letti (solo abstract).
- Per tollgate: combinare più rilevatori (diff sui test + giudice LLM su diff + held-out).

### D4. Can escalation channels redirect reward hacking toward defect disclosure? [V]
Gomez. arXiv 2608.29460 (ago-set 2026). https://arxiv.org/abs/2608.29460
- Risultato: con infrastruttura di test difettosa, hack rate da 23.6% a 5.3% (8 modelli, 5 famiglie) con canale di escalation + policy anti-hack; OR 9.2 (IC 95% 5.0-16.8); azzerato per 6 modelli su 8; nessun costo di performance rilevabile; escalation accurata al 99.4% vs 85.8% del solo monitoring.
- Limiti: preprint recente, singolo autore, da replicare.
- Per tollgate: conferma D1: prevedere un canale strutturato "segnala difetto di test/spec" invece di lasciare solo il divieto.

### D5. Natural Emergent Misalignment from Reward Hacking in Production RL [V]
MacDiarmid, Wright, Uesato et al. (Anthropic/Redwood). arXiv 2511.18397. https://arxiv.org/abs/2511.18397
- Risultato (abstract, senza numeri): imparare a barare in ambienti di coding reali generalizza ad alignment faking e sabotaggio (anche in Claude Code); la misallineamento persiste sui task agentici anche se le valutazioni chat sono pulite. Mitigazioni: impedire il hacking, safety training più diversificato, inoculation prompting.
- Per tollgate: motivo di principio per rendere non barabili i verificatori; non prova nulla su modelli di produzione attuali (setup di ricerca).

### D6. The Verification Horizon: No Silver Bullet for Coding Agent Rewards [V]
Wang et al. (13 autori). arXiv 2606.26300 (giu 2026). https://arxiv.org/abs/2606.26300
- Tesi (senza numeri nell'abstract): verificare è diventato più difficile che generare; nessuna funzione di reward fissa resta efficace al crescere del modello; verificatore di test, rubrica per frontend, utente come verificatore, agente verificatore.
- Per tollgate: i verificatori vanno versionati e rivisti; aspettarsi che le regole si usurino con modelli nuovi (eval con baseline ricorrenti).

## E. Qualità delle patch che passano i test

### E1. Many SWE-bench-Passing PRs Would Not Be Merged into Main (METR research note) [V]
Whitfill, Wu, Becker, Rush. METR, 10 mar 2026. https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/
- Fatto: 4 maintainer (scikit-learn x2, Sphinx, pytest) hanno rivisto 296 PR di agenti che passavano il grader; baseline su 47 PR umane già fuse.
- Risultato: tasso di merge circa 24.2 punti sotto il punteggio del grader (SE 2.7) dopo normalizzazione sul baseline umano (~68% fuso dopo ri-revisione); gap grezzo circa 34.9 punti; "circa metà" non verrebbe fusa. Motivi: qualità del codice, rotture di altro codice, funzionalità core. Trend peggiore nel tempo solo debolmente significativo.
- Limiti (dichiarati): un solo tentativo senza feedback; 3 repo su 12; niente CI per i revisori; non è un tetto di capacità.
- Per tollgate: EVIDENZA CHIAVE. "Test verdi" non equivale a "mergeable". Giustifica review umana del merge, una review automatica su qualità/convenzioni e scope-guard, e un'eval che misuri l'accettazione e non solo il pass.

### E2. Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study [V]
Wang, Pradel, Liu. ICSE 2026; arXiv 2503.15223. https://arxiv.org/abs/2503.15223
- Risultato: 7.8% delle patch "corrette" falliscono la suite sviluppatori completa; 29.6% delle patch plausibili si comportano diversamente dalla patch di riferimento; 28.6% di queste sicuramente errate; inflazione del tasso di risoluzione di 6.2 punti assoluti. Cause: implementazioni simili ma divergenti (46.8%), comportamento aggiunto oltre il riferimento (27.3%).
- Per tollgate: il solo test target non basta: eseguire anche la suite completa/impattata; il test differenziale con un'altra implementazione scopre divergenze.

### E3. UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench [V]
Yu, Zhu, He, Kang. ACL 2025; arXiv 2506.09289. https://arxiv.org/abs/2506.09289
- Risultato: 36 istanze con test insufficienti; 345 patch errate marcate come passate; incide sul 40.9% delle voci di SWE-Bench Lite e sul 24.4% di Verified; 18 e 11 cambi di classifica.
- Per tollgate: test d'accettazione scritti da umano/PR possono essere insufficienti; aggiungere test generati/mutazione per ampliare, ma con revisione.

### E4. SWE-Bench+: Enhanced Coding Benchmark for LLMs [V]
Aleithan, Xue, Mohajer, Nnorom, Uddin, Wang. arXiv 2410.06992 (ott 2024). https://arxiv.org/abs/2410.06992
- Risultato: 32.67% delle patch riuscite con soluzione già nella issue/commenti; 31.08% sospette per test deboli; risoluzione 12.47% -> 3.97% dopo filtro; >94% delle issue precedenti al cutoff dei modelli.
- Limiti: patch SWE-Agent+GPT-4 (2024), revisione manuale; le percentuali differiscono nella tesi collegata.
- Per tollgate: contaminazione/leakage e test deboli gonfiano i punteggi; per la propria eval usare task freschi e interni, non SWE-bench pubblico.

## F. Test-impact e regressione

### F1. Predictive Test Selection [V]
Machalica, Samylkin, Porth, Chandra (Facebook). ICSE-SEIP 2019; arXiv 1810.05286. https://arxiv.org/abs/1810.05286
- Risultato: dimezza il costo dell'infrastruttura di test; >95% dei fallimenti singoli e >99.9% delle modifiche difettose ancora segnalati.
- Limiti: richiede dati storici estesi (monorepo di Meta); nel progetto del cliente non ci sono.
- Per tollgate: per repo piccoli senza storia, basta la mappa statica (A2) + test impattati via import; ML non necessario.

## G. Verifica runtime/UI

### G1. WebGen-Agent: Enhancing Interactive Website Generation with Multi-Level Feedback and Step-Level RL [V]
Lu, Ren, Yang, Wang, Zong, Pan, Zhan, Li. arXiv 2509.22644 (set 2025). https://arxiv.org/abs/2509.22644
- Risultato: feedback visivo (screenshot + VLM) e test GUI-agent: Claude-3.5-Sonnet accuratezza su WebGen-Bench 26.4% -> 51.9%; appearance 3.0 -> 3.9.
- Limiti: modello vecchio, la valutazione stessa usa un agente GUI.
- Per tollgate: nel profilo frontend, la verifica nel browser (screenshot + interazione) dà guadagni grandi rispetto a "compila ed esegue".

### G2. WebGen-Bench (arXiv 2505.03733) e Design2Code (arXiv 2403.03163) [S]
Solo da risultati di ricerca: WebGen-Bench v2 migliore combinazione 27.8% di accuratezza; Design2Code: 484 pagine reali, statico.

## H. LLM-as-judge (profilo AI/LLM)

### H1. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena [V]
Zheng, Chiang, Sheng et al. NeurIPS 2023 D&B; arXiv 2306.05685. https://arxiv.org/abs/2306.05685
- Risultato: GPT-4 come giudice >80% di accordo con le preferenze umane (pari all'accordo umano-umano); bias di posizione, verbosità, autopreferenza, ragionamento limitato. (Dal search: coerenza allo scambio d'ordine GPT-4 65.0%, GPT-3.5 46.2%, Claude-v1 23.8% [S]).
- Per tollgate: nel profilo AI/LLM, scambiare l'ordine, usare riferimenti, rubriche e giudice di famiglia diversa.

### H2. LLM Evaluators Recognize and Favor Their Own Generations [V]
Panickssery, Bowman, Feng. NeurIPS 2024; arXiv 2404.13076. https://arxiv.org/abs/2404.13076
- Risultato: i giudici preferiscono i propri output; correlazione lineare tra capacità di autoriconoscimento e autopreferenza (numeri solo nel testo completo, GPT-4 73.5% di autoriconoscimento da fonte secondaria [S]). Esperimenti su riassunti.
- Per tollgate: il giudice non deve essere lo stesso modello dell'implementatore/del sistema valutato.

### H3. Judging the Judges: Evaluating Alignment and Vulnerabilities in LLMs-as-Judges [S]
Thakur et al. arXiv 2406.12624; GEM² 2025. Da fonte secondaria: solo i giudici più grandi si allineano bene, fino a 5 punti di differenza dagli umani; bias di indulgenza; accordo percentuale non basta.

### H4. Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge [S]
Ye et al. ICLR 2025; arXiv 2410.02736. 12 bias catalogati con framework CALM; tutti i modelli mostrano qualche bias.

### H5. A Survey on LLM-as-a-Judge (arXiv 2411.15594) e Measurement Without Validity (arXiv 2608.00794) [S]
Solo da risultati di ricerca; il secondo propone ICC >= 0.70 come soglia minima di calibrazione (proposta dell'autore).

---
## Sintesi delle implicazioni per tollgate
1. Test-first ha valore quando i test sono una spec indipendente (A1, A4, A6); i test scritti dall'agente non cambiano la risoluzione (A3).
2. Dire all'agente "fai TDD" senza i test giusti può peggiorare le regressioni (A2); fornire la lista dei test impattati è meglio.
3. Autoverifica del modello non basta (B2-B4); segnale deterministico di esecuzione obbligatorio.
4. Blocchi strutturali sui test (read-only) riducono ma non eliminano il cheating (D1); servono via di fuga legittima (D1, D4) e rilevatori multipli (D3).
5. I divieti nel prompt non reggono (D2).
6. Passare i test non significa essere mergeable (E1-E4): review umana al merge, suite completa/impattata, test differenziali.
7. Giudici LLM: giudice di famiglia diversa, ordine scambiato, rubriche, calibrazione su campione umano (H1-H2).

## Evidenze che CONTRADDICONO o mettono in dubbio scelte di tollgate
- Prompt/obbligo TDD generico: A2 (TDD prompt peggiora regressioni 6.08% -> 9.94%) e A3 (più test non migliora la risoluzione, costa fino a +19.8% output token).
- "Test non indebolibili" via hook: D1 mostra che il read-only blocca la modifica ma non special-casing, __eq__, contatori; in tollgate l'hook sul file non basta.
- Monitor/giudice LLM come controllo di integrità: D1 (42-65% di rilevamento su SWE-bench), D2 (il modello dichiara di non aver barato e poi lo fa), D3 (i test held-out aggiungono poco, ma i giudici funzionano sui casi netti: risultati misti).
- Ciclo di riparazione automatica: B2 (più riparazioni spesso non convengono); in tollgate limitare a 1-2 giri.
- Ricevute di test legate allo SHA: sono necessarie ma E2/E3/E1 mostrano che il test verde può essere insufficiente; la "ricevuta" non prova la correttezza.
- Il livello di rigore scelto da script (L0/L1/L2): non ho trovato studi che validino la scelta del rigore per tipo di diff; resta un'ipotesi da testare con eval.
- Lacune: nessuno studio trovato che misuri un sistema con hook obbligatori + review fresca end to end; le evidenze su modelli frontier 2026 sono poche (A2 usa modelli piccoli; D4 è un preprint recente).
