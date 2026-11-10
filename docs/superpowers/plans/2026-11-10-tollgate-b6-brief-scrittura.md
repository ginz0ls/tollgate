# Brief per la sessione che scrive il piano di B6 (profilo `frontend`)

Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa scrivere
Quattro file, con la data di oggi nel nome, sul modello di quelli di B5 (`docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md`, `-esecuzione.md`, `-brief-sessione.md`, `-brief-goal.md`):
- il piano di B6, con «Fatti verificati», «Global Constraints», «Decisioni di questo piano», «Review Focus», «Copertura» e i task con firme e test (non il codice);
- le istruzioni d'esecuzione (dove lavorare, scan pre-flight, ordine e modelli, regole di cautela con le sole eccezioni del controller, quando fermarsi e chiedere, chiusura);
- il brief della sessione che lo eseguirà, con la sezione «Il lavoro è finito quando»;
- il brief corto per l'obiettivo (`/goal`), con la sezione «Finito quando» scritta a situazioni come quello di B5 (regole approvate, rinviate, in attesa dell'utente, fermata per un altro caso), con le righe esatte del ledger e le condizioni verificabili leggendo file e transcript.

Solo documenti: nessun codice, nessun `claude -p`, nessun eval. Rete solo per leggere con `WebFetch` le pagine ufficiali che servono alle fonti di `rules-frontend` e ai fatti del piano. Lavora su `main`, un commit per ogni giro di revisione, niente push.

