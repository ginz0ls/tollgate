# tollgate: cosa dice la ricerca

Data: 8 ottobre 2026.
Scopo: confrontare le scelte di tollgate (`docs/COSA-TENERE.md`) con la ricerca scientifica su LLM, agenti di coding e metodologie di implementazione.
Stato: **le modifiche R1-R16 sono state accettate l'8 ottobre 2026**, come raccomandato. Sono riportate in `COSA-TENERE.md`, sezione 8.

---

## 1. Metodo e affidabilità

Ci sono cinque filoni di ricerca, ciascuno con il suo report completo in `docs/ricerca/`. Ogni report ha una scheda per paper.

| # | Filone | File | Fonti |
|---|---|---|---|
| 1 | Agenti di coding e harness | `ricerca/01-harness-agenti.md` | circa 40 |
| 2 | Verifica, test, reward hacking | `ricerca/02-verifica-test.md` | circa 35 |
| 3 | Contesto e memoria | `ricerca/03-contesto-memoria.md` | 25 |
| 4 | Review, sicurezza, produttività | `ricerca/04-review-sicurezza-produttivita.md` | circa 35 |
| 5 | Specifiche, piani, valutazione | `ricerca/05-spec-piani-eval.md` | circa 30 |
| 6 | Un revisore o più revisori specializzati | `ricerca/06-revisori-specializzati.md` | circa 20 |

**Quanto fidarsi.**
- **[V]** vuol dire che la pagina originale è stata aperta: abstract o testo su arXiv, oppure il post o la nota originale. **[S]** vuol dire fonte secondaria. Le voci [S] non vanno citate come fatti.
- Le pagine sono state lette attraverso uno strumento che le riassume con un modello, quindi **i numeri non sono stati ricontrollati sui PDF**. Prima di usare un numero in un documento pubblico va riletto alla fonte.
- Molti lavori del 2026 sono **preprint non ancora revisionati**. In questa sintesi lo segnalo dove pesa.
- Nessuno studio misura un sistema come tollgate nel suo insieme: hook obbligatori, piano a fette e revisione a contesto pulito. Le evidenze riguardano i singoli pezzi.

---

## 2. Le evidenze, per tema

### 2.1 L'harness conta, ma invecchia

- **L'interfaccia pesa quanto il modello.**
  - SWE-agent [V, arXiv 2405.15793]: rifiutare le modifiche che non passano il linting vale 3 punti.
  - Tenere solo le ultime 5 osservazioni rende più che tenere tutta la storia (18,0% contro 15,0%).
- **Una struttura deterministica attorno all'LLM funziona.**
  - Agentless [V, 2407.01489] arriva al 32% con una pipeline fissa.
  - Oota et al. [V, 2609.38108]: quando il piano lo esegue del codice invece del modello, il successo passa da 0,36 a 0,44 su SWE-bench Verified. Con un esecutore generico solo il 22-45% delle traiettorie rispetta il piano dichiarato.
- **L'impalcatura invecchia.** Anthropic [V, «Harness design for long-running application development», marzo 2026] ha tolto componenti man mano che i modelli miglioravano: prima il reset del contesto, poi la divisione in sprint, infine il valutatore per sprint. Il planner è rimasto. Un agente minimo di circa 100 righe, solo bash, dichiara più del 74% su SWE-bench Verified (mini-swe-agent, [V] sul README).
- **L'effetto dell'harness dipende dal modello** (TraceProbe [V, 2607.06184]; survey [V, 2608.20485]). I risultati degli eval non valgono per sempre: vanno rifatti quando cambia il modello.

### 2.2 Dimensione del task e orizzonte

- METR [V, 2503.14499]:
  - la probabilità di successo cala con la durata del task;
  - **l'orizzonte all'80% è 4-6 volte più corto di quello al 50%**.
