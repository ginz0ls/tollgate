# 06 - Revisori specializzati vs generalista (tollgate L1/L2)

Data: 2026-10-08. Legenda: [V] letto (testo completo o parti rilevanti), [S] solo secondario/snippet di ricerca. Numeri riportati solo se letti.

## Esito in una riga
Nessuno studio controllato confronta, a parita' di modello e budget, "1 revisore con checklist" vs "N revisori per dimensione" su code review. Le evidenze indirette dicono: (a) la verifica/filtro migliora la precisione, (b) piu' passate indipendenti dello stesso prompt migliorano la recall con rendimenti decrescenti oltre n=5, (c) la specializzazione "per ruolo/persona" non ha prova di beneficio, (d) la decomposizione aiuta quando riduce il carico di istruzioni o l'ampiezza del contesto, non per il ruolo in se'.

## Schede

### 1. SWR-Bench [V]
Zeng et al., "SWR-Bench: Assessing LLM Performance in Real-World Code Review Comment Generation" (poi "Benchmarking and Studying the LLM-based Code Review"), arXiv 2509.01494, 2025. https://arxiv.org/abs/2509.01494 (testo letto da https://arxiv.org/html/2509.01494)
- Multi-Review: Self-Agg (n review indipendenti dello STESSO modello) e Multi-Agg (modelli diversi). L'aggregazione e' un LLM che riceve le n review concatenate e tiene i punti validi (nessuna dedup rule-based).
- n testati {0,1,3,5,10}. Gemini-2.5-Flash n=10: F1 21.91% (+43.67%), recall 30.44% (+118.83%). Gemini-2.5-Pro n=5: F1 23.84% (+23.01% su 19.38%). Qwen 7B +26.13%, 32B +19.25% (n=10).
- Il guadagno di recall > guadagno di F1: la precisione resta il problema. Oltre n=5 plateau, costo lineare; n=5 "sweet spot". Flash n=5: F1 20.48% a ~3.68e-3 $/PR contro Pro single-pass 19.38% a ~5.86e-3 $/PR.
- NON distingue review specializzate: sono tutte la stessa prompt-base (PR-Review). Quindi il +43% e' effetto "ensemble di campioni", non di specializzazione.
- L'unico sistema multi-agente valutato (CR-Agent) ha F1 medio 9.22%, attribuito a overhead di interazione e propagazione di errori. Precisione < 10% per la maggior parte degli strumenti.
- Implicazione tollgate: l'alternativa economica alla specializzazione e' n=3-5 passate dello stesso revisore + sintesi; vale solo in L2.

### 2. MARG [V]
D'Arcy, Hope, Birnbaum, Downey, "MARG: Multi-Agent Review Generation for Scientific Papers", arXiv 2401.04259, 2024. https://arxiv.org/html/2401.04259v1 (dominio: peer review di paper, NON codice)
- Commenti generici: 60% (baseline GPT-4 single) -> 29% (MARG-S con esperti experiments/clarity/impact). Commenti "buoni" per paper 1.7 -> 3.7 (p=0.09 vs SARG-B, utenti n=9: debole).
- Ablation: multi-agente SENZA esperti (MARG-TP) ha recall 8.49 < single-agent tuned SARG-TP 10.62 (precisione 5.34 vs 4.61). Gli autori: "simply applying a multi-agent approach does not always result in a performance improvement".
- Esperto singolo da solo: experiments-only recall 4.36, clarity-only 3.25, impact-only 8.88; il sistema completo 15.84. La fase di refinement vale 11.92 -> 15.84.
- Costo MARG-S: 1.236M token input e 51k output per paper contro 15.5k/3.2k del baseline (~80x input). 38-48% dei commenti giudicati molto inesatti in tutti i metodi.
- Implicazione: la specializzazione riduce la genericita' ma a costo enorme; il guadagno viene da esperti + refinement + contesto distribuito (paper lunghi), non dal ruolo. Per un diff che sta in una finestra non c'e' il vincolo di contesto che qui motiva la divisione.

