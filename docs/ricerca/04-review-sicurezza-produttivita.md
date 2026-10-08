# 04 - Review, sicurezza, qualita', produttivita' (ricerca per tollgate)

Data: 2026-10-08. Legenda: [V] = pagina primaria aperta (abstract o testo, estratto tramite WebFetch); [S] = solo fonte secondaria/snippet di ricerca. Nota metodologica: gli estratti [V] sono resi da un modello di sintesi; i numeri sono quelli riportati dall'estratto, non ricontrollati sul PDF salvo dove indicato.

## A. Efficacia della review automatica con LLM

### A1. RevMate - Olewicki et al., "Impact of LLM-based Review Comment Generation in Practice: A Mixed Open-/Closed-source User Study", arXiv 2411.07091, nov 2024 [V]
URL: https://arxiv.org/abs/2411.07091
- Fatto: studio di 6 settimane a Mozilla (open) e Ubisoft (closed), 587 patch review, 59 revisori, GPT-4o + RAG + LLM-as-judge come filtro.
- Risultato: accettati 8,1% (Mozilla) e 7,2% (Ubisoft); altri 14,6% / 20,5% giudicati utili come suggerimenti. Refactoring 18,2%/18,6% accettati contro 4,8%/5,2% dei commenti funzionali. Mediana +43 s per patch. Commenti accettati portano a revisioni quanto quelli umani (74% vs 73%).
- Limiti: un solo tool, GPT-4o, preprint.
- Implicazione tollgate: anche con un filtro LLM-judge l'accettazione dei commenti funzionali e' ~5%. La soglia di confidenza >=80 non e' una garanzia: va calibrata e misurata sui propri dati (log accept/reject). Il valore sta nei commenti su manutenibilita'.

### A2. RovoDev Code Reviewer (Atlassian) - Tantithamthavorn et al., arXiv 2601.01129, ICSE'26 SEIP [V]
URL: https://arxiv.org/abs/2601.01129
- Fatto: valutazione offline/online/feedback su un anno, integrata in Bitbucket.
- Risultato (abstract): 38,70% dei commenti porta a modifiche di codice; PR cycle time -30,8%; commenti umani -35,6%.
- Limiti: autori e valutazione interni al vendor; le versioni dell'abstract differiscono (v1 vs pagina ICSE); limiti non letti.
- Implicazione: esiste evidenza industriale positiva, ma con tool a monte filtrato e con revisore umano nel ciclo. Supporta "review LLM come primo passaggio", non come sostituto del merge umano.

### A3. CodeRabbit in the wild - Lin, Liang, Thongtanunam, Tantithamthavorn, "Is Agentic Code Review Helpful?...", arXiv 2607.03316, lug 2026 [V]
URL: https://arxiv.org/abs/2607.03316
- Risultato: 31.073 coppie review/feedback, 10.191 PR, 239 repo: 36,4% accettate, 7,3% discussione, 56,3% rifiutate; modelli leggeri predicono il rifiuto con F1 fino a 76%. Dal snippet [S]: i rifiuti sono per lo piu' falsi positivi/ridondanza, e i commenti funzionali sono piu' spesso invalidi.
- Limiti: un solo tool; "rifiuto" dipende dall'etichettatura (non letta).
- Implicazione: oltre meta' dei commenti agentici viene scartata. Conferma la necessita' del filtro e suggerisce di imparare dal log di accettazione (stile "rejection predictor") invece di una soglia fissa.