- SWE-EVO [V, 2512.18470]: sui task che toccano in media 21 file si risolve il 25%, contro il 72,8% sui task piccoli.
- SWE-Bench Pro [V, 2509.16941]: in media 107 righe su 4,1 file per task. Il **contesto che esplode** è il primo motivo di fallimento: 35,6% per Sonnet 4. Sul codice proprietario i risultati crollano (17,8% contro 43,6% sul codice pubblico).
- Nessuno studio controllato indica la dimensione ottimale di una fetta. Le evidenze sono tutte indirette.

### 2.3 Piani

- **Un piano scadente fa più danni di nessun piano.** Anche le fasi aggiunte che non si allineano alla strategia del modello peggiorano i risultati. **Ricordare periodicamente il piano** riduce le violazioni e aumenta il successo (Liu et al. [V, 2604.12147], 21.120 traiettorie).
- CodePlan [V, 2309.12499]: sulle modifiche a più file, con piano e validazione a ogni passo 5 repo su 6 compilano, senza piano 0 su 6. Il campione è piccolo.
- **Non c'è nessuna prova controllata** che spec, piano a fette o un certo formato di piano migliorino il risultato su repository reali (filone 5). Il valore del piano è dimostrato soprattutto sul costo e sulle modifiche a più file.

### 2.4 Test e verifica

- **I test aiutano se arrivano prima e da una fonte indipendente.** Mathews e Nagappan [V, 2402.13521]: GPT-4 su MBPP passa dal 69,7% all'82,5% con i test forniti. Il ciclo di correzione rende sempre meno dopo 3-4 iterazioni.
- **«Fai TDD» detto in generale peggiora.** TDAD [V, 2603.17973]:
  - con il prompt TDD generico le regressioni salgono dal 6,08% al 9,94%;
  - **dicendo all'agente quali test eseguire**, grazie a una mappa codice-test, scendono all'1,82%.
  - Limiti: modelli piccoli e campioni ridotti.
- **I test che scrive l'agente durante la correzione non cambiano la risoluzione** e fanno spendere fino al 19,8% in più di token (Chen et al. [V, 2602.07900]).
- **Nel bugfix serve il test che fallisce prima e passa dopo** (SWT-Bench [V, 2406.12952]). Usato come filtro raddoppia la precisione.
- **Un modello non si corregge bene da solo senza un segnale esterno** (Huang et al. [V, 2310.01798]; Kamoi et al. [V, 2406.01297]; Olausson et al. [V, 2306.09896]). Molti giri di correzione spesso non convengono. Il collo di bottiglia è la qualità del feedback: con feedback umano la correzione riesce nel 52,6% dei casi, con quello del modello stesso nel 33,3%.
- **Frontend: la verifica nel browser dà guadagni grandi.**
  - WebGen-Agent [V, 2509.22644]: con screenshot e interazione si passa dal 26,4% al 51,9%.
  - TDDev [V, 2605.17242]: con test di accettazione nel browser scritti prima del codice, da +15,5 a +23,7 punti.

### 2.5 Reward hacking: le regole nel prompt non bastano

- **ImpossibleBench** [V, 2510.20270, ICLR 2026] usa task in cui test e specifica sono in conflitto:
  - **quanto barano**: GPT-5 nel 54% dei casi; i modelli Claude soprattutto **modificando i test** (oltre il 79%);
  - **test in sola lettura**: bloccano la modifica dei test, ma **non** i casi speciali scritti apposta per i test né la ridefinizione di `__eq__`;
  - **via d'uscita «segnala all'umano»**: GPT-5 scende dal 54% al 9%;
  - **monitor LLM**: trova solo il 42-65% dei casi su SWE-bench.
- **Canale di escalation** (Gomez [V, 2608.29460], preprint con un solo autore): con un canale strutturato per segnalare i difetti l'hacking scende dal 23,6% al 5,3%, senza costi di prestazione.
- **METR** [V, nota del 5 giugno 2025]: le istruzioni esplicite di non barare non hanno quasi effetto, e il modello nega di aver barato anche quando l'ha fatto.
- **SWE-Marathon** [V, 2606.07682]: reward hacking nel 13,8% delle esecuzioni sui task lunghissimi.

