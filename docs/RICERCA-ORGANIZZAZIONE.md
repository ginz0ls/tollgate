# tollgate come software house di agenti: ricerca e proposta

Data: 8 ottobre 2026. Domanda dell'utente: importare il metodo delle software house (ruoli, skill, kanban, obiettivi) e riapplicarlo a un team di agenti, con il supporto di paper scientifici dove esistono.

Due ricerche: **paper** sui sistemi multi-agente organizzati come software house (abstract letti su arXiv; nessun articolo letto per intero) e **metodi reali** da fonti primarie lette (Kanban Guide 2025, Shape Up, DORA, Google eng-practices, GitLab, Scrum Guide 2020, Google SRE). I libri (Anderson, *Accelerate*, *Team Topologies*) e il PDF DORA 2025 non sono stati letti.

---

## 1. Cosa dicono i paper

**La leva non è il ruolo.** Le cose misurate che funzionano sono altre:

| Cosa funziona | Fonte |
|---|---|
| Verifica con esecuzione reale (test e build che girano davvero) | AgentForge, arXiv 2604.13120: 40% su SWE-bench Lite, +26-28 punti; l'ablazione attribuisce il guadagno al feedback di esecuzione e alla scomposizione |
| Verifica centralizzata: senza, gli errori si propagano | «Towards a Science of Scaling Agent Systems», arXiv 2512.08296 (260 configurazioni) |
| Revisione con disaccordo istruito: un revisore più un critico che verifica il revisore, con l'ordine di cercare difetti e citare prove | «Adversarial Review», arXiv 2608.18167: 3 agenti battono 5; la revisione ingenua produce falso consenso |
| Passaggi di consegne strutturati (note con campi fissi, non trascrizioni) | «Handoff Debt», arXiv 2606.02875: −42-63% di token alla ripresa |
| Il processo come struttura del prompt | FlowGen-Scrum, arXiv 2403.15852 (ICSE 2025): circa +15%, ma contro GPT-3.5 nudo e senza parità di token |

**Cosa non funziona o costa troppo:**

| Problema | Fonte |
|---|---|
| A parità di token un agente singolo eguaglia o batte il team (ragionamento, non codice) | Tran e Kiela, arXiv 2604.02460 |
| Multi-agente: circa 6 volte energia e tempo, con guadagni limitati | arXiv 2610.03010 |
| Su compiti sequenziali il team può perdere fino al 70% | arXiv 2512.08296 |
| Ruoli e persone: nessun beneficio isolato | Zheng 2024 (già in `docs/ricerca/06`) |
| I sistemi «a ruoli» falliscono per disallineamento tra agenti e verifica debole | MAST, arXiv 2503.13657 |
| Il miglior agente completa il 30% dei compiti di un'azienda software simulata | TheAgentCompany, arXiv 2412.14161 (non aperto) |

**Nessuno studio** ha misurato Definition of Done, limiti al lavoro in corso o retrospettive applicati ad agenti. Per queste pratiche l'evidenza è quella sulle persone (DORA, Google), e l'effetto sugli agenti va misurato nel plugin stesso (sotto-progetto D).

**Conferma per il disegno di tollgate.** Il disegno attuale va già nella direzione indicata: un coordinatore che verifica al centro, un implementatore e un revisore per task con contesto pulito, il gate che esegue davvero i test, il verificatore dei rilievi. Il team «software house» va quindi costruito sui **processi e sulle verifiche**, non su CEO, CTO e altri personaggi.

---

## 2. Cosa dicono i metodi reali

Le pratiche concrete con la loro fonte, in ordine di valore rispetto al costo:

| # | Pratica | Fonte | tollgate oggi |
|---|---|---|---|
| 1 | Task piccoli: circa 100 righe vanno bene, circa 1.000 sono troppe; oltre 500 serve una motivazione; test nello stesso task, refactoring separato. DORA lo raccomanda esplicitamente per il codice generato dall'AI | Google small CLs; GitLab MR workflow; dora.dev small batches | Solo le soglie di L0 |
| 2 | Gravità dei rilievi con criterio di arresto: si approva se il cambiamento migliora la salute del codice anche se non è perfetto; i «nit» non bloccano | Google, standard della revisione | Gravità sì, criterio no |
| 3 | Interruttore a budget fisso: tempo fisso, scope variabile; oltre il budget il lavoro si ferma e si ridisegna | Shape Up (appetite, circuit breaker) | Tetti di giri sì, budget no |
| 4 | Definition of Done versionata, con voci verificabili; ciò che non la rispetta non conta | GitLab (7 aree), Scrum Guide 2020 | Gate sì, DoD esplicita no |
| 5 | Limite al lavoro in corso con regola pull | Kanban Guide; DORA (efficace se accompagnato da visibilità) | No |
| 6 | Metriche di flusso: tempo di ciclo, throughput, età dei lavori, lavoro in corso; tasso di rework | Kanban Guide; DORA | Eventi sì, metriche no |
| 7 | Spec con «tane di coniglio» e «cosa non fare» | Shape Up (pitch) | No |
| 8 | Post-mortem senza colpe che diventano regole, con criteri di attivazione decisi prima | Google SRE | No (lezioni dopo la v1) |
| 9 | Escalation dopo K giri tra autore e revisore | Google | Sì (tetti dei giri) |
| 10 | Prima i punti più incerti; esplorazione distinta da esecuzione | Shape Up (hill chart) | No |

**Da non importare:** sprint e cool-down, story point e velocity, daily scrum, mentoring come scopo della revisione, premi. Sono leve pensate per le persone: per gli agenti si sostituiscono con stato condiviso, budget e regole scritte.

---

## 3. Decisioni (8 ottobre 2026)

**Stato:** tutte approvate dall'utente. O1-O7 sono nella spec del nucleo, revisione 18, ognuna come componente spegnibile; C1-C4 e D1-D2 sono registrate nel piano principale (sezione 6). Le soglie vanno tarate con le misure del sotto-progetto D.

### Nel nucleo (piccoli, alto valore)

| Id | Pratica | Da | Dove nella spec |
|---|---|---|---|
| O1 | **Dimensione del task**: alla chiusura del task, il diff oltre `task_lines_warn` (200) è segnalato al revisore; oltre `task_lines_max` (500) serve una motivazione nel report e `attenzione` lo mostra. `plan-adversary` segnala i task troppo grandi | Pratica 1 | 6.3, 11.4 |
| O2 | **Standard del revisore**: «approva se migliora la salute del codice»; solo `blocker` e `major` chiedono modifiche, `moderate` e `minor` sono note | Pratica 2 | 10, 18.5 |
| O3 | **Revisione con disaccordo istruito**: il revisore deve cercare difetti e citare prove (file e riga, regola `R-…`); il verificatore fa da critico | Paper 2608.18167 | 8.6, 10 |
| O4 | **Budget per task**: `maxTurns` nel frontmatter degli agenti e un tetto di token per livello; oltre il budget, `needs_you` con la proposta di dividere il task | Pratica 3 | 6.3, 11.4 |
| O5 | **Definition of Done per livello**, dichiarata in un file e verificata da comandi: per L1 ricevuta verde, revisione del task, nessun rilievo bloccante; in più le voci dei profili | Pratica 4 | nuovo 8.7 |
| O6 | **Report dell'implementatore a campi fissi** (fatto, test, file, dubbi, cosa resta), per passaggi di consegne economici | Paper 2606.02875 | 6.3, 18.5 |
| O7 | **Spec L2 con «Tane di coniglio» e «Cosa non fare»**, controllate dall'avversario della spec | Pratica 7 | 6.2 |

### Nel sotto-progetto C (kanban, obiettivi)

| Id | Pratica | Da |
|---|---|---|
| C1 | Limite al lavoro in corso con regola pull nella kanban | Pratica 5 |
| C2 | Metriche di flusso calcolate dagli eventi (`events --after-seq`) | Pratica 6 |
| C3 | Obiettivo per milestone, con scope rinegoziabile | Scrum (Sprint Goal) |
| C4 | Prima i lavori più incerti; stato esplorazione/esecuzione | Pratica 10 |

### Dopo la v1 (D e lezioni)

| Id | Pratica | Da |
|---|---|---|
| D1 | Post-mortem automatici: scattano su PR respinta più volte, revert, interruttore; producono una proposta di regola per `rules-<area>` che l'utente approva | Pratica 8 |
| D2 | Misura nel plugin: stesso task con agente singolo e con il team, a parità di token, con tempo, costo e qualità | Paper 2604.02460, 2610.03010 |

### Scartato

- Agenti-personaggio (CEO, CTO, product manager): nessun beneficio misurato, più costo.
- Riunioni simulate e discussioni tra agenti per arrivare a un consenso: falso consenso (2608.18167).
- Team multi-agente sui compiti sequenziali o semplici: peggio del singolo (2512.08296). Il livello L0 resta a un solo agente.