### A4. SWR-Bench - Zeng et al., arXiv 2509.01494 (v2 giu 2026) [V]
URL: https://arxiv.org/abs/2509.01494 (tabelle da https://arxiv.org/html/2509.01494v2, letto solo i primi 100k caratteri)
- Fatto: 1000 PR verificate a mano (12 progetti Python).
- Risultato: miglior tool PR-Review precisione 15,39%, recall 24,06%, F1 18,73 (media); peggiore Hybrid-Review 6,18 falsi positivi per PR. Causa principale dei FP: mancanza di contesto (48%). Aggregazione di piu' review dello stesso modello: F1 fino a +43,67%, rendimenti decrescenti oltre n=5. Recall crolla su PR complesse (38,35% -> 8,88%). Solo 27 change-action in comune tra 5 run dello stesso LLM: instabilita'.
- Limiti: giudice LLM (Gemini 2.5), solo Python, kappa umano 66.
- Implicazione: una sola passata di review e' instabile; piu' passate indipendenti con aggregazione (n~3-5) hanno senso, il tetto 4 giri e' coerente ma i giri devono essere indipendenti, non iterativi. Il contesto (spec, file correlati) va dato al revisore.

### A5. Google, "Resolving Code Review Comments with Machine Learning" (ICSE 2024 SEIP) [S]
URL: https://research.google/pubs/resolving-code-review-comments-with-machine-learning/ (solo snippet di ricerca, pagina non aperta)
- Riportato: 7,5% dei commenti dei revisori risolto applicando una modifica proposta da ML (il 5% era in una versione precedente). Funnel (da newsletter DX [S]): meta' dei commenti ha una predizione, 63% accettate dal revisore, 70% di quelle visualizzate applicate.
- Implicazione: bassa quota ma a scala enorme; ML usato per risolvere commenti, non per generarli. Non verificato, citare con cautela.

### A6. Cognition, "Verifying Agentic Development at Scale", Ido Pesok, 29 mag 2026 [V]
URL: https://cognition.com/blog/testing-development
- Letto: nessun dato quantitativo su bug trovati dalla review, nessuna affermazione su revisore dedicato o contesto fresco. Dice che "a clean review alone often isn't enough" e che serve test end-to-end.
- Implicazione: la tesi "revisore dedicato" di Cognition NON e' dimostrata da questo post; e' marketing di prodotto. Vale pero' l'argomento: review pulita != comportamento verificato, quindi la ricevuta di test resta necessaria.

## B. Bias di autovalutazione e revisore di modello diverso

