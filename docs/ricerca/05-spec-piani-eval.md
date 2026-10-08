# Filone 05 - Specifiche, piani, valutazione degli agenti (ricerca dell'8 ottobre 2026)

Legenda: [V] = testo/pagina aperta e letta (anche solo in parte, indicato); [S] = solo abstract o fonte secondaria. I numeri sono riportati solo se letti nella fonte indicata. Dove le versioni dell'arXiv divergono lo segnalo.

---
## A. Valutazione: varianza, statistica, metriche

### A1. Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations [V, HTML]
Evan Miller (Anthropic), 2024, arXiv:2411.00640 (stat.AP). https://arxiv.org/abs/2411.00640
- Cosa: tratta le eval come esperimenti; formule per SE, confronto fra due modelli, pianificazione della dimensione.
- Risultati: SE binario = sqrt(p(1-p)/n), IC95 = media +/- 1.96 SE. Differenze **appaiate** sulle stesse domande riducono la varianza se i punteggi sono correlati (esempio: correlazione 0.5, varianza ridotta di un terzo). SE a cluster fino a 3.05 volte quello ingenuo (DROP). Ricampionare K risposte per domanda riduce solo la varianza condizionale (limite 2/3 nel caso d'esempio); non pooling di K x N risposte (non indipendenti). Non abbassare la temperatura per ridurre la varianza. Potenza: n = (z_a/2 + z_b)^2 (w^2 + s_A^2/K_A + s_B^2/K_B)/d^2; esempio d=3%, 80% potenza -> n ~ 969 domande. Con n=198 portare K da 1 a 10 abbassa l'effetto minimo rilevabile da 13.2% a 7.5%.
- Limiti: pensato per eval a risposta singola con molte domande (migliaia); assume campione da super-popolazione.
- **Implicazione tollgate**: con pochi casi (decine) il campione di *casi* domina la varianza, non le ripetizioni: 3 run per caso riducono solo la parte "conditional". Analisi obbligatoria: test appaiato per caso (stesso caso con/senza plugin), report con differenza, SE, IC95, correlazione. Con ~30 casi e effetto atteso 10-15 punti si e' al limite; per effetti 5 punti servono centinaia di casi o si dichiara "non rilevabile".

### A2. On Randomness in Agentic Evals [V, HTML]
Bjarni Haukur Bjarnason, Andre Silva, Martin Monperrus (KTH), 2026, arXiv:2602.07150. https://arxiv.org/abs/2602.07150
- Cosa: 60.000 traiettorie su SWE-bench Verified (500 task), 3 modelli (Qwen3-32B, DeepSWE-preview, Devstral-2), 2 scaffold, 10 run per configurazione, a temperatura 0 e suggerita.
- Risultati: pass@1 di singola run varia di 2.2-6.0 punti a seconda della run scelta; deviazione standard > 1.5 punti anche a T=0 (T=0 non e' deterministico). Esempi: DeepSWE R2E-Gym pass@1 34.4, pass@5 52.9, pass^5 15.5; Devstral-2 nano-agent 63.5 / 76.2 / 49.1. Power analysis (t-test a due campioni, SD nota 1.5): rilevare +2 punti (p<.05, 80%) richiede ~9 run per agente; +1 punto ~36 run. Con 10 run si rilevano solo miglioramenti >= 2 punti.
- Limiti: un solo benchmark, due scaffold, contesto append-only (niente compattazione).
- **Implicazione tollgate**: i miglioramenti di 2-3 punti sono dentro il rumore. 3 run/caso NON bastano per effetti piccoli; bastano per effetti grandi (>10 punti) se si riportano IC. Il plugin (hook, subagenti) aumenta probabilmente la varianza di processo: misurare e riportare anche pass^k.

### A3. tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains [V, PDF testo, lettura parziale]
Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan (Sierra), 2024, arXiv:2406.12045. https://arxiv.org/abs/2406.12045
- Cosa: utente simulato + agente con tool e policy; successo = stato finale del DB uguale all'obiettivo. Introduce pass^k = probabilita' che tutte le k prove i.i.d. riescano (pass@k = almeno una).
- Risultati: gpt-4o < 50% di task, pass^8 < 25% in retail.
- Limiti: utente simulato da LLM, due domini.
- **Implicazione**: per un plugin che promette *obblighi* (affidabilita'), la metrica giusta e' pass^k sullo stesso caso, non pass@1. 3 run permettono pass^3; dichiarare k.

### A4. AI Agents That Matter [V, HTML parziale]
Sayash Kapoor, Benedikt Stroebl, Zachary S. Siegel, Nitya Nadgir, Arvind Narayanan (Princeton), 2024 (TMLR 2025 secondo fonte secondaria), arXiv:2407.01502. https://arxiv.org/abs/2407.01502
- Risultati: valutare sempre accuratezza + costo (frontiera di Pareto). Su HumanEval (media di 5 run) baseline semplici (Warming 93.2% a $2.45, Retry 92.0% a $2.51) pari o meglio di agenti complessi (LATS GPT-4 88.0% a $134.50, Reflexion 87.8% a $3.90). Molti benchmark senza holdout; errori in WebArena/HumanEval; errori di misura raramente riportati.
- **Implicazione**: tollgate va confrontato anche con un baseline semplice (Claude Code + CLAUDE.md breve / un solo prompt "usa TDD e verifica"), non solo con "nessun plugin". Riportare token e $ per caso come metrica di primo livello.

### A5. Beyond pass@1: A Reliability Science Framework for Long-Horizon LLM Agents [V, PDF, parziale]
Aaditya Khanal, Yangyang Tao, Junxiu Zhou, 2026, arXiv:2603.29231.
- 396 task in 4 bucket di durata, 10 modelli open, 23.392 episodi, k=3; l'affidabilita' (pass^k) decade con la durata e il ranking per capacita' e per affidabilita' diverge. Le tabelle dettagliate sono su un run di validazione di 19 task (il testo lo dichiara): cautela. Gli "scaffold di memoria" peggiorano GDS.
- **Implicazione**: evidenza debole ma coerente; usare solo come supporto a "stratificare i casi per durata".

---
## B. Task lunghi, decomposizione

### B1. Measuring AI Ability to Complete Long Software Tasks [V, HTML parziale (100k su 188k car.)]
Thomas Kwa, Ben West et al. (METR), 2025, arXiv:2503.14499. https://arxiv.org/abs/2503.14499
- 170 task (HCAST 97, RE-Bench 7, SWAA 66), baseline umane > 800 (2.529 ore). Successo = sigmoide in log(tempo umano). Orizzonte al 50%: o3 ~110 min; raddoppio ~207 giorni (IC95 166-240). Gli orizzonti all'80% sono 4-6 volte piu' corti di quelli al 50%. A parita' di durata i task "piu' disordinati" (messy) vanno peggio. Il titolo e i numeri cambiano fra versioni (v1: Claude 3.7 ~50 min).
- Limiti: dominio, baseliner, validita' esterna; task senza scoring automatico non coperti.
- **Implicazione**: la fetta per cui il piano e' "magro" deve restare sotto l'orizzonte all'80% (decine di minuti, non ore): la scelta di fette + subagente fresco per task e' coerente. Il successo cala con la durata, quindi i casi eval vanno stratificati per durata/dimensione.

### B2. Is there a half-life for the success rates of AI agents? [S, abstract]
Toby Ord, 2025, arXiv:2505.05115. Ipotesi a rischio costante per minuto umano (successo esponenziale in durata); dimostrata su una sola suite (RE-Bench/METR). Se vale, dimezzare la durata del task eleva il successo in modo piu' che lineare: argomento a favore delle fette piccole, ma non verificato su altre suite.

### B3. SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks? [V, HTML v2]
Xiang Deng, Jeff Da et al. (Scale AI), 2025, ICML 2026 (fonte: pagina ICML via ricerca), arXiv:2509.16941. https://arxiv.org/abs/2509.16941
- 1.865 problemi, 41 repo (public 731, held-out 858, commercial 276); soluzioni medie 107.4 righe su 4.1 file. Pass@1 su public: Claude Sonnet 4.5 43.6%, GPT-5 41.8%; commercial: Opus 4.1 17.8%, GPT-5 15.7%. Contaminazione ridotta con repo GPL e codebase privati. v1 diceva "sotto 25%", v2 "sotto 45%": citare la versione. Non riporta run multiple ne' varianza.
- **Implicazione**: per misurare l'effetto di un harness servono task non contaminati e di dimensione realistica (multi-file). Task "piccoli e puliti" gonfiano i risultati di entrambi i bracci e nascondono le differenze.

### B4. Towards a Science of Scaling Agent Systems [S, abstract/blog + grep sul PDF]
Yubin Kim, Xin Liu et al. (Google Research/DeepMind/MIT), 2025, arXiv:2512.08296. Nel testo scaricato: sistemi multi-agente non coordinati amplificano gli errori 17.2x (centralizzato 4.4x); su pianificazione sequenziale il degrado va da -39% a -70%; benefici su task parallelizzabili. Letto solo per grep.
- **Implicazione**: tollgate e' una pipeline sequenziale; un orchestratore che verifica (hook/review) e' coerente con "verifica centralizzata", ma molti subagenti in catena possono peggiorare. Da testare in A/B con numero di passaggi.

---
## C. Specifiche, requisiti, chiarimento

### C1. ClarifyGPT (FSE 2024) [V, PDF testo]
Fangwen Mu, Lin Shi, Song Wang et al., arXiv:2310.10996. https://arxiv.org/abs/2310.10996
- Rilevamento di ambiguita' via test di consistenza del codice, domande mirate, requisito raffinato. Con 10 partecipanti umani (140 problemi ambigui da MBPP-sanitized, in media 2.85 domande/problema): GPT-4 Pass@1 da 70.96% a 80.80% (MBPP-sanitized), da 51.52% a 60.19% (MBPP-ET). Baseline CoT 72.68, GPT-Engineer 73.77 (sanitized). Con utente simulato: media su 4 benchmark 68.02 -> 75.75 (GPT-4).
- Limiti: problemi da una funzione, benchmark piccoli; utente simulato da LLM; modelli 2023.
- **Implicazione**: il chiarimento aiuta (+10 punti su problemi *ambigui*) ma il guadagno e' misurato su casi selezionati come ambigui. Per tollgate: il brainstorming/spec e' utile solo dove c'e' ambiguita'.

### C2. Interactive Agents to Overcome Ambiguity in Software Engineering [V, HTML v1]
Sanidhya Vijayvargiya, Xuhui Zhou, Akhila Yerukola, Maarten Sap, Graham Neubig (CMU), 2025, arXiv:2502.13069. https://arxiv.org/abs/2502.13069
- 500 issue SWE-bench Verified riassunte da GPT-4o (sottospecificate), OpenHands, 30 turni, utente simulato GPT-4o. Con interazione fino a +74% (Haiku) sul non interattivo; Sonnet/Haiku arrivano ~80% della performance "full". I modelli interagiscono raramente se non spinti; solo Claude Sonnet 3.5 distingue bene (84% con incoraggiamento moderato); piu' incoraggiamento = piu' falsi positivi su issue ben specificate. Limiti dichiarati: utente-proxy piu' cooperativo del reale, possibile leakage, incoerenza interna sulla significativita'.
- **Implicazione**: **un obbligo di "chiedi sempre" non e' gratis**: aumenta le domande inutili. Meglio un gate condizionato (L0 niente domande, L1/L2 si').

### C3. Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents [V, alphaxiv]
Nicholas Edwards, Sebastian Schuster (Univ. Vienna), 2026, arXiv:2603.26233.
- Con Claude Sonnet 4.5: multi-agente con agente di intento 69.40% vs agente singolo con promemoria 61.20% (p<0.001), FULL 70.80%. Costo/task $3.50 vs $2.03. Correlazionale, utente e sottospecifica sintetici.
- **Implicazione**: separare "rilevare ambiguita'" dall'esecuzione aiuta ma costa ~70% in piu'.

### C4. ClarifyCodeBench [V, PDF parziale]
Zheng Fang, Dongming Jin, Yihong Dong, Yongmin Li, Kechi Zhang, Zhi Jin, Ge Li (PKU), 2026, arXiv:2607.00711v2. 419 task ambigui (il numero compare nel testo); requisiti ambigui causano un calo grande di pass@1 per tutti i modelli (cali assoluti 7.8-19.8 punti citati in sezione risultati, contesto non pienamente verificato); la chiarificazione oracolo resta leggermente sotto il requisito completo; le prestazioni di chiarimento calano con la densita' di ambiguita'; il ragionamento aiuta il codice piu' del chiarimento.
- **Implicazione**: anche una spec perfetta non porta al 100%; la qualita' del chiarimento non si deduce dalla qualita' del codice: servono casi con ambiguita' annotate.

### C5. Spec-driven development: evidenza empirica quasi assente [S]
Trovati solo: "Citation Discipline in Spec-Driven Development" (arXiv:2606.30689, citazione per riga riduce il determinismo dell'output, d=-0.76 Claude), registered report 2601.03878 (nessun risultato), SPECMINE (corpus di artefatti, 470.795 file in 73.030 repo, nessun outcome). **Non ho trovato uno studio controllato che dimostri che una spec scritta prima migliora l'esito su repository reali.** Il vantaggio dichiarato di spec-driven e' quindi non dimostrato dalla letteratura trovata.

---
## D. Piani

### D1. From Plan to Action: How Well Do Agents Follow the Plan? [V, PDF testo]
Shuyang Liu, Saman Dehghan, Jatin Ganhotra, Martin Hirzel, Reyhaneh Jabbarvand, ASE '26, arXiv:2604.12147. https://arxiv.org/abs/2604.12147
- 21.120 traiettorie SWE-agent, 4 LLM (GPT-5 mini, DeepSeek-V3, DeepSeek-R1, Devstral-small), SWE-bench Verified (497 istanze) e Pro, 8 varianti di piano. Piano standard (navigate-reproduce-patch-validate) migliora; **un piano scadente peggiora piu' di nessun piano**; aggiungere fasi "di buone pratiche" all'inizio puo' peggiorare se non allineate alla strategia interna del modello; promemoria periodici del piano riducono le violazioni e migliorano il successo. Su Pro la compliance cala del 13%. Non determinismo: 3 ripetizioni, McNemar significativo fra run; analisi poi ristretta alle istanze risolte in modo consistente.
- Limiti: solo riparazione di bug, SWE-agent, modelli non Claude Code.
- **Implicazione**: (1) fasi obbligatorie aggiuntive (es. regression test prima) possono nuocere: ogni obbligo L1/L2 va testato singolarmente (ablazione); (2) conferma che un hook che *re-inietta* il piano (reminder) e' sostenuto dai dati; (3) i piani del brainstorming vanno validati, non assunti buoni.

### D2. An Empirical Study of Harness Design for Coding Agents [V, alphaxiv, riassunto]
Run-Ze Fan et al., 2026, arXiv:2609.20804. 4 modelli (Nemotron-3 30B/120B/550B, Mistral-Medium-3.5), SWE-bench Verified + Terminal-Bench 2.1, 176 setting. "Planning shifts from an accuracy scaffold for weaker models to a cost saver for stronger models": poca variazione di accuratezza. Ablazioni solo a un budget.
- **Implicazione**: con modelli forti (Claude) ci si aspetta un effetto sull'accuratezza piccolo e uno sul costo: l'eval deve misurare entrambi; non aspettarsi grandi salti di pass rate.

### D3. RigorBench [V, PDF]
Meher Bhaskar Madiraju, Meher Sai Preetam Madiraju, 2026, arXiv:2606.22678. **Conflitto di interesse dichiarato**: gli autori sono sviluppatori dell'harness "Agent-Rigor" valutato.
- 100 task, ~410 esecuzioni, Gemini 3.5 Flash per tutti. Outcome Score: Agent-Rigor 0.83, Agent-Skills 0.72, Superpowers 0.70, ReAct base 0.64; RigorScore 0.53/0.39/0.41/0.40. Superpowers non migliora le metriche di processo rispetto al baseline. Correlazione processo-esito non significativa *dentro* un harness (r=0.12). Token medi 42.500 -> 37.400 con piano obbligatorio (-12%). I punteggi di processo sono "in parte per costruzione". Giudice LLM unico (Gemini).
- **Implicazione**: serve come esempio di cosa NON fare (benchmark costruito sul comportamento che l'harness impone, nessun test statistico fra bracci, n basso, run non ripetute). Ma e' l'unico dato su Superpowers vs baseline: nessun vantaggio di processo misurato. Misurare per tollgate l'esito (test nascosti), non l'aderenza al processo.

### D4. Piani in linguaggio naturale vs pseudo-codice; livello di dettaglio [S/assente]
Non ho trovato uno studio controllato che confronti formati di piano o dettaglio ottimale per coding agent. D1 e' l'evidenza piu' vicina (piani cattivi/aggiunte fuori allineamento nuocciono).

---
## E. Istruzioni e regole multiple

### E1. When Instructions Multiply (ManyIFEval, StyleMBPP) [V, PDF testo]
Keno Harada, Yudai Yamazaki, Masachika Taniguchi, Edison Marrese-Taylor, Takeshi Kojima, Yusuke Iwasawa, Yutaka Matsuo, Findings of EMNLP 2025, arXiv:2509.21051. https://arxiv.org/abs/2509.21051
- 10 LLM; ManyIFEval fino a 10 istruzioni (500 campioni), StyleMBPP fino a 6 istruzioni di stile su MBPP (300 campioni). Il successo a livello di prompt (tutte le istruzioni) cala col numero di istruzioni mentre l'accuratezza per istruzione resta alta. Esempi StyleMBPP (n=1 -> n=6): Claude 3.5 Sonnet 0.96 -> 0.80 per istruzione; la correttezza funzionale resta stabile ma "test + tutte le istruzioni" crolla. Una logistica sul solo numero di istruzioni predice l'accuratezza con errore ~0.02-0.05 su n=10. I modelli con ragionamento (o3-mini high) calano meno.
- Limiti: istruzioni semplici e verificabili; modelli del 2024-25 (Claude 3.5).
- **Implicazione**: ogni obbligo aggiunto al contesto (skill + hook + regole) riduce la probabilita' di rispettarli *tutti*. Regola di prodotto: pochi obblighi per livello e **applicati da hook deterministici**, non da testo. In eval: misurare l'aderenza a tutti gli obblighi simultaneamente (pass livello-prompt), non per singolo.

### E2. Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents? [V, HTML]
Thibaud Gloaguen, Niels Mundler, Mark Muller, Veselin Raychev, Martin Vechev, 2026, arXiv:2602.11988. https://arxiv.org/abs/2602.11988
- AGENTbench: 138 task Python da 12 repo con file di contesto scritti da sviluppatori; SWE-bench Lite 300 task. Agenti: Claude Code (Sonnet-4.5), Codex (GPT-5.2, GPT-5.1 mini), Qwen Code. File generati da LLM: successo -0.5% (Lite) e -2% (AGENTbench), costo +20% o piu'; file umani: ~+4% di successo, costo fino a ~+19%. Gli agenti *seguono* le istruzioni (uso di `uv` 1.6 volte/istanza se citato, < 0.01 altrimenti) e quindi fanno piu' test ed esplorazione, che rende i task piu' difficili. Gli autori raccomandano file minimi.
- **Implicazione**: le istruzioni extra costano ~20% di token e non migliorano necessariamente l'esito. Il budget di testo che tollgate inietta (skill, rules) va misurato in token e ridotto; il plugin deve dimostrare di battere "un CLAUDE.md minimo".

---
## F. Contaminazione e qualita' dei benchmark

### F1. SWE-Bench+: Enhanced Coding Benchmark for LLMs [V, HTML v2]
Reem Aleithan, Haoran Xue, Mohammad Mahdi Mohajer, Elijah Nnorom, Gias Uddin, Song Wang (York), 2024, arXiv:2410.06992. https://arxiv.org/abs/2410.06992
- Su 251 patch passanti di SWE-Agent+GPT-4: 32.67% con "solution leakage", 31.08% sospette per test deboli. Tasso di risoluzione 12.47% -> 3.97% (filtrato; la sezione 2.2 riporta 5.49%, incoerenza interna) -> 0.55% su issue posteriori al cutoff. Lite e Verified: leakage ~33%. Oltre il 94% delle issue precede i cutoff. Limiti: un solo modello, classificazione manuale, 0.55% = ~3 di 548 istanze.
- **Implicazione**: test deboli e leakage gonfiano il "successo": nei casi eval di tollgate servono test nascosti robusti e ispezione manuale di un campione di patch "passate".

### F2. The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason [V, HTML v4]
Shanchao Liang, Spandan Garg, Roshanak Zilouchian Moghaddam, 2025, arXiv:2506.12286.
- Solo da issue + nome repo: identificazione del file buggy 60-76% su Verified vs < 53% su repo esterni; overlap verbatim massimo 35% di 5-gram. Inferenza indiretta (nessun accesso ai dati di training); numeri variano fra versioni.
- **Implicazione**: non usare SWE-bench Verified come banco principale per Claude; costruire casi da repository privati/recenti o scritti ad hoc.

### F3. LiveCodeBench [S, abstract + grep]
Naman Jain et al., ICLR 2025, arXiv:2403.07974. Problemi con data di rilascio, valutazione per finestre temporali, calo marcato di alcuni modelli su problemi successivi al cutoff; il numero di problemi cambia per versione. Dominio: competizioni, non repository.

### F4. Benchmark realistici di repository [S per SWE-Lancer e FeatBench]
- SWE-Lancer (Miserendino, Wang, Patwardhan, Heidecke, OpenAI, ICML 2025, arXiv:2502.12115): 1.488 job Upwork da $1M, test end-to-end verificati tre volte. Nel testo: il miglior modello guadagna oltre $400.000 su $1.000.000 (sul set completo).
- FeatBench (Haorui Chen, Chengze Li, Jia Li, 2025, arXiv:2509.22237): implementazione di feature da prompt solo in linguaggio naturale, F2P+P2P; successo massimo 29.94%; comportamento di "scope creep" (implementazione aggressiva fuori richiesta).
- **Implicazione**: per tollgate lo scope creep e' un'esito misurabile (test P2P, diff minimality) dove gli obblighi di rigore possono aiutare o nuocere.

---
## G. Risposte alle domande operative per gli eval di tollgate

1. **Quante ripetizioni**: 3 sono il minimo per stimare pass^3 e un'idea della varianza (A3, D1 usa 3). Per rilevare effetti di 2 punti servono ~9-10+ run per configurazione (A2); per 1 punto ~36 (A2). Con budget limitato: pochi casi con effetto atteso grande, non molte run di effetti piccoli.
2. **Quanti casi**: per differenza di 3 punti con 80% di potenza ~1.000 domande (A1, caso d'esempio con omega^2=1/9); per effetto dichiarabile con ~30 casi serve un'enorme differenza (> 15 punti circa; stima mia da A1, non letta). ManyIFEval/StyleMBPP suggeriscono 300-500 campioni per stime stabili di aderenza multi-istruzione (E1). Consiglio: 30-50 casi stratificati per durata/tipo di file, 3-5 run, analisi appaiata per caso, IC95 con cluster per repo; dichiarare in anticipo "non concludente" sotto la soglia di effetto minimo rilevabile.
3. **Grader**: deterministici (test nascosti F2P/P2P, build, hook di conformita') come esito primario; niente giudice LLM come metrica primaria (D3, C2 limiti).
4. **Metriche**: successo, pass^k, token e $ per caso (A4, E2), tempo, scope creep (diff fuori richiesta), aderenza simultanea agli obblighi.
5. **Bracci**: (a) Claude Code puro, (b) Claude Code + CLAUDE.md minimo, (c) Superpowers da solo, (d) tollgate; ablazioni per singolo obbligo (D1).

## Cosa NON ho trovato
Studi controllati su: spec-first vs prompt diretto su repository reali; piano in linguaggio naturale vs pseudo-codice; dimensione ottimale del sotto-task con tassi di successo misurati. Segnalati come lacune, non come assenza di effetto.