### 3. CodeAgent (EMNLP 2024) [V parziale]
Tang, Kim et al., "CodeAgent: Autonomous Communicative Agents for Code Review", arXiv 2402.02172, EMNLP 2024. https://arxiv.org/html/2402.02172v4
- Ruoli: User, CEO, CPO, CTO, Reviewer, Coder + supervisore QA-Checker. Compiti: coerenza commit/codice, vulnerabilita', stile, revisione.
- Ablation QA-Checker (3.545 campioni vulnerabilita'): con QA-Checker 483 trovati / 449 confermati (Rate_cr 92.96%); senza 564 / 413 (73.23%). Cioe' il supervisore riduce i falsi positivi.
- Non c'e' ablation "single agent vs multi" propria; i baseline sono GPT-3.5 (36.69%), GPT-4 (51.42%), CoT (49.34%), ReAct (51.80%). Costi in token in Appendice N non leggibili. Incoerenze interne (15.96 vs 13.39 pp).
- Implicazione: dimostra il valore del controllore/filtro, non della specializzazione per dimensione.

### 4. Towards Practical Defect-Focused Automated Code Review [V parziale]
Lu et al., arXiv 2505.17928, 2025 (Kuaishou, C++ industriale). https://arxiv.org/pdf/2505.17928
- Pipeline: Reviewer (piu' istanze) -> Meta-Reviewer (unisce, scarta commenti segnalati da UN solo reviewer) -> Validator -> Translator.
- Tabella 4 (Full Flow, Top-5): 1 reviewer KBI 22.22, FAR1 78.04; 3 reviewer + meta KBI 31.11, FAR1 89.41; con Validator 3 reviewer KBI 20.00, FAR1 77.96, CPI1 20.97 vs 1 reviewer+validator KBI 15.56, FAR1 71.78, CPI1 20.06. Sintesi autori: "Increasing the number of reviewers lifts key bug inclusion but raises false alarms. A validator mitigates these alarms".
- Il validator abbassa FAR ma riduce anche KBI (scarta bug veri).
- FAR altissimo in assoluto (70-90%) per definizione severa.
- Implicazione: piu' revisori = piu' recall e piu' rumore; il guadagno netto dipende interamente dal filtro. Il vantaggio di 3 vs 1 dopo il validator e' piccolo (CPI1 20.97 vs 20.06).

### 5. Adversarial Review [V]
Qiu, Gill, "Adversarial Review: Structured Disagreement for Grounded Agentic Code Review", arXiv 2608.18167, ago 2026. https://arxiv.org/html/2608.18167
- LiveCodeBench: single-reviewer 77% (2 agenti), MARS (3 revisori indipendenti + meta-reviewer, 5 agenti) 82%, AR (reviewer + critico, 3 agenti) 87%. Due reviewer indipendenti: 75% < 77% single. SWE-PRBench F1: single 0.495, MARS 0.501, AR 0.533 (con vincolo di disaccordo evidenziato; AR naive 0.457 per falso consenso). Costo AR ~4.5x token di zero-shot (SWE-bench Verified).
- Gli autori parlano di "diminishing, and sometimes negative, returns" nello scalare i peer agent. Non valutano specializzazione per ruolo.
- Implicazione: piu' revisori indipendenti ~ nessun guadagno (0.495 -> 0.501); conta il passo avversariale/di verifica fondato sulle prove. Non e' una review di dimensione ma un benchmark misto.

### 6. OpenCodeReview [V]
Li et al. (Alibaba/NJU), "OpenCodeReview: Determinism over Non-Determinism for Cost-Effective Agent-Based Code Review", arXiv 2608.09290, ago 2026. https://arxiv.org/pdf/2608.09290
- Su AACR-Bench (200 PR, 10 linguaggi, 1.505 commenti verificati): fino a 2.17x SEM-F1 (25.10% vs 11.57% di Claude Code, stesso modello), 5-15x meno token. Precisione 25.2-37.8% vs 7.23-15.93% di Claude Code; Claude Code ha la recall piu' alta (28.9%) generando 4.580 commenti su 200 PR.
- Design: file e CRITERI di review scelti in modo deterministico per tipo di file (rule-guided dispatch), subagent paralleli PER FILE (non per dimensione), "Independent Reflection" = filtro che vede solo il diff e non puo' generare. Critica esplicita alle decomposizioni per ruolo (coder/tester): "do not align with the structure of review".
- Non ho trovato un'ablation che isoli ciascun modulo nel testo letto (grep): l'attribuzione e' degli autori.
- Implicazione: i criteri vanno selezionati deterministicamente per tipo di file e la dimensione e' una scelta di checklist, non di agente. Supporta "checklist composta dai profili attivi" in L1 e la parallelizzazione per file/area, non per dimensione.

### 7. Multi-role Consensus (vulnerability detection) [V]
Mao, Li, Jin, Li, Tei, arXiv 2403.14274 v4, 2024. https://arxiv.org/html/2403.14274v4
- gpt-3.5-turbo, C/C++ SySeVR. Developer+tester in discussione (max 5 round) vs singolo ruolo: F1 es. 0.667->0.816 (Group1 FC), 0.302->0.344 (Group3, pochi positivi). Medie dichiarate +13.48% precisione, +18.25% recall, +16.13% F1 (relativo/assoluto non chiaro). Costo: +484% token.
- Un solo modello debole, un solo dataset, nessuna ablation sui ruoli, nessuna significativita'.
- Implicazione: il "consenso a ruoli" costa ~5x token; i ruoli sono avvocati di posizioni (developer/tester) non specialisti di dimensione.

### 8. Persone/role prompting [S]
- Zheng, Pei, Logeswaran, Lee, Jurgens, "When 'A Helpful Assistant' Is Not Really Helpful", arXiv 2311.10054 (EMNLP Findings 2024). https://arxiv.org/pdf/2311.10054 : 162 ruoli, 2.410 domande fattuali, 4 famiglie; i persona non migliorano l'accuratezza rispetto al controllo; effetto "largely random"; scegliere in anticipo il ruolo migliore e' difficile [S, da riepilogo di ricerca].
- Basil, Shapiro, Shapiro, Mollick, Mollick, Meincke, "Prompting Science Report 4: Playing Pretend: Expert Personas Don't Improve Factual Accuracy", arXiv 2512.05858, dic 2025. https://arxiv.org/pdf/2512.05858 : 6 modelli, GPQA Diamond e MMLU-Pro; persona esperti ~ indistinguibili dal baseline; effetti significativi piu' spesso negativi; eccezione Gemini 2.0 Flash su MMLU-Pro [S].
- Controprova parziale: HALURust (arXiv 2503.10793) riporta Codellama 50%->68% accuratezza con ruolo "Rust security expert", ma ruolo e struttura (CO-STAR) sono confusi, modello debole [S].
- Implicazione: "sei un esperto di sicurezza" da solo non e' una ragione per separare un revisore. Se si separa, il valore deve venire da checklist/contesto/tool diversi, non dal ruolo.

### 9. Istruzioni multiple / checklist lunghe [V per IFScale, S per Harada]
- Jaroslawicz et al. (Distyl AI), "How Many Instructions Can LLMs Follow at Once?" (IFScale), arXiv 2507.11538, lug 2025. https://arxiv.org/html/2507.11538v1 [V]. Task: includere N parole-chiave in un report (non code review). Accuracy 10/50/100/250/500 istruzioni: GPT-4o 94.0/82.8/49.0/22.2/15.4; Claude Sonnet 4 100/98.0/94.4/77.2/42.9; Claude Opus 4 100/100/94.6/67.9/44.6; Claude 3.7 Sonnet 100/99.6/94.8/72.9/52.7. Le istruzioni iniziali sono rispettate di piu'.
- Harada et al., "Curse of Instructions" (ManyIFEval, ICLR 2025): tasso di successo su tutte le istruzioni cala quasi esponenzialmente con 1-10 istruzioni [S, non aperto].
- Implicazione: per modelli recenti una checklist da 10-20 voci non e' nella zona di collasso (nei test, 100% a 10 e ~95-100% a 50-100 per i Claude recenti); il rischio e' a centinaia di regole. "Lost in the checklist" non e' dimostrato per liste brevi su modelli attuali. Il costo e' soprattutto attenzione sul codice reale, non sul numero di voci: nessuno studio letto lo misura in code review.

### 10. Mixture-of-Agents / Self-MoA [V abstract]
- Wang et al., "Mixture-of-Agents Enhances Large Language Model Capabilities", arXiv 2406.04692, 2024. https://arxiv.org/pdf/2406.04692 [S].
- Li, Lin, Xia, Jin (Princeton), "Rethinking Mixture-of-Agents: Is Mixing Different Large Language Models Beneficial?", arXiv 2502.00674, feb 2025. https://arxiv.org/pdf/2502.00674 [V abstract]: Self-MoA (solo il miglior modello, piu' campioni) batte MoA misto: +6.6% su AlpacaEval 2.0, +3.8% medio su MMLU/CRUX/MATH; la qualita' del proponente pesa piu' della diversita'.
- Implicazione: la diversita' di prompt/ruolo non garantisce un guadagno; n campioni dello stesso buon modello e' un baseline forte. Non e' code review.

### 11. Anthropic Code Review gestito [V]
Documentazione ufficiale: https://code.claude.com/docs/en/code-review
- "multiple agents analyze the diff and surrounding code in parallel... Each agent looks for a different class of issue, then a verification step checks candidates against actual code behavior to filter out false positives. The results are deduplicated, ranked by severity". Costo medio 15-25 $ per review, ~20 minuti, scala con dimensione/complessita'/numero di issue da verificare. Focus di default sulla correttezza, non su stile o copertura test (per ridurre rumore).
- Nessun dato quantitativo di recall/precisione nella doc. Il perche' del design e' solo accennato (nessun benchmark pubblicato che confronti con un revisore singolo). Cifre di lancio (16% -> 54% PR con commenti sostanziosi, <1% issue marcate errate) provengono da stampa [S: sintesi di ricerca, non verificate sulla fonte Anthropic].
- REVIEW.md: "a long REVIEW.md dilutes the rules that matter most"; regole specifiche del repo "land more reliably" perche' arrivano direttamente agli agenti finder e verifier. Indica che Anthropic considera la lunghezza delle istruzioni un costo reale.
- Implicazione: il prodotto gestito e' multi-agente + verificatore; ma e' per PR di dimensione media/grande (20 min, 15-25 $), non evidenza che serva su cambi piccoli.

### 12. Plugin open source code-review [V]
https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/code-review/README.md e .../commands/code-review.md
- README: 2 agenti CLAUDE.md compliance, 1 bug detector (solo bug evidenti nel diff), 1 history analyzer (blame/storia), 1 scorer di confidenza per issue 0-100, soglia default 80. Motivazioni dichiarate: "Multiple independent agents for comprehensive review", "confidence scoring to filter out false positives". Nessuna spiegazione approfondita ne' dati.
- ATTENZIONE: il file commands/code-review.md che ho letto OGGI (main) e' diverso dalla descrizione ricevuta: Haiku per stop-check e discovery CLAUDE.md, Sonnet per riassunto e CLAUDE.md, Opus per bug scan sul diff e per "introduced-code problems" (sicurezza/logica), validazione per issue con subagent (Opus bug, Sonnet CLAUDE.md), filtro binario "validato o scartato", nessuna scala numerica 0-100. Il README dice ancora soglia 80. Il design e' cambiato nel tempo: citare la versione con data.
- Gli agenti sono divisi per FONTE di evidenza/prospettiva (regole, bug nel diff, storia), NON per dimensione tecnica; l'elenco di esclusione dice di NON segnalare "test coverage o sicurezza generica" a meno che CLAUDE.md lo richieda. Nessun dato su recall.
- Implicazione: il modello Anthropic non e' un'argomentazione per "uno per sicurezza, uno per DB": e' fan-out di finder + verifica per issue. La parte trasferibile e' la verifica per issue, non la specializzazione.

### 13. Cursor Bugbot [V forum]
"Building a better Bugbot" https://forum.cursor.com/t/building-a-better-bugbot/149040
- Prima versione: piu' passate di bug-finding in parallelo con diff mischiati, poi majority voting per tenere le issue che compaiono in piu' passate. Poi passaggio ad anello agentico (strumenti, indagine). Resolution rate ~52% -> oltre 70% in ~40 esperimenti; piu' del doppio di bug risolti per PR. Changelog aprile 2026 riporta 78% [S].
- Nessun confronto specializzati vs generalista; nessun dato di falsi positivi nel post. Metrica interna (resolution rate), non recall.
- Implicazione: la tecnica vincente nota e' ensemble di passate identiche + voto, poi agentico; non specializzazione.

### 14. Qodo 2.0 [V blog, dati di vendor]
https://www.qodo.ai/blog/introducing-qodo-2-0/
- "multi-agent expert review architecture": agenti con contesto proprio per bug, standard, rischio, contesto; judge agent che risolve conflitti, deduplica, filtra. Dichiara F1 60.1%, recall 56.7%, "+9% sul secondo". Benchmark proprio (iniezione di issue verificate), precisione non riportata, numero PR/strumenti non nel post, incoerenza interna sulla "exhaustive mode".
- La motivazione e' "asking one reviewer to do all of this at once leads to tradeoffs between depth, speed, and coverage". E' l'unico argomento pro-specializzazione con dati, ma e' di parte, non replicabile dal testo letto, senza ablation single vs multi.

### 15. Greptile / CodeRabbit [S]
Dati di vendor (Greptile 82% catch su 50 PR proprie, CodeRabbit 44%; fonti in conflitto tra loro). CodeRabbit OpenSSF CVE Benchmark F1 36.19%. Nessuna evidenza su specializzazione. Non usabili come prova.

### 16. Benchmark indipendente c-CRAB [V]
Zhang et al. (NUS), "Code Review Agent Benchmark", arXiv 2603.23448, 2026. https://arxiv.org/html/2603.23448v2
- Claude Code 32.1%, Devin 24.8%, PR-Agent 23.1%, Codex 20.1% di pass rate su 234 test derivati da review umane; unione degli strumenti 41.5%. Piu' forti su robustezza/correttezza funzionale, piu' deboli su documentazione e design. Nessun confronto multi vs single, costo non riportato.
- Implicazione: l'unione degli strumenti recupera 9 punti sopra il migliore: la diversita' di STRUMENTO/modello aggiunge recall, coerente con SWR-Bench Multi-Agg.

### 17. Altro [S] non letto, citato solo come indizio
- Hydra-Reviewer (IEEE TSE 2025, https://ieeexplore.ieee.org/document/11203269/): multi-agente "olistico", BLEU 8.20 vs 7.85 DeepSeek-V3; metrica testuale, non utile per recall/precisione.
- Refute-or-Promote (Agarwal, arXiv 2604.19049, apr 2026): metodo avversariale a stadi per alta precisione; PDF non leggibile, nessun numero preso.
- QASecClaw (arXiv 2605.01885): agente filtro su SAST, precisione 0.695 -> 0.951, recall 0.900 -> 0.871 [S].

## Sintesi per tollgate

Domanda: specializzati anche in L1?
Raccomandazione: NO. Mantenere in L1 un solo revisore a contesto pulito con checklist dei profili attivi, e aggiungere un verificatore per issue prima della consegna (non un secondo finder). In L2 conservare "generale + specialisti" ma motivarlo con contesto/tool diversi per profilo (es. schema e migrazioni per DB, flusso auth per sicurezza), non con il ruolo.
Perche': (1) nessuna evidenza che il ruolo/persona migliori l'accuratezza (Zheng 2024, Basil 2025); (2) piu' revisori alzano la recall ma anche i falsi positivi, e il guadagno netto dipende dal filtro (Lu 2025, MARG-TP, Adversarial Review 0.495 -> 0.501); (3) il costo cresce molto (MARG ~80x input, consenso a ruoli +484%, AR 4.5x); (4) checklist di 10-20 voci non cadono nella zona di collasso nei test su Claude recenti.
Soglia: nessun studio la quantifica. Ipotesi operativa (NON misurata): sotto ~200-300 righe di diff o 1-3 file e senza rischio dichiarato, un solo revisore; il fan-out si giustifica quando il diff supera la finestra di attenzione utile (molti file, dimensioni grandi) o tocca profili ad alto rischio. OpenCodeReview divide per file, non per dimensione, quando il diff e' multi-file.
Condizioni per rivedere: misura interna su un set di PR con bug noti (stesso modello, A/B: checklist vs specialisti), con recall, precisione dopo verifica, varianza tra 3 esecuzioni e token.

## Lacune
- Nessun A/B pubblicato single+checklist vs specialisti per dimensione su codice.
- "Lost in the checklist" specifico per code review non trovato; ho solo IFScale (task sintetico) e Harada (secondario).
- Motivazione ufficiale Anthropic del design a 5 agenti: non trovata; la doc dice solo "each agent looks for a different class of issue".
- Dedup/aggregazione: SWR-Bench usa sintesi LLM, Lu usa voto di accordo, Cursor voto di maggioranza; non c'e' confronto tra metodi di aggregazione.