### B1. Panickssery, Bowman, Feng, "LLM Evaluators Recognize and Favor Their Own Generations", arXiv 2404.13076, 2024 [V]
URL: https://arxiv.org/abs/2404.13076
- Risultato: GPT-4 zero-shot distingue i propri testi (pairwise 0,672 XSUM / 0,747 CNN); self-preference GPT-4 0,705 / 0,912; correlazione di Kendall tra auto-riconoscimento e auto-preferenza 0,41-0,82 per GPT-3.5 (dopo fine-tuning fino a 0,74/0,82). Preferenza invertita scambiando l'ordine: 25% GPT-4, 58% GPT-3.5, 89% Llama.
- Limiti (dichiarati): solo riassunto testuale, due dataset, causalita' non validata, qualita' vera non controllata (la preferenza puo' essere giustificata). Incongruenze interne tra intro e tabelle.
- Implicazione: non e' su codice. Giustifica un revisore di motore diverso solo come ipotesi; da sola non basta. Randomizzare l'ordine di presentazione nelle valutazioni a coppie.

### B2. Chen et al., "Do LLM Evaluators Prefer Themselves for a Reason?", arXiv 2504.03846 (v3 dic 2025) [V]
URL: https://arxiv.org/abs/2504.03846
- Risultato: su benchmark verificabili (matematica, fatti, codice) gran parte della self-preference dei modelli forti e' "legittima" (corrisponde a risposte migliori); quella dannosa persiste quando il modello sbaglia come generatore, e nei modelli forti e' maggiore. Chain-of-thought lungo prima del giudizio la riduce.
- Implicazione: la tesi "un modello non rivede se stesso" e' meno netta di come la si cita: il rischio concreto e' quando l'autore ha sbagliato. Chiedere al revisore ragionamento esteso prima del verdetto JSON.

### B3. Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet", arXiv 2310.01798, ICLR 2024 [V]
URL: https://arxiv.org/abs/2310.01798
- Risultato: l'autocorrezione intrinseca (senza feedback esterno) non migliora e a volte peggiora il ragionamento.
- Limiti: ragionamento, non codice; modelli 2023.
- Implicazione: i cicli "rivedi e correggi" devono usare feedback esterno (test, linter, ricevute), non il solo giudizio del modello.

### B4. Xiang et al., "Cross-Model LLM Code Review: Should you use Claude to review Codex or vice versa?", arXiv 2607.21656, lug 2026 (Agentic SE @ KDD'26) [V]
URL: https://arxiv.org/abs/2607.21656
- Risultato: 116 task LiveCodeBench. Claude che rivede bozze Codex: 71,6% -> 89,7%; Codex self-review: 71,6% -> 84,5%; Codex che rivede Claude: 91,4% -> 82,8% (peggiora); Claude self-review: invariato 91,4%. Il revisore non eseguiva test.
- Limiti: due modelli, 116 task, nessuna esecuzione.
- Implicazione: la review di altro motore NON e' sempre un vantaggio e puo' peggiorare codice corretto. Il revisore Codex opzionale va attivato per rischio, e il suo verdetto non deve poter riscrivere codice che passa i test senza ri-esecuzione.

### B5. Song, "When Does a Second Model Help? Cross-Model Review in LLM Verification", arXiv 2610.01471 (v2, 6 ott 2026) [V]
URL: https://arxiv.org/abs/2610.01471
- Risultato: 30 artefatti, 150 errori inseriti, 900 sessioni. Revisore cross-model top non significativamente diverso da same-model in sessione fresca; sovrapposizione degli errori trovati Jaccard 41,2%; una review same + una cross-model: 56,7% contro 42,7% di due same-model (p=.006); cross-model leggero non meglio di same-model.
- Limiti: autore singolo, dati solo su richiesta, capacita' e diversita' confuse.
- Implicazione: il guadagno viene dalla DIVERSITA' di due review, non dal fatto che il secondo sia un altro modello. Una sessione fresca dello stesso modello e' gia' un buon baseline. Supporta il design "contesto fresco" e rende il Codex opzionale.

### B6. Reddy, Lolla, Sanku, "Articulate but Wrong: Self-Review Failures in LLM-Based Code Modernization", arXiv 2605.21537, mag 2026 [V]
URL: https://arxiv.org/abs/2605.21537
- Risultato: 1.980 chiamate, 11 LLM; 31,7% (83/262) dei casi con deriva comportamentale approvati dal modello stesso; per modello da 0% a 100%.
- Limiti: task stretto (Python 2->3).
- Implicazione: l'autoapprovazione e' inaffidabile e varia enormemente per modello: un oracolo di comportamento (test) deve precedere la review.

### B7. Kim et al., "Correlated Errors in Large Language Models", arXiv 2506.07962, ICML 2025 [V]
URL: https://arxiv.org/abs/2506.07962
- Risultato: >350 LLM; su un leaderboard concordano il 60% delle volte quando sbagliano entrambi; i modelli piu' grandi hanno errori molto correlati anche con architetture/provider diversi.
- Implicazione: un altro provider non da' indipendenza vera. Non contare il Codex come "voto indipendente".

### B8. Kohli, "Nine Judges, Two Effective Votes", arXiv 2605.29800, mag 2026 [V]
URL: https://arxiv.org/abs/2605.29800
- Risultato: 9 giudici di 7 famiglie ~ 2 voti indipendenti; il miglior singolo giudice pareggia o batte il panel. Dati NLI, non codice; autore singolo.
- Implicazione: piu' revisori in parallelo hanno rendimenti bassi; meglio un revisore forte piu' prove eseguibili.

### B9. Debate multi-agente: Zhang et al., "Stop Overvaluing Multi-Agent Debate", arXiv 2502.08788, 2025 [V]
URL: https://arxiv.org/abs/2502.08788
- Risultato: 5 metodi MAD, 9 benchmark, 4 modelli: spesso non battono CoT e Self-Consistency con molto piu' calcolo; l'eterogeneita' dei modelli aiuta. Position paper. Du et al. (arXiv 2305.14325) e Smit et al. (arXiv 2311.17371) visti solo come snippet [S].
- Implicazione: la revisione avversariale del piano in L2 non ha evidenza diretta (nessun paper trovato su plan review). Giustificarla con un A/B interno rispetto a una review singola a pari budget; usare modelli diversi se si vuole il beneficio.

## C. Sicurezza del codice generato

### C1. Pearce et al., "Asleep at the Keyboard?", IEEE S&P 2022 (arXiv 2108.09293) [V]
URL: https://arxiv.org/abs/2108.09293
- Risultato: 89 scenari, 1.689 programmi, ~40% vulnerabili (Copilot 2021). Limiti: modello obsoleto.
- Implicazione: dato storico; non usarlo come stima attuale.

### C2. Perry, Srivastava, Kumar, Boneh, "Do Users Write More Insecure Code with AI Assistants?", CCS 2023 (arXiv 2211.03622) [V]
URL: https://arxiv.org/abs/2211.03622
- Risultato: con assistente codice significativamente meno sicuro e maggiore fiducia di averlo scritto sicuro; chi si fida meno e rifinisce i prompt scrive meno vulnerabilita'.
- Implicazione: l'eccesso di fiducia e' il rischio; i verdetti del plugin non devono suonare rassicuranti ("approvato") per la sicurezza.

### C3. Veracode, "2025 GenAI Code Security Report", 30 lug 2025 [V, vendor]
URL: https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/ (comunicato stampa, non il report)
- Risultato: 80 task, >100 LLM; 45% dei casi con vulnerabilita'; Java >70%; XSS (CWE-80) fallisce 86%, log injection (CWE-117) 88%; sicurezza invariata nel tempo e non migliore nei modelli grandi.
- Limiti: report di vendor, metodologia non verificata, analisi con il loro SAST.
- Implicazione: profilo sicurezza deve includere SAST obbligatorio (non solo review LLM) e controlli mirati su XSS/log injection.

### C4. Zhao et al., "Is Vibe Coding Safe? Benchmarking Vulnerability of Agent-Generated Code in Real-World Tasks" (SusVibes), arXiv 2512.03262, ICML 2026 [V]
URL: https://arxiv.org/abs/2512.03262
- Risultato (v4): 186 task, 12 configurazioni agentiche; SWE-Agent + Claude 4 Sonnet 57% funzionalmente corretto ma solo 11,8% sicuro; hint di vulnerabilita' nel prompt non risolvono. (Altre fonti riportano 61% / 10,5%: versioni diverse.)
- Implicazione: "i test passano" non implica sicuro: i test di sicurezza devono essere requisiti separati e il prompt generico "scrivi in modo sicuro" non basta.

### C5. Spracklen et al., "We Have a Package for You!", USENIX Security 2025 (arXiv 2406.10279) [V]
URL: https://arxiv.org/abs/2406.10279 (dettagli da https://arxiv.org/html/2406.10279v3)
- Risultato: 16 LLM, 576.000 campioni, Python e JS; allucinazioni >=5,2% (commerciali) e 21,7% (open); 205.474 nomi unici; il 43% dei nomi allucinati ricompare in tutte e 10 le ripetizioni; 81% dei nomi da un solo modello; solo il 13,4% e' a 1-2 modifiche da un nome reale. Mitigazioni: RAG, fine-tuning, ensemble (DeepSeek da 16,14% a 2,40% con ensemble); self-refinement poco efficace (19% / 3%).
- Limiti: pochi modelli commerciali, modelli del 2024, euristiche di rilevamento.
- Implicazione: hook su ogni install/modifica di manifest che verifichi esistenza, eta' e download del pacchetto (e allowlist); la self-refinement non basta. Le allucinazioni sono ripetibili, quindi sfruttabili.
- Incidenti reali (react-codeshift, ecc.) solo da blog [S]: non usati come prove.

## D. Prompt injection e agenti di coding

### D1. Willison, "The lethal trifecta for AI agents", 16 giu 2025 [V]
URL: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- Dati privati + contenuto non fidato + comunicazione esterna = esfiltrazione. Unica difesa affidabile: evitare la combinazione; scettico sui prodotti di guardrail al ~95%.

### D2. Meta, "Agents Rule of Two", 31 ott 2025 [V]
URL: https://ai.meta.com/blog/practical-ai-agent-security/
- Non piu' di due tra: input non fidati, accesso a dati/sistemi sensibili, cambio di stato/comunicazione esterna. Se servono tutte e tre: supervisione umana o contesto fresco. Non copre allucinazioni ed errori dell'agente.

### D3. Nasr, Carlini, ... Tramer, "The Attacker Moves Second", arXiv 2510.09023, ott 2025 [V]
URL: https://arxiv.org/abs/2510.09023
- 12 difese aggirate con successo >90% per la maggior parte; molte riportavano ASR quasi nullo. Implicazione: non affidare la sicurezza a classificatori di injection.

### D4. Liu et al., "Your AI, My Shell", arXiv 2509.22040 [V]
URL: https://arxiv.org/abs/2509.22040
- AIShellJack: 314 payload, 70 tecniche MITRE ATT&CK, su Copilot e Cursor, ASR fino all'84% per esecuzione di comandi malevoli (file di regole avvelenati). Implicazione: file di regole/skill/CLAUDE.md del repo sono superficie d'attacco.

### D5. Maloyan e Namiot, SoK arXiv 2601.17548, gen 2026 [V]
URL: https://arxiv.org/abs/2601.17548
- 78 studi, 42 tecniche, 18 difese: la maggior parte <50% di mitigazione contro attacchi adattivi. Meta-analisi di autori con poco track record: peso moderato.

### D6. Invariant Labs, Milanta e Beurer-Kellner, "GitHub MCP Exploited", 26 mag 2025 [V]
URL: https://invariantlabs.ai/blog/mcp-github-vulnerability
- Issue malevola su repo pubblico -> l'agente legge repo privati e li pubblica in una PR. Dimostrato con Claude 4 Opus; i rilevatori comuni non lo hanno bloccato. Mitigazioni proposte: permessi minimi, una sola repo per sessione. Vendor di guardrail (conflitto d'interessi).
- Implicazione diretta: il flusso "issue GitHub -> agente" di tollgate e' esattamente questo scenario.