## Da leggere
1. Il progetto di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero: è l'autorità. Per `frontend`: riga della sezione 3.4 («per ogni libreria UI toccata, documentazione della versione in `package.json`; prima di creare un componente, cerca se ne esiste già uno simile nel progetto»), sezione 4 (livello minimo **L0**), sezione 5 (come nascono le regole e l'approvazione dell'utente), sezioni 11 e 12 (le scelte di B4 e B5: `services/` fuori da `backend` perché è codice d'interfaccia, esclusione per frammento).
2. Il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: la riga `frontend` della sezione 2 (`**/*.{tsx,jsx,vue,svelte,css,scss}`, `**/components/**`, `**/app/**/page.*`, `web/**`) con la **nota sulle graffe** (`globs` non le espande: un pattern per estensione), 2.1 (skill: `frontend-design`, `ui-ux-pro-max`, taste-skill; revisore con `rules-a11y` e anti-ui-slop), 2.3 (`dod` «lint, typecheck, test dei componenti»), 3 (`a11y` e `performance` trasversali), 4 (fonti e licenze di `rules-frontend` e `rules-a11y`), la nota sul prefisso `R-FRONTEND-`.
3. Il piano principale `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2 (riga B6), 3 (righe **B4 → B5-B7** e **B5 → B6-B7**: `parse_pattern`, `concrete_for(..., exclude=)`, `Fragment.exclude`, la regola sui file trovati per contenuto da un altro profilo, `FLAG_EFFECTS`, `script_name`, `AREAS`), 9 (tutti i blocchi aperti, soprattutto **«A B6-B8, da B5»** e le righe «aperto per `**/*.{tsx,jsx}` (B6)»), 14 («Prove di B5»).
4. La spec del nucleo, revisione 32: 6.3 (precedenza tra profili per segmenti letterali), 7.1, 7.3, 8.5, 8.7, 11.2, 11.4, 16, 18.4.
5. Il registro di B5 `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/` (`README.md`, `progress.md`, `final-review.md` con il triage, `carry.md`, `preflight-scan.md`, `task-4-fonti-brief.md`, `task-8-rapporto-brief.md`, `cautele.md`): il metodo più recente, con le lezioni sotto.
6. Gli esempi da copiare: `skills/rules-backend/SKILL.md`, `templates/profiles/backend.toml`, `ai.toml`, `infra.toml`, `docs/profili/backend.md`, `docs/profili/verifiche/backend-fonti.md`, `agents/implementer-backend.md`, `agents/reviewer-backend.md`, `tests/test_rules_backend.py`; il caso `backend` di `spikes/run-b1-flow.sh` e `spikes/b5/flow/`.
7. La memoria del progetto (`plugin-workflow-decisioni.md`, voci di B5; `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`).

## Scelte dell'utente, da non riaprire
- `frontend` ha livello minimo L0: per i lavori piccoli solo l'avviso (progetto, sezione 4).
- Le regole nascono così: bozza con la fonte per ogni regola, verifica delle fonti da un agente di sola lettura, una pagina in parole semplici per l'utente, che approva, corregge o toglie; solo le regole approvate entrano; senza approvazione il profilo non si propone (progetto, sezione 5).
- Le cartelle `services/` sono codice d'interfaccia, non di `backend` (progetto, sezione 12).
- `routes/` e `handlers/` restano di `backend` a qualunque profondità, con il costo che una cartella `routes/` d'interfaccia vada a `backend` finché l'utente non la toglie a mano (approvato il 10/11/2026, punto 5 della pagina di `backend`): B6 può proporre un rimedio, non cambiarlo da solo.
- Un file che il rilevamento per contenuto assegna a un profilo non accende un altro profilo per la sola cartella (correzione di I-1 di B5, scelta dell'utente del 10/11/2026).
- Il repo `ginz0ls/tollgate` è pubblico: dalle pagine dei fornitori e dalle skill si prendono fatti con parole nostre, mai testo intero; niente nomi di progetti privati dell'utente, niente nome utente né host, niente token.

## Da decidere nel piano
- **I pattern per estensione.** `fragments.parse_pattern` oggi rifiuta `**/*.tsx`: serve una forma nuova (`ext`?), il suo percorso concreto in `init` e la sua specificità (zero segmenti letterali: perde contro ogni cartella e nome di `ai`, `infra`, `backend`). Contare sul disco dell'utente, per nome e senza aprire i file, quante cartelle e quali estensioni hanno i progetti con un'interfaccia, come in B5.
- **La precedenza con gli altri profili**, caso per caso e con un test ciascuno: `**/components/**` dentro `server/` o `ai/`; un `.tsx` sotto `api/` o `app/api/` (rotte di Next.js, `backend`); `app/**/page.*` contro `**/routes/**`; `services/` (interfaccia) che resta al generico o va a `frontend`; i file di `ai` in una cartella `components/`. La revisione finale di B5 ha trovato proprio un caso così (I-1): il piano deve avere la tabella delle precedenze e la scansione dei casi prima del codice.
- **Il rimedio per `routes/` d'interfaccia** (rinvio di B5): un rilevamento per contenuto di `frontend` che, con la regola di I-1, tiene i file d'interfaccia fuori da `backend`? Va portato all'utente se tocca il profilo `backend` approvato.
- **Il rilevamento per contenuto di `frontend`**: serve, con quali marcatori (righe di import di React, Vue, Svelte?) e con quali falsi positivi; o bastano le estensioni.
- **`rules-a11y`**: dentro `rules-frontend`, una skill a parte per il solo revisore (catalogo 2.1), o rinviata al profilo trasversale. In parole semplici all'utente, con il costo.
- **Le skill del catalogo** (`frontend-design`, `ui-ux-pro-max`, taste-skill, anti-ui-slop): licenze verificate sulle copie locali, precaricate o solo in «Dove informarsi» (decisione 9 di B5).
- **Il `dod`** («lint, typecheck, test dei componenti»): come in B4 e B5 dipende dal progetto; se resta vuoto, la pagina dice come aggiungerlo.
- **La prova reale**: il progetto di prova non può usare `node`, `npm` né un browser (cautele). Serve un lavoro d'interfaccia verificabile con la sola libreria standard di Python (per esempio un componente in un file `.tsx` e un test che ne legge il testo), o un'altra strada, decisa con una ruling e con il costo.
- **Quali rinvii della sezione 9 si chiudono qui**: almeno `SAVED_READERS` chiuso e `tool_use_result.stderr` di `togli-pagine` (prima della prova reale), l'intestazione «Task 9» di `limiti.txt`, il caso misto in `ai/routes/`, i test di `rules-backend` da copiare con le correzioni.
- Dove la sessione d'esecuzione si ferma per l'approvazione delle regole, e se B6 è abbastanza piccola o va divisa (per esempio pattern per estensione da soli, poi il profilo).

## Lezioni di B5 da mettere nel piano e nelle istruzioni
- **Implementatori fermi dopo la suite.** Quattro su sei si sono fermati aspettando la notifica della suite in background. Dal Task 7 il dispatch diceva di lanciare la suite con l'uscita su un file del workspace e di restare attivi con `until grep -q '^exit ' <file>; do sleep 60; done` in primo piano (timeout 10 minuti, ripetuto): nessuno si è più fermato. Va nelle istruzioni e nel brief di ogni implementatore.
- **Sentinelle del controller.** La corsa su Python 3.13 parte con il percorso intero (`/usr/bin/python3`): una sentinella che cerca `^python3` non la vede, e un `pgrep -f` con il pattern nel proprio comando trova sé stesso. Le istruzioni danno il comando giusto.
- **Lavori in parallelo.** La revisione di un task in sola lettura mentre l'implementatore del task dopo lavora su file diversi ha funzionato, con una ruling per ogni parallelo.
- **Fonti.** Le pagine prese con `WebFetch` sono riassunti del modello: le citazioni del verificatore sono di una riga. Un marcatore o un pattern senza pagina ufficiale esce (B5: `export function POST(`). Un pattern con fonte ma troppo largo resta, con il costo nella pagina.
- **Evidenze.** `togli-pagine` lascia i risultati di `WebFetch` sotto i 5000 caratteri: il controller li legge a mano prima del rapporto e il rapporto lo dice.
- **Brief corto e hook di Stop.** Anche con le situazioni C e D l'hook di Stop ha chiesto di proseguire a ogni fermata: alle fermate (approvazione delle regole, una scelta della revisione finale, il merge, la rimozione del worktree) la sessione ha usato una domanda diretta all'utente. Le istruzioni lo dicono, e il brief corto tiene la domanda sul worktree tra le cose della chiusura.
- **Revisione finale.** Ha trovato un difetto di precedenza tra profili che nessun task guardava: il Review Focus di B6 lo nomina in modo esplicito.

## Come lavorare
- Le scelte vere (compromessi, costi) si chiedono all'utente in parole semplici, con il costo esplicito (gratis, consumo dell'abbonamento o spesa vera) e un consiglio. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere. Il resto si decide con una `Ruling:` scritta nel piano.
- Revisione del piano da opus a contesto pulito, in sola lettura, a giri, finché un giro dice «pronto» con 0 critical e 0 important. La tabella dei giri va in fondo al piano.
- Le regole di cautela vanno nel brief di ogni subagente, al lancio.

## Finito quando
- I quattro file esistono su `main`, committati.
- L'ultima riga della tabella dei giri del piano dice «pronto», 0 critical, 0 important.
- `plugin-workflow-decisioni.md` nella memoria ha una voce sul piano di B6.
- L'utente ha ricevuto, in italiano semplice, nell'ultimo messaggio della sessione: cosa fa B6, le scelte che gli sono state chieste e cosa ha risposto, quanto costerà eseguirlo, quando dovrà approvare le regole, e la riga `/goal` pronta per la sessione d'esecuzione.
