# tollgate, nucleo: piano principale

Data: 8 ottobre 2026.
Spec: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 20). La spec dice **cosa** fa tollgate e perché; questo documento dice **in che ordine** si costruisce e **quale piano** copre ogni parte della spec. Il codice e i passi stanno nei piani specifici P0-P5.

Stato: P0 chiuso l'8 ottobre 2026 (`2026-10-08-tollgate-p0-verifiche.md`; esiti in `docs/verifiche/2026-10-08-p0-esiti.md`, applicati nella revisione 20 della spec). Nessun esito ha smentito un fatto portante: le sezioni 3 e 4 restano valide, con le note della matrice aggiornate. P1-P5 da scrivere.

---

## 1. Regole

1. **Un piano specifico alla volta.** P(n+1) si scrive solo quando P(n) è chiuso, partendo dal codice reale e dalle interfacce che P(n) ha davvero prodotto.
2. **Dopo P0 questo documento si rivede.** Gli esiti delle verifiche possono cambiare il disegno (sezione 16 della spec): prima di scrivere P1 si aggiornano la spec (nella prima revisione libera) e, se serve, le sezioni 3 e 4 di questo documento.
3. **Ogni piano specifico chiude con i suoi criteri.** Un piano è chiuso quando i criteri di accettazione che la matrice (sezione 4) gli assegna passano come test, e la sua revisione finale non ha rilievi `blocker` o `major` aperti.
4. **Si costruisce con Superpowers, non con tollgate.** `tollgate:execute` non esiste finché P3 non è chiuso: P1-P5 si eseguono con subagent-driven-development o executing-plans. Dal momento in cui il nucleo funziona si può usarlo su se stesso, in una cartella diversa da quella di sviluppo (spec, sezione 13).
5. **Una correzione della spec scoperta durante un piano** si registra come nuova revisione della spec, non solo nel piano.
6. **Questo documento si aggiorna alla chiusura di ogni piano**: stato in testa, sezione 2, e le righe della matrice eventualmente spostate.

---

## 2. Sequenza

| Piano | Obiettivo | Richiede | Consegna | Finito quando |
|---|---|---|---|---|
| **P0 Verifiche** | Provare le 14 voci aperte della sezione 16 (compreso `skills:` negli agenti di plugin) | Spec rev 19 | Rapporto `docs/verifiche/2026-10-08-p0-esiti.md`; nuova revisione della spec | Ogni voce di 16 ha esito `sì`, `no` o `non determinato`, e le conseguenze approvate sono nella spec |
| **P1 Fondamenta** | La libreria su cui poggia tutto: configurazione, DB, eventi, fasi, task, atti | P0 chiuso | `bin/tollgate` con i sottocomandi di base; pacchetto `tollgate_core` | Test unitari verdi; criteri 25 e la parte DB del 17 |
| **P2 Guardrail** | Gli hook locali e le analisi pure che userà anche il gate | P1 | Wrapper `hooks/run`, adattatore, registro dei controlli, `verify`, `waiver`, `block`; pacchetto `tollgate_analysis`; `plugin.json`, `hooks.json` | Ogni riga di 7.2 e 7.4 testata con input JSON reale di Claude Code; criteri della colonna P2 |
| **P3 Flusso** | Il ciclo completo in locale: dall'issue alla PR, con l'instradamento ai profili verticali, la Definition of Done e i budget dei task | P2 | Skill, agenti, `start`, `execute` e `task`, `finish`, `open-pr`, `sync`, `adopt`, `cleanup`, `abandon`, `reopen`, audit della spec | Test di integrazione su repo git temporaneo con `TOLLGATE_GH` finto; criteri della colonna P3 |
| **P4 Gate** | Il controllo autorevole su GitHub | P2 (analisi), P3 (blocco JSON della PR) | `gate run/evaluate/guard/base-ids`, i cinque workflow, `init` con la misura della modalità | I casi del criterio 10 sui due repo di prova (`protected` e `detect`); criteri della colonna P4 |
| **P5 Eval e CI** | La prova che tollgate migliora il risultato, e la CI del plugin | P3, P4 | I 9 casi di `claude plugin eval`, la Action di CI del repo di tollgate, documentazione d'uso | Eval con 3 esecuzioni per caso; CI verde |