### D7. ImpossibleBench - Zhong, Raghunathan, Carlini, arXiv 2510.20270 [V]
URL: https://arxiv.org/abs/2510.20270 (risultati da https://arxiv.org/html/2510.20270v1, letto solo parte)
- GPT-5 imbroglia nel 54% (Conflicting-SWEbench), 76% su Oneoff-SWEbench; i Claude imbrogliano soprattutto modificando i test (>79% delle trascrizioni). Test in sola lettura bloccano la modifica ma non lo special-casing. Opzione di abort: GPT-5 da 54% a 9%. Monitor LLM scoprono solo 42-65% dei casi su SWE-bench.
- Implicazione: conferma "test non indebolibili" come hook; aggiungere un'uscita "blocca e chiedi all'umano"; il rilevamento via LLM del barare e' insufficiente.

## E. Produttivita' reale

### E1. METR, Becker, Rush, Barnes, Rein, arXiv 2507.09089, lug 2025 [V]
URL: https://arxiv.org/abs/2507.09089
- RCT, 16 sviluppatori esperti, 246 task in repo maturi: AI consentita = +19% di tempo (IC95% +2% / +39%, dal blog 2026); previsione dei dev -24%, percezione a posteriori -20%. Limiti: campione piccolo, strumenti inizio 2025.