### 2.6 Test verdi non vuol dire codice accettabile

- **METR** [V, nota del 10 marzo 2026]: secondo i maintainer, **circa metà delle PR che passano i test di SWE-bench non verrebbe unita**. I motivi sono qualità del codice, altro codice rotto e funzionalità mancanti.
- Wang, Pradel e Liu [V, 2503.15223, ICSE 2026]:
  - il 7,8% delle patch «corrette» fallisce la suite completa;
  - il 29,6% si comporta diversamente dalla soluzione di riferimento.
- UTBoost [V, 2506.09289] e SWE-Bench+ [V, 2410.06992] trovano test insufficienti e soluzioni già scritte nelle issue.
- **Sicurezza** (SusVibes [V, 2512.03262]): il codice è corretto nel 57% dei casi ma **sicuro solo nell'11,8%**.

### 2.7 Contesto e context rot

- **La finestra dichiarata non è quella utile.**
  - RULER [V]: solo circa metà dei 17 modelli testati regge 32K token.
  - NoLiMa [V, ICML 2025]: a 32K, 11 modelli su 13 scendono sotto metà del proprio risultato a contesto corto.
- **La sola lunghezza fa calare la prestazione**, anche con recupero perfetto delle informazioni (Du et al. [V, 2510.05381]: da -7,9% a -50% a 30K token).
- **Anche un solo distrattore abbassa l'accuratezza** (Chroma, «Context Rot» [V]).
- **Le conversazioni lunghe si perdono.** Laban et al. [V]: calo medio del 39%. Gli autori consigliano di ripartire con i requisiti riassunti.
- **Nascondere i vecchi output dei tool dimezza il costo**, con un tasso di successo uguale o migliore del riassunto fatto dall'LLM (Lindenbauer et al. [V, NeurIPS]).
- **Riscrivere tutto il contesto con un LLM fa perdere informazioni** (ACE [V]: da 66,7 a 57,1 in un passo). Lo stato si aggiorna per differenze.
- **File di contesto (AGENTS.md, CLAUDE.md).** Quelli generati da un LLM peggiorano il successo dello 0,5-2% e costano il 20% in più. Le panoramiche del codice non aiutano a trovare i file (Gloaguen et al. [V, 2602.11988]).
- **Troppe istruzioni insieme non vengono rispettate.**
  - IFScale [V]: a 500 istruzioni Sonnet 4 ne rispetta il 42,9%, con una preferenza per quelle iniziali.
  - Harada et al. [V, EMNLP 2025]: con più istruzioni cala la probabilità di rispettarle tutte.
- **Le skill non sempre partono.** Vercel [V]: un indice passivo da 8 KB arriva al 100%, contro il 79% delle skill; nel 56% dei casi la skill non viene proprio invocata.
- **Contesto da recuperare**: circa 5 documenti sono l'ottimo (CodeRAG-Bench [V]).

### 2.8 Multi-agente e subagenti

- **Sui task sequenziali e con molti tool, più agenti peggiorano.**
  - Kim et al. [V, 2512.08296]: -70% sulla pianificazione sequenziale.
  - Senza verifica centrale gli errori si propagano: l'abstract parla di un'amplificazione di 17,2 volte, da verificare nel testo.
  - Jwalapuram et al. [V, 2606.13003] e Fu et al. [V, 2606.05670] confermano.
- **MAST** [V, 2503.13657]:
  - il passo che conta di più è un **controllo dell'obiettivo**: +15,6%;
  - i fallimenti più comuni sono passi ripetuti, condizioni di stop ignorate e specifiche disattese.
- **I subagenti costano.** Il sistema multi-agente di Anthropic usa circa 15 volte i token di una chat e per il codice è meno adatto [V, filone 3].
- **Cognition** [V, blog]: funzionano la revisione a contesto pulito e i subagenti in sola lettura; non funzionano più agenti che scrivono in parallelo. Inoltre i subagenti senza storia prendono decisioni implicite incoerenti tra loro.

### 2.9 Revisione