P3 e P4 dipendono entrambi da P2 e sono in parte indipendenti: P4 può partire quando P3 ha fissato il blocco JSON della PR (18.1).

---

## 3. Interfacce tra i piani

Sono i punti in cui un piano consegna e un altro si appoggia. **I nomi sono indicativi: li fissa il piano che li produce**, e il piano successivo li copia dal codice, non da qui. Dopo la chiusura di ogni piano questa sezione si aggiorna con i nomi reali.

### Pacchetti

| Pacchetto | Piano | Responsabilità |
|---|---|---|
| `tollgate_core` | P1 | Configurazione, DB e migrazioni, eventi, fasi, `tasks`, atti, cartella di stato |
| `tollgate_analysis` | P2 | Funzioni pure, senza DB né rete: piano e scope, livello, test-guard, JUnit, deroghe, regole sui comandi Bash |
| `tollgate_checks` | P2 | I moduli del registro (spec 3.2): `CHECK` e `decide(event, ctx)` |
| `tollgate_flow` | P3 | Operazioni con git e `gh`: avvio, ripresa, task, finish, open-pr, sync, adopt |
| `tollgate_gate` | P4 | Calcolo del gate da zero, guard, identificativi della base, sentinel |

Regola: `tollgate_analysis` non importa mai `tollgate_core`. Così il gate su GitHub (P4) usa le stesse analisi della copia locale senza portarsi dietro il DB (spec 3.1: «stesso codice in locale e su GitHub»).

### Contratti

| Produce | Consuma | Contratto |
|---|---|---|
| P1 | P2, P3, P4 | Caricamento di `tollgate.toml` da un riferimento git (base del lavoro o punta del predefinito), con `schema_version`, chiavi sconosciute ignorate con avviso, errore sui tipi sbagliati (spec 11.4) |
| P1 | P2, P3 | Apertura del DB nella cartella di stato, con WAL, `busy_timeout`, migrazioni solo in avanti, backup con la API di SQLite (spec 12.1) |
| P1 | P2, P3, P5 | Registrazione di un evento con la busta di 18.4 e `seq` monotono; esportazione `events --after-seq` in JSONL |
| P1 | P2, P3 | Transizioni di fase (12.3) e di `tasks.state` (6.3) che rifiutano tutto ciò che non è in tabella |
| P1 | P2, P3 | Atti: registrazione, legame a sessione/lavoro/oggetto, scadenza, consumo; `finish` legato allo SHA di HEAD (8.4) |
| P2 | P3, P4 | Parsing del piano e scope (7.5), livello (5), test-guard (8.2), JUnit (forma degli identificativi per strumento, spec 7.5), deroghe (18.2) |
| P2 | P3 | Hook installati e registro dei controlli; `verify` produce ricevute (8.1) |
| P3 | P4 | Blocco JSON della PR (18.1), report e file di approvazione (18.3), verdetti (18.5) |
| P4 | P3 | `gate run` locale usato da `finish check` |

---

## 4. Matrice di copertura

### Sezioni della spec