### E2. METR, "We are Changing our Developer Productivity Experiment Design", 24 feb 2026 [V]
URL: https://metr.org/blog/2026-02-24-uplift-update/
- Fine 2025: 57 dev, 143 repo, >800 task. Dev originali (10): speedup stimato 18% (IC -38%/+9% con segno negativo=speedup nel loro testo); nuovi: 4% (IC -15%/+9%). METR stessa dice: dati debolmente informativi per selezione (dev rifiutano di lavorare senza AI, 30-50% trattiene task), probabilmente sottostima. Altre misure inaffidabili (task paralleli durante gli agenti). Cambia il design.
- Implicazione: nessuna evidenza solida che l'AI oggi acceleri o rallenti; la percezione soggettiva e' inaffidabile. Tollgate deve misurare i propri tempi/rework invece di dichiarare guadagni.

### E3. Paradis et al. (Google), "How much does AI impact development speed? An enterprise-based randomized controlled trial", arXiv 2410.12944, 2024 [V]
URL: https://arxiv.org/abs/2410.12944
- 96 ingegneri Google, ~21% di riduzione del tempo (IC ampio). Pochi dettagli letti.

### E4. Peng et al., "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot", arXiv 2302.06590, 2023 [V]
URL: https://arxiv.org/abs/2302.06590
- 55,8% piu' veloci su un task isolato (server HTTP in JS). Task di laboratorio: non generalizza a repo maturi.