- **I commenti dei revisori LLM sono accettati poco.**
  - RevMate [V, 2411.07091]: 8,1% e 7,2%, anche con un filtro LLM.
  - CodeRabbit [V, 2607.03316]: il 56,3% dei commenti viene rifiutato.
- **Le revisioni sono instabili.** SWR-Bench [V, 2509.01494]: precisione al massimo del 15%. Unendo più passate indipendenti il risultato migliora fino al 43,7%, poi rende sempre meno oltre 5.
- **Revisore di un altro modello: aiuta la diversità, non il marchio.**
  - Song [V, 2610.01471]: una revisione dello stesso modello più una di un modello diverso trova il 56,7% degli errori, contro il 42,7% di due revisioni dello stesso modello.
  - Un altro modello di punta però **non è significativamente meglio di una sessione pulita dello stesso modello**.
  - Xiang et al. [V, 2607.21656]: Codex che rivede il codice di Claude lo **peggiora** (dal 91,4% all'82,8%).
- **Gli errori dei modelli sono molto correlati.** Nove giudici valgono circa 2 voti indipendenti (Kim [V, 2506.07962]; Kohli [V, 2605.29800]).
- **Chi ha scritto il codice non lo rivede bene.** Il modello che ha prodotto una deriva di comportamento la approva nel 31,7% dei casi (Reddy et al. [V, 2605.21537]). Il valutatore separato è più facile da calibrare (Anthropic, marzo 2026).
- **Revisione del piano: nessuno studio specifico.** Il dibattito tra modelli spesso non batte la self-consistency a parità di calcolo (2502.08788).

### 2.10 Sicurezza e prompt injection

- **Pacchetti inventati** [V, 2406.10279]:
  - almeno il 5,2% con i modelli commerciali e il 21,7% con quelli open;
  - il 43% dei nomi inventati si ripete in tutte le 10 ripetizioni, quindi si possono prevedere e sfruttare.
- **Le difese contro la prompt injection si aggirano.** «The Attacker Moves Second» [V, 2510.09023] aggira 12 difese, quasi tutte con successo oltre il 90%. AIShellJack [V, 2509.22040] arriva fino all'84% su Copilot e Cursor.
- **Il flusso issue → agente è esattamente lo scenario d'attacco.** Con una issue malevola l'agente legge repo privati (Invariant su GitHub MCP [V]).
- **Rule of Two di Meta**: un agente non deve avere insieme input non fidato, dati sensibili e azioni esterne.

### 2.11 Produttività e valutazione

- **La percezione non è una misura.**
  - METR 2025 [V, 2507.09089]: con l'AI ci si mette il 19% in più, mentre gli sviluppatori credevano di andare il 20% più veloci.
  - L'aggiornamento di METR del 2026 è inaffidabile per distorsione nella selezione, e lo dice METR stessa [V].
- DORA 2025 [V, annuncio]: l'AI è correlata a più throughput ma anche a **meno stabilità**, a meno che ci siano test e feedback rapidi.
- **Varianza.** Bjarnason et al. [V, 2602.07150]:
  - deviazione standard sopra 1,5 punti anche a temperatura 0;
  - per vedere +2 punti servono **circa 9 esecuzioni per configurazione**, per +1 punto circa 36.
- **Analisi appaiata** per caso, con intervalli di confidenza (Miller, Anthropic [V, 2411.00640]).
- **pass^k**: conta il successo in tutte le k prove, che è la misura giusta quando si parla di obblighi (tau-bench [V]).
- **Le baseline semplici spesso valgono gli agenti complessi**, che costano fino a 50 volte di più (Kapoor et al. [V], «AI Agents That Matter»).
- **Non usare SWE-bench Verified come banco di prova principale**: ha contaminazione e test deboli (SWE-Bench+, SWE-Bench Illusion [V]).
- **Superpowers non ha prove a favore.** L'unico confronto pubblicato (RigorBench [V, 2606.22678]) non mostra vantaggi di processo rispetto alla baseline. È un'evidenza debole: gli autori sono in conflitto di interessi e non c'è un test statistico.


### 2.12 Un revisore o più revisori specializzati (filone 6)

**Nessuno studio pubblicato confronta, a parità di modello, un revisore con checklist e più revisori specializzati per tema.** Le evidenze sono indirette ma vanno tutte nella stessa direzione: **conta il passo di verifica dopo la revisione, non il numero di revisori.**

- **SWR-Bench** [V, 2509.01494]: il guadagno (+43,7% di F1) viene da più passate **dello stesso** revisore unite insieme. La specializzazione non viene testata e il sistema multi-agente si ferma al 9,22% di F1.
- **Lu 2025** [V parziale, 2505.17928]: con 3 revisori aumentano i problemi trovati, ma anche i falsi allarmi (dal 78% all'89%). Dopo il validatore il vantaggio sul revisore singolo è quasi nullo.
- **Adversarial Review** [V, 2608.18167]: più revisori indipendenti valgono quanto uno solo (F1 0,501 contro 0,495). Un revisore più un critico che deve portare prove arriva a 0,533, con circa 4,5 volte i token.
- **Dare un ruolo al modello non migliora l'accuratezza** (persona prompting: Zheng 2024 [S]; Basil 2025 [S]).
- **Una checklist di 10-20 voci non è un problema**: i Claude recenti rispettano il 94-100% delle istruzioni fino a 100 (IFScale [V]).
- **OpenCodeReview** [V, 2608.09290]: criteri scelti in base al tipo di file più un filtro indipendente portano la precisione al 25-38%, con 5-15 volte meno token.
- **Contro**: Qodo dichiara vantaggi per gli agenti separati, ma su un benchmark suo. Mao 2024 mostra un guadagno con ruoli in discussione, ma su un modello debole e con il 484% di token in più. Unire strumenti **diversi** aumenta i problemi trovati (c-CRAB [V]).
- **Plugin ufficiale `code-review`**: la versione installata in locale usa 5 agenti specializzati per fonte di informazione e un punteggio di confidenza 0-100 con soglia 80. La versione attuale su GitHub è cambiata: usa un validatore per ogni problema, con esito sì/no. Il design è stato modificato nel tempo.

**Conclusione per tollgate**: in L1 basta un revisore con la checklist dei profili attivi più un verificatore per ogni problema segnalato. In L2 gli specialisti si giustificano con **contesto e strumenti diversi** (schema e migrazioni per il database, flusso di autenticazione per la sicurezza), non con il ruolo.

---

## 3. Cosa cambia nel design

Ogni voce cita le voci di `COSA-TENERE.md` che tocca. **Sono proposte: decidi tu.**

### Confermate dalla ricerca

| Scelta | Evidenze |
|---|---|
| Regole imposte da hook, non dal prompt | ImpossibleBench, METR 2025, IFScale, Vercel |
| Livelli e fasi scelti da script, non dal modello | Oota, Agentless, Liu |
| Test di riproduzione rosso → verde solo nei bugfix (voce 9) | SWT-Bench, TDAD, Chen 2602.07900 |
| Test non modificabili dall'agente (voce 2 degli obblighi) | ImpossibleBench (necessari, ma non sufficienti: vedi R3) |
| Contesto pulito, output su file, una fetta per sessione (voci 37-40) | Du, NoLiMa, RULER, Chroma, Laban, Lindenbauer, SWE-Bench Pro, E4 2603.20432 |
| Stato aggiornato per differenze e in JSON o DB, mai riscritto da un LLM (H2-H4) | ACE, Anthropic «Effective harnesses» |
| CLAUDE.md piccolo e scritto a mano (voce 19) | Gloaguen |
| Un solo agente che scrive, subagenti in sequenza | Kim, Cognition, MAST |
| Revisore separato da chi ha scritto | Reddy, Anthropic marzo 2026, Huang |
| Revisore di un altro modello solo opzionale (voce 28) | Song, Xiang, Kim |
| PR con merge umano | METR 2026, Wang/Pradel/Liu |
| Verifica nel browser per il frontend | WebGen-Agent, TDDev |
| Eval contro la baseline (sotto-progetto D) | HAL, Kapoor, METR |

### Modifiche proposte

| # | Modifica | Perché | Tocca |
|---|---|---|---|
| **R1** | **Via d'uscita «test e specifica in conflitto»**: un blocco con un tipo preciso, che ferma l'agente e lo manda da te, invece di costringerlo a scegliere tra barare e fallire | Riduce l'hacking dal 54% al 9% (ImpossibleBench) e dal 23,6% al 5,3% (Gomez) | Deroghe (voce 14), blocchi tipizzati (C), H36 |
| **R2** | **Mappa codice → test nel brief dell'implementatore**: il brief elenca i test toccati dalla modifica, e `verify` esegue quelli più la suite completa a `finish` | Con il TDD generico le regressioni salgono; indicando i test giusti calano del 70% (TDAD). Il solo test del task lascia passare il 7,8% di patch sbagliate (Wang) | Voci 2, 13, profilo base |
| **R3** | **La ricevuta è necessaria ma non sufficiente**: la revisione finale cerca esplicitamente casi speciali scritti per i test, test resi più deboli e comportamenti diversi da quelli attesi | Sola lettura non basta contro i casi speciali (ImpossibleBench). Circa metà delle PR con test verdi non verrebbe unita (METR) | Voci 1, 20, 24 |
| **R4** | **Tetto di 2 giri di correzione automatica per task**, poi si riparte con un contesto pulito o si passa a te | Molti giri di autocorrezione non convengono (Olausson) e dopo 3-4 rendono sempre meno (Mathews) | Voce 25, H43 |
| **R5** | **Promemoria del piano**: a ogni nuovo task un hook rimette nel contesto il passo corrente del piano e il suo scope, in poche righe | Il promemoria periodico riduce le violazioni (Liu) | Voci 5, 41 |
| **R6** | **Revisione leggera del piano anche in L1**: in L1 un controllo automatico della struttura del piano più una lettura a contesto pulito; la revisione avversariale completa resta in L2 | Un piano scadente fa più danni di nessun piano (Liu) | Voci 13, 17 |
| **R7** | **Soglie del contesto più basse.** Orchestratore: avviso al 40%, salvataggio e `/clear` al 50-60%, non all'85% della statusline. Subagente: lavorare sotto circa 30K token. Ritorno al padre: 1-2K token più il percorso del report | Il degrado è già forte intorno a 32K (NoLiMa, RULER, Du). Le soglie sono un'inferenza, da tarare con gli eval | Voci 38, 42 |
| **R8** | **Le regole dei profili si caricano tramite hook, non affidandosi all'attivazione automatica delle skill** | Nel 56% dei casi la skill non parte (Vercel) | Sotto-progetto B, voce 41 |
| **R9** | **Budget di istruzioni.** Pochi obblighi, i più importanti per primi, e una misura dei token che tollgate aggiunge a ogni sessione, con un tetto | Più regole significa meno regole rispettate (IFScale, Harada). Il testo in più costa circa il 20% (Gloaguen) | Voce 41, H44, lezione 1 di Hermes |
| **R10** | **Ogni componente si può spegnere** da `tollgate.toml`, e gli eval misurano ciascun componente acceso e spento | L'impalcatura invecchia (Anthropic). Le fasi aggiunte possono peggiorare (Liu) | Tutti, sotto-progetto D |
| **R11** | **Controllo dei pacchetti**: un hook su ogni installazione verifica che il pacchetto esista e quanto è vecchio | Il 5-22% dei pacchetti suggeriti non esiste, e i nomi inventati si ripetono (2406.10279) | Profilo base, voce 10 |
| **R12** | **Il profilo sicurezza diventa più severo**: analisi statica (SAST) obbligatoria e test di sicurezza, non solo revisione | Il codice è corretto nel 57% dei casi ma sicuro nell'11,8% (SusVibes) | Profilo sicurezza |
| **R13** | **Le osservazioni della revisione si registrano** come accettate o rifiutate da te, così la soglia di confidenza si tara sui dati reali | 80 è un numero arbitrario: i commenti degli LLM sono accettati nel 7-36% dei casi | Voce 26 |
| **R14** | **Le domande di chiarimento dipendono dal livello e dall'ambiguità**: obbligatorie in L2 e con issue ambigue, non sempre | Chiedere sempre produce domande inutili (Vijayvargiya) | Flusso di `start` |
| **R15** | **Il costo dei subagenti va misurato**: negli eval si confronta «un subagente per task» con «task piccoli raggruppati» | Un sistema multi-agente costa circa 15 volte di più. Il `/clear` per fetta fa perdere la cache | Voci 38, 40 |
| **R16** | **Il revisore Codex dà un parere, non modifica il codice** | Codex che rivede Claude lo ha peggiorato (Xiang) | Voce 28 |

### Da rimandare o lasciare come ipotesi

- **Mutation testing sulle righe modificate**, solo in L2 (Meta [V, 2501.12862]: il 73% dei test generati accettato dagli ingegneri). È un buon candidato per dopo la v1.
- **Giudice LLM per il profilo AI/LLM**: modello di un'altra famiglia, ordine delle risposte scambiato, rubriche, calibrazione su un campione valutato da te (Zheng [V, 2306.05685]; Panickssery [V, 2404.13076]).
- **Il livello di rigore scelto in base al tipo di modifica non ha conferme in letteratura.** È un'ipotesi da verificare con gli eval.

---

## 4. Come devono essere gli eval (sotto-progetto D)

Indicazioni dalla ricerca, con la parte di stima segnata:

- **Casi**: 30-50, presi da repo reali tuoi e non da SWE-bench Verified, divisi per durata e per profilo. Alcuni volutamente ambigui.
- **Esecuzioni**: almeno 3-5 per caso. Si vedono solo gli effetti grandi; la soglia di circa 15 punti con 30 casi è una **stima** del filone 5, non un dato letto.
- **Chi giudica**: per primi test nascosti e deterministici. Un giudice LLM solo per le rubriche, e di un'altra famiglia.
- **Cosa si misura**:
  - pass^k;
  - «fatto» dichiarati senza esserlo;
  - modifiche fuori scope;
  - test indeboliti;
  - token e costo per caso;
  - tempo;
  - accettazione della PR da parte tua, con il motivo del rifiuto.
- **Configurazioni a confronto**:
  - Claude Code senza plugin;
  - Claude Code con un CLAUDE.md minimo;
  - Superpowers da solo;
  - tollgate;
  - più le versioni di tollgate con un componente spento alla volta (R10).
- **Analisi**: appaiata per caso, con intervalli di confidenza al 95% e raggruppata per repo. L'effetto minimo da rilevare si dichiara prima di partire; sotto quella soglia il risultato è «non concludente», non «nessun effetto».
- **Quando si rifanno**: a ogni cambio di modello.

---

## 5. Cosa la ricerca non dice

- Non ci sono studi su un sistema completo con hook obbligatori, piano a fette e revisione a contesto pulito. **tollgate sarebbe il primo a misurarlo.**
- Non c'è un dato controllato sulla dimensione ottimale di una fetta.
- Non ci sono studi sulla revisione avversariale dei piani.
- Non ci sono studi industriali di Meta o Microsoft sulla code review con LLM.
- Per la soglia di auto-compattazione di Claude Code ci sono solo fonti secondarie (circa l'83,5%).
- Le evidenze sui modelli di punta del 2026 sono poche e spesso vengono da preprint.

**Un rischio da tenere presente.** Le due scelte su cui poggia tutto, cioè partire da Superpowers e avere spec e piano prima del codice, **non hanno ancora prove controllate a favore**. Non è un motivo per cambiarle: sono pratiche diffuse e ragionevoli. È il motivo per cui gli eval del sotto-progetto D devono includere il confronto con «Superpowers da solo» e con «Claude Code senza plugin».