| Sezione | Piano | Note |
|---|---|---|
| 0 Glossario | tutti | I nomi del glossario sono i nomi nel codice |
| 1 Scopo e modello di fiducia | — | Guida; i limiti di 1.2 diventano testo di `status` e della documentazione (P5) |
| 2 Decisioni | tutti | Vincoli globali di ogni piano |
| 3 Struttura del plugin | P2 (`plugin.json`, `hooks.json`), P3 (skill e agenti) | `marketplace.json` in P3 |
| 3.1 Sottocomandi | P1 (scheletro, `status`, `stats`, `db restore`, `events`), P2 (`hook`, `verify`, `waiver`, `block`), P3 (`start`, `task`, `finish`, `sync`, `adopt`, `cleanup`, `abandon`, `act apply`), P4 (`gate`, `init`) | Variabili di test con sentinella `.tollgate-test`: P1 |
| 3.2 Principi, registro, adattatore | P1 (configurazione), P2 (registro, adattatore, eventi d'ingresso, `ctx`) | |
| 4 Ruoli | P3 | Agenti e brief; agenti concreti per area in B |
| 5 Livelli | P2 (calcolo), P3 (tetto con `approve level`, fette con `--spec`), P4 (minimo nel gate) | |
| 6.1 Avvio | P3 | |
| 6.2 Spec e piano, audit della spec | P3 | Skill `spec-audit`, agenti avversari e auditor, file di approvazione, `reopen` |
| 6.3 Esecuzione | P1 (`tasks`), P2 (controllo delle skill usate, `PostToolUse Skill`), P3 (`execute`, `task`, agenti, instradamento ai profili, dimensione e budget del task, report a campi fissi) | Implementatori in primo piano con un nome fisso, ripresi per nome (rev 20) |
| 6.4 Chiusura | P3 | `finish check` usa `gate run` di P4: in P3 si usa una versione locale minima, sostituita in P4 |
| 6.5 Dopo la PR | P3 | |
| 6.6 Dove valgono le regole | P2 | |
| 7.1 Wrapper | P2 | |
| 7.2 Tabella degli hook | P2 | Righe di rev 20: `PostToolUse Agent` (nome → `agent_id`, taglio di `maxTurns` con chiusura del subagente), token a `SubagentStop`, `PreToolUse SendMessage` per nome, `SubagentHandback` unica fonte in auto mode, subagenti interni ignorati |
| 7.3 Sola lettura | P2 | |
| 7.4 Regole su Bash | P2 | |
| 7.5 `plan-check` | P2 | |
| 8.1 Ricevute | P2 | |
| 8.2 test-guard | P2 (analisi e hook), P4 (nel gate) | |
| 8.3 Deroghe e blocchi | P2 | |
| 8.4 Atti | P1 (modello), P2 (registrazione via hook), P3 (skill e consumo) | Atto da `command_name` e `command_args` (P0, rev 20) |
| 8.5 Effetti esterni | P2 | |
| 8.6 Revisori | P3 | Standard del revisore e disaccordo istruito (rev 18) |
| 8.7 Definition of Done | P1 (calcolo dai dati), P3 (`finish check`), P4 (voci ricalcolate nel gate) | |
| 9.1-9.6 Gate su GitHub | P4 | |
| 10 Revisione finale | P3 | |
| 11.1 Dipendenze | P2 | I tag esistono con il prefisso `v`; P2 verifica se il risolutore di `dependencies` lo accetta (spec 16), altrimenti il ripiego di 11.1 |
| 11.2 `init` | P4 | |
| 11.3 `setup` e statusline | P3 | Riusa `statusline/statusline.sh` |
| 11.4 `tollgate.toml` | P1 (caricamento e validazione), P4 (`init` lo propone) | |
| 12.1-12.3 Stato locale | P1 | |
| 12.4 Ripresa, adozione, pulizia | P1 (migrazioni), P3 (ripresa, `adopt`, `cleanup`) | |
| 13 Errori e casi limite | P2, P3, P4 | Ogni riga va nel piano che possiede il meccanismo |
| 14 Test del plugin | tutti (test), P5 (eval e CI) | |
| 16 Da verificare | P0 (chiuso) | Voci rimaste, da verificare all'inizio di P2: prefisso `v` in `dependencies`; taglio di `maxTurns` in background e durante una ripresa con `SendMessage` (riguarda i giri di correzione 1-3) |
| 17 Cosa resta aperto | P5 | Documentazione dei limiti |
| 18.1 Blocco JSON | P3 (scrittura), P4 (lettura) | |
| 18.2 Deroghe | P2 | |
| 18.3 Report e approvazioni | P3 | |
| 18.4 Eventi | P1 | |
| 18.5 Rilievi e verdetti | P3 | |

### Criteri di accettazione (sezione 15)

| Criterio | Piano | | Criterio | Piano |
|---|---|---|---|---|
| 1 Avvio | P3 | | 20 Rinomine | P2 |
| 2 Piano | P2 | | 21 Deroghe | P2, P4 |
| 3 Scope | P2 | | 22 Livelli | P2, P3, P4 |
| 4 Implementatore | P2 (hook), P3 (`task`) | | 23 Effetti ripetuti | P2 |
| 5 Commit | P2 | | 24 Audit della spec | P3 |
| 6 Comandi | P2 | | 25 Fasi | P1 |
| 7 Ambito | P2 | | 26 Da correggere | P3 |
| 8 Subagenti | P2 | | 27 Neutralizzazione | P4 |
| 9 Revisori | P3 | | 28 Ripresa | P3 |
| 10 Gate su GitHub | P4 | | 29 Profili | P2, P4 |
| 11 Protezione e modalità | P4 | | 30 Senza test | P2, P4 |
| 12 PR | P3 | | 31 Fasi dopo `finish` | P2, P3 |
| 13 Atti | P2 | | 32 Marcatori e skipped | P2, P4 |
| 14 Wrapper | P2 | | 33 Issue e deroghe nel gate | P4 |
| 15 Ricevute | P2 | | 34 Modalità | P2 (push negato), P4 |
| 16 Sync | P3 | | 35 Componenti spenti | P3, P4 |
| 17 Adozione e ripristino | P1 (`db restore`), P3 (`adopt`) | | 36 Piano registrato nel gate | P4 |
| 18 Componenti | P2, P3, P4 | | 37 Flusso dopo l'approvazione | P2 (hook), P3 |
| 19 Budget | P2 | | 38 Profili verticali | P2 (hook), P3 (`task start`, revisione) |
| | | | 39 Task piccoli e budget | P2 (`SubagentStop`), P3 |
| | | | 40 Revisione | P3 |
| | | | 41 Definition of Done | P3, P4 |
| | | | 42 Must-have legati ai test | P2 (`plan-check`), P3, P4 |
| | | | 43 Statistiche | P1 |
| | | | 44 `attenzione` a due gruppi | P4 |

Casi di eval (spec 14, 1-9): P5.

**Controllo.** Ogni sezione da 0 a 18 e ogni criterio da 1 a 44 ha almeno un piano. Un criterio assegnato a più piani è chiuso solo quando l'ultimo di quei piani lo fa passare.

---

## 5. Rischi della sequenza

| Rischio | Effetto | Come si gestisce |
|---|---|---|
| P0 smentisce un fatto portante (E1 ripresa, E4/I2 atti) | Cambia 6.3 o 8.4 | P1 non parte finché la spec non è aggiornata (regola 2) |
| `finish check` in P3 senza il gate completo | Doppio lavoro tra P3 e P4 | In P3 una versione minima dietro la stessa interfaccia di `gate run`, sostituita in P4 |
| Le interfacce di P1 si rivelano scomode in P2-P4 | Riscritture | P1 espone poche funzioni con test; le modifiche passano da una nuova revisione delle sue interfacce, non da scorciatoie |
| Testare gli hook senza Claude Code vero | Test che passano su input finti | Gli input JSON dei test di P2 vengono dai log reali della sonda di P0: campioni in `spikes/fixtures/hook-inputs/samples.json`, log completi anonimizzati in `docs/verifiche/evidenze/hook/` |
| Costo degli eval in P5 | Token e tempo | 3 esecuzioni per caso, come da spec; il costo si misura e si riporta |

---

## 6. Già decise per i sotto-progetti successivi

**Profili verticali (sotto-progetto B).** Il catalogo è in `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: 13 profili verticali e 2 trasversali, con le regole `tollgate:rules-<area>` distillate da fonti citate e **riviste dall'utente** prima di entrare nel plugin, e gli agenti `implementer-<area>`, `reviewer-<area>`, `final-<area>`. Il nucleo (P2, P3) consegna il contratto e l'instradamento; B scrive regole e agenti. Le bozze delle regole si possono preparare in parallelo a P1-P4, perché non toccano il codice del nucleo.

**Pratiche delle software house rimandate:**

Non sono nel nucleo perché richiedono la kanban (C) o dati accumulati nel tempo (D), ma sono **decise**, non scartate (`docs/RICERCA-ORGANIZZAZIONE.md`):

| Id | Pratica | Dove |
|---|---|---|
| C1 | Limite al lavoro in corso con regola pull | C |
| C2 | Metriche di flusso (tempo di ciclo, throughput, età dei lavori, rework) dagli eventi | C |
| C3 | Obiettivo per milestone con scope rinegoziabile | C |
| C4 | Prima i lavori più incerti; stato esplorazione/esecuzione | C |
| D1 | Post-mortem automatici che propongono regole per `rules-<area>`, approvate dall'utente | Dopo la v1 |
| D2 | Misura del team contro l'agente singolo a parità di token | D |