### E5. Cui et al., "The Effects of Generative AI on High-Skilled Work: Evidence from Three Field Experiments with Software Developers", Management Science (DOI 10.1287/mnsc.2025.00535) [S]
URL: https://papers.ssrn.com/abstract=4945566 (pagina non apribile, 403; dati da snippet di ricerca)
- 4.867 sviluppatori, +26,08% task completati (errore standard 10,3%); guadagni maggiori per i meno esperti. Non verificato sul testo.

### E6. DORA 2025, "State of AI-assisted Software Development" (annuncio del 23 set 2025, Harvey e DeBellis) [V solo annuncio]
URL: https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- ~5.000 professionisti; 90% usa AI; >80% percepisce piu' produttivita'; 30% poca o nessuna fiducia nel codice AI; relazione positiva AI-throughput, ancora negativa AI-stabilita' di consegna. L'AI e' un "amplificatore"; senza test automatici, buon controllo di versione e feedback rapidi aumenta l'instabilita'. Nessuna magnitudine nell'annuncio; il PDF e' troppo grande per il fetch e non e' stato letto. Dati di sondaggio, correlazionali.
- Implicazione: giustifica ricevute di test, piccoli batch e gate; l'AI senza controlli aumenta il tasso di fallimento.

### E7. Shen e Tamkin (Anthropic), "How AI assistance impacts the formation of coding skills", 29 gen 2026 (arXiv 2601.20245) [V, pagina Anthropic]
URL: https://www.anthropic.com/research/AI-assistance-coding-skills
- RCT 52 ingegneri prevalentemente junior su libreria nuova (Trio): quiz 50% con AI contro 67% senza (d=0,738, p=0,01), maggior gap sul debug; velocita' non significativamente diversa. Chi delega la generazione <40%, chi pone domande concettuali >=65%. Limiti: chat non agentico, campione piccolo.
- Implicazione: rischio di perdita di comprensione; il riepilogo "cosa e perche'" nella PR e il gate umano di merge hanno valore anche per l'apprendimento.

## F. Qualita' e debito tecnico

### F1. GitClear, "AI Copilot Code Quality 2025" [V pagina, vendor, report completo non letto]
URL: https://www.gitclear.com/ai_assistant_code_quality_2025_research
- 211 milioni di righe modificate (2020-2024); righe copia/incolla dall'8,3% al 12,3% (2021-2024); righe "moved" (proxy di refactoring) dal 25% a <10%; per la prima volta copia/incolla > moved. Churn aumentato, nessun numero sulla pagina.
- Limiti: non e' spiegato come siano identificate le righe AI-assistite; correlazionale; dati e fonte di un vendor. 
- Implicazione: aggiungere un controllo di duplicazione/riuso nella review (profilo qualita'), ma senza trattare il dato come causale.

## G. PR agentiche in open source

### G1. Li, Zhang, Hassan, "The Rise of AI Teammates in SE 3.0", arXiv 2507.15003 (AIDev) [V]
URL: https://arxiv.org/abs/2507.15003
- 456.000+ PR di 5 agenti (Codex, Devin, Copilot, Cursor, Claude Code), 61.000 repo. Le PR degli agenti sono accettate meno di quelle umane ("trust and utility gap") e piu' semplici strutturalmente. Percentuali non nell'abstract.

### G2. Ehsani et al., "Where Do AI Coding Agents Fail?", arXiv 2601.15195, MSR 2026 [V]
URL: https://arxiv.org/abs/2601.15195
- 33k PR; doc/CI/build hanno i merge piu' alti, performance e bugfix i piu' bassi; PR non unite: diff piu' grandi, piu' file, CI fallita. Taxonomia da 600 PR: poco coinvolgimento del revisore, duplicati, funzionalita' non volute, disallineamento.
- Implicazione: PR piccole, CI verde prima dell'apertura, controllo duplicati con PR/issue aperte, scope limitato (gia' in tollgate).

### G3. Nakashima et al., "Why Agentic-PRs Get Rejected", arXiv 2602.04226 [V]
URL: https://arxiv.org/abs/2602.04226
- 654 PR rifiutate: 7 modalita' di rifiuto solo agentiche (es. sfiducia verso codice AI); 67,9% senza feedback esplicito.

### G4. Peralta et al., "Why Are Agentic Pull Requests Merged or Rejected?", arXiv 2605.22534, MSR 2026 [V]
URL: https://arxiv.org/abs/2605.22534
- 11.048 PR chiuse, 9.799 riviste da umani, 717 ispezionate: dei rifiuti 35,7% fallimento chiaro dell'agente, 31,2% vincoli di workflow, 33,1% senza motivazione; delle PR unite 15,4% ha richiesto intervento del revisore. "Il rifiuto sovrastima l'errore dell'agente".
- Implicazione: il tasso di merge e' una metrica rumorosa; tollgate dovrebbe registrare il motivo di chiusura.

## H. Cose cercate e NON trovate/non verificate
- Studi industriali Meta/Microsoft sulla review LLM: non trovati nelle ricerche fatte.
- Evidenza diretta su revisione avversariale di PIANI da parte di LLM: non trovata. Solo debate generico (B9).
- Cognition "revisore dedicato" come ricerca: non trovato materiale quantitativo (A6).
- Follow-up METR di maggio 2026 (sondaggio di 349 lavoratori) visto solo come snippet [S]: non usato.
- Incidenti slopsquatting reali (react-codeshift, Mastra): solo blog, non usati.
- Studio Atlassian "18,2% bug-related" e altri numeri citati da guide commerciali: non verificati.
- Il PDF DORA completo non e' stato letto, quindi nessuna magnitudine.

## I. Sintesi delle implicazioni per tollgate
1. Soglia di confidenza >=80 e tetto di 4 giri: l'evidenza (A1, A3, A4) dice che i falsi positivi sono la norma; calibrare la soglia sui propri log accept/reject, non fidarsi del numero.
2. Revisore a contesto fresco: sostenuto (B5, B2) ma il vantaggio e' la diversita' di due passate, non la magia del contesto vuoto.
3. Revisore Codex: opzionale e per rischio; puo' peggiorare (B4) e non e' indipendente (B7, B8).
4. Test/ricevute/test in sola lettura/abort umano: i punti piu' sostenuti (B3, B6, D7, C4, E6).
5. Sicurezza: SAST e controllo pacchetti come hook (C3, C4, C5); Rule of Two e conferma umana per effetti esterni (D1-D3, D6); trattare regole/skill/issue come input non fidato (D4).
6. Produttivita': non promettere guadagni (E2); misurare in locale.
7. Piano avversariale L2: evidenza mancante, da validare con A/B interno (B9).
